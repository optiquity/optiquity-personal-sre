# 00 · Introduction — Personal SRE

**Start here.** This is the doorway to the whole framework: first the *philosophy* (why run your
machines this way at all), then the **minimal foundation** that turns an AI coding CLI into a
genuinely useful, unblocked operator for your own systems. Read this, then follow the reading
order at the end.

If you want the concept model in depth, [01 · Concepts](01-concepts.md) is next. If you want to
*do the setup*, [`GETTING-STARTED.md`](../GETTING-STARTED.md) is the procedural front door. This
doc sits between them: the *why*, plus the *minimum that makes it work*.

---

## The philosophy (in one page)

**You run your own machines the way a small ops team runs infrastructure — with an AI coding CLI
as the operator, under explicit rules, against version-controlled configuration, with every
change tracked.**

Three ideas do all the work:

1. **Infrastructure as a tracked conversation.** You state intent in plain language; the operator
   proposes, you approve, it acts, it verifies. The **git history and the rules file are the
   audit log** — what changed, when, why, and who approved it.
2. **Reads are free; changes are gated.** The friction is *asymmetric on purpose*: the operator
   reads, drafts, and investigates with zero friction, but **stops for your approval before
   anything material or outward-facing** (a commit, a push, a deploy, a delete, applying config,
   bootstrapping a service). That asymmetry is what makes handing ops work to a fast, capable AI
   *safe*.
3. **The repo is the source of truth; machines are derived from it.** You edit the repo, never
   the machine. A config manager renders your repo onto each node by its **role** — so your
   whole setup is reproducible, legible, and recoverable, not carried in your head.

The payoff: **leverage** (mechanical ops work happens fast while you stay supervisory),
**safety** (speed never costs you a reviewed-away mistake), and **legibility** (the system's
state is a doc you can read, not tribal knowledge). Deeper: [02 · The operator](02-operator.md).

> **A single laptop is a valid start.** You don't need a company, a cloud account, or an SRE
> background. The model scales from one machine to many *without changing shape*.

---

## The minimal orchestrator: four foundations

To go from "an AI CLI that edits files" to "an operator that genuinely owns your systems and
isn't blocked," you need four things in place. Each below gives the **minimum that works** plus a
link to the section that covers it in full. Get these four right and everything else is opt-in.

### Foundation 1 — Tools (what the operator stands on)

The operator needs a small, concrete toolset. **Minimum for a single node — four things:**

- **git + a git host** (e.g. GitHub) — the source of truth.
- **A config manager (chezmoi)** — renders the repo onto the machine by role.
- **An AI coding CLI + account** (Claude Code is the reference) — the operator itself.
- **A secret store** (your OS keychain or a vault) — runtime credentials, *never* git.

**Add for more than one node:** a **private mesh (Tailscale)** so nodes reach each other
privately, and **SSH with keys** for remote administration. Everything else — a container
runtime, an automation runtime, browser tooling — is added *per project, when needed*, never
preemptively.
→ Full requirements matrix + the installer pattern: [07 · Tools & requirements](07-tools-requirements.md).
Config-as-source-of-truth: [05 · chezmoi](05-chezmoi.md). Networking: [08 · Networking](08-networking.md).

### Foundation 2 — Permissions (what the operator may do, and between which machines)

Two independent permission layers, both deliberate:

- **CLI auto-approve** — your AI CLI's own settings decide what runs *without a prompt*. Start
  with a **preset**: `cautious` (reads only auto-run) → `standard` → `trusting`. Crucially,
  **no preset ever auto-approves a push, delete, deploy, or service bootstrap** — those always
  stop for you. Pick per role: a sit-at `workstation` can be `standard`/`trusting`; an
  unattended `server` should be `cautious`.
- **SSH access between machines** (multi-node) — **key-only, no passwords**, and grant only the
  *edges you actually use* (e.g. `workstation → server`, not every machine to every other). Write
  the intended access graph down; unused access is just risk.

**Minimum:** apply one CLI permission preset (ship-ready in `skeleton/settings/`), and — if
multi-node — set up key-only SSH between the machines that genuinely talk.
→ CLI presets + the two-layer model: [09 · Permissions](09-permissions.md). The SSH access graph:
[08 · Networking](08-networking.md).

