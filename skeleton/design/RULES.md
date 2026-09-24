# Design-phase rules

These rules answer **whether, when, where and which form**. They do **not** describe what to
think about — that is the templates, which own all section-level guidance.

> **One source of truth.** Guidance on filling in a section lives in the template and appears
> here only as a pointer.

---

## D1 · A design pass precedes the work

Every project gets a design document before implementation begins — not a plan of *steps*,
but a record of *what this must survive*.

**Why this exists:** a project can be delivered, function correctly, and still be incomplete —
because durability, detection and testing were never stated as requirements, so were never
designed for. A change that can be silently reverted with nobody noticing is **functional,
not done**.

## D2 · Two forms, chosen deliberately

| Form | For |
|---|---|
| [`TEMPLATE-SHORT.md`](TEMPLATE-SHORT.md) | Small, reversible, low-blast-radius work |
| [`TEMPLATE-LONG.md`](TEMPLATE-LONG.md) | Anything touching multiple machines, security, storage, persistence of configuration, or anything hard to undo |

**Start short if genuinely unsure.** If an answer turns out long, uncertain or uncomfortable,
**switch to long** — discovering that is the form working, not a failure of judgement.

## D3 · Templates are versioned, and so are the documents

Two independent versions: **`template-version`** (which template a document was written
against) and **`design-version`** (this document's own revision — see D9). The templates evolve as incidents teach us what was
missing, and **a document written against an older version stays valid** — it is not
retroactively wrong.

⚠ **Do not let a template freeze a bad implementation.** If a section is fighting the work
rather than improving it, that is a finding about the template. Record it and revise.

## D4 · Every section gets an answer; `N/A` carries a reason

A blank section means nobody thought about it. `N/A — <reason>` means somebody did and
decided it did not apply. **Only the second is due diligence.**

⚠ Reflexive `N/A` across the board means the form is being performed rather than used. Drop
to the short form and be honest.

## D5 · Naming and location

`docs/<project>/DESIGN.md` by default. Where a project has multiple independent threads, use
`DESIGN-<slug>.md` — **matching the postmortem's slug**, so a design thread and its
postmortem thread are visibly paired.

## D6 · The design feeds the postmortem

The design's *alternatives considered* and *chosen approach* become the postmortem's §2 and
§3 **directly**.

⚠ **This is the structural fix for the postmortem's weakest section.** Written at the end,
§2 is reconstruction — or `NOT RECORDED`. Written here, at the moment the alternatives are
actually live, it is simply inherited.

## D7 · The postmortem feeds the design template

When a postmortem's *"what would have caught this sooner"* names a consideration the design
phase should have forced, **that becomes a prompt in the template** — with a version bump.

**This is the loop that makes the practice improve rather than merely persist.**

## D8 · Retrofit only where it will be used — **mirrors `../postmortems/RULES.md` R8**

**Existing completed projects do not get design documents.** **Projects already open when you
adopt this practice do not get a back-dated one either**: a design doc exists to settle
questions *before* the work, and for work already under way that moment has passed. A design
written afterwards would be reconstruction dressed as foresight.

A project that is **reopened** or gains **follow-on work** gets one — covering either the new
work alone or the whole system, whichever the situation calls for.

Two limits, both hard:

- ⚠ **No design doc that will not be used.** A document written to satisfy a rule is
  overhead pretending to be diligence.
- ⚠ **No design doc with incomplete necessary information.** If the durability, detection or
  constraint answers cannot be established for pre-existing work, **either establish them or
  do not write the document.** A design doc with hollow sections is worse than none: it
  implies the questions were answered.

⚠ **This mirrors R8 deliberately.** The design and postmortem practices are a loop (D6/D7); two
halves with different scope rules drift until one stops feeding the other.

## D9 · Revising an agreed design

A design doc carries **`design-version`**, independent of `template-version`.

⚠ **A version bump is for a MAJOR change. A small correction is an edit.**

**Bumping on every small fix creates churn and conflicting histories — and an AI operator reading a
long revision log routinely misreads which version is current.** The version must mean something,
or it means nothing.

| The change | What to do |
|---|---|
| **A fact is wrong** — a stale figure, a misstated tool state, a dead link, a typo | **Edit in place.** No bump, no entry |
| **A finding or conclusion changes** | **Bump + a revision entry** |
| **New work** — the project is reopened or gains follow-on work | **Bump + a revision entry** |
| ⚠ **Unclear which it is** | **ASK THE OWNER.** Do not decide this one alone |

**The test: does the change alter what someone would DO after reading it?** Correcting a fact that
leaves the conclusion standing is an edit. Changing the conclusion is a revision.

**Never live with a design you now know is wrong** — but *"wrong"* means the design, not a
sentence in it.

```markdown
## Revision log
- **v2 — <date>** — <what changed> · <why> · <what it obsoletes>
```

**The point of versioning is to make changing your mind cheap.** If revising a design means
admitting v1 was wrong and rewriting around it, the pressure is to leave it standing. If it
means one version bump and one line of reasoning, the pressure disappears.

⚠ **Do not follow a known-worse path to avoid churn.** The cost of a refactor is *visible* —
links, references, renames — and the cost of a worse design is *diffuse*. That makes the
comparison feel lopsided when it is not, and it is a standing bias of an AI operator, which
will reliably prefer the change that touches fewer files.

**The judgement: leave known problems where impact is low; refactor where it matters.**

| Leave it | Refactor it |
|---|---|
| Cosmetic inconsistency, an awkward name, a stale numbering scheme | A design that will silently produce wrong behaviour |
| Anything whose only cost is tidiness | A structure that makes correctness impossible or verification impractical |
| A wart that is documented and understood | Anything where the workaround must be remembered to stay safe |

⚠ **A partial refactor is worse than none.** Half-updated references produce mixed signals
and two competing sources of truth — the exact condition this practice exists to prevent.
**Scope it before beginning, then finish it or revert it.** Do not discover the blast radius
halfway through.

---

## The lifecycle

```
DESIGN  ──►  WORK  ──►  POSTMORTEM
  ▲                          │
  └──────────────────────────┘
        D7: §6 findings become standard prompts
```

Both documents are created when a project **opens**. The design is agreed before work starts;
the postmortem accumulates entries throughout and is finalised at close.


---

## Template revision log

⚠ **Record what changed between template versions**, so a document's `template-version` resolves to
an actual difference rather than a bare number. **Mirrors the postmortem side.**

| Version | Date | What changed |
|---|---|---|
| **1.2** | 2026-09-23 | §1 asks for **the end state as the owner will check it**; an **open question blocks** the work that depends on it; testing asks for **the planted defect that proves each test fails**. Two postmortem §6 lessons made standing prompts (D7) |
| **1.1** | <date> | ⚠ **Raised the bump threshold** (D9), matching the postmortem side |
| **1.0** | <date> | Initial |
