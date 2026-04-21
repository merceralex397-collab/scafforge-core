---
source_url: https://opencode.ai/docs/plugins
fetched_with: http
---

# Plugins

Write your own plugins to extend OpenCode.

Plugins allow you to extend OpenCode by hooking into various events and customizing behavior. You can create plugins to add new features, integrate with external services, or modify OpenCode’s default behavior.

For examples, check out the plugins created by the community.

There are two ways to load plugins.

Place JavaScript or TypeScript files in the plugin directory.

`.opencode/plugins/`

- Project-level plugins`~/.config/opencode/plugins/`

- Global plugins

Files in these directories are automatically loaded at startup.

Specify npm packages in your config file.

Both regular and scoped npm packages are supported.

Browse available plugins in the ecosystem.

**npm plugins** are installed automatically using Bun at startup. Packages and their dependencies are cached in `~/.cache/opencode/node_modules/`

.

**Local plugins** are loaded directly from the plugin directory. To use external packages, you must create a `package.json`

within your config directory (see Dependencies), or publish the plugin to npm and add it to your config.

Plugins are loaded from all sources and all hooks run in sequence. The load order is:

- Global config (
`~/.config/opencode/opencode.json`

) - Project config ( `opencode.json`

) - Global plugin directory ( `~/.config/opencode/plugins/`

) - Project plugin directory ( `.opencode/plugins/`

)

Duplicate npm packages with the same name and version are loaded once. However, a local plugin and an npm plugin with similar names are both loaded separately.

A plugin is a **JavaScript/TypeScript module** that exports one or more plugin functions. Each function receives a context object and returns a hooks object.

Local plugins and custom tools can use external npm packages. Add a `package.json`

to your config directory with the dependencies you need.

OpenCode runs `bun install`

at startup to install these. Your plugins and tools can then import them.

The plugin function receives:

`project`

: The current project information.`directory`

: The current working directory.`worktree`

: The git worktree path.`client`

: An opencode SDK client for interacting with the AI.`$`

: Bun’s shell API for executing commands.

For TypeScript plugins, you can import types from the plugin package:

Plugins can subscribe to events as seen below in the Examples section. Here is a list of the different events available.

`command.executed`

`file.edited`

`file.watcher.updated`

`installation.updated`

`lsp.client.diagnostics`

`lsp.updated`

`message.part.removed`

`message.part.updated`

`message.removed`

`message.updated`

`permission.asked`

`permission.replied`

`server.connected`

`session.created`

`session.compacted`

`session.deleted`

`session.diff`

`session.error`

`session.idle`

`session.status`

`session.updated`

`todo.updated`

`shell.env`

`tool.execute.after`

`tool.execute.before`

`tui.prompt.append`

`tui.command.execute`

`tui.toast.show`

Here are some examples of plugins you can use to extend opencode.

Send notifications when certain events occur:

We are using `osascript`

to run AppleScript on macOS. Here we are using it to send notifications.

Prevent opencode from reading `.env`

files:

Inject environment variables into all shell execution (AI tools and user terminals):

Plugins can also add custom tools to opencode:

The `tool`

helper creates a custom tool that opencode can call. It takes a Zod schema function and returns a tool definition with:

`description`

: What the tool does`args`

: Zod schema for the tool’s arguments`execute`

: Function that runs when the tool is called

Your custom tools will be available to opencode alongside built-in tools.

Use `client.app.log()`

instead of `console.log`

for structured logging:

Levels: `debug`

, `info`

, `warn`

, `error`

. See SDK documentation for details.

Customize the context included when a session is compacted:

The `experimental.session.compacting`

hook fires before the LLM generates a continuation summary. Use it to inject domain-specific context that the default compaction prompt would miss.

You can also replace the compaction prompt entirely by setting `output.prompt`

:

When `output.prompt`

is set, it completely replaces the default compaction prompt. The `output.context`

array is ignored in this case.
