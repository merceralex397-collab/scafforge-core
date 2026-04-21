---
source_url: https://opencode.ai/docs/cli
fetched_with: http
---

# CLI

OpenCode CLI options and commands.

The OpenCode CLI by default starts the TUI when run without any arguments.

But it also accepts commands as documented on this page. This allows you to interact with OpenCode programmatically.

Start the OpenCode terminal user interface.

| Flag | Short | Description |
|---|---|---|
`--continue` | `-c` | Continue the last session | `--session` | `-s` | Session ID to continue | `--fork` | Fork the session when continuing (use with `--continue` or `--session` ) | | `--prompt` | Prompt to use | | `--model` | `-m` | Model to use in the form of provider/model | `--agent` | Agent to use | | `--port` | Port to listen on | | `--hostname` | Hostname to listen on |

The OpenCode CLI also has the following commands.

Manage agents for OpenCode.

Attach a terminal to an already running OpenCode backend server started via `serve`

or `web`

commands.

This allows using the TUI with a remote OpenCode backend. For example:

| Flag | Short | Description |
|---|---|---|
`--dir` | Working directory to start TUI in | | `--session` | `-s` | Session ID to continue |

Create a new agent with custom configuration.

This command will guide you through creating a new agent with a custom system prompt and tool configuration.

List all available agents.

Command to manage credentials and login for providers.

OpenCode is powered by the provider list at Models.dev, so you can use `opencode auth login`

to configure API keys for any provider you’d like to use. This is stored in `~/.local/share/opencode/auth.json`

.

When OpenCode starts up it loads the providers from the credentials file. And if there are any keys defined in your environments or a `.env`

file in your project.

Lists all the authenticated providers as stored in the credentials file.

Or the short version.

Logs you out of a provider by clearing it from the credentials file.

Manage the GitHub agent for repository automation.

Install the GitHub agent in your repository.

This sets up the necessary GitHub Actions workflow and guides you through the configuration process. Learn more.

Run the GitHub agent. This is typically used in GitHub Actions.

| Flag | Description |
|---|---|
`--event` | GitHub mock event to run the agent for | `--token` | GitHub personal access token |

Manage Model Context Protocol servers.

Add an MCP server to your configuration.

This command will guide you through adding either a local or remote MCP server.

List all configured MCP servers and their connection status.

Or use the short version.

Authenticate with an OAuth-enabled MCP server.

If you don’t provide a server name, you’ll be prompted to select from available OAuth-capable servers.

You can also list OAuth-capable servers and their authentication status.

Or use the short version.

Remove OAuth credentials for an MCP server.

Debug OAuth connection issues for an MCP server.

List all available models from configured providers.

This command displays all models available across your configured providers in the format `provider/model`

.

This is useful for figuring out the exact model name to use in your config.

You can optionally pass a provider ID to filter models by that provider.

| Flag | Description |
|---|---|
`--refresh` | Refresh the models cache from models.dev | `--verbose` | Use more verbose model output (includes metadata like costs) |

Use the `--refresh`

flag to update the cached model list. This is useful when new models have been added to a provider and you want to see them in OpenCode.

Run opencode in non-interactive mode by passing a prompt directly.

This is useful for scripting, automation, or when you want a quick answer without launching the full TUI. For example.

You can also attach to a running `opencode serve`

instance to avoid MCP server cold boot times on every run:

