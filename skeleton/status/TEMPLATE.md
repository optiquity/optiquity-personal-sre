# Status — <project>

```
status:        <open | pending | stable | resolved | …> — <one clause: where it stands>
opened:        <YYYY-MM-DD>
last-updated:  <YYYY-MM-DD>
template:      1.0
```

> **Created when the project opens**, beside its `DESIGN.md` and `POSTMORTEM.md`, by the same action.
> Written by the session working on the project; read first by any session that picks it up — **if the
> session that wrote it ended an hour ago, this file alone must be enough.** When, where and who:
> [`../status/RULES.md`](../status/RULES.md); why: [04 · Structure](../../guide/04-structure.md#where-a-project-stands--its-status-file).
> In the copy, delete this note and the template's revision log at the end.

**Summary:** <one line — the same line the registry shows>

## Current state

<!-- Dated, newest last. Every claim carries its evidence (the command and the date) or says
     "unverified". -->
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

<!-- The lock names this project takes (`locks/<resource>--<project>.md`, see `locks/README.md`), and
     what it deploys; or "none". -->

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

---

## Template revision log

| Version | Date | What changed |
|---|---|---|
| **1.0** | 2026-10-06 | Adopted in the source fleet, where every project's running notes moved into one by script, unaltered, with a test that no line was lost. Same sections as 0.1; the note now points to [`RULES.md`](RULES.md), and the template carries this log |
| **0.1** | 2026-10-05 | Initial, published before use |
