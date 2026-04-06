# GREEN-001: Add weak-model greenfield self-sufficiency proof without duplicating the greenfield gate

## Summary

Add proof that one-shot greenfield generation still exposes one legal next move, truthful blockers, and end-to-end continuation for weaker models without collapsing back into a repair-first or redundant-gate workflow.

## Why

The package is being rewritten to make greenfield self-sufficiency stronger, not to make repair permanent. This ticket proves the rewrite still serves that product direction.

## Package Boundary

- Update package proof harnesses, greenfield fixtures, and contract-facing validation.
- Validate generated-repo behavior through package-owned tests and template assets rather than package-root runtime state.

## Do This

1. Add greenfield proof families that measure one legal next move, truthful blockers, and end-to-end continuation for weaker models.
2. Keep those proofs inside the existing greenfield gate model instead of inventing a second publish pass.
3. Cover planning, implementation, validation, self-correction, and resume behavior in the proof set.
4. Preserve the distinction between greenfield proof and repair or pivot proof.

## Files To Update

- proof harness surfaces used for greenfield validation
- greenfield fixtures or seeding utilities
- contract docs or validation metadata that define the greenfield proof expectations

## Verify

1. Confirm the proof families still exercise the existing greenfield gate sequence.
2. Confirm the resulting fixtures demonstrate one legal next move and truthful blockers without relying on user memory.
3. Confirm the greenfield proof remains separate from repair-first behavior.

## Wave

5

## Lane

greenfield-proof

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

- STACK-002
- CONTRACT-001
- RESTART-001
- AUDIT-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] The proof program validates that a generated repo exposes one legal next move and truthful blockers through the existing greenfield gate sequence
- [ ] Weak-model proof families cover planning, implementation, validation, self-correction, and resume behavior without adding a redundant second greenfield publish pass
- [ ] Greenfield proof remains distinct from repair and pivot proof so the product path does not collapse back into audit-first operation
- [ ] The package demonstrates movement toward end-to-end generated-repo self-sufficiency, not just workflow documentation correctness

## Artifacts

- None yet

## Notes

- RFC coverage: end-state product direction and self-sufficiency proof families.
- Primary surfaces: proof harness, greenfield fixtures, `handoff_publish.ts`, contract docs that define VERIFY010 and VERIFY011 semantics.
- This ticket is the proof-side guard against accidentally making repair the default user path again.
