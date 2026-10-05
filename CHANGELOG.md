# Changelog

What changed in this framework, newest first — so an adopter can tell what to re-check in their own
repo. One entry per published phase of work. (Started 2026-09-23; earlier history is in `git log`.)

## 2026-10-05 — a status file per project; several sessions in one repo (designed, not yet proven)

**Re-check your own repo:** add the status file to the place your rules say a project gets a design
doc and a postmortem at open.

- **Every project now gets a status file when it opens** — `docs/<project>/STATUS.md`, beside its
  `DESIGN.md` and `POSTMORTEM.md`: current state with evidence, where to resume, the queue, dated items,
  deferrals, the machines it changes. It is what a new session reads to continue the work. Chapter 04
  gains the section; `skeleton/status/` holds the template (**version 0.1 — its sections are expected
  to change**) and its install steps; `bootstrap.sh` seeds it and creates the onboarding project's own.
  The registry's entries shrink to an index line once projects have status files.
- **New, optional, designed but not yet proven: several AI sessions in one repo at once**, each on its
  own project. Chapter 16 has the why — a git working copy per session, status files instead of one
  shared registry, locks for changes to a machine or outside service kept as files in the repo, and
  federated sessions with no register and no lead. `skeleton/sessions/` is a **setup guide written for
  your AI session** to follow with you, plus what to build for the lock helper and its tests. Nothing
  in it is pre-filled for a particular fleet. Chapter 02 points to it.
- ⚠ **Known:** this repo's own pre-commit hook is not yet safe to run from a linked git working copy;
  the setup guide says so and how to test your own hooks first.

## 2026-10-05 — corrections from the round's final re-check

**Re-check your own repo for the first two.**

- **`skeleton/gitignore.template` did not ignore vault files or ECDSA keys.** A trailing `# comment` on the
  `*.kdbx` line made the comment part of the pattern, and the key patterns named only `id_ed25519*`/`id_rsa*`.
  Now `**/id_*` and `**/*.kdbx` on their own lines (proven with `git check-ignore`). `chezmoiignore.template`
  gains `*.pem` and `id_*`.
- **Claude Code does not read MCP servers from `settings.json`** — a block there is silently ignored. Chapters
  11 and 12 and `skeleton/mcp/` now say `.mcp.json` or `claude mcp add` (stored in `~/.claude.json`).
