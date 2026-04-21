---
source_url: https://opencode.ai/docs/config
fetched_with: http
---

# Config

Using the OpenCode JSON config.

You can configure OpenCode using a JSON config file.

OpenCode supports both **JSON** and **JSONC** (JSON with Comments) formats.

You can place your config in a couple of different locations and they have a different order of precedence.

Configuration files are merged together, not replaced. Settings from the following config locations are combined. Later configs override earlier ones only for conflicting keys. Non-conflicting settings from all configs are preserved.

For example, if your global config sets `theme: "opencode"`

and `autoupdate: true`

, and your project config sets `model: "anthropic/claude-sonnet-4-5"`

, the final configuration will include all three settings.

Config sources are loaded in this order (later sources override earlier ones):

**Remote config**(from`.well-known/opencode`

) - organizational defaults**Global config**(`~/.config/opencode/opencode.json`

) - user preferences**Custom config**(`OPENCODE_CONFIG`

env var) - custom overrides**Project config**(`opencode.json`

in project) - project-specific settings- agents, commands, plugins`.opencode`

directories**Inline config**(`OPENCODE_CONFIG_CONTENT`

env var) - runtime overrides

This means project configs can override global defaults, and global configs can override remote organizational defaults.

Organizations can provide default configuration via the `.well-known/opencode`

endpoint. This is fetched automatically when you authenticate with a provider that supports it.

Remote config is loaded first, serving as the base layer. All other config sources (global, project) can override these defaults.

For example, if your organization provides MCP servers that are disabled by default:

You can enable specific servers in your local config:

Place your global OpenCode config in `~/.config/opencode/opencode.json`

. Use global config for user-wide preferences like themes, providers, or keybinds.

Global config overrides remote organizational defaults.

Add `opencode.json`

in your project root. Project config has the highest precedence among standard config files - it overrides both global and remote configs.

When OpenCode starts up, it looks for a config file in the current directory or traverse up to the nearest Git directory.

This is also safe to be checked into Git and uses the same schema as the global one.

Specify a custom config file path using the `OPENCODE_CONFIG`

environment variable.

Custom config is loaded between global and project configs in the precedence order.

Specify a custom config directory using the `OPENCODE_CONFIG_DIR`

environment variable. This directory will be searched for agents, commands, modes, and plugins just like the standard `.opencode`

directory, and should follow the same structure.

The custom directory is loaded after the global config and `.opencode`

directories, so it **can override** their settings.

The config file has a schema that’s defined in ** opencode.ai/config.json**.

Your editor should be able to validate and autocomplete based on the schema.

You can configure TUI-specific settings through the `tui`

option.

Available options:

`scroll_acceleration.enabled`

- Enable macOS-style scroll acceleration.**Takes precedence over**`scroll_speed`

.`scroll_speed`

- Custom scroll speed multiplier (default:`3`

, minimum:`1`

). Ignored if`scroll_acceleration.enabled`

is`true`

.`diff_style`

- Control diff rendering.`"auto"`

adapts to terminal width,`"stacked"`

always shows single column.

You can configure server settings for the `opencode serve`

and `opencode web`

commands through the `server`

option.

Available options:

`port`

- Port to listen on.`hostname`

- Hostname to listen on. When`mdns`

is enabled and no hostname is set, defaults to`0.0.0.0`

.`mdns`

- Enable mDNS service discovery. This allows other devices on the network to discover your OpenCode server.`mdnsDomain`

- Custom domain name for mDNS service. Defaults to`opencode.local`

. Useful for running multiple instances on the same network.`cors`

- Additional origins to allow for CORS when using the HTTP server from a browser-based client. Values must be full origins (scheme + host + optional port), eg`https://app.example.com`

.

You can manage the tools an LLM can use through the `tools`

option.

You can configure the providers and models you want to use in your OpenCode config through the `provider`

, `model`

and `small_model`

options.

The `small_model`

option configures a separate model for lightweight tasks like title generation. By default, OpenCode tries to use a cheaper model if one is available from your provider, otherwise it falls back to your main model.

Provider options can include `timeout`

and `setCacheKey`

:

`timeout`

- Request timeout in milliseconds (default: 300000). Set to`false`

to disable.`setCacheKey`

- Ensure a cache key is always set for designated provider.

You can also configure local models. Learn more.

Some providers support additional configuration options beyond the generic `timeout`

