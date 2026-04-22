# Provider Router Policy

## Scope

This document is the package-level summary for provider classification, routing, fallback, and model-update policy. It defines the boundary that adjacent services must follow, but it is **not** the executable router contract.

Scafforge package core and generated repos stay OpenCode-oriented. Adjacent services may use the AI SDK to route service-side work. ChatGPT-facing ingress stays bounded to Apps SDK surfaces.

## Package boundary

- Scafforge package docs define provider categories, trust rules, and routing boundaries.
- Adjacent service repos own executable router schemas, credentials, and runtime selection logic.
- The router may choose between native SDK lanes, AI SDK provider lanes, OpenAI-compatible lanes, Anthropic-compatible lanes, and OpenCode execution lanes.
- Package-core logic must not depend on AI SDK router semantics to keep existing package and generated-repo contracts stable.

## Provider classification matrix

| Provider or lane | Category | Credential posture | Pricing posture | Stability / trust | AI SDK support tier | Default eligibility | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MiniMax family | First-class provider adapter | Service-managed provider credential | Mixed paid / promotional | Medium | Community or native-provider lane | Optional adjacent-service default after implementation-time verification | Strong candidate for multimodal asset/media work through native SDKs; may also appear through OpenCode-compatible coding lanes. |
| Fireworks-hosted models | First-class provider adapter | Service-managed provider credential | Paid | High | First-party | Eligible for adjacent-service defaults | Good fit for orchestration and hosted open-model lanes. |
| Gemini family | First-class provider adapter | Service-managed provider credential or explicit free-tier account lane | Mixed paid / free-tier | Medium to high | First-party | Eligible only when the chosen route is implementation-time verified | Keep free-tier access separate from package defaults. |
| OpenRouter-hosted models | OpenAI-compatible adapter | Service-managed provider credential | Mixed free / paid | Medium | Community or OpenAI-compatible | Optional default for selected open-model lanes after verification | Useful aggregation lane, but package guarantees attach to the chosen route, not to OpenRouter in the abstract. |
| Mistral / Devstral families | Depends on host route | Depends on selected host | Mixed paid / hosted | Medium | First-party or compatible-host lane | Never default by family name alone | Promote only a verified host route, not the family label by itself. |
| GitHub Copilot free or personal-account routes | Experimental or account-coupled | Operator account or client subscription | Free / subscription-backed | Low for package guarantees | Unsupported in package policy; host-specific route only | Never a package default | May be reachable through OpenCode or MCP-sampling-style flows, but remains optional and non-authoritative. |
| OpenCode-backed unofficial or brittle free routes | Experimental or account-coupled | Host-local or unofficial credential path | Free / unstable | Low | Unsupported | Never a package default | Allowed only as explicit degraded-mode or local-operator choice. |
| Paid Codex or paid Copilot fallback | Paid fallback provider | Org-managed billing or explicit operator credential | Paid | High | First-party or host route depending on transport | Allowed only as explicit fallback | Good fallback when free or community lanes fail, but not durable package truth. |

## Provider-access-path matrix

| Family or example lane | Native SDK | AI SDK adapter | OpenAI-compatible | Anthropic-compatible | OpenCode route | Implementation / coding | Orchestration | Embeddings / retrieval | Multimodal asset / media | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MiniMax coding or multimodal families | Yes | Community when supported | Sometimes via compatible host | No package assumption | Sometimes | Yes | Yes | Verify per host | Yes | Same family may use native SDK for media work and OpenCode or compatible lanes for coding. |
| Fireworks-hosted open models, including Kimi-style orchestration lanes | No native family guarantee | First-party | Depends on hosted endpoint | No package assumption | Sometimes | Yes | Yes | Verify per hosted model | Usually no | Treat the hosted route as the guarantee, not the family label. |
| Gemini families | Yes | First-party | Sometimes through gateway-style or compatible lane | No | Sometimes | Yes | Yes | Yes | Some family members | Free-tier account access must remain optional and clearly downgraded. |
| OpenRouter-hosted open models, including Devstral-style coding lanes | No | Community | Yes | No package assumption | Sometimes | Yes | Yes | Verify per model | Usually no | Best treated as a host lane, not as durable package truth for a family. |
| GitHub Copilot account-backed models | No | No package default | No package default | No | Yes | Yes | Limited / host-specific | No package default | No | This is an execution-host capability, not a provider Scafforge should guarantee. |
| Paid Codex or paid Copilot fallback | Depends on chosen product | First-party or host route | Sometimes | No package assumption | Sometimes | Yes | Yes | Verify per product | Usually no | Keep as explicit fallback policy, not hidden default behavior. |

## Router request summary for adjacent services

Adjacent services should expose a request contract that includes, at minimum:

- `capability`: the job class being requested, such as `drafting`, `review`, `orchestration`, `implementation`, `embeddings`, or `multimodal-asset`
- `cost_tier`: the target spend posture, such as `free`, `balanced`, `premium`, or `fallback-only`
- `allowed_route_kinds`: which transports are legal for this request
- `fallback_order`: ordered route or provider-family preferences
- `timeout_ms`: the maximum allowed runtime for the decision
- `trace`: request or job metadata needed for auditability
- `allow_experimental`: whether account-coupled or unofficial routes may be considered
- optional provider-family hints or operator constraints

The router decision record should include, at minimum:

- selected route kind
- provider class and provider identifier
- model family
- exact runtime model ID when one was used
- credential reference or credential lane identifier
- timeout used
- degraded-mode flag
- rationale
- trace metadata copied from the request

The exact runtime model ID belongs in the decision record, service config, or runtime evidence. It does **not** become package-level durable truth.

## Credential and control-plane boundary

- Provider credentials live in adjacent service configuration, deployment secrets, or operator-managed secret stores.
- The control plane may reference credential lanes or provider policies, but it must not copy raw credentials into Scafforge package docs.
- Apps SDK surfaces must not own provider credentials; they call backend services that do.

## Defaults and degradation rules

1. Package defaults may only come from verified first-class or clearly supported compatible routes.
2. Experimental, account-coupled, or unofficial routes may be used only when explicitly allowed and clearly marked as degraded mode.
3. Free or promotional routes must never become the package's required source of truth.
4. When only experimental or free routes remain, the router should record degraded mode instead of pretending the lane is equivalent to a durable supported default.
5. Paid fallback lanes may be selected intentionally when higher-trust defaults are unavailable or have exceeded budget or latency constraints.

## Model update policy

1. Durable package docs name categories, families, and route rules. They do not freeze exact model IDs as long-lived truth.
2. Exact model IDs must be verified at implementation time against current provider docs, provider APIs, or gateway inventory before code or config changes land.
3. Safe homes for exact model IDs are:
   - adjacent service config
   - environment-specific settings
   - deployment-managed router manifests
   - explicit test fixtures and proof artifacts
4. When a provider changes or removes a model ID, update the adjacent service config and the service-local proof artifacts. Do not patch package policy docs with volatile IDs.
5. Prompt-engineering notes in Scafforge should stay at model-family guidance level unless a stable behavior pattern truly requires more detail.

## OpenCode and Apps SDK boundary reminders

- OpenCode remains the execution substrate for generated repos and coding-oriented downstream repo work.
- AI SDK routing belongs in adjacent service layers that need provider abstraction.
- Apps SDK stays limited to ChatGPT-facing ingress and UI surfaces.

This split is the mechanism that lets the same model family appear in more than one legal lane without collapsing provider, SDK, and execution host into one concept.
