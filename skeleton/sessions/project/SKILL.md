---
name: project
description: Choose the project this session works on. Lists the projects, records the choice so the lock helper knows it, and gives the operator the /rename line. The operator runs it at the start of a session.
argument-hint: "[number, project name, all, or new <name>]"
disable-model-invocation: true
allowed-tools:
  - Bash(session-projects)
  - Bash(session-projects *)
---

# /project — choose this session's project

> Copy this folder to `.claude/skills/project/` in your repo — tracked, so every working copy has it. It
> needs `session-projects` installed on each machine (`../session-projects`), and your lock helper reading
> the recorded project (`../BUILD-LOCK-HELPER.md`). How it is used: `../STARTING.md` part D.
>
> ⚠ **A command cannot rename a session** in Claude Code — only the operator's own `/rename` can. So this
> command ends by giving the operator the line to paste.

## The projects, from the remote's main

!`session-projects`

## What to do

The operator's choice, if they typed one after `/project`: **$ARGUMENTS** — if that is empty, show them the
list above exactly as printed and ask them to choose: a number, a project's name, `all`, or `new <name>`. A
name not in the list may be a finished project: check it with `session-projects --all` (new work on a finished
project starts the same way).

1. **Find where you run:** `hostname -s` (the machine — write it in lower case) and `git rev-parse
   --show-toplevel` (your working copy). There are three cases:
   - **The main folder** of the repo: only `all` is valid — this is the general session. For anything else,
     tell the operator to open the session from the session server or with `claude -w <project>`, and stop.
   - **A `claude -w <project>` working copy** (`.claude/worktrees/<project>/`, where `<project>` is in the
     list): it already belongs to that project. If the operator chose a different one, say so and stop.
   - **A session-server working copy** (under `.claude/worktrees/`, its folder named by the server, not after a
     project): write the choice — the project's name, or `general` for `all` — as the only line of
     `<working copy>/.claude/session-project`. That file is gitignored, and it is how the lock helper knows
     your project. Write no other file.
2. **For `new <name>`:** the name must be lower-case letters, digits and hyphens, and not already a project
   (`session-projects --all`). Then follow part C of the starting guide. Locks stay refused until the
   project's opening commit lands — that is expected.
3. **For `all`:** one general session at a time. If the main folder's general session may still be open, say so
   plainly and ask the operator before going on.
4. **Read before working:** the project's `docs/<project>/STATUS.md`, its design and its postmortem; for `all`,
   the registry and part A of the starting guide.
5. **Tell the operator, in plain words, one line each:**
   - where you run: the machine and your working copy — **on the machine, not in a cloud container**, whatever
     the session server's own instructions say; you follow this repo's rules, and your work lands on the
     remote's main the way the rules say — never by pushing a branch of your own;
   - the project you now work on.

   Anything else you found — an out-of-date status file, a question for the operator — comes after those two
   lines.
6. **End the message with the line to paste, on a line of its own, with nothing after it:** one short sentence —
   *paste this to name the session; any name no open session uses is fine* — then `/rename <machine>-<project>`
   (for `all`: `/rename <machine>-all`) alone in a code block, so it copies cleanly. ⚠ **Never inside a list or
   before other text:** in the source fleet the line was given as one bullet among several, and the operator
   missed it. The operator renames **before** you take any lock, because a lock records your name.
