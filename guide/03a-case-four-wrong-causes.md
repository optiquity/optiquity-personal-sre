# 03a · Case study — four causes, all wrong

> A worked example following [03 · Governance](03-governance-rules.md). Generalised from a
> real incident, with the detail kept deliberately.
>
> It is the **least flattering** page in this guide. The rules in chapter 03 read like
> friction until you watch them absorb a bad afternoon.

---

## The short version

An application on one node started crashing — five times in two days after months of
stability. Its working data lived on a network share served by a NAS.

Over roughly thirty-six hours an AI operator asserted **four different causes**. All four
were wrong. Not one had been tested before being stated. The first cost the owner a working
component, disabled on that advice, for four days.

The real cause was a **failing disk in the NAS**, found in about twenty minutes once anyone
correlated crash timestamps against storage errors: **six of six crashes preceded by a
storage error within ninety seconds**, and both symptoms starting within the same hour after
weeks of silence.

**Assertion had not found it in two days. Measurement found it in twenty minutes.**

What kept a bad afternoon from becoming a bad week was structural, not anyone being careful:
every wrong hypothesis produced *investigation* rather than *action*, because the operator
could not write without approval.

---

## The detailed record

### Timeline

| When | What |
|---|---|
| Day 1, 17:26 | First storage error on the share. Nothing notices |
| Day 1, 17:33 | First application crash — **7 minutes later**. Treated as an application bug |
| Day 2, 02:08 | Second crash, overnight |
| Day 2, 06:04 | An unrelated forced OS update reboots the node, destroying work in progress. This dominates attention for hours and is **not** the cause of the crashes |
| Day 2, 13:41 · 14:23 · 15:38 | Three more crashes |
| Day 2, ~13:00–16:00 | **Causes 1–4 asserted.** Component disabled on bad advice |
| Day 2, 18:15 | Crash on the *upgraded* application version — the "stale version" theory dies |
| Day 3, 00:37 | Storage errors: `Input/output error`, then `No space left on device` — **against a volume with 8 TB free** |
| Day 3, 00:39 | Application faults. Its processes cannot be killed for ten minutes |
| Day 3, ~02:10 | Correlation run. Six of six crashes match. Failing disk identified |

### The four causes, in order

**Cause 1 — "a helper script is stopping the application."**

*How it arose:* a scheduled script interacted with the application, and one crash fell near a
scheduled run. Post hoc, ergo propter hoc.

*What would have disproved it instantly:* reading the file. It contained **no process-control
code of any kind** — no terminate call, no kill, no restart. It was structurally incapable of
stopping anything.

*What it cost:* the owner disabled the component on that advice. It stayed disabled for days,
and with it went the capability it provided. **The correction came only when the file was
finally read — two days later.**

⚠ This is the expensive pattern: an assertion that *sounds* like a finding, acted on by
someone who reasonably trusts it, about a file nobody opened.

**Cause 2 — "OS component corruption."**

*How it arose:* the node had recently applied a large OS update; ~1,980 system libraries had
been replaced on disk while the machine ran for several more days without rebooting. A real
and unusual condition — therefore assumed causal.

*Disproof:* the vendor's own integrity check found nothing. Cost: a long scan.

*The error underneath:* **"something unusual happened" is not "this caused it."** The update
was real, anomalous, and irrelevant.

**Cause 3 — "the NAS, broadly."**

*How it arose:* the share was involved in every crash, so the server was blamed as a whole.

*Disproof at the time:* the operator's **own daily-totals data, gathered an hour earlier**,
contradicted it. The owner ruled the NAS out of scope and was right to on the evidence then
available — a whole-server accusation with no specific mechanism is not a diagnosis.

⚠ **The uncomfortable part:** the failing disk *was* in that NAS. Being directionally right
by accident is not the same as being right. Cause 3 named a machine, not a mechanism, and
offered no test — so it was indistinguishable from a guess and was correctly rejected.

**Cause 4 — "a configuration mismatch."**

*How it arose:* a forwarded port and an application setting looked out of sync.

*Disproof:* the owner had set the value by hand, correctly, and said so. A single read of the
live configuration confirmed it.

### Two further failures of the same kind, later the same night

**Fitting evidence to a story.** The operator explained a slowdown using a change the owner
had **already excluded from direct knowledge** — having said plainly that the slowness
predated it. Restated anyway, because it fit.

