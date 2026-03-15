---
name: opencode-team-bootstrap
description: Generate a project-local OpenCode team with a visible orchestrator, hidden specialists, local tools, plugins, commands, skills, and MCP placeholders. Use when a host agent needs to prepare a repo for autonomous OpenCode execution with weak-model-safe prompts and strict internal stage gates.
---

# OpenCode Team Bootstrap

Use this skill when the repo needs the OpenCode operating layer.

## Quick start

To generate only the OpenCode layer:

```powershell
python scripts/bootstrap_opencode_team.py `
  --dest C:\path\to\repo `
  --project-name "Example Project" `
  --model-provider "openrouter" `
  --planner-model "openrouter/anthropic/claude-sonnet-4.5" `
  --implementer-model "openrouter/openai/gpt-5-codex"
```

## Team design

- one visible team leader
- hidden specialists by default
- no `ask` permissions
- explicit `permission.task` allowlists
- commands for humans only
- tools/plugins for autonomous internal flow
- workflow state and ticket tools for stage control instead of raw file edits

## Prompt hardening

When the generated team needs prompt customization, use `agent-prompt-engineering`
to keep prompts explicit, artifact-aware, and capability-aligned for weaker models.

After generating or retrofitting the OpenCode layer, run `repo-process-doctor` in
audit mode so repos that drift toward raw-file stage management are caught early.

## References

- `references/agent-system.md`
- `references/tools-plugins-mcp.md`

Use the main scaffold assets from `../repo-scaffold-factory/assets/project-template/` when a full repo skeleton is needed.

This skill is intentionally a thin `.opencode`-scope wrapper over `repo-scaffold-factory`. It should not grow independent template logic.
