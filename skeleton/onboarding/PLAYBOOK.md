# PLAYBOOK — the operator's entrypoint   ·   STARTER (customize this)

**Start here to *do* or *fix* something.** A thin hub organized in **layers** — hardware → foundation
→ networking → servers → storage → monitoring → applications — plus a cross-cutting **troubleshooting
index** and **external references**. Keep it a **map, not a copy**: every entry links to the doc that
owns the content, so nothing here goes stale.

> **How to adopt.** Copy this to your repo root as `PLAYBOOK.md`. Keep the layered sections; delete the
> ones you don't have yet and add rows as you build. **Index *every* project you own** — the playbook
> is meant to be complete, not a running log. The value compounds in three tables: the layer index,
> the **troubleshooting index**, and **external references**. Resist pasting procedures here — link out.

The registry says *what state a thing is in*; this playbook says *how to do or fix it*; a dashboard
*shows it now*; the guide says *why*. Keep them distinct.

## Which doc for what

| I want to… | Go to |
|---|---|
| **Do an install / follow a procedure** | the project's **runbook** → `docs/<project>/…` |
| **Fix a known problem** | the **Troubleshooting index** below |
| **Look up an external tool** | **External references** below |
| Know a project's **status** | your **registry** (`PROJECTS.md`) |
| See **live state** | your **dashboard**, if you built one |
| Understand a **concept** | the framework **guide** |
| Know the **behavioral rules** | your operator-rules doc (`CLAUDE.md` / `AGENTS.md`) |

---

## 1 · Hardware
The physical inventory — one row per machine (CPU/GPU, RAM, storage), plus the facts you reach for
(UPS wiring, drives, expansion). Full specs can live on a dashboard; keep the essentials here.

## 2 · Foundation (cross-cutting)
The layers everything rides on: **config management**, **container runtime(s)**, the **dashboard**,
**fleet updates**, and your **framework / dev tooling**. These aren't features — they're the ground.

## 3 · Networking & mesh
The private **mesh** (e.g. Tailscale) and per-machine networking. Most cross-cutting gotchas surface
here, so it pairs tightly with the Troubleshooting index.

## 4 · Servers & hosts
Machine-centric: each host's **role** and **what runs where**, linking to the layer entries. This is
the "where does X live" view that the layer sections don't give you.

## 5 · Storage & media
Shared storage, mounts, and media stores.

## 6 · Monitoring & observability
Metrics/health emitters and where they're graphed; your status dashboard as the at-a-glance view.

## 7 · Applications & application support
The actual services, grouped (media, automation, self-host platform, AI, secrets, tooling). Each links
to its runbook.

*(Add or drop layers to fit your system — the point is purposeful sections, not one flat list.)*

---

## Troubleshooting index — "seen this symptom?"
The highest-value section: a central "have I hit this before?" table. Seed it from the guide's
documented **traps**, then add a row every time you solve something non-obvious.

| Symptom | Cause | Fix → doc |
|---|---|---|
| A private mesh service fails from a **roaming** device but works on the LAN / via exit node | Resolves to the provider's **public ingress**, not the mesh DNS | Force clients onto mesh DNS ("override local DNS") → guide § *Publishing a service* |
| Local NAS/LAN traffic **crawls** with a subnet router up | Traffic **hairpins** through the router | Stop on-LAN nodes accepting the route → guide § *Subnet routes and exit nodes* |
| `<your symptom>` | `<cause>` | `<fix → doc/url>` |

---

## External references — vendor docs (out-of-repo)
The upstream docs for every tool you run, so the operator links out to the current source.

| Tool | Docs |
|---|---|
| Mesh VPN (e.g. Tailscale) | `<url>` |
| Config management (e.g. chezmoi) | `<url>` |
| Metrics / dashboards | `<url>` |
| `<tool>` | `<url>` |

---

## Conventions
- **Behavioral rules** → your operator-rules doc.
- **Runbook format** (phases → steps → evidence → gate/rollback) → your structure/dashboard doc.
- **Keep this a thin, layered hub** — add links in the right layer, never a second copy of the runbooks.
