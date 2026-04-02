# Scafforge Comprehensive Review & Enhancement Plan

**Date:** 2026-04-02
**Scope:** Phase 1-9 implementation audit, flaw identification, and forward-looking enhancement proposals
**Evidence basis:** Recovery plan files, implementation source code, glitchblock1.md agent transcript, archived diagnosis plans, all SKILL.md files, audit/repair scripts, and template tools/agents

---

## Part 1: Phase Implementation Verification

### Phase 01: Workflow Tool Contract Fixes — IMPLEMENTED

All six sub-fixes have been implemented with verified evidence:

| Fix | Status | Evidence |
|-----|--------|----------|
| 01-A: Verdict-aware transition guidance | DONE | `ticket_lookup.ts:246-358` — `extractArtifactVerdict()` called for both review and QA stages. Blocking verdicts route to `implementation` with `recovery_action`. Fields `review_verdict`, `qa_verdict`, and `verdict_unclear` all present in guidance output. |
| 01-B: Smoke-test quote tokenization | DONE | `smoke_test.ts:363` — `tokenizeCommandString()` exists. `failure_classification` enum includes `syntax_error`, `test_failure`, `configuration_error`, `missing_executable`, `permission_restriction`, `command_error`. |
| 01-C: Active-ticket split-brain elimination | DONE | `ticket_lookup.ts:477,531-532` — `is_active` boolean added. `requested_ticket` field separated from canonical `active_ticket`. Root `active_ticket` always from manifest. |
| 01-D: Handoff/context verification metadata | DONE | `handoff_publish.ts:58,68,70` — `verified`, `bootstrap_status` fields present in response. |
| 01-E: Verification state real semantics | DONE | `workflow.ts:14` — `smoke_verified` added to `TicketVerificationState` union. `workflow.ts:1125` transitions to `smoke_verified` on passing smoke test. |
| 01-F: Explicit fail-state routing | DONE | `ticket_lookup.ts:267-280,331-346` — `recovery_action` field populated for both review FAIL and QA FAIL. Team-leader template line 176 instructs following `recovery_action` over happy path. `ticket-execution/SKILL.md` documents `smoke_verified` state. |

### Phase 02: Environment Bootstrap Universality — IMPLEMENTED

| Fix | Status | Evidence |
|-----|--------|----------|
| 02-A: Adapter pattern refactor | DONE | `environment_bootstrap.ts:68-71` — `StackAdapter` interface defined. `STACK_ADAPTERS` array at line 762-780 replaces hardcoded function chain. |
| 02-B: Tier 1 adapters (Godot, Java, C/C++, .NET) | DONE | Lines 561-656 — Godot (with Android SDK and version detection), Java/Android (Gradle/Maven/wrapper), C/C++ (CMake/Make/Meson/compiler detection), .NET (SDK version from global.json). |
| 02-B: Tier 2 adapters (Flutter, Swift, Zig, Ruby) | DONE | Lines 658-707 — Flutter/Dart (pubspec.yaml differentiation), Swift(Xcode detection), Zig, Ruby (bundler). |
| 02-B: Tier 3 adapters (Elixir, PHP, Haskell) | DONE | Lines 709-740 — Elixir (mix.exs), PHP (composer.json), Haskell (cabal/stack). |
| 02-B: Tier 4 generic fallbacks | DONE | Lines 742-760 — Generic Makefile and shell script detection. |
| 02-C: Bootstrap command safety | DONE | Lines 73-101 — `SAFE_BOOTSTRAP_PATTERNS` allowlist with `sudo` rejection. Lines 254-260 — `isSafeBootstrapCommand()` filter. |
| 02-D: Extend SAFE_BASH in stage-gate | DONE | `stage-gate-enforcer.ts:24` — `BOOTSTRAP_RECOVERY_BASH` pattern includes godot, gradle, cmake, dotnet, flutter, swift, zig, ruby, mix, php, composer, stack, cabal, ghc, etc. |
| 02-E: Extend SMOKE_COMMAND_PATTERNS | DONE | `smoke_test.ts:63-84` — Includes godot, gradle, dotnet, cmake patterns plus existing Python/Rust/Go/Node. |
| 02-F: Blockers as environment blockers | DONE | `environment_bootstrap.ts:42-47` — `BootstrapBlocker` type. Line 848 — `workflow.bootstrap_blockers` persisted. Team-leader lines 66 — instructions to not proceed with blockers. |

