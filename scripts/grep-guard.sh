#!/usr/bin/env bash
# grep-guard — fail if any personal/secret pattern appears in the tree.
#
# The backstop for a public/shared repo (guide/19-sharing.md). Runs as a pre-commit
# hook and as a CI check. FAILS CLOSED: a hit is a non-zero exit, and so is any
# error while scanning (an error that read as "clean" would be a silent pass). Bias
# toward noise — a false positive costs an annotation; a false negative is a
# permanent leak.
#
# Two layers:
#   1. GENERIC patterns (below) — paths, private IPs, emails, secret shapes. They
#      apply to everyone, so they live here, in public.
#   2. YOUR names — machine names, usernames, tailnet ID, repo names — one literal
#      per line, matched case-insensitively, in a LOCAL, gitignored file:
#      .grep-guard.local at the repo root, or the path in $GREP_GUARD_LOCAL. Never in
#      this script: listing your names in a public file would publish exactly what the
#      guard exists to protect.
#      Make the list mandatory in your own clone with:
#          git config --local grepguard.requireLocal true
#
# ⚠ PORTABILITY. The patterns are POSIX ERE and deliberately use NO `\b`: on macOS,
# `git grep -E` does not honour `\b`, so every pattern using it silently never
# matched there (found 2026-09-23 — IPs, emails and secrets all passed). Boundaries
# are written as `(^|[^0-9.])` etc. --self-test proves every shape on YOUR platform.
#
# Usage:
#   scripts/grep-guard.sh [--staged] [ROOT]   # default ROOT: the current directory
#       (default)  scan the working tree, including untracked files
#       --staged   scan the INDEX — what the commit will actually contain (the hook)
#   scripts/grep-guard.sh --self-test         # plant one leak per file, prove each is caught
#   PATTERNS_ONLY=1 scripts/grep-guard.sh     # print the effective patterns and exit
#
# Exit: 0 clean · 1 forbidden pattern found · 2 could not scan (fails closed)
set -euo pipefail

# ── Files/dirs the guard should NOT scan ────────────────────────────────────
#   - .git internals
#   - the guard itself + the docs that NAME the forbidden shapes by design.
#     Add your own allowlist entries — sparingly; every exclusion is a blind spot.
EXCLUDES=(
  ':(exclude).git/**'
  ':(exclude)**/grep-guard.sh'
  ':(exclude)**/19-sharing.md'
  ':(exclude)**/06-secrets.md'          # documents secret shapes by design
)

# ── Generic pattern classes (apply to everyone) ─────────────────────────────
# Parallel arrays (bash 3.2 has no associative arrays): label | flags | ERE.
# flags: E = extended regex, Ei = extended + case-insensitive.
PAT_LABEL=(); PAT_FLAGS=(); PAT_RE=()
pat() { PAT_LABEL+=("$1"); PAT_FLAGS+=("$2"); PAT_RE+=("$3"); }

pat "home path (macOS)"   E  '/Users/[a-z]'
pat "home path (linux)"   E  '/home/[a-z]'
pat "private IP 192.168"  E  '(^|[^0-9.])192\.168\.[0-9]{1,3}\.[0-9]{1,3}'
pat "private IP 10/8"     E  '(^|[^0-9.])10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'
pat "private IP 172.16/12" E '(^|[^0-9.])172\.(1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3}'
pat "CGNAT/tailnet IP"    E  '(^|[^0-9.])100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.[0-9]{1,3}\.[0-9]{1,3}'
pat "tailnet hostname"    Ei '[a-z0-9-]+\.tail[0-9a-f]{4,}\.ts\.net'
pat "email address"       E  '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'
pat "private key"         E  '-----BEGIN [A-Z ]*PRIVATE KEY-----'
pat "quoted secret"       Ei '(secret|token|passwd|password|api[_-]?key)[a-z0-9_-]*[[:space:]]*[:=][[:space:]]*["'"'"'][^"'"'"'<$[:space:]][^"'"'"']{5,}'
pat "unquoted secret"     E  '[A-Z0-9_]*(SECRET|TOKEN|PASSWORD|PASSWD|API_KEY|APIKEY)[A-Z0-9_]*=[^[:space:]"'"'"'<${][^[:space:]]{7,}'
pat "token: OpenAI/Anthropic" E 'sk-(ant-)?[A-Za-z0-9_-]{20,}'
pat "token: GitHub"       E  '(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,})'
pat "token: AWS key id"   E  'AKIA[0-9A-Z]{16}'
pat "token: Slack"        E  'xox[abprs]-[A-Za-z0-9-]{10,}'
pat "token: Google API"   E  'AIza[0-9A-Za-z_-]{35}'

