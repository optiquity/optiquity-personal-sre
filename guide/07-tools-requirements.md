# 07 · Tools & requirements

A node needs certain tools present to do its job. This section covers **which** tools the
framework requires (hard vs optional), and the **pattern** for ensuring they're installed —
idempotently, by role — so a fresh node converges to "correctly equipped" without manual
babysitting. Per-platform install commands live in the spokes; the model is here.

## Hard requirements (the core)

For a **single node** to run the framework at all:

| Requirement | Role in the framework | Why it's hard |
|---|---|---|
| **git + a git host account** | Source of truth; the whole model is repo-centric. | Everything derives from version control. |
| **A config manager** (chezmoi) | Renders the repo onto the node ([05](05-chezmoi.md)). | Without it, "machines are derived" isn't real. |
| **An AI coding CLI** (Claude Code = reference) | The operator ([03](03-governance-rules.md), [11](11-agents-skills.md)). | It's who does the work under the rules. |
| **A secret store** (OS keychain / vault) | Runtime credentials, zero-in-git ([06](06-secrets.md)). | The alternative is secrets in git — forbidden. |

That's the whole floor: **four things on one machine.** You can run a meaningful personal-SRE
setup with nothing more.

## Hard-for-multi-node

The moment you have **more than one node** and want them to operate together, two more become
hard:

| Requirement | Role | Notes |
|---|---|---|
| **A private network** (Tailscale) | Nodes reach each other without public exposure. | Covered fully in [08 · Networking](08-networking.md). |
| **SSH with keys** | Remote administration, config pull, inventory. | Key-only, no passwords ([08 · Networking](08-networking.md)). |

If you're single-node, these are optional; add them when you grow. This section is about the
*tooling/installer* layer; the network substrate is its sibling, [08 · Networking](08-networking.md).

## Optional / enhancing tools

Add these when a project needs them — never preemptively:

- **A container runtime** (OrbStack / Docker / Podman) — for self-hosted services.
- **An automation runtime** (n8n or similar) — for workflows/webhooks.
- **Browser automation** (a Playwright-class CLI) — for tasks that need a real browser.
- **Doc/diagram tooling** (pandoc, graphviz, d2, …) — for generating docs and diagrams.
- **The multi-node coordination layer** — session transfer, a fleet dashboard.

The framework's stance: **don't install or update tools speculatively.** A node carries the
tools its roles' projects require, and no more. Fewer tools = less surface, less drift, less to
keep current.

## The requirements matrix

Consult this when planning an adoption:

| Capability | Single node | Multi-node | Hard/Optional |
|---|---|---|---|
| git + host | ✅ | ✅ | **Hard** |
| Config manager | ✅ | ✅ | **Hard** |
| AI CLI (operator) | ✅ | ✅ | **Hard** |
| Secret store | ✅ | ✅ | **Hard** |
| Private network | — | ✅ | Hard (multi-node) |
| SSH keys | — | ✅ | Hard (multi-node) |
| Container runtime | optional | optional | Optional |
| Automation runtime | optional | optional | Optional |
| Coordination layer | — | optional | Optional |

## The installer pattern

Tools shouldn't be installed by hand-typed one-offs you forget — they should be **declared**,
so any node converges to having them. The framework's pattern is an **idempotent, role-aware
install script**, run by the config manager on apply ([05 · chezmoi](05-chezmoi.md)):

**Properties a good installer has:**

1. **Idempotent.** Running it twice is safe: it checks whether the tool is present at the right
   version and does nothing if so. Convergence, not blind reinstall.
2. **Role-aware.** It installs what *this node's role* needs. A `server` installer might set a
   service to start at boot; the same tool on a `workstation` installs on-demand.
3. **Absolute-path safe.** When run by the config manager's background/apply context, the
   environment is minimal — a bare `PATH` may not include your package manager. Reference tools
   by absolute path so the installer works in that stripped context, not just in your
   interactive shell.
4. **Loud on failure.** If an install fails, it says so (and where it logged), rather than
   failing silently and leaving a node half-equipped.
5. **Declarative about *what*, imperative about *how*.** The script names the desired
   tools/versions; the per-platform *how* (which package manager) is the platform's business
   — factor it so the same intent works across spokes.

**Sketch (platform-agnostic intent):**

```sh
# for each required tool:
#   if present at acceptable version -> report + skip
#   else -> install via the platform's package manager (absolute path)
#   on failure -> log loudly, non-zero exit
# role-conditional extras (e.g. enable-at-boot) guarded by the role variable
```

The skeleton ships a **generic installer template** (`skeleton/installers/`) embodying these
properties; you fill in your tool list and the platform spoke supplies the package-manager
specifics.

## Keeping tools current (without churn)

Updates are a project, not a reflex:

- **Don't auto-update** everything on every apply — that's how a working node breaks
  unexpectedly. Update **deliberately**, when you choose.
- Some tools **self-update** (an app with its own updater); leave those alone — managing them
  via the package manager as well causes conflicts.
- Track what's installed where, and update on a **cadence you control** (e.g. a periodic pass),
  not continuously. Note anything held back and why.
- A tool the framework installed via the package manager stays on the package manager's update
  path; a tool that self-updates stays on its own. Don't mix the two for one tool.

The principle: **a node's tooling changes when you decide it does**, and every change is
visible — never a surprise from a background auto-upgrade.

**"Deliberate" is about the decision, not the discovery.** It does *not* mean the operator waits to
be asked. Under [principle 11](03-governance-rules.md), the operator is expected to bring you the
available updates, with enough detail to decide; you approve, decline, or defer. Keeping the decision
while offloading the noticing is the whole trade — the alternative makes your attention the only
thing between the fleet and years of quiet drift.

**Automate the *noticing*, not the upgrading.** The posture above only works if you actually know
what's behind — otherwise "deliberate" quietly becomes "never". The framework ships that half:
a scheduled job inventories every node by install method and **emails you a digest**, upgrading
nothing (`fleet-update-check` in [`../skeleton/monitoring/`](../skeleton/monitoring/)). Two traps
it also covers, both of which this chapter warns about but can't catch by hand:

- **"Don't mix the two for one tool"** is detectable — `fleet-install-audit` flags any command
  backed by two package managers at once (a manual shim shadowing a formula, an npm CLI vs a cask).
- **Version-pinned container images are invisible to every package manager.** Pinning is correct
  for an appliance, but nothing tells you the pin is stale — you find out from a banner inside the
  app, if ever. `fleet-container-check` asks the registry instead.

Treat those two as **examples, not the list**. Both are instances of one recurring pattern — a class
of installed thing that nothing enumerates — and it also arrives as language-version managers,
hand-placed binaries, and *entire hosts* that were marked "manual" once and never retested. Patching
it case by case never converges; the fix is to reconcile **discovery against a registry** so anything
present-but-unregistered reports itself. See
[14 · Monitoring → the enumeration blind spot](14-monitoring.md) for the mechanism and the two rules
that keep it honest.

Worked end-to-end in [E16 · Health, alerting & the update digest](examples/E16-fleet-health-and-alerting.md);
the human runbook it feeds is [E10 · A deliberate fleet-update pass](examples/E10-fleet-update-pass.md).

Next: [08 · Networking](08-networking.md) — the private-network + SSH-key substrate that lets
nodes reach each other securely.
