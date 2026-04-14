# Root Cause Map — Scafforge Recovery

Generated: 2026-04-10
Status: Active — updated as fixes are implemented

---

## RC-001: managed_blocked enforcement not centralized

**Symptom:** Agents can potentially bypass managed_blocked state via stage-gate-enforcer gaps.
**Local trigger:** stage-gate-enforcer.ts plugin validates leases and artifact evidence but does NOT check repair_follow_on.outcome.
**Structural cause:** managed_blocked enforcement is scattered across 11+ files (Python repair scripts + TypeScript tools/plugins) with no single enforcement point.
**Evidence:** The original gap was real, but current package code now enforces managed_blocked in both `ticket_update.ts` and `stage-gate-enforcer.ts` (commit `906dc002`), with the missing import corrected in commit `686cc74a`.
**Downstream effect:** Agent could advance ticket lifecycle during active repair block. Could cause stale state or divergent repair tracking.
**Remediation:** Add managed_blocked check to stage-gate-enforcer.ts plugin's pre-execution hook. Verify ticket_create also checks.
**Validation:** Write integration test that seeds managed_blocked state and verifies stage-gate blocks lifecycle tools.
**Status:** RESOLVED — implemented in commit `906dc002`, import fixed in `686cc74a`, and validation-log.md records the managed_blocked blocker firing correctly.

---

## RC-002: deterministic-refresh is a non-catalog stage name

**Symptom:** completed_stages can contain "deterministic-refresh" which is not in FOLLOW_ON_STAGE_CATALOG.
**Local trigger:** run_managed_repair.py line ~1146 injects "deterministic-refresh" into completed_stage_name_set.
**Structural cause:** deterministic-refresh is a repair-internal operation (template variable refresh), not a follow-on stage. It was incorrectly treated as a stage.
**Evidence:** The original contamination was real. Current repair output now marks deterministic refresh as an internal-only operation rather than a catalog stage (commit `906dc002`), so downstream follow-on tracking no longer needs to treat it as a real completed stage.
**Downstream effect:** completed_stages contains a name that can't be validated against catalog. reconcile_repair_follow_on uses completed_stages from the ledger (which won't include deterministic-refresh since it's not recordable), but the workflow-state copy retains it.
**Remediation:** Remove deterministic-refresh from stage name injection. Track it as a repair-internal operation flag, not a stage.
**Validation:** Verify completed_stages only contains catalog-valid names after repair runs.
**Status:** RESOLVED — repair output now keeps deterministic refresh out of the follow-on stage catalog and validation-log.md records the cleaned state.

---

## RC-003: completed_stages assertion-vs-evidence distinction

**Symptom:** Two parallel fields track stage completion: completed_stages (evidence-based) and asserted_completed_stages (assertion-based).
**Local trigger:** reconcile_repair_follow_on.py line ~167-180 preserves asserted_completed_stages from prior state without re-validation while populating completed_stages from persistent ledger.
**Structural cause:** Legacy manual assertion path was never fully deprecated. Both fields can diverge.
**Evidence:** reconcile code keeps both fields. regenerate_restart_surfaces.py line ~250 uses completed_stages directly.
**Downstream effect:** Stale assertion-based completions could be preserved even after evidence is invalidated.
**Remediation:** Deprecate asserted_completed_stages. Only use ledger-recorded completions. Add validation that completed_stages entries are all in the persistent tracking ledger.
**Validation:** After fix, verify only ledger-backed completions appear in completed_stages.
**Status:** OPEN

---

## RC-004: SKILL001 as stage-linked blocker

**Symptom:** SKILL001 (placeholder local skills) creates managed_blocked state that requires project-skill-bootstrap follow-on.
**Local trigger:** audit_contract_surfaces.py detects placeholder skills and emits SKILL001 finding. Repair then requires project-skill-bootstrap stage.
**Structural cause:** This is actually WORKING AS DESIGNED — SKILL001 correctly identifies placeholder drift and routes to managed_blocked with project-skill-bootstrap as required stage.
**Evidence:** glitch repair-execution.json shows SKILL001 correctly routing through managed_blocked → project-skill-bootstrap → reconcile.
**Downstream effect:** None — this is correct behavior. The promptfile lists it for re-examination to confirm it still works.
**Remediation:** Confirm correct behavior. Document as working.
**Validation:** Verify in glitch that project-skill-bootstrap completion correctly cleared SKILL001-induced blocking.
**Status:** CONFIRMED WORKING

---

## RC-005: WFLOW031 — Predictive Repair Trap

