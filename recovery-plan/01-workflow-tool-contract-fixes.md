# Phase 01: Workflow Tool Contract Fixes

**Priority:** P0 — Critical
**Goal:** Stop agents from hitting workflow blockers caused by contradictory tool logic

---

## Problem Statement

Agents in generated repos get stuck because workflow tools contain logical contradictions:
- Transition guidance recommends advancing after FAIL verdicts
- Smoke-test tool drops quote characters from shell commands
- Active-ticket lookup returns split-brain results
- Handoff tools return only paths with no verification metadata
- Verification state is semantically meaningless until closeout

These are not edge cases. The Glitch transcript shows 27 agent confusion events and 500+ lines of circular reasoning caused by these exact issues.

---

## Fix 01-A: Make Transition Guidance Verdict-Aware

### Evidence

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts`
**Problem:** The `transition_guidance` object checks whether a review or QA artifact _exists_ but does not check whether the artifact contains a PASS or FAIL verdict.
**Proof from glitchresearch.md Issue 5:** After review found FAIL with blockers for duplicate autoloads, transition_guidance still showed `next_allowed_stages: ["qa"]` because the system detected a review artifact existed.

### Required Changes

1. **In `ticket_lookup.ts`:** Locate the review-stage transition guidance logic (the section that checks for review artifacts before recommending advancement to QA). Add verdict extraction from the latest review artifact body. If the artifact body contains a FAIL, REJECT, or BLOCKER verdict:
   - Set `recommended_action` to `"Review found blockers. Route back to implementation to address the review findings before advancing."`
   - Set `next_allowed_stages` to `["implementation"]` instead of `["qa"]`
   - Add a `review_verdict` field to the guidance output showing the extracted verdict

2. **In `ticket_lookup.ts`:** Apply the same verdict-awareness to QA-stage guidance. If the latest QA artifact body contains FAIL:
   - Set `recommended_action` to `"QA found issues. Route back to implementation to fix the QA findings."`
   - Set `next_allowed_stages` to `["implementation"]` instead of `["smoke-test"]`
   - Add a `qa_verdict` field to the guidance output

3. **Verdict extraction approach:** Scan the latest artifact body for these patterns:
   - Lines starting with `Overall:`, `Verdict:`, or `Result:` followed by PASS, FAIL, REJECT, APPROVED, BLOCKED
   - Lines containing `❌` followed by FAIL or BLOCKER
   - Lines containing `✅` followed by PASS or APPROVED
   - If no clear verdict pattern is found, flag the artifact as `verdict_unclear` and add a warning to guidance: `"Review artifact exists but verdict could not be extracted. Inspect the artifact manually before advancing."`

4. **In `ticket_update.ts`:** Add a validation check in the review→qa and qa→smoke-test transitions. Before allowing the transition, load the latest review/QA artifact and check for FAIL verdict. If FAIL is found, reject the transition with a clear error: `"Cannot advance past review/qa — latest artifact shows FAIL verdict. Route back to implementation."`

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_update.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts` (add `extractArtifactVerdict()` utility)

### Verification

- Write or extend a smoke test in `scripts/smoke_test_scafforge.py` that creates a ticket with a FAIL review artifact and confirms transition_guidance blocks forward motion.
- Write or extend an integration test that confirms `ticket_update` rejects the review→qa transition when the review artifact contains FAIL.

---

## Fix 01-B: Fix Smoke-Test Quote Tokenization Bug

