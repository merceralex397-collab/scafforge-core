# Agent Catalog

Prefix: `glitch`

Visible entrypoint:

- `glitch-team-leader`

Core hidden specialists:

- `glitch-planner`
- `glitch-plan-review`
- `glitch-implementer`
- `glitch-reviewer-code`
- `glitch-reviewer-security`
- `glitch-tester-qa`
- `glitch-docs-handoff`
- `glitch-backlog-verifier`
- `glitch-ticket-creator`

Utility hidden specialists:

- `glitch-utility-explore`
- `glitch-utility-shell-inspect`
- `glitch-utility-summarize`
- `glitch-utility-ticket-audit`
- `glitch-utility-web-research`

Role notes:

- `glitch-team-leader` coordinates ticket routing, bootstrap gating, and lifecycle enforcement.
- `glitch-planner` produces decision-complete plans grounded in the canonical brief and the current Godot/mobile constraints.
- `glitch-implementer` owns approved gameplay, systems, UI, and content changes inside the claimed lane.
- `glitch-reviewer-code` focuses on correctness, regressions, scene/script integration, and validation evidence.
- `glitch-reviewer-security` focuses on secrets, trust boundaries, unsafe plugins, and release-surface misuse.
- `glitch-tester-qa` validates playable behavior through executable Godot checks and ticket-specific smoke scope.
- `glitch-docs-handoff` keeps handoff and repo-facing docs aligned with the active ticket state.

Workflow contract:

- the team leader advances stages through ticket tools and workflow state, not by manually editing ticket files
- each major stage must leave a canonical artifact before the next stage begins
- read-only specialists return findings, artifacts, or blockers instead of mutating repo files
- per-ticket stage order stays sequential, and the repo defaults to one active lane unless bounded parallel work is explicitly justified
- the backlog verifier reads canonical artifact bodies through `ticket_lookup` before deciding whether old completion still holds
- the team leader runs the deterministic `smoke_test` tool between QA and closeout instead of delegating that stage to another agent
