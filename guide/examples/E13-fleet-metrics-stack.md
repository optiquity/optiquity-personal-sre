# E13 · A fleet metrics stack (exporters → Prometheus + Grafana)

**Section E — fleet operations.** Back to the [catalog](../15-example-projects.md).

**What this shows:** turning "I have no real idea how my machines are doing" into a **live, historical
fleet view** — a lightweight **exporter on every node**, one **central node** that stores + graphs
(Prometheus + Grafana), the whole thing **private on the mesh**, dashboards **provisioned as config**,
and (optionally) **UPS/power** folded in. The *emit-here / store-there* split keeps every node lean.

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

---

## The scenario

You have a handful of always-on machines — a server, a NAS, a mini-PC, a Pi gateway — and no
visibility into any of them over time. When something feels slow or a service dies, you're guessing.
You want CPU / memory / disk / network / uptime per machine, kept for weeks, on one page — without
turning every node into a monitoring appliance or exposing anything to the internet.

## Why do it "the framework way"

- **Emit vs store.** Each node runs only a tiny **exporter** (native, a few MB, keeps no data). One
  capable **always-on node** does the heavy lifting (the time-series DB + dashboards). Nodes stay
  single-purpose.
- **Private by default.** The UI is reachable **only on the mesh** via a Serve sidecar, never the
  public internet — see [E11](E11-publish-a-service.md).
- **Config as source.** The scrape list, the datasource, and the dashboards are **files in your
  repo**, not click-ops that live only inside a container volume.
- **Pin versions.** An appliance you rely on is **never `:latest`** — pin it, bump it deliberately.

## The shape

### 1. An exporter per node (native, lean)

| OS | Exporter | Port | Notes |
|---|---|---|---|
| Linux / Pi | `node_exporter` (`prometheus-node-exporter`) | 9100 | apt; arm64 builds fine |
| macOS | `node_exporter` (brew) | 9100 | fewer collectors; **different memory metric names** than Linux |
| Windows | `windows_exporter` (`.msi`) | 9182 | installs a service; **you must add an inbound firewall rule** |

Run each as a service (systemd / launchd / Windows service). Bind it where your collector can reach
it — see the reachability note next.

### 2. One central node: Prometheus + Grafana, private

Put Prometheus (the time-series DB) and Grafana (the dashboards) on your **most capable always-on
node**. If you run them as containers, front each with a **mesh Serve sidecar** so the UI is
tailnet-only. Give Prometheus a **retention window** + a **named volume**; wire Grafana's datasource
to Prometheus **by container name** with a **fixed `uid`** (provisioned dashboards reference it).

### 3. Scrape reachability — the decision that bites people

If Prometheus runs **in a container behind the mesh's NAT**, it **cannot reach mesh (`100.x`)
addresses** — only the LAN. So **scrape exporters over the LAN**, and bind each exporter to its LAN
address. Host metrics are low-sensitivity and behind your router; firewall them to the collector if
you want it tighter. Don't try to scrape a `*.ts.net` name from a container.

### 4. Provision the dashboards as config

Drop the **datasource** and the **dashboard JSON** into files a provider loads on start — they come
back on any rebuild, unlike a click-imported dashboard that lives only in the volume. Import a
community dashboard once, export its JSON, **pin its datasource `uid`**, and commit it.

### 5. Multi-OS reality: the metric names differ

Linux, macOS, and Windows exporters **don't share metric names** (`node_*` vs `windows_*`, and even
macOS's memory metrics differ from Linux's `MemAvailable`). To show every machine on one panel,
**combine with PromQL `or`**:

```promql
(100 - avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m]))*100)
or
(100 - avg by(instance)(rate(windows_cpu_time_total{mode="idle"}[5m]))*100)
```

Some concepts don't exist everywhere (Windows has no load average) — **say so in the panel** rather
than faking it. Things that would overlap confusingly across machines (network interfaces) are
better as **one panel per node**. A single **snapshot table** (machine × CPU/mem/load/uptime, joined
by `instance`) beats a wall of per-machine stat tiles.

### 6. (Optional) Fold in power / UPS

If a UPS is on the network (e.g., a NAS is the USB master running a NUT server), a **read-only NUT
client** on another node can pull battery / load / runtime, a **textfile collector** turns that into
metrics the exporter already exposes, and a panel graphs it. For graceful shutdown, run the node as
a NUT **secondary** with a `SHUTDOWNCMD` — and **test the mains-unplug with a human present**, since
it powers a machine down.

## Maintenance — the ownership half

- **Add a node:** install its exporter, add **one line** to the scrape file.
- **Bump a version:** change the pin, re-pull, and **re-test that dashboards still provision + render**
  — storage/provisioning behavior changes between major versions.
- Watch the traps below.

## Traps (all real)

- **The Windows exporter is invisible from the LAN** until you add an **inbound firewall rule** — the
  `.msi` adds none (it answers on localhost, `0` from the LAN).
- **Freshly-provisioned Grafana dashboards can be invisible** right after a first deploy — the search
  index is built *before* provisioning runs; **restart Grafana once** (or hard-refresh).
- **Container image pulls hang headless** when a credential helper wants a GUI keychain — pull from an
  interactive session, or bypass the helper with an empty `DOCKER_CONFIG` for public images.
- **A restarted app container strands its Serve sidecar** (new network namespace) — recreate both
  together, don't restart the app alone.

## What you learn from this example

- The **emit / store** split, and why nodes stay lean.
- **Private-by-default** UIs on the mesh.
- **Config-as-source** dashboards that survive any rebuild.
- That a real fleet is **multi-OS**, and how to unify it in PromQL.

## Adapt it

- **One machine?** Still worth it — Prometheus + Grafana + one exporter on the same box.
- **Prefer up/down + alerts over graphs?** Pair this with an availability monitor / status page.
- **Lighter TSDB?** A single-binary Prometheus-compatible store drops into the same slot.
