# E15 · Media automation for a self-hosted library (add-ons, not a second stack)

**Section E — fleet operations.** Back to the [catalog](../15-example-projects.md).

**What this shows:** *enhancing* and *observing* a self-hosted media server (Plex / Jellyfin / Emby)
by folding in **small, single-purpose pieces** — a **config-as-code collection/metadata manager**
(a scheduled batch job, no UI) and an **analytics tool + its exporter** feeding the **Prometheus +
Grafana you already run** ([E13](E13-fleet-metrics-stack.md)) — instead of dropping in a bloated
all-in-one that ships its own everything. Plus the judgment calls that trip people: **where hardware
transcoding actually works**, what **"missing" really means**, and matching automation to a library's
intent.

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

---

## The scenario

You run a media server and it works, but you want two things: to **enhance** the libraries (curated
collections, richer metadata, badges) and to **see what's happening** (who's streaming, direct-play
vs transcode, bandwidth). The popular "media automation" guides hand you a giant compose file with a
dozen services and their *own* bundled Prometheus + Grafana. You don't want a second monitoring stack
fighting the one you have — you want the **individual pieces**, wired into your existing setup, each
pinned and private.

## Why do it "the framework way"

- **Add-ons, not a stack.** Each capability is **one container** (or one native install) that reuses
  what you already run — your metrics stack, your mesh, your secrets file — never a parallel copy.
- **Config as source.** The collection/metadata rules live in **committed YAML**, not click-ops
  inside a container volume. The library setup is reproducible and reviewable.
- **Private by default.** Anything with a UI gets a **mesh Serve sidecar** (tailnet-only), like
  [E11](E11-publish-a-service.md). The batch job and the exporter have **no UI → no sidecar**.
- **Pin versions.** An appliance touching your library or your metrics is **never `:latest`**.
- **Touch the API, not the files.** A metadata manager works entirely through the server's **API** —
  it reads libraries and writes collections; it never opens a media file. Keep it that way.

## The shape

### 1. A collection / metadata manager — a scheduled batch job (no UI)

Tools like **Kometa** (for Plex) run on a **schedule**: they wake, apply your collection + metadata
rules through the media-server API, then sleep. So:

- **No web UI, no mesh sidecar, no dashboard tile** — it's a cron-shaped worker, not a service.
- **Config as code:** a committed `config.yml` naming your libraries and the collection definitions.
- **Secrets by env-injection, not in the config.** Good managers let the committed config reference a
  placeholder (e.g. `<<sometoken>>`) that's resolved from an environment variable at run time — so
  the **real token stays in your secrets file**, never the tracked config. Mind the tool's naming
  rules (some, Kometa included, **forbid underscores** in the secret name).
- **Nothing happens until the schedule fires** — which makes the first run reviewable: check the
  config, or trigger a one-off run on demand, before it touches the library at 05:00.

### 2. An analytics tool + its exporter → your existing Grafana

An analytics app (e.g. **Tautulli** for Plex) gives history, per-user activity, and transcode-vs-
direct decisions in its **own UI** — put that behind a **private Serve sidecar**. Then, exactly as in
[E14](E14-github-metrics.md), add its **Prometheus exporter as one internal container** (no sidecar)
and scrape it into the **Grafana you already have** — a live *streams / transcode / bandwidth* panel
next to your fleet CPU, so a transcode spike lines up with the server's load. **Adopt the exporter,
not a bundled stack.** Know the exporter's scope: many expose **live activity only** — deep history
stays in the analytics UI.

### 3. (Optional) Library optimization / transcoding — read §"Where hardware transcoding works" first

Bulk re-encoding / health-checking (e.g. **Tdarr**) is tempting, but it's the piece most likely to be
in the wrong place. See the judgment call below before you containerize it.

## Judgment call: where hardware transcoding actually works

The media server itself may transcode fine — but a **separate bulk-transcode container** often can't:

