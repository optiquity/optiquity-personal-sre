---
name: vault-read
description: "Read a credential/TOTP from your secret store (read-only), unlocking non-interactively so automation needs no human prompt. The building block for any skill that logs in."
metadata:
  {
    "example": true,
    "requires": { "bins": ["<vault-cli>"] }
  }
---

# vault-read — read-only credential access (example skill)

A generic example of the vault-read pattern (guide/06-secrets.md, guide/11-agents-skills.md).
Adapt `<vault-cli>` and the unlock mechanism to your secret store (KeePassXC, 1Password, `pass`,
the OS keychain — see the platform spokes). **This is a teaching example — it contains no real
credentials, paths, or entry names.**

## What it does

Fetch a single field (password / username / URL / TOTP) from your vault, **read-only**,
unlocking **non-interactively** (the vault's master key comes from the OS keychain, so no human
prompt) — so an operator or another skill can obtain a credential at the moment it's needed.

## The helper

Use a small wrapper (call it `vault`) on `PATH`. It ONLY reads — it never writes, edits, or
deletes the vault:

- Username:  `vault "<Entry Title>" username`
- Password:  `vault "<Entry Title>"`            (password is the default field)
- TOTP code: `vault "<Entry Title>" totp`       (only if the entry has TOTP)
- URL/other: `vault "<Entry Title>" url`
- Find:      `vault --find <keyword>`           (titles only, no values)

## Workflow

1. `vault --find <keyword>` to confirm the store is reachable and find the exact entry title.
2. Fetch **only** the field you need, **at the moment** you need it.
3. For 2FA: fetch the password, then fetch `... totp` immediately before use (codes expire).

## Guardrails

- **Read-only:** never write, edit, add, or delete vault entries through this skill. You manage
  entries yourself, in the vault app.
- **Never** print secrets (passwords, TOTP, the master key) to logs, chat, code, or files.
  Return only the requested value, only where it's needed. Do not copy secrets to disk or env
  files.
- If the store is unreachable or the keychain unlock fails, **report it** — do not prompt for
  the master password or guess credentials.
