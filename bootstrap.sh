#!/usr/bin/env bash
# bootstrap.sh — set up YOUR private personal-SRE repo (guide/13-setup.md, Tier 2).
#
# This framework repo is a READ-ONLY REFERENCE. You do NOT work in it. bootstrap
# creates (or points you at) YOUR OWN private repo, where all your work happens —
# then hands off to an AI CLI session that resumes setup from the seeded state.
#
# What it does:
#   1. Detects your platform + checks hard-core prerequisites (offers to install).
#   2. (optional) Creates your private git repo — only if your `gh` auth can, after
#      a tell-then-ask y/N prompt. Degrades gracefully to manual steps otherwise.
#   3. Seeds your repo (UNCOMMITTED) with a rules file, a project registry, and an
#      onboarding "resume here" doc — so your next AI CLI session picks up where
#      this left off.
#   4. Tells you to continue in the new repo with the AI CLI of your choice.
#
# Everything has a default, is overridable by a flag OR an interactive prompt.
# Precedence: command-line flag > interactive prompt > default.  Nothing is
# committed or pushed; installs and repo creation always ask first.
set -euo pipefail

# ── Defaults (all overridable) ──────────────────────────────────────────────
REPO_NAME=""                 # default computed below (personal-sre)
TARGET_DIR=""                # default $HOME/Developer/<repo-name>
ROLE=""                      # default workstation
GIT_HOST="github.com"
GIT_USER=""                  # default from gh/git config
CREATE_REPO="ask"            # ask | no  (--no-create-repo => no)
ASSUME_YES=0                 # --yes => accept defaults, skip prompts
FRAMEWORK_DIR="$(cd "$(dirname "$0")" && pwd)"   # where this reference repo lives

usage() {
  cat <<EOF
bootstrap.sh — set up your own private personal-SRE repo from this framework.

USAGE:
  ./bootstrap.sh [options]

OPTIONS (all optional; each has a default and can also be entered when prompted):
  --repo-name <name>   Name of your private repo            (default: personal-sre)
  --dir <path>         Where to create/clone it locally     (default: \$HOME/Developer/<repo-name>)
  --role <role>        This node's role                     (default: workstation)
                       one of: workstation | server | nas | windows-node | <your own>
  --git-host <host>    Git host                             (default: github.com)
  --git-user <user>    Your git username                    (default: from gh/git config)
  --no-create-repo     Don't create a remote repo; print manual steps instead
  --yes                Non-interactive: accept all defaults, skip prompts
  -h, --help           Show this help and exit

EXAMPLES:
  ./bootstrap.sh
  ./bootstrap.sh --repo-name my-sre --dir ~/code/my-sre --role server
  ./bootstrap.sh --yes            # accept every default, no prompts

NOTE: This framework repo is a read-only reference — you never edit or commit to
it. bootstrap sets up YOUR repo; your work happens there. Nothing is committed by
this script; it seeds files uncommitted and hands off to your AI CLI.
EOF
}

# ── Parse flags ─────────────────────────────────────────────────────────────
while [ $# -gt 0 ]; do
  case "$1" in
    --repo-name) REPO_NAME="$2"; shift 2 ;;
    --dir)       TARGET_DIR="$2"; shift 2 ;;
    --role)      ROLE="$2"; shift 2 ;;
    --git-host)  GIT_HOST="$2"; shift 2 ;;
    --git-user)  GIT_USER="$2"; shift 2 ;;
    --no-create-repo) CREATE_REPO="no"; shift ;;
    --yes|-y)    ASSUME_YES=1; shift ;;
    -h|--help)   usage; exit 0 ;;
    *) echo "unknown option: $1 (try --help)" >&2; exit 2 ;;
  esac
done

say()  { printf '\n\033[1m%s\033[0m\n' "$*"; }
info() { printf '  %s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }
# prompt with default: prompt_default VAR "question" "default"
# If the var is already set (a flag was passed), keep it. Under --yes, take the
# default without prompting. Otherwise prompt, defaulting on empty input.
prompt_default() {
  local __var="$1" q="$2" def="$3" ans
  if [ -n "${!__var}" ]; then
    return 0                                   # already set via flag — keep it
  fi
  if [ "$ASSUME_YES" = 1 ]; then
    printf -v "$__var" '%s' "$def"
    return 0
  fi
  read -r -p "  $q [$def]: " ans
  printf -v "$__var" '%s' "${ans:-$def}"
  return 0
}
ask() {  # yes/no, default No
  local ans; [ "$ASSUME_YES" = 1 ] && return 0
  read -r -p "  $1 [y/N] " ans; [ "$ans" = y ] || [ "$ans" = Y ]
}

# ── Detect platform ─────────────────────────────────────────────────────────
case "$(uname -s 2>/dev/null)" in
  Darwin) PLATFORM=macos; SPOKE="platforms/macos.md" ;;
  Linux)  PLATFORM=linux; SPOKE="platforms/linux.md" ;;
  *)      PLATFORM=unknown; SPOKE="platforms/*.md" ;;
