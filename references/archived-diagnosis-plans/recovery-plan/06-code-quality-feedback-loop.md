# Phase 06: Code Quality Feedback Loop

**Priority:** P1 — High
**Depends on:** Phase 03 (audit execution depth), Phase 01 (verdict-aware transitions)
**Goal:** Create a closed loop where code quality issues are detected, ticketed, fixed, and verified

---

## Problem Statement

Scafforge currently has no mechanism to ensure generated or agent-written code actually works. The workflow verifies that workflow surfaces are correct (files exist, manifests agree, truth hierarchy is coherent) but never asks "does the code compile?" or "do the tests pass?" or "are internal references valid?"

This creates the core failure: agents claim completion, but the product does NOT work. The missing piece is a feedback loop:

```
Write Code → Check Quality → Find Issues → Create Fix Tickets → Fix Code → Re-Check → Pass
```

None of these connections currently exist in the generated workflow.

---

## Fix 06-A: Define the Code Quality Gate in Ticket Lifecycle

### How It Fits

The current ticket lifecycle is:

```
implementation → review → qa → smoke-test → closeout
```

Code quality checking should happen at two points:

1. **During review stage:** The reviewer should run stack-specific checks (build, lint, reference integrity) as part of the review. If any check fails, the review verdict is FAIL.

2. **During smoke-test stage:** The smoke test should include a build verification command. If the build fails, the smoke test fails.

The code quality gate is NOT a new stage. It is an enrichment of existing stages with actual quality evidence.

### Required Changes

1. **In the generated `review-audit-bridge` skill** (or equivalent review skill): Add instructions for the reviewer to:
   - Run the project's build command and include the result in the review artifact
   - Run the project's lint command (if any) and include the result
   - Check reference integrity for configuration → code references
   - Mark the review as FAIL if any of these checks fail, with specific error details

2. **In the generated `stack-standards` skill:** Add stack-specific quality commands that the reviewer and QA agents should use:
   - Python: `ruff check .`, `mypy .` (if configured), `pytest --collect-only`
   - Node.js: `npm run lint`, `tsc --noEmit`, `npm test`
   - Rust: `cargo clippy`, `cargo test`
   - Go: `go vet ./...`, `golangci-lint run`
   - Godot: scene reference check, autoload validation, `godot --headless --check-only` (if available)
   - C/C++: `cmake --build .`, compiler warning check
   - .NET: `dotnet build`, `dotnet test`
   - Generic: `make check` or `make test`

3. **In `smoke_test.ts`:** The smoke test tool should already handle build commands (Phase 02-E adds patterns). Ensure that a build failure during smoke test produces a clear FAIL artifact with the build error output, not just a generic "test_failure."

### Files to Change

