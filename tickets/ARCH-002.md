# ARCH-002: Align package contract docs and flow manifest to the authority baseline

## Summary

Update the package contract documents and flow manifest so the shipped repo surfaces, skill graph, and authority model all describe the same mutation and publish-gate behavior.

## Why

Once the authority map exists, the package contract has to say the same thing everywhere. Otherwise the rewrite just recreates split authority in the docs and flow metadata.

## Package Boundary

- Work in package docs and flow metadata only.
- Update template behavior descriptions in their package-owned sources; do not create package-root generated state.

## Do This

1. Update `AGENTS.md` so package-vs-generated-repo boundaries, publish-gate ownership, and repair or pivot boundaries match the ADR.
2. Update `skills/skill-flow-manifest.json` so the flow graph and required outputs reflect the new owner map.
3. Update the contract references to reflect the new authority and blocker model.
4. Remove stale wording that still implies dual authority or redundant publication gates.

## Files To Update

- `AGENTS.md`
- `skills/skill-flow-manifest.json`
- `references/competence-contract.md`
- `references/one-shot-generation-contract.md`
- `references/stack-adapter-contract.md`

## Verify

1. Run `npm run validate:contract` after the contract surfaces are updated.
2. Confirm the same owner map appears in `AGENTS.md`, the flow manifest, and the contract references.
3. Confirm no package doc still describes repair-side restart rendering or duplicate mutation logic as canonical.

## Wave

0

## Lane

contract-alignment

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

- [x] `AGENTS.md` reflects the authority map, publish-gate rule, and greenfield versus repair or pivot boundary
- [x] `skills/skill-flow-manifest.json` reflects the new ownership map, required outputs, and downstream routing
- [x] `references/competence-contract.md`, `references/one-shot-generation-contract.md`, and `references/stack-adapter-contract.md` are updated or explicitly verified against the new model
- [x] No stale dual-authority or redundant-gate wording remains in the aligned contract surfaces

## Artifacts

- [AGENTS.md](../AGENTS.md)
- [skills/skill-flow-manifest.json](../skills/skill-flow-manifest.json)
- [references/competence-contract.md](../references/competence-contract.md)
- [references/one-shot-generation-contract.md](../references/one-shot-generation-contract.md)
- [references/stack-adapter-contract.md](../references/stack-adapter-contract.md)

## Notes

- RFC coverage: Workstream F, contract-alignment invariants, greenfield publish-gate boundary.
- Primary surfaces: `AGENTS.md`, `skills/skill-flow-manifest.json`, `references/competence-contract.md`, `references/one-shot-generation-contract.md`, `references/stack-adapter-contract.md`.
- This ticket closes the documentation drift class called out in the RFC review.
