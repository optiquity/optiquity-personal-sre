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
| `fleet-update-check` | the digest; reads `fleet-nodes.conf`; notify-only; local + SSH nodes. Also **reconciles** declared install methods against what is actually installed, and reports anything present-but-undeclared — a hand-maintained list only ever contains what someone remembered to add |
| `fleet-local-check` | local-only probes Gatus can't reach; reads `local-checks.conf`; email on state change |
| `fleet-install-audit` | generalized install-method conflict detector across nodes; email on state change |
| `fleet-container-check` | pinned container images with a newer upstream release (read-only; folded into the digest) |
| `fleet-install-audit.plist.template` | after-install WatchPaths trigger (runs the audit `--local`) |
| `fleet-binaries.conf.template` | hand-placed binaries registry (reconciled against discovery; `upstream` rows version-checked) |
| `fleet-update-decisions.conf.template` | update decisions with a reason and a revisit date |
| `fleet-composes.conf.template` | the compose stacks to check for image updates (reconciled against discovery) |
| `fleet-nodes.conf.template` | your node inventory (`role | ssh-target | os | methods`) |
| `local-checks.conf.template` | typed local checks (`service`, `mount`, `http`, `command`, `hash`, `synclag`) |
| `fleet-local-check.plist.template` | launchd timer for the local probe (every 15 min) |
| `mail.env.template` | SMTP secret stub for `fleet-mail` (host-local, chmod 600) |
| `gatus-mail-relay` + `.service` | sends Gatus alerts through `fleet-mail` (your subject format); localhost only, hardened unit |
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
fleet-mail --kind Report --source Test --text "hello" --body "it works"   # confirm mail works
fleet-update-check --dry-run                        # preview; drop --dry-run to email
```

Remote nodes are reached over SSH (key auth, `BatchMode`); the launchd context inherits your
SSH keys, so the scheduled run reaches them the same way. Unreachable nodes are noted and
skipped, not an error: a laptop asleep is normal.

The digest answers two questions. The weak one is *"is anything I check out of date?"*. The one
that matters is *"what is installed that **nothing** checks?"*
- **Coverage.** Declared methods are reconciled against what is actually installed:
  - **UNDECLARED:** installed, but nothing checks it.
  - **NO CHECKER:** declared, but the tool has no code for it. It is never reported as
    "current".
  - **GAP (`?name`):** a known gap.
  - **NOT AUDITED:** nobody has looked.
  - **Excluded (`!name`):** stays counted.
- **Hand-placed binaries** (`fleet-binaries.conf`): executables no package manager owns are
  discovered and reconciled against the registry, and `upstream` ones are version-checked against
  GitHub. An unregistered one is reported, and so is a registered one that's gone.
- **Decisions** (`fleet-update-decisions.conf`): what you decided not to take, and why. One whose
  revisit date has passed is flagged again.
- **Windows:** declare `winget`. Detection works over SSH, from the cached index.

A malformed row in any of these files is reported, never skipped.

## Gatus (health checks + alerts)

Gatus usually runs on a small always-reachable node (a **gateway/Pi**) so it can see the fleet
independently. Native install (a single Go binary + `config.yaml`).

**Its alerts go through `gatus-mail-relay`**, so they carry your subject format like every other
fleet email. Gatus hard-codes its own subject (v5.36: `<group>/<name>: Alert triggered`), so its
`custom` provider POSTs each alert to the relay on the same host (127.0.0.1 only). The relay builds
the subject with `fleet-mail` and sends it:
`[Fleet/Alert/Apps/api] api: triggered`. The endpoint name is repeated after the bracket because a
mail client may group conversations while ignoring a leading `[tag]`.

```sh
# 0. directories
sudo install -d -m 755 /etc/gatus /usr/local/lib/fleet-monitoring

# 1. the relay + the fleet-mail it imports (the same file your other nodes run)
sudo install -m 755 gatus-mail-relay fleet-mail /usr/local/lib/fleet-monitoring/

# 2. SMTP secret (root:600; systemd hands it to the relay read-only — no copy, no user access)
sudo install -m 600 gatus.env.template /etc/gatus/gatus.env             # then fill every line

# 3. prove the relay, then start it BEFORE Gatus points at it (the reverse is a window of lost alerts)
RELAY_FLEET_MAIL=/usr/local/lib/fleet-monitoring/fleet-mail \
  python3 /usr/local/lib/fleet-monitoring/gatus-mail-relay --self-test    # must be ALL PASS; sends nothing
sudo install -m 644 gatus-mail-relay.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now gatus-mail-relay
curl -s http://127.0.0.1:8099/health                                      # "ok 0 sent, 0 failed, 0 rejected"

