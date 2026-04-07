# CYCLE-001: Align repair-cycle auditing with transaction outcomes and churn rules

## Summary

Update the churn-detection layer so repeated audit and repair analysis is based on disposition bundles, transaction outcomes, and convergence rules rather than only repeated finding codes.

## Why

If churn detection only compares repeated finding strings, it cannot tell the difference between real non-convergence and a truthful persistent follow-up case. This ticket makes the cycle detector measure convergence correctly.

## Package Boundary

- Update package audit logic and package proof fixtures.
- Do not add runtime-like state trackers to score convergence.

## Do This

1. Teach repair-cycle auditing to read disposition bundles and transaction outcomes.
2. Preserve transcript-backed causal-regression coverage while replacing string-only overlap checks.
3. Define convergence rules that distinguish repeated stale publication from truthful persistent findings.
4. Update proof fixtures so one-pass convergence expectations are measurable.

## Files To Update

- `skills/scafforge-audit/scripts/audit_repair_cycles.py`
- repair provenance or metadata helpers used by cycle analysis
- proof fixtures that exercise repeated audit or repair loops

## Verify

1. Confirm repeated-cycle findings now reflect non-convergence rather than string reuse alone.
2. Confirm causal-regression checks still work for transcript-backed repair cases.
3. Run the fixtures that model repeated audit-to-repair loops and inspect the resulting cycle findings.

## Wave

3

## Lane

repair-cycles

## Parallel Safety

- parallel_safe: true
- overlap_risk: low

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

- DIAG-002
- REPAIR-002
- AUDIT-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [x] `audit_repair_cycles.py` understands disposition bundles, transaction outcomes, and final publish-gate state
- [x] Repeated-cycle findings identify true non-convergence rather than stale string-level overlaps
- [x] Transcript-backed repair basis handling remains covered so causal-regression checks do not disappear
- [x] Cycle auditing helps prove that one audit-to-repair pass converges when the package logic is correct

## Artifacts

- None yet

## Notes

- RFC coverage: repeated-cycle churn detection and review note about `audit_repair_cycles.py` being a primary surface.
- Primary surfaces: `skills/scafforge-audit/scripts/audit_repair_cycles.py`, diagnosis manifest handling, repair provenance surfaces.
- This ticket is the main anti-loop check once transaction semantics exist.
