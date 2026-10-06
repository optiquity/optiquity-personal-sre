#!/usr/bin/env python3
"""test_pre_commit_hook — the pre-commit hook works, installed exactly as documented, in the two cases that
once broke it: `git commit -a`, and a commit from a linked working copy (`git worktree`).

The self-test inside the hook used to inherit the real repository's GIT_DIR / GIT_INDEX_FILE: from a working
copy it wrote `core.bare = true` into the shared config (every checkout then failed), and under `commit -a`
it staged its planted leaks into the real commit, so the commit died with "invalid object" after the scan
had read the wrong index. Each case here checks that a clean commit goes through, that a leak is still
blocked, and that the repository is intact afterwards.

  python3 scripts/test_pre_commit_hook.py                     the hook in this repo
  python3 scripts/test_pre_commit_hook.py --guard <path>      another grep-guard.sh — e.g. the version before
                                                              the fix, to see these checks fail (exit 1)
Writes only into TMPDIR. Exit 1 on any FAIL. Takes about a minute: every commit runs the full self-test.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GUARD = sys.argv[sys.argv.index("--guard") + 1] if "--guard" in sys.argv else os.path.join(HERE, "grep-guard.sh")
HOOK = os.path.join(HERE, "pre-commit.hook")
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
MAIL = "hook-test" + "@" + "example.invalid"          # assembled: the guard rightly flags an address shape
ENV.update(GIT_AUTHOR_NAME="hook test", GIT_AUTHOR_EMAIL=MAIL, GIT_COMMITTER_NAME="hook test", GIT_COMMITTER_EMAIL=MAIL)
LEAK = "host " + ".".join(["192", "168", "1", "5"]) + " is private\n"     # assembled: never literal in this repo
RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append(bool(cond))
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name, ("  — " + str(detail)[-400:]) if detail and not cond else ""))


def git(cwd, *args):
    p = subprocess.run(["git", *args], cwd=cwd, env=ENV, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return p.returncode, p.stdout + p.stderr


def head(cwd):
    return git(cwd, "rev-parse", "HEAD")[1].strip()


def make_repo():
    t = tempfile.mkdtemp(prefix="hook-test-")
    repo = os.path.join(t, "repo")
    git(t, "init", "-q", "-b", "main", repo)
    os.makedirs(os.path.join(repo, "scripts"))
    shutil.copy(GUARD, os.path.join(repo, "scripts", "grep-guard.sh"))
    shutil.copy(HOOK, os.path.join(repo, "scripts", "pre-commit.hook"))
    for f in ("grep-guard.sh", "pre-commit.hook"):
        os.chmod(os.path.join(repo, "scripts", f), 0o755)
    open(os.path.join(repo, "README.md"), "w").write("a clean file\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--no-verify", "-m", "seed")
    os.symlink("../../scripts/pre-commit.hook", os.path.join(repo, ".git", "hooks", "pre-commit"))   # as documented
    return t, repo


def intact(repo):
    bare = git(repo, "config", "--bool", "core.bare")[1].strip()
    rc, _ = git(repo, "status", "--short")
    return bare == "false" and rc == 0, "core.bare=%s, git status rc=%d" % (bare, rc)


def main():
    t, repo = make_repo()
    # A: git commit -a
    open(os.path.join(repo, "README.md"), "w").write("a clean file, edited\n")
    before = head(repo)
    rc, out = git(repo, "commit", "-a", "-q", "-m", "clean edit")
    check("commit -a: a clean change is committed", rc == 0 and head(repo) != before, out)
    open(os.path.join(repo, "README.md"), "w").write(LEAK)
    before = head(repo)
    rc, out = git(repo, "commit", "-a", "-q", "-m", "a leak")
    check("commit -a: a leak is still blocked, by the scan of the real commit", rc != 0 and head(repo) == before
          and "grep-guard" in out and "invalid object" not in out, out)
    ok, why = intact(repo)
    check("commit -a: the repository is intact afterwards", ok, why)
    git(repo, "checkout", "--", "README.md")

    # B: a commit from a linked working copy
    wt = os.path.join(t, "wt")
    git(repo, "worktree", "add", "-q", wt, "-b", "side")
    open(os.path.join(wt, "new.txt"), "w").write("clean\n")
    git(wt, "add", "new.txt")
    before = head(wt)
    rc, out = git(wt, "commit", "-q", "-m", "clean from a working copy")
    check("working copy: a clean commit goes through", rc == 0 and head(wt) != before, out)
    ok, why = intact(repo)
    check("working copy: the shared repository is intact (core.bare false, the main checkout works)", ok, why)
    open(os.path.join(wt, "leak.txt"), "w").write(LEAK)
    git(wt, "add", "leak.txt")
    before = head(wt)
    rc, out = git(wt, "commit", "-q", "-m", "a leak from a working copy")
    check("working copy: a leak is still blocked", rc != 0 and head(wt) == before and "grep-guard" in out, out)
    ok, why = intact(repo)
    check("working copy: still intact after the blocked commit", ok, why)

    shutil.rmtree(t, ignore_errors=True)
    print("\n%d checks, %d failed" % (len(RESULTS), RESULTS.count(False)))
    return 1 if False in RESULTS else 0


if __name__ == "__main__":
    sys.exit(main())