### Phase 03: Audit Execution Depth — IMPLEMENTED

| Fix | Status | Evidence |
|-----|--------|----------|
| 03-A: Stack-specific execution auditors | DONE | `audit_execution_surfaces.py` — Node.js (EXEC-NODE-001/002/003), Rust (EXEC-RUST-001/002), Go (EXEC-GO-001/002/003), Godot (EXEC-GODOT-001/002), Java (EXEC-JAVA-001/002), C/C++ (EXEC-CPP-001/002), .NET (EXEC-DOTNET-001/002). All with dispatch pattern. |
| 03-B: Reference integrity checker | DONE | `audit_execution_surfaces.py:859` — `audit_reference_integrity()` with REF-003 finding code. Scene refs, config refs, and import path checks. |
| 03-C/D: Finding routing and reporting | DONE | `audit_reporting.py` — Enhanced with EXEC/REF finding families. |
| 03-E: Standalone audit runner | DONE | `skills/scafforge-audit/scripts/run_audit.py` exists as untracked file in git status. |

### Phase 04: Greenfield Proof Expansion — IMPLEMENTED

| Fix | Status | Evidence |
|-----|--------|----------|
| 04-A: VERIFY009 (bootstrap blockers) | DONE | `shared_verifier.py:434-461` — Checks `bootstrap_blockers` field presence and content. Reports missing environment dependencies with remediation guidance. |
| 04-B: VERIFY010 (execution audit) | DONE | `shared_verifier.py:472-478` — Checks for build/load/compile failures with `remediation_action`. |
| 04-C: VERIFY011 (reference integrity) | DONE | `shared_verifier.py:487-493` — Checks for broken structural references with `remediation_action`. |
| 04-D: Actionable remediation | DONE | `shared_verifier.py:48,61` — `remediation_action` field present in findings format. |

### Phase 05: Agent Prompt Hardening — IMPLEMENTED

| Fix | Status | Evidence |
|-----|--------|----------|
| 05-A: Team-leader stop conditions | DONE | `__AGENT_PREFIX__-team-leader.md:101-108` — Five explicit stop conditions. |
| 05-A: Advancement rules | DONE | Lines 109-115 — Verdict checking with FAIL/REJECT/BLOCKED handling. |
| 05-A: Ticket ownership | DONE | Lines 117-128 — Explicit per-stage ownership and artifact authority. |
| 05-A: Contradiction resolution | DONE | Lines 130-138 — Trust hierarchy rules. |
| 05-B: Implementer build verification | DONE | `__AGENT_PREFIX__-implementer.md:66-72` — Build verification section. |
| 05-B: Implementer scope limits | DONE | Lines 73-83 — Explicit scope restrictions. |
| 05-B: Stack-specific notes placeholder | DONE | Lines 84-90 — `SCAFFORGE:STACK_SPECIFIC_IMPLEMENTATION_NOTES` placeholder. |
| 05-D: Model-tier-aware prompt density | DONE | `bootstrap_repo_scaffold.py:64` — `build_model_operating_profile(model_tier=...)` accepts explicit tier parameter. |

### Phase 06: Code Quality Feedback Loop — IMPLEMENTED

| Fix | Status | Evidence |
|-----|--------|----------|
| 06-A: Code quality in review/QA | DONE | `review-audit-bridge/SKILL.md:40` — Requires build/lint/reference-integrity checks with raw command output. |
| 06-A: Stack-specific quality commands | DONE | `stack-standards/SKILL.md:26-32` — Python (ruff, mypy, pytest), Rust (clippy), Go (vet, golangci-lint), Godot (headless checks), C/C++ (cmake --build), .NET (dotnet build/test). |
| 06-C: Finding source in ticket | DONE | `ticket-execution/SKILL.md:82` — Documents `finding_source` field and remediation behavior. |