and `apiKey`

settings.

Amazon Bedrock supports AWS-specific configuration:

`region`

- AWS region for Bedrock (defaults to`AWS_REGION`

env var or`us-east-1`

)`profile`

- AWS named profile from`~/.aws/credentials`

(defaults to`AWS_PROFILE`

env var)`endpoint`

- Custom endpoint URL for VPC endpoints. This is an alias for the generic`baseURL`

option using AWS-specific terminology. If both are specified,`endpoint`

takes precedence.

You can configure the theme you want to use in your OpenCode config through the `theme`

option.

You can configure specialized agents for specific tasks through the `agent`

option.

You can also define agents using markdown files in `~/.config/opencode/agents/`

or `.opencode/agents/`

. Learn more here.

You can set the default agent using the `default_agent`

option. This determines which agent is used when none is explicitly specified.

The default agent must be a primary agent (not a subagent). This can be a built-in agent like `"build"`

or `"plan"`

, or a custom agent you’ve defined. If the specified agent doesn’t exist or is a subagent, OpenCode will fall back to `"build"`

with a warning.

This setting applies across all interfaces: TUI, CLI (`opencode run`

), desktop app, and GitHub Action.

You can configure the share feature through the `share`

option.

This takes:

`"manual"`

- Allow manual sharing via commands (default)`"auto"`

- Automatically share new conversations`"disabled"`

- Disable sharing entirely

By default, sharing is set to manual mode where you need to explicitly share conversations using the `/share`

command.

You can configure custom commands for repetitive tasks through the `command`

option.

You can also define commands using markdown files in `~/.config/opencode/commands/`

or `.opencode/commands/`

. Learn more here.

You can customize your keybinds through the `keybinds`

option.

OpenCode will automatically download any new updates when it starts up. You can disable this with the `autoupdate`

option.

If you don’t want updates but want to be notified when a new version is available, set `autoupdate`

to `"notify"`

. Notice that this only works if it was not installed using a package manager such as Homebrew.

You can configure code formatters through the `formatter`

option.

By default, opencode **allows all operations** without requiring explicit approval. You can change this using the `permission`

option.

For example, to ensure that the `edit`

and `bash`

tools require user approval:

You can control context compaction behavior through the `compaction`

option.

`auto`

- Automatically compact the session when context is full (default:`true`

).`prune`

- Remove old tool outputs to save tokens (default:`true`

).`reserved`

- Token buffer for compaction. Leaves enough window to avoid overflow during compaction

You can configure file watcher ignore patterns through the `watcher`

option.

Patterns follow glob syntax. Use this to exclude noisy directories from file watching.

You can configure MCP servers you want to use through the `mcp`

option.

Plugins extend OpenCode with custom tools, hooks, and integrations.

Place plugin files in `.opencode/plugins/`

or `~/.config/opencode/plugins/`

. You can also load plugins from npm through the `plugin`

option.

You can configure the instructions for the model you’re using through the `instructions`

option.

This takes an array of paths and glob patterns to instruction files. Learn more about rules here.

You can disable providers that are loaded automatically through the `disabled_providers`

option. This is useful when you want to prevent certain providers from being loaded even if their credentials are available.

The `disabled_providers`

option accepts an array of provider IDs. When a provider is disabled:

- It won’t be loaded even if environment variables are set.
- It won’t be loaded even if API keys are configured through the
`/connect`

command. - The provider’s models won’t appear in the model selection list.

You can specify an allowlist of providers through the `enabled_providers`

option. When set, only the specified providers will be enabled and all others will be ignored.

This is useful when you want to restrict OpenCode to only use specific providers rather than disabling them one by one.

If a provider appears in both `enabled_providers`

and `disabled_providers`

, the `disabled_providers`

takes priority for backwards compatibility.

The `experimental`

key contains options that are under active development.

You can use variable substitution in your config files to reference environment variables and file contents.

Use `{env:VARIABLE_NAME}`

to substitute environment variables:

If the environment variable is not set, it will be replaced with an empty string.

Use `{file:path/to/file}`

to substitute the contents of a file:

File paths can be:

- Relative to the config file directory
- Or absolute paths starting with
`/`

or`~`

These are useful for:

- Keeping sensitive data like API keys in separate files.
- Including large instruction files without cluttering your config.
- Sharing common configuration snippets across multiple config files.
