# Scafforge Process Failures

## Scope

- Subject repo: `/home/pc/projects/GPTTalker`
- Diagnosis timestamp: `2026-03-26T03:12:28Z`
- Scope of this report:
  - map the validated Report 1 findings to managed workflow surfaces
  - explain why the March 25, 2026 audit-to-repair cycle did not prevent the next stall
  - separate historical transcript truth from current repo truth

## Failure Map

### PF-01

- Linked Report 1 finding id: `R1-F1`
- Implicated surfaces:
  - managed `START-HERE.md` block
  - `.opencode/state/context-snapshot.md`
  - handoff publication / restart-surface regeneration path
- Ownership class: `generated-repo managed-surface drift`
- How the workflow allowed the issue through:
  - the repo changed canonical bootstrap and lease state after the repair, but the derived restart surfaces were not regenerated
  - the next session therefore resumed from a false claim set: bootstrap ready, no active leases, workflow deadlock repaired

### PF-02

- Linked Report 1 finding id: `R1-F2`
- Implicated surfaces:
  - `.opencode/tools/ticket_lookup.ts`
  - `.opencode/agents/gpttalker-team-leader.md`
  - `.opencode/skills/ticket-execution/SKILL.md`
- Ownership class: `Scafforge package defect`
- How the workflow allowed the issue through:
  - bootstrap failure was treated as advisory context instead of as the sole legal next action
  - the coordinator was left to infer whether planning, leases, or shell workarounds could resume normal lifecycle progress

### PF-03

- Linked Report 1 finding ids: `R1-F3`, `R1-F4`
- Implicated surfaces:
  - `.opencode/plugins/stage-gate-enforcer.ts`
  - `.opencode/tools/ticket_claim.ts`
  - `.opencode/tools/_workflow.ts`
  - `.opencode/agents/gpttalker-team-leader.md`
  - `.opencode/agents/gpttalker-planner.md`
  - `docs/process/workflow.md`
- Ownership class: `Scafforge package defect`
- How the workflow allowed the issue through:
  - planning artifacts and stage mutations require a write lease in the plugin
  - write leases require `write_lock: true`
  - non-Wave-0 tickets cannot obtain a pre-bootstrap write lock while bootstrap is failed
  - the documented planning path still says “write and register the planning artifact before moving into plan_review”
  - the coordinator therefore had no executable legal path and started searching for bypasses, then attempted to author the planning artifact itself

### PF-04

- Linked Report 1 finding id: `R1-F5`
- Implicated surfaces:
  - audit diagnosis contract
  - repair contract / repair-history handling
  - restart-surface publishing path
- Ownership class: `Scafforge package defect`
- How the workflow allowed the issue through:
  - the repo had already been repaired at `2026-03-25T22:19:11Z` after `diagnosis/20260325-221327`
  - later same-day packs at `20260325-222852` and `20260325-223044` still showed unresolved workflow problems
  - despite that, the managed restart surfaces continued to present the workflow as repaired and ready for ordinary ticket work
  - the diagnosis flow therefore failed to close the loop between post-repair evidence and the restart narrative consumed by the next session

### PF-05

- Linked Report 1 finding id: `R1-F6`
- Implicated surfaces:
  - generated implementation and QA enforcement surfaces
  - subject repo source backlog
- Ownership class: `subject-repo source bug`
- How the workflow allowed the issue through:
  - historical done tickets and current wave routing still coexist with reproduced full-suite failures
  - until the workflow layer is trustworthy again, source failures and process failures risk contaminating one another in closeout reasoning

## Ownership Classification

- `R1-F1`: `generated-repo managed-surface drift`
- `R1-F2`: `Scafforge package defect`
- `R1-F3`: `Scafforge package defect`
- `R1-F4`: `Scafforge package defect`
- `R1-F5`: `Scafforge package defect`
- `R1-F6`: `subject-repo source bug`

## Root Cause Analysis

### Root Cause A: The latest repair fixed earlier findings but left the repo with stale restart truth

- `diagnosis/20260325-221327` identified `SESSION003`, `WFLOW009`, `EXEC003`, and `WFLOW008`.
- repair history then records a managed workflow repair at `2026-03-25T22:19:11Z`.
- later that same evening, `diagnosis/20260325-222852` and `diagnosis/20260325-223044` still reported unresolved workflow-layer issues.
- the repo’s restart surfaces nevertheless kept saying the deadlock was repaired and bootstrap was ready.
- result:
  - the next session resumed from a repo-authored falsehood, not just from an unlucky model inference

### Root Cause B: Bootstrap failure was not elevated into a hard lifecycle stop

- Current canonical truth is explicit:
  - `.opencode/state/workflow-state.json:323` records `bootstrap.status = failed`
  - the latest bootstrap artifact records `Overall Result: FAIL`
- Operational guidance is not explicit:
  - `ticket_lookup.ts:41-48` still tells a planning ticket to write the planning artifact
  - the team-leader prompt and `ticket-execution` mention bootstrap, but do not suspend normal lifecycle routing when bootstrap is failed
- result:
  - the coordinator keeps reasoning about the lifecycle when it should be doing only bootstrap recovery

### Root Cause C: The planning path is internally contradictory

- The managed workflow docs and prompts imply:
  - planning artifact first
  - then `plan_review`
  - leases only for write-capable implementation or docs closeout work
- The live tool/plugin contract enforces:
  - `artifact_write` requires a write lease
  - `ticket_update` requires a write lease
  - only `write_lock: true` counts as a write lease
  - `ticket_claim` with `write_lock: true` requires bootstrap ready unless the ticket is Wave 0 and there are no existing leases
- result:
  - for a failed-bootstrap non-Wave-0 ticket, the repo can demand a planning artifact while simultaneously denying the legal mutation path needed to create or advance it

### Root Cause D: The workflow contract still makes the coordinator absorb contradictions instead of rejecting them cleanly

- The transcript shows the team leader:
  - reading the contradiction-stop rules
  - continuing to search for bypasses anyway
  - eventually attempting planner-owned artifact authorship
- that is not only a prompt issue and not only an agent issue
- it is the predictable output of a repo that:
  - exposes contradictory write/lease semantics
  - leaves bootstrap failure as a soft warning
  - serves stale restart claims that say the deadlock is already fixed

### Historical vs Current Repo Truth

- Historical transcript truth:
  - `continuallylocked.md` proves bypass-seeking and coordinator artifact authorship
- Current repo truth:
  - restart surfaces are still stale
  - bootstrap is still failed
  - the planning/write-lease contradiction is still present in the live managed surfaces
- Inference:
  - even if the exact `uv sync --locked` behavior from the transcript was partly historical, the repo still contains a live workflow defect sufficient to recreate the same stall class
