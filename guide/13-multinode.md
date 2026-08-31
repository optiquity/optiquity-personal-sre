# 13 · Multi-node operations (advanced)

Everything so far works on a single node. This section is the **optional advanced layer**: how
the operator works effectively across *several* nodes at once — inventory, remote apply,
running the operator on more than one machine, and coordinating between them. Skip this until
you have multiple nodes and feel the need; a single-node setup is complete without it.

## When you actually need this

You don't graduate to multi-node ops just because you have two machines. You need this layer
when:

- You want to **administer nodes remotely** from your `workstation` (drive the `server`, check
  the `nas`) rather than sitting at each.
- You **run the operator on more than one node** and want them to not collide.
- You have **services spread across nodes** whose state you want to see and manage centrally.

Below that threshold, "multi-node" is just "I occasionally SSH somewhere" — which the
[Networking](08-networking.md) layer already covers.

## Remote inventory and apply

The foundation (from [Networking](08-networking.md) + [chezmoi](05-chezmoi.md)): the operator,
from your `workstation`, reaches other nodes over the private mesh + SSH and:

- **Inventories them read-only** — what's installed, running, mounted, how much space. Reads
  are free ([Rule 10](03-governance-rules.md)), so the operator can build an accurate picture
  of every node before proposing anything.
- **Pulls + applies config remotely** — updates a node's prod source and applies, with the
  **apply gated** ([Rule 1](03-governance-rules.md)) exactly as if local. A remote apply is
  still a live change; it still gets a backup, a diff, and your approval.

The key discipline: **remote actions carry the same gates as local ones.** Distance doesn't
lower the bar — if anything, a remote `server` you can't see deserves *more* care (its
`cautious` permission preset, verification after every apply).

## Running the operator on multiple nodes

You may run the AI CLI on several nodes — e.g. interactively on the `workstation` and also on
the always-on `server`. Two things to manage:

- **Config symmetry.** Each node's operator uses the *same* rules and skills (rendered by the
  config manager from the one repo), so it behaves consistently everywhere. A rule that exists
  on one node and not another is drift ([Rule 7](03-governance-rules.md)).
- **Per-role permissions.** The *posture* differs by role even though the rules are shared: the
  unattended `server` runs a **cautious** permission preset; the `workstation` you sit at can
  run **standard/trusting** ([09 · Permissions](09-permissions.md)). Same rules, role-appropriate
  capability limits.

## Session mobility and coordination (patterns)

When the operator runs in more than one place, a few coordination patterns become useful. These
are **options**, not requirements — adopt the ones that fit:

- **Remote-attach** — the session stays on its origin node; you drive it from elsewhere (e.g.
  from your phone, or from the `workstation` reaching the `server`). Nothing moves; you're just
  operating a session that lives on another node. Needs the session to be *reachable and
  persistent* on its host.
- **Session transfer** — move a live operator session from one node to another (start on the
  `server`, continue on the `workstation`). Useful for going offline, forking work, or when the
  origin node is going down. Requires a way to serialize + relocate session state.
- **Peer awareness** — multiple independent operator sessions on different nodes notice each
  other's changes to a shared repo (so two sessions don't clobber each other). Earns its keep
  only when 2+ live sessions target the same repo at once; overkill otherwise.

Each is a distinct capability with its own tooling; the framework describes the patterns and
their trade-offs rather than mandating one. Most setups need none of them at first — a single
operator on the `workstation`, occasionally reaching other nodes, is plenty.

## A fleet view

Once you're managing several nodes, the **dashboard** ([04 · Structure](04-structure.md)) becomes
the fleet view: a page per node showing its current state (services, specs, dated snapshots),
plus the config-management adoption matrix and the divergence ledger ([Rule 7](03-governance-rules.md)'s
unavoidable-vs-temporary splits). This is where "what did we agree is true about everything" gets
answered at a glance — the payoff of the structure discipline scaling to many nodes.

**But a dashboard is not a monitor.** It shows the state of *record*, refreshed when you commit;
its figures are dated snapshots. "Is it working *right now*, and who gets told when it isn't?" is
a different job, answered by health checks + alerting — see
[E16](examples/E16-fleet-health-and-alerting.md). Run both: the dashboard for what you decided,
the checker for what is actually true this minute.

