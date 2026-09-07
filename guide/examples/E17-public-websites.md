# E17 · Hosting public websites from one box

**Section E — fleet operations.** Back to the [catalog](../17-example-projects.md).

**What this shows:** serving **public websites** — each on its own domain, each a designed static
base plus a CMS for posts — from a single always-on machine at home, **without opening a single
inbound port**. The emphasis is on the parts that actually decide whether this works: the **DNS
migration** (where you break your own email), the **order of operations** when going public, and the
several ways this fails **silently**.

> Generic pattern, no personal config. `<placeholders>` are yours to fill.

**Status: built and verified.** Every step below was executed end to end, including the parts that
went wrong. The traps are marked ⚠ and are the reason this document is longer than the plan was.

---

## The scenario

You already run an always-on node with a container runtime and a private mesh. You want a site
public on a real domain, another later, and a third after that — without the per-site cost growing.

---

## Why not the mesh ingress you already have

If you publish services over a private mesh, that ingress **almost certainly cannot serve a custom
domain**: it serves only its own hostnames, and often gives each node exactly one clean public
address that something already uses.

| Option | Verdict |
|---|---|
| **Outbound tunnel** (Cloudflare Tunnel and similar) | **Recommended.** A daemon dials *out*; nothing is forwarded at the router. |
| **Port-forward 80/443** | Works, but puts your home connection directly in front of the internet. |
| **Mesh ingress** | Ruled out — wrong domain, usually already occupied. |

---

## The shape

```
Internet
  │  (TLS terminated at the tunnel provider's edge)
  ▼
DNS + Tunnel  ──▶  tunnel daemon (container, outbound-only)
                        │  routes by hostname
                        ▼
                   reverse proxy   (one ingress)
           ┌────────────┼────────────┐
           ▼            ▼            ▼
      site-a static  site-a CMS  site-b static  …
                        │
                        ▼
                    database   (one schema per CMS instance)
```

⚠ **The reverse proxy may bind no host port at all.** If it is reachable only inside the container
network, then **the tunnel daemon must run as a container on that same network** — a copy installed
on the host has nothing to connect to. Check before assuming:

```sh
docker inspect <proxy> --format '{{json .NetworkSettings.Ports}}'   # all null?
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:80/        # 000?
```

The host binary is still worth installing — for `tunnel login` and DNS commands — just not for
running the tunnel.

⚠ **Know how your proxy routes.** A proxy configured by **port** rather than hostname has no `Host`
matching, so the tunnel must target the right port — and the wrong port may return **200 while
serving a different site**. That failure mode is a plausible-looking wrong answer, not an error.
Derive the mapping from whatever config actually binds each site, not from comments.

---

## 1. Prove the tunnel before touching DNS

Most tunnel providers offer a **throwaway hostname** requiring no account, no token, and **no DNS
change**. Use it. It proves tunnel → proxy → site end to end while your domain stays untouched.

```sh
docker run --rm --network <net> <tunnel-image> tunnel --url http://<proxy>:<port>
```

Verify, then **prove the rollback**, which matters as much as proving the exposure:

```sh
curl -s -o /tmp/pub -w '%{http_code} tls=%{ssl_verify_result}\n' https://<throwaway>/
diff /tmp/pub <(curl -s https://<mesh-hostname>/)     # want byte-identical
docker stop <tunnel>
curl -s -o /dev/null -w '%{http_code}\n' https://<throwaway>/   # want an error, not 200
```

A rollback that depends on no DNS propagation and no third party is the property that makes
everything after this safe to attempt.

**Then make the tunnel permanent** as a container with persistent credentials — and **gate it behind
an opt-in profile** so public exposure can never be a side effect of a routine restart:

```yaml
  tunnel:
    profiles: ["public"]     # needs: docker compose --profile public up -d
    command: tunnel --config /etc/tunnel/config.yml run
    volumes:
      - ${HOME}/.<tunnel>:/creds/:ro          # NOT nested inside the config mount
      - ./tunnel/config.yml:/etc/tunnel/config.yml:ro
```

⚠ Mount credentials at their **own** path. Mounting a config file *inside* an already-read-only
directory mount fails at container init (`make mountpoint: read-only file system`).

⚠ Prefer **local config over a dashboard-managed tunnel**. Routing in a file is reviewable and
diffable; routing as web-UI clicks is not version-controlled. Declare hostnames **before** they
resolve, so cutover is a DNS change only — no config edit at the moment mistakes are most expensive.
End with a catch-all returning **404**, so an unrouted hostname fails cleanly rather than silently
serving whichever site happens to be first.

Verify it **registered**, not merely that the container is up:

```sh
docker logs <tunnel> | grep -c 'Registered tunnel connection'   # expect several
```

---

## 2. DNS — the step that breaks your email

**This is the highest-risk part of the project, and it has nothing to do with web hosting.**

