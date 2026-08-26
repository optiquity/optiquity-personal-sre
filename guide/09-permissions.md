# 09 · Permissions — bounding what the operator can do

The governance rules ([03](03-governance-rules.md)) are the operator's *judgment* layer — it
reads them and chooses to pause. This section covers the **capability** layer: the CLI's own
permission settings, which mechanically decide what runs without a prompt, what prompts, and
what's denied outright. You want **both** layers; this explains the second and how they
compose.

This is a first-class part of the framework: **permissions must be documented, explicit, and
deliberate** — never left at a tool's defaults and never silently broadened.

## Two layers, two different jobs

| Layer | What it is | Enforced by | Failure mode it prevents |
|---|---|---|---|
| **Session rules** ([03](03-governance-rules.md)) | The operator's judgment: "pause before material/VC/destructive actions." | The model reading + honoring the rules file. | The operator *choosing* to do something risky. |
| **CLI permissions** (this section) | Capability grants: which tool-calls auto-run, prompt, or are denied. | The CLI harness itself, mechanically. | A rule lapse *reaching* execution — the harness stops it. |

They are complementary. Rules can be reasoned around; permissions cannot. Permissions are
coarse (they don't understand *why*); rules supply the judgment. Together: the operator intends
to pause (rules), **and** the harness would stop it anyway if it didn't (permissions). Neither
layer has to be perfect because the other backstops it — **defense in depth**.

## The CLI permission model

Most AI coding CLIs expose a permission config (for Claude Code, a `settings.json` with a
`permissions` block of `allow` / `deny` / (ask) entries scoped to tool-calls). The framework
uses it to encode capability tiers:

- **allow** — runs with **no prompt**. Reserve for genuinely safe, reversible, local actions.
- **ask** (the default for anything not listed) — the harness **prompts** you before running.
- **deny** — **never** runs, even if asked. For categories you want structurally impossible.

Scope entries as narrowly as the CLI allows. "Allow reading files" and "allow running *any*
shell command" are worlds apart — grant the former freely, the latter almost never.

### What belongs in each bucket

**Safe to `allow` (auto-run):**
- Read-only inspection: reading files, listing, searching (`grep`/`find`-class), viewing diffs
  and status.
- Scoped writes to a throwaway area (a temp/scratch directory only).
- Read-only queries against remote nodes and services.

**Keep as `ask` (prompt):**
- Editing or writing real files (outside scratch).
- Any shell command that isn't a known read-only tool.
- Anything network-mutating, install-related, or service-related.

**Consider `deny` (never):**
- Whole-disk or credential-path access the operator should never need.
- Categories your governance rules forbid anyway (belt-and-suspenders): you can *deny* the
  capability so a rule-lapse can't reach it.

### Auto-approve, honestly

The appeal of "just auto-approve everything" is real — prompts are friction. But **auto-approve
is exactly where people give away safety without noticing.** The framework's guidance:

- **Auto-approve reads freely.** They can't hurt you; frictionless reading makes the operator's
  proposals better.
- **Auto-approve writes only in scratch.** A `Write(/scratch/*)` grant is safe; a blanket
  `Write` grant means the operator can silently overwrite anything.
- **Never auto-approve the outward-facing/material set** — pushes, deploys, deletes, service
  bootstraps — *at the permission layer*, even if you trust the operator. These stay `ask` (or
  are gated by the rules, ideally both). The cost of one wrong auto-approved push outweighs the
  saved prompts.
- **There is usually a "dangerous mode" / skip-all-prompts flag.** Understand exactly what it
  disables before enabling it, and prefer enabling it only on a low-stakes role (e.g. a
  `workstation` where you're present) rather than an always-on `server`. Document the choice.

## Three presets to start from

The framework ships **three permission presets** (`skeleton/settings/`) so you pick a posture
instead of hand-building one:

| Preset | Auto-runs | Prompts | Best for |
|---|---|---|---|
| **cautious** | reads only | everything else (all writes, all shell, all network) | Building trust; a new setup; a sensitive `server`. |
| **standard** | reads + scratch writes + common safe shell tools | real writes, network, installs, VC, material actions | The default day-to-day posture. |
| **trusting** | the above + more low-risk shell/edit categories | still prompts VC pushes, deletes, deploys, service bootstraps | An interactive `workstation` where you're present and want flow. |

**Every preset still prompts (or denies) the outward-facing/material set.** "Trusting" trims
friction on *low-risk* actions; it never hands over the dangerous ones. That invariant is the
point — presets differ in convenience, not in whether a push can happen silently (it can't).

Pick per role: a `server` that runs unattended deserves **cautious**; a `workstation` you sit

**Scheduled checks live outside this model entirely.** A timer-driven health probe or update
inventory runs under launchd/systemd with no session and no CLI, so neither preset nor session
rules apply to it. That is only acceptable because such jobs are strictly **read-only and
notify-only** — they report, they never change a node. Two consequences worth stating: anything
that *would* change a node must come back through a session and Rule 1; and the credential such a
job needs (e.g. SMTP) is a host-local `chmod 600` file, not a permission grant
([06](06-secrets.md), [E16](examples/E16-fleet-health-and-alerting.md)).
at can run **standard** or **trusting**. Because permissions are per-machine config, the config
manager can render the right preset per role ([05 · chezmoi](05-chezmoi.md)).

## MCP servers are a permission grant too

An MCP server ([10 · MCP](10-mcp.md)) gives the operator a **new capability** — reaching GitHub,
a filesystem path, a browser, an external API. Treat enabling one exactly like a permission
grant:

- Only enable the servers a project needs; each is attack surface + capability.
- Scope them (a filesystem MCP should be limited to specific paths, not all of `$HOME`).
- Know what a server can *do* before enabling it — some are read-only, some can mutate external
  state. A GitHub MCP that can *merge PRs* is a very different grant from one that can only
  *read issues*.

The permission mindset carries over: least privilege, scoped, deliberate, documented.

## Documenting the choice

Permissions are only trustworthy if they're **legible**. The framework requires:

- The permission preset (and any deviations) live in **tracked config**, per role — not tweaked
  ad hoc on a machine and forgotten.
- Any **broadening** (moving something from `ask` to `allow`, enabling dangerous mode, adding a
  powerful MCP) is a deliberate, noted change — ideally in a project doc explaining why.
- A periodic review: does each `allow` entry still deserve to be there? Permissions tend to
  accrete; prune them like you prune SSH edges ([08 · Networking](08-networking.md)).

The through-line with governance ([03](03-governance-rules.md)): **the rules say pause; the
permissions make sure it pauses.** Document both, and the operator is powerful *and* bounded.

Next: [10 · MCP](10-mcp.md) — configuring the external capabilities (GitHub, filesystem, and
more) the operator can use, and their trust implications.
