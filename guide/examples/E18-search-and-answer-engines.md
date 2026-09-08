# E18 · Search and answer-engine visibility

**Section E — fleet operations.** Back to the [catalog](../17-example-projects.md).

**What this shows:** making a self-hosted site **findable** — by classic search engines *and* by AI
assistants — as a maintained property of the platform rather than a one-off audit. The emphasis is on
the parts that are mechanically checkable and therefore automatable, and on the several ways this
fails **silently**.

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

**Status: built and verified.** Every trap marked ⚠ cost real time. None of them produced an error.

---

## The three surfaces, and why they are not one job

| Surface | Reached by | Decided by |
|---|---|---|
| **Classic search** | crawler → index → ranking | crawlability, titles, links, authority |
| **AI answers** | retrieval crawler → cited in a generated reply | being *fetchable* and *quotable* |
| **Agents** | a program acting for a user | machine-readable structure, clean sitemaps |

They overlap but do not coincide. The decision that separates them most sharply is below.

---

## 1. Training crawlers and retrieval crawlers are different things

This is the single most consequential distinction, and it is easy to get backwards.

- **Training crawlers** collect content to train models. Blocking them costs you **nothing** in
  visibility.
- **Retrieval crawlers** fetch a page **to answer a live question**, and cite it. Blocking them
  removes you from AI answers entirely.

A defensible default — **block training, allow retrieval** — keeps your content out of model weights
while remaining citable. But it only works if you get the agent list right, and **the split is
per-vendor**:

| Vendor | Training | Retrieval |
|---|---|---|
| OpenAI | `GPTBot` | `OAI-SearchBot`, `ChatGPT-User` |
| Anthropic | `ClaudeBot` | **`Claude-SearchBot`**, `Claude-User` |
| Google | `Google-Extended` | *(no retrieval-only counterpart — see below)* |
| Others | `CCBot`, `Bytespider`, `Amazonbot`, `Applebot-Extended`, `meta-externalagent` | `PerplexityBot` |

⚠ **Anthropic publishes three agents, not two.** `Claude-SearchBot` indexes content for search;
`Claude-User` only fetches a URL a user already has. Allowing `Claude-User` alone still leaves you out
of Claude's search results — the vendor's own documentation says blocking `Claude-SearchBot` *"may
reduce your site's visibility and accuracy in user search results."* A two-agent mental model is the
easy mistake here.

⚠ **Google has no retrieval-only counterpart.** `Google-Extended` governs Gemini training *and*
grounding, so blocking it forfeits Gemini-app grounding. It does **not** affect AI Overviews or AI
Mode, which follow `Googlebot` and normal snippet rules. Decide this deliberately and write down
which trade you took, or it gets re-argued in six weeks.

⚠ **Re-verify quarterly.** This list changed *during* a single planning session. Treat any written
agent list as perishable.

---

## 2. Your CDN may be writing your `robots.txt`

⚠ **The file you ship is not necessarily the file crawlers get.**

A CDN or edge provider may inject its own managed `robots.txt` — commonly an AI-crawler block enabled
by default on new zones. Check the two ends against each other, not just the origin:

```sh
curl -s https://<domain>/robots.txt | wc -c          # what the world gets
# and, from inside your network, whatever your proxy actually serves
```

If the byte counts differ, something between you and the internet is editing it.

**Find out whether it merges or replaces before changing anything.** In the case this documents it
**merged** — the origin's directives and its `Sitemap:` line all survived, with the managed block
prepended. The instinct to "turn the override off" would have been actively harmful: the managed block
was *implementing* the desired posture, and disabling it would have allowed training crawlers.

**Declare the full posture at origin anyway.** Duplicate user-agent groups merge harmlessly per the
spec, and it makes your file correct **standalone** if the managed block is ever disabled. Cheap
insurance against a silent policy reversal.

⚠ **Do not assert a byte-match between origin and edge.** A legitimate prepend means bytes will never
be equal; that check fails forever and trains you to ignore it. Assert instead that **every directive
the origin declares survives** to the edge.

---

## 3. The CDN caches `robots.txt` far longer than your pages

⚠ **This one nearly produced a false "success" report.**

HTML is typically served dynamic and updates immediately. `robots.txt` is a static file and can sit in
the edge cache for **hours** — a 4-hour TTL is common. So after deploying a corrected `robots.txt`:

- the **origin** is right
- **every crawler** still gets the old file
- and nothing anywhere reports a problem

```
cf-cache-status: HIT
age: 7036                  ← ~2 hours stale
cache-control: max-age=14400
```

**A `robots.txt` change is not complete until the cache is purged.** Make the purge an explicit step
in the deploy sequence, not a thing someone remembers.

