# SDK, Model Router, And Provider Strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** TODO
**Goal:** Lock the architecture for how Scafforge should combine OpenCode, the Vercel AI SDK, the OpenAI Apps SDK, and a mixed-provider model router without forcing a premature rewrite.

**Architecture:** Keep OpenCode as the execution substrate for Scafforge-generated repos and package contracts. Use the AI SDK around that substrate for new orchestration services, provider abstraction, and model routing. Use the OpenAI Apps SDK only for ChatGPT-facing app/MCP surfaces. The router itself should live in an adjacent service layer, not inside the package core.

**Tech Stack / Surfaces:** OpenCode config and SDK assumptions, Vercel AI SDK, OpenAI Apps SDK, provider adapters, adjacent orchestration services, package architecture/docs.
**Depends On:** None for planning; implementation should happen before `06`, `07`, and `10`.
**Unblocks:** spec factory implementation, downstream orchestration, control-plane app, and background agents that need provider failover.
**Primary Sources:** current OpenCode docs (`https://opencode.ai/docs/agents/`, `https://opencode.ai/docs/permissions/`, `https://opencode.ai/docs/sdk/`), current AI SDK docs (`https://ai-sdk.dev/docs/agents/overview`, `https://ai-sdk.dev/docs/agents/building-agents`), current OpenAI Apps SDK docs exposed through OpenAI Developers.

---

## Architecture decision

The planning answer is hybrid, not rewrite-first:

- **OpenCode** remains the repo-execution substrate because Scafforge already depends on its session, agent, permission, and generated repo conventions.
- **AI SDK** should power new service-side orchestration, tool-loop agents, provider routing, and MCP-capable services.
- **OpenAI Apps SDK** should only power ChatGPT-facing MCP/app ingress and UI surfaces.

This is the exact opposite of “rip out OpenCode everywhere.”

## Why this plan exists

The autonomous upgrade needs model routing and multi-provider support, but the user’s provider list mixes several categories:

- direct API providers
- OpenAI-compatible providers
- client-subscription or account-coupled providers
- truly free but unstable or unofficial options
- paid fallback providers

Without a real strategy, Scafforge will either hard-code stale model choices or quietly depend on brittle providers in its core contract.

## Required deliverables

- a written architecture decision record for OpenCode vs AI SDK vs Apps SDK
- a provider classification matrix
- a model router contract for adjacent services
- rules for how model IDs are verified and updated
- rules for how experimental or account-coupled providers are isolated from package-core guarantees

## Provider categories this plan must define

The router should classify providers by integration path and operational trust:

- first-class provider adapters
- OpenAI-compatible adapters
- experimental or account-coupled sources
- paid fallback providers

The user’s current candidate pool should be mapped into those categories, including:

- Minimax
- Fireworks
- Gemini
- OpenRouter
- free OpenCode-backed or unofficial routes
- GitHub Copilot free/personal-account routes
- Mistral/Devstral family
- paid Codex or paid Copilot fallback

Durable package docs should name categories and integration rules, not freeze exact model IDs.

## Package and adjacent surfaces likely to change during implementation

- `architecture.md`
- `AGENTS.md`
- `references/stack-adapter-contract.md`
- `skills/agent-prompt-engineering/references/model-notes/README.md`
- `skills/agent-prompt-engineering/references/model-notes/minimax-m2.7.md`
- new package reference docs for provider and router policy
- adjacent service repos for model routing, spec factory, orchestration, and ChatGPT app surfaces

## Phase plan

### Phase 1: Freeze the architecture decision

- [ ] Write an ADR that names OpenCode, AI SDK, and Apps SDK roles clearly.
- [ ] Explain exactly why replacing OpenCode inside existing package and generated-repo contracts is out of scope for this upgrade cycle.
- [ ] Define which future systems must consume OpenCode-generated repos as-is and which systems may be AI SDK-native.
- [ ] Ensure the docs explain this decision in user language, not only architecture shorthand.

### Phase 2: Classify providers and trust levels

- [ ] Build a provider matrix that records integration path, pricing posture, stability, credential model, and intended use class.
- [ ] Separate direct API integrations from account-coupled or unofficial routes such as personal subscription scraping or account borrowing patterns.
- [ ] Define which providers may ever become package defaults and which remain optional experimental lanes.
- [ ] Define how free providers are used without turning brittle freebies into the product’s source of truth.

### Phase 3: Define the router contract

- [ ] Specify the router interface that adjacent services should call: capability requested, cost tier, fallback order, timeout policy, and trace metadata.
- [ ] Decide where provider credentials live and how the control plane can manage them without leaking into package docs.
- [ ] Define how the router records which provider and model were used for each job.
- [ ] Ensure the router can degrade gracefully when only experimental/free providers are available.

### Phase 4: Define model-ID and provider-update policy

- [ ] Explicitly ban durable package docs from hard-coding volatile model IDs as long-lived truth.
- [ ] Require implementation-time model verification against current provider docs or APIs.
- [ ] Define where exact model IDs may live safely: service config, environment-specific settings, or test fixtures.
- [ ] Ensure prompt/model notes in Scafforge stay high-level enough not to go stale immediately.

### Phase 5: Validate the hybrid path

- [ ] Prototype or design one small workflow where AI SDK routes a provider but OpenCode still executes repo work.
- [ ] Validate that Apps SDK use remains bounded to ChatGPT-facing ingress or UI surfaces.
- [ ] Confirm the router contract does not force package-core code to depend on AI SDK semantics.
- [ ] Ensure review, audit, and restart evidence can still record provider usage cleanly.

## Validation and proof requirements

- the package has a clear written answer to “would AI SDK require a big rewrite?”
- provider categories and trust levels are documented
- adjacent services can use a router without changing the generated-repo contract
- exact model IDs are handled as implementation-time config, not durable package truth

## Risks and guardrails

- Do not smuggle an AI SDK rewrite into package-core work.
- Do not promise unsupported providers just because they are free today.
- Do not let account-coupled or unofficial routes become required for normal operation.
- Keep provider policy separate from prompt policy; model choice should not silently rewrite workflow contracts.

## Documentation updates required when this plan is implemented

- `architecture.md`
- package reference docs for provider and routing policy
- model notes and prompt-engineering docs where provider assumptions appear
- service-level docs in adjacent repos that consume the router

## Completion criteria

- the hybrid architecture is frozen and documented
- provider categories and fallback rules are explicit
- implementation teams know when to use OpenCode, AI SDK, or Apps SDK
- package docs no longer imply a hidden rewrite is coming
