# Postmortem rules

These rules answer **whether, when, where and who**. They do **not** describe how to write
the document — that is [`TEMPLATE.md`](TEMPLATE.md), which owns all section-level guidance.

> **One source of truth.** If something tells you how to fill in a section, it belongs in the
> template and appears here only as a pointer. Cross-references are fine; restated content is
> not, because two copies drift and then conflict — and a reader cannot tell which is
> authoritative.

Copy both files into your own repo (a folder such as `docs/postmortems/`), then have your
operator's rules file point at them. See [`README.md`](README.md).

---

## R1 · Mandatory for every completed project

**Every project that completes gets a postmortem** — install, migration, policy change,
decommission and triage alike. Not only the ones that went badly.

A clean install with nothing to report still answers: what was considered, why this option,
and **what would tell us if this degrades later**. That last question is why install projects
are included rather than exempt.

## R2 · Created when the project OPENS, not when it closes

`docs/<project>/POSTMORTEM.md` is created from the template with `status: draft` at the
moment a project becomes **open** — by the same action that creates its runbook.

⚠ **This is the load-bearing rule.** The sections covering what else was considered, what
went wrong, and what would have caught it sooner are only knowable *while the work happens*.
Written afterwards they are reconstruction — and a postmortem that invents its own reasoning
is worse than none, because it reads as authoritative while being partly fiction.

## R3 · The working format is mandatory while a project is open

Entries are appended as work happens; prose is written only at close.

**The mechanics — triggers, format, and what a good entry looks like — are in
[`TEMPLATE.md`](TEMPLATE.md).** This rule establishes only that using it is not optional.

## R4 · One postmortem per causal thread, not per folder

A project containing two unrelated failures gets two postmortems, named
`POSTMORTEM-<slug>.md`, each stating in its **Related** section why they are separate.

Merging unrelated causes into one document recreates exactly the confusion that made them
hard to diagnose in the first place.

## R5 · Postmortems are separate from the working record

The project's runbooks and working notes stay where they are and are **not retired** when the
postmortem is written. They are open-ended and context-independent; the postmortem is
structured and narrow. Two documents, two jobs.

The postmortem **links** to the working record for evidence rather than restating it.

## R6 · If you publish, publish the generalised version

Postmortems in your private repo should carry **full detail** — hostnames, addresses, paths,
capacities. Detail is what makes them useful for operating your own fleet. **No credentials,
keys or secrets, ever.**

Anything published to a public repo must be **sanitised and generalised**: hardware classes
and versions only where they carry the explanation (*"a NAS running its vendor OS"*), never
machine names, addresses, serials or paths.

**The public artifact is a case study. The postmortem is its private source.**

> If you keep a public repo, pair this with a secret-scanning pre-commit hook. See
> [19 · Public/shared repos](../../guide/19-sharing.md) — a guard that fails closed is what
> makes publishing safe, not care alone.

## R7 · Work on a published repo is postmortemed in the private one

A public repo is a *product*, not a workplace. Projects that build it are tracked in your
private repo and postmortemed there, alongside every other project.

The public repo carries only the template and rules, for others to use.

---

## R8 · Retrofit only where it will be used — **mirrors `../design/RULES.md` D8**

**Projects already open when you adopt this practice do not get a back-dated draft.** R2's
trigger — *created when the project opens* — has already passed for them and cannot fire
retroactively. They get a postmortem **at close**, written from the record, accepting that the
*considered / went-wrong / would-have-caught-it* sections will be weaker than a live capture.

⚠ **That weakness is the price of adopting the rule late, not a defect to paper over.** A
back-dated "draft" reconstructed today is exactly the invented-reasoning failure R2 exists to
prevent — it would read as a live record while being written from hindsight.

**A project that is REOPENED or gains FOLLOW-ON WORK gets one then** — covering either the new
work alone or the whole thread, whichever the situation calls for.

⚠ **This mirrors D8 deliberately.** The design and postmortem practices are a loop (D6/D7, R9), and
**a loop whose two halves have different scope rules will drift until one half stops feeding the
other.** If you change one, change both.

