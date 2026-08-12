# E12 · A dedicated mesh gateway (subnet router + exit node, with an HA backup)

**Section E — fleet operations.** Back to the [catalog](../15-example-projects.md).

**What this shows:** giving the mesh's **gateway roles** — subnet router (reach LAN-only gear
remotely) and exit node (route internet traffic out through home) — a **dedicated, capable node**
of their own, instead of bolting them onto a busy multi-duty box; and keeping the previous host as
a **hot standby** for automatic failover. The clean way to own the tailnet's edge.

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

---

## The scenario

Your mesh's gateway roles are running on a node that's busy doing something else — commonly a
**storage node (NAS)** already serving files, backups, and media. It *works*, but:

- the gateway's crypto (WireGuard) **competes** with the box's real job for a weak CPU;
- the box's real job competes back, so **neither** is at its best;
- and one failure mode is nasty: if that node advertises its **own LAN** as a subnet route, other
  always-on LAN nodes that accept the route start **hairpinning local traffic through it** (see
  [08 · Networking](../08-networking.md), Trap 1) — pegging the weak CPU for traffic that never
  needed to leave the switch.

The fix: move the gateway roles onto a **small dedicated node** built for exactly this, and demote
the old host to a **backup**.

## Why do it "the framework way"

A gateway is **edge infrastructure** — every remote-access and exit-node byte flows through it.
The framework's stance: give a role that important its own **dedicated, right-sized** home, keep it
**minimal** (small attack surface, nothing else contending), and make the cutover **reversible**
(the old host stays a hot spare until the new one is proven). Routing should never compete with
storage — or anything else — for the same cores.

## The shape

### 1. Pick dedicated hardware, keep it single-purpose

A **low-power always-on node** (a small single-board computer is ideal) on **wired** Ethernet —
stable, low-jitter, right for a gateway. Flash a **minimal, headless OS**, **key-only SSH from
first boot** (seed the operator's public keys at image time — no password ever), and disable the
extras it doesn't need (a second network interface, unused services). One job, small surface. The
per-OS specifics — image config, boot-persistent tuning, single-interface discipline — live in the
[platform spoke](../../platforms/linux.md).

### 2. Bring it onto the mesh advertising both roles

Install the mesh agent, **enable IP forwarding** (required for a router/exit node), and advertise
the LAN subnet **and** the exit-node route. Then **approve** the routes in the mesh admin console —
they advertise but don't carry traffic until approved. Advertising + the bootstrap are **gated**
([Rule 1](../03-governance-rules.md)); the console approval is yours to do.

### 3. Keep the old host as a hot standby (don't just rip it out)

Leave the previous gateway **advertising the same routes**. A good mesh designates **one** node as
the **active/primary** router and the others as **standby**, failing over automatically if the
primary drops. So the new node carries the traffic (verify it's the **primary** — it should show as
*actively serving* the route), while the old one sits idle (advertising, but *not* primary) as a
**zero-cost hot spare**. You get HA for free, and a one-command rollback if the new node misbehaves.

### 4. Verify from a genuinely-remote peer, then close the hairpin

- From a **remote** device (a phone on cellular, a laptop away from home), confirm you can reach a
  LAN-only device (the printer) via the new gateway, and that the exit node works.
- Confirm the new node is **primary** and the old one is **standby** (not carrying traffic).
- **Close Trap 1:** set **accept-routes off** on every always-on node that lives **on** this LAN
  ([08 · Networking](../08-networking.md)) — they don't need the tunnel to reach their own network,
  and accepting it is what causes the hairpin. Roaming laptops keep accept-routes on.

## Maintenance — the ownership half

- **The gateway is a first-class node** — add it to your machine roster / dashboard and the
  [fleet-update pass](E10-fleet-update-pass.md). Its mesh agent is the one piece you most want
  **current** (security + throughput), so track its version deliberately.
- **Watch the update *channel*, not just "auto-update on."** On some platforms the gateway's mesh
  package comes from a vendor channel that **lags badly** — "auto-update on" can still leave you
  years behind if that channel stalls. Know where the vendor's own latest lives, and treat it as a
  **manually-tracked** update if the built-in channel doesn't advance it (the
  [E10](E10-fleet-update-pass.md) lesson generalizes).
- **Reboots interrupt the edge.** A gateway reboot (kernel/OS update) briefly drops routing — the
  standby takes over automatically, but time updates for a quiet window and re-verify the primary
  afterward.
- **Re-audit accept-routes** as you add nodes: any new always-on on-LAN node needs accept-routes
  **off**, or it reintroduces the hairpin.

## What you learn from this example

- **Dedicate the edge.** Routing/exit is important, contended, and security-sensitive — give it a
  small right-sized node, not a corner of a busy one.
- **Standby, don't discard.** Leaving the old host advertising the same routes buys automatic HA
  failover for zero effort — and a reversible cutover.
- **The hairpin is the non-obvious trap.** On-LAN nodes must *not* accept the tunnel route for
  their own LAN; that discipline keeps local traffic local.

## Adapt it

In **your** repo: track the gateway as its own project (provision → key-only SSH → mesh advertise →
approve → verify → keep old host as standby → document), fold it into the machine roster and the
update pass, and add "re-audit accept-routes" to your maintenance cadence.

**Related:** [08 · Networking](../08-networking.md) (the mesh, subnet routes/exit nodes + both
traps) · [platforms/linux](../../platforms/linux.md) (the headless-appliance *how*) ·
[E10 · Fleet-update pass](E10-fleet-update-pass.md) ·
[E11 · Publish a service](E11-publish-a-service.md) · [catalog](../15-example-projects.md).
