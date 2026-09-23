# 17a · Case study — six green checks over one broken system

> A worked example following [17 · Monitoring](17-monitoring.md). Generalised from a real
> fleet, with the detail kept deliberately.
>
> Chapter 17 says *measure the artifact, not the process.* This is what it costs to learn that
> six times.

---

## The short version

Over about four months, one small fleet's monitoring failed six times. Each failure looked
unrelated to the others — a media pipeline, a router role, a reboot detector, a NAS, a dotfile
sync, a transcode queue. They were argued about separately, fixed separately, and written up
separately.

**They are one defect.** Every probe measured something *adjacent* to the thing it was supposed to
watch. A running process instead of the artifact that process was supposed to produce. A job's exit
code instead of the work the job was supposed to do. An HTTP 200 instead of the role the responding
machine was supposed to perform.

⚠ **The adjacent thing is almost always healthy.** That is what makes the class so expensive: the
dashboard stays green, the digest stays quiet, and the system underneath does not work.

The worst instance ran for three weeks. The one that should sting most is the sixth, where the
monitoring failed to notice that the mechanism keeping the monitoring deployed had been dead for
twenty days.

---

## The detailed record

### The six, in the order they were found

#### 1 · The probe watched a process that was not doing the work

A media server can generate a per-file analysis artifact that enables a downstream feature. A
watcher was written to report progress on that generation across a library of roughly 71,600 items.

The watcher checked **whether a particular scanner process was running**, and emailed *"generation
complete"* when the process exited.

**The artifact is not produced by that process at all.** It is produced by a different subsystem
inside the server, driven by a scheduled internal task with a different name.

- The watcher tracked an **unrelated process** for weeks.
- It declared success at **0.15% actual coverage**.
- It was caught only because a human opened a title and saw *"not processed"* on something the
  fleet believed was finished.

⚠ **Nothing about the probe was broken.** It correctly reported the state of the thing it measured.
It measured the wrong thing, and no amount of reliability engineering on the probe itself would
have helped.

**The fix** was to query the database for the rows the feature actually writes, joined to the media
table — *the artifact*, not a process that might or might not create it.

#### 2 · Two thousand successes over two thousand failures

A workflow engine drove a transcode pipeline. A directory holding conversion presets was renamed
with a capitalisation change; the network share was case-sensitive; every preset import failed;
the encoder exited non-zero; each file was correctly routed to a *failed* directory.

The workflow engine recorded **2,256 consecutive successful executions.**

⚠ **It was not lying.** The workflow *did* run, 2,256 times, to completion, without an engine-level
error. **An execution status means "the workflow ran." It has never meant "the work succeeded."**

Nothing watched the failed-output directory, so the pipeline produced nothing for at least 19 hours
before anyone asked.

#### 3 · The router that answered every check and routed nothing

A small gateway node advertised a subnet route so the rest of the network could be reached over the
mesh VPN. Health checks pinged its services. Every check was green, continuously, for weeks.

**It was not holding the route.** Another node was — an underpowered appliance that throttled the
traffic badly.

⚠ **Reachability and role are different kinds of fact, and the entire monitoring design was
organised around reachability.** A service check *structurally cannot* see a role. It surfaced only
because an unrelated package upgrade made somebody look at that machine.

**The subtlety worth keeping:** the check that fixed it *could not have been written earlier.* The
mesh VPN picks the primary subnet router by join date — oldest wins — with no priority or failback
control, and the wrong node was older. So *"the right node holds the route"* was **not a true
statement** under the old arrangement; the holder was legitimately variable.

⚠ **An assertion you cannot make is a strong signal that the design, not the monitoring, is what
needs changing.** Once the older node stopped advertising the route entirely, the statement became
always-true-when-healthy — and therefore assertable.

#### 4 · The freshness trap

A check reported whether a Windows node had rebooted unexpectedly. It read a **JSON file** that a
scheduled task on that node refreshed after each boot.

The scheduled task was disabled. The file froze. The check went on reporting *"no new restart"* —
for a machine that had rebooted **ten hours earlier.**

⚠ **A stale file and a quiet system produce identical output.** This is the most general form of
the whole class: *the absence of a signal and the absence of a problem look the same unless
something checks the signal's own freshness.*

