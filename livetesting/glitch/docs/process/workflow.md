# Workflow

The default workflow for `Glitch` is:

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
- keep autonomous flow inside agents, tools, plugins, and local skills
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
- only Wave 0 setup work may claim a write-capable lease before bootstrap is ready
- the team leader owns `ticket_claim` and `ticket_release`; specialists write only under the already-active ticket lease
- do not substitute raw shell package-manager commands for `environment_bootstrap` when bootstrap is missing, stale, or failed
- treat coordinator-authored planning, implementation, review, or QA artifacts as suspect evidence that must be remediated

## Glitch-Specific Execution Rules

- Product work should stay vertical-slice-first until the Startup Sector proves movement, glitches, hazards, checkpoints, and mobile controls together.
- Movement feel and input readability are foundational. Do not bury them behind cosmetic or narrative work.
- Glitch features must preserve telegraphing, recovery space, and curated event pools.
- Room structure should remain readable on mobile screens. Prefer hand-authored rooms with constrained mutation layers over full procedural generation.
- Validation should prefer Godot-native or repo-native commands such as headless startup, import checks, test harnesses, and ticket-defined smoke commands.

## Bounded Parallel Work

- keep each individual ticket sequential through its own stage order
- default to one active foreground lane at a time during normal execution
- the team leader may opt into bounded parallel work only when `parallel_safe` is `true`, `overlap_risk` is `low`, no dependency edge exists, and the tickets do not overlap in write ownership
- workflow-state keeps one active foreground ticket for synthesis and restart, while `ticket_state` preserves per-ticket plan approval when the foreground ticket changes
- keep the active open ticket as the foreground lane even when historical reverification is pending

## Canonical Ownership

- durable project facts live in `docs/spec/CANONICAL-BRIEF.md`
- machine queue state and artifact metadata live in `tickets/manifest.json`
- transient foreground stage and per-ticket approval state live in `.opencode/state/workflow-state.json`
- artifact bodies live in the stage-specific directories under `.opencode/state/`
- cross-stage artifact metadata lives in `.opencode/state/artifacts/registry.json`
- `.opencode/meta/bootstrap-provenance.json` stays provenance-only
- restart guidance lives in `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md`

## Stage Proof

- before plan review: a `planning` artifact must exist
- before implementation: the assigned ticket must already be in `plan_review`, and `approved_plan` must already be `true` in workflow-state
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
