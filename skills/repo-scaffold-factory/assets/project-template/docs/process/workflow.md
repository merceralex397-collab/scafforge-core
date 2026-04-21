# Workflow

The default workflow for `__PROJECT_NAME__` is:

1. spec intake
2. ticket selection
3. planning
4. plan review
5. implementation
6. code review
7. security review when relevant
8. QA
9. deterministic smoke test
10. handoff and closeout

Rules:

- do not skip plan review
- do not start implementation without an approved plan
- do not close a ticket until artifacts and state files are updated
- keep the autonomous flow internal to agents, tools, and plugins
- keep ticket `status` coarse and queue-oriented: `todo`, `ready`, `plan_review`, `in_progress`, `blocked`, `review`, `qa`, `smoke_test`, `done`
- keep ticket `stage` lifecycle-oriented: `planning`, `plan_review`, `implementation`, `review`, `qa`, `smoke-test`, `closeout`
- keep plan approval in `.opencode/state/workflow-state.json`, not in ticket status
- treat `tickets/BOARD.md` as a derived human view, not an authoritative workflow surface
- write planning, implementation, review, QA, and optional handoff artifact bodies with `artifact_write` and then register them with `artifact_register`
- reserve `smoke-test` proof to the deterministic `smoke_test` tool
- require a registered stage artifact before advancing to the next stage
- let `ticket_update` derive the matching queue status from the lifecycle stage unless a compatible status is explicitly required
- stop on repeated lifecycle-tool contradictions; re-run `ticket_lookup`, inspect `transition_guidance`, and return a blocker instead of probing alternate stage/status values
- treat bootstrap readiness as a pre-lifecycle execution gate; if `ticket_lookup.bootstrap.status` is not `ready`, run `environment_bootstrap` first, then rerun `ticket_lookup` before any stage change
- if repeated bootstrap artifacts show the same command trace but it still omits the extra or group flags the repo layout requires, treat that as a managed bootstrap defect and stop retrying until audit or repair refreshes the tool
- only Wave 0 setup work may claim a write-capable lease before bootstrap is ready
- the team leader owns `ticket_claim` and `ticket_release`; planning, implementation, review, QA, and optional handoff specialists write only under the already-active ticket lease
- do not substitute raw shell package-manager commands for `environment_bootstrap` when bootstrap is missing, stale, or failed
- treat coordinator-authored planning, implementation, review, or QA artifacts as suspect evidence that must be remediated instead of accepted as canonical progression

## Bounded parallel work

- keep each individual ticket sequential through its own stage order
- default to one active foreground lane at a time during normal execution
- the team leader may opt into bounded parallel work only when all of these are true:
  - `parallel_safe` is `true`
  - `overlap_risk` is `low`
  - no direct or indirect dependency exists between the tickets being advanced
  - the tickets do not target the same ownership lane for write-capable work at the same time
- workflow-state keeps one active foreground ticket for tool enforcement, while `ticket_state` preserves per-ticket plan approval when the foreground ticket changes
- open active-ticket work remains the primary foreground lane; post-migration reverification is a follow-up path, not a reason to ignore an already-open active ticket
- keep one visible team leader by default and treat broader manager or section-leader hierarchies as advanced patterns for unusually large repos, not as a first-class scaffold profile

## Process-change verification

- `.opencode/meta/bootstrap-provenance.json` owns the canonical `workflow_contract.process_version`; `.opencode/state/workflow-state.json` mirrors the active process state for day-to-day execution
- if `.opencode/state/workflow-state.json` shows `pending_process_verification: true`, completed tickets are not treated as fully trusted yet
- `repair_follow_on` in `.opencode/state/workflow-state.json` owns post-repair follow-on stage truth; do not infer that state from restart prose or from `.opencode/meta/repair-execution.json`
- `repair_follow_on.outcome` is explicit:
  - `managed_blocked` means managed repair follow-on still blocks ordinary lifecycle routing
  - `source_follow_up` means Scafforge repair converged but source-layer follow-up remains
  - `clean` means managed repair itself is no longer blocking execution
