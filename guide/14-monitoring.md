# 14 · Monitoring — knowing it works, and hearing when it doesn't

Everything so far makes your system **legible**: config in one place, projects tracked, rules the
operator obeys. None of it tells you that the thing is *still working right now* — or wakes you
when it isn't.

That gap is where self-hosted setups quietly rot. A service dies and you find out days later
because you happened to open it. A package sits three versions behind because nothing ever said
so. A mount drops and the automation that depends on it fails silently until you notice the
output stopped. The system was legible the whole time; nobody was looking.

This chapter is the **looking**, and it has exactly two jobs:

1. **Is it working?** — health checks that assert *function*, and alert a human when they fail.
2. **What's fallen behind?** — a scheduled inventory of what's out of date, delivered as a digest.

Both are **notify-only**: they surface work and raise alarms, they never change a node. That is
what makes it safe to run them unattended (see [Rule 10](03-governance-rules.md) — reads are free,
and [Rule 1](03-governance-rules.md) — anything that *changes* a node still comes back to you).

## Check function, not reachability

A ping proves a box answers. It does not prove the app behind it works. The failure that actually
costs you is **up but broken** — the service is listening, the port is open, and every request
returns a 500 or an empty page.

So assert what a *working* response looks like:

```
status is 200
AND the body contains the thing only a healthy instance returns
AND it answered within a sane time
```

That last clause matters more than it looks: a service degrading toward death usually gets slow
before it stops. A latency ceiling catches it while you can still act.

## Liveness is not completion

The rule above has a batch-job twin, and it is the one that will fool you. For a *service*, "up but
broken" is the trap. For a *job*, the trap is **"the process exited, therefore the work is done."**

It isn't. A process exits when it is finished, when it fails, when it is killed, when it never had
anything queued, and when it was the wrong process entirely. Only one of those is success, and the
exit tells you nothing about which.

A real case. A long analysis pass was believed complete because a watcher checked whether the
relevant tool was running and emailed "generation complete" when it stopped. The work was **0.15%
done**. The tool being watched never performed that work at all — the analysis came from a
different subsystem entirely, on a different trigger. The probe was measuring an unrelated process
with a plausible name, and it had been reporting success for weeks. It surfaced only when a human
used the system and hit the missing result.

**A second instance, with a different mechanism — worth recognising because the first fix does not
catch it.** An automation platform ran a media-conversion job every 30 seconds and recorded
**2,256 consecutive successful executions** while converting nothing at all. Its status was not
lying about a *process*: the workflow genuinely ran, genuinely completed, and genuinely took the
correct branch — its own failure branch, which filed each item in a `failed/` directory exactly as
designed. Detection was never broken. **The runner's status means "the workflow ran", never "the
work succeeded"**, and nothing watched the directory where the failures piled up.

Two things made it invisible for weeks rather than minutes:

- **The tool failed soft.** The encoder printed "preset import failed", *continued anyway*, then
  exited non-zero for what looked like an unrelated reason. A tool that degrades instead of stopping
  converts a small mistake into an undiagnosable one.
- **The reason was only ever in memory.** The error existed solely in the execution record, which
  the platform prunes after about a day. By the time anyone looked, the evidence had aged out.
  **Write the failure reason to disk** — next to the artifact that failed — or you will be
  diagnosing from absence.

*(The trigger, for the record: a directory renamed `Presets` → `PRESETS`. The share was
case-sensitive; the automation was not updated. A case-only rename is invisible in every listing you
would naturally reach for, and is worth grepping your automation for before you make one.)*

So for anything batch, long-running, or queue-driven:

**Count the artifact the work produces.** Not the process, not the trigger, not the log line saying
it started. If the job writes rows, count rows. If it writes files, count files. Then express it as
**coverage** — `done / total`, a percentage — because a percentage cannot silently mean zero the way
a boolean can. `complete: true` is a claim; `41,802 of 71,623 (58.4%)` is a measurement.

**A percentage also gives you the completion signal a long job otherwise lacks.** A multi-week sweep
has no clean end event, so the honest terminal signal is *absence of progress*: coverage stopped
advancing for N hours. Report the number alongside it and let the reader distinguish "finished" from
"died at 12%" — the same alert covers both, and neither can masquerade as the other.

