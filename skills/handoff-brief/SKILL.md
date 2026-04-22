---
name: handoff-brief
description: Create concise project handoff artifacts, especially a top-level START-HERE document and resume context for the next session or machine. Use when scaffolding finishes, a milestone closes, or long-running autonomous work needs a compact restart surface.
---

# Handoff Brief

Use this skill to create a restartable handoff surface with actual project state.

The top-level handoff must stay derived from canonical state. `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` summarize the repo; they do not outrank `tickets/manifest.json` or `.opencode/state/workflow-state.json`.

## Procedure

### 1. Gather current state

Read these files to understand current project state:
- `docs/spec/CANONICAL-BRIEF.md` — what the project is
- `tickets/manifest.json` — current ticket state
- `tickets/BOARD.md` — work queue overview
- `.opencode/state/workflow-state.json` — current workflow state
- `.opencode/meta/bootstrap-provenance.json` — how the scaffold was generated

### 2. Write START-HERE.md

Use the template in `assets/templates/START-HERE.template.md` as a starting structure, but populate it with ACTUAL project state:

**What This Repo Is** — actual project summary from the canonical brief

**Current State** — actual current state:
- What has been completed
- What is in progress
- What is blocked

**Read In This Order** — actual reading order for this project:
1. README.md
2. AGENTS.md
3. docs/spec/CANONICAL-BRIEF.md
4. docs/process/workflow.md
5. tickets/manifest.json
6. tickets/BOARD.md

**Current Or Next Ticket** — the actual active ticket or recommended next ticket from the manifest

**Generation Status** — the current generation state and whether the repo is ready for the first development handoff

**External Orchestration Boundary** — the canonical files an adjacent orchestration service may read, the repo truth it must not write directly, and the PR boundary for downstream autonomous phases

**Pre-Handoff Proof** — the current-cycle proof status that justifies the handoff narrative, including whether the proof passed, failed, or is still missing

**Bootstrap Note** — machine-specific bootstrap warning (always include this):

> ⚠️ **Bootstrap is machine-specific.** Bootstrap was last verified on a specific host. If you are on a DIFFERENT machine or a fresh git clone, run `environment_bootstrap` FIRST before picking up any ticket. Tools will throw `"Bootstrap stale. Run environment_bootstrap."` if this is needed — that is the correct signal, not an error.

**Post-Generation Audit Status** — optional later audit or repair state, if any exists

**Resume Semantics** — the current resume status, the repo-local trigger when repair follow-up exists, and the reminder that package-defect wait states stay outside canonical repo state

**Known Risks** — actual risks and open questions from the canonical brief

**Next Action** — the exact next useful action for whoever opens this repo next

### 3. Validate

Verify the handoff:
- START-HERE.md exists and has all sections populated with real content
- `.opencode/state/latest-handoff.md` exists and agrees with the same canonical state
- The referenced ticket actually exists in the manifest
- The reading order files all exist
- The next action is specific and actionable
- The next action matches the one legal first move exposed by canonical state when bootstrap is not yet ready
- If current-cycle handoff proof is failed or missing, START-HERE does not claim the repo is ready for continued development
- if `.opencode/meta/pivot-state.json` exists, the handoff surfaces reflect the current pivot state truthfully
- The handoff is a truthful restart surface bounded by current evidence, even when later audit, repair, or backlog reverification is still pending
- external orchestration guidance stays read-only over canonical repo truth and does not hide package-defect wait states inside repo workflow state

## Output contract

Before leaving this skill, confirm all of these are true:
- `START-HERE.md` exists and uses canonical manifest/workflow-state facts rather than stale narrative memory
- `.opencode/state/latest-handoff.md` exists and agrees with `START-HERE.md` on active ticket, bootstrap status, and pending process verification
- active pivot state is reflected in `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` when present
- the read order lists `tickets/manifest.json` before `tickets/BOARD.md`
- the next action is actionable and does not overclaim readiness beyond current evidence
- the handoff proves immediate continuation rather than only surface agreement

## Repair follow-on artifact

When this skill runs as a `scafforge-repair` follow-on closeout, read `.opencode/meta/repair-follow-on-state.json` and, after the restart surfaces are actually refreshed for the current repair cycle, write:

- `.opencode/state/artifacts/history/repair/handoff-brief-completion.md`

Use this minimal shape so the public repair runner can auto-recognize `handoff-brief` completion for the current repair cycle on the next run:

```md
# Repair Follow-On Completion

- completed_stage: handoff-brief
- cycle_id: <cycle_id from .opencode/meta/repair-follow-on-state.json>
- completed_by: handoff-brief

## Summary

- Refreshed START-HERE.md, context-snapshot.md, and latest-handoff.md for the current repair cycle.
```

Do not emit this artifact speculatively. Only write it once the handoff refresh work is actually complete for the current repair cycle.

## After this step

The scaffold flow is complete. Return to `../scaffold-kickoff/SKILL.md` step 10 for the done checklist.

## Rules

- This skill is a closeout and restart refiner, not a scaffold entrypoint
- Populate with actual project state, not template placeholders
- Keep it concise — this is a restart surface, not comprehensive documentation

## References

- `references/handoff-checklist.md` for the required sections
- `assets/templates/START-HERE.template.md` for the base template
