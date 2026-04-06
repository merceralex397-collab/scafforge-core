# RFC: Scafforge Reliability Re-architecture

## Status
Proposed final RFC for package implementation, revised to incorporate architecture review feedback and explicit implementation-surface ownership.

## Decision Summary
This RFC makes the following decisions final:

1. Diagnosis is the sole authority for finding ownership and follow-up disposition.
2. The generated repo runtime is the canonical mutation layer for ticket, workflow, artifact, and restart-surface mutations.
3. The largest current split-authority seam is repair-side restart rendering and raw workflow mutation in `apply_repo_process_repair.py` and `regenerate_restart_surfaces.py`; collapsing that seam is a primary implementation priority, not a secondary cleanup.
4. The existing pivot runtime-adapter pattern is the seed of the package-side bridge into generated runtime mutations and will be generalized rather than replaced.
5. `.opencode/meta/pivot-state.json` is a canonical truth domain with one explicit owner for pivot classification, stale-surface routing, downstream refresh obligations, and pivot restart inputs.
6. Managed repair is a transaction, not a sequence of loosely related steps.
7. Restart surfaces may only be published from a final verified post-mutation state.
8. The greenfield path already satisfies the publish-gate requirement through VERIFY010, VERIFY011, and `handoff_publish.ts`; this RFC formalizes the same rule for repair and pivot rather than adding a second greenfield gate.
9. `managed_blocked` is restricted to true managed-workflow or environment blockers.
10. For package development and release, Tier 1 execution proofs are mandatory on full-toolchain proof hosts.
11. Missing toolchains on other hosts must degrade truthfully, but release acceptance will not rely on best-effort-only hosts.
12. Legacy repos are upgraded by repair through an explicit migration path, not by indefinite compatibility drift.
13. Shadow validation is an internal Scafforge migration technique only. It is not part of the end-user product workflow.
14. The existing fixture and harness program will be extended from finding-code and coverage checks into convergence, publish-safety, and transactional proof. It will not be rebuilt from scratch.
15. Package contract documents and flow manifests must change in lockstep with authority and invariant changes.
16. The end-state product contract remains one-shot greenfield generation plus generated-repo self-sufficiency. Audit and repair remain internal lifecycle and legacy recovery tools, not the ideal user-facing path.

## Purpose
Scafforge exists to generate a repo that weaker models can operate from start to finish with minimal user intervention. The generated repo should expose one clear legal next move at all times, obtain or generate the assets it needs, validate and repair its own work through tests and checks, and drive toward a compiled, working product.

This RFC defines the architecture changes required to make that goal realistic. It is not a Glitch-only fix. It is a package-wide re-architecture intended to stop recurring contradiction loops, repair churn, blocked-agent states, and split-authority drift at the source.

## Product Direction

### Desired end-state
The ideal Scafforge product flow is:

1. generate the repo once
2. hand the repo to the weaker model
3. let the generated repo workflow carry the model from planning through implementation, validation, and release proof
4. finish with a working compiled product and truthful closeout surfaces

In that ideal state, Scafforge audit and repair are not part of normal product use. They are development, support, and containment tools for package engineering and legacy recovery.

### Implication
This RFC does not optimize for keeping audit and repair as permanent first-class user workflows. It optimizes for making them unnecessary in the normal greenfield path. They still matter now, because they are the only safe containment surfaces while the package matures, but the architecture must bias toward greenfield self-sufficiency.

## Problem Statement

### User-visible failure
Scafforge can enter repeated loops of:

1. audit
2. package work
3. post-package audit
4. repair
5. blocked agent or contradictory restart state

The visible problem is not merely that Scafforge misses a bug. It is that Scafforge can publish a state that the next session immediately treats as ambiguous, contradictory, or blocked.

### Core architectural problem
Scafforge is not acting like one state machine. Workflow truth is re-derived in multiple places:
- audit classifies findings and routes ownership
- repair reclassifies findings and derives repair outcomes
- ticket follow-up scripts mutate the graph again
- repair-side scripts re-render restart surfaces and rewrite workflow state in parallel to the generated runtime workflow layer
- restart surfaces are regenerated from whatever state exists after those later mutations

Because those layers do not share one authority model or one invariant engine, Scafforge can repair one state, mutate into another, and publish a third.

### Why narrow fixes do not hold
Point fixes remove one contradiction family but do not remove the structural conditions that create new contradiction families later. A fresh post-package audit is not enough protection if the later repair or pivot phase can still synthesize a new invalid graph, stale restart guidance, or blocker classification.

## Goals
- Eliminate contradictory post-repair and post-pivot state publication.
- Ensure Scafforge exposes one legal next move after audit, repair, pivot, and resume.
- Make blocker semantics narrow and truthful.
- Make ticket graph, workflow, and restart-surface mutation atomic and canonical.
- Give pivot state one explicit owner and bounded write contract.
- Ensure repair cannot introduce new contradictions after verification.
- Convert recurring failures such as Glitch into durable convergence fixtures.
- Align package architecture with the end-state vision of one-shot greenfield generation and generated-repo self-sufficiency.

