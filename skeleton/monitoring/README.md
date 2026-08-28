# skeleton/monitoring — fleet health, failure email, and an update digest

Reusable tools + templates that answer two questions without you going to look — *is it still
working?* and *what has fallen behind?* — and tell you by email when the answer is bad. Everything
here is **notify-only**: it surfaces work and raises alarms, it never auto-mutates a running node.

1. **App/infra health checks** — Gatus runs a battery of functional checks (API status + body +
   latency, not just up/down) and **emails you when one fails**.
2. **Local checks a remote prober can't do** — a service with no listening port, a local mount,
   the monitor itself (`fleet-local-check`).
3. **An update digest** — a weekly job inventories what's behind on every node, **by install
   method** — including **pinned container images**, which no package manager can see
   (`fleet-update-check` + `fleet-container-check`). It **upgrades nothing**; you run the
   upgrades deliberately (guide example **E10**).
4. **An install-method audit** — catches one command installed two ways, the trap that makes
   upgrades break confusingly (`fleet-install-audit`).
5. **Failure email** — a standalone SMTP path (e.g. an app password) shared by all of them, so
   alerting still fires when the rest of the stack is down (`fleet-mail`).

The worked narrative is **[`guide/examples/E16-fleet-health-and-alerting.md`](../../guide/examples/E16-fleet-health-and-alerting.md)**. This folder is the parts.

## Files

| File | What |
|---|---|
| `fleet-mail` | dependency-free SMTP mailer; reads `mail.env`; used by the digest + any script alert |
| `fleet-update-check` | the digest; reads `fleet-nodes.conf`; notify-only; local + SSH nodes |
| `fleet-local-check` | local-only probes Gatus can't reach; reads `local-checks.conf`; email on state change |
| `fleet-install-audit` | generalized install-method conflict detector across nodes; email on state change |
| `fleet-container-check` | pinned container images with a newer upstream release (read-only; folded into the digest) |
| `fleet-install-audit.plist.template` | after-install WatchPaths trigger (runs the audit `--local`) |
| `fleet-nodes.conf.template` | your node inventory (`role | ssh-target | os | methods`) |
| `local-checks.conf.template` | typed local checks (`service | mount | http | command`) |
| `fleet-local-check.plist.template` | launchd timer for the local probe (every 15 min) |
| `mail.env.template` | SMTP secret stub for `fleet-mail` (host-local, chmod 600) |
| `gatus-config.yaml.template` | Gatus endpoints (infra + apps) + email alerter |
| `gatus.env.template` | SMTP secret stub for Gatus (root-owned on the Gatus node) |
| `gatus-smtp.dropin.conf` | systemd drop-in so Gatus loads the SMTP env |
| `fleet-update-check.plist.template` | launchd weekly timer (macOS always-on node) |
| `bootstrap-monitoring.sh` | installs the tools + seeds config/secret stubs (+ optional timer) |

## Quick start (the update digest + failure email)

On your **always-on** node (the one that can SSH to the rest of the fleet):

