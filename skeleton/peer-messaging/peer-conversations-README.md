# docs/peer-conversations/

One file per peer session this repo has talked to, named for the peer
(`<machine>-<repo>.md`). **Each side writes its own view** — these are not shared transcripts,
because each session can only vouch for its own half.

Standard: `<framework-dir>/skeleton/peer-messaging/PEER-MESSAGING.md` · rule: see this repo's
rules file.

**What to log — the bar:** an exchange that **changed shipped output, produced a finding, or needs
the operator.** Not every message; routine acknowledgements are noise. Expect to log a minority of
exchanges.

Every entry ends with a **`Needs <operator>:`** line, even when the answer is "nothing" — that is
the field they scan, and a read-only briefing command collects them across all peers.

```markdown
## <date> — <subject>

**With:** <peer-name> · **Direction:** they asked / I asked

**Asked:** <the request>
**Decided:** <the outcome, and which side owns what>
**Corrections in flight:** <anything either side got wrong and fixed>
**Needs <operator>:** <a decision, or "nothing">
```