esac

say "Personal-SRE framework · bootstrap"
info "This reference repo: $FRAMEWORK_DIR (read-only — you won't edit it)"
info "Platform: $PLATFORM   ·   platform guide: $SPOKE"
info "Goal: set up YOUR OWN private repo where all your work will happen."

# ── 1. Hard-core prerequisites ──────────────────────────────────────────────
say "1. Checking hard-core requirements (guide/07-tools-requirements.md)…"
MISSING=()
for t in git chezmoi; do have "$t" && info "✓ $t" || { info "✗ $t (missing)"; MISSING+=("$t"); }; done
have gh   && info "✓ gh (GitHub CLI — enables repo creation below)" || info "• gh not found (optional, but needed to auto-create your repo)"
have node && info "✓ node ($(node --version 2>/dev/null))" || info "• node not found — needed for the AI CLI + most MCP servers (guide/07, guide/10)"
have claude && info "✓ claude (AI CLI)" || info "• AI CLI (Claude Code) not on PATH — install per $SPOKE; you'll also need an account/subscription"
info "• Secret store: set up per $SPOKE (Keychain / Credential Manager / libsecret / a vault) — guide/06-secrets.md"

if [ "${#MISSING[@]}" -gt 0 ]; then
  say "Missing core tools: ${MISSING[*]}"
  if [ "$PLATFORM" = macos ] && have brew; then
    ask "Install with 'brew install ${MISSING[*]}'?" && brew install "${MISSING[@]}"
  else
    info "Install ${MISSING[*]} via your package manager (see $SPOKE), then re-run."
  fi
fi

# ── 2. Resolve settings (flag > prompt > default) ───────────────────────────
say "2. Your repo settings"
: "${REPO_NAME:=}"; prompt_default REPO_NAME "Private repo name" "personal-sre"
: "${TARGET_DIR:=}"; prompt_default TARGET_DIR "Local directory for it" "$HOME/Developer/$REPO_NAME"
: "${ROLE:=}"; prompt_default ROLE "This node's role" "workstation"
if [ -z "$GIT_USER" ]; then
  GIT_USER="$(gh api user --jq .login 2>/dev/null || git config user.name 2>/dev/null || echo '')"
fi
: "${GIT_USER:=}"; prompt_default GIT_USER "Your git username" "${GIT_USER:-<your-username>}"
info "→ repo: $GIT_HOST/$GIT_USER/$REPO_NAME   dir: $TARGET_DIR   role: $ROLE"

# ── 3. Create (or point at) YOUR private repo ───────────────────────────────
say "3. Your private repo"
CAN_CREATE=0
if [ "$CREATE_REPO" = "no" ]; then
  info "Skipping repo creation (--no-create-repo)."
elif ! have gh; then
  info "gh (GitHub CLI) not installed — can't auto-create. Install it, or create the repo"
  info "manually at https://$GIT_HOST/new (PRIVATE), then re-run or clone it to $TARGET_DIR."
elif ! gh auth status >/dev/null 2>&1; then
  info "gh is installed but not authenticated. Run 'gh auth login' (grant 'repo' scope to let"
  info "bootstrap create your repo), then re-run. Or create it manually at https://$GIT_HOST/new."
else
  # Authed — check whether the token can create a repo (needs 'repo' scope).
  SCOPES="$(gh auth status 2>&1 | grep -i 'Token scopes' || true)"
  if echo "$SCOPES" | grep -qiE "'repo'|\brepo\b"; then
    CAN_CREATE=1
  else
    info "Your gh token is authenticated but may lack the 'repo' scope needed to create a repo."
    info "  Detected: ${SCOPES:-<none reported>}"
    info "  Grant it with:  gh auth refresh -h $GIT_HOST -s repo"
    info "  (More GitHub permission = more the operator can automate without asking you —"
    info "   the convenience/blast-radius trade-off; see guide/09-permissions.md.)"
    info "Falling back to manual: create a PRIVATE repo at https://$GIT_HOST/new, then re-run."
  fi
