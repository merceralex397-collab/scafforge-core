# Generated Repo Root And Inventory Architecture

**Status:** DONE  
**Goal:** Define the permanent boundary between the ecosystem workspace and generated repo roots, then freeze the orchestration-owned inventory contract for tracked generated repos, host bindings, and path roles.  
**Depends On:** `07-autonomous-downstream-orchestration`, `10-viewer-control-plane-winui`, `11-repository-documentation-sweep`  
**Unblocks:** `16-existing-machine-migration-and-adoption`, `17-worker-fabric-and-host-registration`, `18-control-plane-project-tracking`, `19-generated-repo-lifecycle-policy`

## Problem statement

The current workspace cleanup solved where the ecosystem repos live, but it did not define where generated repos belong or how the system should track them across Windows, WSL, and SSH Linux hosts. Leaving that implicit would force the control plane to guess from local folders and would blur the line between the factory and its outputs.

## Required outcomes

- `Scafforge/` remains the ecosystem workspace for factory repos only
- generated repos live outside that root by default
- `ScafforgeProjects/` becomes the recommended sibling generated-repo root
- orchestration-owned inventory becomes the canonical source of truth for tracked generated repos
- local folder scanning is explicitly non-canonical

## Package and adjacent surfaces likely to change

- bootstrap repo docs and workspace helpers
- `architecture.md`
- `references/generated-repo-inventory-contract.md`
- `references/orchestration-wrapper-contract.md`
- `references/control-plane-client-contract.md`
- adjacent orchestration service docs and persistence model

## Architecture decisions to freeze

### Root separation

- `Scafforge/` contains only ecosystem repos
- generated repos must not be nested under `Scafforge/` by default
- the recommended host-local generated-repo root is `ScafforgeProjects/`
- absolute paths may differ per host; only the separation rule is fixed

### Inventory ownership

- tracked generated-repo records are adjacent orchestration state
- repo identity, class, lifecycle, host assignment, and path bindings are not package-root truth
- the control plane consumes inventory through backend APIs
- the control plane must not create canonical inventory state by scanning folders

### Minimum record model

The plan should lock these record families:

- `RepoRecord`
- `HostRecord`
- `PathBinding`
- minimum lifecycle vocabulary shared with plan `19`

It should also lock field semantics tightly enough that later worker and control-plane work does not invent incompatible shapes.

## Phase plan

### Phase 1: Freeze the root policy

- [x] Document the ecosystem workspace and generated-repo root as separate concerns.
- [x] Freeze `ScafforgeProjects/` as the recommended sibling root, while keeping absolute paths host-specific.
- [x] Explicitly document that generated repos are outputs, not ecosystem repos.
- [x] Prohibit default nesting of generated repos inside `Scafforge/`.

### Phase 2: Freeze the inventory schema

- [x] Define `RepoRecord` fields and semantic meanings.
- [x] Define `HostRecord` fields and host-kind vocabulary.
- [x] Define `PathBinding` fields and path-role vocabulary.
- [x] Freeze the minimum lifecycle vocabulary used across inventory and control-plane read models.
- [x] Define how inventory records reference Git remotes, human-facing names, and product-family labels.

### Phase 3: Define registration and adoption entrypoints

- [x] Define how freshly scaffolded repos enter inventory automatically.
- [x] Define how existing repos are adopted without moving into `Scafforge/`.
- [x] Define how multiple path bindings for the same repo are represented across Windows, WSL, and SSH Linux.
- [x] Define when a repo is considered inventory-known even if the local Windows machine does not have a checkout.

### Phase 4: Validate the control-plane and orchestration boundary

- [x] Ensure the orchestration wrapper contract owns tracked generated-repo inventory.
- [x] Ensure the control-plane contract consumes tracked repos through backend read models only.
- [x] Prove that the folder-scan approach is explicitly rejected in the docs and contracts.

## Implementation closeout

- inventory fields now include repo class, lifecycle, inventory origin, autonomy level, host registration, path bindings, agent sessions, and ticket records
- workspace docs now state that generated repos are separate from the ecosystem workspace and that no machine-local durable set is shipped as product default state
- example inventory material is generic rather than hardcoded to the current local durable set

## Validation and proof requirements

- generated repos are clearly separate from ecosystem repos
- `ScafforgeProjects/` is documented as the default sibling root
- repo/host/path binding records are defined tightly enough for implementation
- local folder scanning is clearly non-authoritative
- existing durable repos can be adopted without being moved into `Scafforge/`

## Documentation updates required

- bootstrap repo root docs
- `architecture.md`
- `references/generated-repo-inventory-contract.md`
- `references/orchestration-wrapper-contract.md`
- `references/control-plane-client-contract.md`
- plan `18` and plan `19` references once those plans lock their dependent vocabularies

## Completion criteria

- generated repo placement and tracking are decision-complete
- inventory ownership is unambiguous
- the control plane can be built against the inventory contract without guessing
