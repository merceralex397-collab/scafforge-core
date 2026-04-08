# Report 4: Live Repo Repair Plan

- Repo: /home/pc/projects/GPTTalker
- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.

## Repeated Failure Note

- This repo has already gone through at least one audit-to-repair cycle and still reproduces workflow-layer findings.
- Before another repair run, compare the latest previous diagnosis pack against repair history and explain why those findings survived.

## Safe repair boundary

- Route 22 workflow-layer findings into `scafforge-repair` for deterministic managed-surface repair.

- Do not stop at tool replacement: rerun project-local skill regeneration, agent-team follow-up, and prompt hardening before handoff.

- Refresh generated ticket-update, ticket-lookup, stage-gate, smoke-test, handoff, workflow-doc, and coordinator-prompt surfaces together; these findings indicate a managed workflow-contract defect, not just repo-local operator error.

- Rerun project-local skill regeneration and prompt hardening after the deterministic refresh so the repo-local `ticket-execution` skill and team-leader prompt explain the same state machine the tools enforce.

## Intent-changing boundary

- Escalate any stack, scope, provider, or curated human-decision changes instead of labeling them as safe repair.

## Ticket recommendations

### REMED-001 (error)

- Title: A previous audit-to-repair cycle did not clear one or more workflow-layer findings before work resumed
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `CYCLE001`
- Summary: Before another repair run, compare the latest diagnosis pack against repair_history, identify which findings persisted, and treat repeated deprecated package-managed drift as a repair failure to fix rather than as preserved intent.

### REMED-002 (error)

- Title: The supplied session transcript shows repeated retries of the same rejected lifecycle transition
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION002`
- Summary: After the same lifecycle blocker repeats, re-run `ticket_lookup`, read `transition_guidance`, load `ticket-execution` if needed, and stop with a blocker instead of retrying the same transition.

### REMED-003 (error)

- Title: The supplied session transcript shows the agent searching for workflow bypasses instead of following the lifecycle contract
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION003`
- Summary: Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.

### REMED-004 (error)

- Title: The supplied session transcript shows the agent searching for workflow bypasses instead of following the lifecycle contract
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION003`
- Summary: Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.

### REMED-005 (error)

- Title: The supplied session transcript shows the agent searching for workflow bypasses instead of following the lifecycle contract
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION003`
- Summary: Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.

### REMED-006 (error)

- Title: The supplied session transcript shows the agent searching for workflow bypasses instead of following the lifecycle contract
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION003`
- Summary: Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.

### REMED-007 (error)

- Title: The supplied session transcript shows the agent searching for workflow bypasses instead of following the lifecycle contract
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION003`
- Summary: Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.

### REMED-008 (error)

- Title: The supplied session transcript shows the agent searching for workflow bypasses instead of following the lifecycle contract
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION003`
- Summary: Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.

### REMED-009 (error)

- Title: The supplied session transcript shows the coordinator writing specialist stage artifacts directly instead of routing those outputs through the owning lane or deterministic tool
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION005`
- Summary: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

### REMED-010 (error)

- Title: The supplied session transcript shows the coordinator writing specialist stage artifacts directly instead of routing those outputs through the owning lane or deterministic tool
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION005`
- Summary: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

### REMED-011 (error)

- Title: The supplied session transcript shows the coordinator writing specialist stage artifacts directly instead of routing those outputs through the owning lane or deterministic tool
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION005`
- Summary: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

### REMED-012 (error)

- Title: The supplied session transcript shows the coordinator writing specialist stage artifacts directly instead of routing those outputs through the owning lane or deterministic tool
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION005`
- Summary: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

### REMED-013 (error)

- Title: The generated backlog reverification path is structurally deadlocked for closed tickets
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW009`
- Summary: Let `ticket_reverify` mutate closed done tickets through a narrow reverification guard instead of a normal lane write lease, and expose that path in `ticket_lookup.transition_guidance` so the coordinator sees a legal trust-restoration route.

### REMED-014 (error)

- Title: The generated lease-ownership contract is split across coordinator and worker surfaces, so agents can disagree about who should claim a ticket and when bootstrap gates apply
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW012`
- Summary: Adopt one lease model everywhere: the team leader owns `ticket_claim` and `ticket_release`, specialists work only inside the already-active ticket lease, and only Wave 0 setup work may claim before bootstrap is ready.

### REMED-015 (error)

- Title: The generated resume contract still gives too much authority to derived handoff text or lets reverification obscure the active open ticket
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW013`
- Summary: Make manifest + workflow-state canonical for `/resume`, keep `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` derived-only, and preserve the active open ticket as the primary lane until it is resolved.

### REMED-016 (error)

- Title: The supplied session transcript shows the runtime exposing or invoking broken workflow helper tools instead of only executable tool modules
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW015`
- Summary: Keep workflow helpers private under `.opencode/lib/workflow.ts`, expose only real `tool({...})` modules to the model, and make audit treat transcript-level missing-`execute` failures as managed workflow-contract defects.

### REMED-017 (error)

- Title: The supplied session transcript shows the runtime exposing or invoking broken workflow helper tools instead of only executable tool modules
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW015`
- Summary: Keep workflow helpers private under `.opencode/lib/workflow.ts`, expose only real `tool({...})` modules to the model, and make audit treat transcript-level missing-`execute` failures as managed workflow-contract defects.

### REMED-018 (error)

- Title: The supplied session transcript shows the runtime exposing or invoking broken workflow helper tools instead of only executable tool modules
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW015`
- Summary: Keep workflow helpers private under `.opencode/lib/workflow.ts`, expose only real `tool({...})` modules to the model, and make audit treat transcript-level missing-`execute` failures as managed workflow-contract defects.

### REMED-019 (error)

- Title: The supplied session transcript shows the runtime exposing or invoking broken workflow helper tools instead of only executable tool modules
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW015`
- Summary: Keep workflow helpers private under `.opencode/lib/workflow.ts`, expose only real `tool({...})` modules to the model, and make audit treat transcript-level missing-`execute` failures as managed workflow-contract defects.

### REMED-020 (error)

- Title: Workflow tools or docs still use deprecated status or stage vocabulary
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `workflow-vocabulary-drift`
- Summary: Keep workflow defaults and stage checks aligned on `todo|ready|in_progress|blocked|review|qa|done` plus `planning|implementation|review|qa` stage proof.

### REMED-021 (warning)

- Title: Test suite has failures: 7 test(s) failed
- Route: `ticket-pack-builder`
- Repair class: generated-repo remediation ticket
- Source finding: `EXEC003`
- Summary: Run `pytest tests/ -v` and fix all failures before marking a ticket done. QA artifacts must include pytest output showing 0 failures.

### REMED-022 (warning)

- Title: One or more repo-local skills still contain generic placeholder text instead of project-specific guidance
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SKILL001`
- Summary: Populate every baseline local skill with concrete repo-specific rules and validation commands; generated `.opencode/skills/` files must not retain template filler.

### REMED-023 (warning)

- Title: Post-repair process verification is still pending for one or more historical done tickets
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW008`
- Summary: Keep `pending_process_verification` visible, route the backlog verifier across the affected done-ticket set, and do not call verification clean until `ticket_reverify` or current backlog-verification evidence clears those tickets.

## Post-repair follow-up

- Route 1 source-layer remediation item(s) through `ticket-pack-builder` and any generated repo guarded ticket surfaces after workflow repair is complete.

