# MCP server config templates

Templates for the operator's external capabilities (guide/10-mcp.md). **Placeholders only —
never real tokens or personal paths.** Each server is a capability grant: enable only what a
project needs, scope it tightly, and know whether it's read-only or mutating.

## Files here

- `claude.mcp.json` — MCP servers for Claude Code (goes in its settings' `mcpServers`).
- `codex.mcp.toml` — the equivalent for Codex (`~/.codex/config.toml` MCP section).

## The GitHub server — use GitHub's OFFICIAL one

Use **`github/github-mcp-server`** (GitHub's official server). The older community
`@modelcontextprotocol/server-github` npm package is **deprecated/archived (Apr 2025)** — don't
use it. Two deployment modes:

- **Local binary** (what the templates show): install `brew install github-mcp-server` (or run
  Docker `ghcr.io/github/github-mcp-server`), run as `github-mcp-server stdio`, authed by a
  `GITHUB_PERSONAL_ACCESS_TOKEN`. Best for control / GitHub Enterprise / offline.
- **Remote hosted:** `https://api.githubcopilot.com/mcp/` (OAuth, token in memory) — easiest if
  your CLI supports a remote/HTTP MCP endpoint; no local install.

**Scope it (least privilege — this is a capability grant):** limit toolsets with
`--toolsets=repos,issues,pull_requests` (20+ exist: actions, code_security, …), and add
**`--read-only`** to disable all mutations. A GitHub MCP that can merge PRs and delete branches
is a much bigger grant than a read-only one — grant deliberately (guide/09-permissions.md).

## Rules (both from guide/06-secrets.md)

1. **No tokens in committed config.** Auth is read from the environment / secret store at launch
   (e.g. `${GITHUB_PERSONAL_ACCESS_TOKEN}`), never a literal value.
2. **No personal paths.** Filesystem scopes are `$HOME`-relative or placeholders; fill your
   real paths locally, and keep them OUT of anything you publish.

## Trust checklist before enabling a server

- What can it *do* — read-only or can it mutate external state? Prefer least-capable variants.
- Scope it (a filesystem server → specific dirs, never `$HOME` root or a secret path).
- Provenance — prefer official/well-known servers; audit unknowns.
- Keep the CLI permission layer (guide/09) gating its dangerous tools on *ask*.
