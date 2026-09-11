# docs/peer-conversations/ — template

Copy to `docs/peer-conversations/README.md` in **your own repo**, and add the directory to
`.gitignore`. One file per peer, named for the peer session.

    docs/peer-conversations/<peer-name>.md

**Each side writes its own view** — not a shared transcript. Two half-views, each authored by the
side that can vouch for it.

**Gitignored by default.** These files record your operator's infrastructure, working habits and
half-finished decisions. **A repo's visibility can change, and git history keeps whatever you
committed.** Keeping them out of history is the safe default; commit them deliberately or not at all.
*Caveat emptor: ignored files are not backed up by git and are not reviewable.*

**What to log:** an exchange that changed shipped output, produced a finding, or needs the operator.
Not every message. Every entry carries a **`Needs <operator>:`** line even when the answer is
"nothing", and is **closed with its evidence** once resolved — a stale open item is a false
outstanding.

```markdown
## <date> — <subject>

**With:** <peer-name> · **Their version:** <n> · **Direction:** they asked / I asked

**Asked:** <the request>
**Decided:** <the outcome, and which side owns what>
**Verified against:** <what you checked, and at which version — omit if nothing was verified>
**Needs <operator>:** <a decision, or "nothing">
```

Standard: `PEER-MESSAGING.md` beside this file. **Copy that into your repo too** — a repo holding the
standard is a propagation node, so the next repo can bootstrap from you.
