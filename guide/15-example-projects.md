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