## Non-Goals
- Fix subject-repo product code inside package repair.
- Keep audit and repair permanently central to the ideal product workflow.
- Preserve duplicate mutation or classification paths for convenience.
- Support arbitrary host-specific workflow semantics inside the core contract.
- Rebuild the fixture program or package proof harness from scratch.
- Solve all weak-model implementation quality limitations by prompt tuning alone.

## Definitions

### Host
The machine or runtime environment executing Scafforge or the generated repo workflow. Examples include the developer machine, CI runner, remote VM, or IDE-integrated agent runtime.

### Toolchain
The real stack-specific executables, SDKs, compilers, package managers, and runtime dependencies required to prove execution for a stack. Examples include Godot, Android SDK, JDK, Gradle, Node, Cargo, Go, .NET SDK, and C or C++ compilers.

### Canonical mutation layer
The one authoritative layer allowed to mutate canonical repo workflow state. In this RFC, that means the generated repo runtime workflow layer, not secondary package-side scripts with separate graph logic.

### Disposition bundle
The structured diagnosis output that assigns every finding to one and only one ownership and follow-up class.

### Pivot state
The machine-readable pivot truth recorded in `.opencode/meta/pivot-state.json`, including pivot classification, stale-surface scope, downstream refresh obligations, ticket lineage execution state, and pivot-specific restart-surface inputs.

### Final-state publish gate
The rule that restart surfaces and repair or pivot outcome state may only be published from the exact post-mutation repo snapshot that has already passed invariant validation and final verification.

## Evidence and Context

### Observed failure pattern
The package has shown repeated cycles where:
- diagnosis correctly identifies package defects
- package work lands
- a fresh audit runs
- repair still republishes contradictory or misleading state

### Representative failure classes
- duplicated finding disposition between audit and repair
- duplicated ticket graph mutation between generated runtime tools and package-side Python follow-up logic
- large-scale duplication of restart rendering and workflow mutation between `workflow.ts`, `apply_repo_process_repair.py`, and `regenerate_restart_surfaces.py`
- pivot state and restart publication being written through separate script paths without one explicit truth-domain owner
- repair outcomes that overuse `managed_blocked`
- restart surfaces published before the exact post-mutation state is proven coherent
- validation that is stronger on generated file details than on workflow convergence

### Existing assets the re-architecture should preserve and extend
Scafforge already contains important seeds of the target architecture:

- The pivot skill already invokes generated runtime ticket tools through a Node subprocess adapter instead of reimplementing ticket mutation.
- The GPTTalker fixture program already contains curated families for repeated lifecycle contradiction, restart-surface drift, and split-scope reconciliation.
- The greenfield contract already requires VERIFY010 and VERIFY011 before `handoff-brief`, and `handoff_publish.ts` already publishes restart surfaces through the generated runtime workflow layer.

The re-architecture should generalize those assets rather than replacing them with a new parallel system.

### Representative package surfaces
- `skills/scafforge-audit/scripts/audit_repo_process.py`
- `skills/scafforge-audit/scripts/audit_reporting.py`
- `skills/scafforge-audit/scripts/audit_ticket_graph.py`
- `skills/scafforge-audit/scripts/audit_contract_surfaces.py`
- `skills/scafforge-audit/scripts/audit_lifecycle_contracts.py`
- `skills/scafforge-audit/scripts/audit_restart_surfaces.py`
- `skills/scafforge-audit/scripts/audit_repair_cycles.py`
- `skills/scafforge-audit/scripts/audit_execution_surfaces.py`
- `skills/scafforge-repair/scripts/run_managed_repair.py`
- `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
- `skills/scafforge-repair/scripts/regenerate_restart_surfaces.py`
- `skills/scafforge-repair/scripts/record_repair_stage_completion.py`
- `skills/scafforge-pivot/scripts/generated_tool_runtime.py`
- `skills/scafforge-pivot/scripts/apply_pivot_lineage.py`
- `skills/scafforge-pivot/scripts/plan_pivot.py`
- `skills/scafforge-pivot/scripts/publish_pivot_surfaces.py`
- `skills/scafforge-pivot/scripts/pivot_tracking.py`
- `skills/scafforge-pivot/scripts/record_pivot_stage_completion.py`
- `skills/ticket-pack-builder/scripts/apply_remediation_follow_up.py`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_create.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_reconcile.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`
- `scripts/smoke_test_scafforge.py`
- `scripts/integration_test_scafforge.py`
- `scripts/validate_scafforge_contract.py`
- `scripts/validate_gpttalker_migration.py`
- `scripts/test_support/scafforge_harness.py`
- `scripts/test_support/repo_seeders.py`
- `scripts/test_support/gpttalker_fixture_builders.py`
- `tests/fixtures/gpttalker/index.json`

## Current Architecture Failure Analysis

### 1. Split authority over finding disposition
Audit emits findings and routing intent, but repair still interprets ownership and outcome again. The same finding can therefore be treated as source follow-up in one phase and as a managed blocker in another.

### 2. Split authority over ticket and workflow mutation
The generated repo runtime already has canonical ticket tools and workflow helpers, but package-side repair and follow-up code can still mutate manifest semantics, workflow state, and publication inputs independently. That creates multiple writers for one truth surface.

