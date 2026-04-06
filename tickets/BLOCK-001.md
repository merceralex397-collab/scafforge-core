# BLOCK-001: Narrow blocker semantics across audit, repair, and restart surfaces

## Summary

Tighten the blocker model so `managed_blocked`, `source_follow_up`, transcript-only follow-up, and `pending_process_verification` each mean one thing across diagnosis, repair, and restart guidance.

## Why

False blocker states were one of the main churn loops behind the RFC. This ticket narrows those meanings so the package stops freezing work for the wrong reasons.

## Package Boundary

- Update package diagnosis, repair, restart guidance, and validation.
- Do not create extra package-root state to paper over ambiguous blocker semantics.

## Do This

1. Define the blocker meanings precisely across diagnosis, repair, and restart publication.
2. Restrict `managed_blocked` to true managed-workflow and environment blockers.
3. Ensure source-follow-up, transcript-only follow-up, and pending process verification remain non-blocking unless another real blocker exists.
4. Add validation and fixture coverage for the false-blocker loops the RFC calls out.

## Files To Update

- `skills/scafforge-audit/scripts/audit_reporting.py`
- `skills/scafforge-repair/scripts/run_managed_repair.py`
- restart publication or guidance surfaces affected by blocker wording
- fixture or validation coverage for blocker semantics

## Verify

1. Confirm repos with only source follow-up or transcript follow-up no longer land in `managed_blocked`.
2. Confirm genuine managed-workflow or environment blockers still surface as blocking.
3. Run the relevant proof fixtures that previously reproduced false-blocker churn.

## Wave

3

## Lane

blocker-semantics

## Parallel Safety

- parallel_safe: false
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

- DIAG-002
- REPAIR-002
- AUDIT-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `managed_blocked` is emitted only for true managed-workflow or environment blockers
- [ ] `source_follow_up` and transcript-only follow-up do not block ordinary lifecycle continuation by themselves
- [ ] `pending_process_verification` alone does not escalate a repo into `managed_blocked`
- [ ] Audit, repair, and restart surfaces all describe the tightened blocker model consistently
- [ ] Validation covers the false-blocker loop that motivated the RFC

## Artifacts

- None yet

## Notes

- RFC coverage: blocker semantics, outcome invariants, and the original managed_blocked churn loop.
- Primary surfaces: `audit_reporting.py`, `run_managed_repair.py`, restart render or derivation contract surfaces, contract docs.
- This ticket should rerun the finding families that previously misclassified SESSION-derived follow-up as managed blockers.
