---
source_url: https://opencode.ai/docs/agents
fetched_with: http
---

# Agents

Configure and use specialized agents.

Agents are specialized AI assistants that can be configured for specific tasks and workflows. They allow you to create focused tools with custom prompts, models, and tool access.

You can switch between agents during a session or invoke them with the `@`

mention.

There are two types of agents in OpenCode; primary agents and subagents.

Primary agents are the main assistants you interact with directly. You can cycle through them using the **Tab** key, or your configured `switch_agent`

keybind. These agents handle your main conversation. Tool access is configured via permissions — for example, Build has all tools enabled while Plan is restricted.

OpenCode comes with two built-in primary agents, **Build** and **Plan**. We’ll look at these below.

Subagents are specialized assistants that primary agents can invoke for specific tasks. You can also manually invoke them by **@ mentioning** them in your messages.

OpenCode comes with two built-in subagents, **General** and **Explore**. We’ll look at this below.

OpenCode comes with two built-in primary agents and two built-in subagents.

*Mode*: `primary`

Build is the **default** primary agent with all tools enabled. This is the standard agent for development work where you need full access to file operations and system commands.

*Mode*: `primary`

A restricted agent designed for planning and analysis. We use a permission system to give you more control and prevent unintended changes. By default, all of the following are set to `ask`

:

`file edits`

: All writes, patches, and edits`bash`

: All bash commands

This agent is useful when you want the LLM to analyze code, suggest changes, or create plans without making any actual modifications to your codebase.

*Mode*: `subagent`

A general-purpose agent for researching complex questions and executing multi-step tasks. Has full tool access (except todo), so it can make file changes when needed. Use this to run multiple units of work in parallel.

*Mode*: `subagent`

A fast, read-only agent for exploring codebases. Cannot modify files. Use this when you need to quickly find files by patterns, search code for keywords, or answer questions about the codebase.

*Mode*: `primary`

Hidden system agent that compacts long context into a smaller summary. It runs automatically when needed and is not selectable in the UI.

*Mode*: `primary`

Hidden system agent that generates short session titles. It runs automatically and is not selectable in the UI.

*Mode*: `primary`

Hidden system agent that creates session summaries. It runs automatically and is not selectable in the UI.

-
For primary agents, use the

**Tab**key to cycle through them during a session. You can also use your configured`switch_agent`

keybind. - Subagents can be invoked:

-
**Automatically**by primary agents for specialized tasks based on their descriptions. -
Manually by

**@ mentioning**a subagent in your message. For example.

-
-
**Navigation between sessions**: When subagents create their own child sessions, you can navigate between the parent session and all child sessions using:**<Leader>+Right**(or your configured`session_child_cycle`

keybind) to cycle forward through parent → child1 → child2 → … → parent**<Leader>+Left**(or your configured`session_child_cycle_reverse`

keybind) to cycle backward through parent ← child1 ← child2 ← … ← parent

This allows you to seamlessly switch between the main conversation and specialized subagent work.

You can customize the built-in agents or create your own through configuration. Agents can be configured in two ways:

Configure agents in your `opencode.json`

config file:

You can also define agents using markdown files. Place them in:

- Global:
`~/.config/opencode/agents/`

- Per-project:
`.opencode/agents/`

The markdown file name becomes the agent name. For example, `review.md`

creates a `review`

agent.

Let’s look at these configuration options in detail.

Use the `description`

option to provide a brief description of what the agent does and when to use it.

This is a **required** config option.

Control the randomness and creativity of the LLM’s responses with the `temperature`

config.

Lower values make responses more focused and deterministic, while higher values increase creativity and variability.

Temperature values typically range from 0.0 to 1.0:

**0.0-0.2**: Very focused and deterministic responses, ideal for code analysis and planning**0.3-0.5**: Balanced responses with some creativity, good for general development tasks**0.6-1.0**: More creative and varied responses, useful for brainstorming and exploration

