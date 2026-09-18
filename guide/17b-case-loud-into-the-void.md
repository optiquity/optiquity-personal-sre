# 17b · Case study — it failed loudly, for six days, into a file nobody reads

> A worked example following [17 · Monitoring](17-monitoring.md), and a companion to
> [17a · Six green checks over one broken system](17a-case-monitoring-the-proxy.md).
> Generalised from a real fleet.
>
> 17a is about probes that measure the wrong thing. This one measured the **right** thing,
> reported it **correctly**, and still nobody found out for six days.

---

## The short version

A nightly database backup ran on a schedule, wrote to network storage, and was written with
unusual care. Its own header says so:

> *Hardened: logs locally and **fails loudly** — non-zero exit plus a log line — if the target is
> unreachable or not writable. **Never a silent exit-0 skip.***

Every word of that is true, and it was true on all six nights it failed.

```
SKIP: target unreachable or not writable. No backup taken.     exit 2
```

It was discovered only because an unrelated upgrade required a fresh backup, and someone went
looking for one. The newest was six days old.

⚠ **The author had correctly identified the failure mode — a silent skip — and correctly fixed it.
The fix produced a loud skip into a local log file with no reader, and a non-zero exit code
returned to a scheduler that does nothing with exit codes.**

**Loud is not the same as heard.**

---

## Why this is a distinct defect from 17a

In 17a the probes were wrong: they measured a proxy instead of the artifact. Here there was no
probe at all, and none of the usual advice applies:

| Common advice | Why it did not help |
|---|---|
| "Fail loudly, never silently" | ✅ It did. Into a file. |
| "Exit non-zero on failure" | ✅ It did. To a scheduler that discards it. |
| "Log the reason" | ✅ It did, with the precise cause. |
| "Don't pretend success" | ✅ It never did. |

Every piece of conventional guidance was followed. ⚠ **The missing step is the one nobody states:
name the reader.**

> **An error message is not an alert until you can name the human or system that will see it, and
> the path by which it arrives.**

---

## The root cause, and the part that stings

The backup connected to its target by a **mesh-network DNS name**. An unrelated storage incident
took that host off the mesh; the name stopped resolving; the precondition check failed correctly
and the job skipped, exactly as designed.

⚠ **A monitoring script on the very same machine already dialled the same host by its stable
address specifically to avoid this**, with a comment in the source explaining why.

**The hardening existed, in the same repository, and had never been applied to the job that guarded
irreplaceable data.** The monitoring tool was protected against an outage the backup was not.

> ⚠ **A lesson recorded in one place is not a lesson applied everywhere.** When you harden something
> against a dependency failure, the immediate next question is *what else depends on that same
> thing* — and the answer must come from a command that lists them, not from memory.

---

## Three things that would each have caught it

**① Backup freshness as a monitored signal.** Nothing checked *how old the newest backup was*.
Comparing the newest artifact's date against today would have gone red on **day one** instead of
day six. ⚠ **Note what is being measured: the artifact, not the job.** "Did the job run?" and "does
a recent backup exist?" diverge exactly when it matters.

**② A reader for the failure path.** Anything that turned a non-zero exit into a message a human
receives — a wrapper that mails on failure, a scheduler that reports, a log shipper with an alert —
would have surfaced the first skip.

**③ Auditing dependency style across the fleet.** *"Which scheduled jobs resolve a host by a name
that can stop resolving?"* is answerable by grep in seconds, and returns the list that should have
been hardened together.

---

## What the fix looked like

Dial the stable address directly, and **read no shared client configuration at all** — because the
shared config had picked up an unrelated include that behaved differently depending on which user
ran it. The connection string became self-contained: explicit address, explicit port, explicit
identity, no inherited configuration.

⚠ **The comment matters as much as the code**, and is the reason this class recurs:

```
# Connects by stable address with no shared config DELIBERATELY — do not "simplify"
# this back to the friendly name. It silently stopped six days of backups when the
# name stopped resolving, and the job reported it loudly into a log with no reader.
```

**Without that comment the next person tidies it back.** It looks like needless verbosity, which is
precisely what it is until the day it is not.

---

## The transferable rules

> ⚠ **"Fails loudly" is a claim about the SENDER. Alerting is a property of the RECEIVER.** A
> message with no reader is a diary entry.

> ⚠ **For anything holding irreplaceable data, monitor the ARTIFACT's freshness, not the job's
> outcome.** The job can be healthy and absent. The artifact cannot lie about its own age.

> ⚠ **When you harden one thing against a dependency, enumerate what else shares it — with a
> command.** The second instance is never found by remembering it exists.

> ⚠ **Prefer self-contained connection settings in unattended jobs.** Inherited configuration is
> a channel through which unrelated changes reach your most critical work.

---

## What it cost

Six days with no recoverable copy of a database that takes many hours to rebuild and holds state
that cannot be regenerated — watch history, curated collections, hand-made organisation.

Nothing was lost, because nothing failed during those six days. ⚠ **The exposure was total and the
damage was zero, and only the second of those was ever visible.** A backup gap is invisible right
up until the moment it is the only thing that matters.
