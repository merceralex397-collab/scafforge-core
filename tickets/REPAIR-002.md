# REPAIR-002: Convert run_managed_repair into a staged transaction

## Summary

Refactor `run_managed_repair.py` into a closed transaction that resolves the repair basis, applies runtime-backed mutations, validates the candidate state, verifies the exact publication snapshot, and fails closed when any stage breaks.

## Why

This is the orchestration core of the rewrite. If repair is not transactional, the package can still diagnose the right thing and then publish the wrong thing.

## Package Boundary

- Update package repair orchestration and package validation.
- Drive generated behavior through package-owned runtime bridges or template assets; do not recreate runtime state at the package root.

## Do This

1. Break managed repair into explicit stages from basis resolution through final publication.
2. Add candidate-state invariant validation before any restart or `repair_follow_on` publication.
3. Run final verification on the exact post-mutation snapshot that repair intends to publish.
4. Fail closed on partial or invalid transactions and record enough staged evidence to diagnose the failure.

## Files To Update

- `skills/scafforge-repair/scripts/run_managed_repair.py`
- repair execution metadata helpers
- package validation or fixture coverage that proves transactional behavior

## Verify

1. Confirm repair cannot publish restart state from an intermediate snapshot.
2. Confirm transaction failures leave evidence but do not leave stale published guidance behind.
3. Run the relevant package smoke or integration coverage for interrupted and successful repair flows.

## Wave

3

## Lane

repair-engine

## Parallel Safety

- parallel_safe: false
- overlap_risk: high

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

- DIAG-002
- REPAIR-001
- RESTART-002
- INV-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `run_managed_repair.py` executes repair as a closed stage sequence from basis resolution through final publication
- [ ] Candidate-state invariant validation occurs before any restart publication or `repair_follow_on` publication
- [ ] Final-state verification runs on the exact post-mutation snapshot that repair intends to publish
- [ ] Repair fails closed when any stage breaks rather than leaving partially refreshed restart truth behind
- [ ] Repair records enough staged evidence to diagnose interrupted or invalid transactions

## Artifacts

- None yet

## Notes

- RFC coverage: Workstream D transactional repair orchestration and final-state publish gate.
- Primary surfaces: `skills/scafforge-repair/scripts/run_managed_repair.py`, repair execution metadata, and any candidate-state validation helpers introduced by this work.
- This is the central ticket that makes stale post-repair publication materially harder.
