# Scafforge Prevention Actions

## Package Changes Required

### PA-01

- change target: Scafforge managed surface for `.opencode/tools/smoke_test.ts`
- why it prevents recurrence:
  - Python smoke tests must prefer repo-native execution when `uv.lock`, `.venv`, or an explicit smoke-test override exists
  - this removes false failures like `/usr/bin/python3: No module named pytest` on uv-managed repos
- safe or intent-changing: safe
- validation:
  - rerun smoke-test detection in this repo and confirm it selects `uv run` or `.venv/bin/python`
  - confirm `EXEC-001` smoke-test stage can pass without manual artifact replacement

### PA-02

- change target: `audit_repo_process.py`
- why it prevents recurrence:
  - the audit should not return a clean diagnosis while the active ticket is still blocked by failing repo-managed execution evidence
  - it should at minimum inspect active-ticket stage, canonical smoke-test artifacts, and the actual result of the repo-managed test/import commands when those commands are already encoded by the repo contract
- safe or intent-changing: safe
- validation:
  - rerun the audit on this repo and confirm the script flags the smoke-test mismatch and failing full suite

## Validation and Test Updates

### PA-03

- change target: Scafforge tests for the managed smoke-test tool
- why it prevents recurrence:
  - the tool currently has no regression proof for uv-managed Python repos
- safe or intent-changing: safe
- validation:
  - add coverage for projects with `uv.lock`, `.venv`, and no system `pytest`

### PA-04

- change target: Scafforge audit/closeout regression tests
- why it prevents recurrence:
  - derived handoff text should not claim a dependent ticket is unblocked when the prerequisite ticket is not `done` and the full suite still fails
- safe or intent-changing: safe
- validation:
  - add a fixture repo where collection passes, full suite fails, and the active ticket is still in `smoke_test`

## Documentation or Prompt Updates

### PA-05

- change target: Scafforge docs/prompts for smoke-test and closeout
- why it prevents recurrence:
  - repo-managed acceptance commands must outrank generic language-default commands when they disagree
  - handoff surfaces should distinguish "ticket-local acceptance passed" from "full dependent suite passed"
- safe or intent-changing: safe
- validation:
  - audit a uv-managed Python repo and verify the handoff text names both the local blocker and any still-failing downstream suite work

## Open Decisions

- whether the managed smoke-test tool should support per-ticket command overrides directly or only smarter project-environment detection
- whether the audit script should execute repo-managed test commands directly or consume canonical artifacts plus targeted lightweight repro commands
