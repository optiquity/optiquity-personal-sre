# Changelog

What changed in this framework, newest first — so an adopter can tell what to re-check in their own
repo. One entry per published phase of work. (Started 2026-09-23; earlier history is in `git log`.)

## 2026-09-25 — measuring a link honestly; the pre-flight question (design templates 1.4)

- **New in § 08: "Measuring a link honestly".** Test each layer on its own: the pure link memory to
  memory; writes flushed and larger than any write cache; reads warm and cold, labelled. A worked
  case: one link measured at about 85%, 40% and 13% of line rate, and only the first was the link.
  ⚠ A comparison is only valid between the same test.
- **Design templates 1.4:** testing asks, before an irreversible step, what must be proven healthy
  first, and whether that includes the parts you are not changing. **Re-check your own templates**
  if you copied them earlier.

## 2026-09-25 — tooling traps: command names, side-effect agents, file modes, silent checks

- **New in § 07: "Naming a new command".** A `PATH` collision runs the wrong program without an
  error. Check `PATH` on every node, the package registries, and the wrapped tool's former name.
- **New in § 07: "A command that installs a service".** Some CLIs install a background agent from
  routine commands such as `start` or `pair`; beside your own copy, that makes two instances. Fix the
  reach: a guard, a wrapper, and a check that exactly one instance runs.
- **§ 05:** a file-sync service is not a config manager (it can keep the content and drop the
  permissions), and a captured script must declare its mode in the source.
- **New in § 17: "Empty output is not a clean result".** A check that passes by printing nothing must
  prove it ran. Four shell traps that fake a clean result: `xargs` and shell functions, zsh's
  empty-glob abort, BSD `find -size` units, and zsh not word-splitting a variable. Plus: an in-place
  edit resets a file's creation time.
- **`platforms/macos.md`:** list LaunchAgents before and after running a tool's setup, start or pair
  commands.

## 2026-09-24 — discovery folders you choose

- **`fleet-nodes.conf` takes an optional fifth column: extra discovery folders** for that node
  (comma list, `~/` resolved in the node's home), searched along with `/usr/local/bin`, plus `/opt`
  on Linux. A program you placed by hand in, say, `/usr/local/lib/<you>` can now be reported as
  unregistered instead of never seen.
  - ⚠ The template carries the warning with it: add only a folder that really holds hand-placed
    programs. One full of managed scripts and shims reported 35 of 36 entries as unregistered.
  - An empty or extra field is reported as malformed, as before.
- **Fixed: Linux discovery split paths that contain a space.** It now reads `find`'s output line by
  line.
- 1 new test running the real probes; 10 planted defects, each caught at its own assertion.
- § 16 and the monitoring README describe the new column.

## 2026-09-24 — secrets as files, failures in the browser, asking the owner, status that decays

- **§ 06, the daemon recipe now leads with `LoadCredential` + `DynamicUser`.** The secret is
  read-only, there is no second copy, and the service owns no files (systemd 247+). `EnvironmentFile`
  is the fallback. The worked example now points at the relay unit that already did this.
- **New in § 06: "A secret a container reads".** A read-only file under `/run/secrets` or compose
  `secrets:`, not `environment:`, which `docker inspect` shows. Use the image's `*_FILE` variables.
  The honest scope: it is not access control.
- **Aligned:**
  - E16, `platforms/linux.md`, C6 and C7 now teach secrets as files or credentials;
  - E16's sample config and failure-email section, and the monitoring README, now describe the
    relay default, not Gatus's built-in email.
- **New in E17:**
  - "A form that breaks in the browser sends your servers nothing": zero messages is ambiguous; use
    a scheduled headless submission (*labelled: designed, not yet built in the fleet it came
    from*).
  - "Abuse on a public form: measure before you fix": 0 honeypot catches in 6,219 submissions
    ruled out every page-side fix.
- **New in § 02: "When you need the owner, ask; don't report".** Put the one required action first,
  on its own.
- **New in § 04: "Status decays".** It covers `verified <date> (<command>)` stamps, re-measuring
  before acting, and a scheduled re-check. Rule 18 in § 03 now points to it.

## 2026-09-24 — config drift: generated settings, a wedged apply, code that didn't reload (templates 1.3)

- **New in § 17: "Settings the platform owns".**
  - A generated file is changed at its source, not by hand.
  - Change the setting, not the task that delivers it.
  - Some settings live only in the platform's database.
  - Keep a registry read *live*. *Labelled: designed, not yet built in the fleet it came from.*
  - A script that changes a setting reads the result back.
- **Corrected in § 05:** an unattended apply that meets a changed file doesn't only "wait forever".
  It can also **error on every run**, applying nothing after that file (about 960 runs over 20 days,
  in one fleet). Either way one file stops sync for all. New in the same chapter:
  - app-owned files are seeded once (`create_`), with the diff as the tell;
  - check `chezmoi managed` before deleting on a managed node;
  - read a stalled queue entry by entry, because a lost execute bit shows only as `old mode` /
    `new mode` header lines.
- **New in § 09:** the mirror of "recreating is not restarting". `compose up -d` with only a mounted
  file changed reports "Running" and reloads nothing. Restart, and verify from a line only the new
  version prints.
- **`synclag` can name the sync job** (a launchd label or a systemd unit) and then also checks
  that the job's last run succeeded: a fresh fetch followed by a failed apply used to pass.
  - A unit systemd doesn't know reports "success, exit 0", so loading is checked first (measured
    on systemd 257).
  - It trusts systemd's own verdict, which honours `SuccessExitStatus=`.

  1 new test; 11 planted defects, each caught at its own assertion. One survived at first, and
  that exposed the raw exit-code comparison as wrong.
