# C7 · A container runtime + app stack

**Section C — self-hosted apps over the private mesh.** Back to the [catalog](../15-example-projects.md).

**What this shows:** installing a **container runtime** and bringing up a small **app stack**
reachable over the mesh — the container *foundation* under [C6](C6-automation-runtime.md), plus a
clean example of **per-host run-mode divergence** (always-on on a `server`, on-demand on a
`workstation`).

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

---

## The scenario

Self-hosting needs a **container runtime**. You want one installed across the nodes that host
services, and a small **app stack** (a database + an app + maybe a reverse proxy) brought up on the
`server` — reachable privately over the mesh. And you want the runtime to behave differently by
role: **always running** on the always-on `server`, but **on-demand** on your interactive
`workstation` (a laptop shouldn't burn battery running containers at boot).

## Why do it "the framework way"

Two framework ideas show up crisply here:

- **Role-based divergence done right** — "start at login on `server`, on-demand on `workstation`"
  is a *role rule* in the config manager, not a per-machine hack ([05 · chezmoi](../05-chezmoi.md),
  [Rule: symmetry with justified divergence](../03-governance-rules.md)).
- **Pick one runtime, avoid conflicts** — installing two competing runtimes (e.g. two Docker-API
  providers) causes socket/daemon conflicts. Choose one per node and don't stack them (the
  container analogue of [A3](A3-npm-global-cli.md)'s "one install method").

## The shape

### 1. Install one runtime, role-aware

Choose a runtime (OrbStack, Docker Desktop/Engine, Podman, containerd — per your
[platform spoke](../../platforms/macos.md)) and install it via the [installer pattern](../07-tools-requirements.md):

```sh
# install <runtime> (absolute pkg-manager path; idempotent)
# role-conditional autostart:
#   server)      enable start-at-login/boot  -> always-on
#   workstation) leave autostart OFF          -> on-demand
```

The **autostart-at-boot toggle is the role divergence** — one installer, two behaviors, both
recorded. Don't install a *second* runtime alongside it (daemon/socket conflicts).

### 2. Bring up the app stack (tracked compose)

```
# Compose-style intent (tracked; secrets via ${VAR} from the vault):
#   db:    <database> image, persistent volume, restart: always
#   app:   <app> image, depends_on db, bound to loopback/mesh (NOT 0.0.0.0)
#   proxy: (optional) a reverse proxy fronting the app on the mesh
```

Compose file tracked ([05 · chezmoi](../05-chezmoi.md)); data on **persistent volumes**; secrets
**referenced**, never inline ([06 · Secrets](../06-secrets.md)).

### 3. Expose over the mesh (private first)

Reach the app at a **tailnet MagicDNS name**, private by default ([08 · Networking](../08-networking.md));
publish publicly only a specific surface if truly needed, documented
([E11 · Publishing a service safely](E11-publish-a-service.md)). Bringing the stack up is a
**gated service bootstrap** ([Rule 1](../03-governance-rules.md)).

### 4. Track it

Registry row + `PLAN.md` ([04 · Structure](../04-structure.md)): the runtime + version per role,
the stack's images/volumes, exposure, and the **role divergence** (server always-on vs workstation
on-demand) recorded as *unavoidable* (a genuine role difference), per
[Rule 7](../03-governance-rules.md).

## Maintenance — the ownership half

- **Update the runtime + images deliberately**, in a window, with a smoke test (the stack comes
  up, the app responds). Pin image versions; back up stateful volumes before major bumps
  ([B4](B4-nightly-backup-daemon.md)).
- **Keep the "one runtime" rule** — if a tool tries to pull in a second container provider,
  that's a conflict to resolve, not accept.
- **Watch the role divergence stays intentional** — the `server`-always-on / `workstation`-on-demand
  split is recorded; if a third node appears, decide its role's behavior explicitly rather than
  copying whichever was handy.
- **Persistent volumes are state** — reproducible compose ≠ backed-up data.

## What you learn from this example

- **Role-based divergence** is a first-class, *justified* pattern — not every node is identical,
  and the config manager expresses the difference cleanly.
- **One runtime per node** avoids the daemon/socket conflict class (the container cousin of
  "one install method").
- The **container is the easy part**; **exposure, persistence, and role-correct autostart** are
  the ownership.

## Adapt it

In **your** repo: install one runtime role-aware, write the tracked compose with vault secrets +
persistent volumes, bring it up private over the mesh (gated), record the role divergence, and fold
its volumes into backups + its images into your update pass.

**Related:** [05 · chezmoi (roles)](../05-chezmoi.md) · [08 · Networking](../08-networking.md) ·
[C6 · Automation runtime](C6-automation-runtime.md) · [A3 · one install method](A3-npm-global-cli.md)
· [catalog](../15-example-projects.md).
