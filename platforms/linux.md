# Platform spoke · Linux

**Maturity: Partial.** The **single-purpose headless appliance / mesh-gateway** path (below) is
battle-tested; the rest of the mappings are the well-known Linux equivalents, correct in outline —
treat the remaining ⛏ TODO items as "verify + expand before relying on." Read `guide/` for the
*why*; this is the Linux *how*.

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
Schedule with a **`.timer`** unit (the cron / `StartCalendarInterval` equivalent), or trigger on a
filesystem change with a **`.path`** unit (the `WatchPaths` equivalent — e.g. run an audit after
anything is installed). Two habits worth keeping:

- **Extend a unit with a drop-in, don't edit it.** `/etc/systemd/system/<unit>.d/10-thing.conf`
  survives package upgrades and keeps your change separable — that's also how you hand a daemon a
  secret (`EnvironmentFile=`, see [06](../guide/06-secrets.md)).
- **Order anything that binds a specific address after the network.** A service that binds a fixed
  LAN IP can start before DHCP assigns it, fail with *cannot assign requested address*, exhaust its
  restart burst, and stay dead until you notice. `After=/Wants=network-online.target` plus a
  patient `RestartSec=` prevents it. (Or bind `0.0.0.0` and sidestep it entirely.)

Worked units + a drop-in ship in [`../skeleton/monitoring/`](../skeleton/monitoring/).

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

## Single-purpose headless appliance (e.g. a mesh gateway)

A dedicated one-job Linux node — the archetype being a **mesh gateway**
([08 · Networking](../guide/08-networking.md),
[E12](../guide/examples/E12-dedicated-mesh-gateway.md)), or any small always-on box that does
exactly one thing. The pattern:

- **Key-only SSH from first boot.** Flash the image with the OS's headless config (an SD-card
  imager, cloud-init, or an autoinstall file): set the hostname, create the operator's user, and
  **seed the operator's public keys into `authorized_keys` at image time** with **password auth
  disabled**. The box comes up key-only on first boot — no password window, and no default account
  to remove.
- **Passwordless sudo for automation — deliberately.** So the operator can run privileged commands
  **non-interactively** over SSH (the framework never handles a `sudo` password —
  [08](../guide/08-networking.md)), grant the operator's user `NOPASSWD` sudo. The blast radius is
  bounded because inbound SSH is **key-only from just the operator's machines** — the key *is* the
  credential. (A shared/multi-user box keeps the password; a single-purpose appliance you alone
  administer is where passwordless sudo pays off.)
- **Single-interface discipline.** A gateway/router node should run on **one** interface (wired
  Ethernet). If the board also has Wi-Fi, keep it as a *setup fallback*, then disable it once the
  wired path is proven — two addresses on the same LAN muddy routing. Soft-off via the network
  manager (`nmcli radio wifi off`); permanent via the boot config (a `disable-wifi` overlay on a
  Pi, or blacklisting the module).

### A boot-persistent tuning unit — the systemd oneshot pattern

Some settings don't survive a reboot and must be **re-applied at boot** — an interface offload
tweak, an `ethtool` flag, a one-time device setup. A **systemd oneshot** is the clean, tracked way
(the worked systemd example this spoke owed you):

```ini
# /etc/systemd/system/<name>-tuning.service
[Unit]
Description=<what this applies, and why>
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/<command> <args>     # e.g. an ethtool offload flag on <iface>

[Install]
WantedBy=multi-user.target
```
```sh
sudo systemctl daemon-reload
sudo systemctl enable --now <name>-tuning.service   # (gated) applies now + every boot
```
Ship the unit via config-management or `install` it from a tracked source; enabling it is the
**material action** ([Rule 1](../guide/03-governance-rules.md)). For *scheduled* work (not
boot-once), pair a `.service` with a `.timer` — the cron / calendar-interval equivalent.

### IP forwarding (for a router / exit node)

A subnet router or exit node must forward packets — enable it persistently in `sysctl.d`:
```sh
printf 'net.ipv4.ip_forward = 1\nnet.ipv6.conf.all.forwarding = 1\n' \
  | sudo tee /etc/sysctl.d/99-<gateway>.conf
sudo sysctl -p /etc/sysctl.d/99-<gateway>.conf
```

## Monitoring the fleet from a host (native)

A Linux node can watch the rest of the fleet without a container stack. Two complementary tools answer
two different questions — don't conflate them. Ready-to-fill config, an email-alerting drop-in, and
the surrounding tools are in [`../skeleton/monitoring/`](../skeleton/monitoring/); the end-to-end
narrative is [E16](../guide/examples/E16-fleet-health-and-alerting.md):

