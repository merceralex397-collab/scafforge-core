# WinUI Control Boundary

This document is the Phase 1 exit artifact for plan `10-viewer-control-plane-winui`.

## Scope

The WinUI app is an adjacent operator client for the autonomous factory. It may observe, summarize, and request actions, but it is not a second workflow engine and it is not a second mutation authority.

## Responsibility boundary

| Surface | WinUI app may do directly | WinUI app must ask backend to do | WinUI app must never do |
| --- | --- | --- | --- |
| Orchestration jobs | Render job lists, job detail, cached snapshots, local filters, and dashboard layout state | Pause, resume, retry, split, escalate, or merge any job-related phase | Invent job state locally or mark a job complete without backend evidence |
| Generated repo truth | Display backend projections of `docs/spec/CANONICAL-BRIEF.md`, `tickets/manifest.json`, `.opencode/state/workflow-state.json`, restart surfaces, proofs, and PR links | Trigger repo repair, revalidation, or resume actions through the orchestration service | Mutate repo files, ticket state, workflow state, or restart surfaces directly |
| Package investigations | Show investigator reports, package-fix PR linkage, and `resume-ready` status supplied by the backend/meta-loop surfaces | Acknowledge, reopen, or route package follow-up through backend APIs | Rewrite `active-audits/` evidence or claim package revalidation success locally |
| Provider/router state | Show provider policy summaries, route health, degraded-mode markers, and router decision evidence already owned by adjacent services | Apply policy changes or fallback-lane changes through backend APIs | Hold raw provider credentials or become the executable router |
| Connectivity | Track local connectivity, SSH trust, WSL availability, and stale-cache overlays | Refresh trusted sessions, backend auth, or tunnel lifecycle through supported backend/auth flows | Use ambiguous connectivity as permission to dispatch direct mutation commands |

## Direct action rules

The app may own only local presentation and local operator convenience:

- window layout, navigation state, column choices, and local filters
- secure local storage for app credentials and trusted-host metadata
- transient provider-credential entry forms that immediately hand secrets to backend-managed storage
- cached read models marked with freshness metadata
- read-only environment preflight checks for WSL availability or SSH trust

Everything that changes system truth remains backend-mediated:

- approvals and override decisions
- pause, resume, retry, merge-approval, and escalation actions
- provider/router policy changes
- repo-level repair and package-resume actions

The app must never:

- call GitHub mutation APIs directly for repo, PR, or review actions
- call repo-local tools as a fallback mutation lane
- dispatch mutable commands through `wsl.exe`, `ssh`, or an embedded terminal
- persist raw provider credentials in local settings or local secret stores
- store canonical orchestration state as local truth

## Operating-mode vocabulary

The app renders a backend-owned operating mode plus an app-local safety overlay.

| Mode | Source of truth | Meaning |
| --- | --- | --- |
| `observe-only` | backend or operator policy | Dashboards and logs remain visible, but no mutation controls are available |
| `merge-approval` | backend orchestration policy | Agents may execute and review, but merge requires explicit human approval |
| `strict` | backend orchestration policy | High-risk actions require explicit operator approval before backend dispatch |
| `fully-autonomous` | backend orchestration policy | Backend may advance through merge once policy and proof gates are satisfied |
| `read-only-degraded` | app-local safety overlay | Connectivity, trust, or auth is ambiguous, so the app disables all mutation controls even if backend policy would otherwise allow them |

The local `read-only-degraded` overlay never changes backend policy. It is a client-side fail-closed state.

## Packaging posture

The initial posture is **unpackaged/internal-tool first**:

- use an unpackaged WinUI 3 app for fast local build/run loops
- set `<WindowsPackageType>None</WindowsPackageType>` and rely on Windows App SDK runtime auto-initialization for the early inner loop
- keep MSIX or sparse packaging as a later decision if the app truly needs package identity or enterprise deployment features

Packaged-only behavior should not be assumed in the first implementation wave. Revisit packaging only when the app needs one or more of:

- package-identity-only Windows features such as notifications, background tasks, share targets, or file associations
- enterprise software-distribution requirements that make MSIX materially better than the internal-tool loop
- PasswordVault as the primary secret store instead of the unpackaged DPAPI-first baseline

## Repo identity and naming

The app belongs in an adjacent repository, not in the Scafforge package root.

Recommended adjacent identity:

- repo: `scafforge-control-plane-winui`
- solution: `Scafforge.ControlPlane.sln`
- projects:
  - `Scafforge.ControlPlane.App` for the WinUI shell
  - `Scafforge.ControlPlane.Contracts` for HTTP/event DTOs shared with tests
  - `Scafforge.ControlPlane.Infrastructure` for connectivity, settings, and secure storage

The app consumes Scafforge contracts, orchestration service APIs, and package evidence. It does not become part of package core.

## Windows App SDK version policy

The exact Windows App SDK version should live in the adjacent app repo, not in Scafforge package docs.

Policy:

1. Pin the exact Windows App SDK version in the adjacent repo build files such as `Directory.Build.props`.
2. Record the justification and upgrade notes in adjacent app docs.
3. Keep Scafforge package docs at the boundary/policy level: "current stable Windows App SDK release verified by the adjacent app repo."

This avoids package-core drift into Windows-specific runtime pinning.
