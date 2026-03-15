# GitHub Copilot CLI Adapter

This adapter explains how to run the shared Scafforge CLI from **GitHub Copilot CLI**.
It does not change the generated runtime target; the output is still an OpenCode-oriented repo.

## Prerequisites

- GitHub Copilot CLI is already installed and authenticated in your environment.
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

From GitHub Copilot CLI you can then run `scafforge ...` directly, or skip the global install and invoke the bin wrapper:

```bash
node ./bin/scafforge.mjs --help
```

See [package-publish.md](package-publish.md) for the shared publication and install contract.

## Invoke Scafforge from GitHub Copilot CLI

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

GitHub Copilot CLI does not replace Scafforge's runtime model contract.
Pass the choices through explicitly:

- `--model-provider`: provider label recorded in the scaffold metadata
- `--planner-model`: planner/reviewer/team-lead model string
- `--implementer-model`: implementation model string
- `--utility-model`: optional helper/docs/QA model string
- `--profile`: optional scaffold profile (`full` by default, `minimum` for the lighter pack)

## Handoff into the generated repo

Once Scafforge finishes, move into the generated repo and continue in OpenCode.
See [opencode-runtime.md](opencode-runtime.md) for the runtime handoff.
