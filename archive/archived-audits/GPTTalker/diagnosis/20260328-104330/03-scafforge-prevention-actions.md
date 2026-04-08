# Scafforge Prevention Actions

## Package Changes Required

### PKG-001

- Change target:
  - `.opencode/tools/ticket_reconcile.ts`
  - `.opencode/plugins/stage-gate-enforcer.ts`
  - `.opencode/tools/ticket_create.ts`
  - `.opencode/tools/issue_intake.ts`
  - `.opencode/tools/handoff_publish.ts`
- Why it prevents recurrence:
  - This bundle is the current live deadlock. The package needs one legal path to reconcile or safely route an artifactless, superseded, invalidated ticket so closeout publication is not trapped behind impossible preconditions.
- Safe or intent-changing:
  - safe
- Validation:
  - Add a regression scenario with:
    - a closed active ticket in workflow state
    - a superseded `done` ticket with `verification_state: invalidated`
    - no source artifacts on that invalidated ticket
  - Prove that:
    - reconciliation does not throw a runtime variable error
    - the reconciliation path can clear the publish blocker cleanly
    - `handoff_publish` succeeds afterward

### PKG-002

- Change target:
  - team-leader prompt template
  - `ticket-execution` scaffold guidance
  - lifecycle transition regression coverage
- Why it prevents recurrence:
  - The transcript still shows repeated retries after the same blocker. Package tests should fail if a future prompt/tool refresh reintroduces stage probing after repeated rejection.
- Safe or intent-changing:
  - safe
- Validation:
  - Transcript-style regression where `ticket_update` returns the same lifecycle blocker twice; expected outcome is blocker surfacing, not a third transition attempt.

### PKG-003

- Change target:
  - coordinator prompt template
  - stage-proof validation tests
  - transcript-backed audit regression fixtures
- Why it prevents recurrence:
  - The package must keep coordinators from authoring planning/implementation/review/QA artifacts directly and must reject PASS-style proof when execution evidence is missing.
- Safe or intent-changing:
  - safe
- Validation:
  - Regression transcript where validation is unavailable:
    - implementation/QA artifacts must not be accepted as PASS without raw command output
    - coordinator-authored specialist artifacts must be flagged as suspect evidence

## Validation and Test Updates

- Preserve the current `smoke_test` fixes with regression coverage:
  - shell-style `KEY=VALUE cmd ...` override parsing
  - acceptance-backed smoke-command inference before heuristic command detection
- Add a package-level closeout test that proves restart-surface publication is still possible after all tickets are done and a historical superseded ticket needs reconciliation.

## Documentation or Prompt Updates

- Keep the team-leader prompt and repo-local `ticket-execution` skill aligned on:
  - stop after repeated lifecycle blockers
  - specialist-owned artifact bodies
  - deterministic smoke-test ownership
- Document the historical/live split explicitly:
  - transcript-backed failures can be historical even when current surfaces are partially repaired
  - current-state deadlocks must be handled as live package defects first

## Open Decisions

- None identified for the subject repo. The required changes are package/workflow-contract fixes, not product-intent decisions.
