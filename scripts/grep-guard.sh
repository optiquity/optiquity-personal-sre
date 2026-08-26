#!/usr/bin/env bash
# grep-guard — fail if any personal/secret pattern appears in the tree.
#
# The backstop for a public/shared repo (guide § 13). Runs as a pre-commit hook
# and/or a CI check. FAILS CLOSED: any hit is a non-zero exit. Bias toward noise —
# a false positive costs an annotation; a false negative is a permanent leak.
#
# Configure the FORBIDDEN_* lists below with YOUR specific identifiers (the names,
# usernames, emails, and repo name you are scrubbing away). The generic pattern
# classes (paths, IPs, secret shapes) apply to everyone.
#
# Usage:
#   scripts/grep-guard.sh [path ...]      # default: the repo root
#   PATTERNS_ONLY=1 scripts/grep-guard.sh # print the effective patterns and exit
#
# Pre-commit hook: symlink or call this from .git/hooks/pre-commit.
# CI: run it as a step; a non-zero exit fails the build.
set -euo pipefail

ROOT="${1:-.}"

# ── Files/dirs the guard should NOT scan ────────────────────────────────────
#   - .git internals
#   - the guard itself + the sharing guide, which NAME the forbidden patterns by
#     design (they document what to exclude). Add your own allowlist entries.
EXCLUDES=(
  ':(exclude).git/**'
  ':(exclude)**/grep-guard.sh'
  ':(exclude)**/15-sharing.md'
  ':(exclude)**/06-secrets.md'          # documents secret shapes by design
)

# ── Generic pattern classes (apply to everyone) ─────────────────────────────
# Personal paths, private IP ranges, tailnet-ID shape, and secret shapes.
GENERIC_PATTERNS=(
  '/Users/[a-z]'                         # macOS home paths
  '/home/[a-z]'                          # linux home paths
  '\b(192\.168|10\.|172\.(1[6-9]|2[0-9]|3[01]))\.[0-9]'  # RFC1918 IPs
  '\b100\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b'          # CGNAT / tailscale range
  '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'   # any email address
  '-----BEGIN [A-Z ]*PRIVATE KEY-----'   # private keys
  '\b[A-Za-z0-9_-]*(secret|token|passwd|password|api[_-]?key)[A-Za-z0-9_-]*\s*[:=]\s*["'"'"'][^"'"'"']+'  # key=value secrets
)

# ── YOUR forbidden identifiers — FILL THESE IN ──────────────────────────────
# The specific strings unique to you that must never appear. Examples commented;
# replace with your real values (they live only in this local guard config, which
# itself is NOT published — or is published with these lists emptied/placeholdered).
FORBIDDEN_LITERALS=(
  # 'your-github-username'
  # 'your-real-name'
  # 'your-machine-name-1'
  # 'your-private-repo-name'
  # 'your-tailnet-id'
)

fail=0
note() { printf '%s\n' "$*" >&2; }

if [ "${PATTERNS_ONLY:-0}" = "1" ]; then
  note "== generic patterns =="; printf '  %s\n' "${GENERIC_PATTERNS[@]}" >&2
  note "== forbidden literals =="; printf '  %s\n' "${FORBIDDEN_LITERALS[@]:-<none set>}" >&2
  exit 0
fi

scan() {
  local label="$1" pat="$2" fixed="${3:-}"
  local flags=(-nI --color=never)
  [ "$fixed" = "fixed" ] && flags+=(-F) || flags+=(-E)
  local hits
  if git -C "$ROOT" rev-parse >/dev/null 2>&1; then
    # --untracked: scan working-tree files too (a leak is most likely in a NOT-yet-
    # committed file — the whole point of a pre-commit guard). Excludes still apply.
    hits="$(git -C "$ROOT" grep "${flags[@]}" --untracked -e "$pat" -- . "${EXCLUDES[@]}" 2>/dev/null || true)"
  else
    # Not a repo: plain recursive grep, minus .git and the self/allowlisted docs.
    hits="$(grep "${flags[@]}" -r \
      --exclude-dir=.git \
      --exclude=grep-guard.sh --exclude=15-sharing.md --exclude=06-secrets.md \
      -e "$pat" "$ROOT" 2>/dev/null || true)"
  fi
  if [ -n "$hits" ]; then
    note "✗ [$label] forbidden pattern found:"; note "$hits"; note ""
    fail=1
  fi
}

for p in "${GENERIC_PATTERNS[@]}"; do scan "generic" "$p"; done
for lit in "${FORBIDDEN_LITERALS[@]:-}"; do [ -n "$lit" ] && scan "literal" "$lit" fixed; done

if [ "$fail" -ne 0 ]; then
  note "grep-guard: FAILED — generalize the above before committing. Do NOT suppress the guard."
  exit 1
fi
note "grep-guard: clean ✅"
