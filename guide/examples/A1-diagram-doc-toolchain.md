# A1 · A diagram/doc toolchain

**Section A — install-and-keep-current tools.** Back to the [catalog](../16-example-projects.md).

**What this shows:** the core **installer pattern** — the operator installs a small CLI toolchain
symmetrically across nodes via an *idempotent, role-aware* script the config manager runs on
apply, tracks it as a project, and keeps it current with the deliberate update pass. This is the
cleanest, lowest-risk example of "the SRE owns install *and* maintenance," so it's a good first
one to read.

> Generic pattern, no personal config. `<placeholders>` are yours to fill in your own repo.

---

## The scenario

You want a set of **diagram/doc generation tools** available on every node that produces docs —
e.g. a graph renderer, a diagram-as-code CLI, and a document converter. Concretely, tools of the
shape:

- a graph renderer (DOT-language → images),
- a diagram-as-code CLI (text → diagrams),
- a document converter (markdown → PDF/HTML, using a lightweight PDF engine so you avoid a
  multi-GB LaTeX install).

The goal: **present + current on every doc-producing node, installed by config not by hand, and
updated on your schedule — never silently.**

## Why do it "the framework way"

You *could* just `brew install`/`apt install` them on each machine. But then:

- a new node doesn't get them until you remember to,
- versions drift between machines (a subtle source of "works on one, breaks on another"),
- there's no record that they're part of your setup.

Instead, you **declare** them in a tracked installer the config manager runs, so any node
converges to "correctly equipped," symmetrically ([Rule: default to symmetry](../03-governance-rules.md)),
and the install is *visible* in the repo.

## The shape

### 1. A role-aware, idempotent installer

Add an installer to your repo that the config manager runs on apply (a `run_onchange`-style
script — see the [installer pattern](../07-tools-requirements.md) and
[`skeleton/installers/install-tooling.sh.template`](../../skeleton/installers/install-tooling.sh.template)).
Key properties (all from [07](../07-tools-requirements.md)):

- **Idempotent** — checks whether each tool is already present at an acceptable version; does
  nothing if so. Convergence, not blind reinstall.
- **Absolute-path safe** — call the package manager by absolute path, because the config
  manager's apply context has a **minimal `PATH`** that may not include it (a bare command name
  silently fails there — see the [macOS spoke](../../platforms/macos.md) note on this exact trap).
- **Role-aware** — install on the roles that need it (e.g. any node that generates docs); skip
  elsewhere.
- **Loud on failure** — if an install fails, say so and where it logged; never leave a node
  half-equipped silently.

Sketch (platform-agnostic intent — the per-OS package manager comes from your
[platform spoke](../../platforms/macos.md)):

```sh
# for each tool in <graph-renderer> <diagram-cli> <doc-converter> <pdf-engine>:
#   if present at acceptable version -> report + skip
#   else -> install via the platform package manager (ABSOLUTE path)
#   on failure -> log loudly, non-zero exit
# guard by role: only on nodes whose role produces docs
```

### 2. Track it as a project

Add a row to your registry ([04 · Structure](../04-structure.md)) — `docs/<toolchain>/PLAN.md` —
recording what's installed, on which roles, the versions, and the "as of" date. Now it's part of
your setup, not a forgotten one-off. Install is a first-class, reviewable change.

### 3. Bring it up under governance

- The installer lands via the config manager: **pull → back up → diff → (approval) apply →
  verify** ([05 · chezmoi](../05-chezmoi.md)). The **apply is gated** ([03 · Governance](../03-governance-rules.md)).
- Verify: the tools resolve on each intended node (at their absolute paths, given the minimal-PATH
  gotcha), and produce output (`<graph-renderer> --version`, render a trivial diagram).

## Maintenance — the half most setups forget

This is what makes it an *ownership* example, not just an install:

- **Update deliberately, not on every apply.** These are leaf tools with no service depending on
  them, so they're low-risk to bump — but you still update on **your** cadence (a periodic pass,
  see [E10 · Fleet-update pass](E10-fleet-update-pass.md)), not continuously. A working node's
  tooling changes when *you* decide it does.
- **Keep the nodes symmetric.** When you update on one doc-producing node, update the others to
  the same versions ([Rule: symmetry](../03-governance-rules.md)); note any deliberate divergence.
- **Leave self-updaters alone.** If one of these tools ships its own updater, don't *also* manage
  it via the package manager — pick one path per tool (the general form of the trap that
  [A3 · npm-global CLI](A3-npm-global-cli.md) covers in depth).

## What you learn from this example

- The **idempotent, role-aware installer** is the atom of "the operator owns install."
- The **absolute-path / minimal-PATH gotcha** is real and bites silently — it recurs across the
  framework (installers, scheduled jobs, launchd/systemd units).
- **Install is a tracked project + a gated apply**, and **maintenance is a deliberate pass** —
  together that's *ownership*, not a one-time setup.

## Adapt it

In **your** repo: pick your actual tools, drop the installer in (from the skeleton template),
fill the package-manager block from your platform spoke, add the registry row, and run it through
the gated apply. Then fold its updates into your periodic maintenance pass.

**Related:** [07 · Tools & requirements](../07-tools-requirements.md) ·
[05 · chezmoi](../05-chezmoi.md) · [A3 · npm-global CLI](A3-npm-global-cli.md) ·
[E10 · Fleet-update pass](E10-fleet-update-pass.md) · [catalog](../16-example-projects.md).