# 4. config (fill every <placeholder>; conditions verify function, not just reachability)
sudo install -m 644 gatus-config.yaml.template /etc/gatus/config.yaml   # then edit
sudo systemctl restart gatus
```

Prefer Gatus's own email provider (its fixed subject; add a second mail filter)? Use the commented
`email:` block in the template instead, and give *Gatus* the credential with the drop-in:
`sudo install -m 644 gatus-smtp.dropin.conf /etc/systemd/system/gatus.service.d/10-smtp-env.conf`.

**Watch the relay from another node.** It is now a single point for every health-check email, and a
dead relay cannot report its own death. From your always-on node, through *its* mail path, add to
`local-checks.conf` (a `command` exiting 3 is UNKNOWN, so an unreadable journal never passes as clean):

```
command | gatus relay up     | ssh <gatus-host> 'systemctl is-active --quiet gatus-mail-relay && curl -sf http://127.0.0.1:8099/health >/dev/null'
command | gatus alerts sent  | ssh <gatus-host> 'J=$(sudo -n journalctl -u gatus --since -20min --no-pager) || exit 3; ! printf %s "$J" | grep -q "Failed to send an alert"'
```

And because the relay's two files were installed **by hand**, compare them with your repo copies
after every change to `fleet-mail`. A fix that reaches every other node through the config manager
never reaches this one on its own.

Gatus needs a `gatus.service` unit, which a bare binary does not bring with it. If you have none,
this minimal one (hardened; fine with the template's in-memory storage) goes at
`/etc/systemd/system/gatus.service`, run as a dedicated system user
(`sudo useradd --system --no-create-home --shell /usr/sbin/nologin gatus`):

```ini
[Unit]
Description=Gatus health checks
After=network-online.target
Wants=network-online.target

[Service]
User=gatus
Group=gatus
Environment=GATUS_CONFIG_PATH=/etc/gatus/config.yaml
ExecStart=/usr/local/bin/gatus
Restart=on-failure
RestartSec=10
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

Then `sudo systemctl daemon-reload && sudo systemctl enable --now gatus`. If you switch Gatus to disk
storage, `ProtectSystem=strict` makes its data path read-only: add a `StateDirectory=`.

**Test the alert path** before trusting it: add a throwaway endpoint that fails immediately
(`url: "tcp://127.0.0.1:1"`, `conditions: ["[CONNECTED] == true"]`, `failure-threshold: 1`),
confirm the email lands, then remove it. Pointing the config at a service that's up is not proof
the *alert* works — only an induced failure is.

## Local checks (what Gatus can't reach)

