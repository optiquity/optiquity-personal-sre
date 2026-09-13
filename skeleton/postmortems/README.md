# postmortems — the practice

Two files to copy into your own repo, plus the one rule that makes them stick.

| File | What it is | When to read it |
|---|---|---|
| [`RULES.md`](RULES.md) | **Whether / when / where / who** — the binding practice | At the lifecycle moments your rules file names |
| [`TEMPLATE.md`](TEMPLATE.md) | **How to write each section** | Whenever writing or appending to one |

Explained in **[04 · Structure](../../guide/04-structure.md)**; the governing principle is in
**[03 · Governance](../../guide/03-governance-rules.md)**.

---

## Install it in three steps

**1. Copy the two files** into your repo — `docs/postmortems/` works well. They are
infrastructure, not a project: this folder owns the *practice*, while the postmortems
themselves live at `docs/<project>/POSTMORTEM.md`.

**2. Add a rule to your operator's rules file** — and make it a rule about **when to read**,
not merely where to look:

```markdown
NN. **Every completed project gets a postmortem. The rules live in
    `docs/postmortems/RULES.md` and must be RE-READ, never recalled from memory.**

    Read that file at each of these moments, every time:
    - When a project moves to `open` — the draft is created THEN, not at close
    - Before appending to one during the work
    - When a project closes, before tidying entries into prose
    - Before writing any retroactive postmortem
```

⚠ **A pointer nobody follows is a dead rule.** Naming the moments is what keeps the practice
alive; "see the postmortem doc" on its own will be skipped within a month.

**3. Add a route in your playbook** so the everyday question lands somewhere:

```markdown
| Learn why a past decision was made, or what was ruled out | that project's POSTMORTEM.md |
```

---

## The shape of it, in one paragraph

A postmortem is **created when a project opens**, not when it closes, and accumulates **dated
append entries** under headings identical to the finished document — so appending *is*
drafting, with no transcription step at the end. It stays **separate from the project's
working record**, which is open-ended and remains; the postmortem is structured and narrow,
and links to that record rather than restating it. Its most valuable sections are precisely
the ones that cannot be reconstructed afterwards: **what else was considered**, **what went
wrong**, and **what would have caught this sooner**.

## The section most people get wrong

**§6 — "what would have caught this sooner" — is about detection, not remedy.**

> Replacing a failing part is the **fix**.
> Noticing it three weeks earlier is the **improvement**.

The test: *could someone act on this entry before the next incident?* If not, it is restating
the fix. The most common honest answer is the most uncomfortable one — **a signal that
already existed, cost nothing to read, and nothing was reading.**
