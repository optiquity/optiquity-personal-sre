# PROJECTS.md — <repo-name> (project registry)

The index of every project in this repo: its status word, one line, and its status file. This is your
source of truth for "what's going on" (governance Rule 8). **Where a project stands** — its state, queue,
dated items, deferrals and documents — is in its own `docs/<project>/STATUS.md` (rules in
`docs/status/RULES.md`). See `guide/04-structure.md` in the framework reference for the full pattern.

> Seeded by `bootstrap.sh`. This is YOUR repo — edit freely (unlike the framework reference,
> which is read-only). Nothing here is committed yet; your first commit is part of onboarding.

## Status legend
pending · open · stable · resolved · deprecated · superseded · cancelled
(see `guide/04-structure.md` for definitions)

## Projects

| Project | Status | Summary | Status file |
|---|---|---|---|
| onboarding | **open** | Finish standing up this repo (node role: <role>): first commit, config manager, secrets, permission preset. | `docs/onboarding/STATUS.md` |

---

*Add a row when a project opens — in the same commit as its design doc, postmortem draft and status file
(the order: the framework's `skeleton/sessions/STARTING.md` part C). A row changes only when the status
word or the line changes, and the line is the status file's Summary, word for word. If this file and any
status view disagree, this file wins.*
