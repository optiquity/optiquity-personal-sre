# E16 · Fleet health, alerting, and the update digest

**Section E — fleet operations.** Back to the [catalog](../15-example-projects.md).

**What this shows:** giving your operator **eyes and a voice** — a battery of functional health
checks across the fleet (with Gatus), a **weekly digest of what's behind** on every node, and
**email when something fails** — all **notify-only**: it surfaces work and raises alarms, it
never auto-mutates a running node. The tools + templates are in
[`skeleton/monitoring/`](../../skeleton/monitoring/).

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

---

## The scenario

You have services and nodes doing real work. Two blind spots hurt:

1. **"Is it actually working?"** — a node answering `ping` tells you nothing about whether its
   app still serves requests. You want *functional* checks: the API returns 200 **with the
   expected body**, the page renders, the response is timely.
2. **"What's fallen behind?"** — packages and tools drift out of date, but auto-updating
   everything is how an always-on node breaks mid-task. You want to *know* what's behind and
   decide, not be surprised.

And when either goes wrong, you want to **find out by email**, not by stumbling on it.

## Why do it "the framework way"

- **Notify-only, always.** The digest upgrades nothing (governance Rule 7 / § 07 — a node's
  tooling changes when *you* decide). Health checks observe; they never restart or "fix." The
  operator's job here is to *surface*, yours is to *act*.
- **Alerting independent of the stack.** Email goes out over a standalone SMTP credential, not
  through your automation platform — because an alert must still fire when the very thing it's
  warning about is down.
- **Reads are free.** Inventory and health probes are read-only (Rule 10), so this whole layer
  runs unattended without tripping the permission model.
- **Roles, not hostnames.** Everything is driven by a node inventory of *roles* (always-on,
  laptop, gateway, NAS, …), so it's your fleet's shape, not anyone's specific machines.

## The shape

### 1. Health checks — Gatus (functional, with alerts)

[Gatus](https://github.com/TwiN/gatus) is a tiny Go health-check dashboard: it periodically hits
each endpoint and asserts **conditions**, alerting when they fail. Run it native on a small
always-reachable node — your **gateway** is ideal (it's up whenever the network is, and can see
the fleet independently; see [E12 · dedicated mesh gateway](E12-dedicated-mesh-gateway.md)).

Conditions verify *function*, not just reachability — that's what catches "up but broken":

```yaml
- name: Automation platform
  url: "https://<service-host>/healthz"
  conditions:
    - "[STATUS] == 200"
    - "[BODY].status == ok"        # the API actually answered correctly
    - "[RESPONSE_TIME] < 3000"     # …and in time
  alerts: [{type: email}]
```

Start from [`skeleton/monitoring/gatus-config.yaml.template`](../../skeleton/monitoring/gatus-config.yaml.template):
a group of infra reachability checks (TCP/DNS) plus one functional check per self-hosted app.
The email alerter reads its credential from the environment (`${SMTP_USERNAME}` /
`${SMTP_PASSWORD}`) via a service drop-in — never from the versioned config.

> **Prove the alert fires.** Add a throwaway endpoint that fails immediately
> (`tcp://127.0.0.1:1`, `failure-threshold: 1`), confirm the email arrives, then remove it. A
> config full of green endpoints proves the *checks* work, not the *alerting*.

### 2. The update digest — inventory by email (notify-only)

A scheduled job reads a node inventory and, per node × install method, lists what's behind — then
emails you an actionable digest. It is the automation of the E10 inventory step; it upgrades
nothing.

```
# ~/.config/fleet-monitoring/fleet-nodes.conf
# role | ssh-target | os | methods
always-on | local          | macos    | brew,npm,softwareupdate
laptop    | <laptop-host>  | macos    | brew,npm,softwareupdate
gateway   | <gateway-host> | linux    | apt
windows   | <win-host>     | windows  | manual        # winget needs an interactive session
nas       | <nas-host>     | synology | manual        # updates go through the NAS UI
```

`fleet-update-check` runs on your **always-on** node, checks it locally and the others over SSH
(key auth), and emails when there's something to do (or a check errored). Schedule it weekly with
the launchd timer (macOS) or a systemd timer/cron (Linux). "manual" nodes get an OS-specific
reminder rather than a silent gap.

### 3. Failure email — one standalone credential

Both pieces send through the same **host-local SMTP credential** (e.g. a Gmail *app password*):
Gatus's native email alerter for endpoint failures, and the `fleet-mail` helper for the digest
and any script-level failure (`some_job || fleet-mail -s "job failed" --body "…"`). The secret
lives only in a `chmod 600` env file on each sending node and is **never committed** (§ 06).

## Bootstrap

On the always-on node:

```sh
skeleton/monitoring/bootstrap-monitoring.sh --with-timer
$EDITOR ~/.config/fleet-monitoring/mail.env          # SMTP_PASSWORD + from/to
$EDITOR ~/.config/fleet-monitoring/fleet-nodes.conf  # your fleet
fleet-mail -s "test" --body "hello"                  # confirm mail
fleet-update-check --dry-run                         # preview the digest
```

Deploy Gatus on the gateway per [`skeleton/monitoring/README.md`](../../skeleton/monitoring/README.md) § Gatus.

## What you end up with

- A health page that goes **red and emails you** the moment an app stops answering correctly.
- A **weekly digest** of exactly what's behind on each node, with nothing changed behind your back.
- One credential, kept out of git, that makes both speak up — even when the stack is down.

## Related

- [E10 · a deliberate fleet-update pass](E10-fleet-update-pass.md) — the runbook the digest feeds.
- [E12 · dedicated mesh gateway](E12-dedicated-mesh-gateway.md) — where Gatus lives.
- [E13 · fleet metrics stack](E13-fleet-metrics-stack.md) — metrics/history (Prometheus/Grafana);
  Gatus is the up/down + alerting complement, not a replacement.
- Governance [§ 03](../03-governance-rules.md) (Rules 7/10) · secrets [§ 06](../06-secrets.md).
