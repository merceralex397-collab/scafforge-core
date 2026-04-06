# AUDIT-001: Align audit modules to the runtime invariant and restart contract

## Summary

Align the audit modules so they validate the same runtime mutation contract, restart derivation contract, pivot-state contract, and execution-proof rules that the implementation actually uses.

## Why

Once mutation and restart authority move, audit has to stop judging the package by the old contract. Otherwise audit becomes a source of false regressions and stale findings.

## Package Boundary

- Update package audit code and package validation only.
- Consume runtime-owned contract definitions from package sources or template assets; do not invent package-root state to compare against.

## Do This

1. Align the ticket-graph, contract-surface, lifecycle, restart, repair-cycle, and execution audit modules with the new runtime mutation contract.
2. Make restart drift checks point back to the canonical derivation contract instead of private audit assumptions.
3. Account for pivot-state ownership and the final-state publish gate in the relevant audit modules.
4. Remove or rewrite audit logic that still assumes the pre-cutover package behavior is canonical.

## Files To Update

- `skills/scafforge-audit/scripts/audit_ticket_graph.py`
- `skills/scafforge-audit/scripts/audit_contract_surfaces.py`
- `skills/scafforge-audit/scripts/audit_lifecycle_contracts.py`
- `skills/scafforge-audit/scripts/audit_restart_surfaces.py`
- `skills/scafforge-audit/scripts/audit_repair_cycles.py`
- `skills/scafforge-audit/scripts/audit_execution_surfaces.py`

## Verify

1. Run the package validation commands that exercise audit behavior after the alignment work.
2. Confirm audit findings now describe violations of the new runtime contract rather than the retired package-side behavior.
3. Confirm pivot-state and publish-gate regressions are detectable through the updated audit suite.

## Wave

2

## Lane

audit-contract

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

- INV-001
- INV-002
- RESTART-002

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `audit_ticket_graph.py`, `audit_contract_surfaces.py`, `audit_lifecycle_contracts.py`, `audit_restart_surfaces.py`, and `audit_execution_surfaces.py` validate the same contract the runtime mutation layer enforces
- [ ] Audit checks for restart publication and derived-surface drift point back to the canonical derivation contract instead of parallel logic
- [ ] Audit surfaces account for pivot-state ownership and publish-gate behavior where relevant
- [ ] The audit layer no longer assumes a contract that the runtime mutation path has already replaced

## Artifacts

- None yet

## Notes

- RFC coverage: Workstream E audit alignment and the review note about missing audit surfaces.
- Primary surfaces: all major audit modules listed in the RFC revision, especially `audit_repair_cycles.py`, `audit_restart_surfaces.py`, and `audit_execution_surfaces.py`.
- This ticket prevents the package from shipping an implementation contract that audit still misunderstands.
