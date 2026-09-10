# ~/.claude/peer-conversations/ — template

Copy to `~/.claude/peer-conversations/README.md` on each machine. **Not seeded into any repo** — the
whole point is that these logs never live in one.

    ~/.claude/peer-conversations/<your-repo>/<peer-name>.md

`<your-repo>` is the repo of the session doing the logging; every session on the machine shares this
tree, so that segment keeps them apart. **Write only inside your own subtree** — reading a peer's is
fine and useful for the §0 check, writing into one is a cross-repo write by another name.

**Why user level:** repo visibility is mutable. A private repo that later goes public carries its
whole conversation history with it, and deleting the files then does not help because git history
keeps them. One location also removes the need to check whether a repo is published before knowing
where to log. **Durability is your home-directory backup — verify it actually covers this path.**

**What to log:** an exchange that changed shipped output, produced a finding, or needs the operator.
Not every message. Every entry ends with a **`Needs <operator>:`** line even when the answer is
"nothing", and is **closed with its evidence** once resolved — a stale open item is a false
outstanding.

```markdown
## <date> — <subject>

**With:** <peer-name> · **Direction:** they asked / I asked

**Asked:** <the request>
**Decided:** <the outcome, and which side owns what>
**Corrections in flight:** <anything either side got wrong and fixed>
**Needs <operator>:** <a decision, or "nothing">
```

Standard: `skeleton/peer-messaging/PEER-MESSAGING.md`
