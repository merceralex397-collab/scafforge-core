# Viewer Control Plane WinUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** IN PROGRESS
**Goal:** Design the Windows control app that monitors and controls the autonomous Scafforge factory across local WSL and remote SSH environments without becoming a hidden workflow engine.

**Architecture:** Build the control plane as a dedicated WinUI 3 application backed by explicit orchestration APIs and event streams. The app should observe and control the system, not own its truth. During early implementation, prefer an internal-tool packaging posture that optimizes local build/run and operator workflows; revisit packaged distribution only when the app’s Windows feature needs are clear.

**Tech Stack / Surfaces:** WinUI 3, Windows App SDK, WSL and SSH connectivity, orchestration APIs, secure settings storage, event dashboards, package integration docs.
**Depends On:** `07-autonomous-downstream-orchestration`, `08-meta-improvement-loop`, and `09-sdk-model-router-and-provider-strategy`.
**Unblocks:** operator-facing autonomy control and system observability.
**Primary Sources:** `_source-material/autonomy/hugeupgrade/ScafforgeAutonomousOrchestrationDRAFTPLAN.md` for the substantive app concept, plus current WinUI 3 guidance from Microsoft Learn on packaged versus unpackaged apps and Windows App SDK runtime initialization.

---

## Problem statement

The autonomous vision needs a human-operable control surface, but the current concept mixes UI, orchestration, routing, secrets, approvals, and analytics into one loose description. Without a clear plan, the app will either become a second backend or a thin screen that cannot actually control anything safely.

## Required deliverables

- a responsibility boundary for the WinUI app
- a screen and workflow map
- a backend consumption contract for event/state/control APIs
- a connectivity plan for WSL and SSH targets
- a secret/configuration plan for provider keys, app auth, and remote connections
- a launch/verification plan for the app itself
- committed phase-exit artifacts that can be reviewed before implementation begins

## Per-phase dependency map

- Phase 1 can begin now as design work
- Phase 2 is blocked until plan `07`’s orchestration API direction exists, because the app is only a client of that service and must share the same live-update transport decision
- Phase 3 can begin design work now for Windows-local concerns, but backend-auth specifics depend on plan `07` and must forbid direct mutation by `wsl.exe`, `ssh`, GitHub API, or repo-local shell fallback
- Phase 4 can begin as UI and workflow design
- Phase 5 can begin for local credential-storage and auditability design, but backend auth depends on plan `07` and provider policy depends on plan `09`
- Phase 6 is fully blocked until plan `07` provides the orchestration API and event stream, plan `08` provides the meta-loop evidence surfaces and `resume-ready.json` contract, and plan `09` provides the provider/router policy the app must expose without re-authoring it

## Packaging and deployment stance

This plan should explicitly compare:

- **unpackaged/internal-tool development** for fast local build-run loops
- **packaged/MSIX distribution** if the app later needs package-identity features or enterprise distribution

The current expectation is to optimize for internal orchestration use first, not Store delivery.

## Source-material override note

The draft autonomy notes sometimes describe the Windows app as a direct command-routing "bridge" into WSL or SSH targets. This plan supersedes that framing for mutation paths. Observation channels may use local transport choices defined in Phase 3, but approvals, overrides, retries, merge signals, pause/resume commands, and any other mutations must remain backend-mediated through plan `07`’s orchestration service.

## Package and adjacent surfaces likely to change during implementation

### Scafforge package surfaces

- `architecture.md`
- `AGENTS.md`
- new integration docs describing orchestration/control-plane event contracts
- any package references that describe operator workflows or remote execution assumptions

### Adjacent WinUI app surfaces

- dedicated WinUI repo or workspace
- app shell and navigation
- API/event client
- WSL and SSH connection modules
- secure settings and credential storage
- dashboard and intervention screens

## Core screens this plan must define

- project initiation / “Forge” surface for rough ideas, reference-file drop, and spec-factory handoff
- pipeline overview and job board
- per-project drill-down with tickets, PRs, review state, and proofs
- live agent/log feeds
- model-router and provider configuration
- approval and override workflows
- meta-loop dashboard for package investigations and fixes
- archive intelligence/history views

## Required phase-exit artifacts

