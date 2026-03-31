# Scafforge Session Analysis

## Overview

These files document real agent coding sessions using Scafforge, both successful and problematic.

## Contents

### spinner/

A simple Android toddler toy/game project generated as a greenfield Scafforge project. The project uses Godot 4.x with GDScript targeting Android 2D export.

**Session logs:**
- `spinner-kickoff.jsonl` — Initial greenfield scaffold session. Codex ran `scaffold-kickoff`, read all downstream skill files, presented a blocking-decision packet to the user, then received decisions (project name "Spinner", MiniMax-M2.7 for all agents). Session was paused waiting for decisions to be confirmed.

**Blocked session exports (spinner1.md, spinner2.md):**
- `spinner1.md` — Session export showing the Spinner agent working through SETUP-001 (environment bootstrap) and SETUP-002 (Godot project skeleton). Contains detailed trace of the smoke_test tool failures and fixes. The agent got stuck on:
  1. smoke_test command override parsing — `!` prefix being treated as missing executable
  2. Regex pattern mismatch (`bootstrap.status.*ready` vs actual `status: ready`)
  3. Ticket state inconsistency between top-level `active_ticket` and workflow `active_ticket`
  4. Planner blocked by artifact_write tool checking wrong `active_ticket` field

- `spinner2.md` — Session export continuing from spinner1.md. Covers CORE-001, CORE-002 completion, then TOY-001 planning/implementation/review. The agent continued to hit the same blocker pattern — when the planner tried to write artifacts, it was blocked because the top-level `active_ticket` was stale/incorrect.

**What we learned from spinner:**
- The `artifact_write` tool resolves active ticket from top-level `active_ticket` field, not from the workflow section — this state inconsistency causes planners to block
- smoke_test command parsing doesn't handle shell operators like `!` or `;` correctly
- grep regex patterns in smoke_test need to match actual file content exactly (`.` in regex = literal dot, not "any character")
- Bounded parallel ticket advancement (TOY-001 + TOY-002) requires careful lease management

### GPTTalker/

- `blocker1.md` — Diagnostic records of blockers encountered during scaffold patching and pivot skill implementation in a GPTTalker repo.

### codex-logs/

Raw Codex CLI session logs (JSONL format) from 2026-03-31:

- `rollout-2026-03-31T02-31-54-*.jsonl` — Session 1: Code review (commit-by-commit review of remediation/repair/pivot branch)
- `rollout-2026-03-31T12-55-02-*.jsonl` — Session 2: Cloudflare Tunnel → ngrok pivot with managed repair
- `rollout-2026-03-31T13-20-07-*.jsonl` — Session 3: Skill bootstrap and ticket-pack-builder repair

## Key Findings

All sessions exhibited common failure patterns:

1. **Token/context waste** — Same files re-read 5+ times
2. **Tool failure without recovery** — `apply_pivot_lineage.py` crashed and agent never adapted
3. **Environment not bootstrapped** — `uv sync` never run before audit, causing false-positive import errors
4. **Didn't follow explicit instructions** — Commit-by-commit review done as file-thematic; "run $skill" turned into extended analysis
5. **Over-engineering simple tasks** — Routine refreshes expanded into multi-phase analysis marathons
6. **Circular reasoning** — Agents second-guessed and re-decided already-made decisions
7. **Ticket state inconsistency** — Top-level `active_ticket` vs workflow `active_ticket` causing artifact_write blockers

## Session Outcomes

| Session | Task | Outcome |
|---------|------|---------|
| spinner-kickoff | Greenfield scaffold | Blocked — awaiting user decision confirmation |
| spinner1/spinner2 | Bootstrap + TOY tickets | Blocked — ticket state inconsistency causes planner/artifact_write failures |
| GPTTalker blocker1 | Scaffold repair | Partial — pivot recorded but verification failed |
| codex-logs Session 1 | Code review | Found 3 bugs but didn't follow methodology |
| codex-logs Session 2 | Pivot | Partial — pivot recorded, verification failed |
| codex-logs Session 3 | Skill repair | Created tickets but never fixed Python import issue |
