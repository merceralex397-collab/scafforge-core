# Agent Caller Prompts

## planchecker
{{COMMON_PLANCHECKER}}

Plan-specific focus:
- verify the plan never treats `active-plans/` or `_source-material/` as disposable archive staging
- check that the plan keeps canonical plans, root summaries, and supporting references clearly separated
- confirm the implementation remains documentation-only and does not invent runtime state

## planimplementer
{{COMMON_PLANIMPLEMENTER}}

Plan-specific focus:
- clean and align `active-plans/`, root guidance, and `AGENTS.md`
- keep this plan scoped to planning/documentation hygiene only
- preserve active documentation in-repo while improving navigability

## planprreviewer methodology
{{COMMON_PR_REVIEW_METHODOLOGY}}

Plan-specific review focus:
- look for wording that still implies active planning docs should move out of the repo
- check for hidden duplicate planning state or confusing file roles
- ensure the final docs make the planning portfolio easier, not harder, to navigate

## planprreviewer big-pickle
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: systemic documentation-contract drift, hidden ambiguity, and any cleanup change that accidentally weakens the portfolio structure.

## planprreviewer minimax-m2.7
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: workflow coherence, state/ownership clarity, and whether contributors can follow the planning rules without guessing.

## planprreviewer devstral-2512
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: concrete documentation regressions, missing checklists, and any unsupported assumptions in the implementation details.

## planprreviewer mistral-large-latest
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: architecture/documentation consistency, root-vs-reference boundaries, and long-term maintainability.

## planprreviewer kimi-k2.5-turbo
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: operator clarity, practical usability, and whether the resulting docs would actually guide an agent cleanly.



