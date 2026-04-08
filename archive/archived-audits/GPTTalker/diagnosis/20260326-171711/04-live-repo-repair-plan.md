# Report 4: Live Repo Repair Plan

- Repo: /home/pc/projects/GPTTalker
- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.

## Safe repair boundary

- Route 16 workflow-layer findings into `scafforge-repair` for deterministic managed-surface repair.

- Refresh generated ticket-update, ticket-lookup, stage-gate, smoke-test, handoff, workflow-doc, and coordinator-prompt surfaces together; these findings indicate a managed workflow-contract defect, not just repo-local operator error.

- Rerun project-local skill regeneration and prompt hardening after the deterministic refresh so the repo-local `ticket-execution` skill and team-leader prompt explain the same state machine the tools enforce.

## Intent-changing boundary

- Escalate any stack, scope, provider, or curated human-decision changes instead of labeling them as safe repair.

## Ticket recommendations

### REMED-001 (error)

- Title: The supplied session transcript shows repeated retries of the same rejected lifecycle transition
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION002`
- Summary: After the same lifecycle blocker repeats, re-run `ticket_lookup`, read `transition_guidance`, load `ticket-execution` if needed, and stop with a blocker instead of retrying the same transition.

### REMED-002 (error)

- Title: The supplied session transcript shows the agent searching for workflow bypasses instead of following the lifecycle contract
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION003`
- Summary: Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.

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

- Title: The supplied session transcript shows the coordinator writing specialist stage artifacts directly instead of routing those outputs through the owning lane or deterministic tool
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION005`
- Summary: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

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

- Title: The supplied session transcript shows the runtime exposing or invoking broken workflow helper tools instead of only executable tool modules
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW015`
- Summary: Keep workflow helpers private under `.opencode/lib/workflow.ts`, expose only real `tool({...})` modules to the model, and make audit treat transcript-level missing-`execute` failures as managed workflow-contract defects.

### REMED-013 (error)

- Title: The supplied session transcript shows the runtime exposing or invoking broken workflow helper tools instead of only executable tool modules
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW015`
- Summary: Keep workflow helpers private under `.opencode/lib/workflow.ts`, expose only real `tool({...})` modules to the model, and make audit treat transcript-level missing-`execute` failures as managed workflow-contract defects.

### REMED-014 (error)

- Title: The supplied session transcript shows the runtime exposing or invoking broken workflow helper tools instead of only executable tool modules
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW015`
- Summary: Keep workflow helpers private under `.opencode/lib/workflow.ts`, expose only real `tool({...})` modules to the model, and make audit treat transcript-level missing-`execute` failures as managed workflow-contract defects.

### REMED-015 (error)

- Title: The supplied session transcript shows the runtime exposing or invoking broken workflow helper tools instead of only executable tool modules
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW015`
- Summary: Keep workflow helpers private under `.opencode/lib/workflow.ts`, expose only real `tool({...})` modules to the model, and make audit treat transcript-level missing-`execute` failures as managed workflow-contract defects.

### REMED-016 (warning)

- Title: Test suite has failures: 7 test(s) failed
- Route: `ticket-pack-builder`
- Repair class: generated-repo remediation ticket
- Source finding: `EXEC003`
- Summary: Run `pytest tests/ -v` and fix all failures before marking a ticket done. QA artifacts must include pytest output showing 0 failures.

### REMED-017 (warning)

- Title: Post-repair process verification is still pending for one or more historical done tickets
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW008`
- Summary: Keep `pending_process_verification` visible, route the backlog verifier across the affected done-ticket set, and do not call verification clean until `ticket_reverify` or current backlog-verification evidence clears those tickets.

## Post-repair follow-up

- Route 1 source-layer remediation item(s) through `ticket-pack-builder` and any generated repo guarded ticket surfaces after workflow repair is complete.

