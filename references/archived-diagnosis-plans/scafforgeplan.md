# Scafforge Deadlock-Prevention Overhaul

## Summary

- GPTTalker exposed two workflow deadlock families:
  - audit/repair churn after real workflow defects had already narrowed into source and ticket reconciliation
  - ticket-state deadlock when Scafforge lacked a canonical way to split or reconcile ticket graphs cleanly
- `SCAFFORGE-STATE-CLEANUP-2026-03-27.md` was useful in one key way: it proved Scafforge was missing a first-class open-parent split route. The ad hoc `split_scope` change was worth adopting into the package contract.
- The cleanup note also highlighted a truth-hierarchy risk: `.opencode/meta/bootstrap-provenance.json` must stay provenance-only. It may record real regeneration history, but it must not become a mutable restart or queue surface.
- The package now needs explicit workflow upgrades, not more additive repo-local drift.

## Public Contract Changes

- Bump generated workflow contract to `process_version: 7`.
- Replace boolean-style `repair_follow_on` gating with an explicit outcome model:
  - `managed_blocked`
  - `source_follow_up`
  - `clean`
- Gate `ticket_lookup`, `/resume`, and restart-blocking behavior only on `repair_follow_on.outcome == managed_blocked`.
- Keep `handoff-brief` as a publication step, not a blocking repair-follow-on stage.
- Add a guarded `ticket_reconcile` tool for evidence-backed ticket-graph repair. It must support:
  - superseding stale follow-up tickets
  - rewriting stale follow-up scope
  - removing contradictory dependencies
  - updating source and follow-up linkage atomically
  - writing a reconciliation artifact
- Extend `TicketSourceMode` with `split_scope` for child tickets created from an open or reopened parent ticket during planned decomposition.
- Define split-parent semantics:
  - the source ticket must be open or reopened
  - split children use `source_mode: split_scope`
  - the parent remains open and is explicitly linked to its children instead of being mis-routed as historical remediation
- Broaden guarded closed-ticket evidence routing:
  - `ticket_create` and `issue_intake` may create `process_verification` and `post_completion_issue` follow-up from completed source tickets without a normal write lease, but only from current registered evidence
- Add new audit findings:
  - `WFLOW018`: closed-ticket remediation routing is deadlocked by lease rules
  - `WFLOW019`: remediation ticket graph is stale or contradictory to current acceptance evidence
  - `WFLOW020`: open-ticket split routing is missing or inconsistent, forcing non-canonical child-ticket creation

## Implementation Changes

- Audit convergence:
  - keep repo truth, transcript chronology, and current-state reconciliation separate
  - stop treating truthful `pending_process_verification` as a managed-repair failure
  - surface repeated diagnosis churn as package work, not another subject-repo audit loop
- Repair convergence:
  - classify post-verify repair state as exactly one of `managed_blocked`, `source_follow_up`, or `clean`
  - clear managed blocking when only `EXEC*` source follow-up or truthful `pending_process_verification` remains
  - regenerate restart surfaces from canonical state in the same repair run
  - record repair provenance with package and process revision metadata
- Ticket graph and split handling:
  - add first-class `split_scope` routing for planned open-parent decomposition
  - add `ticket_reconcile` for stale or contradictory source and follow-up graphs
  - reject tickets that both name a source ticket and depend on that same source ticket
  - keep open-parent splits out of `net_new_scope` and `post_completion_issue`
- Truth hierarchy hardening:
  - keep `tickets/manifest.json` and `.opencode/state/workflow-state.json` canonical for queue and routing state
  - keep `.opencode/meta/bootstrap-provenance.json` provenance-only
- Prompt and workflow updates:
  - teach the team leader, `/resume`, and `ticket-execution` that only `managed_blocked` halts ordinary ticket lifecycle work
  - require `split_scope` for open-parent decomposition
  - require `ticket_reconcile` when fresh evidence invalidates an older follow-up split
- Validation overhaul:
  - retain synthetic smoke coverage
  - add GPTTalker-shaped regression fixtures for closed-ticket follow-up deadlock, contradictory ticket graphs, and missing split routing

## Test Plan

- Contract validation:
  - require `process_version: 7`
  - require `split_scope`
  - require `ticket_reconcile`
  - require explicit `repair_follow_on.outcome`
  - require `WFLOW018`, `WFLOW019`, and `WFLOW020`
- Synthetic smoke coverage:
  - keep `WFLOW009`, `WFLOW016`, `WFLOW017`, `CYCLE001`, and `CYCLE002`
  - add fixtures for:
    - closed-ticket follow-up deadlock -> `WFLOW018`
    - contradictory source and follow-up graph -> `WFLOW019`
    - missing open-parent split routing -> `WFLOW020`
    - source-follow-up-only repair completion -> `repair_follow_on.outcome == source_follow_up`
    - truthful pending process verification -> `repair_follow_on.outcome == clean`
- Proving-ground acceptance:
  - rerun the updated audit and repair flow against GPTTalker
  - require one stable diagnosis, no oscillating repair recommendation set, canonical split-parent routing, and resumption of ordinary ticket work without manual state surgery

## Assumptions

- Backward compatibility is secondary to resolving the deadlock cleanly; existing repos migrate through managed repair.
- GPTTalker raw logs remain reference material, but the package gate should rely on distilled fixtures and canonical failure shapes.
- Source code fixes stay outside `scafforge-repair`; repair owns managed workflow convergence, restart truthfulness, and canonical ticket-state repair.
