# Scafforge State Cleanup - 2026-03-27

## Purpose

This note records the workflow-state diagnosis and cleanup performed after `cc12.md` captured a confusing mixed-state resume sequence.

## What Was Diagnosed

- `cc12.md` contained stale historical state and should not be treated as a canonical execution surface.
- Current canonical state had already moved the foreground ticket to `EXEC-013`, but the repo still carried leftover `EXEC-011` workflow debris.
- The main live problems were:
  - stale `EXEC-011` write lease left in `.opencode/state/workflow-state.json`
  - incomplete split bookkeeping from `EXEC-011` into child tickets
  - missing `EXEC-014`
  - `EXEC-013` present without correct linkage back to `EXEC-011`
  - derived restart surfaces lagging behind canonical state
  - workflow contract gap for creating split follow-up tickets from an open parent

## Canonical State Changes

- Cleared the stale `EXEC-011` lane lease from `.opencode/state/workflow-state.json`.
- Kept `EXEC-013` as the active foreground ticket in planning.
- Reclassified `EXEC-011` as a blocked split parent instead of an active implementation lane.
- Linked `EXEC-011` to `EXEC-013` and `EXEC-014` through `follow_up_ticket_ids`.
- Added the missing `EXEC-014` ticket.
- Corrected `EXEC-013` to reflect the live alias-modernization Ruff subset:
  - `UP017`
  - `UP035`
  - `UP041`
- Updated the registered `EXEC-011` planning artifact path to the canonical stage directory path:
  - `.opencode/state/plans/exec-011-planning-plan.md`

## Restart Surface Updates

Regenerated and reconciled:

- `START-HERE.md`
- `.opencode/state/context-snapshot.md`
- `.opencode/state/latest-handoff.md`
- `.opencode/meta/bootstrap-provenance.json`

These updates removed the stale `EXEC-011` lease from restart prose, clarified that `EXEC-011` is a split parent, and kept `EXEC-013` as the correct foreground ticket.

## Workflow Contract Fix

Added an explicit `split_scope` source mode so Scafforge/OpenCode can create linked child tickets from an open parent ticket without abusing `process_verification` or falling back to `net_new_scope`.

Files updated for that contract change:

- `.opencode/lib/workflow.ts`
- `.opencode/tools/ticket_create.ts`
- `.opencode/plugins/stage-gate-enforcer.ts`
- `docs/process/tooling.md`
- `docs/process/workflow.md`
- `AGENTS.md`

## Ticket Files Updated

- `tickets/manifest.json`
- `tickets/BOARD.md`
- `tickets/EXEC-011.md`
- `tickets/EXEC-013.md`
- `tickets/EXEC-014.md`

## Live Ruff State At Time Of Cleanup

The repo still had 49 Ruff violations when checked during diagnosis. This cleanup did not resolve the code issues themselves; it repaired workflow routing and ticket accuracy so the next agent can continue correctly.

Observed rule counts:

- `B007`: 1
- `B008`: 8
- `C401`: 3
- `C414`: 1
- `E402`: 1
- `F401`: 11
- `F541`: 2
- `F841`: 1
- `I001`: 16
- `UP017`: 3
- `UP035`: 1
- `UP041`: 1

## Important Notes For The Next Agent

- Do not resume work from `cc12.md`.
- Treat `tickets/manifest.json` and `.opencode/state/workflow-state.json` as canonical.
- Continue from `EXEC-013` first.
- Treat `EXEC-011` as a blocked parent ticket, not the active implementation lane.
- After `EXEC-013` is complete, continue into `EXEC-014`.
- Use `split_scope` if another open-ticket split is needed.

## Validation Performed

- Parsed edited JSON files successfully after the cleanup.
- Confirmed canonical and derived workflow surfaces now agree on `EXEC-013`.
- Confirmed the stale `EXEC-011` lease was removed.

## Not Done Here

- No Ruff fixes were implemented.
- No TypeScript build/test pass was run for the workflow tool changes.
- No commit was created in this step.
