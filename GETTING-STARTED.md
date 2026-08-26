# Getting started

This walks you from zero to a working personal-SRE setup. Read the first two sections before
you do anything — they explain **where you're supposed to work** (a common point of confusion)
and **the fastest path**.

---

## First: the two-repo model (read this)

**This repo — `optiquity-personal-sre` — is a read-only REFERENCE. You do not edit it or commit
to it.** It's the framework: the guide, the templates, the tools.

**Your work happens in YOUR OWN private repo**, which the setup creates for you. That repo holds
your actual dotfiles, configs, project registry, and status — with references to your machines
and accounts, so it is **private, always**.

```
  optiquity-personal-sre   (this repo — READ-ONLY reference; adopt FROM it)
          │  bootstrap / setup creates ↓
  <your-name>/personal-sre (YOUR private repo — where ALL your work happens)
```

If you ever find yourself editing a file inside this framework repo, stop — that change belongs
in your own repo. (More: `guide/01-concepts.md` → "The two-repo model".)

---

## The fastest path (Tier 3): let the AI CLI do it — recommended ⭐

Because this framework is AI-CLI-driven, the quickest setup is to **let the operator set it up
for you** — installing prerequisites, creating your repo, wiring everything — pausing for your
approval at each material step.

**How:**
1. Install an AI coding CLI (Claude Code is the reference — see your platform spoke below) and
   sign in to its account/subscription.
2. Open it **in the directory where you want your own repo to live** (empty is fine — it will
   create/clone *your* private repo there, not touch this framework repo).
3. **Paste the prompt below.** Answer its questions and approve its steps.

> **Two-repo reminder:** when the prompt says "your repo," that's **your own private repo**,
> which the operator creates — not this framework repo (which stays a read-only reference).

**The prompt (copy the whole block):**

```
You are helping me adopt the "personal-SRE framework" on this machine. Act as the operator
described in that framework: do the mechanical work, but PAUSE for my explicit approval before
any material or version-control action (creating a repo, committing, pushing, applying config,
bootstrapping a service, installing software). Reads and drafts are free; changes are gated.

Work through these phases with me, one at a time, confirming before moving on:

1. ORIENT. Ask me: my git host + username; whether this is single- or multi-node; this
   machine's role (workstation/server/nas/other); my OS. Then tell me which platform spoke
   applies and summarize the hard-core requirements (git, Node.js, an AI CLI + account, a
   config manager (chezmoi), a secret store).

2. REPO. Create (or clone) MY OWN private repo — this is where all my work lives; the framework
   repo is a read-only reference I never edit. Confirm the repo name + local directory with me.

3. RULES FIRST. Create a rules file (CLAUDE.md for Claude Code / AGENTS.md for Codex) from the
   framework's template, filled in for my repo and role — in ROLES and PLACEHOLDERS, never
   hard-coding machine names. These rules govern everything you do next, including your approval
   gates. Show it to me and get my ok. Make the initial commit (with my approval).

4. STRUCTURE. Set up the project registry (PROJECTS.md) + a docs/ layout + (optionally) the
   status dashboard skeleton. Explain the status taxonomy.

5. CONFIG MANAGER. Help me install and initialize chezmoi against my repo: set my node's role and
   non-secret data (from chezmoi.toml.example), and explain the dev-clone -> prod-source ->
   pull+apply flow. Do NOT apply anything to the machine without showing me the diff + approval.

6. SECRETS. Set up the ignore files (allowlist/fail-closed pattern) and my secret store for the
   platform, and a runtime env file if needed. Confirm the "zero secrets in git" invariant.
   Never put a secret in a tracked file.

7. PERMISSIONS. Recommend a permission preset for my role (cautious/standard/trusting) and help
   me apply it to the CLI settings. Explain that even "trusting" never auto-approves pushes,
   deletes, deploys, or service bootstraps.

8. (OPTIONAL) NETWORKING, if multi-node: help me generate an SSH key (key-only, no passwords),
   set up the private mesh (Tailscale), and record the SSH access edges I actually need.

9. (OPTIONAL) MCP: ask which external capabilities I need (git host, filesystem, ...) and help me
   configure them from the templates — no tokens in committed config, filesystem scopes limited.

10. FIRST PROJECT. Help me track one real thing I'm working on as a project in the registry with
    a plan doc — to exercise the whole loop.

11. VERIFY. Confirm: you pause before material actions; a secret-scan of my repo finds nothing; a
    config change flows edit->commit->apply->verify without hand-editing the machine; the
    registry answers "what's going on" without me reciting it.

Throughout: use the framework's guide/ sections as your reference for the WHY, and the
platforms/<os>.md spoke for the HOW. When a step is version-control or material, describe
exactly what you'll do and wait for my go. Start with phase 1 now.
```

**Notes:**
- **Claude-first.** The prompt uses Claude Code conventions. For **Codex**, two swaps: the rules
  file is `AGENTS.md`, and permission/MCP config lives in `~/.codex/config.toml` (see
  `skeleton/mcp/codex.mcp.toml`). Where an equivalent isn't obvious, tell the operator to "adapt
  here" — `guide/` is CLI-agnostic. (Config-location table: `guide/11-agents-skills.md`.)
