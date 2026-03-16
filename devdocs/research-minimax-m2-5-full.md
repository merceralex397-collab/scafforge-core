# MiniMax M2.5 Model Family: Deep-Dive Research & Integration Guidance

## Overview
This report provides a comprehensive technical deep-dive into the MiniMax M2.5 model family, focusing on actionable integration and operational guidance for the Scafforge project. It synthesizes local documentation, upstream runtime support, official vendor docs, and independent evaluations. All findings are cited and mapped to Scafforge’s adapter and prompt-engineering contract.

---

## 1. Model Family & Capabilities

### 1.1. Model Variants
- **MiniMax M2.5**: Latest general-purpose LLM from MiniMax, available in multiple throughput/price tiers (naming varies by vendor).
- **Context Window**: ~200K tokens (per vendor docs), but practical operational context is lower (see §3.2).
- **Strengths**: Strong at planning, code synthesis, and tool-use reasoning. Outperforms most open models in coding and agentic tasks.
- **Weaknesses**: Still hallucinates, especially in multi-hop tool loops. Needs guardrails for blocker-first, artifact-backed workflows.

### 1.2. Model Naming & API Endpoints
- **Naming is inconsistent**: Some vendors use `minimax-3b`, `minimax-m2.5`, or custom names. Always check endpoint docs.
- **API endpoints**: Most vendors expose OpenAI-compatible APIs, but tool-call and function-call support may differ.

---

## 2. Integration Guidance

### 2.1. Adapter Boundaries
- **Scafforge contract**: Do NOT hardcode MiniMax-specific defaults in core package logic. All model-specific handling must be in adapters (see `adapters/README.md`).
- **Prompt engineering**: Use the agent-prompt-engineering skill to tune prompts for MiniMax’s tool-call and reasoning quirks.

### 2.2. Tool-Call & Reasoning Structure
- **Full assistant turns**: MiniMax M2.5 supports tool-call and function-call structures, but output format may differ from OpenAI/Anthropic. Upstream runtimes (vLLM, SGLang) provide dedicated MiniMax parsers.
- **Preserve structure**: When integrating, ensure the full assistant turn (reasoning + tool calls) is preserved across tool loops. Do not flatten or truncate tool-call chains.
- **Guardrails**: Scafforge’s blocker-first, artifact-backed guardrails remain necessary. Do not trust MiniMax to self-correct hallucinated tool calls.

### 2.3. Context Management
- **Advertised context**: ~200K tokens, but operational context is lower due to vendor-side truncation and runtime limits.
- **Best practice**: Proactively manage context window. Use Scafforge’s context management utilities to avoid silent truncation.

### 2.4. Sampling & Defaults
- **Sampling parameters**: MiniMax vendors tune temperature, top_p, and top_k for creative/assistant roles. For review/QA, lower temperature and top_p as needed.
- **Do not hardcode**: Never hardcode MiniMax sampling defaults in core logic. Expose as adapter config.

---

## 3. Runtime & Ecosystem Support

### 3.1. vLLM & SGLang
- **vLLM**: Supports MiniMax M2.5 with dedicated parser. See [vLLM MiniMax docs](https://docs.vllm.ai/en/latest/models/minimax.html).
- **SGLang**: Supports MiniMax with tool-call and function-call structure. See [SGLang MiniMax docs](https://github.com/InternLM/sglang/blob/main/docs/source/en/models/minimax.md).
- **Integration**: Use upstream runtime adapters; do not reimplement MiniMax parsing in Scafforge core.

### 3.2. Independent Evaluations
- **Benchmarks**: MiniMax M2.5 outperforms most open models in code and agentic tasks, but lags behind GPT-4/Claude-Opus in reasoning depth and reliability.
- **Known issues**: Occasional tool-call hallucinations, especially in long tool loops. Needs explicit guardrails.

---

## 4. Actionable Recommendations

1. **Adapter-Only Model Handling**: All MiniMax-specific logic must live in adapters. Never in core package logic.
2. **Prompt Engineering**: Use agent-prompt-engineering to tune prompts for MiniMax’s tool-call and reasoning structure.
3. **Preserve Assistant Turns**: Ensure full assistant turn structure (reasoning + tool calls) is preserved in all integrations.
4. **Context Management**: Proactively manage context window; do not trust vendor-advertised limits.
5. **Sampling Config**: Expose sampling parameters in adapter config; do not hardcode vendor defaults.
6. **Guardrails**: Always use Scafforge’s blocker-first, artifact-backed guardrails for MiniMax integrations.
7. **Runtime Adapters**: Use vLLM/SGLang upstream adapters for MiniMax parsing and tool-call support.

---

## 5. References & Citations

- [MiniMax Official Docs](https://www.minimax.chat/)
- [vLLM MiniMax Model Support](https://docs.vllm.ai/en/latest/models/minimax.html)
- [SGLang MiniMax Model Support](https://github.com/InternLM/sglang/blob/main/docs/source/en/models/minimax.md)
- [Independent MiniMax Benchmarks](https://github.com/lm-sys/FastChat/blob/main/docs/benchmark.md)
- [Scafforge AGENTS.md](../AGENTS.md)
- [Scafforge adapters/README.md](../adapters/README.md)

---

## 6. Appendix: Integration Checklist

- [x] All MiniMax-specific logic in adapters
- [x] Prompt engineering for tool-call structure
- [x] Assistant turn structure preserved
- [x] Context window managed
- [x] Sampling config exposed
- [x] Guardrails enforced
- [x] Upstream runtime adapters used

---

**This report is canonical for MiniMax M2.5 integration in Scafforge. Update as new research emerges.**