| Flag | Short | Description |
|---|---|---|
`--command` | The command to run, use message for args | | `--continue` | `-c` | Continue the last session | `--session` | `-s` | Session ID to continue | `--fork` | Fork the session when continuing (use with `--continue` or `--session` ) | | `--share` | Share the session | | `--model` | `-m` | Model to use in the form of provider/model | `--agent` | Agent to use | | `--file` | `-f` | File(s) to attach to message | `--format` | Format: default (formatted) or json (raw JSON events) | | `--title` | Title for the session (uses truncated prompt if no value provided) | | `--attach` | Attach to a running opencode server (e.g., http://localhost:4096) | | `--port` | Port for the local server (defaults to random port) |

Start a headless OpenCode server for API access. Check out the server docs for the full HTTP interface.

This starts an HTTP server that provides API access to opencode functionality without the TUI interface. Set `OPENCODE_SERVER_PASSWORD`

to enable HTTP basic auth (username defaults to `opencode`

).

| Flag | Description |
|---|---|
`--port` | Port to listen on | `--hostname` | Hostname to listen on | `--mdns` | Enable mDNS discovery | `--cors` | Additional browser origin(s) to allow CORS |

Manage OpenCode sessions.

List all OpenCode sessions.

| Flag | Short | Description |
|---|---|---|
`--max-count` | `-n` | Limit to N most recent sessions | `--format` | Output format: table or json (table) |

Show token usage and cost statistics for your OpenCode sessions.

| Flag | Description |
|---|---|
`--days` | Show stats for the last N days (all time) | `--tools` | Number of tools to show (all) | `--models` | Show model usage breakdown (hidden by default). Pass a number to show top N | `--project` | Filter by project (all projects, empty string: current project) |

Export session data as JSON.

If you don’t provide a session ID, you’ll be prompted to select from available sessions.

Import session data from a JSON file or OpenCode share URL.

You can import from a local file or an OpenCode share URL.

Start a headless OpenCode server with a web interface.

This starts an HTTP server and opens a web browser to access OpenCode through a web interface. Set `OPENCODE_SERVER_PASSWORD`

to enable HTTP basic auth (username defaults to `opencode`

).

| Flag | Description |
|---|---|
`--port` | Port to listen on | `--hostname` | Hostname to listen on | `--mdns` | Enable mDNS discovery | `--cors` | Additional browser origin(s) to allow CORS |

Start an ACP (Agent Client Protocol) server.

This command starts an ACP server that communicates via stdin/stdout using nd-JSON.

| Flag | Description |
|---|---|
`--cwd` | Working directory | `--port` | Port to listen on | `--hostname` | Hostname to listen on |

Uninstall OpenCode and remove all related files.

| Flag | Short | Description |
|---|---|---|
`--keep-config` | `-c` | Keep configuration files | `--keep-data` | `-d` | Keep session data and snapshots | `--dry-run` | Show what would be removed without removing | | `--force` | `-f` | Skip confirmation prompts |

Updates opencode to the latest version or a specific version.

To upgrade to the latest version.

To upgrade to a specific version.

| Flag | Short | Description |
|---|---|---|
`--method` | `-m` | The installation method that was used; curl, npm, pnpm, bun, brew |

The opencode CLI takes the following global flags.

| Flag | Short | Description |
|---|---|---|
`--help` | `-h` | Display help | `--version` | `-v` | Print version number | `--print-logs` | Print logs to stderr | | `--log-level` | Log level (DEBUG, INFO, WARN, ERROR) |

OpenCode can be configured using environment variables.

| Variable | Type | Description |
|---|---|---|
`OPENCODE_AUTO_SHARE` | boolean | Automatically share sessions | `OPENCODE_GIT_BASH_PATH` | string | Path to Git Bash executable on Windows | `OPENCODE_CONFIG` | string | Path to config file | `OPENCODE_CONFIG_DIR` | string | Path to config directory | `OPENCODE_CONFIG_CONTENT` | string | Inline json config content | `OPENCODE_DISABLE_AUTOUPDATE` | boolean | Disable automatic update checks | `OPENCODE_DISABLE_PRUNE` | boolean | Disable pruning of old data | `OPENCODE_DISABLE_TERMINAL_TITLE` | boolean | Disable automatic terminal title updates | `OPENCODE_PERMISSION` | string | Inlined json permissions config | `OPENCODE_DISABLE_DEFAULT_PLUGINS` | boolean | Disable default plugins | `OPENCODE_DISABLE_LSP_DOWNLOAD` | boolean | Disable automatic LSP server downloads | `OPENCODE_ENABLE_EXPERIMENTAL_MODELS` | boolean | Enable experimental models | `OPENCODE_DISABLE_AUTOCOMPACT` | boolean | Disable automatic context compaction | `OPENCODE_DISABLE_CLAUDE_CODE` | boolean | Disable reading from `.claude` (prompt + skills) | `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT` | boolean | Disable reading `~/.claude/CLAUDE.md` | `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS` | boolean | Disable loading `.claude/skills` | `OPENCODE_DISABLE_MODELS_FETCH` | boolean | Disable fetching models from remote sources | `OPENCODE_FAKE_VCS` | string | Fake VCS provider for testing purposes | `OPENCODE_DISABLE_FILETIME_CHECK` | boolean | Disable file time checking for optimization | `OPENCODE_CLIENT` | string | Client identifier (defaults to `cli` ) | `OPENCODE_ENABLE_EXA` | boolean | Enable Exa web search tools | `OPENCODE_SERVER_PASSWORD` | string | Enable basic auth for `serve` /`web` | `OPENCODE_SERVER_USERNAME` | string | Override basic auth username (default `opencode` ) | `OPENCODE_MODELS_URL` | string | Custom URL for fetching models configuration |

These environment variables enable experimental features that may change or be removed.

| Variable | Type | Description |
|---|---|---|
`OPENCODE_EXPERIMENTAL` | boolean | Enable all experimental features | `OPENCODE_EXPERIMENTAL_ICON_DISCOVERY` | boolean | Enable icon discovery | `OPENCODE_EXPERIMENTAL_DISABLE_COPY_ON_SELECT` | boolean | Disable copy on select in TUI | `OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS` | number | Default timeout for bash commands in ms | `OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX` | number | Max output tokens for LLM responses | `OPENCODE_EXPERIMENTAL_FILEWATCHER` | boolean | Enable file watcher for entire dir | `OPENCODE_EXPERIMENTAL_OXFMT` | boolean | Enable oxfmt formatter | `OPENCODE_EXPERIMENTAL_LSP_TOOL` | boolean | Enable experimental LSP tool | `OPENCODE_EXPERIMENTAL_DISABLE_FILEWATCHER` | boolean | Disable file watcher | `OPENCODE_EXPERIMENTAL_EXA` | boolean | Enable experimental Exa features | `OPENCODE_EXPERIMENTAL_LSP_TY` | boolean | Enable experimental LSP type checking | `OPENCODE_EXPERIMENTAL_MARKDOWN` | boolean | Enable experimental markdown features | `OPENCODE_EXPERIMENTAL_PLAN_MODE` | boolean | Enable plan mode |
