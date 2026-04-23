# Control Plane Client Contract

This document is the package-level summary for the adjacent control plane boundary. It freezes how an operator client may observe and control the autonomous factory without becoming a second workflow engine.

## Scope

The adjacent control plane is a client of:

- the adjacent orchestration service
- orchestration-owned tracked generated-repo inventory and worker-host registration
- generated repo truth projections exposed by that service
- package-investigation evidence exposed through the meta-loop path
- provider/router summaries exposed by adjacent service layers

Windows-specific implementation details stay in the adjacent app repo and plan-10 phase artifacts. This package reference owns only the durable client boundary.

## Boundary

- The control plane may render orchestration state, tracked generated-repo inventory, repo-truth projections, package investigations, and provider/router summaries.
- The control plane may render host inventory, worker health, agent session state, ticket state, archive research lanes, and operator mode.
- The control plane may keep local UI state, cached snapshots with freshness markers, and secure local settings.
- The control plane may present transient provider-credential enrollment UX only when the submitted secret is handed directly to backend-managed storage and not retained locally.
- The control plane must route all approvals, overrides, pause/resume, retry, merge-approval, and router-policy changes through backend APIs.
- The control plane may submit direct project-creation requests, autonomy-level changes, repo adoption requests, host rebinding requests, and agent stop or pause requests only through backend APIs.
- The control plane must not mutate generated repos, GitHub review state, package evidence, or provider credentials directly.
- The control plane must not treat `wsl.exe`, `ssh`, or repo-local shell commands as fallback mutation lanes.

## State domains that must stay separate

The client must not collapse these into one generic status field:

1. orchestration job state
2. tracked generated-repo inventory and worker-host health
3. generated repo truth
4. host and worker inventory
5. agent and ticket state
6. package investigation state
7. provider/router state
8. local connectivity and trust overlay

This is the minimum boundary required for the app to represent tracked repos, downstream repo failures, package investigations, and provider/router state without ambiguity.

## Tracked generated-repo inventory rule

The control plane may render:

- tracked repo identity and human name
- repo class (`ephemeral` or `durable`)
- lifecycle state
- autonomy level
- current assigned host
- host-local path bindings and path roles
- worker and host health summaries
- ticket summaries
- live agent-session summaries

The control plane must not:

- discover the canonical tracked repo set by scanning local folders
- infer durable or ephemeral classification from path naming
- promote, archive, or rebind repos except through backend APIs
- ship machine-local project names as product defaults

## Packaging posture

The initial control-plane posture is internal-tool first:

- optimize the early implementation for unpackaged local build/run loops
- keep MSIX or sparse packaging as a later decision if package identity or enterprise deployment becomes necessary
- do not let package-identity-only Windows features leak into the package contract before the adjacent app actually needs them

## Connectivity rule

Local WSL and remote SSH are transport concerns, not alternate authority surfaces.

- use the same orchestration HTTPS and event-stream contract in local and remote cases
- treat host-resident workers as the real execution targets behind that orchestration API
- keep mutation paths backend-mediated
- fail closed to read-only when auth, trust, or connectivity is ambiguous

## Experience modes

The adjacent app supports two operator experiences built over the same backend contract:

- `dev mode` for package improvement, archive research, and skill-system work
- `release mode` for autonomous factory operations and durable project supervision

Those modes change emphasis, defaults, and visible work surfaces. They do not create a second authority model.

## Operator customization rule

The control plane may manage local or backend-bound operator settings for:

- theme and layout preferences
- connection profiles
- generated-repo root preferences
- prompt profiles
- model-route preferences
- provider lane enrollment state
- first-run walkthrough state

Raw provider secrets remain transient and backend-managed.

## CLI/API fallback rule

The control plane must not become the only usable control surface.

- the backend API and CLI remain the canonical mutation path
- the app is one client of that path
- no WinUI-only hidden commands or stateful side channels are allowed
