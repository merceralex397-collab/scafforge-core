# Ticket System

This repo uses:

- `tickets/manifest.json` as the machine-readable source of truth
- `tickets/BOARD.md` as the human board
- `tickets/templates/TICKET.template.md` as the ticket file template
- the stage-specific directories under `.opencode/state/` for canonical stage artifact bodies

Rules:

- keep ticket `status` coarse: `todo`, `ready`, `plan_review`, `in_progress`, `blocked`, `review`, `qa`, `smoke_test`, `done`
- keep ticket `stage` lifecycle-oriented: `planning`, `plan_review`, `implementation`, `review`, `qa`, `smoke-test`, `closeout`
- keep `wave`, `lane`, `parallel_safe`, and `overlap_risk` aligned with the real ownership and concurrency boundaries
- keep plan approval in `.opencode/state/workflow-state.json`
- treat `tickets/BOARD.md` as a derived human board, not a second state machine
- only Wave 0 setup work may claim a write-capable lease before bootstrap is ready
- the team leader owns `ticket_claim` and `ticket_release`; specialist agents write stage artifacts and code under the active ticket lease
- use registered artifacts for stage proof instead of inferring state from raw ticket text
- keep artifact metadata on the owning ticket entry in `tickets/manifest.json`
- keep `tickets/<id>.md` synchronized with manifest-backed ticket state; use the Notes section for durable human context
- mirror artifact metadata into `.opencode/state/artifacts/registry.json`
- create migration, remediation, or reverification follow-up tickets through the guarded `ticket_create` tool instead of raw manifest edits
- treat post-audit and post-repair follow-up as a first-class ticket flow when current evidence identifies concrete next work
- use `ticket_lookup.transition_guidance` before changing a ticket stage
