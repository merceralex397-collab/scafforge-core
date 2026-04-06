# DOCS-001: Post-implementation reconcile root docs and contracts to the shipped package state

## Summary

After implementation tickets land, rewrite the root package docs and contract markdowns so `AGENTS.md`, `README.md`, contract references, skill docs, and related markdown surfaces describe the shipped package behavior rather than the planned rewrite.

## Why

The root docs will drift during the implementation program. This ticket is the deliberate final pass that brings every authoritative markdown surface back into sync with the code that actually shipped.

## Package Boundary

- Update package docs and package skill docs only.
- Describe generated-repo behavior through the package docs and template assets; do not create package-root runtime scaffolding.
- Run this ticket after the implementation PR sequence is complete, not as an early speculative rewrite.

## Do This

1. Rewrite root `AGENTS.md` so it reflects the final shipped package rules rather than the in-progress implementation program.
2. Update root `README.md` to describe the final package behavior, flows, validation, and proof model accurately.
3. Update the contract references and any affected `SKILL.md` files so they match the landed code and template behavior.
4. Audit other root or reference markdowns for stale rewrite-era assumptions and either fix or explicitly archive them.

## Files To Update

- `AGENTS.md`
- `README.md`
- affected `skills/*/SKILL.md` files
- `references/*.md`
- transition-guide docs introduced during implementation

## Verify

1. Confirm root `AGENTS.md`, `README.md`, contract references, and affected skill docs all describe the same shipped behavior.
2. Confirm stale rewrite-planning language, temporary warnings, or pre-cutover assumptions have been removed or clearly marked as historical context.
3. Run `npm run validate:contract` after the doc reconciliation pass.

## Wave

5

## Lane

package-docs

## Parallel Safety

- parallel_safe: true
- overlap_risk: low

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

- ARCH-002
- CONTRACT-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] Root `AGENTS.md`, root `README.md`, affected `references/*.md`, and affected `skills/*/SKILL.md` files describe the shipped package behavior rather than the planned rewrite
- [ ] Docs remove stale dual-authority language around repair-side restart rendering, mutation ownership, and blocker semantics
- [ ] Any transition-guide docs created during implementation are either updated to final state or explicitly archived
- [ ] `npm run validate:contract` passes after the final documentation reconciliation

## Artifacts

- None yet

## Notes

- RFC coverage: Workstream F documentation alignment and rollout policy.
- Primary surfaces: root `AGENTS.md`, root `README.md`, affected `references/*.md`, affected `SKILL.md` files, and any transition-guide docs introduced during implementation.
- This ticket is intentionally last in the implementation sequence.