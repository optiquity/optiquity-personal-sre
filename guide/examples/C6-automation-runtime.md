# C6 · A self-hosted automation runtime

**Section C — self-hosted apps over the private mesh.** Back to the [catalog](../17-example-projects.md).

**What this shows:** standing up a real self-hosted service — a **workflow/automation runtime**
(n8n-style) — in a container, reachable **privately over the mesh by default** and **publicly only
when a specific webhook needs it**. The full "own a service end-to-end" example, applying the
[08 · Networking](../08-networking.md) *publish-a-service* discipline.

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

---

## The scenario

You want a **self-hosted automation runtime** on your always-on `server` — a service that runs
workflows, reacts to webhooks, and glues your tools together (n8n, Node-RED, Huginn, and similar
are all this shape). It should:

- run **24/7** on the `server`,
- be reachable **privately** (just your own devices) for the admin UI,
- expose **only specific webhooks publicly** when an external service must call in — not the whole
  app,
- keep its **secrets out of git** and its data persistent.

## Why do it "the framework way"

Self-hosting is where "the operator owns a service" gets real — install, expose, secure, persist,
and maintain, all as one tracked project. The framework's opinion is strong here:
**private-by-default, public-only-deliberately** — you expose the *one* surface that genuinely
needs it, document what's exposed, and everything else stays on the mesh.

## The shape

### 1. Prereqs (added per this project, not preemptively)

- A **container runtime** on the `server` (see [C7 · Container runtime + stack](C7-container-runtime-stack.md)
  for standing that up).
- The **private mesh** (Tailscale) already in place ([08 · Networking](../08-networking.md)).
- A place for **persistent data** (a named volume / bind mount) and **secrets from the vault**
  ([06 · Secrets](../06-secrets.md)), never inline.

### 2. Run the service in a container, config tracked

```
# Compose-style intent (tracked in your repo; secrets via ${VAR}, never literals):
#   service: <automation-runtime> image, restart: always
#   volumes: a persistent data volume (workflows, credentials store)
#   env:     ${WEBHOOK_URL}, ${ENCRYPTION_KEY}, ... resolved at runtime from the vault
#   bind:    loopback or the mesh interface — NOT 0.0.0.0 public by default
```

The compose file / unit is **tracked** ([05 · chezmoi](../05-chezmoi.md)); the **secrets are
references** resolved on the node.

### 3. Expose it — private first

- **Admin UI + normal use → private over the mesh.** Front the service with the mesh's private
  "serve" mechanism (e.g. Tailscale Serve) so it's reachable at a **MagicDNS name, tailnet-only**,
  with no public port. Your devices reach it; nothing else can.
- Bringing the service up + fronting it is a **service bootstrap → gated**
  ([Rule 1](../03-governance-rules.md)).

### 4. Expose a webhook publicly — only when required, only that surface

When an external service (a payment provider, a SaaS callback) *must* reach one webhook:

- publish **only that path/port** via the mesh's public mechanism (e.g. Tailscale Funnel) — a
  dedicated hostname for the webhook, **not** the admin UI,
- keep the rest private,
- **document** in the project doc exactly what's public, why, and how to unpublish (see
  [E11 · Publishing a service safely](E11-publish-a-service.md)).

Mind any platform limits (e.g. a cap on the number of public ports) — front multiple services
with per-service sidecars rather than piling onto one public port.

### 5. Track it

Registry row + `docs/<automation>/PLAN.md` ([04 · Structure](../04-structure.md)): the image +
version, data volume, what's private vs public (and why), the secrets it needs (by name), and how
to back up its data (its DB/credentials store is exactly the kind of thing
[B4 · Backup daemon](B4-nightly-backup-daemon.md) protects).

## Changing a workflow: what's in your repo is not what runs

You will export your workflows to JSON and commit them. That is right — it is the only way a
workflow is reviewable, diffable, and recoverable. But it creates a gap that looks exactly like
success:

> **An export is a copy. Committing one changes nothing about the running system.**

Worse, most automation runtimes now separate the workflow you *edit* from the workflow that *runs* —
a draft and a published version, with a pointer between them. Under that model a direct database
edit, an API `PUT`, or a restart each change the draft and leave the pointer alone. The editor shows
your change. The scheduler keeps running the old one. Nothing errors.

⚠ **Find out whether your runtime has a draft/published split before you deploy anything.** If it
does, publishing is a **separate step** and skipping it is silent.

### The import trap

Whatever CLI imports a workflow, read its flags before the first real use. In the runtime this
documents, `import` **deactivates every workflow it imports** by default — it says so in a log line
that reads like progress:

```
Importing 1 workflows...
Deactivating workflow "<name>".
Successfully imported 1 workflow.
```

Stop there and the automation is dead. Not broken — *deactivated*, which is a legitimate state, so
no probe fires and no error appears. The publish step is what turns it back on.

⚠ **The obvious escape usually isn't one.** The flag that would preserve the active state was
rejected outright: it only works in a clustered deployment mode. Assuming a flag exists because it
is documented, without running it, is the same class of error as assuming the import worked.

### Verify from the record of what ran