### Evidence

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts`
**Problem:** `tokenizeCommandString()` detects quote characters but discards them instead of preserving them in the output tokens. This means:
- Input: `grep -E '(PlayerState|GlitchState).*Initialized'`
- Tokenizer sees opening `'`, enters quoted mode, but does not add `'` to the token
- Tokenizer sees closing `'`, exits quoted mode, but does not add `'` to the token
- Result: `grep -E (PlayerState|GlitchState).*Initialized` — shell interprets `(` as subshell
- Error: `"Missing language argument, aborting"`

**Proof from glitchresearch.md Issue 3:** Lines 4716-4761 show the smoke test failing with exit code 1, misclassified as "environment failure" instead of "syntax error."

### Required Changes

1. **In `smoke_test.ts`:** Locate `tokenizeCommandString()` (or its equivalent — the function that splits a single command string into argv tokens). Fix the quote handling:
   - When the tokenizer encounters a quote character (`'` or `"`) at the START of a token or when not currently in a quoted context, it should preserve the quote in the output token
   - When the tokenizer encounters the matching closing quote, it should also preserve it
   - Alternative approach: since the purpose is to create argv for `spawn()`, quotes should be CONSUMED (not passed through) but the content between them should be kept as a single token WITHOUT shell expansion. This is the standard behavior of shell-style tokenization for `spawn()`.

2. **Fix the actual tokenization logic:** The correct approach for spawn-style argv tokenization is:
   - When encountering an opening quote, set a quote context flag but do NOT add the quote to the token
   - While in quote context, add all characters to the current token (including spaces)
   - When encountering the closing quote, clear the quote context but do NOT add the quote to the token
   - The result should be: `grep -E '(PlayerState|GlitchState).*Initialized'` → `["grep", "-E", "(PlayerState|GlitchState).*Initialized"]`
   - If the current code IS doing this, the bug may be elsewhere — in how the argv is reassembled for display or how `spawn()` receives it

3. **Improve failure classification:** In addition to the quote fix, classify smoke-test failures more precisely:
   - `"syntax_error"` — when the error output contains "syntax error", "unexpected token", "missing language argument", or command-not-found for what should be an argument
   - `"missing_executable"` — when the error is ENOENT for the first token
   - `"test_failure"` — when the command ran but returned non-zero with test output
   - `"permission_restriction"` — when EACCES/EPERM
   - `"configuration_error"` — when the command ran but the output indicates a misconfiguration
   - `"command_error"` — fallback for all other non-zero exits

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts` — `tokenizeCommandString()` and `CommandResult.failure_classification`

### Verification

- Add a test in `scripts/smoke_test_scafforge.py` that creates a smoke command with single-quoted grep patterns and verifies the tokenizer produces correct argv.
- Add a test that confirms `failure_classification` is `"syntax_error"` when a quote-dependent command fails with a shell-interpretation error.

---

## Fix 01-C: Eliminate Active-Ticket Split-Brain

### Evidence

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts`
**Problem:** When a ticket_id is specified, `ticket_lookup` can return divergent `active_ticket` values — the root-level field shows the manifest's active ticket, but the `workflow` section shows whichever ticket was looked up. This causes weaker models to see two different "current" tickets depending on which field they read.

**Proof from glitchresearch.md Issue 7:** Root-level `active_ticket: "SETUP-001"` vs `workflow.active_ticket: "SYSTEM-001"` appeared simultaneously in lookup output.

### Required Changes

1. **In `ticket_lookup.ts`:** When the tool receives a specific `ticket_id` argument, still return the CANONICAL active ticket from the manifest in the `active_ticket` root field. Add a separate `requested_ticket` field for the looked-up ticket data. Never override the root `active_ticket` with the requested ticket ID.

2. **Add an explicit `is_active` boolean** to the ticket response so agents can immediately see whether the requested ticket IS the active one without comparing IDs.

3. **Remove any logic** that temporarily rewrites `workflow.active_ticket` in the response based on the requested ticket. The workflow section should always reflect the canonical workflow state.

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts`

### Verification

- Add a test that requests ticket_lookup for a non-active ticket and confirms the root `active_ticket` still matches the manifest.
- Add a test that confirms the `is_active` field is `false` for non-active tickets and `true` for the active ticket.

---

## Fix 01-D: Add Verification Metadata to Handoff and Context Tools

### Evidence

**Files:**
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/context_snapshot.ts`

**Problem:** Both tools return only file paths in their response. Agents cannot confirm whether the files were actually written, what their content hash is, or whether they agree with canonical state.

**Proof from glitchresearch.md Issue 6:** Handoff tool returns `{ start_here: "path", latest_handoff: "path" }` with no verification that the surfaces agree with manifest/workflow state.

### Required Changes

1. **In `handoff_publish.ts`:** After writing restart surfaces, add to the response:
   - `verified: true/false` — whether the written surfaces agree with `tickets/manifest.json` and `.opencode/state/workflow-state.json`
   - `active_ticket` — the active ticket ID at time of publication
   - `bootstrap_status` — current bootstrap status
   - `pending_process_verification` — whether process verification is pending

2. **In `context_snapshot.ts`:** After writing the snapshot, add to the response:
   - `verified: true/false`
   - `snapshot_size_bytes` — size of written snapshot
   - `active_ticket` — ticket context of the snapshot

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/context_snapshot.ts`

### Verification

- Extend existing template tool tests to check for the presence of verification metadata in tool output.

---

## Fix 01-E: Give `verification_state` Real Semantics

### Evidence

**File:** `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
**Problem:** `verification_state` stays `"suspect"` for the entire ticket lifecycle regardless of review, QA, and smoke-test results. It only becomes `"trusted"` at closeout. This makes the field a synonym for `"not closed"` rather than an actual indicator of verification quality.

**Proof from glitchresearch.md Issue 4:** Lines 832-5380 show verification_state remaining "suspect" through all stages despite passing reviews, QA, and smoke tests.

### Required Changes

1. **In `workflow.ts` or `ticket_update.ts`:** Add transitions for `verification_state`:
   - After a PASS smoke-test artifact is registered: set `verification_state` to `"smoke_verified"`
   - After closeout: set to `"trusted"`
   - After reopen or supersede: set to `"suspect"`
   - After reverify with current proof: set to `"reverified"`
   - After process-version change with `pending_process_verification`: set to `"suspect"`

2. **Add `"smoke_verified"` to the allowed `TicketVerificationState` union** in `workflow.ts`. Current allowed values appear to be `"suspect"`, `"trusted"`, `"reverified"`, `"invalidated"`. Add `"smoke_verified"` as an intermediate state.

3. **Update `ticket-execution/SKILL.md` template** to document the verification state transitions so agents understand what each state means.

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_update.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/skills/ticket-execution/SKILL.md`

### Verification

- Add tests that confirm `verification_state` transitions correctly through the lifecycle.
- Confirm that `ticket_lookup.transition_guidance` uses the verification state in its recommendations.

---

## Fix 01-F: Define Explicit Fail-State Routing

### Evidence

**Problem:** When review or QA returns FAIL, there is no explicit, documented path for remediation. The workflow tools and docs describe the happy path thoroughly but leave the failure path ambiguous. Glitch's agent spent 500+ lines trying to reconcile a QA FAIL with guidance that said "advance to smoke-test."

### Required Changes

1. **In `ticket-execution/SKILL.md` template:** Add a `## Failure Recovery Paths` section:
   - **Review FAIL:** Route back to `implementation` stage. Implementer must address the specific review findings. Then re-route to `review`.
   - **QA FAIL:** Route back to `implementation` stage. Implementer must address QA findings. Then re-route through `review` → `qa`.
   - **Smoke-test FAIL (test failure):** Inspect the failure output. If it's a code issue, route back to `implementation`. If it's an environment issue, route to `environment_bootstrap`.
   - **Smoke-test FAIL (tool error):** If the smoke_test tool itself malfunctioned (syntax_error, configuration_error), flag as a workflow blocker and do NOT route to implementation.
   - **Bootstrap FAIL:** Classify the failure (missing executable, permission restriction, command error). If missing executable, surface as environment blocker.

2. **In `ticket_lookup.ts`:** When a ticket's latest stage artifact shows FAIL, set `transition_guidance.recovery_action` describing the fail-state path explicitly.

3. **In the team-leader template:** Add explicit instructions: "When `ticket_lookup.transition_guidance` contains `recovery_action`, follow that path instead of the normal advancement path."

### Files to Change

- `skills/repo-scaffold-factory/assets/project-template/.opencode/skills/ticket-execution/SKILL.md`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md`

### Verification

- Create an integration test that advances a ticket to review, writes a FAIL review artifact, then confirms transition_guidance contains `recovery_action` pointing to implementation.

---

## Audit Coverage for Phase 01

After implementing these fixes, add the following audit checks to detect regressions:

1. **In `audit_lifecycle_contracts.py` or `audit_contract_surfaces.py`:** Check that `ticket_lookup.ts` contains verdict extraction logic (search for "extractArtifactVerdict" or equivalent).
2. **In `audit_restart_surfaces.py`:** Check that `handoff_publish.ts` returns verification metadata (search for "verified" in the response shape).
3. **In `audit_contract_surfaces.py`:** Check that `ticket-execution/SKILL.md` contains a "Failure Recovery Paths" section.
4. **In `audit_execution_surfaces.py`:** Check that `smoke_test.ts` does not contain the quote-dropping bug pattern.

---

## Summary Checklist

| Fix | Done? |
|-----|-------|
| 01-A: Verdict-aware transition guidance | |
| 01-B: Smoke-test quote tokenization | |
| 01-C: Active-ticket split-brain elimination | |
| 01-D: Handoff/context verification metadata | |
| 01-E: Verification state real semantics | |
| 01-F: Explicit fail-state routing | |
| Audit regression coverage | |
| Test coverage | |
