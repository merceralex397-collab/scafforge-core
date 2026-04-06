# STACK-002: Add Tier 1 full-toolchain execution proof coverage and audit alignment

## Summary

Add real Tier 1 execution proof coverage on full-toolchain hosts and align audit execution reporting so package release proof no longer falls back to detection-only semantics for stacks that claim runnable or buildable coverage.

## Why

The rewrite promises Tier 1 proof. This ticket turns that promise into real build or execution evidence instead of stack detection and good intentions.

## Package Boundary

- Update package proof harnesses, package validation, and audit reporting.
- Do not represent proof-host state through package-root runtime files.

## Do This

1. Implement proof-host validation for each Tier 1 stack defined by `STACK-001`.
2. Align `audit_execution_surfaces.py` with the proof-host contract so non-proof hosts degrade truthfully.
3. Mark which proof checks are mandatory for release in the package validation surfaces.
4. Document any host prerequisites needed to run the full Tier 1 proof program.

## Files To Update

- `skills/scafforge-audit/scripts/audit_execution_surfaces.py`
- `scripts/integration_test_scafforge.py`
- proof-host docs or validation metadata tied to the Tier 1 matrix

## Verify

1. Run the Tier 1 proof program on a full-toolchain host when implementing this ticket.
2. Confirm missing-toolchain hosts report truthful degradation instead of false success.
3. Confirm release validation now distinguishes mandatory Tier 1 proof from detection-only checks.

## Wave

4

## Lane

execution-proof

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

- STACK-001
- AUDIT-001
- PROOF-002

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] Proof-host validation covers Python, Node, Rust, Go, Godot, Java or Android, C or C++, and .NET with real execution or build evidence
- [ ] `audit_execution_surfaces.py` aligns with the proof-host contract and reports truthful degradation on non-proof hosts
- [ ] Smoke, integration, or dedicated proof validation surfaces know which Tier 1 checks are mandatory for release
- [ ] The package no longer relies on detection-only proof for Tier 1 release acceptance

## Artifacts

- None yet

## Notes

- RFC coverage: Tier 1 execution proof policy and the explicit Tier 1 stack list named in the RFC.
- Primary surfaces: `skills/scafforge-audit/scripts/audit_execution_surfaces.py`, `scripts/integration_test_scafforge.py`, fixtures or proof-host docs.
- This ticket is the operational follow-through on the proof-host matrix frozen by `STACK-001`.
