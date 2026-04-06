# PROOF-002: Extend the harness and fixture builders for stale-state edge cases

## Summary

Extend the existing harness, seeders, and fixture builders so the package can construct restart drift, split-scope, pivot-state, migration, and partial-transaction failure cases instead of only the current happy-path or code-list coverage surfaces.

## Why

The proof harness needs to manufacture the stale-state and interrupted-flow cases the RFC is trying to eliminate. Without that, the rewrite will be tested mostly on happy-path repos.

## Package Boundary

- Update package harness and fixture-seeding utilities.
- Keep generated-repo runtime state inside seeded fixtures, not as package-root state for this repo.

## Do This

1. Add harness support for restart drift, split-scope contradictions, pivot-state edge cases, migration states, and interrupted transactions.
2. Extend the repo seeders and GPTTalker fixture builders to generate those cases cheaply.
3. Ensure the harness remains reusable across smoke, integration, and migration validation.
4. Cover the hidden stale-state writers the RFC identifies, not just explicit ticket errors.

## Files To Update

- `scripts/test_support/scafforge_harness.py`
- `scripts/test_support/repo_seeders.py`
- `scripts/test_support/gpttalker_fixture_builders.py`

## Verify

1. Confirm the harness can seed each targeted edge case on demand.
2. Confirm those seeded cases are consumable by smoke, integration, and migration validators.
3. Run the relevant validation paths against at least one interrupted-transaction and one restart-drift case.

## Wave

4

## Lane

validation-harness

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

- PROOF-001
- LEG-002
- PIVOT-002

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `scafforge_harness.py`, `repo_seeders.py`, and `gpttalker_fixture_builders.py` can seed restart drift, split-scope, pivot-state, migration, and partial-transaction failure cases
- [ ] The harness can construct the hidden stale-state cases called out in the RFC instead of only happy-path repos
- [ ] New proof families include interrupted repair or pivot scenarios where stale state would otherwise leak through
- [ ] The harness remains reusable across smoke, integration, and migration validation surfaces

## Artifacts

- None yet

## Notes

- RFC coverage: Workstream G harness evolution and the review note about `scripts/test_support/` being real delivery surfaces.
- Primary surfaces: `scripts/test_support/scafforge_harness.py`, `repo_seeders.py`, `gpttalker_fixture_builders.py`.
- This ticket is where stale-state edge cases become easy to reproduce on demand.