### 3. Repair-side restart rendering is a large duplicate-authority seam
The largest current duplication seam is not only ticket follow-up. `apply_repo_process_repair.py` and `regenerate_restart_surfaces.py` each implement restart-surface rendering and workflow mutation logic in parallel to `workflow.ts`. That duplication is large enough to recreate stale restart truth even when ticket mutation is otherwise correct.

### 4. Pivot state is real workflow truth, but its ownership is under-specified
Pivot already demonstrates the right mutation pattern for ticket lineage by routing into generated runtime tools, but pivot tracking and pivot publication still write `.opencode/meta/pivot-state.json` directly through separate script paths. If pivot state feeds restart publication, it must be treated as a formal truth domain with one owner.

### 5. Non-transactional repair publication
Managed repair currently behaves like a sequence of partial phases rather than a closed transaction. It can refresh managed surfaces, mutate follow-up tickets, regenerate restart surfaces, and then publish repair state without proving that the final published repo state is coherent as a whole.

### 6. Overloaded blocker semantics
`managed_blocked` has been used as a broad fail state rather than a narrow managed-workflow or environment blocker. That freezes ordinary active-ticket lifecycle work even when the actual remaining work is only source follow-up, transcript follow-up, or truthful process verification.

### 7. Validation gap at the architecture level
The package has meaningful smoke and contract validation, and it already has curated fixture families, but too much of the proof contract still centers on exact strings, expected finding codes, or generated implementation details rather than convergence, publish safety, and repeated-cycle correctness.

### 8. Contract and implementation surfaces can drift independently
Authority changes are not safe if `AGENTS.md`, `skill-flow-manifest.json`, the competence contract, and generated/runtime behavior are allowed to change on different schedules. That creates the same contradiction class at the documentation layer that this RFC is trying to eliminate in code.

## Architectural Principles

### Principle 1: One authority per truth domain
Each truth domain must have one owner:
- diagnosis owns finding ownership and disposition
- generated runtime owns ticket, workflow, artifact, and restart-surface mutations
- pivot tracking owns pivot-state persistence
- final-state publish gate owns restart publication timing

### Principle 2: No re-derivation without explicit reconcile
If a later phase must disagree with an earlier classification or candidate state, that disagreement must be explicit, recorded, and validated. Silent reclassification is forbidden.

### Principle 3: Repair and pivot publication are transactions
Repair is not complete when deterministic refresh finishes. Repair is complete only when the exact candidate final state has passed invariant validation and final verification and is then published. The same principle applies to pivot publication once pivot changes have mutated canonical state.

### Principle 4: Greenfield is the product path
Audit and repair are containment and lifecycle tools. Greenfield one-shot generation remains the product path Scafforge is optimizing toward.

### Principle 5: Proof beats prose
Real failure families must become replayable fixtures. Architecture must be proven through execution, not preserved by documentation alone.

### Principle 6: Preserve and generalize working patterns already present
Where Scafforge already has the right pattern, such as pivot runtime tool invocation or curated fixture families, the package should generalize that asset instead of adding another competing layer.

## Target Architecture

### A. Authoritative disposition model
Diagnosis will emit a structured disposition bundle that classifies each finding into exactly one of these buckets:
- `managed_blocker`
- `manual_prerequisite_blocker`
- `source_follow_up`
- `process_state_only`
- `advisory`

Repair will consume that bundle directly. Repair will not infer ownership from finding-code prefixes or fallback heuristics.

### B. Canonical repo mutation layer
The canonical mutation layer will live in the generated repo runtime workflow implementation. That layer will own:
- ticket graph mutations
- workflow-state mutations
- artifact registration mutations
- derived restart-surface regeneration triggers
- runtime handoff publication through `handoff_publish.ts`

Package-side audit, repair, and pivot will not hand-edit canonical repo graph or restart semantics directly. They will either:
- invoke the canonical mutation layer through supported commands or adapters
- or use a shared mutation contract that reuses the exact same invariant engine and persistence semantics

The package will not maintain parallel Python and TypeScript repo mutation semantics as separate authorities.

### C. Repair-side renderer collapse
The first concrete collapse target inside the mutation re-architecture is repair-side restart rendering and raw workflow writes.

That means:
- `apply_repo_process_repair.py` must stop owning parallel `render_start_here`, `render_context_snapshot`, `refresh_restart_surfaces`, and direct workflow-state reconstruction as an independent truth source
- `regenerate_restart_surfaces.py` must stop being an independent restart renderer and become either a thin adapter or disappear behind the runtime mutation layer
- stage-completion scripts must not republish restart surfaces or rebuild follow-on state through private parallel semantics

### D. Package-side runtime adapter pattern
Scafforge already has a viable package-side bridge in `skills/scafforge-pivot/scripts/generated_tool_runtime.py`. That pattern will be generalized and reused for repair-side and ticket-follow-up mutations that must invoke generated runtime tools from package-side Python.

The package should not create a second independent Python mutation engine when an adapter into runtime tools is sufficient.

### E. Pivot-state truth domain
Pivot state is canonical for:
- pivot classification
- stale-surface maps
- downstream refresh routing
- ticket lineage action tracking
- pivot restart-surface inputs
- pivot publication tracking