**The fix** made the *live* boot time the trigger and demoted the file to enrichment.

#### 5 · Three weeks of a failing disk behind a green ping

A NAS held a RAID array. One drive began failing. Because that drive was a member of the OS
partition, the swap partition and the data volume simultaneously, its stalls wedged all three: an
administrative login that hung, blocked file-service threads, and an application on another machine
failing with *"no space left on device"* against **8 TB of free space.**

**This ran for about three weeks.** The monitoring's view of the NAS was *reachability*, and the
NAS answered pings throughout.

⚠ **The storage vendor's own management UI reported all drives "Healthy" — while its own backend
held a per-drive field reading `critical` for that disk.** The headline was an aggregate that did
not escalate on that field alone. **The same defect one layer down: a derived status standing in
for a measurement.**

The field was **world-readable and required no elevated privileges**. Nothing in the fleet read it.

#### 6 · The one that should sting

The fleet's configuration manager ran every 30 minutes on two machines to keep dotfiles in sync. An
application had begun rewriting its own config file, so the config manager wanted to prompt before
overwriting it. A scheduled job has no terminal to prompt on, so **the run aborted before applying
anything else.**

It reported **failure, on both machines, for roughly 962 consecutive runs — about 20 days.**

The cost was not the one contested file. It was everything the abort took with it: one machine was
missing a tool entirely and running three stale ones; the other had 14 pending changes queued,
including an automation job and a database-backup schedule.

⚠ **The health checks watched services and artifacts. They did not watch whether the fleet's own
scheduled jobs were running.** The monitoring did not notice that the mechanism which keeps the
monitoring deployed had been dead for three weeks.

**And the second failure hid behind the first.** Fixing the config file did not restore the sync:
a routine package upgrade earlier that same day had replaced the config manager's binary and
repointed its symlink, so the scheduler could no longer launch the program at all. It failed with a
configuration-error exit code **and no output whatsoever.**

⚠ **A job that fails to spawn writes nothing — and an unchanged log is indistinguishable from a
healthy, quiet one.** The stale log from the *previous* failure made it look like the original
problem was ongoing.

---

### The one question that would have caught all six

Not a tool. A question, asked of each probe at the time it is written:

> **"What exactly goes wrong here — and would this signal change if it did?"**

| Failure to catch | Would the probe have changed? |
|---|---|
| The analysis artifact is not being generated | **No.** The scanner runs either way |
| A conversion produces nothing usable | **No.** The engine records that the workflow ran |
| The gateway stops routing | **No.** It still answers HTTP |
| A node reboots unexpectedly | **No.** A frozen file reports "no new restart" |
| A disk is failing | **No.** The NAS still answers pings |
| The config sync is dead | **No.** Nothing watched the scheduler at all |

**Six probes. Six times "No."** ⚠ **The question was never asked** — not because anyone decided
against it, but because nothing in the workflow prompted it, and a probe that returns *green* on a
healthy system looks finished.

### The failure mode the question does not catch

One of these was believed for a specific and nastier reason.

The email that falsely announced the analysis was complete **also announced a second thing was
complete — and that second claim was true.** The other artifact genuinely was at ~99.4%.

⚠ **One verifiable true half lent credibility to an unverifiable false half.** A wholly wrong alert
invites checking. A half-true one does not.

**The rule that falls out: a probe asserting two things must measure both, or claim only the one it
measures.**

### What actually found each one

Worth listing, because none was found by monitoring:

| # | Found by |
|---|---|
| 1 | A human opening a file and seeing it unprocessed |
| 2 | A human asking why nothing had come out of the pipeline |
| 3 | An **unrelated** package upgrade that made someone look at the machine |
| 4 | Investigating a different incident |
| 5 | An application on another machine crashing repeatedly |
| 6 | An SSH session unexpectedly falling back to a password prompt |

⚠ **Six for six, by accident or by a human noticing.** A monitoring system with this much coverage
and this failure mode is not neutral — **it is worse than none, because it actively tells you
things are fine.**

### The verification discipline that ends the class

**A check that has never gone red is not a check.**

