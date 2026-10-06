# sessions — set up several AI sessions in one repo

> ⛏ **Designed, not yet proven in use.** Published before its first pilot so it can be read and argued
> with; expand before relying on it. The *why* is in
> [16 · Multi-node](../../guide/16-multinode.md#several-sessions-in-one-repo).

**This file is written for your AI session.** Point a session at it and it walks you through building
the setup for your own fleet — asking you for what only you know, proposing each change, and waiting for
your approval before anything is committed. Nothing here is pre-filled for any particular fleet.

**You need this only if** you will run two or more sessions at the same time **in the same repo**, each
on a different project. With one session per repo, principle 12's default
([03 · Governance](../../guide/03-governance-rules.md)) already covers you.

| File | What it is |
|---|---|
| `README.md` | This: the setup steps, then how the sessions work once it is set up |
| [`BUILD-LOCK-HELPER.md`](BUILD-LOCK-HELPER.md) | What the lock helper must do and refuse, and the tests that prove it — for your session to build |
| [`../status/`](../status/README.md) | The status file every project gets — a prerequisite |

---

## Part 1 — the setup (for the session doing it)

Work through these in order. **Ask; do not guess.** Each step that changes the repo is a proposal your
operator approves under their normal rules.

### Step 1 — ask your operator

| Ask | Why |
|---|---|
| Which machines, and which outside accounts or services, will sessions change? (Include anything configured only through a web portal) | These become the names that can be locked (step 5) |
| Which projects will run in parallel first? | Each needs a status file (step 3) and gets its own working copy |
| Which machines do sessions run on? | Each lock records the machine its holder runs on — session names may repeat across machines |
| Do they reach sessions from other devices (remote access)? | Every session must be visible to the others, or a live lock holder looks gone |
| Which of the repo's gitignored files does every working copy need? | They are not copied into a new working copy unless listed (step 2) |

### Step 2 — prepare the repo for working copies

Propose, as one change:

- **`.claude/worktrees/` in the tracked `.gitignore`** — an entry only in `.git/info/exclude` exists in
  one clone.
- **A tracked `.claude/settings.json` with `"worktree": {"baseRef": "fresh"}`**, so each new working copy
  starts from the remote's main. The main folder falls behind while sessions push from their own copies.
- **A `.worktreeinclude`** listing the files from step 1's last answer. ⚠ A leak guard that fails closed
  without its private list will refuse every commit in a working copy that lacks it.
- ⚠ **Check every commit hook first.** From a linked working copy, git hands hooks `GIT_DIR` and
  `GIT_INDEX_FILE` as absolute paths. A hook that runs `git` in a scratch repository inherits them and can
  rewrite the **shared** config so that no checkout works. Test each hook by committing from a throwaway
  working copy before any session uses one. The fix is one line before a hook touches any other
  repository: `unset $(git rev-parse --local-env-vars)` — git's own list of the variables that tie a
  process to one repository. *(This framework's own pre-commit hook had that defect until 2026-10-06;
  `scripts/test_pre_commit_hook.py` now proves, in CI, that a commit from a working copy and a
  `git commit -a` both work and both still block a leak.)*

### Step 3 — give every project a status file

Follow [`../status/README.md`](../status/README.md): one `STATUS.md` per project, the registry cut to one
line per project. With several sessions, this is what stops them all editing the same registry entry.

### Step 4 — split anything every project writes

List the files every project's work updates — typically the registry and any status dashboard. For each,
propose a split so a project writes only its own part: a status file per project, a data file per
project assembled into the dashboard. **If the dashboard is assembled, write down how** — sections, their
order, which file fills which part, and what happens to a missing or broken file (the build stops and
names it) — so the same files always produce the same page.

### Step 5 — create the lock folder

Create `locks/README.md` in the repo — a short page your sessions read — from step 1's answers:

- **The lockable names:** one short lowercase name per machine or outside service from step 1's first
  answer. Any name not on this list is refused, so one machine can never be locked under two names.
- **The file name rule:** `<name>--<project>.md`, where `<project>` is a project folder or `ALL`.
- **What a lock file records:** in plain words — which session holds it, which machine that session runs
  on, what it is changing, when it started and when it expects to finish, and who permitted it if the
  resource was already locked.
- **The rules in Part 2 §4** below, in your own words.

Show your operator the page before committing it.

### Step 6 — build the lock helper

Build it to [`BUILD-LOCK-HELPER.md`](BUILD-LOCK-HELPER.md), with every test there, each seen to fail on its
planted defect. Then ask your operator one question: **may the helper commit and push lock changes
without asking each time?** Its self-check (it can only ever change one file under `locks/`) is what
makes that safe. Their answer is theirs; without it, every lock waits for them.

### Step 7 — the rules

Propose adding to your rules file, under principle 12: *several sessions may work in this repo at once,
each on one project, each in its own working copy, keeping its project's status file and taking a lock
before changing a machine or outside service*. Then the peer-messaging standard's current version
([`../peer-messaging/`](../peer-messaging/PEER-MESSAGING.md)) for naming and logging.

### Step 8 — detection, then a pilot

- **Propose three checks for your monitoring:** a lock older than a day; an open project whose status
  has not changed in two weeks; a working copy with unpushed work and no change for a week. Prove each by
  planting the condition.
- **Pilot with two sessions** on two low-risk projects for a few days before a third. Record every
  overlap and every machine change as it happens.

---

## Part 2 — how the sessions work, once set up

### §1 Starting a session

One command (Claude Code shown; check the flags in your version):

```sh
claude -w <project> -n <any-name> --remote-control <the-same-name>
```

`-w` gives it its own working copy and branch; Claude Code then refuses that session's edits to the main
folder, so **it cannot commit another session's unfinished edits**. **The name is whatever you choose** —
no format is required; it is how other sessions address this one. **On start, on resume, and after a
context summary**, a session reads its project's `STATUS.md` and lists the locks held in its own name.

### §2 Landing a commit

One approval covers all of it: commit in its own working copy (exact paths, never "everything") → fetch
→ rebase onto the remote's main → run the repo's checks → push **without force**; if the remote refuses
because main moved, go back to the fetch. A conflict in its own files: it resolves it. In a file another
live session is working on: it messages that session first, and asks the operator when in doubt. Each
request to the operator stands alone — it names the session and the project, and is never buried in a
status report.

### §3 Who edits what

| What | Who | How overlaps resolve |
|---|---|---|
| The project's own folder | its session | — |
| Its own registry line, its own dashboard data | its session | at landing |
| Shared code several projects use | any session that needs to, saying so in the commit | at landing; message the other session if its work is affected |
| Rules files and templates | any session, **with the operator's approval** | at landing; then it tells every live session to re-read them |
| The agent's per-machine memory, if it keeps one | any session — behavioural notes only | ⚠ not in git and shared by every working copy, so a later write silently replaces an earlier one: one small edit at a time, re-read straight after |
| Exchanges with **another repo's** sessions | any session talking to that peer | append-only, per the peer-messaging standard |
| Exchanges **between sessions of this repo** | the project's own `STATUS.md` | no shared log per short-lived session |

A user-level rules file every session reads is the same problem at its worst — two sessions can each
write it with approval and the later one silently wins. Manage it from the repo through your config
manager, so its changes go through git too.

### §4 Locks — for changing a machine or an outside service

- **Locks are for changes, never reads**, and cover one change from its start until it is verified — not
  a project's whole life. Long-running jobs are machine state that monitoring watches, not locks. A
  session that only reads a locked resource treats what it sees as possibly mid-change.
- **`ALL` is the default.** **Any second lock on a resource needs permission** from each existing holder,
  or from the operator — recorded in the new lock. That permission covers sharing the lock only; the
  change itself still needs the operator's approval.
- **The holder releases it** once the change is verified, and before the session ends.
- **Deciding a lock is stale:** the holder is listed and answers → its answer decides · listed as
  offline, or listed but silent for ten minutes → **ask the operator** · not listed at all, while
  every session runs with remote access → stale; on the same machine, its recorded process is gone.
  **Can't tell is never "stale".**
- **Taking over a stale lock:** the earlier change may be half-done. Read what the lock says it was
  changing, check the resource without changing anything, and include both in the request to the
  operator. A resumed session that finds its lock taken over has lost it: it stops and reports.
- **Several resources at once:** lock them in alphabetical order; if one is refused, release the rest.
- **The operator's own hands-on step:** the session that prepared it holds the lock for them.
- **Automation ignores locks.** A change that clashes with a scheduled job pauses that job, with approval.
  A commit that your config manager will apply to machines is itself a change to them: check their locks
  before landing it.
- **The git host unreachable:** no lock can be taken or checked, so a locked change goes ahead only with
  the operator's go, and is recorded once the host is back.

### §5 Every overlap, and its handling

| Overlap | Handled by |
|---|---|
| Two sessions editing the same file | Separate working copies — unfinished edits cannot meet; finished ones meet at landing |
| Two sessions pushing at once | Push without force; the refused one rebases and retries |
| Files every project updates | A status file per project; the registry an index; assembled dashboards |
| Rules files and shared memory | Operator approval, then a re-read message to every live session |
| Two sessions changing one machine or service | A lock; a second lock needs permission |
| Two sessions with one name | The agent de-duplicates names on one machine; a lock records its holder's machine as well as its name |
| The operator's attention | Each request stands alone and names its session |

### §6 What this does not catch

- **A session that changes a machine without taking a lock.** Lock-taking is a rule, not enforced;
  deciding which commands are "state-changing" in a hook is not reliable. A missing lock leaves no trace
  except the machine's own state.
- **Checks scheduled inside a session die with it** — the status file's dated list is the record.
- **Anything a pilot has not yet shown** — see the banner.
