# skeleton/repo-index — enabling a repo index

Starter files for giving your AI operator a **queryable model of a repo** instead of making it
grep. The concepts, the trade-offs, and the failure modes are in
[12 · Repo comprehension](../../guide/12-repo-comprehension.md); this folder is the parts.

**Tool-agnostic on purpose.** The framework doesn't pick your indexer — this ships the *committed
footprint* every indexer needs, plus the operational lessons that cost real debugging. Substitute
your tool's filenames and verbs.

| File | What it is |
|---|---|
| `indexignore.template` | The exclusion list — annotated with matcher rules, the `.gitignore` interaction, and a secrets-first default set |
| `enable-repo-index.sh` | Idempotent per-repo enablement: drops the ignore file, adds the output dir to `.gitignore`, prints the remaining manual steps |

## The committed footprint is tiny

That's what makes this cheap to roll out. Per repo, you commit exactly two things:

1. **The ignore file** (`indexignore.template` → your tool's name, e.g. `.graphifyignore`)
2. **One `.gitignore` line** for the index output directory

Everything else — the tool, the built index — is per-machine and per-clone. **Never commit the
index**: it's large, it churns on every build, and it's derivable.

## Then two things the files can't do for you

**Tell the operator it exists.** Add a line to your rules file (`CLAUDE.md` / `AGENTS.md`) saying
the index is there and to prefer querying it over grepping. Without this you've built something
nobody uses — the operator has no way to know.

**Install the refresh hook — per clone.** Git hooks live in `.git/hooks/`, which is **per-clone and
never committed**, so a repo *cannot ship a working hook*. Every clone on every machine installs it
once. That's why a committed installer script (like `enable-repo-index.sh`) is the right pattern:
the repo carries the *instructions*, each clone runs them.

## The failure mode that will actually bite you

**Staleness is silent.** A stale index doesn't look broken — the operator answers confidently from
last month's structure. Worse, refresh hooks are usually written to be *non-blocking* (so they
never fail a commit or push), which means a failing refresh is invisible by design.

Two habits that catch it:

- **Check the hook's own status**, not just that the hook file exists. If your tool writes a status
  file, read it. A hook that runs and fails looks identical to one that works.
- **Compare index age to repo age** — e.g. `git log --oneline --since="$(date -r <index-file>)" | wc -l`.
  A number that keeps growing means the refresh is dead.

**After upgrading your indexer, re-baseline once.** Indexers commonly ship a *shrink guard* that
refuses to overwrite when the new index has fewer nodes than the old — a good safety net against a
half-built index. But an upgrade that changes ignore semantics legitimately shrinks the index, so
the guard blocks the write **forever**, and (being non-blocking) tells no one. Symptom: the index
never updates again after an upgrade. Fix: one forced rebuild to reset the baseline, then normal
operation resumes. Check your tool's force flag/env var.

## Privacy

An index is a derived artifact that an assistant reads and that may be fed to a hosted service.
Exclude secrets-adjacent paths **even when they're already gitignored** — the ignore file's default
set leads with exactly that. Treat the index like any other output: know where it lives, know it's
gitignored, and know what went into it.
