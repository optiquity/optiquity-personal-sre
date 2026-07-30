# Onboarding — resume here

**You are setting up your personal-SRE repo (`<repo-name>`, role `<role>`).** `bootstrap.sh`
did the first part; this doc is where your AI CLI session picks up. If you're an AI operator
reading this at session start: this is an **open** project — orient from it, then offer the
user the next uncompleted step. Reference the framework's `GETTING-STARTED.md` and `guide/`
(read-only reference at `<framework-dir>`) for the how/why.

## What bootstrap already did ✅
- Detected the platform + checked hard-core prerequisites.
- Created/cloned this **private** repo and seeded it (UNCOMMITTED) with:
  - `CLAUDE.md` (your rules file — the operator's guardrails; filled for this repo/role)
  - `PROJECTS.md` (the registry, with this onboarding project)
  - `docs/onboarding/PLAN.md` (this file)

## Next steps ⬜ (operator: propose these one at a time, pausing for approval on anything material)

1. **First commit.** Review the seeded files, then make the initial commit (governed: show the
   user what will be committed, get approval — Rule 2). This is the first exercise of the loop.
2. **Read the rules.** Confirm `CLAUDE.md` matches how the user wants you to behave; adjust the
   permission posture (cautious/standard/trusting — `guide/09-permissions.md`) for this role.
3. **Secrets.** Set up the ignore files (allowlist pattern) + the platform secret store, and a
   runtime secrets file if needed (`.env`/shell env) — `guide/06-secrets.md`. Confirm the
   zero-secrets-in-git invariant. NEVER put a secret in a tracked file.
4. **Config manager (chezmoi).** Install + `chezmoi init` this repo as the source; set the role
   in the config data; explain the dev-clone → prod-source → pull+apply flow
   (`guide/05-chezmoi.md`). Do not apply to the machine without a diff + approval.
5. **MCP (optional).** Configure the external capabilities the user needs (GitHub, filesystem)
   from the templates — no tokens in committed config, filesystem scopes limited
   (`guide/10-mcp.md`).
6. **Multi-node (optional).** If >1 node: SSH keys (key-only) + a private mesh (Tailscale) +
   record the access edges (`guide/08-networking.md`).
7. **First real project.** Track something the user is actually doing as a project in
   `PROJECTS.md` with a plan doc — to exercise the whole loop end to end.
8. **Close onboarding.** When the above are done, flip this project to `resolved` in
   `PROJECTS.md`.

## Notes
- **This repo is yours** — edit freely. The framework at `<framework-dir>` is a **read-only
  reference**; never edit it.
- The fastest way through steps 2–7 is to let the operator drive conversationally
  (the Tier-3 prompt in the framework's GETTING-STARTED.md) — that's what this hand-off enables.
