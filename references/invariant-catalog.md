# Invariant Catalog

## Purpose

This catalog turns the RFC invariants into a checklist that later tickets can implement and validate against. Anything that changes authority, mutation, restart, or proof behavior should satisfy these invariants explicitly.

## Invariants

### Finding-disposition

1. Every diagnosis finding resolves to exactly one authoritative disposition class.
2. Repair may not silently reclassify a diagnosis finding into a different class.
3. `repair_follow_on` must be derived from the disposition bundle plus final-state verification only.

### Ticket graph

4. A ticket may not name the same parent in both `source_ticket_id` and `depends_on`.
5. Reverse follow-up linkage must be symmetric.
6. A `split_scope` child may not block on its open parent.
7. No circular `depends_on` graph may be published.
8. No ticket may end in an impossible combination of lifecycle, resolution, and verification state.

### Workflow and restart

9. `manifest.active_ticket` and `workflow.active_ticket` must converge after every successful mutation.
10. Derived restart surfaces may only be generated from canonical manifest, workflow state, and pivot state.
11. No repair or pivot phase may publish restart surfaces before final-state verification of the candidate final snapshot.
12. Repair-side restart renderers may not remain independently authoritative after the mutation-layer cutover.

### Pivot state

13. Pivot state has one explicit persistence owner.
14. Pivot operations that mutate tickets or workflow state must route through canonical runtime tools or a shared adapter that reuses the runtime invariant contract.
15. Restart surfaces may consume pivot state but may not synthesize pivot truth on behalf of pivot tracking.

### Outcome semantics

16. `managed_blocked` may only represent true managed-workflow or environment blockers.
17. `source_follow_up` may not block ordinary active-ticket lifecycle execution by itself.
18. Truthful `pending_process_verification` may not be escalated to `managed_blocked` by itself.

### Product direction

19. Greenfield remains the primary user path.
20. Audit and repair remain non-primary lifecycle tools and may not be required for normal greenfield success.
21. The package must bias toward generated-repo self-sufficiency rather than host-side rescue dependence.

### Contract alignment

22. `AGENTS.md`, `skills/skill-flow-manifest.json`, and the reference contracts must agree on authority ownership and publish-gate behavior.
23. The greenfield contract may not be accidentally strengthened into a redundant second gate when repair and pivot publish gating are tightened.

### Validation

24. Every recurring loop class must have a replayable regression fixture.
25. End-to-end repair tests must assert convergence and publish safety, not only exact strings.
26. Tier 1 stacks must have real execution proof coverage on proof hosts.
27. Existing curated fixture families must be preserved and upgraded rather than discarded.
