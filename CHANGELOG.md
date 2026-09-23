# Changelog

What changed in this framework, newest first — so an adopter can tell what to re-check in their own
repo. One entry per published phase of work. (Started 2026-09-23; earlier history is in `git log`.)

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
