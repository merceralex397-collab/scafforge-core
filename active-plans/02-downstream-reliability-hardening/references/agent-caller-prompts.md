# Agent Caller Prompts

## planchecker
{{COMMON_PLANCHECKER}}

Plan-specific focus:
- verify both user criteria are enforced: fresh-repo prevention and audit/repair recovery
- look for missing failure families around parse/load/import/layout truth
- confirm the plan ties failures to real package surfaces, fixtures, and validation commands

## planimplementer
{{COMMON_PLANIMPLEMENTER}}

Plan-specific focus:
- implement the womanvshorse/spinner failure taxonomy, regression fixtures, stronger gates, and truthful audit/repair routing
- preserve evidence and causality; do not overclaim repo health
- make restart/handoff surfaces reflect real failure and recovery state

## planprreviewer methodology
{{COMMON_PR_REVIEW_METHODOLOGY}}

Plan-specific review focus:
- check that new gates are real and test-backed, not prose-only
- look for misclassification between package-managed and repo-local defects
- verify the implementation does not “solve” reliability by loosening standards or hiding failures

## planprreviewer big-pickle
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: systemic reliability holes, missing regression coverage, and hidden edge cases in audit/repair lifecycle behavior.

## planprreviewer minimax-m2.7
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: lifecycle coherence from failure detection to resume, and any contradiction in the recovery path.

## planprreviewer devstral-2512
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: concrete script/test gaps, fixture quality, validator regressions, and implementation holes in the changed files.

## planprreviewer mistral-large-latest
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: contract alignment across skills, template docs, and validation surfaces.

## planprreviewer kimi-k2.5-turbo
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: practical repo-operability, clarity of next steps after failure, and whether the recovery UX is believable.



