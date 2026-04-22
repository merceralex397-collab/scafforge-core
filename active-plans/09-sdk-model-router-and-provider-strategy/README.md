# SDK, Model Router, And Provider Strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** DONE
**Goal:** Lock the architecture for how Scafforge should combine OpenCode, the Vercel AI SDK, the OpenAI Apps SDK, and a mixed-provider model router without forcing a premature rewrite.

**Architecture:** Keep OpenCode as the execution substrate for Scafforge-generated repos and package contracts. Use the AI SDK around that substrate for new orchestration services, provider abstraction, and model routing. Use the OpenAI Apps SDK only for ChatGPT-facing app/MCP surfaces. The router itself should live in an adjacent service layer, not inside the package core. Model availability and transport path must be treated as separate concerns: the same model family may be reachable through a native provider SDK, an OpenAI-compatible or Anthropic-compatible adapter, the AI SDK, and OpenCode.

**Tech Stack / Surfaces:** OpenCode config and SDK assumptions, Vercel AI SDK, OpenAI Apps SDK, provider adapters, adjacent orchestration services, package architecture/docs.
**Depends On:** None for planning; implementation should happen before `06`, `07`, and `10`.
**Unblocks:** spec factory implementation, downstream orchestration, control-plane app, and background agents that need provider failover.
**Primary Sources:** current OpenCode docs (`https://opencode.ai/docs/agents/`, `https://opencode.ai/docs/permissions/`, `https://opencode.ai/docs/sdk/`), current AI SDK docs (`https://ai-sdk.dev/docs/agents/overview`, `https://ai-sdk.dev/docs/agents/building-agents`), current OpenAI Apps SDK docs exposed through OpenAI Developers.

---

## Architecture decision

The planning answer is hybrid, not rewrite-first:

- **OpenCode** remains the repo-execution substrate because Scafforge already depends on its session, agent, permission, and generated repo conventions.
- **OpenCode** must be treated as a host and execution substrate, not as a tiny fixed model catalog. It may front many external providers and account-backed routes, including GitHub Copilot, Gemini, OpenRouter-backed models, Minimax, Fireworks-hosted models, and similar paths where OpenCode compatibility exists.
- **AI SDK** should power new service-side orchestration, tool-loop agents, provider routing, and MCP-capable services.
- **OpenAI Apps SDK** should only power ChatGPT-facing MCP/app ingress and UI surfaces.

This means the router policy must classify both the provider and the access path. “Use OpenCode” does not mean “use only OpenCode-native models.”

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
- a provider-access-path matrix showing which providers or models can be reached via native SDKs, AI SDK adapters, OpenAI-compatible adapters, Anthropic-compatible adapters, and OpenCode
- a model router contract for adjacent services
- rules for how model IDs are verified and updated
- rules for how experimental or account-coupled providers are isolated from package-core guarantees
- rules for how the same model family may be used in multiple contexts, such as coding through OpenCode and multimodal asset work through a native SDK
- at least one small executable prototype proving the hybrid path is real

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

The matrix should also record when the same model family has multiple valid lanes. Example patterns the plan must account for:

- MiniMax M2.7 may be used through the MiniMax native SDK for image, music, TTS, video, or multimodal asset workflows and also through OpenCode for coding or implementation work
- Kimi K2.5 Turbo may be reachable through Fireworks or other compatible routes for both orchestration and implementation work
- GitHub Copilot free models, Gemini free-tier models, and other account-backed options may be reachable through OpenCode even though they are not package-owned providers

## Package and adjacent surfaces likely to change during implementation

- `architecture.md`
- `references/stack-adapter-contract.md`
- `skills/agent-prompt-engineering/references/model-notes/README.md`
- `skills/agent-prompt-engineering/references/model-notes/minimax-m2.7.md`
- new package reference docs for provider and routing policy
- adjacent service repos for model routing, spec factory, orchestration, and ChatGPT app surfaces

`AGENTS.md` should only change if a short pointer to the new durable provider-policy reference docs is truly needed. It is not a primary home for provider strategy.

## Router contract artifact decision

The router contract should have two layers:

- package-level summary:
  - `references/provider-router-policy.md`
- adjacent service contract:
  - service-local contract doc or schema in the adjacent router/orchestration repo

Scafforge should document the policy and boundary. The executable router interface itself belongs in the adjacent service layer, not in package core.

## Validation approach

This plan is documentation-heavy, but it still needs executable proof and machine-checkable presence requirements.

- extend `scripts/validate_scafforge_contract.py` to require the named package-side policy docs this plan creates
- require a small runnable prototype that proves AI SDK can route a provider while OpenCode still executes repo work
- record the prototype result in a committed reference or proof note so reviewers can verify it in a PR diff
- require the matrix to distinguish coding or implementation use, orchestration use, embeddings or retrieval use, and multimodal asset-media use instead of flattening all model access into one bucket