**Offering a correlation as a cause without asking for the base rate.** A power-management
behaviour looked compelling: **78% of storage errors occurred inside those windows**. It
collapsed on one question — *how often does that behaviour occur without any error?*
**Roughly 190 times over sixteen months.** The correlation was real; the causation was not.

That question is free, takes one command, and would have prevented a confident wrong answer.

**A claim built on a misread log line.** A "system wake event" was asserted from an
*application* log entry. The system power log showed **zero** such events in that window. The
application had inferred a wake from a network discontinuity.

### What actually found it

Not insight. A table.

```
CRASH             LAST STORAGE ERROR BEFORE     GAP
crash 1           17:33:05                     0.5 min
crash 2           02:07:38                     0.7 min
crash 3           13:41:22                     0.0 min
crash 4           14:22:07                     1.5 min
crash 5           15:38:34                     0.0 min
crash 6           18:13:59                     1.1 min
```

Six of six, both versions of the application, plus **co-onset**: the first storage error and
the first crash fell seven minutes apart after a quiet fortnight.

The disk's own counters then confirmed it: an *uncorrectable errors* attribute at **1 against
a failure threshold of 0**, still incrementing minutes apart; a pre-fail seek attribute
already recorded as having breached; ~53,000 power-on hours. The kernel was logging medium
errors with sense data and taking **~16 seconds of error handling per event**, which stalled
every array the disk belonged to.

⚠ **Meanwhile the NAS's own dashboard displayed the drive as "Healthy"** — while a
world-readable file in its own runtime state classified it as **critical**. The vendor's
software had made the correct judgement. The summary label did not surface it, and nothing
in the fleet read the underlying field.

### What the rules did

**Reads are free; writes need approval.** Four wrong causes produced four *investigations*.
Under a permissive setup they would have produced four *changes* — to a system with a failing
disk and a single parity drive. The one change that did happen (disabling the component) went
through the owner, which is why it was recoverable.

**Approval gates turned assertions into proposals.** The operator could say *"this is the
cause."* It could not act on that. The owner could say no — and did, repeatedly, on grounds
the operator had not weighed.

**The owner's domain knowledge outranked the operator's inference, every time.** Paraphrased
from the record, each of these was correct and each was doubted:

> *"It is not the network adapter — that has been working fine."*
> *"The slowness was happening before that change."*
> *"This is not a VPN problem."*
> *"Never suggest workarounds when you cannot diagnose the real problem."*

That last one redirected the operator from patching a symptom to finding what had changed —
which produced the answer within minutes.

**Write-it-down made the wrongness durable.** Because each hypothesis was recorded as it was
made, including the damage from cause 1, this page exists. Otherwise it would be a vague
memory of "there was some confusion."

### Dead ends worth recording

- **Two probes were themselves invalid.** One reported a backup destination missing; the same
  probe reported the application's *live, actively-writing* data path as missing. The probe
  ran in a session without the credentials to see either. **A probe that cannot see something
  is not evidence that it is absent.**
- A configuration value read back empty because the tool writes it under a **different name**
  than it reads — briefly suggesting a change had been lost when it had not.
- A vendor status page was checked for a platform outage. There was none. Ruling out the
  obvious external cause took two minutes and was worth it.

---

## What to take from it

**Distinguish "I checked" from "I concluded", and make the operator say which.** All four
causes were delivered in the register of a finding. None was one. A fluent operator produces
a plausible cause faster than it can test one — explanation is cheap, verification costs a
command and a wait and a possibly inconvenient result.

**A confident wrong answer is indistinguishable in tone from a verified one.** That is the
core hazard, and no amount of care fixes it. Structure does.

**A wrong cause is not free.** It costs trust, time, and sometimes a working system.

**Read-only-by-default is what makes a fluent operator safe.** Not because it prevents
mistakes — because it prevents mistakes from *becoming actions*. That is the argument of
[10 · Permissions](10-permissions.md), demonstrated.

**When the owner contradicts the operator about their own system, the owner is usually
right.** They hold years of context; the operator holds this session.

**Ask for the base rate.** Every correlation offered as a cause needs *"how often does that
happen without the failure?"* One question, free, and it killed a confident wrong answer here.

**Name a mechanism, not a machine.** "The NAS" is not a diagnosis. "This disk is returning
uncorrectable reads, and here are six crashes within ninety seconds of one" is.

---

Next: [04 · Structure](04-structure.md).
