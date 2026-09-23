# Changelog

What changed in this framework, newest first — so an adopter can tell what to re-check in their own
repo. One entry per published phase of work. (Started 2026-09-23; earlier history is in `git log`.)

## 2026-09-23 — navigation: every cross-reference points where it says

- **New: `scripts/check-guide-links.py`, run in CI.** It checks four things a renumbering breaks:
  relative links resolve; a numbered link label matches its target (`[14](19-sharing.md)` was
  wrong); chapter files named in plain text exist (templates cited `09-permissions.md`,
  `10-mcp.md`, `13-setup.md`); and the "Next:" reading order holds, including case studies.
- **Fixed, all 21 problems it found:** 5 mislabelled links, 6 stale chapter names in templates,
  and 10 broken or missing "Next:" links. The case-study chain now reads 03 → 03a → 03b → 04,
  05 → 05a → 05b → 06, and 17 → 17a → 17b → 18.
- **Fixed by hand:**
  - three "§ 14" references meaning monitoring (now 17);
  - two bare `guide/NN` references;
  - the 03a/05a descriptions attached to the 03b/05b links;
  - a sentence in § 12 cut in half by another bullet;
  - the README's Linux status.

  The example catalogue now explains its ID gaps.

## 2026-09-23 — `fleet-container-check`: every stack, every registry, no silent errors

- **Fixed: every non-ghcr image was looked up on Docker Hub,** so `lscr.io` and `quay.io` images
  failed. The check now speaks the standard OCI anonymous-token flow to any registry (verified live
  against Docker Hub, ghcr.io, quay.io and lscr.io).
- **Fixed: a failed check reported as current.** Errors now exit 2, and `fleet-update-check` reports
  them instead of treating exit 2 as "no updates".
- **New: `fleet-composes.conf`.** Registered stacks are checked, and discovered-but-unregistered ones
  are reported. The hard-coded `~/selfhost/compose.yaml` default is gone.
- **New: variant-aware tags** (`5.13-apache`, `mysql-v2.19.0`), **floating tags** not reported as
  behind, and `# pin: <reason>` for intentional pins.
- **Docs:** the sidecar table gains the dangerous case, an app that restarted **by itself**, which
  leaves a namespace-sharing sidecar dark with no error anywhere.

## 2026-09-23 — `fleet-update-check`: coverage you can trust

- **Fixed: gaps reported as "current".**
  - A declared method with no checker (gem, cargo, pipuser …) is now reported as **NO CHECKER**
    every run.
  - `not-audited` is reported as NOT AUDITED, instead of being treated as a method name.
  - New: `?name` records a known gap.
- **Fixed: brew was never discovered on macOS.** Its count came from padded `wc -l` output.
- **Fixed: every Windows node read as unreachable.** The probe was `ssh … true`, and a Windows SSH
  shell has no `true`. It is now `echo ok`.
- **Fixed: an offline node sent a weekly error.** It is now noted and skipped, since a laptop
  asleep is not an error.
- **Fixed: malformed rows in `fleet-nodes.conf` were silently skipped.** They are reported.
- **New: `winget` method.** Detection works over SSH (cached index; the digest says so). The parser
  follows the table's structure; a first version counted a progress-spinner line as a package.
- **New: `fleet-binaries.conf`.** Executables no package manager owns are discovered and
  reconciled: UNREGISTERED, MISSING, and `upstream` rows version-checked against GitHub.
- **New: `fleet-update-decisions.conf`.** Decisions with a reason and a revisit date; overdue ones
  are flagged.
- **Tests:** 35 in the suite (9 new for this tool).

## 2026-09-23 — Gatus alerts in your subject format: `gatus-mail-relay`

- **New: `skeleton/monitoring/gatus-mail-relay`** and a hardened systemd unit. Gatus hard-codes its
  email subject, so its `custom` provider now POSTs each alert to this localhost relay, which builds
  the subject with `fleet-mail` (`[Fleet/Alert/Apps/api] api: triggered`) and sends it.
  - The endpoint name is repeated after the bracket, because a mail client may thread while
    ignoring a leading `[tag]`.
  - A `/` or bracket in a group or name no longer costs an alert.
  - The self-test runs in CI.
- **Changed: `gatus-config.yaml.template` alerts through the relay by default.** Gatus's own
  `email` provider remains as a commented alternative. `gatus.env.template` gains `MAIL_FROM`,
  `MAIL_TO` and an optional `SUBJECT_TAG`. The drop-in is only for the alternative. The
  `Metrics/dashboards` endpoint is renamed `Dashboards`.