**Symptom:** Agents preemptively route to repair/audit flow when they encounter state that LOOKS problematic but is actually normal workflow state (e.g., verification_state: "suspect", pending_process_verification: true).
**Local trigger:** Team leader agent sees "suspect" verification state or pending flags and interprets them as requiring repair action, instead of continuing normal ticket lifecycle.
**Structural cause:** Insufficient guidance in team-leader agent template about what constitutes a REAL repair need vs. normal lifecycle state. glitchresearch.md Issue 4 documents verification_state "suspect" persisting through entire lifecycle until closeout — agents misread this as a problem.
**Evidence:** glitchresearch.md Issue 4 (Verification_State Semantics Gap), evenmoreblockers.md observations, and the follow-up package fix in commit `906dc002` that added explicit anti-pattern guidance to the team-leader template.
**Downstream effect:** Agent enters repair analysis instead of advancing tickets, creating time waste and potential repair loops.
**Remediation:** 1) Add explicit guidance to team-leader template about what states are NORMAL (suspect until closeout, pending_process_verification during backlog verification). 2) Add WFLOW031 finding code to audit scripts to detect when agents route to repair without managed_blocked outcome. 3) Clarify verification_state semantics in docs.
**Validation:** Run agent against repo with "suspect" verification_state and confirm it continues normally.
**Status:** RESOLVED — anti-pattern guidance landed in commit `906dc002`; validation-log.md records agents self-unblocking instead of spiraling into predictive repair.

---

## RC-006: stage-gate-enforcer backward routing during managed_blocked

**Symptom:** Backward routing (review→implementation, qa→implementation) could be allowed even when managed_blocked is active.
**Local trigger:** stage-gate-enforcer validates backward routing based on artifact verdict only, not repair_follow_on state.
**Structural cause:** Backward routing validation and managed_blocked validation are separate concerns that were never connected.
**Evidence:** stage-gate-enforcer.ts lines 100-123 check verdict but not repair state. Integration tests cover backward routing but not combined with managed_blocked.
**Downstream effect:** Agent could route backward during active repair, potentially creating state confusion.
**Remediation:** Add managed_blocked check before allowing any stage transition (forward or backward) in stage-gate-enforcer.
**Validation:** Test that backward routing is blocked when managed_blocked is active.
**Status:** OPEN — but low severity since managed_blocked also blocks via ticket_update.ts

---

## RC-007: Smoke test monolithic structure

**Symptom:** smoke_test_scafforge.py is 9778 lines with 1 test function and a single main() entrypoint.
**Local trigger:** All validation logic accumulated in one file over time.
**Structural cause:** No refactoring discipline applied as test grew.
**Evidence:** File size: 9778 lines. grep "def test_" finds only 1 function (a stub). 65 functions total but all called from main().
**Downstream effect:** Cannot isolate test failures. No pytest integration. Slow iteration.
**Remediation:** This is a Phase 4 concern — assess whether splitting is needed for current work. The promptfile says "smoke tool architecture if it has become monolithic or diagnostically weak."
**Validation:** After any restructuring, all existing test scenarios must still pass.
**Status:** OPEN — deferred to implementation phase assessment

---

## RC-008: Python-only validation gap

**Symptom:** Scafforge generates repos for any stack (Godot, Rust, Go, Java, etc.) but audit/validation tooling only validates Python projects.
**Local trigger:** audit scripts use Python-specific checks (import validation, pytest discovery, etc.).
**Structural cause:** Validation layer was built for initial Python-only targets and never generalized.
**Evidence:** glitchresearch.md "Critical Discovery: Universal Generation vs Python-Only Validation."
**Downstream effect:** Non-Python repos get false success reports from audit. Godot repos (glitch, spinner) cannot be properly validated.
**Remediation:** Add stack-aware validation adapters. For current work: at minimum, Godot export validation (APK build check). Longer term: stack adapter contract (references/stack-adapter-contract.md exists).
**Validation:** Audit of spinner/glitch should detect Godot-specific issues.
**Status:** OPEN — partial fix needed for current targets

---

## RC-009: Transition guidance ignores artifact verdict

**Symptom:** transition_guidance says "advance to QA" even when review verdict is FAIL.
**Local trigger:** buildTransitionGuidance() checks artifact PRESENCE but not artifact VERDICT.
**Structural cause:** Guidance builder treats artifact existence as evidence of stage completion, ignoring the content of the artifact.
**Evidence:** glitchresearch.md Issue 5 (Transition Guidance / Verdict Mismatch).
**Downstream effect:** Agent sees contradictory signals — verdict says FAIL, guidance says advance. Causes "Wait/Actually" confusion loops.
**Remediation:** Already implemented in current code.
**Validation:** ticket_lookup.ts lines 282-316 extract review verdict and route back to implementation on FAIL. Lines 348-393 do the same for QA verdict. Verified by code inspection.
**Status:** ALREADY FIXED — no action needed

---

## Downstream Repo Status (Not Scafforge bugs — current state for agent runs)

**GPTTalker:** All tickets appear done (EDGE-004 closeout/done). repair_follow_on: source_follow_up (not blocking). Need: verify MCP server starts, code review.
**Spinner:** RELEASE-001 at review stage. repair_follow_on: source_follow_up (not blocking). Need: continue through review→qa→smoke-test→closeout.
**Glitch:** RELEASE-001 at qa stage. repair_follow_on: clean (not blocking). Need: continue through qa→smoke-test→closeout.
