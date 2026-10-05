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

**Trigger on a file change, not a clock.** Besides `StartCalendarInterval`/`StartInterval`, a
LaunchAgent can use **`WatchPaths`** — it fires whenever a watched directory changes. That's how
you run something *after any install* (watch the package manager's bin dirs) rather than guessing
a schedule. Pair it with `ThrottleInterval` so a bulk upgrade can't fire it a hundred times.
Ready-to-use agent templates (weekly timer, periodic probe, WatchPaths trigger) ship in
[`../skeleton/monitoring/`](../skeleton/monitoring/).

**After running a tool's setup, start or pair commands, look for agents you did not create.** Some
CLIs install a LaunchAgent as a side effect of routine commands
([07 · Tools & requirements](../guide/07-tools-requirements.md#a-command-that-installs-a-service)).
List `~/Library/LaunchAgents` and `launchctl list` before and after, and account for every new label.

### The big macOS gotcha: privacy prompts nobody answers

macOS **privacy protection (TCC)** gates access to protected places — a mounted network share, iCloud
Drive, Documents, Desktop, removable volumes — **program by program**. The first time a program macOS has
not approved touches one, macOS shows a prompt, and **the access waits until someone answers it**. That
holds for reads as well as writes. On a Mac nobody is watching, nobody answers: the scheduled job hangs,
and so does anything else waiting on the same access.

Three things decide when this bites:

- **Which program macOS asks about.** It charges a job's access to the job's *responsible* program and
  **skips Apple's own programs**. A shell script run by `/bin/bash` is charged to the first non-Apple
  program it runs: the package manager's `python3`, `rsync`, and so on.
- **Updates ask again.** A package update replaces that program with a new build, which macOS treats as a
  new program. The approval does not carry over, so the next scheduled run prompts again, on a screen
  nobody watches.
- **Your terminal hides it.** The terminal you test from is already approved, so a job that works when
  you run it can still hang when launchd runs it.

**What to do:**

- Test a job **as launchd runs it**, and look at the screen (Screen Sharing) the first time it runs and
  after every update to a program it runs.
- **Watch for unanswered prompts.** macOS's privacy service logs each request and its answer; a request
  still unanswered after a few minutes is a prompt on a screen. Read that log with `/usr/bin/log`, by full
  path: in zsh, a bare `log` is a different, built-in command.
- **Start jobs through a small launcher you approve once and never rebuild.** macOS then charges the
  access to the launcher, so updates to what it runs no longer ask again. Let it run only the commands you
  list, in a file only an administrator can change, and give the commands a fixed environment.
- Or **keep the job away from protected places**: push data over SSH to the host that holds it, rather
  than reading or writing through the mount.

The whole incident, from the first wrong turn to the launcher, is case study
[17c](../guide/17c-case-the-check-that-stopped-the-server.md).

⚠ **A network mount is not "bound to the login session".** Earlier versions of this guide said so, to
explain why reading a share hangs from a scheduled job; the hang they described was this prompt. A check
that a share is mounted should still not read inside it: check the **kernel mount table** (`mount`, or
`os.path.ismount`), which asks for no access. It is not free of I/O — `ismount` stats the mount point, and
reading the table can block on an unresponsive server — so treat a check that cannot answer as unknown,
not unmounted. To catch a mounted-but-hung share, read inside it from a `command` check with a time limit,
run by a program macOS has approved, and treat a timeout as unknown.

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

## Metrics exporter — node_exporter

For the fleet metrics stack ([E13](../guide/examples/E13-fleet-metrics-stack.md)), macOS runs
**`node_exporter`** natively:

- **Install:** `brew install node_exporter` + `brew services start node_exporter` → a LaunchAgent on
  **`:9100`**. **Pin the version** for anything you rely on.
- **Fewer collectors than Linux, and different memory metrics** — macOS has no
  `node_memory_MemAvailable_bytes`; use `node_memory_active/wired/compressed/total_bytes` (used ≈
  `(active+wired+compressed)/total`). CPU (`node_cpu_seconds_total`), load (`node_load1`), and uptime
  match Linux.

**Consequence for dashboards:** the popular community "Node Exporter Full" dashboard is written
against **Linux** metric names, so on a Mac its memory panels render *No data* — macOS exposes
`node_memory_total_bytes` / `active` / `wired` / `compressed` and has **no** `MemAvailable` or
`MemTotal`. Don't debug it as a broken exporter: use a Darwin-specific dashboard (or fix the
queries) and keep the Linux one for Linux nodes.

## Roles on macOS — common mapping

- **`workstation`** — a MacBook; Tailscale on; services on-demand; permission preset
  standard/trusting ([10](../guide/10-permissions.md)).
- **`server`** — a Mac mini / always-on Mac; LaunchDaemons for 24/7 services; NAS mounts;
  permission preset cautious. Watch the privacy-prompt gotcha above for any scheduled job.

## Verifying (macOS)

- `brew doctor` clean; core tools resolve at their absolute paths.
- A launchd job you rely on actually runs **under launchd** (check its log), not just from your
  shell — the privacy-prompt trap. After any update to a program a job runs, check the screen.
- `security find-generic-password …` returns your vault key so non-interactive unlock works.
