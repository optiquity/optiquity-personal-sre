# 12 · Repo comprehension — making your codebase legible to the operator

An AI operator working in a repo it doesn't understand does what you'd do on your first day: it
greps. It opens files, follows imports, reads a lot to answer a little. That works, and it is
expensive — in tokens, in latency, and in the quality of the answer, because "I read twelve files"
is not the same as "I understand how this fits together."

This chapter is about giving the operator a **model of your repo** it can query, so questions like
*"what would break if I change this?"* or *"where does this behaviour actually live?"* are answered
from structure rather than reconstructed by reading.

It's optional. For a small repo, grepping is fine. It earns its place when a repo gets big enough
that reading-to-answer becomes the dominant cost — or when you want to *write about* the codebase
(see the [pipeline pattern](#feeding-content-not-just-answers) below).

## Two different things, often confused

| | What it does | Good for |
|---|---|---|
| **Packing** | Flatten some-or-all of the repo into one big text/XML blob for a model to read | One-shot: "here's my repo, now help" — external tools, a fresh model, a notebook |
| **Indexing** | Build a persistent, queryable structure (a graph, a symbol index) of entities and relationships | Repeated, cheap, targeted questions inside a working session |

Packing is stateless and complete; indexing is stateful and selective. **They're complements.**
A common setup runs both: an index for the operator's day-to-day questions, and a pack when you
need to hand the whole thing to something else.

## What a repo index buys you

- **Fewer tokens per answer.** The operator queries the structure instead of reading files to
  rebuild it.
- **Relationship answers.** Call paths, blast radius, "what depends on this" — questions that grep
  can't answer without you already knowing where to look.
- **A shared vocabulary.** Communities/clusters in the graph often *are* your architecture's real
  seams, which is useful even to a human.
- **Grounding.** Anything generated from the index — a summary, a doc, a post — can cite what it
  was derived from, rather than being the model's impression of your code.

## The traps, learned the hard way

**Staleness is silent and it is the main risk.** An index built last month describes last month's
repo, and nothing about a stale index *looks* wrong — the operator answers confidently from it.
Decide a refresh trigger up front: a commit hook, a scheduled rebuild, or a "rebuild when N commits
behind" check. Then verify the trigger actually runs; an index nobody refreshes is worse than none,
because it converts "I don't know" into "here's a confident wrong answer."

**The ignore file is not your `.gitignore`, and its semantics may change.** Indexers usually take
their own exclusion list. Read the current docs for *matcher syntax* (glob? gitignore pathspec?
`fnmatch`?), *precedence* (first match or last match wins?), and *interaction with `.gitignore`*
(merged, or does the presence of your file replace it?). These differ **between versions of the
same tool** — an exclusion file written for one minor version can silently change what's indexed
after an upgrade. Re-read the rules when you upgrade, and treat the ignore file as config that
needs review, not set-and-forget.

**A refresh that fails is invisible.** Refresh hooks are written to be *non-blocking* — they must
never fail your commit or push — so a broken one looks identical to a working one. Check the
index's age against the repo's, not just that the hook is installed: if "commits since the index
was last written" keeps climbing, the refresh is dead. A hook that writes its own status line
turns this into a one-glance check; without one, the index file's mtime is the tell.

**After upgrading the indexer, re-baseline once.** Indexers commonly refuse to overwrite an index
that has *fewer* entries than the stored one — a sensible guard against a half-built index. But an
upgrade that changes ignore semantics *legitimately* shrinks the index, so the guard then blocks
every future write **permanently**, and (being non-blocking) tells nobody. The symptom is an index
that simply never updates again after an upgrade. One forced rebuild resets the baseline. Check
your tool's force flag before you need it.

**A docs repo and a code repo want different treatment.** This one is easy to miss because the
tooling doesn't warn you. On a code repo, the routine "refresh the index" operation is a
*structural* rebuild — cheap, deterministic, safe to run on every commit. On a repo that is mostly
prose, the same command can **replace a curated semantic index with raw heading-level nodes**,
discarding the interpreted layer that made it useful, and it will look like it succeeded. If your
index has a semantic/LLM-derived layer, find out which refresh path preserves it *before*
automating anything — and if the answer is "the cheap one doesn't", then a commit hook is actively
harmful there and the right setting is no hook at all. Per-repo guidance should say which kind of
repo it was written for.

**The semantic pass has a model dial — turn it down.** If indexing runs through an AI CLI it likely
defaults to the largest model, but the work is structured extraction into a fixed shape, not
open-ended reasoning. A mid-tier model is the right default; save the top tier for a prose-heavy
repo where concept quality is the point. That knob is also your escape hatch when a usage limit
stops a build — indexers cache per file, so switching model and re-running resumes rather than
restarting.

**Exclude what shouldn't be read.** Secrets-adjacent paths, vendored dependencies, build output,
archives. This is a *privacy* decision as much as a signal-quality one — an index is a derived
artifact that can end up somewhere you didn't intend.

**Don't commit the index.** It's large, it churns every build, and it's derivable. Gitignore the
output directory and let each clone build its own. What you *do* commit is the small config: the
ignore file and the gitignore entry.

**Pin the tool, and then actually track the pin.** A pinned version is correct for reproducibility
across nodes, but a pin nobody watches is just a stale install — and tools installed outside your
main package manager (a Python tool installer, a language-specific tool manager) are exactly the
ones your update checks are most likely to miss. Make sure they're in scope
([14 · Monitoring](14-monitoring.md)).

## Adopting it per repo

The committed footprint is deliberately tiny — that's what makes this cheap to roll out:

1. **An ignore file** at the repo root, written against the current tool's documented semantics.
2. **A gitignore entry** for the output directory, so the index never lands in version control.
3. **A line in your rules file** (`CLAUDE.md` / `AGENTS.md`) telling the operator the index exists
   and to prefer querying it over grepping — otherwise it won't know, and you've built something
   nobody uses.
4. **A refresh trigger**, per the staleness warning above.

Everything else — the tool itself, the built index — is per-machine and per-clone, installed by
your normal tooling path ([07 · Tools & requirements](07-tools-requirements.md)).

Starter files for exactly this footprint — an annotated exclusion template and an idempotent
enablement script — are in [`../skeleton/repo-index/`](../skeleton/repo-index/).

## Feeding content, not just answers

There's a second payoff that isn't obvious until you try it: **an index is a grounding source for
writing about your own work.** Documentation, a README, a release note, a post explaining an
architecture decision — all of these are much better when derived from the actual structure than
from a model's recollection of a codebase it skimmed.

If you go that route, keep the boundary clean: the thing that *builds and maintains* the index
belongs to your infrastructure (install it, update it, keep it fresh); the thing that *reads* the
index to produce prose is a separate concern with its own repo and its own review loop. Mixing
them means your publishing pipeline can dirty the repos it's writing about.

Two properties matter for that use: the index should be **read-only** to consumers, and it should
be **attributable** — a claim in a generated doc should trace back to something real.

## What to reach for

The tooling here moves fast, so this chapter names *categories*, not winners:

- **A repo packer** for one-shot handoffs to external tools. Look for token counting, an ignore
  file, and some form of compression/summarization for large trees.
- **A code-graph indexer** for repeated structural questions. Most are built on tree-sitter and
  expose a CLI plus an MCP server; the good ones handle many languages and give you communities or
  clustering, not just a call graph.
- **A wiki/narrative generator** if your goal is prose about the repo rather than answers about it.
  These are a genuinely different category — indexers give you structure, not sentences.

Evaluate against your own repo, not a benchmark: file composition (code vs docs vs data) changes
which tool wins, and a tool that's brilliant on a Python monorepo can be useless on a repo that's
mostly Markdown.

Next: [13 · Multi-node](13-multinode.md) — the advanced layer: remote apply, session mobility, and
the fleet view.
