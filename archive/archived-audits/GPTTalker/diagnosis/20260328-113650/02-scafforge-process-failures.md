# Report 2: Scafforge Process Failures

This report maps validated issues back to Scafforge-owned skills, contracts, templates, or generated surfaces.

## SESSION002

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Instead of treating the repeated `ticket_update` rejection as a contract contradiction, the agent kept probing the state machine and burned time without acquiring new evidence.
- Safer target pattern: After the same lifecycle blocker repeats, re-run `ticket_lookup`, read `transition_guidance`, load `ticket-execution` if needed, and stop with a blocker instead of retrying the same transition.

## SESSION004

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: The coordinator substituted visual inspection or expected results for executable proof, then let artifacts claim PASS even though the earlier transcript said verification commands were unavailable.
- Safer target pattern: If validation cannot run, return a blocker; require raw command output in implementation and QA artifacts, and reserve smoke-test PASS proof to the deterministic `smoke_test` tool.

## SESSION005

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the workflow became confusing, the team leader started manufacturing implementation, review, QA, or smoke-test evidence itself instead of delegating the stage body to the assigned specialist or deterministic tool.
- Safer target pattern: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

## SESSION006

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Multiple workflow surfaces failed at once: lifecycle gates, closeout publication, acceptance scope, or deterministic tool execution disagreed about what could legally happen next. The coordinator then had to infer workarounds instead of following one competent contract path.
- Safer target pattern: Design every workflow state so it exposes one legal next action, one named owner, and one blocker return path. When transcript evidence shows a trap, audit adjacent surfaces together instead of treating each symptom as isolated noise.

## WFLOW024

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: Historical reconciliation still assumes the relevant evidence remains directly attached to the old source/target ticket, and the supersede path leaves the target publish-blocking invalidated. That traps the repo between stale historical state and closeout publication.
- Safer target pattern: Give `ticket_reconcile`, `ticket_create(post_completion_issue|process_verification)`, and `issue_intake` one legal path that can use current registered evidence for historical tickets, and make successful supersede-through-reconciliation non-blocking for handoff publication.

