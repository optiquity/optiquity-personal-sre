# 01 · Concepts

What this framework is, the model it assumes, and the vocabulary the rest of the guide uses.
Read this first; every later section builds on it.

## What this is

A **personal-SRE framework**: a way to run your own machines, services, and dotfiles the way
a small ops team runs infrastructure — with an **AI coding CLI** (Claude Code, and optionally
others) as the operator, working under **explicit rules**, against **version-controlled
configuration**, with **every change tracked**.

It is not a program you install. It's a set of **patterns + templates + guides** you adopt and
adapt: a governance model, a repository structure, a config-management flow, a permission
model, and the glue (networking, secrets, MCP) that ties them together. You bring the accounts
and machines; the framework gives you the operating system for running them.

## Who it's for

- You have **more than a handful of machines, services, or dotfiles** and want them managed,
  not just accumulated.
- You use an **AI coding CLI** and want it to *do ops work* — edit configs, run deploys, manage
  a fleet — but only under rules you control.
- You want the whole thing **reproducible, auditable, and recoverable**: what changed, when,
  why, and how to roll it back.

You do **not** need a company, a cloud account, or a background in SRE. A single laptop is a
valid starting point; the model scales up to many nodes without changing shape.

## The core idea: infrastructure-as-a-tracked-conversation

Three things, working together:

1. **An AI CLI as the operator.** It reads your intent, proposes changes, and executes them —
   but it is bound by a **rules file** (see [03 · Governance](03-governance-rules.md)) that
   forces it to pause for approval before anything destructive or outward-facing.
2. **Version-controlled configuration.** Your dotfiles, service configs, and install scripts
   live in git and are applied to each machine by a **config manager** (see
   [05 · chezmoi](05-chezmoi.md)). The repo is the source of truth; machines are derived from
   it.
3. **A tracked project structure.** Every piece of work is a **project** with a status, a plan,
   and a paper trail (see [04 · Structure](04-structure.md)), so the state of your whole system
   is legible at a glance — not carried in your head.

The result: running your machines becomes a **reviewable conversation** with an AI operator,
where the rules and the git history are the audit log.

## Nodes as roles, never names

The single most important modeling choice: **describe machines by the role they play, not by
their identity.**

A **node** is any machine the framework manages. Instead of naming them, you assign each a
**role** that determines what runs on it and how it's configured:

| Role | What it is | Typical traits |
|---|---|---|
| **`workstation`** | Your primary interactive machine | Where you edit, commit, and drive the AI CLI. Often a laptop. |
| **`server`** | An always-on host | Runs 24/7 services, automation, the fleet dashboard. Often headless. |
| **`nas`** | Network storage | Serves files; a backup target. May run a limited OS. |
| **`windows-node`** | A Windows host | Joined for specific workloads; different tooling (see the Windows spoke). |
| *(add your own)* | e.g. `edge`, `builder`, `ci` | Roles are yours to define; the framework only assumes a few defaults. |

**Why roles matter:**
- **Config divergence becomes principled.** "Start containers at login on `server` but not
  `workstation`" is a role rule, not a per-machine hack. The config manager templates on role
  (see [05 · chezmoi](05-chezmoi.md)).
- **The default is symmetry.** Two machines of the same role should be configured the same;
  any divergence is either *unavoidable* (a genuine role difference) or *temporary* (with a
  cleanup noted). This keeps drift visible.
- **It generalizes.** Your setup and someone else's differ in *names and counts*, but the
  *roles* are the same — which is exactly what makes a framework shareable.

Throughout this guide, machines are referred to by role. When you adopt the framework, you map
your real machines onto roles once, in your config data — and never scatter machine names
through configs again.

## The two-repo model

The framework assumes a clean separation between **what's private** and **what's shareable**:

- **Your private repo** — your actual dotfiles, configs, project docs, and status. Contains
  references to your machines, paths, and accounts. **Private, always.** This is where you
  live day to day.
