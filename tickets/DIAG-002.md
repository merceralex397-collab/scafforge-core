# DIAG-002: Consume the disposition bundle in repair and surface reclassification deltas

## Summary

Teach repair to read the authoritative disposition bundle, report shadow-mode deltas against the legacy classifier, and stop silently inventing its own ownership model.

## Why

This is the bridge from the new diagnosis-owned routing model to the old repair logic. It lets the package prove the new classification model before removing the legacy one.

## Package Boundary

- Change repair orchestration and metadata in package code.
- Do not introduce package-root runtime trackers to record shadow-mode state.

## Do This

1. Update repair to load the diagnosis disposition bundle instead of classifying findings from prefixes.
2. Add shadow-mode comparison between the legacy classifier and the new authoritative bundle.
3. Record any reconcile reasons when repair needs to report a difference rather than silently swallowing it.
4. Start deriving `repair_follow_on` from the disposition bundle plus verification inputs.

## Files To Update

- `skills/scafforge-repair/scripts/run_managed_repair.py`
- shared schema or metadata helpers introduced by `DIAG-001`
- repair evidence or provenance helpers touched by the shadow-mode reporting

## Verify

1. Confirm repair reads the disposition bundle from a diagnosis pack.
2. Confirm shadow-mode output shows classification deltas when the two models disagree.
3. Confirm repair no longer hides its ownership decisions behind implicit prefix heuristics.

## Wave

2

## Lane

repair-disposition

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

- DIAG-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `run_managed_repair.py` reads the diagnosis disposition bundle instead of re-deriving ownership from finding prefixes
- [ ] Shadow-mode comparison reports any legacy-versus-authoritative classification delta before full cutover
- [ ] `repair_follow_on` outcome derivation no longer depends on silent local reclassification heuristics
- [ ] Repair output records any explicit reconcile reason when a later phase must disagree with diagnosis

## Artifacts

- None yet

## Notes

- RFC coverage: Workstream A cutover from diagnosis-owned routing to repair consumption.
- Primary surfaces: `skills/scafforge-repair/scripts/run_managed_repair.py`, repair execution metadata, and any shared schema module introduced by `DIAG-001`.
- This ticket must leave enough evidence for later removal of legacy classifier paths.
