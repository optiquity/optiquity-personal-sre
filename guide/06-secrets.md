# 06 · Secrets — the never-in-git discipline

Secrets are the one thing that must **never** enter version control — not once, not "just
temporarily," not in history. This section defines the discipline that makes "zero secrets in
git" a structural guarantee rather than a hope, and how the operator and config manager get the
credentials they need at runtime without ever storing them.

This is governance [Rule 3](03-governance-rules.md) made concrete.

## Why zero, and why structural

A secret committed to git is **compromised permanently**. Deleting it in a later commit doesn't
help — it's in the history, in every clone, in every fork, and (if the repo is ever public) in
every scraper's cache. There is no "unpublish."

So the target isn't "few" secrets in git — it's **zero**, enforced by structure, not memory. A
human who has to *remember* not to commit a secret will eventually forget. The framework makes
the safe path the default: secrets are **excluded by the ignore files** and **supplied at
runtime from a vault**, so committing one requires actively defeating the setup rather than
simply slipping.

## What counts as a secret

Treat all of these as never-in-git:

- API keys, tokens, OAuth credentials, refresh tokens
- Passwords, passphrases, PINs
- Private SSH keys, TLS private keys, signing keys
- Cloud credential files, service-account JSON
- Container-registry / package-registry auth
- Session state that embeds any of the above
- `.env` files (they almost always contain the above)
- **SMTP / app passwords** — the credential your alerting uses to send mail. Easy to overlook
  because it feels like "just notifications", but it can send mail *as you*.

**Not** secrets (safe to version): public keys, non-sensitive config, *references* to secrets
(a variable name like `${GITHUB_TOKEN}`, not its value), and the *names* of vault entries.

## The two mechanisms

Zero-in-git rests on two independent mechanisms. Use **both** — defense in depth.

### 1. Structural exclusion (ignore files)

