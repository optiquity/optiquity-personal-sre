# websites — a multi-site starter

For a platform that serves several websites, each with **its own repo and its own AI session**.
Two files and a test. The *why* is in
[E17 · Public websites § 7](../../guide/examples/E17-public-websites.md#7-adding-site-n-must-be-trivial).

| File | What it is |
|---|---|
| `sites.conf.template` | The **site registry**: one line per site — name, repo path, build command, output dir. It lives on the **platform side**, never in a site's repo. |
| `deploy-site.sh` | Build the site and publish it. **Takes no site argument**: it finds the site by looking up the repo it is run from in the registry. |
| `tests/test_deploy_site.py` | Runs the real script against throwaway repos and a throwaway platform root, one test per thing it must refuse. |

## Set up

```
<websites-root>/                 default ~/websites (WEBSITES_ROOT moves it)
├── sites.conf                   from sites.conf.template, filled in
├── bin/deploy-site.sh           this script
└── srv/<name>/  srv/<name>-stg/ what your web server serves, one folder per site and stage
```

Then, from inside a site's repo (the root or any subdirectory):

```
<websites-root>/bin/deploy-site.sh              # build, publish to production
<websites-root>/bin/deploy-site.sh --staging    # build, publish to staging
<websites-root>/bin/deploy-site.sh --dry-run    # build, show what would change
<websites-root>/bin/deploy-site.sh --no-build   # publish the existing output
```

## What it guards, and what it does not

- **A site's session cannot publish another site.** There is no argument to point elsewhere, and
  the registry it consults is outside the repo the session works in. Keep the script there too:
  run it by its platform path, never from a copy inside a site repo, which the site's session
  could edit.
- **It fails closed:** an unregistered repo, a repo listed twice, a name or output folder that could
  escape its directory, a failed build, and an **empty** build output all refuse. The last matters
  most: publishing mirrors with `--delete`, so an empty build would otherwise delete the live site.
- ⚠ **It does not stop a session that means to do damage.** Sessions that run as the same OS user
  can reach each other's files directly. This makes cross-site damage by accident hard and visible;
  preventing it on purpose needs a separate OS user or container per site.

**Adding a site is more than a registry row.** Provision its serving roots, proxy block,
monitoring endpoint and backup in the same change: monitoring and backups do not follow a new site
on their own ([E17 § 5](../../guide/examples/E17-public-websites.md#5-monitoring-must-follow-the-traffic),
[§ 6](../../guide/examples/E17-public-websites.md#6-back-up-and-prove-the-restore)).

## Test

```
python3 skeleton/websites/tests/test_deploy_site.py
```

It needs `git` and `rsync`. On macOS it runs each publishing test against every rsync it finds
(Homebrew's GNU rsync and the system's openrsync are separate implementations).
