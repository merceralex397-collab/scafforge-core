# Report 4: Live Repo Repair Plan

- Repo: /home/pc/projects/GPTTalker
- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.

## Safe repair boundary

- Route 1 workflow-layer findings into `scafforge-repair` for deterministic managed-surface repair.

- Do not stop at tool replacement: rerun project-local skill regeneration, agent-team follow-up, and prompt hardening before handoff.

## Intent-changing boundary

- Escalate any stack, scope, provider, or curated human-decision changes instead of labeling them as safe repair.

## Ticket recommendations

### REMED-001 (warning)

- Title: One or more repo-local skills still contain generic placeholder text instead of project-specific guidance
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SKILL001`
- Summary: Populate every baseline local skill with concrete repo-specific rules and validation commands; generated `.opencode/skills/` files must not retain template filler.

