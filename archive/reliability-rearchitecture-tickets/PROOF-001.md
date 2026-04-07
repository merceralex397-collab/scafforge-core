# PROOF-001: Upgrade existing GPTTalker fixture contracts to convergence assertions

## Summary

Keep the existing GPTTalker fixture families but redefine their contracts around convergence, publish-safety, and blocker-truth so the proof program validates end-state correctness instead of only expected finding codes.

## Why

The fixture program already exists and already encodes real failure families. This ticket upgrades that asset instead of throwing it away and losing accumulated coverage.

## Package Boundary

- Update package fixtures, fixture metadata, and fixture builders.
- Do not create package-root runtime state to represent fixture outcomes.

## Do This

1. Preserve the existing GPTTalker fixture families and reframe their assertions around convergence, publish-safety, and blocker truth.
2. Replace code-list-only expectations with end-state correctness expectations where appropriate.
3. Keep the fixture metadata readable enough that future contributors can extend it deliberately.
4. Ensure the key failure families from the RFC remain explicitly represented.

## Files To Update

- `tests/fixtures/gpttalker/index.json`
- `scripts/test_support/gpttalker_fixture_builders.py`
- related fixture metadata consumed by smoke or integration validation

## Verify

1. Confirm the existing GPTTalker families still exist after the contract rewrite.
2. Confirm fixture assertions now measure convergence, publish-safety, or blocker truth where intended.
3. Run the package validation that consumes these fixture definitions.

## Wave

4

## Lane

fixture-proof

## Parallel Safety

- parallel_safe: true
- overlap_risk: medium

## Stage

complete

## Status

done

## Trust

- resolution_state: completed
- verification_state: verified
- finding_source: None
- source_ticket_id: None
- source_mode: None

## Depends On

- REPAIR-002
- BLOCK-001
- CYCLE-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [x] Existing GPTTalker fixture families are preserved and redefined around convergence, publish-safety, and blocker-truth assertions
- [x] Fixture contracts stop depending only on `expected_finding_codes` and `expected_coverage`
- [x] Repeated lifecycle contradiction, restart drift, and split-scope reconciliation families all assert end-state truth instead of only finding lists
- [x] Fixture metadata remains readable enough for package contributors to extend without guessing the new proof contract

## Artifacts

- `tests/fixtures/gpttalker/index.json`
- `scripts/test_support/gpttalker_fixture_builders.py`
- `scripts/integration_test_scafforge.py`
- `scripts/validate_scafforge_contract.py`
- `npm run validate:contract`
- `npm run validate:smoke`
- `python3 scripts/integration_test_scafforge.py`

## Notes

- RFC coverage: proof-program evolution and review note that the fixture program already exists.
- Primary surfaces: `tests/fixtures/gpttalker/index.json`, `scripts/test_support/gpttalker_fixture_builders.py`.
- This ticket ensures Phase 6 evolves the current fixture system instead of replacing it.