- **Docs:** install order (relay first, so no alert finds it absent), and how to watch the relay
  from another node.

## 2026-09-23 — `fleet-local-check`: three states, and two new check types

- **Changed: every check has three outcomes, OK, FAIL or UNKNOWN,** as guide § 17 teaches.
  - A timeout or an unreadable mount table is UNKNOWN. It keeps the previous state and sends no
    mail. Four in a row become a FAIL worded as blindness.
  - Mount checks retry before concluding.
  - `command` checks can exit 3 to mean "could not determine" (the Nagios convention).
  - Your state file is migrated automatically.
- **Fixed:** a malformed config line was silently skipped. It is now reported as a failing check.
- **New: `hash`** (an installed file must match its reference copy) and **`synclag`** (the last
  successful fetch must be recent). These watch what a config manager doesn't: a script installed
  by hand on a node it doesn't manage, and a sync that has quietly stopped.
- **Tests:** 26, including in-process probe classification; 7 mutants caught.

## 2026-09-23 — rules, presets and practices agree with the guide

**If you seeded a repo from `CLAUDE.md.template` or `AGENTS.md.template`, compare your Rules section
with the new template.** Rule numbers changed.

- **Changed: the rules templates now number rules 1–18 exactly as `guide/03-governance-rules.md`
  does, with the same titles.** They had 12 rules, numbered differently: "Rule 7" meant symmetry
  in the guide but deferral in the template. The six missing principles (updates, one plan/one
  owner, postmortems, the design pass, stateful services, exposure, evidence-or-doubt) are added.
  Your own rules start at 19. CI (`scripts/check-rules-templates.py`) keeps them in sync.
- **Changed: principle 1 covers writes outside the repo.** Any overwrite there counts, and the AI
  CLI's live settings change only through the config manager.
- **Fixed: permission presets that were less safe than described.**
  - `cautious` ("reads only") allowed `find` (`-delete`).
  - `standard` and `trusting` allowed `sed` and `awk` (which write), and `trusting` allowed
    `git branch` (`-D`).
  - `standard` allowed unscoped `Edit`.
  - `/tmp/*` meant `~/.claude/tmp/*`. It is now `//tmp/**`.
  - `.env` was denied only at the repo root.
- **Fixed:** the design-practice rule D8 now mirrors the postmortem rule R8 (no back-dated design
  for work already under way). The template-version stamps now match the rules' revision logs
  (1.1, 1.2). The concepts diagram names the real design templates. `AGENTS.md` counts were
  corrected, as were two wrong rule citations (§ 02, § 14). A sentence in § 10 was cut in half by
  another paragraph.

## 2026-09-23 — setup works for a new user

- **Fixed: `bootstrap.sh` was not executable** (`./bootstrap.sh` gave *Permission denied*).
- **Fixed: `bootstrap.sh` could damage or skip an existing repo.**
  - It re-cloned over a clone you had made by hand, and aborted.
  - It never seeded with `--no-create-repo`.
  - It **overwrote** an existing repo's `CLAUDE.md`, `PROJECTS.md` and the other seeded files.
  - Now it uses an existing clone as-is (`--no-create-repo --dir <clone>`), refuses a non-empty
    non-git directory, **never overwrites a file**, and lists what it kept.
  - It no longer falls back to your git *display name* as your username.
- **Changed: `bootstrap.sh` also seeds the design + postmortem practice** and the onboarding
  project's own design doc and postmortem draft, as principles 14–15 require.
- **Docs: `--yes` answers yes to installs and repo creation.** The header used to claim those
  always ask. Guide 18's Tiers 1 and 2 now describe what actually ships:
  - Tier 1 is by hand, since no `.chezmoi.toml.tmpl` ships.
  - Tier 2 creates and seeds your repo. It does not set up SSH keys or the mesh.
- **Fixed: `install-tooling.sh.template`.** Its default role never matched its own `case`, and it
  reinstalled any tool whose command differs from its package (`ripgrep` → `rg`). Use
  `package:command`.
- **Docs fixes:**
  - The monitoring README now creates `/etc/gatus` and shows a minimal, hardened `gatus.service`.
  - `platforms/linux.md` and the monitoring README no longer claim systemd units ship.
  - The README no longer points at a dashboard starter that does not exist.
  - `enable-repo-index.sh` no longer claims to commit.

## 2026-09-23 — corrections: six things this guide taught that were wrong

No code behaviour changes. If you followed any of these, re-check your setup:

