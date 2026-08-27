# CLAUDE.md — optiquity-personal-sre

**The operating rules for this repo live in [`AGENTS.md`](AGENTS.md). Read that file.**

It is the single source deliberately: keeping two rule files in sync is a bug waiting to happen,
and this framework's own guidance ([11 · Agents & skills](guide/11-agents-skills.md)) is to keep
the rule *content* identical across CLIs rather than let them drift.

The short version, so this file is useful on its own:

- **This is a read-only reference framework**, not a working repo. Adoption happens in *your own*
  private repo (the two-repo model — see [`README.md`](README.md)). Edits here are the exception.
- **Nothing personal, ever** — no real hostnames, IPs, emails, tenant names, or service URLs.
  Run `bash scripts/grep-guard.sh` before committing; it fails closed.
- **Don't confuse this file with `skeleton/CLAUDE.md.template`**, which is the rules file a *user*
  copies into their own repo. That one is a product of this repo, not rules for it.
- **A repo index may exist in your clone** (`graphify-out/`, gitignored) — prefer querying it over
  grepping. **There is deliberately no refresh hook here**; this repo is ~90% prose, where an
  automatic structural refresh can destroy a curated semantic index. Refresh deliberately with
  `/graphify . --update`. See [`AGENTS.md`](AGENTS.md) § Repo index.

Everything else — layout, the editing rules, style — is in [`AGENTS.md`](AGENTS.md).
