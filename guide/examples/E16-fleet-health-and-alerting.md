# E16 · Fleet health, alerting, and the update digest

**Section E — fleet operations.** Back to the [catalog](../17-example-projects.md).

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

- **Notify-only, always.** The digest upgrades nothing — upgrading a running node is a *material
  action*, so it needs a human (governance [Rule 1](../03-governance-rules.md) / [§ 07](../07-tools-requirements.md) — a node's
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

### 4. Local checks — the things a remote prober can't reach

Gatus sees anything on the network. Some things aren't: a **service with no listening port** (an
outbound bridge), a **local mount**, the **monitor itself**, or a check needing **local DB/CLI**
access. `fleet-local-check` runs on the node that can see them, driven by typed checks
(`service | mount | http | command`), and emails only on **state transitions** (a state file
dedups) so a 15-minute cadence never spams.

```
# ~/.config/fleet-monitoring/local-checks.conf
service | bridge daemon    | com.example.some-bridge     # no port → Gatus can't see it
mount   | media share      | /path/to/your/mount         # local NFS/SMB
http    | gatus cross-ping | https://<gatus-host>/        # catch the monitor's own outage
command | workflows active | test "$(…count active…)" -ge 1   # escape hatch for anything
```

**Two lessons this encodes (both cost real debugging):**