- **Gatus's subject** (E16, monitoring README, § 17): it is `<group>/<name>: Alert triggered`, with no
  brackets, not `[<group>/<name>] …`. New advice: route it through a localhost relay into your own
  mailer, or add a second filter. Test in the client you read, because clients may group alerts that
  differ only inside the leading `[tag]`.
- **Subnet-router "hot standby"** (E12): under oldest-wins primary selection, the old gateway takes
  the route back at the first re-election, silently. Retire its route instead, and assert the role.
- **Automation-runtime deploys** (C6): a public-API `PUT` on an active workflow *publishes*. Only a
  database edit or a restart leaves the pointer alone. New traps: settings aren't versioned, and the
  stored timestamp format matters.
- **Windows updates** (windows.md, E16, `fleet-update-check`): *detecting* works over SSH. Only
  *installing* needs elevation.
- **Windows Update pinned to manual** (windows.md): the OS repairs this. Verify the scripts' own
  result, check the live values on a schedule, and set no-auto-restart-with-logged-on-users.
- **"`mount` checks do no I/O, reliable everywhere"** (monitoring README, `fleet-local-check`): false.
  The mount point and table both touch the network, so a failure can mean *could not determine*.

## 2026-09-23 — the monitoring tools' alert mail works again

**If you installed `skeleton/monitoring/`, re-run `bootstrap-monitoring.sh` (or copy the four tools),
then send yourself a test:** `fleet-mail --kind Report --source Test --text "hello" --body "it works"`.

- **Fixed: every real alert from `fleet-local-check`, `fleet-install-audit` and `fleet-update-check`
  crashed.** An undefined name (`SUBJECT_PREFIX`) sat on the send line. `--dry-run` never reaches
  that line, so the quick start could not show it. Two of the tools saved their state before the
  crash, so those alerts were lost for good.
- **Changed: `fleet-mail` is the one owner of the subject format.**
  - New: `--kind Alert|Report|Digest --source <Source> --text "…"`.
  - A pre-built `--subject` must already match `[<Tag>/…] text`, or it is **refused** (exit 2).
    `fleet-mail -s "test"`-style calls no longer send; use `--kind/--source/--text`.
  - New: `--dry-run` (prints the subject and body; needs no credentials).
  - Your tag: `SUBJECT_TAG` in `mail.env` or `$FLEET_SUBJECT_TAG`; the default is `Fleet`. The old
    `FLEET_SUBJECT_PREFIX` form is still accepted.
  - Usage and config errors now exit 2, as documented.
- **Changed: alerts are no longer lost.**
  - `fleet-local-check` now also mails when a check is failing on its **first** run (a new check,
    or a lost state file).
  - `fleet-local-check` and `fleet-install-audit` save state only **after** the email is sent. A
    failed send exits 3, and the next run retries.
- **Changed: `fleet-update-check`'s default mailer** is `~/.local/bin/fleet-mail`, like the others.
- **New: `skeleton/monitoring/tests/`** (17 tests, stdlib only), which drive the real send path
  through a fake mailer. **New: CI `tools` workflow:** `pyflakes`, the tests, and `bash -n`.
- **Docs:** guide § 17 gains "Syntax-checked is not correct" and "build every subject in one place".

## 2026-09-23 — the leak guard works again, on every platform

**If you copied `scripts/grep-guard.sh` or the pre-commit hook, replace both and run
`scripts/grep-guard.sh --self-test`.**

- **Fixed: on macOS the guard caught only home paths.** `git grep -E` there ignores `\b`, and most
  patterns used it, so private IPs, emails and secret assignments all passed. The patterns are now
  portable POSIX ERE with no `\b`.
- **Fixed:** the `10.x.x.x` pattern could never match on any platform. A scan *error* was treated as
  clean; it now fails closed (exit 2). The hook now scans the **index** (`--staged`), so a leak that
  was staged and then edited away can no longer slip through. `pre-commit.hook` is now executable,
  so the symlink install works.
- **New: `--self-test`.** It plants one leak of each shape, **one per file**, and proves each is
  caught, in both modes. The hook and CI run it before scanning, so a guard that stops matching
  blocks the commit or build instead of reporting clean.
- **New: a local list of your names** (`.grep-guard.local`, gitignored; or `$GREP_GUARD_LOCAL`). It
  is mandatory once you set `git config --local grepguard.requireLocal true`.
- **New patterns:** the 172.16/12 range, the CGNAT/tailnet range (narrowed to 100.64/10), tailnet
  hostnames, unquoted `*_KEY=`-style values, and common token prefixes.
- **Docs:** [`guide/19-sharing.md`](guide/19-sharing.md) now lists what the guard actually checks,
  including what it does **not** detect (arbitrary high-entropy strings).
