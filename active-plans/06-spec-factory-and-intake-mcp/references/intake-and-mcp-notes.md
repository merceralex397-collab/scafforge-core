# Intake And MCP Notes

## Official Product Inputs

- OpenAI Developers homepage: Apps SDK extends ChatGPT with apps built on top of MCP
- OpenAI resources page: Apps SDK examples are an official starting point
- AI SDK MCP docs: `createMCPClient()` is suitable for tool/resource/prompt access in services
- AI SDK OpenAI provider docs: `openai.tools.mcp` is available when using OpenAI Responses models

## Planning Consequence

- Use the Apps SDK only for ChatGPT-facing app or ingress surfaces.
- Use the AI SDK or direct service code for backend orchestration inside the spec factory.
- Keep Scafforge package contracts separate from the spec-factory runtime.

## Primary Local Inputs

- `../../_source-material/autonomy/hugeupgrade/scafforgeautonomousnotes.md`
- `../../_source-material/autonomy/hugeupgrade/ScafforgeAutonomousOrchestrationDRAFTPLAN.md`

## Boundary Reminder

The spec factory should feed Scafforge. It should not become a hidden replacement for `scaffold-kickoff` or `spec-pack-normalizer`.
