# 08 · Networking — private mesh + SSH with keys

Once you have more than one node, they need to reach each other — securely, without exposing
anything to the public internet. The framework's substrate is a **private mesh network**
(Tailscale) plus **key-only SSH**. This section covers the model and the access patterns;
per-platform setup (installing the SSH server, key locations, firewall specifics) is in the
spokes.

Single-node users can skip this until they add a second node.

## The goal: nodes reachable, internet not

Two properties you want simultaneously:

1. **Any node can reach any other node** it's supposed to — for config pull, remote admin,
   inventory, and service-to-service traffic — from anywhere (home, traveling, another
   network).
2. **Nothing is exposed to the public internet** unless you explicitly choose to publish it.
   No open ports on your router, no services on `0.0.0.0`.

A private mesh gives you both: nodes get stable private addresses that work across networks,
and traffic is encrypted end-to-end, but none of it is reachable from the open internet.

## The private mesh (Tailscale)

**Tailscale** (a WireGuard-based mesh) is the reference. What it gives the framework:

- **Stable identity per node.** Each node gets a fixed private address and a **MagicDNS name**
  that works regardless of which physical network the node is on. You reference nodes by their
  mesh name, not by a LAN IP that changes.
- **Cross-network reachability.** A `workstation` traveling on hotel Wi-Fi reaches the
  always-on `server` at home exactly as if they were side by side. No port-forwarding, no
  dynamic-DNS.
- **Private by default.** Nodes on your mesh (your "tailnet") reach each other; nothing else
  can. Encryption is end-to-end.
- **Selective publishing when you *want* it.** If a service should be reachable — privately to
  just your devices, or publicly — the mesh provides an explicit mechanism to expose that one
  service (a reverse-proxy/"serve" feature), rather than opening a port. Default is private;
  public is a deliberate, per-service act.

**The pattern:** put every node on the tailnet; reference nodes by mesh name; keep everything
private unless a specific project needs one service published, and then publish *only* that
service, *only* as widely as required.

Alternatives (a self-hosted WireGuard mesh, a VPN, or plain LAN if all nodes are always on the
same network) can fill this slot — the *model* (private mesh, stable names, private-by-default)
is what the framework depends on, not the specific product.

## SSH with keys — the access layer

On top of the mesh, **SSH is how the operator administers remote nodes** and how config is
pulled. The framework's rules for SSH are strict and simple:

- **Keys only. No passwords.** Password auth is disabled on every node that accepts SSH. A
  stolen password is a breach; a key that never leaves its machine is not.
- **One key per source identity**, with a clear name, so you know which machine/role a key
  authorizes.
- **Least privilege.** A node accepts inbound SSH only from the identities that genuinely need
  it, and only in the direction needed (below).

### Directionality: one-way vs mutual

Not every node needs to SSH into every other. Model the access as a **directed graph** and
grant only the edges you use:

- **One-way** — e.g. your `workstation` administers the `server`, but the `server` never needs
  to log into the `workstation`. Grant `workstation → server` only. This is the common case and
  the safest: the always-on node (a bigger target) can't reach *into* your personal machine.
- **Mutual** — two nodes that genuinely call each other (e.g. they run peers of a coordinated
  service). Grant both directions, deliberately.
- **None** — nodes that never interact directly need no SSH edge at all, even though they share
  the mesh.

Write the intended graph down (a small table in your networking project doc: *from → to, why*).
An SSH edge that exists but isn't in the table is a candidate to remove — unused access is just
risk.

### Making SSH ergonomic (and correct)

- **Host aliases.** Configure short aliases (in your SSH config) so the operator and you use
  `ssh <role-or-name>` instead of raw addresses — and so the mesh name, key, and user are
  pinned in one place. (The SSH config itself is a candidate for config-management, minus any
  sensitive bits.)
- **Known-hosts hygiene.** Pin host keys so a changed host key is a *warning*, not a silent
  accept.
- **The private repo never holds a private key.** SSH *config* (aliases, which key to use) can
  be managed; the **private keys themselves** are secrets ([06 · Secrets](06-secrets.md)) —
  generated per machine, never committed, never synced through the repo.

## How the operator uses this

With the mesh + SSH in place, the operator (under the governance rules) can:

- **Inventory remote nodes** — run read-only commands over SSH to see a `server`'s state
  (what's installed, running, mounted). Reads are always free ([Rule 10](03-governance-rules.md)).
- **Pull + apply config remotely** — bring a node's prod source up to date and apply
  ([05 · chezmoi](05-chezmoi.md)) — with the **apply still gated** ([Rule 1](03-governance-rules.md)),
  same as local.
- **Never handle passwords.** Because auth is key-only and non-interactive, the operator never
  sees, types, or stores a password. Anything that *would* require an interactive password
  (a `sudo` prompt, an unlock) is handed back to you — the operator doesn't attempt it.

## Publishing a service (when you mean to)

Sometimes a node's service *should* be reachable — a dashboard on your phone, a webhook a
third party calls. The framework's stance:

- **Private first.** Expose it to just your own devices over the mesh (a "serve"-style private
  proxy) before considering anything public.
- **Public is explicit and minimal.** If a service must face the internet, publish **only that
  service**, document *why* and *what's exposed*, and put it behind the mesh's controlled
  publishing mechanism — never by opening a router port to your LAN.
- **Treat every published surface as a project** with its own doc: what's exposed, to whom, and
  how to unpublish. Exposure you can't describe is exposure you can't secure.

Next: [09 · Permissions](09-permissions.md) — the CLI-level permission layer that, together
with the governance rules, bounds what the operator may do without asking.
