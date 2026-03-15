---
name: repo-scaffold-factory
description: Build an initial repository structure, README, project AGENTS file, docs layout, ticket pack, and OpenCode scaffold from a normalized spec. Use when a host agent needs to create a greenfield repo foundation or reset a weakly structured project into a deterministic, signposted layout that weaker models can operate inside.
---

# Repo Scaffold Factory

Use this skill when the goal is to create the initial repository operating system, not just a few starter files.

## Quick start

Run the bootstrap script when you want a full project skeleton:

```powershell
python scripts/bootstrap_repo_scaffold.py `
  --dest C:\path\to\repo `
  --project-name "Example Project" `
  --model-provider "openrouter" `
  --planner-model "openrouter/anthropic/claude-sonnet-4.5" `
  --implementer-model "openrouter/openai/gpt-5-codex"
```

Important flags:

- `--project-slug` to override the inferred slug
- `--agent-prefix` to override the inferred OpenCode agent prefix
- `--utility-model` to override utility, docs, and QA helper lanes when they should differ from the planner model
- `--scope opencode` to generate only the OpenCode layer
- `--force` to overwrite an existing target tree

## What this skill generates

- Root `README.md`
- Root `AGENTS.md`
- Root `START-HERE.md`
- `docs/process/` and `docs/spec/`
- `tickets/` with manifest, board, and template
- `opencode.jsonc`
- `.opencode/agents/`, `.opencode/tools/`, `.opencode/plugins/`, `.opencode/commands/`, and `.opencode/skills/`

## Workflow

1. Normalize the source material first.
2. Decide the project name, slug, provider, planner model, implementer model, and optional utility/helper model.
3. Run the scaffold bootstrap script.
4. Use `agent-prompt-engineering` if the repo needs custom team-leader, reviewer, or command prompts.
5. Review the generated docs and replace placeholders with project-specific facts.
6. Run `repo-process-doctor` in audit mode so prompt or ticket drift is caught before handoff.
7. Add stack-specific local skills after the repo stack is known.

This skill owns the scaffold template assets under `assets/project-template/`. Wrapper skills should call into this template rather than duplicating `.opencode`, ticket, or doc scaffolding logic elsewhere.

## References

- `references/layout-guide.md` for the intended repo shape
- `references/workflow-guide.md` for the ticketed lifecycle
- `references/community-skill-audit.md` for notes on external skill patterns to inspect rather than auto-install
- `assets/project-template/` for the copied scaffold source
