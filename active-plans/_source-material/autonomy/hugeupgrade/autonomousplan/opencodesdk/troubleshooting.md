---
source_url: https://opencode.ai/docs/troubleshooting
fetched_with: http
---

# Troubleshooting

Common issues and how to resolve them.

To debug issues with OpenCode, start by checking the logs and local data it stores on disk.

Log files are written to:

**macOS/Linux**:`~/.local/share/opencode/log/`

**Windows**: Press`WIN+R`

and paste`%USERPROFILE%\.local\share\opencode\log`

Log files are named with timestamps (e.g., `2025-01-09T123456.log`

) and the most recent 10 log files are kept.

You can set the log level with the `--log-level`

command-line option to get more detailed debug information. For example, `opencode --log-level DEBUG`

.

opencode stores session data and other application data on disk at:

**macOS/Linux**:`~/.local/share/opencode/`

**Windows**: Press`WIN+R`

and paste`%USERPROFILE%\.local\share\opencode`

This directory contains:

`auth.json`

- Authentication data like API keys, OAuth tokens`log/`

- Application logs`project/`

- Project-specific data like session and message data- If the project is within a Git repo, it is stored in
`./<project-slug>/storage/`

- If it is not a Git repo, it is stored in
`./global/storage/`

- If the project is within a Git repo, it is stored in

OpenCode Desktop runs a local OpenCode server (the `opencode-cli`

sidecar) in the background. Most issues are caused by a misbehaving plugin, a corrupted cache, or a bad server setting.

- Fully quit and relaunch the app.
- If the app shows an error screen, click
**Restart**and copy the error details. - macOS only:
`OpenCode`

menu ->**Reload Webview**(helps if the UI is blank/frozen).

If the desktop app is crashing on launch, hanging, or behaving strangely, start by disabling plugins.

Open your global config file and look for a `plugin`

key.

**macOS/Linux**:`~/.config/opencode/opencode.jsonc`

(or`~/.config/opencode/opencode.json`

)**macOS/Linux**(older installs):`~/.local/share/opencode/opencode.jsonc`

**Windows**: Press`WIN+R`

and paste`%USERPROFILE%\.config\opencode\opencode.jsonc`

If you have plugins configured, temporarily disable them by removing the key or setting it to an empty array:

OpenCode can also load local plugins from disk. Temporarily move these out of the way (or rename the folder) and restart the desktop app:

**Global plugins****macOS/Linux**:`~/.config/opencode/plugins/`

**Windows**: Press`WIN+R`

and paste`%USERPROFILE%\.config\opencode\plugins`

**Project plugins**(only if you use per-project config)`<your-project>/.opencode/plugins/`

If the app starts working again, re-enable plugins one at a time to find which one is causing the issue.

If disabling plugins doesn’t help (or a plugin install is stuck), clear the cache so OpenCode can rebuild it.

- Quit OpenCode Desktop completely.
- Delete the cache directory:

**macOS**: Finder ->`Cmd+Shift+G`

-> paste`~/.cache/opencode`

**Linux**: delete`~/.cache/opencode`

(or run`rm -rf ~/.cache/opencode`

)**Windows**: Press`WIN+R`

and paste`%USERPROFILE%\.cache\opencode`

- Restart OpenCode Desktop.

OpenCode Desktop can either start its own local server (default) or connect to a server URL you configured.

If you see a **“Connection Failed”** dialog (or the app never gets past the splash screen), check for a custom server URL.

From the Home screen, click the server name (with the status dot) to open the Server picker. In the **Default server** section, click **Clear**.

If your `opencode.json(c)`

contains a `server`

section, temporarily remove it and restart the desktop app.

If you have `OPENCODE_PORT`

set in your environment, the desktop app will try to use that port for the local server.

- Unset
`OPENCODE_PORT`

(or pick a free port) and restart.

On Linux, some Wayland setups can cause blank windows or compositor errors.

- If you’re on Wayland and the app is blank/crashing, try launching with
`OC_ALLOW_WAYLAND=1`

. - If that makes things worse, remove it and try launching under an X11 session instead.

On Windows, OpenCode Desktop requires the Microsoft Edge **WebView2 Runtime**. If the app opens to a blank window or won’t start, install/update WebView2 and try again.

If you’re experiencing slow performance, file access issues, or terminal problems on Windows, try using WSL (Windows Subsystem for Linux). WSL provides a Linux environment that works more seamlessly with OpenCode’s features.

OpenCode Desktop only shows system notifications when:

- notifications are enabled for OpenCode in your OS settings, and
- the app window is not focused.

If the app won’t start and you can’t clear settings from inside the UI, reset the desktop app’s saved state.

- Quit OpenCode Desktop.
- Find and delete these files (they live in the OpenCode Desktop app data directory):

`opencode.settings.dat`

(desktop default server URL)`opencode.global.dat`

and`opencode.workspace.*.dat`

(UI state like recent servers/projects)

To find the directory quickly:

**macOS**: Finder ->`Cmd+Shift+G`

->`~/Library/Application Support`

(then search for the filenames above)**Linux**: search under`~/.local/share`

for the filenames above**Windows**: Press`WIN+R`

->`%APPDATA%`

(then search for the filenames above)

If you’re experiencing issues with OpenCode:

-
**Report issues on GitHub**The best way to report bugs or request features is through our GitHub repository:

Before creating a new issue, search existing issues to see if your problem has already been reported.

-
**Join our Discord**For real-time help and community discussion, join our Discord server:

Here are some common issues and how to resolve them.

- Check the logs for error messages
- Try running with
`--print-logs`

to see output in the terminal - Ensure you have the latest version with `opencode upgrade`

- Try re-authenticating with the
`/connect`

command in the TUI - Check that your API keys are valid
- Ensure your network allows connections to the provider’s API

- Check that you’ve authenticated with the provider
- Verify the model name in your config is correct
- Some models may require specific access or subscriptions

If you encounter `ProviderModelNotFoundError`

you are most likely incorrectly referencing a model somewhere. Models should be referenced like so: `<providerId>/<modelId>`

Examples:

`openai/gpt-4.1`

`openrouter/google/gemini-2.5-flash`

`opencode/kimi-k2`

To figure out what models you have access to, run `opencode models`

If you encounter a ProviderInitError, you likely have an invalid or corrupted configuration.

To resolve this:

-
First, verify your provider is set up correctly by following the providers guide

-
If the issue persists, try clearing your stored configuration:

On Windows, press

`WIN+R`

and delete:`%USERPROFILE%\.local\share\opencode`

-
Re-authenticate with your provider using the

`/connect`

command in the TUI.

If you encounter API call errors, this may be due to outdated provider packages. opencode dynamically installs provider packages (OpenAI, Anthropic, Google, etc.) as needed and caches them locally.

To resolve provider package issues:

-
Clear the provider package cache:

On Windows, press

`WIN+R`

and delete:`%USERPROFILE%\.cache\opencode`

-
Restart opencode to reinstall the latest provider packages

This will force opencode to download the most recent versions of provider packages, which often resolves compatibility issues with model parameters and API changes.

Linux users need to have one of the following clipboard utilities installed for copy/paste functionality to work:

**For X11 systems:**

**For Wayland systems:**

**For headless environments:**

opencode will detect if you’re using Wayland and prefer `wl-clipboard`

, otherwise it will try to find clipboard tools in order of: `xclip`

and `xsel`

.
