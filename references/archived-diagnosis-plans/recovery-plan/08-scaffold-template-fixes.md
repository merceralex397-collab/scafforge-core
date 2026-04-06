# Phase 08: Scaffold Template Fixes

**Priority:** P2 — Medium (some overlap with earlier phases; this covers residual template issues)
**Depends on:** Phase 01, Phase 02 (those cover tool logic; this covers non-tool template content)
**Goal:** Fix concrete bugs and gaps in the template files that are not covered by other phases

---

## Problem Statement

Beyond the tool logic fixes in Phases 01–02, the template directory contains several other issues:
- `bootstrap_repo_scaffold.py` has fragile model detection and no idempotency
- `verify_generated_scaffold.py` checks structure but not content validity
- Agent templates use hardcoded placeholder patterns that may collide
- The `workflow.ts` library has structural issues beyond verification_state
- Generated commands lack error handling for missing prerequisites

---

## Fix 08-A: Harden `bootstrap_repo_scaffold.py`

### Evidence

**File:** `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py`

### Required Changes

1. **Fix `build_model_operating_profile()`:**
   - Replace substring matching (`if "gpt-4" in model_name`) with a tier-based approach (Phase 05-D)
   - Accept `model_tier` as an explicit parameter with default `"weak"`
   - Remove model-name guessing entirely

2. **Add idempotency check:**
   - Before scaffolding, check if the target directory already contains a `.opencode/` folder
   - If it does, refuse to scaffold and suggest retrofit flow instead
   - This prevents accidental double-scaffolding that corrupts existing state

3. **Fix `template_commit()` error handling:**
   - Currently returns `"missing_provenance"` on git failure, which downstream code may not handle
   - Change to raise an explicit error or return a structured result: `{ success: false, reason: "git_failure", detail: "..." }`
   - Log the git error output for debugging

4. **Add placeholder collision check:**
   - Before substitution, verify that `__AGENT_PREFIX__`, `__PROJECT_NAME__`, and other placeholders don't resolve to strings that appear naturally in the template content
   - Flag if a placeholder value would cause double-substitution (e.g., if the project name contains `__`)

### Files to Change

- `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py`

---

## Fix 08-B: Extend `verify_generated_scaffold.py`

### Evidence

**File:** `skills/repo-scaffold-factory/scripts/verify_generated_scaffold.py`
**Problem:** Verifies that expected files exist in the generated scaffold but does not check:
- Are placeholder substitutions complete (no remaining `__PLACEHOLDER__` strings)?
- Are JSON files valid JSON?
- Are JSONC files valid JSONC?
- Do agent files reference tools that exist?
- Do skill files reference the correct project name?

### Required Changes

1. **Add placeholder residue check:**
   - Scan all generated files for remaining `__` delimited strings
   - Flag any file that still contains `__AGENT_PREFIX__`, `__PROJECT_NAME__`, or similar
   - Finding: `SCAFFOLD-001` (unsubstituted placeholder)

2. **Add JSON validity check:**
   - Parse `tickets/manifest.json`, `.opencode/state/workflow-state.json`, `opencode.jsonc`
   - Flag any that fail to parse
   - Finding: `SCAFFOLD-002` (invalid JSON/JSONC)

3. **Add cross-reference check:**
   - For each agent file, check that referenced tools exist in `.opencode/tools/`
   - For each agent file, check that referenced skills exist in `.opencode/skills/`
   - Finding: `SCAFFOLD-003` (agent references non-existent tool/skill)

4. **Add project name consistency check:**
   - Verify that `README.md`, `AGENTS.md`, `opencode.jsonc`, and `START-HERE.md` all reference the same project name
   - Finding: `SCAFFOLD-004` (inconsistent project name across surfaces)

### Files to Change

- `skills/repo-scaffold-factory/scripts/verify_generated_scaffold.py`

---

## Fix 08-C: Template Command Error Handling

### Evidence

**Files:** `skills/repo-scaffold-factory/assets/project-template/.opencode/commands/`
**Problem:** Generated commands (ticket operations, workflow operations, handoff) call tools but don't handle the case where a prerequisite file is missing. For example, `ticket_claim` may fail silently if `manifest.json` doesn't exist yet.

### Required Changes

1. **In each command template:** Add a prerequisite check at the start:
   - Check that required files exist (manifest.json, workflow-state.json, etc.)
   - If missing, return a clear error: `"Cannot run {command} — {file} does not exist. Run bootstrap first."`

2. **Priority commands to fix:**
   - `ticket_claim.ts` — needs manifest.json
   - `ticket_update.ts` — needs manifest.json and workflow-state.json
   - `handoff_publish.ts` — needs manifest.json and workflow-state.json

3. **This is a simple guard clause at the top of each file**, not a deep refactor. Example:
   ```typescript
   const manifestPath = path.join(projectRoot, "tickets", "manifest.json");
   if (!fs.existsSync(manifestPath)) {
     return { error: "tickets/manifest.json not found. Run bootstrap first." };
   }
   ```

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_claim.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_update.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts`

---

## Fix 08-D: Workflow Library Structural Fixes

### Evidence

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`

### Required Changes

1. **Type the ticket manifest schema explicitly.** Currently the manifest is a loosely typed JSON object. Add TypeScript interfaces:
   ```typescript
   interface TicketManifest {
     project_id: string;
     active_ticket: string | null;
     tickets: Record<string, TicketEntry>;
     metadata: ManifestMetadata;
   }
   
   interface TicketEntry {
     id: string;
     title: string;
     status: TicketStatus;
     stage: TicketStage;
     verification_state: TicketVerificationState;
     finding_source?: string;  // Phase 06-C
     // ... other fields
   }
   ```

2. **Add `finding_source` field** to the ticket schema (Phase 06-C dependency).

3. **Add `bootstrap_blockers` field** to workflow state (Phase 02-F dependency).

4. **Export utility functions** that other tools need:
   - `extractArtifactVerdict()` (Phase 01-A)
   - `readManifest()`, `writeManifest()`
   - `readWorkflowState()`, `writeWorkflowState()`

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`

---

## Fix 08-E: Plugin Template Robustness

### Evidence

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/`
**Problem:** The generated plugin (if any) may reference environment variables or system paths that don't exist. The plugin should gracefully degrade if its dependencies are missing.

### Required Changes

1. **In any generated plugin template:** Add a startup check that verifies required environment variables and paths exist. If not, log a warning and disable the plugin's features gracefully rather than crashing.

2. **This is a template-level concern:** The plugin template should include the guard pattern. Project-specific plugins generated by `opencode-team-bootstrap` should inherit this pattern.

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/` (any plugin templates)

---

## Summary Checklist

| Fix | Done? |
|-----|-------|
| 08-A: Fix model detection in bootstrap_repo_scaffold.py | |
| 08-A: Add idempotency check | |
| 08-A: Fix template_commit() error handling | |
| 08-A: Add placeholder collision check | |
| 08-B: Placeholder residue check | |
| 08-B: JSON/JSONC validity check | |
| 08-B: Cross-reference check (agents → tools/skills) | |
| 08-B: Project name consistency check | |
| 08-C: Command prerequisite guards | |
| 08-D: Workflow library type definitions | |
| 08-D: Add finding_source and bootstrap_blockers fields | |
| 08-E: Plugin graceful degradation | |
