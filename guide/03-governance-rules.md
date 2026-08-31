# 03 · Governance — the rules the operator works under

Handing ops work to an AI CLI is only safe if the AI is bound by **explicit, enforced rules**.
This section defines the governance model: the principles, why each exists, and how you encode
them into a rules file the operator reads at the start of every session.

This is the **judgment layer**. A separate, coarser layer — the CLI's own permission settings
— is covered in [09 · Permissions](09-permissions.md). You want both; here's the one that
carries the reasoning.

## Why rules, not just trust

An AI operator is capable and fast, which is exactly the problem: it can also delete the wrong
directory, push a secret, or bootstrap a service you didn't want — fast. The rules exist to
make the operator **pause at the boundaries that matter** and get a human decision, while
staying out of the way everywhere else.

Good governance is **asymmetric**: near-zero friction for safe, reversible work (reading,
drafting, editing a scratch file); a hard stop for anything **material** (hard to undo) or
**outward-facing** (leaves your machine). The art is drawing that line clearly enough that the
operator honors it every time.

## The core principles

These are the durable rules. Adapt the specifics to your setup, but keep the shape.

### 1. No destructive or material action without explicit approval
The operator must stop and ask before anything hard to reverse or outward-facing:
- Applying config to a machine (a `chezmoi apply`-class action)
- Deleting or overwriting files that aren't in a repo / aren't backed up
- Creating remote artifacts (repos, releases, deploys)
- Bootstrapping a background service (a scheduled job, a daemon)
- Any state-changing command on a remote node

**Why:** these are the actions whose blast radius exceeds the current file. Reversible,
local, in-repo work does **not** need this gate — that's what keeps friction low.

### 2. No version-control state changes without explicit approval
**Every** git/host mutation is gated — not just the scary ones. That includes **staging**
(`git add`), commit, push (to *any* remote), branch/tag deletion, resets, and any host-side
mutation (creating/editing/merging a PR or issue, creating a repo). Read-only queries
(`status`, `log`, `diff`, viewing a PR) are always fine.

**Why:** version control is your audit log and your source of truth. Silent commits erode
both. Gating *staging* too means the human sees exactly what will enter history before it
does. (This is stricter than most people's default — it's deliberate.)

### 3. Secrets never enter version control
`.env` files, tokens, keys, credentials, auth files — permanently excluded, enforced by the
ignore files (see [06 · Secrets](06-secrets.md)). When in doubt, don't stage it.

**Why:** a secret in git history is compromised forever, even after deletion. The only safe
secret-in-git count is zero, enforced structurally, not by memory.

### 4. Back up before you apply
Any action that overwrites live state (applying config, replacing files) is preceded by a
**timestamped backup** of what it will touch.

**Why:** "reversible" should mean *actually* reversible. A backup turns a bad apply into an
inconvenience instead of a loss.

### 5. Preview the next steps before a commit
Before asking for commit approval, the operator **lists what will happen after** the commit +
push (the next actions in the plan). If nothing follows, it says so explicitly.

**Why:** the commit is the moment momentum takes over. Seeing the queued next steps lets you
redirect *before* they run — approving the commit implicitly approves the previewed steps, so
they must be visible.

### 6. Re-read the rules before every commit
The operator re-reads this rules file at the start of any commit workflow, before requesting
approval.

**Why:** long sessions drift. A cheap re-read at the highest-stakes moment keeps the rules
live rather than a thing skimmed hours ago.

### 7. Default to symmetry across same-role nodes
Two nodes of the same role are configured the same unless there's a stated reason. Any
divergence is either **unavoidable** (a real role difference) or **temporary** (with a
scheduled cleanup written down). Anything else is drift — flag it.

**Why:** unexplained per-machine differences are how fleets rot. Making divergence *justify
itself* keeps the config legible.

### 8. Status lives in tracked docs, not in memory
The state of the system — what's done, in progress, deferred — lives in the project registry
and docs (see [04 · Structure](04-structure.md)), not in the operator's conversational memory.

**Why:** memory is lost at the end of a session; a deferred task mentioned only in chat is a
task forgotten. If it matters, it's written down.

### 9. No silent deferral
The operator only defers work when it's genuinely blocked, out of scope, or better grouped
later — and **every deferral is written into a plan doc** with a reason and a rough when.

**Why:** silent deferrals become dropped work. A visible backlog is a managed backlog.

### 10. Reads are always free
Every read-only operation — inspecting files, `git status`, config diffs, dry-runs, remote
inventory over SSH — needs no approval, anywhere.

**Why:** the gates are about *change*. Making reads frictionless is what lets the operator
investigate thoroughly before proposing an action, which makes its proposals better.

