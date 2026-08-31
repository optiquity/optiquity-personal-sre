# 05 · chezmoi — config as the source of truth

The framework treats your git repo as the **single source of truth** for machine
configuration, and applies it to each node with a **config manager**. The reference tool is
**chezmoi**. This section covers the model — the flow, roles, templating, and the safety
discipline — platform-agnostically. Install commands and per-OS paths are in the spokes.

> Why chezmoi specifically: it's cross-platform, templating-native (so one repo configures
> many roles), secret-aware (it integrates with password managers instead of storing
> secrets), and it treats *apply* as an explicit, diff-able step. Other managers (yadm,
> bare-git dotfiles, Ansible) can fill the same slot; the *model* below is what matters.

## The principle: machines are derived, never authored

The cardinal rule: **you edit the repo, not the machine.** A node's live config is a
*rendering* of the repo for that node's role — never the place you make changes. If you edit a
file on a machine directly, you've created drift the config manager will either overwrite or be
confused by.

This inverts the usual dotfiles habit ("I'll just tweak `~/.zshrc` on this box"). Under the
framework, that tweak goes into the repo, is committed, and is *applied* — so every machine
stays a faithful, reproducible projection of version-controlled truth.

## The three-tier flow

Config moves through three stages. Keeping them distinct is what makes the system safe and
multi-machine:

```
   ┌─────────────────────────────────────────────────────────────┐
   │  1. SOURCE OF TRUTH  —  the git host (e.g. GitHub)           │
   │     the canonical repo; every node syncs from here          │
   └───────────────┬─────────────────────────────┬───────────────┘
                   │                             │
        ┌──────────▼──────────┐       ┌──────────▼──────────┐
        │  2. DEV CLONE       │       │  3. PROD SOURCE     │
        │  where you EDIT     │       │  per node; the      │
        │  + commit + push    │       │  config manager     │
        │  (config mgr never  │──────▶│  reads THIS; apply  │
        │   reads this)       │  pull │  renders it live    │
        └─────────────────────┘       └─────────────────────┘
```

1. **Source of truth** — the repo on your git host. Canonical.
2. **Dev clone** — a normal clone where you make edits, commit, and push. The config manager
   **does not** read this; it's just your editing workspace. (Often on your `workstation`.)
3. **Prod source** — on *each* node, the config manager's own source directory. Updating a node
   is: **pull** the latest from the git host into its prod source, then **apply**.

**Why separate the dev clone from the prod source?** So editing never risks a live machine.
You edit and push freely in the dev clone; a node only changes when you deliberately pull +
apply into *its* prod source. The two never collide.

A node update is therefore two explicit steps — `pull`, then `apply` — and (per governance
[Rule 1](03-governance-rules.md)) the **apply is gated**: it changes live state, so it's
preceded by a backup and a diff you approve.

## Roles, not hostnames

[Concepts](01-concepts.md) introduced nodes-as-roles; this is where roles do their work. The
config manager templates files on a **role variable** you set per node, so one repo renders
correctly everywhere:

```
# conceptually, in a templated config file:
{{ if eq .role "server" }}
  # always-on: start background services at login
{{ else if eq .role "workstation" }}
  # interactive: services on-demand only
{{ end }}
```

Set the role once, in each node's **config-manager data** (a small local file — see the
skeleton's [`chezmoi.toml.example`](../skeleton/chezmoi.toml.example)), never scattered through
the configs — and pair it with [`chezmoiignore.template`](../skeleton/chezmoiignore.template),
which lists what the manager must never apply. Then:

- A file that's identical everywhere is just a plain managed file.
- A file that differs by role uses a role template.
- Adding a new node of an existing role requires **zero** new templating — it inherits its
  role's rendering.

This is [Rule 7](03-governance-rules.md) (default to symmetry) made mechanical: same role →
same render, by construction. Divergence has to be *written as a role condition*, which forces
it to justify itself.

## When a node runs a different OS

Roles carry you a long way, but they assume every node can *render the same tree*. Add one node on a
different operating system and that assumption breaks hard: a source repo grown on macOS or Linux is
usually **overwhelmingly** that OS — shell rc files, dotfile directories, scripts in `~/.local/bin` —
and pointing the config manager at it from the odd node out will cheerfully try to create all of it
there.

The failure is not subtle, but it *is* easy to walk into, because nothing warns you. The manager has
no idea those files are meaningless on the new platform.

**Partition the source explicitly, and make it default-deny in both directions:**

```
{{- if eq .chezmoi.os "windows" }}
*                    # ignore everything…
!Scripts             # …except the paths that are for this OS
!Scripts/**
{{- else }}
Scripts              # and elsewhere, ignore those
Scripts/**
{{- end }}
```

Two properties matter more than the syntax:

- **Both branches are explicit.** A partition that only guards the new OS leaves the original nodes
  quietly picking up files meant for the newcomer. Say what each side ignores.
