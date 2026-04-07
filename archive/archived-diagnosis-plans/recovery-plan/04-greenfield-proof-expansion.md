# Phase 04: Greenfield Proof Expansion

**Priority:** P1 — High
**Depends on:** Phase 02 (environment bootstrap), Phase 03 (audit execution depth)
**Goal:** Make the greenfield proof gates catch non-functional scaffolds before handoff

---

## Problem Statement

`shared_verifier.py` contains two greenfield verification functions:
- `verify_greenfield_bootstrap_lane()` — confirms one canonical first move exists
- `verify_greenfield_continuation()` — checks 8 contract-alignment markers (VERIFY001–VERIFY008)

All 8 markers check **workflow surface alignment** — do the files exist, do they reference each other correctly, does the truth hierarchy agree. None of them check:
- Can the project actually build?
- Are required tools present on this system?
- Are there broken references between code files and configuration?
- Does the generated code contain obvious structural errors?

This means a greenfield scaffold can pass VERIFY001–VERIFY008 while being completely non-functional. Glitch passed the workflow verifiers despite having broken autoloads, missing Android SDK, and non-compilable scenes.

---

## Fix 04-A: Add Stack-Viability Verification Gate

### Required Changes

Add `VERIFY009` to `shared_verifier.py`:

**VERIFY009: Environment bootstrap reports zero unresolved blockers**

1. After environment_bootstrap tool output is captured (during the bootstrap-lane proof), parse the response for the `blockers` array (added in Phase 02-F).
2. If `blockers` is non-empty, VERIFY009 fails with message: `"Greenfield proof failed — missing environment dependencies: {list_of_blockers}"`
3. If `blockers` is empty or absent, VERIFY009 passes.

**Implementation approach:** Since `shared_verifier.py` runs as a Python script in the Scafforge host context (not inside the generated repo), it cannot directly invoke the TypeScript `environment_bootstrap.ts`. Instead:
- Option A: Have the bootstrap-lane step write an `environment-bootstrap-result.json` to `.opencode/state/artifacts/` and have VERIFY009 read that JSON.
- Option B: Re-implement the detection logic in Python within `shared_verifier.py`. (Simpler but duplicates logic.)
- **Recommended: Option A.** The bootstrap-lane proof already exercises tools; having it emit a machine-readable bootstrap result is cheap and avoids duplication.

### Files to Change

- `skills/scafforge-audit/scripts/shared_verifier.py` — add `VERIFY009` check
- `skills/scaffold-kickoff/SKILL.md` — update bootstrap-lane proof to emit `environment-bootstrap-result.json`

---

## Fix 04-B: Add Build-Readiness Verification Gate

### Required Changes

Add `VERIFY010` to `shared_verifier.py`:

**VERIFY010: Stack-specific execution check reports zero CRITICAL findings**

1. After the scaffold is generated and the bootstrap-lane proof runs, the greenfield flow should run a lightweight execution audit (from Phase 03-A) against the generated repo.
2. The execution audit writes findings to `.opencode/state/artifacts/execution-audit-result.json`.
3. VERIFY010 reads that JSON. If any findings have severity CRITICAL, VERIFY010 fails with the finding details.
4. HIGH and MEDIUM findings are logged as warnings but do not fail the gate.

**What counts as CRITICAL at greenfield time:**
- `EXEC-*-001` (entry point or main module cannot load/compile) — CRITICAL
- `EXEC-*-002` (test compilation failure) — HIGH (tests may not exist yet)
- `REF-001` (scene→script reference broken) — CRITICAL for game projects, HIGH otherwise
- `REF-002` (config→code reference broken) — CRITICAL
- `REF-003` (import→module missing) — HIGH

### Files to Change

- `skills/scafforge-audit/scripts/shared_verifier.py` — add `VERIFY010` check
- `skills/scaffold-kickoff/SKILL.md` — update continuation verification to reference VERIFY010

---

## Fix 04-C: Add Reference-Integrity Verification Gate

### Required Changes

Add `VERIFY011` to `shared_verifier.py`:

**VERIFY011: Reference integrity audit reports zero broken structural references**

This specifically catches the Glitch failure pattern:
- `project.godot` declares autoloads pointing to non-existent scripts
- `.tscn` files reference scripts that don't exist
- Config files reference paths that don't resolve

1. The continuation verification step runs `audit_reference_integrity()` (from Phase 03-B) against the generated repo.
2. Results are written to `.opencode/state/artifacts/reference-integrity-result.json`.
3. VERIFY011 reads that JSON. If any structural reference is broken, VERIFY011 fails.

### Files to Change

- `skills/scafforge-audit/scripts/shared_verifier.py` — add `VERIFY011` check

---

## Fix 04-D: Fail Fast with Actionable Remediation

### Problem

When a VERIFY check fails during greenfield, the failure message is often a code like `VERIFY004 failed` with a brief description. The host agent does not always know what to do next.

### Required Changes

1. **Add remediation guidance to each VERIFY failure.** When a check fails, the verifier should return not just the failure code and message, but also:
   - `remediation_action`: What the host should do (e.g., "Install the missing dependency", "Fix the broken autoload reference in project.godot line 42")
   - `remediation_target`: Which file needs fixing
   - `is_user_action`: Boolean — whether this requires user input (e.g., installing system packages) vs. can be fixed by the agent

2. **In `shared_verifier.py`:** Extend the findings format to include `remediation_action`, `remediation_target`, `is_user_action`.

3. **In `scaffold-kickoff/SKILL.md`:** Update the greenfield flow description to specify: "If continuation verification fails with `is_user_action: true`, surface the failure to the user. If `is_user_action: false`, attempt automated remediation before retrying."

### Files to Change

- `skills/scafforge-audit/scripts/shared_verifier.py`
- `skills/scaffold-kickoff/SKILL.md`

---

## Updated Greenfield Proof Chain

After Phase 04, the complete greenfield verification chain becomes:

### Bootstrap-Lane Proof (Step 4)
| Check | Description |
|-------|-------------|
| VERIFY001 | START-HERE.md exists and references active ticket |
| VERIFY002 | Active ticket exists in manifest |
| VERIFY003 | Workflow state references correct stage |
| VERIFY004 | Bootstrap command layout is valid |
| VERIFY005 | Agent skill allowlists reference only existing skills |
| VERIFY006 | Tool definitions reference only existing tool files |
| VERIFY007 | Smoke-test configuration is valid |
| VERIFY008 | Handoff surfaces agree with canonical state |

### Continuation Verification (Step 9)
| Check | Description |
|-------|-------------|
| VERIFY009 | Environment bootstrap reports zero unresolved blockers |
| VERIFY010 | Stack-specific execution audit reports zero CRITICAL findings |
| VERIFY011 | Reference integrity audit reports zero broken structural references |

### Gate Semantics

- **VERIFY001–008 failures** block the greenfield scaffold entirely — these are structural problems in the generated workflow.
- **VERIFY009 failures** indicate missing system dependencies — surface to user for resolution.
- **VERIFY010 failures** indicate the generated code cannot build — the scaffold must fix code before handoff.
- **VERIFY011 failures** indicate broken cross-file references — the scaffold must fix references before handoff.

---

## Summary Checklist

| Fix | Done? |
|-----|-------|
| 04-A: Stack-viability verification (VERIFY009) | |
| 04-B: Build-readiness verification (VERIFY010) | |
| 04-C: Reference-integrity verification (VERIFY011) | |
| 04-D: Actionable remediation guidance | |
| Updated scaffold-kickoff SKILL.md | |
| Integration test for VERIFY009–011 | |
