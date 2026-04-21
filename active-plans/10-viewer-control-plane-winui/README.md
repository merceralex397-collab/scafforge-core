# Viewer Control Plane WinUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** TODO
**Goal:** Design the Windows control app that monitors and orchestrates the autonomous Scafforge factory across local WSL and remote SSH environments without becoming a hidden workflow engine.

**Architecture:** Build the control plane as a dedicated WinUI 3 application backed by explicit orchestration APIs and event streams. The app should observe and control the system, not own its truth. During early implementation, prefer an internal-tool packaging posture that optimizes local build/run and operator workflows; revisit packaged distribution only when the app’s Windows feature needs are clear.

**Tech Stack / Surfaces:** WinUI 3, Windows App SDK, WSL and SSH connectivity, orchestration APIs, secure settings storage, event dashboards, package integration docs.
**Depends On:** `07-autonomous-downstream-orchestration`, `08-meta-improvement-loop`, and `09-sdk-model-router-and-provider-strategy`.
**Unblocks:** operator-facing autonomy control and system observability.
**Primary Sources:** `_source-material/autonomy/hugeupgrade/ScafforgeAutonomousOrchestrationDRAFTPLAN.md`, `_source-material/autonomy/hugeupgrade/scafforgeautonomousnotes.md`, current WinUI 3 guidance from Microsoft Learn on packaged versus unpackaged apps and Windows App SDK runtime initialization.

---

## Problem statement

The autonomous vision needs a human-operable control surface, but the current concept mixes UI, orchestration, routing, secrets, approvals, and analytics into one loose description. Without a clear plan, the app will either become a second backend or a thin screen that cannot actually control anything safely.

## Required deliverables

- a responsibility boundary for the WinUI app
- a screen and workflow map
- a backend contract for event/state/control APIs
- a connectivity plan for WSL and SSH targets
- a secret/configuration plan for provider keys and remote connections
- a launch/verification plan for the app itself

## Packaging and deployment stance

This plan should explicitly compare:

- **unpackaged/internal-tool development** for fast local build-run loops
- **packaged/MSIX distribution** if the app later needs package-identity features or enterprise distribution

The current expectation is to optimize for internal orchestration use first, not Store delivery.

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

- project initiation / “Forge” surface
- pipeline overview and job board
- per-project drill-down with tickets, PRs, review state, and proofs
- live agent/log feeds
- model-router and provider configuration
- approval and override workflows
- meta-loop dashboard for package investigations and fixes
- archive intelligence/history views

## Phase plan

### Phase 1: Freeze the app’s boundary and packaging model

- [ ] Document exactly what the WinUI app is allowed to do directly versus what it must ask the backend to do.
- [ ] Decide the initial packaging model for development and internal deployment.
- [ ] Record which Windows features the app truly needs before choosing packaged-only behavior.
- [ ] Ensure the plan never assumes the app itself is the workflow source of truth.

### Phase 2: Define the backend contract

- [ ] Specify the event and state APIs the app consumes: project list, pipeline state, review state, provider config summaries, and intervention endpoints.
- [ ] Define how the app receives live updates: polling, streaming, or event subscriptions.
- [ ] Decide how job identifiers, repo identifiers, and package-investigation identifiers are represented consistently across screens.
- [ ] Ensure the app can distinguish downstream repo failures from package-level investigations cleanly.

### Phase 3: Define connectivity and operator environment rules

- [ ] Design the WSL integration contract for local orchestration work.
- [ ] Design the SSH integration contract for remote runners or build hosts.
- [ ] Define how credentials, host trust, and failure states are surfaced to the operator.
- [ ] Ensure the app can fail closed when connectivity or permissions are ambiguous.

### Phase 4: Design the UI surface area

- [ ] Choose a shell/navigation structure appropriate for a multi-pane operations app.
- [ ] Map the major screens and the most important operator journeys: start project, inspect failure, approve merge, pause/resume, inspect package fix, adjust provider settings.
- [ ] Decide which screens are read-only dashboards versus command surfaces.
- [ ] Keep dashboards tied to backend truth instead of inventing local state transitions.

### Phase 5: Define security, settings, and auditability

- [ ] Design secure storage for API keys, tokens, and remote credentials.
- [ ] Define how the app logs operator interventions and approval decisions.
- [ ] Ensure sensitive data is not echoed into general logs or screenshots accidentally.
- [ ] Define a supportable local-environment setup path for operators using the app.

### Phase 6: Validate the internal-tool workflow

- [ ] Prove the app can connect to at least one WSL target and one SSH target.
- [ ] Prove the app can show pipeline truth, PR/review truth, and package-investigation truth without confusion.
- [ ] Exercise pause, retry, merge-approval, and escalation flows.
- [ ] Confirm the app itself can be built, launched, and objectively verified before claiming readiness.

## Validation and proof requirements

- the app has a clear authority boundary
- WSL and SSH expectations are explicit and testable
- operator override paths are designed before implementation begins
- the UI can distinguish repo execution, package investigation, and router/provider state

## Risks and guardrails

- Do not hide orchestration state in the WinUI app.
- Do not choose packaged-only behavior before confirming the app needs package identity.
- Do not make the app the only control surface; CLI/API fallback should remain possible.
- Do not let dashboard ambitions outrun the backend contracts they depend on.

## Documentation updates required when this plan is implemented

- integration docs in the Scafforge package
- operator setup docs for WSL/SSH and secret handling
- app-specific architecture and runbook docs in the WinUI repo
- any package references that mention control-plane assumptions

## Completion criteria

- the WinUI control plane has a precise boundary, screen map, and backend contract
- packaging and local-development posture are deliberate rather than assumed
- WSL and SSH operator workflows are explicit
- the app can observe and control the autonomous system without becoming its hidden source of truth
