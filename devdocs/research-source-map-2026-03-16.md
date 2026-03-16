# Scafforge Research Source Map (2026-03-16)

## Problem
Identify repo-local and external sources relevant or adaptable for Scafforge, using `devdocs/research-workflows.md` as the heuristic. Focus on sources that inform host-agnostic package behavior, OpenCode-oriented output, workflow contracts, ticketing, prompt hardening, adapters, and multi-agent orchestration.

## Approach
- Extracted search criteria from `devdocs/research-workflows.md`.
- Swept the repository for directly relevant docs, references, templates, and adapter metadata.
- Searched the public web for complementary sources on multi-agent workflow architecture, OpenCode-adjacent patterns, prompt hardening, ticket/process state, and repo scaffolding.
- Grouped findings by theme and explained how each source could be adapted for Scafforge.

## Repo-local Sources
- **README.md, AGENTS.md**: Core product contract, skill chain, workflow contract, truth hierarchy.
- **adapters/README.md, adapters/manifest.json**: Host abstraction, adapter contract, machine-readable split.
- **devdocs/research-workflows.md**: Comparative analysis of workflow patterns (Scafforge, GPS, GPTTalker, academic references).
- **devdocs/research-opencode-ecosystem.md**: OpenCode ecosystem analysis, integration guidance.
- **devdocs/research-minimax-m2-5.md**: MiniMax M2.5-specific guidance for weak-model adaptation.
- **skills/repo-process-doctor/references/safe-stage-contracts.md, process-smells.md, repair-playbook.md**: Stage model, anti-patterns, migration/repair guidance.
- **skills/repo-scaffold-factory/references/workflow-guide.md, layout-guide.md**: Canonical workflow, directory contract.
- **skills/ticket-pack-builder/references/ticket-system.md**: Ticket schema, concurrency rules, manifest/board separation.
- **skills/agent-prompt-engineering/references/prompt-contracts.md, weak-model-profile.md, anti-patterns.md, examples.md**: Prompt contracts, weak-model hardening, anti-patterns, templates.
- **skills/opencode-team-bootstrap/references/agent-system.md, tools-plugins-mcp.md**: Agent taxonomy, delegation, tool/plugin/MCP packaging.
- **skills/spec-pack-normalizer/references/brief-schema.md**: Canonical brief schema for project intake.
- **skills/pr-review-ticket-bridge/references/review-contract.md**: PR review ticket bridge contract.
- **skills/repo-scaffold-factory/assets/project-template/**: Generated contract surfaces (agents, tools, plugins, skills, tickets, state, provenance, restart surface).

## External/Public Sources
- **OpenCode docs**: [Agents](https://opencode.ai/docs/agents/), [Skills](https://opencode.ai/docs/skills), [Plugins](https://opencode.ai/docs/plugins/), [Tools](https://opencode.ai/docs/tools), [MCP](https://deepwiki.com/opencode-ai/opencode/4.1-mcp-and-external-tools), [Ecosystem](https://www.opencode.live/ecosystem/), [GitHub](https://github.com/anomalyco/opencode/)
- **Microsoft**: [AI Agent Orchestration Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns), [Multi-Agent Reference Architecture](https://microsoft.github.io/multi-agent-reference-architecture/index.html)
- **Anthropic**: [Multi-Agent Research System](https://www.anthropic.com/engineering/built-multi-agent-research-system), [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- **AWS**: [Multi-Agent Collaboration Guidance](https://aws.amazon.com/blogs/hpc/engineering-at-the-speed-of-thought-accelerating-complex-processes-with-multi-agent-ai-and-synera/)
- **MetaGPT**: [MetaGPT SOP](https://arxiv.org/abs/2308.00352)
- **Academic**: [Multi-Agent SWE Review](https://arxiv.org/abs/2404.04834), [Experimenting with Multi-Agent SWE](https://arxiv.org/abs/2406.05381)
- **Prompt Engineering**: [Prompt-Engineering-Guide](https://github.com/dair-ai/Prompt-Engineering-Guide), [IBM 2026 Guide](https://www.ibm.com/think/prompt-engineering), [Springer Key Challenges](https://link.springer.com/chapter/10.1007/978-3-031-86206-9_4), [StackAI RAG Guide](https://www.stackai.com/blog/prompt-engineering-for-rag-pipelines-the-complete-guide-to-prompt-engineering-for-retrieval-augmented-generation), [Prompt Engineering Institute](https://promptengineering.org/tag/agentic-workflow/)
- **MiniMax/vLLM**: [MiniMax Tool Use](https://platform.minimax.io/docs/guides/text-m2-function-call), [vLLM MiniMax M2](https://docs.vllm.ai/projects/recipes/en/latest/MiniMax/MiniMax-M2.html), [Artificial Analysis](https://artificialanalysis.ai/articles/minimax-m2-5-everything-you-need-to-know)

## Categorization
- **Directly reusable**: Most of the above repo-local sources, OpenCode docs, Microsoft/AWS/Anthropic/MiniMax patterns.
- **Adaptable**: Academic reviews, prompt-engineering guides, MetaGPT, vLLM, ecosystem plugin lists.
- **Watchlist**: New OpenCode ecosystem plugins, future weak-model research, evolving agent orchestration architectures.

## Notes
- Prioritize sources that strengthen Scafforge's backbone skills and generated truth hierarchy.
- Prefer evidence-backed workflow/process contracts over generic multi-agent hype.
- Include both “directly reusable” and “indirect but adaptable” sources, but label them clearly.
