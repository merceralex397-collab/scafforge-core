---
source_url: https://opencode.ai/docs/
fetched_with: http
---

# Intro

Get started with OpenCode.

**OpenCode** is an open source AI coding agent. It’s available as a terminal-based interface, desktop app, or IDE extension.

Let’s get started.

To use OpenCode in your terminal, you’ll need:

-
A modern terminal emulator like:

-
API keys for the LLM providers you want to use.

The easiest way to install OpenCode is through the install script.

You can also install it with the following commands:

-
**Using Node.js** -
**Using Homebrew on macOS and Linux**We recommend using the OpenCode tap for the most up to date releases. The official

`brew install opencode`

formula is maintained by the Homebrew team and is updated less frequently. -
**Installing on Arch Linux**

-
**Using Chocolatey** -
**Using Scoop** -
**Using NPM** -
**Using Mise** -
**Using Docker**

Support for installing OpenCode on Windows using Bun is currently in progress.

You can also grab the binary from the Releases.

With OpenCode you can use any LLM provider by configuring their API keys.

If you are new to using LLM providers, we recommend using OpenCode Zen. It’s a curated list of models that have been tested and verified by the OpenCode team.

-
Run the

`/connect`

command in the TUI, select opencode, and head to opencode.ai/auth. - Sign in, add your billing details, and copy your API key.

-
Paste your API key.

Alternatively, you can select one of the other providers. Learn more.

Now that you’ve configured a provider, you can navigate to a project that you want to work on.

And run OpenCode.

Next, initialize OpenCode for the project by running the following command.

This will get OpenCode to analyze your project and create an `AGENTS.md`

file in the project root.

This helps OpenCode understand the project structure and the coding patterns used.

You are now ready to use OpenCode to work on your project. Feel free to ask it anything!

If you are new to using an AI coding agent, here are some examples that might help.

You can ask OpenCode to explain the codebase to you.

This is helpful if there’s a part of the codebase that you didn’t work on.

You can ask OpenCode to add new features to your project. Though we first recommend asking it to create a plan.

-
**Create a plan**OpenCode has a

*Plan mode*that disables its ability to make changes and instead suggest*how*it’ll implement the feature.Switch to it using the

**Tab**key. You’ll see an indicator for this in the lower right corner.Now let’s describe what we want it to do.

You want to give OpenCode enough details to understand what you want. It helps to talk to it like you are talking to a junior developer on your team.

-
**Iterate on the plan**Once it gives you a plan, you can give it feedback or add more details.

OpenCode can scan any images you give it and add them to the prompt. You can do this by dragging and dropping an image into the terminal.

-
**Build the feature**Once you feel comfortable with the plan, switch back to

*Build mode*by hitting the**Tab**key again.And asking it to make the changes.

For more straightforward changes, you can ask OpenCode to directly build it without having to review the plan first.

You want to make sure you provide a good amount of detail so OpenCode makes the right changes.

Let’s say you ask OpenCode to make some changes.

But you realize that it is not what you wanted. You **can undo** the changes using the `/undo`

command.

OpenCode will now revert the changes you made and show your original message again.

From here you can tweak the prompt and ask OpenCode to try again.

Or you **can redo** the changes using the `/redo`

command.

The conversations that you have with OpenCode can be shared with your team.

This will create a link to the current conversation and copy it to your clipboard.

Here’s an example conversation with OpenCode.

And that’s it! You are now a pro at using OpenCode.

To make it your own, we recommend picking a theme, customizing the keybinds, configuring code formatters, creating custom commands, or playing around with the OpenCode config.