- **The operator honors the gates from step 3 on** — because the first real thing it does is put
  the rules in place. It won't push, apply, or create remote artifacts without your go.

Prefer to run things yourself, or want to understand the machinery? Use **Tier 2**
(`bootstrap.sh`, below) or **Tier 1** (`chezmoi init`). All three reach the same place.

---

## Requirements

Set these up first (or let the AI path / `bootstrap.sh` help). Full detail:
`guide/07-tools-requirements.md`.

### Hard — single node
| Requirement | Why | Notes |
|---|---|---|
| **git + a git host account** (e.g. GitHub) | source of truth | you'll create a private repo |
| **Node.js + npm/npx** | the AI CLI + many **MCP servers** run on Node | install first; several MCP servers launch via `npx` (others are native binaries or Docker — e.g. GitHub's official server) |
| **An AI coding CLI + account** | the operator | Claude Code = reference; needs an Anthropic (or your provider's) account/subscription |
| **A config manager — chezmoi** | renders the repo onto the machine | `guide/05-chezmoi.md` |
| **A secret store** (OS keychain / vault) | runtime secrets, zero-in-git | `guide/06-secrets.md` + your platform spoke |

### Recommended
| Tool | Why |
|---|---|
| **GitHub CLI (`gh`) + GitHub auth** | lets setup create your repo + lets the operator manage repos/PRs. **The more permission you grant the token, the more the operator can automate without stopping to ask you** — a read-only token means it drafts and you push; a token that can create repos / merge PRs means it can do those unattended. Same convenience-vs-blast-radius trade-off as the permission presets (`guide/09-permissions.md`). Grant deliberately. |
| **A backup target** | governance requires "back up before apply" (Rule 4). Decide where — a local dir, an external disk, a NAS — before you apply config. |
| **`jq`** | JSON parsing (handy with `gh` and scripts). |

### Hard — only if multi-node
| Requirement | Why |
|---|---|
| **A private mesh (Tailscale)** | nodes reach each other privately (`guide/08-networking.md`) |
| **SSH with keys** | remote admin, config pull — key-only, no passwords |

### Optional — add per project
- **MCP servers** (high value): each is a **capability grant** — enable only what you need and
  scope it (`guide/10-mcp.md`). For **GitHub**, use the official `github/github-mcp-server`
  (`brew install github-mcp-server` / Docker, PAT auth — or the remote hosted server; **not** the
  deprecated community `@modelcontextprotocol/server-github`). Plus filesystem, docs, browser,
  and more.
- A container runtime · an automation runtime · the multi-node coordination layer.
- **Health checks + alerting** — an SMTP credential (an app password is fine) and a health checker,
  so the system mails you when something breaks or falls behind. Ready to run in
  `skeleton/monitoring/`; narrated in `guide/examples/E16-fleet-health-and-alerting.md`.

---

## Step-by-step (Tier 2 — `bootstrap.sh`)

`bootstrap.sh` sets up **your** private repo and hands off to your AI CLI. It never edits this
framework repo, and it commits nothing.

1. **Install the hard requirements** above (or let bootstrap offer to install the basics).
2. **Run it** (all options have defaults; override via flags or the prompts — `./bootstrap.sh --help`):
   ```sh
   ./bootstrap.sh
   # or fully specified:
   ./bootstrap.sh --repo-name my-sre --dir ~/code/my-sre --role workstation
   ```
   It will: check prerequisites → (if your `gh` auth allows, after a y/N prompt) **create your
   private repo** → **seed it (uncommitted)** with a rules file, a project registry, a starter
   **playbook** (the layered entrypoint), and an onboarding "resume here" doc. If `gh` can't create the repo, it tells you exactly what's
   missing and prints the manual steps — it degrades gracefully.
3. **Continue in YOUR repo.** When bootstrap finishes, open your AI CLI **in the new repo's
   directory**:
   ```sh
   cd <your-new-repo-dir> && <your-ai-cli>
   ```
   The session reads the seeded rules + `PROJECTS.md`, sees the open **onboarding** project, and
   offers the next steps (referencing this guide). Its first proposed action is your **initial
   commit** — approve it to exercise the governed loop.
4. **Finish onboarding** — the session walks you through: first commit → secrets → config
   manager → permissions → (optional) networking/MCP → your first real project. Details live in
   the seeded `docs/onboarding/PLAN.md`.

---

## Verifying you're set up

You're done when:
- The operator reads your rules at session start and **pauses** before material actions.
- A secret-scan of your repo finds **nothing** (`guide/06-secrets.md`).
- A config change flows edit → commit → apply → verify **without hand-editing any machine**.
- Your `PROJECTS.md` answers "what's going on" without you reciting it.
- If you set up alerting: **a deliberately-failed check actually emails you.** Green endpoints
  prove the checks run; only an induced failure proves the *alerting* does.

Full reference: the `guide/` sections (the *why*) and your platform spoke in `platforms/` (the
*how*).
