# MiniMax M2.5 guidance for Scafforge-generated agents

## Executive summary

Scafforge should not make MiniMax M2.5 a hidden package default, but its current workflow design already matches many M2.5-friendly patterns:

- short, explicit prompt sections
- explicit non-ownership
- artifact proof before stage changes
- bounded delegation
- low-temperature review roles
- blocker-first behavior when ambiguity remains

MiniMax support belongs in adapter-specific or profile-specific guidance, not in the package core.

## What local evidence says to preserve

### Short, explicit prompt contracts

Scafforge’s existing prompt contracts and weak-model profile already fit MiniMax-style robustness well:

- exact output sections
- canonical paths and tool names
- proof before transitions
- blockers over hidden assumptions

This should remain the base style for MiniMax-oriented generated prompts.

### Clear delegation boundaries

Team leaders may delegate. Implementers generally should not. Utility agents should stay narrow and bounded. This is especially important for weaker or drift-prone models.

### Canonical tool use

The strongest local pattern is still:

- use ticket/state tools for workflow control
- write artifacts first
- register metadata second
- keep read-only agents truly read-only
- findings first for reviewers

## Practical MiniMax guidance

### Good role split

- review / QA / summarize: low temperature
- planner: low-to-moderate temperature
- implementer: moderate temperature
- team leader: low-to-moderate temperature

### Good prompt shape

1. role
2. owned scope
3. explicit non-ownership
4. workflow contract
5. stop or blocker rules
6. exact output sections
7. canonical artifact or tool path

### Additional guidance worth emphasizing

- explicit phase labels for multi-step work
- one helper at a time where delegation exists
- output schema validation before downstream effects
- context sharding for very large repos
- preserve full reasoning and tool-call history in any MiniMax-specific adapter/runtime

## Caveats from external guidance

- good agentic performance does not remove hallucination risk
- context and tool history handling matter
- runtime adapters may need MiniMax-specific parser or reasoning-history handling

Useful references:

- MiniMax tool-use guidance: <https://platform.minimax.io/docs/guides/text-m2-function-call>
- vLLM MiniMax M2 notes: <https://docs.vllm.ai/projects/recipes/en/latest/MiniMax/MiniMax-M2.html>
- Artificial Analysis overview: <https://artificialanalysis.ai/articles/minimax-m2-5-everything-you-need-to-know>

## Bottom line

Scafforge should keep its current weak-model-first guardrails and treat MiniMax M2.5 as a model that benefits from strong workflow structure, explicit phase boundaries, narrow delegation, and hard artifact-backed stage gates.
