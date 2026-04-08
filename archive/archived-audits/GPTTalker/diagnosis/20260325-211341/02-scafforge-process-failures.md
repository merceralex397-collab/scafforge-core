# Report 2: Scafforge Process Failures

This report maps validated issues back to Scafforge-owned skills, contracts, templates, or generated surfaces.

## SESSION002

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Instead of treating the repeated `ticket_update` rejection as a contract contradiction, the agent kept probing the state machine and burned time without acquiring new evidence.
- Safer target pattern: After the same lifecycle blocker repeats, re-run `ticket_lookup`, read `transition_guidance`, load `ticket-execution` if needed, and stop with a blocker instead of retrying the same transition.

## SESSION003

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the lifecycle gate became confusing, the agent started trying unsupported stages or explicit workarounds rather than resolving the missing proof or contradictory contract.
- Safer target pattern: Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.

## SESSION005

- Surface: scafforge-audit transcript chronology and causal diagnosis surfaces
- Root cause: Once the workflow became confusing, the team leader started manufacturing implementation, review, QA, or smoke-test evidence itself instead of delegating the stage body to the assigned specialist or deterministic tool.
- Safer target pattern: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

## WFLOW004

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: When implementation gating depends on `status` instead of lifecycle `stage`, or unknown stages are not rejected up front, weaker models start probing the state machine instead of following it.
- Safer target pattern: Validate every requested stage/status pair through one explicit lifecycle contract, reject unsupported stages, and gate implementation on `ticket.stage == plan_review` plus workflow-state approval.

## WFLOW005

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: If generic artifact surfaces can create smoke-test artifacts, a weaker model can bypass executed validation and publish closeout-ready proof that no deterministic tool produced.
- Safer target pattern: Reserve smoke-test artifacts to `smoke_test`, and make the plugin plus transition guidance reject generic PASS-proof fabrication while keeping optional handoff artifacts consistent with docs-lane ownership.

## SKILL002

- Surface: project-skill-bootstrap and agent-prompt-engineering surfaces
- Root cause: When the local workflow explainer omits transition guidance, contradiction-stop rules, artifact ownership, or command boundaries, agents fall back to guess-and-check against the tools.
- Safer target pattern: Make `ticket-execution` the canonical lifecycle explainer: require transition guidance, explicit stop conditions, specialist-owned stage artifacts, `smoke_test`-only smoke proof, and blocker returns instead of fabricated PASS evidence.

## WFLOW006

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: Without explicit transition guidance, contradiction-stop behavior, artifact-ownership rules, and command boundaries, the coordinator has to infer the state machine and may start authoring artifacts or testing workaround transitions itself.
- Safer target pattern: Tell the team leader to route from `ticket_lookup.transition_guidance`, stop after repeated lifecycle errors, leave stage artifacts to the owning specialist, and keep slash commands human-only.

