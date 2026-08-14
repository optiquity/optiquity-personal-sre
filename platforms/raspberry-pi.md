# Platform spoke · Raspberry Pi

> **Maturity: partial** — the Pi-specific facts a fleet operator actually hits (SD-card wear, headless
> flash, arm64 build realities, single-purpose appliance). A Pi runs a Debian-family OS, so the
> **[Linux spoke](linux.md)** carries the common ground (apt, systemd, secrets, chezmoi, the
> mesh-gateway pattern); **this page is only the delta** — the ways a Pi is *not* a typical Linux box.

## Why a Pi gets its own spoke

A Raspberry Pi is a great always-on fleet node — cheap, silent, low-power — but it differs from a
server or workstation in ways that change how you operate it:

| Trait | Consequence for the operator |
|---|---|
| **Boots from a microSD card** | Flash storage has limited write endurance + weak random-write → **minimize writes**, and treat the card as a replaceable consumable with an off-box backup. |
| **arm64 (aarch64)** | Not every tool ships an arm64 binary; some are **Docker-only** → you build from source or use a distro package. |
| **Headless by design** | No monitor/keyboard, no BMC/IPMI, no serial console by default → provision **fully at flash time** (hostname, SSH keys, network) so first boot is already reachable. |
| **Modest, shared SoC** | One small CPU + RAM shared by everything → a Pi doing a **critical role** (gateway, DNS) should stay lean: native services, resource-capped, no heavy extras. |
| **Thermal + power sensitivity** | Passive cooling + USB-C power → watch temperature/throttling; and if it's on a UPS, coordinate shutdown. |

## microSD: the write-endurance problem

The single most important Pi-specific discipline. Reduce writes, and keep a restorable backup:

- **RAM-back the temporary paths.** Modern Raspberry Pi OS already mounts `/tmp` as tmpfs and enables
  **zram** swap (via `rpi-swap` / `systemd-zram-generator`) — *verify it's active* (`/proc/swaps`,
  `findmnt /tmp`) rather than assuming, and **don't double-install** a second zram package on top.
- **Bound the logs.** Cap journald so it can't grind the card:
  ```ini
  # /etc/systemd/journald.conf.d/10-microsd.conf
  [Journal]
  SystemMaxUse=100M
  MaxRetentionSec=7day
  Compress=yes
  ```
- **Use a high-endurance card** for an always-on Pi (endurance-rated, not just fast), and accept the
  card is replaceable.
- **Back up *config*, not a full image.** A live `dd` image is heavy and inconsistent; the robust
  recovery is *reflash + restore configuration*. Back up the small stuff — your systemd units, the
  network/boot config, tuning files, and a **prefs snapshot of the mesh client** — to the fleet's
  backup target, on a timer. **Never clone the mesh node's identity/state directory** into what would
  become a duplicate node; on restore, reinstall the mesh client and re-authenticate.

## Headless flash — provision at image time

Use **Raspberry Pi Imager**, pick the **64-bit OS Lite** (no desktop for a server role), and set the
customization *before* writing so the Pi is reachable on first boot with no monitor:

- **hostname**, **a non-default user** (not the legacy default), **SSH = public-key only** (paste the
  fleet's pubkeys), locale/timezone, and Wi-Fi only if needed.
- First boot is then already **key-only SSH** on the network — no password step, no console.

## arm64 reality: when there's no binary

Some tools you'll want ship **only a container image or amd64 builds**. On a Pi kept deliberately
container-free (see below), the options are:

- **A distro package** (`apt`, or a vendor `.deb`/`.apk` for arm64) — easiest; prefer it.
- **Build from source.** For a Go/Rust tool with no arm64 binary, install the toolchain *temporarily*,
  build the static binary, install it, then **remove the toolchain + caches**:
  ```bash
  sudo apt-get install -y golang-go              # temporary
  GOBIN=/tmp/b go install <module>@<version>     # build the static binary
  sudo install -m755 /tmp/b/<tool> /usr/local/bin/
  sudo apt-get remove -y golang-go && sudo apt-get autoremove -y   # clean up
  ```
  You end with just the binary — no toolchain, no runtime. (Building on the Pi is slow but reliable;
  cross-compiling on a faster host and copying the binary is the shortcut if you have a toolchain there.)

## Keep a role-critical Pi lean (native, not containers)

If the Pi runs something the fleet *depends on* — a mesh gateway, DNS, a UPS monitor — treat it as a
**single-purpose appliance**: prefer **native services over a container runtime** (fewer interacting
network/NAT layers to reason about on a small box), cap optional services with systemd
(`Nice=`, `CPUWeight=`, `MemoryMax=`), and **test the critical role after every change**. The generic
[Linux appliance/gateway pattern](linux.md#single-purpose-headless-appliance-eg-a-mesh-gateway) applies
directly; the Pi just makes "stay lean" non-negotiable.

- **Wired appliance?** Disable Wi-Fi for determinism (`dtoverlay=disable-wifi` in the boot config +
  turn the radio off), and give it a static/reserved address.
- **Publishing a small UI from the Pi** (a status page, a LAN inventory): bind it to **loopback** and
  expose it through the **mesh's private proxy** ("serve"), never a raw LAN port — the Pi is a *real
  host*, so its mesh Serve reaches roaming clients directly (unlike a container behind a NAT). See
  guide [08 · Networking](../guide/08-networking.md) § *Publishing a service*.

## Thermal, power, UPS

- **Watch throttling** — a Pi under sustained load can thermal- or under-voltage-throttle. Check
  temperature and the throttled state periodically (surface it in your monitoring).
- **On a UPS?** Run the mesh/NUT **client** so the Pi shuts down gracefully on low battery, with the
  UPS's USB-connected host as the master — no extra wiring, and the Pi never becomes the authority.
- **Feed it into metrics.** The Pi runs the same `node_exporter` + **textfile collector** as any Linux
  node ([linux.md](linux.md) · [E13](../guide/examples/E13-fleet-metrics-stack.md)): a small timer
  script writes the **Pi-specific** signals the built-ins miss — `vcgencmd measure_temp` /
  `get_throttled`, and a `upsc` read of the network UPS — as `.prom` files the exporter serves. Keep
  the write cadence modest (SD wear) and the exporter version **pinned**.

## Reuse the Linux spoke

Everything not listed here is just Debian-family Linux — **package manager, systemd units, secret
store, chezmoi, roles, the mesh-gateway pattern** all live in **[platforms/linux.md](linux.md)**. Read
that first; this page only adds the Pi delta.

## Verifying (Raspberry Pi)

- `cat /proc/swaps` + `findmnt /tmp` — zram + tmpfs actually active.
- `journalctl --disk-usage` — logs bounded.
- `vcgencmd get_throttled` / `vcgencmd measure_temp` — no under-voltage/thermal throttling.
- `dpkg --print-architecture` → `arm64` on a 64-bit image.
- `df -h /` — card not filling; your config backup landing off-box on its timer.