Pivot state may be written by one bounded owner through `pivot_tracking.py` and associated orchestration surfaces. Any pivot operation that mutates tickets or workflow state must still route through the canonical repo mutation layer. Restart surfaces may read pivot state, but they may not synthesize or backfill it.

### F. Transactional managed repair
Managed repair will execute in the following order:

1. resolve repair basis
2. load authoritative disposition bundle
3. refresh managed surfaces
4. migrate legacy repo workflow contract if needed
5. apply follow-up mutations through the canonical mutation layer
6. validate all write-time invariants on the candidate final state
7. run final-state verification on that exact post-mutation snapshot
8. derive `repair_follow_on` outcome from disposition bundle plus final verification
9. publish restart surfaces from that verified final state only

If any step fails, repair fails closed and does not publish contradictory restart truth.

### G. Final-state publish gate
The following outputs may only be published from the verified final snapshot:
- `repair_follow_on`
- `START-HERE.md`
- `.opencode/state/context-snapshot.md`
- `.opencode/state/latest-handoff.md`
- any closeout-ready or continuation-ready restart narrative

The greenfield path already satisfies this rule through its verification sequence and `handoff_publish.ts`. This RFC formalizes that same gate for repair and pivot flows so the contract is uniform.

### H. Greenfield self-sufficiency bias
All architectural choices in this RFC must support the end-state where the generated repo is self-sufficient enough that a weaker model can:
- follow the workflows correctly
- obtain or generate required assets
- implement code
- run checks and tests
- detect failures
- repair failures within ticket scope
- finish with a compiled working product and truthful closeout state

This does not assume perfection today. It defines the direction the package architecture must support.

### I. Contract and proof alignment
The authority model, invariant catalog, flow manifest, and proof harness must evolve together. No code cutover is complete until the contract docs and harness assertions say the same thing as the implementation.

## Canonical Truth Ownership

### Canonical state
- `docs/spec/CANONICAL-BRIEF.md` owns durable project truth
- `tickets/manifest.json` owns machine queue and ticket graph state
- `.opencode/state/workflow-state.json` owns transient workflow, approval, lease, bootstrap, repair-follow-on, and process-version state
- `.opencode/state/artifacts/` and manifest-backed artifact metadata own stage proof
- `.opencode/meta/bootstrap-provenance.json` owns generation and migration provenance
- `.opencode/meta/pivot-state.json` owns pivot classification, stale-surface routing, downstream refresh obligations, ticket lineage action tracking, and pivot restart inputs

### Derived state
- `tickets/BOARD.md`
- `START-HERE.md`
- `.opencode/state/context-snapshot.md`
- `.opencode/state/latest-handoff.md`

Derived state is never authoritative. It is always a render from canonical state after canonical mutation succeeds.

## Required Invariants

### Finding-disposition invariants
1. Every diagnosis finding resolves to exactly one authoritative disposition class.
2. Repair may not silently reclassify a diagnosis finding into a different class.
3. `repair_follow_on` outcome is derived from the disposition bundle plus final-state verification only.

### Ticket-graph invariants
4. A ticket may not name the same parent in both `source_ticket_id` and `depends_on`.
5. Reverse follow-up linkage must be symmetric.
6. A `split_scope` child may not block on its open parent.
7. No circular `depends_on` graph may be published.
8. No ticket may end in an impossible combination of lifecycle, resolution, and verification state.

### Workflow and restart invariants
9. `manifest.active_ticket` and `workflow.active_ticket` must converge after every successful mutation.
10. Derived restart surfaces may only be generated from canonical manifest, workflow state, and pivot state.
11. No repair or pivot phase may publish restart surfaces before final-state verification of the candidate final snapshot.
12. Repair-side restart renderers may not remain independently authoritative after the mutation-layer cutover.

### Pivot-state invariants
13. Pivot state has one explicit persistence owner.
14. Pivot operations that mutate tickets or workflow state must route through canonical runtime tools or a shared adapter that reuses the runtime invariant contract.
15. Restart surfaces may consume pivot state but may not synthesize pivot truth on behalf of pivot tracking.

### Outcome-semantics invariants
16. `managed_blocked` may only represent true managed-workflow or environment blockers.
17. `source_follow_up` may not block ordinary active-ticket lifecycle execution by itself.
18. Truthful `pending_process_verification` may not be escalated to `managed_blocked` by itself.

### Product-direction invariants
19. Greenfield remains the primary user path.
20. Audit and repair remain non-primary lifecycle tools and may not be required for normal greenfield success.
21. The package must bias toward generated-repo self-sufficiency rather than host-side rescue dependence.

### Contract-alignment invariants
22. `AGENTS.md`, `skill-flow-manifest.json`, and the package contract references must agree on authority ownership and publish-gate behavior.
23. The greenfield contract may not be accidentally strengthened into a redundant second gate when repair and pivot publish gating are tightened.

### Validation invariants
24. Every recurring loop class must have a replayable regression fixture.
25. End-to-end repair tests must assert convergence and publish safety, not only exact strings.
26. Tier 1 stacks must have real execution proof coverage on release proof hosts.
27. Existing curated fixture families must be preserved and upgraded rather than discarded.