```sh
dig +short NS  <domain>      # who serves DNS today
dig +short MX  <domain>      # ← your email. This is what you can break.
dig +short TXT <domain>      # SPF, DKIM, domain verification
dig +short TXT _dmarc.<domain>
dig +short A   <domain>
for h in www mail calendar docs drive sites store; do echo "$h: $(dig +short CNAME $h.<domain>)"; done
```

| Record | Action |
|---|---|
| `MX` — every entry, with priorities | **Recreate identically. Never change.** |
| `TXT` — SPF, DKIM, DMARC, verification | **Recreate identically. Never change.** |
| `A` / `CNAME` — apex and `www` | **These, and only these, get repointed** |
| Anything else | Recreate identically unless explicitly decided |

⚠ **Count your mail-carrying domains before you start — you probably have more than you think.**
Defensive registrations (`.net`, `.org`, country TLDs) are often configured as **mail aliases** of
the main domain: full MX sets and their own verification records. Their web records point at
registrar parking, so in a domain list they look like throwaways. The mail configuration is
invisible unless you query MX directly.

⚠ **An idle mail domain that breaks produces no signal.** Nothing bounces, no monitor fires, nobody
complains — because nobody is sending. It is discovered by the first person who finally uses the
address, long after the cause. Idle aliases need no urgent protection, but *"we would have noticed"*
is not available as a safety argument.

**For alias domains that only need to redirect to the main site: use registrar URL forwarding and
leave their nameservers alone.** Zero mail risk, against N× the recreation risk for a convenience
feature. The one real weakness is HTTPS — a browser asked for `https://<alias>` wants a valid
certificate for *that* name before any redirect can happen, and registrar forwarding often cannot
supply one. `http://` works. If an alias ever carries real traffic, migrate that one deliberately.

### The gate: diff, don't trust the import

Providers scan and import existing records automatically. **"Usually correct" is not good enough for
your email.** The scan can only find what is publicly resolvable, so it silently misses anything it
cannot guess.

**Enumerate independently and diff the two.** Query subdomains explicitly — `_dmarc` is a *subdomain*
TXT, and a bare `dig TXT <domain>` misses it, manufacturing a false discrepancy against the scan.

⚠ **Providers default imported web records to "proxied".** That breaks anything whose target requires
a direct connection — hosted-productivity CNAMEs (`mail`, `calendar`, `docs`), SaaS storefronts that
provision their own certificates. Set every one of them to **DNS-only** before activating. Mail
records default correctly, so the exposure is to the *web* names.

The goal is that after the nameserver move the new provider behaves **identically** to the old one.
Change one thing — who answers DNS — not simultaneously how traffic is served.

### The switch

Test mail **before**: send to the domain from outside and confirm receipt; send from it. If receive
is already broken, fix that first rather than migrating a broken thing and guessing afterwards.

⚠ **Do not delete the old provider's records.** Switching nameservers makes them dormant, not gone.
That dormant zone *is* your rollback; deleting it turns a five-minute revert into a reconstruction.

Verify **against public resolvers, never your local stub**:

```sh
for R in 1.1.1.1 8.8.8.8; do
  dig +short NS <domain> @$R; dig +short MX <domain> @$R | wc -l
  dig +short TXT <domain> @$R; dig +short TXT _dmarc.<domain> @$R
done
```

⚠ A stale local resolver can make a clean cutover **look broken** — reporting nameservers that were
never delegated. The machine doing the checking is a variable in its own answer.

⚠ A provider's *"this may take a few hours"* banner is a **formality, not a status**. It polls the
registry before marking a zone active regardless of what has already propagated. `dig` is the answer.

**Then re-test mail.** DNS resolving correctly is *not* the same as mail arriving. **Then stop for the
day** — no proxy toggles, no repointing. If mail misbehaves you want one variable.

---

## 3. Point the hostnames at the tunnel

⚠ Tunnel CLIs **refuse to create a DNS route when a record already exists** — correctly, since that
record is your live site. **Edit the records in place** rather than delete-and-recreate, which leaves
a resolution gap:

| Record | To | Proxy |
|---|---|---|
| apex (change type `A` → `CNAME`) | the tunnel's hostname | **Proxied** |
| `www` | same | **Proxied** |

Tunnel hostnames **must** be proxied — that is how a tunnel routes. Record the old values first.

**Add a `www` → apex redirect at the proxy.** Both hostnames reach the same backend, so without it
identical content is served at two addresses — splitting analytics and creating duplicate-content
ambiguity. Match the `Host` header the tunnel passes through, and place the redirect **first**: a
redirect that runs after a handler has served content never happens.

---

## 4. The failures that are invisible from inside

These cost the most time, because nothing errors.

### ⚠ Client-side integrations built on the mesh break the moment you go public

A site developed behind a mesh may reference **mesh hostnames** in its HTML — analytics, search, fonts.
Those resolve **only on the mesh**. Every check run *from* the mesh passes; every public visitor's
request fails silently. Analytics recording **zero** is the usual symptom, and dashboards look
healthy throughout because they are reporting on the absence of data, not an error.