## The node that isn't like the others

Most fleets end up with one. A different OS, a different role, a machine that got added for one job
and never fitted the pattern. It is worth naming, because the odd node fails in a characteristic way:
**not loudly, but by quietly dropping out of everything.**

### "It can't be automated" is usually two claims, and only one is true

The most expensive label you can put on a node is *manual*. It reads as a decision someone made after
investigating — so nobody investigates again — when it usually records a single failed attempt years
earlier. A node marked manual stops appearing in coverage, stops being counted, and accrues work
indefinitely while the fleet reports itself healthy.

Almost always, the underlying claim conflates two different things:

| | Typically needs privilege / interactivity | Typically does not |
|---|---|---|
| **Installing** an update | ✅ | |
| **Detecting** what is available | | ✅ |

Windows' `winget` will list available upgrades over a plain SSH session; only applying them wants an
elevated interactive context. A NAS package manager may exist but simply not be on the non-interactive
`PATH`. Test the narrow claim before you write down the broad one — and when a node genuinely has not
been assessed, label it **`not-audited`, never `manual`**, so the distinction between *"we decided"*
and *"nobody looked"* survives.

### Cached results are fine; pretending they are fresh is not

Detection often works but degrades without privilege — an index that cannot refresh, a source list
that is a day old. That is usually still worth having. Say so in the output (*"from cache; refreshing
the index needs elevation"*) exactly as you would for an unrefreshed package index. The failure mode
is not the staleness; it is a report that reads as authoritative when it is not.

### Quoting across an OS boundary will bite you

Sending a command from one platform's shell, through SSH, into another platform's shell means the
string passes through two or three quoting regimes. Anything containing backslashes, nested quotes or
path separators will eventually be mangled — and the failure is often *silent*, producing empty output
that looks exactly like "nothing to report".

**Ship a script file to the node and invoke that.** It removes the entire class of bug, and it makes
the remote logic reviewable and version-controllable instead of buried in an escaped one-liner. Have
it emit trivially parseable output (`KEY=value` lines) so the caller needs no cleverness.

The same reasoning applies to the probe itself: prefer a command that exists everywhere. A reachability
check that runs `true` will report a Windows node as unreachable forever, because `true` is not a
command there — while your interactive SSH to it works perfectly.

### Credentials, not capability, are usually the real blocker

Config management, private repositories and package registries all assume the node can authenticate.
The odd node often cannot: it has no key, no token, no credential helper. That is a **decision about
where secrets live**, not a technical gap — and it belongs with the person who owns the risk, not
quietly solved by whoever hits it first. Do the work that does not need it, then stop and ask.

### Workloads that assume a human are the real fragility

A background job that depends on someone being logged in is a latent outage on any node, but it is
most common on the odd one — a desktop-oriented machine pressed into service. Two questions decide it:

- **Does the workload need a graphical session?** GUI applications can fail to start with no desktop
  present, and fail *silently* — no crash, no log line, nothing to grep for.
- **Does anything establish the prerequisites at boot?** A VPN client that keeps a tunnel alive once
  connected does not necessarily *connect* one unattended. Persistence and initiation are different
  capabilities, and it is easy to verify the first and assume the second.

The test that matters is the one that reproduces production: **log out, or reboot.** Any check run
while someone is signed in proves only that the job works *alongside* a session — never *without* one.
That distinction is invisible until the machine restarts on its own at 2am.

## Keeping multi-node sane

The failure mode of multi-node is **divergence you didn't notice** — a tweak on one node, a
tool updated on another, a rule that drifted. Counter it with the disciplines already defined:

- **Symmetry by default** ([Rule 7](03-governance-rules.md)); divergence must justify itself as
  unavoidable or temporary-with-cleanup.
- **A periodic drift check** across nodes ([chezmoi](05-chezmoi.md)) — a read that catches
  surprises early.
- **The divergence ledger** on the dashboard — every intentional per-node difference written
  down, so it's a decision, not an accident.

Multi-node doesn't change the framework's shape — it's the same rules, structure, and
config-flow applied to more nodes. That invariance is what keeps it manageable as you grow.

Next: [14 · Monitoring](14-monitoring.md) — knowing the fleet works, and hearing when it doesn't.
