# PIVOT-002: Align pivot publication with the final-state publish gate

## Summary

Apply the same final-state publish gate to pivot planning and publication so pivot restart surfaces only publish from verified post-mutation state and cannot bypass the runtime restart contract.

## Why

Pivot already has part of the right adapter pattern, but it can still drift at publication time. This ticket brings pivot under the same publish-gate discipline as repair.

## Package Boundary

- Update package pivot orchestration and package callers into runtime-owned restart logic.
- Do not add package-root restart files to represent pivot state.

## Do This

1. Align pivot publication with the same final-state publish gate used by repair.
2. Update pivot planning and publishing surfaces so they depend on verified post-mutation state.
3. Route pivot restart publication through the canonical restart contract.
4. Preserve truthful reporting of pending downstream pivot stages and ticket lineage work after the change.

## Files To Update

- `skills/scafforge-pivot/scripts/publish_pivot_surfaces.py`
- `skills/scafforge-pivot/scripts/plan_pivot.py`
- shared restart-contract callers used by pivot

## Verify

1. Confirm pivot publication does not occur before verification of the candidate final state.
2. Confirm pivot restart output comes from the canonical restart contract.
3. Confirm pivot still reports pending stages and lineage actions accurately after the gate change.

## Wave

3

## Lane

pivot-orchestration

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

- PIVOT-001
- RESTART-001
- REPAIR-002

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `publish_pivot_surfaces.py` only publishes restart surfaces from a verified post-mutation pivot state
- [ ] `plan_pivot.py` and related pivot orchestration surfaces reference the same publish-gate semantics as repair
- [ ] Pivot publication cannot bypass the runtime restart contract through private recomputation of restart inputs
- [ ] Pivot output remains truthful about pending downstream stages and lineage work after the gate change

## Artifacts

- None yet

## Notes

- RFC coverage: Workstream C and D pivot publication alignment.
- Primary surfaces: `skills/scafforge-pivot/scripts/publish_pivot_surfaces.py`, `plan_pivot.py`, runtime adapter or restart contract callers.
- This ticket makes the pivot path obey the same truthfulness rules that greenfield and repair already require.
