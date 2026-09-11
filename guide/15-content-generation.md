# 15 · Documentation & content generation — writing from a source of truth

A fleet produces documentation constantly: runbooks, project status, decision records, setup notes,
a dashboard, release notes, and eventually something outward-facing. This chapter is about producing
that writing **from your repo rather than from memory**, and about the failure mode that makes it a
reliability problem rather than a publishing one.

If "documentation" sounds like a stretch for an SRE guide, here is the argument: **stale
documentation fails the same way a stale monitor does — silently, while looking healthy.** This
framework already names that pattern in three places. A doc that describes a design you reversed
last month is not a tidiness problem; it is a system telling you something untrue with full
confidence.

## The problem: drift is silent, and prose has no tests

Code has a compiler and tests. Config has a diff against the machine. Prose has nothing. A document
becomes wrong the moment the thing it describes changes, and **nothing reports it**.

Three real shapes of this:

- **The derived copy.** A second copy of a document, marked "derived" or "staging", drifts from the
  original while keeping the appearance of authority. A copy marked derived still drifts — it just
  drifts with a label on it.
- **The stale index.** A generated artifact — a search index, a knowledge graph, an API reference —
  built once and never rebuilt. It answers every query successfully and cites the codebase as it was
  in some earlier month.
- **The listing nobody checks.** A hand-maintained list of files, chapters, or services in prose. It
  is wrong within weeks and nothing compares it to disk.

All three pass every check you have, because you have no checks. That is the gap this chapter fills.

## Grounding: the load-bearing idea

**Grounded generation means every claim traces to a source you control.** The generator does not
recall what your system does; it reads your repo and writes from what it finds.

This is the direct payoff of [13 · Repo comprehension](13-repo-comprehension.md). Once your
codebase is legible to the operator — indexed, queryable, with relationships extracted — it can be
written *from*. The same structure that lets an operator answer "what calls this?" lets it answer
"what does this system actually do, in order, with citations."

The property to insist on: **when grounding is missing, the generator blocks rather than invents.**
A tool that fills a gap with a plausible sentence has produced the worst possible artifact — an
authoritative-sounding claim with nothing behind it, indistinguishable from the true ones around it.

⚠ **And here is the trap that makes this an SRE concern: a generator cannot tell a stale grounding
source from a current one.** A ten-day-old index passes every grounding gate. Every claim traces
correctly — to the repo as it was ten days ago. If the design changed in between, the output is
confidently, traceably wrong, and the block-on-missing-grounding safeguard never fires because
nothing is missing.

**So the freshness of the grounding source is your obligation, not the tool's.** Rebuild it on a
schedule or on a commit hook, and record when it was built. *Cached results are fine; pretending
they are fresh is not.*

## The field

**Docs-as-code** — prose in the repo, rendered by a static site generator.

- **MkDocs**, **Docusaurus**, **Hugo**, **Sphinx**, **mdBook** — mature, reviewable in pull
  requests, and the right answer for most documentation. The repo is the source of truth; the site
  is derived.

**Extraction and indexing** — making a codebase queryable.

- **Language servers** and **AST tools** for structure, **repository packers** for whole-corpus
  context, **knowledge-graph builders** for relationships across files and formats.

**Grounded generation pipelines** — producing prose from an indexed corpus.

- **[`optiquity-content-pipeline`](https://github.com/optiquity/optiquity-content-pipeline)** is
  this framework's reference implementation: it grounds each claim in an extracted graph of the
  source and **blocks rather than invents** when grounding is absent. It is the same relationship
  chezmoi has to config in [05](05-chezmoi.md) — one worked answer, named so you have something
  concrete to compare against.
- **Retrieval-augmented setups** built on a vector store or graph store do the same job with more
  assembly.

**The axes that decide it:**

1. **Does it block or invent when grounding is missing?** The only axis with a wrong answer.
2. **Is the output reproducible** — same input, same result — or does it drift run to run?
3. **Can you see the citation?** A claim you cannot trace is a claim you have to verify by hand,
   which removes the point.
4. **Who owns the corpus?** A pipeline that uploads your repo somewhere is a privacy decision
   ([06 · Secrets](06-secrets.md)), not a tooling one.
5. **What does it cost to rebuild?** This decides whether you can afford freshness, which decides
   whether the whole thing is honest.

**Adapt, don't adopt.** Most readers need docs-as-code and nothing else. Reach for generation when
the corpus is too large to hold in your head and the writing is repetitive enough to be worth
automating — not because generation is impressive.

## Owning it

**The generated artifact is derived. Commit the config, not the output** — or commit the output
deliberately, knowing you have taken on the job of keeping it current. Generated output in the repo
that nobody regenerates is the stale-index problem with a commit hash on it.

**Give the grounding source a build timestamp and check it.** The one thing that makes staleness
visible is a recorded build time compared against the repo's own history. *"Built at commit X, now
N commits behind"* is a health check. Without it, staleness has no symptom.

**Rebuild on a trigger, not on memory.** A commit hook, a schedule, or a step in the publish flow —
anything that is not a person remembering ([14 · Workflows & automation](14-automation.md)).

⚠ **A refresh that fails is invisible.** If the rebuild is automated, something must report that it
ran and succeeded. An automated refresh that has been failing for a month leaves you strictly worse
off than a manual one, because you stopped checking.

**Review generated prose as prose.** Grounded does not mean correct: a pipeline can cite a real
source and still assemble a misleading paragraph. Grounding removes invention, not judgement.

## What to write down

- which documents are **authored** and which are **generated**, because the rules differ
- the grounding source, how it is built, and **when it was last built**
- what triggers a rebuild, and what reports a failed one
- which generated artifacts are committed and which are derived at publish time
- for anything outward-facing: what may be published and what may not
  ([19 · Public/shared repos](19-sharing.md))

Next: [16 · Multi-node operations](16-multinode.md) — running all of this across more than one
machine.
