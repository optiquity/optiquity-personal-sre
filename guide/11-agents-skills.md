# 11 · Agents & skills

Beyond running commands, the operator can take on **packaged, repeatable capabilities** and
**delegate work to subagents**. This section covers two patterns: **skills** (documented
capabilities the operator loads on demand) and **subagents** (parallel or specialized helpers).
Both are how you turn "the operator can figure it out each time" into "the operator has a
reliable, reviewed way to do this."

## Skills — packaged capabilities

A **skill** is a small, self-contained instruction set that teaches the operator *how* to do a
specific task — with the exact tools, steps, and guardrails — so it does the task the same
reliable way every time instead of improvising.

The reference format is a **`SKILL.md`**: a markdown file with a metadata header (name,
description, required tools) and a body of instructions. The operator loads it when the task
matches, follows it, and — crucially — obeys the guardrails written into it.

### What makes a good skill

- **Composes existing capabilities.** The best skills wire together tools you already trust
  rather than introducing new dependencies. A "log into service X and do Y" skill composes a
  browser-automation capability + a vault-read capability ([06 · Secrets](06-secrets.md)) —
  not a bespoke scraper.
- **Declares its requirements.** The header lists the binaries/tools it needs, so it fails
  clearly ("tool not installed") rather than mysteriously.
- **Encodes guardrails, not just steps.** The valuable part is often the *don'ts*: "confirm
  before deleting," "never echo the secret," "stay on this site," "one session at a time."
  Skills are where task-specific safety lives.
- **Is credential-safe.** A skill that logs into something reads the credential from the vault
  just-in-time, fills it directly, never logs it — the [06 · Secrets](06-secrets.md) pattern,
  restated in the skill so it can't be skipped.
- **Is scrubbable.** A shared/public skill contains *no* personal specifics — no real
  usernames, no account-specific values. It references a vault *entry title* and a *pattern*,
  not your actual login. (Personal skills — ones tied to your specific accounts — stay in your
  private repo and are never published.)

### Two example skills the framework ships (generic)

The skeleton (`skeleton/skills/`) includes two **generic** examples that demonstrate the
pattern without any personal detail:

1. **A vault-read skill** — read a credential/token from the secret store, read-only,
   non-interactive, never-logged. The building block for anything that needs a login.
2. **A browser-automation skill** — drive a real browser for tasks with no API, logging in via
   the vault-read skill. Demonstrates composition + the "confirm before destructive actions"
   guardrail.

These are teaching examples. Your own skills — especially ones bound to specific services or
accounts — live in *your* repo and follow the same rules, but are yours, not the framework's.

### A note on anti-automation

Real-world skills that drive web UIs will meet sites that resist automation (bot-detection,
WAFs). When you find the specific approach that works for a site (a particular browser mode,
human-like interaction, pacing), **bake it into the skill** with a note on *why* — so the
operator doesn't rediscover the block every run. And keep such skills honest about their
fragility: an approach that works today may need revisiting if the site tightens. Document that.

## Subagents — delegation and parallelism

A **subagent** is a fresh operator instance the main operator spawns to handle a scoped piece
of work. Two reasons to use them:

1. **Parallelism / fan-out.** Independent tasks (searching several subsystems, reviewing many
   files, checking multiple sources) run concurrently as subagents, and the main operator
   synthesizes their results. Faster, and it keeps the main context focused on the conclusion
   rather than the raw material.
2. **Specialization.** A subagent can be a focused role (a code reviewer, a researcher, a
   search agent) with its own tools and instructions, better at its narrow job than a
   general pass.

### Guidance for subagents

- **Delegate reads and research freely** — a subagent sweeping files or the web is low-risk and
  keeps the main thread clean. This pairs with [Rule 10](03-governance-rules.md) (reads are
  free).
- **Keep material actions in the main thread, under the rules.** A subagent that *proposes*
  changes is fine; the actual gated action (commit, apply, deploy) happens in the main
  operator where you approve it. Don't scatter approval-requiring actions across subagents
  where they're harder to supervise.
- **A subagent's result is a report, not a side effect.** Use subagents to *learn* and
  *decide*; use the main operator to *act*.
- **Scope them.** A subagent gets the tools and context its task needs — not blanket access.
  The permission model ([09](09-permissions.md)) still applies.

## The operator's config across CLIs

The operator's rules, skills, and subagent setup live in CLI-specific config, but the framework
keeps the *pattern* portable:

| CLI | Rules file | Model/global config | MCP config | Permissions |
|---|---|---|---|---|
| **Claude Code** (reference) | `CLAUDE.md` | `settings.json` | `settings.json` → `mcpServers` | `settings.json` → `permissions` (3 presets, [09](09-permissions.md)) |
| **Codex** | `AGENTS.md` | `~/.codex/config.toml` | `config.toml` → `[mcp_servers]` | Codex's approval settings |
| **Gemini / agy** | its own rules doc | its own config | its own MCP section | its own approval settings |
| **Others** | their equivalent | varies | varies | varies |

The framework is **Claude-first**: it ships the Claude reference complete, with the Codex
equivalents alongside it — `skeleton/CLAUDE.md.template` **and** `skeleton/AGENTS.md.template`
(identical rules, different filename), and `skeleton/mcp/claude.mcp.json` **and**
`skeleton/mcp/codex.mcp.toml`. Everything in `guide/` is CLI-agnostic (it's the *why*); only
the config *locations* differ, mapped in the table above.

Where an equivalent isn't obvious (a Gemini/agy specific), it's marked "adapt here" rather than
blocking — a personal-SRE setup with **one** CLI is completely valid; multi-CLI is an
enhancement, not a requirement. If you run **more than one** CLI, keep the rule *content*
synchronized between the rules files (or generate both from one source via the config manager)
so the operator behaves the same whichever CLI you invoke — [Rule 7](03-governance-rules.md)
(symmetry) applied to your own tooling.

## Keeping skills and agents legible

Same discipline as everywhere else:

- Skills are **tracked** (in your repo, under config-management) so they're versioned and
  applied consistently across nodes — a skill is only reliable if every node has the same
  version.
- Each skill's **guardrails are reviewed** — especially destructive-action confirmations and
  credential handling.
- **Personal skills stay private; generic skills can be shared** — the same scrub discipline
  that governs the whole public/private split ([14 · Sharing](14-sharing.md)).

Next: [12 · Multi-node operations](12-multinode.md) — the advanced layer for coordinating an
operator across several nodes at once.
