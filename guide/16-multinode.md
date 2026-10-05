# 16 · Multi-node operations (advanced)

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
  run **standard/trusting** ([10 · Permissions](10-permissions.md)). Same rules, role-appropriate
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
- **Several sessions in one repo** — two or more sessions working in the *same* repo at once, each
  on its own project. Awareness alone is not enough here: it cannot stop two sessions changing the
  same machine. Earns its keep only when you actually run sessions side by side; overkill otherwise.
  See [Several sessions in one repo](#several-sessions-in-one-repo) below.

- **Peer messaging** — the operator sessions that own *different repos* message each other
  directly, instead of you copying questions between terminals. Increasingly this is **native** to
  the coding agent, so check before building. It is the one pattern here that pays off immediately
  with only two repos, because without it **you are the transport** — and that quietly removes the
  only party who can challenge a claim, since you were not the one who measured it.
  **A ready-to-adopt standard is in
  [`skeleton/peer-messaging/PEER-MESSAGING.md`](../skeleton/peer-messaging/PEER-MESSAGING.md)** — it
  is **versioned and propagates peer to peer**: each repo carries its own stamped copy, every message
  declares a version, and a session that is behind pulls the newer one. ⚠ **Do not put it in a shared
  per-machine location** — that is the obvious move and it is not federated; it does not travel
  between nodes, which on a multi-node fleet is exactly the failure you would not notice.
  **A session joining later needs one link:**
  [`skeleton/peer-messaging/QUICKSTART.md`](../skeleton/peer-messaging/QUICKSTART.md) walks it
  through the rest, including how to ask the session that owns a machine for an install.

Each is a distinct capability with its own tooling; the framework describes the patterns and
their trade-offs rather than mandating one. Most setups need none of them at first — a single
operator on the `workstation`, occasionally reaching other nodes, is plenty.

> **⚠ Peer messaging arrives with a permission problem, and it is not obvious.** Permission
> boundaries are **per-session**: a command your session was blocked from running is not blocked in
> your peer's. So "ask the other agent to do it" is a working bypass of your approval unless a rule
> forbids it. Adopt the contract before you adopt the channel —
> [03 · Governance](03-governance-rules.md) carries the rule; **[E19 · Agents that talk to each
> other](examples/E19-agents-that-talk-to-each-other.md)** is the worked example, including the
> naming convention that turns out to be the addressing scheme and the conversation log that keeps
> decisions visible to you.

## Several sessions in one repo

> ⛏ **Designed, not yet proven in use.** What follows is an agreed design, published before its pilot.
> The setup steps — written for your AI session to follow with you — are in
> [`skeleton/sessions/`](../skeleton/sessions/README.md).

A repo that holds many small projects invites running several sessions at once: one on a backup, one
on a network change, one on the public docs. Each is assigned one project by you and works on it alone.
Four things collide when they share a repo, and each gets its own answer:

| What collides | Why it matters | The answer |
|---|---|---|
| **Unfinished edits** in the same folder | A commit picks up another session's half-done work | **A git working copy per session.** The agent's own isolation then refuses that session's edits to the main folder |
| **Files every project updates** — the registry, the dashboard | Every session edits the same lines | **A status file per project** ([04 · Structure](04-structure.md#where-a-project-stands--its-status-file)); the registry an index; dashboards assembled from per-project data by a written spec |
| **The same machine or outside service** | Git merges files; nothing merges two half-applied changes to a NAS | **A lock** — a file in the repo, taken before a change and released after it |
| **Names** | Session lists de-duplicate names on one machine only | **`<machine>-<repo>-<project>`** |

### Federated, deliberately

**No session controls another, and nothing keeps a list of them.** A "lead" session may draft a starter
prompt or send a message; it cannot assign, approve or wait on anyone. Two designs were rejected for
exactly this reason: **a register of live sessions** (one central place every session must keep current —
the same failure as a shared per-machine rules file), and **a coordinator that hands out work** (one
session that the others depend on). What coordinates the sessions is what each already has: its
project's documents, git, cross-session messaging, and the locks folder.

### Why the locks live in the repo, not on the machines

Putting a lock on the machine being changed looks natural, and fails three ways: there is no standard
location or owner across several operating systems; nothing guarantees it survives; and a service you can
only configure through its web portal has nowhere to put one at all. A folder on `main` of your private
repo is one place, one format, durable, and visible to every session on every machine. Two more options
were weighed: a cloud key-value store with create-only writes (atomic, but every session needs cloud
credentials and it is a second record outside the repo), and hidden git refs (atomic and quiet, but
invisible on the host's web page and gone from history).

What makes a folder of files safe is **one writer**: a helper that builds a single-file commit on top of
the remote's main and pushes without force, so two sessions racing for one lock cannot both win. Because
it can change nothing else, you can give lock commits a standing approval while every other commit still
waits for yours.

**`ALL` by default, and a second lock needs permission.** A lock names the resource and the project —
`nas--ALL`, or `nas--share-cleanup` beside it. Any second lock on a resource needs the holder's permission,
or yours. The permission covers sharing the lock only; the change itself still needs your approval, so a
peer never grants escalation ([03 · Governance](03-governance-rules.md), principle 13).

**A lock outlives a session that forgets it.** So every session checks for its own locks when it starts,
resumes or is summarised; your monitoring lists locks older than a day; and **"can't tell whether the
holder is alive" is never "stale"** — a holder that is offline, or silent while it works, is your call.

### What it cannot do

A session that changes a machine **without** taking a lock leaves no trace except the machine's state:
lock-taking is a rule, not something a hook can reliably enforce. And none of this has yet survived a
week of sessions working side by side — the pilot comes first, and this section will change with it.

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

### A fix that reaches four nodes out of five looks done

A config manager keeps the nodes it manages in step, and nothing else. Two kinds of file sit outside
it, and both fall behind the repo without a sound:

- **Hand-installed copies on the node it doesn't manage.** The odd node is often not under the
  config manager at all, so its scripts were copied there once. Fix a tool in the repo and the fix
  reaches every other node, while this one keeps the old copy. It looks done, because everywhere you
  look is fixed.
- **Files it stages but cannot install.** Some live paths need root (a system service definition, a
  daemon's binary), which a user-level config manager cannot write. It puts the new version in a
  staging directory, and someone installs it by hand. Until they do, the change is committed, applied
  and reported, and not running.

One check closes both: **compare the file that actually runs with the repo copy, by checksum, on a
schedule, and name the stale file.** In the first case the file is on another machine, so read its
checksum over SSH, and treat a node you cannot reach as *unknown*, not current. The skeleton's
`hash` check does both ([`skeleton/monitoring/`](../skeleton/monitoring/)). Then **register** each
program you placed by hand in the update checker's `fleet-binaries.conf`. Its discovery walks the
usual install folders (`/usr/local/bin`, plus `/opt` on Linux), so a program placed there and never
registered is reported. That is the registry-and-discovery pattern from
[17 · Monitoring](17-monitoring.md). ⚠ A file anywhere else, such as a service definition, is watched
only by the `hash` line you wrote for it. Nothing will report one you forgot, so put hand-placed
programs where discovery looks, or add their folder to that node's line (an optional fifth column).
Add only a folder that really holds hand-placed programs: one full of managed scripts and tool
shims reported 35 of 36 entries as unregistered, which trains the reader to ignore the digest.

⚠ **It happens within minutes.** A shared mail tool was edited in the repo and synced to every
managed node. The gateway's hand-installed copy was three lines behind within minutes, and nothing
compared the two until a check was written for it.

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

Next: [17 · Monitoring](17-monitoring.md) — knowing the fleet works, and hearing when it doesn't.
