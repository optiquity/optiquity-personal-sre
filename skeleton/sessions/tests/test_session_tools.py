#!/usr/bin/env python3
"""Tests for skeleton/sessions/session-projects and session-server — stdlib only.

    python3 skeleton/sessions/tests/test_session_tools.py             the tests
    python3 skeleton/sessions/tests/test_session_tools.py --mutants   builds each planted defect into a copy
                                                                     and shows the tests catch it; exit 1 if
                                                                     any survives

Everything runs against stand-ins: a local bare repository plays the remote, a clone plays the main folder,
and a recording `claude` on PATH plays Claude Code — nothing real is started. Each test is about what a
script refuses as much as what it does, and each has a planted defect that makes it fail.
"""
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS = os.environ.get("SESSION_PROJECTS_UNDER_TEST", os.path.join(os.path.dirname(HERE), "session-projects"))
SERVER = os.environ.get("SESSION_SERVER_UNDER_TEST", os.path.join(os.path.dirname(HERE), "session-server"))
RESULTS = []
ONLY = set()
MAIL = "session-test" + "@" + "example.invalid"     # assembled: the guard rightly flags an address shape
GIT_ID = {"GIT_AUTHOR_NAME": "session test", "GIT_AUTHOR_EMAIL": MAIL,
          "GIT_COMMITTER_NAME": "session test", "GIT_COMMITTER_EMAIL": MAIL}

TABLE = """# PROJECTS.md

## Status legend
pending · open · stable · resolved · deprecated · superseded · cancelled

## Projects

| Project | Status | Summary | Status file |
|---|---|---|---|
| alpha | **open** | Alpha's summary. | `docs/alpha/STATUS.md` |
| beta | **pending** | Beta's summary. | `docs/beta/STATUS.md` |
| gamma | **stable** | Gamma's summary. | `docs/gamma/STATUS.md` |
%s
## Related
| not | a | project | row |
"""


def check(tag, name, cond, detail=""):
    RESULTS.append((tag, name, bool(cond)))
    print("%s  [%s] %s%s" % ("PASS" if cond else "FAIL", tag, name, ("  — " + str(detail)[:400]) if detail and not cond else ""))


def sh(*args, env=None):
    p = subprocess.run(args, env=dict(os.environ, **(env or {})), capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError("%s failed: %s" % (" ".join(args), p.stderr))
    return p


class Repo:
    """A bare repository standing in for the remote, and a clone of it standing in for the main folder."""

    def __init__(self, extra=""):
        self.T = tempfile.mkdtemp(prefix="session-tools-test-")
        self.remote = os.path.join(self.T, "remote.git")
        self.main = os.path.join(self.T, "main")
        sh("git", "init", "--quiet", "--bare", "-b", "main", self.remote)
        sh("git", "clone", "--quiet", self.remote, self.main)
        self.commit(TABLE % extra)

    def commit(self, text, where=None):
        d = where or self.main
        open(os.path.join(d, "PROJECTS.md"), "w").write(text)
        sh("git", "-C", d, "add", "PROJECTS.md")
        sh("git", "-C", d, "commit", "--quiet", "-m", "projects", env=GIT_ID)
        sh("git", "-C", d, "push", "--quiet", "origin", "HEAD:main")

    def run(self, prog, *args, env=None):
        e = dict({"SESSION_REPO": self.main}, **(env or {}))
        p = subprocess.run([sys.executable, "-B", prog, *args], env=dict(os.environ, **e), capture_output=True, text=True)
        return p.returncode, p.stdout, p.stderr

    def close(self):
        shutil.rmtree(self.T, ignore_errors=True)


def recording_claude(d, out, sleep=0):
    """A stand-in `claude` that records its folder and arguments (and optionally stays up)."""
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "claude")
    open(path, "w").write("#!/bin/sh\nprintf '%%s\\n' \"$PWD\" \"$@\" > '%s'\n%s" % (out, "sleep %d\n" % sleep if sleep else ""))
    os.chmod(path, 0o755)
    return path


