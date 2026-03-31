# Diagnosis Plan Addendum

This document is a proposed replacement-contract addendum only. It amends the planning docs under `out/` and is not a claim that the live package already behaves this way.

## Purpose

This addendum amends `DIAGNOSIS-4-REPORT-PLAN.md` and should be read together with `DIAGNOSIS-ARCHITECTURE-AND-NAMING-PROPOSAL.md`.

Its purpose is to resolve the plan details that were previously ambiguous or contradictory.

## Amendment 1: Replace the old combined doctor model

Do not continue planning around `repo-process-doctor` as the long-term shape.

Recommended replacement:

- `scafforge-audit` owns diagnosis and report generation
- `scafforge-repair` owns repair execution and follow-up

This avoids one skill becoming an oversized diagnosis/repair catch-all.

## Amendment 2: Keep one public entrypoint

`scaffold-kickoff` remains the single public entrypoint.

It should classify the run into:

1. Greenfield scaffold
2. Retrofit scaffold
3. Managed repair/update
4. Diagnosis/review

Diagnosis routes internally to `scafforge-audit`.
Managed repair routes internally to `scafforge-repair`.

## Amendment 3: Remove the standalone refinement route

Do not continue planning around a package-level `refinement` route.

Recommended direction:

- remove it from the routing model
- disperse any genuinely useful refinement behavior into the relevant package skills
- keep first-pass scaffold quality as the main contract instead of normalizing repeated package reruns as a default operating mode

## Amendment 4: Remove the CLI from the package direction

The earlier docs treated the CLI as optional convenience.

That should now be tightened:

- the CLI should be removed
- package plans should stop assuming CLI commands remain part of the product surface
- docs, package metadata, validators, and smoke tests should be updated accordingly
- the package should be treated as a skill bundle, not an npm-facing product

## Amendment 5: Clarify the diagnosis non-taint rule

The core prohibition during diagnosis is against semantic mutation of the subject repo.

That means:

- diagnosis must not implement fixes
- diagnosis must not rewrite code, tickets, workflow state, or managed surfaces

It does **not** mean:

- "never run tests"
- "never execute verification"
- "never produce temporary runtime byproducts"

Transient byproducts such as logs, caches, and bytecode are operational side effects, not the same thing as tainting the evidence through repairs or edits.

The sole intentional file-creation exception is the repo-local `diagnosis/` folder and its report/log outputs.

## Amendment 6: Clarify result states

Diagnosis outputs should distinguish:

- `validated failures found`
- `no validated failures found`
- `inconclusive or partially verified`

If no validated failures are found and verification completed, then no action is needed beyond recording that result.

## Amendment 7: PR evidence remains optional

Diagnosis must work without PR metadata.

PR comments, review threads, and check metadata can enrich the result, but they are not required inputs.

## Amendment 8: Add ownership classification

Each issue should be typed as one of:

- `Scafforge package defect`
- `generated-repo managed-surface drift`
- `repo-specific customization drift`
- `subject-repo source bug`

This is stronger than only naming a related skill because it directly shapes the next action.

## Amendment 9: Add repair action typing to Report 4

Report 4 should classify each recommendation as one of:

- `safe Scafforge package change`
- `intent-changing package change`
- `generated-repo remediation ticket/process repair`

## Amendment 10: Reframe ticket follow-up as fragmented, not missing

The diagnosis/repair system needs an explicit ticket addition path, but the current system is fragmented rather than absent.

Current state:

- `ticket-pack-builder` covers bootstrap and some refine behavior
- generated repos have guarded ticket-creation concepts
- existing repair guidance already expects remediation tickets in some cases

Missing state:

- explicit post-audit/post-repair ticket rules as a first-class contract
- clear routing from Report 4 into the ticket system

Recommended addition:

- refine `ticket-pack-builder` so it explicitly supports remediation-oriented follow-up
- require guarded ticket creation where the generated repo supports it
- have `scafforge-audit` recommend the needed tickets
- have `scafforge-repair` trigger or route the ticket follow-up after repair

## Amendment 11: Keep generated review/audit bridge repo-local

The generated repo-local `review-audit-bridge` should remain generated-repo functionality, not a Scafforge core skill.

Recommended direction:

- keep ownership under `project-skill-bootstrap`
- store larger guidance in that generated skill's `references/` subfolder
- let it review the live repo, recommend tickets for poor implementations, and emit a log folder explaining what went wrong in the development process

## Amendment 12: Add skill-creation planning

If the package really creates new skills named `scafforge-audit` and `scafforge-repair`, that implementation should include a structured skill-creation pass using the local `skill-creator` guidance.

This is not a runtime dependency.
It is a package-maintenance aid to keep the new skills well-scoped and coherent.

## Amendment 13: Clarify execution-check naming

Current labels such as `EXEC001` are opaque and should not be treated as user-facing product language.

Recommended direction:

- treat them as current internal identifiers only
- prefer plain-English labels in reports and plan docs
- rename them later if they continue to exist after the audit refactor

## Amendment 14: Add package change inventory work

The implementation plan must carry a dedicated reference-update inventory because this repository is markdown-heavy and routing/name changes will have broad fallout.

The inventory is tracked in:

- [REFERENCE-UPDATE-INVENTORY.md](C:/Users/PC/Documents/GitHub/Scafforge/out/REFERENCE-UPDATE-INVENTORY.md)

## Summary Recommendation

The plan should now be read as a package refactor with these decisions already taken:

- one public entrypoint through `scaffold-kickoff`
- separate audit and repair host-side skills
- no standalone refinement route
- CLI removal
- PR bridge likely folded into audit
- generated repo-local review/audit bridge stays under `project-skill-bootstrap`
- explicit ticket follow-up path required
- diagnosis means no fixes, not "no verification"
- diagnosis outputs live in the subject repo `diagnosis/` folder
- package rename fallout must be tracked as a first-class workstream
