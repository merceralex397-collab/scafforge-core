---
source_url: https://opencode.ai/docs/share
fetched_with: http
---

# Share

Share your OpenCode conversations.

OpenCode’s share feature allows you to create public links to your OpenCode conversations, so you can collaborate with teammates or get help from others.

When you share a conversation, OpenCode:

- Creates a unique public URL for your session
- Syncs your conversation history to our servers
- Makes the conversation accessible via the shareable link —
`opncd.ai/s/<share-id>`

OpenCode supports three sharing modes that control how conversations are shared:

By default, OpenCode uses manual sharing mode. Sessions are not shared automatically, but you can manually share them using the `/share`

command:

This will generate a unique URL that’ll be copied to your clipboard.

To explicitly set manual mode in your config file:

You can enable automatic sharing for all new conversations by setting the `share`

option to `"auto"`

in your config file:

With auto-share enabled, every new conversation will automatically be shared and a link will be generated.

You can disable sharing entirely by setting the `share`

option to `"disabled"`

in your config file:

To enforce this across your team for a given project, add it to the `opencode.json`

in your project and check into Git.

To stop sharing a conversation and remove it from public access:

This will remove the share link and delete the data related to the conversation.

There are a few things to keep in mind when sharing a conversation.

Shared conversations remain accessible until you explicitly unshare them. This includes:

- Full conversation history
- All messages and responses
- Session metadata

- Only share conversations that don’t contain sensitive information.
- Review conversation content before sharing.
- Unshare conversations when collaboration is complete.
- Avoid sharing conversations with proprietary code or confidential data.
- For sensitive projects, disable sharing entirely.

For enterprise deployments, the share feature can be:

**Disabled**entirely for security compliance**Restricted**to users authenticated through SSO only**Self-hosted**on your own infrastructure

Learn more about using opencode in your organization.