- `skills/project-skill-bootstrap/SKILL.md` — add guidance for generating review/QA skills with code quality checks
- `skills/repo-scaffold-factory/assets/project-template/.opencode/skills/stack-standards/SKILL.md` — add quality command catalog
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts` — ensure build failure classification

---

## Fix 06-B: Generate Remediation Tickets from Audit Findings

### Problem

When `scafforge-audit` finds code quality issues (after Phase 03), there is no automatic path from "finding identified" to "ticket created for the fix." The diagnosis pack is a report, not an action.

### Required Changes

1. **In `audit_reporting.py`:** The `build_ticket_recommendations()` function already generates ticket recommendations. After Phase 03, it will also include EXEC and REF findings. Ensure that:
   - Each CRITICAL finding generates a specific remediation ticket recommendation
   - The ticket recommendation includes: title, description, affected files, suggested fix approach, assignee (implementer)
   - HIGH findings are grouped into batch remediation tickets (one per area, not one per finding)

2. **In `scafforge-repair/SKILL.md`:** When scafforge-repair runs after an audit that found code quality issues, it should:
   - Create the recommended remediation tickets in the subject repo's ticket system
   - Set them as blocked-by the current active ticket (if any) or add them to the backlog
   - NOT attempt to fix the code itself (repair only handles workflow surfaces)

3. **In `ticket-pack-builder/SKILL.md`:** Add a "remediation mode" that accepts a list of audit findings and converts them into properly formatted tickets. This is distinct from "bootstrap mode" (initial backlog) and "refine mode" (backlog expansion).

### Files to Change

- `skills/scafforge-audit/scripts/audit_reporting.py`
- `skills/scafforge-repair/SKILL.md`
- `skills/ticket-pack-builder/SKILL.md`

---

## Fix 06-C: Post-Fix Re-Verification

### Problem

After a remediation ticket is implemented, there's no mechanism to re-run the quality checks that originally found the issue. The fix is merged, the ticket is closed, but nobody checks if the fix actually resolved the finding.

### Required Changes

1. **In the generated `ticket-execution` skill:** Add re-verification instructions for remediation tickets:
   ```
   ## Remediation Ticket Closeout
   
   When closing a ticket that was created from an audit finding:
   1. Identify the original finding code (e.g., EXEC-GODOT-001)
   2. Re-run the specific check that produced the finding
   3. If the check now passes, include the pass result in the closeout artifact
   4. If the check still fails, the ticket cannot be closed — route back to implementation
   ```

2. **In the generated `review-audit-bridge` skill** (or review skill): When reviewing a fix for a remediation ticket, the reviewer should specifically:
   - Re-run the original check command
   - Verify the specific error from the finding is gone
   - Check for regressions (other checks that previously passed should still pass)

3. **Tag remediation tickets** with their original finding code so the re-verification step can automatically identify which check to re-run. Add a `finding_source` field to the ticket metadata in `tickets/manifest.json`.

### Files to Change

- `skills/project-skill-bootstrap/SKILL.md` — guidance for generating ticket-execution skill with re-verification
- `skills/repo-scaffold-factory/assets/project-template/.opencode/skills/ticket-execution/SKILL.md` — add remediation closeout section
- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts` — add `finding_source` to ticket manifest schema

---

## Fix 06-D: Quality Dashboard in Restart Surface

### Problem

START-HERE.md shows ticket status but does not show code quality status. An agent resuming a session has no idea whether the project currently builds, whether tests pass, or whether there are known quality issues.

### Required Changes

1. **In `handoff_publish.ts`:** When generating START-HERE.md, add a `## Code Quality Status` section that includes:
   - Last build result (pass/fail + timestamp)
   - Last test run result (pass/fail + timestamp)
   - Number of open remediation tickets
   - Number of known reference-integrity issues

2. **The data source for this section:** Read from `.opencode/state/artifacts/` for the latest smoke-test, build, and audit results.

3. **Keep it simple:** This is a snapshot, not a live dashboard. It reflects the state at time of handoff publication.

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts`

---

## The Complete Loop

After Phases 01, 03, and 06, the code quality feedback loop is:

```
1. Agent writes code (implementation stage)
2. Reviewer runs quality checks (review stage, Fix 06-A)
   → If FAIL: route back to implementation (Phase 01-A verdict-aware)
3. QA runs quality checks (QA stage, Fix 06-A)
   → If FAIL: route back to implementation (Phase 01-A verdict-aware)
4. Smoke test runs build + test (smoke-test stage, Phase 02-E)
   → If FAIL: route to fail-state recovery (Phase 01-F)
5. Audit finds residual issues (diagnosis flow, Phase 03)
   → Generates remediation tickets (Fix 06-B)
6. Remediation tickets are implemented with re-verification (Fix 06-C)
7. Restart surface shows current quality status (Fix 06-D)
```

---

## Summary Checklist

| Fix | Done? |
|-----|-------|
| 06-A: Code quality in review and QA stages | |
| 06-A: Stack-specific quality commands in stack-standards | |
| 06-B: Remediation ticket generation from audit findings | |
| 06-B: Remediation mode in ticket-pack-builder | |
| 06-C: Post-fix re-verification in ticket execution | |
| 06-C: Finding source tagging in ticket manifest | |
| 06-D: Quality dashboard in restart surface | |
