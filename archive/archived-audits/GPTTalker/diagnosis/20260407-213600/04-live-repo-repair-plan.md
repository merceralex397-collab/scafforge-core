# Live Repo Repair Plan

- **Subject repo:** `/home/pc/projects/GPTTalker`
- **Diagnosis timestamp:** 2026-04-07T21:36:00Z

## Preconditions

- User has confirmed all permission gates are granted for full-scale repair
- Model is confirmed as `minimax-coding-plan/MiniMax-M2.7` — do not change
- The prior repair cycle auto-detected completion of `opencode-team-bootstrap` and `agent-prompt-engineering` without executing them — those stages must be re-run for real
- No Scafforge package changes are required before this repair (the package rewrite has already happened; the agents just weren't regenerated from it)
- The `repair-follow-on-state.json` still shows `ticket-pack-builder` as `currently_required: true` — that must remain addressed after agent repair

## Package Changes Required First

**None.** The Scafforge package rewrite has already occurred. The problem is that the repo-local agents were never regenerated from the new package. Repair can proceed directly against the subject repo.

## Post-Update Repair Actions

These repairs must be applied in order. All are safe managed-surface replacements. None change project intent or source code.

---

### R-001 — Regenerate all agents from current template (opencode-team-bootstrap)

- **Linked findings:** AGENT-001, AGENT-002, AGENT-003, AGENT-004, AGENT-005, AGENT-006, AGENT-007, AGENT-008, STATE-001
- **Action type:** generated-repo remediation — managed-surface replacement
- **Files affected:** All 21 files under `.opencode/agents/`
- **What must happen:**
  - Run `opencode-team-bootstrap` skill fully — do not auto-detect completion
  - The skill must regenerate every agent from the current template, preserving:
    - The model string `minimax-coding-plan/MiniMax-M2.7` throughout (do not revert to M2.5)
    - Project-specific task routing in team-leader (`gpttalker-implementer-hub`, `gpttalker-implementer-node-agent`, `gpttalker-implementer-context`, `gpttalker-implementer`, and `gpttalker-lane-executor`)
    - Project-specific bash allowlists in implementer agents (python, pytest, uv, pip, ruff)
    - Project-specific skills (`context-intelligence`, `mcp-protocol`, `node-agent-patterns`) where referenced
    - Implementer domain descriptions (hub, node-agent, context are project-specific)
  - The following must be freshly applied from the current template:
    - Team leader: stop conditions, advancement rules, ticket ownership, contradiction resolution, bootstrap recovery rules, `"explore": allow` in task, stack-specific delegation brief fields
    - Reviewer-code: `review-audit-bridge` skill, compile-check bash entries, execution-proof rules
    - Reviewer-security: `review-audit-bridge` skill, lease-blocked return rule
    - Tester-QA: `review-audit-bridge` skill, lease-blocked return rule, updated body reference
    - Ticket-creator: `ticket_reconcile: allow`, updated description and body, reconciliation rules
    - Planner: `"explore": allow` in task
    - Plan-review: lease-blocked return rule
    - Backlog-verifier: smoke-test artifact check, lease-blocked return rule
- **Should `scafforge-repair` run?** Yes — this is the next step
- **Target repo:** Subject repo (GPTTalker)

---

### R-002 — Run agent-prompt-engineering pass after regeneration

- **Linked findings:** AGENT-001 (stop conditions, contradiction resolution)
- **Action type:** generated-repo remediation — prompt hardening
- **What must happen:**
  - After `opencode-team-bootstrap` completes, run `agent-prompt-engineering` skill to verify that the prompts and the local workflow skill describe the same contract
  - Confirm that the team leader stop conditions, advancement rules, and contradiction resolution rules are consistent with `ticket-execution` skill and `docs/process/workflow.md`
- **Target repo:** Subject repo (GPTTalker)

---

### R-003 — Update repair-execution.json and repair-follow-on-state.json

- **Linked findings:** STATE-001
- **Action type:** generated-repo remediation — provenance update
- **What must happen:**
  - Append a new repair history entry to `.opencode/meta/bootstrap-provenance.json` recording this repair
  - Update `.opencode/meta/repair-execution.json` to show `opencode-team-bootstrap` and `agent-prompt-engineering` as genuinely completed (not auto-detected)
  - Set `pending_process_verification: true` in `.opencode/state/workflow-state.json` so the backlog verifier re-checks previously completed tickets against the updated agent contract
  - Regenerate `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md`
- **Target repo:** Subject repo (GPTTalker)

---

### R-004 — Address ticket-pack-builder follow-up (currently_required: true)

- **Linked findings:** repair-execution.json `ticket-pack-builder` stage
- **Action type:** generated-repo remediation — ticket follow-up
- **What must happen:**
  - The `repair-follow-on-state.json` shows `ticket-pack-builder` as `currently_required: true` with finding code `EXEC001`
  - After agent repair, route the EXEC001 finding through `ticket-pack-builder` to ensure remediation tickets exist for any remaining source-layer execution failures
- **Target repo:** Subject repo (GPTTalker)

## Ticket Follow-Up

| Proposed ticket id | Title | Route | Source finding |
|---|---|---|---|
| REMED-AGENTS-001 | Regenerate `.opencode/agents/` from current package template | `scafforge-repair` → `opencode-team-bootstrap` | AGENT-001 through AGENT-008 |
| REMED-AGENTS-002 | Apply `agent-prompt-engineering` hardening pass after agent regeneration | `scafforge-repair` → `agent-prompt-engineering` | AGENT-001 |

No new source-layer tickets are needed. The EXEC001 ticket from the prior repair cycle should be evaluated after agent repair is complete.

## Reverification Plan

1. After `scafforge-repair` completes R-001 through R-003:
   - Rerun `audit_repo_process.py` with `--diagnosis-kind post_repair_verification`
   - Confirm AGENT-001 through AGENT-008 findings are gone
   - Confirm `review-audit-bridge` is present in reviewer-code, reviewer-security, and tester-qa skill blocks
   - Confirm ticket-creator has `ticket_reconcile: allow`
   - Confirm team leader has stop conditions, advancement rules, and contradiction resolution blocks
   - Confirm model string remains `minimax-coding-plan/MiniMax-M2.7` throughout
2. After verifying agents, address R-004 (ticket-pack-builder follow-up for EXEC001)
3. After ticket-pack-builder follow-up is complete, clear `pending_process_verification` only after backlog verifier confirms affected done tickets

## Summary

No Scafforge package work is required before repair. All repair actions are safe managed-surface replacements. The primary repair is a full agent regeneration from the current template with the `opencode-team-bootstrap` skill, followed by an `agent-prompt-engineering` hardening pass. The model string `MiniMax-M2.7` must be preserved throughout. `scafforge-repair` should run now.
