# B4 · A nightly backup daemon

**Section B — scheduled services & backups.** Back to the [catalog](../15-example-projects.md).

**What this shows:** a scheduled job that ships a database or directory to a **backup target over
SSH** every night, with a **remote integrity check** and **loud failure** — where governance
**Rule 4 (back up before apply)** and the **gated service-bootstrap** rule become concrete, plus
the classic gotchas (a scheduled job runs with a *stripped environment* and often **cannot write a
network mount**).

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

---

## The scenario

You have irreplaceable state on a node — a service's database, a config directory, an app's data
dir — and you want an **unattended nightly backup** to a separate machine (a `nas`, another
`server`, or off-box storage), so a bad disk or a bad `apply` is an inconvenience, not a loss.

Requirements that make this non-trivial:

- runs **on a schedule**, unattended,
- writes to a **remote** target (not the same disk),
- **verifies** the backup is intact (a copied-but-corrupt backup is worse than none),
- **fails loudly** — a silently-broken backup is the classic ops horror story,
- has a **bounded footprint** (rotation), and doesn't bloat other backups (e.g. exclude it from a
  whole-disk Time Machine).

## Why do it "the framework way"

Backups are *the* thing governance already insists on — [Rule 4](../03-governance-rules.md) says
"back up before you apply." This example is that rule as a durable service: the operator stands it
up **under approval** (a scheduled job is a service bootstrap — [gated](../03-governance-rules.md)),
tracks it as a project, and — critically — **proves it works before trusting it**, because an
unverified backup isn't a backup.

## The shape

### 1. Two big platform gotchas to design around (up front)

These bite silently, so plan for them (see your [platform spoke](../../platforms/macos.md)):

- **Stripped environment.** A scheduled job (launchd/systemd/Task Scheduler) runs with a **minimal
  `PATH`** and **no interactive login** — no ssh-agent, sometimes no `HOME`. So: reference every
  tool by **absolute path**, use a **dedicated passwordless SSH key** by explicit path, and don't
  assume anything your interactive shell provides.
- **Can't write a network mount.** On macOS especially, a scheduled job is often **blocked from
  writing a mounted network volume** (a privacy/permission restriction on background processes) —
  even when your interactive shell can. **The robust fix: don't write through the mount — push
  over SSH to the remote host directly** (`gzip -c file | ssh <target> "cat > dest"`), which
  sidesteps the whole class of failure. Test the job **as the scheduler runs it**, not just from
  your shell.

### 2. The backup script (intent)

```sh
# 1. Make a consistent, read-only snapshot of the source (e.g. a DB .backup, or a
#    quiesced copy). Never back up a file mid-write.
# 2. Stream it to the remote target over SSH, compressed:
#      gzip -c <snapshot> | ssh -i <backup-key> <target> "cat > <dest>.partial"
# 3. VERIFY on the remote: integrity-check the transferred file
#      (e.g. remote `gzip -t`, or a checksum compare) — gate the next step on it.
# 4. Atomic publish: only on a passing check, rename <dest>.partial -> <dest>.
# 5. Rotate: delete backups older than <N> days on the remote (bounded footprint).
# 6. LOG loudly (success AND failure) to a known file; non-zero exit on any failure.
```

The **verify-then-publish** and **loud failure** steps are what make it a *real* backup, not a
cron job that might be silently broken.

### 3. Schedule it (the gated bootstrap)

Wrap the script in a scheduled unit — a `launchd` LaunchDaemon, a `systemd` timer, or a Task
Scheduler task (per your [platform spoke](../../platforms/macos.md)). **Bootstrapping the unit is a
material action** — the operator pauses for your approval ([Rule 1](../03-governance-rules.md)).
Keep the schedule off peak hours, and away from times you might be applying config.

### 4. Track it as a project

Registry row + `docs/<backup>/PLAN.md` ([04 · Structure](../04-structure.md)): what's backed up,
to where, the schedule, the retention, and — importantly — the **"first real run verified"** date.

## Maintenance — the ownership half

- **Prove it before trusting it.** The install isn't done until a **real, unattended run** has
  produced a backup you've **restored-tested** (or at least integrity-verified end to end). Record
  that verification.
- **Watch for silent failure.** Because it's unattended, add a check you'll actually notice — the
  loud log, plus periodically confirming the newest backup's timestamp + integrity on the target.
- **Exclude the backup from other backups.** If a whole-disk backup (e.g. Time Machine) also runs,
  **exclude the DB/data from it** (back it up *this* way instead) so you don't double-store
  gigabytes or capture an inconsistent mid-write copy.
- **Re-verify after changes.** If you move the target, rotate the SSH key, or change the source,
  do a manual run and re-confirm — a backup that broke months ago is the worst kind.

## What you learn from this example

- A scheduled job's **stripped environment** (minimal PATH, no agent) and the **network-mount
  write block** are the two traps — **push over SSH, use absolute paths + a dedicated key**.
- **Verify-then-publish + loud failure** is what separates a backup from a false sense of security.
- **The bootstrap is gated; the verification is the real "done"** — install *and* proof, both
  tracked.

## Adapt it

In **your** repo: pick the source + target, write the snapshot→stream→verify→rotate script with
absolute paths and a dedicated key, add the scheduled unit from your platform spoke, get approval
to bootstrap it, then **do a verified first run** before you rely on it.

**Related:** [Rule 4 — back up before apply](../03-governance-rules.md) ·
[08 · Networking (SSH keys)](../08-networking.md) · [B5 · Network-mount keeper](B5-network-mount-keeper.md)
· [platform spoke](../../platforms/macos.md) · [catalog](../15-example-projects.md).
