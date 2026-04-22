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
- scaffold_verified: false
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
- completion_primary_family: cli-script
- completion_overlay_families: none
- completion_claim_active: false
- completion_proof_blocking: false
- completion_proof_status: cli-script=inactive [static-contract:not_required, build-or-bootstrap:not_required, command-runtime:not_required, visual-review:not_required]
- process_changed_at: Not yet recorded.

## External Orchestration Boundary

- orchestration_may_read: docs/spec/CANONICAL-BRIEF.md, tickets/manifest.json, .opencode/state/workflow-state.json, START-HERE.md, .opencode/meta/bootstrap-provenance.json
- orchestration_must_not_write: tickets/manifest.json, .opencode/state/workflow-state.json
- phase_boundary: every autonomous phase ends in a PR or reviewable diff
- merge_gate_inputs: stage-gate evidence, registered artifacts, reviewer decision, and stack-specific validation outputs

## Post-Generation Audit Status

- audit_or_repair_follow_up: none recorded
- reopened_tickets: none
- done_but_not_fully_trusted: none
- pending_reverification: none
- repair_follow_on_blockers: none

## Resume Semantics

- resume_status: blocked
- repo_local_resume_path: none-active
- package_defect_wait_state: external orchestration only; keep outside canonical repo state
- resume_trigger: Do not begin downstream PR work until the one-shot scaffold clears VERIFY009 plus zero blocking VERIFY010 and VERIFY011 findings and publishes the verified restart surfaces.

## Known Risks

- Validation can fail for environment reasons until bootstrap proof exists.
- Historical completion should not be treated as current trust once defects or process drift are discovered.
- Delegation mistakes can cause lifecycle loops; check `docs/AGENT-DELEGATION.md` before improvising a new handoff path.

## Next Action

Run `environment_bootstrap`, register its proof artifact, rerun `ticket_lookup`, and do not continue lifecycle work until bootstrap is ready.
<!-- SCAFFORGE:START_HERE_BLOCK END -->