### Foundation 3 — Privacy & security (keep secrets and identity out of git)

The load-bearing invariant: **zero secrets in git, ever** — enforced structurally, not by memory.

- **Ignore files, allowlist-style** — for anything near secrets, *deny broadly, allow narrowly*
  so a new file fails **closed** (excluded until you deliberately allow it). Hard-exclude
  `**/.env`, `**/*.key`, `**/*.pem`, `**/id_*`, `**/*.kdbx`, credential dirs.
- **A secret store / vault** — the real values live in your OS keychain or a vault (KeePassXC,
  1Password, `pass`, cloud secret manager). Tracked config references them by name (`${VAR}`);
  the value is resolved at runtime, on the node.
- **(Optional) a scrub guard** — if you ever share a repo publicly, a fail-closed pre-commit/CI
  scanner keeps personal info out too.

**Minimum:** copy the ignore templates (`skeleton/gitignore.template`,
`skeleton/chezmoiignore.template`), wire your platform's secret store, and confirm a secret-scan
of your repo finds nothing.
→ The full discipline + the `.env`/keychain recipes: [06 · Secrets](06-secrets.md). Sharing safely:
[16 · Public/shared repos](16-sharing.md).

### Foundation 4 — Rules (how the operator stays grounded and knows when to ask)

This is what keeps a fast AI operator *safe and on-priority*. The operator reads a **rules file**
(`CLAUDE.md` / `AGENTS.md`) at the start of every session; those rules are the first thing set up,
so everything after happens under governance.

The rules encode the **grounding principles**:

- **Ask before anything material** — applying config, deleting non-backed-up files, creating
  remote artifacts, bootstrapping a service, any state-changing remote command.
- **Ask before any version-control change** — *including* `git add`; the human sees what enters
  history before it does.
- **Back up before you apply.** **Default to symmetry** across same-role nodes. **Status lives in
  tracked docs, not memory.** **Preview the next steps before a commit.** **Re-read the rules
  before committing.**

You set the *strictness* to your risk tolerance, but the shape is fixed: **reads and drafts flow;
consequential changes stop for a human.**

**Minimum:** put a rules file in place (from `skeleton/CLAUDE.md.template`) *first*, tuned to your
repo and role. Everything the operator does thereafter respects it.
→ The full rule set + the *why* behind each: [03 · Governance](03-governance-rules.md). The
interaction rhythm: [02 · The operator](02-operator.md).

---

## How the four fit together

```
   Foundation 4: RULES ........ the operator pauses at the right moments (judgment)
   Foundation 2: PERMISSIONS .. the CLI + SSH bound what it *can* do (capability)
   Foundation 3: PRIVACY ...... secrets/identity can't leak (structural)
   Foundation 1: TOOLS ........ git · config-manager · AI CLI · secret store (the ground)
```

Defense in depth: even if one layer slips, another catches it. The rules say *pause*; the
permission layer makes it *pause*; the ignore files make a secret *un-committable*; the config
manager makes every change *reproducible*. No single layer has to be perfect.

---

## What "done" looks like (the minimal, unblocked orchestrator)

You have a genuinely useful, unblocked personal-SRE operator when:

- The operator **reads your rules at session start** and **pauses before material actions**.
- A **secret-scan of your repo finds nothing** — the privacy invariant holds by construction.
- A config change flows **edit → commit → apply → verify** without hand-editing any machine.
- Your **project registry answers "what's going on"** without you reciting it from memory.

That's the whole minimum. From here you add nodes, services, skills, and automation *as real
projects need them* — never preemptively.

---

## Reading order

1. **This doc** — the philosophy + the four foundations.
2. [01 · Concepts](01-concepts.md) — the model + vocabulary in depth.
3. [02 · The operator](02-operator.md) — how you actually work with the operator.
4. [03 · Governance](03-governance-rules.md) — the rules that make it safe.
5. Skim [04](04-structure.md)–[14](16-sharing.md) for the pieces you'll use; see
   [`_contents.md`](_contents.md) for the one-line index.
6. Worked, end-to-end examples of the operator owning install *and* maintenance:
   [17 · Example projects](17-example-projects.md).
7. Then your platform spoke (`platforms/<os>.md`) and a setup tier in
   [`GETTING-STARTED.md`](../GETTING-STARTED.md).
