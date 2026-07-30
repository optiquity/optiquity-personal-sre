# Platform spoke · Linux

**Maturity: Stub.** The mappings below are the well-known Linux equivalents and are correct in
outline, but this spoke has **not** been battle-tested the way macOS has — treat the ⛏ TODO
items as "verify + expand before relying on." Read `guide/` for the *why*; this is the Linux
*how*.

## At a glance

| Concept (hub) | Linux specific | Status |
|---|---|---|
| Package manager ([07](../guide/07-tools-requirements.md)) | `apt` (Debian/Ubuntu) · `dnf` (Fedora/RHEL) · `pacman` (Arch) | ✅ outline |
| Service manager ([07](../guide/07-tools-requirements.md)) | **systemd** — user units + system units | ✅ outline |
| Secret store ([06](../guide/06-secrets.md)) | **libsecret** (`secret-tool`) / **`pass`** (GPG) / keyring | ⛏ verify |
| Home path ([01](../guide/01-concepts.md)) | `$HOME` = `/home/<you>` | ✅ |
| SSH ([08](../guide/08-networking.md)) | OpenSSH (usually preinstalled); keys in `~/.ssh` | ✅ |
| Private mesh ([08](../guide/08-networking.md)) | Tailscale (official repos) | ✅ |

## Package manager

```sh
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install -y git chezmoi
# Fedora/RHEL
sudo dnf install -y git chezmoi
# Arch
sudo pacman -S --noconfirm git chezmoi
```
The installer template ([skeleton](../skeleton/installers/install-tooling.sh.template)) sets
`PM`/`PM_INSTALL` per distro. Unlike macOS/Windows, Linux package managers drive **cleanly
non-interactively** (no elevated-interactive requirement) — good for automation.

## Service manager — systemd

The launchd equivalent:
- **User units** (`~/.config/systemd/user/<name>.service`, `systemctl --user`) — per-user
  services, the common case.
- **System units** (`/etc/systemd/system/`, `sudo systemctl`) — always-on/system services.

Bootstrapping a unit is the **material action** ([Rule 1](../guide/03-governance-rules.md)):
```sh
systemctl --user daemon-reload
systemctl --user enable --now <name>.service     # (gated) enable + start
journalctl --user -u <name> -f                   # inspect (a read)
```
Schedule with a `.timer` unit (the cron/StartCalendarInterval equivalent). ⛏ TODO: a worked
user-unit + timer example from tracked config.

## Secret store — ⛏ verify

- **libsecret** via `secret-tool` (GNOME Keyring / KWallet backends) is the closest Keychain
  analog for non-interactive reads.
- **`pass`** (GPG-backed) is a strong CLI-native vault; its non-interactive unlock uses a
  gpg-agent.
- ⛏ TODO: pin the **non-interactive vault-unlock** pattern ([06](../guide/06-secrets.md)) for a
  headless Linux `server` (no desktop keyring session) — this is the part most likely to bite,
  since many keyring backends assume a graphical session.

## SSH + mesh

- OpenSSH server (`openssh-server`) — enable `sshd`, set `PasswordAuthentication no`, keys in
  `~/.ssh` (never committed — [06](../guide/06-secrets.md)).
- **Tailscale** from the official repos; the node joins the mesh + MagicDNS like any other
  ([08](../guide/08-networking.md)). Headless Linux boxes are the *ideal* always-on `server`.

## chezmoi on Linux

Standard ([05](../guide/05-chezmoi.md)); `run_onchange_`/`run_once_` scripts are POSIX sh, so
the [skeleton installer](../skeleton/installers/install-tooling.sh.template) works with minimal
adaptation (just the `PM` block). Source dir default: `~/.local/share/chezmoi`.

## Roles on Linux — common mapping

- **`server`** — a headless Linux box is the archetypal always-on `server`: systemd units for
  24/7 services, Tailscale, cautious permission posture. The cleanest home for automation.
- **`workstation`** — a Linux desktop/laptop; keyring for secrets; standard/trusting posture.

## ⛏ Expand before relying on
- A verified headless secret-unlock recipe (the keyring-without-a-session problem).
- A worked systemd user-unit + timer from tracked config.
- Distro-specific package-name differences for the optional tools.

## Verifying (Linux)
- `systemctl --user status <name>` shows your service healthy.
- Non-interactive `ssh <node>` is key-only.
- The vault-read helper unlocks **without** a graphical session on a headless `server`.