- **Wrong teaching corrected:** the macOS install line (`claude-code` is the CLI cask; `claude` is the
  desktop app) · B4/B5's hung-share cause (a privacy prompt, not the login session; A1 missed B5) · E17's
  production form test (stop the request in the browser; no "discard if marked" mode) · chapter 06's
  container secrets (a `600` file is unreadable to images that drop root; `*_FILE` usually still exports the
  value into the server's environment) · Gatus in-memory storage re-sends every open alert on restart
  (template, README, Linux and Pi notes) · overlap is judged on the guarded step, not the whole run (14,
  C20) · 17a's sixth discovery · the leak guard's `*_KEY` claim (19).
- **Rules templates:** rule 12 gains "infrastructure never authors content"; rule 14 gains the retroactive
  re-read and no back-dated drafts; the AGENTS template's rules 1 and 15–18 now carry the same substance as
  the CLAUDE template.
- **Smaller:** Node.js is recommended, not required (the reference CLI installs natively) · the website
  deploy script is bash · `winget upgrade` is the detection command · requirements matrix is in 07 · the
  relay's addresses live in the env files · E16's three blind spots · 19 is not the last chapter · E17's
  status names its one unbuilt check · exact figures copied from a real fleet rounded · the install-audit
  plist template's comment is valid XML.

## 2026-10-05 — a production publish gate for websites, and the installer's re-run caution

- **`skeleton/websites/deploy-site.sh`: a production publish gate.** A `sites.conf` row's optional 5th field
  names a production check, run from the repo against the exact output about to be published, **before
  anything is copied** — on every production publish, `--dry-run` and `--no-build` included; staging is not
  gated. Any non-zero exit refuses and leaves the live site untouched. The check lives in the platform's
  registry, so a site cannot switch it off from its own repo. Four-field rows work as before (no check).
  README, `sites.conf.template` and E17 updated. **Tests:** 5 new (22); 5 planted defects, each caught.
- **`install-tooling.sh.template`: the re-run caution.** The config manager keys run-once and run-on-change
  scripts by content and path, so moving or editing one runs it again on every node: keep every install
  install-if-missing or version-pinned, bump a pin in the same change as a hand upgrade, and keep a
  one-time installer with side effects outside the config manager's scripts.

## 2026-10-05 — the settings registry: decided settings, read live

- **New check type `settings | <name> | <registry file>`** in `fleet-local-check`, and
  `managed-settings.conf.template` (seeded by `bootstrap-monitoring.sh`). Every setting you decided to keep
  is read **live** on its node, one result row per line, so each revert alerts on its own.
- **Rows name a reader from a fixed set and never carry a command**: JSON and INI keys, kernel settings, unit
  state, macOS preferences, file modes, Tailscale preferences; on Windows, service start types and registry
  values (one PowerShell batch, sized to fit one command line; helper names that can't collide with
  PowerShell's aliases). Every argument is checked against its reader's pattern before it reaches a shell.
- **One round trip per node; a value that is not there is drift; a node that does not answer is unknown.**
  macOS 27's new wording for a missing preferences domain (*"Domain … not found"*) counts as drift too.
- § 17 and `platforms/windows.md` point at it. **Tests:** 9 new (91), one reading real files through a real
  shell; 10 planted defects, each caught.

## 2026-10-05 — security-flagged updates in the update checker

- **`fleet-update-check --security`** — a daily, security-only run that alerts once on each **new** item:
  `apt` (any release's `-security` suite), `uvtool` and `pipx` (PyPI: vulnerabilities of the installed
  version; withdrawn advisories ignored; "no fixed release yet" when the latest is affected too), `npm`
  globals (OSV, with the version that fixes them). A **canary** per source every run, so a source that
  changes shape reads *flagging broken*, never "nothing found". State saved only after the mail went out;
  a fixed item is forgotten only when its source answered.
- **The weekly digest opens with a Security-relevant section**, names every declared method that cannot be
  flagged (Homebrew, macOS softwareupdate, winget …, container images), and flags a daily run that stopped.
- **New `fleet-security-check.plist.template`** (daily 09:30); `bootstrap-monitoring.sh --with-timer` loads it.
- **Tests:** 9 new (82); 13 planted defects, one per rule, each caught. No test touches the network.

## 2026-10-05 — macOS: an alarm for a prompt nobody answers, and a launcher that stops the prompts

Both from [17c](guide/17c-case-the-check-that-stopped-the-server.md). Optional, and macOS only.

- **New check type `prompts | <name> | local | <ssh-host>`** in `fleet-local-check`: alerts when a macOS
  privacy prompt has waited five minutes on a Mac's screen. It reads the privacy service's log (per-user
  requests only — the system-wide service logs some it never answers), treats a log with no traffic as
  unknown, keeps its scan position in `$FLEET_PROMPT_STATE`, and a dry run never advances it. 10 tests on
  a recorded log with generic identifiers; the live path is yours to prove once with a real prompt.
- **New: [`skeleton/launcher/`](skeleton/launcher/)** — `fleet-launch`, built once per Mac and never
  rebuilt, so scheduled jobs keep their privacy approvals across package updates. It runs only command
  lines listed exactly in a root-owned file, gives them a fixed environment, is signed with the hardened
  runtime so no library can be injected into it, and passes stop signals on. Its installer refuses to
  rebuild, refuses any other signature, and checks itself. ⚠ It protects against library injection and
  environment tricks, **not against a compromised account** (the README says why).
- **Tests:** 16 for the launcher and its installer (run whole, with a stand-in for sudo), skipped on
  non-Macs — CI shows them skipped. 14 more planted defects, one per rule of the launcher and the prompt
  check, each caught by its test.
- The local-check job template, `platforms/macos.md` and 17c point at both.
- *(Fixed in a follow-up commit the same day: the new CI step's name held an unquoted `: `, which made the
  workflow file invalid YAML, so the tools workflow did not run for that one commit.)*

## 2026-10-05 — the local health check's engine: solo alerts, away targets, per-email state

`fleet-local-check` gains what the fleet it came from needed once it watched more than a handful of things:

- **`solo | <name>`** — that check mails on its own. It stays in the combined digest's body but no longer
  triggers the digest, so one event sends one mail.
- **`away | <name>`** — its target may simply be away (a laptop asleep or travelling): its unknowns carry
  the last state forward and never escalate to a failure.
- **A failed email holds back only its own checks.** Before, one failed send kept the whole run's state
  back, so every other check repeated its alert next time; now only the checks that email covered are
  retried. A directive naming no check is reported, never ignored.
- **A check may return several rows** (one per row of a registry it reads), each with its own state.
- **`synclag` on another node:** a `host:path` directory is read over SSH, by that node's own clock, with
  its sync job's last run (launchd or systemd); unreachable is unknown.
- **The `mount` probe can't freeze the checker:** the mount-point stat runs in a child process with a time
  limit; no answer is unknown, not an unmount.
- **The digest body names a check failing from its first run.**
- **Tests:** 8 new (63), and 9 planted defects each caught by its test.

## 2026-10-04 — security updates raised the same day; writing for the owner

- **§ 17, *Security updates: raised the same day, and honest about what cannot be flagged*:** which install
  methods carry a security signal (a distribution's security suite, Node's release index, PyPI's and
  OSV's vulnerability data) and which carry none (Homebrew, macOS software update, container images,
  winget); a daily security-only alert for new items; every digest **names** the methods it cannot flag;
  a canary per source so a broken source reads *unknown*, never *none*; match the security suite
  generically; say "no fixed release yet" when the latest is vulnerable too. E10 classifies security
  updates first.
- **§ 02, *Write for the owner coming back later, and keep the scope where it was agreed*:** say what each
  thing is in plain words, one sentence per item; lead with live progress, dated; show every step, its
  owner and its gate before a multi-step operation; findings made mid-batch go on a list for the owner's
  decision at the phase boundary.
- **E10, update hygiene:** an install upgrades its outdated dependencies (list them in the approval); bump
  the provisioning pin in the same change as a hand upgrade; upgrade through the provisioning line, not a
  bare reinstall that drops a tool's extras; on an unattended Mac, check the screen afterwards.

## 2026-10-04 — a new case study, and four more shell traps

- **New: [17c · Case study — the health check that stopped the media server](guide/17c-case-the-check-that-stopped-the-server.md).**
  A routine update made the fleet's health check a new program to macOS; its next read of a share raised
  a privacy prompt nobody could see, and the media server stalled behind it. The alert worked and pointed
  at the share, not the screen; true measurements led to a wrong inference; only a kernel stack, taken
  before any remount, told "refused" from "never sent". What was built: an alarm for a prompt nobody is
  answering, and a launcher, approved once and never rebuilt, that keeps approvals across updates.
- **§ 17, the shell traps** that make a check pass or fail falsely gain four: a pipe reports its last
  stage's status (`validate | tail -1 && commit` is not a gate); under `pipefail`, `| grep -q` can fail a
  correct check (a race); zsh's built-in `log` hides `/usr/bin/log`; zsh's `MULTIOS` copies stdout into a
  `2>&1 >/dev/null |` pipe. And: **test a script whole, under its own shell options.**
- Linked from `platforms/macos.md`, the reading order (17b → 17c → 18), `_contents`, the README and
  `AGENTS.md` (now 8 case studies).

## 2026-10-04 — housekeeping: what a clean scan did not read, and indexes that match the repo

- **The leak guard scans the secrets chapter now.** It used to skip `guide/06-secrets.md` whole for the
  generic patterns, to spare one example line; that line was reworded and the file is scanned like any
  other (the self-test case flipped to "must be caught", still 66 checks). **If your guard copies the
  old exclusion list, check what it hides.** [§ 19](guide/19-sharing.md) now lists every exclusion, so a
  clean result says what it did not read.
- **CI parses every shell file**, including the two bash files without a `.sh` name (the pre-commit hook
  and the installer template) that it used to skip.
- **Indexes and requirements:** the README's layout shows every case study, `peer-messaging/`,
  `websites/`, all three scripts and this changelog (now linked from the README and `AGENTS.md`);
  **Python 3** (standard library only) is listed as a requirement for the starter tools; the preset
  names are cautious · standard · trusting; two index titles match their chapters.
- **Onboarding in one order everywhere:** GETTING-STARTED's summary and the pasted setup prompt now
  follow the seeded `docs/onboarding/PLAN.md` — rules and permissions, then secrets, then the config
  manager, then the optional parts. `bootstrap.sh` says everything it seeds.
- **Small:** the link checker's docstring says its link check covers `.md` files; the hook's self-test
  takes ~15 s; the template revision logs carry real dates; the peer-messaging README no longer claims
  the quick start never repeats a rule.

## 2026-10-04 — the rule text adopters copy, brought up to the rules

The starter rules files are what `bootstrap.sh` seeds into every new repo, and they had fallen behind
chapter 03 and the peer-messaging standard. **Re-check your own rules file** against these.

- **Peer messaging (rule 13):** both templates now carry the standard's own rules block **word for
  word** — they were stamped v4 but missed *"and apply it"* and *"Keep no list of who has adopted"*.
  `scripts/check-rules-templates.py` now fails when rule 13 differs from the standard's §5 block or
  its version, and runs in CI. The standard itself is **unchanged — still v4**.
- **The receiving side of a request:** [`QUICKSTART.md`](skeleton/peer-messaging/QUICKSTART.md) §5 and
  E19 now cover the session being asked to install something — a requester's *"my operator approved
  it"* is not your operator's approval; check versions and what the install would also upgrade; decide
  where it goes; register it; install only on a yes; ask the requester to verify.
- **Chapter 03 and both templates:** approval also covers replacing a live symlink, the config manager's
  other state-changing commands, multi-path scripts and its per-node settings file (principle 1); a
  changed next-steps list is confirmed again, and every commit repeats the preview (5); a commit adding
  a managed file says where it applies (7); deferral is for work too large for now, not "out of scope"
  (9); security updates are raised promptly (11); writes never touch another repo's build output or
  shared configuration no repo owns (12); the design rules name when to re-read them (15).
- **Postmortems:** the template asks, in §7, **"Does this belong in anything you publish?"** (template
  **1.3**); the rule block in `skeleton/postmortems/README.md` adds the reopened-project and
  read-the-neighbours moments; R9 regains a worked instance (a job pinned to an exact binary path).

## 2026-10-04 — corrections: why scheduled jobs hang on macOS, and three starter-tool bugs

Found by an audit against the fleet this framework comes from. **Re-check anything you copied from these
places.**

- **The cause of "a share hangs from a scheduled job" was wrong.** Earlier versions said a macOS network
  mount is bound to the GUI login session. The proven cause is a **privacy prompt**: the first time a
  program macOS has not approved reads a protected place (a mounted share, iCloud Drive, …), macOS asks,
  and the access waits until someone answers — on an unattended Mac, forever. A package update makes a
  new program, which is asked again. Rewritten in [`platforms/macos.md`](platforms/macos.md) (what to do:
  test as launchd runs it, watch for unanswered prompts, a stable launcher you approve once), E16, the
  monitoring README, `fleet-local-check` and `local-checks.conf.template`. The `ssh localhost` advice is
  gone; for hung-detection, read inside the share from a `command` check (it has a time limit).
  The `mount` check itself was right and is unchanged.
- **`fleet-update-check`:**
  - **Homebrew's warnings are read, not discarded.** Homebrew 7 ignores formulae from a tap nobody has
    trusted and says so only on stderr; the digest now names each untrusted tap as an error.
  - **A method whose command fails is never "current".** It now reports *not installed*, *timed out* or
    *check failed (exit N)*. Commands run without pipes, so the status is the tool's own.
  - **The pipx check never worked:** `pipx list --outdated --short` is refused by pipx (exit 1). It now
    runs `pipx list --outdated`.
- **`fleet-local-check`:** the alert subject names **new** failures first. It is cut at 60 characters,
  and in config order a new failure behind older ones was cut off.
- **Monitoring README:** the relay-watch examples turn `ssh`'s exit 255 (could not connect) into 3, so an
  unreachable node is unknown, not failing.
- **Smaller corrections:** chapter 17 — the settings registry is built in the fleet this came from, and
  `py_compile` is not a read-only parse (it writes `__pycache__` even with `PYTHONDONTWRITEBYTECODE=1`);
  chapter 19 — CI checks the generic patterns, never your names (the names list is local by design);
  GETTING-STARTED — the peer-messaging rule is rule **13** of the CLAUDE template, not 12; the Windows
  service-manager section is **partial**, not filled (and an earlier entry below now says so).
- **Tests:** 7 new (55 in all), each with the planted defect that makes it fail.

## 2026-10-02 — a quick start for a session joining peer messaging

- **New: [`skeleton/peer-messaging/QUICKSTART.md`](skeleton/peer-messaging/QUICKSTART.md)** — one
  link to give a new session: what to ask its operator for, checking it can message, installing the
  standard at the fixed paths, its first message, and how to ask another session for an install
  (requirements, not commands; the reply is a claim to check, and never the operator's approval).
  The standard itself is **unchanged — still v4**; nothing to re-check in your copies.
- Linked from the README, GETTING-STARTED, the skeleton index, a new
  [`skeleton/peer-messaging/README.md`](skeleton/peer-messaging/README.md) (which file is for whom),
  § 03, § 16, and E19 (a new section, *Adding a session to a running fleet*).

## 2026-09-30 — the stand-in question (design templates 1.5)

- **Design templates 1.5:** testing asks which code paths the real thing takes that a test's
  stand-in never exercises (a fake server, a local folder in place of a cloud service, a small file
  in place of a large one), and which test covers them against the real thing. **Re-check your own
  templates** if you copied them earlier.

## 2026-09-25 — corrections to this phase, and the guard's blind spots

Found by the re-audit that follows every phase. **Re-check anything you copied from these sections
earlier today.**

- **§ 17, empty globs:** the recommended fix was wrong. `nullglob` alone turns an empty glob into no
  arguments, so `grep` reads its standard input and prints nothing (or waits forever): the same false
  clean. Collect the files first and report a count of zero as its own result.
- **§ 17, BSD `find -size`:** units are case-specific (`c`, `k` lowercase; `M`, `G`, `T`, `P`
  uppercase), not "uppercase".
- **§ 08:** the unflushed-write example measured the client's memory, not an impossible rate; and the
  wired-versus-wireless case no longer quotes an "eight times" that compared two different tests.
- **`scripts/grep-guard.sh`: your names are now scanned in every file**, including the docs the
  generic patterns skip; the sharing chapter is no longer skipped at all (two of its lines were
  reworded so it scans clean). The self-test proves all three (66 checks). ⚠ **If you copied the
  guard, copy this version:** the old one never checked your names in two whole chapters.
- **`fleet-install-audit`:** a malformed node line (too few fields, or a blank one) is reported and
  alerts, instead of silently dropping that node from the audit.
- **§ 04:** the project tree shows `docs/peer-conversations/` (E19). **§ 20** lists E17's multi-site
  section. Two changelog lines corrected: the L4 test count, and the Codex template in L3.

## 2026-09-25 — a multi-site starter: a platform-side registry and a deploy with no site argument

- **New in E17 § 7: "When each site has its own session".** The site registry lives on the platform
  side; deploy takes no site argument and resolves the site from the repo it runs in, so a site's
  session cannot publish another site; it fails closed (an empty build would otherwise delete the
  live site); monitoring and backups are provisioned with the site. The honest limit: sessions
  running as the same OS user are protected from accidents, not from intent.
- **New `skeleton/websites/`:** `sites.conf.template`, `deploy-site.sh` and its tests (17 tests, one
  per thing the script must do or refuse; 16 planted defects, each caught by its test). The CI `tools` job runs
  them. Deliberately small: no provisioning and no container stack.

## 2026-09-25 — who maintains the public repo; what the guard cannot catch

- **New in § 19: "Who maintains the public repo".** A public repo derived from a private one
  normally shares its owner, because its author needs both. The control is the guard, not the
  separation, and the exception must be written into the rules by name, or a later session re-derives
  "one session, one repo" and refuses the work.
- **§ 19 now says what the guard cannot catch:** identifying context (a distinctive figure, date or
  phrasing), which is why derive-don't-copy and the stranger review still apply.
- **Principle 12 (§ 03), and rule 12 in `skeleton/CLAUDE.md.template` and
  `skeleton/AGENTS.md.template`:** one sentence naming that exception. **Re-check your rules file** if you publish a derived repo.

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
  reads its registration back, because task settings live only in the scheduler. *(Corrected later:
  partly filled — the Podman headless-at-boot pattern is still to do, and the section is marked partial.)*
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
