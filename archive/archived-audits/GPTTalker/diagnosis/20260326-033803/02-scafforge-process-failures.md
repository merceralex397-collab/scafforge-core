# Report 2: Scafforge Process Failures

This report maps validated issues back to Scafforge-owned skills, contracts, templates, or generated surfaces.

## SESSION003

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the lifecycle gate became confusing, the agent started trying unsupported stages or explicit workarounds rather than resolving the missing proof or contradictory contract.
- Safer target pattern: Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.

## SESSION005

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the workflow became confusing, the team leader started manufacturing implementation, review, QA, or smoke-test evidence itself instead of delegating the stage body to the assigned specialist or deterministic tool.
- Safer target pattern: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

## WFLOW009

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: Closed historical tickets need reverification after a process change, but the current contract treats `ticket_reverify` like ordinary lease-bound write work while `ticket_claim` forbids claiming closed tickets. That makes trust restoration impossible without bypassing the workflow.
- Safer target pattern: Let `ticket_reverify` mutate closed done tickets through a narrow reverification guard instead of a normal lane write lease, and expose that path in `ticket_lookup.transition_guidance` so the coordinator sees a legal trust-restoration route.

## EXEC003

- Surface: generated repo implementation and validation surfaces
- Root cause: Tests were marked done in QA artifacts without verifying the full suite passes. Failing tests indicate incomplete implementations, broken contracts, or regressions.
- Safer target pattern: Run `pytest tests/ -v` and fix all failures before marking a ticket done. QA artifacts must include pytest output showing 0 failures.

## WFLOW008

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The workflow contract changed, but the repo still contains completed tickets whose trust predates the current process window or lacks current backlog-verification evidence. Declaring the repo clean before that reverification finishes hides unresolved process risk.
- Safer target pattern: Keep `pending_process_verification` visible, route the backlog verifier across the affected done-ticket set, and do not call verification clean until `ticket_reverify` or current backlog-verification evidence clears those tickets.

