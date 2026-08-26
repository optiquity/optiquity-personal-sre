# 13 · Monitoring — knowing it works, and hearing when it doesn't

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

## Some things a central checker cannot see

A remote prober reaches anything on the network. Three important things aren't on the network:

- **A service with no listening port** — an outbound bridge, an agent, a queue worker. Nothing to
  probe; the right check is "is the process actually running?"
- **Local state** — a mount, a disk filling up, a batch job's last exit code.
- **The monitor itself.** If your health checker dies, it does not alert you that it died. Some
  *other* node has to cross-ping it.

So expect **two tiers**: a central checker for everything reachable, and a small local probe on
each node that matters, covering what the central one structurally can't.

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

## A dashboard is not a monitor

If you keep a status dashboard ([04 · Structure](04-structure.md)), be clear about the division:

| | Answers | Freshness |
|---|---|---|
| **Registry dashboard** | "What did we decide is true?" | Refreshed when you commit |
| **Health checker** | "Is it broken right now, and who was told?" | Live, and it calls you |

Both are worth having. Neither substitutes for the other. A dated snapshot that *looks* like
health is worse than no dashboard, because it invites you to trust it.

## What to run

The framework ships this as a working module — a mailer, a health-check config with email
alerting, a local probe, an update digest, plus the two blind-spot checks above:
[`../skeleton/monitoring/`](../skeleton/monitoring/). The end-to-end narrative, including the
platform traps that cost real debugging, is
[E16 · Fleet health, alerting, and the update digest](examples/E16-fleet-health-and-alerting.md).

Start with one health check and a working alert email. That single loop — something breaks, you
find out without looking — is most of the value; everything else is refinement.

Next: [14 · Setup](14-setup.md) — the onboarding journey that ties everything together into a
first working adoption.