- the affected done-ticket set is: done tickets whose latest smoke-test proof (or QA proof from an older contract) predates the current recorded process change, plus any done ticket without a registered `review` / `backlog-verification` artifact for the current process window
- use `ticket_lookup` to inspect the affected done-ticket set before routing work to the backlog verifier
- do not let pending process verification overwrite the active foreground lane when that active ticket is still open and its dependencies remain trusted
- use `ticket_reverify` to restore trust on a historical ticket after current backlog-verification or follow-up evidence exists; this trust-restoration path is allowed on closed done tickets and on reopened historical tickets when current evidence proves the reopened defect no longer reproduces, but it must not bypass a pending canonical acceptance refresh
- create migration, remediation, or reverification follow-up tickets only through the guarded `ticket_create` tool and only from current registered evidence
- use `ticket_create(source_mode=split_scope)` when an open or reopened parent ticket needs planned child decomposition; do not encode open-parent splits as `net_new_scope` or `post_completion_issue`
- keep split parents open while their child lanes are active, but do not foreground a parallel child ahead of missing parent planning proof or missing plan approval; do not mark an earlier ticket blocked just because later split children now carry the work
- use `ticket_reconcile` when fresh evidence proves an existing follow-up graph is stale or contradictory; pass the authoritative owner as `source_ticket_id` / `replacement_source_ticket_id` and the stale duplicate or child as `target_ticket_id`; when the stale ticket should disappear entirely, set `supersede_target: true` so reconciliation also closes that target as superseded; do not force no-op closeout artifacts or hand-edit `tickets/manifest.json`
- when `ticket_reconcile` supersedes or relinks an open `split_scope` child from its current parent, the parent lease is sufficient authority for that mutation in sequential mode; do not require an impossible dual-lease claim on both parent and child
- treat post-audit and post-repair follow-up as a first-class workflow path when diagnosis or repair work identifies concrete next tickets
- treat `repair_follow_on.outcome == managed_blocked` as the fail-closed gate; `source_follow_up` and truthful `pending_process_verification` remain visible but do not by themselves stop ordinary active-ticket lifecycle work

## Canonical ownership

- durable project facts live in `docs/spec/CANONICAL-BRIEF.md`
- machine queue state and artifact metadata live in `tickets/manifest.json`
- transient foreground stage and per-ticket approval state live in `.opencode/state/workflow-state.json`
- artifact bodies live in the stage-specific directories under `.opencode/state/`
- cross-stage artifact metadata lives in `.opencode/state/artifacts/registry.json`
- `.opencode/meta/bootstrap-provenance.json` stays provenance-only; queue and restart routing belong to manifest, workflow-state, and the derived restart surfaces
- restart guidance lives in `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md`; all three are derived views that should be regenerated from canonical state after workflow mutations

## Stage Proof

- before plan review: a `planning` artifact must exist
- before implementation: the assigned ticket must already be in `plan_review`, and `approved_plan` must already be `true` in workflow-state from a prior approval step
- before code review: an `implementation` artifact must exist
- before QA: a review artifact must exist
- before deterministic smoke test: a `qa` artifact must exist, include executable evidence, and include structured visual proof when `.opencode/meta/bootstrap-provenance.json` marks the repo as requiring it
- before closeout: a passing `smoke-test` artifact produced by `smoke_test` must exist
- before a ready or finished handoff claim: the current-cycle `handoff_proof` state in `.opencode/state/workflow-state.json` must be `passed`
- if `handoff_proof.status` is `failed` or `missing`, restart surfaces must stay blocked on proof rather than claiming ready state

## Visual proof block

Visually reviewable repos should record visual proof inside the QA artifact instead of relying on implied human taste. Use these machine-readable fields:

- `visual_proof_status`
- `visual_proof_evidence`
- `visual_proof_surfaces`
- `visual_rubric_blockers`
- `visual_style_note`
- the repo-level trigger is `.opencode/meta/bootstrap-provenance.json -> requires_visual_proof: true`

This keeps style choice separate from quality failure while giving the stage gate concrete evidence to enforce.

## Transition Examples

- planning -> plan_review:
  - `ticket_update { "ticket_id": "<id>", "stage": "plan_review", "activate": true }`
- plan_review approval:
  - `ticket_update { "ticket_id": "<id>", "stage": "plan_review", "approved_plan": true, "activate": true }`
- approved plan_review -> implementation:
  - `ticket_update { "ticket_id": "<id>", "stage": "implementation", "activate": true }`
- implementation -> review:
  - `ticket_update { "ticket_id": "<id>", "stage": "review", "activate": true }`
- review -> qa:
  - `ticket_update { "ticket_id": "<id>", "stage": "qa", "activate": true }`
- qa -> smoke-test:
  - `ticket_update { "ticket_id": "<id>", "stage": "smoke-test", "activate": true }`
- smoke-test -> closeout:
  - `ticket_update { "ticket_id": "<id>", "stage": "closeout", "activate": true }`

## Diagnosis outputs

- diagnosis or review work may create a repo-local `diagnosis/` folder for report packs, process logs, and machine-readable manifests
- those diagnosis outputs are evidence surfaces, not implementation edits
- do not treat diagnosis report creation as permission to mutate product code or bypass canonical ticket and artifact tools
