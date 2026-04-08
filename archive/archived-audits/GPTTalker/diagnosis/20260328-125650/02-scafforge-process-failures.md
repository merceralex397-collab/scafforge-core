# Scafforge Process Failures

## Scope

- Subject repo: `/home/pc/projects/GPTTalker`
- Diagnosis timestamp: `2026-03-28T12:56:50Z`
- Diagnosis kind: `initial_diagnosis`
- Failure map reconciled from:
  - canonical state in `tickets/manifest.json` and `.opencode/state/workflow-state.json`
  - derived restart surfaces in `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md`
  - supplied agent export `session2.md`
  - sampled raw OpenCode log `2026-03-28T123330.log`

## Failure Map

### CURR-001 -> restart-surface truth drift

- Linked Report 1 finding id: `CURR-001`
- Implicated generated surfaces:
  - `START-HERE.md`
  - `.opencode/state/context-snapshot.md`
  - `.opencode/state/latest-handoff.md`
  - `.opencode/state/workflow-state.json`
- Ownership class: `generated-repo restart-surface drift`
- How the workflow allowed the issue through:
  - The repo contract already says derived restart surfaces must agree with canonical state and that `pending_process_verification` is cleared only after `ticket_lookup.process_verification.affected_done_tickets` is empty.
  - Despite that, the session published prose claiming process verification was cleared while canonical workflow state still said otherwise.
  - The raw OpenCode log confirms the session performed real writes and reread the restart surfaces afterward, so this is not just summarization noise.
  - The deterministic audit script missed this class of failure because it did not compare restart-surface prose against canonical workflow-state truth.

### HIST-001 -> session routing misread

- Linked Report 1 finding id: `HIST-001`
- Ownership class: `workflow robustness gap with current-state residue`
- How the workflow allowed the issue through:
  - The session treated truthful `pending_process_verification` visibility as if it were a blocker to `ticket_reverify`, even though the contract already separates that state from `managed_blocked`.
  - The session conflated the broader restart-surface backlog summary with the narrower `affected_done_tickets` working set and then over-claimed completion.
  - Current prompt and workflow docs already encode the safer rule, so this is not sufficient evidence for a new package-first loop on its own.

## Ownership Classification

- `CURR-001`: `generated-repo restart-surface drift`
- `HIST-001`: `workflow robustness gap with current-state residue`

## Root Cause Analysis

- The live issue is not missing package work in the abstract. The repo already contains explicit contract text saying canonical and derived state must agree.
- The current failure is that the restart publication outcome no longer matches canonical truth: either the canonical flag should have been cleared through the supported workflow path, or the derived prose should not have claimed clearance.
- The historical session matters because it explains how the repo reached this contradictory state:
  - it misread `pending_process_verification`
  - it treated derived-surface mismatch as mere staleness instead of a stop condition
  - it concluded successfully with prose that outran canonical state
- The deterministic audit package also has a prevention gap: it can report `0` findings even when restart prose and canonical workflow state disagree.
