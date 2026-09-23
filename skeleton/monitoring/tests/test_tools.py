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
import importlib.util, json, os, shutil, subprocess, sys, tempfile, textwrap, unittest
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


class LocalCheck(Sandbox):
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

    def test_first_run_failure_mails_and_saves_state(self):
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stderr)
        m = self.mails()
        self.assertEqual(len(m), 1)
        self.assertEqual(m[0]["subject"], "[Fleet/Alert/Health] 1 failing — beta")
        self.assertEqual(read_json(self.state), {"alpha": True, "beta": False})

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
        self.assertEqual(read_json(self.state)["beta"], True, "state must not record an unsent alert")
        r = self.check()                                    # mailer back: the alert goes out now
        self.assertEqual(self.mails()[-1]["subject"], "[Fleet/Alert/Health] 1 failing — beta")
        self.assertEqual(read_json(self.state)["beta"], False)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
