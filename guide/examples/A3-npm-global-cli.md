# A3 · An npm-global CLI (avoiding the self-update trap)

**Section A — install-and-keep-current tools.** Back to the [catalog](../17-example-projects.md).

**What this shows:** a CLI whose *own* updater targets **one** package manager, so installing it a
*second* way (or letting it self-update alongside a package-manager copy) spawns a **duplicate**
that fights over the binary on `PATH`. The lesson: **one install method per tool, chosen
deliberately** — and how the operator owns both the install and the "don't let it drift into two"
maintenance.

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

---

## The scenario

You want a developer CLI that's distributed as an **npm package** and **self-updates via npm**
(an AI coding CLI, a repo-packer, a codegen tool — many are shaped this way). You *also* have a
system package manager (Homebrew/apt) that offers the same tool. So which do you use?

The trap: if you install it via the **system package manager** *and* the tool later
**self-updates via npm**, you now have **two copies** — one the package manager tracks, one npm
installed — and whichever appears first on `PATH` wins. Symptoms:

- the tool "won't update" (you update the package-manager copy; the npm copy on `PATH` is stale),
  **or**
- it "updates but reverts" (the npm self-update writes a copy the package-manager symlink then
  shadows), **or**
- endless "update available" prompts because the running copy never matches the updated one.

## Why do it "the framework way"

Because the fix is a *decision recorded once*, not a thing you re-diagnose every few weeks. The
operator's job is to **pick the single install method the tool actually maintains itself with**,
remove the other, make `PATH` unambiguous, and write down why — so a future session (or a new
node) doesn't reintroduce the duplicate.

**Rule of thumb:** install a tool the way it *updates itself*. If it self-updates via npm, npm is
the sole install method; don't also add the system-package-manager copy.

## The shape

### 1. Diagnose which copy is which

```sh
# where are the copies, and which wins?
which -a <tool>                 # every match on PATH, in precedence order
<tool> --version                # the one that actually runs
npm ls -g <tool> 2>/dev/null    # the npm-global copy + version
<pkgmgr> list <tool> 2>/dev/null # the system-package-manager copy + version
readlink "$(command -v <tool>)"  # does the winning PATH entry point at npm or the pkg manager?
```

You're looking for **two installs at different versions**, with the *wrong* (older, or
pkg-manager) one shadowing the one the tool self-maintains.

### 2. Consolidate to the self-update method

- **Remove the copy the tool does NOT maintain itself.** If it self-updates via npm, remove the
  system-package-manager copy (`<pkgmgr> uninstall <tool>`), keep npm as the sole install.
- **Reinstall/refresh the surviving one** to the current version
  (`npm install -g <tool>@latest`).
- **Verify one copy:** `which -a <tool>` shows a single path, and it points into the npm install.

### 3. Make `PATH` unambiguous (the recurring root cause)

Duplicate-`PATH` confusion is often *why* the wrong copy wins. In your shell config
([05 · chezmoi](../05-chezmoi.md)-managed), keep `PATH` entries unique. In zsh the one-liner is:

```sh
typeset -U path PATH    # keep PATH entries unique, first-occurrence wins
```

so a directory added twice collapses to one entry and `which <tool>` is deterministic. (This is a
general fix that pays off well beyond this one tool.)

### 4. Track the decision

Record it in the tool's project doc ([04 · Structure](../04-structure.md)): *"install method =
npm-global (the tool self-updates via npm); the pkg-manager copy is deliberately NOT used —
adding it spawns a duplicate."* This one sentence prevents the whole class of recurrence.

## Maintenance — the ownership half

- **Ride the tool's own update path.** For an npm-self-updating tool, updates come via
  `npm install -g <tool>@latest` (or its own `<tool> update`) — folded into your
  [fleet-update pass](E10-fleet-update-pass.md). Don't *also* bump a pkg-manager copy; there
  shouldn't be one.
- **Leave true self-updaters entirely alone.** Some tools ship a fully self-contained updater
  (an app that updates in place). For those, *neither* npm nor the package manager should manage
  them — let the app update itself, and don't create a second copy.
- **Symmetry across nodes** ([Rule](../03-governance-rules.md)): the same single install method
  on every node that has the tool.

## What you learn from this example

- **Install a tool the way it updates itself** — mismatched install/update paths are the root of
  "won't update / reverts / nags."
- **`PATH` de-duplication** (`typeset -U path PATH`) removes the "which copy runs?" ambiguity that
  makes the duplicate bite.
- The decision is **recorded once** as a tracked fact, so it doesn't recur on the next node or in
  the next session — that's the maintenance discipline, not just a fix.

## Adapt it

In **your** repo: for each self-updating CLI, confirm its single install method, remove any
second copy, add the `typeset -U path PATH` line to your managed shell config, and write the
"install method = X, don't add Y" note in its project doc.

**Related:** [07 · Tools & requirements](../07-tools-requirements.md) ·
[A1 · Diagram/doc toolchain](A1-diagram-doc-toolchain.md) ·
[E10 · Fleet-update pass](E10-fleet-update-pass.md) · [catalog](../17-example-projects.md).
