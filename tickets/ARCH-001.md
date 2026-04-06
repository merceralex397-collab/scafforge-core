# ARCH-001: Publish authority ADR and canonical truth-domain inventory

## Summary

Write the authority ownership ADR and invariant catalog that define diagnosis ownership, runtime mutation ownership, pivot-state ownership, contract-alignment obligations, and publish-gate ownership for the Scafforge package and generated repos.

## Why

The RFC cannot be implemented safely until the package has one written owner map for every truth domain it is changing. This ticket makes later code changes answer to an explicit authority document instead of implied assumptions.

## Package Boundary

- Define authority in package docs and references.
- Do not introduce package-root generated-repo runtime state while doing this work.
- If generated behavior is affected, document it through the template or package contract surfaces rather than by simulating a generated repo here.

## Do This

1. Write the authority ADR that names one owner for diagnosis disposition, runtime mutation, pivot-state persistence, restart publication, and contract alignment.
2. Write the invariant catalog that turns the RFC invariants into an explicit checklist future tickets can implement and validate against.
3. Call out repair-side restart rendering and raw workflow mutation as the first duplicate-authority seam to collapse.
4. Link the new docs from the package contract surfaces that need them.

## Files To Update

- `references/`
- `AGENTS.md`
- `skills/skill-flow-manifest.json`

## Verify

1. Confirm every truth domain named in the RFC has exactly one owner in the new docs.
2. Confirm the invariant catalog covers diagnosis, mutation, restart, pivot-state, blocker, and validation invariants.
3. Confirm later contract surfaces can cite the ADR and invariant catalog directly instead of restating ownership ad hoc.

## Wave

0

## Lane

authority-contract

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

- SETUP-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [x] A new authority ADR names one owner for diagnosis disposition, repo mutation, pivot state, restart publication, and contract alignment
- [x] A new invariant catalog covers every RFC invariant including pivot-state, publish-gate, and contract-alignment rules
- [x] The authority documents explicitly call out repair-side restart duplication as the first collapse target
- [x] The ADR and invariant catalog are referenced from the contract surfaces that depend on them

## Artifacts

- [references/authority-adr.md](../references/authority-adr.md)
- [references/invariant-catalog.md](../references/invariant-catalog.md)

## Notes

- RFC coverage: Phase 0 authority freeze and invariant catalog.
- Primary surfaces: new reference docs for authority ownership and invariant catalog, plus contract documents that consume them.
- This ticket is the source of truth for later cutovers; no implementation ticket should proceed with a different owner map.
