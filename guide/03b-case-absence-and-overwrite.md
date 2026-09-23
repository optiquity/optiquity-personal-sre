# 03b · Case study — auditing damage: absence is only half the question

> A worked example following [03 · Governance rules](03-governance-rules.md), and a companion to
> [03a · Four wrong causes](03a-case-four-wrong-causes.md). Generalised from a real fleet.
>
> 03a is about diagnosing a fault. This is about the step immediately after: **establishing what
> the fault actually damaged**, before deciding what to restore.

---

## The short version

A configuration manager applied a **four-month-old snapshot** of eight entries over a live home
directory. The obvious question is *what did it destroy?*

The audit asked: **which files existed before and are missing now?** It came back with a clean,
confident answer: three files identical, three directories intact, two files damaged.

⚠ **That audit was wrong, and not because the comparison was wrong — because the question was.**
An overwrite **removes nothing**. A file replaced with an older version is present, correctly
named, the right type, and completely wrong. *Every absence test in the world reports it as fine.*

The gap was caught by someone asking a question the audit had not: *"is there anything else in the
backup I need to restore?"*

---

## The two questions

| Question | Catches | Misses |
|---|---|---|
| **What existed then and is gone now?** | deletions, truncations to nothing | ⚠ **every overwrite** |
| **What differs from the known-good copy?** | overwrites, silent reverts | nothing — but see below |

The second question alone is not usable either, for a reason that matters: **a live system changes
legitimately.** Comparing a config directory against a week-old snapshot produced roughly 1,800
differing files, essentially all of them normal application activity. *A test that flags everything
flags nothing.*

---

## The test that worked

**Differs from the known-good copy AND carries the damage's timestamp.**

The bad run happened in a known window. Anything it wrote carries a modification time inside that
window. Intersecting the two questions gives a precise answer:

```
directory A   0 files both differing and stamped in the window
directory B   0
directory C   0
```

Three directories cleared in one pass, with evidence, and no manual review of 1,800 diffs.

### ⚠ The timestamp alone is a trap

It is tempting to skip the comparison and just list everything modified in the window. On this
system that returned **144 files** — and almost all of them were innocent: a routine repository
pull that ran the same evening, and a handful of package installs.

> **A timestamp tells you a file was written. It does not tell you it was damaged.**

Used alone it produces a long list of false positives, and the natural response to a long list of
false positives is to stop reading it.

---

## Why the first answer felt so convincing

This is the part worth internalising. The absence test was:

- **correctly executed** — the comparison logic had no bug;
- **cleanly reported** — three categories, unambiguous counts;
- **entirely consistent** with the damage that had already been found.

⚠ **It produced a confident, tidy, wrong-shaped answer**, and nothing inside the audit could have
revealed that, because the limitation was in the question rather than the method. *A well-executed
answer to the wrong question is more dangerous than a messy answer to the right one* — it ends the
investigation.

---

## The transferable rule

> ⚠ **When auditing damage, enumerate the SHAPES of damage before choosing a test.** Deletion,
> overwrite, truncation, permission change, and partial write are different events, and a test
> built for one is silent on the others.

A practical checklist for "what did this bad change do?":

1. **What is missing** that was present before?
2. **What is present but different** from the known-good copy?
3. **What is present, identical in content, but different in mode, owner, or link target?**
4. **What is new** that should not exist?
5. ⚠ **Which of those can this comparison actually see?** — state it explicitly, because the
   answer is usually "not all of them".

**Then bound the result with an independent axis** — a timestamp window, a known-bad revision, a
process's write log — so the answer is short enough to read.

---

## The second finding: the record was wrong too

While deciding what to delete afterwards, one entry was listed as junk to remove. A single command
against the configuration manager showed it was a **live deployment target on every machine** —
deleting it would have been undone on the next run, and the prose describing it as junk had been
written by someone reading an earlier note rather than querying the system.

⚠ **The audit's own notes had become a source of truth without ever being verified as one.** The
rule that prevents this is mechanical, not attitudinal:

> **Before acting on a claim about system state, name the command that produced it.** If you cannot,
> it is a memory, and memories are what this whole class of failure is made of.

---

## What it cost

Nothing, in the end — the second test cleared all three directories and confirmed the original
two-file conclusion. **The damage really was two files.**

But that outcome was luck, not process. ⚠ **The audit would have reported exactly the same clean
result whether or not an overwrite existed**, and the only reason anyone knows the difference is
that a human asked a better question than the tool had been pointed at.

---

Next: [04 · Structure](04-structure.md).
