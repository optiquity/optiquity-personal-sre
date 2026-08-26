# Guide contents

The hub — platform-agnostic concepts (the *why*). New? Begin with **00 · Introduction**, then
read in order. Per-platform *how* lives in [`../platforms/`](../platforms/); starter files —
including the ready-to-run **monitoring module** — in [`../skeleton/`](../skeleton/).

| # | Doc | In one line |
|---|---|---|
| 00 | [Introduction](00-introduction.md) | **Start here** — the philosophy + the four minimal foundations of a personal-SRE operator. |
| 01 | [Concepts](01-concepts.md) | The model + vocabulary: nodes-as-roles, source-of-truth, the two-repo model. |
| 02 | [The operator](02-operator.md) | How you actually work with the AI operator — the propose→approve→act rhythm. |
| 03 | [Governance rules](03-governance-rules.md) | The rules the operator obeys, and *when it must stop and ask*. |
| 04 | [Structure](04-structure.md) | Projects, the registry, the status taxonomy, the optional dashboard, and the operator's `PLAYBOOK.md`. |
| 05 | [chezmoi](05-chezmoi.md) | Config as source of truth: the dev-clone → prod-source → pull+apply flow, by role. |
| 06 | [Secrets](06-secrets.md) | Zero-secrets-in-git: allowlist ignore files, vault/keychain, the `.env` recipe. |
| 07 | [Tools & requirements](07-tools-requirements.md) | Hard vs optional tools + the idempotent, role-aware installer pattern. |
| 08 | [Networking](08-networking.md) | Private mesh (Tailscale) + key-only SSH, the access-edge graph, and subnet-router / exit-node gateways (+ their traps). |
| 09 | [Permissions](09-permissions.md) | The two permission layers: CLI auto-approve presets + session rules. |
| 10 | [MCP](10-mcp.md) | External capabilities (GitHub, filesystem, …) — each a scoped capability grant. |
| 11 | [Agents & skills](11-agents-skills.md) | Subagents + the `SKILL.md` pattern; the multi-CLI config-location map. |
| 12 | [Multi-node](12-multinode.md) | The advanced layer: remote apply, session mobility, the fleet view. |
| 13 | [Monitoring](13-monitoring.md) | Knowing it works and hearing when it doesn't: health checks, alerting, and the update digest. |
| 14 | [Setup](14-setup.md) | The onboarding journey — the three tiers and what they share. |
| 15 | [Public/shared repos](15-sharing.md) | Publishing a scrubbed framework: derive-don't-copy + the grep-guard. |
| 16 | [Example projects](16-example-projects.md) | A catalog of worked, end-to-end examples of the operator owning install + maintenance. |

**Worked examples** — [`examples/`](examples/), catalogued in [15](16-example-projects.md): the
A/B/C/D/E series, each an end-to-end project the operator owns. Several ship starter files in
[`../skeleton/`](../skeleton/) — notably **[E16 · Health, alerting & the update digest](examples/E16-fleet-health-and-alerting.md)**,
whose tools live in [`../skeleton/monitoring/`](../skeleton/monitoring/).

**Starter files** — [`../skeleton/`](../skeleton/) is the parts bin: templates and ready-to-run
modules, each explained by the chapter it belongs to. Its
[README](../skeleton/README.md) indexes every entry and points back to that chapter.

**Platform spokes** (the *how*): [macOS](../platforms/macos.md) (complete) ·
[Windows](../platforms/windows.md) (partial) · [Linux](../platforms/linux.md) (partial) ·
[Raspberry Pi](../platforms/raspberry-pi.md) (partial) · [Cloud](../platforms/cloud.md) (stub).