### Phase 07: Repair Safety and Coverage — IMPLEMENTED

| Fix | Status | Evidence |
|-----|--------|----------|
| 07-A: Non-destructive replacement with backup | DONE | `apply_repo_process_repair.py:66,297-325` — `--preserve-backups` flag. `backup_path` computed, `copytree` backup before replacement, restore on failure. |
| 07-A: Diff summary | DONE | Line 178 — `build_managed_surface_diff_summary()`. Lines 1042,1155 — `diff_summary` in provenance records. |
| 07-B: Enhanced provenance | DONE | Lines 278-285, 1021-1049 — `diff_summary`, `backup_path`, audit findings addressed in provenance. |

### Phase 08: Scaffold Template Fixes — IMPLEMENTED

| Fix | Status | Evidence |
|-----|--------|----------|
| 08-A: Fix model detection | DONE | `bootstrap_repo_scaffold.py:64` — `model_tier` explicit parameter. Line 132 — Idempotency check for existing `.opencode`. |
| 08-B: Scaffold verification | DONE | `verify_generated_scaffold.py:15,85,112,162,173,190` — `PLACEHOLDER_PATTERN`, SCAFFOLD-001 (residue), SCAFFOLD-002 (invalid JSON), SCAFFOLD-003 (cross-reference), SCAFFOLD-004 (project name consistency). |

### Phase 09: Contract and Doc Updates — IMPLEMENTED

| Fix | Status | Evidence |
|-----|--------|----------|
| 09-C: README.md | DONE | README.md now includes Supported Stacks section with 4 tiers. |
| 09-D: AGENTS.md | DONE | AGENTS.md updated with environment bootstrap, VERIFY009-011 references, maintenance checklist additions. |
| 09-E: stack-adapter-contract.md | DONE | File exists at `references/stack-adapter-contract.md`. |
| 09-G: Archived references annotated | DONE | `archived-diagnosis-plans/README.md` marked as REFERENCE. Deadlock hardening marked as ARCHIVED. |

### Summary: All 9 phases are substantively implemented

The implementation is thorough and well-executed. Every major fix from the plan is present in the codebase.

---

## Part 2: Critical Flaw — QA/Review FAIL Backward Transition is Blocked

### The Problem

Despite Phase 01's verdict-aware guidance being correctly implemented in `ticket_lookup.ts`, the Glitch agent **still got permanently stuck** because `ticket_update.ts` enforces a hard gate at line 90:

```typescript
if (targetStage === "implementation" && ticket.stage !== "plan_review") {
  throw new Error(`Cannot move ${ticket.id} to implementation before it passes through plan_review.`)
}
```

**This means backward transitions from review or QA to implementation are rejected by `ticket_update`**, even though `ticket_lookup.transition_guidance` correctly recommends them.

### Evidence from glitchblock1.md

The Glitch agent session ends at line 13317-13411 with the agent recognizing exactly this contradiction:

> "The QA verdict is FAIL with blockers that prevent the glitch system from functioning at runtime. Advancing to smoke-test would be inappropriate since the initialization chain is fundamentally broken."

> "The workflow cannot advance forward from QA with a FAIL verdict, and cannot move backward to implementation due to lifecycle constraints. This blocker must be resolved before CORE-002 can proceed."

The agent correctly identified the transition guidance says "route back to implementation" but the lifecycle enforcement prevents it. This is the **exact deadlock** that caused the 500+ line circular reasoning documented in the recovery plan.

### Root Cause

`ticket_lookup.ts` (Phase 01-A) now correctly sets `next_allowed_stages: ["implementation"]` when review or QA verdict is FAIL. But `ticket_update.ts` only allows the `implementation` stage from `plan_review`. There's no backward transition path.

