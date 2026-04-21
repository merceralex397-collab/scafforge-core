---
source_url: https://opencode.ai/docs/custom-tools
fetched_with: http
---

# Custom Tools

Create tools the LLM can call in opencode.

Custom tools are functions you create that the LLM can call during conversations. They work alongside opencode’s built-in tools like `read`

, `write`

, and `bash`

.

Tools are defined as **TypeScript** or **JavaScript** files. However, the tool definition can invoke scripts written in **any language** — TypeScript or JavaScript is only used for the tool definition itself.

They can be defined:

- Locally by placing them in the
`.opencode/tools/`

directory of your project. - Or globally, by placing them in `~/.config/opencode/tools/`

.

The easiest way to create tools is using the `tool()`

helper which provides type-safety and validation.

The **filename** becomes the **tool name**. The above creates a `database`

tool.

You can also export multiple tools from a single file. Each export becomes **a separate tool** with the name ** <filename>_<exportname>**:

This creates two tools: `math_add`

and `math_multiply`

.

You can use `tool.schema`

, which is just Zod, to define argument types.

You can also import Zod directly and return a plain object:

Tools receive context about the current session:

Use `context.directory`

for the session working directory. Use `context.worktree`

for the git worktree root.

You can write your tools in any language you want. Here’s an example that adds two numbers using Python.

First, create the tool as a Python script:

Then create the tool definition that invokes it:

Here we are using the `Bun.$`

utility to run the Python script.
