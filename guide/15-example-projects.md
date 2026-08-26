# 15 · Example projects

Worked, end-to-end examples of the personal-SRE operator **owning a tool or service across its
whole lifecycle — install *and* maintenance**, not just a one-time setup. Each shows the same
loop: bring it up under governance, track it as a project, and keep it current deliberately.

These are **generic patterns, not anyone's real config** — they use roles and placeholders
(`<...>`), no personal names, paths, or credentials. Adopt the *shape*; fill in your specifics
in **your own** repo.

Each example lives in its own doc under [`examples/`](examples/). This page is the catalog.

> **Read the concepts first.** Every example leans on the installer pattern
> ([07 · Tools](07-tools-requirements.md)), the config-manager flow
> ([05 · chezmoi](05-chezmoi.md)), the governance gates ([03 · Governance](03-governance-rules.md)),
> and — where relevant — networking ([08](08-networking.md)), secrets ([06](06-secrets.md)),
> and skills ([11](11-agents-skills.md)).

---

## A · Install-and-keep-current tools

Tools the operator installs symmetrically across nodes and keeps updated deliberately (never
auto-updating into surprises).

- **[A1 · A diagram/doc toolchain](examples/A1-diagram-doc-toolchain.md)** — install a small,
  role-aware CLI toolchain (graph/diagram/doc generators) via an idempotent `run_onchange`
  installer the config manager runs on apply; keep it current with the update pass. The cleanest
  demonstration of the core installer pattern.
- **[A3 · An npm-global CLI (avoiding the self-update trap)](examples/A3-npm-global-cli.md)** — a
  CLI whose native updater targets one package manager (npm), so installing it a *second* way
  spawns a duplicate that fights over the binary. Shows install + the "one install method,
  deliberately" maintenance discipline.

## B · Scheduled services & backups

Small always-on or scheduled jobs — the place governance **Rule 4 (back up before apply)** and
the **gated service-bootstrap** rule become concrete, plus the classic platform gotchas.

- **[B4 · A nightly backup daemon](examples/B4-nightly-backup-daemon.md)** — ship a database or
  directory to a backup target over SSH on a schedule, with a remote integrity check and *loud*
  failure. Covers scheduled services, the bare-PATH / can't-write-a-network-mount traps, and the
  approval-gated bootstrap.
- **[B5 · A network-mount keeper](examples/B5-network-mount-keeper.md)** — a passive scheduled job
  that keeps a network volume (NFS/SMB) mounted and re-mounts it if it drops. A minimal always-on
  service and its per-platform service-manager mapping.

## C · Self-hosted apps over the private mesh

Standing up real services and exposing them **private-first, public-only-deliberately** over the
mesh — the [08 · Networking](08-networking.md) publish-a-service discipline, applied.

- **[C6 · A self-hosted automation runtime](examples/C6-automation-runtime.md)** — stand up a
  workflow/automation service (n8n-style) in a container, reachable **privately** over the mesh by
  default, **publicly** only when a specific webhook needs it. Owning a real service end-to-end.
- **[C7 · A container runtime + app stack](examples/C7-container-runtime-stack.md)** — install a
  container runtime and bring up an app stack reachable over the mesh; the container half of
  self-hosting, plus per-host run-mode divergence (always-on `server` vs on-demand `workstation`).

## D · Composed skills & credentials

Turning credential access + automation into a **governed, reusable skill** — secrets + skills +
guardrails together.

- **[D9 · A vault-read helper + login-automation skill](examples/D9-vault-login-skill.md)** —
  compose a **read-only** vault helper with browser automation into a `SKILL.md` that logs into a
  service the operator can't reach by API, with destructive-op confirmation baked in. Ties
  [06 · Secrets](06-secrets.md) + [11 · Agents & skills](11-agents-skills.md).

## E · Fleet operations

The *maintenance* half made explicit — operating across several nodes without letting drift or
exposure creep in.

- **[E10 · A deliberate fleet-update pass](examples/E10-fleet-update-pass.md)** — the "don't
  auto-update; inventory what's behind, update per machine, verify, note what's held and why"
  runbook. Shows updates as a governed *project*, not a reflex.
- **[E11 · Publishing a service safely](examples/E11-publish-a-service.md)** — take a local
  service and expose it **private-first** (mesh-only), **public only deliberately**, with what's
  exposed and how-to-unpublish written down. The exposure discipline as its own tracked example.
- **[E12 · A dedicated mesh gateway (+ HA backup)](examples/E12-dedicated-mesh-gateway.md)** — move
  the mesh's subnet-router + exit-node roles off a busy multi-duty box onto a small **dedicated**
  node, keep the old host as a **standby** for automatic failover, and close the **subnet-route
  hairpin** (on-LAN nodes must not accept the tunnel route for their own LAN). Owning the tailnet's
  edge.
- **[E13 · A fleet metrics stack (exporters → Prometheus + Grafana)](examples/E13-fleet-metrics-stack.md)** —
  a lightweight **exporter on every node** (multi-OS), one **central node** that stores + graphs, the UI
  **private on the mesh**, dashboards **provisioned as config**, and power/**UPS** folded in. The
  emit-here / store-there fleet watch — with the multi-OS metric-name reality and the real traps.
- **[E14 · GitHub-as-a-service metrics](examples/E14-github-metrics.md)** — fold **GitHub repo metrics**
  into the metrics stack you already run: a **maintained exporter as one internal container** (no mesh
  sidecar), a gentle rate-limited scrape, a **read-only scoped token**, and the judgment call of **which
  repos are worth tracking** (public yes; private usually not, and why). Adopt the *piece*, not the demo stack.
- **[E15 · Media automation for a self-hosted library](examples/E15-media-automation.md)** — *enhance*
  and *observe* a media server with **small add-ons, not a second stack**: a **config-as-code
  collection manager** (scheduled batch job, no UI, env-injected secrets) and an **analytics exporter**
  into the Grafana you already run. The judgment calls people miss — **where hardware transcoding
  actually works** (container vs native), what **"missing" really means** (titles ≠ episodes), and
  matching collection sources to a library's intent.
- **[E16 · Fleet health, alerting, and the update digest](examples/E16-fleet-health-and-alerting.md)** —
  give the operator **eyes and a voice**: **functional health checks** across the fleet (Gatus —
  status + body + latency, not just up/down) with **email on failure**, plus a **weekly update
  digest** that inventories what's behind on every node and mails it to you — **notify-only**, it
  upgrades nothing. Ships reusable tools + a bootstrap hook in
  [`skeleton/monitoring/`](../skeleton/monitoring/). The observe/alert complement to E13's metrics
  and the automation of E10's inventory.

---

## Using these examples

- **They are illustrative.** Copy the *structure* — the installer script shape, the plan doc, the
  update cadence — into **your** repo, then fill in your real tools and hosts. Never copy an
  example's placeholders as if they were config.
- **Track each as a project.** The point of every example is that the work becomes a row in your
  registry with a plan doc ([04 · Structure](04-structure.md)) — install *and* the ongoing
  maintenance, both visible.
- **Respect the gates.** Anything material in an example (a service bootstrap, an apply, a push)
  stops for your approval in real use, exactly as [03 · Governance](03-governance-rules.md)
  requires.
