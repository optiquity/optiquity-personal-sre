# 05a · Case study — the config migration that hid for 26 hours

> A worked example following [05 · chezmoi](05-chezmoi.md). Generalised from a real incident,
> with the detail kept deliberately.
>
> This failure mode is **specific to config managers**, invisible while it happens, and
> produced **different outcomes on two machines from the same commit**.

---

## The short version

A repo reorganisation moved the config-manager source tree out of the repo root into a
subdirectory, using chezmoi's `.chezmoiroot` file to declare the new location. Clean change,
committed, applied with `chezmoi update` on each machine.

On one machine that apply wrote a **months-old snapshot of `$HOME` over the live one** —
replacing the SSH client config, the git config and a shell profile, and dropping a copy of
the repo's documentation tree into the home directory.

**The command exited 0. Nothing reported an error. The dashboard stayed green.** It surfaced
**26 hours later**, when an SSH session that had worked for months asked for a password.

Two ordinary facts combined:

1. **The root-redirection file is resolved before the pull that introduces it.**
2. **Telling version control to ignore a path means it can never delete that path.**

The fix was **deleting** the orphaned tree, not restoring the overwritten files — removing
the capability rather than repairing the damage.

---

## The detailed record

### Timeline

| When | What |
|---|---|
| Day 0, 23:00 | `chezmoi update` runs on machine A. Exits 0. `$HOME` files silently replaced from a stale snapshot |
| Day 0 → Day 2 | **26 hours of normal operation.** No error, no alert, no pending changes. The overwritten files are ones you touch occasionally |
| Day 2, ~01:00 | `ssh` to another node falls back to a **password prompt** for the first time in months |
| Day 2, ~01:10 | Config file found to be **210 bytes**, containing only a third-party tool's boilerplate. Backups on disk show it was **686 bytes** two months earlier |
| Day 2, ~01:20 | The stale source directory is found still present in the production source tree, dated **four months earlier**, byte-identical to what is now in `$HOME` |
| Day 2, ~01:35 | Orphaned tree removed, after a backup. Verified: config manager reports the same managed-entry count, clean status, `$HOME` untouched by the removal |

### What was overwritten

Comparing each live file against the stale source copy and against the peer machine:

| File | Live | Peer machine | Verdict |
|---|---|---|---|
| SSH client config | **210 B**, timestamped the bad apply | — | **clobbered** — was 686 B |
| git config | **442 B**, timestamped the bad apply | 726 B | **clobbered** — lost three sections |
| shell profile | 285 B, timestamped the bad apply | 197 B | **rewritten**; whether content was lost is undeterminable |
| four other dotfiles | byte-identical to the stale copy | — | ⚠ **not damage** — timestamps predate the apply by months. Identical because they never changed |
| documentation tree | **120 files** written into `$HOME` | absent | repo content misplaced; inert |

⚠ **That fourth row is the trap in the analysis.** Four files matched the stale snapshot
exactly, which looks like four more casualties. Their modification times were *months older*
than the apply — they matched because they had never changed since the snapshot was taken.
**Comparing content alone would have reported four false positives.** Only the timestamp
separated real damage from coincidence.

### Mechanism 1 — the root file is resolved before the pull

`chezmoi update` means *git pull, then apply*. But the source root is resolved when the
process **starts** — before that pull.

So the invocation that first introduced `.chezmoiroot` ran with the **old** layout in effect,
treating the whole repo root as the source tree, including directories that were only
*becoming* non-source in the very commit being fetched.

Everything root-level that looked like a config entry was applied. Among them: a snapshot of
the SSH config taken months earlier, before that year's edits.

⚠ **The migration was correct. The transition was not atomic.** A tool that pulls and applies
in one command cannot use the *new* layout to interpret *the pull that introduces it*. The
safe sequence is `git pull`, then `apply` — two commands, so the second sees what the first
brought.

### Mechanism 2 — ignored files cannot be deleted by a pull

The same reorganisation added ignore patterns for the old root-level config paths. Correct in
itself: those paths were no longer source, and patterns like `/dot_*` and `/private_*` stop
them being tracked.