fi

REPO_READY=0
if [ "$CAN_CREATE" = 1 ]; then
  say "Ready to create your private repo:"
  info "  • create  https://$GIT_HOST/$GIT_USER/$REPO_NAME  (PRIVATE)"
  info "  • clone it to  $TARGET_DIR"
  info "  • seed it (UNCOMMITTED) with your rules file, project registry, and an onboarding doc"
  info "  Nothing is committed or pushed; the seed is left for your AI CLI to commit (with your ok)."
  if ask "Proceed?"; then
    if gh repo view "$GIT_USER/$REPO_NAME" >/dev/null 2>&1; then
      info "Repo already exists — cloning it instead of creating."
      gh repo clone "$GIT_USER/$REPO_NAME" "$TARGET_DIR"
    else
      gh repo create "$GIT_USER/$REPO_NAME" --private --clone --description "Personal-SRE (from optiquity-personal-sre framework)"
      # gh clones into ./<name>; move if the user chose a different dir
      [ -d "./$REPO_NAME/.git" ] && [ "$(cd "./$REPO_NAME" && pwd)" != "$TARGET_DIR" ] && { mkdir -p "$(dirname "$TARGET_DIR")"; mv "./$REPO_NAME" "$TARGET_DIR"; }
    fi
    REPO_READY=1
  else
    info "Skipped. You can create it later, or run with --no-create-repo for manual steps."
  fi
fi

# ── 4. Seed the repo (UNCOMMITTED) ──────────────────────────────────────────
if [ "$REPO_READY" = 1 ] && [ -d "$TARGET_DIR/.git" ]; then
  say "4. Seeding your repo (uncommitted)…"
  # Copy the onboarding seed from this framework, filling placeholders.
  mkdir -p "$TARGET_DIR/docs/onboarding"
  # Rules file (filled from the template):
  sed -e "s|<your-repo-name>|$REPO_NAME|g" -e "s|<git-host>|$GIT_HOST|g" -e "s|<git-user>|$GIT_USER|g" \
      "$FRAMEWORK_DIR/skeleton/CLAUDE.md.template" > "$TARGET_DIR/CLAUDE.md" 2>/dev/null || true
  # Onboarding registry + resume-here doc:
  if [ -f "$FRAMEWORK_DIR/skeleton/onboarding/PROJECTS.md" ]; then
    sed -e "s|<repo-name>|$REPO_NAME|g" -e "s|<role>|$ROLE|g" \
        "$FRAMEWORK_DIR/skeleton/onboarding/PROJECTS.md" > "$TARGET_DIR/PROJECTS.md"
  fi
  if [ -f "$FRAMEWORK_DIR/skeleton/onboarding/onboarding-PLAN.md" ]; then
    sed -e "s|<repo-name>|$REPO_NAME|g" -e "s|<role>|$ROLE|g" -e "s|<framework-dir>|$FRAMEWORK_DIR|g" \
        "$FRAMEWORK_DIR/skeleton/onboarding/onboarding-PLAN.md" > "$TARGET_DIR/docs/onboarding/PLAN.md"
  fi
  info "✓ Seeded (uncommitted): CLAUDE.md, PROJECTS.md, docs/onboarding/PLAN.md"
  info "  Review + your first commit happen in the next step, under your approval."
fi

# ── 5. Hand off ─────────────────────────────────────────────────────────────
say "Bootstrap done."
if [ "$REPO_READY" = 1 ]; then
  info "Your private repo is ready at:  $TARGET_DIR"
  info "CONTINUE THERE — open your AI CLI of choice IN THAT DIRECTORY:"
  info "    cd \"$TARGET_DIR\" && <your-ai-cli>"
  info "It will read the seeded rules + PROJECTS.md, see the open 'onboarding' project, and"
  info "offer the next steps (referencing GETTING-STARTED.md + guide/). Its first proposed"
  info "action will be your initial commit — approve it to exercise the governed loop."
else
  info "No repo was created. Next: create a PRIVATE repo, clone it, then either run the"
  info "Tier-3 path (paste the Tier-3 prompt from GETTING-STARTED.md into your AI CLI) or 'chezmoi init' (Tier 1)."
  info "Full walkthrough: GETTING-STARTED.md."
fi
info "Reminder: never edit THIS framework repo ($FRAMEWORK_DIR) — it's a read-only reference."
