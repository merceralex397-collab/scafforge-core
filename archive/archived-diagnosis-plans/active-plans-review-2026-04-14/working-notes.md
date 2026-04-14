# Working Notes — Scafforge Recovery Session

## Session Context
- Branch: autofixing
- Start: 2026-04-08
- Scope: Full recovery, validation, and expansion per promptfile.md

## Key Decisions

### Agent Architecture
- opencode runs ticket work in downstream repos (headless via `opencode run`)
- codex runs scafforge-audit and scafforge-repair (headless via `codex exec`)
- Host agent (this session) coordinates, fixes Scafforge, monitors
- NEVER edit downstream repos directly

### Model Choices
- Downstream: minimax-coding-plan/MiniMax-M2.7 (user has unlimited usage)
- Codex: gpt-5.4
- Host: claude-opus-4.6 (this session)

### Repair Follow-On Resolution
- Repair leaves `managed_blocked` requiring host-agent skills
- Downstream agents can self-resolve via `repair_follow_on_refresh`
- Improved BLOCKER message to guide agents to this tool (commit 9460cc63)

## Active Observations

### GPTTalker
- 68/68 tickets done but server crashes on startup
- Root cause: CREATE_INDEXES in migration 1 references tables from migrations 3/4
- Agent launched to fix this — identified the bug, delegating to implementer

### Spinner
- 14/19 tickets done, 5 remaining
- Agent unblocked, attempting Godot export for RELEASE-001
- Export templates exist at /home/pc/.local/share/godot/export_templates/4.6.2.stable/templates/
- Agent using glob (project-scoped) instead of bash for external paths — may struggle

### Glitch
- 4/17 tickets done, 13 remaining
- Agent unblocked, working on REMED-004 implementation
- Delegated to glitch-implementer

## Recurring Patterns
1. managed_blocked prevents all agent work until follow-on resolved
2. Agents initially didn't know how to self-unblock (fixed with better error message)
3. Glob tool is project-scoped — agents can't discover external paths (need bash)
4. Team leader delegates to implementer but implementer may also hit blockers
