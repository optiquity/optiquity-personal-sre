# skeleton — the parts bin

Starter files you **copy into your own repo and fill in**. Everything here is generic: no real
hostnames, no secrets, `<placeholders>` throughout. Nothing in this folder runs as-is against your
fleet until you edit it.

This is a reference index. **Each entry is explained by the guide chapter it belongs to** — that's
where the *why* lives; this table is just the map back.

| Entry | What it is | Explained in |
|---|---|---|
| `CLAUDE.md.template` | The operator's rules file — the governance the AI reads at session start. | [03 · Governance](../guide/03-governance-rules.md) |
| `AGENTS.md.template` | The same rules for a second CLI, so behaviour matches whichever you invoke. | [11 · Agents & skills](../guide/11-agents-skills.md) |
| `settings/` | Three permission presets (permissive → cautious) for the CLI's auto-approve layer. | [09 · Permissions](../guide/09-permissions.md) |
| `mcp/` | MCP server configs — each one a scoped capability grant. | [10 · MCP](../guide/10-mcp.md) |
| `skills/` | Two worked `SKILL.md` examples (a vault read, a browser login). | [11 · Agents & skills](../guide/11-agents-skills.md) |
| `installers/` | The idempotent, role-aware install-script pattern. | [07 · Tools & requirements](../guide/07-tools-requirements.md) |
| `monitoring/` | **Ready-to-run**: health-check config + email alerting, a local probe, an update digest, install-conflict and stale-image checks, and the timers to schedule them. Has its own [README](monitoring/README.md). | [13 · Monitoring](../guide/13-monitoring.md) |
| `onboarding/` | The seed for a brand-new personal-SRE repo (registry, playbook, first docs). | [04 · Structure](../guide/04-structure.md) |
| `github/` | CI workflow — runs the secret-scan on every push, so the never-leak rule is enforced by a machine. | [15 · Public/shared repos](../guide/15-sharing.md) |
| `chezmoi.toml.example` | Config-manager settings: role/node data the templates branch on. | [05 · chezmoi](../guide/05-chezmoi.md) |
| `chezmoiignore.template` | What the config manager must never apply to a machine. | [05 · chezmoi](../guide/05-chezmoi.md) |
| `gitignore.template` | The allowlist-shaped ignore file — the structural half of zero-secrets-in-git. | [06 · Secrets](../guide/06-secrets.md) |
| `env.example` | The runtime-secrets file's shape. Copy to a real, git-ignored `.env`; **never commit the filled one.** | [06 · Secrets](../guide/06-secrets.md) |

> The secret-scan script itself (`grep-guard.sh`) lives at [`../scripts/`](../scripts/), not here —
> it guards the whole repo rather than being copied into yours.

## How to use this folder

1. **Don't copy it wholesale.** Take the pieces the chapter you're reading tells you to take.
   A working adoption starts with a rules file, a permission preset, and the ignore templates.
2. **Fill every `<placeholder>`.** They are deliberate: a file that still contains one is a file
   that hasn't been adapted to your fleet yet.
3. **Commit the `.template` / `.example`, never the filled secret file.** That split is the whole
   discipline — the shape is reviewable, the values stay on the node
   ([06 · Secrets](../guide/06-secrets.md)).
4. **Adopt gradually.** Nothing here is required all at once; each piece earns its place when a
   project needs it.
