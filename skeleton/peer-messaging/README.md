# skeleton/peer-messaging — sessions that message each other

Two files, for two different readers. The concepts and the reasons are in
[E19 · Agents that talk to each other](../../guide/examples/E19-agents-that-talk-to-each-other.md).

| File | Who reads it | Copied into repos? |
|---|---|---|
| [`PEER-MESSAGING.md`](PEER-MESSAGING.md) | **Every participating session — it is the standard**: naming, the six rules (including no cross-session permission laundering), the log, versioning | **Yes** — each repo tracks its own copy at `docs/peer-messaging/PEER-MESSAGING.md`; `bootstrap.sh` seeds it |
| [`QUICKSTART.md`](QUICKSTART.md) | **A session joining an operator's existing messaging** — read once, by link, then followed step by step | **No** — give the session its raw URL; it installs the standard, not this |

**Giving a new session the link:**
`https://raw.githubusercontent.com/optiquity/optiquity-personal-sre/main/skeleton/peer-messaging/QUICKSTART.md`

⚠ **The quick start never restates a rule** — it points at the standard's sections. A rule change is
a new version of the standard, minted only in this repo; the quick start follows it.
