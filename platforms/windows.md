# Platform spoke · Windows

**Maturity: Partial.** The networking, package-manager, container, and OS-update parts are
written from real experience; the config-manager-templating, service-manager, and secret-store
mappings are **stubbed** (marked ⛏ TODO) — fill them as you go. As with every spoke, this maps
the hub's concepts to Windows; read `guide/` for the *why*.

## At a glance

| Concept (hub) | Windows specific | Status |
|---|---|---|
| Package manager ([07](../guide/07-tools-requirements.md)) | **winget** (built-in) or **scoop** | ✅ |
| Private mesh + SSH ([08](../guide/08-networking.md)) | Tailscale + **OpenSSH for Windows** (key-only) | ✅ |
| Container runtime ([07](../guide/07-tools-requirements.md)) | **Podman** (+ Podman Desktop) over **WSL2** | ✅ |
| OS updates | **Windows Update** — pin to manual (see below) | ✅ |
| Config manager ([05](../guide/05-chezmoi.md)) | chezmoi on Windows (PowerShell templating) | ⛏ partial |
| Service manager ([07](../guide/07-tools-requirements.md)) | **Task Scheduler** / Windows Services | ⛏ TODO |
| Secret store ([06](../guide/06-secrets.md)) | **Windows Credential Manager** / DPAPI | ⛏ TODO |
| Home path ([01](../guide/01-concepts.md)) | `%USERPROFILE%` (`$HOME` in PowerShell/WSL) | ✅ |

## Package manager — winget / scoop

```powershell
winget install --id Git.Git
winget install --id twpayne.chezmoi
winget install --id RedHat.Podman           # container runtime
# scoop is an alternative that installs to userspace (no admin):
#   irm get.scoop.sh | iex ; scoop install git chezmoi
```
Prefer **winget** for system tools, **scoop** where you want no-admin userspace installs.

**Gotcha — non-interactive install:** over SSH/automation, `winget` frequently needs an
**elevated, interactive** session — it can return *"Access is denied"* from a plain
non-interactive SSH shell. Run package updates from an **elevated PowerShell on the box** (local
console or RDP), not from the fleet's SSH automation. This is a real constraint: Windows package
management doesn't drive cleanly headless the way `brew`/`apt` do.

## SSH with keys (OpenSSH for Windows)

Windows ships OpenSSH. To make a Windows node a key-only SSH target ([08](../guide/08-networking.md)):

- Install/enable the **OpenSSH Server** feature; set the `sshd` service to start automatically.
- **Key placement is the gotcha.** For a standard user, authorized keys go in
  `%USERPROFILE%\.ssh\authorized_keys`. For an **administrator** account, Windows OpenSSH
  instead uses a single shared file: `C:\ProgramData\ssh\administrators_authorized_keys`, and
  it is **strict about ACLs** — that file must be owned/writable only by Administrators/SYSTEM
  or `sshd` ignores it. Getting the ACLs wrong = silent key rejection.
- Disable password auth in `C:\ProgramData\ssh\sshd_config` (`PasswordAuthentication no`) once
  keys work.
- Keys are secrets — never committed ([06](../guide/06-secrets.md)).

Inbound key-only SSH from your other nodes (e.g. `workstation → windows-node`) then works like
any other node, over the Tailscale mesh.

## Private mesh — Tailscale

Install Tailscale for Windows; the node joins the tailnet and gets a MagicDNS name like any
other ([08](../guide/08-networking.md)). Note a common LAN reality: if the Windows box is on
Wi-Fi and other nodes are wired (or vice versa) with **client isolation** between them, the
**tailnet is the reliable path** even on the same premises — reference the node by its tailnet
name, not a LAN IP.

## Container runtime — Podman over WSL2

- **Podman** (CLI + optional Podman Desktop) runs Linux containers via **WSL2**. Install WSL2
  first (`wsl --install`), then Podman.
- Podman is a good Docker-Desktop alternative (no licensing friction). Containers are **Linux**
  containers running in the WSL2 VM.
- Run mode is typically **on-demand** unless you set up headless-at-boot (which ties into the
  Task Scheduler / service story below — ⛏ TODO).

