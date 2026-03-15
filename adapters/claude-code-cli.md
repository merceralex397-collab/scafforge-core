# Claude Code / Claude CLI Adapter

This adapter explains how to run the shared Scafforge CLI from **Claude Code** or a comparable **Claude CLI** workflow.
Claude is the host layer here; OpenCode is still the generated runtime target.

## Prerequisites

- Claude Code or Claude CLI is already installed and usable in your environment.
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

Or run the local bin wrapper without installing globally:

```bash
node ./bin/scafforge.mjs --help
```

See [package-publish.md](package-publish.md) for the shared publication and install contract.

## Invoke Scafforge from Claude Code / Claude CLI

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

Claude Code / Claude CLI should pass Scafforge's model configuration explicitly:

- `--model-provider`
- `--planner-model`
- `--implementer-model`
- `--utility-model` when needed
- `--profile` for `minimum` vs the default `full` scaffold pack

The host runs Scafforge; the generated repo later uses the emitted OpenCode configuration and metadata.

## Handoff into the generated repo

When generation completes, move into the generated repo and continue from OpenCode.
See [opencode-runtime.md](opencode-runtime.md) for the runtime handoff.
