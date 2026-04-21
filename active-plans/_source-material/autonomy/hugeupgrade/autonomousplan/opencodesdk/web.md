---
source_url: https://opencode.ai/docs/web
fetched_with: http
---

# Web

Using OpenCode in your browser.

OpenCode can run as a web application in your browser, providing the same powerful AI coding experience without needing a terminal.

Start the web interface by running:

This starts a local server on `127.0.0.1`

with a random available port and automatically opens OpenCode in your default browser.

You can configure the web server using command line flags or in your config file.

By default, OpenCode picks an available port. You can specify a port:

By default, the server binds to `127.0.0.1`

(localhost only). To make OpenCode accessible on your network:

When using `0.0.0.0`

, OpenCode will display both local and network addresses:

Enable mDNS to make your server discoverable on the local network:

This automatically sets the hostname to `0.0.0.0`

and advertises the server as `opencode.local`

.

You can customize the mDNS domain name to run multiple instances on the same network:

To allow additional domains for CORS (useful for custom frontends):

To protect access, set a password using the `OPENCODE_SERVER_PASSWORD`

environment variable:

The username defaults to `opencode`

but can be changed with `OPENCODE_SERVER_USERNAME`

.

Once started, the web interface provides access to your OpenCode sessions.

View and manage your sessions from the homepage. You can see active sessions and start new ones.

Click “See Servers” to view connected servers and their status.

You can attach a terminal TUI to a running web server:

This allows you to use both the web interface and terminal simultaneously, sharing the same sessions and state.

You can also configure server settings in your `opencode.json`

config file:

Command line flags take precedence over config file settings.
