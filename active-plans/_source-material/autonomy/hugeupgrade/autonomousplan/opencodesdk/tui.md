---
source_url: https://opencode.ai/docs/tui
fetched_with: http
---

# TUI

Using the OpenCode terminal user interface.

OpenCode provides an interactive terminal interface or TUI for working on your projects with an LLM.

Running OpenCode starts the TUI for the current directory.

Or you can start it for a specific working directory.

Once you’re in the TUI, you can prompt it with a message.

You can reference files in your messages using `@`

. This does a fuzzy file search in the current working directory.

The content of the file is added to the conversation automatically.

Start a message with `!`

to run a shell command.

The output of the command is added to the conversation as a tool result.

When using the OpenCode TUI, you can type `/`

followed by a command name to quickly execute actions. For example:

Most commands also have keybind using `ctrl+x`

as the leader key, where `ctrl+x`

is the default leader key. Learn more.

Here are all available slash commands:

Add a provider to OpenCode. Allows you to select from available providers and add their API keys.

Compact the current session. *Alias*: `/summarize`

**Keybind:** `ctrl+x c`

Toggle tool execution details.

**Keybind:** `ctrl+x d`

Open external editor for composing messages. Uses the editor set in your `EDITOR`

environment variable. Learn more.

**Keybind:** `ctrl+x e`

Exit OpenCode. *Aliases*: `/quit`

, `/q`

**Keybind:** `ctrl+x q`

Export current conversation to Markdown and open in your default editor. Uses the editor set in your `EDITOR`

environment variable. Learn more.

**Keybind:** `ctrl+x x`

Show the help dialog.

**Keybind:** `ctrl+x h`

Create or update `AGENTS.md`

file. Learn more.

**Keybind:** `ctrl+x i`

List available models.

**Keybind:** `ctrl+x m`

Start a new session. *Alias*: `/clear`

**Keybind:** `ctrl+x n`

Redo a previously undone message. Only available after using `/undo`

.

Internally, this uses Git to manage the file changes. So your project **needs to be a Git repository**.

**Keybind:** `ctrl+x r`

List and switch between sessions. *Aliases*: `/resume`

, `/continue`

**Keybind:** `ctrl+x l`

Share current session. Learn more.

**Keybind:** `ctrl+x s`

List available themes.

**Keybind:** `ctrl+x t`

Toggle the visibility of thinking/reasoning blocks in the conversation. When enabled, you can see the model’s reasoning process for models that support extended thinking.

Undo last message in the conversation. Removes the most recent user message, all subsequent responses, and any file changes.

Internally, this uses Git to manage the file changes. So your project **needs to be a Git repository**.

**Keybind:** `ctrl+x u`

Unshare current session. Learn more.

Both the `/editor`

and `/export`

commands use the editor specified in your `EDITOR`

environment variable.

To make it permanent, add this to your shell profile; `~/.bashrc`

, `~/.zshrc`

, etc.

To make it permanent, use **System Properties** > **Environment Variables**.

To make it permanent, add this to your PowerShell profile.

Popular editor options include:

`code`

- Visual Studio Code`cursor`

- Cursor`windsurf`

- Windsurf`nvim`

- Neovim editor`vim`

- Vim editor`nano`

- Nano editor`notepad`

- Windows Notepad`subl`

- Sublime Text

Some editors need command-line arguments to run in blocking mode. The `--wait`

flag makes the editor process block until closed.

You can customize TUI behavior through your OpenCode config file.

`scroll_acceleration`

- Enable macOS-style scroll acceleration for smooth, natural scrolling. When enabled, scroll speed increases with rapid scrolling gestures and stays precise for slower movements.**This setting takes precedence over**`scroll_speed`

and overrides it when enabled.`scroll_speed`

- Controls how fast the TUI scrolls when using scroll commands (minimum:`1`

). Defaults to`3`

.**Note: This is ignored if**`scroll_acceleration.enabled`

is set to`true`

.

You can customize various aspects of the TUI view using the command palette (`ctrl+x h`

or `/help`

). These settings persist across restarts.

Toggle whether your username appears in chat messages. Access this through:

- Command palette: Search for “username” or “hide username”
- The setting persists automatically and will be remembered across TUI sessions