### Assessment

This is a **P0 critical bug** — it means the primary benefit of Phase 01-A (verdict-aware routing) is blocked at the execution layer. The agent can see the correct action but cannot execute it.

### Required Fix

In `ticket_update.ts`, the guard at line 90 must be relaxed to allow backward transitions from review/QA stages when the verdict is FAIL:

```typescript
if (targetStage === "implementation" && ticket.stage !== "plan_review"
    && ticket.stage !== "review" && ticket.stage !== "qa") {
  throw new Error(`Cannot move ${ticket.id} to implementation. Allowed source stages: plan_review, review (on FAIL verdict), qa (on FAIL verdict).`)
}
```

This is the **single most important remaining fix** in the entire project.

---

## Part 3: Additional Flaws and Gaps

### Flaw 3.1: Glitch Agent Used Outdated Template (Pre-Phase 01)

**Evidence:** The `livetesting/glitch/` project was generated BEFORE the 10-phase plan was implemented. The `ticket_lookup.ts` in glitch (line 13244 of glitchblock1.md) shows `next_allowed_stages: ["smoke-test"]` despite a QA FAIL — this is pre-Phase-01 behavior where transition guidance did not check verdict.

**Impact:** The glitch project's tools are stale. Even if Phase 01 code is correct in the Scafforge template, the live glitch instance has the old tools.

**Recommendation:** After fixing the backward-transition bug (Part 2), re-scaffold or repair `livetesting/glitch/` with updated templates. This validates the fix against the original failure scenario.

### Flaw 3.2: No Integration Test for Backward Transitions

**Evidence:** The recovery plan Phase 01 verification section says to "Write or extend an integration test that confirms `ticket_update` rejects the review->qa transition when the review artifact contains FAIL." It does NOT mention testing the backward (review->implementation or qa->implementation) transition path.

**Impact:** The backward transition bug could have been caught by a test that creates a ticket at QA stage with a FAIL artifact and then attempts `ticket_update(stage="implementation")`.

