# Agent Caller Prompts

## planchecker
{{COMMON_PLANCHECKER}}

Plan-specific focus:
- verify the plan keeps package investigation separate from generated-repo repair
- check that escalation thresholds, evidence bundles, and investigator outputs are concrete enough to audit
- confirm archive mining can suggest work without bypassing review, validation, or PR controls

## planimplementer
{{COMMON_PLANIMPLEMENTER}}

Plan-specific focus:
- implement the escalation matrix, evidence-bundle contract, investigator/fixer workflow, and downstream resume rules
- keep package mutation high-trust and evidence-backed; no silent self-modifying loop
- ensure package validation, downstream revalidation, and restart-surface truth all move together

## planprreviewer methodology
{{COMMON_PR_REVIEW_METHODOLOGY}}

Plan-specific review focus:
- check that package-level investigation is triggered from real evidence instead of vague repetition heuristics
- look for any collapse of package repair and downstream repair into one ambiguous workflow
- verify GitHub issue/PR linkage, revalidation gates, and resume conditions are explicit and testable

## planprreviewer big-pickle
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: systemic failure escalation logic, hidden automation risk, and whether the self-improvement loop stays bounded and reviewable.

## planprreviewer minimax-m2.7
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: evidence-chain coherence from downstream failure through package investigation, fix, revalidation, and repo resume.

## planprreviewer devstral-2512
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: implementation holes in evidence storage, scripts, issue linkage, validator coverage, and machine-readable artifacts.

## planprreviewer mistral-large-latest
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: contract alignment across audit, repair, investigation, documentation, and active-audits handling.

## planprreviewer kimi-k2.5-turbo
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: operational believability for long-running autonomy, especially pause/resume, human review, and error recovery UX.



