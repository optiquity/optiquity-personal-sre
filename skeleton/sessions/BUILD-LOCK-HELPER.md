# Build the lock helper

> ⛏ **Designed, not yet proven in use.** No reference code is published yet; your session builds the
> helper from this description and its tests. When a proven version exists, it will appear beside this
> file. Part of the setup in [`README.md`](README.md) (Part 1, step 6).

The helper is a small command your sessions call to take, release, list and check locks. **It is the
only thing that writes in `locks/`.** Its whole value is that it is the one writer and that it refuses
everything outside its job — so build the refusals first.

## What it does

| Command | Does |
|---|---|
| `take <resource> [project]` | Adds the lock file for this session; `project` defaults to `ALL`. Records the **holder's project** too: its working copy's folder name, or a `--for <project>` flag, or `general` in the main folder |
| `release <resource> [project]` | Removes this session's own lock file |
| `list` | Shows every current lock, read from the remote |
| `mine` | Shows the locks held in this session's name — run on start, on resume, after a context summary |
| `takeover <resource> [project]` | Replaces a stale holder's lock with this session's, recording whose it was |

## How it must work

1. **Read the remote's main, never a local copy.** A local checkout can be minutes behind.
2. **Build one commit** on top of that main that adds, changes or removes **exactly one file under
   `locks/`** — without touching any working copy or the main folder. Git can build a commit from a tree
   directly; no checkout is needed.
3. **Check its own commit before pushing**: one file changed, under `locks/`, nothing else. Refuse
   otherwise. This check is what lets the operator give lock commits a standing approval.
4. **Push without force.** The remote accepts a push only if main has not moved since the helper read
   it. If two sessions race, one is accepted; the other is refused, reads main again, and reports the
   lock as held.
5. **Fixed commit-message prefix** (`lock:` / `unlock:`), so lock commits can be filtered out of history.
6. **Time-limit every network call and fail loudly.** Never assume a lock was taken.

## What it must refuse

- A resource name not in `locks/README.md`'s list.
- A project that is not an existing project folder, or `ALL`.
- A **holder's project** that has no folder on the remote's main — so a new project's session cannot
  take any lock until its opening commit has landed.
- A second lock on a resource that already has one, **unless** a permission is recorded (from the
  holder, or from the operator).
- Releasing a lock this session does not hold.
- A lock file it cannot read (a hand edit) — report it, never overwrite it.
- Anything when the remote is unreachable — and say so plainly.

## Tests — each with the planted defect that proves it can fail

| Test | Planted defect it must catch |
|---|---|
| An unlisted resource name is refused | the list check removed |
| A second lock without a recorded permission is refused — as a project lock under `ALL`, as `ALL` over a project lock, and as two project locks | the permission check removed |
| Two takes of the same lock at the same moment: exactly one succeeds | a variant that pushes with force (both "succeed") |
| A commit that would change a second file is refused before pushing | a variant that also writes outside `locks/` |
| Releasing another session's lock is refused | the holder check removed |
| An unreachable remote fails loudly and claims nothing | a wrong remote address |
| A lock taken from a working copy records that folder as the holder's project; one whose project is not on main is refused | the holder-project check removed |
| Two takeovers of one stale lock: exactly one succeeds | as the race above |

⚠ **A local bare repository can stand in for the git host in fast tests, but it cannot show how the real
host handles two pushes arriving together, its authentication, or its latency.** Run the race, the
takeover race and the unreachable case against the real host too, on a test resource name kept in the
list for that purpose.

## Deploying it

Install it once per machine through your config manager rather than running it from the repo — each
working copy has its own copy of the repo's files, so a helper run from a working copy could be an older
version than the one beside it.

⚠ **Then check it is installed — on each machine, with a command (`command -v <helper>`).** A config
manager that installs a folder like `~/.local/bin` from an allow-list skips a file missing from that
list without a word, and git's own ignore files are a separate list. In the source fleet the helper was
added to git's list, never to the config manager's, and sat uninstalled on every machine while its
records said "deployed" — found by chance a day later, while checking something else. Its tests passed
throughout, because they ran it from the repo.
