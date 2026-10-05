#!/usr/bin/env bash
# install-fleet-launch.sh — build fleet-launch ONCE on this Mac and install it root-owned, with its
# allowlist. Run it yourself, in your own Terminal: sudo asks for your password.
#
#   skeleton/launcher/install-fleet-launch.sh            first install
#   skeleton/launcher/install-fleet-launch.sh --list     re-install ONLY the allowlist
#
# The allowlist is read from $FLEET_LAUNCH_STAGED (default ~/.config/fleet-launch/fleet-launch.allow) —
# stage it there with your config manager, per Mac, from fleet-launch.allow.example.
#
# Why it exists: guide/17c. Background jobs started through fleet-launch keep their macOS approvals
# across package updates, because macOS charges their access to fleet-launch — which this script builds
# once and NEVER again.
#
# ⚠ It refuses to rebuild an installed fleet-launch: a rebuild is a new program to macOS, and every
#   approval (network volumes, iCloud Drive) would be asked for again, on a screen nobody watches.
#   The allowlist is a separate file so it can change without a rebuild (--list).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/fleet-launch.c"
BIN=/usr/local/libexec/fleet-launch
ALLOW=/usr/local/etc/fleet-launch.allow
STAGED="${FLEET_LAUNCH_STAGED:-$HOME/.config/fleet-launch/fleet-launch.allow}"

say() { printf '%s\n' "$*"; }

[ "$(uname -s)" = Darwin ] || { say "✗ fleet-launch is macOS-only (it exists for macOS's privacy approvals)"; exit 1; }
[ -f "$STAGED" ] || { say "✗ no staged allowlist at $STAGED — stage it first (see fleet-launch.allow.example)"; exit 1; }

install_list() {
    sudo install -d -m 755 -o root -g wheel /usr/local/etc
    sudo install -m 644 -o root -g wheel "$STAGED" "$ALLOW"
    say "✓ allowlist installed: $ALLOW (root:wheel 644)"
    awk '!/^#/ && length { print "    " $0 }' "$ALLOW"    # awk, not grep: grep exits 1 on an empty list
}

if [ "${1:-}" = "--list" ]; then
    install_list
    exit 0
fi

if [ -e "$BIN" ]; then
    say "✗ $BIN is already installed — refusing to rebuild it."
    say "  A rebuild is a new program to macOS: every approval would be asked for again."
    say "  To change what it may run, edit the staged allowlist and run: $0 --list"
    exit 1
fi

command -v xcrun >/dev/null || { say "✗ no Xcode command-line tools (xcrun) — install them first"; exit 1; }
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
xcrun clang -O2 -Wall -Werror -o "$T/fleet-launch" "$SRC"
# the hardened runtime makes dyld ignore DYLD_* for this program: nobody can load code INTO it
codesign --force -s - -o runtime "$T/fleet-launch"
# ⚠ Read codesign's output into a variable first: `codesign | grep -q` under pipefail fails whenever
#   grep stops reading early and codesign is cut off — it refused a correct signature in 17 runs of 30.
sig=$(codesign -dv "$T/fleet-launch" 2>&1)
case "$sig" in
    *'flags=0x10002(adhoc,runtime)'*) ;;
    *) say "✗ signature is not ad-hoc + hardened runtime — refusing"; say "$sig"; exit 1 ;;
esac

sudo install -d -m 755 -o root -g wheel /usr/local/libexec
sudo install -m 755 -o root -g wheel "$T/fleet-launch" "$BIN"
install_list

# Self-check: a command that is NOT listed must be refused (exit 126) — proves the list is read and
# trusted (root-owned) by the installed binary.
set +e
"$BIN" /usr/bin/true 2>/dev/null
rc=$?
set -e
[ "$rc" = 126 ] || { say "✗ self-check: an unlisted command returned $rc, expected 126"; exit 1; }
hash=$(codesign -dvvv "$BIN" 2>&1 | awk -F= '$1 == "CDHash" { print $2 }' || true)   # awk reads it all: no cut-off
say "✓ installed: $BIN  (cdhash $hash)"
say "✓ self-check: an unlisted command is refused"
say ""
say "Next: point your scheduled jobs at it (README.md), then approve its prompts ONCE on this Mac's screen."
