#!/usr/bin/env bash
# enable-repo-index.sh — turn on a repo index for THIS repository. Idempotent.
#
# Commits exactly two things: the ignore file and one .gitignore line. Everything else (the tool,
# the built index, the refresh hook) is per-clone/per-machine and is reported as a manual step,
# because a repo cannot ship a working git hook — .git/hooks/ is never committed.
#
# Nothing here is destructive: existing files are kept, never overwritten.
#
# Usage:
#   ./enable-repo-index.sh [--ignore-name .graphifyignore] [--out-dir graphify-out] [repo-root]
set -euo pipefail

IGNORE_NAME=".graphifyignore"     # your indexer's exclusion file
OUT_DIR="graphify-out"            # your indexer's output directory
ROOT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --ignore-name) IGNORE_NAME="$2"; shift 2 ;;
    --out-dir)     OUT_DIR="$2";     shift 2 ;;
    -h|--help)     sed -n '2,12p' "$0"; exit 0 ;;
    *)             ROOT="$1";        shift ;;
  esac
done

HERE="$(cd "$(dirname "$0")" && pwd)"
[ -n "$ROOT" ] || ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

echo "Enabling repo index in: $ROOT"

# 1) the exclusion file — never clobber one you've already tuned
if [ -e "$IGNORE_NAME" ]; then
  echo "  kept existing: $IGNORE_NAME"
else
  cp "$HERE/indexignore.template" "$IGNORE_NAME"
  echo "  created: $IGNORE_NAME  (EDIT IT — the defaults are a starting point, not your repo)"
fi

# 2) the .gitignore line — the index must never be committed
if [ -f .gitignore ] && grep -qx "${OUT_DIR}/" .gitignore 2>/dev/null; then
  echo "  kept existing: .gitignore already ignores ${OUT_DIR}/"
else
  printf '\n# Repo index output — derived, large, churns every build. Never commit.\n%s/\n' "$OUT_DIR" >> .gitignore
  echo "  appended to .gitignore: ${OUT_DIR}/"
fi

cat <<EOF

Committed footprint done. Three manual steps remain — the script cannot do these for you:

  1. TELL THE OPERATOR IT EXISTS. Add a line to CLAUDE.md / AGENTS.md saying the index is present
     and to prefer querying it over grepping. Skip this and nothing will use it.

  2. BUILD THE INDEX (per clone; the output is gitignored, so this never dirties the repo).

  3. INSTALL THE REFRESH HOOK (per clone, per machine — .git/hooks/ is never committed, so this
     cannot ship with the repo). Then VERIFY IT ACTUALLY RUNS: a refresh hook is usually
     non-blocking, so a failing one is invisible. Read its status output, don't just check that
     the hook file exists.

  If this repo already had an index built by an OLDER version of your indexer, do ONE forced
  rebuild now to re-baseline. Upgrades that change ignore semantics legitimately shrink the index,
  and a shrink guard will otherwise refuse every future write — silently. See
  ../../guide/12-repo-comprehension.md.
EOF
