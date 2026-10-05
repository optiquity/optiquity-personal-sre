# 17c · Case study — the health check that stopped the media server

> A worked example following [17 · Monitoring](17-monitoring.md), alongside
> [17a](17a-case-monitoring-the-proxy.md) and [17b](17b-case-loud-into-the-void.md). Generalised from a
> real fleet.
>
> 17a's probes measured the wrong thing; 17b's job reported into a file nobody read. Here the monitoring
> **caused** the outage — and the alert it raised pointed at the wrong layer.

---

## The short version

On a headless, always-on Mac, a routine package-manager update replaced the Python interpreter. The
fleet's local health check runs **as** that interpreter, from launchd, every 15 minutes. Its next read of
a mounted network share was, to macOS, a brand-new program touching a protected place — so macOS put up
a privacy prompt and **held the read until someone answered it**. Nobody was at the screen.

For about an hour and a half the check waited. The media server, which reads the same share, stopped
playing anything stored there. Answering the prompt on the screen — and a remount of the share in the
same minute — released everything; the record cannot say which of the two did it.

## What the alert said, and why it misled

The check's *"can I read the work folders?"* probe timed out, turned **unknown**, and after four unknowns
in a row it escalated, as designed ([§ 17](17-monitoring.md#a-probe-that-could-not-answer-has-not-told-you-anything)).
That took about 45 minutes. **The alert worked.** But it said *"can't read the share"* — which points at
the share, the network and the NAS, not at a dialog box on a screen in a closet.

## The wrong turn, kept because it is the useful part

Every first measurement pointed at the network file system. The NAS was idle and answering; the network
path was direct; and the Mac's NFS client had sent **zero requests in ten seconds**. All true. The
inference — "the NFS client is wedged" — was not. Zero requests meant the calls **never reached** NFS,
not that NFS refused to send them, and only one piece of evidence can tell those apart: **the kernel
stack of a stuck call.** It was taken *before* anything was remounted, and it ended in the sandbox:

```
__open_nocancel → mac_vnode_check_open → hook_vnode_check_open (Sandbox)
  → … → approval_solicit → approval_response_wait → __WAITING_ON_APPROVAL_FROM_SANDBOXD__
```

The `open()` stopped **before the file system**, waiting for a person. Twenty-seven of the media server's
threads were waiting at the same place.

A second trap hid the cause for an hour: every search of macOS's privacy log came back empty, because in
zsh **`log` is a shell built-in**, not `/usr/bin/log`. *"Nothing in the log"* was written into the record
before anyone noticed which `log` had run.

## The cause

The privacy service's own log, read with `/usr/bin/log`, had it all. The new interpreter asked for
network-volume access the first time the check ran after the update, and the request sat unanswered for
about an hour and a half. The media server's own requests reached the privacy service **the moment that
prompt was answered** (the share was being remounted in the same minute), and were allowed from the
permission it already had — consistent with later requests queuing behind a pending prompt, but **not
proven**.

One more fact settles which program is asked. Another scheduled service on the same Mac ran **the same
updated interpreter** and kept working throughout. It was started by a program that had *not* changed.
macOS charges an access to the job's *responsible* program — the one launchd started — and skips Apple's
own programs. An approved program that never changes carries its approval to whatever it runs.

## What was built

**Detection — an alarm for a prompt nobody is answering.** macOS's privacy service logs every request
and its answer. A check reads that log and alerts on any request still unanswered after five minutes.
The details are where it would have gone wrong:

- **A log with no requests and no replies at all is *unknown*, not "no prompts".** Silence is what a
  broken query also prints.
- **Watch the per-user service, not the system one.** The system-wide privacy service logs some requests
  that never get an answer line at all: the first live run raised 22 false alarms until that was
  filtered — and the fixture built from the incident had passed, because it held only requests that do
  get answers.
- **Call `/usr/bin/log` by full path.**
- **Proven on a real prompt left unanswered on purpose:** the email arrived about five minutes later.
  ⚠ And that proof found one more defect: the alert's **subject** listed three older failures first and
  was cut at 60 characters, so the prompt was not in it. New failures now come first, and a prompt alerts
  in a mail of its own. An alert is proven by what the person *reads*.

**Prevention — a launcher that never changes.** A test with three throwaway builds answered the design
question outright:

| How the new program was started | What macOS did |
|---|---|
| launchd started it directly | **prompted**, and the job waited until answered |
| launchd started Apple's `bash`, which ran it | **prompted for the new program** — Apple's shell is never the one charged |
| launchd started an already-approved, non-Apple program, which ran it | **no prompt** |

So the jobs now start through a tiny launcher, approved once per Mac and **never rebuilt**. Because it
carries approvals, it is built defensively: it runs only command lines listed exactly in a file only an
administrator can change; it gives them a fixed environment, so a variable cannot point an allowed command
at someone else's code; it is signed with the hardened runtime, so injected libraries are ignored; and it
passes stop signals to its child. Network shares and iCloud Drive alike are charged to it, as the
privacy log showed on the first run. ⚠ Its installer refused a correct signature on its first real run —
a `codesign | grep -q` line under `set -o pipefail` ([§ 17, the shell traps](17-monitoring.md)). The
installer is now tested whole, the way its user runs it.

## Three things that would each have caught it sooner

- **After any package update on an unattended Mac, look at its screen and run each scheduled job that
  touches a protected place once.** The update was the trigger, and its time was known.
- **A check for scheduled jobs running far longer than usual.** A file-sync job sat almost two hours on
  the same day, unnoticed.
- **The privacy log itself.** It recorded the request, the program and the wait from the first minute.
  It was free to read; nothing was reading it.

## The transferable rules

> ⚠ **Your monitoring is a program too.** It needs the same approvals, receives the same updates, and can
> cause the outage it exists to report.

> ⚠ **When the kernel can tell you where a call is waiting, ask it before you change anything.** A
> remount, a restart or a reboot destroys the one piece of evidence that separates *"refused"* from
> *"never sent"*.

> ⚠ **On macOS, an approval belongs to a program, and an update makes a new program.** Anything that runs
> unattended needs either a launcher that never changes, or a person at the screen after every update.

> ⚠ **An alert is proven by what the person reads**, not by the row turning red.

---

Next: [18 · Setup](18-setup.md).
