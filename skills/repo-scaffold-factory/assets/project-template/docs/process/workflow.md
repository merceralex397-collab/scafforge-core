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

## Bounded parallel work

- keep each individual ticket sequential through its own stage order
- default to one active foreground lane at a time during normal execution
- the team leader may opt into bounded parallel work only when all of these are true:
  - `parallel_safe` is `true`
  - `overlap_risk` is `low`
  - no direct or indirect dependency exists between the tickets being advanced
  - the tickets do not target the same ownership lane for write-capable work at the same time
- workflow-state keeps one active foreground ticket for tool enforcement, while `ticket_state` preserves per-ticket plan approval when the foreground ticket changes
- keep one visible team leader by default and treat broader manager or section-leader hierarchies as advanced patterns for unusually large repos, not as a first-class scaffold profile

## Process-change verification

- `.opencode/meta/bootstrap-provenance.json` owns the canonical `workflow_contract.process_version`; `.opencode/state/workflow-state.json` mirrors the active process state for day-to-day execution
- if `.opencode/state/workflow-state.json` shows `pending_process_verification: true`, completed tickets are not treated as fully trusted yet
- the affected done-ticket set is: done tickets whose latest smoke-test proof (or QA proof from an older contract) predates the current recorded process change, plus any done ticket without a registered `review` / `backlog-verification` artifact for the current process window
- use `ticket_lookup` to inspect the affected done-ticket set before routing work to the backlog verifier
- use `ticket_reverify` to restore trust on a closed done ticket after current backlog-verification or follow-up evidence exists; this trust-restoration path is allowed on closed tickets and does not require reopening them
- create migration, remediation, or reverification follow-up tickets only through the guarded `ticket_create` tool and only from current registered evidence
- treat post-audit and post-repair follow-up as a first-class workflow path when diagnosis or repair work identifies concrete next tickets

## Canonical ownership

- durable project facts live in `docs/spec/CANONICAL-BRIEF.md`
- machine queue state and artifact metadata live in `tickets/manifest.json`
- transient foreground stage and per-ticket approval state live in `.opencode/state/workflow-state.json`
- artifact bodies live in the stage-specific directories under `.opencode/state/`
- cross-stage artifact metadata lives in `.opencode/state/artifacts/registry.json`
- restart guidance lives in `START-HERE.md` and should be regenerated from canonical state

## Stage Proof

- before plan review: a `planning` artifact must exist
- before implementation: the assigned ticket must already be in `plan_review`, and `approved_plan` must already be `true` in workflow-state from a prior approval step
- before code review: an `implementation` artifact must exist
- before QA: a review artifact must exist
- before deterministic smoke test: a `qa` artifact must exist and include executable evidence
- before closeout: a passing `smoke-test` artifact produced by `smoke_test` must exist

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
