# 09 · Container & virtualization runtimes — where services actually run

Almost everything you run on a fleet — a metrics stack, an automation platform, a media library, a
web server — runs in a container. That makes the container runtime **substrate**, not a topic: it
sits under the rest of the guide the way the config manager and the mesh do. This section covers
choosing one, owning it, and the failure modes that are specific to it. Per-platform install
commands live in the spokes.

Single-node users need this as much as fleet operators. It is usually the second thing you install
after the config manager.

## The goal: services that are reproducible and not welded to the OS

A service installed natively spreads: a package, a config file in `/etc`, a user, a service unit, a
data directory, and a version that upgrades when the OS does. Six months later you cannot say what
it touched, and you cannot move it to another node without repeating archaeology.

A containerized service gives you three properties that matter to an operator:

- **Reproducible** — the definition is a file in your repo. The node is derived from it
  ([05 · chezmoi](05-chezmoi.md)).
- **Enumerable** — you can ask a node what it is running and get an answer, which is what makes
  monitoring possible ([17 · Monitoring](17-monitoring.md)).
- **Removable** — stopping a service leaves nothing behind except the data you deliberately kept.

That last one is why this belongs in a reliability guide rather than a tooling one. **Reversibility
is a safety property.** An operator that can undo what it did is one you can let do more.

## Choosing a runtime — the field, honestly

There is no single right answer, and the framework does not mandate one. What it asks is that you
**choose deliberately and write down why**, because the choice leaks into every example you build.

**Container runtimes**

| | |
|---|---|
| **Docker Engine** | The reference implementation of the ecosystem. Everything is tested against it. On Linux it is just a daemon; on macOS and Windows it needs a VM underneath. |
| **Docker Desktop** | Docker Engine plus a managed VM and GUI. ⚠ **Check the licence** — it is not free for larger organisations, and that is a real constraint for some readers. |
| **Podman** | Daemonless and rootless-first, with a Docker-compatible CLI. Strong on Linux; on Windows it runs over WSL2. `podman-compose` is not quite `docker compose`. |
| **OrbStack** | A fast, low-overhead macOS runtime with good battery and filesystem behaviour. macOS only, and a commercial product with a free tier. |
| **Colima / Lima** | Open-source Linux VMs for macOS that host Docker or containerd. More assembly, no licence question. |
| **Rancher Desktop** | Open-source desktop runtime with Kubernetes built in, if you want that. |
| **containerd + nerdctl** | The layer underneath most of the above. Pick it when you want the minimum. |

**System containers and VMs** — for when a process container is the wrong shape:

- **LXD / Incus** — full-OS containers that behave like lightweight machines. Good when software
  expects an init system and a persistent filesystem.
- **Proxmox, libvirt/KVM, UTM, multipass** — real virtualization. You need this when you need a
  **different kernel** (running Linux workloads on a Mac beyond what the runtime's VM gives you), a
  full Windows or BSD guest, or hard isolation you can snapshot and roll back.

**The axes that actually decide it:**

1. **Licence.** The only axis that can make a choice impossible rather than inconvenient.
2. **Rootless or rootful.** Rootless is safer and changes file ownership on bind mounts in ways that
   will surprise you once, memorably.
3. **Compose compatibility.** If your definitions are compose files — and in this framework they
   are, because they are tracked config — then how faithfully a runtime implements compose is not a
   detail.
4. **Overhead.** On a laptop this is battery and fan noise. On an always-on node it is the power
   bill.
5. **Platform reach.** A fleet with mixed operating systems will use **different runtimes per
   node**, and that is fine — it is the same "roles, not hostnames" idea from
   [16 · Multi-node](16-multinode.md). The definitions stay portable; the runtime under them does
   not have to be identical.

**Adapt, don't adopt.** If you already run something that works, keep it. The rest of this guide
assumes *a* container runtime with compose-style definitions, not a specific vendor.

## Owning it — the runtime is itself a stateful dependency

The most common mistake is treating the runtime as infrastructure that simply exists. It is a
service you own, and the governance rules apply to it.

**It holds state you cannot rebuild.** Named volumes, networks, and the images you have pinned are
not in your repo. A runtime reinstall that drops volumes takes your databases with it. Before you
upgrade the runtime, the same question applies as to any other stateful service: *what does this
hold that I cannot reproduce from the repo?*

**Pin images. Never `latest` for anything holding data.** A floating tag turns an unrelated restart
into an unannounced migration, and migrations are frequently one-way. Pin the tag, and let the
update digest tell you when a new one exists ([17 · Monitoring](17-monitoring.md)).

⚠ **A compose file is config; the data under it is not.** Track the definition, ignore the data
directory, and know which is which before you run a destructive command. The operator should be able
to recreate any service from the repo and get the same service — with its data still attached,
because the data was never in the repo to begin with.

⚠ **Recreating is not restarting, and the difference bites sidecars.** When a compose service is
recreated it becomes a **new container** with a new id. Anything that attached itself to the old
container — a network sidecar, a proxy sharing its namespace, a log shipper following it — is now
attached to something that no longer exists. It will usually keep running and silently do nothing.
**If a service is recreated, recreate what was attached to it**; do not restart it and assume the
attachment survived.

⚠ **Don't let the runtime update itself under you.** Desktop runtimes in particular like to
auto-update. An update that changes the embedded VM, the network stack, or compose semantics will
break running services at a moment you did not choose. Turn it off, and let the noticing be
automated instead ([17 · Monitoring](17-monitoring.md)).

## Enumerate services, not containers

When you ask a node what it is running, ask at the level you care about.

A container list answers *"what processes are up"*. It does not answer *"is the thing I depend on
working"* — a container can be running while the service inside it is refusing connections, and a
service can be legitimately absent because it is on-demand rather than always-on. Health checks
built on container counts produce both false alarms and false silence.

**Define the list of services you expect, per role, in the repo.** Check each one by function:
does it answer, with the right status, in a reasonable time. That list is also what makes an
unregistered service *visible* rather than merely absent — the same reconciliation idea the update
checker uses.

## When a container is the wrong answer

Containers are the default here, not a religion. Reach for something else when:

- **The software expects to be a machine** — a full init system, multiple daemons, a package
  manager it manages itself. A system container (LXD/Incus) fits better than contorting a process
  container.
- **You need a different kernel or OS.** Testing a Linux-only tool on a Mac beyond what the
  runtime's VM offers, or running a Windows-only service, is virtualization work.
- **You need snapshot-and-rollback of the whole environment.** VM snapshots are a coarse but
  extremely effective undo, and there is no container equivalent for "put the entire machine back
  the way it was an hour ago".
- **It is a desktop application.** Not everything should be a service.

## What to write down

The framework's bias is that decisions live in the repo, not in memory. For this one, record:

- which runtime each **role** uses, and the reason — licence, platform, or overhead
- the compose definitions, tracked
- what is **not** tracked: data directories, named volumes, anything holding non-reproducible state
- the pinned image tags, so a diff shows you an upgrade rather than hiding it
- which services are expected on which role, for the health check to reconcile against

That is enough for an operator to bring a node back from nothing but the repo, and enough for you to
answer "what is this node running and why" six months later without archaeology.

Next: [10 · Permissions](10-permissions.md) — the CLI-level permission layer that, with the
governance rules, bounds what the operator may do without asking.
