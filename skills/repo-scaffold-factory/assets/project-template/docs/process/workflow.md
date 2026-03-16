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
9. handoff and closeout

Rules:

- do not skip plan review
- do not start implementation without an approved plan
- do not close a ticket until artifacts and state files are updated
- keep the autonomous flow internal to agents, tools, and plugins
- keep ticket `status` coarse and queue-oriented: `todo`, `ready`, `in_progress`, `blocked`, `review`, `qa`, `done`
- keep plan approval in `.opencode/state/workflow-state.json`, not in ticket status
- treat `tickets/BOARD.md` as a derived human view, not an authoritative workflow surface
- write stage artifact bodies with `artifact_write` and then register them with `artifact_register`
- require a registered stage artifact before advancing to the next stage

## Parallel lanes

- keep each individual ticket sequential through its own stage order
- the team leader may advance multiple tickets in parallel only when all of these are true:
  - `parallel_safe` is `true`
  - `overlap_risk` is `low`
  - no direct or indirect dependency exists between the tickets being advanced
  - the tickets do not target the same ownership lane for write-capable work at the same time
- default to a single visible team leader with parallel lanes; treat manager or section-leader hierarchies as an advanced pattern for unusually large repos

## Process-change verification

- if `.opencode/state/workflow-state.json` shows `pending_process_verification: true`, completed tickets are not treated as fully trusted yet
- route affected done tickets through the backlog verifier before creating migration follow-up work
- create migration follow-up tickets only through the guarded `ticket_create` tool and only from a registered `backlog-verification` artifact

## Canonical ownership

- durable project facts live in `docs/spec/CANONICAL-BRIEF.md`
- machine queue state and artifact metadata live in `tickets/manifest.json`
- transient approval and current-stage state live in `.opencode/state/workflow-state.json`
- artifact bodies live in the stage-specific directories under `.opencode/state/`
- cross-stage artifact metadata lives in `.opencode/state/artifacts/registry.json`
- restart guidance lives in `START-HERE.md` and should be regenerated from canonical state

## Stage Proof

- before plan review: a `planning` artifact must exist
- before implementation: `approved_plan` must be `true`
- before code review: an `implementation` artifact must exist
- before QA: a review artifact must exist
- before closeout: a `qa` artifact must exist
