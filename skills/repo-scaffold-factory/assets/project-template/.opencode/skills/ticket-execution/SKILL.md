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
- use `ticket_update` for stage movement; do not probe alternate stage or status values to see what passes
- when `ticket_update` returns the same lifecycle error twice, stop and return a blocker instead of inventing a workaround
- stage artifacts belong to the specialist for that stage:
  - planner writes `planning`
  - implementer writes `implementation`
  - reviewers write `review`
  - QA writes `qa`
  - `smoke_test` is the only legal producer of `smoke-test`
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
- `qa`:
  - required proof before exit: a registered QA artifact with raw command output
  - next legal transition: `ticket_update stage=smoke-test`
- `smoke-test`:
  - required proof before exit: a current smoke-test artifact produced by `smoke_test`
  - next legal transition: `ticket_update stage=closeout`
- `closeout`:
  - required proof before exit: a passing smoke-test artifact
  - expected final state: `status=done`

Parallel rules:

- keep each ticket sequential through its own stage order
- only advance tickets in parallel when `parallel_safe` is `true`, `overlap_risk` is `low`, and dependencies are already satisfied

Process-change rules:

- if `pending_process_verification` is `true`, verify affected done tickets before trusting their completion
- migration follow-up tickets must come from backlog-verifier proof through `ticket_create`, not raw manifest edits
- previously completed tickets are not fully trusted again until backlog verification says so
