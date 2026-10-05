#!/usr/bin/env python3
"""Tests for fleet-launch.c and install-fleet-launch.sh — stdlib only.

    python3 skeleton/launcher/tests/test_fleet_launch.py

**macOS only.** They build real binaries with Xcode's clang and sign them with codesign, so on any other
system (CI runs Linux) every test is SKIPPED, and says so. Run them on a Mac before relying on the launcher.

Each rule has a test, and the planted defect that makes it fail is either in the test itself (a "leaky"
build, a build without the hardened runtime, an old line of the installer) or run by hand. They build
throwaway copies pointed at a temporary allowlist — never the installed binary, which must not be rebuilt.
The installer is run WHOLE, under its own `set -euo pipefail`, from a copy aimed at a scratch folder with a
stand-in for sudo: a check that passed when tried alone once refused a correct signature inside the script.
"""
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
LAUNCHER = os.path.dirname(HERE)
SRC = os.path.join(LAUNCHER, "fleet-launch.c")
INSTALLER = os.path.join(LAUNCHER, "install-fleet-launch.sh")
ON_MAC = sys.platform == "darwin" and bool(shutil.which("xcrun")) and bool(shutil.which("codesign"))
WHY_SKIP = "macOS with Xcode's command-line tools only (it builds and signs real binaries)"

FAKE_SUDO = """#!/bin/bash
# test stand-in for sudo: runs the command as this user, dropping install's -o/-g (owner and group)
a=()
while [ $# -gt 0 ]; do case "$1" in -o|-g) shift 2 ;; *) a+=("$1"); shift ;; esac; done
exec "${a[@]}"
"""
OLD_SIG_CHECK = """codesign -dv "$T/fleet-launch" 2>&1 | grep -q 'flags=0x10002(adhoc,runtime)' \\
    || { say "✗ signature is not ad-hoc + hardened runtime — refusing"; exit 1; }"""
NEW_SIG_CHECK = """sig=$(codesign -dv "$T/fleet-launch" 2>&1)
case "$sig" in
    *'flags=0x10002(adhoc,runtime)'*) ;;
    *) say "✗ signature is not ad-hoc + hardened runtime — refusing"; say "$sig"; exit 1 ;;
esac"""


def read(path):
    with open(path) as fh:
        return fh.read()


def write(path, text, mode=None):
    with open(path, "w") as fh:
        fh.write(text)
    if mode is not None:
        os.chmod(path, mode)


def build(out, allow, uid, hardened=True, src=SRC):
    """As the installer builds it: clang, then an ad-hoc signature WITH the hardened runtime."""
    p = subprocess.run(["xcrun", "clang", "-O2", "-Wall", "-Werror", "-o", out, src,
                        '-DALLOW="%s"' % allow, "-DALLOW_UID=%d" % uid], capture_output=True, text=True)
    if p.returncode != 0:
        raise AssertionError("build failed: " + p.stderr)
    if hardened:
        subprocess.run(["codesign", "--force", "-s", "-", "-o", "runtime", out], check=True, capture_output=True)
    return out


