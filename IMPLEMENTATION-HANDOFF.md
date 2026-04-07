# Implementation Handoff

This document is the historical execution contract for the completed implementation sequence and the reviewer.

Current state:
- package backlog cleanup is complete
- package-root generated-repo runtime state has been removed
- `SETUP-001`, `ARCH-001`, `ARCH-002`, `STACK-001`, `DIAG-001`, `DIAG-002`, `MUT-001`, `MUT-002`, `PIVOT-001`, `REPAIR-001`, `RESTART-001`, `RESTART-002`, `INV-001`, `INV-002`, `AUDIT-001`, `BLOCK-001`, and `CYCLE-001` are complete
  - the `PR-06` bundle is complete, the `PR-07` bundle is complete, the `PR-08` bundle is complete, the `PR-09` bundle is complete, the `PR-10` bundle is complete, the `PR-11` bundle is complete, and this handoff is retained as historical context for the shipped package state

## Non-Negotiable Rules

1. Treat the package-vs-generated-repo boundary as law. No package-root `.opencode/` runtime state may be introduced.
2. Use the ticket markdown as the implementation source of truth. `tickets/manifest.json` and `tickets/BOARD.md` are trackers only.
3. If generated-repo behavior changes, edit package sources or template assets under `skills/repo-scaffold-factory/assets/project-template/` rather than simulating generated state in the package root.
4. Keep PR scope aligned to the listed ticket bundle. Do not mix unrelated cleanup, opportunistic refactors, or speculative future work into an implementation PR.
5. Update touched ticket files, `tickets/manifest.json`, and `tickets/BOARD.md` in the same PR when a ticket meaningfully changes state.
6. Use `python3` or `sys.executable` for Python commands in this repo.
7. Preserve existing proof assets and fixture families unless the ticket explicitly changes their contract.

## Branch And PR Rules

- Base branch: `main`
- Remote: `origin`
- Branch naming: `impl/NN-short-scope`
- PR title format: `impl(NN): short scope summary`
- One PR per bundle below
- Rebase or merge from current `main` before opening a review request
- Each PR description must include:
  - ticket ids covered
  - concise scope summary
  - primary files or surfaces changed
  - validations run
  - known residual risk, if any

## PR Sequence

### PR-00

- Branch: already completed on `main`
- Scope: package backlog cleanup, package-boundary reset, root `AGENTS.md` revamp, and implementation handoff creation
- Tickets: `SETUP-001` complete

### PR-01

- Branch: `impl/01-authority-contract`
- Tickets: `ARCH-001`, `ARCH-002`, `STACK-001`
- Scope:
  - authority ADR
  - invariant catalog
  - flow-manifest alignment baseline
  - Tier 1 proof-host matrix and release-proof command contract
- Minimum validation:
  - `npm run validate:contract`

### PR-02

- Branch: `impl/02-diagnosis-disposition`
- Tickets: `DIAG-001`, `DIAG-002`
- Scope:
  - disposition bundle schema
  - diagnosis-pack output integration
  - repair-side shadow-mode consumption and delta reporting
- Minimum validation:
  - `npm run validate:smoke`
  - targeted diagnosis-pack or repair-path coverage touched by the PR

### PR-03

- Branch: `impl/03-runtime-restart-core`
- Tickets: `MUT-001`, `PIVOT-001`, `RESTART-001`, `INV-001`
- Scope:
  - shared runtime adapter baseline
  - pivot-state ownership baseline
  - canonical restart-derivation contract
  - write-time invariant enforcement in runtime mutation code
- Minimum validation:
  - `npm run validate:smoke`
  - `python3 scripts/integration_test_scafforge.py`

### PR-04

- Branch: `impl/04-shadow-writer-cutover`
- Tickets: `MUT-002`, `REPAIR-001`, `RESTART-002`, `INV-002`
- Scope:
  - route package-side ticket mutation through runtime-owned paths
  - remove repair-side workflow reconstruction
  - retire independent restart rendering
  - extend invariant enforcement to adapter and pivot paths
- Minimum validation:
  - `npm run validate:smoke`
  - `python3 scripts/integration_test_scafforge.py`

### PR-05

- Branch: `impl/05-transactional-publication`
- Tickets: `REPAIR-002`, `PIVOT-002`, `STAGE-001`
- Scope:
  - transactional repair orchestration
  - pivot publish-gate alignment
  - removal of hidden stage-completion publication paths
- Minimum validation:
  - `npm run validate:smoke`
  - transaction-focused integration coverage touched by the PR

### PR-06

- Branch: `impl/06-audit-blockers-cycles`
- Tickets: `AUDIT-001`, `BLOCK-001`, `CYCLE-001`
- Scope:
  - audit alignment to the new runtime contract
  - narrowed blocker semantics
  - convergence-aware repair-cycle auditing
- Minimum validation:
  - `npm run validate:contract`
  - `npm run validate:smoke`
  - `python3 scripts/integration_test_scafforge.py`

### PR-07

- Branch: `impl/07-legacy-migration`
- Tickets: `LEG-001`, `LEG-002`
- Scope:
  - explicit migration stage
  - migration provenance
  - legacy upgrade proof and escalation handling
- Minimum validation:
  - `npm run validate:smoke`
  - `python3 scripts/validate_gpttalker_migration.py`

### PR-08

- Branch: `impl/08-proof-harness`
- Tickets: `PROOF-001`, `PROOF-002`
- Scope:
  - upgrade existing GPTTalker fixture contracts
  - extend harness and seeders for stale-state edge cases
