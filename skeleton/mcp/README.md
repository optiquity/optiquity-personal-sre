# MCP server config templates

Templates for the operator's external capabilities (guide/10-mcp.md). **Placeholders only —
never real tokens or personal paths.** Each server is a capability grant: enable only what a
project needs, scope it tightly, and know whether it's read-only or mutating.

## Files here

- `claude.mcp.json` — MCP servers for Claude Code (goes in its settings' `mcpServers`).
- `codex.mcp.toml` — the equivalent for Codex (`~/.codex/config.toml` MCP section).

## Rules (both from guide/06-secrets.md)

1. **No tokens in committed config.** Auth is read from the environment / secret store at
   launch (`${GITHUB_TOKEN}`), never a literal value.
2. **No personal paths.** Filesystem scopes are `$HOME`-relative or placeholders; fill your
   real paths locally, and keep them OUT of anything you publish.

## Trust checklist before enabling a server

- What can it *do* — read-only or can it mutate external state? Prefer least-capable variants.
- Scope it (a filesystem server → specific dirs, never `$HOME` root or a secret path).
- Provenance — prefer official/well-known servers; audit unknowns.
- Keep the CLI permission layer (guide/09) gating its dangerous tools on *ask*.
