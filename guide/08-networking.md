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

## Subnet routes and exit nodes — reaching beyond the mesh (and two traps)

Two mesh features let a node act as a **gateway** for traffic that isn't itself on the mesh.
Both are useful; both have a trap that bites hard if you don't know it.

- **Subnet routing.** One node (the **subnet router**) advertises a whole LAN — your home
  network's CIDR — into the tailnet, so **remote** mesh devices can reach LAN-only gear that
  *can't* run the mesh itself: a printer, a smart-home hub, an appliance. Without it, a traveling
  `workstation` reaches your mesh nodes but not the printer next to your `server`.
- **Exit node.** A node advertises a default route (all traffic), so other devices can send their
  **internet** traffic out through it — appearing at that node's location (useful on untrusted
  Wi-Fi, or to reach the internet as if from home).

Advertising either is a **material action** ([Rule 1](03-governance-rules.md)), and the routes
must be **approved** in the mesh's admin console before they carry traffic. Keep the role on a
**dedicated, capable, always-on** node — see the worked
[E12 · dedicated mesh gateway](examples/E12-dedicated-mesh-gateway.md) — not bolted onto a busy
multi-duty box, for the reason the first trap makes clear.

### Trap 1 — the subnet-route hairpin (the expensive one)

If the subnet router advertises **its own LAN**, and another always-on node that is **physically
on that same LAN** *accepts* that route, that node will send **local** traffic to its on-LAN
neighbors **through the mesh tunnel** — encrypting it, shipping it to the router node and back —
instead of straight across the switch. On capable hardware you might not notice; on a modest or
busy box the crypto pegs a core and throughput **collapses**: a fast local transfer can drop to a
**crawl**, with the router node's mesh daemon pinned near a full core for traffic that never
needed to leave the LAN.

**The rule:** a node that is **always on its home LAN** does **not** need — and must **not** use
— the tailnet route for that LAN. Set **accept-routes off** on such nodes; they reach the LAN
directly. Accept-routes stays **on** only for devices that are genuinely **remote** and need the
router to reach LAN-only gear (a **roaming** laptop while traveling). This is the mesh analog of
the SSH access-edge graph: use the route only where it's actually needed.

