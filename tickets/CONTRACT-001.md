# CONTRACT-001: Extend contract, smoke, and integration validation to enforce the new architecture

## Summary

Teach the package validation commands to enforce the re-architecture directly so authority drift, hidden stale-state writers, and publish-gate regressions become build-breaking problems instead of review-only findings.

## Why

The rewrite only holds if package validation starts failing when the architecture drifts. This ticket turns the new contract into an enforceable build condition.

## Package Boundary

- Update package validation scripts and package fixtures.
- Do not depend on generated-repo runtime state at the package root for validation.

## Do This

1. Extend contract validation so it checks authority alignment, publish-gate behavior, and blocker semantics.
2. Extend smoke and integration validation so they assert runtime mutation ownership and publish-safety.
3. Add checks for hidden stale-state writers and contract drift.
4. Ensure the validation set directly covers the regressions the RFC is meant to prevent.

## Files To Update

- `scripts/validate_scafforge_contract.py`
- `scripts/smoke_test_scafforge.py`
- `scripts/integration_test_scafforge.py`
- fixtures or helper code those validators depend on

## Verify

1. Run `npm run validate:contract` after the contract-validation work lands.
2. Run `npm run validate:smoke` and any targeted integration coverage touched by the new checks.
3. Confirm each new architectural regression class now has a failing validation path.

## Wave

4

## Lane

contract-validation

## Parallel Safety

- parallel_safe: true
- overlap_risk: medium

## Stage

planning

## Status

todo

## Trust

- resolution_state: open
- verification_state: suspect
- finding_source: None
- source_ticket_id: None
- source_mode: None

## Depends On

- ARCH-002
- PROOF-001
- PROOF-002
- BLOCK-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `python3 scripts/validate_scafforge_contract.py` enforces authority alignment, publish-gate semantics, and blocker-truth expectations
- [ ] `python3 scripts/smoke_test_scafforge.py` and `python3 scripts/integration_test_scafforge.py` assert runtime mutation ownership and publish-safety rather than only exact strings
- [ ] Validation fails when hidden stale-state writers or contract drift reappear
- [ ] The package validation set directly covers the architectural regressions the RFC is meant to prevent

## Artifacts

- None yet

## Notes

- RFC coverage: Workstream G validation enforcement and contract-alignment invariants.
- Primary surfaces: `scripts/validate_scafforge_contract.py`, `scripts/smoke_test_scafforge.py`, `scripts/integration_test_scafforge.py`.
- This ticket turns the architecture into a failing build when it drifts.