```sh
./bootstrap-monitoring.sh --with-timer          # installs the 5 tools, seeds config, loads the timers
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

## Local checks (what Gatus can't reach)

Gatus checks anything reachable over the network. Some things aren't: a **service with no
listening port** (an outbound bridge/agent), a **local network mount**, the **monitor itself**
(if Gatus is down it can't alert on its own outage), or a check that needs **local DB/CLI
access**. `fleet-local-check` runs on the node that *can* see them, driven by
`local-checks.conf` — typed checks (`service`, `mount`, `http`, `command`). It emails only when
a check **transitions** (a state file dedups), so a 15-minute cadence never spams.

```sh
$EDITOR ~/.config/fleet-monitoring/local-checks.conf   # seeded by bootstrap
fleet-local-check --dry-run                             # preview; drop --dry-run to arm it
```

Two gotchas worth internalizing (both cost real debugging):

- **Enumerate services, not containers.** It's easy to build a monitoring list from
  `docker ps` (or your container UI) and silently miss **native** services — a launchd/systemd
  agent, a gateway daemon. List what's *running*, by role, not what's *containerized*.
- **`mount` checks do NO I/O.** On macOS an NFS/SMB share is bound to the GUI login session, so
  `ls`/`stat` against it **hangs from a launchd/background run even when the mount is healthy** —
  a guaranteed false alarm on a schedule. `fleet-local-check`'s `mount` type reads only the
  kernel mount table (reliable everywhere); for genuine hung-detection, use a `command` check
  through a login shell (`ssh localhost 'ls <path>'`).

## Install-method audit (catch "installed two ways")

The trap that bites over time: one command ends up provided by two package managers — a manual
shim shadowing a brew formula, an npm CLI vs a cask, a `pip` in `/usr/local` over the system one.
Whichever wins the `$PATH` race decides what runs, and upgrades silently break. `fleet-install-audit`
scans every executable in each node's `$PATH` (it reads your `fleet-nodes.conf`, so it grows on its
own) and flags any command backed by **2+ distinct real binaries via user methods** — the real
conflict signal.

It is deliberately **low-noise**: it excludes intentional coexistences — **version managers**
(nvm/pyenv/rbenv/asdf/…), **app-bundled CLIs** (a container tool's own bin dir), and package-manager
keg `libexec` — and dedups multiple symlinks that point at one binary. Benign system-vs-brew
overrides (`python3` in `/usr/bin` and `/opt/homebrew/bin`) are **not** flagged. It also reports
duplicate `$PATH` entries and self-updating (`auto_updates`) casks.

```sh
fleet-install-audit --dry-run     # print; --local audits just this host; drop --dry-run to email
```

Two intended triggers (both wired by bootstrap): **after any install** — the
`fleet-install-audit.plist.template` WatchPaths agent runs it `--local` whenever an install dir
changes (throttled, state-deduped); and **weekly** — `fleet-update-check` folds the audit into its
digest email. On Linux, use a systemd `.path` unit watching your install dirs instead of WatchPaths.

## Container images — the blind spot package managers can't see

`fleet-update-check` covers brew / npm / softwareupdate / apt. Your **self-hosted stack is
containers**, and an image pinned to a version tag (correct for an appliance — you don't want it
moving under you) **never moves on its own and no package manager sees it**. In practice it rots
until somebody happens to notice a "new version available" banner inside the app's own UI. That is
a terrible detection mechanism.

`fleet-container-check` closes it: parse your compose file, find version-pinned images (skipping
`:latest`, which moves at pull time anyway), ask the registry (Docker Hub / ghcr.io) for newer
semver tags, and report. **Read-only — it never pulls and never recreates.** It's folded into the
weekly digest, so stale images arrive in the same email as everything else.

```sh
fleet-container-check                 # or: FLEET_COMPOSE=/path/to/compose.yaml fleet-container-check
```

**Updating a pinned image** — bump the tag, then:

```sh
docker compose pull <svc> && docker compose up -d <svc>
docker compose up -d ts-<svc>     # if a mesh sidecar shares its netns — see below
```

Verify afterwards: the service's own health endpoint, its published URL, **and anything that
consumes it** (an exporter, a dashboard). A **major** bump deserves a look at the image's
entrypoint/env first — a rewrite can silently change the contract; check that dependent dashboard
queries still return data before you call it done.

## Gotcha: a sidecar shares the app's network namespace

If you publish services through a mesh sidecar (`network_mode: service:<app>`), **touching the app
container breaks the sidecar's networking** — the app stays healthy but its published URL goes dark:

| What you did | Fix |
|---|---|
| `docker restart <app>` (id unchanged) | `docker restart ts-<app>` |
| `docker compose up -d <app>` / recreate (**new** id) | `docker compose up -d ts-<app>` — a plain restart fails; it still points at the dead container id |

Sweep your published URLs after any such change; anything returning no response needs its sidecar
restarted or recreated. Better still, **avoid the restart**: dashboard provisioners and config
reload endpoints (e.g. a `POST /-/reload`) usually apply changes without touching the container.

## Subject taxonomy — make the inbox filterable

Alerts are only useful if you can triage them at a glance. Give every sender you control **one
subject shape**:

```
[<YourTag>/<Kind>/<Source>] descriptive text
```

- **Kind** is the *triage* axis — what do I do with this?
  `Alert` (broken, act now) · `Digest` (scheduled summary) · `Report` (a job finished, FYI)
- **Source** is the subsystem — `Health`, `Installs`, `Updates`, or an app name.

**Keep Kind and Source in separate slots.** "What kind of message" and "what it's about" are
different axes; collapsing them into one (`Alert` next to `Plex` in the same position) makes every
filter ambiguous. As a bonus, alphabetical sort puts `Alert` above `Digest`/`Report` — the order you
want to read them in.

Set your tag once; the tools read `FLEET_SUBJECT_PREFIX` (default `[Fleet`):

```sh
export FLEET_SUBJECT_PREFIX='[MyFleet'      # in the timer's env, or leave the default
```

**Expect your health-check tool to ignore all this.** Gatus, for example, **hardcodes its subject**
(`[<group>/<name>] Alert triggered` / `... Alert resolved`) with no prefix setting — the only lever
is what you name the group and endpoint. Don't contort the tool's UI to force cosmetic consistency:
its subjects are already a usable `[area/endpoint]` hierarchy. Just write **two** filter rules
instead of one — one matching your prefix, one matching the health checker's fixed phrasing — and
confirm both with real test emails before you rely on them.

## Coverage probes — for batch work, count the artifact

The probes above answer *"is it working right now?"*. Long-running batch work needs a different
question: *"how much of it is actually done?"* — and the naive version of that check is the most
dangerous probe you can write. See guide **§ 14 (Liveness is not completion)** for the full case.

The failure: a watcher that tests whether the job's process is running, and reports success when it
exits. A process exits on success, on failure, on being killed, and when it had nothing queued —
the exit distinguishes none of them. Worse, it may not even be the process doing the work. One such
probe reported "generation complete" for weeks at **0.15%** actual coverage.

Write these instead as **coverage probes**:

- **Count the artifact**, not the process — the rows, files, or records the work actually produces.
  If you can't name the artifact, you can't write the probe.
- **Report `done / total` as a percentage.** A percentage cannot silently mean zero the way a
  boolean can. `complete: true` is a claim; `41,802 of 71,623 (58.4%)` is a measurement.
- **Two phases, so it stays useful after the backlog clears.** While below target, report milestones
  and treat *no progress for N hours* as the terminal signal (a multi-week sweep has no clean end
  event, and this one alert covers both "finished" and "died early" — the percentage says which).
  At or above target, go silent: a plateau is correct. The lasting signal is then **regression** —
  coverage falling and staying down past a grace window, meaning newly added work has stopped being
  processed. The grace window is what keeps normal add-then-catch-up quiet.
- **Give it a no-side-effect mode** (`--print`) that computes and prints without mailing or writing
  state, so you can check on demand without perturbing the alerting.
- **Never assert what you don't measure.** If the probe reports on two artifacts, count both. A
  half-true alert is worse than a false one: the verifiable half makes the fabricated half credible.

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
