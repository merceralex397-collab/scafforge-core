# Control Plane Project Tracking

**Status:** DONE  
**Goal:** Extend the control-plane contract so the Windows app can track generated repos, host bindings, lifecycle class, and worker health through backend inventory rather than folder scans.  
**Depends On:** `10-viewer-control-plane-winui`, `15-generated-repo-root-and-inventory-architecture`, `17-worker-fabric-and-host-registration`  
**Unblocks:** durable project visibility in the Windows app and truthful multi-host operator views

## Problem statement

The current control-plane contract covers orchestration jobs, repo truth, package investigations, and provider/router state, but it does not yet define how the app should track the generated repos themselves. Without that, the app will either hide durable generated repos or start inferring them from local filesystem scans.

## Required outcomes

- the app can list tracked generated repos even when they are not on the local Windows machine
- the app can show durable versus ephemeral class
- the app can show current assigned host and host-local path bindings
- the app can show worker and host health without becoming a discovery engine

## Surfaces likely to change

- `references/control-plane-client-contract.md`
- `references/control-plane-operator-workflows.md`
- plan `10` follow-on references if the adjacent repo needs a new tracking phase
- adjacent control-plane repo docs and UI contracts

## Required control-plane read models

The app should be able to render at least:

- tracked repo list
- repo class (`ephemeral` or `durable`)
- lifecycle state
- current assigned host
- path-binding summary
- worker/host health
- repo-local truth linkout once a repo is selected

## Phase plan

### Phase 1: Freeze the tracking boundary

- [x] Explicitly prohibit canonical project discovery by local folder scan.
- [x] Freeze orchestration inventory as the app’s source of truth for tracked repos.
- [x] Freeze the minimum generated-repo fields the app is allowed to render.

### Phase 2: Define the main operator views

- [x] Define the default durable-project view.
- [x] Define how ephemeral repos are filtered, hidden, or demoted by default.
- [x] Define how the app distinguishes repo tracking state from repo-local truth state.

### Phase 3: Define host and path binding rendering

- [x] Define how assigned host, path-role, and missing-local-checkout states are shown.
- [x] Define how multiple host bindings for one repo are represented without ambiguity.
- [x] Define how offline hosts and stale bindings appear in the UI.

### Phase 4: Define operator actions

- [x] Freeze which actions are read-only versus backend-mediated mutations.
- [x] Include repo adoption, host rebinding, durable promotion, and archival initiation as backend-mediated actions only.
- [x] Ensure these actions never turn into direct WSL/SSH shell flows from the app.

## Implementation closeout

- the control-plane contract now includes tracked repos, host summaries, agent sessions, ticket records, operator experience modes, and backend-mediated lifecycle actions
- the adjacent app repo is being expanded against those read models instead of local folder discovery

## Validation and proof requirements

- the app can render tracked repos without scanning local folders
- the app can represent repos absent from the local Windows filesystem
- repo class, host binding, and worker health remain distinct from repo-local truth
- operator actions remain backend-mediated

## Documentation updates required

- `references/control-plane-client-contract.md`
- `references/control-plane-operator-workflows.md`
- adjacent control-plane docs and screen contracts
- plan `15` and `17` references if field names or host vocabulary changes

## Completion criteria

- control-plane project tracking is decision-complete
- UI-level project discovery no longer depends on local scans
- repo, host, and worker state are clearly separable in the app
