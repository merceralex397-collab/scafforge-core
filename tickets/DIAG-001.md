# DIAG-001: Emit the authoritative disposition bundle from audit outputs

## Summary

Define and emit the machine-readable disposition bundle so diagnosis, repair, and follow-up routing all start from one authoritative ownership surface instead of finding-prefix heuristics.

## Why

Repair cannot stop inventing its own ownership model until diagnosis produces a structured routing artifact that repair can consume directly.

## Package Boundary

- Implement this in package audit code and diagnosis-pack outputs.
- Do not solve it by adding package-root runtime trackers.

## Do This

1. Define the disposition bundle schema and name the allowed ownership classes.
2. Update audit reporting and repo-process assembly so every diagnosis finding emits a disposition entry.
3. Persist the disposition bundle in diagnosis-pack outputs alongside the existing human-readable reports.
4. Preserve current evidence provenance and explanatory report content while adding the new machine-readable layer.

## Files To Update

- `skills/scafforge-audit/scripts/audit_reporting.py`
- `skills/scafforge-audit/scripts/audit_repo_process.py`
- diagnosis-pack output helpers or schemas used by those scripts

## Verify

1. Run the relevant smoke or integration coverage for diagnosis-pack generation.
2. Confirm every finding in a diagnosis pack receives exactly one disposition class.
3. Confirm the machine-readable bundle and human-readable reports describe the same findings and provenance.

## Wave

1

## Lane

audit-disposition

## Parallel Safety

- parallel_safe: false
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

- [x] `audit_reporting.py` and `audit_repo_process.py` emit a structured disposition bundle for every diagnosis finding
- [x] The bundle distinguishes managed blockers, manual prerequisites, source follow-up, process-state-only, and advisory findings
- [x] Diagnosis packs persist the disposition bundle in a machine-readable form that repair can consume directly
- [x] Existing audit output surfaces continue to explain the same findings without losing evidence provenance

## Artifacts

- None yet

## Notes

- RFC coverage: Workstream A authoritative disposition model.
- Primary surfaces: `skills/scafforge-audit/scripts/audit_reporting.py`, `skills/scafforge-audit/scripts/audit_repo_process.py`.
- This ticket is the authoritative input required before repair can stop reclassifying findings locally.
