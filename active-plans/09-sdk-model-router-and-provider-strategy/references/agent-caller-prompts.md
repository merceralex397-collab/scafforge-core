# Agent Caller Prompts

## planchecker
{{COMMON_PLANCHECKER}}

Plan-specific focus:
- verify the plan really preserves OpenCode as the execution substrate instead of accidentally rewriting around AI SDK
- check the provider matrix, trust classes, and model-ID policy for volatility and realism
- confirm free or account-coupled providers are isolated from package-core guarantees

## planimplementer
{{COMMON_PLANIMPLEMENTER}}

Plan-specific focus:
- implement the architecture decision, provider-classification matrix, router contract, and model-update policy
- keep router logic in adjacent services rather than inside package-core code paths
- ensure ChatGPT-facing ingress stays bounded to Apps SDK surfaces

## planprreviewer methodology
{{COMMON_PR_REVIEW_METHODOLOGY}}

Plan-specific review focus:
- check for any quiet reintroduction of “rewrite everything around AI SDK”
- verify provider categories, credential handling, and trust levels are documented and enforceable
- look for stale hard-coded model IDs or package docs that pretend volatile providers are stable truth

## planprreviewer big-pickle
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: architecture risk, provider fallback holes, and places where the hybrid decision is not actually preserved.

## planprreviewer minimax-m2.7
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: router lifecycle coherence, model-selection policy, and contradictions between package-core and adjacent services.

## planprreviewer devstral-2512
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: concrete implementation gaps in configs, adapters, service boundaries, and validation artifacts.

## planprreviewer mistral-large-latest
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: documentation and contract consistency across OpenCode, AI SDK, Apps SDK, and provider notes.

## planprreviewer kimi-k2.5-turbo
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: practical operator experience with free providers, degraded-mode routing, and whether the architecture remains maintainable.