Your ignore files (`.gitignore` for git, plus the config manager's own ignore file) are the
**wall**. The robust pattern is **allowlist, not denylist**: for sensitive directories, ignore
everything and then explicitly un-ignore only the specific non-secret files you intend to
track.

```gitignore
# Deny-all a sensitive area, then allow only known-safe files back in:
secrets-adjacent-dir/*
!secrets-adjacent-dir/README.md          # a safe file, explicitly allowed
# never add the .env, the .kdbx, the *token* files
```

Why allowlist beats denylist: a denylist (`ignore *.env`) misses the file you didn't
anticipate; an allowlist (`ignore everything, allow these three known-safe files`) fails
*closed* — a new file is excluded until you deliberately allow it. For anything near secrets,
fail closed.

Hard-exclude, everywhere and permanently:
- `**/.env`, `**/*.pem`, `**/*.key`, `**/id_*` (SSH keys), `**/*.kdbx` (vault files)
- credential/auth directories for your tools
- anything a tool writes that embeds a token

### 2. Runtime supply (a vault / keychain)

Config that *needs* a secret references it **by name**; the real value lives in a **secret
store** and is fetched at the moment of use:

- **Runtime secrets** (an app needs a token to run): stored in your OS keychain or a vault; the
  service reads them from there at start, or from an untracked local `.env` the app loads but
  git ignores.
- **Interactive/automation secrets** (the operator needs to log into a site): stored in a
  vault (e.g. KeePassXC, 1Password, `pass`, or the OS keychain), read **just-in-time** by a
  small helper, used, and never written to disk or logs.

In tracked config you write a **reference** — `${VAR}` or a vault-entry title — never a value.
The config manager renders the reference; the value is resolved locally, on the node, from the
store. The repo stays clean by construction.

Per-platform secret stores (Keychain, Credential Manager, libsecret/`pass`, cloud secret
managers) are covered in the spokes; the **pattern** is identical everywhere: *reference in
git, value in the store, resolve at runtime.*

### The ignore-file policy (spelled out)

The ignore files are the wall, and the policy is **allowlist / fail-closed** for anything near
secrets. Two rules:

1. **Deny broadly, allow narrowly.** For a sensitive directory, ignore everything (`dir/*`),
   then explicitly un-ignore (`!dir/known-safe-file`) only the specific files you *intend* to
   track. A file you didn't anticipate is excluded until you deliberately allow it.
2. **Hard-exclude secret shapes globally**, everywhere, permanently: `**/.env`, `**/*.pem`,
   `**/*.key`, `**/id_*`, `**/*.kdbx`, credential/auth dirs.

You maintain this in **two** ignore files — `.gitignore` (what git tracks) and your config
manager's ignore file (what it renders onto nodes). The skeleton ships both as templates
(`gitignore.template`, `chezmoiignore.template`) with the allowlist pattern and heavy inline
comments — copy and adapt. Verify the policy holds with a secret-scan before committing (below).

### Recipe: a runtime secrets file (`.env` + shell env)

For secrets a service or your shell needs at runtime (as opposed to a vault-read at the moment
of use), the concrete setup:

1. **Create a git-ignored env file.** Copy the skeleton's [`env.example`](../skeleton/env.example)
   to a real file — either
   `~/.env` (outside any repo) or a repo-local `.env` (the ignore templates already exclude
   `**/.env`). Fill in real values. **The filled file is never committed; the `env.example`
   with placeholders may be.**
2. **Load it from your shell** so tools inherit the vars. In `~/.zshenv` (zsh) or `~/.bashrc`:
   ```sh
   [ -f "$HOME/.env" ] && set -a && . "$HOME/.env" && set +a
   ```
   (`set -a` exports everything the file defines; `set +a` turns that off again.)
3. **Reference, never inline.** In tracked config, write `${GITHUB_TOKEN}` — the config manager
   renders the reference; the value comes from the loaded env or the store at runtime.

### Recipe: a secret a *daemon* reads (not your shell)

A background service — a health checker, a scheduled job — has no shell and no session, so the
recipe above doesn't reach it. The shape that does:

1. **A dedicated env file next to the service's config**, owned by whoever runs the service and
   `chmod 600` (root-owned if the unit starts as root). Not in any repo.
2. **Hand it to the service the way its runtime does it** — a systemd `EnvironmentFile=` drop-in,
   or the timer/job's own environment. A **drop-in** is better than editing the shipped unit:
   it survives package upgrades and keeps your change separable.
3. **Commit the `.template`, never the filled file.** Ship `<placeholder>` values so the shape is
   documented and reviewable; the real one is created on the node and stays there.
4. **Split secret from non-secret.** Only the credential needs the locked file — sender and
   recipient addresses aren't secrets and can live in the versioned config as plain values.

Worked example: the alerting credential in
[`../skeleton/monitoring/`](../skeleton/monitoring/) (`mail.env.template`, `gatus.env.template`,
`gatus-smtp.dropin.conf`), narrated in [E16](examples/E16-fleet-health-and-alerting.md).

> `~/.zshenv` itself is a dotfile you may config-manage — but it should only ever *load* the
> secrets file, never *contain* secrets. Keep the split: env file = values (git-ignored);
> shell rc = the one line that loads it (trackable).

High-value or interactive secrets still belong in the **vault/keychain** (read just-in-time via
the helper pattern below), not a flat env file — an env file is for convenience vars and things
a service reads at startup.

## The vault-read helper pattern

For automation that needs credentials (the operator logging into a service, a skill fetching a
token), the framework's pattern is a small **read-only helper** that:

- Unlocks the vault **non-interactively** (its master key comes from the OS keychain, so no
  human prompt is needed for automation), and
- Fetches **only the one field requested**, at the moment it's needed, and
- **Never** writes, edits, or deletes the vault, and **never** prints the secret to logs, chat,
  or files.

Read-only-ness is deliberate: automation reads credentials, it never manages them. You add and
edit vault entries yourself, in the vault app. This keeps the blast radius of the automation
tiny — the worst it can do is *read* a secret it was already entitled to.

A concrete example skill using this pattern ships in the skeleton
([11 · Agents & skills](11-agents-skills.md)).

## Verifying the discipline holds

Trust, but verify — make "no secrets in git" checkable, not assumed:

- **A scan before committing.** Grep the staged change for secret-shaped patterns (`*_KEY`,
  `token`, `BEGIN PRIVATE KEY`, high-entropy strings). The operator does this as part of the
  commit workflow.
- **A guard for shared repos.** If any repo is or may become public, add a **pre-commit hook
  and/or CI check** that *fails* on personal patterns and secret shapes — so a mistake is
  blocked mechanically, not caught by luck. (The framework's own public repo uses exactly this;
  see [16 · Public/shared repos](16-sharing.md).)
- **Periodic history audit.** Occasionally scan the *history*, not just the working tree — a
  secret committed months ago won't show in `status`.

If a secret does reach git: treat it as **compromised** — rotate/revoke it immediately, then
scrub history (filter-repo/BFG) as cleanup. Rotation is the real fix; history-scrubbing is
hygiene, not absolution.

## The payoff

This discipline is what makes everything else safe to version and to share:

- Your private repo can hold your entire configuration **because** it holds no secrets.
- The operator can freely commit, and even a public derivative of your setup carries no risk —
  the secrets were never there to leak.
- "Is it safe to push this?" has a boring, reliable answer: **yes, there are no secrets here,
  by construction.**

That boring reliability is the whole point.

Next: [07 · Tools & requirements](07-tools-requirements.md) — the idempotent, role-aware
installer pattern that ensures each node has the tools it needs.
