#!/usr/bin/env bash
# deploy-site.sh — build a site from its own repo and publish it to the platform.
#
# RUN IT FROM INSIDE THE SITE'S REPO, BY ITS PLATFORM PATH. It takes no site argument, on purpose:
# the site is found by looking up THE REPO YOU RAN IT FROM in the platform's registry
# (<websites-root>/sites.conf, never in a site repo). A site's own session cannot publish another
# site: there is no argument to misuse, and nothing it edits inside its own repo changes the answer.
# See guide/examples/E17-public-websites.md § 7.
#
# Usage, from the site's repo root or any subdirectory:
#   <websites-root>/bin/deploy-site.sh              build, then publish to PRODUCTION
#   <websites-root>/bin/deploy-site.sh --staging    build, then publish to STAGING
#   <websites-root>/bin/deploy-site.sh --dry-run    build, then show what would change
#   <websites-root>/bin/deploy-site.sh --no-build   publish the existing output as it is
#
# Publishing mirrors the output dir into <websites-root>/srv/<name>/ (or <name>-stg/) with
# `rsync -a --delete`; your web server serves that folder. Nothing restarts.
#
# Fails closed. It refuses to publish when: not in a git repo · the repo is not registered, or is
# registered twice · the name could escape its folder · the output dir resolves outside the repo ·
# the build fails · the build output is EMPTY (--delete would otherwise wipe the live site).
#
# WEBSITES_ROOT (default ~/websites) moves the registry AND the serving roots together. It exists
# for tests and for a platform kept elsewhere; a crafted root only redirects the caller into it.
#
# Honest limit: sessions running as the same OS user can still reach each other's files. This makes
# cross-site damage by accident structurally hard and visible; it does not prevent it on purpose.
#
# Exit: 0 published, or a dry run · 1 refused or failed · 2 bad usage
set -euo pipefail

ROOT="${WEBSITES_ROOT:-$HOME/websites}"
REGISTRY="$ROOT/sites.conf"
SERVE="$ROOT/srv"
STAGING=0; DRYRUN=0; BUILD=1

usage() { awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"; }
die() { echo "deploy-site.sh: $*" >&2; exit 1; }
trim() { local s="$1"; s="${s#"${s%%[![:space:]]*}"}"; s="${s%"${s##*[![:space:]]}"}"; printf '%s' "$s"; }

for a in "$@"; do
  case "$a" in
    --staging)  STAGING=1 ;;
    --dry-run)  DRYRUN=1 ;;
    --no-build) BUILD=0 ;;
    -h|--help)  usage; exit 0 ;;
    *) echo "deploy-site.sh: unknown argument '$a'. There is deliberately no site argument:" \
            "run it from inside the site's repo." >&2
       exit 2 ;;
  esac
done

[ -f "$REGISTRY" ] || die "no site registry at $REGISTRY — is the platform set up?"
command -v rsync >/dev/null 2>&1 || die "rsync not found"

# ── which repo are we in? ───────────────────────────────────────────────────────────────────────
REPO="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$REPO" ] || die "not inside a git repository — run this from the site's repo"
REPO_REAL="$(cd "$REPO" && pwd -P)"

# ── look that repo up in the PLATFORM's registry, by real path ──────────────────────────────────
NAME=""; BUILD_CMD=""; OUT=""; MATCHES=0
while IFS= read -r line || [ -n "$line" ]; do
  case "$(trim "$line")" in ''|\#*) continue ;; esac
  IFS='|' read -r f_name f_path f_cmd f_out _ <<EOF
$line
EOF
  f_path="$(trim "${f_path:-}")"
  # shellcheck disable=SC2088  # matching a LITERAL ~ from the registry, then expanding it by hand
  case "$f_path" in "~"|"~/"*) f_path="$HOME${f_path#\~}" ;; esac
  real="$(cd "$f_path" 2>/dev/null && pwd -P || true)"
  if [ -n "$real" ] && [ "$real" = "$REPO_REAL" ]; then
    MATCHES=$((MATCHES + 1))
    NAME="$(trim "${f_name:-}")"; BUILD_CMD="$(trim "${f_cmd:-}")"; OUT="$(trim "${f_out:-}")"
  fi
done < "$REGISTRY"

if [ "$MATCHES" -eq 0 ]; then
  echo "deploy-site.sh: this repo is not a registered site." >&2
  echo "  repo: $REPO_REAL" >&2
  echo "  Sites are registered on the platform side ($REGISTRY), not from a site's repo." >&2
  exit 1
fi
[ "$MATCHES" -eq 1 ] || die "this repo is registered $MATCHES times in $REGISTRY — refusing to guess"

# The name becomes a folder under the serving root, so it must not be able to leave it, and
# "-stg" is reserved for the staging root of the name before it.
case "$NAME" in
  ''|-*|*[!a-z0-9-]*|*-stg) die "registry name '$NAME' is not allowed: lowercase letters, digits and hyphens, not ending in -stg" ;;
esac

TARGET="$SERVE/$NAME"; ENVNAME=PRODUCTION
if [ "$STAGING" -eq 1 ]; then TARGET="$SERVE/$NAME-stg"; ENVNAME=STAGING; fi

echo "  repo:   $REPO_REAL"
echo "  site:   $NAME ($ENVNAME)"
echo "  target: $TARGET"

# ── build ───────────────────────────────────────────────────────────────────────────────────────
if [ "$BUILD" -eq 1 ] && [ -n "$BUILD_CMD" ] && [ "$BUILD_CMD" != "-" ]; then
  echo "  build:  $BUILD_CMD"
  ( cd "$REPO_REAL" && bash -c "$BUILD_CMD" ) || die "build failed — nothing was published"
else
  echo "  build:  skipped"
fi

# ── what to publish: inside the repo, and not empty ─────────────────────────────────────────────
SRC="$REPO_REAL/$OUT"
[ -d "$SRC" ] || die "build output not found: $SRC"
SRC_REAL="$(cd "$SRC" && pwd -P)"
case "$SRC_REAL/" in
  "$REPO_REAL"/?*) ;;
  *) die "output dir '$OUT' resolves to $SRC_REAL, which is not a folder inside the repo" ;;
esac
[ -n "$(ls -A "$SRC_REAL")" ] \
  || die "build output is EMPTY: $SRC_REAL — refusing to publish (--delete would wipe the live site)"

# ── publish ─────────────────────────────────────────────────────────────────────────────────────
echo "  publishing $(find "$SRC_REAL" -type f | wc -l | tr -d ' ') file(s)…"
if [ "$DRYRUN" -eq 1 ]; then
  if [ -d "$TARGET" ]; then
    rsync -a --delete --dry-run --itemize-changes "$SRC_REAL"/ "$TARGET"/ | sed 's/^/    /' \
      || die "rsync --dry-run failed"
  else
    echo "    (no $TARGET yet: every file would be new)"
  fi
  echo "  DRY RUN — nothing was published."
  exit 0
fi

mkdir -p "$TARGET"
rsync -a --delete "$SRC_REAL"/ "$TARGET"/ || die "rsync failed — the target may be partly updated"
echo "  published: $NAME ($ENVNAME)"