- **(Optional) a public/shared repo** — if you want to publish *your* generalized framework
  (as this one is published), it's a **separate** repo, derived and scrubbed of all personal
  detail. Most users never need this; it exists because sharing the patterns is itself a
  use case.

You only need the first. The distinction matters because it forces the discipline that keeps
**secrets and personal identifiers out of version control from day one** (see
[06 · Secrets](06-secrets.md)) — the private repo is private, but it *still* never contains
secrets, so that if any part is ever shared, the habit is already in place.

## Required vs optional (the shape of an adoption)

You do not adopt everything at once. The framework has a **hard core** and **optional layers**:

**Hard core (single node):**
- **git + a git host** (e.g. GitHub) — the source of truth.
- **A config manager** (chezmoi) — applies the repo to the machine.
- **An AI coding CLI** (Claude Code as the reference) — the operator.
- **A secret store** — your OS keychain or a vault; *never* git.

**Optional layers (add when you have >1 node or want more):**
- **A private network** (Tailscale) + **SSH with keys** — for multi-node operation.
- **A container/automation runtime** — for self-hosted services.
- **The multi-node coordination layer** — session transfer, a fleet-wide dashboard.
- **Monitoring + alerting** — health checks that tell you when something breaks, and a scheduled
  digest of what's fallen behind, delivered by mail ([E16](examples/E16-fleet-health-and-alerting.md)).

A complete requirements matrix (hard/optional × single/multi-node) is in
[13 · Setup](13-setup.md). The point here: **a working adoption can be one machine with four
tools.** Everything else is opt-in.

## Vocabulary (used throughout)

- **Node** — a machine the framework manages.
- **Role** — what a node is *for* (`workstation`, `server`, …); drives its config.
- **The operator** — the AI coding CLI doing the work, under the rules.
- **The rules** — the governance file (a `CLAUDE.md`-style document) the operator must obey.
- **Source of truth** — the git repo; machines are applied *from* it, never edited *into* it.
- **Config manager** — the tool (chezmoi) that renders the repo onto each node by role.
- **Project** — a tracked unit of work with a status, docs, and a paper trail.
- **Registry** — the master index of all projects and their statuses.
- **Dashboard** — an optional single-page, at-a-glance status view rendered from the registry +
  node state (see [04 · Structure](04-structure.md)). It is the **state of record**, refreshed
  when you commit — *not* live health. (A health checker also calls its page a "dashboard"; when
  both are in play, say **registry dashboard** vs **health page**.)
- **Health check** — a probe that asserts a service *works* (status + expected body + timeliness),
  not merely that it answers. "Up but broken" is the failure worth catching.
- **Notify-only** — automation that surfaces work and raises alarms but never mutates a node;
  the safe default for anything running unattended on a timer.
- **Digest** — a scheduled summary email (e.g. what's behind on every node), as opposed to an
  **alert**, which fires on a state change and wants action now.
- **Material / destructive action** — anything hard to undo or outward-facing (a deploy, a
  push, a delete, a service bootstrap); the rules gate these behind approval.
- **Placeholder** — a `<like-this>` token you replace with your own value; the framework's
  templates are full of them, never real values.

## How to read the rest of this guide

- **The hub** (these `guide/` sections) is **platform-agnostic** — concepts and patterns, no
  OS-specific commands, no personal detail.
- **The spokes** (`platforms/macos.md`, `windows.md`, `linux.md`, `cloud.md`) answer *"what's
  the equivalent of this on my platform?"* — install commands, service managers, secret
  stores, paths. They **don't** re-explain concepts; they map them.
- **The skeleton** (`skeleton/`) is the generic starter files you copy and fill.
- **Setup** ([13 · Setup](13-setup.md)) ties it together into a step-by-step (or automated)
  onboarding.

Next: [02 · The operator](02-operator.md) — how you actually work with the AI operator (the
interaction model), then [03 · Governance](03-governance-rules.md) — the rules the operator works under, which is
what makes handing ops work to an AI safe.
