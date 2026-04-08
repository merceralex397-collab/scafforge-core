# Report 4: Live Repo Repair Plan

- Repo: /home/pc/projects/GPTTalker
- Diagnosis remains read-only. No repo edits were made by this audit run.

## Safe repair boundary

- Route 2 workflow-layer findings into `scafforge-repair` for deterministic managed-surface repair.

- Do not stop at tool replacement: rerun project-local skill regeneration, agent-team follow-up, and prompt hardening before handoff.

- Refresh generated ticket-update, ticket-lookup, stage-gate, smoke-test, handoff, workflow-doc, and coordinator-prompt surfaces together; these findings indicate a managed workflow-contract defect, not just repo-local operator error.

## Intent-changing boundary

- Escalate any stack, scope, provider, or curated human-decision changes instead of labeling them as safe repair.

## Ticket recommendations

### REMED-001 (warning)

- Title: One or more repo-local skills still contain generic placeholder text instead of project-specific guidance
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SKILL001`
- Summary: Populate every baseline local skill with concrete repo-specific rules and validation commands; generated `.opencode/skills/` files must not retain template filler.

### REMED-002 (warning)

- Title: The team leader prompt leaves workflow mechanics underspecified enough that weaker models can thrash or search for bypasses
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW006`
- Summary: Tell the team leader to route from `ticket_lookup.transition_guidance`, stop after repeated lifecycle errors, leave stage artifacts to the owning specialist, and keep slash commands human-only.

