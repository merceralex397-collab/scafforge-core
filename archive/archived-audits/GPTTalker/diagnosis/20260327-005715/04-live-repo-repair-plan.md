# Report 4: Live Repo Repair Plan

- Repo: /home/pc/projects/GPTTalker
- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.

## Safe repair boundary

- Route 6 workflow-layer findings into `scafforge-repair` for deterministic managed-surface repair.

- Do not stop at tool replacement: rerun project-local skill regeneration, agent-team follow-up, and prompt hardening before handoff.

- Refresh generated ticket-update, ticket-lookup, stage-gate, smoke-test, handoff, workflow-doc, and coordinator-prompt surfaces together; these findings indicate a managed workflow-contract defect, not just repo-local operator error.

- Rerun project-local skill regeneration and prompt hardening after the deterministic refresh so the repo-local `ticket-execution` skill and team-leader prompt explain the same state machine the tools enforce.

## Intent-changing boundary

- Escalate any stack, scope, provider, or curated human-decision changes instead of labeling them as safe repair.

## Ticket recommendations

### REMED-001 (error)

- Title: The supplied session transcript shows the agent searching for workflow bypasses or soft dependency overrides instead of following the lifecycle contract
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION003`
- Summary: Reject unsupported stages and dependency overrides up front, tell the coordinator not to probe alternate transitions or close blocked tickets anyway, and return the contract contradiction as a blocker when the required proof is missing.

### REMED-002 (error)

- Title: The supplied session transcript shows the coordinator writing specialist stage artifacts directly instead of routing those outputs through the owning lane or deterministic tool
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION005`
- Summary: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

### REMED-003 (error)

- Title: Derived restart surfaces disagree with canonical workflow state, so resume guidance can route work from stale or contradictory facts
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW010`
- Summary: Regenerate `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` from canonical manifest/workflow state after every workflow save, keep handoff readiness verification-gated, and fail repair verification if any derived restart surface drifts.

### REMED-004 (error)

- Title: The generated lease-ownership contract is split across coordinator and worker surfaces, so agents can disagree about who should claim a ticket and when bootstrap gates apply
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW012`
- Summary: Adopt one lease model everywhere: the team leader owns `ticket_claim` and `ticket_release`, specialists work only inside the already-active ticket lease, and only Wave 0 setup work may claim before bootstrap is ready.

### REMED-005 (error)

- Title: The supplied session transcript shows the smoke-test stage running a heuristic command that does not match the ticket's explicit acceptance command
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW017`
- Summary: Treat acceptance-backed smoke commands as canonical, let `smoke_test` infer them automatically, and reject heuristic scope changes unless the caller provides an intentional exact command override.

### REMED-006 (warning)

- Title: Test suite has failures: 6 test(s) failed
- Route: `ticket-pack-builder`
- Repair class: generated-repo remediation ticket
- Source finding: `EXEC003`
- Summary: Run `pytest tests/ -v` and fix all failures before marking a ticket done. QA artifacts must include pytest output showing 0 failures.

### REMED-007 (warning)

- Title: Post-repair process verification is still pending for one or more historical done tickets
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW008`
- Summary: Keep `pending_process_verification` visible, route the backlog verifier across the affected done-ticket set, and do not call verification clean until `ticket_reverify` or current backlog-verification evidence clears those tickets.

## Post-repair follow-up

- Route 1 source-layer remediation item(s) through `ticket-pack-builder` and any generated repo guarded ticket surfaces after workflow repair is complete.

