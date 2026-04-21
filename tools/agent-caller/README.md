# agent-caller

`agent-caller` is a small local CLI for the Scafforge active-plan workflow. It wraps:

- `copilot` for `planchecker`
- `copilot` for `planimplementer`
- `opencode` plus `gh` for `planprreviewer`

The CLI is intentionally narrow. It is for the active-plan cycle, not a general orchestration framework.
It is also intentionally local-only for this repo and this implementation program. It exists to save tokens and standardize command invocation while working through the plans.

## Commands

- `agent-caller planchecker --plan 02`
- `agent-caller planimplementer --plan 01`
- `agent-caller planprreviewer --plan 02 --pr 123`

## Install

From the Scafforge repo root:

```powershell
uv tool install --force --editable .\tools\agent-caller
```

## Prompt Packs

By default, `agent-caller` reads plan-specific prompts from:

```text
active-plans/<plan-folder>/references/agent-caller-prompts.md
```

Each prompt pack should contain these `##` sections:

- `planchecker`
- `planimplementer`
- `planprreviewer methodology`
- `planprreviewer big-pickle`
- `planprreviewer minimax-m2.7`
- `planprreviewer devstral-2512`
- `planprreviewer mistral-large-latest`
- `planprreviewer kimi-k2.5-turbo`

## Examples

Show the wrapped command without executing it:

```powershell
agent-caller planchecker --plan 02 --dry-run
agent-caller planimplementer --plan 01 --dry-run
agent-caller planprreviewer --plan 02 --pr 123 --dry-run
```

Run the checker:

```powershell
agent-caller planchecker --plan 02
```

Run the implementer with Claude Sonnet 4.6 instead of GPT-5.4:

```powershell
agent-caller planimplementer --plan 01 --model claude-sonnet-4.6
```

Run the PR reviewers and emit a machine-readable summary:

```powershell
agent-caller planprreviewer --plan 02 --pr 123 --json
```

`planprreviewer` uses OpenCode to generate each model's review body, then posts that body to GitHub with `gh pr comment`. This keeps the review content model-authored while making comment delivery deterministic.