Two limits, both hard:

- ⚠ **No postmortem that will not be read.** One written to satisfy a rule is overhead pretending
  to be diligence.
- ⚠ **No postmortem with hollow sections.** If the load-bearing sections cannot be established from
  the record, **either establish them or do not write the document.**

## R9 · Research completed work before writing up new work

**When a new project's write-up begins — design doc, postmortem draft, or both — read the completed
projects and docs that bear on it first.**

Not as a courtesy to history: **the context is load-bearing.** Most of what a new project needs to
know about its own failure modes has already been recorded next door.

⚠ **The defect this prevents is specific and common: a fix applied to the one file, probe or
service that hurt, while the *class* it belongs to goes unexamined.** A fix's *class* is what
should be applied, not just the fix — and the question that closes it usually takes a minute:
***which other things have this property?***

Worked instances of the cost, all from one real fleet:

- A protocol's session semantics documented during one project, then rediscovered the hard way
  **four months later** in another, because the note lived in a project folder rather than anywhere
  a fleet-wide check would look.
- A config-manager fix correctly diagnosed and correctly applied to one app-owned file — while
  **the sibling file two lines away in the same rules list** stayed broken for **86 days**, then
  caused **20 days of silent, fleet-wide sync failure**.
- A health probe rejected in one project for *"reads cached data, calls a dead handle healthy"* —
  the exact defect that later shipped, repeatedly, in a different subsystem's monitoring.

**In practice:** before writing up work on X, read the postmortems and docs of the projects your
registry lists as *related* to X, plus anything touching the same machine, protocol or install
method. **Cite what you found — including when the answer is "nothing relevant."** ⚠ **An
unrecorded search is indistinguishable from one that never ran.**

⚠ **This is the only rule here that applies to work which has not gone wrong yet**, which is
exactly why it is the easiest to skip.

## R10 · Templates are versioned, and so are the documents — **mirrors `../design/RULES.md` D3/D9**

Two independent versions: **`template-version`** (which template the document was written against)
and **`postmortem-version`** (this document's own revision).

**`template-version`** matters because the template *changes* — that is the upstream half of the
loop (D7): a finding becomes a new standing question, and the template is bumped. ⚠ **Being able
to see which documents predate a lesson is the whole point**; without it you cannot tell an
absent section from one written before the question existed.

**`postmortem-version` will usually stay at 1, and that is correct.** A postmortem is a draft that
*accumulates* while the project runs (R2/R3), so its content grows without the version moving.
**Appending during the work is not a revision.**

**It exists for after `final`:**

- the project is **reopened or gains follow-on work** (R8) and this postmortem gains a new thread
- a finding proves **wrong** and the conclusion changes
- a follow-on **resolves**, changing the final-state answer

⚠ **Never edit a `final` postmortem in place — bump and append.** What was believed at the time
**is the evidence**, most of all for *what would have caught this sooner*: a detection gap is only
meaningful against what was known then. **A document that quietly becomes right is worth less than
one that shows where it was wrong.**

**The point of versioning is to make changing your mind cheap** — the same reason it exists on the
design side. If revising means admitting the first version was wrong and rewriting around it, the
pressure is to leave it standing.

## Retroactive backfill

**Do not postmortem every completed project indiscriminately.** Research first — read each
project's docs and version history, then judge whether a postmortem would carry real content.

Where the record cannot support "solutions considered", either write it with that gap stated
plainly (the template says how), or **skip the project and record why**.

**A postmortem that says nothing is worse than an acknowledged gap**, because it implies the
question was asked and answered.


---

## Template revision log

⚠ **Record what changed between template versions**, so a document's `template-version` resolves to
an actual difference rather than a bare number. Without it the field is unreadable.

| Version | Date | What changed |
|---|---|---|
| **1.1** | <date> | Added `postmortem-version` + `template-version` and a **Revision log** section (R10) |
| **1.0** | <date> | Initial |