The draft can be correct, the published version stale, and every file on disk right. So do not
verify against any of them. Most runtimes store, with each execution, **a snapshot of the workflow
as it actually ran**. That is the only artifact that answers the question.

Look for a **boundary**: the last execution before your deploy lacks the change, the first one after
carries it. A boundary is evidence. "The file looks right" is not.

⚠ **The marker you measure with must be unique to the new version.** This is subtle and it cost a
correction here. The natural marker was a string the fix introduced — but a *superseded* version of
the same fix contained it too. Measured that way, the already-patched workflow reported as
current and its second deploy vanished from the record entirely. **A marker both versions share
cannot date a change.** Pick a string that exists only in the version you are deploying, and
sanity-check it against the old one before you trust the result.

Then check the whole set, not the one you touched: **reconcile every committed export against the
running definitions.** Drift is silent, and it accumulates in the workflows you are not currently
thinking about.

## Traps in the workflows themselves

Workflow steps are shell one-liners wearing a GUI. They inherit every shell trap, without the review
a script would get.

⚠ **A bare `mv` into a destination that already holds that name fails two different ways, and
errors neither.**

| moving a… | onto an existing same name | result |
|---|---|---|
| **directory** | `mv "<name>" "<dst>/<name>"` | moved **inside** it → `<name>/<name>/` |
| **file** | `mv "<f>" "<dst>/<f>"` | **overwrites it** — silent data loss |

Both exit `0`. The runtime records `success`, because the step ran. The directory case surfaces days
later as a missing result; the file case never surfaces at all.

Pick the next free name instead, and say so in the output:

```sh
D="$(dirname "$DST")"; B="$(basename "$DST")"
if [ -d "$SRC" ]; then N="$B"; E=""
else case "$B" in *.*) N="${B%.*}"; E=".${B##*.}";; *) N="$B"; E="";; esac; fi
T="$DST"; i=1
while [ -e "$T" ]; do T="$D/$N ($i)$E"; i=$((i+1)); done
[ "$T" != "$DST" ] && echo "NAME COLLISION: $B exists - using $(basename "$T")"
mv "$SRC" "$T"
```

⚠ **The counter goes before the extension, and only for files.** `video.mkv (1)` will not play and
no media server will match it. The `[ -d "$SRC" ]` test is what makes the split safe — without it a
directory named `Show.S01` becomes `Show (1).S01`. Splitting an extension off a name that has none
is the trap, not the splitting.

⚠ **Announce the rename.** An `echo` in the step output makes a collision visible in the execution;
without it you discover a stray `<name> (1)` months later and cannot tell what produced it.

### The general lesson, which is the expensive one

The collision was reported as a *folder* nesting. The fix was written, tested against a folder,
deployed, and verified — correctly — against a folder. One node away, in the same workflow, a step
moved **files**, where the same fix would have produced `video.mkv (1)`, and the underlying bug was
not nesting but **overwriting**.

**A fix verified against the case that prompted it is not verified.** The reported symptom is a
sample, not the population. Before deploying, ask what *else* runs this code path — and test the
case nobody complained about, because that is the one with no witness.

## Maintenance — the ownership half

- **Update deliberately, in a window.** Pin the image version; update on your cadence with a quick
  post-update smoke test (a workflow runs, a webhook responds). A workflow runtime is *stateful* —
  back up its data before a major version bump.
- **Back up its data** ([B4](B4-nightly-backup-daemon.md)) — the workflows + credential store are
  irreplaceable; a container is not "backed up" by virtue of being reproducible.
- **Re-check exposure periodically** — confirm the admin UI is still **private** and only the
  intended webhook is public. Exposure creep is the risk with self-hosted services.
- **Rotate secrets** in the vault, not the compose file.
- **Re-export after every UI edit, and reconcile periodically.** A workflow edited in the browser and
  never exported exists in exactly one place — the thing you are backing up, not the thing you can
  review. Reconciling every committed export against the running definitions is how you find the
  ones that drifted.

## What you learn from this example

- **Private-by-default, public-only-deliberately** — expose the one surface that needs it, keep
  the rest on the mesh, and write down what's exposed.
- A self-hosted service is **install + expose + persist + secure + maintain**, all one tracked
  project — the container is the easy part.
- **Stateful services need real backups** and **windowed, version-pinned updates** — reproducible
  ≠ backed up.
- **A committed export is not a deployment.** Know whether your runtime has a draft/published split,
  treat publishing as its own step, and verify from the record of what actually ran — not from the
  file you edited.
- **A fix verified against the case that prompted it is not verified.** Test the path nobody
  complained about; it is the one with no witness.

## Adapt it

In **your** repo: pick the runtime, write the tracked compose/unit with vault-referenced secrets,
bring it up private over the mesh (gated), publish only the webhook you need (documented), track
it, and wire its data into your backup routine.

**Related:** [08 · Networking](../08-networking.md) · [C7 · Container runtime + stack](C7-container-runtime-stack.md)
· [E11 · Publishing a service safely](E11-publish-a-service.md) ·
[B4 · Nightly backup daemon](B4-nightly-backup-daemon.md) · [catalog](../17-example-projects.md).