This is also what makes **unattended monitoring** safe. Scheduled health probes and update
inventories run from a timer, outside any session and outside the CLI's permission model — that
is only acceptable because they are strictly read-only and **notify-only**: they surface work and
raise alarms, they never mutate a node. Anything that would *change* a node comes back through
Rule 1 and waits for you. See [E16](examples/E16-fleet-health-and-alerting.md).

### 11. Updates are proposed by the operator, decided by you
No tool, package, image, or binary is upgraded without your explicit per-update approval. But the
operator is expected to **raise** them: staying silent about a known-available update is a failure,
not caution. You should never have to discover what is stale.

A proposal has to carry enough to decide **without further research**: what it is and where it runs ·
current → available version · why it matters (security, capability, or merely currency) · what could
break, including irreversible migrations · whether a backup exists and has been *restore-tested* ·
the rollback, and whether rollback is actually possible.

**"Available" means verified, not assumed.** A version claim comes with the source that produced it
and the *version of the tool that read it* — a stale validator or a floating tag can manufacture a
difference that doesn't exist.

**Exclusions are registered, reasoned, and visible.** Self-updating software, a deliberately frozen
version, a declined proposal, an unused tool awaiting removal — each recorded with its reason, and a
revisit date where the decision is time-bound. Excluded items are still discovered and **counted**,
because an exclusion that disappears from view is indistinguishable from a gap in coverage.

**A denial is a durable answer**, not an invitation to re-ask next week. Re-propose only when the
facts change or a revisit date arrives.

**Why:** the naive version of this rule is "don't touch anything unless asked", which is safe and
quietly corrosive — it makes *your attention* the only thing standing between the fleet and years of
accumulated drift. Moving the burden of noticing onto the operator while keeping the decision with
you gets the safety without the rot. See [14 · Monitoring](14-monitoring.md) for the detection side.

## Encoding the rules: the rules file

The operator reads a **rules file** at the repo root — for Claude Code this is `CLAUDE.md`;
Codex uses `AGENTS.md`; other CLIs have their own (see
[11 · Agents & skills](11-agents-skills.md)). The framework ships a **template** you tune:
`skeleton/CLAUDE.md.template`.

A good rules file has these parts:

1. **Identity & scope** — what this repo is, which machine-roles it governs, what's in/out of
   scope. Written in roles and placeholders, never machine names.
2. **The locked rules** — a numbered list like the principles above. Numbered so you can
   reference them ("Rule 2 applies here") and so "re-read rules 1–N before committing" is
   unambiguous.
3. **Workflow** — the standard change flow (edit in dev clone → commit → apply on nodes →
   verify), so the operator follows one repeatable path.
4. **File scope** — which paths the operator may edit freely vs. which are sensitive
   (credentials, SSH config) and off-limits without instruction.
5. **Remote-node rules** — if you have a `server`, how the operator reaches it and what still
   requires approval there (same gates as local).

Keep it **specific and locked**. Vague rules ("be careful") don't constrain; concrete ones
("no `git add` without approval") do.

## Making the rules enforceable, not aspirational

Rules the operator can quietly skip aren't rules. Reinforce them structurally:

- **Pair with CLI permissions** ([09 · Permissions](09-permissions.md)): the settings layer
  can *auto-deny* or *prompt* on categories, so even a rule-lapse hits a second wall.
- **Pair with ignore files** ([06 · Secrets](06-secrets.md)): a secret can't be committed if
  it's ignored, regardless of the operator's judgment.
- **Make approval the path of least resistance**: the operator asks because asking is the
  rule *and* because the permission layer would prompt anyway.
- **Re-read at commit time** (Rule 6): the cheapest enforcement is re-loading the rules at the
  highest-stakes moment.

The goal is **defense in depth**: judgment (these rules) + capability limits (permissions) +
structural exclusion (ignore files). No single layer has to be perfect.

## Adapting the rules to your risk tolerance

The principles are the skeleton; the strictness is yours to set:

- **Cautious:** gate everything above (recommended while you build trust with the operator).
- **Standard:** the set above roughly as written — reads free, changes gated, VC always gated.
- **Trusting:** auto-approve more low-risk categories at the permission layer — but keep the
  material/VC/secrets gates (7 · Permissions covers the presets). Even "trusting" never
  auto-approves a push or a delete.

Whatever you choose, **write it down explicitly** in the rules file. An operator can't honor a
policy that only lives in your head — which is Rule 8 applied to governance itself.

Next: [04 · Structure](04-structure.md) — how work is organized into tracked projects and a
registry, so Rule 8 ("status in docs, not memory") has somewhere to live.
