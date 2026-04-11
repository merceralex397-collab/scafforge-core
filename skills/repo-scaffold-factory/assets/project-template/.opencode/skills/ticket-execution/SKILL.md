---
name: ticket-execution
description: Follow the required ticket lifecycle for this repo. Use when an agent is advancing a ticket through planning, review, implementation, QA, deterministic smoke testing, and closeout and needs the repo-specific stage rules.
---

# Ticket Execution

Before enforcing the lifecycle, call `skill_ping` with `skill_id: "ticket-execution"` and `scope: "project"`.

Required order:

1. ticket lookup
2. planning
3. plan review
4. implementation
5. code review
6. security review when relevant
7. QA
8. deterministic smoke test
9. handoff and closeout

Core rules:

- resolve the ticket through `ticket_lookup` first and read `transition_guidance` before calling `ticket_update`
- if `ticket_lookup.bootstrap.status` is not `ready`, stop normal lifecycle routing, run `environment_bootstrap`, then rerun `ticket_lookup` before any `ticket_update`
- if bootstrap still is not `ready` after that rerun, return a blocker; do not improvise raw shell installation or lifecycle workarounds
- if repeated bootstrap proofs show the same command trace but it still omits the dependency-group or extra flags the repo layout requires, stop retrying and route a managed bootstrap defect instead of bypassing `environment_bootstrap`
- the team leader owns `ticket_claim` and `ticket_release`; the team leader claims and releases write leases; specialists work inside the already-active ticket lease and return a blocker if no lease exists
- use `ticket_update` for stage movement; do not probe alternate stage or status values to see what passes
- when `ticket_update` returns the same lifecycle error twice, stop and return a blocker instead of inventing a workaround
- stage artifacts belong to the specialist for that stage:
  - planner writes `planning`
  - implementer writes `implementation`
  - reviewers write `review`
  - QA writes `qa`
  - `smoke_test` is the only legal producer of `smoke-test`
- if the ticket acceptance criteria already define executable smoke commands, treat those commands as canonical smoke scope; let `smoke_test` infer them or pass the exact canonical command instead of improvising broader full-suite smoke or ad hoc narrower `test_paths`
- if execution or validation cannot run, return a blocker or open risk; do not convert expected results into PASS evidence
- do not claim that a command ran unless its output is present in the canonical artifact
- slash commands are human entrypoints, not internal autonomous workflow tools

Transition contract:

- `planning`:
  - required proof before exit: a registered planning artifact
  - next legal transition: `ticket_update stage=plan_review`
- `plan_review`:
  - required proof before exit: the plan exists and approval is recorded in workflow state while the ticket remains in `plan_review`
  - first legal approval step: `ticket_update stage=plan_review approved_plan=true`
  - do not combine initial approval and the implementation transition in one call
  - next legal transition after approval: `ticket_update stage=implementation`
- `implementation`:
  - required proof before exit: a registered implementation artifact with compile, syntax, import, or test output
  - next legal transition: `ticket_update stage=review`
- `review`:
  - required proof before exit: at least one registered review artifact
  - next legal transition: `ticket_update stage=qa`
  - latest review verdict must be PASS or APPROVED; FAIL, REJECT, BLOCKED, or an unclear verdict must route back to implementation or manual inspection before QA
- `qa`:
  - required proof before exit: a registered QA artifact with raw command output
  - next legal transition: `ticket_update stage=smoke-test`
  - latest QA verdict must be PASS or APPROVED; FAIL, REJECT, BLOCKED, or an unclear verdict must route back to implementation or manual inspection before smoke-test
- `smoke-test`:
  - required proof before exit: a current smoke-test artifact produced by `smoke_test`
  - next legal transition: `ticket_update stage=closeout`
- `closeout`:
  - required proof before exit: a passing smoke-test artifact
  - expected final state: `status=done`

Failure recovery paths:

- Review FAIL, REJECT, or BLOCKED: route back to `implementation`, address the review findings, then return to `review`
- Review verdict unclear: stop progression and inspect the current review artifact manually before any `ticket_update`
- QA FAIL, REJECT, or BLOCKED: route back to `implementation`, fix the QA findings, then return through `review` and `qa`
- QA verdict unclear: stop progression and inspect the current QA artifact manually before any `ticket_update`
- Smoke-test FAIL with `failure_classification: test_failure`: route back to `implementation` and fix the product issue
- Smoke-test FAIL with `failure_classification: missing_executable` or host-surface `runtime_setup`: run `environment_bootstrap` and treat the failure as an environment blocker first
- Smoke-test FAIL with `failure_classification: syntax_error` or `configuration_error`: treat the smoke tool surface as the blocker; do not route that failure straight to implementation

Remediation ticket closeout:

- when a ticket carries `finding_source`, treat it as a remediation or reverification ticket
- identify the original finding code before closeout and rerun the command or check that originally produced that finding
- include the rerun output and whether the original error signature is gone in the closeout evidence
- if the finding-specific rerun still fails, do not close the ticket; route back to implementation with the fresh command output
- if the finding-specific rerun passes, also confirm adjacent quality gates that previously passed still remain green
- for process-remediation or reverification tickets, keep smoke-test scope limited to checks that are valid at the repo's current backlog state; do not broaden smoke into a product boot command that is expected to fail because prerequisite feature tickets are still unfinished

Verification state semantics:

- `suspect`: normal in-flight state, or a ticket returned to implementation after new findings
- `smoke_verified`: a passing smoke-test artifact exists, but closeout has not completed yet
- `trusted`: closeout completed with current passing evidence
- `reverified`: historical completion was re-proven after drift or process-version change
- `invalidated`: accepted historical completion was disproven by later defect intake

Parallel rules:

- keep each ticket sequential through its own stage order
- only advance tickets in parallel when `parallel_safe` is `true`, `overlap_risk` is `low`, and dependencies are already satisfied

Process-change rules:

- if `pending_process_verification` is `true`, verify affected done tickets before trusting their completion
- if `repair_follow_on.outcome` is `managed_blocked`, stop ordinary lifecycle routing and surface the canonical blocker before continuing ticket work
- `repair_follow_on.outcome == source_follow_up` does not by itself block the active open ticket from continuing
- migration follow-up tickets must come from backlog-verifier proof through `ticket_create`, not raw manifest edits
- use `ticket_create(source_mode=split_scope)` when an open or reopened parent ticket needs planned child decomposition
- use `ticket_reconcile` when evidence proves an existing follow-up graph is stale or contradictory
- previously completed tickets are not fully trusted again until backlog verification says so

Bootstrap gate:

- bootstrap readiness is a pre-lifecycle execution gate for every validation-heavy stage
- when bootstrap is `missing`, `failed`, or `stale`, the next required action is `environment_bootstrap`, not a stage transition or non-Wave-0 write claim
- only Wave 0 setup work may claim a write-capable lease before bootstrap is ready
- after bootstrap succeeds, rerun `ticket_lookup` and follow its refreshed `transition_guidance`
