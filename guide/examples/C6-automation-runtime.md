# C6 · A self-hosted automation runtime

**Section C — self-hosted apps over the private mesh.** Back to the [catalog](../16-example-projects.md).

**What this shows:** standing up a real self-hosted service — a **workflow/automation runtime**
(n8n-style) — in a container, reachable **privately over the mesh by default** and **publicly only
when a specific webhook needs it**. The full "own a service end-to-end" example, applying the
[08 · Networking](../08-networking.md) *publish-a-service* discipline.

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

---

## The scenario

You want a **self-hosted automation runtime** on your always-on `server` — a service that runs
workflows, reacts to webhooks, and glues your tools together (n8n, Node-RED, Huginn, and similar
are all this shape). It should:

- run **24/7** on the `server`,
- be reachable **privately** (just your own devices) for the admin UI,
- expose **only specific webhooks publicly** when an external service must call in — not the whole
  app,
- keep its **secrets out of git** and its data persistent.

## Why do it "the framework way"

Self-hosting is where "the operator owns a service" gets real — install, expose, secure, persist,
and maintain, all as one tracked project. The framework's opinion is strong here:
**private-by-default, public-only-deliberately** — you expose the *one* surface that genuinely
needs it, document what's exposed, and everything else stays on the mesh.

## The shape

### 1. Prereqs (added per this project, not preemptively)

- A **container runtime** on the `server` (see [C7 · Container runtime + stack](C7-container-runtime-stack.md)
  for standing that up).
- The **private mesh** (Tailscale) already in place ([08 · Networking](../08-networking.md)).
- A place for **persistent data** (a named volume / bind mount) and **secrets from the vault**
  ([06 · Secrets](../06-secrets.md)), never inline.

### 2. Run the service in a container, config tracked

```
# Compose-style intent (tracked in your repo; secrets via ${VAR}, never literals):
#   service: <automation-runtime> image, restart: always
#   volumes: a persistent data volume (workflows, credentials store)
#   env:     ${WEBHOOK_URL}, ${ENCRYPTION_KEY}, ... resolved at runtime from the vault
#   bind:    loopback or the mesh interface — NOT 0.0.0.0 public by default
```

The compose file / unit is **tracked** ([05 · chezmoi](../05-chezmoi.md)); the **secrets are
references** resolved on the node.

### 3. Expose it — private first

- **Admin UI + normal use → private over the mesh.** Front the service with the mesh's private
  "serve" mechanism (e.g. Tailscale Serve) so it's reachable at a **MagicDNS name, tailnet-only**,
  with no public port. Your devices reach it; nothing else can.
- Bringing the service up + fronting it is a **service bootstrap → gated**
  ([Rule 1](../03-governance-rules.md)).

### 4. Expose a webhook publicly — only when required, only that surface

When an external service (a payment provider, a SaaS callback) *must* reach one webhook:

- publish **only that path/port** via the mesh's public mechanism (e.g. Tailscale Funnel) — a
  dedicated hostname for the webhook, **not** the admin UI,
- keep the rest private,
- **document** in the project doc exactly what's public, why, and how to unpublish (see
  [E11 · Publishing a service safely](E11-publish-a-service.md)).

Mind any platform limits (e.g. a cap on the number of public ports) — front multiple services
with per-service sidecars rather than piling onto one public port.

### 5. Track it

Registry row + `docs/<automation>/PLAN.md` ([04 · Structure](../04-structure.md)): the image +
version, data volume, what's private vs public (and why), the secrets it needs (by name), and how
to back up its data (its DB/credentials store is exactly the kind of thing
[B4 · Backup daemon](B4-nightly-backup-daemon.md) protects).

## Maintenance — the ownership half

- **Update deliberately, in a window.** Pin the image version; update on your cadence with a quick
  post-update smoke test (a workflow runs, a webhook responds). A workflow runtime is *stateful* —
  back up its data before a major version bump.
- **Back up its data** ([B4](B4-nightly-backup-daemon.md)) — the workflows + credential store are
  irreplaceable; a container is not "backed up" by virtue of being reproducible.
- **Re-check exposure periodically** — confirm the admin UI is still **private** and only the
  intended webhook is public. Exposure creep is the risk with self-hosted services.
- **Rotate secrets** in the vault, not the compose file.

## What you learn from this example

- **Private-by-default, public-only-deliberately** — expose the one surface that needs it, keep
  the rest on the mesh, and write down what's exposed.
- A self-hosted service is **install + expose + persist + secure + maintain**, all one tracked
  project — the container is the easy part.
- **Stateful services need real backups** and **windowed, version-pinned updates** — reproducible
  ≠ backed up.

## Adapt it

In **your** repo: pick the runtime, write the tracked compose/unit with vault-referenced secrets,
bring it up private over the mesh (gated), publish only the webhook you need (documented), track
it, and wire its data into your backup routine.

**Related:** [08 · Networking](../08-networking.md) · [C7 · Container runtime + stack](C7-container-runtime-stack.md)
· [E11 · Publishing a service safely](E11-publish-a-service.md) ·
[B4 · Nightly backup daemon](B4-nightly-backup-daemon.md) · [catalog](../16-example-projects.md).