**Never let a probe assert something it doesn't measure.** That same false alert claimed *two*
things — and the other one was true. The verifiable half made the fabricated half credible; nobody
questioned a message that was half right. If a probe reports on two artifacts, it must count both,
or claim only the one it counts.

**Watch for this shape in your own probes:** any check whose evidence is a process, a PID, a lock
file, a "started" log line, or a job's exit code, standing in for output that was never inspected.
Ask what would happen if the work silently produced nothing — if the probe still reports success,
it is measuring the wrong thing.

## Some things a central checker cannot see

A remote prober reaches anything on the network. Three important things aren't on the network:

- **A service with no listening port** — an outbound bridge, an agent, a queue worker. Nothing to
  probe; the right check is "is the process actually running?" — but that answers whether a service
  is **up**, never whether a **job finished**. See *Liveness is not completion* above before reusing
  it on batch work.
- **Local state** — a mount, a disk filling up, a batch job's last exit code.
- **The monitor itself.** If your health checker dies, it does not alert you that it died. Some
  *other* node has to cross-ping it.

So expect **two tiers**: a central checker for everything reachable, and a small local probe on
each node that matters, covering what the central one structurally can't.

## The services that survive are the ones that mislead you

Worth stating plainly, because it decides *what* to check. When a node half-fails, the components most
likely to still be running are the **infrastructure** ones — the SSH daemon, the mesh VPN client, the
remote-access agent. They are services proper: they start at boot, they need no session, they have
nothing to do with the work.

So they stay green. The machine answers, resolves, and accepts connections while the thing it exists
to do is not running at all. Every "is the host up?" check agrees that everything is fine, and the
better your access tooling, the more convincing the illusion.

Check the **work**, and prefer a signal that a merely-running process cannot produce:

- Not "the service listens" but "it returns the expected content".
- Not "the queue manager is up" but "the queue is non-empty" — an application that restarted without
  its state will happily serve an empty one, and a process check passes every time.
- Not "the tunnel is connected" but "traffic is actually flowing through it on the port we expect".

The rule of thumb: if a check would pass on a freshly-installed copy of the application with none of
your data, it is testing the wrapper rather than the work.

## Alert out-of-band from what you're watching

Your alerting must not depend on the stack it monitors. If notifications route through the
automation platform, then the outage that takes down automation also takes down the notification
about it — you learn nothing precisely when it matters most.

Give alerting **its own path**: a standalone mailer with its own credential (an SMTP app password
is enough), independent of your services. The credential is a secret a *daemon* reads, not your
shell — see [06 · Secrets](06-secrets.md) for that recipe.

## Alerts a human will actually read

An alert nobody reads is worse than no alert: it trains you to ignore the channel.

- **Dampen flapping.** Fire after N consecutive failures, not the first blip, and say when it
  recovers. A network hiccup should not page you.
- **Deduplicate by state, not by run.** A check that runs every 15 minutes must notify on the
  *transition* (ok→fail, fail→ok), never on every run. This one decision is the difference
  between a useful channel and a filtered-to-trash one.
- **Say what broke in the subject.** `2 failing — media mount, bridge daemon` beats `alert`.
- **Give every sender one subject shape** so you can filter and triage:
  `[<YourTag>/<Kind>/<Source>] text`, where **Kind** is the triage axis (`Alert` = act now,
  `Digest` = scheduled summary, `Report` = finished, FYI) and **Source** is the subsystem. Keep
  Kind and Source as separate slots — "what kind of message" and "what it's about" are different
  axes, and merging them makes every filter ambiguous.
- **Expect one tool to refuse.** Health checkers often hardcode their subject line. Don't contort
  its config to force cosmetic consistency — accept its format and write a second filter rule.

## Prove the alert path — an induced failure, not a green page

**A dashboard full of green endpoints proves your checks run. It proves nothing about alerting.**
The credential, the sender, the recipient, the spam folder — none of that is exercised until a
check actually fails.

So exercise it deliberately: add a throwaway check guaranteed to fail (point it at a closed port,
threshold 1), confirm the mail lands in the inbox you actually read, then remove it. Do this when
you set it up, and again whenever you change the credential or the recipient. Until you have seen
a real failure email arrive, you have an untested alarm.

