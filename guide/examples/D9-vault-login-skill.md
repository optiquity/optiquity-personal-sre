# D9 · A vault-read helper + login-automation skill

**Section D — composed skills & credentials.** Back to the [catalog](../16-example-projects.md).

**What this shows:** turning credential access + browser automation into a **governed, reusable
skill** — a **read-only** vault helper composed with browser automation into a `SKILL.md` that
logs into a service the operator can't reach by API, with **destructive-op confirmation** baked in.
Ties [06 · Secrets](../06-secrets.md) + [11 · Agents & skills](../11-agents-skills.md) together.

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

---

## The scenario

You want the operator to act on a web service that has **no usable API** — read something, or
perform an action only the web UI supports — **without ever exposing a credential** and **without
a bespoke scraper**. The clean way: compose two capabilities you already trust:

1. a **read-only vault helper** that fetches a credential just-in-time, and
2. a **browser-automation** capability that drives the site,

into a single **skill** the operator loads on demand, with the guardrails written into it.

## Why do it "the framework way"

This is where secrets, skills, and governance meet. The framework's stance:

- **Credentials come from the vault, read-only, just-in-time** — never inlined, never logged
  ([06 · Secrets](../06-secrets.md)).
- **Skills compose existing capabilities** rather than introducing bespoke, brittle code
  ([11 · Agents & skills](../11-agents-skills.md)).
- **Guardrails live in the skill** — especially confirmation before destructive actions — so the
  safety travels with the capability.

The framework even ships two generic starter skills for exactly this: a
[`vault-read`](../../skeleton/skills/vault-read/SKILL.md) helper and a
[`browser-login`](../../skeleton/skills/browser-login/SKILL.md) example.

## The shape

### 1. The read-only vault helper

A small wrapper (`<vault>`) that fetches **one field at a time** from your secret store, unlocking
**non-interactively** (its master key comes from the OS keychain, so automation needs no prompt),
and that **only ever reads** — never writes, edits, or deletes the vault:

```sh
<vault> "<Entry Title>"            # password (default field)
<vault> "<Entry Title>" username
<vault> "<Entry Title>" totp       # if the entry has 2FA
<vault> --find <keyword>           # locate the entry (titles only, no values)
```

Read-only-ness is deliberate: automation *reads* credentials it's already entitled to; you manage
the vault yourself. Worst case, its blast radius is a read.

### 2. The login-automation skill (composition)

A `SKILL.md` ([11 · Agents & skills](../11-agents-skills.md)) that uses browser automation to log
in via the vault helper — **filled just-in-time, never echoed**:

```
# 1. Resolve the entry:  <vault> --find <site>  -> the login URL + fields
# 2. Open the login page in a sandboxed browser session (headless unless watching)
# 3. Fill username <- <vault> "<Entry>" username ; password <- <vault> "<Entry>"
#    (+ TOTP <- <vault> "<Entry>" totp if prompted) — fill directly, never log
# 4. Do the task: READ (extract structured data) or CRUD via the UI
# 5. Save the session state for reuse so you don't re-login every run
```

### 3. Guardrails in the skill (the important part)

Bake these into the `SKILL.md` so the safety can't be skipped:

- **Destructive ops need explicit confirmation** — before any delete, or an update that
  overwrites data, state exactly what will change (item, old→new) and get a yes.
- **Never echo secrets** into logs, chat, files, or saved state beyond the browser's own encrypted
  storage.
- **Stay on the intended site**; don't exfiltrate page content beyond the task.
- **One session at a time** per account (avoid double-submits); on repeated login failure, **stop
  and report** rather than loop (which can lock an account).

### 4. Track it

Skills are **tracked** ([05 · chezmoi](../05-chezmoi.md)) so every node has the same version, and
recorded as a project ([04 · Structure](../04-structure.md)). Note whether it's a **generic** skill
(shareable) or **personal** (tied to a specific account — stays in your private repo, never
published — see [14 · Sharing](../15-sharing.md)).

## Maintenance — the ownership half

- **Sites change + fight automation.** When a site tightens bot-protection and you find the
  approach that works again (a real-browser mode, human-like pacing), **record it in the skill with
  the reason**, so the operator doesn't rediscover the block every run — and stay honest that a
  working approach may need revisiting.
- **Rotate credentials in the vault**, never in the skill; the skill only ever *reads*.
- **Review the guardrails** on changes — the destructive-op confirmation and no-echo rules are the
  load-bearing parts.
- **Keep skills versioned + symmetric** across nodes ([Rule](../03-governance-rules.md)) — a skill
  is only reliable if every node runs the same one.

## What you learn from this example

- **Compose, don't scrape** — a vault-read helper + browser automation beats a bespoke,
  credential-embedding client.
- **Read-only credential access** keeps the automation's blast radius tiny.
- **Guardrails belong in the skill** — destructive-op confirmation and no-echo travel with the
  capability, and **personal skills stay private** while generic ones can be shared.

## Adapt it

In **your** repo: wire your platform's secret store into a read-only `<vault>` helper (from the
skeleton), write a `SKILL.md` that composes it with browser automation for the specific site,
bake in the confirmation + no-echo guardrails, and track it (private if it's tied to your account).

**Related:** [06 · Secrets](../06-secrets.md) · [11 · Agents & skills](../11-agents-skills.md) ·
[`skeleton/skills/vault-read`](../../skeleton/skills/vault-read/SKILL.md) ·
[`skeleton/skills/browser-login`](../../skeleton/skills/browser-login/SKILL.md) ·
[14 · Sharing](../15-sharing.md) · [catalog](../16-example-projects.md).
