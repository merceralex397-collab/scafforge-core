# Scafforge Process Failures

## Chronology Reconstruction

### 1. Post-repair baseline already remained incomplete

- The last successful repair verification pack was `diagnosis/20260328-131434`.
- Canonical workflow state after that repair still truthfully kept `pending_process_verification: true`.
- That was acceptable only if the managed restart layer continued to expose one truthful next action.

### 2. `session4.md` resumed against canonical state correctly at first

- The operator explicitly instructed the agent to treat `tickets/manifest.json` plus `.opencode/state/workflow-state.json` as canonical.
- The session correctly reconfirmed:
  - `repair_follow_on.outcome: source_follow_up`
  - `pending_process_verification: true`
  - bootstrap `ready`
  - active ticket `EXEC-011` already `done`

### 3. `ticket_lookup` exposed that process verification no longer needed more done-ticket work

- In `session4.md`, `ticket_lookup` returned:
  - `transition_guidance.next_action_kind: "noop"`
  - `recommended_action: "Ticket is already closed."`
  - `process_verification.affected_done_tickets: []`
- That means the legal workflow-level next step was clearing the pending process-verification flag, not running another backlog-verification pass.

### 4. Managed tooling then created a catch-22

- The agent called `ticket_update` to clear `pending_process_verification`.
- The stage gate rejected that mutation because the target ticket lacked a write lease.
- The agent then called `ticket_claim`.
- The claim failed because the same ticket was already closed.

This is the critical package failure:

- `ticket_update` is the advertised mutation path for `pending_process_verification`
- `ticket_update` itself knows how to validate the clear operation against `ticketsNeedingProcessVerification`
- but the stage-gate layer blocks that workflow-level mutation behind a closed-ticket write lease that cannot be obtained

### 5. The managed handoff path then accepted false clean-state prose

- After hitting the catch-22, the session called `handoff_publish` with an explicit `next_action` saying:
  - all tickets complete and verified
  - system is in a clean state
  - the only remaining issue is a tooling constraint
- `handoff_publish` accepted that message and republished it into:
  - `START-HERE.md`
  - `.opencode/state/latest-handoff.md`
- The current repo still contains that contradictory result.

## Root Causes

### WFLOW-A — Workflow-level process-verification clearing is routed through a ticket-level lease contract

- Current code:
  - `.opencode/tools/ticket_update.ts` supports `pending_process_verification`
  - `.opencode/plugins/stage-gate-enforcer.ts` unconditionally requires a target-ticket write lease for every `ticket_update`
  - `.opencode/plugins/stage-gate-enforcer.ts` also forbids claiming a closed ticket
- Effect:
  - once the active foreground ticket is closed, the legal clear path can become unreachable even when `affected_done_tickets` is empty

### WFLOW-B — Handoff validation does not reject canonical-state contradictions

- Current code:
  - `.opencode/lib/workflow.ts::validateHandoffNextAction()` only blocks a narrow set of readiness and “single cause” claims
  - it does not reject “clean state” prose while `pending_process_verification` is still true
  - it does not compare an explicit `next_action` override against canonical restart truth
- Effect:
  - weaker models can publish authoritative restart text that contradicts canonical workflow state

### WFLOW-C — Restart rendering uses the wrong trust signal

- Current code:
  - `.opencode/lib/workflow.ts::ticketNeedsProcessVerification()` correctly treats current `backlog-verification` artifacts as clearing process-verification need
  - `.opencode/lib/workflow.ts::renderStartHere()` does not use that logic for `done_but_not_fully_trusted`
  - it instead derives that list directly from `verification_state !== trusted/reverified`
- Effect:
  - the restart surfaces keep telling the operator that 33 tickets are still not fully trusted even after backlog-verification artifacts exist for all 33
  - this pushes weaker models toward unnecessary reverification loops and stale blocker narratives

## Why The Previous Audit/Repair Cycle Failed

The previous cycle failed because it diagnosed only the published contradiction, not the package behaviors that recreate it.

- Prior diagnosis:
  - treated the subject repo restart contradiction as the live problem
  - kept `package_work_required_first: false`
- What was missed:
  - `handoff_publish` was still allowed to override canonical next action with contradictory prose
  - `renderStartHere` was still deriving distrust from `verification_state` instead of process-verification truth
  - `ticket_update` clearing remained blocked by the stage gate on a closed ticket

So the earlier repair refreshed this repo to the same flawed managed contract.

## Classification

- `WFLOW-A`: package defect
- `WFLOW-B`: package defect
- `WFLOW-C`: package defect
- current contradictory restart prose in this subject repo: downstream manifestation of those package defects

## Final Failure Statement

This is not another case where the repo merely “drifted” after a correct repair.
The managed package still contains logic that:

1. blocks the legal workflow-level clear path
2. allows contradictory restart publication
3. computes restart trust exposure from the wrong signal

That is why repeated subject-repo audit+repair churn has not solved the weaker-agent blockage.