- **A container can't always reach the host's hardware video encoder.** On some hosts — notably
  **Apple Silicon under a Linux-VM container runtime** — the container has **no access to the host's
  hardware encoder**, so bulk transcoding runs **CPU-only**: slow, hot, and it pegs the machine for
  hours. (The media server transcodes fine because it runs **native** and *can* reach the encoder —
  but that's playback, not a bulk re-encode job.) **Check whether your runtime exposes the GPU /
  hardware encoder before committing bulk transcode to a container.** If it doesn't, run that tool
  **native**, or don't run it.
- **Bulk transcode over a network mount is heavy.** If the media lives on a NAS mounted over NFS/SMB,
  a re-encode reads and writes **terabytes** over that link and **mutates originals** — so it's a
  **deliberate, gated job**, never an always-on service. Health-checking + remuxing (no re-encode)
  is the lighter, safer win if space isn't the goal.

## Judgment call: "missing" means two different things

A collection manager reports **"missing"** — but not the way you might assume:

- A metadata manager's **"missing" = whole titles** on a curated or popularity list (e.g. "Top Rated")
  that **you don't own**. Useful for *movies* (it surfaces real gaps), noisy for some libraries (see
  next), and it **reports only** — it does **not** acquire anything.
- **Missing *episodes* of shows you already have** is a **different tool's** job — an acquisition
  manager (the *-arr family, e.g. Sonarr) that tracks the full episode list per series and flags
  aired-but-absent episodes. Don't expect the metadata manager to do it. Decide up front which you
  want; wiring an acquisition manager is a separate, opt-in project (and pulls in indexer + download
  choices that are yours to make).

## Judgment call: match collection sources to the library's intent

Default "popularity" collections (Trending / Popular / Airing Now) are built from **current** global
data. Point them at a **classic / archive** library and they come out **mostly "missing"** (an
"Airing Today" collection over an archive can match **zero** of your items) — and for TV, global
popularity skews to international reality/news, so the lists are largely noise. **Basic** ("Recently
Added") and **Top Rated** collections fit almost anything; reserve trending/airing sources for
*current* libraries. Review the per-library report the manager writes before deciding what to keep.

## Traps (all real)

- **The required-variable guard is all-or-nothing at parse time.** If your compose marks the
  analytics **and** manager secrets as required (`${VAR:?...}`), **nothing** in the file starts —
  not even the analytics UI — until *every* one is set. But the analytics exporter's key only exists
  **after** the analytics tool's first-run setup. **Seed placeholders** so the stack parses, bring up
  the UI, then replace the real value after setup.
- **Two tokens to the same server is normal.** The metadata manager authenticates with a token from
  your **secrets file**; the analytics tool gets its **own** token via its setup wizard (stored in
  its data volume). Don't try to unify them.
- **Analytics apps mis-warn on named Docker volumes.** Some (Tautulli among them) **can't detect a
  named volume** and warn *"data may be cleared."* It's a **false positive** — named volumes persist
  — but the clean fix is a **bind mount** (which is also **host-visible and captured by a host-dir
  backup**, unlike a named volume), or disable the app's mount check.
- **A container behind the mesh NAT can't scrape mesh (`100.x`) addresses** — scrape the exporter by
  container name on the compose network (same lesson as [E13](E13-fleet-metrics-stack.md)); the
  manager reaches the **native** media server over the **LAN**, not a mesh name.
- **A scheduled batch container buffers stdout** — you'll see *no* logs while it sleeps until the next
  run. Force unbuffered output (e.g. `PYTHONUNBUFFERED=1` for a Python tool) so it streams into your
  log viewer; otherwise the log tab reads empty even after a run.
- **Container image pulls hang headless** on a GUI-keychain credential helper — pull from an
  interactive session, or bypass with an empty client-config dir for public images (but that same
  empty dir can hide the `compose` plugin — use it for the **pull**, not the `up`).

## What you learn from this example

- **Adopt the pieces, reuse your stack** — a metadata worker + an analytics exporter fold into the
  metrics stack you already run; no second Prometheus/Grafana.
- The **container-vs-hardware boundary** — where a bulk-transcode job actually belongs.
- **Config-as-code + env-injected secrets** for a reproducible, review-before-it-runs library setup.
- The real meaning of **"missing"**, and picking the right tool for episode gaps.
- **Matching automation to a library's intent** instead of applying one template everywhere.

## Adapt it

- **Jellyfin / Emby** have their own metadata managers and analytics + exporters — same "adopt the
  piece" shape.
- **Requests + cleanup** (a request portal, a rules-based library pruner) slot in as more private
  add-ons when you want them.
- **Acquisition automation** (the *-arr family) is the separate opt-in for *episode/movie gaps* — add
  it deliberately, with its own indexer + download-client decisions, when "missing episodes" is the
  real goal.