- **Up/down of always-on infrastructure** — a lightweight health checker (e.g. Gatus) with
  **in-memory storage** (no disk writes), checking internet / DNS / router / servers by
  TCP/HTTP/DNS. Bind it to loopback and publish via the mesh's private proxy ("serve"). If the tool
  ships **Docker-only** (no arm64/native binary), build the static binary from source rather than
  dragging a container runtime onto a lean node.
- **Presence/inventory of *everything* on the LAN** — an ARP-based scanner (e.g. WatchYourLAN) that
  discovers every device and tracks **last-seen + new-device alerts**. This is the right tool for
  **sleep-prone devices** — printers, streamers, TVs, a 3D printer — which power down their network
  interface in energy-saver and would show a permanent false "down" under an up/down check. Presence
  ("last seen 2 h ago") is honest where up/down lies. It needs raw sockets → grant **`CAP_NET_RAW`**
  (don't run it as full root); bind loopback + serve (it has no auth of its own).

Rule of thumb: **up/down-monitor only what's *supposed* to always be up; inventory everything else.**
Mixing sleepers into up/down alerts just trains you to ignore the dashboard.

## Metrics exporter — node_exporter (+ textfile collector, UPS/NUT)

For the fleet metrics stack ([E13](../guide/examples/E13-fleet-metrics-stack.md)), Linux (incl. the
Pi) runs **`prometheus-node-exporter`** (apt) as a systemd service on **`:9100`**. **Pin what you
rely on**, resource-cap it, and bind it where your collector can reach it — the LAN address if your
Prometheus is a container that can't reach the mesh (see E13's reachability note).

- **Textfile collector.** Point the exporter at a directory
  (`--collector.textfile.directory=/var/lib/node_exporter/textfile_collector`) and a tiny
  timer-driven script can drop `<name>.prom` files there for anything the built-in collectors don't
  cover (a speedtest, mesh direct-vs-relay, a UPS read). Write **atomically** (`mv` a temp file) and
  leave it world-readable so the exporter's user can read it.
- **UPS over the network (NUT).** If a UPS's USB host runs a NUT server, `apt install nut-client` and
  read it **read-only** with `upsc <ups>@<host>` (the server must allowlist your client); a textfile
  collector turns that into `ups_*` metrics → a panel. For **graceful shutdown**, set
  `MODE=netclient` and add an `upsmon` **secondary** (`MONITOR <ups>@<host> 1 <user> <pass> secondary`)
  with a `SHUTDOWNCMD` — the USB host stays the authority and shuts down last.
  - **Debian trap:** upsmon may log `fopen /run/nut/…: No such file or directory` if the packaged
    tmpfiles entry is missing — create `/run/nut` (and an `/etc/tmpfiles.d/` entry). It's cosmetic
    under `Type=simple`, but tidy it.

## chezmoi on Linux

Standard ([05](../guide/05-chezmoi.md)); `run_onchange_`/`run_once_` scripts are POSIX sh, so
the [skeleton installer](../skeleton/installers/install-tooling.sh.template) works with minimal
adaptation (just the `PM` block). Source dir default: `~/.local/share/chezmoi`.

## Roles on Linux — common mapping

- **`server`** — a headless Linux box is the archetypal always-on `server`: systemd units for
  24/7 services, Tailscale, cautious permission posture. The cleanest home for automation.
- **`workstation`** — a Linux desktop/laptop; keyring for secrets; standard/trusting posture.
- **`gateway` / appliance** — a small single-board box dedicated to one job (the mesh subnet
  router + exit node is the archetype): key-only from first boot, passwordless sudo for
  automation, single-interface, minimal surface. See the appliance section above +
  [E12](../guide/examples/E12-dedicated-mesh-gateway.md).

## ⛏ Expand before relying on
- A verified headless secret-unlock recipe (the keyring-without-a-session problem).
- A worked systemd **user**-unit + timer from tracked config (the system oneshot is covered above).
- Distro-specific package-name differences for the optional tools.

## Verifying (Linux)
- `systemctl --user status <name>` shows your service healthy.
- Non-interactive `ssh <node>` is key-only.
- The vault-read helper unlocks **without** a graphical session on a headless `server`.
- A **gateway** node: `ip -br addr` shows a single wired interface; the mesh status shows it
  **actively serving** the subnet route; `sysctl net.ipv4.ip_forward` returns `1`.
