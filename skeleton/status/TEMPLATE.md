# Status — <project>

```
status:        <open | pending | stable | resolved | …> — <one clause: where it stands>
opened:        <YYYY-MM-DD>
last-updated:  <YYYY-MM-DD>
template:      0.1   # ⛏ not yet proven in use; expect the sections to change
```

> **Copy to `docs/<project>/STATUS.md` when the project opens**, beside its `DESIGN.md` and
> `POSTMORTEM.md`. Written by the session that owns the project. It is what a **new** session reads to
> continue the work — so if the session that wrote it ended an hour ago, this file alone must be enough.
> How it is used: [`README.md`](README.md); why: [04 · Structure](../../guide/04-structure.md#where-a-project-stands--its-status-file).

**Summary:** <one line — the same line the registry shows>

## Current state

<!-- Dated. Every claim carries its evidence (the command and the date) or says "unverified". -->
- **<YYYY-MM-DD>** — <what is true now> (verified: `<command>`) / (unverified)

## Resume here

<!-- What a new session does first. One short paragraph. -->

## Queue

| # | Item | Who | Needs | State |
|---|---|---|---|---|
| 1 | <what> | <operator / session> | <what it waits for> | <— / waiting / ✅ date> |

## Dated items

<!-- Anything due on a date. ⚠ Checks scheduled inside a session die with that session: this list is
     the record, not the schedule. -->

## Deferred

<!-- Each with its reason and a revisit date. "Later" is not a date. -->

## Machines and services it changes

<!-- The lock names this project takes (`locks/<resource>--<project>.md`), or "none". -->

## Documents

| Document | Status |
|---|---|
| `DESIGN.md` | <draft / agreed date> |
| `POSTMORTEM.md` | <draft / final> |

## Related

<!-- Other projects, and why. -->

## Session log

<!-- Exchanges with other sessions of THIS repo, and locks taken and released. Exchanges with sessions
     of other repos go in the peer-messaging log instead. -->
- **<YYYY-MM-DD>** — <who, what was asked or decided, what needs the operator>
