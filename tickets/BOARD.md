# Ticket Board

Package backlog only. This board is a tracker, not runtime workflow state.

Current focus: `DIAG-001`

| Wave | ID | Title | Lane | Stage | Status | Resolution | Verification | Parallel Safe | Overlap Risk | Depends On | Follow-ups |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | SETUP-001 | Establish package-local execution baseline and affected-surface inventory | repo-foundation | complete | done | completed | verified | no | high | - | - |
| 0 | ARCH-001 | Publish authority ADR and canonical truth-domain inventory | authority-contract | complete | done | completed | verified | no | high | SETUP-001 | - |
| 0 | ARCH-002 | Align package contract docs and flow manifest to the authority baseline | contract-alignment | complete | done | completed | verified | no | medium | ARCH-001 | - |
| 0 | STACK-001 | Define Tier 1 proof-host matrix and release-gate command contract | release-proof | complete | done | completed | verified | yes | low | SETUP-001 | - |
| 1 | DIAG-001 | Emit the authoritative disposition bundle from audit outputs | audit-disposition | planning | todo | open | suspect | no | medium | ARCH-001 | - |
| 1 | MUT-001 | Generalize the pivot runtime adapter into the package-wide runtime bridge | runtime-adapter | planning | todo | open | suspect | yes | medium | ARCH-001 | - |
| 1 | PIVOT-001 | Formalize pivot-state ownership and bounded persistence rules | pivot-state | planning | todo | open | suspect | yes | medium | ARCH-001 | - |
| 1 | RESTART-001 | Implement the runtime-backed restart derivation contract | restart-surfaces | planning | todo | open | suspect | no | high | ARCH-001, MUT-001 | - |
| 1 | INV-001 | Enforce graph and lifecycle invariants at write time in workflow.ts | mutation-invariants | planning | todo | open | suspect | no | high | ARCH-001, RESTART-001 | - |
| 2 | DIAG-002 | Consume the disposition bundle in repair and surface reclassification deltas | repair-disposition | planning | todo | open | suspect | no | medium | DIAG-001 | - |
| 2 | MUT-002 | Route package-side ticket mutations through canonical runtime tools | ticket-mutation | planning | todo | open | suspect | yes | medium | MUT-001, PIVOT-001 | - |
| 2 | REPAIR-001 | Remove raw workflow-state reconstruction from apply_repo_process_repair | repair-engine | planning | todo | open | suspect | no | high | MUT-001, RESTART-001 | - |
| 2 | RESTART-002 | Retire regenerate_restart_surfaces as an independent renderer | restart-surfaces | planning | todo | open | suspect | no | high | REPAIR-001, RESTART-001 | - |
| 2 | INV-002 | Extend stage-gate and pivot-state enforcement to the new invariant contract | mutation-invariants | planning | todo | open | suspect | yes | medium | INV-001, PIVOT-001, MUT-001 | - |
| 2 | AUDIT-001 | Align audit modules to the runtime invariant and restart contract | audit-contract | planning | todo | open | suspect | yes | medium | INV-001, INV-002, RESTART-002 | - |
| 3 | REPAIR-002 | Convert run_managed_repair into a staged transaction | repair-engine | planning | todo | open | suspect | no | high | DIAG-002, REPAIR-001, RESTART-002, INV-001 | - |
| 3 | PIVOT-002 | Align pivot publication with the final-state publish gate | pivot-orchestration | planning | todo | open | suspect | yes | medium | PIVOT-001, RESTART-001, REPAIR-002 | - |
| 3 | STAGE-001 | Align stage-completion scripts to transaction-owned state updates | stage-tracking | planning | todo | open | suspect | yes | low | REPAIR-002, PIVOT-002 | - |
| 3 | BLOCK-001 | Narrow blocker semantics across audit, repair, and restart surfaces | blocker-semantics | planning | todo | open | suspect | no | medium | DIAG-002, REPAIR-002, AUDIT-001 | - |
| 3 | CYCLE-001 | Align repair-cycle auditing with transaction outcomes and churn rules | repair-cycles | planning | todo | open | suspect | yes | low | DIAG-002, REPAIR-002, AUDIT-001 | - |
| 3 | LEG-001 | Implement the legacy workflow contract migration stage and escalation rules | legacy-migration | planning | todo | open | suspect | no | high | ARCH-001, REPAIR-001 | - |
| 4 | LEG-002 | Record migration provenance and validate legacy upgrade flows | migration-proof | planning | todo | open | suspect | yes | medium | LEG-001 | - |
| 4 | PROOF-001 | Upgrade existing GPTTalker fixture contracts to convergence assertions | fixture-proof | planning | todo | open | suspect | yes | medium | REPAIR-002, BLOCK-001, CYCLE-001 | - |
| 4 | PROOF-002 | Extend the harness and fixture builders for stale-state edge cases | validation-harness | planning | todo | open | suspect | yes | medium | PROOF-001, LEG-002, PIVOT-002 | - |
| 4 | STACK-002 | Add Tier 1 full-toolchain execution proof coverage and audit alignment | execution-proof | planning | todo | open | suspect | no | medium | STACK-001, AUDIT-001, PROOF-002 | - |
| 4 | CONTRACT-001 | Extend contract, smoke, and integration validation to enforce the new architecture | contract-validation | planning | todo | open | suspect | yes | medium | ARCH-002, PROOF-001, PROOF-002, BLOCK-001 | - |
| 5 | GREEN-001 | Add weak-model greenfield self-sufficiency proof without duplicating the greenfield gate | greenfield-proof | planning | todo | open | suspect | no | high | STACK-002, CONTRACT-001, RESTART-001, AUDIT-001 | - |
| 5 | DOCS-001 | Post-implementation reconcile root docs and contracts to the shipped package state | package-docs | planning | todo | open | suspect | yes | low | ARCH-002, CONTRACT-001 | - |
