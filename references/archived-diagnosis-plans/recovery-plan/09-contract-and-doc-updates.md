# Phase 09: Contract and Documentation Updates

**Priority:** P2 — Medium
**Depends on:** Phases 01–08 (docs should reflect completed work, not aspirations)
**Goal:** Update all contract files, references, and docs to reflect the hardened package

---

## Problem Statement

After Phases 01–08 land, the package's documentation and contract files will be out of date. They currently describe behavior that will have changed. Contracts must reflect actual package behavior or they lose authority.

---

## Fix 09-A: Update `competence-contract.md`

### Evidence

**File:** `references/competence-contract.md`

### Required Changes

1. **Add universal stack support commitment.** The contract should state that Scafforge detects and bootstraps dependencies for all Tier 1 stacks (Python, Node, Rust, Go, Godot, Java/Android, C/C++, .NET) and gracefully degrades for unsupported stacks.

2. **Add code quality commitment.** The contract should state that greenfield scaffolds must pass stack-specific execution checks and reference-integrity checks before handoff.

3. **Add audit depth commitment.** The contract should state that the audit produces code-quality findings in addition to workflow-surface findings.

4. **Add repair safety commitment.** The contract should state that managed-surface replacement is non-destructive with backup and diff tracking.

5. **Verify and update any existing assertions** that are now inaccurate after the other phases.

### Files to Change

- `references/competence-contract.md`

---

## Fix 09-B: Update `one-shot-generation-contract.md`

### Evidence

**File:** `references/one-shot-generation-contract.md`

### Required Changes

1. **Add the new VERIFY checks** (009, 010, 011) to the greenfield verification chain documentation.

2. **Add the environment bootstrap gate** to the one-shot flow. The contract should specify that the single greenfield pass includes environment detection and that blockers halt the pass with user-actionable guidance.

3. **Clarify the code quality position:** Generated code must pass basic structural integrity checks (can it build? are references valid?) but the contract does not guarantee bug-free implementation — that's what the ticket lifecycle and code quality feedback loop handle.

4. **Document the model-tier configuration.** The one-shot contract should note that `model_tier` affects prompt density but not flow fidelity.

### Files to Change

- `references/one-shot-generation-contract.md`

---

## Fix 09-C: Update `README.md`

### Evidence

**File:** `README.md`

### Required Changes

1. **Add a "Supported Stacks" section** listing the Tier 1–4 stacks with detection and bootstrap support levels:
   - Tier 1 (full detection + bootstrap + execution audit): Python, Node, Rust, Go, Godot, Java/Android, C/C++, .NET
   - Tier 2 (detection + bootstrap): Flutter, Swift, Zig, Ruby
   - Tier 3 (detection): Elixir, PHP, Haskell
   - Tier 4 (generic fallback): Makefile, shell scripts

2. **Update the "What Scafforge generates" section** to mention:
   - Code quality feedback loop (review/QA stages check build and references)
   - Stack-specific smoke tests and environment bootstrap
   - Verdict-aware ticket transitions

3. **Update the "How to use" section** to mention:
   - `model_tier` configuration option
   - Multi-stack capability
   - The recovery-plan directory for implementation details

### Files to Change

- `README.md`

---

## Fix 09-D: Update `AGENTS.md`

### Evidence

**File:** `AGENTS.md`

### Required Changes

1. **In "Default scaffold spine":** Note that the phase runs environment bootstrap detection and stack-specific execution checks as part of the greenfield proof chain.

2. **In "Canonical workflow contract > Greenfield full-cycle scaffold":** Add:
   - Step 3.5: Environment bootstrap runs, blockers halted
   - Update step 4 (bootstrap-lane proof) to reference VERIFY009
   - Update step 9 (continuation verification) to reference VERIFY010, VERIFY011

3. **In "Product contract refinements":** Add:
   - The greenfield handoff must pass stack-specific execution checks, not just workflow alignment
   - Audit diagnosis includes code quality findings (EXEC, REF families)
   - Repair is non-destructive with backup and diff tracking

