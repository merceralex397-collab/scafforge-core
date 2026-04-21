# Agent Caller Prompts

## planchecker
{{COMMON_PLANCHECKER}}

Plan-specific focus:
- verify the plan creates a bounded skill-evolution lifecycle instead of enabling random skill sprawl
- check that external-source evaluation, provenance, and package-vs-repo skill boundaries are explicit
- confirm downstream skill injection and repair are routed intentionally, not silently

## planimplementer
{{COMMON_PLANIMPLEMENTER}}

Plan-specific focus:
- implement the skill-gap intake path, external-source evaluation rubric, packaging rules, and downstream repair policy
- keep the skill catalog navigable for weaker models and prune overlaps instead of only adding new surfaces
- ensure researched material is distilled into Scafforge-owned artifacts with provenance and validation

## planprreviewer methodology
{{COMMON_PR_REVIEW_METHODOLOGY}}

Plan-specific review focus:
- check for boundary violations between package skills, repo-local synthesized skills, and copied external material
- verify new skill or reference surfaces actually reduce ambiguity rather than increasing catalog sprawl
- look for missing provenance, licensing, or validation obligations around imported ideas

## planprreviewer big-pickle
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: system-level skill-governance risk, overlap, and uncontrolled growth in the skill catalog.

## planprreviewer minimax-m2.7
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: lifecycle coherence from skill-gap detection through packaging, validation, and downstream repair.

## planprreviewer devstral-2512
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: concrete implementation gaps in catalogs, references, validation hooks, and packaging logic.

## planprreviewer mistral-large-latest
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: conceptual clarity, provenance rules, and alignment with AGENTS.md skill-boundary guidance.

## planprreviewer kimi-k2.5-turbo
Review the supplied PR context for PR #{{PR_NUMBER}} in {{OWNER_REPO}}, then return one complete top-level PR comment body for agent-caller to post.
Model emphasis: practical usability for agents choosing or repairing skills, especially under weak-model constraints.



