# SDK Layering ADR

## Status

Final for plan 09.

## Purpose

This ADR freezes how Scafforge layers OpenCode, the Vercel AI SDK, and the OpenAI Apps SDK so adjacent services can add provider routing without implying a hidden rewrite of package-core or generated-repo contracts.

## Decision

| Surface | Primary SDK or host | Role |
| --- | --- | --- |
| Scafforge package core and generated-repo runtime | OpenCode | Execution substrate for generated repos, repo-local agent sessions, permission boundaries, and `.opencode/` contracts. |
| Adjacent service orchestration, provider abstraction, and model routing | AI SDK | Service-side routing, provider registry use, tool-loop agents, and provider transport selection outside package core. |
| ChatGPT-facing ingress and UI | OpenAI Apps SDK | Thin app or widget layer for intake, review, and MCP-connected UX only. |

## What this means in practice

- OpenCode stays in place for Scafforge package behavior and generated-repo execution.
- The AI SDK wraps new adjacent services that need provider routing, provider failover, or service-side orchestration.
- The Apps SDK stays bounded to ChatGPT-facing app surfaces and must not become hidden workflow authority.
- The executable router contract lives in an adjacent service repo, not in Scafforge package core.

## Why an AI SDK rewrite is out of scope

Replacing OpenCode inside the current package and generated-repo contract would be a significant rewrite because Scafforge already depends on:

- `.opencode/` runtime surfaces
- OpenCode session, agent, and permission behavior
- generated repo conventions that downstream agents already follow
- repair and audit flows that assume OpenCode-shaped repos exist

The approved direction for this upgrade cycle is layering, not replacement.

## User-language answer

**Would adding the AI SDK require a big rewrite?** No. The AI SDK should be added around Scafforge in adjacent services. It lets the spec factory, orchestration layer, router, and future control-plane helpers choose providers and run service-native agent logic while Scafforge and its generated repos keep using OpenCode as their execution substrate.

## Allocation by future system

### Must consume OpenCode-generated repos as-is

- generated repos created by Scafforge
- `scaffold-kickoff` and the package skill chain
- package validation, audit, repair, and handoff flows
- downstream host-agent repo execution against `.opencode/`

### May be AI SDK-native

- adjacent model-router and orchestration services
- background agents and service-side worker processes
- spec-factory backend drafting or review helpers
- control-plane backend helpers that need provider abstraction

### May use the Apps SDK

- ChatGPT-facing intake widgets
- ChatGPT-facing review rendering
- ChatGPT-facing attachment UX

Those Apps SDK surfaces remain clients of the adjacent services. They do not own durable approval, router credentials, or repo mutation authority.

## Consequences

1. Provider routing policy is documented in Scafforge, but executable router behavior remains outside package core.
2. Package docs should describe provider categories and transport lanes, not freeze volatile model IDs.
3. Adjacent services may choose between native SDK lanes, AI SDK provider lanes, compatible-adapter lanes, and OpenCode execution lanes intentionally for each job.

## Dependent references

- [Scafforge Architecture](..\architecture.md)
- [Provider Router Policy](provider-router-policy.md)
- [Spec Factory Intake And Approval Flow](spec-factory-intake-and-approval.md)
- [Orchestration Wrapper Contract](orchestration-wrapper-contract.md)