- **Enumerate services, not containers.** Building the health list from `docker ps` silently
  drops **native** services (a launchd/systemd agent, a gateway daemon that isn't containerised).
  List what's *running by role*, not what's *containerised* — the thing you forget is exactly the
  thing with no obvious dashboard.
- **A `mount` check must do no I/O.** On macOS an NFS/SMB share is bound to the GUI login
  session, so `ls`/`stat` against it **hangs from a launchd/background run even when the mount is
  healthy** — a guaranteed false alarm on a timer. Check the **kernel mount table** (`ismount` /
  `mount`), not the filesystem; for real hung-detection, go through a login shell
  (`ssh localhost 'ls <path>'`) as a `command` check.

### 5. Install-method audit — catch "installed two ways"

Over time a command ends up provided by two package managers — a manual shim shadowing a brew
formula, an npm CLI vs a cask, a `pip` in `/usr/local` over the system one. Whichever wins the
`$PATH` race decides what runs; upgrades then break in confusing ways. `fleet-install-audit` scans
every `$PATH` executable per node (reads your `fleet-nodes.conf`, so it grows on its own) and flags
any command backed by **2+ distinct real binaries via user methods** (brew / npm / pipx / manual).

The whole trick is being **low-noise**: exclude intentional coexistences — **version managers**
(nvm/pyenv/…), **app-bundled CLIs**, package-manager keg `libexec` — and dedup symlinks that point
at one binary. A blunt "flag every command in 2+ dirs" drowns you in `python3`-style overrides;
this rule surfaces only real duplicate installs.

Two triggers: **after any install** (a launchd WatchPaths agent — or a Linux systemd `.path` unit —
runs it `--local`, throttled, state-deduped) and **weekly** (folded into the `fleet-update-check`
digest). It's the guard that keeps the "one install method per tool" discipline (§ 07) honest as
the fleet grows.

### 6. Container images — the update path no package manager can see

The digest covers brew / npm / apt. But a self-hosted stack is **containers**, and an image pinned
to a version tag — which is the *right* call for an appliance — **never moves on its own and no
package manager sees it**. It quietly rots until someone happens to open the app and notice a "new
version available" banner. Discovering updates by luck is not a strategy.

`fleet-container-check` reads your compose file, finds version-pinned images (skipping `:latest`,
which moves at pull time), asks the registry for newer semver, and reports — **read-only, it never
pulls**. Folded into the weekly digest, so a stale image lands in the same email as everything else.

Updating one is a small, gated ritual, and the verification is the important half:

```sh
# bump the tag in compose.yaml, then
docker compose pull <svc> && docker compose up -d <svc>
docker compose up -d ts-<svc>        # sidecar shares the netns — see the gotcha below
```

- Verify the service's **own health endpoint**, its **published URL**, and **whatever consumes it**
  (an exporter, a dashboard). "The container started" is not "it works".
- On a **major** bump, check the image's entrypoint/env before trusting it — a rewrite can change
  the contract silently. (One exporter went from a Python image to a Go binary across a major; the
  env contract happened to hold, but that was verified by confirming every dependent dashboard
  query still returned data, not assumed.)

**The sidecar gotcha** (bites anyone using the `network_mode: service:<app>` publishing pattern):
touching the app container breaks the sidecar's networking — the app stays healthy while its
published URL goes dark. `restart` the app → restart the sidecar; **recreate** the app (new
container id) → **recreate** the sidecar, since a plain restart still points at the dead id. Sweep
your published URLs after any such change. Better: avoid the restart entirely — dashboard
provisioners and config-reload endpoints usually apply changes without touching the container.

### 7. Make the inbox filterable — one subject shape

Alerts you can't triage at a glance become noise you archive unread. Give every sender **you
control** one shape — `[<YourTag>/<Kind>/<Source>] text` — where **Kind** is the *triage* axis
(`Alert` / `Digest` / `Report`) and **Source** is the subsystem. Keep them as **separate slots**:
"what kind of message" and "what it's about" are different axes, and merging them makes filters
ambiguous. Alphabetical sort then lists `Alert` above `Digest`/`Report`, which is the reading order
you want.

```
[MyFleet/Alert/Health]    2 failing — media mount, bridge daemon
[MyFleet/Digest/Updates]  updates available + container images (2026-01-05 09:00)
[MyFleet/Report/Health]   all checks recovered
```

**Your health checker probably won't cooperate — that's fine.** Gatus hardcodes its subject
(`[<group>/<name>] Alert triggered|resolved`); there's no prefix setting. Renaming its groups to
force the prefix would pollute its dashboard to fix an email cosmetic. Better: accept its native
format (already a clean `[area/endpoint]` hierarchy) and write **two** filter rules — one for your
prefix, one for the checker's fixed phrasing. **Verify both with real test emails**; a filter you
assumed works is a filter that silently drops alerts.

### 8. Coverage probes — the check that lies most convincingly

Everything above answers *"is it working now?"*. A long backlog needs *"how much is actually done?"*,
and the naive version of that check is the most dangerous thing in this chapter.

**The failure.** A watcher reported a multi-week media-analysis job **complete**. It had checked
whether the relevant tool was running and declared success when the process exited. Actual
coverage: **0.15%**. The tool it watched never performed that work at all — the analysis came from
a different subsystem on a different trigger. It had been reporting success for weeks, and surfaced
only when a human used the system and hit the missing result.

**Worse, the same alert claimed two things and one was true.** It also reported thumbnail
generation complete — and thumbnails genuinely *were* at 99%. The verifiable half made the
fabricated half credible; nobody questions a message that's half right. **If a probe reports on two
artifacts, count both, or claim only the one you count.**

So for anything batch:

```
count the artifact the work produces   →  rows, files, records — not the process
report done/total as a percentage      →  a boolean can silently mean zero; a percentage can't
two phases:
  below target  →  milestones, plus "no progress for N hours" as the terminal signal
  at target     →  silent (a plateau is correct), alert only on sustained regression
--print mode    →  compute and report, mutate nothing
```

That "no progress for N hours" is not a nicety — a multi-week sweep has **no clean end event**, so
absence of progress is the only honest completion signal. Report the number beside it and the same
alert covers both "finished" and "died at 12%", with neither able to impersonate the other.

**Then check what's actually capping it.** Two things distorted every estimate in that case:

- **The maintenance window.** The sweep wasn't running continuously — the platform killed it at the
  window's end hour nightly. Four hours a day instead of twenty-four is the difference between ~11
  days and ~2 months, and nothing announced it. Completion timestamps clustered at a wall-clock
  hour are the tell. See § 14 for the pattern, including why a *manual* trigger often escapes the
  window's start but not its end — and why the daily nudge that exploits that should
  **retire itself** once the backlog clears.
- **The remote store, not the local box.** The client sat at 3.6% CPU and 32% of its link, which
  read as idle capacity begging for more concurrency. The NAS said otherwise: 42% I/O wait, 278 ms
  read latency. More readers on a saturated array multiplies seeks and *reduces* throughput. See
  § 08 for isolating which layer is actually binding before you tune anything.

**Both bugs found in this section were found by testing, not review.** The state-file handling had
a path where corrupt input killed the probe mid-run *while still exiting 0* — the same silent
success it was written to eliminate, one layer down. Exercise every branch of a probe against
synthetic inputs, and make its state path overridable so you can.

## Bootstrap

On the always-on node:

```sh
skeleton/monitoring/bootstrap-monitoring.sh --with-timer
$EDITOR ~/.config/fleet-monitoring/mail.env           # SMTP_PASSWORD + from/to
$EDITOR ~/.config/fleet-monitoring/fleet-nodes.conf   # your fleet (the digest)
$EDITOR ~/.config/fleet-monitoring/local-checks.conf  # your local-only checks
fleet-mail -s "test" --body "hello"                   # confirm mail
fleet-update-check --dry-run                          # preview the digest (folds in the audit)
fleet-local-check  --dry-run                          # preview the local probes
fleet-install-audit --dry-run                         # preview the install-method audit
fleet-container-check                                 # preview pinned-image updates
```

Deploy Gatus on the gateway per [`skeleton/monitoring/README.md`](../../skeleton/monitoring/README.md) § Gatus.

## What you end up with

- A health page that goes **red and emails you** the moment an app stops answering correctly.
- A **weekly digest** of exactly what's behind on each node, with nothing changed behind your back.
- One credential, kept out of git, that makes both speak up — even when the stack is down.

## Adapt it

- **One machine?** Still worth it — the local checks and the update digest need no fleet, and the
  alert path is the same. Skip the SSH node list; keep `local` in it.
- **Already running Prometheus + Grafana ([E13](E13-fleet-metrics-stack.md))?** You could alert
  from Alertmanager instead. The deliberate argument for a *separate*, out-of-band checker: it
  keeps working when the metrics stack is the thing that broke, and it needs no query language to
  answer "is it up".
- **Don't want mail?** The shape is unchanged — swap the mailer for whatever you actually read
  (push, chat webhook). Keep it **out-of-band** from the stack it watches.
- **Nervous about noise?** Start with `Alert` only: health checks and nothing else. Add the
  weekly digest once you trust it, and keep state-dedup on so recoveries don't double-notify.
- **Track it as a project.** Give it a registry row and a plan doc like any other work
  ([04 · Structure](../04-structure.md)) — including which checks you deliberately *don't* alert
  on, which is the kind of decision that's invisible six months later.

## Related

- [E10 · a deliberate fleet-update pass](E10-fleet-update-pass.md) — the runbook the digest feeds.
- [E12 · dedicated mesh gateway](E12-dedicated-mesh-gateway.md) — where Gatus lives.
- [E13 · fleet metrics stack](E13-fleet-metrics-stack.md) — metrics/history (Prometheus/Grafana);
  Gatus is the up/down + alerting complement, not a replacement.
- [09 · Permissions](../09-permissions.md) — why unattended, read-only probes are safe.
- [13 · Multi-node](../13-multinode.md) — the dashboard is state-of-record; this is live health.
- [15 · Setup](../15-setup.md) — where standing this up belongs in the onboarding path.
- Governance [§ 03](../03-governance-rules.md) (Rule 1 = material actions need you; Rule 10 =
  reads are free) · secrets [§ 06](../06-secrets.md) (the daemon-read credential recipe).