## Resolved Architecture Decisions

### Decision 1: Canonical mutation layer location
The canonical mutation layer will live in generated repo runtime code.

Rationale:
- generated repos must eventually be self-sufficient
- runtime ticket and workflow semantics already belong to generated repo lifecycle surfaces
- keeping mutation authority in the generated runtime avoids reintroducing a package-side parallel writer
- package-side repair and pivot can still operate through adapters or controlled invocation of that same mutation authority

Implication:
Package-side repair code must stop directly inventing or maintaining separate ticket, workflow, and restart-surface semantics.

### Decision 2: Repair-side restart duplication priority
The first major collapse target under the mutation re-architecture is repair-side restart rendering and raw workflow mutation.

Rationale:
- it is the largest current split-authority seam
- it directly affects the truthfulness of restart guidance
- it can recreate stale state even when ticket mutation is correct

Implication:
`apply_repo_process_repair.py` and `regenerate_restart_surfaces.py` are not supporting cleanup. They are primary implementation targets.

### Decision 3: Pivot adapter generalization
The existing pivot runtime-adapter pattern becomes the model for package-side runtime invocation.

Rationale:
- it already proves the package can drive generated runtime tools without duplicating ticket semantics
- it is a better base than inventing another Python-side workflow engine

Implication:
Repair-side and ticket-follow-up mutations should adopt the same adapter strategy where package-side orchestration is still required.

### Decision 4: Pivot-state ownership
Pivot state is a canonical truth domain with one explicit owner.

Policy:
- `pivot_tracking.py` and bounded pivot orchestration surfaces own pivot-state persistence
- pivot-state writers may not invent ticket or workflow semantics outside the canonical runtime mutation layer
- restart surfaces may read pivot state, but they may not repair or synthesize pivot truth on its behalf

Implication:
Pivot state is no longer an implicit sidecar. It is part of the authority map.

### Decision 5: Legacy repo upgrade policy
Repair will upgrade legacy repos through an explicit migration stage before ordinary follow-up mutation occurs.

Policy:
- recent legacy repos are auto-migrated in place to the new workflow contract
- a short-lived compatibility shim may exist during migration rollout, but it is package-internal only
- very old or structurally inconsistent repos may fail closed with an explicit migration escalation instead of receiving unsafe silent mutation

Implication:
Repair still fixes legacy repos, but only through a defined migration policy rather than through indefinite compatibility drift.

### Decision 6: Tier 1 execution proof policy
For package development and release, Tier 1 execution proofs are mandatory on full-toolchain proof hosts.

Policy:
- Scafforge’s package proof environment must include the full Tier 1 toolchain set used by the solo developer and release gate
- release acceptance may not rely on detection-only or best-effort-only validation for Tier 1 stacks
- on other hosts lacking a given toolchain, generated repos must fail truthfully and report the missing prerequisite rather than pretending the proof passed

Implication:
Package quality is gated by real runnable or buildable proof on full-toolchain hosts, while generated repos still degrade truthfully on hosts missing tools.

### Decision 7: Shadow validation policy
Shadow validation is an internal package-migration technique only.

Policy:
- shadow validation will run inside package development, local live-testing, and proof harnesses during migration
- generated repos and end users will not be asked to run extra Scafforge passes as part of the intended product experience
- once the new architecture is proven, legacy paths are removed rather than preserved indefinitely

Implication:
Shadow validation does not become part of the product contract. It is a temporary package-engineering safety rail.

### Decision 8: Proof-harness evolution policy
The existing fixture and harness program will be extended, not replaced.

Policy:
- preserve current GPTTalker fixture families and harness utilities
- evolve them from expected-finding and coverage assertions into convergence, publish-safety, and transactional assertions
- treat harness builders and seeders as first-class delivery surfaces for proof work

Implication:
Phase 6 means upgrading the existing proof program, not reinventing it.

### Decision 9: Contract and documentation alignment policy
Authority and invariant changes must land together with contract and flow-manifest updates.

Policy:
- `AGENTS.md` must reflect the authority map and publish-gate semantics
- `skills/skill-flow-manifest.json` must reflect downstream ownership, required outputs, and flow behavior
- `references/competence-contract.md` must reflect tightened blocker semantics and truth-domain ownership
- `references/one-shot-generation-contract.md` must be verified so repair and pivot changes do not silently distort greenfield guarantees

Implication:
No code cutover is accepted if the package contract surfaces still describe the old authority model.

### Decision 10: Audit and repair product role
Audit and repair remain supported, but they are no longer treated as the target user workflow for a mature Scafforge release.

Policy:
- greenfield one-shot generation is the intended user path
- audit and repair exist for package engineering, support, legacy recovery, retrofit, and controlled diagnosis
- the package architecture must steadily reduce dependence on audit and repair for normal greenfield success

## Workstreams

### Workstream A: Authoritative disposition bundle and diagnosis routing
Deliver a structured diagnosis output that repair consumes directly and align repair-cycle diagnosis with the new ownership model.