4. **In "Canonical generated-repo truth hierarchy":** No changes needed unless the truth hierarchy changed.

5. **In "Skill boundary rules":** Update `scafforge-audit` to mention code quality finding capability. Update `scafforge-repair` to mention code-quality ticket generation.

6. **In "Maintenance checklist":** Add:
   - Verify stack adapter registry covers Tier 1 stacks
   - Verify post-repair verification uses stack-specific checks
   - Verify audit produces code quality findings for non-Python stacks

### Files to Change

- `AGENTS.md`

---

## Fix 09-E: Create `references/stack-adapter-contract.md`

### Rationale

The stack adapter pattern (environment bootstrap, execution audit, smoke test) is a cross-cutting concern that touches multiple skills. A reference contract keeps the adapter interface consistent.

### Content

1. **Stack adapter interface:** Define the common interface for detection, bootstrap, and execution audit adapters.

2. **Tier classification:** Define what each tier means (full, detection + bootstrap, detection only, generic fallback).

3. **Adding a new stack:** Step-by-step guide for adding a new stack adapter:
   - Add detection in `environment_bootstrap.ts`
   - Add patterns in `smoke_test.ts`
   - Add patterns in `stage-gate-enforcer.ts`
   - Add execution auditor in `audit_execution_surfaces.py`
   - Add guidance fragment for `opencode-team-bootstrap`
   - Update README and AGENTS.md

4. **Testing a new adapter:** What the proof program (Phase 10) requires for each new stack.

### Files to Create

- `references/stack-adapter-contract.md`

---

## Fix 09-F: Update Skill SKILL.md Files

### Required Changes

After phases 01–08 land, several skill files will need minor updates:

1. **`scaffold-kickoff/SKILL.md`:** Reference VERIFY009–011, environment bootstrap gate, model_tier parameter.

2. **`repo-scaffold-factory/SKILL.md`:** Reference stack adapter registry, updated template content, verify_generated_scaffold additions.

3. **`scafforge-audit/SKILL.md`:** Reference EXEC and REF finding families, code quality in diagnosis reports, finding routing precision.

4. **`scafforge-repair/SKILL.md`:** Reference non-destructive replacement, code-quality ticket generation, intent-changing escalation criteria.

5. **`project-skill-bootstrap/SKILL.md`:** Reference stack-specific quality commands in generated skills.

6. **`opencode-team-bootstrap/SKILL.md`:** Reference stack-specific delegation, delegation chain document, stack guidance fragments.

7. **`ticket-pack-builder/SKILL.md`:** Reference remediation mode.

8. **`agent-prompt-engineering/SKILL.md`:** Reference model-tier prompt density.

### Approach

These updates should happen AFTER the corresponding phase is implemented. Each skill file update should be a direct reflection of what actually changed, not forward-looking documentation.

### Files to Change

- All `skills/*/SKILL.md` files as listed above

---

## Fix 09-G: Clean Up Archived References

### Evidence

**Directory:** `references/archived-diagnosis-plans/`
**Problem:** Contains 15+ files from previous diagnosis, remediation, and review iterations. Some may contain outdated or contradictory guidance.

### Required Changes

1. **Review each file** in `archived-diagnosis-plans/` against the new recovery plan.
2. **If a file contradicts the recovery plan:** Add a note at the top: `> **ARCHIVED:** This document is superseded by the recovery-plan/ directory.`
3. **If a file contains still-valid reference information:** Keep it but add a note: `> **REFERENCE:** Still valid as historical context. See recovery-plan/ for current work.`
4. **Do NOT delete files** — they contain provenance and historical context.

### Files to Review

- All files in `references/archived-diagnosis-plans/`

---

## Summary Checklist

| Fix | Done? |
|-----|-------|
| 09-A: Update competence-contract.md | |
| 09-B: Update one-shot-generation-contract.md | |
| 09-C: Update README.md | |
| 09-D: Update AGENTS.md | |
| 09-E: Create stack-adapter-contract.md | |
| 09-F: Update skill SKILL.md files (after implementation) | |
| 09-G: Annotate archived references | |
