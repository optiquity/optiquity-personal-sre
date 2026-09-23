# Changelog

What changed in this framework, newest first — so an adopter can tell what to re-check in their own
repo. One entry per published phase of work. (Started 2026-09-23; earlier history is in `git log`.)

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
