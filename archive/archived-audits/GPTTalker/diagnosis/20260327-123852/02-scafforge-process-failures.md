# Report 2: Scafforge Process Failures

This report maps validated issues back to Scafforge-owned skills, contracts, templates, or generated surfaces.

## ENV002

- Surface: scafforge-audit and scafforge-repair host verification plus prerequisite-classification surfaces
- Root cause: This repo is uv-managed and the host already provides `uv`, so the missing pytest command is not primarily a host-prerequisite absence. The repo-local test environment was never successfully bootstrapped, or the recorded bootstrap state is stale after workflow changes.
- Safer target pattern: Rerun `environment_bootstrap` to restore the repo-local test environment before audit or repair verification. For uv repos with dev extras, bootstrap should sync with `uv sync --locked --extra dev`, then verify pytest from the repo-local environment.

## WFLOW019

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The repo has follow-up tickets whose lineage, dependency edges, or parent linkage no longer agree with the current manifest. Without a canonical reconciliation path, agents get trapped between stale source-follow-up history and current evidence.
- Safer target pattern: Use `ticket_reconcile` to atomically repair stale source/follow-up linkage, remove contradictory parent dependencies, and supersede invalidated follow-up tickets from current evidence.

## WFLOW020

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The workflow lacks a first-class split route for child tickets created from an open parent, or it still renders split parents as blocked, so agents encode decomposition through remediation semantics and the parent/child graph drifts.
- Safer target pattern: Support `ticket_create(source_mode=split_scope)` for open-parent decomposition, keep the parent open and non-foreground, and keep open-parent child tickets out of `net_new_scope` and `post_completion_issue` routing.