## OS updates — pin Windows Update to manual

Unlike the framework's "update deliberately" stance ([07](../guide/07-tools-requirements.md)),
Windows Update wants to run itself. To take control, **pin it to manual** and patch on your
schedule:

- Disable/handle the automatic update behavior (Group Policy, the `wuauserv` service, or a
  toggle script) so updates don't apply unattended.
- Keep a simple **on/off pair** of scripts (`wu-on` / `wu-off`) to re-enable, patch via
  **Settings → Windows Update**, then re-pin. Patch *deliberately*, not routinely.
- This is the Windows equivalent of "don't auto-update everything" — the OS just fights you
  harder about it.

Also worth doing on a fresh Windows node: **remove vendor bloat/AV** (OEM "security" add-ons)
that interferes with a clean setup.

## ⛏ Config manager on Windows — partial

chezmoi runs on Windows, but templating and script hooks differ:
- Source dir + `chezmoi.toml` live under `%USERPROFILE%`; the [05](../guide/05-chezmoi.md) flow
  (dev clone → prod source → pull+apply) is the same.
- Scripts run via **PowerShell**, not POSIX sh — the installer template
  ([skeleton](../skeleton/installers/install-tooling.sh.template)) needs a PowerShell
  equivalent on Windows. **⛏ TODO:** a `.ps1` installer variant + notes on run_onchange behavior
  on Windows.

## ⛏ Service manager on Windows — TODO

For fleet monitoring, the practical note today: Windows nodes are **digest-only**. `winget` needs
an elevated *interactive* session, so an update pass can't be driven over SSH the way `apt`/`brew`
can — the framework's update digest therefore reports Windows as a **manual** node (it tells you to
go run it, rather than pretending it can). Metrics are fine: `windows_exporter` scrapes like any
other node. Task Scheduler is the launchd/systemd-timer analog if you want local scheduled checks.

The launchd equivalent is **Task Scheduler** (for scheduled jobs) and **Windows Services** (for
daemons). **⛏ TODO:** how to define a scheduled task / service from tracked config, the
approval-gated "bootstrap" step, and the headless-at-boot pattern for Podman.

## ⛏ Secret store on Windows — TODO

The Keychain equivalent is **Windows Credential Manager** (and **DPAPI** for encryption at
rest). **⛏ TODO:** the non-interactive vault-unlock pattern on Windows (how a helper reads a
master key from Credential Manager, à la `security` on macOS), and which vault CLIs
(`keepassxc-cli`, `op`) behave well on Windows.

## Metrics exporter — windows_exporter

For the fleet metrics stack ([E13](../guide/examples/E13-fleet-metrics-stack.md)), Windows uses
**`windows_exporter`**, not `node_exporter`:

- **Install:** grab the latest `windows_exporter-<ver>-amd64.msi` from GitHub releases (no `winget`
  needed) and `msiexec /i … /quiet`. It installs a **service** on **`:9182`** with default collectors
  (cpu, memory, net, os, …). **Pin the version.**
- **⚠️ Firewall — you must add an inbound rule.** The `.msi` adds none, so `:9182` answers on
  localhost but is **invisible from the LAN** (the collector gets nothing). Add a LAN-scoped allow:
  `New-NetFirewallRule -DisplayName windows_exporter -Direction Inbound -Protocol TCP -LocalPort 9182 -Action Allow -RemoteAddress <lan-cidr>`.
- **Different metric namespace** — Windows metrics are `windows_*`, not `node_*`; combine them in
  PromQL with `or` (see E13). Windows has **no load average**.

## Roles on Windows — common mapping

- **`windows-node`** — a Windows box joined for specific workloads (containers, Windows-only
  tools). Key-only SSH inbound; Tailscale on; Windows Update pinned to manual; Podman on-demand.
  A cautious permission posture if it runs unattended.

## Verifying (Windows)

- `ssh <windows-node>` from another node works **key-only** (no password prompt) — the ACL trap
  is the usual failure.
- The node answers over its **tailnet name** even if LAN isolation blocks the direct path.
- `winget list` / `podman version` succeed from an **elevated** session.
- Windows Update shows **manual/paused**, not auto-applying.
