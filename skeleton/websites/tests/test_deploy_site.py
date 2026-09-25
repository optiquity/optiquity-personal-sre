#!/usr/bin/env python3
"""Tests for skeleton/websites/deploy-site.sh — stdlib only.

    python3 skeleton/websites/tests/test_deploy_site.py

The script's job is a guardrail, so every test is about what it REFUSES as much as what it does.
Each one runs the real script as a subprocess, from inside a real throwaway git repo, against a
throwaway platform root (WEBSITES_ROOT) and a throwaway $HOME. Where more than one rsync is on
this machine (GNU rsync and macOS's openrsync), the publishing tests run against each.
"""
import os, shutil, subprocess, sys, tempfile, unittest

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.environ.get("DEPLOY_SITE_UNDER_TEST", os.path.join(os.path.dirname(HERE), "deploy-site.sh"))
BUILD_OK = "mkdir -p dist && echo hello > dist/index.html"


def rsync_dirs():
    """One PATH entry per distinct rsync binary found, so each implementation is exercised."""
    seen, dirs = set(), []
    for cand in (shutil.which("rsync"), "/usr/bin/rsync"):
        if cand and os.path.exists(cand):
            real = os.path.realpath(cand)
            if real not in seen:
                seen.add(real)
                dirs.append(os.path.dirname(cand))
    return dirs


