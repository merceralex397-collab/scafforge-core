# Agent Caller Prompts

## planchecker
{{COMMON_PLANCHECKER}}

Plan-specific focus:
- verify the plan creates a real authority map instead of just a general docs cleanup
- check that package docs, reference docs, and generated-template docs are kept distinct and routed clearly
- confirm documentation updates are required as part of every contract-changing implementation

## planimplementer
{{COMMON_PLANIMPLEMENTER}}

Plan-specific focus:
- implement the authority map, routing-layer rewrites, reference rationalization, and generated-template doc alignment
- keep root docs short and authoritative while moving durable detail into references
- make documentation verification a standing delivery requirement, not a final polish step

## planprreviewer methodology
{{COMMON_PR_REVIEW_METHODOLOGY}}

Plan-specific review focus:
- check for contradictory truth domains, stale references, or docs that blur package and generated-repo layers
- verify documentation changes actually match current code and template behavior
- look for missing update paths that would cause the docs to drift again immediately

## planprreviewer big-pickle
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: authority-map defects, navigation gaps, and structural documentation risk that would mislead agents.

## planprreviewer minimax-m2.7
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: truth-hierarchy coherence across root docs, references, template docs, and generated guidance.

## planprreviewer devstral-2512
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: precise documentation mismatches, broken links, missing examples, and incomplete update coverage.

## planprreviewer mistral-large-latest
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: conceptual consistency, contract phrasing, and whether the docs present one authoritative story.

## planprreviewer kimi-k2.5-turbo
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: newcomer and operator usability, context acquisition speed, and whether the repo is easier to navigate in practice.



