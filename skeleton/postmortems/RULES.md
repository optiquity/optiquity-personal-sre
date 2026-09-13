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

## Retroactive backfill

**Do not postmortem every completed project indiscriminately.** Research first — read each
project's docs and version history, then judge whether a postmortem would carry real content.

Where the record cannot support "solutions considered", either write it with that gap stated
plainly (the template says how), or **skip the project and record why**.

**A postmortem that says nothing is worse than an acknowledged gap**, because it implies the
question was asked and answered.
