# Host Adapter Contract

This directory documents the **host layer** for Scafforge.

Scafforge has two layers:

- **Host layer**: a supported CLI host runs the Scafforge package or bin wrapper.
- **Output layer**: Scafforge generates an OpenCode-oriented repo runtime.

OpenCode belongs to the **output layer**. It is **not** a host adapter for installing or invoking Scafforge itself.

## Supported host adapters

- [GitHub Copilot CLI](github-copilot-cli.md)
- [Codex](codex.md)
- [Claude Code / Claude CLI](claude-code-cli.md)

## Shared package responsibilities

- normalize messy inputs
- render the OpenCode-oriented scaffold
- enforce the generated repo contract
- validate template and documentation consistency

## Shared adapter responsibilities

- explain how a host runs the shared Scafforge CLI
- show truthful install and invocation guidance for the current package state
- require explicit provider/model inputs instead of hiding them in host-specific defaults
- explain how the host hands work off into the generated OpenCode runtime

## Package distribution state

Shared install and publish guidance lives in [package-publish.md](package-publish.md).

In short:

- `@scafforge/core` is configured for public npm publication
- after a published release, install with `npm install --global @scafforge/core`
- before the first release or when validating local changes, use `npm install --global .` or `node ./bin/scafforge.mjs --help`
- Scafforge currently expects Node.js 20+ and Python 3.10+

## Shared invocation contract

Every supported host runs the same Scafforge commands:

```bash
scafforge render-full \
  --dest /path/to/new-repo \
  --project-name "Example Project" \
  --model-provider "openrouter" \
  --planner-model "openrouter/anthropic/claude-sonnet-4.5" \
  --implementer-model "openrouter/openai/gpt-5-codex" \
  --utility-model "openrouter/anthropic/claude-sonnet-4.5"
```

```bash
scafforge render-opencode \
  --dest /path/to/existing-repo \
  --project-name "Example Project" \
  --model-provider "openrouter" \
  --planner-model "openrouter/anthropic/claude-sonnet-4.5" \
  --implementer-model "openrouter/openai/gpt-5-codex"
```

Provider/model choices are part of the host contract and must be passed explicitly:

- `--model-provider`
- `--planner-model`
- `--implementer-model`
- `--utility-model` (optional; defaults to the planner model in `render-full`)
- `--profile` (optional; `full` by default, `minimum` for the lighter deterministic pack)

No host adapter should pretend OpenCode chooses these for Scafforge. The host passes them into Scafforge during scaffold generation.

## Generated runtime handoff

After scaffold generation, hand work off to the generated OpenCode-oriented repo runtime.
That runtime story is documented separately in [opencode-runtime.md](opencode-runtime.md).

Use `adapters/manifest.json` as the machine-readable summary of this split.
