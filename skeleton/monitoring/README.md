# skeleton/monitoring — fleet health, failure email, and an update digest

Reusable tools + templates to give your operator three things, all **notify-only** (they surface
work and raise alarms; they never auto-mutate a running node):

1. **App/infra health checks** — Gatus runs a battery of functional checks (API status + body +
   latency, not just up/down) and **emails you when one fails**.
2. **An update digest** — a weekly job inventories what's behind on every node (by install
   method) and emails an actionable list. It **upgrades nothing** — you run the upgrades
   deliberately (guide example **E10**).
3. **Failure email** — a standalone SMTP path (e.g. a Gmail app password) shared by both, so
   alerting still fires when the rest of the stack is down.

The worked narrative is **[`guide/examples/E16-fleet-health-and-alerting.md`](../../guide/examples/E16-fleet-health-and-alerting.md)**. This folder is the parts.

## Files

| File | What |
|---|---|
| `fleet-mail` | dependency-free SMTP mailer; reads `mail.env`; used by the digest + any script alert |
| `fleet-update-check` | the digest; reads `fleet-nodes.conf`; notify-only; local + SSH nodes |
| `fleet-nodes.conf.template` | your node inventory (`role | ssh-target | os | methods`) |
| `mail.env.template` | SMTP secret stub for `fleet-mail` (host-local, chmod 600) |
| `gatus-config.yaml.template` | Gatus endpoints (infra + apps) + email alerter |
| `gatus.env.template` | SMTP secret stub for Gatus (root-owned on the Gatus node) |
| `gatus-smtp.dropin.conf` | systemd drop-in so Gatus loads the SMTP env |
| `fleet-update-check.plist.template` | launchd weekly timer (macOS always-on node) |
| `bootstrap-monitoring.sh` | installs the tools + seeds config/secret stubs (+ optional timer) |

## Quick start (the update digest + failure email)

On your **always-on** node (the one that can SSH to the rest of the fleet):

```sh
./bootstrap-monitoring.sh --with-timer          # installs tools, seeds config, schedules weekly
$EDITOR ~/.config/fleet-monitoring/mail.env         # SMTP_PASSWORD + from/to (chmod 600)
$EDITOR ~/.config/fleet-monitoring/fleet-nodes.conf # your nodes
fleet-mail -s "test" --body "hello"                 # confirm mail works
fleet-update-check --dry-run                        # preview; drop --dry-run to email
```

Remote nodes are reached over SSH (key auth, `BatchMode`); the launchd context inherits your
SSH keys, so the scheduled run reaches them the same way. Unreachable nodes are noted, not fatal.

## Gatus (health checks + alerts)

Gatus usually runs on a small always-reachable node (a **gateway/Pi**) so it can see the fleet
independently. Native install (a single Go binary + `config.yaml`), then:

```sh
# 1. config (fill every <placeholder>; conditions verify function, not just reachability)
sudo install -m 644 gatus-config.yaml.template /etc/gatus/config.yaml   # then edit

# 2. SMTP secret (root-owned; systemd reads it at unit load, so the service user needn't)
sudo install -m 600 gatus.env.template /etc/gatus/gatus.env             # then fill SMTP_PASSWORD

# 3. let the service see the credential env, then reload
sudo mkdir -p /etc/systemd/system/gatus.service.d
sudo install -m 644 gatus-smtp.dropin.conf /etc/systemd/system/gatus.service.d/10-smtp-env.conf
sudo systemctl daemon-reload && sudo systemctl restart gatus
```

**Test the alert path** before trusting it: add a throwaway endpoint that fails immediately
(`url: "tcp://127.0.0.1:1"`, `conditions: ["[CONNECTED] == true"]`, `failure-threshold: 1`),
confirm the email lands, then remove it. Pointing the config at a service that's up is not proof
the *alert* works — only an induced failure is.

## Secrets & privacy

Both `.env` files are **host-local secrets** — `chmod 600`, never committed (guide § 06). Version
the *config* (`config.yaml`, `fleet-nodes.conf`) in your private repo if you like; keep the
credentials out. The from/to addresses are not secret (they live in `config.yaml`); only the
password is.

## Why notify-only

Auto-updating a running node trades a little convenience for the risk of a surprise breakage
mid-task on your always-on host. So the digest *surfaces* the work and you apply it deliberately,
per node, with verification — see **E10** and guide **§ 07 (Tools & requirements)**. Self-updating
apps (ones with their own updaters) should be listed nowhere and left alone.
