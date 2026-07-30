# Platform spoke · macOS

**Maturity: Complete.**

This spoke maps the hub's platform-agnostic concepts to macOS specifics — package manager,
service manager, secret store, paths, and the gotchas. It does **not** re-explain concepts;
read the linked `guide/` sections for the *why*, then use this for the macOS *how*.

## At a glance

| Concept (hub) | macOS specific |
|---|---|
| Package manager ([07](../guide/07-tools-requirements.md)) | **Homebrew** (`/opt/homebrew/bin/brew` on Apple Silicon, `/usr/local/bin/brew` on Intel) |
| Service manager ([05](../guide/05-chezmoi.md), [07](../guide/07-tools-requirements.md)) | **launchd** — LaunchAgents (per-user) + LaunchDaemons (system) |
| Secret store ([06](../guide/06-secrets.md)) | **Keychain** (`security` CLI); vaults: KeePassXC, 1Password, `pass` |
| Home path ([01](../guide/01-concepts.md)) | `$HOME` = `/Users/<you>` |
| SSH ([08](../guide/08-networking.md)) | built-in OpenSSH; keys in `~/.ssh` |
| Private mesh ([08](../guide/08-networking.md)) | Tailscale (App Store or `brew install --cask tailscale`) |

## Installing the core requirements

```sh
# Homebrew (the package manager) — see https://brew.sh for the current bootstrap
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# The framework's hard core:
brew install chezmoi git
brew install --cask claude          # or your AI CLI; check its own docs for the current cask/installer
# secret store — one of:
brew install --cask keepassxc       # or 1password, or `brew install pass`
# multi-node substrate (optional):
brew install --cask tailscale
```

**Absolute brew path matters** ([07 · installer property 3](../guide/07-tools-requirements.md)):
launchd and chezmoi's apply context run with a **minimal `PATH`** that lacks `/opt/homebrew/bin`.
In install scripts and service definitions, call brew and brew-installed tools by **absolute
path**, not a bare command name — a bare `brew` works in your interactive shell and fails
silently under the agent.

## Service manager — launchd

macOS background jobs are **launchd** plists:

- **LaunchAgent** (`~/Library/LaunchAgents/<label>.plist`) — runs in your user session. Use for
  most per-user services.
- **LaunchDaemon** (`/Library/LaunchDaemons/<label>.plist`) — runs at system scope, as root or a
  named user. Use for always-on services that must run without login.

Bootstrapping one (a **material action** — [Rule 1](../guide/03-governance-rules.md), needs
approval):
```sh
# user agent:
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/<label>.plist
# system daemon (sudo):
sudo launchctl bootstrap system /Library/LaunchDaemons/<label>.plist
launchctl kickstart -k gui/$(id -u)/<label>     # (re)start
launchctl bootout gui/$(id -u)/<label>          # stop/unload
launchctl print gui/$(id -u)/<label>            # inspect
```
Schedule with `StartCalendarInterval`; keep the config file chezmoi-managed, but treat the
`bootstrap` itself as the gated step.

### The big macOS gotcha: TCC + network volumes

macOS **TCC** (privacy protection) blocks launchd-spawned processes from **writing** to network
volumes (a mounted NAS share) and some protected paths — *even as your user* — unless the
process has **Full Disk Access**. A daemon that works when you run it interactively can **fail
silently** when launchd runs it, because the interactive shell inherited FDA and the daemon
didn't.

**Implication:** don't have a launchd job write to a mounted network share and assume it works.
Either grant the specific binary Full Disk Access, or (more robust) **avoid the mount** — e.g.
push data over SSH to the remote host instead of writing through the mount. Test the job **as
launchd runs it**, not just from your shell.

## Secret store — Keychain + vaults

- **Keychain** holds per-item secrets; the `security` CLI reads them non-interactively:
  ```sh
  security find-generic-password -s "<service-name>" -w      # prints the password
  ```
  This is how a vault-read helper ([06](../guide/06-secrets.md)) unlocks a vault
  **non-interactively** — store the vault's master password as a Keychain item, read it with
  `security` at runtime, never echo it.
- **Vaults** (KeePassXC / 1Password / `pass`) hold the bulk of credentials; their CLIs
  (`keepassxc-cli`, `op`, `pass`) do the fetch. Wrap them in the read-only helper pattern.

## chezmoi on macOS

Standard ([05](../guide/05-chezmoi.md)); macOS notes:
- The config manager's source dir default is `~/.local/share/chezmoi`.
- `run_onchange_` / `run_once_` scripts run under a minimal PATH — **absolute tool paths**.
- Applying files under `~/Library/` works, but some are managed by macOS/apps; prefer managing
  a tool's *config* over app-owned state.

## SSH + mesh on macOS

- OpenSSH is built in; the SSH server is toggled in **System Settings → General → Sharing →
  Remote Login** (or `systemsetup -setremotelogin on`). Enforce **key-only** by disabling
  password auth in `/etc/ssh/sshd_config` (`PasswordAuthentication no`).
- Keys live in `~/.ssh` (never committed — [06](../guide/06-secrets.md)); config aliases in
  `~/.ssh/config`.
- **Tailscale** provides the private mesh + MagicDNS ([08](../guide/08-networking.md)); its
  "serve"/"funnel" features publish a service privately/publicly when a project needs it.

## Roles on macOS — common mapping

- **`workstation`** — a MacBook; Tailscale on; services on-demand; permission preset
  standard/trusting ([09](../guide/09-permissions.md)).
- **`server`** — a Mac mini / always-on Mac; LaunchDaemons for 24/7 services; NAS mounts;
  permission preset cautious. Watch the TCC-network-volume gotcha above for any scheduled job.

## Verifying (macOS)

- `brew doctor` clean; core tools resolve at their absolute paths.
- A launchd job you rely on actually runs **under launchd** (check its log), not just from your
  shell — the TCC trap.
- `security find-generic-password …` returns your vault key so non-interactive unlock works.
