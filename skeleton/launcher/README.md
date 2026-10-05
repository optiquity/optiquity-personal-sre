# launcher — keep macOS approvals across package updates (optional, macOS only)

**The problem** ([guide 17c](../../guide/17c-case-the-check-that-stopped-the-server.md)). macOS asks before
a program it has not approved reads a protected place — a mounted network share, iCloud Drive — and the
read **waits until someone answers**. A scheduled job is charged to the first non-Apple program it runs
(the package manager's `python3`, `rsync` …), and **every update of that program is a new program**, asked
again, on an unattended Mac where nobody answers.

**The fix.** `fleet-launch` is a tiny program you **build once per Mac and never rebuild**. A scheduled job
starts its script *through* it, so macOS charges the job's access to `fleet-launch` — approved once, never
changing — and updates to what it runs no longer ask again. Tested: started directly or by Apple's
`bash`, a newly built program was prompted; started by an already-approved launcher, it was not.

| File | What |
|---|---|
| `fleet-launch.c` | the launcher (≈150 lines of C) |
| `install-fleet-launch.sh` | builds, signs and installs it root-owned, with its allowlist; refuses to rebuild |
| `fleet-launch.allow.example` | the allowlist format |
| `tests/test_fleet_launch.py` | 16 tests, including the installer run whole; macOS only (skipped elsewhere) |

## Because it carries approvals, it is built defensively

- **It runs only what you list**, exactly: a command runs only if its whole argument list (joined by TAB)
  is a line in `/usr/local/etc/fleet-launch.allow`, a regular file owned by root that nobody else can
  write. Otherwise any program running as you could borrow its access.
- **A fixed, minimal environment** for the command (`HOME` from the password database, a fixed `PATH`) — so
  `PYTHONPATH`, a `DYLD_*` variable, or a variable naming a program to run cannot make an allowed command
  run someone else's code.
- **Signed with the hardened runtime** (`codesign -o runtime`), so the dynamic loader ignores `DYLD_*` for
  the launcher itself and nobody can inject a library into it. The installer refuses any other signature.
- **Stop signals reach the command**, so launchd can still stop the job.

⚠ **Its limits, stated:** the allowlist names scripts *you* can edit, so code that can rewrite those
scripts can still run through the launcher — just as it could already rewrite the jobs themselves. It
protects against library injection and environment tricks, **not against a compromised account.**

## Install (once per Mac, in your own Terminal)

1. Stage your allowlist at `~/.config/fleet-launch/fleet-launch.allow` (or set `FLEET_LAUNCH_STAGED`) —
   from `fleet-launch.allow.example`, ideally through your config manager, per Mac.
2. Run `skeleton/launcher/install-fleet-launch.sh`. It needs Xcode's command-line tools, asks for your
   password (sudo), and ends with two ✓ lines. To change the list later: `install-fleet-launch.sh --list`.
3. Point each job at it — in its launchd plist, put the launcher first:

   ```xml
   <key>ProgramArguments</key>
   <array>
       <string>/usr/local/libexec/fleet-launch</string>
       <string>/Users/<you>/.local/bin/your-job</string>
   </array>
   ```
   An `EnvironmentVariables` key no longer reaches the script — the launcher sets the environment.
4. Reload each job and **approve the launcher's prompts once, at the screen**, one per kind of access
   (network volumes; iCloud Drive). macOS's privacy log should now name `fleet-launch` as the program
   responsible for each request.

Then the update procedure still includes one check, the first time each program the jobs run is updated:
run the jobs and confirm no prompt appears — the proof that the launcher is doing its job on your Mac.
Pair it with the `prompts` check in [`../monitoring/`](../monitoring/), which alerts on any prompt left
waiting, launcher or not.
