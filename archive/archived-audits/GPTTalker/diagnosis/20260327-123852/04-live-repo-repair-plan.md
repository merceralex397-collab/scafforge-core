# Report 4: Live Repo Repair Plan

- Repo: /home/pc/projects/GPTTalker
- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.

## Safe repair boundary

- Route 2 workflow-layer findings into `scafforge-repair` for deterministic managed-surface repair.

- Refresh generated ticket-update, ticket-lookup, stage-gate, smoke-test, handoff, workflow-doc, and coordinator-prompt surfaces together; these findings indicate a managed workflow-contract defect, not just repo-local operator error.

## Intent-changing boundary

- Escalate any stack, scope, provider, or curated human-decision changes instead of labeling them as safe repair.

## Ticket recommendations

### REMED-001 (error)

- Title: The repo has Python tests, but repo-local pytest is still unavailable because bootstrap state is failed, missing, or stale
- Route: `manual-prerequisite`
- Repair class: host prerequisite or operator follow-up
- Source finding: `ENV002`
- Summary: Rerun `environment_bootstrap` to restore the repo-local test environment before audit or repair verification. For uv repos with dev extras, bootstrap should sync with `uv sync --locked --extra dev`, then verify pytest from the repo-local environment.

### REMED-002 (error)

- Title: The ticket graph contains stale or contradictory source/follow-up linkage
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW019`
- Summary: Use `ticket_reconcile` to atomically repair stale source/follow-up linkage, remove contradictory parent dependencies, and supersede invalidated follow-up tickets from current evidence.

### REMED-003 (error)

- Title: Open-parent ticket decomposition is missing or routed through non-canonical source modes
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW020`
- Summary: Support `ticket_create(source_mode=split_scope)` for open-parent decomposition, keep the parent open and non-foreground, and keep open-parent child tickets out of `net_new_scope` and `post_completion_issue` routing.

## Host Prerequisites

- The following findings are current-machine blockers or package stop conditions. Repair may refresh workflow surfaces, but these items still need operator action or Scafforge package work before verification can be trusted.

- `ENV002`: Rerun `environment_bootstrap` to restore the repo-local test environment before audit or repair verification. For uv repos with dev extras, bootstrap should sync with `uv sync --locked --extra dev`, then verify pytest from the repo-local environment.

