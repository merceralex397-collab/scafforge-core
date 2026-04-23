# Worker Fabric And Host Registration

**Status:** DONE  
**Goal:** Define the host-resident worker model and the host registration contract for Windows, WSL, and SSH Linux execution targets.  
**Depends On:** `09-sdk-model-router-and-provider-strategy`, `15-generated-repo-root-and-inventory-architecture`  
**Unblocks:** `18-control-plane-project-tracking`, backend dispatch implementation, and real multi-host execution

## Problem statement

The control plane and orchestration contracts currently assume remote execution exists, but they do not freeze how real workers live on hosts. Without a host-worker contract, the system will drift into ad hoc shell execution or UI-driven SSH mutation.

## Required outcomes

- host-resident workers become the canonical execution model
- host registration is explicit and shared across Windows, WSL, and SSH Linux
- the backend owns dispatch and health state
- the Windows app remains a client, not a worker runtime

## Surfaces likely to change

- `references/worker-host-contract.md`
- `references/orchestration-wrapper-contract.md`
- `references/control-plane-client-contract.md`
- adjacent orchestration service and worker runtime docs
- control-plane operator workflows

## Host model this plan must freeze

Supported host kinds:

- `windows`
- `wsl`
- `ssh-linux`

Each host must present:

- stable host identity
- connectivity or health state
- worker version
- capability summary
- reachable repo roots

## Phase plan

### Phase 1: Freeze the worker boundary

- [x] State explicitly that real agents run on host-resident workers, not in the Windows app.
- [x] Freeze backend-only dispatch of mutation work.
- [x] Prohibit direct control-plane fallback shell execution as canonical worker behavior.

### Phase 2: Define host registration

- [x] Define minimum host identity fields.
- [x] Define host-kind vocabulary and capability reporting.
- [x] Define health-state vocabulary and stale/offline handling.
- [x] Define how worker versioning and compatibility are surfaced.

### Phase 3: Define dispatch and repo affinity

- [x] Define how a job targets a worker host.
- [x] Define how repo path bindings interact with host dispatch.
- [x] Define how repos without a local Windows checkout can still be targeted on WSL or SSH Linux.
- [x] Define how the backend responds when a repo binding exists but the host is unavailable.

### Phase 4: Define trust and operational guardrails

- [x] Separate host trust from provider credentials and app auth.
- [x] Define how SSH, WSL, and Windows-local trust are represented without becoming hidden mutation lanes.
- [x] Define minimum worker evidence and progress reporting expected back to the backend.

## Implementation closeout

- worker and host contracts now include worker state, generated repo roots, active agent counts, supported autonomy levels, and lifecycle control verbs
- the boundary now explicitly covers backend-mediated start, pause, resume, and stop actions for running agent sessions

## Validation and proof requirements

- the worker model is explicit and backend-owned
- host registration fields are sufficient for dispatch and UI rendering
- mixed host types share one contract
- the Windows app can observe worker state without acting as the worker

## Documentation updates required

- `references/worker-host-contract.md`
- `references/orchestration-wrapper-contract.md`
- `references/control-plane-client-contract.md`
- `references/control-plane-operator-workflows.md`
- adjacent orchestration and worker runtime docs

## Completion criteria

- worker residency is decision-complete
- host registration and health rules are frozen
- dispatch no longer depends on UI or shell guesswork
