# Phase 05: Agent Prompt and Delegation Hardening

**Priority:** P1 — High
**Depends on:** Phase 01 (tool fixes must land first so prompts can reference correct behavior)
**Goal:** Make generated agent prompts robust for weak models, with clear delegation and stop conditions

---

## Problem Statement

The generated agent templates in `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/` contain broad role descriptions but lack:
- Explicit stop conditions (when to stop working, when to escalate)
- Verdict checking instructions (agents do not check if review/QA passed before advancing)
- Stack-specific delegation (the team leader gives the same generic instructions regardless of stack)
- Lease ownership clarity (who owns a ticket at each stage is implicit, not stated)
- Contradiction resolution (what to do when tools disagree with each other or with docs)

The Glitch transcript shows the agent entering 500+ lines of circular reasoning because the team leader prompt did not tell it to stop when tools returned contradictory information.

---

## Fix 05-A: Harden Team-Leader Template

### Evidence

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md`

### Required Changes

Add or tighten these sections in the team-leader prompt template:

1. **Stop conditions section:**
   ```
   ## Stop Conditions
   
   Stop working and escalate to the user when:
   - Two or more workflow tools return contradictory information about ticket state
   - environment_bootstrap reports unresolved blockers after an install attempt
   - Three consecutive attempts to advance a ticket fail with the same error
   - The active ticket cannot advance because a dependency ticket is blocked
   - You cannot determine a single legal next move from the available tools
   ```

2. **Verdict checking section:**
   ```
   ## Advancement Rules
   
   Before advancing any ticket past review or QA:
   1. Run ticket_lookup for the active ticket
   2. Check transition_guidance.review_verdict or transition_guidance.qa_verdict
   3. If the verdict is FAIL, REJECT, or BLOCKED — route back to implementation
   4. If the verdict is verdict_unclear — inspect the artifact manually
   5. NEVER advance past a FAIL verdict
   ```

3. **Ticket ownership section:**
   ```
   ## Ticket Ownership
   
   At each stage, exactly one agent owns the ticket:
   - implementation: the implementer agent
   - review: the reviewer agent (or you, if no reviewer agent exists)
   - qa: the QA agent (or you, if no QA agent exists)
   - smoke-test: you (the team leader)
   - closeout: you (the team leader)
   
   Only the owning agent may produce stage artifacts.
   Only you may advance the ticket to the next stage.
   ```

4. **Contradiction resolution section:**
   ```
   ## Contradiction Resolution
   
   If workflow tools disagree:
   - ticket_lookup vs ticket_update: trust ticket_lookup (read) over ticket_update (write) for status
   - workflow_state vs manifest: trust manifest.json over workflow-state.json
   - BOARD.md vs manifest.json: trust manifest.json (BOARD.md is derived)
   - START-HERE.md vs manifest.json: trust manifest.json (START-HERE.md is derived)
   
   If the contradiction cannot be resolved by these rules, stop and escalate.
   ```

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md`

---

## Fix 05-B: Harden Implementer Template

### Evidence

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-implementer.md`

### Required Changes

1. **Add build verification instructions:**
   ```
   ## Build Verification
   
   After completing implementation work on any ticket:
   1. Run the project's build command (if one exists)
   2. If the build fails, fix the errors before claiming implementation is complete
   3. If no build command exists, run a smoke check appropriate to the stack
   4. Never claim implementation is complete without at least one successful build or load check
   ```

2. **Add scope limitation:**
   ```
   ## Scope
   
   You implement ONLY the work specified in the current ticket.
   You do NOT:
   - Advance tickets to review or QA (that's the team leader's job)
   - Modify workflow state files
   - Modify ticket files
   - Create new tickets
   - Make architectural decisions beyond the ticket scope
   ```

3. **Add stack-awareness placeholder:**
   ```
   ## Stack-Specific Notes
   
   {{STACK_SPECIFIC_IMPLEMENTATION_NOTES}}
   ```
   
   This placeholder is filled by `opencode-team-bootstrap` during the greenfield flow with stack-specific guidance (e.g., "For Godot projects: test scenes with `godot --headless`", "For Rust projects: run `cargo clippy` before claiming done").

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-implementer.md`

---

## Fix 05-C: Add Stack-Specific Delegation to Team Bootstrap

### Evidence

