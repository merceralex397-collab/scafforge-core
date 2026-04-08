# Report 4: Live Repo Repair Plan

- Repo: /home/pc/projects/GPTTalker
- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.

## Safe repair boundary

- Route 4 workflow-layer findings into `scafforge-repair` for deterministic managed-surface repair.

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

- Title: The supplied session transcript shows PASS-style implementation, QA, or smoke-test claims after validation had already failed or could not run
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION004`
- Summary: If validation cannot run, return a blocker; require raw command output in implementation and QA artifacts, and reserve smoke-test PASS proof to the deterministic `smoke_test` tool.

### REMED-003 (error)

- Title: The supplied session transcript shows the coordinator writing specialist stage artifacts directly instead of routing those outputs through the owning lane or deterministic tool
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION005`
- Summary: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

### REMED-004 (error)

- Title: The supplied session transcript shows the operator trapped between contradictory workflow rules instead of having one clear legal next move
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION006`
- Summary: Design every workflow state so it exposes one legal next action, one named owner, and one blocker return path. When transcript evidence shows a trap, audit adjacent surfaces together instead of treating each symptom as isolated noise.

### REMED-005 (error)

- Title: The current workflow has no legal reconciliation path for a superseded invalidated historical ticket, so closeout publication can deadlock on impossible preconditions
- Route: `manual-prerequisite`
- Repair class: Scafforge package work required before the next subject-repo repair run
- Source finding: `WFLOW024`
- Summary: Give `ticket_reconcile`, `ticket_create(post_completion_issue|process_verification)`, and `issue_intake` one legal path that can use current registered evidence for historical tickets, and make successful supersede-through-reconciliation non-blocking for handoff publication.

## Host Prerequisites

- The following findings are current-machine blockers or package stop conditions. Repair may refresh workflow surfaces, but these items still need operator action or Scafforge package work before verification can be trusted.

- `WFLOW024`: Give `ticket_reconcile`, `ticket_create(post_completion_issue|process_verification)`, and `issue_intake` one legal path that can use current registered evidence for historical tickets, and make successful supersede-through-reconciliation non-blocking for handoff publication.

