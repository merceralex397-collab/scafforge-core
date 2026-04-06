# RESTART-001: Implement the runtime-backed restart derivation contract

## Summary

Make `workflow.ts` and `handoff_publish.ts` the canonical owners of restart derivation so `START-HERE.md`, `context-snapshot.md`, and `latest-handoff.md` are always rendered from runtime-owned state instead of package-side parallel logic.

## Why

Repair-side restart rendering is the largest duplicate-authority seam in the package. This ticket defines the one derivation contract the rest of the rewrite is supposed to obey.

## Package Boundary

- Change generated-repo behavior by editing package-owned template assets and package callers.
- Do not compensate by adding package-root restart state files.

## Do This

1. Define the restart-derivation contract in `workflow.ts` for all three derived restart surfaces.
2. Make `handoff_publish.ts` call that contract as the canonical publication path.
3. Include manifest, workflow, and pivot inputs explicitly in the contract and document when publication is legal.
4. Expose the contract in a way that repair and pivot callers can reuse later without inventing private render logic.

## Files To Update

- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts`
- package docs or validation surfaces that describe restart publication

## Verify

1. Confirm `START-HERE.md`, `context-snapshot.md`, and `latest-handoff.md` all derive from one runtime-owned contract.
2. Confirm the derivation contract names its canonical inputs and publication preconditions.
3. Run the relevant package validation so restart publication expectations stay in sync with the template behavior.

## Wave

1

## Lane

restart-surfaces

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

- ARCH-001
- MUT-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [x] `workflow.ts` defines the canonical restart-derivation contract for `START-HERE.md`, `context-snapshot.md`, and `latest-handoff.md`
- [x] `handoff_publish.ts` uses that contract as the runtime publication path
- [x] The contract explicitly includes manifest, workflow, and pivot inputs and defines when restart publication is legal
- [x] Repair and pivot can call the restart contract without inventing local render semantics

## Artifacts

- None yet

## Notes

- RFC coverage: Workstream B canonical restart derivation and greenfield publish-gate clarification.
- Primary surfaces: `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`, `.../.opencode/tools/handoff_publish.ts`.
- This ticket should account for all three derived restart surfaces together rather than leaving any single renderer behind.
