# 02 · The operator — how AI does the work

[Concepts](01-concepts.md) introduced "the operator" — the AI coding CLI that does the work.
This section is about the **interaction model**: how you actually work with it day to day, the
propose→approve→act rhythm, and where it gets its rules, capabilities, and skills. It's the
"how AI is used" companion to the concepts — read it before the governance rules, which define
the *boundaries* of what's described here.

## The operator, defined

The **operator** is an AI coding CLI (Claude Code as the reference; Codex and others work too —
see [11 · Agents & skills](11-agents-skills.md)) running in your repo, with:

- a **rules file** it reads at the start of every session ([03 · Governance](03-governance-rules.md)),
- a **permission configuration** bounding what it can do without asking ([09 · Permissions](09-permissions.md)),
- optional **external capabilities** via MCP ([10 · MCP](10-mcp.md)),
- and optional **skills** — packaged, repeatable procedures ([11 · Agents & skills](11-agents-skills.md)).

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

## Reads are free; changes are gated

The single most important property of working this way: **the friction is asymmetric, on
purpose.**

- **Reading, drafting, analyzing, dry-running** — zero friction. The operator explores as much
  as it needs to.
- **Changing something material** — a commit, a push, a deploy, a delete, applying config,
  bootstrapping a service — a hard stop for your go.

This is what makes handing ops work to a capable, fast AI *safe*: it can do a lot quickly, but
never crosses a consequential line without you. Sections [03 · Governance](03-governance-rules.md)
(the judgment layer) and [09 · Permissions](09-permissions.md) (the capability layer) define
exactly where that line sits — and let you move it as your trust grows.

## What the operator honors from the first minute

Because the operator reads its **rules file** at session start, its guardrails are live before
it does anything. In a well-set-up repo, the *first* thing established is the rules themselves —
so from that point on it won't push, apply, delete, or create remote artifacts without your
explicit approval. You're not hoping it behaves; you've configured it to, and the permission
layer backstops the configuration.

This is why onboarding ([13 · Setup](13-setup.md)) puts the rules file in place **first**: every
later step happens under governance, including the operator's own setup work.

## Where the operator gets its "self"

The operator's behavior isn't magic or memory — it's assembled from tracked files, which is why
it's consistent across sessions and nodes:

| What | Where it comes from | Section |
|---|---|---|
| **Its rules / guardrails** | the rules file (`CLAUDE.md` / `AGENTS.md`) | [03](03-governance-rules.md) |
| **What it can auto-do** | the CLI's permission settings | [09](09-permissions.md) |
| **External reach** (git host, files, browser) | MCP servers | [10](10-mcp.md) |
| **Packaged procedures** | skills (`SKILL.md`) | [11](11-agents-skills.md) |
| **Its memory of the system** | the project registry + docs, not chat | [04](04-structure.md) |

Because all of these are **files in your repo**, rendered onto each node by the config manager,
the operator behaves the same whether you invoke it on your `workstation` or your `server` — and
a new session picks up exactly where the last left off by reading them.

## One operator, many sessions (and CLIs)

- **A new session is not a blank slate.** It reads the rules + registry and orients itself —
  which is how a fresh session resumes an in-progress project (this is what onboarding's
  hand-off relies on: [13 · Setup](13-setup.md)).
- **You can run more than one CLI.** Claude Code is the reference; Codex and others map cleanly
  ([11 · Agents & skills](11-agents-skills.md) has the config-location table). Keep the rule
  *content* in sync across them so the operator behaves identically whichever you invoke.
- **You can run it on more than one node.** Same rules everywhere (symmetry —
  [Rule 5](03-governance-rules.md)); role-appropriate permission posture per node
  ([12 · Multi-node](12-multinode.md)).

## Delegation and parallelism (briefly)

For big or independent work, the operator can spawn **subagents** — parallel helpers that
search, review, or research concurrently while the main operator synthesizes and acts. Reads and
research delegate freely; **material actions stay in the main thread under your approval.** Full
treatment in [11 · Agents & skills](11-agents-skills.md).

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
