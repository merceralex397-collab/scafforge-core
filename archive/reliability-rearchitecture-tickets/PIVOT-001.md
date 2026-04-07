# PIVOT-001: Formalize pivot-state ownership and bounded persistence rules

## Summary

Turn `.opencode/meta/pivot-state.json` into an explicitly owned truth domain by bounding which pivot surfaces may write it, which surfaces may only derive from it, and how it feeds restart publication.

## Why

Pivot state already behaves like canonical workflow truth. Until the package names its owner and write rules, pivot can still drift through sidecar behavior and private script assumptions.

## Package Boundary

- Define and enforce pivot-state ownership in package pivot code and docs.
- Do not manage pivot-state through package-root generated-repo runtime files.

## Do This

1. Define the pivot-state write contract and name the one persistence owner.
2. Separate canonical pivot fields from fields that are only derived inputs to restart publication.
3. Update pivot planning, tracking, and publishing surfaces so they all describe the same ownership model.
4. Make the restart contract read pivot-state truth rather than synthesize it.

## Files To Update

- `skills/scafforge-pivot/scripts/pivot_tracking.py`
- `skills/scafforge-pivot/scripts/plan_pivot.py`
- `skills/scafforge-pivot/scripts/publish_pivot_surfaces.py`
- related package reference docs

## Verify

1. Confirm there is exactly one package surface that persists pivot-state.
2. Confirm other pivot surfaces read or derive from that state without silently backfilling it.
3. Confirm the pivot-state fields are documented well enough for restart and audit work to consume correctly.

## Wave

1

## Lane

pivot-state

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

- ARCH-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [x] `.opencode/meta/pivot-state.json` has one explicit persistence owner and documented write contract
- [x] `pivot_tracking.py`, `plan_pivot.py`, and related pivot surfaces stop implying that pivot state is an unowned sidecar
- [x] Pivot-state fields distinguish canonical pivot truth from derived restart-surface data
- [x] The contract documents how restart surfaces may read pivot state without synthesizing it

## Artifacts

- None yet

## Notes

- RFC coverage: pivot-state truth domain, pivot-state invariants, and workstream C ownership model.
- Primary surfaces: `skills/scafforge-pivot/scripts/pivot_tracking.py`, `plan_pivot.py`, `publish_pivot_surfaces.py`, and related reference docs.
- This ticket closes the under-specified pivot-state ownership gap identified in review.
