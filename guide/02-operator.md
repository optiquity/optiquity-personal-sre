# 02 · The operator — how AI does the work

[Concepts](01-concepts.md) introduced "the operator" — the AI coding CLI that does the work.
This section is about the **interaction model**: how you actually work with it day to day, the
propose→approve→act rhythm, and where it gets its rules, capabilities, and skills. It's the
"how AI is used" companion to the concepts — read it before the governance rules, which define
the *boundaries* of what's described here.

## The operator, defined

The **operator** is an AI coding CLI (Claude Code as the reference; Codex and others work too —
see [12 · Agents & skills](12-agents-skills.md)) running in your repo, with:

- a **rules file** it reads at the start of every session ([03 · Governance](03-governance-rules.md)),
- a **permission configuration** bounding what it can do without asking ([10 · Permissions](10-permissions.md)),
- optional **external capabilities** via MCP ([11 · MCP](11-mcp.md)),
- and optional **skills** — packaged, repeatable procedures ([12 · Agents & skills](12-agents-skills.md)).

You don't program it. You **converse** with it: you state intent, it proposes, you approve, it
acts. The repo and the git history are the record of that conversation.

## The core rhythm: propose → approve → act

Working with the operator has a distinct, repeating shape:

1. **You state intent** — "back up the database nightly," "migrate this service to the server,"
   "why is this failing?" Plain language, not commands.
2. **It reads first, freely.** It inspects files, runs read-only commands, checks state across
   nodes — no approvals needed ([Rule 10](03-governance-rules.md)). Good proposals come from
   thorough reading, so frictionless reads are a feature.
3. **It proposes** — a concrete plan or change, described before it happens.
4. **You approve (or redirect)** — for anything **material or outward-facing**, it stops and
   waits. Reversible, local work it may just do (per your permission preset).
5. **It acts, then verifies** — makes the change, confirms it worked, reports honestly.

The skill you develop is **steering at the approval points** — the operator handles the
mechanical work; you supply judgment where it matters. Over a session this feels less like
running commands and more like directing a fast, literal colleague who always shows you the
risky steps before taking them.

## Before building: restate the end state, and wait for every yes

Step 3 of that rhythm, *it proposes*, has one characteristic failure: the operator builds its own
version of what you asked for. Every step was approved, yet the result is not what you wanted,
and why is hard to see until it runs. Three habits prevent it:

- **Restate the end state the way the owner will check it.** Before anything is built, write down
  what will exist when it is done: a tree of the files and folders, a table, a sample of the
  output. The result, not the steps. A wrong layout is visible in one diagram and invisible in a
  paragraph describing the plan.
- **An unanswered question is still open.** If you ask the owner to decide a point and the reply
  doesn't answer it, that point is not agreed, however sensible your recommendation. Ask again,
  directly, and build nothing that depends on it until it is answered.
- **Add nothing that wasn't asked for:** no helper file, temp folder or renamed output, even to fix
  a real problem. If the fix needs something new, propose it and wait. Something unrequested,
  appearing where the owner looks, costs trust out of all proportion to its size.

⚠ **The case that taught this.** A media pipeline was being rebuilt so that folders would come
out as folders. The owner's description said everything else in the folder should be copied
too. A clarifying question about that point went unanswered, and the operator built its own
recommendation instead. It also added hidden build folders, to fix a race nobody had asked it to
fix. Those folders made a healthy conversion look stalled, the layout was wrong, and the owner
could no longer tell what was working. The whole day's work was reverted. The redo restated the
end state as folder trees, got a yes on every open point before anything was built, and went live
clean.

The design templates ask for both ([04 · Structure](04-structure.md)): §1 wants the end state as the
owner will check it, and an open question blocks the work that depends on it. Step 5, *it verifies*,
has its own discipline: a test is proven only once it has been seen to fail
([17 · Monitoring](17-monitoring.md), "Prove each test").

## When you need the owner, ask; don't report

When the work is waiting on the owner, **put the one thing they must do first, on its own, as a
direct question or instruction.** Status goes after it, or in a separate message. A request buried
in a detailed update has not really been asked: the owner reads the state, finds nothing to do, and
the work waits on both of you.