def run(binary, args, env=None, timeout=20):
    p = subprocess.run([binary, *args], capture_output=True, text=True, env=env, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def write_allow(path, lines, mode=0o644):
    write(path, "\n".join(lines) + "\n", mode)


@unittest.skipUnless(ON_MAC, WHY_SKIP)
class Launcher(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="fleet-launch-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.allow = os.path.join(self.tmp, "allow")
        self.fl = build(os.path.join(self.tmp, "fl"), self.allow, os.getuid())

    def test_the_production_build_compiles_cleanly(self):
        p = subprocess.run(["xcrun", "clang", "-O2", "-Wall", "-Werror", "-o", os.path.join(self.tmp, "prod"), SRC],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr[-300:])

    def test_an_allowed_command_runs_and_its_exit_code_comes_back(self):
        write_allow(self.allow, ["# comment", "", "/bin/sh\t-c\texit 7"])
        self.assertEqual(run(self.fl, ["/bin/sh", "-c", "exit 7"])[0], 7)

    def test_a_command_not_in_the_list_is_refused(self):
        write_allow(self.allow, ["/bin/sh\t-c\texit 7"])
        rc, _, err = run(self.fl, ["/bin/sh", "-c", "exit 8"])
        self.assertEqual(rc, 126)
        self.assertIn("not in", err)
        write_allow(self.allow, ["/bin/sh\t-c\texit 7", "/bin/sh\t-c\texit 8"])     # planted: now listed
        self.assertEqual(run(self.fl, ["/bin/sh", "-c", "exit 8"])[0], 8, "the list did the refusing")

    def test_only_exact_lines_match(self):
        write_allow(self.allow, ["/bin/sh\t-c\texit 7"])
        self.assertEqual(run(self.fl, ["/bin/sh", "-c", "exit 7", "extra"])[0], 126)

    def test_a_relative_program_path_is_refused(self):
        write_allow(self.allow, ["sh\t-c\texit 7"])
        self.assertEqual(run(self.fl, ["sh", "-c", "exit 7"])[0], 2)

    def test_a_list_others_can_write_is_refused(self):
        write_allow(self.allow, ["/bin/sh\t-c\texit 7"], mode=0o666)
        self.assertEqual(run(self.fl, ["/bin/sh", "-c", "exit 7"])[0], 125)

    def test_a_list_not_owned_by_root_is_refused_by_the_real_build(self):
        write_allow(self.allow, ["/bin/sh\t-c\texit 7"])
        root_fl = build(os.path.join(self.tmp, "fl-root"), self.allow, 0)
        self.assertEqual(run(root_fl, ["/bin/sh", "-c", "exit 7"])[0], 125)

    def test_a_list_reached_through_a_symbolic_link_is_refused(self):
        write_allow(self.allow, ["/bin/sh\t-c\texit 7"])
        link = os.path.join(self.tmp, "allow-link")
        os.symlink(self.allow, link)
        link_fl = build(os.path.join(self.tmp, "fl-link"), link, os.getuid())
        self.assertEqual(run(link_fl, ["/bin/sh", "-c", "exit 7"])[0], 125)

    def test_the_child_gets_only_a_fixed_environment(self):
        write_allow(self.allow, ["/usr/bin/env"])
        hostile = dict(os.environ, PYTHONPATH="/evil", FLEET_MAILER="/evil/mail", DYLD_INSERT_LIBRARIES="/evil.dylib",
                       DYLD_LIBRARY_PATH="/evil", HOME="/evil-home", PATH="/evil/bin:/usr/bin:/bin")
        rc, out, _ = run(self.fl, ["/usr/bin/env"], env=hostile)
        env = dict(l.split("=", 1) for l in out.splitlines() if "=" in l)
        self.assertEqual(rc, 0)
        self.assertEqual(sorted(env), ["HOME", "LANG", "LOGNAME", "PATH", "TMPDIR", "USER"])
        self.assertEqual(env["HOME"], os.path.expanduser("~" + os.environ.get("USER", "")))
        self.assertNotIn("/evil", env["PATH"])
        # planted: the caller's environment passed through — PYTHONPATH leaks (the fixed list did the work)
        leaky_src = os.path.join(self.tmp, "leaky.c")
        text = read(SRC)
        self.assertEqual(text.count("&argv[1], env);"), 1)
        write(leaky_src, "#include <crt_externs.h>\n" +
              text.replace("&argv[1], env);", "&argv[1], *_NSGetEnviron()); (void)env;"))
        leaky = os.path.join(self.tmp, "fl-leaky")
        subprocess.run(["xcrun", "clang", "-O2", "-o", leaky, leaky_src, '-DALLOW="%s"' % self.allow,
                        "-DALLOW_UID=%d" % os.getuid()], check=True, capture_output=True)
        subprocess.run(["codesign", "--force", "-s", "-", "-o", "runtime", leaky], check=True, capture_output=True)
        self.assertIn("PYTHONPATH=/evil", run(leaky, ["/usr/bin/env"], env=hostile)[1])

    def test_a_library_injected_into_the_launcher_is_ignored(self):
        dylib, marker = os.path.join(self.tmp, "inject.dylib"), os.path.join(self.tmp, "injected")
        write(os.path.join(self.tmp, "inject.c"),
              '#include <stdio.h>\n__attribute__((constructor)) static void hit(void) '
              '{ FILE *f = fopen("%s", "w"); if (f) fclose(f); }\n' % marker)
        subprocess.run(["xcrun", "clang", "-dynamiclib", "-o", dylib, os.path.join(self.tmp, "inject.c")],
                       check=True, capture_output=True)
        inject = dict(os.environ, DYLD_INSERT_LIBRARIES=dylib)
        write_allow(self.allow, ["/bin/sh\t-c\texit 7"])
        self.assertEqual(run(self.fl, ["/bin/sh", "-c", "exit 7"], env=inject)[0], 7)
        self.assertFalse(os.path.exists(marker), "the hardened runtime must make dyld ignore it")
        soft = build(os.path.join(self.tmp, "fl-soft"), self.allow, os.getuid(), hardened=False)
        run(soft, ["/bin/sh", "-c", "exit 7"], env=inject)               # planted: no hardened runtime
        self.assertTrue(os.path.exists(marker), "without it, the library runs inside the launcher")

    def test_a_stop_signal_reaches_the_child(self):
        write_allow(self.allow, ["/bin/sleep\t30"])
        proc = subprocess.Popen([self.fl, "/bin/sleep", "30"])
        time.sleep(0.5)
        os.kill(proc.pid, signal.SIGTERM)
        t0 = time.time()
        rc = proc.wait(timeout=10)
        left = subprocess.run(["pgrep", "-f", "^/bin/sleep 30$"], capture_output=True, text=True).stdout.split()
        self.assertEqual(rc, 128 + signal.SIGTERM)
        self.assertLess(time.time() - t0, 5)
        self.assertEqual(left, [], "the child must stop too")


@unittest.skipUnless(ON_MAC, WHY_SKIP)
class Installer(unittest.TestCase):
    """The installer run WHOLE, as its user runs it — not line by line."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="fleet-launch-installer-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        os.makedirs(os.path.join(self.tmp, "fakebin"))
        write(os.path.join(self.tmp, "fakebin", "sudo"), FAKE_SUDO, 0o755)
        self.staged = os.path.join(self.tmp, "staged.allow")
        self.root = os.path.join(self.tmp, "root")
        self.allow = os.path.join(self.root, "etc", "fleet-launch.allow")
        self.binary = os.path.join(self.root, "libexec", "fleet-launch")
        self.script = self.copy("install.sh")

    def copy(self, name, plant=()):
        """The installer, aimed at <tmp>/root instead of /usr/local and building against that list. Every
        rewrite must match exactly once, so a changed installer fails here rather than going untested."""
        text = read(INSTALLER)
        for old, new in [
            ('SRC="$HERE/fleet-launch.c"', 'SRC="%s"' % SRC),
            ("BIN=/usr/local/libexec/fleet-launch", "BIN=%s/libexec/fleet-launch" % self.root),
            ("ALLOW=/usr/local/etc/fleet-launch.allow", "ALLOW=%s" % self.allow),
            ("-g wheel /usr/local/libexec\n", "-g wheel %s/libexec\n" % self.root),
            ("-g wheel /usr/local/etc\n", "-g wheel %s/etc\n" % self.root),
            ('-o "$T/fleet-launch" "$SRC"\n', '-o "$T/fleet-launch" "$SRC" \'-DALLOW="%s"\' -DALLOW_UID=%d\n'
             % (self.allow, os.getuid())),
            *plant,
        ]:
            self.assertEqual(text.count(old), 1, "installer rewrite no longer matches: " + old)
            text = text.replace(old, new)
        path = os.path.join(self.tmp, name)
        write(path, text)
        return path

    def install(self, script, *args):
        env = dict(os.environ, PATH=os.path.join(self.tmp, "fakebin") + ":" + os.environ["PATH"], TMPDIR=self.tmp,
                   FLEET_LAUNCH_STAGED=self.staged)
        p = subprocess.run(["bash", script, *args], capture_output=True, text=True, env=env, timeout=120)
        return p.returncode, p.stdout + p.stderr

    def test_it_refuses_when_nothing_is_staged(self):
        rc, out = self.install(self.script)
        self.assertEqual(rc, 1)
        self.assertIn("no staged allowlist", out)

    def test_the_whole_installer_installs_and_passes_its_self_check(self):
        write(self.staged, "# header\n\n/bin/sh\t-c\texit 7\n")
        rc, out = self.install(self.script)
        self.assertEqual(rc, 0, out[-600:])
        self.assertIn("✓ installed", out)
        self.assertIn("✓ self-check", out)
        sig = subprocess.run(["codesign", "-dvvv", self.binary], capture_output=True, text=True).stderr
        cdhash = next(l.split("=", 1)[1] for l in sig.splitlines() if l.startswith("CDHash="))
        self.assertIn("(cdhash %s)" % cdhash, out)
        self.assertIn("flags=0x10002(adhoc,runtime)", sig)
        self.assertEqual(run(self.binary, ["/bin/sh", "-c", "exit 7"])[0], 7)
        rc, out = self.install(self.script)                              # and never twice
        self.assertEqual(rc, 1)
        self.assertIn("already installed", out)

    def test_list_reinstalls_a_list_with_no_commands_left(self):
        write(self.staged, "# only comments\n\n")
        rc, out = self.install(self.script, "--list")
        self.assertEqual(rc, 0, out)
        self.assertEqual(read(self.allow), "# only comments\n\n")
        grep_print = self.copy("install-grep.sh", plant=[(
            """awk '!/^#/ && length { print "    " $0 }' "$ALLOW\"""",
            """grep -v '^#' "$ALLOW" | grep -v '^$' | sed 's/^/    /'""")])
        self.assertNotEqual(self.install(grep_print, "--list")[0], 0, "planted: grep exits 1 on an empty list")

    def test_it_refuses_a_signature_without_the_hardened_runtime(self):
        write(self.staged, "/bin/sh\t-c\texit 7\n")
        soft = self.copy("install-soft.sh", plant=[(
            'codesign --force -s - -o runtime "$T/fleet-launch"', 'codesign --force -s - "$T/fleet-launch"')])
        rc, out = self.install(soft)
        self.assertEqual(rc, 1)
        self.assertIn("signature is not", out)
        self.assertFalse(os.path.exists(self.binary))

    def test_the_old_grep_q_check_refuses_a_correct_signature(self):
        """Planted: `codesign | grep -q` under pipefail. A race — try up to 20 times; one refusal proves it."""
        write(self.staged, "/bin/sh\t-c\texit 7\n")
        old = self.copy("install-oldsig.sh", plant=[(NEW_SIG_CHECK, OLD_SIG_CHECK)])
        for _ in range(20):
            rc, out = self.install(old)
            if rc == 1 and "signature is not" in out:
                return
            shutil.rmtree(self.root, ignore_errors=True)
        self.fail("the old check never refused in 20 runs — the harness may not be running the installer whole")


if __name__ == "__main__":
    unittest.main(verbosity=2)