Primary surfaces:
- `skills/scafforge-audit/scripts/audit_reporting.py`
- `skills/scafforge-audit/scripts/audit_repo_process.py`
- `skills/scafforge-audit/scripts/audit_repair_cycles.py`
- `skills/scafforge-repair/scripts/run_managed_repair.py`

### Workstream B: Canonical repo mutation layer and repair-side renderer collapse
Collapse ticket, workflow, artifact, and restart mutation into one canonical path and remove repair-side duplicate restart authority.

Primary surfaces:
- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_create.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_reconcile.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`
- `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
- `skills/scafforge-repair/scripts/regenerate_restart_surfaces.py`
- `skills/ticket-pack-builder/scripts/apply_remediation_follow_up.py`

### Workstream C: Pivot-state truth ownership and runtime adapter generalization
Assign one owner to pivot state and generalize the existing pivot runtime-adapter pattern for package-side runtime mutations.

Primary surfaces:
- `skills/scafforge-pivot/scripts/generated_tool_runtime.py`
- `skills/scafforge-pivot/scripts/apply_pivot_lineage.py`
- `skills/scafforge-pivot/scripts/plan_pivot.py`
- `skills/scafforge-pivot/scripts/publish_pivot_surfaces.py`
- `skills/scafforge-pivot/scripts/pivot_tracking.py`
- `skills/scafforge-pivot/scripts/record_pivot_stage_completion.py`

### Workstream D: Transactional repair and publish-gate orchestration
Make repair and pivot publication emit only one verified final state and align stage-completion scripts with that transaction model.

Primary surfaces:
- `skills/scafforge-repair/scripts/run_managed_repair.py`
- `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
- `skills/scafforge-repair/scripts/regenerate_restart_surfaces.py`
- `skills/scafforge-repair/scripts/record_repair_stage_completion.py`
- `skills/scafforge-pivot/scripts/publish_pivot_surfaces.py`
- `skills/scafforge-pivot/scripts/record_pivot_stage_completion.py`

### Workstream E: Write-time invariant enforcement and audit alignment
Move critical graph, lifecycle, restart, churn, and execution checks from audit-only expectations into mutation-time enforcement and aligned audit verification.

Primary surfaces:
- `skills/scafforge-audit/scripts/audit_ticket_graph.py`
- `skills/scafforge-audit/scripts/audit_contract_surfaces.py`
- `skills/scafforge-audit/scripts/audit_lifecycle_contracts.py`
- `skills/scafforge-audit/scripts/audit_restart_surfaces.py`
- `skills/scafforge-audit/scripts/audit_repair_cycles.py`
- `skills/scafforge-audit/scripts/audit_execution_surfaces.py`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`

### Workstream F: Contract and documentation alignment
Make package contract surfaces reflect the new ownership map, publish gate, and blocker semantics.

Primary surfaces:
- `AGENTS.md`
- `skills/skill-flow-manifest.json`
- `references/competence-contract.md`
- `references/one-shot-generation-contract.md`
- `references/stack-adapter-contract.md`

### Workstream G: Existing proof harness evolution and self-sufficiency program
Extend the current fixture and harness program into convergence, publish-safety, transactional, and self-sufficiency proof.

Primary surfaces:
- `scripts/smoke_test_scafforge.py`
- `scripts/integration_test_scafforge.py`
- `scripts/validate_scafforge_contract.py`
- `scripts/validate_gpttalker_migration.py`
- `scripts/test_support/scafforge_harness.py`
- `scripts/test_support/repo_seeders.py`
- `scripts/test_support/gpttalker_fixture_builders.py`
- `tests/fixtures/gpttalker/index.json`

## Implementation Plan

### Phase 0: Freeze authority, truth domains, and contract alignment
Objective:
Define the sole owner for finding disposition, ticket mutation, workflow mutation, pivot-state mutation, restart publication, and repair outcome derivation.

Deliverables:
- authority ownership ADR
- invariant catalog adopted into package docs and proof targets
- explicit truth-domain inventory including pivot state
- aligned updates to `AGENTS.md`, `skill-flow-manifest.json`, and the competence contract
- verification that the one-shot generation contract does not need an extra greenfield publish gate

Exit gate:
- no new repair, pivot, or ticket-graph features land without mapping to this authority model

### Phase 1: Introduce authoritative diagnosis disposition
Objective:
Make audit authoritative for ownership and routing.

Deliverables:
- disposition schema
- diagnosis pack extended with disposition bundle
- repair consuming bundle in shadow mode during package development only
- audit-cycle and audit-report surfaces aligned to the new disposition model

Exit gate:
- repair can compare legacy classification to diagnosis classification and surface deltas without yet using the new path for publication

### Phase 2: Build and adopt the canonical mutation layer
Objective:
Collapse ticket, workflow, artifact, and restart mutation into one path and generalize the runtime adapter pattern.

Deliverables:
- canonical mutation interface in generated runtime
- shared package-side adapter pattern derived from pivot runtime invocation
- repair-side restart rendering and raw workflow writes collapsed behind the runtime mutation contract
- ticket follow-up creation routed through the same canonical mutation path
- explicit pivot-state owner and bounded pivot-state write contract

Exit gate:
- split-scope, process-verification, reconcile, restart, and package-side runtime invocation all use the same invariant checks and persistence semantics

