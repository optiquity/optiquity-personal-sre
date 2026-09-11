# 14 · Workflows & automation — the fleet's glue

A fleet accumulates jobs: fetch this nightly, react to that webhook, reconcile two systems that do
not know about each other, tell me when something changed. This section is about where those jobs
live, and about the operator's second role here — not just **keeping an automation platform
running**, but **writing the automations**.

Both halves matter, and the second is the one people skip.

## Start at the floor: you may not need a platform

**Cron and systemd timers are the honest baseline.** A scheduled script in your repo, run by the
node's own scheduler, has properties a platform cannot beat: no service to keep alive, no database
to back up, no upgrade that breaks your jobs, and the whole thing is `git log`-able.

Reach for a platform when you need something the floor genuinely cannot give you:

- **Reacting to events** — webhooks, file drops, inbound mail — rather than to a clock
- **Multi-step flows with state** — retries, branching, "wait for approval", resumable runs
- **Many integrations you would otherwise hand-write** — dozens of APIs with auth already solved
- **A view of what ran** — a run history you can inspect after the fact

If none of those apply, a timer and a tracked script is the better engineering. ⚠ **A platform you
adopted for one webhook is a stateful service you now own forever.**

## The field

**Visual / low-code, self-hosted**

- **n8n** — large integration library, visual editor, webhook-native. Source-available under a
  restrictive licence; check it if you are commercial.
- **Node-RED** — flow-based, strong in the IoT and event-wiring space, genuinely open source.
- **Activepieces** — newer, MIT-licensed, similar shape to n8n.
- **Huginn** — long-lived Ruby agent system; pull-and-transform rather than integration-first.
- **Windmill** — scripts-first with a generated UI; sits between "visual tool" and "code".

**Code-first orchestrators**

- **Temporal** — durable execution; the right answer when a workflow must survive crashes and run
  for days. Heavier than a personal fleet usually needs.
- **Prefect / Dagster / Airflow** — data-pipeline orchestrators. Excellent at DAGs of work with
  dependencies; overkill as general glue.

**The floor**

- **cron**, **systemd timers**, **launchd** on macOS, **Task Scheduler** on Windows — plus a script
  in your repo.

**The axes that decide it:**

1. **Licence**, again. Several tools in this category are source-available rather than open source.
2. **Where credentials live.** A platform that stores API keys in its own database has become part
   of your secrets surface ([06 · Secrets](06-secrets.md)). Prefer references to a vault or
   environment over secrets pasted into the tool.
3. **What it holds that you cannot rebuild.** Workflows, credentials, run history, queue state. This
   is the question that decides your backup obligation, not the feature list.
4. **Visual or code.** Visual tools are faster to start and harder to review — a diff of a workflow
   export is not readable the way a script is. Code-first is the opposite trade.
5. **Blast radius when it is down.** If a broken platform means the backups stop, you have coupled
   two things that should be independent.

**Adapt, don't adopt.** The examples in this guide describe the *shape* of owning an automation
runtime. Any tool in the list above fits that shape.

## Owning the platform

An automation runtime is a stateful service, and usually the one people are laxest about because it
feels like a tool rather than a database.

**It holds things you cannot reproduce from the repo** — the workflows themselves, the credentials
they use, the history of what ran. Back it up on a schedule, and **restore-test it at least once**.
A backup you have not restored is a hypothesis ([Rule 4](03-governance-rules.md)).

⚠ **A committed export is not a deployment.** This is the single most expensive trap in the
category. You export a workflow, commit it, see it in `git log`, and believe the running system
matches. It does not. The export is a *record*; the platform runs from its own database. **What is
in your repo is not what runs** unless something imported it, and nothing did.

⚠ **Importing can deactivate.** Many platforms import workflows in a disabled state, or overwrite
the active version with the exported one. An import intended as a restore can silently stop
production work. Know which your tool does — before you need the restore, not during it.

⚠ **Draft and published are different objects.** Editing a workflow in the UI often changes a draft
that is not what is executing. The thing you are looking at and the thing that runs at 3am can
disagree indefinitely, and nothing tells you.

**Verify from the record of what ran, not from what is on screen.** The execution history is the
only honest source. A workflow that looks correct and has not executed in three weeks is broken in a
way the editor will never show you — which is the same *liveness is not completion* problem the
monitoring chapter deals with.

## The other half: the operator as author

This is where a personal SRE setup stops looking like dotfiles with extra steps.

Your fleet has APIs everywhere — the config manager, the mesh, the container runtime, the metrics
stack, your repo host, the services themselves. Most useful automation is **glue between two of them
that no vendor will ever write**, because it only makes sense for your fleet. That is exactly the
kind of work an operator is good at: small, well-specified, testable, and boring to write by hand.

**What makes a good candidate:**

- It **reconciles two sources of truth** and reports the difference — declared versus installed,
  exported versus running, expected services versus answering services.
- It **notices**, rather than acts. Noticing is cheap to get right and safe to get wrong.
- Its output is **a record you can check later**, not a side effect you have to trust.
- It is **idempotent** — running it twice is the same as running it once.

**What to keep away from it:**

- ⚠ **Anything that acts on production without a human gate.** Automate the noticing, not the
  upgrading. The operator proposes; you decide ([Rule 11](03-governance-rules.md)).
- ⚠ **Anything holding a credential the workflow platform can read but you cannot audit.**
- ⚠ **Anything whose failure is silent.** If the automation stops running, something must say so.
  An automation nobody notices has stopped is worse than no automation, because you are now relying
  on it.

**Write automations the way you write everything else here:** the definition in the repo, the
secrets by reference, the schedule declared, and a check that the thing actually ran. An automation
without a liveness check is an assumption with a cron entry.

## Long-running agent services

A variant worth naming: an agent that runs **continuously** on a node rather than being invoked, and
reacts to events on its own. It is an automation platform of a different shape, and it inherits all
of this section's obligations plus one more — **it can act, and it does not have you in the loop by
default.**

Treat it as the highest-privilege service on the fleet. Bound it with the same three layers
everything else gets: the rules it reads ([03 · Governance](03-governance-rules.md)), the
permissions of the account it runs as ([10 · Permissions](10-permissions.md)), and the capability
grants you gave it ([11 · MCP](11-mcp.md)). Give it the narrowest credentials that let it do its
job, and make its actions land somewhere you can read afterwards.

## What to write down

- which runtime, and **why that one** — licence, credential handling, or "the floor was enough"
- what it holds that is not reproducible, and where the backup goes
- the restore test, with a date
- the schedule or trigger for each automation, and **what tells you it stopped**
- which automations are allowed to act, and which only notice

Next: [15 · Documentation & content generation](15-content-generation.md) — the other thing a fleet
produces continuously, and the one that rots fastest.
