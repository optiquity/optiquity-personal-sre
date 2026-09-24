# C20 · A queue pipeline: drop work in, get results out

**Section C — self-hosted apps over the private mesh.** Back to the [catalog](../20-example-projects.md).

**What this shows:** a watched-folder pipeline. You drop work into a queue, an automation runtime
([C6](C6-automation-runtime.md)) picks it up, a tool processes it, and results and originals are
filed. It is designed so that you can see what is happening, nothing is ever picked up half-built,
and every way it can stop is reported. The monitoring half matters as much as the pipeline.

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

---

## The scenario

You want to drop files or folders into one place and get processed results out: convert a video,
embed subtitles, extract tracks, resize images. A workflow polls the folder every 30 seconds and
runs a tool on whatever it finds. It is simple, until:

- a folder still being copied in gets picked up half-complete;
- someone moves an item mid-job, and a second job starts beside the first;
- a name with a trailing space breaks a step that addressed files by a trimmed copy of the name;
- one workflow's failures hide behind another's;
- a queue sits full for a day and nothing says so.

## Why do it "the framework way"

The pipeline's definition is tracked, its stages are visible, and it is watched by **outcome**, not
by the runtime's opinion of itself. A workflow runtime's "success" means only that the workflow
ran ([17 · Monitoring](../17-monitoring.md), "Liveness is not completion").

## The shape

### 1. One folder per stage, visible, under real names

```
queue/     drop work here (polled)
fence/     the item being worked on        not empty = busy
work/      the result being built, under its REAL name — you can watch it grow
done/      originals of jobs that succeeded
failed/    originals of jobs that failed, with a log or note beside them
results/   outputs
```

**No hidden or temp files anywhere.** Hidden build folders once made a healthy conversion look
stalled, and the owner could no longer tell what was working
([02 · The operator](../02-operator.md), "Before building").

### 2. Every hand-off is one move on one filesystem

A polled queue must never see something half-built. A rename within one filesystem is
all-or-nothing; a copy is not.

- **Verify that the stages share a filesystem**, and re-verify after any storage change.
- **If a move would ever cross filesystems, fail the item** rather than copy it piece by piece.
- **For people dropping work in by hand:** copy a folder somewhere else first, then *move* it into
  the queue. A folder being copied straight in can be picked up before it is complete.

### 3. Fix names once, on pickup; never trim a name you use as an address

Leading and trailing spaces break tools in quiet ways. Fix them **on disk, at every level, when the
item is picked up**, and let every later step use the name exactly as it then is.

- If a fix would clash, **rename nothing**. That covers a fixed name that already exists, two names
  that collapse to one, a name that is only spaces, and a fix that would create a hidden name.
  Move the item to `failed/` with a note listing the clashes, so it doesn't block the head of the
  queue.
- ⚠ **The case:** a step trimmed a name in memory and then built paths from it. The paths did not
  exist, the tool did nothing, and the runtime recorded every run as a success.

### 4. One job at a time, with a guard nobody can defeat by hand

The fence serialises the pipeline, but a person can move the item out of it mid-job. Once, that
opened the fence and started a second job beside the first. The guard that closes it tests
something a person can't move: see
[14 · Workflows & automation](../14-automation.md), "Serialising a pipeline without lock files".

### 5. Filing never overwrites

Every move into `done/`, `failed/` or `results/` takes a ` (n)` suffix rather than overwriting,
and says so in the step's output. An overwrite loses the item that was already there.

### 6. Monitor the outcome

| Alert | Fires when |
|---|---|
| **STALLED** | an item has waited in a queue past a threshold **while that pipeline is idle**. Waiting behind a running job is healthy, not stalled. |
| **STUCK** | a job is running and **nothing has been written in its work area** for N minutes. A long job is not a stuck one: a large batch can run for hours. |
| **Failure, one check per workflow** | a run exited with **any** non-zero code, not just the last step's. Also when the runtime **stopped** a run (canceled, error, crashed; see [C6](C6-automation-runtime.md), "Time limits"), or when two runs of one workflow overlapped. One combined check would hide a second workflow's failure behind the first. |

The measurements have traps of their own:

- **Measure age with ctime, not mtime.** `mv` and most file managers preserve mtime, so a file
  downloaded weeks ago and dropped in a minute ago looks weeks old. ctime changes on the rename.
- **A network share stamps times with the server's clock.** Compare against that clock, or
  measure the skew.
- **Discover the pipelines by their folder pattern**, not from a hand-kept list. **A scan that
  finds none is UNKNOWN, not "all clear".** Scan a hard-mounted share in a time-bounded child
  process, so that a hung mount can't hang the check.
- **A check whose source has gone is blind, and blind is FAIL.** That covers a workflow that was
  deleted, or whose live version no longer writes the marker the check reads. It is not UNKNOWN
  ([17 · Monitoring](../17-monitoring.md), "A probe that could not answer").

⚠ **What no alert can see:** a result with the **wrong contents** looks healthy. Prove the layouts
by tests, replaying the workflow's real steps on scratch folders, not by monitoring.

## Maintenance — the ownership half

- **Re-measure the runtime's time limit after every upgrade** ([C6](C6-automation-runtime.md)).
- **Keep the stages on one filesystem.** A storage change that splits them turns every hand-off
  into a failure (by design) or, worse, into a copy.
- **Test a changed workflow on scratch folders first,** with its real steps, before it touches the
  live queue. Then prove the switch per workflow from the runtime's own record of what ran.

## What you learn from this example

- **Make every stage visible.** Nothing hidden, nothing temporary, and results built under their
  real names.
- **One move per hand-off, on one filesystem.** A polled queue must never see half of anything.
- **Fix names once, on disk.** Never address a file by a transformed copy of its name.
- **Watch outcomes:** stalled while idle, no progress, any non-zero code per workflow, stopped runs.
  **A blind check is a failed check.**

## Adapt it

In **your** repo: lay out the stage folders on one filesystem, write the pickup step (names fixed on
disk, clashes to `failed/` with a note), put the busy guard in front of the tool, and add the four
alerts. Replay the workflow on scratch folders before it touches real work.

**Related:** [C6 · Automation runtime](C6-automation-runtime.md) (time limits, deployment) ·
[14 · Workflows & automation](../14-automation.md) (the guard) ·
[17 · Monitoring](../17-monitoring.md) (liveness vs completion; three states) ·
[E15 · Media automation](E15-media-automation.md) · [catalog](../20-example-projects.md).