## Phase plan

### Phase 1: Freeze the architecture decision

- [x] Write an ADR that names OpenCode, AI SDK, and Apps SDK roles clearly.
- [x] Explain exactly why replacing OpenCode inside existing package and generated-repo contracts is out of scope for this upgrade cycle.
- [x] Define which future systems must consume OpenCode-generated repos as-is and which systems may be AI SDK-native.
- [x] Ensure the docs explain this decision in user language, not only architecture shorthand.

### Phase 2: Classify providers and trust levels

- [x] Build a provider matrix that records integration path, pricing posture, stability, credential model, intended use class, and AI SDK support tier.
- [x] Record access paths separately from provider names: native SDK, AI SDK adapter, OpenAI-compatible adapter, Anthropic-compatible adapter, and OpenCode route.
- [x] Separate direct API integrations from account-coupled or unofficial routes such as personal subscription scraping or account borrowing patterns.
- [x] Add an explicit AI SDK support tier column: first-party, community, OpenAI-compatible, or unsupported.
- [x] Add intended use columns that distinguish implementation or coding work, orchestration work, embeddings or retrieval work, and multimodal asset-media work.
- [x] Explicitly model same-family multi-path cases, such as MiniMax or Kimi being available through both native provider lanes and OpenCode-compatible coding lanes.
- [x] Define which providers may ever become package defaults and which remain optional experimental lanes.
- [x] Define how free providers are used without turning brittle freebies into the product’s source of truth.

### Phase 3: Define the router contract

- [x] Specify the router interface that adjacent services should call: capability requested, cost tier, fallback order, timeout policy, and trace metadata.
- [x] Publish the package-side summary in `references/provider-router-policy.md` and keep executable router details in the adjacent service repo.
- [x] Decide where provider credentials live and how the control plane can manage them without leaking into package docs.
- [x] Ensure the router can choose between native SDK paths and OpenCode-executed paths intentionally instead of assuming one transport per provider.
- [x] Define how the router records which provider and model were used for each job.
- [x] Ensure the router can degrade gracefully when only experimental/free providers are available.

### Phase 4: Define model-ID and provider-update policy

- [x] Explicitly ban durable package docs from hard-coding volatile model IDs as long-lived truth.
- [x] Require implementation-time model verification against current provider docs or APIs.
- [x] Define where exact model IDs may live safely: service config, environment-specific settings, or test fixtures.
- [x] Update `architecture.md` to remove or replace stale model-ID strings such as the current `minimax-coding-plan/MiniMax-M2.7` reference with category-level wording that matches this policy.
- [x] Ensure prompt/model notes in Scafforge stay high-level enough not to go stale immediately.

### Phase 5: Validate the hybrid path with a real prototype

- [x] Build a small runnable prototype where AI SDK routes a provider but OpenCode still executes repo work.
- [x] Validate that Apps SDK use remains bounded to ChatGPT-facing ingress or UI surfaces.
- [x] Confirm the router contract does not force package-core code to depend on AI SDK semantics.
- [x] Ensure review, audit, and restart evidence can still record provider usage cleanly.
- [x] Commit a short proof note or artifact summary that reviewers can inspect alongside the prototype.

## Validation and proof requirements

- the package has a clear written answer to “would AI SDK require a big rewrite?”
- provider categories, trust levels, and AI SDK support tiers are documented
- adjacent services can use a router without changing the generated-repo contract
- exact model IDs are handled as implementation-time config, not durable package truth
- contract validators check for the required package-side reference artifacts
- a small executable prototype proves the hybrid path is real

## Risks and guardrails

- Do not smuggle an AI SDK rewrite into package-core work.
- Do not promise unsupported providers just because they are free today.
- Do not let account-coupled or unofficial routes become required for normal operation.
- Keep provider policy separate from prompt policy; model choice should not silently rewrite workflow contracts.
- Keep executable router semantics out of package-core code unless a later plan explicitly changes that boundary.
- Do not collapse “provider,” “SDK,” and “execution host” into one concept; the same model may legitimately appear through multiple lanes with different guarantees.

## Documentation updates required when this plan is implemented

- `architecture.md`
- package reference docs for provider and routing policy
- model notes and prompt-engineering docs where provider assumptions appear
- service-level docs in adjacent repos that consume the router

## Completion criteria

- the hybrid architecture is frozen and documented
- provider categories, AI SDK support tiers, and fallback rules are explicit
- implementation teams know when to use OpenCode, AI SDK, or Apps SDK
- package docs no longer imply a hidden rewrite is coming
- a runnable prototype demonstrates the layering in practice
