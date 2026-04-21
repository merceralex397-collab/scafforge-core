---
source_url: https://opencode.ai/docs/providers
fetched_with: http
---

# Providers

Using any LLM provider in OpenCode.

OpenCode uses the AI SDK and Models.dev to support **75+ LLM providers** and it supports running local models.

To add a provider you need to:

- Add the API keys for the provider using the
`/connect`

command. - Configure the provider in your OpenCode config.

When you add a provider’s API keys with the `/connect`

command, they are stored in `~/.local/share/opencode/auth.json`

.

You can customize the providers through the `provider`

section in your OpenCode config.

You can customize the base URL for any provider by setting the `baseURL`

option. This is useful when using proxy services or custom endpoints.

OpenCode Zen is a list of models provided by the OpenCode team that have been tested and verified to work well with OpenCode. Learn more.

-
Run the

`/connect`

command in the TUI, select opencode, and head to opencode.ai/auth. - Sign in, add your billing details, and copy your API key.

-
Paste your API key.

-
Run

`/models`

in the TUI to see the list of models we recommend.

It works like any other provider in OpenCode and is completely optional to use.

Let’s look at some of the providers in detail. If you’d like to add a provider to the list, feel free to open a PR.

-
Head over to the 302.AI console, create an account, and generate an API key.

-
Run the

`/connect`

command and search for**302.AI**. - Enter your 302.AI API key.

-
Run the

`/models`

command to select a model.

To use Amazon Bedrock with OpenCode:

-
Head over to the

**Model catalog**in the Amazon Bedrock console and request access to the models you want. -
**Configure authentication**using one of the following methods:Set one of these environment variables while running opencode:

Or add them to your bash profile:

For project-specific or persistent configuration, use

`opencode.json`

:**Available options:**`region`

- AWS region (e.g.,`us-east-1`

,`eu-west-1`

)`profile`

- AWS named profile from`~/.aws/credentials`

`endpoint`

- Custom endpoint URL for VPC endpoints (alias for generic`baseURL`

option)

If you’re using VPC endpoints for Bedrock:

: Create an IAM user and generate access keys in the AWS Console`AWS_ACCESS_KEY_ID`

/`AWS_SECRET_ACCESS_KEY`

: Use named profiles from`AWS_PROFILE`

`~/.aws/credentials`

. First configure with`aws configure --profile my-profile`

or`aws sso login`

: Generate long-term API keys from the Amazon Bedrock console`AWS_BEARER_TOKEN_BEDROCK`

: For EKS IRSA (IAM Roles for Service Accounts) or other Kubernetes environments with OIDC federation. These environment variables are automatically injected by Kubernetes when using service account annotations.`AWS_WEB_IDENTITY_TOKEN_FILE`

/`AWS_ROLE_ARN`

Amazon Bedrock uses the following authentication priority:

**Bearer Token**-`AWS_BEARER_TOKEN_BEDROCK`

environment variable or token from`/connect`

command**AWS Credential Chain**- Profile, access keys, shared credentials, IAM roles, Web Identity Tokens (EKS IRSA), instance metadata

-
Run the

`/models`

command to select the model you want.

-
Once you’ve signed up, run the

`/connect`

command and select Anthropic. - Here you can select the

**Claude Pro/Max**option and it’ll open your browser and ask you to authenticate. -
Now all the Anthropic models should be available when you use the

`/models`

command.

You can also select **Create an API Key** if you don’t have a Pro/Max subscription. It’ll also open your browser and ask you to login to Anthropic and give you a code you can paste in your terminal.

Or if you already have an API key, you can select **Manually enter API Key** and paste it in your terminal.

-
Head over to the Azure portal and create an

**Azure OpenAI**resource. You’ll need:**Resource name**: This becomes part of your API endpoint (`https://RESOURCE_NAME.openai.azure.com/`

)**API key**: Either`KEY 1`

or`KEY 2`

from your resource

-
Go to Azure AI Foundry and deploy a model.

-
Run the

`/connect`

command and search for**Azure**. - Enter your API key.

-
Set your resource name as an environment variable:

Or add it to your bash profile:

-
Run the

`/models`

command to select your deployed model.

-
Head over to the Azure portal and create an

