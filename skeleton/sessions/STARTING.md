# Starting a session — the three kinds

> ⛏ **Designed, not yet proven in use.** Published before its first pilot, like the rest of this folder.
> The commands are Claude Code's; check the flags in your version.

**For you, the operator, and for your sessions:** how to start, resume and end each kind of session in a
repo set up by [`README.md`](README.md), with examples. `<repo>` below is your private repo's folder.

**Part C applies with one session per repo too.** Opening a project follows the same order whether or not
other sessions are running; skip what it says about working copies and locks.

---

## Which kind do you need?

| You want to… | Start |
|---|---|
| See where everything stands; change the rules, the shared practices, the dashboard's template or the tools; anything that spans several projects | **A · the general session** |
| Work on a project that already has a folder under `docs/` (a row in the registry) — including new work on a finished one | **B · a project session** |
| Start something that has no folder yet | **C · a new-project session** |

Not sure which? Ask the general session.

- **One general session at a time.** It works in the main folder, and two sessions there would pick up
  each other's unfinished edits.
- **One session per project at a time.** A project's session works in that project's own working copy;
  a second session on the same project would share it.

## What all three have in common

- **The name** is anything you like that no live session already uses. Other sessions message it by
  that name, and its locks record it with the machine it runs on.
- **Remote access is always on** (`--remote-control` in Claude Code). Without it, a session on another
  machine is invisible to the others, and a lock it holds would look abandoned. After resuming a session,
  turn it back on if it is off (`/remote-control`).
- **What every session does first, without being asked:** reads its project's `STATUS.md`, design and
  postmortem, and lists the locks held in its name.
- **What it asks you:** each request names the session and its project and stands on its own. One
  approval covers a commit, landing it on the remote's main and pushing it ([`README.md`](README.md)
  Part 2 §2). If you gave lock commits a standing approval (Part 1, step 6), taking and releasing a lock
  needs none; the change the lock covers still does.

---

## A · The general session

**What it is for:** oversight, and everything shared — the rules files, the shared practices
(`docs/status/`, `docs/design/`, `docs/postmortems/`), the dashboard's template, the lockable list,
the repo's own tools, and work that spans several projects. It does not do a single project's own work;
that is a project session's job. Its locks record its project as `general`.

**Start it:**

1. Open a terminal.
2. `cd <repo>`
3. `claude -n general --remote-control general` — no `-w`: it works in the main folder.
4. Type: *"You are the general session for this repo. Pull from the remote, read the rules file and the
   registry, list the locks, then tell me what needs my attention across all projects."*

It pulls before it works because the main folder falls behind while project sessions push from their own
copies.

**Come back to it:** in the same folder, `claude --resume` and pick it by name.

**Examples of what to ask it:**

- *"Where does everything stand? What is waiting on me?"*
- *"Rule 7 should also cover X — draft the change for my approval."* Once a rules change lands, it tells
  every live session to re-read the rules.
- *"Two projects both need the NAS this week. Where do they overlap?"*

---

## B · A session for an existing project

**Before you start:** find the project's folder name in the registry. Check that no other session is
working on it.

**Start it:**

1. Open a new terminal window.
2. `cd <repo>`
3. `claude -w <folder> -n <name> --remote-control <name>` — for example
   `claude -w backup-audit -n backup --remote-control backup`.
4. Type: *"You are the session for the `backup-audit` project. Read the rules file and the project's
   `STATUS.md`, design and postmortem, check for locks in your name, then tell me where it stands and
   what's next."*

**What `-w` does:** gives the session its own working copy of the repo at
`.claude/worktrees/<folder>/`, on its own branch, started from the remote's main (with
`"baseRef": "fresh"` — Part 1, step 2). Its unfinished edits cannot mix with another session's, and
Claude Code stops it from editing the main folder. If that working copy is still there from an earlier
session, the same command reopens it with its work intact.

**What it does by itself:** keeps the project's `STATUS.md` and dashboard data current; takes a lock
before changing any machine or outside service, and releases it once the change is verified; asks you
once to land each commit.

**New work on a finished project** starts the same way. The session changes its status word back to
`open`, and writes a design for the new work first if it warrants one.

**Come back to it:**