## Updates: automate the noticing, not the upgrading

[07 · Tools & requirements](07-tools-requirements.md) argues you should update deliberately rather
than auto-upgrade. That posture only holds if you actually *know* what's behind — otherwise
"deliberate" quietly becomes "never".

So schedule the **inventory**, not the upgrade: a job that walks every node, asks each package
manager what's outdated, and emails you a digest. It changes nothing. You act on it when you
choose, following [E10](examples/E10-fleet-update-pass.md).

Two blind spots are worth building in from the start, because neither shows up in any package
manager:

- **Version-pinned container images.** Pinning is correct for an appliance, but nothing tells you
  the pin went stale — you find out from a banner inside the app, if ever. Ask the registry.
- **One tool installed two ways.** A manual shim shadowing a package-managed binary, an npm CLI
  next to a cask. Whichever wins the `$PATH` race decides what runs, and upgrades break
  confusingly. This is detectable: flag any command backed by two *different* real binaries.

### The enumeration blind spot, and why patching it one case at a time fails

Those two are not a list. They are the first two instances of a pattern that will keep recurring:
**a class of installed thing that nothing enumerates.** Expect it in at least four shapes:

| Shape | Example |
|---|---|
| A whole **install method** unchecked | containers · language-version tools · binaries dropped into `/usr/local/bin` |
| An **instance** of a checked method unregistered | a second compose stack the image checker was never pointed at |
| **Unreadable input** to a working checker | tags with a variant (`5.13-apache`, `mysql-v2.19.0`) that the parser silently skips |
| A whole **host** unchecked | a machine marked "manual" years ago and never revisited |

The last one is the expensive one, and the easiest to acquire. A host gets labelled *manual* because
some early attempt failed; the label then reads as a decision rather than an absence, and nobody
retests it. Retest the premise — the reason is often narrower than the label. "Needs an elevated
session" is usually true of **installing** and false of **detecting**, and those get conflated. A CLI
believed absent may just not be on the non-interactive `PATH`.

Each of these is tempting to fix with one more special case. Don't: the next one is already waiting,
and a special case can be added *to the very tool built to close the previous three*.

**The general fix is reconciliation.** Invert the question — instead of "check the things on my
list", ask *"what is installed here that nothing is watching?"*

```
   DISCOVERY  (probe each host: which install methods actually hold packages?)
        │
        ├── present + registered as checked    → fine
        ├── present + registered as excluded   → COUNTED in the digest, never silent
        └── present + NOT REGISTERED           → reported as a finding   ← the point
```

Both halves are load-bearing. **A registry alone has the identical blind spot** — it only ever
contains what someone remembered to add. **Discovery alone is noise** — it can't know that a
system-vendored Ruby is deliberately untracked. Skip methods with **zero** installs, or the report
cries wolf about every tool you have but don't use.

Two rules keep this honest as it grows:

- **Never mark something "checked" before its check exists.** A registry that claims coverage it
  doesn't have manufactures precisely the false confidence it was built to remove. Verify **both**
  directions: that the check finds a real update, *and* that deregistering the thing makes it report
  as unregistered. One direction proves nothing.
- **Exclusions must stay visible.** An exclude list whose entries vanish from the report becomes the
  next blind spot. Give every exclusion a reason that stands on its own, print an
  `excluded (N)` count, and support a revisit date so "not now" can't silently become "never".

### Three outcomes, never two

Every check must distinguish **clean**, **could-not-run**, and **unregistered**. Collapsing the first
two is the most common bug in this kind of tooling: a command that errors produces no output, and no
output renders exactly like "nothing to report".

Concretely: say *"index not refreshed"* rather than implying an exact count; report an unreadable
version as `UNREADABLE`, never as "current"; and if a discovery pass finds items that are all
registered, say *"3 found, all registered"* — not *"nothing found"*, which is a different and false
claim.

### Don't let the report train you to ignore it

A row that can never be cleared is worse than no row. Two ways to create one:

- **Comparing a floating tag against a pinned resolution.** `3.14-alpine` *resolves to* `3.14.7`;
  reporting an "update" to the image already running produces a permanent, unfixable line.
- **Re-proposing something already declined.** A decline is a durable answer. Record it, and
  re-surface it only when the facts change or a revisit date arrives.

Either one teaches the reader to skim the one report where real updates appear.

## A dashboard is not a monitor

If you keep a status dashboard ([04 · Structure](04-structure.md)), be clear about the division:

| | Answers | Freshness |
|---|---|---|
| **Registry dashboard** | "What did we decide is true?" | Refreshed when you commit |
| **Health checker** | "Is it broken right now, and who was told?" | Live, and it calls you |

Both are worth having. Neither substitutes for the other. A dated snapshot that *looks* like
health is worse than no dashboard, because it invites you to trust it.

## Background work has a window, and the window is not the schedule

Most platforms run their heavy background jobs — reindexing, analysis, thumbnailing, compaction —
inside a **maintenance window**, so they don't compete with real use. That window is a *cap on
runtime*, and it's easy to miss because nothing reports it: the job simply stops, and the next day
it starts again.

The failure mode is arithmetic. A backlog that needs 240 hours of processing finishes in ten days
if the job runs continuously — and in **two months** if it only runs a four-hour nightly window.
Same throughput, same hardware, a 6× difference in delivery, and nothing anywhere states which one
you're getting. A real case: a sweep believed to be running continuously was being killed at the
window's end hour every night, discovered only because a human noticed it had gone quiet.

Two things to establish before trusting any ETA for a long backlog:

- **Confirm the actual runtime, don't assume it.** Look at *when* work stops, not just that it
  progresses. Completion timestamps clustered at a wall-clock hour are the tell — a job whose last
  output lands at the same time every night is window-bound, not finished.
- **Check whether a manual trigger has the same bounds.** Often it doesn't: a hand-started job may
  run immediately regardless of the window's *start*, yet still be killed at its *end*. That
  asymmetry is what makes a single daily nudge worthwhile, and it's worth testing directly rather
  than reasoning about — trigger one outside the window and watch whether work begins.

**Settings that sound relevant frequently aren't.** In that case a "process new items as soon as
they arrive" option was read as "run continuously"; it actually governed only how *newly added*
items were handled and had no bearing on whether a backlog sweep respected the window. Adjacent
naming is not documentation — verify what a setting gates by observing behaviour.

## Scaffolding should retire itself

If you automate around a limit like that, the automation is usually for a **one-off backlog**, not
a permanent condition. Once the backlog clears, the platform's normal schedule handles ongoing work
and the extra job is pure residue — a timer firing forever for a reason nobody remembers, which is
how a fleet accumulates cron jobs no one dares delete.

So build the exit condition in from the start. A self-retiring job needs three things:

- **Two ways to be done**, because "done" has two shapes: the target is reached, *or* a full cycle
  produced **nothing new**. The second matters — a backlog often has an unreachable floor (items
  that can't be processed at all), and without that test the job loops against it forever.
- **A refusal to retire on error.** If it can't measure, it must stay installed and exit loudly.
  *Can't tell* is not *finished*, and a job that removes itself on a transient failure is worse
  than one that never retires.
- **A parting message** saying which condition fired and what now covers the work — otherwise its
  disappearance is indistinguishable from it having broken.

Keep it **separate from your monitoring**. It's tempting to let the probe that detects the stall
also fix it, but that turns a notify-only layer into one that mutates, and you lose the guarantee
that your monitoring is safe to run anywhere. Measuring and acting are different jobs; keep them in
different files.

## What to run

The framework ships this as a working module — a mailer, a health-check config with email
alerting, a local probe, an update digest, plus the two blind-spot checks above:
[`../skeleton/monitoring/`](../skeleton/monitoring/). The end-to-end narrative, including the
platform traps that cost real debugging, is
[E16 · Fleet health, alerting, and the update digest](examples/E16-fleet-health-and-alerting.md).

Start with one health check and a working alert email. That single loop — something breaks, you
find out without looking — is most of the value; everything else is refinement.

Next: [15 · Setup](15-setup.md) — the onboarding journey that ties everything together into a
first working adoption.