⚠ **Never verify with a cache-busting query string.** `?v=1` measures the **origin**; crawlers get the
**cached** response, and this incident proves those differ by hours. A buster reports success on a
file no crawler can yet see. If the check looks flaky, **the cache is the finding**.

---

## 4. Sitemaps: two files, not one

If a CMS lives under a path (`/blog`), it usually publishes **its own** sitemap. The instinct is to
reference it from the main index. That is invalid:

⚠ **A sitemap index cannot reference another sitemap index.** Most CMS sitemaps *are* indexes with
children (posts, pages, authors, tags). Nesting them produces a "Nested indexing" error in search
consoles — silently ignored until you look.

**Instead:** declare both in `robots.txt` and submit both separately to each search console.

```
Sitemap: https://<domain>/sitemap-index.xml
Sitemap: https://<domain>/blog/sitemap.xml
```

Also worth doing: redirect the conventional `/sitemap.xml` to your real index. A **301**, not a
served copy — two files claiming to be the sitemap is a divergence problem in miniature.

---

## 5. Push as well as pull: IndexNow

Sitemaps are *pull* — you wait to be crawled. **IndexNow** is *push*: notify participating engines the
moment content changes. Bing, Yandex, Seznam and Naver participate; **Google does not** and uses the
sitemap, so this complements rather than replaces it.

Ownership is proved by serving a key at `/<key>.txt` containing the key itself. **The key is public by
design** — it is not a credential and belongs in your repo, unlike anything in an `.env`.

**Serve it from the platform, not from a site build.** That makes it fleet-wide: site #2 inherits
IndexNow by adding a registry row, with no change in its content repo.

⚠ **Make the ping advisory.** A search engine being slow, down or rate-limiting must never fail a
deploy that actually succeeded. *"The deploy worked"* and *"the notification worked"* are different
facts and must not share an exit code.

---

## 6. Check the served surface, not the build

A build-time SEO check (missing titles, duplicate descriptions, broken internal links) belongs in the
site's own build. But it can only see **what the build produced**. A second check belongs in the
platform, asserting **what the internet receives**:

| | Build check | Served check |
|---|---|---|
| **Inspects** | build output | the live response |
| **Catches** | missing meta, dupes, bad canonicals | edge overrides, injected headers, cached failures, stale files |

Neither substitutes for the other. Useful served-side assertions: every origin `robots.txt` directive
survives to the edge · both sitemaps declared *and* reachable · no `X-Robots-Tag` suppressing indexing
· canonical points at the canonical host · no internal-only hostnames in resource URLs.

### ⚠ Three bugs found in that checker by running it — all the shape it exists to catch

1. **It followed redirects**, so a *working* 301 was reported as the 200 it landed on. A checker that
   misreports a passing state is worse than no checker.
2. **A custom `User-Agent` drew a 403** from the CDN, which it would have reported as a site fault.
   **The tool must not be a variable in its own measurement.**
3. **It assumed HTML attribute order** — requiring `rel=` before `href=` — and the minifier emitted
   `href` first, hiding a correct canonical. Never assume attribute order in emitted HTML; minifiers,
   frameworks and templating engines reorder freely.

A tool that measures a surface can be wrong about that surface **in exactly the ways the surface can
be wrong**.

---

## 7. None of this is measurement

Everything above proves the **plumbing**. Whether you are indexed, ranked or cited is a different
question, and it needs accounts you must create yourself:

- **Search consoles** (Google, Bing) — verification, then submit both sitemaps. Bing can usually
  import verification from Google, avoiding a second DNS record.
- ⚠ **Check for an existing verification record before adding one.** A domain already using hosted
  email often carries a verification `TXT` that satisfies a domain property outright — and that record
  is load-bearing for mail. Adding a redundant one next to it is a needless edit to a live mail zone.
- **A recurring AI-citation check.** Ask each major assistant a handful of questions your site should
  answer, monthly, and record whether it is cited. **This is the only thing that tells you whether the
  crawler posture in §1 achieved anything** — and it is easy to omit precisely because it is manual.

⚠ Without these, both the platform and the content side are working blind — the same trap as
monitoring an internal hostname and calling it public coverage.

---

## Splitting the work

Roughly: **the platform owns delivery and verification; content owns the words and the markup.** Where
an artifact is authored in one and enforced in the other — a `robots.txt` you ship and your CDN
rewrites — neither side can fix it alone. Name that boundary explicitly before starting, and see
[principle 12](../03-governance-rules.md) if two sessions are involved.

---

## Related

- [E17 · Hosting public websites from one box](E17-public-websites.md) — the platform this sits on
- [08 · Networking](../08-networking.md) · [14 · Monitoring](../14-monitoring.md)
- [03 · Governance](../03-governance-rules.md) — principle 12, one plan and one owner
