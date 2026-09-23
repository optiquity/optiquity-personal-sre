# 18 · Setup — the onboarding journey

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

From there, multi-node ([12](16-multinode.md)) and optional layers are additive.

## The requirements checklist (before you start)

Confirm you have or will set up:

**Hard (single node):** git + a git-host account · a config manager · an AI CLI · a secret
store. (Full matrix in [07 · Tools](07-tools-requirements.md).)

**Hard (only if multi-node now):** a private mesh (Tailscale) · SSH keys.
([08 · Networking](08-networking.md).)

**Decisions to make up front:** your **roles** (map your machine[s] to `workstation` /
`server` / etc. — [01 · Concepts](01-concepts.md)); your **permission posture** per role
(cautious / standard / trusting — [10](10-permissions.md)); which **MCP servers** you'll enable
([11](11-mcp.md)).

## Tier 1 — by hand, with the config manager

The most hands-on-but-transparent path: you place every file yourself.

1. Install git and the config manager (see your platform spoke), and create + clone your
   **private** repo.
2. Copy in the skeleton files you want: the rules template (`skeleton/CLAUDE.md.template` or
   `AGENTS.md.template`), the ignore templates, a permission preset (`skeleton/settings/`), the
   installer template, and the design + postmortem practice (`skeleton/design/`,
   `skeleton/postmortems/`). **Fill every `<placeholder>` yourself** — roles and placeholders,
   never real machine names in anything you might publish.
3. `chezmoi init` with your repo as the source, then put this node's role and non-secret data in
   chezmoi's **local, untracked** config: `skeleton/chezmoi.toml.example` shows the keys. The
   framework ships no `.chezmoi.toml.tmpl`, so `init` does not prompt. The example's last section
   shows how to add prompts if you want them.
4. Review the diff, apply ([05 · chezmoi](05-chezmoi.md)'s gated apply), verify.

You see exactly what's placed. Good if you want to understand the machinery as you go.

## Tier 2 — the bootstrap script (`bootstrap.sh`)

A bash script at the framework's root that **creates and seeds your repo**, then hands off to
your AI CLI (Tier 3) to finish. It does, in order:

1. **Detects your platform** and points you at the right spoke.
2. **Checks prerequisites.** It requires git and chezmoi, and on macOS with Homebrew offers to
   install them. It notes whether `gh`, node and the AI CLI are present. It does not set up SSH
   keys or the mesh: those are onboarding steps, later.
3. **Creates your private repo** with `gh`, if your auth has the `repo` scope, after a y/N
   prompt. Otherwise it prints the manual steps. **Already cloned one?** Run it with
   `--no-create-repo --dir <your-clone>`, and it uses the clone as-is.
4. **Seeds the repo, uncommitted.** It writes a rules file, `PROJECTS.md`, `PLAYBOOK.md`, the
   design + postmortem practice, the onboarding project's own design doc and postmortem draft,
   peer messaging, and a "resume here" plan. It **never overwrites a file that already exists**;
   it lists what it kept.
5. **Hands off.** It tells you to open your AI CLI in the new repo, which resumes from the plan.

It commits and pushes nothing, and it is safe to re-run. Installs and repo creation ask first —
**except under `--yes`, which answers yes to both.** Use `--yes` only for a run whose effect you
already know.

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
4. **Add a second node** ([16 · Multi-node](16-multinode.md)) — bring the mesh + SSH online,
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

Next: [19 · Public/shared repos](19-sharing.md) — if you want to publish your own generalized
framework (as this one is), how to do it without leaking anything.
