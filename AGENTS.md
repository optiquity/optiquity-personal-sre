# AGENTS.md — optiquity-personal-sre

Guidance for an AI agent working in **this** repository.

## What this repo is — and what it is not

This is a **reference framework**: patterns, guides, and starter files for running your own
machines and services with an AI operator under explicit rules. It is **documentation and
templates, not a program**. There is nothing to install here and nothing that runs against a
fleet.

**It is read-only in normal use.** People adopt this framework by creating **their own private
repo** and copying pieces across (the "two-repo model" — see `README.md`). If you are helping
someone adopt it, your edits belong in *their* repo, not this one.

Contributions to this repo itself are the exception, not the default. If that is genuinely the
task, everything below applies.

## Do not confuse the two rule files

- **This file** governs an agent working *in this repository*.
- **`skeleton/CLAUDE.md.template`** and **`skeleton/AGENTS.md.template`** are the rules a user
  copies into **their own** repo. They are products of this repo, not rules for it.

Editing one when you meant the other is the easiest mistake to make here.

## Layout

| Path | What it holds |
|---|---|
| `guide/` | The *why* — 18 numbered chapters, platform-agnostic. Start at `guide/_contents.md`. |
| `guide/examples/` | Worked end-to-end examples (A/B/C/D/E series), catalogued in chapter 17. |
| `platforms/` | The *how*, per OS — macOS, Linux, Windows, Raspberry Pi, Cloud. |
| `skeleton/` | Starter files users copy. Indexed by `skeleton/README.md`. |
| `scripts/` | `grep-guard.sh` — the secret-scan that guards this repo. |
| `bootstrap.sh` | Creates a user's own repo (Tier-2 onboarding). |

## Rules for editing this repo

1. **Never add anything personal.** No real hostnames, IPs, emails, tenant/tailnet names, vault
   paths, or service URLs. Use `<placeholders>` and role words (`workstation`, `server`, `nas`).
   This is the single hardest constraint here — the content is *derived* from a real private
   fleet, so specifics leak in easily.
2. **Run the guard before committing:** `bash scripts/grep-guard.sh`. It fails closed. Do not
   suppress it; fix the content.
3. **Keep numbering consistent.** Chapters are `NN-name.md` and cross-link by filename. If you
   insert or renumber a chapter, sweep every reference, fix the in-file `# NN · Title` heading,
   fix the `Next:` chain, and update `guide/_contents.md`. Verify with a link check — and check
   that a link's *label* number matches its *target* filename, which a filename-only sweep misses.
4. **Cite rules by number carefully.** Chapter `03-governance-rules.md` defines rules 1–10.
   Citing a number outside that range, or attaching the wrong label to a real one (calling
   symmetry by the wrong number, say), is an error that propagates into every copied template.
   Check both the number *and* the label against the chapter.
5. **`.template` files are content too.** They are not `.md`, so naive checks skip them. Include
   them when sweeping links, rule citations, or renumbering.
6. **Prefer editing in place over restructuring.** This repo is cross-linked densely; a
   reorganization costs a full reference sweep. If a new capability has no chapter that fits,
   that is the signal it needs its own — say so rather than wedging it somewhere.
7. **Say what is verified.** These docs describe real, working setups. If something is untested
   or aspirational, mark it (`⛏ TODO`, "expand before relying on") rather than asserting it.

## Repo index

This repo carries a `.graphifyignore`, so it can be indexed by a repo-comprehension tool
(see [12 · Repo comprehension](guide/12-repo-comprehension.md)). If an index has been built in your
clone — the output directory is gitignored, so check rather than assume — **prefer querying it over
grepping**: it answers structural questions ("what links to this chapter", "where is this concept
explained") far more cheaply than reading files.

If no index exists, just work normally; nothing here depends on it.

## Style

Plain, direct prose. Concrete over abstract. Tables for comparisons, short code blocks for
commands. Explain the *trap* alongside the instruction — the hard-won failure modes are the most
valuable content here and the reason someone reads this instead of a vendor tutorial.

## If you also run Claude Code

There is deliberately no `CLAUDE.md` at this repo root; this file is the single source. Read it
either way.
