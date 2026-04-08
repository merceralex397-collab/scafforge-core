# Report 2: Scafforge Process Failures

This report maps validated issues back to Scafforge-owned skills, contracts, templates, or generated surfaces.

## SESSION003

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the lifecycle gate became confusing, the agent started trying unsupported stages, explicit workarounds, or softer 'close it anyway' / dependency-override reasoning instead of resolving the missing proof or contradictory contract.
- Safer target pattern: Reject unsupported stages and dependency overrides up front, tell the coordinator not to probe alternate transitions or close blocked tickets anyway, and return the contract contradiction as a blocker when the required proof is missing.

## SESSION005

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the workflow became confusing, the team leader started manufacturing implementation, review, QA, or smoke-test evidence itself instead of delegating the stage body to the assigned specialist or deterministic tool.
- Safer target pattern: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

## WFLOW017

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The generated `smoke_test` tool does not inspect the ticket's explicit acceptance commands before falling back to generic repo-level smoke detection. That lets the coordinator run a broader full-suite command or an ad hoc narrowed subset that does not match the ticket's canonical smoke requirement.
- Safer target pattern: Infer smoke commands from explicit ticket acceptance criteria first, treat those commands as canonical smoke scope, and only fall back to generic repo-level detection when no acceptance-backed smoke command exists.

## WFLOW017

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The generated `smoke_test` tool fell back to repo-level pytest detection or caller-supplied `test_paths` instead of binding itself to the ticket's canonical smoke acceptance command. That can widen smoke scope to unrelated failures or narrow it away from the actual closeout requirement.
- Safer target pattern: Treat acceptance-backed smoke commands as canonical, let `smoke_test` infer them automatically, and reject heuristic scope changes unless the caller provides an intentional exact command override.

## EXEC003

- Surface: generated repo implementation and validation surfaces
- Root cause: Tests were marked done in QA artifacts without verifying the full suite passes. Failing tests indicate incomplete implementations, broken contracts, or regressions.
- Safer target pattern: Run `pytest tests/ -v` and fix all failures before marking a ticket done. QA artifacts must include pytest output showing 0 failures.

## WFLOW008

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The workflow contract changed, but the repo still contains completed tickets whose trust predates the current process window or lacks current backlog-verification evidence. Declaring the repo clean before that reverification finishes hides unresolved process risk.
- Safer target pattern: Keep `pending_process_verification` visible, route the backlog verifier across the affected done-ticket set, and do not call verification clean until `ticket_reverify` or current backlog-verification evidence clears those tickets.

