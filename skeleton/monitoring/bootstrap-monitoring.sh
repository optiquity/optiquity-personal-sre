#!/usr/bin/env bash
# bootstrap-monitoring.sh — stand up the fleet-monitoring tools on THIS node.
#
# Run on your ALWAYS-ON node (the one that SSHes out to the rest of the fleet). Idempotent:
# installs the two CLIs, seeds config + secret stubs (never clobbering ones you've filled), and
# — with --with-timer — installs the weekly update-digest timer. Deploying Gatus itself and its
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
DO_TIMER=0
[ "${1:-}" = "--with-timer" ] && DO_TIMER=1

mkdir -p "$BIN" "$CFG"
install -m 755 "$HERE/fleet-mail"          "$BIN/fleet-mail"
install -m 755 "$HERE/fleet-update-check"  "$BIN/fleet-update-check"
echo "installed: $BIN/fleet-mail, $BIN/fleet-update-check"

seed() {  # src dest mode — never overwrite a file you've already filled in
  if [ -e "$2" ]; then echo "kept existing: $2"; else install -m "$3" "$1" "$2"; echo "seeded:  $2  (edit me)"; fi
}
seed "$HERE/mail.env.template"          "$CFG/mail.env"          600
seed "$HERE/fleet-nodes.conf.template"  "$CFG/fleet-nodes.conf"  644

if [ "$DO_TIMER" = 1 ]; then
  case "$(uname -s)" in
    Darwin)
      LA="$HOME/Library/LaunchAgents"; mkdir -p "$LA"
      PL="$LA/$LABEL.plist"
      sed -e "s#__HOME__#$HOME#g" -e "s#__LABEL__#$LABEL#g" \
          "$HERE/fleet-update-check.plist.template" > "$PL"
      chmod 644 "$PL"
      launchctl bootstrap "gui/$(id -u)" "$PL" 2>/dev/null \
        || echo "  (already loaded — 'launchctl bootout gui/$(id -u) $PL' to reload)"
      echo "timer: installed + loaded $PL  (weekly Mon 09:00; edit the plist to change)"
      ;;
    *)
      echo "timer: on Linux, wrap fleet-update-check in a weekly systemd timer or cron entry (see README)."
      ;;
  esac
fi

cat <<EOF

next steps:
  1) SMTP secret:   \$EDITOR $CFG/mail.env         # SMTP_PASSWORD + from/to; keep it chmod 600
  2) node list:     \$EDITOR $CFG/fleet-nodes.conf  # your roles, ssh-targets, os, methods
  3) test mail:     fleet-mail -s "test" --body "hello from \$(hostname)"
  4) test digest:   fleet-update-check --dry-run    # then drop --dry-run to email it
  5) schedule:      re-run with --with-timer (macOS) or add a systemd timer/cron (Linux)
  6) Gatus health + alerts: separate node-specific deploy — see README.md § Gatus.
EOF
