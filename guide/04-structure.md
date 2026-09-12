# 04 · Structure — projects, the registry, and the dashboard

Governance Rule 8 says *status lives in tracked docs, not memory*. This section defines where.
The framework organizes all work into **projects**, indexed by a **registry**, and optionally
surfaced through a **status dashboard** — so the state of your whole system is legible without
holding it in your head.

## Everything is a project

A **project** is a tracked unit of work — a migration, a service you're standing up, a tool
you're adopting, a recurring maintenance thread. Each project is a folder:

```
docs/
  <project-name>/
    PLAN.md          # the plan + running status (or STATUS.md, SETUP.md — your call)
    ...              # any supporting design/reference docs
```

Projects are **the unit of organization and the unit of memory**. When the operator finishes a
migration, the record isn't in the chat — it's in `docs/<project>/PLAN.md`, with what was
done, verified, and deferred. Six months later, that folder answers "what did we do and why."

## Where files live — mechanism, not topic

Projects organize *work*. They do not organize *files*, and conflating the two is how a repo
turns into a pile of top-level directories nobody can classify.

**Name each top-level directory for its mechanism — what happens to files in here — not for
its topic.** Topic lives one level down, named after a registry entry.

| Mechanism | Typical name |
|---|---|
| **deployed to a machine** | `home/` — the config manager's source tree |
| **read by a human** | `docs/`, `guide/` |
| **run by the repo itself** | `scripts/` — hooks, guards, checks that never leave the repo |
| **generated, never hand-edited** | a clearly-named output dir, gitignored or committed deliberately |

⚠ **In a config manager's source tree, the source layout *is* the destination layout.** A
top-level directory in the source maps to a top-level directory in `$HOME`. That axis is
already spoken for, so it cannot also carry your topic grouping — and if you put the source
tree at the repo root, every deployment target becomes a top-level directory that looks
exactly like a project folder and is nothing of the kind.

The fix is a **source-root marker**: chezmoi reads `.chezmoiroot`, and a single line naming a
subdirectory confines the whole managed tree to it. Everything else in the repo becomes
invisible to the config manager, and the root is yours again.

⚠ **Migrating to one is where this bites, and it bites twice.**

**The marker is read at startup, before the tool pulls.** A combined "pull and apply" command
resolves the source root *first*, so the very run that introduces the marker still applies with
the **old** root — and your new subdirectory is treated as a *destination* directory. You get a
full duplicate tree at `~/<subdir>/`. On the migration run only, **pull and apply as two
separate commands**; every run after that is fine. Anything on a schedule needs the same care:
pull ahead of it, or pause it until the marker has landed.

**And a pull moves only *tracked* files.** Untracked or ignored ones — staged config awaiting a
decision, caches, anything a machine generated locally — stay at the old root, where the ignore
file that used to cover them no longer reaches. Check *every* machine for leftovers, not just
the one you did the work on, and keep root-anchored ignore patterns for anything
config-manager-shaped so a stranded file cannot become committable.

⚠ **A project's docs and its deployables cannot be co-located, and you should stop trying.**
A service you run has design docs *and* a deployment directory that must land at a specific
path. Nesting them under one project folder changes where it deploys. Tie them together in the
**registry** instead — give each project a `Deploys:` line naming what it owns. The registry
is already the index; let it carry this too.

⚠ **Ignore files are anchored by position, and moving one silently changes what it matches.**
Any `.gitignore` pattern containing a slash is relative to the directory holding that file. A
cascade like `config/*` followed by `!config/keep-this/` stops matching the moment the tree
moves beneath it — and it fails *open*, quietly widening what can be committed. Prefer moving
the ignore file **with** the tree it describes over rewriting its patterns, and keep repo-wide
defences (`**/`-anchored secret and junk patterns) in a separate root-level file so they still
cover the docs tree.

**What to write down:** one table in your `README.md` saying what each top-level directory
means, and the `Deploys:` field in the registry. Both are short. The reason they earn their
keep is that six months later "where does this go?" has one answer instead of a judgement call.


## The registry — one index of everything

A single file at the repo root — call it `PROJECTS.md` — is the **master index**: every
project, its status, a one-line summary, its related projects, and its docs. It's the entry
point to the whole system.

```markdown
## <project-name> — **<status>**
**Folder:** `docs/<project-name>/` · **Related:** <other-projects>
<One paragraph: what it is, where it stands, what's left.>
- `PLAN.md` — **<status>** (<short note>)
```

The registry is **authoritative**. If a doc and the registry disagree, the registry wins and
the doc is reconciled to it. This gives you one place to look and one place to trust.

## Status taxonomy

A small, fixed vocabulary keeps statuses meaningful across every project:

| Status | Meaning |
|---|---|
| **pending** | Approved/intended, not started. |
| **open** | Actively in progress. |
| **stable** | Works as-is; nothing to do now, but scope may grow. |
| **resolved** | Done and closed; no expected further work. |
| **deprecated** | Being phased out. |
| **superseded** | Replaced by another project (see its Related). |
| **cancelled** | Abandoned. |

Track status **per project and per doc** — a project can be `open` while one of its sub-docs is
`resolved`. The distinction between `stable` and `resolved` matters: `stable` invites future
growth ("the base config works, but I'll add to it"); `resolved` is closed.

## Why this structure earns its keep

- **Legibility.** The registry is a one-screen answer to "what is going on across everything."
- **Memory that survives sessions.** Rule 8's requirement has a home; nothing important lives
  only in a conversation.
