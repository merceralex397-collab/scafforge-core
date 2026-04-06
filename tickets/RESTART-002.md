# RESTART-002: Retire regenerate_restart_surfaces as an independent renderer

## Summary

Turn `regenerate_restart_surfaces.py` into a thin runtime-backed adapter or eliminate its independent renderer role so package-side restart publication can no longer drift from runtime restart truth.

## Why

The restart contract is not real until the old package-side renderer stops behaving like a second authority. This ticket removes that escape hatch.

## Package Boundary

- Rework package repair or pivot callers and package-owned renderer code.
- Keep restart truth in runtime-owned template behavior rather than package-root state.

## Do This

1. Reduce `regenerate_restart_surfaces.py` to a thin adapter over the canonical restart-derivation contract, or remove it if direct callers can be updated cleanly.
2. Update all package callers that still depend on the independent renderer.
3. Remove any private recomputation of restart inputs from that path.
4. Add validation coverage so a future package-side restart writer causes a failing test.

## Files To Update

- `skills/scafforge-repair/scripts/regenerate_restart_surfaces.py`
- package callers that invoke restart regeneration
- validation coverage for restart publication drift

## Verify

1. Confirm there is no authoritative package-side restart renderer left after the change.
2. Confirm repair and pivot publication routes through the same restart contract.
3. Confirm validation catches any future drift between package callers and runtime-owned restart truth.

## Wave

2

## Lane

restart-surfaces

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

- REPAIR-001
- RESTART-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `regenerate_restart_surfaces.py` becomes a thin runtime-backed adapter or is otherwise stripped of independent render logic
- [ ] No package-side restart renderer remains authoritative after this cutover
- [ ] Repair and pivot restart publication use the same canonical derivation contract
- [ ] Validation clearly fails if a package-side restart writer drifts from runtime-owned restart truth

## Artifacts

- None yet

## Notes

- RFC coverage: Workstream B repair-side renderer collapse and final-state publish gate preconditions.
- Primary surfaces: `skills/scafforge-repair/scripts/regenerate_restart_surfaces.py`, `workflow.ts`, `handoff_publish.ts`, repair or pivot callers.
- This ticket is the explicit answer to the review note that restart rendering duplication was understated.
