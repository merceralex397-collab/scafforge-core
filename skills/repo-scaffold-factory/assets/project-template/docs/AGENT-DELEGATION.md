# Agent Delegation

This document is the human-readable delegation map for the generated OpenCode team.
`opencode-team-bootstrap` must refresh it so it matches the actual agent files in `.opencode/agents/` for this repo.

## Team Composition

- visible coordinator: `__AGENT_PREFIX__-team-leader`
- planning lane: `__AGENT_PREFIX__-planner` and `__AGENT_PREFIX__-plan-review`
- implementation lane: `__AGENT_PREFIX__-lane-executor` and `__AGENT_PREFIX__-implementer`
- review lane: `__AGENT_PREFIX__-reviewer-code` and `__AGENT_PREFIX__-reviewer-security`
- QA lane: `__AGENT_PREFIX__-tester-qa`
- closeout lane: `__AGENT_PREFIX__-docs-handoff`
- trust-restoration lane: `__AGENT_PREFIX__-backlog-verifier` and `__AGENT_PREFIX__-ticket-creator`

## Delegation Chain

1. `__AGENT_PREFIX__-team-leader` resolves canonical state with `ticket_lookup`
2. `__AGENT_PREFIX__-planner` writes the planning artifact
3. `__AGENT_PREFIX__-plan-review` approves or rejects the plan
4. `__AGENT_PREFIX__-lane-executor` or `__AGENT_PREFIX__-implementer` performs the approved implementation lane
5. `__AGENT_PREFIX__-reviewer-code` and `__AGENT_PREFIX__-reviewer-security` return findings or approval evidence
6. `__AGENT_PREFIX__-tester-qa` runs QA and returns the QA artifact
7. `__AGENT_PREFIX__-team-leader` runs `smoke_test`, advances lifecycle state, and routes closeout
8. `__AGENT_PREFIX__-docs-handoff` synchronizes restart surfaces when closeout is ready

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