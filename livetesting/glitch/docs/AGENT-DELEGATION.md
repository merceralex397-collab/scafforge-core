# Agent Delegation

This document is the human-readable delegation map for Glitch's OpenCode team.
It should match the actual agent files in `.opencode/agents/` and the current workflow state.

## Team Composition

- visible coordinator: `glitch-team-leader`
- planning lane: `glitch-planner` and `glitch-plan-review`
- implementation lane: `glitch-lane-executor` and `glitch-implementer`
- review lane: `glitch-reviewer-code` and `glitch-reviewer-security`
- QA lane: `glitch-tester-qa`
- closeout lane: `glitch-docs-handoff`
- trust-restoration lane: `glitch-backlog-verifier` and `glitch-ticket-creator`

## Delegation Chain

1. `glitch-team-leader` resolves canonical state with `ticket_lookup`
2. `glitch-planner` writes the planning artifact
3. `glitch-plan-review` approves or rejects the plan
4. `glitch-lane-executor` or `glitch-implementer` performs the approved implementation lane
5. `glitch-reviewer-code` and `glitch-reviewer-security` return findings or approval evidence
6. `glitch-tester-qa` runs QA and returns the QA artifact
7. `glitch-team-leader` runs `smoke_test`, advances lifecycle state, and routes closeout
8. `glitch-docs-handoff` synchronizes restart surfaces when closeout is ready

## Ownership Rules

- only the team leader advances ticket lifecycle state
- only the owning specialist or tool writes the stage artifact body
- read-only specialists return findings, blockers, or evidence; they do not mutate repo-tracked files
- write-capable specialists work only inside a claimed lease and only for the bounded lane they were assigned

## Escalation Path

Stop and escalate to the operator when:

- canonical workflow tools disagree and the contradiction rules in the team-leader prompt do not resolve the conflict
- `environment_bootstrap` still reports unresolved blockers after safe recovery commands were attempted
- the same ticket advance fails three times with the same blocker or error signature
- a dependency ticket is blocked and prevents the active ticket from moving
- no single legal next move can be resolved from `ticket_lookup.transition_guidance` and the canonical artifacts

## Restart Procedure

1. read `START-HERE.md`
2. read `docs/spec/CANONICAL-BRIEF.md` and `docs/process/workflow.md` when the current state is unclear
3. run `ticket_lookup` for the active ticket
4. trust `tickets/manifest.json` and `.opencode/state/workflow-state.json` over derived restart surfaces
5. resume from the next required stage instead of improvising a new delegation path