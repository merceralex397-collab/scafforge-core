---
source_url: https://opencode.ai/docs/sdk
fetched_with: http
---

# SDK

Type-safe JS client for opencode server.

The opencode JS/TS SDK provides a type-safe client for interacting with the server. Use it to build integrations and control opencode programmatically.

Learn more about how the server works. For examples, check out the projects built by the community.

Install the SDK from npm:

Create an instance of opencode:

This starts both a server and a client

| Option | Type | Description | Default |
|---|---|---|---|
`hostname` | `string` | Server hostname | `127.0.0.1` | `port` | `number` | Server port | `4096` | `signal` | `AbortSignal` | Abort signal for cancellation | `undefined` | `timeout` | `number` | Timeout in ms for server start | `5000` | `config` | `Config` | Configuration object | `{}` |

You can pass a configuration object to customize behavior. The instance still picks up your `opencode.json`

, but you can override or add configuration inline:

If you already have a running instance of opencode, you can create a client instance to connect to it:

| Option | Type | Description | Default |
|---|---|---|---|
`baseUrl` | `string` | URL of the server | `http://localhost:4096` | `fetch` | `function` | Custom fetch implementation | `globalThis.fetch` | `parseAs` | `string` | Response parsing method | `auto` | `responseStyle` | `string` | Return style: `data` or `fields` | `fields` | `throwOnError` | `boolean` | Throw errors instead of return | `false` |

The SDK includes TypeScript definitions for all API types. Import them directly:

All types are generated from the server’s OpenAPI specification and available in the types file.

The SDK can throw errors that you can catch and handle:

You can request structured JSON output from the model by specifying an `format`

with a JSON schema. The model will use a `StructuredOutput`

tool to return validated JSON matching your schema.

| Type | Description |
|---|---|
`text` | Default. Standard text response (no structured output) | `json_schema` | Returns validated JSON matching the provided schema |

When using `type: 'json_schema'`

, provide:

| Field | Type | Description |
|---|---|---|
`type` | `'json_schema'` | Required. Specifies JSON schema mode | `schema` | `object` | Required. JSON Schema object defining the output structure | `retryCount` | `number` | Optional. Number of validation retries (default: 2) |

If the model fails to produce valid structured output after all retries, the response will include a `StructuredOutputError`

:

**Provide clear descriptions**in your schema properties to help the model understand what data to extract**Use**to specify which fields must be present`required`

**Keep schemas focused**- complex nested schemas may be harder for the model to fill correctly**Set appropriate**- increase for complex schemas, decrease for simple ones`retryCount`

The SDK exposes all server APIs through a type-safe client.

| Method | Description | Response |
|---|---|---|
`global.health()` | Check server health and version | `{ healthy: true, version: string }` |

| Method | Description | Response |
|---|---|---|
`app.log()` | Write a log entry | `boolean` | `app.agents()` | List all available agents | `Agent[]` |

| Method | Description | Response |
|---|---|---|
`project.list()` | List all projects | `Project[]` | `project.current()` | Get current project | `Project` |

| Method | Description | Response |
|---|---|---|
`path.get()` | Get current path | `Path` |

| Method | Description | Response |
|---|---|---|
`config.get()` | Get config info | `Config` | `config.providers()` | List providers and default models | `{ providers: ` `Provider[]` `, default: { [key: string]: string } }` |

| Method | Description | Notes |
|---|---|---|
`session.list()` | List sessions | Returns `Session[]` | `session.get({ path })` | Get session | Returns `Session` | `session.children({ path })` | List child sessions | Returns `Session[]` | `session.create({ body })` | Create session | Returns `Session` | `session.delete({ path })` | Delete session | Returns `boolean` | `session.update({ path, body })` | Update session properties | Returns `Session` | `session.init({ path, body })` | Analyze app and create `AGENTS.md` | Returns `boolean` | `session.abort({ path })` | Abort a running session | Returns `boolean` | `session.share({ path })` | Share session | Returns `Session` | `session.unshare({ path })` | Unshare session | Returns `Session` | `session.summarize({ path, body })` | Summarize session | Returns `boolean` | `session.messages({ path })` | List messages in a session | Returns `{ info: ` `Message` `, parts: ` `Part[]` `}[]` | `session.message({ path })` | Get message details | Returns `{ info: ` `Message` `, parts: ` `Part[]` `}` | `session.prompt({ path, body })` | Send prompt message | `body.noReply: true` returns UserMessage (context only). Default returns `AssistantMessage` with AI response. Supports `body.outputFormat` for structured output | `session.command({ path, body })` | Send command to session | Returns `{ info: ` `AssistantMessage` `, parts: ` `Part[]` `}` | `session.shell({ path, body })` | Run a shell command | Returns `AssistantMessage` | `session.revert({ path, body })` | Revert a message | Returns `Session` | `session.unrevert({ path })` | Restore reverted messages | Returns `Session` | `postSessionByIdPermissionsByPermissionId({ path, body })` | Respond to a permission request | Returns `boolean` |

| Method | Description | Response |
|---|---|---|
`find.text({ query })` | Search for text in files | Array of match objects with `path` , `lines` , `line_number` , `absolute_offset` , `submatches` | `find.files({ query })` | Find files and directories by name | `string[]` (paths) | `find.symbols({ query })` | Find workspace symbols | `Symbol[]` | `file.read({ query })` | Read a file | `{ type: "raw" | "patch", content: string }` | `file.status({ query? })` | Get status for tracked files | `File[]` |

`find.files`

supports a few optional query fields:

`type`

:`"file"`

or`"directory"`

`directory`

: override the project root for the search`limit`

: max results (1–200)

| Method | Description | Response |
|---|---|---|
`tui.appendPrompt({ body })` | Append text to the prompt | `boolean` | `tui.openHelp()` | Open the help dialog | `boolean` | `tui.openSessions()` | Open the session selector | `boolean` | `tui.openThemes()` | Open the theme selector | `boolean` | `tui.openModels()` | Open the model selector | `boolean` | `tui.submitPrompt()` | Submit the current prompt | `boolean` | `tui.clearPrompt()` | Clear the prompt | `boolean` | `tui.executeCommand({ body })` | Execute a command | `boolean` | `tui.showToast({ body })` | Show toast notification | `boolean` |

| Method | Description | Response |
|---|---|---|
`auth.set({ ... })` | Set authentication credentials | `boolean` |

| Method | Description | Response |
|---|---|---|
`event.subscribe()` | Server-sent events stream | Server-sent events stream |
