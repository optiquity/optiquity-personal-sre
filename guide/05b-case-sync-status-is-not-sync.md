# 05b · Case study — the status command that could not see the failure

> A worked example following [05 · chezmoi](05-chezmoi.md). Generalised from a real fleet,
> with the detail kept deliberately.
>
> Chapter 05 says the dotfile manager is the mechanism every other project stands on. This is
> what happens when the command you use to check it is *structurally incapable* of reporting
> the failure you care about.

---

## The short version

A laptop's dotfile sync stopped working. For two days it pulled nothing, fell sixteen commits
behind the repository, and reported itself **clean** the entire time.

Nothing was broken about the check being run. `status` did exactly what it is documented to do:
**compare the local source tree against the target files.** Both were internally consistent, so
it said so.

⚠ **It never fetches.** A machine can be arbitrarily far behind its remote and still pass that
check perfectly, because being behind is not a disagreement between source and target — it is a
disagreement between the local source and *the world*, which `status` does not look at.

**The question the operator was asking was "is this machine up to date?" The question the command
answers is "is this machine self-consistent?" Those are different questions, and only one of them
was being asked out loud.**

---

## What actually broke

The system git binary stopped running. On that platform the vendor's git refuses to execute until
a licence agreement is accepted, and **the licence re-arms after every toolchain upgrade**. The
sync agent shells out to `git pull`, so:

```
agent log:    git: exit status 69      (repeated, every run, for two days)
source HEAD:  frozen, 16 commits behind
agent exit:   1                        (on the healthy machine: 0)
status:       clean
```

Three of those four lines are screaming. The fourth is the one anybody would have looked at.

---

## Why the obvious signals were not enough

### "Check the exit code"

Reasonable, and insufficient. The same fleet had already been bitten by an upgrade that replaced
the binary a scheduled job pointed at, **silently killing the job on two machines**. It exited 78
with no output at all.

⚠ **A job that fails to *spawn* writes nothing and can leave a stale success code behind.** "Last
exit code" is a property of the last run that *happened*, not evidence that runs are still
happening. It cannot distinguish *succeeding* from *not running*.

### "Compare local HEAD against the remote"

Closer, and still wrong in a subtle way: both the local branch ref and the cached remote-tracking
ref are **only updated by a fetch**. When fetching is what broke, the two stay equal to each
other and the comparison reports agreement. **A broken fetch makes the comparison agree.**

---

## The signal that works

**The age of the fetch marker.**

Most git implementations rewrite a fetch-head marker file on **every successful fetch** — whether
or not anything new arrived. That property is what makes it useful:

| Question | Answer |
|---|---|
| Did anything change upstream? | Irrelevant |
| Did the last fetch succeed? | **Yes if the marker is fresh** |
| Did fetching stop? | **Yes if the marker is stale**, whatever any status command says |

⚠ **It measures the ACT, not the STATE.** A quiet system and a dead system look identical in every
state-based check and completely different in this one.

```
[OK  ] sync: both machines fetching
[FAIL] sync: server: last successful fetch 9.0 h ago (limit 3 h)
```

**Thresholds by role, not one global number.** The always-on server runs its agent every 30
minutes, so three hours is six consecutive missed runs and unambiguous. The laptop sleeps and
travels, so a long quiet period is a nap; it gets a full day before the same silence is treated as
a fault. ⚠ **An unreachable machine is UNKNOWN, never a failure** — a closed laptop is not an
outage, and a monitor that cries wolf at one teaches you to ignore it at the other.

---

## Proving it

A check that has never gone red is not a check. This one was proven in **both** directions before
being trusted: the fetch marker was back-dated past the limit and the check went **red** with the
right message; it was restored and the check went **green** again.

⚠ **Both directions matter.** A check that only ever goes red is as useless as one that never
does — you need evidence it *clears*, or the first real green is indistinguishable from a bug.

---

## The transferable rule

> ⚠ **Before trusting a status command, ask what it actually compares.** If the failure you fear
> lives outside the two things it compares, it cannot report that failure — and it will say so in
> the most reassuring possible way.

This generalises well past dotfiles:

- A backup tool reporting the **last backup succeeded** cannot tell you backups stopped being
  attempted.
- A replication check comparing **two local values** cannot tell you the feed went away.
- A config manager reporting **no drift** cannot tell you it has not been told about new config.

**In each case the fix has the same shape: find something the system rewrites as a side effect of
the work actually happening, and watch that instead.** A timestamp touched only by success is
worth more than any number of internally consistent reports.

---

## What it cost

Two days of a machine silently not receiving changes — including, with some irony, **the fix for
an unrelated fault that had been pushed specifically to reach it.**

Nothing was corrupted and nothing was lost; the machine simply stopped moving while every
instrument said it was fine. ⚠ **That is the expensive kind of failure**, because there is no
moment at which anyone is prompted to look.