**Azure OpenAI**resource. You’ll need:**Resource name**: This becomes part of your API endpoint (`https://AZURE_COGNITIVE_SERVICES_RESOURCE_NAME.cognitiveservices.azure.com/`

)**API key**: Either`KEY 1`

or`KEY 2`

from your resource

-
Go to Azure AI Foundry and deploy a model.

-
Run the

`/connect`

command and search for**Azure Cognitive Services**. - Enter your API key.

-
Set your resource name as an environment variable:

Or add it to your bash profile:

-
Run the

`/models`

command to select your deployed model.

-
Head over to the Baseten, create an account, and generate an API key.

-
Run the

`/connect`

command and search for**Baseten**. - Enter your Baseten API key.

-
Run the

`/models`

command to select a model.

-
Head over to the Cerebras console, create an account, and generate an API key.

-
Run the

`/connect`

command and search for**Cerebras**. - Enter your Cerebras API key.

-
Run the

`/models`

command to select a model like*Qwen 3 Coder 480B*.

Cloudflare AI Gateway lets you access models from OpenAI, Anthropic, Workers AI, and more through a unified endpoint. With Unified Billing you don’t need separate API keys for each provider.

-
Head over to the Cloudflare dashboard, navigate to

**AI**>**AI Gateway**, and create a new gateway. -
Set your Account ID and Gateway ID as environment variables.

-
Run the

`/connect`

command and search for**Cloudflare AI Gateway**. - Enter your Cloudflare API token.

Or set it as an environment variable.

-
Run the

`/models`

command to select a model.You can also add models through your opencode config.

-
Head over to the Cortecs console, create an account, and generate an API key.

-
Run the

`/connect`

command and search for**Cortecs**. - Enter your Cortecs API key.

-
Run the

`/models`

command to select a model like*Kimi K2 Instruct*.

-
Head over to the DeepSeek console, create an account, and click

**Create new API key**. -
Run the

`/connect`

command and search for**DeepSeek**. - Enter your DeepSeek API key.

-
Run the

`/models`

command to select a DeepSeek model like*DeepSeek Reasoner*.

-
Head over to the Deep Infra dashboard, create an account, and generate an API key.

-
Run the

`/connect`

command and search for**Deep Infra**. - Enter your Deep Infra API key.

-
Run the

`/models`

command to select a model.

-
Head over to the Firmware dashboard, create an account, and generate an API key.

-
Run the

`/connect`

command and search for**Firmware**. - Enter your Firmware API key.

-
Run the

`/models`

command to select a model.

-
Head over to the Fireworks AI console, create an account, and click

**Create API Key**. -
Run the

`/connect`

command and search for**Fireworks AI**. - Enter your Fireworks AI API key.

-
Run the

`/models`

command to select a model like*Kimi K2 Instruct*.

GitLab Duo provides AI-powered agentic chat with native tool calling capabilities through GitLab’s Anthropic proxy.

-
Run the

`/connect`

command and select GitLab. - Choose your authentication method:

Select

**OAuth**and your browser will open for authorization.- Go to GitLab User Settings > Access Tokens
- Click
**Add new token** - Name:
`OpenCode`

, Scopes:`api`

- Copy the token (starts with
`glpat-`

) - Enter it in the terminal

-
Run the

`/models`

command to see available models.Three Claude-based models are available:

**duo-chat-haiku-4-5**(Default) - Fast responses for quick tasks**duo-chat-sonnet-4-5**- Balanced performance for most workflows**duo-chat-opus-4-5**- Most capable for complex analysis

For self-hosted GitLab instances:

If your instance runs a custom AI Gateway:

Or add to your bash profile:

In order to make Oauth working for your self-hosted instance, you need to create a new application (Settings → Applications) with the callback URL `http://127.0.0.1:8080/callback`

and following scopes:

- api (Access the API on your behalf)
- read_user (Read your personal information)
- read_repository (Allows read-only access to the repository)

Then expose application ID as environment variable:

More documentation on opencode-gitlab-auth homepage.

Customize through `opencode.json`

:

To access GitLab tools (merge requests, issues, pipelines, CI/CD, etc.):

This plugin provides comprehensive GitLab repository management capabilities including MR reviews, issue tracking, pipeline monitoring, and more.

