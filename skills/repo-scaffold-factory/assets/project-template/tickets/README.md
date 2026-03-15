# Ticket System

This repo uses:

- `tickets/manifest.json` as the machine-readable source of truth
- `tickets/BOARD.md` as the human board
- `tickets/templates/TICKET.template.md` as the ticket file template
- the stage-specific directories under `.opencode/state/` for canonical stage artifact bodies

Rules:

- keep ticket `status` coarse: `todo`, `ready`, `in_progress`, `blocked`, `review`, `qa`, `done`
- keep plan approval in `.opencode/state/workflow-state.json`
- treat `tickets/BOARD.md` as a derived human board, not a second state machine
- use registered artifacts for stage proof instead of inferring state from raw ticket text
- keep artifact metadata on the owning ticket entry in `tickets/manifest.json`
- mirror artifact metadata into `.opencode/state/artifacts/registry.json`