- **The same conversation:** run the command Claude Code printed when you closed it (it begins
  `claude --worktree <folder> --resume`), or `claude --resume` in the repo folder and pick it by name.
  ⚠ `claude --continue` in the main folder finds the general session's conversation, not this one: each
  session is recorded under the folder it ran in.
- **A fresh conversation on the same project:** run step 3 again. The new session picks up from the
  status file.

**End it:** ask it to wrap up — it releases its locks, brings *Resume here* in the status file up to date,
and lands its work or tells you what has not landed. Then `/exit`. Claude Code asks whether to keep the
working copy: **keep** it if anything has not landed; **remove** it if everything has. Your monitoring
lists a kept copy whose work has not landed after a week without change (README Part 1, step 8).

**Example:** you start `claude -w backup-audit -n backup --remote-control backup`. It reads the status
file, confirms last night's backup finished, and proposes turning on the alarm for the weekly
comparison — a setting on the server. You approve. It takes the `server` lock, makes the change,
verifies it, releases the lock, updates `STATUS.md` and the dashboard data, and asks you once to land
the commit.

---

## C · A session for a new project

**Before you start:** choose the project's folder name — lower-case letters, digits and hyphens, such as
`garden-sensors`, and not already a folder under `docs/`. It becomes the project's name everywhere: its
folder, its working copy, its registry row, its dashboard data and every lock it takes.

**What you do:**

1. Open a new terminal window.
2. `cd <repo>`
3. `claude -w garden-sensors -n sensors --remote-control sensors` *(one session per repo: plain
   `claude`)*
4. Type: *"You are the session for a new project, `garden-sensors`: <what you want, in your own words —
   the goal, what it touches, any deadline>. Open it by our rules."*
5. Answer its design questions, then agree the design or ask for changes.
6. Approve the opening commit.
7. From then on it is a project session, as in B.

**What the session does, in order:**

1. **Reads the rules for opening a project:** `docs/design/RULES.md`, `docs/postmortems/RULES.md` and
   `docs/status/RULES.md` — fresh, not from memory.
2. **Reads past work that bears on it** — the status files, designs and postmortems of related projects,
   and of any project touching the same machines — and **cites what it found**, including "nothing
   relevant".
3. **Drafts the design:** the short form for small, reversible work; the long form for anything touching
   several machines, security, storage, or anything hard to undo. It asks you only what it cannot find
   out. Reading machines is fine at this stage; changing them is not.
4. **Writes the project's other files:**
   - `docs/garden-sensors/STATUS.md`, from `docs/status/TEMPLATE.md`;
   - `docs/garden-sensors/POSTMORTEM.md`, a draft from `docs/postmortems/TEMPLATE.md`, its "solutions
     considered" taken from the design;
   - a row in the registry, whose line is the status file's *Summary*, word for word;
   - its dashboard data, if your dashboard is assembled from per-project files, with a page only as deep
     as the work honestly is.
5. **Asks you to agree the design.** Nothing is built before that.
6. **Asks you to approve one commit with all of those files**, and lands it. One commit, so that nothing
   ever sees the project half-registered — an assembled dashboard that refuses a registered project
   without its data file would otherwise fail in between.
7. **Only then does the work begin — including any lock.** A lock helper built to
   [`BUILD-LOCK-HELPER.md`](BUILD-LOCK-HELPER.md) refuses a lock from a project whose folder is not yet on
   the remote's main.

⚠ **If the design takes more than one sitting,** the drafts stay in the working copy: keep it when
Claude Code asks on exit, and come back as in B. They are not on the remote until the opening commit
lands, so your monitoring lists the working copy if it sits untouched for a week.

**Example (an illustration):** you start the session and type *"You are the session for a new project,
`garden-sensors`: I want soil-moisture readings from three sensors in the garden on the dashboard, with an
alert if a bed dries out. Open it by our rules."* It reads the rules, finds that your monitoring and
automation projects bear on it, drafts a short design with the options it weighed, and asks you how the
sensors connect and how fast an alert must arrive. You answer and agree the design. It asks to land the
opening commit — design, postmortem draft, status file, registry row, dashboard data — and you approve.
Its first change to the server, a new automation workflow, starts by taking the `server` lock.
