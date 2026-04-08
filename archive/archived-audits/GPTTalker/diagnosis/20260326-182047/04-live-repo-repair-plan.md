# Report 4: Live Repo Repair Plan

- Repo: /home/pc/projects/GPTTalker
- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.

## Safe repair boundary

- Route 3 workflow-layer findings into `scafforge-repair` for deterministic managed-surface repair.

- Refresh generated ticket-update, ticket-lookup, stage-gate, smoke-test, handoff, workflow-doc, and coordinator-prompt surfaces together; these findings indicate a managed workflow-contract defect, not just repo-local operator error.

- Rerun project-local skill regeneration and prompt hardening after the deterministic refresh so the repo-local `ticket-execution` skill and team-leader prompt explain the same state machine the tools enforce.

## Intent-changing boundary

- Escalate any stack, scope, provider, or curated human-decision changes instead of labeling them as safe repair.

## Ticket recommendations

### REMED-001 (error)

- Title: The managed smoke-test override contract can fail before the requested smoke command even starts
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW016`
- Summary: Parse one-item shell-style overrides into argv, treat leading `KEY=VALUE` tokens as environment overrides, and report malformed overrides as configuration errors instead of misclassifying them as runtime environment failures.

### REMED-002 (error)

- Title: The supplied session transcript shows the managed smoke-test override path failing before the requested smoke command starts
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW016`
- Summary: Parse shell-style smoke-test overrides before execution, strip leading `KEY=VALUE` env assignments into the spawn environment, and report malformed overrides as configuration errors rather than environment failures.

### REMED-003 (warning)

- Title: Test suite has failures: 7 test(s) failed
- Route: `ticket-pack-builder`
- Repair class: generated-repo remediation ticket
- Source finding: `EXEC003`
- Summary: Run `pytest tests/ -v` and fix all failures before marking a ticket done. QA artifacts must include pytest output showing 0 failures.

### REMED-004 (warning)

- Title: Post-repair process verification is still pending for one or more historical done tickets
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW008`
- Summary: Keep `pending_process_verification` visible, route the backlog verifier across the affected done-ticket set, and do not call verification clean until `ticket_reverify` or current backlog-verification evidence clears those tickets.

## Post-repair follow-up

- Route 1 source-layer remediation item(s) through `ticket-pack-builder` and any generated repo guarded ticket surfaces after workflow repair is complete.