- Phase 1 exit artifact: `active-plans/10-viewer-control-plane-winui/references/winui-control-boundary.md` covering authority boundaries, operating modes, packaging posture, repo identity, and Windows App SDK version policy
- Phase 2 exit artifact: `active-plans/10-viewer-control-plane-winui/references/winui-backend-consumption-contract.md` covering read models, control endpoints, identifier rules, and the jointly agreed live-update transport decision from plan `07`
- Phase 2 cross-plan coordination artifact: `active-plans/07-autonomous-downstream-orchestration/references/orchestration-transport-decision.md`, owned by plan `07`, with plan `10` providing client-side requirements before that document is finalized
- Phase 3 exit artifact: `active-plans/10-viewer-control-plane-winui/references/winui-connectivity-and-fail-closed.md` covering WSL transport choice, SSH transport choice, backend auth, host trust, and explicit fail-closed behavior
- Phase 4 exit artifact: `active-plans/10-viewer-control-plane-winui/references/winui-screen-and-journey-map.md` covering shell/navigation, read-only versus mutation surfaces, and the main operator journeys
- Phase 5 exit artifact: `active-plans/10-viewer-control-plane-winui/references/winui-security-and-settings.md` covering credential storage, audit logging, redaction rules, and local operator setup
- Phase 6 exit artifact: in the adjacent WinUI repo, `docs/validation/phase-06-control-plane-validation.md` plus an `artifacts/phase-06/` bundle containing connectivity proof, fail-closed simulation captures, mutation-flow logs, and CLI/API fallback verification evidence; package-side docs must then be updated to describe the validated boundary

## Fail-closed rule

This plan should not leave “fail closed” as a vague slogan.

Minimum default behavior:

- ambiguous connectivity or permissions should force the app into read-only mode
- command dispatch and mutation controls should be disabled until trust is restored
- cached state may remain visible, but it must be clearly marked stale

## CLI/API fallback rule

The WinUI app must not become the only usable control surface.

- plan `07` owns the backend service and its API/CLI accessibility
- plan `10` must consume that backend as a client
- phase 6 for this plan must verify that the backend remains usable without the WinUI app

## Phase plan

### Phase 1: Freeze the app’s boundary and packaging model

- [x] Document exactly what the WinUI app is allowed to do directly versus what it must ask the backend to do.
- [x] Decide the initial packaging model for development and internal deployment.
- [x] Record which Windows features the app truly needs before choosing packaged-only behavior.
- [x] Decide and record the WinUI app repo identity, naming, and its relationship to the Scafforge package.
- [x] Record where the Windows App SDK version decision will live so it does not drift.
- [x] Freeze the operating-mode vocabulary for the app, including any human-in-the-loop versus autonomous modes that affect approvals and overrides.
- [x] Ensure the plan never assumes the app itself is the workflow source of truth.
- [x] Exit Phase 1 only when `references/winui-control-boundary.md` exists and is reviewed against plan `07`’s ownership boundaries.

### Phase 2: Define the backend consumption contract

- [x] Scope this phase to what the app needs from the backend, not to authoring the backend API itself.
- [x] Specify the event and state data the app consumes: project list, pipeline state, review state, provider config summaries, and intervention endpoints.
- [x] Define how the app receives live updates: polling, streaming, or event subscriptions.
- [x] Coordinate the live-update transport decision jointly with plan `07` before finalizing this phase so the app and backend cannot be designed into incompatibility.
- [x] Treat `active-plans/07-autonomous-downstream-orchestration/references/orchestration-transport-decision.md` as the canonical coordination artifact and do not finalize this phase until that document records the shared transport choice and rationale.
- [x] Decide how job identifiers, repo identifiers, and package-investigation identifiers are represented consistently across screens.
- [x] Ensure the app can distinguish downstream repo failures from package-level investigations cleanly.
- [x] Require that all mutations, including approvals, overrides, pause/resume, retry, and merge signals, are dispatched through the plan `07` orchestration API rather than directly to GitHub, generated repos, or shell invocations.
- [x] Keep API authoring authority in plan `07`’s orchestration service repo.
- [x] Exit Phase 2 only when `references/winui-backend-consumption-contract.md` exists and is cross-checked against the current plan `07` contract notes.

### Phase 3: Define connectivity and operator environment rules

