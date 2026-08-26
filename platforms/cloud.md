# Platform spoke · Cloud

**Maturity: Stub — generic model only.** Cloud nodes are mostly **Linux nodes**
([linux.md](linux.md)) with a different *provisioning* and *secret-management* story. This is the
**generic, provider-agnostic** cloud model.

> **Provider-specific docs are coming later.** Cloud setups, IAM, secret managers, and use cases
> differ enough between providers that each warrants its own doc — planned as separate
> `platforms/cloud-aws.md`, `cloud-azure.md`, `cloud-gcp.md`, etc. This generic doc is the shared
> foundation they'll build on; the ⛏ TODO rows below mark where the per-provider specifics go.
> None of those provider docs exist yet — use this + [linux.md](linux.md) for now, and treat any
> provider detail here as illustrative until its dedicated doc lands.

## The key idea: a cloud node is a Linux `server` with cloud-native edges

Most of [linux.md](linux.md) applies unchanged — package manager, systemd, SSH, Tailscale,
chezmoi. What's *different* on cloud:

| Concept | Cloud twist |
|---|---|
| Provisioning ([13](../guide/14-setup.md)) | **cloud-init** / provider images / IaC (Terraform) instead of hand-setup |
| Secret store ([06](../guide/06-secrets.md)) | a **managed secret manager** (per provider) instead of a local keyring |
| Private mesh ([08](../guide/08-networking.md)) | Tailscale still works great; cloud VPCs/security-groups are an *additional* layer |
| Identity | cloud **IAM** roles/service accounts — often better than long-lived keys |
| Cost | a running cloud node costs money — scale-to-zero / ephemeral patterns matter |

## First-boot provisioning — cloud-init

The cloud analog of "run bootstrap.sh" is **cloud-init**: a first-boot config that installs the
core tools, pulls the repo, joins Tailscale, and applies chezmoi — all unattended. ⛏ TODO: a
generic cloud-init snippet that installs chezmoi + git + Tailscale and runs a first apply, with
the Tailscale auth key supplied from the provider's secret manager (never inline).

## Secrets on cloud — use the managed manager

The single biggest change from local platforms: **don't ship a local vault; use the provider's
secret manager** and IAM. This is *more* secure than a local keyring for a cloud node — secrets
never live on disk, and access is IAM-scoped.

| Provider | Secret manager | Identity | Status |
|---|---|---|---|
| **AWS** | Secrets Manager / SSM Parameter Store | IAM roles / instance profiles | ⛏ TODO |
| **Azure** | Key Vault | Managed Identities | ⛏ TODO |
| **GCP** | Secret Manager | Service Accounts / Workload Identity | ⛏ TODO |
| **Hetzner / DigitalOcean** (+ small VPS) | no managed vault → use `pass`/`sops` or a self-hosted vault | SSH keys / API tokens | ⛏ TODO |

The [06 · Secrets](../guide/06-secrets.md) invariant holds everywhere: **references in git,
values in the manager, resolved at runtime.** The vault-read helper pattern becomes a
"secret-manager-read" helper using the provider CLI (`aws secretsmanager get-secret-value`,
`az keyvault secret show`, `gcloud secrets versions access`, …). ⛏ TODO: worked helper per
provider.

## Networking on cloud

- **Tailscale still the private substrate** — a cloud node joins your tailnet and is reachable
  by MagicDNS from your other nodes, without a public IP. This is often simpler and safer than
  wrangling VPC peering.
- The provider's **VPC + security groups/firewall** are an *additional* layer: default-deny
  inbound, and if a service must be public, publish it deliberately (via Tailscale funnel or a
  provider load balancer) — the [08 · publish-a-service](../guide/08-networking.md) discipline,
  cloud edition.
- ⛏ TODO: the minimal security-group posture (allow Tailscale + deny the rest) per provider.

## Cost-shaped patterns (cloud-only concern)

A cloud `server` costs money while it runs, which changes the calculus:
- **Scale-to-zero / ephemeral** — for bursty automation (a build, an occasional job), prefer
  serverless or on-demand instances that spin up, do the work, and stop, over a 24/7 VM.
- **Right-size** — the always-on coordination layer might be cheaper self-hosted on a home
  `server` (see the other spokes), with cloud reserved for what genuinely needs it.
- ⛏ TODO: guidance on when a home `server` beats a cloud VM for personal-SRE workloads (usually:
  most of them, until you need public reachability or elastic scale).

## Roles on cloud

- **`server` (cloud)** — same role as a home `server`, provisioned via cloud-init, secrets from
  the managed manager, on the tailnet. Use when you need public reachability, an always-on node
  without home hardware, or elastic scale.

## ⛏ This whole spoke needs per-provider build-out
Each provider row above is a section waiting to be written: the cloud-init snippet, the
secret-manager-read helper, the IAM/identity setup, and the security-group posture. Contributions
welcome — the hub + linux.md carry the concepts; this spoke just needs the provider specifics
filled in.

## Verifying (cloud)
- A freshly-provisioned node joins the tailnet and is reachable by MagicDNS with **no public
  IP**.
- Secrets resolve from the **managed manager** at runtime; none are on disk or in the image.
- The node's security group is **default-deny inbound** except the mesh.
