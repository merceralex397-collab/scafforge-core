---
source_url: https://opencode.ai/docs/keybinds
fetched_with: http
---

# Keybinds

Customize your keybinds.

OpenCode has a list of keybinds that you can customize through the OpenCode config.

OpenCode uses a `leader`

key for most keybinds. This avoids conflicts in your terminal.

By default, `ctrl+x`

is the leader key and most actions require you to first press the leader key and then the shortcut. For example, to start a new session you first press `ctrl+x`

and then press `n`

.

You don’t need to use a leader key for your keybinds but we recommend doing so.

You can disable a keybind by adding the key to your config with a value of “none”.

The OpenCode desktop app prompt input supports common Readline/Emacs-style shortcuts for editing text. These are built-in and currently not configurable via `opencode.json`

.

| Shortcut | Action |
|---|---|
`ctrl+a` | Move to start of current line | `ctrl+e` | Move to end of current line | `ctrl+b` | Move cursor back one character | `ctrl+f` | Move cursor forward one character | `alt+b` | Move cursor back one word | `alt+f` | Move cursor forward one word | `ctrl+d` | Delete character under cursor | `ctrl+k` | Kill to end of line | `ctrl+u` | Kill to start of line | `ctrl+w` | Kill previous word | `alt+d` | Kill next word | `ctrl+t` | Transpose characters | `ctrl+g` | Cancel popovers / abort running response |

Some terminals don’t send modifier keys with Enter by default. You may need to configure your terminal to send `Shift+Enter`

as an escape sequence.

Open your `settings.json`

at:

Add this to the root-level `actions`

array:

Add this to the root-level `keybindings`

array:

Save the file and restart Windows Terminal or open a new tab.
