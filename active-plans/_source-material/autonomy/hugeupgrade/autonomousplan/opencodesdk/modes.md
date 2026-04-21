---
source_url: https://opencode.ai/docs/modes
fetched_with: http
---

# Modes

Different modes for different use cases.

Modes in opencode allow you to customize the behavior, tools, and prompts for different use cases.

It comes with two built-in modes: **build** and **plan**. You can customize these or configure your own through the opencode config.

You can switch between modes during a session or configure them in your config file.

opencode comes with two built-in modes.

Build is the **default** mode with all tools enabled. This is the standard mode for development work where you need full access to file operations and system commands.

A restricted mode designed for planning and analysis. In plan mode, the following tools are disabled by default:

`write`

- Cannot create new files`edit`

- Cannot modify existing files, except for files located at`.opencode/plans/*.md`

to detail the plan itself`patch`

- Cannot apply patches`bash`

- Cannot execute shell commands

This mode is useful when you want the AI to analyze code, suggest changes, or create plans without making any actual modifications to your codebase.

You can switch between modes during a session using the *Tab* key. Or your configured `switch_mode`

keybind.

See also: Formatters for information about code formatting configuration.

You can customize the built-in modes or create your own through configuration. Modes can be configured in two ways:

Configure modes in your `opencode.json`

config file:

You can also define modes using markdown files. Place them in:

- Global:
`~/.config/opencode/modes/`

- Project:
`.opencode/modes/`

The markdown file name becomes the mode name (e.g., `review.md`

creates a `review`

mode).

Let’s look at these configuration options in detail.

Use the `model`

config to override the default model for this mode. Useful for using different models optimized for different tasks. For example, a faster model for planning, a more capable model for implementation.

Control the randomness and creativity of the AI’s responses with the `temperature`

config. Lower values make responses more focused and deterministic, while higher values increase creativity and variability.

Temperature values typically range from 0.0 to 1.0:

**0.0-0.2**: Very focused and deterministic responses, ideal for code analysis and planning**0.3-0.5**: Balanced responses with some creativity, good for general development tasks**0.6-1.0**: More creative and varied responses, useful for brainstorming and exploration

If no temperature is specified, opencode uses model-specific defaults (typically 0 for most models, 0.55 for Qwen models).

Specify a custom system prompt file for this mode with the `prompt`

config. The prompt file should contain instructions specific to the mode’s purpose.

This path is relative to where the config file is located. So this works for both the global opencode config and the project specific config.

Control which tools are available in this mode with the `tools`

config. You can enable or disable specific tools by setting them to `true`

or `false`

.

If no tools are specified, all tools are enabled by default.

Here are all the tools can be controlled through the mode config.

| Tool | Description |
|---|---|
`bash` | Execute shell commands | `edit` | Modify existing files | `write` | Create new files | `read` | Read file contents | `grep` | Search file contents | `glob` | Find files by pattern | `list` | List directory contents | `patch` | Apply patches to files | `todowrite` | Manage todo lists | `todoread` | Read todo lists | `webfetch` | Fetch web content |

You can create your own custom modes by adding them to the configuration. Here are examples using both approaches:

Create mode files in `.opencode/modes/`

for project-specific modes or `~/.config/opencode/modes/`

for global modes:

Here are some common use cases for different modes.

**Build mode**: Full development work with all tools enabled**Plan mode**: Analysis and planning without making changes**Review mode**: Code review with read-only access plus documentation tools**Debug mode**: Focused on investigation with bash and read tools enabled**Docs mode**: Documentation writing with file operations but no system commands

You might also find different models are good for different use cases.
