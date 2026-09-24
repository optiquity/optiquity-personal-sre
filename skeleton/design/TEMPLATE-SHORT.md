# Design — <project or thread>

```
status:           draft | agreed | superseded
design-version:   1          # THIS document's version — bump on a MAJOR change only (D9)
template-version: 1.3        # which template version it was written against
form:             short
opened:           <YYYY-MM-DD>
agreed:           <YYYY-MM-DD or em-dash>
```

> **When this is created, which form to use, and how it is named are governed by
> [`RULES.md`](RULES.md).** Sections 2–3 become the postmortem's §2 and §3.
>
> **Use the short form for small, reversible, low-blast-radius work.** If any answer below
> turns out to be long, uncertain, or uncomfortable — **switch to
> [`TEMPLATE-LONG.md`](TEMPLATE-LONG.md).** Discovering that is the form doing its job, not a
> failure.

---

**Every section gets an answer. `N/A` is allowed and must carry a reason** — a blank means
nobody thought about it; `N/A — <reason>` means somebody did.

## 1. The requirement, and what "done" means

One paragraph. State the outcome, and state the condition that makes it finished.

**Then the end state, as the owner will check it:** a tree, a table, a sample of the output. The
result, not the steps. A wrong layout shows in one diagram and hides in a paragraph.

## 2. Constraints, and the feasibility verdict

What you are working under, then one verdict, defended:
**impossible as constrained** · **possible with effort** · **possible but not worth it**.

⚠ **"Remove the constraint" is not a verdict.** If you think a constraint should be
revisited, say so once with the cost quantified, then design within it.

## 3. Alternatives considered, and the choice

What else was weighed, why not, and what was chosen. *(Becomes postmortem §2 and §3.)*

## 4. Durability — what can silently undo this?

⭐ OS or vendor updates · another tool overwriting it · reboot · rebuild · restore · machine
replacement.
**Is the file you are changing generated?** Then change what generates it.

**If anything here would silently undo it, either prevent that or make §5 detect it.**

## 5. Detection — how would we know it stopped working?

⭐ Name the **signal**, whether it exists yet, and what looks at it.

⚠ *"We'd notice"* is not an answer.

## 6. Testing — the work, and the alarm

How the work is verified **by function**, and how the §5 signal is proven to fire — by
**inducing the failure**. A check that has never gone red is not a check.

**And prove each test can fail:** for each rule the work enforces, name the planted defect that
makes its test fail. A test nobody has seen fail is as unproven as an untested alarm.

## 7. Rollback

Can it be undone, how, and at what cost? If it cannot, **say so explicitly** so the one-way
door is deliberate.

## 8. Anything else that matters here

Blast radius, dependencies, ownership, documentation — whichever apply. If two or more need
real answers, **this is long-form work.**

---

## Open questions

Unresolved items, who decides, by when.

⚠ **An open point blocks the work that depends on it.** A question put to the owner and not
answered is still open: ask again, and build nothing that depends on it until it is.

---

## Revision log

⚠ **Not every change.** A **major** change to the design bumps `design-version` and appends a line
here; **a small correction — a wrong fact, a stale figure, a typo — is just an edit.** Bumping on
every fix creates churn and conflicting histories, and a long revision log gets misread. **If it is
unclear which one this is, ask.** Full rule: [`RULES.md`](RULES.md) D9.

- **v1 — <date>** — initial design, agreed.