To use your GitHub Copilot subscription with opencode:

-
Run the

`/connect`

command and search for GitHub Copilot. - Navigate to github.com/login/device and enter the code.

-
Now run the

`/models`

command to select the model you want.

To use Google Vertex AI with OpenCode:

-
Head over to the

**Model Garden**in the Google Cloud Console and check the models available in your region. -
Set the required environment variables:

`GOOGLE_CLOUD_PROJECT`

: Your Google Cloud project ID`VERTEX_LOCATION`

(optional): The region for Vertex AI (defaults to`global`

)- Authentication (choose one): `GOOGLE_APPLICATION_CREDENTIALS`

: Path to your service account JSON key file- Authenticate using gcloud CLI: `gcloud auth application-default login`

Set them while running opencode.

Or add them to your bash profile.

-
Run the

`/models`

command to select the model you want.

-
Head over to the Groq console, click

**Create API Key**, and copy the key. -
Run the

`/connect`

command and search for Groq. - Enter the API key for the provider.

-
Run the

`/models`

command to select the one you want.

Hugging Face Inference Providers provides access to open models supported by 17+ providers.

-
Head over to Hugging Face settings to create a token with permission to make calls to Inference Providers.

-
Run the

`/connect`

command and search for**Hugging Face**. - Enter your Hugging Face token.

-
Run the

`/models`

command to select a model like*Kimi-K2-Instruct*or*GLM-4.6*.

Helicone is an LLM observability platform that provides logging, monitoring, and analytics for your AI applications. The Helicone AI Gateway routes your requests to the appropriate provider automatically based on the model.

-
Head over to Helicone, create an account, and generate an API key from your dashboard.

-
Run the

`/connect`

command and search for**Helicone**. - Enter your Helicone API key.

-
Run the

`/models`

command to select a model.

For more providers and advanced features like caching and rate limiting, check the Helicone documentation.

In the event you see a feature or model from Helicone that isn’t configured automatically through opencode, you can always configure it yourself.

Here’s Helicone’s Model Directory, you’ll need this to grab the IDs of the models you want to add.

Helicone supports custom headers for features like caching, user tracking, and session management. Add them to your provider config using `options.headers`

:

Helicone’s Sessions feature lets you group related LLM requests together. Use the opencode-helicone-session plugin to automatically log each OpenCode conversation as a session in Helicone.

Add it to your config.

The plugin injects `Helicone-Session-Id`

and `Helicone-Session-Name`

headers into your requests. In Helicone’s Sessions page, you’ll see each OpenCode conversation listed as a separate session.

| Header | Description |
|---|---|
`Helicone-Cache-Enabled` | Enable response caching (`true` /`false` ) | `Helicone-User-Id` | Track metrics by user | `Helicone-Property-[Name]` | Add custom properties (e.g., `Helicone-Property-Environment` ) | `Helicone-Prompt-Id` | Associate requests with prompt versions |

See the Helicone Header Directory for all available headers.

You can configure opencode to use local models through llama.cpp’s llama-server utility

In this example:

`llama.cpp`

is the custom provider ID. This can be any string you want.`npm`

specifies the package to use for this provider. Here,`@ai-sdk/openai-compatible`

is used for any OpenAI-compatible API.`name`

is the display name for the provider in the UI.`options.baseURL`

is the endpoint for the local server.`models`

is a map of model IDs to their configurations. The model name will be displayed in the model selection list.

IO.NET offers 17 models optimized for various use cases:

-
Head over to the IO.NET console, create an account, and generate an API key.

-
Run the

`/connect`

command and search for**IO.NET**. - Enter your IO.NET API key.

-
Run the

`/models`

command to select a model.

You can configure opencode to use local models through LM Studio.

In this example:

`lmstudio`

is the custom provider ID. This can be any string you want.`npm`

specifies the package to use for this provider. Here,`@ai-sdk/openai-compatible`

is used for any OpenAI-compatible API.`name`

is the display name for the provider in the UI.`options.baseURL`

is the endpoint for the local server.`models`

is a map of model IDs to their configurations. The model name will be displayed in the model selection list.

To use Kimi K2 from Moonshot AI:

-
Head over to the Moonshot AI console, create an account, and click

**Create API key**. -
Run the

`/connect`

command and search for**Moonshot AI**. - Enter your Moonshot API key.

-
Run the

`/models`

command to select*Kimi K2*.

-
Head over to the MiniMax API Console, create an account, and generate an API key.

-
Run the

`/connect`

command and search for**MiniMax**. - Enter your MiniMax API key.

-
Run the

`/models`

command to select a model like*M2.1*.

-
Head over to the Nebius Token Factory console, create an account, and click

**Add Key**. -
Run the

`/connect`

command and search for**Nebius Token Factory**. - Enter your Nebius Token Factory API key.

-
Run the

`/models`

command to select a model like*Kimi K2 Instruct*.

You can configure opencode to use local models through Ollama.

In this example:

`ollama`

is the custom provider ID. This can be any string you want.`npm`

specifies the package to use for this provider. Here,`@ai-sdk/openai-compatible`

is used for any OpenAI-compatible API.`name`

is the display name for the provider in the UI.`options.baseURL`

is the endpoint for the local server.`models`

is a map of model IDs to their configurations. The model name will be displayed in the model selection list.

To use Ollama Cloud with OpenCode:

-
Head over to https://ollama.com/ and sign in or create an account.

-
Navigate to

**Settings**>**Keys**and click**Add API Key**to generate a new API key. -
Copy the API key for use in OpenCode.

-
Run the

`/connect`

command and search for**Ollama Cloud**. - Enter your Ollama Cloud API key.

-
**Important**: Before using cloud models in OpenCode, you must pull the model information locally: -
Run the

`/models`

command to select your Ollama Cloud model.

We recommend signing up for ChatGPT Plus or Pro.

-
Once you’ve signed up, run the

`/connect`

command and select OpenAI. - Here you can select the

**ChatGPT Plus/Pro**option and it’ll open your browser and ask you to authenticate. -
Now all the OpenAI models should be available when you use the

`/models`

command.

If you already have an API key, you can select **Manually enter API Key** and paste it in your terminal.

OpenCode Zen is a list of tested and verified models provided by the OpenCode team. Learn more.

-
Sign in to

**OpenCode Zen**and click**Create API Key**. -
Run the

`/connect`

command and search for**OpenCode Zen**. - Enter your OpenCode API key.

-
Run the

`/models`

command to select a model like*Qwen 3 Coder 480B*.

-
Head over to the OpenRouter dashboard, click

**Create API Key**, and copy the key. -
Run the

`/connect`

command and search for OpenRouter. - Enter the API key for the provider.

-
Many OpenRouter models are preloaded by default, run the

`/models`

command to select the one you want.You can also add additional models through your opencode config.

-
You can also customize them through your opencode config. Here’s an example of specifying a provider

SAP AI Core provides access to 40+ models from OpenAI, Anthropic, Google, Amazon, Meta, Mistral, and AI21 through a unified platform.

-
Go to your SAP BTP Cockpit, navigate to your SAP AI Core service instance, and create a service key.

-
Run the

`/connect`

command and search for**SAP AI Core**. - Enter your service key JSON.

Or set the

`AICORE_SERVICE_KEY`

environment variable:Or add it to your bash profile:

-
Optionally set deployment ID and resource group:

-
Run the

`/models`

command to select from 40+ available models.

STACKIT AI Model Serving provides fully managed soverign hosting environment for AI models, focusing on LLMs like Llama, Mistral, and Qwen, with maximum data sovereignty on European infrastructure.

-
Head over to STACKIT Portal, navigate to

**AI Model Serving**, and create an auth token for your project. -
Run the

`/connect`

command and search for**STACKIT**. - Enter your STACKIT AI Model Serving auth token.

-
Run the

`/models`

command to select from available models like*Qwen3-VL 235B*or*Llama 3.3 70B*.

-
Head over to the OVHcloud panel. Navigate to the

`Public Cloud`

section,`AI & Machine Learning`

>`AI Endpoints`

and in`API Keys`

tab, click**Create a new API key**. - Run the

`/connect`

command and search for**OVHcloud AI Endpoints**. - Enter your OVHcloud AI Endpoints API key.

-
Run the

`/models`

