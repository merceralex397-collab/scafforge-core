---
source_url: https://opencode.ai/docs/acp
fetched_with: http
---

# ACP Support

Use OpenCode in any ACP-compatible editor.

OpenCode supports the Agent Client Protocol or (ACP), allowing you to use it directly in compatible editors and IDEs.

ACP is an open protocol that standardizes communication between code editors and AI coding agents.

To use OpenCode via ACP, configure your editor to run the `opencode acp`

command.

The command starts OpenCode as an ACP-compatible subprocess that communicates with your editor over JSON-RPC via stdio.

Below are examples for popular editors that support ACP.

Add to your Zed configuration (`~/.config/zed/settings.json`

):

To open it, use the `agent: new thread`

action in the **Command Palette**.

You can also bind a keyboard shortcut by editing your `keymap.json`

:

Add to your JetBrains IDE acp.json according to the documentation:

To open it, use the new ‘OpenCode’ agent in the AI Chat agent selector.

Add to your Avante.nvim configuration:

If you need to pass environment variables:

To use OpenCode as an ACP agent in CodeCompanion.nvim, add the following to your Neovim config:

This config sets up CodeCompanion to use OpenCode as the ACP agent for chat.

If you need to pass environment variables (like `OPENCODE_API_KEY`

), refer to Configuring Adapters: Environment Variables in the CodeCompanion.nvim documentation for full details.

OpenCode works the same via ACP as it does in the terminal. All features are supported:

- Built-in tools (file operations, terminal commands, etc.)
- Custom tools and slash commands
- MCP servers configured in your OpenCode config
- Project-specific rules from
`AGENTS.md`

- Custom formatters and linters
- Agents and permissions system
