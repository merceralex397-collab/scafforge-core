# Examples

## Team leader routing

Before:

- "status is planned, so plan review must be next"

After:

- "resolve the ticket through `ticket_lookup`, confirm the planning artifact exists, and only then route to plan review"

## Planner persistence

Before:

- "update the ticket file with the detailed plan"

After:

- "write the full plan with `artifact_write`, then register it with `artifact_register` at the canonical planning artifact path and return that same path in the handoff"

## Read-only shell utility

Before:

- allow `sed *` on a read-only inspection agent

After:

- keep the allowlist to `pwd`, `ls`, `find`, `rg`, `cat`, `head`, `tail`, and safe git inspection commands

## Ticket status model

Before:

- `planned`, `approved`, `in_progress`, `done`

After:

- ticket status: `todo`, `ready`, `in_progress`, `blocked`, `review`, `qa`, `done`
- workflow state: `ticket_state.<ticket-id>.approved_plan: true|false` with the top-level `approved_plan` mirroring the current active ticket
- stage proof: registered artifacts

## Visual-proof routing

Before:

- "the QA notes say the menu looks better now, so move to smoke test"

After:

- "if bootstrap provenance requires visual proof, keep the ticket in QA until the artifact includes `visual_proof_status`, evidence paths, reviewed surfaces, rubric blockers, and a style note that distinguishes intentional style from failure"