But **a pull cannot delete an untracked file.** The moment those patterns landed, version
control lost both the right and the ability to remove the old tree.

So it stayed: on disk, outside version control, absent from `status`, shaped exactly like a
source tree. Eight entries, all a single months-old snapshot, every one of which would be
applied again by any future mis-resolution.

```
verification after removal
  source root      no config-shaped entries remain — matches the peer machine
  managed entries  95 before, 95 after (unchanged)
  pending changes  0 before, 0 after
  $HOME            untouched by the deletion
```

### The same commit, two different outcomes

On the peer machine the migration left **nothing** behind. Its ordering happened to delete
the old paths before the ignore rules took effect.

⚠ **Identical commit, identical tool, opposite results** — decided by transient local state
at the moment of the pull. *"It worked on the other machine"* was true and proved nothing.

### Why nothing caught it for a day

Every available signal was accurate and pointed elsewhere:

- **Config manager: no pending changes.** Correct — it no longer considered those files
  managed, so it had no opinion about them.
- **Version control: clean tree.** Correct — the files were ignored.
- **Health checks: green.** None inspected `$HOME` file contents.
- **The blast radius was low-frequency files.** A shell profile and a git config can be wrong
  for a long time before anyone notices. The git damage was *still* unnoticed after the SSH
  symptom appeared; it was found only by comparison against the peer machine.

The one thing that eventually broke did so because the SSH client, with no host block, fell
back to a default identity the server did not accept. **A user-visible symptom, a day late,
by luck.**

### What the damage actually was

The git config lost three sections — a filter definition and two credential-helper entries.
Effects: version-control operations against the hosting service could start prompting for
credentials instead of using the helper.

⚠ **One of those "lost" sections should not be restored.** The filter referenced a binary that
is **not installed on either machine** and was configured as *required*, meaning operations
would **fail rather than warn** the first time it was needed. The clobbered file was, in that
one respect, more correct than the original.

**Restoring a file wholesale would have reinstated a latent fault.** The right unit of
recovery was the one key that mattered, not the file.

---

## What would have caught it sooner

**(a) A signal that already existed and nothing read.** Modification timestamps. Several
`$HOME` dotfiles changed **within the same second**, during an apply that reported no managed
changes. Those two facts are contradictory and both were sitting there.

**(b) A signal that did not exist.** An assertion that `$HOME` contains no **repo-shaped**
directories. A documentation folder in a home directory is a structural impossibility in a
healthy state, trivial to test, and would have fired within minutes.

**(b) A second one.** A check that the config-manager source root contains **no config-shaped
entries outside the declared root**. That is precisely the loaded-gun condition, and it is one
directory listing.

**(c) A verification discipline.** A migration that moves *where the source tree lives*
deserves a post-apply diff on one machine before propagating. **A zero exit code says the
command ran, not that it did what you meant.**

---

## What to take from it

**Migrations that move the source tree are not ordinary changes.** The tool must interpret the
change using rules the change itself is rewriting. Apply on one machine, verify by inspection,
then propagate — and prefer `pull` then `apply` as separate commands.

**When you add an ignore rule, ask what becomes unremovable.** An ignore rule tells version
control to stop managing a path — including stopping *deleting* it. Anything you ignore *and*
leave on disk is permanently yours to clean up by hand.

**A green dashboard describes what it measures.** Every check here was accurate; none looked
at the thing that changed. The gap was not a broken check but the absence of one.

**Prefer removing a risk to mitigating it.** *"The setting is correct"* is a weaker guarantee
than *"the file no longer exists."*

**Use timestamps to separate damage from coincidence.** Content comparison alone reported four
false positives. Mismatched content is suspicious; **content that matches an old snapshot and
carries the incident's timestamp is the actual signal.**

**Restore the key, not the file.** A wholesale restore reinstates whatever was wrong with the
original — here, a config entry that would have made operations fail outright.

---

Next: [06 · Secrets](06-secrets.md).