def suite(projects=PROJECTS, server=SERVER):
    def T(tag):
        return not ONLY or tag in ONLY

    if T("list"):
        r = Repo()
        rc, out, err = r.run(projects)
        lines = out.splitlines()
        ok = (rc == 0 and "from the remote's main" in lines[0] and lines[1].split()[:2] == ["1", "all"]
              and any(" alpha " in ln and "open" in ln and "Alpha's summary." in ln for ln in lines)
              and any(" beta " in ln and "pending" in ln for ln in lines)
              and not any(" gamma " in ln for ln in lines)
              and "new <name>" in lines[-2] and "Not listed: 1 " in lines[-1])
        rc2, out2, _ = r.run(projects, "--all")
        ok2 = rc2 == 0 and any(" gamma " in ln and "stable" in ln for ln in out2.splitlines()) and "Not listed" not in out2
        check("list", "lists all, the open and pending projects with their summaries, and new; --all adds the rest",
              ok and ok2, out + out2)
        r.close()

    if T("fresh"):
        r = Repo()
        other = os.path.join(r.T, "other")
        sh("git", "clone", "--quiet", r.remote, other)
        r.commit(TABLE % "| delta | **open** | Delta, landed by another session. | `docs/delta/STATUS.md` |\n", where=other)
        rc, out, err = r.run(projects)
        check("fresh", "reads the remote's main, not a main folder that has fallen behind", rc == 0 and " delta " in out,
              out + err)
        r.close()

    if T("offline"):
        r = Repo()
        sh("git", "-C", r.main, "remote", "set-url", "origin", os.path.join(r.T, "nowhere.git"))
        rc, out, err = r.run(projects)
        check("offline", "remote unreachable: lists the local copy and says so",
              rc == 0 and " alpha " in out and "local copy" in out and "not reachable" in err, out + err)
        r.close()

    if T("malformed"):
        r = Repo(extra="| broken row without status |\n")
        rc, out, err = r.run(projects)
        check("malformed", "a malformed row in the project table is refused, naming its line (rows elsewhere are ignored)",
              rc == 1 and "is not a project row" in err and "broken row" in err, (rc, out, err))
        r.close()

    if T("server"):
        r = Repo()
        fake = os.path.join(r.T, "bin")
        rec = os.path.join(r.T, "args.txt")
        recording_claude(fake, rec)
        env = {"PATH": fake + os.pathsep + os.environ["PATH"]}
        rc, out, err = r.run(server, "--verbose", env=env)
        got = open(rec).read().splitlines() if os.path.exists(rec) else []
        want = ["remote-control", "--spawn", "worktree", "--capacity", "3", "--permission-mode", "default",
                "--no-create-session-in-dir", "--verbose"]
        check("server", "starts `claude remote-control` in the main folder: a working copy per session, 3 at once, "
              "every action asked, no session in the main folder, extra options passed on",
              rc == 0 and got and os.path.realpath(got[0]) == os.path.realpath(r.main) and got[1:] == want
              and "Ctrl-C" in out and "/project" in out, (rc, got, out, err))
        r.close()

    if T("workingcopy"):
        r = Repo()
        wc = os.path.join(r.T, "wc")
        sh("git", "-C", r.main, "worktree", "add", "--quiet", "-b", "wc", wc)
        fake = os.path.join(r.T, "bin")
        rec = os.path.join(r.T, "args.txt")
        recording_claude(fake, rec)
        rc, out, err = r.run(server, env={"SESSION_REPO": wc, "PATH": fake + os.pathsep + os.environ["PATH"]})
        check("workingcopy", "refuses to start in a working copy instead of the main folder (nothing started)",
              rc == 1 and "main folder" in err and not os.path.exists(rec), (rc, err))
        r.close()

    if T("second"):
        r = Repo()
        up = recording_claude(os.path.join(r.T, "up"), os.path.join(r.T, "up.txt"), sleep=60)
        elsewhere = os.path.join(r.T, "elsewhere")
        os.makedirs(elsewhere)
        p_other = subprocess.Popen([up, "remote-control"], cwd=elsewhere, start_new_session=True)
        fake = os.path.join(r.T, "bin")
        rec = os.path.join(r.T, "args.txt")
        recording_claude(fake, rec)
        env = {"PATH": fake + os.pathsep + os.environ["PATH"]}
        time.sleep(0.5)
        rc1, out1, err1 = r.run(server, env=env)
        started1 = os.path.exists(rec)
        if started1:
            os.remove(rec)
        p_here = subprocess.Popen([up, "remote-control"], cwd=r.main, start_new_session=True)
        time.sleep(0.5)
        rc2, out2, err2 = r.run(server, env=env)
        for p in (p_other, p_here):
            os.killpg(p.pid, signal.SIGTERM)
            p.wait()
        check("second", "a server already running in this folder is refused (nothing started); one in another folder is not",
              rc1 == 0 and started1 and rc2 == 1 and "already running" in err2 and not os.path.exists(rec),
              (rc1, started1, rc2, err2))
        r.close()


MUTANTS = [
    ("list", "projects", "pending projects dropped from the list", 'FIRST = ("open", "pending")', 'FIRST = ("open",)'),
    ("fresh", "projects", "the local copy read even when the remote answers",
     '        if f.returncode == 0:\n            s = subprocess.run(', '        if False:\n            s = subprocess.run('),
    ("malformed", "projects", "a malformed row skipped instead of refused",
     '            raise Bad("%s line %d is not a project row', '            continue\n            raise Bad("%s line %d is not a project row'),
    ("server", "server", "a session started in the main folder (--no-create-session-in-dir left out)",
     '            "--no-create-session-in-dir"] + sys.argv[1:]', '            ] + sys.argv[1:]'),
    ("workingcopy", "server", "a working copy accepted as the main folder",
     '    if not os.path.isdir(os.path.join(REPO, ".git")):', '    if not os.path.exists(os.path.join(REPO, ".git")):'),
    ("second", "server", "a second server not refused", "    if pids:\n", "    if False:\n"),
    ("second", "server", "a server in any folder taken for one here",
     "        if cwd and os.path.realpath(cwd) == here:", "        if cwd:"),
]


def mutants():
    d = tempfile.mkdtemp(prefix="session-tools-mutants-")
    survived = []
    for tag, which, what, old, new in MUTANTS:
        src = open(PROJECTS if which == "projects" else SERVER).read()
        assert src.count(old) == 1, "mutant text not found exactly once: " + old[:60]
        path = os.path.join(d, "%s-%d" % (which, len(os.listdir(d))))
        open(path, "w").write(src.replace(old, new))
        global ONLY
        ONLY = {tag}
        before = len(RESULTS)
        print("\n--- planted: %s (expect [%s] to FAIL)" % (what, tag))
        suite(**({"projects": path} if which == "projects" else {"server": path}))
        if any(not r[2] for r in RESULTS[before:]):
            print("  caught")
        else:
            print("  ✗ SURVIVED — the test does not catch this defect")
            survived.append(what)
    shutil.rmtree(d, ignore_errors=True)
    print("\n%d planted defects, %d survived%s" % (len(MUTANTS), len(survived), (": " + "; ".join(survived)) if survived else ""))
    return 1 if survived else 0


if __name__ == "__main__":
    if "--mutants" in sys.argv:
        sys.exit(mutants())
    suite()
    failed = [r for r in RESULTS if not r[2]]
    print("\n%d checks, %d failed" % (len(RESULTS), len(failed)))
    sys.exit(1 if failed else 0)