*(Symptom to recognize: a "network is slow" that's really a local transfer or mount silently
routing over the tunnel — check whether the connection's **local** address is the node's **mesh**
address instead of its LAN address. If so, it's hairpinning.)*

### Trap 2 — exit-node throughput is bounded, and must go *direct*

Routing through an exit node has hard ceilings that are physics, not misconfiguration — worth
knowing before you conclude "the node is too slow":

- **Your download through the exit node ≈ the exit node's *upload* bandwidth.** The exit node
  downloads on your behalf, then **uploads** it all back to you — so *its* upstream is your cap.
  It will never match a direct connection's raw speed.
- **The connection must be *direct*, not relayed.** A mesh falls back to a bandwidth-limited
  **relay** when it can't punch a direct peer-to-peer path, and relayed throughput is badly
  throttled. The path **upgrades** to direct a short while after connecting, so a speed test run
  *immediately* can catch it still relayed. Check the mesh status for `direct` vs `relay` first.
- **Carrier-grade NAT (cellular) is usually bypassed via IPv6.** Phones on cell sit behind CGNAT
  that defeats direct IPv4 traversal — but if the exit node has a **public IPv6** address, the
  direct path forms over IPv6 automatically. You don't toggle this; the mesh picks it.
- **Throughput varies by the *target's* distance.** You now route via the exit node's location,
  so per-connection speed follows the round-trip to each target (bandwidth-delay product) — a
  well-connected target is fast, a distant one much slower. Don't judge an exit node by one far
  speed-test server.
- **The node usually isn't the bottleneck.** Diagnose by **isolating the layer**: measure the
  node's own internet speed, watch its **per-core** CPU during a transfer (a single pegged core =
  crypto-bound; low CPU = it's the path/RTT), and check direct-vs-relay. More often the limit is
  your upstream or the target RTT, not the box.

## Slow work: isolate the layer before you tune anything

The bullet above generalises past exit nodes. When a long job runs slower than you expect, the
instinct is to tune the machine you're sitting on — it's the one you can see, and its idle CPU
looks like wasted capacity. That instinct is usually wrong, and acting on it costs restarts and
downtime for no gain.

There are at least **three** layers, and a slow job feels identical from the console whichever one
is binding:

| Layer | How to measure it | What the answer means |
|---|---|---|
| **Local CPU** | per-**process** CPU, not system total | a worker pegged near 100% of a core is compute-bound and single-threaded — concurrency helps |
| **The link** | interface bytes/sec vs the negotiated rate | near the ceiling = bandwidth-bound; well under = look elsewhere |
| **Remote storage** | on the *server*: I/O wait %, read latency, load split | high wait + high latency = the store is the limit, and **concurrency makes it worse** |

That last row is the one people skip, because it means logging into the other machine.

**A worker at partial CPU is waiting — the whole question is what for.** A transcoder pinned at
~40% of one core is not "using 40% of the CPU"; it is idle 60% of the time waiting on input.
Low CPU alone doesn't tell you whether that's link latency, remote disk, or a lock. Measure each.

A real case: a multi-week analysis job, client at **3.6% of 14 cores**, link at **32% of gigabit**,
single-stream reads at **36 MB/s**. Everything visible locally screamed "add concurrency" — three
separate times. Then the NAS was checked: **42% I/O wait, 278 ms average read latency**, load
almost entirely I/O rather than CPU. The array was already saturated. Raising the client's job
count would have put six concurrent readers on spinning disks and multiplied random seeks —
*reducing* throughput, on hardware that had failed this exact way before.

**On rotational storage, concurrency is not free.** More readers means more seeking, and past a
low threshold aggregate throughput falls rather than rises. The client's idle CPU is not headroom
when the work is I/O-bound on something else entirely.

Two habits that make this diagnosis honest:

- **Count every stage of the pipeline.** Work often flows through several processes — fetch, decode,
  analyse. If your process counter matches only one stage's name, you'll conclude the wrong thing
  about concurrency and never see the stage that's actually slow. Enumerate with `ps` and read what
  is really running before trusting a `pgrep` pattern.
- **Distrust rate estimates from short windows.** Throughput on heterogeneous work swings with the
  size of each item. Successive five-minute samples can yield wildly different projections that are
  each internally consistent and all wrong. Sample across a long window, say the range rather than a
  point estimate, and don't re-quote a new ETA with confidence every time the number moves.

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

### Trap — a *private* service that answers on the *public* door

Mesh publishing tools (Tailscale's `serve`/`funnel`, and equivalents) often give a node's service a
**mesh DNS name** that *also* carries a **public DNS record** pointing at the provider's public
ingress — so the same name resolves two ways, and which one a client gets decides everything:

- A client using the **mesh's DNS** resolves the name to the node's **mesh IP** → the **private**
  proxy answers. ✅
- A client that falls back to **public DNS** (a phone off the mesh's DNS path; the mesh not
  overriding the system resolver) resolves it to the **public ingress** → and if the service is
  private, the ingress **rejects** the connection. ❌

This is maddening because it *looks* like a transport/TLS fault — the connection reaches the node
and dies mid-handshake — while the mesh, the DNS name, and the certificate are all fine. It works
from on-mesh devices and breaks from a roaming client, so it points the finger at the network when
the real cause is **name resolution**. (Reproduce it and you'll chase MTU, relays, and IPv6 for
hours; the tell is in the *service's own log*, which will say it rejected an unconfigured public
ingress connection.)

**Guardrails:**
- **Make mesh clients always use the mesh's DNS.** Enable the mesh's *"override local DNS"* option so
  every device resolves the mesh domain through the mesh resolver (→ mesh IPs), not the public
  record. This is the single fix for "works via the exit node / on the LAN, fails roaming."
- **Never enable public exposure on a private service, even briefly to test.** Many providers publish
  the public DNS record the instant you flip it on and **leave it in place after you flip it off** —
  a stale public door that then intercepts roaming clients.
- **Scope the public-exposure *capability* narrowly** (to the one node that needs it) so private
  services can't inherit it through a shared tag/role.
- **When a published service is refused but reachable, read the service's own logs first** — the
  transport is almost always fine; the app is rejecting the connection and will tell you why.

Next: [09 · Permissions](09-permissions.md) — the CLI-level permission layer that, together
with the governance rules, bounds what the operator may do without asking.
