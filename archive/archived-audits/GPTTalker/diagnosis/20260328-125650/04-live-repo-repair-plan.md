# Live Repo Repair Plan

## Preconditions

- Audit scope stayed non-mutating with respect to product code and workflow state. Only the diagnosis pack under `diagnosis/20260328-125650/` was written.
- This is a reconciled diagnosis result, not the raw deterministic audit-script output.
- The supplied `session2.md` export remains the main chronology source; the raw `2026-03-28T123330.log` sample is supporting execution telemetry, not a replacement for canonical state review.

## Package Changes Required First

- No package work is required before the next subject-repo action.
- Evidence:
  - the current team-leader prompt already says derived restart views must agree with canonical state and that `pending_process_verification` clears only after `affected_done_tickets` is empty
  - the current workflow doc already encodes the same rule
  - the surviving blocker is a live repo-state contradiction, not a missing package refresh prerequisite

## Safe Repo Repair Actions

- Next required action: repo-local workflow-state and restart-surface reconciliation.
- Safe repair scope:
  - re-run canonical `ticket_lookup` / process-verification inspection to determine whether `affected_done_tickets` is actually empty
  - if the canonical list is still non-empty, remove the “cleared / all work complete” prose from:
    - `START-HERE.md`
    - `.opencode/state/context-snapshot.md`
    - `.opencode/state/latest-handoff.md`
  - if the canonical list is empty, clear `pending_process_verification` through the supported workflow path and then regenerate the derived restart surfaces from canonical state
  - preserve truthful `repair_follow_on.outcome: clean` while separating it from process-verification state

## Ticket Follow-Up

### REMED-001

- Linked Report 1 / Report 2 ids: `CURR-001`
- Action type: `generated-repo remediation / state reconciliation`
- Should `scafforge-repair` run: `yes`
- Manual carry into Scafforge dev repo first: `no`
- Target repo: `subject repo`
- Summary:
  - Reconcile canonical process-verification state with derived restart publication so the repo exposes one truthful next move instead of contradictory completion claims.

## Reverification Plan

- After repair:
  - prove `.opencode/state/workflow-state.json` and all three derived restart surfaces agree on whether process verification is still pending
  - prove the restart surfaces no longer claim “cleared” while canonical state remains `true`
  - if process verification is still pending, prove the published next action points to the correct reverification path instead of “all work complete”
  - rerun one fresh audit after the repair step and verify the contradiction no longer appears
