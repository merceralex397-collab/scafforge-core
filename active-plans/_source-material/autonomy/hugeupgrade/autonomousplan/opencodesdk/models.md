---
source_url: https://opencode.ai/docs/models
fetched_with: http
---

# Models

Configuring an LLM provider and model.

OpenCode uses the AI SDK and Models.dev to support **75+ LLM providers** and it supports running local models.

Most popular providers are preloaded by default. If you’ve added the credentials for a provider through the `/connect`

command, they’ll be available when you start OpenCode.

Learn more about providers.

Once you’ve configured your provider you can select the model you want by typing in:

There are a lot of models out there, with new models coming out every week.

However, there are only a few of them that are good at both generating code and tool calling.

Here are several models that work well with OpenCode, in no particular order. (This is not an exhaustive list nor is it necessarily up to date):

- GPT 5.2
- GPT 5.1 Codex
- Claude Opus 4.5
- Claude Sonnet 4.5
- Minimax M2.1
- Gemini 3 Pro

To set one of these as the default model, you can set the `model`

key in your OpenCode config.

Here the full ID is `provider_id/model_id`

. For example, if you’re using OpenCode Zen, you would use `opencode/gpt-5.1-codex`

for GPT 5.1 Codex.

If you’ve configured a custom provider, the `provider_id`

is key from the `provider`

part of your config, and the `model_id`

is the key from `provider.models`

.

You can globally configure a model’s options through the config.

Here we’re configuring global settings for two built-in models: `gpt-5`

when accessed via the `openai`

provider, and `claude-sonnet-4-20250514`

when accessed via the `anthropic`

provider. The built-in provider and model names can be found on Models.dev.

You can also configure these options for any agents that you are using. The agent config overrides any global options here. Learn more.

You can also define custom variants that extend built-in ones. Variants let you configure different settings for the same model without creating duplicate entries:

Many models support multiple variants with different configurations. OpenCode ships with built-in default variants for popular providers.

OpenCode ships with default variants for many providers:

**Anthropic**:

`high`

- High thinking budget (default)`max`

- Maximum thinking budget

**OpenAI**:

Varies by model but roughly:

`none`

- No reasoning`minimal`

- Minimal reasoning effort`low`

- Low reasoning effort`medium`

- Medium reasoning effort`high`

- High reasoning effort`xhigh`

- Extra high reasoning effort

**Google**:

`low`

- Lower effort/token budget`high`

- Higher effort/token budget

You can override existing variants or add your own:

Use the keybind `variant_cycle`

to quickly switch between variants. Learn more.

When OpenCode starts up, it checks for models in the following priority order:

-
The

`--model`

or`-m`

command line flag. The format is the same as in the config file:`provider_id/model_id`

. - The model list in the OpenCode config.

The format here is

`provider/model`

. - The last used model.

-
The first model using an internal priority.