### Phase 3: Convert managed repair into a transaction
Objective:
Ensure repair verifies and publishes one coherent final state only, and align stage-completion scripts with that model.

Deliverables:
- staged repair transaction model
- candidate-state invariant validation before publication
- final-state verification gate before any restart publication
- `record_repair_stage_completion.py` aligned to the repair transaction instead of acting as a free-standing secondary publication path
- pivot publication surfaces aligned to the same publish-gate principle

Exit gate:
- repair cannot publish `repair_follow_on` or restart surfaces from intermediate state

### Phase 4: Migrate legacy repos through explicit contract upgrade
Objective:
Make repair responsible for safe legacy contract upgrade before normal mutation.

Deliverables:
- legacy migration stage
- bounded compatibility shim for package-internal migration only
- explicit escalation path for unsafe or too-old repos
- migration coverage for legacy restart and pivot-state surfaces where applicable

Exit gate:
- recent legacy repos can be upgraded automatically into the new mutation contract

### Phase 5: Narrow blocker semantics and cut over authority
Objective:
Make blocker semantics truthful and stable.

Deliverables:
- `managed_blocked` restricted to managed-workflow and environment blockers
- source and transcript follow-up routed through non-blocking classes when appropriate
- repair outcome derived entirely from disposition bundle plus final verification
- audit and restart surfaces aligned to the tighter blocker model

Exit gate:
- fixtures with only source follow-up or transcript follow-up no longer freeze ordinary lifecycle execution

### Phase 6: Extend the existing proof program and remove legacy paths
Objective:
Replace brittle validation with convergence proofs and remove duplicate-authority paths.

Deliverables:
- existing GPTTalker fixture families upgraded from expected-finding and expected-coverage checks into convergence, publish-safety, and transactional assertions
- repeated-cycle fixtures
- split-scope contradiction fixtures
- publish-safety fixtures
- weak-model self-sufficiency fixtures
- full Tier 1 execution proof fixtures on full-toolchain hosts
- legacy duplicate-authority paths removed or hard-disabled

Exit gate:
- package validation demonstrates convergence across representative loop families and greenfield proof families rather than only one-pass generated-surface success

## Validation and Proof Program

### A. Mandatory release-gate proof suites
The following suites are mandatory for package development and release sign-off:
- contract validation
- smoke cycle validation
- repeated diagnosis and repair churn fixtures
- split-scope graph consistency fixtures
- restart publish safety fixtures
- legacy migration fixtures
- weak-model continuation fixtures
- Tier 1 real execution proof fixtures on full-toolchain hosts

### B. Existing fixture and harness evolution
Scafforge already has an active fixture and harness layer. The proof program will build on that layer rather than replacing it.

That means:
- retain the existing GPTTalker fixture families in `tests/fixtures/gpttalker/index.json`
- retain the harness and seeding utilities in `scripts/test_support/`
- evolve fixture contracts from `expected_finding_codes` and `expected_coverage` toward convergence, publish-safety, transactional, and blocker-truth assertions
- add new seeders and fixture builders only where new invariants require them

### C. Tier 1 execution proof policy
Tier 1 stacks must have real execution proof on release proof hosts. Detection-only validation is not sufficient for package release.

Tier 1 proof hosts must cover:
- Python
- Node
- Rust
- Go
- Godot
- Java or Android
- C or C++
- .NET

Generated repos on hosts that lack one or more toolchains must:
- detect the missing prerequisite truthfully
- persist blocker state truthfully
- stop unsafe continuation truthfully

They must not claim that the proof passed on a host that could not run it.

### D. Greenfield self-sufficiency proof families
The package proof program must increasingly validate that the generated repo can carry a weaker model through:
- canonical workflow following
- asset acquisition or generation
- implementation
- testing and checks
- self-correction within scope
- compiled or release-proof output

This remains a progressive program, but it is now an explicit package objective rather than an informal aspiration.

## Acceptance Criteria

### Architecture acceptance
1. Audit emits one authoritative disposition bundle that repair consumes directly.
2. Package-side repair no longer contains an independent finding ownership model that can disagree with diagnosis.
3. Ticket, workflow, artifact, and restart mutation occur through one canonical mutation layer with one invariant engine.
4. Repair-side restart renderers are no longer independently authoritative after cutover.
5. Pivot state has one explicit owner and pivot ticket lineage continues to route through generated runtime tools.
6. Restart publication happens only after the exact post-mutation repo state has passed final-state verification.
7. Legacy repos can be upgraded through explicit migration rather than indefinite compatibility drift.
8. Package contract surfaces and the flow manifest are aligned with the shipped authority model.

### Behavioral acceptance
9. A repo with only source follow-up or transcript follow-up remaining ends in `source_follow_up`, not `managed_blocked`.
10. A repo with an actual managed-workflow defect or environment blocker ends in `managed_blocked` with a truthful blocker reason.
11. A split-scope child cannot be published with its open parent duplicated in `depends_on`.
12. A repair or pivot run cannot publish `START-HERE.md`, `context-snapshot`, or `latest-handoff` that disagrees with canonical state.
13. A fresh post-package audit followed by one repair run is sufficient for unchanged fixture families unless an explicit escalation condition is present.
14. The greenfield path continues to satisfy publish-gate requirements through the existing VERIFY010, VERIFY011, and `handoff_publish.ts` sequence without requiring a redundant second pass.
15. Greenfield remains the intended product path rather than audit-first or repair-first lifecycle dependence.

