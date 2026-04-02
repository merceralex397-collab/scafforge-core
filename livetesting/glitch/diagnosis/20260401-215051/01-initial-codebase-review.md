# Initial Codebase Review

## Scope

- subject repo: /home/pc/projects/Scafforge/livetesting/glitch
- diagnosis timestamp: 2026-04-01T21:50:51Z
- audit scope: managed workflow, restart, ticket, prompt, and execution surfaces
- verification scope: current repo state only

## Result State

- result_state: validated failures found
- finding_count: 4
- errors: 3
- warnings: 1

## Validated Findings

### WFLOW012

- finding_id: WFLOW012
- summary: The generated lease-ownership contract is split across coordinator and worker surfaces, so agents can disagree about who should claim a ticket and when bootstrap gates apply.
- severity: error
- evidence_grade: repo-state validation
- affected_files_or_surfaces: docs/process/workflow.md, tickets/README.md, .opencode/commands/kickoff.md, .opencode/commands/run-lane.md, .opencode/skills/ticket-execution/SKILL.md, .opencode/agents/glitch-team-leader.md, .opencode/agents/glitch-implementer.md, .opencode/agents/glitch-lane-executor.md, .opencode/agents/glitch-docs-handoff.md
- observed_or_reproduced: Some workflow docs and prompts still describe worker-owned lease claims while others expect the team leader to coordinate claims. That contradiction is enough to make weaker models thrash around ticket ownership and pre-bootstrap write rules.
- evidence:
  - .opencode/commands/kickoff.md does not state that the team leader owns ticket_claim and ticket_release.
  - .opencode/commands/kickoff.md does not limit pre-bootstrap write claims to Wave 0 setup work.
  - .opencode/skills/ticket-execution/SKILL.md does not limit pre-bootstrap write claims to Wave 0 setup work.
  - .opencode/agents/glitch-team-leader.md does not make the coordinator-owned lease model explicit before specialist work.
  - .opencode/agents/glitch-team-leader.md does not preserve the Wave 0-only pre-bootstrap claim rule.
- remaining_verification_gap: None recorded beyond the validated finding scope.

### WFLOW013

- finding_id: WFLOW013
- summary: The generated resume contract still gives too much authority to derived handoff text or lets reverification obscure the active open ticket.
- severity: error
- evidence_grade: repo-state validation
- affected_files_or_surfaces: tickets/manifest.json, .opencode/state/workflow-state.json, .opencode/commands/resume.md, .opencode/state/latest-handoff.md, docs/process/workflow.md, docs/process/tooling.md, AGENTS.md, README.md
- observed_or_reproduced: When `/resume` and the surrounding docs do not put `tickets/manifest.json` plus `.opencode/state/workflow-state.json` first, weaker models start following stale restart text, ignore `.opencode/state/latest-handoff.md`, or abandon the active foreground ticket for historical reverification too early.
- evidence:
  - .opencode/commands/resume.md does not preserve active open-ticket priority over backlog reverification.
  - docs/process/workflow.md does not encode the updated resume truth hierarchy.
- remaining_verification_gap: None recorded beyond the validated finding scope.

### read-only-shell-mutation-loophole

- finding_id: read-only-shell-mutation-loophole
- summary: Read-only shell agents still allow commands that can mutate repo-tracked files.
- severity: error
- evidence_grade: repo-state validation
- affected_files_or_surfaces: .opencode/agents/glitch-tester-qa.md
- observed_or_reproduced: The repo labels an agent as inspection-only while its shell allowlist still includes mutating commands.
- evidence:
  - .opencode/agents/glitch-tester-qa.md
- remaining_verification_gap: None recorded beyond the validated finding scope.

### WFLOW006

- finding_id: WFLOW006
- summary: The team leader prompt leaves workflow mechanics underspecified enough that weaker models can thrash or search for bypasses.
- severity: warning
- evidence_grade: repo-state validation
- affected_files_or_surfaces: .opencode/agents/glitch-team-leader.md
- observed_or_reproduced: Without explicit transition guidance, contradiction-stop behavior, artifact-ownership rules, and command boundaries, the coordinator has to infer the state machine and may start authoring artifacts or testing workaround transitions itself.
- evidence:
  - Team leader prompt does not tell the agent to stop after repeated lifecycle contradictions.
  - Team leader prompt does not forbid stage-artifact authorship overreach by the coordinator.
  - Team leader prompt does not mark slash commands as human entrypoints only.
- remaining_verification_gap: None recorded beyond the validated finding scope.

## Verification Gaps

- The diagnosis pack validates the concrete failures above. It does not claim broader runtime-path coverage than the current audit and supporting evidence actually exercised.