Inducing the failure takes minutes and is definitive: disable the thing, confirm the probe goes
red, re-enable it. Every one of the six would have been caught the first time anyone tried it.

⚠ **It became policy only after the fifth.** The five NAS checks written afterwards were each
proven to go red against an induced failure before being trusted — and writing them that way
immediately exposed that two *existing* checks on another machine were structurally incapable of
ever reporting failure.

**A related discipline, from the same fleet, for anything that repairs rather than reports:**

A mount-recovery daemon ran a liveness probe as root. The file server's export mapped the client's
root user to an unprivileged account, so **the probe failed on every five-minute tick, forever, for
a reason that had nothing to do with liveness.** Its failure action was to force-unmount and
remount — so it destroyed whatever long-running job was in flight, on a five-minute cycle, while
looking like a flaky network.

⚠ **Anything that repairs automatically needs more evidence than anything that merely reports.** A
false positive costs nothing in the second case and destroys work in the first.

### The counter-example: what it looks like done right

The same fleet, in the same months, built a subtitle-extraction pipeline that got this correct — so
this is not a story about one team lacking the skill.

It defined **three** exit states, not two:

```
0  success
1  nothing extracted — no subtitles present, invalid input, or all tracks failed
2  PARTIAL — at least one track succeeded AND at least one failed
```

⚠ **A dedicated code for partial.** Partial success is the state naive exit codes collapse — into
success (losing the failure) or failure (losing the successes). Both are wrong and both are silent.

It also kept **two different questions in two different mechanisms**: *did the pipeline handle this
file?* is answered by which directory the source lands in; *did every track come out?* is answered
by a per-track marker file. And *"nothing to do"* was explicitly distinguished from *"failed to do
it."*

⚠ **And then nothing ever counted the markers.** The information is written to disk on every run
and read by nobody — the same blind spot as the unwatched failed-output directory in #2.

**Good design does not produce monitoring on its own.** Someone still has to read what it writes.

### Dead ends worth recording

- **Hardening the probe.** When the mount-recovery probe kept failing, the first instinct was a
  better probe. The correct answer was **no probe** — the daemon was redesigned to act only when
  the mount was *absent*, never to check a live one. ⚠ *A probe that can fail for reasons unrelated
  to health is a liability, and making it more elaborate makes it a more elaborate liability.*
- **Tuning the timeout.** A hang was chased through two opposite timeout settings, one of which
  made things worse. The fault was in a *different protocol path* that no timeout setting touched.
  ⚠ *A knob whose two opposite settings both change nothing is not connected to your problem.*
- **Trusting a config file over a running daemon.** A protocol was enabled in configuration and not
  actually being served. ⚠ *A config file records intent; only the running service records fact.*

---

## What to take from it

1. **Name the failure first, then ask what proves it.** Listing what you will *check* is not the
   same as listing what you need to *catch*. The gap between those two lists is where all six
   lived.
2. **Prefer the artifact to the process, the outcome to the exit code, the role to the response.**
   In every case the correct signal existed and was cheap — a database row, a routing table, a live
   timestamp, a world-readable status field.
3. **Check the freshness of anything you read from a file.** A frozen file and a healthy system
   produce identical output.
4. **Induce the failure before you trust the check.** *A check that has never gone red is not a
   check.* This single practice would have caught all six.
5. **Watch your own scheduled jobs**, and assert they are *running on schedule* — not merely that
   the last exit code was zero. A job that fails to spawn writes nothing at all.
6. **Require more evidence to repair than to report.**
7. **A probe asserting two things must measure both.** A true half makes a false half credible.
8. **Read what your good designs already write down.** Two of these systems were emitting perfect
   failure evidence into directories nobody watched.

⚠ **And the meta-lesson, which is the reason this page merges six incidents instead of listing
them:** each was written up separately and fixed separately, and the pattern only became visible
when they were read *together*. **A fix's class is what should be applied, not just the fix.** The
question takes a minute — ***which other things have this property?*** — and nothing in a normal
workflow prompts it.

---

Next: [17b · Case study — it failed loudly, for six days, into a file nobody reads](17b-case-loud-into-the-void.md).
