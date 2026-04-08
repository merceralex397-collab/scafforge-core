# Report 4: Live Repo Repair Plan

- Repo: /home/pc/projects/GPTTalker
- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.

## Safe repair boundary

- No safe managed-surface repair was identified from the current findings.

## Intent-changing boundary

- Escalate any stack, scope, provider, or curated human-decision changes instead of labeling them as safe repair.

## Ticket recommendations

### REMED-001 (error)

- Title: The repo has Python tests, but repo-local pytest is still unavailable because bootstrap state is failed, missing, or stale
- Route: `manual-prerequisite`
- Repair class: host prerequisite or operator follow-up
- Source finding: `ENV002`
- Summary: Rerun `environment_bootstrap` to restore the repo-local test environment before audit or repair verification. For uv repos with dev extras, bootstrap should sync with `uv sync --locked --extra dev`, then verify pytest from the repo-local environment.

## Host Prerequisites

- The following findings are current-machine blockers or package stop conditions. Repair may refresh workflow surfaces, but these items still need operator action or Scafforge package work before verification can be trusted.

- `ENV002`: Rerun `environment_bootstrap` to restore the repo-local test environment before audit or repair verification. For uv repos with dev extras, bootstrap should sync with `uv sync --locked --extra dev`, then verify pytest from the repo-local environment.