# Test hook only: an extra pattern, used by --self-test to prove a scan ERROR fails closed.
[ -n "${GREP_GUARD_EXTRA_PATTERN:-}" ] && pat "extra (test)" E "$GREP_GUARD_EXTRA_PATTERN"

note() { printf '%s\n' "$*" >&2; }

# ── YOUR names: one literal per line in the local file ─────────────────────
FORBIDDEN_LITERALS=()
load_local() {
  local root="$1" file line
  file="${GREP_GUARD_LOCAL:-$root/.grep-guard.local}"
  if [ -f "$file" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
      line="${line%%#*}"                                   # strip comments
      line="$(printf '%s' "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
      [ -n "$line" ] && FORBIDDEN_LITERALS+=("$line")
    done < "$file"
    note "grep-guard: ${#FORBIDDEN_LITERALS[@]} personal name(s) from $file"
  else
    if [ "$(git -C "$root" config --bool grepguard.requireLocal 2>/dev/null || true)" = "true" ]; then
      note "grep-guard: FAILED — grepguard.requireLocal is set but $file does not exist."
      note "  Your personal names are NOT being checked. Restore the file; do not unset the flag."
      exit 2
    fi
    note "grep-guard: no local names list ($file) — generic patterns only. See guide/19-sharing.md."
  fi
}

fail=0
MODE=tree

# scan LABEL FLAGS PATTERN ROOT  — records hits; exits 2 on a scan error.
scan() {
  local label="$1" flags_kind="$2" pattern="$3" root="$4" rc=0 hits
  local flags=(-nI --color=never)
  case "$flags_kind" in
    E)  flags+=(-E) ;;
    Ei) flags+=(-E -i) ;;
    F)  flags+=(-F) ;;
    Fi) flags+=(-F -i) ;;
  esac
  if git -C "$root" rev-parse >/dev/null 2>&1; then
    if [ "$MODE" = staged ]; then
      hits="$(git -C "$root" grep "${flags[@]}" --cached -e "$pattern" -- . "${EXCLUDES[@]}" 2>&1)" || rc=$?
    else
      # --untracked: a leak is most likely in a NOT-yet-committed file.
      hits="$(git -C "$root" grep "${flags[@]}" --untracked -e "$pattern" -- . "${EXCLUDES[@]}" 2>&1)" || rc=$?
    fi
  else
    hits="$(grep "${flags[@]}" -r --exclude-dir=.git \
      --exclude=grep-guard.sh --exclude=19-sharing.md --exclude=06-secrets.md \
      --exclude=.grep-guard.local -e "$pattern" "$root" 2>&1)" || rc=$?
  fi
  case "$rc" in
    0) note "✗ [$label] forbidden pattern found:"; note "$hits"; note ""; fail=1 ;;
    1) : ;;                                                # no match
    *) note "grep-guard: FAILED — could not scan for [$label] (grep exit $rc):"; note "$hits"
       note "  An unscanned tree is not a clean tree."; exit 2 ;;
  esac
}

