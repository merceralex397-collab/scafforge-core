---
source_url: https://opencode.ai/docs/commands
fetched_with: http
---

# Commands

Create custom commands for repetitive tasks.

Custom commands let you specify a prompt you want to run when that command is executed in the TUI.

Custom commands are in addition to the built-in commands like `/init`

, `/undo`

, `/redo`

, `/share`

, `/help`

. Learn more.

Create markdown files in the `commands/`

directory to define custom commands.

Create `.opencode/commands/test.md`

:

The frontmatter defines command properties. The content becomes the template.

Use the command by typing `/`

followed by the command name.

You can add custom commands through the OpenCode config or by creating markdown files in the `commands/`

directory.

Use the `command`

option in your OpenCode config:

Now you can run this command in the TUI:

You can also define commands using markdown files. Place them in:

- Global:
`~/.config/opencode/commands/`

- Per-project:
`.opencode/commands/`

The markdown file name becomes the command name. For example, `test.md`

lets you run:

The prompts for the custom commands support several special placeholders and syntax.

Pass arguments to commands using the `$ARGUMENTS`

placeholder.

Run the command with arguments:

And `$ARGUMENTS`

will be replaced with `Button`

.

You can also access individual arguments using positional parameters:

`$1`

- First argument`$2`

- Second argument`$3`

- Third argument- And so on…

For example:

Run the command:

This replaces:

`$1`

with`config.json`

`$2`

with`src`

`$3`

with`{ "key": "value" }`

Use *! command* to inject bash command output into your prompt.

For example, to create a custom command that analyzes test coverage:

Or to review recent changes:

Commands run in your project’s root directory and their output becomes part of the prompt.

Include files in your command using `@`

followed by the filename.

The file content gets included in the prompt automatically.

Let’s look at the configuration options in detail.

The `template`

option defines the prompt that will be sent to the LLM when the command is executed.

This is a **required** config option.

Use the `description`

option to provide a brief description of what the command does.

This is shown as the description in the TUI when you type in the command.

Use the `agent`

config to optionally specify which agent should execute this command. If this is a subagent the command will trigger a subagent invocation by default. To disable this behavior, set `subtask`

to `false`

.

This is an **optional** config option. If not specified, defaults to your current agent.

Use the `subtask`

boolean to force the command to trigger a subagent invocation. This is useful if you want the command to not pollute your primary context and will **force** the agent to act as a subagent, even if `mode`

is set to `primary`

on the agent configuration.

This is an **optional** config option.

Use the `model`

config to override the default model for this command.

This is an **optional** config option.

opencode includes several built-in commands like `/init`

, `/undo`

, `/redo`

, `/share`

, `/help`

; learn more.

If you define a custom command with the same name, it will override the built-in command.