- **If you hold the authority and have a recommendation, act on it.** Handing the same item back
  for a decision you could make yourself makes the work look deadlocked when it isn't.
- **List under "needs the owner" only what truly waits on them.** An item that is really waiting on
  evidence, framed as the owner's decision, makes the owner look like the holdup. Close items that
  are done, with the evidence that closed them.

⚠ **The case.** For an afternoon, two sessions sent the owner rich status while the one action they
needed from the owner was a single sentence in the middle. It happened twice, until the owner said
they had no idea what to do. One instruction, with nothing else attached, unblocked it.

## Reads are free; changes are gated

The single most important property of working this way: **the friction is asymmetric, on
purpose.**

- **Reading, drafting, analyzing, dry-running** — zero friction. The operator explores as much
  as it needs to.
- **Changing something material** — a commit, a push, a deploy, a delete, applying config,
  bootstrapping a service — a hard stop for your go.

This is what makes handing ops work to a capable, fast AI *safe*: it can do a lot quickly, but
never crosses a consequential line without you. Sections [03 · Governance](03-governance-rules.md)
(the judgment layer) and [10 · Permissions](10-permissions.md) (the capability layer) define
exactly where that line sits — and let you move it as your trust grows.

## What the operator honors from the first minute

Because the operator reads its **rules file** at session start, its guardrails are live before
it does anything. In a well-set-up repo, the *first* thing established is the rules themselves —
so from that point on it won't push, apply, delete, or create remote artifacts without your
explicit approval. You're not hoping it behaves; you've configured it to, and the permission
layer backstops the configuration.

This is why onboarding ([18 · Setup](18-setup.md)) puts the rules file in place **first**: every
later step happens under governance, including the operator's own setup work.

## Where the operator gets its "self"

The operator's behavior isn't magic or memory — it's assembled from tracked files, which is why
it's consistent across sessions and nodes:

| What | Where it comes from | Section |
|---|---|---|
| **Its rules / guardrails** | the rules file (`CLAUDE.md` / `AGENTS.md`) | [03](03-governance-rules.md) |
| **What it can auto-do** | the CLI's permission settings | [10](10-permissions.md) |
| **External reach** (git host, files, browser) | MCP servers | [11](11-mcp.md) |
| **Packaged procedures** | skills (`SKILL.md`) | [12](12-agents-skills.md) |
| **Its memory of the system** | the project registry + docs, not chat | [04](04-structure.md) |

Because all of these are **files in your repo**, rendered onto each node by the config manager,
the operator behaves the same whether you invoke it on your `workstation` or your `server` — and
a new session picks up exactly where the last left off by reading them.

## One operator, many sessions (and CLIs)

- **A new session is not a blank slate.** It reads the rules + registry and orients itself —
  which is how a fresh session resumes an in-progress project (this is what onboarding's
  hand-off relies on: [18 · Setup](18-setup.md)).
- **You can run more than one CLI.** Claude Code is the reference; Codex and others map cleanly
  ([12 · Agents & skills](12-agents-skills.md) has the config-location table). Keep the rule
  *content* in sync across them so the operator behaves identically whichever you invoke.
- **You can run it on more than one node.** Same rules everywhere (symmetry —
  [Rule 7](03-governance-rules.md)); role-appropriate permission posture per node
  ([16 · Multi-node](16-multinode.md)).

## Delegation and parallelism (briefly)

For big or independent work, the operator can spawn **subagents** — parallel helpers that
search, review, or research concurrently while the main operator synthesizes and acts. Reads and
research delegate freely; **material actions stay in the main thread under your approval.** Full
treatment in [12 · Agents & skills](12-agents-skills.md).

## Why work this way at all

The payoff of the operator model:

- **Leverage** — mechanical ops work (edits, migrations, audits, deploys) happens fast, while
  you stay in a supervisory role.
- **Safety** — the asymmetric friction means speed never costs you a consequential mistake made
  without review.
- **Legibility** — because the operator works through tracked files and gated changes, the git
  history *is* the audit log: what changed, when, why, and who approved it.

Next: [03 · Governance](03-governance-rules.md) — the rules that define exactly where the
operator must pause, which is what makes everything above safe.
