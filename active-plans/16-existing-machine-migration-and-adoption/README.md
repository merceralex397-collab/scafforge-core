# Existing-Machine Migration And Adoption

**Status:** DONE  
**Goal:** Define the exact migration and adoption playbooks for machines that already have old Scafforge layouts, existing generated repos, and mixed Windows/WSL/SSH execution setups.  
**Depends On:** `15-generated-repo-root-and-inventory-architecture`  
**Unblocks:** clean rollout of Workspace V2 on current machines and later host adoption tooling

## Problem statement

The Workspace V2 model only helps if existing machines can reach it without wipe-and-reclone. Right now there is no explicit playbook for the awkward cases:

- old single-repo `Scafforge` package clones
- generated repos already sitting as siblings in ad hoc folders
- repos present on Windows but not WSL
- repos present on remote Linux but not on the local Windows machine

## Required outcomes

- explicit cutover for old `Scafforge` package clones
- explicit separation between ecosystem repos and generated repos
- adoption flow for existing durable repos without forced relocation
- mixed-host normalization guidance across Windows, WSL, and SSH Linux

## Surfaces likely to change

- bootstrap migration docs
- bootstrap adoption scripts
- orchestration inventory adoption contract
- control-plane operator setup docs

## Migration scenarios this plan must cover

1. Old standalone `Scafforge` clone still occupying the desired top-level `Scafforge/` path.
2. Ecosystem repos already present as siblings but not grouped under `platform/` and `agent-tools/`.
3. Durable generated repos already present outside any `ScafforgeProjects/` root.
4. Generated repos present on WSL or remote Linux only.
5. Generated repos present on multiple hosts with different absolute paths.

## Phase plan

### Phase 1: Freeze the machine cutover order

- [x] Define the exact order for renaming the old package clone to `scafforge-core`.
- [x] Define the exact point where the bootstrap workspace takes the `Scafforge/` path.
- [x] Define when `ScafforgeProjects/` should be created and when it can remain absent temporarily.
- [x] Ensure no step assumes the user must delete and reclone healthy repos.

### Phase 2: Define ecosystem-repo adoption

- [x] Freeze how existing ecosystem repos are moved into `platform/` and `agent-tools/`.
- [x] Define how SSH versus HTTPS remotes are treated during validation.
- [x] Define how the adoption scripts detect old sibling layouts and report required moves.

### Phase 3: Define generated-repo adoption

- [x] Freeze how existing durable repos are registered into orchestration inventory without forced relocation.
- [x] Define when a repo should be moved into `ScafforgeProjects/` versus left in place and merely adopted.
- [x] Define how existing repos on remote hosts are registered when the Windows machine has no local checkout.

### Phase 4: Define mixed-host normalization

- [x] Define how Windows, WSL, and SSH Linux path bindings are captured for the same repo.
- [x] Define how missing host-local checkouts are represented truthfully.
- [x] Define what “migration complete” means when only some hosts are normalized.

## Implementation closeout

- bootstrap migration docs now explain the `Scafforge` root-name collision and the deterministic cutover
- generated repo migration now distinguishes clean moves into `ScafforgeProjects/` from adopt-in-place cases
- adoption remains criteria-based and safe for mixed Windows/WSL/SSH layouts without wipe-and-reclone

## Validation and proof requirements

- old `Scafforge` installs can be cut over without recloning
- ecosystem repos end up under the canonical workspace layout
- durable generated repos can be adopted whether or not they move into `ScafforgeProjects/`
- multi-host path differences are represented explicitly instead of hidden
- the migration docs contain no ambiguous “just move stuff around” steps

## Documentation updates required

- bootstrap `README.md`
- `docs/migration-guide.md`
- adoption-report output expectations
- plan `15` and `17` references once schema and host rules are locked

## Completion criteria

- the migration path is machine-safe and deterministic
- existing generated repos can be adopted without guesswork
- mixed-host setups have an explicit normalization story
