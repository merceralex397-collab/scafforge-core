# Generated Repo Lifecycle Policy

**Status:** DONE  
**Goal:** Define how generated repos move between `ephemeral`, `durable`, `blocked`, and `archived`, including promotion, adoption, and cleanup rules.  
**Depends On:** `15-generated-repo-root-and-inventory-architecture`, `17-worker-fabric-and-host-registration`  
**Unblocks:** control-plane lifecycle views, inventory retention policy, and long-term repo cleanup automation

## Problem statement

If every scaffolded repo is treated the same forever, the system becomes cluttered and the control plane becomes noisy. If only “important” repos are ever tracked, then repeated failures and forgotten experiments disappear from the system. The right answer is a formal lifecycle policy.

## Required outcomes

- all scaffolded repos can enter inventory
- `ephemeral` and `durable` are first-class lifecycle categories
- promotion and archival are explicit backend-managed actions
- durable repos worth keeping stay visible in the app

## Surfaces likely to change

- `references/generated-repo-inventory-contract.md`
- `references/control-plane-client-contract.md`
- orchestration inventory docs
- adoption and archive policies in adjacent services

## Lifecycle rules this plan must freeze

- `ephemeral` for disposable experiments, test scaffolds, or short-lived outputs
- `durable` for repos intended to be kept, repaired, reviewed, and tracked long-term
- `blocked` for repos that are known but currently unable to proceed
- `archived` for repos intentionally retired from active execution

## Phase plan

### Phase 1: Freeze the class model

- [x] Define the semantic difference between `ephemeral` and `durable`.
- [x] Define how these classes interact with runtime states like `active`, `blocked`, and `archived`.
- [x] Define how first-time scaffolds are initially classified.

### Phase 2: Define promotion and demotion

- [x] Define how an `ephemeral` repo becomes `durable`.
- [x] Define who may approve that promotion.
- [x] Define when a durable repo may be archived or demoted.

### Phase 3: Define adoption of existing durable repos

- [x] Freeze the adoption criteria instead of shipping a global durable repo list.
- [x] Define how already-existing repos enter the lifecycle system.
- [x] Define how adopted repos differ from freshly scaffolded repos in inventory provenance.

### Phase 4: Define cleanup and retention

- [x] Define whether ephemeral repos are hidden by default in the control plane.
- [x] Define archival triggers and minimum retained metadata.
- [x] Define what evidence remains after archival so package improvement and audit history are not lost.

## Implementation closeout

- lifecycle policy now freezes criteria-based promotion and adoption rather than a hardcoded durable repo set
- archive research paths are formalized so historical evidence survives archival without turning the archive into canonical repo truth

## Validation and proof requirements

- repo lifecycle vocabulary is explicit and shared
- promotion to `durable` is not guesswork
- archival preserves enough history for later analysis
- the control plane can prioritize durable repos without losing ephemeral traceability

## Documentation updates required

- `references/generated-repo-inventory-contract.md`
- `references/control-plane-client-contract.md`
- adjacent orchestration inventory docs
- any adoption or archive procedures in the bootstrap repo once implemented

## Completion criteria

- generated repo lifecycle is policy-complete
- durable versus ephemeral is enforced as real state
- existing important repos can be adopted cleanly
