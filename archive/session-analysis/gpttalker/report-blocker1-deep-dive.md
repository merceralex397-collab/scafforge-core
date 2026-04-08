# Blocker 1 Deep-Dive: Stale Active Ticket in Lease Enforcement

## Executive Summary

The `artifact_write` tool rejected writes for EDGE-003 with "Active ticket REMED-001 must hold an active write lease" because the stage-gate-enforcer plugin's `ensureWriteLease` function checks `workflow.active_ticket` from `workflow-state.json` instead of the ticket the tool is actually operating on. When the active ticket transitions across closeout, `workflow-state.json` can lag behind `manifest.json`, causing the lease check to reference a stale ticket.

## Root Cause Analysis

### Exact Location

**Primary bug**: `/home/rowan/Scafforge/skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`, lines 63-83 and lines 298-315.

The `ensureWriteLease` function at line 63:

```typescript
async function ensureWriteLease(pathValue?: string) {
  const workflow = await loadWorkflowState()
  if (!hasWriteLeaseForTicket(workflow, workflow.active_ticket)) {
    throwWorkflowBlocker({
      type: "BLOCKER",
      reason_code: "missing_write_lease",
      explanation: `Active ticket ${workflow.active_ticket} must hold an active write lease...`,
```

This function **always** checks `workflow.active_ticket` regardless of which ticket the calling tool is operating on.

The `artifact_write` handler at lines 298-315 applies **two** lease checks:

```typescript
if (input.tool === "artifact_write") {
  const manifest = await loadManifest()
  const ticketId = typeof output.args.ticket_id === "string" ? output.args.ticket_id : manifest.active_ticket
  ...
  if (!historicalVerificationMutation) {
    await ensureTargetTicketWriteLease(ticketId)   // Line 310: checks EDGE-003 -- PASSES
  }
  if (artifactPath && !historicalVerificationMutation) {
    await ensureWriteLease(artifactPath)            // Line 313: checks REMED-001 -- FAILS
  }
}
```

### The Failure Sequence

1. REMED-001 was closed via `ticket_update(stage=closeout, status=done, activate=true)`
2. `ticket_update` sets `manifest.active_ticket = EDGE-003` and calls `syncWorkflowSelection(workflow, manifest)` which sets `workflow.active_ticket = EDGE-003`
3. `saveWorkflowBundle` persists both files
4. `ticket_claim` for EDGE-003 registers a new write lease
5. `ticket_lookup` correctly shows EDGE-003 as active (reads `manifest.active_ticket` at line 430 of `ticket_lookup.ts`)
6. `artifact_write` is called for EDGE-003
7. The stage-gate-enforcer intercepts:
   - `ensureTargetTicketWriteLease("EDGE-003")` passes -- EDGE-003 has a lease
   - `ensureWriteLease(path)` fails -- it checks `workflow.active_ticket` which is still REMED-001

### Why workflow.active_ticket Was Stale

The `ticket_update` tool at line 116 of `ticket_update.ts` only updates `manifest.active_ticket` when `args.activate` is true:

```typescript
if (args.activate) manifest.active_ticket = ticket.id
```

Then `syncWorkflowSelection` at line 121 syncs `workflow.active_ticket` from the manifest:

```typescript
syncWorkflowSelection(workflow, manifest)
```

If the agent closed REMED-001 in one `ticket_update` call (without `activate: true`) and moved EDGE-003 forward in a separate call, the manifest could have been updated to EDGE-003 via a different mechanism (manual edit, separate activate-only call) while the workflow state's `active_ticket` remained stale.

The `ticket_lookup` tool returns `active_ticket: manifest.active_ticket` (line 430), so it correctly shows EDGE-003. But `ensureWriteLease` reads `workflow.active_ticket` from `workflow-state.json`, which was stale.

### Bug Classification

This is a **design flaw in the stage-gate-enforcer plugin**, not a caching issue. The function `ensureWriteLease` conflates two concerns:

1. Checking that the active ticket has a write lease (correct for `bash`, `write`, `edit`)
2. Checking that the target ticket's lease covers the path (correct for `artifact_write`, `artifact_register`)

For tools that operate on a specific ticket (`artifact_write`, `artifact_register`), the path-coverage check should use the target ticket's lease, not `workflow.active_ticket`'s lease.

## Why Tests Did Not Catch This

### Smoke Tests (`scripts/smoke_test_scafforge.py`)

The smoke test suite seeds various failure scenarios but **does not test ticket transitions across closeout to a new active ticket**. The relevant seeders are:

- `seed_closed_ticket_with_blocked_dependent` (line 272) -- tests closed-ticket routing but does not exercise `artifact_write` after activation of a new ticket
- `seed_minimal_npm_repo` -- seeds a basic repo with no ticket transitions

No test scenario exercises: close ticket A, activate ticket B, claim lease on B, write artifact for B.

### Integration Tests (`scripts/integration_test_scafforge.py`)

The integration tests cover:
- Greenfield scaffold + bootstrap-lane verification
- Repair cycle with placeholder skills and prompt drift
- Pivot with downstream stage recording
- GPTTalker fixture families (6 fixtures)

None of the 6 fixture families test the closeout-to-new-ticket transition with artifact writes:
- `bootstrap-dependency-layout-drift` -- bootstrap focus
- `host-tool-or-permission-blockage` -- permission blockage focus
- `repeated-lifecycle-contradiction` -- repair cycle focus
- `restart-surface-drift-after-repair` -- surface drift focus
- `placeholder-skill-after-refresh` -- skill survival focus
- `split-scope-and-historical-trust-reconciliation` -- pivot/lineage focus

### Test Fixtures (`tests/fixtures/gpttalker/`)

