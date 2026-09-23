# 07a · Case study — the fix that installed its own outage

> A worked example following [07 · Tools and requirements](07-tools-requirements.md). Generalised
> from a real fleet.
>
> Chapter 07 says pin your tools and know where they come from. This is about the part nobody
> checks: **what a package manager writes on your behalf, at a precedence level above your own
> config.**

---

## The short version

A vendor-supplied `git` had stopped working, so the obvious hardening was to install an
independent copy from a package manager. That was the right call for the right reason.

Within minutes the next push **hung forever** with no error, no timeout, and no output.

The package had installed a **system-level** config file containing one line:

```
[credential]
	helper = osxkeychain
```

Nothing about that line is wrong. It is the sensible default. ⚠ **The problem is where it sits.**

---

## The mechanism, in three facts

**① Credential helpers are a list, not a value.** Multiple entries accumulate and are tried in
order until one answers. This is a documented feature, used for exactly the kind of per-host
override many people already have.

**② Config levels stack, and the system level comes FIRST.** So the entry the package manager
installed is tried **before** anything in the user's own config. Adding your own helper does not
replace it; it appends *after* it.

**③ The helper name resolves relative to the binary that runs it.** A bare helper name is found in
the calling binary's own support directory — so the same one word means **the vendor's helper** when
the vendor's git runs, and **the package manager's helper** when the new git runs. Two different
executables, same config line.

On this platform the credential store's access control is **per-executable**. The stored credential
had been authorised for the vendor's helper. The new one was a stranger, so the operating system did
the correct and catastrophic thing: **it raised a graphical permission prompt** — on an unattended
machine, inside a non-interactive process. The push waited for a click that would never come.

---

## Two fixes that did not work, and why they are instructive

### Attempt 1 — set the helper in the user config

Reasonable, and useless. The user level is **lower precedence**, so this only *appended* a second
entry. The package manager's line was still tried first, still hung.

⚠ **"I configured it" and "my configuration is the one being used" are different claims.** The first
was true throughout.

### Attempt 2 — leave the working helper first, add the bare name as a fallback

This looked strictly safer: try the known-good one, fall back if it fails. It **re-broke the push**.

⚠ **On a successful authentication, the tool calls every helper in the chain to store the result.**
The lookup stops at the first answer; the *write-back* does not. So the hanging helper was invoked
anyway, on the success path, by a fallback that could never be reached on the failure path.

> **A fallback is not free. It is another thing that runs.**

---

## The fix that worked

The tool has a documented **reset** idiom: an empty value discards everything accumulated so far.

```
[credential]
	helper =                              # discard the system-level entry
	helper = /absolute/path/to/the/known-good/helper
```

Two properties make this right where the others were wrong: it is **order-aware** — placed after the
system entry, it erases it rather than competing with it — and it is **explicit**, naming a binary
rather than a word that resolves differently depending on who asks.

---

## The larger finding: the hardening did not harden what it was for

The package was installed so that a **scheduled background job** would stop depending on the vendor
toolchain. It did not achieve that.

⚠ **The job ran under the scheduler's default environment, which does not include the package
manager's binary directory.** So the job kept resolving the vendor's binary — exactly what the change
was meant to prevent — while the interactive shell, which *does* have that directory in its path,
resolved the new one.

**The change fixed the environment nobody was worried about and left the one that mattered untouched.**

⚠ And this was already written down. The same fleet had recorded, a week earlier, that a scheduled
job under a bare environment could not find a package-manager binary, with the note: *"it is invisible
from an interactive shell — running it by hand succeeds; only the job fails."* That note was not read
before the fix was proposed.

The real fix was to give the job an explicit environment path, and then to **prove which binary the
word now resolves to** rather than assume:

```
1. print the job's environment      →  the path is set
2. resolve the command under it     →  the package manager's copy      ← the only line that proves anything
3. run the job                      →  succeeds, and did real work
```

⚠ **Step 1 proves a setting exists. Only step 2 proves it changed what the command MEANS.** Stopping
at step 1 is how the first version of this fix was declared done.

---

## The transferable rules

> ⚠ **Installing a tool can install configuration.** After adding any package that ships defaults,
> ask what files it wrote outside your own config, and at what precedence.

> ⚠ **A bare command or helper NAME is a relative reference.** It resolves against whoever is
> asking. When two implementations coexist, prefer an absolute path for anything load-bearing.

> ⚠ **Know whether your tool's config is a single value or an accumulating list.** For a list, adding
> is not replacing, and there is usually a documented way to reset — find it before layering.

> ⚠ **An unattended process cannot answer a prompt.** Any credential path that *can* become
> interactive will eventually hang something with no error at all. That is worse than failing.

---

## What it cost

A hung push, two wrong fixes, and a hardening that had to be redone after it was believed complete —
all inside the session that was cleaning up an unrelated incident.

⚠ **The most expensive part was not the hang.** It was believing the original problem was solved for
several hours while the scheduled job — the thing the change existed to protect — was still running
the old binary.

---

Next: [08 · Networking](08-networking.md).
