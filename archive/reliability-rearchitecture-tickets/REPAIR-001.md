# REPAIR-001: Remove raw workflow-state reconstruction from apply_repo_process_repair

## Summary

Strip `apply_repo_process_repair.py` of its private workflow reconstruction logic so repair orchestration records intent and provenance but no longer manufactures canonical workflow truth on its own.

## Why

This is the concrete collapse point for the biggest duplicate-authority seam in the repair flow. Until this logic is removed, repair can still publish stale state after doing the right diagnosis work.

## Package Boundary

- Change package repair orchestration only.
- Push canonical workflow behavior back into runtime-owned template code rather than emulating it at the package root.

## Do This

1. Identify and remove private workflow reconstruction code in `apply_repo_process_repair.py`.
2. Route workflow-state changes triggered during repair through the shared runtime path.
3. Keep package-level intent, diff, and provenance recording, but stop using repair as a canonical workflow-state writer.
4. Preserve the repair data that still belongs at package level without rebuilding runtime truth locally.

## Files To Update

- `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
- shared runtime adapter or helper surfaces invoked by repair
- provenance helpers touched by the orchestration change

## Verify

1. Confirm repair no longer reconstructs canonical workflow state directly.
2. Confirm repair still records intent and provenance needed for later diagnosis.
3. Confirm workflow-related changes produced during repair now flow through the runtime-owned mutation contract.

## Wave

2

## Lane

repair-engine

## Parallel Safety

- parallel_safe: false
- overlap_risk: high

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

- MUT-001
- RESTART-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [x] `apply_repo_process_repair.py` no longer rebuilds canonical workflow state through a private parallel truth model
- [x] Workflow-state changes triggered during repair route through the canonical runtime mutation contract or a shared adapter path
- [x] Repair-side workflow updates preserve `active_ticket`, `repair_follow_on`, bootstrap, process-version, and lane-lease truth without inventing secondary semantics
- [x] The repair script records only orchestration intent and provenance that belong at package level

## Artifacts

- None yet

## Notes

- RFC coverage: Workstream B and D repair-side duplicate-authority collapse.
- Primary surfaces: `skills/scafforge-repair/scripts/apply_repo_process_repair.py`, runtime mutation adapter, and any provenance helpers used after cutover.
- This ticket specifically targets the large raw workflow-state writer identified as the biggest duplicate seam.