- **Onboarding (including the operator's).** A new session — or a new person — reads the
  registry and the relevant `docs/<project>/` and is caught up, without you re-explaining.
- **Honest deferral.** Rule 9's "no silent deferral" works because deferred items land in a
  project doc with a reason and a when.

The overhead is real but small: a folder and a registry row per project, updated as work moves.
The payoff is never again wondering what state something is in.

## The dashboard (optional, recommended)

For a system of any size, a **status dashboard** turns the registry + project docs into a
single at-a-glance view. The framework's pattern is a **single self-contained HTML page** —
one file, no server, no build step, no external dependencies — driven by a **data block** you
edit.

### The shape

- One HTML file with a `DATA` object at the top (the single source of truth) and render logic
  below it. **You edit only the `DATA` block**; the rendering is mechanical.
- It renders: an **overview** of all projects grouped by status; a **detailed page per active
  project**; a page per **node**; and a page for the **config-management foundation**.
- Self-contained so it can be opened anywhere (a file, an artifact host, an internal page) with
  no infrastructure.

### Two page formats

The dashboard deliberately uses **two different formats**, because a plan and a machine are
different kinds of thing:

1. **In-flight project pages = a phased runbook.** For each active project: `phases` →
   numbered `steps` → per-step `detail` + `evidence` → per-phase `gate` / `rollback` /
   `warning`. Depth reflects **reality** — a deep migration has many verified-evidence phases;
   a barely-started project honestly has two thin ones. **Never invent phases or fake evidence
   to look further along.** The value is seeing true progress and true remaining work.
2. **Node + foundation pages = stateful, not a plan.** No phases — these show **current state
   at a glance**: a status header, per-service **status pills** (running / on-demand / passive
   / stopped / gated), verified "as of" dates on measured facts, and — for config management —
   an adoption matrix and a divergence ledger (Rule 7's unavoidable-vs-temporary splits). Live,
   drifting figures (free space, backup size) appear only as **dated snapshots** under a
   drift note — never as fake real-time health.
   - Each node page also carries a **static hardware inventory** — CPU (cores, plus any
     performance/efficiency split), GPU and other accelerators (a Neural Engine, a discrete
     card), total memory, internal **and** external/expansion storage (capacity + layout), and
     OS. It's the reference you reach for when sizing work or diagnosing, so keep it complete.
     **Query it from the host itself, never guess** (`system_profiler`/`diskutil` on macOS,
     `lscpu`/`lsblk` on Linux, `systeminfo`/`Get-CimInstance` on Windows, `/sys/block` +
     `/proc/mdstat` for a NAS array). Stamp the whole block with a single "as of" date and
     refresh it only when the hardware actually changes (a RAM or disk upgrade, an OS bump) —
     it belongs **with state, distinct from the drifting snapshots**, precisely because it
     rarely moves.

### Keeping it honest and current

The dashboard is only useful if it's **true**, so make refreshing it **deterministic**:

- **Refresh trigger:** any change that moves a project's status, adds/removes a project, or
  advances an in-flight thread (a step's state, a new phase, new evidence, a gate flip)
  **refreshes the dashboard in the same commit** as that change. Tie this to a governance rule
  so it isn't optional.
- **Reality, not padding:** the dashboard mirrors the registry and the real project docs. It
  never shows more progress than exists.
- **The registry is still the source of truth** — the dashboard is a view of it, reconciled to
  it when they differ.

If you build one, keep it to a single self-contained page with one `DATA` block as its only
source of truth, and record the refresh procedure alongside it so it's reproducible. Treat it as
the **state of record** — what you and the operator agreed is true — not as live health: dated
snapshots are not a monitor. For live up/down and alerting, see
[E16 · Health & alerting](examples/E16-fleet-health-and-alerting.md).

## The playbook — where the operator starts

The registry, the runbooks, the guide, and the dashboard each answer a different question. When you
(or the operator) sit down to actually *do* or *fix* something, you need a **single front door** that
routes you to the right one. That's the **playbook** — a thin **`PLAYBOOK.md`** at the repo root.

It is deliberately a **hub, not a home for content** — a map that links out and in, so it never goes
stale:

- **Which doc for what** — a short table: procedure → the project's runbook; known problem → the
  troubleshooting index; concept → the guide; status → the registry; live state → the dashboard.
- **Layered sections, not one flat list** — index **every** project, grouped by purpose/level rather
  than dumped in a single list: *hardware → foundation (cross-cutting: config management, the mesh,
  container runtime, the dashboard) → networking → servers/hosts → storage → monitoring →
  applications*. Add or drop layers to fit your system; the point is that someone scanning for "the
  monitoring stuff" or "the networking stuff" lands in one place. A per-host "what runs where" section
  complements the layers.
- **A troubleshooting index** — the highest-value part: a growing "seen this symptom?" table where
  each row points to the doc that fixed it. Seed it from this guide's documented **traps**, then add
  a row every time you solve something non-obvious. This is what turns scattered fixes into a
  reference someone can actually search.
- **External references** — the upstream vendor docs for every tool you run, so the operator links
  out to the current source instead of trusting stale memory.

Keep it thin on purpose: content lives in the runbooks and the guide; the playbook only *routes*.
The distinction from the registry matters — the **registry says what state a thing is in; the
playbook says how to do or fix it.** The framework ships a **starter `PLAYBOOK.md`**
(`skeleton/onboarding/`); you copy it to your root and grow the three tables as you build, your first
project supplying the first real rows.

## Scaling down and up

- **One machine, three projects?** You still benefit: the registry is your to-do-with-context,
  and the per-project docs are your memory. Skip the dashboard until it earns itself.
- **Many nodes, many services?** The structure doesn't change shape — more rows in the
  registry, more folders under `docs/`, more pages on the dashboard. That invariance is the
  point: the same organizational model works from a laptop to a fleet.

Next: [05 · chezmoi](05-chezmoi.md) — the config manager that makes the repo the source of
truth and applies it to each node by role.