- **`platforms/windows.md`:** its TODO is filled. Define scheduled tasks from a tracked script that
  reads its registration back, because task settings live only in the scheduler.
- **Design templates 1.2 → 1.3:** Durability asks *"is the file you are changing generated?"*.
- **Corrected in `platforms/windows.md`:** Group Policy is Pro and above only (Home has none), and the
  repair service is the likely cause of a reverted update pin, not a proven one.

## 2026-09-24 — automation runtime: time limits, a busy guard, a queue pipeline

- **New in C6: "Time limits: measure what a timeout does".** It explains how to measure a
  timeout with a throwaway run.
  - What one runtime was measured doing (n8n 2.21.7, regular mode): the run is marked canceled at
    the limit and later steps never run, but **the remote work keeps running**. Its documentation
    says the opposite.
  - So: alert on stopped statuses; assert the global cap; re-measure after upgrades.
- **New in § 14: "Serialising a pipeline without lock files".** A pipeline is busy while its fence
  holds anything, or while a running process names its in-progress path. The needle must not
  match the guard itself, and the self-match is tested from a shell inside a shell. It fails
  closed, and overlaps are detected. *Labelled: designed and deployed, not yet proven on a live
  job.*
- **New example C20: a queue pipeline.** It covers visible stages; one-move hand-offs on one
  filesystem; names fixed once on pickup; filing that never overwrites. The alerts are STALLED
  while idle, STUCK (no progress), and any failure, one check per workflow. It also covers the
  measurement traps: ctime rather than mtime, the server's clock, zero found = UNKNOWN, and a
  blind check = FAIL.
- **§ 17:** a check whose source has gone is blind, and blind is a failure, not "unknown".

## 2026-09-23 — prove each test: one planted defect per rule

- **New in § 17: "Prove each test: one planted defect per rule".** It covers:
  - the method, which needs no tool: list the rules, plant the smallest faithful defect, and
    require that rule's test to fail *at its own assertion*, then restore;
  - a surviving defect is a finding about the test;
  - the four traps, each met in practice: a bytecode cache running the previous mutant; discarded
    stderr hiding a crash; a pass that ran the wrong branch; tests that could not fail.
- § 02's "restate the end state" section now points to it for step 5, *it verifies*. The design
  templates have asked for this since 1.2.

## 2026-09-23 — what your config manager never deploys

- **New in § 16: "A fix that reaches four nodes out of five looks done".** It covers two kinds of
  file that fall behind the repo silently:
  - copies installed by hand on the node the config manager doesn't manage;
  - files it stages but cannot install, because the live path needs root.

  The remedy for both: compare the file that runs with the repo copy by checksum, and register
  hand-placed programs so discovery reports new ones. § 17 points to it from reconciliation.
- **Fixed: the `hash` check couldn't do the first case, which its own example claimed.** It read
  both files on the machine it ran on. On a node the config manager doesn't manage, the installed
  file and the repo copy are on different machines, so the example could not pass anywhere.
  - The installed side may now be `host:/path`, read over SSH.
  - An unreachable node is UNKNOWN; a missing or different file is FAIL.
  - A one-letter "host" is a drive letter, so it stays local.

  2 new tests; 9 planted defects, each caught by its own assertion.
- **Re-check:** if you copied the `hash | gateway relay | …` example, add the `host:` prefix. As
  written, it could never have passed.

## 2026-09-23 — build what was asked (design templates 1.2)

- **New in § 02: "Before building: restate the end state, and wait for every yes".** Restate the
  result the way the owner will check it (a tree, a table, a sample output). A question that
  wasn't answered is still open, so build nothing that depends on it. Add nothing that wasn't
  asked for; propose it and wait. It comes with the case that taught it: a day's work reverted.
- **Design templates 1.1 → 1.2** (short and long). Two postmortem lessons became standing prompts:
  - §1 now asks for the end state as the owner will check it;
  - testing asks for the planted defect that proves each test can fail;
  - "Open questions" changed meaning. They used to be *carried into the work*; now an open point
    **blocks** the work that depends on it.

  **Re-check:** designs you write from now on should use 1.2. Existing designs keep the version
  they were written against. That is what the field is for.

## 2026-09-23 — what the earlier corrections missed

The corrections below finish two changes that earlier entries only partly made. No code behaviour
changes. If you followed either one, re-check your setup:

- **Subnet-router "hot standby"** (E12, example catalogue): the earlier fix corrected E12's
  section 3 but left the title, intro, rationale and checklist, and the catalogue entry, still
  recommending a standby. All of them now say to retire the old host's route. Section 3 also had the
  cutover backwards. Under oldest-wins the new node cannot become primary while the old one
  advertises, so you withdraw the old route first, then verify.
- **Network-mount keeper** (B5): it read inside the share to test health and unmounted a "stale"
  mount automatically. Both are wrong. The first can hang from a scheduled job, and the second cannot
  tell *broken* from *busy*, so it kills in-flight writes. The keeper is now passive: it checks the
  mount table, mounts what is missing, and never touches a mount that is present. Detecting a hung
  mount is left to monitoring, where a timeout means unknown.
- **"A mount check does no I/O"** (E16, `platforms/macos.md`): now matches the monitoring README. The
  check never reads inside the share, but checking the mount point and the mount table can still
  block, so a check that cannot answer is unknown, not unmounted.
- **Two smaller fixes:** § 11's diagram labelled CLI permissions `[09]` (it is chapter 10), and a
  bullet in § 19's exclusion list was cut in half by another bullet.

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
