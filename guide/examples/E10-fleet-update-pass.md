# E10 · A deliberate fleet-update pass

**Section E — fleet operations.** Back to the [catalog](../17-example-projects.md).

**What this shows:** the *maintenance* half made explicit — the **"don't auto-update; inventory
what's behind, update per machine, verify, note what's held and why"** runbook. Updates as a
governed **project**, not a reflex.

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

---

## The scenario

Across your nodes, installed tools, packages, and services drift out of date. You want them
current — but **not** by letting everything auto-update (that's how a working node breaks
unexpectedly, mid-task). You want a **deliberate, reviewable pass**: see what's behind, decide
what to update, do it per machine, verify, and record what you're deliberately holding back.

## Why do it "the framework way"

The framework's stance on updates is explicit ([07 · Tools & requirements](../07-tools-requirements.md)):
**a node's tooling changes when *you* decide it does.** Auto-updating everything trades a small
convenience for the risk of a surprise breakage on an always-on node. So updates are a *project*
with a runbook — the operator inventories, proposes, and (with approval) applies, one node at a
time, and writes down the result.

## The shape

### 1. Inventory (read-only, free)

The operator surveys each node — reads are always free ([Rule 10](../03-governance-rules.md)):

```sh
# per node, per package source:
#   <pkgmgr> outdated            # system packages behind
#   npm outdated -g              # global CLIs behind
#   <language/tool> version checks
# note the "index staleness": some managers need a refresh before "outdated" is accurate
```

Produce a **backlog snapshot** — what's behind, on which node — and note it's a *floor* if any
index is stale.

### 2. Classify before touching anything

Not everything should be updated the same way:

- **Leaf tools** (CLIs, doc tooling) — low-risk; safe to bump.
- **Service runtimes** (a language runtime an app depends on, a container image) — update only in
  a **window**, with a restart + smoke test; never mid-use.
- **Self-updaters** (apps with their own updater) — **leave them alone**; don't also manage them
  via a package manager ([A3](A3-npm-global-cli.md)).
- **Platform/OS + anything that reboots** (a NAS, a Windows box) — schedule for a quiet window; a
  reboot may drop mounts/services other nodes depend on.
- **Vendor channels that stall** — a tool can be installed *through* a package manager whose
  channel **lags or freezes**: a third-party app-store repo that quietly stopped publishing, a
  distro repo far behind upstream. **"Auto-update is on" does not mean "current"** — an automatic
  channel that's stalled is doing no good. For these, know where the vendor's *own* latest lives,
  and **track them manually** (a periodic check against upstream) if the built-in channel doesn't
  advance them. A security-sensitive tool stuck years behind on a "self-maintaining" box is exactly
  the drift a deliberate pass is meant to catch.

### 3. Update per machine, verify, record

- One node at a time; **refresh the index first**, then update the classified-safe set.
- **Back up before anything material** ([Rule 4](../03-governance-rules.md)); the apply/update on a
  node is **gated** ([Rule 1](../03-governance-rules.md)).
- **Verify** after: services still up, tools resolve, a quick smoke test.
- **Keep same-role nodes symmetric** ([Rule 7](../03-governance-rules.md)) — update a `workstation`
  as a canary, then mirror to the other same-role nodes.

### 4. Track it — including what you held back

Registry row + a `PLAN.md` ([04 · Structure](../04-structure.md)) with the **backlog snapshot**,
what you updated, and — importantly — **what you deliberately held back and why** (a pinned
version, a runtime you're not ready to bump). Held-back items are a *managed* backlog, not
forgotten work ([Rule: no undocumented deferral](../03-governance-rules.md)).

## Maintenance — the ownership half (this example *is* maintenance)

- **Cadence, not continuous.** A periodic pass (e.g. monthly for leaf tools; on advisories or
  quarterly for OS/service updates) you *drive*, rather than background auto-upgrades.
- **The held-back list is living** — revisit it each pass; a pin you added for a reason may be
  ready to lift.
- **Watch for the platform gotchas** — some updates can't be driven headless (e.g. an OS package
  manager that needs an elevated interactive session; a NAS that updates via its own UI) — note
  those as "do at the machine," don't pretend they're automatable.

## What you learn from this example

- **Updates are a governed project, not a reflex** — inventory → classify → update-per-machine →
  verify → record.
- **Classification matters** — leaf tools, service runtimes, self-updaters, and OS/reboots each get
  different handling.
- **Write down what you held back** — a visible backlog is a managed backlog; silent staleness is
  the failure mode.

## Adapt it

In **your** repo: run the inventory across your nodes, classify the backlog, update the safe set
per machine (canary → mirror), verify, and record the pass — including the held-back list — as a
recurring project.

**Related:** [07 · Tools & requirements](../07-tools-requirements.md) ·
[A3 · one install method](A3-npm-global-cli.md) · [Rule 4 + Rule 7](../03-governance-rules.md) ·
[13 · Multi-node](../13-multinode.md) ·
[E16 · Health + alerting](E16-fleet-health-and-alerting.md) (automates this inventory into a weekly digest) ·
[catalog](../17-example-projects.md).
