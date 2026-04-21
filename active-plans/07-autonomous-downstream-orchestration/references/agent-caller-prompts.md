# Agent Caller Prompts

## planchecker
{{COMMON_PLANCHECKER}}

Plan-specific focus:
- verify the orchestration layer wraps Scafforge instead of replacing it
- check the state model, PR-phase flow, and failure/resume rules
- confirm package defects and repo-local defects remain clearly separated

## planimplementer
{{COMMON_PLANIMPLEMENTER}}

Plan-specific focus:
- implement the orchestration job contract, scaffold trigger boundary, PR-phase workflow, review gates, and resume semantics
- keep Scafforge generation discrete and package-owned
- preserve one-shot generation and truthful restart state

## planprreviewer methodology
{{COMMON_PR_REVIEW_METHODOLOGY}}

Plan-specific review focus:
- look for hidden second workflow engines or orchestration-owned package truth
- verify PR/review/merge gates are explicit and enforceable
- check that failure and resume semantics preserve causality

## planprreviewer big-pickle
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: systemic orchestration drift, hidden authority duplication, and brittle retry/resume edges.

## planprreviewer minimax-m2.7
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: lifecycle/state-machine coherence across scaffold, phase, review, failure, and resume.

## planprreviewer devstral-2512
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: concrete automation gaps, GitHub/runner integration issues, and missing validation/test coverage.

## planprreviewer mistral-large-latest
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: architectural clarity, maintainability, and contract alignment with the package docs.

## planprreviewer kimi-k2.5-turbo
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: operator trust, workflow clarity, and practical readability of the orchestration behavior.



