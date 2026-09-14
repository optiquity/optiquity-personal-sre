# design — the phase before the work

Templates and rules for a design pass, plus the one rule that makes it stick.

| File | What it is |
|---|---|
| [`RULES.md`](RULES.md) | Whether / when / where / which form |
| [`TEMPLATE-LONG.md`](TEMPLATE-LONG.md) | Full pass — multiple machines, security, storage, persistence, anything hard to undo |
| [`TEMPLATE-SHORT.md`](TEMPLATE-SHORT.md) | Small, reversible, low-blast-radius work |

**Pairs with [`../postmortems/`](../postmortems/).** Design is prospective, the postmortem is
retrospective, and they feed each other in both directions.

Explained in **[04 · Structure](../../guide/04-structure.md)**; the governing principle is in
**[03 · Governance](../../guide/03-governance-rules.md)**.

---

## Why this exists

**A project can be delivered, work correctly, and still be incomplete.**

The case that produces this practice, in one form or another, happens to everyone: an
OS-level configuration change is made, verified, and closed. It works. Months later the
platform has silently reverted it and **nothing noticed** — there was no check that the change
persisted, because durability was never stated as a requirement, so was never designed for,
so was never tested.

The work was not *wrong*. It was **functional but not durable**, and nothing in the process
asked the difference.

## The two sections that carry it

**§ Durability — what can silently undo this?** OS updates, vendor agents, another config
tool, a rebuild, a restore, the machine being replaced. If the answer is *"it would be
silently undone"*, the design is incomplete until that is prevented or detected.

**§ Detection — how would we know it stopped working?** Name the signal, say whether it exists
yet, say what looks at it. ⚠ *"We'd notice"* is not an answer. And **a monitor watching the
wrong layer is worse than none, because it produces confidence** — reachability is not
function.

## The one about constraints

⚠ **"Remove the constraint" is not a design verdict**, and proposing it repeatedly is that
section failing.

Constraints are usually decisions someone already made for reasons that outlive the project —
a platform edition they chose, hardware they own, a risk they accept. Treating the constraint
as the problem is the shortest path to a clean design and the fastest way to be useless. An AI
operator reaches for it by default, because removing a constraint makes the design tidy.

Three honest answers: **impossible as constrained**, **possible with effort**, or **possible
but not worth the effort**. Pick one and defend it. Raise a constraint for revisiting *once*,
with the cost quantified — then design within it.

## The one about changing your mind

Design docs carry **`design-version`**, independent of the template's version. Revising an
agreed design is a version bump plus a line of reasoning in the revision log — **not a rewrite
and not an admission.**

⚠ That is deliberate. **If changing a design is expensive, known-worse designs survive.** The
cost of a refactor is visible — links, references, renames — while the cost of a worse design
is diffuse, so the comparison feels lopsided when it is not.

**Leave known problems where impact is low; refactor where it matters** — where behaviour will
be silently wrong, or where staying safe depends on someone remembering a quirk. And if you
start a refactor, **finish it: a half-updated set of references is worse than none.**

---

## Install it

**1. Copy this folder** into your repo — `docs/design/` works well. It is infrastructure, not
a project: it owns the *practice*, while design docs live at `docs/<project>/DESIGN.md`.

**2. Add a rule to your operator's rules file**, naming **when to read it** — not merely where
it lives:

```markdown
NN. **Every project gets a design pass BEFORE the work. The rules live in
    `docs/design/RULES.md` and must be RE-READ, never recalled from memory.**

    Read that file at each of these moments:
    - When a project moves to `open` — the design doc is created THEN, and agreed
      before implementation begins
    - When choosing between the short and long form
    - When a project is reopened or gains follow-on work
    - When a postmortem's "what would have caught this sooner" names a consideration
      the design phase should have forced — it becomes a template prompt, with a
      version bump
```

**3. Add a playbook route** so starting a project routes through it.
