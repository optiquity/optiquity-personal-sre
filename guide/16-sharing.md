# 16 · Public/shared repos — publishing without leaking

Most adopters never need this section: your setup lives in your **private repo** and stays
there. But if you want to **publish a generalized version of your framework** — as *this*
framework is published — this section is how you do it without leaking a single personal
detail. It's also the reference for how this repo's own public edition is produced.

## The two-repo split, restated

From [01 · Concepts](01-concepts.md): keep **what's private** and **what's shareable** in
**separate repos**.

- **Private repo** — your real configs, machine references, project status. Never public.
- **Public/shared repo** — a **derived, scrubbed** edition containing only the generic patterns,
  templates, and guides. No names, no paths, no accounts, no anything-yours.

The public repo is **not a filtered view** of the private one and **not a fork** — it's a
separate repo, populated by *deriving* generic content from your private patterns. Deriving (not
copying) is the safe default; the guard below is the backstop.

## The cardinal rule: derive, don't copy

**Never `cp` a file from private to public.** Copying carries personal detail by default and
relies on you to remember to scrub — which is exactly the failure mode. Instead:

- **Rewrite** each artifact into placeholders and roles as you move it. A config becomes a
  *template*; a machine name becomes a *role*; `/Users/you` becomes `$HOME`; your email becomes
  `<your-email>`.
- The scrub is the **act of moving**, not a cleanup pass afterward. If you find yourself
  "scrubbing a copied file," stop and rewrite it instead.

## What must never appear in the public repo

The non-negotiable exclusion list:

- **Personal identifiers** — real names, usernames, emails, account IDs, handles.
- **Machine names** — use roles (`server`, `workstation`, …), never actual hostnames.
- **Paths that reveal you** — `/Users/<name>`, `/home/<name>`; use `$HOME` or placeholders.
- **Network specifics** — real IPs, LAN subnets, tailnet names/IDs, MagicDNS names.
- **Any secret** — the entire [06 · Secrets](06-secrets.md) list, obviously; but also
  *references* that happen to embed a real value.
- **Personal skills/projects** — anything tied to *your* specific accounts or services stays
  private. Only *generic* example skills ([11](11-agents-skills.md)) go public.
- **Vault paths, backup locations, service URLs** — anything that describes *your* actual
- **Monitoring config**, which is quietly full of your topology: node inventories (SSH targets and
  hostnames), local-check configs (mount paths, service labels), and health-check configs (service
  URLs, mesh names). Publish the `.template` with `<placeholders>`; never the filled file. The
  alerting credential and the recipient address are secrets in the ordinary sense.
  infrastructure.

If you're unsure whether something is personal: it's personal. Leave it out.

## The grep-guard (mechanical enforcement)

Human diligence isn't enough for a public repo — one slip is permanent
([06 · Secrets](06-secrets.md)). So enforce the exclusion list **mechanically** with a
**grep-guard**: a script that scans the tree and **fails** if any forbidden pattern appears.

The framework ships one ([`scripts/grep-guard.sh`](../scripts/grep-guard.sh) — it guards this
repo, so it lives at the root rather than in the skeleton); it checks for:

- Path patterns: `/Users/`, `/home/<name>`-style user paths
- Email patterns: anything matching a real address
- Network patterns: `192.168.`, `10.`, `100.`-range IPs, tailnet-ID shapes
- Your specific tokens: the machine names, usernames, and repo name you're scrubbing away
  (you configure these — the guard is parameterized with *your* forbidden strings)
- Secret shapes: `*_KEY`, `token`, `BEGIN … PRIVATE KEY`, high-entropy strings

Wire it in two places:

1. **Pre-commit hook** in the public repo — every commit is scanned before it lands. A hit
   **blocks the commit**.
2. **CI check** (a GitHub Action — see [`skeleton/github/`](../skeleton/github/)) — every push/PR
   is scanned server-side, so a bypassed local
   hook is still caught.

The guard **fails closed**: if it can't decide, it flags. A false positive costs you a
`git` annotation; a false negative costs you a permanent leak — so bias it toward noise.

## The publish workflow

Putting it together, publishing (or updating) the public repo:

1. **Derive/scrub** the content you're publishing — rewrite to templates, roles, placeholders.
   Never copy.
2. **Run the grep-guard** over the whole tree. **Must be clean.** Fix any hit by
   generalizing further — never by suppressing the guard.
3. **Review the diff** as if you were a stranger reading it. Would anything here identify you or
   your infrastructure? If yes, generalize it.
4. **Commit + push** — gated on your approval like any VC action ([Rule 2](03-governance-rules.md)),
   with the guard running as a pre-commit hook.
5. **Keep it private until you're satisfied.** A new public-intended repo can start **private**;
   flip it to public only once the content is complete and the guard is clean. Flipping to
   public is a deliberate, human action — not something automated.

## If something leaks anyway

Treat it like a secret leak ([06 · Secrets](06-secrets.md)):

- **A personal identifier** — it's in history now. Scrub the working tree, and for anything
  sensitive (not just a stray name), rewrite history (filter-repo/BFG) and force-push. For a
  low-sensitivity slip, a forward fix + a note may suffice — your call on the risk.
- **An actual secret** — rotate/revoke it immediately (the real fix), then scrub history.
- **Tighten the guard** so that class of leak can't recur — every incident should teach the
  guard a new pattern.

## Why this is worth the discipline

A public framework repo is only valuable if it's **trustworthy** — if adopters can read it
knowing it contains patterns, not a stranger's private life. The derive-don't-copy rule plus a
fail-closed guard makes "this repo has nothing personal in it" a **structural guarantee**, the
same way [06 · Secrets](06-secrets.md) makes "no secrets in git" structural. That guarantee is
what lets you share the work at all.

---

*This is the last section of the master guide. For platform-specific commands, see the spokes
(`platforms/`); for starter files, see `skeleton/`; to begin, see [15 · Setup](15-setup.md).*
