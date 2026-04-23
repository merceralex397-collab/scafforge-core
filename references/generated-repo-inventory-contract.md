# Generated Repo Inventory Contract

This document freezes the minimum contract for orchestration-owned tracking of generated repos.

## Boundary

- Scafforge generates and repairs repos, but it does not own the cross-repo inventory for where those repos live or which host currently owns execution.
- The adjacent orchestration service owns tracked generated-repo inventory.
- The control plane consumes that inventory through backend APIs.
- Generated repo canonical truth remains inside each generated repo and must not be replaced by the inventory.

## Root policy

Generated repos are outside the ecosystem workspace by default.

- `Scafforge/` is for the ecosystem repos.
- A separate sibling root such as `ScafforgeProjects/` is the default host-local home for generated repos.
- Existing durable repos may be adopted from older locations without moving immediately, but the inventory still becomes their canonical tracking surface.

## Minimum record types

### `RepoRecord`

Required fields:

- `repo_id`
- `human_name`
- `git_remote`
- `repo_class` with `ephemeral` or `durable`
- `product_family`
- `lifecycle_state`
- `current_assigned_host`
- `inventory_origin` with `scaffolded` or `adopted`
- `autonomy_level` with `none`, `partial`, or `full`
- `last_inventory_sync_at`

Optional but recommended:

- `ticket_system_ref`
- `canonical_brief_ref`
- `archive_project_key`
- `default_branch`

### `HostRecord`

Required fields:

- `host_id`
- `host_kind` with `windows`, `wsl`, or `ssh-linux`
- `display_name`
- `connectivity_state`
- `worker_state`
- `worker_version`
- `worker_capabilities`
- `connection_profile_id`
- `generated_repo_root`

### `PathBinding`

Required fields:

- `repo_id`
- `host_id`
- `absolute_path`
- `path_role` with `primary`, `mirror`, `archived`, or `detached`
- `binding_state` with `present`, `missing`, `stale`, or `unknown`

### `AgentSessionRecord`

Required fields:

- `agent_session_id`
- `repo_id`
- `host_id`
- `agent_lane`
- `runtime_label`
- `provider_label`
- `model_label`
- `session_state` with `queued`, `running`, `paused`, `blocked`, `stopped`, or `completed`
- `latest_ticket_id`
- `last_heartbeat_at`

### `TicketRecord`

Required fields:

- `ticket_id`
- `repo_id`
- `summary`
- `ticket_kind`
- `ticket_state`
- `owner_lane`
- `requires_human_decision`
- `updated_at`

## Lifecycle states

The minimum lifecycle vocabulary is:

- `scaffolded`
- `active`
- `blocked`
- `archived`
- `ephemeral`
- `durable`

`ephemeral` and `durable` are class markers that determine default operator views and cleanup posture. They are not a shipped list of favored repos. Systems may carry finer-grained runtime state, but they must not weaken these minimum distinctions.

## Registration rules

- Every scaffolded repo should enter the inventory.
- A repo may begin as `ephemeral` and later be promoted to `durable`.
- Existing repos may be adopted without being moved into `Scafforge/`.
- Path bindings may differ per host, and multiple bindings may exist for the same repo.
- Local folder scanning is not the canonical registration mechanism.
- No machine-local durable candidate list is part of the product contract. Adoption policy is criteria-based and operator-approved.

## Control-plane read model rule

The control plane may render inventory state, but it must not:

- invent the tracked repo set from local files
- rewrite lifecycle class by itself
- treat path presence on the Windows machine as proof that a repo is the active canonical target
- assume a repo belongs to the product simply because it lives inside `ScafforgeProjects/`