- **The majority OS keeps its exact previous behaviour.** This is the bit to verify rather than
  assume: capture the managed-file list *before* the change, and diff it after. If the list and its
  pending changes are byte-identical, the partition is inert for existing nodes — which is the only
  evidence that matters, because a mistake here breaks machines that were working fine.

**Expect the per-node data file to need attention too.** Templates that reference a variable — a role,
a hostname, a flag — fail on any node where that variable was never defined, and the error surfaces
as a template failure long before anything is applied. The new node needs its own data file with the
same keys the others have, even where the values differ.

**A caution on scope.** Partitioning the source is a change to a file *every* node depends on, so it
earns a deliberate pass of its own — not a rider on unrelated work. It is also worth asking whether
the odd node needs the config manager at all: if it runs two scripts and a service, version-controlling
those files may be the whole requirement, and wiring up full config management is effort spent on a
capability nobody asked for.

## What the config manager should manage

- **Dotfiles** — shell config, editor config, CLI configs, the AI-operator's config/rules.
- **Install scripts** — idempotent, role-aware scripts that ensure required tools are present
  (see [07 · Tools](07-tools-requirements.md)). The config manager runs these on apply.
- **Service definitions** — the *files* that define background jobs (the plist/unit/task); the
  config manager places them, but **bootstrapping** the service is a separate, gated action
  (governance Rule 1).
- **Its own data model** — the role definitions and per-node knobs.

## What it should NOT manage

- **Secrets.** The config manager places *config*, not credentials. Secrets come from a
  keychain/vault at apply-time via references, never as stored values (see
  [06 · Secrets](06-secrets.md)).
- **Large or machine-generated state** — caches, build output, databases. Manage the *config*
  that produces them, not the artifacts.
- **Anything you can't regenerate or that isn't yours to version** — one-off local knobs can
  stay unmanaged; document that they're intentionally out of scope.

## The apply discipline (safety)

Because *apply* is the one step that changes a live machine, it gets the most care —
encoded as governance rules:

1. **Pull first, deliberately.** Bring the node's prod source up to date from the git host as
   an explicit step, so you know exactly what you're about to apply.
2. **Back up before applying** ([Rule 4](03-governance-rules.md)) — a timestamped snapshot of
   what apply will touch, so a bad render is reversible.
3. **Diff, then apply** — review the config manager's dry-run diff (a read, always free), and
   only then apply. The apply itself is **gated on approval** ([Rule 1](03-governance-rules.md)).
4. **Verify after.** Confirm the node behaves (services up, mounts present, tools resolve).
   Applied ≠ working.

Prefer a **manual pull+apply** you drive over a fully automatic background sync, at least
until you trust the setup — automatic apply removes the human from the one step that changes
live state.

### If you do automate the apply

A scheduled sync is reasonable once the setup is proven, and it needs three things the manual
workflow gets for free:

- **Force non-interactivity explicitly.** This is the one that will actually break you. Config
  managers *prompt* when a managed file was changed by something other than themselves —
  *"has changed since I last wrote it: diff / overwrite / skip / quit?"* With nobody to answer, the
  job does not fail; it **waits forever**, and typically holds the tool's **state lock** while it
  does, so every later invocation blocks too. The schedule then re-fires and wedges again. Pass the
  explicit no-terminal flag rather than trusting the tool to notice there is no terminal.
- **Decide the conflict policy up front, and log it.** *"Plain apply, reconcile by hand later"*
  sounds careful but is what produces the hang above. Since the model is **machines are derived,
  never authored**, letting the source win is consistent — but **record every overwrite**, because a
  hand-edit on a node is an anomaly worth seeing rather than erasing silently.
- **Verify what landed, not just that it landed.** Unreviewed changes now reach every node within one
  interval, and a script with a syntax error is written to disk perfectly happily — it fails only when
  something *runs* it, which may be days later and far from the cause. Syntax-check what you applied
  and surface failures where you will read them. *"The file was written"* is not *"the file works"* —
  the same distinction as *"the process ran"* versus *"the work happened"* ([14 · Monitoring](14-monitoring.md)).

## Handling drift

**Drift** is when a node's live files differ from what the repo would render — usually because
something (you, an app, an installer) edited a file directly. The config manager can *show*
drift (a status/diff command — always a free read). When you find it, decide per file:

- **Capture** — the change was good; pull it back into the repo (re-add), commit, so it
  becomes canonical.
- **Revert** — the change was unwanted; re-apply from the repo to overwrite it.
- **Leave** — intentionally machine-local; document it as out-of-scope.

A periodic "check drift" pass (a read across your nodes) keeps surprises small. Drift you never
look at is drift that eventually breaks an apply.

## Adopting incrementally

You don't chezmoi-manage everything on day one. Start with a few high-value files (shell
config, the AI-operator rules), get the pull→apply→verify loop comfortable on one node, then
bring more under management as trust grows. A file is either managed (in the repo, rendered) or
explicitly unmanaged (documented) — avoid the murky middle of "sort of managed."

Next: [06 · Secrets](06-secrets.md) — the never-in-git discipline that lets the config manager
place credential *references* without any secret ever touching the repo.
