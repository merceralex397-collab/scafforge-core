# Scafforge Process Failures

## Scope

- Maps each validated finding back to the Scafforge-owned workflow surface that allowed it through.

## Failure Map

### WFLOW012

- linked_report_1_finding: WFLOW012
- implicated_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- ownership_class: managed workflow contract surface
- workflow_failure: The generated lease-ownership contract is split across coordinator and worker surfaces, so agents can disagree about who should claim a ticket and when bootstrap gates apply.

### WFLOW013

- linked_report_1_finding: WFLOW013
- implicated_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- ownership_class: managed workflow contract surface
- workflow_failure: The generated resume contract still gives too much authority to derived handoff text or lets reverification obscure the active open ticket.

### read-only-shell-mutation-loophole

- linked_report_1_finding: read-only-shell-mutation-loophole
- implicated_surface: project-skill-bootstrap and agent-prompt-engineering surfaces
- ownership_class: managed workflow contract surface
- workflow_failure: Read-only shell agents still allow commands that can mutate repo-tracked files.

### WFLOW006

- linked_report_1_finding: WFLOW006
- implicated_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- ownership_class: managed workflow contract surface
- workflow_failure: The team leader prompt leaves workflow mechanics underspecified enough that weaker models can thrash or search for bypasses.

## Ownership Classification

### WFLOW006

- ownership_class: managed workflow contract surface
- affected_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces

### WFLOW012

- ownership_class: managed workflow contract surface
- affected_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces

### WFLOW013

- ownership_class: managed workflow contract surface
- affected_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces

### read-only-shell-mutation-loophole

- ownership_class: managed workflow contract surface
- affected_surface: project-skill-bootstrap and agent-prompt-engineering surfaces

## Root Cause Analysis

### WFLOW012

- root_cause: Some workflow docs and prompts still describe worker-owned lease claims while others expect the team leader to coordinate claims. That contradiction is enough to make weaker models thrash around ticket ownership and pre-bootstrap write rules.
- safer_target_pattern: Adopt one lease model everywhere: the team leader owns `ticket_claim` and `ticket_release`, specialists work only inside the already-active ticket lease, and only Wave 0 setup work may claim before bootstrap is ready.
- how_the_workflow_allowed_it: The generated lease-ownership contract is split across coordinator and worker surfaces, so agents can disagree about who should claim a ticket and when bootstrap gates apply.

### WFLOW013

- root_cause: When `/resume` and the surrounding docs do not put `tickets/manifest.json` plus `.opencode/state/workflow-state.json` first, weaker models start following stale restart text, ignore `.opencode/state/latest-handoff.md`, or abandon the active foreground ticket for historical reverification too early.
- safer_target_pattern: Make manifest + workflow-state canonical for `/resume`, keep `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` derived-only, and preserve the active open ticket as the primary lane until it is resolved.
- how_the_workflow_allowed_it: The generated resume contract still gives too much authority to derived handoff text or lets reverification obscure the active open ticket.

### read-only-shell-mutation-loophole

- root_cause: The repo labels an agent as inspection-only while its shell allowlist still includes mutating commands.
- safer_target_pattern: Keep read-only shell allowlists to inspection commands only and move mutation into write-capable roles.
- how_the_workflow_allowed_it: Read-only shell agents still allow commands that can mutate repo-tracked files.

### WFLOW006

- root_cause: Without explicit transition guidance, contradiction-stop behavior, artifact-ownership rules, and command boundaries, the coordinator has to infer the state machine and may start authoring artifacts or testing workaround transitions itself.
- safer_target_pattern: Tell the team leader to route from `ticket_lookup.transition_guidance`, stop after repeated lifecycle errors, leave stage artifacts to the owning specialist, and keep slash commands human-only.
- how_the_workflow_allowed_it: The team leader prompt leaves workflow mechanics underspecified enough that weaker models can thrash or search for bypasses.

