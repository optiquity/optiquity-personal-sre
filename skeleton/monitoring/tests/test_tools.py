#!/usr/bin/env python3
"""Tests for the skeleton monitoring tools — stdlib only.

    python3 skeleton/monitoring/tests/test_tools.py        (or: python3 -m unittest discover skeleton/monitoring/tests)

The rule these tests exist for: **exercise the send path, not just --dry-run.** A --dry-run
never reaches the code that emails, and for four weeks an undefined name there crashed every
real alert while every documented check passed (guide § 17, "Syntax-checked is not correct").

So every tool runs as a real subprocess, in a throwaway $HOME, with $FLEET_MAILER pointing at a
FAKE mailer. The fake calls the REAL fleet-mail with --dry-run, so each subject a tool produces
is built and validated by the real code — then records what it was asked to send, and can be
told to fail (FAKE_MAIL_RC) to prove a failed send is retried rather than forgotten.
"""
import contextlib, importlib.util, json, os, shutil, subprocess, sys, tempfile, textwrap, time, unittest, urllib.error
from importlib.machinery import SourceFileLoader

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
FLEET_MAIL = os.path.join(TOOLS, "fleet-mail")


def load(path, name):
    """Import an extension-less script as a module (exec_module — load_module is deprecated)."""
    spec = importlib.util.spec_from_loader(name, SourceFileLoader(name, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write(path, text):
    with open(path, "w") as f:
        f.write(text)


def read_json(path):
    with open(path) as f:
        return json.load(f)


class Sandbox(unittest.TestCase):
    """A throwaway $HOME, a fake mailer, and helpers to run a tool and read what it mailed."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="fleet-tools-test-")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)
        self.log = os.path.join(self.tmp, "mail.jsonl")
        self.fake = os.path.join(self.tmp, "fake-mail")
        with open(self.fake, "w") as f:
            f.write(textwrap.dedent(f"""\
                #!{sys.executable}
                import json, os, subprocess, sys
                r = subprocess.run([sys.executable, {FLEET_MAIL!r}, "--dry-run", *sys.argv[1:]],
                                   capture_output=True, text=True)
                subject = r.stdout.splitlines()[0] if r.returncode == 0 and r.stdout else None
                with open({self.log!r}, "a") as fh:
                    fh.write(json.dumps({{"argv": sys.argv[1:], "rc": r.returncode, "subject": subject,
                                          "stderr": r.stderr}}) + "\\n")
                sys.exit(int(os.environ.get("FAKE_MAIL_RC", "0")) or r.returncode)
                """))
        os.chmod(self.fake, 0o755)
        self.env = dict(os.environ, HOME=self.home, FLEET_MAILER=self.fake, PYTHONDONTWRITEBYTECODE="1")
        for k in ("FLEET_SUBJECT_TAG", "FLEET_SUBJECT_PREFIX", "FLEET_MAIL_ENV", "FAKE_MAIL_RC"):
            self.env.pop(k, None)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_tool(self, name, *args, **env):
        e = dict(self.env, **env)
        # stdin=DEVNULL: fleet-mail reads a body from stdin when none is given, and an inherited,
        # never-closing stdin would hang the run
        return subprocess.run([sys.executable, os.path.join(TOOLS, name), *args], stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, env=e, timeout=120)

    def mails(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log) as f:
            return [json.loads(l) for l in f]


class FleetMail(Sandbox):
    def fm(self, *args, **env):
        return self.run_tool("fleet-mail", *args, **env)

    def test_parts_build_the_subject(self):
        r = self.fm("--dry-run", "--kind", "Alert", "--source", "Health", "--text", "1 failing — backup")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.splitlines()[0], "[Fleet/Alert/Health] 1 failing — backup")

    def test_tag_from_environment(self):
        r = self.fm("--dry-run", "--kind", "Report", "--source", "Test", "--text", "hi", FLEET_SUBJECT_TAG="MyFleet")
        self.assertEqual(r.stdout.splitlines()[0], "[MyFleet/Report/Test] hi")

    def test_legacy_prefix_variable_still_works(self):
        r = self.fm("--dry-run", "--kind", "Report", "--source", "Test", "--text", "hi", FLEET_SUBJECT_PREFIX="[Old")
        self.assertEqual(r.stdout.splitlines()[0], "[Old/Report/Test] hi")

    def test_tag_from_env_file(self):
        envf = os.path.join(self.tmp, "mail.env")
        write(envf, "SUBJECT_TAG=FileTag\n")
        r = self.fm("--dry-run", "--env", envf, "--kind", "Digest", "--source", "Updates", "--text", "weekly")
        self.assertEqual(r.stdout.splitlines()[0], "[FileTag/Digest/Updates] weekly")

    def test_prebuilt_subject_in_format_is_accepted(self):
        r = self.fm("--dry-run", "--subject", "[Fleet/Report/Backup] done")
        self.assertEqual((r.returncode, r.stdout.splitlines()[0]), (0, "[Fleet/Report/Backup] done"))

    def test_free_form_subject_is_refused(self):
        r = self.fm("--dry-run", "--subject", "nightly job output")
        self.assertEqual(r.returncode, 2)
        self.assertIn("REFUSING", r.stderr)

    def test_subject_with_another_tag_is_refused(self):
        r = self.fm("--dry-run", "--subject", "[Other/Alert/Health] x")
        self.assertEqual(r.returncode, 2)

    def test_usage_errors_exit_2(self):
        cases = [("--dry-run", "--subject", "[Fleet/Alert/X] y", "--kind", "Alert", "--source", "X", "--text", "y"),
                 ("--dry-run", "--kind", "Alert", "--source", "Health"),                    # no --text
                 ("--dry-run", "--kind", "Alert", "--source", "a/b", "--text", "x"),        # / in a segment
                 ("--kind", "Alert", "--source", "Health", "--text", "x")]                  # real send, no env file
        for args in cases:
            with self.subTest(args=args):
                self.assertEqual(self.fm(*args).returncode, 2)
        self.assertEqual(self.fm("--dry-run", "--kind", "Alert", "--source", "H", "--text", "x",
                                 FLEET_SUBJECT_TAG="My/Fleet").returncode, 2)

    def test_real_send_path_builds_and_sends(self):
        """In-process, with smtplib replaced: proves the path --dry-run never reaches."""
        fm = load(FLEET_MAIL, "fleet_mail_under_test")
        sent = []

        class FakeSMTP:
            def __init__(self, *a, **k): pass
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def ehlo(self): pass
            def starttls(self, **k): pass
            def login(self, u, p): pass
            def send_message(self, msg): sent.append(msg)

        envf = os.path.join(self.tmp, "mail.env")
        # a fake credential, assembled so it does not look like a real assignment to the leak guard
        write(envf, "\n".join(["SMTP_USERNAME=u", "SMTP_PASSWORD=" + "p", "MAIL_TO=ops"]) + "\n")
        fm.smtplib.SMTP = FakeSMTP
        rc = fm.main(["--env", envf, "--kind", "Alert", "--source", "Backup", "--text", "failed", "--body", "b"])
        self.assertEqual(rc, 0)
        self.assertEqual(sent[0]["Subject"], "[Fleet/Alert/Backup] failed")

        class BrokenSMTP(FakeSMTP):
            def login(self, u, p): raise OSError("connection refused")
        fm.smtplib.SMTP = BrokenSMTP
        self.assertEqual(fm.main(["--env", envf, "--kind", "Alert", "--source", "B", "--text", "x", "--body", "b"]), 1)


class LocalCheckBase(Sandbox):
    """Setup shared by the local-check tests (holds no tests itself)."""

    def setUp(self):
        super().setUp()
        self.flag = os.path.join(self.tmp, "beta-ok")
        self.conf = os.path.join(self.tmp, "local-checks.conf")
        self.state = os.path.join(self.tmp, "local-check.state")
        self.write_conf(["command | alpha | true", f"command | beta | test -f {self.flag}"])

    def write_conf(self, lines):
        write(self.conf, "\n".join(lines) + "\n")

    def check(self, *args, **env):
        return self.run_tool("fleet-local-check", "--config", self.conf, *args,
                             FLEET_LOCAL_CHECK_STATE=self.state, **env)


class LocalCheck(LocalCheckBase):
    def test_first_run_failure_mails_and_saves_state(self):
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stderr)
        m = self.mails()
        self.assertEqual(len(m), 1)
        self.assertEqual(m[0]["subject"], "[Fleet/Alert/Health] 1 failing — beta")
        self.assertEqual(read_json(self.state)["states"], {"alpha": True, "beta": False})

    def test_steady_state_is_silent_and_recovery_reports(self):
        self.check()
        self.check()                                        # unchanged: no second mail
        self.assertEqual(len(self.mails()), 1)
        write(self.flag, "")                        # beta recovers
        r = self.check()
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.mails()[-1]["subject"], "[Fleet/Report/Health] all checks recovered")

    def test_failed_send_is_retried_not_forgotten(self):
        write(self.flag, "")
        self.check()                                        # all ok, no mail, state saved
        os.remove(self.flag)                                # beta breaks …
        r = self.check(FAKE_MAIL_RC="1")                    # … and the mailer is down
        self.assertEqual(r.returncode, 3)
        self.assertEqual(read_json(self.state)["states"]["beta"], True, "state must not record an unsent alert")
        r = self.check()                                    # mailer back: the alert goes out now
        self.assertEqual(self.mails()[-1]["subject"], "[Fleet/Alert/Health] 1 failing — beta")
        self.assertEqual(read_json(self.state)["states"]["beta"], False)

    def test_new_failing_check_mails_even_with_existing_state(self):
        write(self.flag, "")
        self.check()
        self.write_conf(["command | alpha | true", f"command | beta | test -f {self.flag}", "command | gamma | false"])
        self.check()
        self.assertEqual(self.mails()[-1]["subject"], "[Fleet/Alert/Health] 1 failing — gamma")

    def test_dry_run_neither_mails_nor_saves(self):
        self.check("--dry-run")
        self.assertEqual(self.mails(), [])
        self.assertFalse(os.path.exists(self.state))


class LocalCheckStates(LocalCheckBase):
    """Three states, the unknown streak, state migration, config errors, and the new check types."""

    def dry(self):
        return self.check("--dry-run").stdout

    def test_unknown_carries_state_then_escalates(self):
        write(self.flag, "")                                           # beta ok
        gamma_ok = os.path.join(self.tmp, "gamma-ok")
        write(gamma_ok, "")
        gamma = f"command | gamma | test -f {gamma_ok} || exit 3"      # exit 3 = UNKNOWN
        self.write_conf(["command | alpha | true", f"command | beta | test -f {self.flag}", gamma])
        self.check()                                                    # all OK, state saved, no mail
        os.remove(gamma_ok)                                             # gamma now answers UNKNOWN
        for n in (1, 2, 3):
            r = self.check()
            self.assertEqual(r.returncode, 0, f"unknown run {n} must not fail")
            self.assertIs(read_json(self.state)["states"]["gamma"], True, "unknown carries the previous state")
            self.assertEqual(read_json(self.state)["unknown_streaks"]["gamma"], n)
        self.assertEqual(self.mails(), [], "no mail while merely unknown")
        r = self.check()                                                # 4th consecutive unknown
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.mails()[-1]["subject"], "[Fleet/Alert/Health] 1 failing — gamma")
        self.assertIn("could not determine state for 4 consecutive runs", self.mails()[-1]["argv"][-1])

    def test_unknown_on_first_run_is_not_an_alert(self):
        self.write_conf(["command | alpha | true", "command | delta | exit 3"])
        r = self.check()
        self.assertEqual((r.returncode, self.mails()), (0, []))
        self.assertIn("[????] delta", self.dry())

    def test_old_flat_state_is_migrated(self):
        write(self.state, json.dumps({"alpha": True, "beta": False}))   # the pre-2026-09 format
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.mails(), [], "beta was already failing: no transition, no mail")
        self.assertEqual(read_json(self.state), {"states": {"alpha": True, "beta": False}, "unknown_streaks": {}})

    def test_malformed_line_is_reported_not_skipped(self):
        self.write_conf(["command | alpha | true", "bogus | x | y", "command | half-a-line"])
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.mails()[0]["subject"], "[Fleet/Alert/Health] 2 failing — config line 2, config line 3")

    def test_hash_check(self):
        ref, inst = os.path.join(self.tmp, "ref"), os.path.join(self.tmp, "inst")
        write(ref, "v1\n")
        cases = [("v1\n", "[OK  ] h: matches its reference"), ("v0\n", "[FAIL] h: " + inst + " differs from"),
                 (None, "[FAIL] h: " + inst + " is NOT installed")]
        for content, want in cases:
            with self.subTest(content=content):
                if content is None:
                    os.remove(inst)
                else:
                    write(inst, content)
                self.write_conf([f"hash | h | {inst} | {ref}"])
                self.assertIn(want, self.dry())
        os.remove(ref)
        write(inst, "v1\n")
        self.assertIn("[FAIL] h: reference copy missing", self.dry(), "a missing reference must FAIL, not pass")

    def test_synclag_check(self):
        repo = os.path.join(self.tmp, "src")
        os.makedirs(os.path.join(repo, ".git"))
        self.write_conf([f"synclag | sync | {repo} | 3"])
        self.assertIn("[????] sync", self.dry(), "never fetched: UNKNOWN, not OK and not FAIL")
        fh = os.path.join(repo, ".git", "FETCH_HEAD")
        write(fh, "")
        self.assertIn("[OK  ] sync", self.dry())
        old = time.time() - 5 * 3600
        os.utime(fh, (old, old))
        self.assertIn("[FAIL] sync: last successful fetch 5.0 h ago (limit 3 h)", self.dry())


class LocalCheckProbes(unittest.TestCase):
    """The probes' three-way classification, in-process with the system calls replaced."""

    def setUp(self):
        self.lc = load(os.path.join(TOOLS, "fleet-local-check"), "fleet_local_check_under_test")
        self.lc.RETRY_PAUSE = 0

    def test_mount(self):
        lc = self.lc
        lc.os.path.ismount = lambda p: True
        lc.sh = lambda *a, **k: (124, "", "timed out")
        self.assertIsNone(lc.chk_mount("m", "/mnt/x")[1], "an unreadable table is UNKNOWN, never an unmount")
        lc.sh = lambda *a, **k: (0, "server:/share on /mnt/x (nfs)", "")
        self.assertIs(lc.chk_mount("m", "/mnt/x")[1], True)
        calls = []
        lc.os.path.ismount = lambda p: calls.append(p) or False
        r = lc.chk_mount("m", "/mnt/x")
        self.assertIs(r[1], False)
        self.assertEqual(len(calls), lc.MOUNT_RETRIES, "an unmount is confirmed over several attempts")

    def test_http(self):
        lc = self.lc
        for rc, out, want in [(0, "200", True), (0, "503", False), (7, "000", False), (28, "000", None), (124, "", None)]:
            with self.subTest(rc=rc, out=out):
                lc.sh = lambda *a, rc=rc, out=out, **k: (rc, out, "")
                self.assertIs(lc.chk_http("h", "https://example.invalid/")[1], want)

    def test_service(self):
        lc = self.lc
        lc.IS_MAC = True
        for rc, out, err, want in [(0, "state = running", "", True), (0, "state = waiting", "", False),
                                   (113, "", "Could not find service", False), (124, "", "timed out", None),
                                   (1, "", "", None)]:
            with self.subTest(rc=rc, err=err):
                lc.sh = lambda *a, rc=rc, out=out, err=err, **k: (rc, out, err)
                self.assertIs(lc.chk_service("s", "com.example.x")[1], want)
        lc.IS_MAC = False
        for rc, out, want in [(0, "active", True), (3, "inactive", False), (124, "", None)]:
            with self.subTest(linux=out):
                lc.sh = lambda *a, rc=rc, out=out, **k: (rc, out, "")
                self.assertIs(lc.chk_service("s", "x.service")[1], want)


class InstallAudit(Sandbox):
    def audit(self, *args, **env):
        conf = os.path.join(self.tmp, "fleet-nodes.conf")
        write(conf, "# no nodes\n")
        state = os.path.join(self.tmp, "install-audit.state")
        return self.run_tool("fleet-install-audit", "--config", conf, *args,
                             FLEET_INSTALL_AUDIT_STATE=state, **env), state

    def test_send_path_uses_parts(self):
        r, state = self.audit("--always")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.mails()[0]["subject"], "[Fleet/Report/Installs] audit all clear")
        self.assertTrue(os.path.exists(state))

    def test_failed_send_keeps_no_state(self):
        r, state = self.audit("--always", FAKE_MAIL_RC="1")
        self.assertEqual(r.returncode, 3)
        self.assertFalse(os.path.exists(state))


class UpdateCheck(Sandbox):
    def test_digest_send_path_uses_parts(self):
        conf = os.path.join(self.tmp, "fleet-nodes.conf")
        write(conf, "# no nodes\n")
        r = self.run_tool("fleet-update-check", "--config", conf, "--always")
        self.assertEqual(r.returncode, 0, r.stderr)
        subj = self.mails()[0]["subject"]
        self.assertTrue(subj.startswith("[Fleet/Digest/Updates] "), subj)
        r = self.run_tool("fleet-update-check", "--config", conf, "--always", FAKE_MAIL_RC="1")
        self.assertEqual(r.returncode, 1)



WINGET_FIXTURE = """   -    \\    |
Failed in attempting to update the source: winget
Name                 Id                      Version   Available Source
-----------------------------------------------------------------------
Some Editor          Vendor.SomeEditor       1.2.0     1.3.1     winget
Runtime Pack         Vendor.Runtime.8        8.0.1     8.0.4     winget
2 upgrades available.
"""


class UpdateCheckRegistry(unittest.TestCase):
    """Coverage statuses, registries and parsers — in-process, the SSH layer replaced."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="fleet-uc-test-")
        self.uc = load(os.path.join(TOOLS, "fleet-update-check"), "fleet_update_check_under_test")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def node(self, methods, os_="linux", role="gateway"):
        return {"role": role, "target": "gw", "os": os_, "methods": methods}

    def test_reachability_is_echo_ok(self):
        uc = self.uc
        uc.sh = lambda *a, **k: (0, "ok", "")
        self.assertTrue(uc.reachable(self.node([])))
        uc.sh = lambda *a, **k: (0, "", "")                   # connected, but no answer to `echo ok`
        self.assertFalse(uc.reachable(self.node([])))
        seen = []
        uc.sh = lambda args, *a, **k: seen.append(args) or (0, "ok", "")
        uc.reachable(self.node([]))
        self.assertEqual(seen[0][-1], "echo ok", "not `true` — a Windows SSH shell has no `true`")

    def test_coverage_statuses(self):
        uc = self.uc
        uc.run_on = lambda node, cmd, timeout=300: (0, "brew=0npm=5gem=2cargo=1vscode=4apt=1", "")
        lines, count, errs = uc.reconcile_node(self.node(["apt", "gem", "?cargo", "!vscode", "not-audited"]))
        text = "\n".join(lines)
        self.assertIn("NOT AUDITED", text)
        self.assertIn("NO CHECKER  gem", text)
        self.assertIn("GAP         cargo", text)
        self.assertIn("UNDECLARED  npm (5 installed)", text)
        self.assertIn("excluded (1): vscode", text)
        self.assertNotIn("UNDECLARED  vscode", text, "an exclusion is counted, not reported as undeclared")
        self.assertEqual((count, errs), (4, []))              # not-audited + gem + cargo + npm

    def test_windows_skips_posix_discovery(self):
        uc = self.uc
        uc.run_on = lambda *a, **k: self.fail("no POSIX probe may run on a Windows node")
        lines, count, _ = uc.reconcile_node(self.node(["winget"], os_="windows"))
        self.assertIn("discovery not supported", "\n".join(lines))
        self.assertEqual(count, 0)

    def test_malformed_rows_are_reported(self):
        conf = os.path.join(self.tmp, "fleet-nodes.conf")
        write(conf, "gateway | gw | linux | apt\nbroken | only-two\nlaptop | | macos | brew\n")
        nodes, errs = self.uc.load_nodes(conf)
        self.assertEqual([n["role"] for n in nodes], ["gateway"])
        self.assertEqual(len(errs), 2, errs)

    def test_brew_probe_count_is_unpadded(self):
        """Run the REAL probe against a fake `brew` — wc -l's padding is what hid brew entirely."""
        bindir = os.path.join(self.tmp, "bin")
        os.makedirs(bindir)
        write(os.path.join(bindir, "brew"), "#!/bin/sh\nprintf 'git\\njq\\n'\n")
        os.chmod(os.path.join(bindir, "brew"), 0o755)
        r = subprocess.run(["sh", "-c", self.uc.METHOD_PROBES["brew"]], capture_output=True, text=True,
                           env=dict(os.environ, PATH=bindir + os.pathsep + os.environ["PATH"]))
        # parse it exactly as reconcile_node does — no strip(): the padding IS the bug
        self.assertRegex("brew=" + r.stdout, r"^brew=2\b", "the count must be parseable as the probe emits it")

    def test_winget_parser(self):
        rows = self.uc.parse_winget(WINGET_FIXTURE)
        self.assertEqual(len(rows), 2, rows)
        self.assertTrue(rows[0].startswith("Some Editor"))

    def test_binaries_registry(self):
        uc = self.uc
        reg = os.path.join(self.tmp, "fleet-binaries.conf")
        write(reg, "gateway | /usr/local/bin/gatus | upstream | example/gatus | v5\\.[0-9]+\\.[0-9]+\n"
                   "gateway | /usr/local/bin/backup.sh | local | - | -\n"
                   "gateway | /usr/local/bin/gone | local | - | -\n")
        uc.BINARIES_CONF = reg
        def run_on(node, cmd, timeout=300):
            if cmd.startswith("strings"):
                return 0, "v5.36.0", ""
            return 0, "/usr/local/bin/gatus\n/usr/local/bin/backup.sh\n/usr/local/bin/mystery\n", ""
        uc.run_on = run_on
        uc.github_latest = lambda repo: "v5.37.0"
        lines, count, errs = uc.binaries_block([self.node(["apt"])], {"gateway": True})
        text = "\n".join(lines)
        self.assertIn("UNREGISTERED  gateway: /usr/local/bin/mystery", text)
        self.assertIn("gatus v5.36.0 -> v5.37.0", text)
        self.assertIn("MISSING     gateway: /usr/local/bin/gone", text)
        self.assertEqual((count, errs), (3, []))
        uc.run_on = lambda node, cmd, timeout=300: (0, "", "") if cmd.startswith("strings") else (0, "/usr/local/bin/gatus\n", "")
        self.assertIn("UNREADABLE", "\n".join(uc.binaries_block([self.node(["apt"])], {"gateway": True})[0]))

    def test_decisions(self):
        uc = self.uc
        dec = os.path.join(self.tmp, "fleet-update-decisions.conf")
        write(dec, "gateway | old-db | frozen | major migrates the schema | 2000-01-01\n"
                   "laptop | editor | declined | self-updates | 2999-01-01\n"
                   "laptop | thing | declined | reason | someday\n")
        uc.DECISIONS_CONF = dec
        lines, count, errs = uc.decisions_block()
        text = "\n".join(lines)
        self.assertIn("REVISIT DUE  gateway: old-db", text)
        self.assertNotIn("REVISIT DUE  laptop: editor", text)
        self.assertEqual(count, 1)
        self.assertEqual(len(errs), 1, "a date that isn't YYYY-MM-DD is reported")


class UpdateCheckReachability(Sandbox):
    def test_unreachable_node_is_skipped_not_an_error(self):
        conf = os.path.join(self.tmp, "fleet-nodes.conf")
        write(conf, "gateway | nohost.invalid | linux | apt\n")
        r = self.run_tool("fleet-update-check", "--config", conf, "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("gateway (linux) — unreachable, skipped", r.stdout)
        self.assertIn("gateway skipped", r.stdout)
        self.assertNotIn("method discovery failed", r.stdout)


class ContainerCheck(unittest.TestCase):
    """Registries, variants, pins, floating tags and exit codes — the network replaced."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="fleet-cc-test-")
        self.cc = load(os.path.join(TOOLS, "fleet-container-check"), "fleet_container_check_under_test")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_split_ref(self):
        cases = {"caddy:2.10-alpine": ("docker.io", "library/caddy", "2.10-alpine"),
                 "grafana/grafana:12.0.0": ("docker.io", "grafana/grafana", "12.0.0"),
                 "docker.io/library/nginx:1.27": ("docker.io", "library/nginx", "1.27"),
                 "ghcr.io/org/app:v1.2.3": ("ghcr.io", "org/app", "v1.2.3"),
                 "lscr.io/linuxserver/nginx:1.26.2": ("lscr.io", "linuxserver/nginx", "1.26.2"),
                 "quay.io/prometheus/node-exporter:v1.8.0": ("quay.io", "prometheus/node-exporter", "v1.8.0"),
                 "registry.local:5000/team/svc:2.0": ("registry.local:5000", "team/svc", "2.0"),
                 "app": ("docker.io", "library/app", "")}
        for ref, want in cases.items():
            with self.subTest(ref=ref):
                self.assertEqual(self.cc.split_ref(ref), want)

    def test_variants_and_floating_tags(self):
        cc = self.cc
        tags = ["5.12-apache", "5.13-apache", "5.13.0-apache", "5.14-fpm", "6.0-fpm"]
        cc.tags_dockerhub = lambda repo: tags
        self.assertEqual(cc.newest("docker.io", "library/matomo", "apache", 2), "5.13-apache",
                         "same variant only; same component count preferred")
        self.assertTrue(cc.is_behind("2.10-alpine", "2.11.4-alpine"), "a real minor bump is behind")
        self.assertFalse(cc.is_behind("3.14-alpine", "3.14.7-alpine"), "a floating tag is not stale")
        self.assertFalse(cc.is_behind("1.2.3", "1.2.3"))
        self.assertEqual(cc.parse_tag("mysql-v2.19.0"), ((2, 19, 0), "mysql", 3))
        self.assertIsNone(cc.parse_tag("latest"))

    def test_scan_pins_errors_and_skips(self):
        compose = os.path.join(self.tmp, "compose.yaml")
        write(compose, "services:\n"
                       "  web:\n    image: caddy:2.10-alpine\n"
                       "  db:\n    # pin: LTS track, majors migrate the schema\n    image: mysql:8.4\n"
                       "  py:\n    image: python:3.14-alpine\n"
                       "  bad:\n    image: example/broken:1.0\n"
                       "  moving:\n    image: app:latest\n"
                       "  quoted:\n    image: \"ghcr.io/org/app:v1.2.3\"\n")
        answers = {"library/caddy": "2.11.4-alpine", "library/mysql": "9.1", "library/python": "3.14.7-alpine",
                   "org/app": "v1.2.3"}
        def lookup(registry, repo, variant, parts):
            if repo == "example/broken":
                raise RuntimeError("registry said no")
            return answers[repo]
        rows = {r["image"]: r for r in self.cc.scan(compose, set(), [], lookup=lookup)}
        self.assertTrue(rows["docker.io/library/caddy"]["outdated"])
        self.assertFalse(rows["docker.io/library/mysql"]["outdated"], "an intentional pin is not an update")
        self.assertEqual(rows["docker.io/library/mysql"]["pinned"], "LTS track, majors migrate the schema")
        self.assertFalse(rows["docker.io/library/python"]["outdated"], "floating tag")
        self.assertIn("error", rows["docker.io/example/broken"])
        self.assertNotIn("docker.io/library/app", rows, "latest moves at pull time: skipped")
        self.assertFalse(rows["ghcr.io/org/app"]["outdated"])

    def test_oci_anonymous_token_flow(self):
        cc = self.cc
        calls = []
        class Resp:
            def __init__(self, body): self.body = json.dumps(body).encode()
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self, *a): return self.body
        def urlopen(req, timeout=15):
            url, auth = req.full_url, req.headers.get("Authorization")
            calls.append((url, auth))
            if url.startswith("https://quay.io/v2/auth?"):      # the realm the challenge advertised
                return Resp({"token": "anon"})
            if auth != "Bearer anon":
                import email.message, io
                h = email.message.Message()
                h["WWW-Authenticate"] = 'Bearer realm="https://quay.io/v2/auth",service="quay.io",scope="repository:p/n:pull"'
                raise urllib.error.HTTPError(url, 401, "Unauthorized", h, io.BytesIO(b""))
            return Resp({"tags": ["v1.8.0", "v1.12.1"]})
        cc.urllib.request.urlopen = urlopen
        self.assertEqual(cc.tags_oci("quay.io", "p/n"), ["v1.8.0", "v1.12.1"])
        self.assertTrue(any("quay.io/v2/auth" in u and "scope=" in u for u, _ in calls), calls)

    def test_non_docker_hub_registries_use_the_oci_client(self):
        cc = self.cc
        cc.tags_dockerhub = lambda repo: self.fail(f"{repo} must not be looked up on Docker Hub")
        cc.tags_oci = lambda registry, repo: ["v1.8.0", "v1.12.1"]
        for registry in ("quay.io", "lscr.io", "ghcr.io", "registry.local:5000"):
            with self.subTest(registry=registry):
                self.assertEqual(cc.newest(registry, "p/n", "", 3), "v1.12.1")

    def test_exit_code_reflects_errors_and_updates(self):
        cc = self.cc
        compose = os.path.join(self.tmp, "compose.yaml")
        write(compose, "services:\n  x:\n    image: example/app:1.0\n")
        argv = sys.argv
        try:
            sys.argv = ["fleet-container-check", "--compose", compose]
            cc.newest = lambda *a: (_ for _ in ()).throw(RuntimeError("registry down"))
            with open(os.devnull, "w") as null, contextlib.redirect_stdout(null):
                self.assertEqual(cc.main(), 2, "a failed check is an error, never 'current'")
                cc.newest = lambda *a: "1.1"
                self.assertEqual(cc.main(), 1)
                cc.newest = lambda *a: "1.0"
                self.assertEqual(cc.main(), 0)
        finally:
            sys.argv = argv

    def run_cc(self, *args):
        env = dict(os.environ, HOME=self.tmp, PYTHONDONTWRITEBYTECODE="1")
        env.pop("FLEET_COMPOSES", None)
        return subprocess.run([sys.executable, os.path.join(TOOLS, "fleet-container-check"), *args],
                              stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env, timeout=60)

    def test_registry_discovery_and_exit_codes(self):
        cfg = os.path.join(self.tmp, ".config", "fleet-monitoring")
        os.makedirs(cfg)
        for stack in ("a", "b"):
            os.makedirs(os.path.join(self.tmp, stack))
            write(os.path.join(self.tmp, stack, "compose.yaml"), "services:\n  x:\n    image: app:latest\n")
        r = self.run_cc()
        self.assertEqual(r.returncode, 2, "no registry file: nothing checked is an error, not 'current'")
        self.assertIn("register your compose stacks", r.stdout)
        write(os.path.join(cfg, "fleet-composes.conf"), "~/a/compose.yaml\n")
        r = self.run_cc()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("UNREGISTERED", r.stdout)
        self.assertIn(os.path.join(self.tmp, "b", "compose.yaml"), r.stdout)
        write(os.path.join(cfg, "fleet-composes.conf"), "~/a/compose.yaml\n~/b/compose.yaml\n~/gone/compose.yaml\n")
        r = self.run_cc()
        self.assertEqual(r.returncode, 2)
        self.assertIn("registered but MISSING", r.stdout)


class UpdateCheckFoldsContainerErrors(Sandbox):
    def test_container_check_error_is_reported_not_swallowed(self):
        bindir = os.path.join(self.home, ".local", "bin")
        os.makedirs(bindir)
        write(os.path.join(bindir, "fleet-container-check"), "#!/bin/sh\necho 'Pinned container images'\necho 'boom' >&2\nexit 2\n")
        os.chmod(os.path.join(bindir, "fleet-container-check"), 0o755)
        conf = os.path.join(self.tmp, "fleet-nodes.conf")
        write(conf, "# no nodes\n")
        r = self.run_tool("fleet-update-check", "--config", conf)
        self.assertEqual(r.returncode, 0, r.stderr)
        subj = self.mails()[0]["subject"]
        self.assertIn("check errors", subj, "exit 2 from the container check must surface as an error")
        self.assertIn("container check exited 2", self.mails()[0]["argv"][-1])

if __name__ == "__main__":
    unittest.main(verbosity=2)
