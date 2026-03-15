# Codex Adapter

This adapter explains how to run the shared Scafforge CLI from **Codex**.
Codex is the host that launches Scafforge; OpenCode remains the generated repo runtime after scaffolding.

## Prerequisites

- Codex is already installed and usable in your environment.
- Node.js 20+ and Python 3.10+ are available.
- You have either a published `@scafforge/core` install or a local checkout for unreleased validation.

## Install or run Scafforge

For a published release:

```bash
npm install --global @scafforge/core
```

Before the first npm release, or when testing a local checkout:

```bash
npm install --global .
```

If you prefer not to install globally, invoke the local bin wrapper directly:

```bash
node ./bin/scafforge.mjs --help
```

See [package-publish.md](package-publish.md) for the shared publication and install contract.

## Invoke Scafforge from Codex

Full greenfield scaffold:

```bash
scafforge render-full \
  --dest /path/to/new-repo \
  --project-name "Example Project" \
  --model-provider "openrouter" \
  --planner-model "openrouter/anthropic/claude-sonnet-4.5" \
  --implementer-model "openrouter/openai/gpt-5-codex" \
  --utility-model "openrouter/anthropic/claude-sonnet-4.5"
```

OpenCode-layer retrofit into an existing repo:

```bash
scafforge render-opencode \
  --dest /path/to/existing-repo \
  --project-name "Example Project" \
  --model-provider "openrouter" \
  --planner-model "openrouter/anthropic/claude-sonnet-4.5" \
  --implementer-model "openrouter/openai/gpt-5-codex"
```

## Passing provider/model choices

Codex should pass provider/model choices into Scafforge exactly as CLI flags:

- `--model-provider`
- `--planner-model`
- `--implementer-model`
- `--utility-model` when you want the helper lane to differ from the planner lane
- `--profile` when you want the lighter minimum scaffold instead of the default full pack

These values are recorded into the generated OpenCode-oriented repo metadata; they are not inferred by Codex.

## Handoff into the generated repo

After scaffold generation, switch to the generated repo's OpenCode workflow.
See [opencode-runtime.md](opencode-runtime.md) for the runtime handoff.