command to select a model like*gpt-oss-120b*.

To use Scaleway Generative APIs with Opencode:

-
Head over to the Scaleway Console IAM settings to generate a new API key.

-
Run the

`/connect`

command and search for**Scaleway**. - Enter your Scaleway API key.

-
Run the

`/models`

command to select a model like*devstral-2-123b-instruct-2512*or*gpt-oss-120b*.

-
Head over to the Together AI console, create an account, and click

**Add Key**. -
Run the

`/connect`

command and search for**Together AI**. - Enter your Together AI API key.

-
Run the

`/models`

command to select a model like*Kimi K2 Instruct*.

-
Head over to the Venice AI console, create an account, and generate an API key.

-
Run the

`/connect`

command and search for**Venice AI**. - Enter your Venice AI API key.

-
Run the

`/models`

command to select a model like*Llama 3.3 70B*.

Vercel AI Gateway lets you access models from OpenAI, Anthropic, Google, xAI, and more through a unified endpoint. Models are offered at list price with no markup.

-
Head over to the Vercel dashboard, navigate to the

**AI Gateway**tab, and click**API keys**to create a new API key. -
Run the

`/connect`

command and search for**Vercel AI Gateway**. - Enter your Vercel AI Gateway API key.

-
Run the

`/models`

command to select a model.

You can also customize models through your opencode config. Here’s an example of specifying provider routing order.

Some useful routing options:

| Option | Description |
|---|---|
`order` | Provider sequence to try | `only` | Restrict to specific providers | `zeroDataRetention` | Only use providers with zero data retention policies |

-
Head over to the xAI console, create an account, and generate an API key.

-
Run the

`/connect`

command and search for**xAI**. - Enter your xAI API key.

-
Run the

`/models`

command to select a model like*Grok Beta*.

-
Head over to the Z.AI API console, create an account, and click

**Create a new API key**. -
Run the

`/connect`

command and search for**Z.AI**.If you are subscribed to the

**GLM Coding Plan**, select**Z.AI Coding Plan**. -
Enter your Z.AI API key.

-
Run the

`/models`

command to select a model like*GLM-4.7*.

-
Head over to the ZenMux dashboard, click

**Create API Key**, and copy the key. -
Run the

`/connect`

command and search for ZenMux. - Enter the API key for the provider.

-
Many ZenMux models are preloaded by default, run the

`/models`

command to select the one you want.You can also add additional models through your opencode config.

To add any **OpenAI-compatible** provider that’s not listed in the `/connect`

command:

-
Run the

`/connect`

command and scroll down to**Other**. - Enter a unique ID for the provider.

-
Enter your API key for the provider.

-
Create or update your

`opencode.json`

file in your project directory:Here are the configuration options:

**npm**: AI SDK package to use,`@ai-sdk/openai-compatible`

for OpenAI-compatible providers**name**: Display name in UI.**models**: Available models.**options.baseURL**: API endpoint URL.**options.apiKey**: Optionally set the API key, if not using auth.**options.headers**: Optionally set custom headers.

More on the advanced options in the example below.

-
Run the

`/models`

command and your custom provider and models will appear in the selection list.

Here’s an example setting the `apiKey`

, `headers`

, and model `limit`

options.

Configuration details:

**apiKey**: Set using`env`

variable syntax, learn more.**headers**: Custom headers sent with each request.**limit.context**: Maximum input tokens the model accepts.**limit.output**: Maximum tokens the model can generate.

The `limit`

fields allow OpenCode to understand how much context you have left. Standard providers pull these from models.dev automatically.

If you are having trouble with configuring a provider, check the following:

-
**Check the auth setup**: Run`opencode auth list`

to see if the credentials for the provider are added to your config.This doesn’t apply to providers like Amazon Bedrock, that rely on environment variables for their auth.

-
For custom providers, check the opencode config and:

- Make sure the provider ID used in the
`/connect`

command matches the ID in your opencode config. - The right npm package is used for the provider. For example, use `@ai-sdk/cerebras`

for Cerebras. And for all other OpenAI-compatible providers, use`@ai-sdk/openai-compatible`

. - Check correct API endpoint is used in the `options.baseURL`

field.

- Make sure the provider ID used in the
