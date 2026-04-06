# STAGE-001: Align stage-completion scripts to transaction-owned state updates

## Summary

Rework the repair and pivot stage-completion helpers so they update only transaction-owned state and can no longer act as hidden restart publishers or secondary outcome calculators.

## Why

Stage-completion helpers are easy to forget and easy to let drift. This ticket closes those hidden writer paths before they reintroduce stale-state publication behind the transaction model.

## Package Boundary

- Update package repair and pivot helper scripts only.
- Keep published restart truth in runtime-owned behavior rather than helper-side side effects.

## Do This

1. Audit the current side effects of the repair and pivot stage-completion scripts.
2. Remove any restart publication or outcome-calculation behavior that belongs to the transaction owner instead.
3. Leave only the narrow state updates these helpers still legitimately own.
4. Document the remaining side effects so future tickets can validate them directly.

## Files To Update

- `skills/scafforge-repair/scripts/record_repair_stage_completion.py`
- `skills/scafforge-pivot/scripts/record_pivot_stage_completion.py`
- validation coverage for hidden writer regressions

## Verify

1. Confirm stage-completion scripts no longer publish restart surfaces or compute final outcomes independently.
2. Confirm the transaction or publish-gate owner still receives the data it needs.
3. Confirm validation fails if stage-completion helpers reintroduce hidden publication side effects.

## Wave

3

## Lane

stage-tracking

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

- REPAIR-002
- PIVOT-002

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [x] `record_repair_stage_completion.py` no longer behaves like an independent publication path outside the repair transaction
- [x] `record_pivot_stage_completion.py` no longer behaves like an independent publication path outside the pivot publish gate
- [x] Stage-completion scripts update only the state they still own and defer restart publication to the transaction or publish-gate owner
- [x] Hidden stage-completion side effects are documented and covered by validation after the change

## Artifacts

- `skills/scafforge-repair/scripts/record_repair_stage_completion.py`
- `skills/scafforge-pivot/scripts/record_pivot_stage_completion.py`
- `scripts/smoke_test_scafforge.py`
- `npm run validate:smoke`
- `npm run validate:contract`
- `python3 scripts/integration_test_scafforge.py`

## Notes

- RFC coverage: review finding about standalone `record_*_stage_completion.py` mutation paths.
- Primary surfaces: `skills/scafforge-repair/scripts/record_repair_stage_completion.py`, `skills/scafforge-pivot/scripts/record_pivot_stage_completion.py`.
- This ticket closes a class of easy-to-forget hidden writers that can otherwise leave stale restart or outcome state behind.
