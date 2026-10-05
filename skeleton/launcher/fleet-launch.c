/*
 * fleet-launch — run an allowlisted command as a child, so that macOS charges the child's file-access
 * approvals (network volumes, iCloud Drive …) to THIS program, which never changes — instead of to a
 * package-manager program that every update replaces, re-prompting on an unattended Mac where nobody
 * answers (guide/17c-case-the-check-that-stopped-the-server.md).
 *
 * Why it works (tested with three throwaway builds): macOS holds a launchd job's *responsible* process
 * accountable for what its children access, skipping Apple's own programs. An approved, unchanging,
 * non-Apple launcher therefore carries its approval across any change to what it runs; Apple's
 * /bin/bash does not.
 *
 * ⚠ BUILT ONCE PER MAC by install-fleet-launch.sh and NEVER REBUILT — a rebuild is a new program to
 *   macOS, and every approval would be asked for again.
 * ⚠ SIGNED WITH THE HARDENED RUNTIME (codesign -o runtime), which makes dyld ignore DYLD_* variables for
 *   this program — without it, DYLD_INSERT_LIBRARIES could load someone's code INTO the approved
 *   launcher, allowlist or not (tests/test_fleet_launch.py proves both ways).
 *
 * Usage:   fleet-launch /absolute/program [args...]
 * Runs it only if the exact argument list — joined by TAB — is a line in ALLOW, and ALLOW is a regular
 * file owned by ALLOW_UID (root) that group and others cannot write. Changing the list needs sudo, not
 * a rebuild. The child gets a FIXED minimal environment (HOME from the password database, never the
 * caller's): otherwise PYTHONPATH, DYLD_*, or a variable naming a program to run could make an allowed
 * command run someone else's code with this program's access.
 * Exit: the child's exit code (128+signal if killed) · 125 allowlist unusable · 126 not allowed ·
 * 127 could not start.
 */
#include <errno.h>
#include <fcntl.h>
#include <pwd.h>
#include <signal.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

#ifndef ALLOW                       /* tests build their own copy with a temporary list */
#define ALLOW "/usr/local/etc/fleet-launch.allow"
#endif
#ifndef ALLOW_UID
#define ALLOW_UID 0
#endif

static volatile pid_t child = 0;

static void forward(int sig) {      /* launchd stops the job by signalling us: pass it on */
    if (child > 0)
        kill(child, sig);
}

int main(int argc, char **argv) {
    if (argc < 2 || argv[1][0] != '/') {
        fprintf(stderr, "usage: fleet-launch /absolute/program [args...]\n");
        return 2;
    }
    struct stat st;
    int fd = open(ALLOW, O_RDONLY | O_NOFOLLOW);
    if (fd < 0 || fstat(fd, &st) != 0 || !S_ISREG(st.st_mode) || st.st_uid != (uid_t)ALLOW_UID ||
        (st.st_mode & (S_IWGRP | S_IWOTH))) {
        fprintf(stderr, "fleet-launch: %s is missing, not owned by uid %d, or writable by others — refusing\n",
                ALLOW, ALLOW_UID);
        return 125;
    }

    size_t need = 1;
    for (int i = 1; i < argc; i++)
        need += strlen(argv[i]) + 1;
    char *want = calloc(need, 1);
    if (!want)
        return 125;
    for (int i = 1; i < argc; i++) {
        if (i > 1)
            strcat(want, "\t");
        strcat(want, argv[i]);
    }

    FILE *f = fdopen(fd, "r");
    char *line = NULL;
    size_t cap = 0;
    ssize_t n;
    int allowed = 0;
    while (f && (n = getline(&line, &cap, f)) >= 0) {
        while (n > 0 && (line[n - 1] == '\n' || line[n - 1] == '\r'))
            line[--n] = '\0';
        if (n == 0 || line[0] == '#')
            continue;
        if (strcmp(line, want) == 0) {
            allowed = 1;
            break;
        }
    }
    free(line);
    if (f)
        fclose(f);
    if (!allowed) {
        fprintf(stderr, "fleet-launch: not in %s: %s\n", ALLOW, want);
        return 126;
    }

    struct passwd *pw = getpwuid(getuid());
    char tmp[1024] = "";
    confstr(_CS_DARWIN_USER_TEMP_DIR, tmp, sizeof tmp);
    static char e_home[1100], e_user[300], e_logname[300], e_path[1400], e_tmp[1100];
    snprintf(e_home, sizeof e_home, "HOME=%s", pw ? pw->pw_dir : "/");
    snprintf(e_user, sizeof e_user, "USER=%s", pw ? pw->pw_name : "");
    snprintf(e_logname, sizeof e_logname, "LOGNAME=%s", pw ? pw->pw_name : "");
    snprintf(e_path, sizeof e_path, "PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:%s/.local/bin",
             pw ? pw->pw_dir : "");
    snprintf(e_tmp, sizeof e_tmp, "TMPDIR=%s", tmp[0] ? tmp : "/tmp/");
    char *env[] = {e_home, e_user, e_logname, e_path, e_tmp, "LANG=en_US.UTF-8", NULL};

    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = forward;
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGHUP, &sa, NULL);

    /* Block the stop signals across the spawn, so one arriving before `child` is set is held, then
       forwarded — and start the child with them UNblocked (it would otherwise inherit our mask). */
    sigset_t stops, old, none;
    sigemptyset(&stops);
    sigaddset(&stops, SIGTERM);
    sigaddset(&stops, SIGINT);
    sigaddset(&stops, SIGHUP);
    sigemptyset(&none);
    sigprocmask(SIG_BLOCK, &stops, &old);
    posix_spawnattr_t attr;
    posix_spawnattr_init(&attr);
    posix_spawnattr_setsigmask(&attr, &none);
    posix_spawnattr_setflags(&attr, POSIX_SPAWN_SETSIGMASK);
    pid_t pid;
    int rc = posix_spawn(&pid, argv[1], NULL, &attr, &argv[1], env);
    posix_spawnattr_destroy(&attr);
    if (rc != 0) {
        sigprocmask(SIG_SETMASK, &old, NULL);
        fprintf(stderr, "fleet-launch: cannot start %s: %s\n", argv[1], strerror(rc));
        return 127;
    }
    child = pid;
    sigprocmask(SIG_SETMASK, &old, NULL);
    int status;
    while (waitpid(pid, &status, 0) < 0)
        if (errno != EINTR)
            return 127;
    if (WIFEXITED(status))
        return WEXITSTATUS(status);
    if (WIFSIGNALED(status))
        return 128 + WTERMSIG(status);
    return 1;
}
