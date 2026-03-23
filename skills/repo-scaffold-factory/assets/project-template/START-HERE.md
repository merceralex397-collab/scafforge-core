# START HERE

<!-- SCAFFORGE:START_HERE_BLOCK START -->
## Project

__PROJECT_NAME__

## Current State

The repo is operating with a ticketed OpenCode workflow that separates historical completion from current trust and enforces lease-based write lanes.

## Process Contract

- process_version: 5
- parallel_mode: parallel-lanes
- pending_process_verification: false
- bootstrap_status: pending
- bootstrap_proof: not yet recorded
- process_changed_at: Not yet recorded.
- process_note: No recorded process change summary.
- process_state: No pending process-change verification.

## Read In This Order

1. README.md
2. AGENTS.md
3. docs/spec/CANONICAL-BRIEF.md
4. docs/process/workflow.md
5. tickets/BOARD.md
6. tickets/manifest.json

## Current Ticket

- ID: SETUP-001
- Title: Bootstrap environment and confirm scaffold readiness
- Wave: 0
- Lane: repo-foundation
- Stage: planning
- Status: todo
- Resolution state: open
- Verification state: suspect
- Parallel safe: no

## Bootstrap and Trust Status

- Bootstrap is still pending. Run the bootstrap/setup lane before treating missing dependencies as product defects.
- No completed tickets currently require reverification.
- No reopened or done-but-untrusted tickets are recorded yet.

## Known Risks

- Validation can fail for environment reasons until bootstrap proof exists.
- Historical completion should not be treated as current trust once defects or process drift are discovered.

## Next Action

Replace the canonical brief placeholders, run `/bootstrap-check` or the Wave 0 setup lane to install and verify dependencies, then use `/kickoff` or the team leader agent to begin planning.
<!-- SCAFFORGE:START_HERE_BLOCK END -->
