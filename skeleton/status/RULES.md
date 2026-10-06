# Status file rules

**Version 1.0.** These rules answer **whether, when, where and who**. How to fill in each section is
[`TEMPLATE.md`](TEMPLATE.md)'s job — one source of truth each, as for [`../design/`](../design/RULES.md)
and [`../postmortems/`](../postmortems/RULES.md). Copy this file to `docs/status/RULES.md` in your repo.

## S1 · Every project has one

`docs/<project>/STATUS.md`, from `TEMPLATE.md`, **created when the project opens** — by the same action
that creates its design doc and postmortem draft. The order a new project's files are written and landed
in: [`../sessions/STARTING.md`](../sessions/STARTING.md) part C, which applies with one session per repo
too.

## S2 · It is where the project stands — nothing else is

Status, the queue, dated items, deferrals and the project's documents live here. **The registry is an
index**: the status legend and one row per project — status word, one line, link to this file. A row
changes only when the status word or the line changes, and **the line is this file's `Summary`, word for
word**.

## S3 · Who writes it, and when it is read

- **Written by the session working on the project**, and updated in every commit that changes where the
  project stands; `last-updated` is set to that date.
- **Read first** by any session that starts on the project, resumes it, or continues after a context
  summary — with its design and postmortem.
- **Current state entries are dated, and every claim carries its evidence or says "unverified"**
  ([principle 18](../../guide/03-governance-rules.md)). Newer entries go last; an entry that proves
  wrong is corrected with a dated note, never silently rewritten.

## S4 · Dated items are the record

⚠ **A check scheduled inside a session dies with that session.** Anything due on a date is written in
*Dated items*; the schedule is only a convenience on top.

## S5 · Deferrals carry a reason and a date

Blocked, huge, or grouped with later work — and *when*. "Later" is not a date.

## S6 · Machines, services and other sessions

*Machines and services it changes* lists the lock names the project takes and what it deploys. The
*Session log* records exchanges with other sessions **of this repo** and the locks taken and released;
exchanges with sessions of other repos go in the peer-messaging log
([`../peer-messaging/`](../peer-messaging/PEER-MESSAGING.md)).

## S7 · Staleness is detected, not trusted

An **open** project whose `last-updated` is more than **two weeks** old is reported by your monitoring.
The fix is to update the file — or the status word, if the project is no longer open. ⚠ A migration
that stamps every file with one date makes them all go stale on the same day; expect it.

## S8 · Moving existing projects in

When you adopt this with projects already running, move each one's text from the registry into its
status file **unaltered**, by a script, with a test that no line was lost — in one pass if you can: half
the projects in one place and half in another is two places to look. Sections the old text did not fill
say so (*"not recorded at the move"*) and are filled the next time a session works on the project.
**Never fill one by reconstruction**: a section that reads as answered when it was not is worse than an
empty one.

## S9 · The template is versioned

`TEMPLATE.md` carries a version and a revision log. A format change bumps the version, adds a row, and
is applied to every `STATUS.md` **by a script**, never by hand-editing each file. Each file's header says
which version it follows.
