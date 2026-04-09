# Validation Log

## Scafforge Fixes Validated

| Fix | Validation Method | Result | Date |
|-----|------------------|--------|------|
| hasPendingRepairFollowOn import (686cc74a) | Repair + agent launch on all 3 repos | Tool calls work | 2026-04-09 |
| Copytree .venv exclusion (6e9bb3dc) | Repair runs on GPTTalker (has .venv) | No crash | 2026-04-09 |
| Model prefix stripping (7ead92e0) | Inspect rendered opencode.jsonc | Correct model string | 2026-04-09 |
| Provenance round-trip (03adb917) | Inspect rendered surfaces after repair | Correct stack labels | 2026-04-09 |
| REMED-RELEASE-GATE idempotency (c8bb368f) | Re-run repair on spinner/glitch | No crash | 2026-04-09 |
| managed_blocked error message (9460cc63) | Glitch agent self-unblocked immediately | repair_follow_on_refresh used | 2026-04-09 |
| RC-001 managed_blocked enforcement (906dc002) | GPTTalker agent blocked correctly | BLOCKER thrown | 2026-04-09 |
| RC-002 deterministic-refresh (906dc002) | Inspect workflow state after repair | No polluted stages | 2026-04-09 |
| CONFIG audit (c7546b95) | Audit runs on all 3 repos | Findings generated | 2026-04-09 |

## Downstream Agent Execution

### GPTTalker Agent Runs

| Run | Time | Outcome | Key Events |
|-----|------|---------|------------|
| Run 1 (pre-import-fix) | 13:29 | FAILED | hasPendingRepairFollowOn undefined |
| Run 2 (post-import-fix) | 13:29 | FAILED | managed_blocked — old error message |
| Run 3 (improved message) | 13:36 | IN PROGRESS | Unblocked, identified migration bug, delegating to implementer |

### Spinner Agent Runs

| Run | Time | Outcome | Key Events |
|-----|------|---------|------------|
| Run 1 (pre-import-fix) | 13:29 | FAILED | hasPendingRepairFollowOn undefined |
| Run 2 (improved message) | 13:36 | IN PROGRESS | Self-unblocked, attempting Godot export |

### Glitch Agent Runs

| Run | Time | Outcome | Key Events |
|-----|------|---------|------------|
| Run 1 (pre-import-fix) | 13:29 | FAILED | hasPendingRepairFollowOn undefined |
| Run 2 (improved message) | 13:37 | IN PROGRESS | Self-unblocked via repair_follow_on_refresh, working on REMED-004 |