**File:** `skills/opencode-team-bootstrap/SKILL.md`
**Problem:** `opencode-team-bootstrap` customizes agent prompts based on the canonical brief, but it does not inject stack-specific operational guidance like "how to verify a Godot scene works" or "how to run Android tests."

### Required Changes

1. **In `opencode-team-bootstrap/SKILL.md`:** Add a section specifying that the bootstrap step must inject stack-specific implementation notes into the implementer template. These notes should cover:
   - How to build the project in this stack
   - How to run a basic verification for this stack
   - Common pitfalls for this stack that agents should avoid
   - Which files are configuration files that need special care

2. **Create a set of stack-specific guidance fragments** that the bootstrap can select from:
   - Godot: scene validation, autoload registration, GDScript type checking
   - Java/Android: gradle tasks, SDK configuration, manifest requirements
   - C/C++: build system invocation, header management, linking
   - .NET: project file structure, NuGet restoration, framework targeting
   - Node.js: dependency management, module resolution, TypeScript compilation
   - Python: virtual environment, dependencies, import verification
   - Rust: cargo commands, feature flags, edition compatibility
   - Go: module management, go vet, go generate

3. **These fragments should NOT be hardcoded into the template.** Instead, the `opencode-team-bootstrap` skill should synthesize them from the canonical brief's stack information. The fragments above serve as a reference catalog.

### Files to Change

- `skills/opencode-team-bootstrap/SKILL.md`

---

## Fix 05-D: Model-Tier-Aware Prompt Density

### Evidence

**File:** `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py`
**Problem:** `build_model_operating_profile()` uses fragile substring matching to detect the model (e.g., checking if the model name contains "gpt-4" or "claude"). The profile affects how verbose the generated prompts are, but the detection is unreliable and the differences between profiles are minor.

### Required Changes

1. **Fix model detection:** Replace substring matching with a more robust approach:
   - Accept a `model_tier` configuration parameter (`"strong"`, `"standard"`, `"weak"`) instead of trying to detect the model name
   - Default to `"weak"` (conservative prompts) if not specified
   - This honors the AGENTS.md principle: "weaker-model-first bias is intentional"

2. **Define tier-specific prompt density:**
   - `"weak"`: Include all stop conditions, all verification checklists, explicit truth-source hierarchy, concrete examples in every section
   - `"standard"`: Include stop conditions and verification checklists, reference truth-source hierarchy by link, fewer examples
   - `"strong"`: Include stop conditions, reference checklists by link, minimal examples

3. **Apply density in agent-prompt-engineering step:** The `agent-prompt-engineering` skill already hardens prompts. Give it access to the model tier so it can adjust prompt density.

### Files to Change

- `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py` — fix model detection
- `skills/agent-prompt-engineering/SKILL.md` — add tier-aware density guidance

---

## Fix 05-E: Add Delegation Chain Documentation

### Problem

The generated repo contains agents but no single document explains who delegates to whom, what the full lifecycle of a ticket looks like from agent perspective, and what happens when an agent gets stuck.

### Required Changes

1. **Generate a `docs/AGENT-DELEGATION.md`** in the generated repo that documents:
   - The agent team composition (generated by opencode-team-bootstrap)
   - The delegation chain: team-leader → implementer → team-leader → reviewer → team-leader → QA → team-leader
   - What each agent can and cannot do
   - The escalation path when an agent is stuck
   - The restart procedure (read START-HERE.md, run ticket_lookup, find active ticket, resume)

2. **This document should be generated by `opencode-team-bootstrap`** as part of the agent team design step. It is derived from the actual agents created, not a generic template.

3. **Reference this document from START-HERE.md** so any agent starting a session can find the delegation chain.

### Files to Change

- `skills/opencode-team-bootstrap/SKILL.md` — add delegation doc generation
- `skills/repo-scaffold-factory/assets/project-template/START-HERE.md` — add reference to delegation doc

---

## Summary Checklist

| Fix | Done? |
|-----|-------|
| 05-A: Team-leader stop conditions and advancement rules | |
| 05-A: Team-leader contradiction resolution | |
| 05-B: Implementer build verification and scope limits | |
| 05-B: Implementer stack-awareness placeholder | |
| 05-C: Stack-specific delegation in team bootstrap | |
| 05-D: Model-tier-aware prompt density | |
| 05-D: Fix model detection in bootstrap_repo_scaffold.py | |
| 05-E: Delegation chain documentation | |
