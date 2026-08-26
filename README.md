# optiquity-personal-sre

## What is an SRE?

SRE stands for Site Reliability Engineering (or Engineer). It is a practice that applies
software engineering to IT operations and infrastructure. Pioneered by Google, SRE aims to
create ultra-reliable, scalable software systems by replacing manual administrative work with
code and automation.

## What is this repo?

**A framework for running your own machines, services, and dotfiles the way a small ops team
runs infrastructure — with an AI coding CLI as the operator, under explicit rules, against
version-controlled configuration, with every change tracked.**

It's not a program you install. It's a set of **patterns + templates + guides** you adopt and
adapt: a governance model, a repo structure, a config-management flow, a permission model, and
the glue (networking, secrets, MCP, skills) that ties them together. You bring the accounts and
machines; the framework gives you the operating system for running them.

> **Status:** the concepts (the guide), the starter files (the skeleton), and the platform maps
> are complete for macOS, partial for Windows, stubbed for Linux/Cloud — and grow over time.
> See the maturity banners in `platforms/`.

## ▶ Start here

**New?** Two entry points, depending on what you want first:

- **Understand it →** read the guide's **[`guide/00-introduction.md`](guide/00-introduction.md)**
  first — the *philosophy* plus the **four minimal foundations** (tools, permissions, privacy,
  rules) that make the operator genuinely useful and unblocked. It's the doorway to the whole
  guide (index: [`guide/_contents.md`](guide/_contents.md)).
- **Set it up →** **[`GETTING-STARTED.md`](GETTING-STARTED.md)** — the requirements and
  step-by-step.

Two things to know before anything else:

- **This repo is a read-only REFERENCE — you don't edit it or commit to it.** Your work happens
  in **your own private repo**, which the setup creates for you (the "two-repo model" below).
- **The fastest path is to let your AI CLI do the setup for you** — paste the AI-guided-setup
  prompt from [`GETTING-STARTED.md`](GETTING-STARTED.md) into the CLI and it walks you through
  everything, installing prerequisites included, exactly as the framework was built.

## The two-repo model

```
  optiquity-personal-sre   (this repo — READ-ONLY reference; adopt FROM it)
          │  setup creates ↓
  <you>/personal-sre       (YOUR private repo — where ALL your work happens)
```

You clone this framework as a reference. Everything *you* do — dotfiles, configs, projects,
status — lives in **your own private repo**, created for you by `bootstrap.sh` (or the AI-setup
path). If you're ever editing a file inside *this* repo, it belongs in yours instead. Details:
`guide/01-concepts.md` and [`GETTING-STARTED.md`](GETTING-STARTED.md).

## Who it's for

- You have more than a handful of machines/services/dotfiles and want them *managed*, not just
  accumulated.
- You use an AI coding CLI and want it to *do ops work* — but only under rules you control.
- You want the whole thing reproducible, auditable, and recoverable.

You don't need a company, a cloud account, or an SRE background. **A single laptop is a valid
start**; the model scales to many nodes without changing shape.

## The 60-second model

- **Nodes are roles, not names** — `workstation`, `server`, `nas`, … — so config generalizes.
- **The repo is the source of truth** — machines are *derived* from it by a config manager
  (chezmoi), never edited directly.
- **An AI operator does the work under a rules file** that makes it pause before anything
  material or outward-facing.
- **Everything is a tracked project** in a registry, so the system's state is legible, not in
  your head.
- **Zero secrets in git, ever** — enforced structurally (ignore files + a vault), not by memory.
- **It tells you when something breaks** — health checks + a scheduled digest, delivered by mail,
  so you learn about a failure or a stale package without going to look
  ([E16](guide/examples/E16-fleet-health-and-alerting.md), tools in `skeleton/monitoring/`).

## The playbook — the operator's entrypoint

When you sit down to *do* or *fix* something, you need one front door that routes you to the right
place. That's **`PLAYBOOK.md`** at your repo root — a thin, **layered** hub (hardware → foundation →
networking → servers → storage → monitoring → applications) that indexes every project and links to
its runbook, plus a cross-cutting **troubleshooting index** ("seen this symptom?") and **external
vendor docs**. It holds no content of its own — it only links out and in — so it never drifts. Where
the registry says *what state* a thing is in, the playbook says *how to do or fix it*. See
`guide/04-structure.md` → "The playbook" for the pattern, and `skeleton/onboarding/PLAYBOOK.md` for a
starter.

## The dashboard (optional)

For a system of any size, an optional **status dashboard** turns your project registry + node
state into a single at-a-glance view — a self-contained HTML page (no server, no build step)
driven by a data block you edit. It renders all your projects grouped by status, a detailed page
per active project, and a page per node. It's opt-in — skip it until you have enough going on to
want the overview. See `guide/04-structure.md` → "The dashboard" for the pattern, and
`skeleton/` for a starter.

