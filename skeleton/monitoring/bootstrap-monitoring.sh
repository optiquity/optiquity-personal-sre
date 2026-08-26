#!/usr/bin/env bash
# bootstrap-monitoring.sh — stand up the fleet-monitoring tools on THIS node.
#
# Run on your ALWAYS-ON node (the one that SSHes out to the rest of the fleet). Idempotent:
# installs the five CLIs, seeds config + secret stubs (never clobbering ones you've filled), and
# — with --with-timer — loads three launchd jobs: the weekly update digest, the ~15-min local
# health probe, and the after-install WatchPaths audit trigger. Deploying Gatus itself and its
# config is a separate, node-specific step (see README.md § Gatus), because Gatus usually runs
# on a different node (a gateway/Pi) with root-owned config.
#
# Usage:
#   ./bootstrap-monitoring.sh                 # tools + config/secret stubs only
#   ./bootstrap-monitoring.sh --with-timer    # also install + load the weekly launchd timer (macOS)
#   FLEET_LABEL=com.you.fleet-update-check ./bootstrap-monitoring.sh --with-timer
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="$HOME/.local/bin"
CFG="$HOME/.config/fleet-monitoring"
LABEL="${FLEET_LABEL:-com.example.fleet-update-check}"
LOCAL_LABEL="${FLEET_LOCAL_LABEL:-com.example.fleet-local-check}"
AUDIT_LABEL="${FLEET_AUDIT_LABEL:-com.example.fleet-install-audit}"
DO_TIMER=0
[ "${1:-}" = "--with-timer" ] && DO_TIMER=1

mkdir -p "$BIN" "$CFG"
install -m 755 "$HERE/fleet-mail"           "$BIN/fleet-mail"
install -m 755 "$HERE/fleet-update-check"   "$BIN/fleet-update-check"
install -m 755 "$HERE/fleet-local-check"    "$BIN/fleet-local-check"
install -m 755 "$HERE/fleet-install-audit"  "$BIN/fleet-install-audit"
install -m 755 "$HERE/fleet-container-check" "$BIN/fleet-container-check"
echo "installed: fleet-mail, fleet-update-check, fleet-local-check, fleet-install-audit, fleet-container-check (in $BIN)"

seed() {  # src dest mode — never overwrite a file you've already filled in
  if [ -e "$2" ]; then echo "kept existing: $2"; else install -m "$3" "$1" "$2"; echo "seeded:  $2  (edit me)"; fi
}
seed "$HERE/mail.env.template"           "$CFG/mail.env"           600
seed "$HERE/fleet-nodes.conf.template"   "$CFG/fleet-nodes.conf"   644
seed "$HERE/local-checks.conf.template"  "$CFG/local-checks.conf"  644

if [ "$DO_TIMER" = 1 ]; then
  case "$(uname -s)" in
    Darwin)
      LA="$HOME/Library/LaunchAgents"; mkdir -p "$LA"
      load_timer() {  # label template desc
        local pl="$LA/$1.plist"
        sed -e "s#__HOME__#$HOME#g" -e "s#__LABEL__#$1#g" "$HERE/$2" > "$pl"; chmod 644 "$pl"
        launchctl bootstrap "gui/$(id -u)" "$pl" 2>/dev/null \
          || echo "  (already loaded — 'launchctl bootout gui/$(id -u) $pl' to reload)"
        echo "timer: $pl  ($3)"
      }
      load_timer "$LABEL"       fleet-update-check.plist.template "weekly Mon 09:00"
      load_timer "$LOCAL_LABEL" fleet-local-check.plist.template  "every 15 min"
      load_timer "$AUDIT_LABEL" fleet-install-audit.plist.template "WatchPaths, after any install"
      ;;
    *)
      echo "timer: on Linux, wrap fleet-update-check (weekly) + fleet-local-check (~15 min) in systemd timers or cron, and fleet-install-audit --local in a systemd .path unit watching your install dirs (see README)."
      ;;
  esac
fi

cat <<EOF

next steps:
  1) SMTP secret:   \$EDITOR $CFG/mail.env          # SMTP_PASSWORD + from/to; keep it chmod 600
  2) node list:     \$EDITOR $CFG/fleet-nodes.conf   # roles, ssh-targets, os, methods (digest)
  3) local checks:  \$EDITOR $CFG/local-checks.conf  # service/mount/http/command probes
  4) test mail:     fleet-mail -s "test" --body "hello from \$(hostname)"
  5) test digest:   fleet-update-check --dry-run     # then drop --dry-run to email
  6) test local:    fleet-local-check  --dry-run     # then drop --dry-run to email on transitions
  7) schedule:      re-run with --with-timer (macOS) or add systemd timers/cron (Linux)
  8) Gatus health + alerts: separate node-specific deploy — see README.md § Gatus.
EOF