### Validation acceptance
16. The proof harness includes a replay of the recurring loop family: audit -> package fix -> post-package audit -> repair -> resume.
17. The proof harness includes split-scope parent and child contradiction fixtures.
18. The proof harness includes restart-surface drift fixtures and repeated-cycle churn fixtures that fail unless the package truly converges.
19. Existing GPTTalker fixture families are preserved and upgraded rather than replaced.
20. Harness and seeding layers in `scripts/test_support/` are used as delivery surfaces for the convergence program.
21. Tier 1 stack coverage verifies actual runnable or buildable behavior on full-toolchain proof hosts.
22. Validation asserts invariants and convergence outcomes, not only exact generated strings or exact finding lists.
23. Weak-model continuation fixtures demonstrate that generated repos expose one legal next move and truthful blockers without relying on user memory.

### Product-direction acceptance
24. The package architecture no longer assumes audit and repair as normal greenfield user dependencies.
25. The generated repo moves closer to start-to-finish self-sufficiency for weaker models.
26. No new feature may reintroduce split authority over classification, repo mutation, restart publication, or pivot-state ownership.

## Risks and Tradeoffs
- Building a single canonical mutation layer increases near-term refactor cost.
- Moving invariants to write time will surface more explicit failures at first.
- Tightening blocker semantics may expose existing prompt or restart-surface assumptions.
- Full Tier 1 proof coverage raises package maintenance cost because proof hosts must carry real toolchains.
- Legacy migration adds temporary complexity, but that complexity is bounded and preferable to indefinite dual-authority support.
- Treating pivot state as a formal truth domain increases explicit orchestration overhead, but it is preferable to leaving pivot publication behavior implicit.

## Mitigations
- Keep migration compatibility strictly bounded and internal.
- Use shadow validation only in package development until canonical behavior is proven.
- Treat real-world repos such as Glitch as fixture families, not ad hoc exceptions.
- Use acceptance gates that prove end-state convergence before deleting legacy paths.
- Reuse the existing pivot adapter pattern and existing fixture harness so the re-architecture does not create unnecessary new infrastructure.

## Rollout Policy
The rollout policy is:
- use shadow validation only during package migration
- cut over to canonical disposition and mutation once proof fixtures and live-test repos stabilize
- remove legacy classification and mutation paths rather than preserving them indefinitely
- retain audit and repair as lifecycle and support tools, while continuing to push greenfield one-shot generation toward the primary user contract
- land contract and flow-manifest updates with the same changeset family as authority cutovers, not later

## Final Resolutions
No architectural open questions remain at the RFC level.

Implementation detail choices may still vary as long as they preserve the decisions, invariants, migration policy, proof requirements, and acceptance criteria defined in this RFC.

## Appendix: Primary Affected Surfaces
- `AGENTS.md`
- `skills/skill-flow-manifest.json`
- `references/competence-contract.md`
- `references/one-shot-generation-contract.md`
- `references/stack-adapter-contract.md`
- `skills/scafforge-audit/scripts/audit_repo_process.py`
- `skills/scafforge-audit/scripts/audit_reporting.py`
- `skills/scafforge-audit/scripts/audit_ticket_graph.py`
- `skills/scafforge-audit/scripts/audit_contract_surfaces.py`
- `skills/scafforge-audit/scripts/audit_lifecycle_contracts.py`
- `skills/scafforge-audit/scripts/audit_restart_surfaces.py`
- `skills/scafforge-audit/scripts/audit_repair_cycles.py`
- `skills/scafforge-audit/scripts/audit_execution_surfaces.py`
- `skills/scafforge-repair/scripts/run_managed_repair.py`
- `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
- `skills/scafforge-repair/scripts/regenerate_restart_surfaces.py`
- `skills/scafforge-repair/scripts/record_repair_stage_completion.py`
- `skills/scafforge-pivot/scripts/generated_tool_runtime.py`
- `skills/scafforge-pivot/scripts/apply_pivot_lineage.py`
- `skills/scafforge-pivot/scripts/plan_pivot.py`
- `skills/scafforge-pivot/scripts/publish_pivot_surfaces.py`
- `skills/scafforge-pivot/scripts/pivot_tracking.py`
- `skills/scafforge-pivot/scripts/record_pivot_stage_completion.py`
- `skills/ticket-pack-builder/scripts/apply_remediation_follow_up.py`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_create.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_reconcile.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`
- `scripts/smoke_test_scafforge.py`
- `scripts/integration_test_scafforge.py`
- `scripts/validate_scafforge_contract.py`
- `scripts/validate_gpttalker_migration.py`
- `scripts/test_support/scafforge_harness.py`
- `scripts/test_support/repo_seeders.py`
- `scripts/test_support/gpttalker_fixture_builders.py`
- `tests/fixtures/gpttalker/index.json`
