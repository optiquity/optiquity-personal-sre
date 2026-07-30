# 10 · MCP — external capabilities for the operator

An AI operator is far more useful when it can reach *outside* its own process — to your git
host, a scoped part of the filesystem, a browser, an external API. The **Model Context
Protocol (MCP)** is the standard way to grant those capabilities. This section covers which
MCP servers the framework treats as core vs optional, how they're configured per CLI, and —
critically — the **trust implications**, because every MCP server is a capability grant
([09 · Permissions](09-permissions.md)).

## What MCP is, in one paragraph

An **MCP server** is a small process that exposes a set of tools (and sometimes data) to the AI
CLI over a standard protocol. Enable a server and the operator gains its tools — e.g. a GitHub
server lets it read issues and open PRs; a filesystem server lets it read/write specific paths;
a browser server lets it drive a real browser. The CLI is the **client**; you configure which
servers it connects to.

The framework's stance: **MCP servers are how you extend the operator deliberately** — each one
added because a project needs it, scoped to the minimum, and understood before it's enabled.

## Core vs optional servers

**Core-ish (most setups want these):**

| Server | Grants | Why core |
|---|---|---|
| **git host** (e.g. GitHub) | Read/manage repos, issues, PRs, releases | The framework is git-host-centric; the operator manages your repos. |
| **filesystem** (scoped) | Read/write specific paths | Structured file access beyond the CLI's built-in tools, scoped to chosen dirs. |
| **shell** (scoped) | Run commands | Some CLIs route shell through MCP; scope it tightly. |

**Optional (add per project):**

| Server | Grants | Add when |
|---|---|---|
| **docs/context** (e.g. a docs-fetcher) | Current library/API docs | You want the operator citing up-to-date docs, not training memory. |
| **browser automation** (e.g. Playwright) | Drive a real browser | A task needs the web UI (see [11 · Agents & skills](11-agents-skills.md)). |
| **domain APIs** | Whatever that API does | A specific integration (a cloud provider, a service) is in scope. |

Keep the enabled set **small**. Every server is capability *and* attack surface; an unused
server is pure downside.

## Configuring MCP per CLI

Each AI CLI stores MCP config differently, but the shape is the same — a list of servers, each
with a launch command/args and (often) a scope. The framework ships **config templates** in
`skeleton/mcp/` with **placeholders, never real paths or tokens**:

- **Claude Code** — MCP servers declared in its settings; plugins can bundle common ones.
- **Codex** — its own config file (`config.toml`) with an MCP section.
- **Other CLIs** — their respective config; the template notes the location.

**Two hard rules for MCP config (both from [06 · Secrets](06-secrets.md)):**

1. **No tokens in the config that's committed.** An MCP server that needs auth reads it from
   the environment or a secret store at launch (`${GITHUB_TOKEN}`), never a literal value in
   tracked config.
2. **No personal paths.** A filesystem server's allowed directories are written as placeholders
   / `$HOME`-relative in the template; the user fills their real paths locally. The committed
   template must be scrubbable and generic.

## Trust implications — treat enabling a server like granting a permission

This is the part people skip and shouldn't. **An MCP server is a capability the operator
gains** — reason about it exactly as you would a permission grant ([09](09-permissions.md)):

- **Know what it can *do*, not just what you'll use it for.** A git-host server that can *merge
  PRs and delete branches* is a far bigger grant than one that can only *read issues*. Prefer
  read-only or least-capable variants when they exist.
- **Scope it.** A filesystem server pointed at all of `$HOME` can read your secrets, SSH keys,
  and browser data. Point it at the specific directories the work needs — never the home
  root, never a secret-bearing path.
- **Mutating vs read-only.** Classify each server: does it only *read* external state, or can
  it *change* it? A server that can mutate external systems (push code, send messages, spend
  money) deserves the same gating as a material action — its powerful tools should require
  approval, and your governance rules should say so.
- **Provenance.** You're running someone's code. Prefer official/well-known servers; audit or
  sandbox unknown ones. An MCP server has the capabilities you grant it *plus* whatever its own
  code does.
- **The operator's permission layer still applies.** Even with a server enabled, the CLI's
  permission settings ([09](09-permissions.md)) can keep its more dangerous tools on *ask*.
  Enabling a server is "the capability exists"; permissions decide "and it runs without a
  prompt or not."

## The MCP + permissions + rules stack

Putting the three capability-bounding layers together:

```
  Governance rules ([03])  — the operator PAUSES before material MCP actions (judgment)
  CLI permissions ([09])   — the harness PROMPTS/DENIES an MCP tool-call (capability limit)
  MCP scope (this section) — the server only CAN do what you scoped it to (surface limit)
```

Least privilege at every layer. A GitHub MCP scoped to one repo, with merge on *ask*, under a
rule that gates VC mutations, is safe to hand a fast operator. The same server unscoped, all
tools auto-allowed, with lax rules, is a foot-gun. Same software — the difference is entirely
how you bound it.

## Documenting your MCP setup

Like permissions and SSH edges, the enabled-server set should be **legible and reviewed**:

- Which servers are enabled, on which roles, and *why* (a project doc or the setup guide).
- Which are read-only vs mutating.
- Any that hold powerful capabilities, flagged — so a review can ask "does the operator still
  need the ability to merge PRs unattended?"

Prune enabled servers you no longer use. Capability accretes; a periodic review keeps the
operator's reach matched to actual need.

Next: [11 · Agents & skills](11-agents-skills.md) — subagents and the SKILL.md pattern that let
the operator take on packaged, repeatable capabilities.