The fixture index confirms no fixture covers this scenario. The closest is `split-scope-and-historical-trust-reconciliation` which deals with ticket lineage but not the active-ticket lease check after closeout.

## Why This Survived Audit and Repair

### Audit Skill (`skills/scafforge-audit/SKILL.md`)

The audit skill is a **read-only diagnosis tool** that inspects repo state and produces findings. It checks for:
- Workflow contract violations
- Process smells
- Lifecycle thrash
- Smoke-test defects
- Closeout contradictions

The audit skill at line 105 checks "whether lease ownership is consistently coordinator-owned or still split across worker prompts" but does **not** check for state drift between `manifest.active_ticket` and `workflow.active_ticket`. This is a gap in the audit rule set.

The audit also checks "whether the workflow exposed one clear legal next move or forced the operator to infer a workaround from contradictory surfaces" (line 105), which would catch the symptom but not the root cause.

### Repair Skill (`skills/scafforge-repair/SKILL.md`)

The repair skill at lines 132-141 lists the "contract family" that should be refreshed together during repair:
- `.opencode/lib/workflow.ts`
- `.opencode/tools/ticket_update.ts`
- `.opencode/tools/ticket_lookup.ts`
- `.opencode/tools/artifact_write.ts`
- `.opencode/tools/artifact_register.ts`
- `.opencode/plugins/stage-gate-enforcer.ts`

However, the repair skill treats these as **prompt/tool surface refreshes**, not as code-level bug fixes. The stage-gate-enforcer plugin was not identified as having a logic defect because the audit did not flag it.

## Related Bugs in Other Tools

### `artifact_register` (same pattern)

The `artifact_register` handler at lines 272-296 has the identical issue:

```typescript
if (input.tool === "artifact_register") {
  ...
  if (!historicalVerificationMutation) {
    await ensureTargetTicketWriteLease(ticketId)   // Checks target ticket
  }
  if (LEASED_ARTIFACT_STAGES.has(stage) && !historicalVerificationMutation) {
    const artifactPath = typeof output.args.path === "string" ? output.args.path : ""
    await ensureWriteLease(artifactPath || undefined)  // Checks workflow.active_ticket -- BUG
  }
```

### `bash` and `write`/`edit` tools

The `bash` handler (line 124) and `write`/`edit` handler (line 134) call `ensureWriteLease()` without a specific ticket context. These are correct in checking `workflow.active_ticket` because they operate in the context of the active ticket. No bug here.

### `ticket_update`

The `ticket_update` handler at lines 317-382 calls `ensureTargetTicketWriteLease(ticketId)` which correctly checks the target ticket. No bug here.

## Permanent Fix

### Fix 1: Add optional `ticketId` parameter to `ensureWriteLease`

In `stage-gate-enforcer.ts`, modify `ensureWriteLease` to accept an optional ticket ID:

```typescript
async function ensureWriteLease(pathValue?: string, ticketId?: string) {
  const workflow = await loadWorkflowState()
  const checkedTicket = ticketId || workflow.active_ticket
  if (!hasWriteLeaseForTicket(workflow, checkedTicket)) {
    throwWorkflowBlocker({
      type: "BLOCKER",
      reason_code: "missing_write_lease",
      explanation: `Active ticket ${checkedTicket} must hold an active write lease before write-capable work can proceed.`,
      next_action_tool: "ticket_claim",
      next_action_args: ticketClaimBlockerArgs(checkedTicket),
    })
  }
  if (pathValue && !hasWriteLeaseForTicketPath(workflow, checkedTicket, pathValue)) {
    throwWorkflowBlocker({
      type: "BLOCKER",
      reason_code: "write_path_not_covered",
      explanation: `The active write lease for ${checkedTicket} does not cover ${pathValue}.`,
      next_action_tool: "ticket_claim",
      next_action_args: ticketClaimBlockerArgs(checkedTicket, [pathValue]),
    })
  }
}
```

### Fix 2: Pass the target ticket ID for artifact tools

For `artifact_write` (line 313):
```typescript
await ensureWriteLease(artifactPath, ticketId)
```

For `artifact_register` (line 288):
```typescript
await ensureWriteLease(artifactPath || undefined, ticketId)
```

### Fix 3: Add audit rule for active-ticket drift

Add a new audit check that compares `manifest.active_ticket` against `workflow.active_ticket` and flags any mismatch as a state-drift finding.

### Fix 4: Add regression test

Add a smoke test scenario that:
1. Closes the active ticket
2. Activates a new ticket
3. Claims a lease on the new ticket
4. Writes an artifact for the new ticket
5. Verifies no lease error occurs

## Files Requiring Changes

| File | Change |
|------|--------|
| `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts` | Add `ticketId` parameter to `ensureWriteLease`, pass it from `artifact_write` and `artifact_register` handlers |
| `scripts/smoke_test_scafforge.py` | Add `seed_closed_ticket_with_new_active_artifact_write` scenario |
| `scripts/test_support/repo_seeders.py` | Add helper for seeding the closeout-to-new-ticket transition |
| `skills/scafforge-audit/scripts/audit_repo_process.py` | Add active-ticket drift check |

## Severity

**High**. This bug blocks any agent from writing artifacts for a newly activated ticket after the previous ticket was closed, which is the fundamental closeout-to-continuation flow that the entire workflow is designed around.

## Reproduction Steps

1. Generate a Scafforge repo with at least two tickets
2. Close ticket A (status=done)
3. Activate ticket B (manifest.active_ticket = B)
4. Claim a write lease on ticket B
5. Attempt to write an artifact for ticket B using `artifact_write`
6. Observe: "Active ticket A must hold an active write lease" error

The error occurs because `ensureWriteLease` reads `workflow.active_ticket` from `workflow-state.json` (still A) instead of the target ticket (B).
