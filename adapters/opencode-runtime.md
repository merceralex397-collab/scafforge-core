# OpenCode Generated Runtime

OpenCode is the **generated runtime target** for Scafforge output.
It is **not** a host adapter for installing or invoking Scafforge itself.

## When OpenCode enters the flow

1. A supported host runs Scafforge:
   - GitHub Copilot CLI
   - Codex
   - Claude Code / Claude CLI
2. Scafforge renders either:
   - the full scaffold with docs, tickets, and `.opencode/`, or
   - the OpenCode layer for a retrofit
3. Work then continues inside the generated repo using OpenCode conventions.

## Full scaffold handoff

After `scafforge render-full`, the generated repo is intended to be opened as an OpenCode-oriented workspace.

Typical handoff:

```bash
cd /path/to/generated-repo
opencode
```

Then follow the generated repo contract, including:

- `START-HERE.md`
- `AGENTS.md`
- `docs/process/`
- `.opencode/commands/`

## Retrofit handoff

After `scafforge render-opencode`, the existing repo gains the OpenCode layer.
Open the repo in OpenCode and work from the injected `.opencode/` surface and related process docs.

## Provider/model relationship

Provider/model choices are passed into Scafforge during generation by the host:

- `--model-provider`
- `--planner-model`
- `--implementer-model`
- `--utility-model` when needed

Scafforge writes those choices into generated metadata and docs for the OpenCode runtime to consume later.
OpenCode does not act as the installer or launcher for Scafforge.
