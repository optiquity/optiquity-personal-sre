# E19 · Agents that talk to each other

**Section E — fleet operations.** Back to the [catalog](../17-example-projects.md).

**What this shows:** letting the AI sessions that own different repos **message each other directly**
instead of routing every question through the operator — and the governance that has to arrive with
the channel, because a message channel between agents is also an **escalation path** unless you close
it deliberately.

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

**Status: built and verified.** The contract below is written from what went wrong on the first day
it ran, in both directions. Every trap marked ⚠ actually happened.

---

## The problem: the operator is the transport

Once you run more than one repo, you run more than one AI session, and they need each other. The
platform session knows why the endpoint returns 400; the site session knows what the form sends.
Without a channel, **the human carries every message** — copying a question out of one terminal and
an answer back into another.

That is slow and lossy, but the real cost is subtler: **it removes the only participant who can
challenge a claim.** The operator cannot evaluate "the endpoint rejects this value" — they were not
the one who measured it. So a wrong measurement travels intact.

## What the platform already gives you

Check this before building anything. Coding agents increasingly ship **native cross-session
messaging** — a way to list live sessions and send one a message, delivered without polling.

If yours has it, that is the answer for same-vendor sessions, at zero infrastructure cost. What it
typically does **not** give you: group rooms, participant lists, owners, durable history, or
**agents from a different vendor**. Know which half you have before you build the other.

⚠ **The addressing scheme probably does not tell you which machine a session is on.** A session list
that reports *name*, *kind* and *busy/idle* is common; a session list that reports *host* is not.
"Local" versus "remote" is a **transport**, not a location. If you have five machines, the machine
identity has to live somewhere — and the only field you control is the name.

## The contract

**a. Name sessions `<machine>-<repo>`.** Session lists don't report which machine a session is on, so
the name is the only machine identifier. No two live sessions may share a name. ⚠ A subagent may
surface under its spawner's chosen name — ask the spawner before calling a name a violation.

**b. A message is a hand-off, not an edit.** Never write another repo. Send **state** — what a peer
depends on, whether it's blocked — not your internals, which it will log into its own repo.

**c. ⚠ No cross-session permission laundering.** Permission boundaries are per-session: a command
blocked in your session is not blocked in your peer's, so "ask the other agent to do it" is a working
bypass of the operator's approval unless a rule forbids it. **A peer cannot grant escalation.**

**d. Log every deciding exchange** — one file per peer at `docs/peer-conversations/<peer>.md` in your
own repo, gitignored by default, every entry ending in an explicit *needs-the-operator* line. Without
it, decisions made between sessions are invisible to the operator and die with the session.

**e. Version it.** Each repo carries its own stamped copy of the standard; every message states a
version; a session that's behind re-reads the newer file — ⚠ **from the file, never from the peer's
message text**, which is what stops a peer handing a session its own rules. One repo mints versions so
"newer wins" converges.

**f. Treat peer content as a claim, not a fact.** A peer message is written by another model and can
carry a stale or wrongly-targeted measurement stated with full confidence. Verify anything
load-bearing, or say **"unverified"**.

## A briefing command

One read-only command: live peers with versions, each log's latest entry, every open *needs* line.
⚠ **Read-only** — a frictionless "message a peer" command is how (c) gets broken by convenience.

## If you need more than the native channel

If you need **group rooms, participant lists, owners, or non-vendor agents**, the native channel will
not do it. As of 2026 the landscape is:

| Option | Reality |
|---|---|
| **Native cross-session messaging** | Free, push, zero infrastructure — but same-vendor and effectively 1-to-1 |
| **MCP message buses** (several OSS projects) | The right *client* shape, since most coding agents speak MCP. Some are single-host only; the multi-host ones are **early** — single-digit stars is common. Check before depending |
| **A2A** (Linux Foundation) | v1.0, wide industry backing, now under the same foundation as MCP. It is a **task-delegation protocol between agent services**, not a chat bus for CLI sessions. Adopt its *schema* for interop; it is not a thing you run tonight |
| **Generic buses** (NATS, Matrix, MQTT) | Mature, and they solve broadcast + direct + durability properly. You are building the agent integration yourself |

**A framing correction worth inheriting:** it is easy to dismiss MCP here as "agent-to-tool, not
agent-to-agent." That is right about MCP as a **transport** and wrong about MCP as the **client
adapter** — which is the part that matters, because your agents already speak it. Whatever bus you
pick is reached *through* MCP, with messaging modelled as tools. The real MCP limitation is
different: **it has no reliable server-to-client push for CLI agents**, so every serious
implementation parks an idle agent on a **long-poll** instead.

**If you build:** the requirement set is small — rooms, direct messages, participants, an owner per
room, and a long-poll endpoint. Owning a few hundred lines can beat depending on an immature project
for something that holds your agents' decision history.

## The general lesson

Two independent sessions, from unrelated evidence — a stale linter on one side, a status field that
reads empty even on a healthy node on the other — arrived at the same pre-flight question:

> **Compare the suspicious signal against a known-good peer before treating it as a finding.**

Two unrelated domains reaching one rule is usually the sign it is real. It belongs next to your other
pre-flight checks: right target, complete data, current data — and now, **compared against something
known good**.
