# 15 · Setup — the onboarding journey

> **Doing setup right now?** Start with **[`GETTING-STARTED.md`](../GETTING-STARTED.md)** — the
> practical front door (intro, requirements, step-by-step, and the paste-in AI-setup prompt).
> This section is the *conceptual* companion: the model behind the onboarding tiers and the
> journey they share.

This section ties the whole framework together into an **adoption path**: what to do, in what
order, to go from nothing to a working personal-SRE setup. It offers **three tiers** of
onboarding so you can pick your comfort level, all converging on the same end state.

The concepts are here; the **platform-specific commands** (how to install each tool on your OS)
are in the spokes — this section tells you *what* to do and points you to the right spoke for
*how*.

## The end state you're building toward

A minimal but complete **single-node** adoption:

- A **private git repo** that is your source of truth.
- A **config manager** (chezmoi) rendering that repo onto your machine by role.
- An **AI CLI** (the operator) configured with your **rules file**, **permission preset**, and
  any **MCP servers** you need.
- A **secret store** wired up, with **zero secrets in git**.
- Your first **project** tracked in the registry.

From there, multi-node ([12](13-multinode.md)) and optional layers are additive.

## The requirements checklist (before you start)

Confirm you have or will set up:

**Hard (single node):** git + a git-host account · a config manager · an AI CLI · a secret
store. (Full matrix in [07 · Tools](07-tools-requirements.md).)

**Hard (only if multi-node now):** a private mesh (Tailscale) · SSH keys.
([08 · Networking](08-networking.md).)

**Decisions to make up front:** your **roles** (map your machine[s] to `workstation` /
`server` / etc. — [01 · Concepts](01-concepts.md)); your **permission posture** per role
(cautious / standard / trusting — [09](09-permissions.md)); which **MCP servers** you'll enable
([10](10-mcp.md)).

## Tier 1 — guided by the config manager (`chezmoi init`)

The most hands-on-but-transparent path: initialize the config manager against the framework
skeleton, and let its **data prompts** collect your specifics.

1. Install the config manager (see your platform spoke).
2. Point it at the skeleton / your new repo. On init, it **prompts** for your data — your role,
   your git-host username *(placeholder-filled, not hardcoded)*, your tailnet name if any, etc.
   — and writes them to a **local, untracked** data file.
3. It renders the skeleton files (rules, permission preset, ignore files, installer) for your
   node, filling every placeholder from your answers.
4. Review the diff, apply ([05 · chezmoi](05-chezmoi.md)'s gated apply), verify.

You see exactly what's placed. Good if you want to understand the machinery as you go.

## Tier 2 — the bootstrap script (`bootstrap.sh`)

A single interactive script that **checks and sets up prerequisites**, then hands off to Tier 1.
The framework ships `bootstrap.sh` (POSIX, in the skeleton root):

1. **Detects your platform** and points you at the right spoke.
2. **Checks prerequisites** — git, the config manager, the AI CLI, (optionally) Tailscale and
   SSH keys — and offers to install what's missing (via the platform's package manager).
3. **Helps generate an SSH key** and explains the mesh setup, if you're going multi-node.
4. **Offers to run `chezmoi init`** (Tier 1) to finish.

Good if you want the prereqs handled for you but still like a script you can read. It installs
nothing without asking, and it's idempotent — safe to re-run.

## Tier 3 — set up *with the operator* (recommended)

The most on-brand path: since the framework is AI-CLI-driven, you can have the **operator set
itself up**, conversationally. `GETTING-STARTED.md` carries a **canned prompt** you paste into
the AI CLI:

1. Install the AI CLI (your platform spoke) and open it in an empty directory.
2. Paste the setup prompt. It instructs the operator to read the framework's guide, ask you the
   handful of decisions (roles, posture, MCP), and walk you through creating the repo, wiring
   the config manager, setting up secrets, and tracking your first project — **pausing for your
   approval at every material step** (per the governance rules the setup itself establishes).
3. You answer questions and approve steps; the operator does the mechanical work.

Good if you'd rather converse than run commands. The setup prompt is **Claude-first**; a Codex
variant is noted where it differs. Even here, the operator honors the gates — it won't push,
apply, or create remote artifacts without your explicit go, because those rules are the first
thing it puts in place.

## All three converge

Whichever tier you pick, you end at the same place: a working single-node setup with the repo,
config manager, operator (rules + permissions + MCP), and secret store in place. The tiers
differ only in **how much is automated vs. explained** — not in the result. You can even mix
them (bootstrap the prereqs with Tier 2, finish with the operator via Tier 3).

## After the minimal setup

Recommended next steps, in rough order:

1. **Track your first real project** ([04 · Structure](04-structure.md)) — pick something you're
   actually doing; put it in the registry with a plan doc. This exercises the whole loop.
2. **Tune your rules** ([03](03-governance-rules.md)) — adjust the template `CLAUDE.md` to your
   risk tolerance now that you've felt the defaults.
3. **Stand up the dashboard** ([04](04-structure.md)) — once you have a few projects, the
   at-a-glance view earns itself.
4. **Add a second node** ([13 · Multi-node](13-multinode.md)) — bring the mesh + SSH online,
   map the new node to a role, apply.
5. **Add optional tools** ([07](07-tools-requirements.md)) — a container runtime, automation,
   browser skills — as specific projects need them, never preemptively.
6. **Stand up health checks + the update digest** ([E16](examples/E16-fleet-health-and-alerting.md))
   — the point at which the system starts telling *you* things instead of waiting to be asked.
   `skeleton/monitoring/bootstrap-monitoring.sh` installs the tools and seeds the config; you add
   an SMTP credential and your node list. Worth doing as soon as anything runs unattended.

## Verifying your setup

You're set up correctly when:

- The operator reads your rules at session start and **pauses** before material actions.
- `git status` is clean of anything sensitive; a secret-scan of the repo finds **nothing**
  ([06 · Secrets](06-secrets.md)).
- A config change flows edit → commit → apply → verify without hand-editing any machine.
- Your registry answers "what's going on" without you reciting it from memory.
- **A deliberately-broken check actually emails you.** If you've set up alerting
  ([E16](examples/E16-fleet-health-and-alerting.md)), point a check at something guaranteed to
  fail, confirm the mail lands, then remove it. A page full of green endpoints proves the
  *checks* run; only an induced failure proves the *alerting* does.

If those hold, the framework is working as intended: your system is version-controlled,
governed, legible, operated by an AI you've bounded — and it tells you when something breaks.

Next: [16 · Public/shared repos](16-sharing.md) — if you want to publish your own generalized
framework (as this one is), how to do it without leaking anything.
