# WinUI Backend Consumption Contract

This document is the Phase 2 exit artifact for plan `10-viewer-control-plane-winui`.

## Scope

This is a **client contract** for the adjacent WinUI app. It defines what the app must be able to consume from the adjacent orchestration service and related package-evidence surfaces. It does **not** make the WinUI app the API-authoring owner.

Backend API authoring authority remains in plan `07`'s orchestration-service repo.

## Canonical upstreams

The WinUI app reads and acts through four distinct backend domains:

1. **orchestration job state** owned by the adjacent orchestration service
2. **generated repo truth projections** mirrored by that service from canonical repo surfaces
3. **package investigation state** supplied from the meta-loop evidence chain
4. **provider/router summaries** supplied from the adjacent router/service layer

The app must not read these domains by bypassing the backend and talking directly to GitHub, generated repo files, or repo-local shells.

## Shared live-update transport decision

The shared transport decision for backend live updates is:

- **HTTPS JSON** for snapshots and command endpoints
- **Server-Sent Events (SSE)** for live one-way updates
- **polling only as a reconnect/resync fallback**

The canonical cross-plan coordination artifact is:

- `active-plans/07-autonomous-downstream-orchestration/references/orchestration-transport-decision.md`

This choice keeps command dispatch separate from live event delivery, matches the mostly server-to-client dashboard flow, and preserves CLI/API fallback without requiring a WinUI-only session model.

## Read models

### `ProjectSummary`

Minimum fields:

- `job_id`
- `repo_id`
- `project_label`
- `run_type`
- `operator_mode`
- `orchestration_state`
- `scaffold_verified`
- `current_phase`
- `review_state`
- `blocking_kind` (`none`, `repo-local`, `package-change`, `router`, `auth`, `connectivity`)
- `last_event_at`
- `stale`

### `ProjectDetail`

Minimum fields:

- `job_id`
- `repo_id`
- `canonical_brief_ref`
- `ticket_manifest_ref`
- `workflow_state_ref`
- `latest_handoff_ref`
- `active_ticket_ids`
- `phase_branch`
- `pull_request_ref`
- `review_summary`
- `validation_summary`
- `resume_state`

### `RepoTruthProjection`

This is a backend mirror of generated repo truth, not a second canonical store.

Minimum fields:

- `repo_id`
- `canonical_brief_revision`
- `workflow_stage`
- `ticket_counts`
- `pending_follow_on_count`
- `current_owner`
- `next_legal_move`
- `proof_artifacts`
- `restart_surface_generated_at`

### `PackageInvestigationSummary`

Minimum fields:

- `package_investigation_id`
- `origin_repo_ids`
- `diagnosis_kind`
- `triggering_finding_codes`
- `investigator_report_ref`
- `package_fix_pr_ref`
- `package_commit_ref`
- `resume_ready`
- `remaining_repo_local_work`

### `ProviderRouterSummary`

Minimum fields:

- `provider_policy_id`
- `default_cost_tier`
- `allowed_route_kinds`
- `active_route_kind`
- `degraded_mode`
- `recent_router_decision_refs`
- `credential_lane_labels`

### `ApprovalWorkItem`

Minimum fields:

- `approval_id`
- `job_id`
- `approval_kind` (`spec`, `override`, `merge`, `resume`, `router-policy`)
- `required_by_mode`
- `requested_at`
- `requested_by`
- `decision_deadline`
- `summary`

## Event-stream envelope

Every live update event should carry:

- `event_id`
- `sequence`
- `occurred_at`
- `entity_kind`
- `entity_id`
- `event_kind`
- `job_id` when applicable
- `correlation_id`
- `causation_id`
- `severity`
- `snapshot_version`
- `payload`

Minimum event kinds:

- `job.snapshot`
- `job.transitioned`
- `phase.updated`
- `review.updated`
- `repo-truth.updated`
- `package-investigation.updated`
- `router-policy.updated`
- `router-decision.recorded`
- `approval.requested`
- `approval.resolved`
- `connectivity.overlay.updated`

`entity_kind` must stay explicit so the UI can never confuse downstream repo state, package investigations, and provider/router state.

## Control endpoints the app needs

All mutation endpoints are backend-mediated and must remain usable from CLI or raw API clients without the WinUI app.

| Endpoint family | Purpose | Notes |
| --- | --- | --- |
| `POST /api/forge/intake-submissions` | Start a project from a rough idea or approved handoff pointer | The app submits; the backend owns intake routing |
| `POST /api/jobs/{jobId}/pause` | Pause downstream orchestration | No direct shell stop commands |
| `POST /api/jobs/{jobId}/resume` | Resume orchestration after an allowed wait state | Must cross-check proof and policy |
| `POST /api/jobs/{jobId}/retry` | Retry a failed phase or scaffold step | Backend decides whether retry is legal |
| `POST /api/jobs/{jobId}/escalations` | Route a stuck job into review/audit/escalation | App provides reason; backend owns classification |
| `POST /api/approvals/{approvalId}/approve` | Resolve approval requests | Applies to spec, override, resume, or merge requests |
| `POST /api/approvals/{approvalId}/reject` | Reject a requested action | Rejection remains part of the job evidence |
| `POST /api/provider-credentials/{credentialLane}/enroll` | Submit or rotate a provider credential into backend-managed secret storage | The app may capture a secret transiently for this request but must not persist it locally after submission |
| `POST /api/router-policies/{policyId}/activate` | Apply an allowed provider/router policy change | Raw credentials remain out of the UI payload |

No endpoint in the WinUI client contract authorizes direct GitHub merge calls, direct repo mutation, or direct `wsl.exe` / `ssh` command mutation.

## Identifier rules

Identifiers must be opaque, stable, and globally unique within their own namespace.

Recommended prefixes:

- `job_...`
- `repo_...`
- `pkginv_...`
- `approval_...`
- `routerpol_...`
- `routerdec_...`

Rules:

1. IDs are never inferred from display labels.
2. Repo identity and orchestration-job identity stay separate.
3. Package-investigation IDs never reuse repo IDs.
4. Event stream records both `entity_kind` and `entity_id`.
5. Screen routing keys must preserve the state domain in the route, for example `/jobs/{jobId}`, `/repos/{repoId}`, `/package-investigations/{packageInvestigationId}`, and `/router/policies/{policyId}`.

## State-domain separation rules

The app must represent the following as separate lanes:

- **downstream orchestration state**: queue, phase, PR, review, pause, retry
- **generated repo truth**: tickets, workflow state, proofs, restart surfaces
- **package investigation state**: audit bundle, investigator report, package-fix PR, resume-ready status
- **provider/router state**: policy, route kind, degraded mode, recent decisions
- **local app safety overlay**: connectivity, trust, auth freshness, stale cache

No screen may compress those into one undifferentiated "status" field.

## CLI/API fallback rule

The backend must remain usable without the WinUI app:

- the same command endpoints must be callable by CLI tooling
- the same event/state feeds must be representable without a GUI
- the app must not rely on hidden WinUI-only commands or unreplayable local state