- [x] Design the WSL integration contract for local orchestration work.
- [x] Choose and record the WSL transport mechanism explicitly; do not leave this as an implementation-time assumption.
- [x] Design the SSH integration contract for remote runners or build hosts.
- [x] Distinguish read-only observation channels from mutation channels and prohibit direct `wsl.exe`, `ssh`, or ad hoc shell mutation flows outside the plan `07` orchestration API.
- [x] Define how credentials, host trust, and failure states are surfaced to the operator.
- [x] Define app-to-backend authentication separately from provider API key handling, and explicitly compare at least shared API key, OAuth 2.0 client-credentials, and mTLS before choosing the implementation path.
- [x] Freeze the default fail-closed behavior for ambiguous connectivity or permissions before implementation begins.
- [x] Exit Phase 3 only when `references/winui-connectivity-and-fail-closed.md` exists and includes specific stale-state, trust-loss, and disabled-control rules.

### Phase 4: Design the UI surface area

- [x] Choose a shell/navigation structure appropriate for a multi-pane operations app.
- [x] Map the major screens and the most important operator journeys: start project from a rough idea, attach reference files into the spec-factory flow, inspect failure, approve merge, pause/resume, inspect package fix, adjust provider settings.
- [x] Decide which screens are read-only dashboards versus command surfaces.
- [x] Define the meta-loop dashboard’s exact dependencies on plan `08`, including investigator reports, package-fix PR linkage, and the `resume-ready.json` signal.
- [x] Mark the meta-loop dashboard contract provisional until plan `08` finalizes the `resume-ready.json` field contract, then require a lock pass before implementation begins.
- [x] Keep dashboards tied to backend truth instead of inventing local state transitions.
- [x] Exit Phase 4 only when `references/winui-screen-and-journey-map.md` exists and marks every mutation surface as backend-mediated.

### Phase 5: Define security, settings, and auditability

- [x] Design secure handling for provider API keys plus secure local storage for app auth tokens and remote credentials, using backend-managed custody for provider keys and `Windows.Security.Credentials.PasswordVault` or DPAPI-backed encrypted storage only for app-local secrets.
- [x] Explicitly prohibit plaintext config files and environment variables as the steady-state storage mechanism for provider keys, backend auth tokens, or SSH credentials.
- [x] Define how the app logs operator interventions and approval decisions.
- [x] Ensure sensitive data is not echoed into general logs or screenshots accidentally.
- [x] Define a supportable local-environment setup path for operators using the app.
- [x] Exit Phase 5 only when `references/winui-security-and-settings.md` exists and includes storage, redaction, and auditability rules.

### Phase 6: Validate the internal-tool workflow

- [ ] This phase is blocked until plans `07`, `08`, and `09` provide the real backend and state contracts the app consumes.
- [ ] Prove the app can connect to at least one WSL target and one SSH target.
- [ ] Prove the app can show pipeline truth, PR/review truth, and package-investigation truth without confusion.
- [ ] Exercise pause, retry, merge-approval, and escalation flows.
- [ ] Simulate trust loss or transport failure and prove fail-closed behavior disables mutation controls while marking cached state stale.
- [ ] Verify the backend remains usable through CLI/API paths without the UI.
- [ ] Confirm the app itself can be built, launched, and objectively verified before claiming readiness.

## Validation and proof requirements

- the app has a clear authority boundary
- WSL and SSH expectations are explicit and testable
- operator override paths are designed before implementation begins
- the UI can distinguish repo execution, package investigation, and router/provider state
- the app remains a client of orchestration truth rather than an API-authoring surface
- each design phase leaves a committed artifact that can be reviewed before Phase 6 is unblocked
- the backend remains usable through CLI/API paths without the WinUI app

## Risks and guardrails

- Do not make the app the hidden owner of orchestration state.
- Do not let package references drift into Windows-only assumptions that belong in the adjacent app repo.
- Do not make the app the only control surface; CLI/API fallback should remain possible through the backend service.
- Keep security decisions explicit; provider keys, backend auth, and SSH credentials are different trust domains.

## Documentation updates required when this plan is implemented

- package integration docs describing the control-plane boundary
- orchestration/control-plane contract notes
- operator docs for connectivity, auth, and override flows
- adjacent app repo docs for build, run, and deployment

## Completion criteria

- the WinUI app has a precise client boundary and screen map
- backend consumption requirements are clear without duplicating backend ownership
- WSL and SSH workflows are explicit and testable
- the app observes and controls the system without owning workflow truth
- phase-exit artifacts exist for boundary, contract, connectivity, screen mapping, and security decisions
