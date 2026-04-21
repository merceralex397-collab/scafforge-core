# SDK And Provider Notes

## Current Official Evidence

- OpenCode SDK: [https://opencode.ai/docs/sdk/](https://opencode.ai/docs/sdk/)
  - exposes session, project, config, path, file, and app APIs suitable for controlling OpenCode programmatically
- OpenCode agents: [https://opencode.ai/docs/agents/](https://opencode.ai/docs/agents/)
  - exposes primary/subagent concepts, permissions, model overrides, and agent configuration
- AI SDK Agent interface: [https://ai-sdk.dev/docs/reference/ai-sdk-core/agent](https://ai-sdk.dev/docs/reference/ai-sdk-core/agent)
  - shows the AI SDK is suitable for reusable agent wrappers and `ToolLoopAgent`-style orchestration
- AI SDK MCP docs: [https://ai-sdk.dev/docs/ai-sdk-core/mcp-tools](https://ai-sdk.dev/docs/ai-sdk-core/mcp-tools)
  - confirms backend services can connect to MCP servers through `createMCPClient()`
- AI SDK OpenAI provider docs: [https://ai-sdk.dev/providers/ai-sdk-providers/openai](https://ai-sdk.dev/providers/ai-sdk-providers/openai)
  - confirms OpenAI models can use provider-defined MCP via `openai.tools.mcp`
- AI SDK MiniMax provider: [https://ai-sdk.dev/providers/community-providers/minimax](https://ai-sdk.dev/providers/community-providers/minimax)
  - confirms there is a current community MiniMax provider
- AI SDK Fireworks provider: [https://ai-sdk.dev/providers/ai-sdk-providers/fireworks](https://ai-sdk.dev/providers/ai-sdk-providers/fireworks)
  - confirms current first-party Fireworks support
- AI SDK OpenRouter provider: [https://ai-sdk.dev/providers/community-providers/openrouter](https://ai-sdk.dev/providers/community-providers/openrouter)
  - confirms OpenRouter is a viable provider path
- AI SDK OpenAI-compatible provider docs: [https://ai-sdk.dev/providers/openai-compatible-providers](https://ai-sdk.dev/providers/openai-compatible-providers)
  - confirms generic OpenAI-compatible services can be wrapped cleanly
- AI SDK MCP Sampling provider: [https://ai-sdk.dev/providers/community-providers/mcp-sampling](https://ai-sdk.dev/providers/community-providers/mcp-sampling)
  - relevant if you want to leverage client subscriptions such as VS Code + Copilot through MCP sampling, but only in compatible contexts
- OpenAI Developers: [https://developers.openai.com/](https://developers.openai.com/)
  - confirms the Apps SDK is the ChatGPT-facing app surface built on MCP

## Planning Answer To The Rewrite Question

Switching Scafforge wholesale from OpenCode to the AI SDK would be a significant rewrite because current package and generated-repo assumptions already depend on:

- `.opencode/` surfaces
- OpenCode session and agent concepts
- OpenCode tool/permission models
- generated repo workflows oriented around OpenCode runtime behavior

The practical move is not replacement. It is layering:

- OpenCode for current package and generated-repo execution
- AI SDK for new orchestration and provider routing services
- Apps SDK for ChatGPT-facing surfaces only

## Provider Strategy Direction

- `core`: MiniMax, Fireworks, Gemini, OpenRouter, Mistral/Devstral through a supported provider path, OpenAI/Codex when budget allows
- `experimental or conditional`: OpenCode free model paths, MCP sampling/Copilot-derived paths, niche community providers, temporary free-tier gateways with unstable SLAs
- `rule`: verify exact model IDs at implementation time, not in durable plan docs

## Practical Mapping For The User’s Candidate Providers

- MiniMax: current community AI SDK provider exists
- Fireworks: current first-party AI SDK provider exists
- Gemini: route through a supported AI SDK provider or the gateway during implementation
- OpenRouter: current community AI SDK provider exists and is a practical home for many free/open models
- Mistral/Devstral and similar open models: prefer OpenRouter or another supported provider adapter unless a first-party route is chosen later
- GitHub Copilot free models: treat as experimental unless the implementation intentionally uses MCP sampling or another supported client-subscription path
- OpenCode free model lanes: treat as execution-environment-specific, not the foundation of the package contract
