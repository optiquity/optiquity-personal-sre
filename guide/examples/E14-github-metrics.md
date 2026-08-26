# E14 · GitHub-as-a-service metrics (a maintained exporter, not a bundled stack)

**Section E — fleet operations.** Back to the [catalog](../16-example-projects.md).

**What this shows:** folding **GitHub repository metrics** (stars, forks, watchers, open issues/PRs,
size) into the metrics stack you *already* run ([E13](E13-fleet-metrics-stack.md)) — with a
**maintained exporter as one internal container**, not a bundled all-in-one that ships its own
Prometheus + Grafana. Plus the judgment call most write-ups skip: **which repos are even worth tracking.**

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

---

## The scenario

You want to watch your repos over time — stars trending, issues piling up, the occasional fork.
GitHub's built-in **Insights** shows some of this, but **traffic (clones/views) is only kept 14 days**,
it's **per-repo with no aggregation**, and there's no long-term history. You already have Prometheus +
Grafana (E13); you just want GitHub feeding into it.

The popular demo repos for this (search "github monitoring prometheus") **bundle their own Prometheus +
Grafana** — great for *learning*, but dropping one next to a stack you already run gives you a *second*
of each, fighting the first. You don't want their stack. You want their **exporter**.

## Why do it "the framework way"

- **Exporter, not a stack.** Add one exporter container; reuse your Prometheus + Grafana.
- **Internal by default.** A metrics exporter has **no UI** — it's a `/metrics` endpoint. Give it **no
  mesh sidecar**; Prometheus scrapes it by container name on the internal network. Nothing exposed.
- **Pick a maintained exporter.** The demo repos often pin an **abandoned** one. Use something actively
  maintained (e.g. `promhippie/github_exporter`) and **pin its version**.
- **Minimal secret.** A **read-only** token, scoped as narrowly as the repos require.

## The shape

### 1. One exporter container (internal)
Run the exporter on your compose network, pointed at the repos you want, with the token in the
environment — and **no Serve/mesh sidecar**, because it's not a UI. Pin the version.

### 2. One scrape job — slow, but mind Prometheus's staleness
Add a single job to `prometheus.yml` targeting `<exporter>:<port>`. GitHub data moves slowly and the
API is **rate-limited** (5000 req/hr authenticated), so you *want* a slow scrape — **but keep it under
Prometheus's lookback window** (default 5 min), or `stat`/table panels flip to **"No data"** between
scrapes as the last sample ages out. **1–2 min** is the sweet spot: gentle on the API, never stale.
(Scraping *at* 5 min with a 5-min lookback is the classic trap.)

### 3. A read-only token, scoped tight
A fine-grained PAT: for **public** repos, "Public repositories (read-only)" grants read across every
public repo with **zero private access**. Keep it in your secrets file (`.env`), never git.

### 4. A dashboard, provisioned as config
Provision a "GitHub repos" dashboard (stars / forks / watchers / open issues + a per-repo table) the
same way as any other — a file in your repo, not a click-import.

## The judgment call: public vs private repos

This is where "track everything" is the wrong instinct. **The metrics that make a GitHub dashboard
interesting are social/external** — stars, forks, watchers, traffic. A **private** repo is visible only
to you + collaborators, so those are **structurally near-zero and flat** — nothing to trend.

- **Track public repos** — that's where the signal is.
- **Skip private repos by default.** The only metrics with any signal on a private repo are **open
  issues/PRs, size, and CI (workflow runs / Actions minutes)** — and on a solo repo those are ~0 too.
  Tracking them also forces a **broader token** (private-repo read) and multiplies API calls for flat
  data. Add a specific private repo **only** if it has active issues/PRs or CI worth graphing.

## What you get — and what you don't

- **Get:** stars, forks, watchers, open issues/PRs, repo size — and, if you enable those collectors,
  **workflow runs**, **Actions/billing**, and **API rate-limit** headroom.
- **Don't (well):** **traffic (clones/views)** — support is spotty across exporters, and GitHub only
  serves 14 days anyway; and deep **contributor / code-frequency** stats. If clones/views over time is
  the real goal, GitHub **Insights** or a small scheduled **Action** that snapshots the traffic API is
  the better tool for *that* slice.

## Traps

- **Don't add a mesh sidecar** to an exporter — no UI ⇒ keep it internal.
- **Scrape interval vs staleness** — slow enough to spare the API, but **under Prometheus's ~5-min
  lookback** (1–2 min), or `stat`/table panels flicker to "No data" between scrapes. Scrape only the
  repos you care about.
- **The bundled-stack repos are demos** — reuse the exporter, discard the Prometheus/Grafana they ship.

## What you learn

- **Exporter, not a stack** — adopt the *piece*, not the demo.
- **Internal-by-default** exporters (no UI ⇒ no mesh exposure).
- **Scope + minimal-token** discipline.
- The **public-vs-private judgment** — track where the signal actually is.

## Adapt it

- **GitLab / Gitea / other SaaS** have equivalent exporters — same "adapt, don't adopt" applies.
- **Org-wide?** Most exporters can enumerate an org — but mind the rate limit and the noise.
- Pair it with your **fleet** dashboards (E13) so infrastructure and project health share one Grafana.
