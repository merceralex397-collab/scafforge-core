---
name: ticket-execution
description: Follow the required lifecycle for Glitch tickets, from planning through smoke-tested closeout, with bootstrap-first routing and evidence-backed stage proof.
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
- the team leader owns `ticket_claim` and `ticket_release`; specialists work only inside the already-active ticket lease
- use `ticket_update` for stage movement; do not probe alternate stage or status values
- when `ticket_update` returns the same lifecycle error twice, stop and return a blocker
- stage artifacts belong to the specialist for that stage:
  - planner writes `planning`
  - implementer writes `implementation`
  - reviewers write `review`
  - QA writes `qa`
  - `smoke_test` is the only legal producer of `smoke-test`
- if execution or validation cannot run, return a blocker or open risk; do not convert expected results into PASS evidence
- slash commands are human entrypoints, not internal autonomous workflow tools

Glitch-specific requirements:

- treat mobile control readability, movement feel, and glitch telegraphing as correctness-critical concerns
- when a ticket changes movement, checkpoints, hazards, controls, or glitch events, require the artifact to name the affected gameplay surface explicitly
- if the ticket acceptance criteria already define executable Godot or scene-specific smoke commands, treat those commands as canonical smoke scope
- prefer headless Godot startup, import, and project checks when no richer test harness exists yet

Transition contract:

- `planning`:
  - required proof before exit: a registered planning artifact
  - next legal transition: `ticket_update stage=plan_review`
- `plan_review`:
  - required proof before exit: the plan exists and approval is recorded in workflow state while the ticket remains in `plan_review`
  - first legal approval step: `ticket_update stage=plan_review approved_plan=true`
  - next legal transition after approval: `ticket_update stage=implementation`
- `implementation`:
  - required proof before exit: a registered implementation artifact with executable evidence
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
