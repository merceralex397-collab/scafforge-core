# START HERE

<!-- SCAFFORGE:START_HERE_BLOCK START -->
## What This Repo Is

__PROJECT_NAME__

## Current State

The repo is operating under the managed OpenCode workflow. Use the canonical state files below instead of memory or raw ticket prose, and keep the single-lane-first execution posture unless bounded parallel work is explicitly justified.

## Read In This Order

1. README.md
2. AGENTS.md
3. docs/AGENT-DELEGATION.md
4. docs/spec/CANONICAL-BRIEF.md
5. docs/process/workflow.md
6. tickets/manifest.json
7. tickets/BOARD.md

## Current Or Next Ticket

- ID: SETUP-001
- Title: Bootstrap environment and confirm scaffold readiness
- Wave: 0
- Lane: repo-foundation
- Stage: planning
- Status: todo
- Resolution: open
- Verification: suspect

## Dependency Status

- current_ticket_done: no
- dependent_tickets_waiting_on_current: none
- split_child_tickets: none

## Generation Status

- handoff_status: bootstrap recovery required
- process_version: 7
- parallel_mode: sequential
- pending_process_verification: false
- repair_follow_on_outcome: clean
- repair_follow_on_required: false
- repair_follow_on_next_stage: none
- repair_follow_on_verification_passed: true
- repair_follow_on_updated_at: Not yet recorded.
- bootstrap_status: missing
- bootstrap_proof: None
- process_changed_at: Not yet recorded.

## Post-Generation Audit Status

- audit_or_repair_follow_up: none recorded
- reopened_tickets: none
- done_but_not_fully_trusted: none
- pending_reverification: none
- repair_follow_on_blockers: none

## Known Risks

- Validation can fail for environment reasons until bootstrap proof exists.
- Historical completion should not be treated as current trust once defects or process drift are discovered.
- Delegation mistakes can cause lifecycle loops; check `docs/AGENT-DELEGATION.md` before improvising a new handoff path.

## Next Action

Run `environment_bootstrap`, register its proof artifact, rerun `ticket_lookup`, and do not continue lifecycle work until bootstrap is ready.
<!-- SCAFFORGE:START_HERE_BLOCK END -->
