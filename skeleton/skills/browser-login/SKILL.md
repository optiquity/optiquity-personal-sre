---
name: browser-login
description: "Drive a real browser to operate a web service that has no usable API, logging in with credentials from the vault-read skill. Composes existing capabilities; confirms before destructive actions."
metadata:
  {
    "example": true,
    "requires": { "bins": ["<browser-automation-cli>", "<vault-cli>"] }
  }
---

# browser-login — automate a web UI safely (example skill)

A generic example (guide/11-agents-skills.md) of the highest-value skill shape: **compose**
a browser-automation capability + the `vault-read` skill to operate a service that has no API —
without a bespoke scraper, and without ever exposing a credential. **Teaching example: no real
site, account, or credentials.**

## When to use

A task needs to read or change something in a web service that offers no (usable) API, so the
web UI is the only path. Prefer any official no-credential path first (e.g. an email-in or
import feature) for *creating* data; use this for read/update/delete that only the UI supports.

## Session & login

1. Use a **named, persistent** browser session so you log in once and reuse it (headless by
   default; headed only if a human wants to watch — or if the site's bot-protection requires it,
   see below).
2. Open the login page; get the credential from the vault **just-in-time** via the `vault-read`
   skill (`vault "<Entry>" username`, `vault "<Entry>"`, and `vault "<Entry>" totp` if 2FA);
   fill directly, submit.
3. On success, save the session state and reuse it on later runs to skip re-login.

## CRUD, carefully

- **Read** — navigate, extract the fields you need; return structured data, not whole pages.
- **Create/Update** — fill forms, save, then **re-verify** the saved value before reporting
  success.
- **Delete** — only after an explicit user confirmation naming exactly what will be removed.

## Anti-automation note

Some sites block automation (bot-detection / WAF). If you find the specific approach that gets
through (a real-browser channel instead of a bundled engine, non-headless, human-like pacing),
**record it here with the reason**, so the operator doesn't rediscover the block each run — and
stay honest that a working approach may need revisiting if the site tightens.

## Guardrails

- **Destructive ops need explicit confirmation.** Before any Delete — and any Update that
  overwrites existing data — state exactly what will change (which item, old → new) and get a
  yes. Never bulk-delete without per-item or explicitly-scoped confirmation.
- **Credentials:** read-only against the vault (`vault-read` only); never echo the password/TOTP
  into logs, chat, saved files, or session state beyond the browser's own encrypted storage.
- **Stay on the intended site**; don't navigate off or exfiltrate page content beyond the task.
- **One session at a time** for a given account, to avoid double-submits.
- If login or 2FA can't be satisfied, **report it** — don't loop-retry in a way that could lock
  the account.
