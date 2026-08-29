# B4 · A nightly backup daemon

**Section B — scheduled services & backups.** Back to the [catalog](../17-example-projects.md).

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

### 5. Never store the key beside the data it protects

If the thing you are backing up is **encrypted at rest** — an automation platform's stored
credentials, a password manager's vault, an app's secret store — its key is usually a separate
small file. **Do not back that key up into the same directory as the encrypted data.** Co-locating
lock and key defeats the encryption entirely: anyone who reaches the backup target has both halves.

Put the key in your vault instead, and **write the consequence down where the person restoring will
read it** — in the script header, in capitals. Because without the key, a restore produces working
application data and credentials that cannot be decrypted, and **that looks exactly like a
successful restore** until the first thing tries to authenticate. A restore that fails loudly is
recoverable; one that appears to succeed is not.

The corollary: **a restore test that only checks the data is half a test.** Confirm the key is
recoverable from the vault too, or you have verified the half that was never at risk.

## Which services need one — and how you find the ones you missed

The hard part isn't writing the script. It's noticing that something **needs** one.

Backups tend to get added the way this example describes: someone notices a service holds something
irreplaceable, and builds it a daemon. That works exactly as far as attention reaches. In one real
fleet the media server got a carefully-built backup daemon because it was obviously precious — while
the **automation platform**, holding every workflow *and* every stored credential, had **no
automated backup at all**. The only copies in existence were two made by hand, 32 days apart. Nobody
decided that; nobody was asked.

So make it a rule rather than a habit, and state it in the general form:

> **Before a service holding non-reproducible data is relied on, it must be registered with the
> update checker, version-pinned, backed up on a schedule, and restore-tested at least once.**

Then ask the question the rule implies, out loud, for everything already running: *what does this
hold that I cannot rebuild?* Config regenerates from your repo. Container images re-pull. But
workflow definitions, credential stores, accumulated history, and anything a person authored by hand
do not — and those are rarely the services that look important.

## What you learn from this example

- A scheduled job's **stripped environment** (minimal PATH, no agent) and the **network-mount
  write block** are the two traps — **push over SSH, use absolute paths + a dedicated key**.
- **Verify-then-publish + loud failure** is what separates a backup from a false sense of security.
- **The bootstrap is gated; the verification is the real "done"** — install *and* proof, both
  tracked.
- **"The file exists" is not a backup; "it restored" is.** And a restore test that skips the
  decryption key verifies only the half that was never at risk.
- **The backup you don't have is the one nobody decided against** — coverage is a rule to apply,
  not a judgement to make service by service.

## Adapt it

In **your** repo: pick the source + target, write the snapshot→stream→verify→rotate script with
absolute paths and a dedicated key, add the scheduled unit from your platform spoke, get approval
to bootstrap it, then **do a verified first run** before you rely on it.

**Related:** [Rule 4 — back up before apply](../03-governance-rules.md) ·
[08 · Networking (SSH keys)](../08-networking.md) · [B5 · Network-mount keeper](B5-network-mount-keeper.md)
· [platform spoke](../../platforms/macos.md) · [catalog](../17-example-projects.md).
