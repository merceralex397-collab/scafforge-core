# Report 2: Scafforge Process Failures

This report maps validated issues back to Scafforge-owned skills, contracts, templates, or generated surfaces.

## CYCLE001

- Surface: scafforge-audit diagnosis contract
- Root cause: The repo contains a prior diagnosis pack and a later repair history entry, but the current audit still reproduces workflow-layer findings. That means the previous repair either skipped a required regeneration step, used stale package logic, or misclassified drift as protected intent.
- Safer target pattern: Before another repair run, compare the latest diagnosis pack against repair_history, identify which findings persisted, and treat repeated deprecated package-managed drift as a repair failure to fix rather than as preserved intent.

## SESSION002

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Instead of treating the repeated `ticket_update` rejection as a contract contradiction, the agent kept probing the state machine and burned time without acquiring new evidence.
- Safer target pattern: After the same lifecycle blocker repeats, re-run `ticket_lookup`, read `transition_guidance`, load `ticket-execution` if needed, and stop with a blocker instead of retrying the same transition.

## SESSION003

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the lifecycle gate became confusing, the agent started trying unsupported stages or explicit workarounds rather than resolving the missing proof or contradictory contract.
- Safer target pattern: Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.

## SESSION003

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the lifecycle gate became confusing, the agent started trying unsupported stages or explicit workarounds rather than resolving the missing proof or contradictory contract.
- Safer target pattern: Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.

## SESSION003

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the lifecycle gate became confusing, the agent started trying unsupported stages or explicit workarounds rather than resolving the missing proof or contradictory contract.
- Safer target pattern: Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.

## SESSION003

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the lifecycle gate became confusing, the agent started trying unsupported stages or explicit workarounds rather than resolving the missing proof or contradictory contract.
- Safer target pattern: Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.

## SESSION003

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the lifecycle gate became confusing, the agent started trying unsupported stages or explicit workarounds rather than resolving the missing proof or contradictory contract.
- Safer target pattern: Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.

## SESSION003

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the lifecycle gate became confusing, the agent started trying unsupported stages or explicit workarounds rather than resolving the missing proof or contradictory contract.
- Safer target pattern: Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.

## SESSION005

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the workflow became confusing, the team leader started manufacturing implementation, review, QA, or smoke-test evidence itself instead of delegating the stage body to the assigned specialist or deterministic tool.
- Safer target pattern: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

## SESSION005

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the workflow became confusing, the team leader started manufacturing implementation, review, QA, or smoke-test evidence itself instead of delegating the stage body to the assigned specialist or deterministic tool.
- Safer target pattern: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

## SESSION005

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the workflow became confusing, the team leader started manufacturing implementation, review, QA, or smoke-test evidence itself instead of delegating the stage body to the assigned specialist or deterministic tool.
- Safer target pattern: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

## SESSION005

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the workflow became confusing, the team leader started manufacturing implementation, review, QA, or smoke-test evidence itself instead of delegating the stage body to the assigned specialist or deterministic tool.
- Safer target pattern: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

## WFLOW012

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: Some workflow docs and prompts still describe worker-owned lease claims while others expect the team leader to coordinate claims. That contradiction is enough to make weaker models thrash around ticket ownership and pre-bootstrap write rules.
- Safer target pattern: Adopt one lease model everywhere: the team leader owns `ticket_claim` and `ticket_release`, specialists work only inside the already-active ticket lease, and only Wave 0 setup work may claim before bootstrap is ready.

## WFLOW013

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: When `/resume` and the surrounding docs do not put `tickets/manifest.json` plus `.opencode/state/workflow-state.json` first, weaker models start following stale restart text, ignore `.opencode/state/latest-handoff.md`, or abandon the active foreground ticket for historical reverification too early.
- Safer target pattern: Make manifest + workflow-state canonical for `/resume`, keep `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` derived-only, and preserve the active open ticket as the primary lane until it is resolved.

## WFLOW015

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The tool surface leaked `_workflow_*` helpers or other non-executable exports into the model-visible tool list. When the coordinator called them, the runtime failed before any workflow logic could run.
- Safer target pattern: Keep workflow helpers private under `.opencode/lib/workflow.ts`, expose only real `tool({...})` modules to the model, and make audit treat transcript-level missing-`execute` failures as managed workflow-contract defects.

## WFLOW015

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The tool surface leaked `_workflow_*` helpers or other non-executable exports into the model-visible tool list. When the coordinator called them, the runtime failed before any workflow logic could run.
- Safer target pattern: Keep workflow helpers private under `.opencode/lib/workflow.ts`, expose only real `tool({...})` modules to the model, and make audit treat transcript-level missing-`execute` failures as managed workflow-contract defects.

## WFLOW015

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The tool surface leaked `_workflow_*` helpers or other non-executable exports into the model-visible tool list. When the coordinator called them, the runtime failed before any workflow logic could run.
- Safer target pattern: Keep workflow helpers private under `.opencode/lib/workflow.ts`, expose only real `tool({...})` modules to the model, and make audit treat transcript-level missing-`execute` failures as managed workflow-contract defects.

## WFLOW015

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The tool surface leaked `_workflow_*` helpers or other non-executable exports into the model-visible tool list. When the coordinator called them, the runtime failed before any workflow logic could run.
- Safer target pattern: Keep workflow helpers private under `.opencode/lib/workflow.ts`, expose only real `tool({...})` modules to the model, and make audit treat transcript-level missing-`execute` failures as managed workflow-contract defects.

## EXEC003

- Surface: generated repo implementation and validation surfaces
- Root cause: Tests were marked done in QA artifacts without verifying the full suite passes. Failing tests indicate incomplete implementations, broken contracts, or regressions.
- Safer target pattern: Run `pytest tests/ -v` and fix all failures before marking a ticket done. QA artifacts must include pytest output showing 0 failures.

## WFLOW008

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The workflow contract changed, but the repo still contains completed tickets whose trust predates the current process window or lacks current backlog-verification evidence. Declaring the repo clean before that reverification finishes hides unresolved process risk.
- Safer target pattern: Keep `pending_process_verification` visible, route the backlog verifier across the affected done-ticket set, and do not call verification clean until `ticket_reverify` or current backlog-verification evidence clears those tickets.