**Recommendation:** Add regression tests in `scripts/integration_test_scafforge.py` that verify:
1. From review with FAIL verdict, `ticket_update(stage="implementation")` succeeds
2. From QA with FAIL verdict, `ticket_update(stage="implementation")` succeeds
3. From review with PASS verdict, `ticket_update(stage="implementation")` is rejected (don't allow arbitrary backward motion)

### Flaw 3.3: Plan 05-E (Delegation Chain Documentation) Not Verified

**Evidence:** The recovery plan specifies generating a `docs/AGENT-DELEGATION.md` in generated repos. Checking the template:

```
skills/repo-scaffold-factory/assets/project-template/docs/AGENT-DELEGATION.md
```

This file exists as an untracked file in git status (`?? skills/repo-scaffold-factory/assets/project-template/docs/AGENT-DELEGATION.md`), suggesting it was created but not yet committed.

**Impact:** Minor — the delegation chain documentation exists in the template but may not be connected to the generation flow yet.

### Flaw 3.4: Phase 06-B and 06-D Not Fully Verified

**Evidence:** The plan calls for:
- 06-B: Remediation ticket generation from audit findings with `ticket-pack-builder` remediation mode
- 06-D: Quality dashboard in START-HERE.md via `handoff_publish.ts`

These are harder to verify from static code reading. The `handoff_publish.ts` shows `verified` and `bootstrap_status` but does not clearly show a "Code Quality Status" section in the restart surface. The `ticket-pack-builder/SKILL.md` should have a "remediation mode" entry.

**Recommendation:** Verify these during Phase 10 proof targets.

### Flaw 3.5: `run_audit.py` Is Untracked

**Evidence:** `skills/scafforge-audit/scripts/run_audit.py` appears in git status as untracked (`??`).

**Impact:** This standalone audit runner exists but is not committed to the repository.

---

## Part 4: Issues That Could Surface in the Future

### 4.1: Multi-Session State Corruption

**Risk:** When an agent session crashes mid-transition (between `ticket_update` writing to manifest and the subsequent tool call), the workflow state can become inconsistent. The current save pattern in `saveWorkflowBundle()` writes multiple files (manifest.json, workflow-state.json) non-atomically.

**Evidence:** The archived `SCAFFORGE-STATE-CLEANUP-2026-03-27.md` documents state drift from exactly this pattern.

**Mitigation already present:** The team-leader template has lease cleanup instructions.

**Potential enhancement:** Add a write-ahead-log or transaction-id pattern to `saveWorkflowBundle()` so that partial writes can be detected and rolled back. This is a low-frequency but high-impact failure mode.

### 4.2: Ticket Graph Cycles and Deadlocks

**Risk:** When `ticket_create(source_mode=split_scope)` creates child tickets, and those child tickets have dependency edges pointing at each other or back at the parent, the ticket graph can contain cycles. The `blockedDependentTickets()` function may not detect cycles.

**Evidence:** Commit `0c3f7d6` — "Auto-fix WFLOW019 ticket graph contradictions during managed repair" suggests this has already surfaced.

**Potential enhancement:** Add cycle detection to `ticket_lookup.ts` or `ticket_update.ts` that rejects transitions creating dependency cycles.

### 4.3: Weak Model Prompt Overflow

**Risk:** The team-leader template is now 247 lines long with detailed stop conditions, advancement rules, ownership tables, contradiction resolution, process-change verification, and many rules. Weak models may not reliably follow all of these instructions, especially when the prompt is near the model's effective instruction-following limit.

**Evidence:** The Glitch agent used MiniMax-M2.7 (line 13317 of glitchblock1.md). The thinking trace shows the model correctly identifying the contradiction but not having a tool-level escape hatch.

**Potential enhancement:** For weak-model profiles, consider splitting the team-leader prompt into a core prompt + dynamically loaded skill expansions. Only load the "Contradiction Resolution" and "Process-change verification" sections when the current state actually triggers those conditions.

### 4.4: Smoke Test Tool Doesn't Validate Quote Handling

**Evidence:** Phase 01-B says to fix quote tokenization in `tokenizeCommandString()`. The function exists at `smoke_test.ts:363`, but the actual implementation wasn't fully verified for correctness. The original bug was quote characters being dropped during tokenization.

**Recommendation:** Add a unit-level test specifically for `tokenizeCommandString()` with the original failing input:
```
grep -E '(PlayerState|GlitchState).*Initialized'
```
Verify the output is `["grep", "-E", "(PlayerState|GlitchState).*Initialized"]`.

### 4.5: Audit Execution Surfaces Require System Toolchains

**Risk:** The stack-specific execution auditors (Phase 03-A) try to run `cargo check`, `go vet`, `cmake -S . -B build_check`, `dotnet build`, etc. If these tools are not installed on the audit host, the audit silently skips those checks rather than reporting "cannot audit this stack."

**Evidence:** The Godot auditor at `audit_execution_surfaces.py:782` checks if Godot is available before running headless checks, but the reporting of "audit skipped because tool not available" is not a first-class finding.

**Potential enhancement:** Add an `AUDIT-SKIP-*` finding family that reports when an audit check was skipped because the required toolchain was not present. This prevents false confidence from an audit that reports zero findings simply because it couldn't run any checks.

---

## Part 5: Enhancement Opportunities

### 5.1: Automatic Backward Transition with Audit Trail

Beyond the critical fix in Part 2, the backward transition should create an audit trail:
- When routing from QA back to implementation, automatically record which QA findings triggered the regression
- Increment a `regression_count` on the ticket
- After 3 regressions on the same ticket, escalate to the operator rather than continuing the loop

### 5.2: Pre-flight Validation in ticket_update

Currently `ticket_update` validates prerequisites for forward transitions but not for backward ones. Add pre-flight validation for backward transitions:
- From review to implementation: require a review artifact with FAIL verdict
- From QA to implementation: require a QA artifact with FAIL verdict
- This prevents arbitrary backward motion while enabling verdict-driven regression routing

### 5.3: Health Check Command in Generated Repos

Add a `health_check` tool to the generated template that runs all available quality checks and returns a single pass/fail with details. This gives agents a one-command "is this project healthy?" check without needing to know which stack-specific commands to run.

### 5.4: Incremental Audit Mode

Currently `scafforge-audit` runs a full audit every time. For large repos, add an incremental mode that:
- Tracks which files changed since the last audit
- Only runs checks relevant to changed files
- Falls back to full audit when too many files changed or when forced

### 5.5: Verdict Normalization

The `extractArtifactVerdict()` function parses free-text artifacts looking for PASS/FAIL patterns. This is inherently fragile. Consider:
- Adding a structured `verdict` field to artifact metadata at registration time
- Having `artifact_register` extract the verdict once and store it
- Using the stored verdict in `ticket_lookup` instead of re-parsing every time

This eliminates the "verdict_unclear" edge case and makes verdict checking deterministic.

### 5.6: Session Recovery Playbook

When an agent session ends unexpectedly (crash, context limit, tool error), the restart surface (START-HERE.md) may not reflect the latest state. Add:
- A `session_recovery` tool that detects dirty state (incomplete lease, partial artifact, staged but uncommitted artifact writes)
- Automatic invocation guidance in the team-leader template when the latest context-snapshot is stale

---

## Part 6: Prioritized Action Items

### P0 — Must Fix Before Phase 10

1. **Fix backward transition guard in `ticket_update.ts`** (Part 2)
   - Allow `implementation` stage from `review` and `qa` when verdict is FAIL
   - This unblocks the primary value proposition of Phase 01-A

2. **Add backward transition regression tests** (Flaw 3.2)
   - Test forward-block: cannot go to smoke-test with FAIL QA
   - Test backward-allow: can go to implementation from QA with FAIL
   - Test backward-block: cannot go to implementation from QA with PASS

### P1 — Should Fix Before Production Use

3. **Add AUDIT-SKIP finding family** (Issue 4.5)
   - Report when stack-specific audit checks were skipped due to missing toolchain
   - Prevents false confidence from zero-finding audits on unchecked stacks

4. **Verify and commit `run_audit.py`** (Flaw 3.5)
   - Ensure standalone audit runner works end-to-end
   - Commit to repository

5. **Re-scaffold `livetesting/glitch/` with updated templates** (Flaw 3.1)
   - Validates the backward transition fix against the original failure
   - Serves as Phase 10 Target 05 proof

6. **Add pre-flight validation for backward transitions** (Enhancement 5.2)
   - Require FAIL verdict evidence before allowing backward motion
   - Prevents arbitrary backward transitions while enabling verdict-driven routing

### P2 — Quality Improvements

7. **Structured verdict storage at artifact registration** (Enhancement 5.5)
8. **Cycle detection in ticket graph** (Issue 4.2)
9. **AUDIT-SKIP to diagnosis reports** (Issue 4.5)
10. **Session recovery tooling** (Enhancement 5.6)

---

## Reasoning Summary

The 10-phase recovery plan was ambitious and has been executed with remarkable thoroughness. Phases 1-9 are all substantively implemented. The universal stack adapter registry (Phase 02), verdict-aware transition guidance (Phase 01-A), and stack-specific execution auditors (Phase 03-A) in particular represent major improvements to the package.

However, the **single critical remaining flaw** — the `ticket_update.ts` backward transition guard at line 90 — means the most important fix (verdict-aware fail routing) cannot actually execute. The agent can SEE it should go back to implementation, but the tool BLOCKS it. This is the exact deadlock that caused the Glitch agent to get permanently stuck at the end of its session.

Fixing this one guard clause, adding the corresponding regression test, and then re-running against the Glitch test case would prove the entire 10-phase plan works end-to-end. Without this fix, verdict-aware transition guidance is guidance-only, not enforcement.
