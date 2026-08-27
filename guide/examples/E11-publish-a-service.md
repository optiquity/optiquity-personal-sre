# E11 · Publishing a service safely

**Section E — fleet operations.** Back to the [catalog](../17-example-projects.md).

**What this shows:** taking a local service and exposing it **private-first** (mesh-only), then
**public only deliberately**, with **what's exposed and how to unpublish written down**. The
exposure discipline as its own tracked example — the standalone version of the pattern
[C6](C6-automation-runtime.md) and [C7](C7-container-runtime-stack.md) apply.

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

---

## The scenario

You have a service running on a node — a dashboard, an API, a webhook receiver, an app UI — and
you need to *reach* it from somewhere else: another of your devices, your phone while traveling, or
a third-party service that must call in. The question is **how much to expose, to whom** — and the
default answer is usually "less than you'd reflexively reach for."

## Why do it "the framework way"

Exposure is the highest-consequence, easiest-to-get-wrong part of self-hosting. The framework's
rule ([08 · Networking](../08-networking.md)): **private first; public is explicit, minimal, and
documented.** You expose the smallest surface that does the job, you say *why* and *what*, and you
know how to take it back down. "Exposure you can't describe is exposure you can't secure."

## The shape — three levels, least first

### Level 1 — Private to your own devices (the default)

Reach the service over the **private mesh** (Tailscale), at a **MagicDNS name, tailnet-only**, with
**no public port**:

- Front it with the mesh's private "serve" mechanism (e.g. Tailscale Serve).
- Your devices (and only your devices) reach it; nothing on the public internet can.
- **Never** do this by opening a router port to your LAN — that's public exposure by another name.

This covers the large majority of "I need to reach my service" cases. Bringing the service up +
serving it is a **gated bootstrap** ([Rule 1](../03-governance-rules.md)).

### Level 2 — Public, but only one surface

When an external service *must* reach the node (a payment callback, a SaaS webhook):

- publish **only that path/port** via the mesh's public mechanism (e.g. Tailscale Funnel) — a
  **dedicated hostname** for that one surface,
- keep the admin UI / everything else **private** (Level 1),
- mind platform limits (e.g. a small cap on public ports) — use **per-service sidecars** rather
  than multiplexing everything onto one public port.

### Level 3 — Public web service (rare, deliberate)

If something genuinely must be a public site, put it behind the mesh's controlled public mechanism
or a real reverse proxy, **default-deny** everything else, and treat it as a hardened surface — not
a port you casually opened.

## Document it (the part people skip)

For **every** published surface, the project doc ([04 · Structure](../04-structure.md)) records:

- **what** is exposed (which service, which path/port, which hostname),
- **to whom** (private-mesh vs public) and **why** it needs that level,
- **how to unpublish** it (the exact command / step to take it back down).

A one-line "this webhook is public via `<hostname>` for `<reason>`; unpublish with `<cmd>`" is what
makes the exposure *auditable* instead of a mystery you find later.

## Maintenance — the ownership half

- **Re-audit exposure periodically** — confirm what's public is *still* only what should be. This
  is the #1 self-hosting drift: an admin UI that quietly became reachable, a temporary public
  surface that was never taken down.
- **Prefer private; sunset public.** When a public surface's reason ends (a one-off integration
  finished), unpublish it — don't leave it up "just in case."
- **Treat every public surface as attack surface** — keep the service updated
  ([E10](E10-fleet-update-pass.md)), secrets in the vault ([06 · Secrets](../06-secrets.md)), and
  the exposure minimal.
- **Track temporary exposure with a cleanup date** ([Rule 7 — temporary divergence](../03-governance-rules.md)):
  a public surface that's meant to be temporary gets a written when-to-remove.

## What you learn from this example

- **Private-first, public-only-deliberately, documented** — the exposure discipline in three
  levels.
- **Expose the smallest surface** — one webhook public, not the whole app; the mesh handles the
  private case for almost everything.
- **Write down what's exposed + how to unpublish** — undocumented exposure is the drift that bites;
  re-auditing it is ongoing ownership.

## Adapt it

In **your** repo: for each service you need to reach, start at Level 1 (mesh-private), go public
only for the specific surface that requires it (Level 2), document what/why/how-to-unpublish, and
add "re-audit exposure" to your maintenance pass.

**Related:** [08 · Networking](../08-networking.md) · [C6 · Automation runtime](C6-automation-runtime.md)
· [C7 · Container runtime + stack](C7-container-runtime-stack.md) ·
[E10 · Fleet-update pass](E10-fleet-update-pass.md) · [catalog](../17-example-projects.md).