If no temperature is specified, OpenCode uses model-specific defaults; typically 0 for most models, 0.55 for Qwen models.

Control the maximum number of agentic iterations an agent can perform before being forced to respond with text only. This allows users who wish to control costs to set a limit on agentic actions.

If this is not set, the agent will continue to iterate until the model chooses to stop or the user interrupts the session.

When the limit is reached, the agent receives a special system prompt instructing it to respond with a summarization of its work and recommended remaining tasks.

Set to `true`

to disable the agent.

Specify a custom system prompt file for this agent with the `prompt`

config. The prompt file should contain instructions specific to the agent’s purpose.

This path is relative to where the config file is located. So this works for both the global OpenCode config and the project specific config.

Use the `model`

config to override the model for this agent. Useful for using different models optimized for different tasks. For example, a faster model for planning, a more capable model for implementation.

The model ID in your OpenCode config uses the format `provider/model-id`

. For example, if you’re using OpenCode Zen, you would use `opencode/gpt-5.1-codex`

for GPT 5.1 Codex.

Control which tools are available in this agent with the `tools`

config. You can enable or disable specific tools by setting them to `true`

or `false`

.

You can also use wildcards to control multiple tools at once. For example, to disable all tools from an MCP server:

You can configure permissions to manage what actions an agent can take. Currently, the permissions for the `edit`

, `bash`

, and `webfetch`

tools can be configured to:

`"ask"`

— Prompt for approval before running the tool`"allow"`

— Allow all operations without approval`"deny"`

— Disable the tool

You can override these permissions per agent.

You can also set permissions in Markdown agents.

You can set permissions for specific bash commands.

This can take a glob pattern.

And you can also use the `*`

wildcard to manage permissions for all commands. Since the last matching rule takes precedence, put the `*`

wildcard first and specific rules after.

Control the agent’s mode with the `mode`

config. The `mode`

option is used to determine how the agent can be used.

The `mode`

option can be set to `primary`

, `subagent`

, or `all`

. If no `mode`

is specified, it defaults to `all`

.

Hide a subagent from the `@`

autocomplete menu with `hidden: true`

. Useful for internal subagents that should only be invoked programmatically by other agents via the Task tool.

This only affects user visibility in the autocomplete menu. Hidden agents can still be invoked by the model via the Task tool if permissions allow.

Control which subagents an agent can invoke via the Task tool with `permission.task`

. Uses glob patterns for flexible matching.

When set to `deny`

, the subagent is removed from the Task tool description entirely, so the model won’t attempt to invoke it.

Customize the agent’s visual appearance in the UI with the `color`

option. This affects how the agent appears in the interface.

Use a valid hex color (e.g., `#FF5733`

) or theme color: `primary`

, `secondary`

, `accent`

, `success`

, `warning`

, `error`

, `info`

.

Control response diversity with the `top_p`

option. Alternative to temperature for controlling randomness.

Values range from 0.0 to 1.0. Lower values are more focused, higher values more diverse.

Any other options you specify in your agent configuration will be **passed through directly** to the provider as model options. This allows you to use provider-specific features and parameters.

For example, with OpenAI’s reasoning models, you can control the reasoning effort:

These additional options are model and provider-specific. Check your provider’s documentation for available parameters.

You can create new agents using the following command:

This interactive command will:

- Ask where to save the agent; global or project-specific.
- Description of what the agent should do.
- Generate an appropriate system prompt and identifier.
- Let you select which tools the agent can access.
- Finally, create a markdown file with the agent configuration.

Here are some common use cases for different agents.

**Build agent**: Full development work with all tools enabled**Plan agent**: Analysis and planning without making changes**Review agent**: Code review with read-only access plus documentation tools**Debug agent**: Focused on investigation with bash and read tools enabled**Docs agent**: Documentation writing with file operations but no system commands

Here are some example agents you might find useful.
