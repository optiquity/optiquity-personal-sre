# B5 · A network-mount keeper

**Section B — scheduled services & backups.** Back to the [catalog](../15-example-projects.md).

**What this shows:** a small **always-on / passive scheduled job** that keeps a network volume
(NFS/SMB) mounted and re-mounts it if it drops — the minimal shape of "a service the operator
owns," plus how the same job maps onto each platform's service manager.

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

---

## The scenario

A node depends on a **network volume** — a `nas` share it reads media/files from, or a target that
other automation writes to. Network mounts are fragile: they drop on network blips, sleep/wake,
the server rebooting, or DHCP changes. When the mount is gone, whatever depends on it breaks
quietly (a service can't find its files; a backup job has nowhere to write).

You want the mount to be **present and self-healing** — mounted at boot/login and **re-mounted
automatically if it disappears** — without you noticing or intervening.

## Why do it "the framework way"

This is the smallest possible "own a service" example, which makes it a good template: a passive,
low-risk background job, tracked as part of your setup, with the platform-specific service-manager
mapping made explicit. It also pairs with [B4 · Backup daemon](B4-nightly-backup-daemon.md) — a
backup that writes to a mount needs the mount to *be there*.

## The shape

### 1. A tiny idempotent keeper script

```sh
# Is the mount present + healthy?
#   mount | grep -q "<mount-point>"  AND  a quick read/stat of it succeeds
# If NOT mounted -> (re)mount it:
#   mount the <NFS|SMB> share to <mount-point> (credentials from the vault/keychain,
#   never inline — see 06-secrets)
# If a stale/hung mount -> unmount first, then remount.
# Idempotent: when already healthy, it's a no-op. Loud on repeated failure.
```

Keep it **cheap** (it runs frequently) and **idempotent** (a no-op when the mount is fine).

### 2. Run it passively on a schedule / keep-alive

- **macOS:** a `launchd` agent/daemon with `StartInterval` (every few minutes) or `KeepAlive` +
  `WatchPaths`.
- **Linux:** a `systemd` mount/automount unit (the native, best option) or a `.timer` running the
  keeper; on desktops, `autofs`.
- **Windows:** a scheduled task at logon + interval, or a persistent mapped drive.

See your [platform spoke](../../platforms/macos.md) for the exact unit. **Bootstrapping the unit
is a service bootstrap → gated** ([Rule 1](../03-governance-rules.md)).

### 3. Two mount gotchas to design around

- **Credentials for SMB/NFS** come from the **vault/keychain** ([06 · Secrets](../06-secrets.md)),
  never written into the script or a tracked file.
- **`nobrowse` for automation mounts.** If the mount is purely for background automation (not for
  you to browse in Finder/Explorer), mounting it hidden/`nobrowse` avoids it cluttering the UI and
  reduces accidental interaction — a nice touch for a `server`.

### 4. Track it

Registry row + a short `PLAN.md` ([04 · Structure](../04-structure.md)): which share, mount point,
protocol, which role, and the keeper's schedule. A passive service is still a tracked part of your
setup.

## Maintenance — the ownership half

- **It's passive, so watch it doesn't fail silently.** The keeper should log when it has to
  re-mount; a mount that's *constantly* re-mounting signals a deeper problem (flaky link, server
  issue) worth investigating — not just papering over.
- **Re-verify after network/host changes.** New subnet, NAS reboot, credential rotation, or a
  protocol change → do a manual check that the keeper still mounts cleanly.
- **Symmetry / role fit** ([Rule](../03-governance-rules.md)): if two nodes of the same role both
  need the share, they get the same keeper; a node that mounts a *different* protocol (e.g. NFS on
  a `server` for automation, SMB on a `workstation` for Finder) is a deliberate, documented
  divergence.

## What you learn from this example

- The **minimal always-on service**: an idempotent keeper + a platform-native scheduled/keep-alive
  unit, bootstrapped under approval.
- **Native > scripted where it exists** — e.g. a `systemd` automount beats a shell keeper on
  Linux; use the platform's real mechanism when it has one.
- Even a **passive** job is tracked and watched for silent failure — that's ownership.

## Adapt it

In **your** repo: write the keeper (credentials from the vault), pick the platform-native unit
from your spoke, get approval to bootstrap it, and record it. If a backup or service depends on
the mount, note that dependency so the ordering is clear.

**Related:** [08 · Networking](../08-networking.md) · [06 · Secrets](../06-secrets.md) ·
[B4 · Nightly backup daemon](B4-nightly-backup-daemon.md) · [platform spoke](../../platforms/macos.md)
· [catalog](../15-example-projects.md).
