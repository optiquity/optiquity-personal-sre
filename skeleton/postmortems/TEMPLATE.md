# Postmortem — <project or causal thread>

```
status:  draft | final
kind:    triage | install | migration | policy | decommission
opened:  <YYYY-MM-DD>
closed:  <YYYY-MM-DD, or an em-dash while open>
```

> **When this is created, where it lives, and how it is named are governed by
> [`RULES.md`](RULES.md).** This file owns only *how to write it*.
>
> **Supporting record:** link the project's working docs here. This document is the
> *structured retrospective* — it points at the operational record rather than restating it.

---

## ⚠ THE WORKING FORMAT — read this before writing anything

**While the project is open, every section accumulates DATED APPEND ENTRIES.** You do not
write prose during the work. You append a line the moment something happens, under the
section it belongs to:

```markdown
## 2. Solutions considered
<!-- WORKING ENTRIES — append as they happen, tidy into prose at close -->
- **<date>** — Considered <option>. Rejected: <reason>.
- **<date>** — <owner> refused <option> outright. Do not re-propose.
```

**At close, the entries are tidied into prose and `status:` becomes `final`.** Dates stay
where they carry meaning.

### Why this is mandatory rather than encouraged

**Sections 2, 5 and 6 are only knowable while the work is happening.** Written afterwards
they become reconstruction — and a postmortem that reconstructs its own reasoning is worse
than no postmortem, because it reads as authoritative while being partly invented. An
alternative weighed at 2am and never written down is gone.

**The headings here are identical to the headings in the finished document**, so there is no
transcription step. Appending *is* drafting.

### The minimum bar

Append an entry whenever any of these occurs — it takes seconds:

| Trigger | Goes under |
|---|---|
| An option is weighed and rejected | §2 |
| A decision is made | §3 |
| Something works because of an earlier decision | §4 |
| A claim proves wrong · something breaks · a wrong turn | §5 |
| You notice *"nothing was watching that"* | §6 |
| Follow-on work is identified | §7 |

---

## 1. The task or problem

What was actually wrong, or what was being built.

**Symptoms as OBSERVED, before diagnosis.** Not the eventual explanation written backwards —
a reader needs to see what the evidence looked like *before* anyone knew the answer, because
that is the position they will be in. If several symptoms later proved to share one cause,
list them as they appeared, separately.

Include what the owner reported in their own words where it later proved significant —
especially where it was doubted and turned out to be correct.

## 2. Solutions considered

Every option seriously entertained, **including ones rejected quickly**. For a triage, every
**hypothesis** entertained about the cause.

The rejected options routinely carry more information than the chosen one.

**Two lists are required:**

**(a) Hypotheses or options weighed** — with how each was resolved. For a triage, a table of
hypothesis → outcome works well.

**(b) Explicitly refused — do not re-propose.** Options the owner ruled out by *decision*
rather than by evidence. Record them with their reasoning so they are never raised again.
This is one of the highest-value parts of the document: without it, the same rejected idea
returns every few months and costs the same argument.

⚠ **If this was not recorded at the time, write `NOT RECORDED` and say what the version
history does or does not show.** Never reconstruct a deliberation that may not have happened.
An admitted gap is honest; an invented rationale is a fiction that will later be trusted —
including by the person who wrote it.

## 3. The chosen solution, and why the others were ruled out

The decision **and its reasoning**. For each significant rejected option, why.

This is what stops a settled question being relitigated months later, and what lets someone
else — or you, with the context gone — understand a choice that looks wrong without it.

Where a decision was a **trade rather than a right answer**, say so and name both sides.

## 4. What went right

Not a consolation section. Specifically:

- **Things that worked because of a prior decision** — a guard that fired, a backup that
  existed *and had been verified*, a rule that blocked something harmful, a second access
  path that was available when the first failed.
- **Design properties that limited the damage**, even if nobody was thinking about them at
  the time.

These are the parts of the system earning their keep — and the evidence for keeping them
later, when they look like overhead.

## 5. What went wrong, and how it was mitigated

Wrong turns, false starts, claims that proved untrue, damage caused, time lost.

⚠ **Blameless in TONE, complete in CONTENT.** *"A cause was asserted before being tested"* is
a mechanism worth recording. Softening it to *"some hypotheses were explored"* removes the
lesson and leaves the failure mode intact.

**The test: would someone reading this avoid the same failure?** If the wording makes that
impossible, it is too soft.

**Separate two kinds:**
- **Failures of execution** — mistakes made during the work
- **Systemic failures** — ways the system itself misled, hid something, or failed to warn

The systemic half is usually the more valuable, and it feeds §6.

For each, note how it was mitigated — **or that it was not**.

## 6. What would have caught this sooner

⚠ **NOT the fix. The DETECTION.**

Ask one question: *what signal, if anything had been watching it, would have surfaced this
before it became a problem?*

**Three valid shapes — label which applies:**

**(a) A signal that ALREADY EXISTED and nothing was reading.**
The most common, and the most damning. Name the exact source, say what it said, and say what
it would have cost to read. If it was free and nobody read it, say so plainly.

**(b) A signal that did NOT exist and should.**
What would have to be built. Be concrete enough to act on.

**(c) A verification or test discipline that would have exposed it.**
Not a signal but a practice — inducing a failure to prove an alarm fires, testing a restore,
checking a claim against a second source. Often the answer when monitoring existed but was
never proven to work.

### Distinguishing the fix from the detection

> Replacing a failing part is the **fix**.
> Noticing it three weeks earlier is the **improvement**.

**The test: could someone act on this entry *before* the next incident?** If not, it is
restating the remedy and has not been thought about yet.

### Also record: alert paths that exist but were never verified

**An alarm nobody has tested is an assumption, not a safety net.** If the incident revealed a
notification that *should* have fired and did not, that belongs here — it is usually the
cheapest fix available.

### When this section is legitimately empty

A clean install, a policy change or a decommission where nothing went wrong and no latent
condition existed. **Even then, prefer the forward-looking form:** *what would tell us if
this degrades later?*

Write `N/A — <reason>` and mean it.

⚠ **An empty §6 on a triage project is almost always a §6 nobody thought about.** If
something broke, something failed to warn you first. Find it.

## 7. Final state, and follow-on work

Where things actually ended — **measured, not assumed**.

**Follow-on work**, each marked `proposed` · `scheduled` · `done` · `declined` · `deferred`,
with a pointer if it became its own project and a reason where it was declined or deferred.

⚠ **A follow-on that is neither scheduled nor declined is an open loop.** Say which it is —
*"we should probably…"* with no status is how work quietly disappears.

---

## Related

Other postmortems sharing this project folder, and why they are separate.