run_guard() {
  local root="$1" i
  load_local "$root"
  for i in "${!PAT_RE[@]}"; do scan "${PAT_LABEL[$i]}" "${PAT_FLAGS[$i]}" "${PAT_RE[$i]}" "$root"; done
  if [ "${#FORBIDDEN_LITERALS[@]}" -gt 0 ]; then
    for i in "${!FORBIDDEN_LITERALS[@]}"; do scan "your name #$((i + 1))" Fi "${FORBIDDEN_LITERALS[$i]}" "$root"; done
  fi
  if [ "$fail" -ne 0 ]; then
    note "grep-guard: FAILED — generalize the above before committing. Do NOT suppress the guard."
    exit 1
  fi
  note "grep-guard: clean ✅ ($MODE)"
}

# ── --self-test: one planted leak per file, each must be caught on its own ──
# Leaks are assembled at runtime so this script never contains one literally.
# One leak PER FILE matters: a line holding two leaks is caught by whichever
# pattern works, which is how a broken IP pattern once passed as "proven".
SELFTEST_TMP=""
self_test() {
  local self tmp ok=0 bad=0 i name content have_git=1 modes
  self="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
  # global, not local: the EXIT trap runs after the function's scope is gone on some bash versions
  SELFTEST_TMP="$(mktemp -d "${TMPDIR:-/tmp}/grep-guard-selftest.XXXXXX")"
  trap 'rm -rf "${SELFTEST_TMP:-}"' EXIT
  tmp="$SELFTEST_TMP"
  command -v git >/dev/null 2>&1 || have_git=0
  if [ "$have_git" -eq 1 ]; then modes="tree staged plain"; else
    modes="plain"; note "grep-guard self-test: git not found — testing the plain-directory path only"
  fi
  local D="." A="@" U="/Us""ers/" H="/ho""me/" K="-----BEGIN"
  local names=() contents=()
  add() { names+=("$1"); contents+=("$2"); }
  add "home path (macOS)"    "path ${U}someone/project"
  add "home path (linux)"    "path ${H}someone/project"
  add "192.168 address"      "host 192${D}168${D}1${D}5 here"
  add "10.x address"         "net 10${D}0${D}0${D}1 here"
  add "172.16/12 address"    "net 172${D}20${D}3${D}4 here"
  add "CGNAT address"        "node 100${D}101${D}102${D}103 here"
  add "tailnet hostname"     "url https://box${D}tail1a2b${D}ts${D}net/"
  add "email address"        "contact someone${A}example${D}org"
  add "private key"          "${K} OPENSSH PRIVATE KEY-----"
  add "quoted secret"        "password = \"hunter2hunter2\""
  add "unquoted secret"      "export API_KEY=abcd1234efgh5678"
  add "Anthropic-style key"  "key sk-ant-$(printf 'x%.0s' $(seq 1 24))"
  add "GitHub token"         "tok ghp_$(printf 'A%.0s' $(seq 1 36))"
  add "AWS key id"           "id AKIA$(printf 'Z%.0s' $(seq 1 16))"
  add "Slack token"          "tok xoxb-1234567890-abcdefghij"
  add "Google API key"       "key AIza$(printf 'b%.0s' $(seq 1 35))"
  add "your name (any case)" "the machine SelfTestBox9 is private"

  # A leak must be caught in BOTH modes; a clean file must pass in both.
  for i in "${!names[@]}"; do
    name="${names[$i]}"; content="${contents[$i]}"
    for mode in $modes; do
      rm -rf "$tmp/r"; mkdir -p "$tmp/r"
      printf '%s\n' "$content" > "$tmp/r/planted.txt"
      printf 'selftestbox9\n' > "$tmp/r/.grep-guard.local"
      if [ "$mode" != plain ]; then
        git -C "$tmp/r" init -q
        printf '.grep-guard.local\n' > "$tmp/r/.git/info/exclude"
        git -C "$tmp/r" add planted.txt
      fi
      local args=(); [ "$mode" = staged ] && args+=(--staged)
      if ( cd "$tmp/r" && "$self" ${args[@]+"${args[@]}"} . ) >/dev/null 2>&1; then
        note "  FAIL  $name ($mode) — NOT caught"; bad=$((bad + 1))
      else
        ok=$((ok + 1))
      fi
    done
  done
  # clean fixture: must pass (proves the patterns are not simply matching everything)
  for mode in $modes; do
    rm -rf "$tmp/r"; mkdir -p "$tmp/r"
    printf 'Use $HOME/project, <your-host>, 127.0.0.1 and version 10.4 of the tool.\nSMTP_PASSWORD=\nAPI_KEY=<your-key>\n' > "$tmp/r/clean.txt"
    printf 'selftestbox9\n' > "$tmp/r/.grep-guard.local"      # the names file itself is never a hit
    if [ "$mode" != plain ]; then
      git -C "$tmp/r" init -q; printf '.grep-guard.local\n' > "$tmp/r/.git/info/exclude"
      git -C "$tmp/r" add clean.txt
    fi
    local args=(); [ "$mode" = staged ] && args+=(--staged)
    if ( cd "$tmp/r" && "$self" ${args[@]+"${args[@]}"} . ) >/dev/null 2>&1; then ok=$((ok + 1))
    else note "  FAIL  clean fixture ($mode) — flagged"; bad=$((bad + 1)); fi
  done
  if [ "$have_git" -eq 1 ]; then
  # --staged must read the INDEX: a leak staged and then cleaned in the working copy is
  # still in the commit, so the tree scan passes it but the staged scan must not
  rm -rf "$tmp/r"; mkdir -p "$tmp/r"; git -C "$tmp/r" init -q
  printf 'host 192%s168%s1%s5\n' "$D" "$D" "$D" > "$tmp/r/a.txt"; git -C "$tmp/r" add a.txt
  printf 'clean now\n' > "$tmp/r/a.txt"
  if ( cd "$tmp/r" && "$self" --staged . ) >/dev/null 2>&1; then
    note "  FAIL  a leak in the index but not the working copy passed --staged"; bad=$((bad + 1))
  else ok=$((ok + 1)); fi
  # a scan ERROR must fail closed (exit 2), never read as clean
  rm -rf "$tmp/r"; mkdir -p "$tmp/r"; git -C "$tmp/r" init -q; printf 'x\n' > "$tmp/r/a.txt"
  local rc=0
  ( cd "$tmp/r" && GREP_GUARD_EXTRA_PATTERN='(' "$self" . ) >/dev/null 2>&1 || rc=$?
  if [ "$rc" -eq 2 ]; then ok=$((ok + 1)); else note "  FAIL  scan error exited $rc, not 2 (fail closed)"; bad=$((bad + 1)); fi
  # requireLocal set + list missing must fail (exit 2)
  rm -rf "$tmp/r"; mkdir -p "$tmp/r"; git -C "$tmp/r" init -q; git -C "$tmp/r" config grepguard.requireLocal true
  printf 'x\n' > "$tmp/r/a.txt"; rc=0
  ( cd "$tmp/r" && "$self" . ) >/dev/null 2>&1 || rc=$?
  if [ "$rc" -eq 2 ]; then ok=$((ok + 1)); else note "  FAIL  requireLocal without a list exited $rc, not 2"; bad=$((bad + 1)); fi
  fi

  if [ "$bad" -eq 0 ]; then note "grep-guard self-test: ALL $ok PASS"; exit 0; fi
  note "grep-guard self-test: $bad FAILED, $ok passed — the guard is NOT protecting this repo."
  exit 1
}

# ── main ────────────────────────────────────────────────────────────────────
ROOT="."
while [ $# -gt 0 ]; do
  case "$1" in
    --self-test) self_test ;;
    --staged)    MODE=staged ;;
    -h|--help)   sed -n '2,33p' "$0"; exit 0 ;;
    *)           ROOT="$1" ;;
  esac
  shift
done

if [ "${PATTERNS_ONLY:-0}" = "1" ]; then
  note "== generic patterns =="
  for i in "${!PAT_RE[@]}"; do note "  [${PAT_LABEL[$i]}] ${PAT_RE[$i]}"; done
  load_local "$ROOT"
  exit 0
fi

run_guard "$ROOT"