## Getting started

Full walkthrough (intro, requirements, step-by-step): **[`GETTING-STARTED.md`](GETTING-STARTED.md)**.

Three onboarding tiers, all reaching the same working single-node setup — they differ only in
how much is automated vs. explained:

| Tier | You do | Best if |
|---|---|---|
| **3 · AI-guided setup** ⭐ | paste the prompt from [`GETTING-STARTED.md`](GETTING-STARTED.md) into your AI CLI | **Recommended** — the operator sets it up for you, prerequisites included. |
| **2 · bootstrap.sh** | `./bootstrap.sh` (creates your repo; `--help` for options) | You want a script you can read that also creates your repo. |
| **1 · chezmoi init** | `chezmoi init …` with data prompts | You already have your repo and want to see every file placed. |

Start with your platform's **spoke** for install specifics: `platforms/macos.md`,
`platforms/windows.md`, `platforms/linux.md`, `platforms/raspberry-pi.md`, `platforms/cloud.md`.

## Requirements

**Hard (single node):** git + a git host · **Node.js + npm/npx** (for the AI CLI + most MCP
servers) · an **AI coding CLI + account** (Claude Code = reference) · a config manager
(chezmoi) · a secret store (OS keychain / vault).
**Recommended:** **GitHub CLI (`gh`) + GitHub auth** (lets setup create your repo + lets the
operator manage repos/PRs — *more token scope = more the operator can automate without asking*,
see `guide/09-permissions.md`) · a **backup target** (governance Rule 4 requires backups) · `jq`.
**Hard (multi-node):** a private mesh (Tailscale) · SSH with keys.
**Optional:** **MCP servers** (GitHub, filesystem, … — each a capability grant, `guide/10-mcp.md`)
· a container runtime · an automation runtime · the multi-node coordination layer.

Full detail + matrix in [`GETTING-STARTED.md`](GETTING-STARTED.md), `guide/07-tools-requirements.md`,
and `guide/14-setup.md`.

## Repository layout

```
guide/          # THE HUB — platform-agnostic concepts (read these for the "why")
  _contents        # one-line index of the whole guide
  00-introduction  # ▶ start here: philosophy + the four minimal foundations
  01-concepts · 02-operator · 03-governance-rules · 04-structure · 05-chezmoi ·
  06-secrets · 07-tools-requirements · 08-networking · 09-permissions · 10-mcp ·
  11-agents-skills · 12-multinode · 13-setup · 14-sharing
  15-example-projects · examples/   # worked, end-to-end install+maintenance examples
platforms/      # THE SPOKES — per-OS "how" (macos ✓ · windows ◑ · linux ◑ · raspberry-pi ◑ · cloud ○)
skeleton/       # generic starter files you copy + fill (all placeholders, no secrets)
  CLAUDE.md.template · AGENTS.md.template · chezmoi.toml.example · *ignore templates ·
  env.example · settings/ (3 permission presets) · mcp/ · installers/ ·
  skills/ (2 examples) · onboarding/ (repo seed) · github/ ·
  monitoring/ (health checks, alert mail, update digest — ready to run)
scripts/        # grep-guard (the never-leak backstop) + pre-commit hook
GETTING-STARTED.md # ▶ the front door: intro + requirements + step-by-step
bootstrap.sh    # Tier-2 onboarding (creates YOUR repo; --help for options)
```

## Reading order

1. **`guide/00-introduction.md`** — start here: the philosophy + the four minimal foundations.
2. `guide/01-concepts.md` — the model + vocabulary.
3. `guide/02-operator.md` — how you actually work with the AI operator.
4. `guide/03-governance-rules.md` — the rules that make handing ops to an AI safe.
5. Skim `guide/04`–`14` for the pieces you'll use (`guide/_contents.md` is the one-line index).
6. `guide/16-example-projects.md` — worked, end-to-end examples of owning install + maintenance.
7. Your platform spoke, then a setup tier above.

## A note on safety & sharing

The framework's own disciplines are load-bearing: **zero secrets in git**
(`guide/06-secrets.md`) and — because this is a public repo — **zero personal info**
(`guide/15-sharing.md`), enforced by the `scripts/grep-guard` (pre-commit + CI). If you publish
your own generalized version, use the same guard: derive-don't-copy, and let a fail-closed
scanner be the backstop.

## License

Apache-2.0 — see `LICENSE`.

---

*Contributions especially welcome on the Windows/Linux/Cloud spokes and the per-provider cloud
sections — the hub carries the concepts; the spokes just need the platform specifics filled in.*