Gatus checks anything reachable over the network. Some things aren't: a **service with no
listening port** (an outbound bridge/agent), a **local network mount**, the **monitor itself**
(if Gatus is down it can't alert on its own outage), or a check that needs **local DB/CLI
access**. `fleet-local-check` runs on the node that *can* see them, driven by
`local-checks.conf` — typed checks (`service`, `mount`, `http`, `command`, `hash`, `synclag`). It
emails when a check **transitions** or fails on its first run (a state file dedups), so a 15-minute
cadence never spams.

Every check has **three outcomes**: OK, FAIL, or **UNKNOWN**, when the probe itself could not
answer (a timeout, an unreadable mount table, a `command` exiting 3). An unknown keeps the previous
state and sends no mail. Four in a row become a failure that says *"could not determine state for 4
consecutive runs"*, because an hour of blindness is itself an outage. A config line that doesn't
parse is reported as a failing check, never skipped.

```sh
$EDITOR ~/.config/fleet-monitoring/local-checks.conf   # seeded by bootstrap
fleet-local-check --dry-run                             # preview; drop --dry-run to arm it
```

Two gotchas worth internalizing (both cost real debugging):

- **Enumerate services, not containers.** It's easy to build a monitoring list from
  `docker ps` (or your container UI) and silently miss **native** services — a launchd/systemd
  agent, a gateway daemon. List what's *running*, by role, not what's *containerized*.
- **`mount` checks avoid reading the share, but they are not free of I/O.** On macOS an NFS/SMB
  share is bound to the GUI login session, so `ls`/`stat` *inside* it **hangs from a
  launchd/background run even when the mount is healthy**, a guaranteed false alarm on a schedule.
  `fleet-local-check`'s `mount` type therefore checks the mount point and the mount table instead.
  ⚠ Both still touch the network. `os.path.ismount()` stats the mount point, and an unreachable
  server reads as "not a mount point". Reading the mount table can block on an unresponsive server.
  So the probe retries, and a table it cannot read is **UNKNOWN**, not "unmounted" (guide § 17,
  "A probe that could not answer has not told you anything"). For genuine hung-detection, use a
  `command` check through a login shell (`ssh localhost 'ls <path>'`).
- **Watch what your config manager doesn't deploy.** A script installed by hand, on a node it
  doesn't manage, falls behind the repo silently; `hash` compares it with the repo copy. And
  `synclag` checks that sync is actually happening, since a status command that never fetches reports
  "clean" while days behind.

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

Two intended triggers (on macOS both are wired by `bootstrap-monitoring.sh --with-timer`; on Linux
it prints what to set up, since no systemd units ship): **after any install** — the
`fleet-install-audit.plist.template` WatchPaths agent runs it `--local` whenever an install dir
changes (throttled, state-deduped); and **weekly** — `fleet-update-check` folds the audit into its
digest email. On Linux, use a systemd `.path` unit watching your install dirs instead of WatchPaths.

## Container images — the blind spot package managers can't see

`fleet-update-check` covers brew / npm / softwareupdate / apt. Your **self-hosted stack is
containers**, and an image pinned to a version tag (correct for an appliance — you don't want it
moving under you) **never moves on its own and no package manager sees it**. In practice it rots
until somebody happens to notice a "new version available" banner inside the app's own UI. That is
a terrible detection mechanism.

`fleet-container-check` closes it. It reads every stack registered in `fleet-composes.conf`, finds
the version-pinned images, asks the registry for newer tags, and reports. **Read-only: it never
pulls and never recreates.** It's folded into the weekly digest.

- **Every stack is seen.** Discovery (`~/*/compose.yaml`, `~/*/docker-compose.yml`) reports any stack
  that exists but isn't registered. Forgetting to register a stack is a finding, not silence.
- **Variant-aware.** `5.13-apache`, `2.10-alpine` and `mysql-v2.19.0` are compared only with tags of
  the same variant: `-fpm` is a different image, not a newer one.
- **Floating tags aren't stale.** `3.14-alpine` *is* today's 3.14.x, so it is not reported as behind
  `3.14.7-alpine`. A real bump (`2.10 → 2.11`) still is.
- **Intentional pins.** A `# pin: <reason>` comment above an `image:` line keeps the image listed (with
  the newest version) but not counted as an update. A digest that nags about a version you
  declined gets filtered to trash.
- **Any registry.** Docker Hub, plus any OCI registry through the standard anonymous-token flow:
  ghcr.io, quay.io, lscr.io, or your own.
- **A failed check is an error, not "current".** It exits 2, and the digest reports it.

```sh
fleet-container-check                      # every registered stack
fleet-container-check --compose ./compose.yaml   # just one file
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
| **Nothing — the app restarted by itself** (a crash and its restart policy, or a boot where the sidecar joined first) | Recreate the sidecar. ⚠ This is the dangerous row: no human action to remember, and the sidecar keeps "running" in an empty namespace. In one fleet it stayed dark for four days; only an endpoint check noticed. **Monitor the published URL, not the container state.** |

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

Set your tag once: `SUBJECT_TAG=MyFleet` in `mail.env`, or `FLEET_SUBJECT_TAG=MyFleet` in the timer's
environment. The default is `Fleet`. The older documented `FLEET_SUBJECT_PREFIX='[MyFleet'` form is
accepted too.

**Only `fleet-mail` builds subjects.** The tools pass the parts, and `fleet-mail` assembles them:

```sh
fleet-mail --dry-run --kind Alert --source Health --text "2 failing — backup, mount"
# [Fleet/Alert/Health] 2 failing — backup, mount
```

A pre-built `--subject` that is not in the shape is **refused** (exit 2), never sent. Your own scripts
should call `fleet-mail` the same way, so every message you send lands under your filters.

**Tests.** `python3 tests/test_tools.py` runs every tool for real in a throwaway `$HOME`, with a fake
mailer that records what would have been sent. That exercises the **send path**, which `--dry-run`
never reaches. See guide § 17, "Syntax-checked is not correct".

**Expect your health-check tool to ignore all this.** Gatus, for example (checked on v5.36),
**hardcodes its subject** as `<group>/<name>: Alert triggered` / `…: Alert resolved`: no brackets and
no setting to change it. Either route its alerts through a small localhost relay (its `custom`
provider POSTs each alert to a URL) that builds the subject with `fleet-mail`, or accept its phrasing
and add a second filter rule. **Confirm with real test emails in the client you read.** A client may
group different alerts into one conversation if they differ only inside the leading `[tag]`, so make
the text after the tag name the source. See guide E16 §7.

## Coverage probes — for batch work, count the artifact

The probes above answer *"is it working right now?"*. Long-running batch work needs a different
question: *"how much of it is actually done?"* — and the naive version of that check is the most
dangerous probe you can write. See guide **§ 17 (Liveness is not completion)** for the full case.

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

## If you automate around a maintenance window, make the job retire itself

Platform background work (reindex, analysis, compaction) usually runs inside a **maintenance
window**, which caps its runtime — a backlog needing 240 hours finishes in ten days if run
continuously and **two months** in a four-hour nightly window. See guide **§ 17 (Background work
has a window)** for how to spot it; a manual trigger often bypasses the window's *start* but not
its *end*, which is what makes one daily nudge effective.

That nudge is **scaffolding for a one-off backlog, not a permanent fixture.** Once the backlog
clears, the platform's own schedule handles new work and the extra timer is residue nobody
remembers the reason for. Build the exit in:

- **Two completion tests** — target reached, *or* a full cycle produced nothing new (backlogs have
  unreachable floors; without this it loops against one forever).
- **Never retire on error** — if it can't measure, stay installed and exit loudly. "Can't tell" is
  not "finished."
- **Say goodbye** — email which condition fired and what covers the work now, or its disappearance
  looks like a failure.
- **Keep it out of your monitoring.** The probe that *detects* the stall should not be the thing
  that *fixes* it — that turns a notify-only layer into one that mutates. Measuring and acting are
  different jobs; keep them in different files.

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