- Minimum validation:
  - `npm run validate:smoke`
  - `python3 scripts/integration_test_scafforge.py`

### PR-09

- Branch: `impl/09-tier1-contract-validation`
- Tickets: `STACK-002`, `CONTRACT-001`
- Scope:
  - Tier 1 full-toolchain proof coverage
  - validator enforcement of the new architecture
- Minimum validation:
  - `npm run validate:contract`
  - `npm run validate:smoke`
  - `python3 scripts/integration_test_scafforge.py`
  - proof-host checks for the stacks touched in the PR

### PR-10

- Branch: `impl/10-greenfield-self-sufficiency`
- Tickets: `GREEN-001`
- Scope:
  - weak-model greenfield self-sufficiency proof
  - confirmation that greenfield remains one-shot and not repair-first
- Minimum validation:
  - `npm run validate:contract`
  - `npm run validate:smoke`
  - targeted greenfield proof coverage touched by the PR

### PR-11

- Branch: `impl/11-post-implementation-doc-sync`
- Tickets: `DOCS-001`
- Scope:
  - final rewrite of root `AGENTS.md`, `README.md`, contract references, skill docs, and other authoritative markdowns to match the shipped implementation
- Minimum validation:
  - `npm run validate:contract`

## Global Reviewer Checklist

Review every PR for these recurring Scafforge failure modes:

### Package-vs-output boundary

- No package-root generated-repo runtime state was added.
- Any `.opencode/` changes are either template assets or live-test or fixture data, not package-root state.
- Package planning still lives in `tickets/` as tracker plus self-contained ticket markdown.

### Authority and mutation ownership

- No second package-side mutation engine was introduced.
- Diagnosis remains the owner of disposition.
- Runtime-owned mutation paths remain the canonical writers for generated queue or restart behavior.
- Pivot-state ownership stays single-writer and explicit.

### Restart and publication safety

- Restart surfaces derive from the canonical contract, not private recomputation.
- Repair and pivot publication happen only after candidate-state validation and final verification.
- Stage-completion helpers do not publish restart truth or final outcomes independently.

### Blocker and follow-up semantics

- `managed_blocked` is not widened beyond managed-workflow or environment blockers.
- `source_follow_up`, transcript-only follow-up, and pending process verification are not silently escalated into blockers.
- Split-scope and follow-up linkage stay coherent and non-contradictory.

### Audit and proof discipline

- Audit changes reflect the new contract instead of merely preserving old findings.
- Validators and fixtures are updated when behavior changes.
- Existing GPTTalker or harness coverage is preserved unless the ticket explicitly redefines its contract.
- Contract-validator string additions are backed by real behavior, not cosmetic patches alone.

### Standard repo hygiene

- Python invocations use `python3` or `sys.executable`.
- No unrelated reformatting or drive-by cleanup was mixed into the PR.
- Ticket, manifest, and board updates match the actual work completed.
- Validation commands listed in the PR description are actually relevant to the touched surfaces.

## PR-Specific Reviewer Focus

### PR-01

- The authority ADR, invariant catalog, flow manifest, and proof-host matrix all describe the same owner map.
- The new docs do not accidentally describe package-root generated-repo state as part of the package repo.

### PR-02

- Every finding gets exactly one disposition class.
- Repair reads the disposition bundle instead of reclassifying by prefix.
- Shadow-mode reporting makes deltas explicit rather than hiding them.

### PR-03

- The shared runtime bridge does not become a second mutation engine.
- The restart contract covers `START-HERE.md`, `context-snapshot.md`, and `latest-handoff.md` together.
- `workflow.ts` write-time invariants reject contradictory graph or lifecycle states.

### PR-04

- Direct package-side ticket or restart writers are actually removed from the covered surfaces.
- Adapter and pivot paths hit the same invariant checks as direct runtime tool calls.
- Repair-side workflow reconstruction is gone rather than merely wrapped.

### PR-05

- Transaction stages are explicit and fail closed.
- Pivot publication obeys the same final-state gate as repair.
- Stage-completion helpers have no hidden publication side effects left.

### PR-06

- Audit validates the new runtime contract rather than stale assumptions.
- Blocker semantics are narrow and mechanically enforced.
- Cycle detection measures non-convergence, not just repeated string output.

### PR-07

- Migration is explicit, bounded, and provenance-backed.
- Unsafe legacy repos fail closed with escalation.
- Migration validation covers post-migration restart and repair behavior.

### PR-08

- Existing GPTTalker fixture families are preserved.
- New stale-state and interrupted-flow fixtures are reusable across validators.
- The harness did not regress into happy-path-only coverage.

### PR-09

- Tier 1 proof is real runnable or buildable evidence on proof hosts, not detection-only success.
- Validation scripts fail when hidden writers or contract drift reappear.
- Non-proof hosts degrade truthfully.

### PR-10

- Greenfield stays one-shot and immediately continuable.
- Repair is not smuggled back in as a default greenfield dependency.
- Proof cases demonstrate one legal next move and truthful blockers.

### PR-11

- Root `AGENTS.md`, `README.md`, contract references, and skill docs match the shipped implementation rather than planned work.
- Legacy wording, temporary migration notes, and stale assumptions are removed or clearly marked.

## If A PR Proves Too Large

Split it only inside its assigned workstream.

Allowed example:
- split `impl/04-shadow-writer-cutover` into `impl/04a-ticket-mutation` and `impl/04b-restart-renderer-cutover`

Not allowed example:
- pulling `BLOCK-001` or `DOCS-001` forward into a mutation PR for convenience

If a bundle is split, update this handoff document in the same branch so the reviewer can follow the actual sequence.
