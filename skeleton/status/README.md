# status — where each project stands

> ⛏ **Version 1.0 — adopted in the source fleet, not yet proven by several sessions at once.** Its
> sections held when every project's running notes moved into one; the pilot of several sessions may
> still change them. Your copy carries the version it came from, so a later change is easy to spot.

One file per project, created **when the project opens** — the same moment as its design doc
([`../design/`](../design/README.md)) and its postmortem draft ([`../postmortems/`](../postmortems/README.md)).
Opening a project produces all three.

| File | What it is |
|---|---|
| [`RULES.md`](RULES.md) | **Whether, when, where and who** — read when a project opens, and when a session starts or resumes |
| [`TEMPLATE.md`](TEMPLATE.md) | The blank status file. Copy it to `docs/<project>/STATUS.md` |

**Opening a new project** — the order its design, postmortem, status file and registry row are written
and landed in: [`../sessions/STARTING.md`](../sessions/STARTING.md) part C. It applies with one session
per repo too.

Explained in **[04 · Structure](../../guide/04-structure.md#where-a-project-stands--its-status-file)**.

---

## The three files, and what each answers

| File | Answers | Changes |
|---|---|---|
| `DESIGN.md` | What must this survive, and how will we know? | Agreed once, before the work; revised only on a major change |
| `STATUS.md` | Where is it now, and what happens next? | Every working session |
| `POSTMORTEM.md` | What was tried, what went wrong, what would have caught it sooner? | Appended as things happen; finalised at close |

## Why a file per project

- **A new session continues from it.** Sessions end; projects do not. If the last session that worked
  on a project closed an hour ago, the next one starts from this file alone — so "resume here", the
  queue and the dated items must be in it, not in a chat.
- **The registry stays an index.** `PROJECTS.md` keeps one line per project — its status word and a
  summary — and points here for everything else. A registry that holds every project's running notes
  becomes the file every change touches, and with several sessions working at once it becomes the file
  they all fight over ([`../sessions/`](../sessions/README.md)).
- **Checks scheduled inside a session die with it.** The status file's dated list is the record of what
  is due; the schedule is only a convenience.

## Install it

1. **Copy `RULES.md` and `TEMPLATE.md`** to `docs/status/` in your repo (`bootstrap.sh` does this for a
   new repo).
2. **Add one line to your rules file** where it already says a project gets a design doc and a
   postmortem at open: *"…and a status file from `docs/status/TEMPLATE.md`."*
3. **Give existing projects one** by [`RULES.md`](RULES.md) S8 — their running notes moved in unaltered,
   by a script with a test that no line was lost, and each registry entry cut to one line. ⚠ Do it for
   all of them in one pass if you can: half the projects in one place and half in another is two places
   to look.