class DeploySite(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="deploy-site-test-"))
        self.home = os.path.join(self.tmp, "home")
        self.root = os.path.join(self.tmp, "platform")
        self.srv = os.path.join(self.root, "srv")
        os.makedirs(self.home)
        os.makedirs(self.srv)
        self.repo = self.make_repo("site-a")
        self.register([("site-a", self.repo, BUILD_OK, "dist")])
        self.path_dir = rsync_dirs()[0]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ── helpers ─────────────────────────────────────────────────────────────────────────────────
    def make_repo(self, name):
        path = os.path.join(self.tmp, name)
        os.makedirs(path)
        subprocess.run(["git", "init", "-q", path], check=True)
        return path

    def register(self, rows, root=None):
        lines = ["# test registry", ""] + [" | ".join(r) for r in rows]
        with open(os.path.join(root or self.root, "sites.conf"), "w") as f:
            f.write("\n".join(lines) + "\n")

    def run_deploy(self, *args, cwd=None, root=None):
        env = {"HOME": self.home, "WEBSITES_ROOT": root or self.root,
               "PATH": self.path_dir + os.pathsep + os.environ.get("PATH", "/usr/bin:/bin")}
        return subprocess.run(["bash", SCRIPT, *args], cwd=cwd or self.repo, env=env,
                              capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60)

    def live(self, name="site-a"):
        return os.path.join(self.srv, name)

    def seed_live(self, name="site-a", files=("old.html",)):
        os.makedirs(self.live(name), exist_ok=True)
        for f in files:
            with open(os.path.join(self.live(name), f), "w") as fh:
                fh.write("live\n")

    # ── it publishes, from the repo it runs in ──────────────────────────────────────────────────
    def test_publishes_from_repo_root(self):
        for d in rsync_dirs():
            with self.subTest(rsync=d):
                self.path_dir = d
                shutil.rmtree(self.live(), ignore_errors=True)
                r = self.run_deploy()
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("site:   site-a (PRODUCTION)", r.stdout)
                self.assertTrue(os.path.isfile(os.path.join(self.live(), "index.html")))

    def test_resolves_from_subdirectory(self):
        sub = os.path.join(self.repo, "src", "deep")
        os.makedirs(sub)
        r = self.run_deploy(cwd=sub)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(os.path.join(self.live(), "index.html")))

    def test_staging_goes_to_its_own_root(self):
        r = self.run_deploy("--staging")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isfile(os.path.join(self.live("site-a-stg"), "index.html")))
        self.assertFalse(os.path.exists(self.live()), "staging must not touch production")

    def test_publish_mirrors_the_output(self):
        for d in rsync_dirs():
            with self.subTest(rsync=d):
                self.path_dir = d
                self.seed_live(files=("stale.html",))
                r = self.run_deploy()
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertFalse(os.path.exists(os.path.join(self.live(), "stale.html")),
                                 "a file no longer in the build must leave the live site")

    # ── what it refuses ─────────────────────────────────────────────────────────────────────────
    def test_site_argument_refused(self):
        other = self.make_repo("site-b")
        self.register([("site-a", self.repo, BUILD_OK, "dist"), ("site-b", other, BUILD_OK, "dist")])
        r = self.run_deploy("site-b")
        self.assertEqual(r.returncode, 2)
        self.assertIn("no site argument", r.stderr)
        self.assertEqual(os.listdir(self.srv), [], "a refused call publishes nothing")

    def test_unregistered_repo_refused(self):
        stranger = self.make_repo("stranger")
        r = self.run_deploy(cwd=stranger)
        self.assertEqual(r.returncode, 1)
        self.assertIn("not a registered site", r.stderr)
        self.assertEqual(os.listdir(self.srv), [])

    def test_not_a_git_repo_refused(self):
        plain = os.path.join(self.tmp, "plain")
        os.makedirs(plain)
        r = self.run_deploy(cwd=plain)
        self.assertEqual(r.returncode, 1)
        self.assertIn("not inside a git repository", r.stderr)

    def test_missing_registry_refused(self):
        os.remove(os.path.join(self.root, "sites.conf"))
        r = self.run_deploy()
        self.assertEqual(r.returncode, 1)
        self.assertIn("no site registry", r.stderr)

    def test_repo_registered_twice_refused(self):
        self.register([("site-a", self.repo, BUILD_OK, "dist"), ("site-z", self.repo, BUILD_OK, "dist")])
        r = self.run_deploy()
        self.assertEqual(r.returncode, 1)
        self.assertIn("registered 2 times", r.stderr)
        self.assertEqual(os.listdir(self.srv), [])

    def test_names_that_could_escape_or_collide_refused(self):
        for bad in ("../escape", "Site-A", "site-a-stg", "-x", "a/b"):
            with self.subTest(name=bad):
                self.register([(bad, self.repo, BUILD_OK, "dist")])
                r = self.run_deploy()
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("not allowed", r.stderr)
                self.assertEqual(os.listdir(self.srv), [])
        self.assertFalse(os.path.exists(os.path.join(self.root, "escape")))

    def test_output_outside_the_repo_refused(self):
        outside = os.path.join(self.tmp, "elsewhere")
        os.makedirs(outside)
        with open(os.path.join(outside, "secret.txt"), "w") as f:
            f.write("not a site\n")
        os.symlink(outside, os.path.join(self.repo, "linked"))
        for out in ("../elsewhere", "linked", ".", ""):
            with self.subTest(out=out):
                self.register([("site-a", self.repo, "-", out)])
                r = self.run_deploy()
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertFalse(os.path.exists(os.path.join(self.live(), "secret.txt")))

    def test_failed_build_publishes_nothing(self):
        self.seed_live()
        self.register([("site-a", self.repo, "false", "dist")])
        r = self.run_deploy()
        self.assertEqual(r.returncode, 1)
        self.assertIn("build failed", r.stderr)
        self.assertEqual(os.listdir(self.live()), ["old.html"], "the live site must be untouched")

    def test_empty_output_refused_and_live_site_kept(self):
        self.seed_live()
        self.register([("site-a", self.repo, "mkdir -p dist", "dist")])
        r = self.run_deploy()
        self.assertEqual(r.returncode, 1)
        self.assertIn("EMPTY", r.stderr)
        self.assertEqual(os.listdir(self.live()), ["old.html"], "an empty build must not wipe the site")

    # ── modes ───────────────────────────────────────────────────────────────────────────────────
    def test_dry_run_writes_nothing(self):
        for d in rsync_dirs():
            with self.subTest(rsync=d, target="exists"):
                self.path_dir = d
                self.seed_live()
                r = self.run_deploy("--dry-run")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("DRY RUN", r.stdout)
                self.assertEqual(os.listdir(self.live()), ["old.html"])
        shutil.rmtree(self.live())
        r = self.run_deploy("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(os.path.exists(self.live()), "a dry run must not create the target")

    def test_no_build_publishes_existing_output(self):
        os.makedirs(os.path.join(self.repo, "dist"))
        with open(os.path.join(self.repo, "dist", "index.html"), "w") as f:
            f.write("prebuilt\n")
        self.register([("site-a", self.repo, "false", "dist")])
        r = self.run_deploy("--no-build")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("build:  skipped", r.stdout)
        self.assertTrue(os.path.isfile(os.path.join(self.live(), "index.html")))

    def test_root_override_moves_registry_and_serving_roots_together(self):
        """A crafted WEBSITES_ROOT can only redirect the caller into itself, never into the real root."""
        real_srv = os.path.join(self.home, "websites", "srv")
        os.makedirs(os.path.join(real_srv, "site-b"))
        crafted = os.path.join(self.tmp, "crafted")
        os.makedirs(crafted)
        self.register([("site-b", self.repo, BUILD_OK, "dist")], root=crafted)
        r = self.run_deploy(root=crafted)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(os.listdir(os.path.join(real_srv, "site-b")), [], "the real root must be untouched")
        self.assertTrue(os.path.isfile(os.path.join(crafted, "srv", "site-b", "index.html")))

    def test_help_exits_0_and_prints_usage(self):
        r = self.run_deploy("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("no site argument", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