**Fix: proxy those endpoints same-origin** through the site's own proxy block and reference relative
paths. Same-origin is better regardless — it survives ad-blockers and third-party-cookie
restrictions that kill cross-origin trackers.

⚠ **Proxy only the data endpoints, never the admin UI.** Verify the admin path is *not* reachable
publicly after you add the rule.

### ⚠ A CDN caches failures, including 404s

After fixing a route, static assets can keep returning the old **404 for hours** — the origin is
correct and the CDN is serving a cached failure (`cf-cache-status: HIT`, a multi-hour `max-age`). A
cache-busting query string returns 200 immediately, which is the tell.

**A fix is not complete until the cache is purged**, and this is invisible from the origin. Any deploy
that changes static assets needs a purge.

### ⚠ Exposing an app exposes everything under its path

Proxying `/<app>*` to a CMS publishes **its admin panel too**. Check explicitly:

```sh
curl -s -o /dev/null -w '%{http_code}\n' https://<domain>/<app>/admin-path/
```

⚠ **The obvious fix is often wrong.** Many CMSes offer a separate "admin URL" setting — but pointing
it at a private hostname can move the app's **entire** admin-prefixed namespace there, *including
public read APIs* that site search depends on. Search then 404s for every visitor while the panel
looks correctly secured.

**Let the app believe everything is public and enforce the split at the proxy** — deny the admin UI
and admin API on the public hostnames, and **carve out** the public read API. The proxy is the only
component that knows which hostname a request arrived on.

⚠ **Scope the deny by host, not just path,** if one backend serves both public and mesh traffic —
otherwise you lock yourself out of the panel everywhere.

### ⚠ The CMS bakes its own base URL into every page

A CMS generates absolute links — canonical, `og:url`, RSS, images, embedded APIs — from **one
configured URL**. If it still names the mesh hostname after going public, every one of those links
is unreachable for visitors. **Invisible from inside the mesh**, where the hostname resolves fine.

---

## 5. Monitoring must follow the traffic

⚠ **Checks against your mesh hostname do not cover the public path.** They stay green with the CDN,
the tunnel, and public DNS all completely broken.

Add **public-hostname** checks, including a certificate-expiry condition. Write them early if you
like — but be honest that a check written and left disabled is **not coverage**: a dormant check is
indistinguishable on a board from a passing one, and worse than none because the board looks
complete. Record the exact enable trigger next to it.

**Prove the alert by inducing a failure.** Stop the tunnel, confirm the alert arrives, restart, and
confirm the **resolve** notification too — a monitor that alarms but never stands down trains you to
distrust it.

⚠ **An induced failure is indistinguishable from a real one by design.** Tell whoever watches the
alerts *before* you stop the service.

⚠ **Container "started" is not application "serving".** A CMS restart reports done in seconds while
migrations and template compilation run for minutes. Measure from outside.

---

## 6. Back up, and prove the restore

The CMS database is the only copy of your posts. Schedule a backup, and then **restore it**:

1. Fetch the archive **from the remote target**, not a local copy — a test that reads a file the
   origin still has proves nothing about the offsite one.
2. Verify the archive before trusting it (`gzip -t`, table count vs production).
3. Restore into a **scratch database**, never over production.
4. Compare counts **and content** — a restore can produce the right number of empty rows.
5. Drop the scratch copy; confirm production still serves.

⚠ A verification step that cannot distinguish *"bad file"* from *"no file"* reports alarming failures
for boring causes. Check existence before integrity.

---

## 7. Adding site N must be trivial

Per site: one static build, one CMS instance, one database schema, one proxy block, one tunnel
ingress rule, one DNS record. Script it so the cost does not grow — and have the script **print the
next command including any profile flag**. Omitting an opt-in profile flag leaves the public tunnel
**down while the stack looks fully up**, and a hand-off that tells the next person to do that is a
documentation bug with an operational blast radius.

---

## 8. If you also build a status page

⚠ **Out-of-flow CSS rules belong in the global block, not inside a media query.** A `display:none` or
`position:fixed` that lives only inside a `max-width` breakpoint leaves the element **in flow** at
larger widths. In a fixed-column grid it becomes an extra grid item and shifts every sibling by one —
panes read as swapped, with valid CSS, parsing JS, and a correct DOM. Nothing errors; the grid does
what it was told. Audit by counting a grid container's in-flow children against its declared columns.

---

## Adapt it

- **One site, no CMS?** Skip the CMS and database; the tunnel and DNS work is unchanged.
- **Don't want a tunnel provider?** Port-forwarding works, but you own the exposure.
- **Already have public DNS elsewhere?** The record-diff gate still applies; it is about **your mail**,
  not about any particular provider.

---

## Related

- [08 · Networking](../08-networking.md) — the private mesh, and publishing a service deliberately
- [14 · Monitoring](../14-monitoring.md) — checks, alerting, proving the alert
- [E11 · Publish a service](E11-publish-a-service.md) — the single-service, mesh-hostname case
- [E16 · Health, alerting & the update digest](E16-fleet-health-and-alerting.md)
