# Design — <project or thread>

```
status:           draft | agreed | superseded
design-version:   1          # THIS document's version — bump when the design changes
template-version: 1.0        # which template version it was written against
form:             long
opened:           <YYYY-MM-DD>
agreed:           <YYYY-MM-DD or em-dash>
```

> **When this is created, which form to use, and how it is named are governed by
> [`RULES.md`](RULES.md).** This file owns only *what to think about*.
>
> **Pairs with** `docs/<project>/POSTMORTEM.md`. Sections 2–4 here become the postmortem's
> §2 and §3 directly — **written once, at the point they are actually known.**

---

## How to use this

**Every section gets an answer. `N/A` is allowed and must carry a reason.**

A section left blank means nobody thought about it. A section saying `N/A — <reason>` means
somebody did, and decided it did not apply. Those are different, and only the second is due
diligence.

⚠ **The failure mode to design against is reflexive `N/A`.** A template long enough to be
thorough is long enough to be skipped, or filled in defensively. If the reasons start reading
like *"not relevant here"* across the board, the form is being performed rather than used —
drop to the short form and be honest about it.

---

## 1. The requirement

What this must do, in terms of outcome rather than implementation. One paragraph.

**What does "done" mean?** State it now, because §5–§8 exist to test whether that definition
is complete. *"It works"* is almost never a sufficient definition of done — the rest of this
document is the argument for why.

## 2. Constraints, and an honest feasibility verdict

**List the constraints you are actually working under** — platform edition, hardware, budget,
downtime tolerance, a decision already made and not up for revisiting.

Then, for the requirement **as constrained**, give one of three verdicts and defend it:

| Verdict | Meaning |
|---|---|
| **Impossible as constrained** | It genuinely cannot be done. Say what would have to change, then stop — do not design around a wish |
| **Possible with effort** | Achievable, at a stated cost. Say what the effort is |
| **Possible but not worth it** | Achievable and not justified. Say what the cheaper alternative gives up |

⚠ **"Remove the constraint" is not a verdict, and proposing it repeatedly is a failure of
this section.** The constraint is usually a decision someone already made for reasons that
outlive this project — a platform edition they chose, hardware they own, a risk they accept.
Treating it as the problem is the shortest path to a clean design and the fastest way to be
useless.

**If you believe a constraint should be revisited, say so ONCE, with the cost of keeping it
quantified — then design within it.** Raising it again is not diligence; it is avoidance of
the real work, which is determining which of the three verdicts is true.

## 3. Alternatives considered

Every approach seriously weighed, with why each was rejected.

**This section becomes the postmortem's §2** — so writing it properly here means the
postmortem inherits it rather than reconstructing it months later, when the reasoning is
gone. It is the single highest-leverage section in this document.

Include options rejected quickly; the fast rejections are often the ones nobody remembers
were considered at all.

## 4. Chosen approach

What will be built, and why this over the alternatives.

Where the choice is a **trade rather than a right answer**, say so and name both sides. A
future reader finding this decision surprising deserves to know it was surprising at the time
too.

## 5. Durability — what can silently undo this?

⭐ **The section whose absence most often turns a working change into an incomplete one.**

Ask specifically:

- Can an **OS or vendor update** revert it? (Service configurations, registry policy, power
  settings, firewall rules — all of these are routinely "repaired" by the platform)
- Can **another tool** overwrite it? A config manager, an installer, a vendor agent?
- Does it survive a **reboot**? A **rebuild**? A **restore from backup**?
- Does it survive the **machine being replaced**?
- Is it recorded anywhere that a future operator would look, or only in the live system?

**If the answer to any of these is "it would be silently undone", the design is incomplete
until either that is prevented or §6 detects it.**

A change that can be reverted with nobody noticing is *functional*, not *done*.

## 6. Detection — how would we know it stopped working?

⭐ **Answer this before building, not after something breaks.**

- What **signal** says it is still working? Does that signal exist yet, or must it be built?
- What signal says it has been **undone** (per §5)?
- Who or what **looks** at that signal, and how often?
- What does the failure look like from **outside** — would anything user-visible change, or
  would it fail silently?

⚠ **"We'd notice" is not an answer.** Name the mechanism.

⚠ **A monitor that watches the wrong layer is worse than none**, because it produces
confidence. Reachability is not function: a host that answers pings while doing no work is
the classic shape of this mistake.

*(Whatever this section misses, the postmortem's §6 will eventually find — and that finding
should come back here as a standing prompt.)*

## 7. Testing — how do we verify it, including the alarm?

Two distinct questions, both required:

**(a) How is the work verified?** What proves it does what §1 says — by function, not by
readback. A setting accepted is not a setting working.

**(b) How is the DETECTION verified?** How do we prove the §6 signal actually fires?

⚠ **An alarm nobody has tested is an assumption, not a safety net.** The only proof is
**inducing the failure** and watching it fire. A check that has never gone red is not a
check.

## 8. Reliability — behaviour when a dependency is unavailable

What does this depend on — network, another host, a service, a share, an external API?

For each: when it is unavailable, does this **degrade** or **fail**? Does it fail *loudly* or
*silently*? Does it recover on its own, or need a human?

⚠ Pay attention to anything that **blocks** rather than errors. A component waiting forever
on an unavailable dependency is the hardest kind of failure to diagnose, because nothing
reports anything.

## 9. Fault tolerance — what survives one thing breaking?

Single points of failure, named explicitly. For each, what happens: degraded service, total
loss, or silent wrongness?

**Where redundancy exists, state how much margin it gives and what consumes it.** Redundancy
you have already spent is not redundancy.

## 10. Rollback

Can this be undone? By what procedure, and at what cost?

- Is rollback **tested**, or assumed?
- Is there a point after which rollback stops being possible? Name it
- What does rollback lose — data, configuration, time?

⚠ **A design with no rollback is not disqualified, but it must say so explicitly**, so the
one-way door is walked through deliberately rather than discovered later.

## 11. Blast radius

What does this grant, expose, or reach?

New network exposure · credentials or tokens involved · what a compromise would reach · what
a bug could damage · which other systems are touched.

**Anything that widens reach deserves a sentence on why the widening is necessary.**

## 12. Dependencies, both directions

**What this relies on** — versions, services, hardware, other projects.
**What will come to rely on this** — because that determines how expensive it becomes to
change or retire later.

## 13. Lifecycle and ownership

Who maintains it. When it is revisited. What conditions retire it. Whether it is registered
with whatever tracks updates, backups and health — and if not, why not.

⚠ **A project with no revisit trigger becomes permanent by default**, including the parts
that were meant to be temporary.

## 14. Documentation

What a future reader must be told, and where it will live. Which runbook, which index entry,
which playbook route.

**If the only record of how this works is the live system, it is undocumented** — and the
first thing that changes it will erase the explanation.

---

## Open questions

Anything unresolved at the time of agreement, with who decides and by when. Carry these into
the work rather than letting them dissolve.

---

## Revision log

Every change to an **agreed** design bumps `design-version` and appends a line here. Do not
edit an agreed design in place — the reasoning for the change is as valuable as the change.

- **v1 — <date>** — initial design, agreed.
