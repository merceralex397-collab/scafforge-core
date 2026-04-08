# Initial Codebase Review

- **Subject repo:** `/home/pc/projects/GPTTalker`
- **Diagnosis timestamp:** 2026-04-07T21:36:00Z
- **Diagnosis kind:** post_package_revalidation (full-scale package rewrite — all permission gates granted)
- **Audit scope:** Agent markdowns in `.opencode/agents/`, managed workflow surfaces, repair-follow-on state
- **Evidence mode:** current_state + repair-execution trace

## Scope

This diagnosis was triggered after a complete Scafforge package rewrite (30+ commits). The user explicitly stated all permission gates are granted and this is a full-scale overhaul. The focus area identified by the user is the agent markdowns in `.opencode/agents/`.

Surfaces inspected:
- All 21 agent files under `.opencode/agents/`
- Current scaffold template at `/home/pc/.copilot/skills/repo-scaffold-factory/assets/project-template/.opencode/agents/`
- `.opencode/meta/repair-execution.json`
- `.opencode/meta/repair-follow-on-state.json`
- `.opencode/meta/bootstrap-provenance.json`
- `.opencode/state/workflow-state.json`
- `tickets/manifest.json`
- `opencode.jsonc`

## Result State

**validated failures found**

The prior repair cycle (2026-04-07T21:12:10Z, `repair_package_commit: bundle-f70a91576bfbed45`) recorded all follow-on stages — including `opencode-team-bootstrap` and `agent-prompt-engineering` — as `completion_mode: recorded_execution` with `completed_by: *:auto-detected`. None of those stages actually ran their respective skills. Current agent content proves they were never regenerated: multiple agents are missing significant content that exists in the current scaffold template.

## Validated Findings

---

### AGENT-001

- **Summary:** Team leader missing stop conditions, advancement rules, ticket ownership, contradiction resolution, and bootstrap recovery rule blocks
- **Severity:** critical
- **Evidence grade:** observed
- **Affected file:** `.opencode/agents/gpttalker-team-leader.md`
- **What was observed:** The current team leader prompt is missing these entire sections that are present in the current template:
  - "Stop conditions" (6-item block covering when to escalate vs continue)
  - "Advancement rules" (numbered block: check transition_guidance verdict before advancing past review/QA)
  - "Ticket ownership" (per-stage owner map: planner, plan-review, lane-executor, reviewer, QA, smoke-test, closeout)
  - "Contradiction resolution" (explicit tie-breaker rules for manifest vs workflow-state vs board vs START-HERE)
  - `"After running environment_bootstrap, if the response contains blockers..."` rule
  - `"If repeated bootstrap proofs show the same command trace but it still contradicts..."` rule
  - Stack-specific fields in delegation brief ("Stack-specific build, verification, or load-check commands…" and "Stack-specific pitfalls…")
  - `"explore": allow` in task permissions
- **Impact:** Without stop conditions and advancement rules the team leader will not consistently gate on review/QA verdicts or escalate correctly. Without contradiction resolution the leader improvises when surfaces disagree. Without the bootstrap rule block, repeated failed bootstrap won't surface as a managed defect.
- **Remaining verification gap:** None — direct file comparison confirms omissions.

---

### AGENT-002

- **Summary:** `gpttalker-reviewer-code.md` missing `review-audit-bridge` skill, compile-check bash allowlist, and execution-proof rules
- **Severity:** critical
- **Evidence grade:** observed
- **Affected file:** `.opencode/agents/gpttalker-reviewer-code.md`
- **What was observed:**
  - `"review-audit-bridge": allow` missing from skill permissions block
  - Compile/syntax-check bash commands missing: `python -m py_compile*`, `python -c *`, `python3 -m py_compile*`, `python3 -c *`, `node -e *`, `cargo check*`, `go vet*`, `tsc --noEmit*`
  - Template body says "Use `review-audit-bridge` for output ordering and blocker rules" — missing in repo
  - Template rules block includes "verify that new or modified source files compile…", "verify that the primary module imports succeed", "include compile or import-check output in the review artifact", "do not approve code that fails to compile or import cleanly" — all missing
  - Missing `"if artifact creation is blocked because the ticket lease is missing…"` rule
- **Impact:** Reviewer-code can approve code without running any compile or import check. Review artifacts can pass without execution evidence. Downstream QA and smoke-test will receive unvalidated code.
- **Remaining verification gap:** None.

---

### AGENT-003

- **Summary:** `gpttalker-reviewer-security.md` missing `review-audit-bridge` skill and lease-blocked return rule
- **Severity:** major
- **Evidence grade:** observed
- **Affected file:** `.opencode/agents/gpttalker-reviewer-security.md`
- **What was observed:**
  - `"review-audit-bridge": allow` missing from skill permissions
  - Template body: "Use `review-audit-bridge` for output ordering and blocker rules" — missing
  - Missing `"if artifact creation is blocked because the ticket lease is missing, return that blocker..."` rule
- **Remaining verification gap:** None.

---

### AGENT-004

- **Summary:** `gpttalker-tester-qa.md` missing `review-audit-bridge` skill and lease-blocked return rule
- **Severity:** major
- **Evidence grade:** observed
- **Affected file:** `.opencode/agents/gpttalker-tester-qa.md`
- **What was observed:**
  - `"review-audit-bridge": allow` missing from skill permissions
  - Template QA body: "Use `review-audit-bridge` for QA output ordering and blocker rules, then report:" — repo says "Run the minimum meaningful validation…and report:"
  - Missing `"if artifact creation is blocked because the ticket lease is missing, return that blocker..."` rule
- **Remaining verification gap:** None.

---

### AGENT-005

- **Summary:** `gpttalker-ticket-creator.md` is the old narrow version — missing `ticket_reconcile` permission and reconciliation handling
- **Severity:** major
- **Evidence grade:** observed
- **Affected file:** `.opencode/agents/gpttalker-ticket-creator.md`
- **What was observed:**
  - Template description: "Hidden guarded ticket router for evidence-backed follow-up creation **and lineage reconciliation**" — repo has older "…for migration follow-up work proven by backlog verification"
  - `ticket_reconcile: allow` missing from permissions block
  - Template body: "Create or reconcile ticket lineage only from current accepted evidence" — repo: "Create a follow-up ticket only from an accepted backlog-verifier finding"
  - Template rules include `ticket_reconcile` invocation rules, delegation brief field requirements for reconciliation, error handling for both `ticket_create` and `ticket_reconcile` — all absent in repo
- **Impact:** Ticket creator cannot reconcile stale lineage. WFLOW019/WFLOW024 paths are broken at the agent level.
- **Remaining verification gap:** None.

---

### AGENT-006

- **Summary:** `gpttalker-planner.md` missing `"explore": allow` in task permissions
- **Severity:** minor
- **Evidence grade:** observed
- **Affected file:** `.opencode/agents/gpttalker-planner.md`
- **What was observed:** Template planner task block includes `"explore": allow`. Repo planner does not.
- **Remaining verification gap:** None.

---

### AGENT-007

- **Summary:** `gpttalker-plan-review.md` missing lease-blocked return rule
- **Severity:** minor
- **Evidence grade:** observed
- **Affected file:** `.opencode/agents/gpttalker-plan-review.md`
- **What was observed:** Template includes `"if artifact creation is blocked because the ticket lease is missing, return that blocker to the team leader instead of trying to claim a lease yourself"`. Repo version omits this.
- **Remaining verification gap:** None.

---

### AGENT-008

- **Summary:** `gpttalker-backlog-verifier.md` missing smoke-test artifact check and lease-blocked return rule
- **Severity:** minor
- **Evidence grade:** observed
- **Affected file:** `.opencode/agents/gpttalker-backlog-verifier.md`
- **What was observed:**
  - Repo body: "read the latest planning, implementation, review, and QA artifact bodies" — template adds "and smoke-test"
  - Missing `"if artifact creation is blocked because the ticket lease is missing..."` rule
- **Remaining verification gap:** None.

---

### STATE-001

- **Summary:** Prior repair cycle auto-detected completion of `opencode-team-bootstrap` and `agent-prompt-engineering` without actually executing them
- **Severity:** critical
- **Evidence grade:** observed
- **Affected file:** `.opencode/meta/repair-execution.json`, `.opencode/meta/repair-follow-on-state.json`
- **What was observed:** The repair cycle `2026-04-07T21:12:10Z` shows `completion_mode: recorded_execution` with `completed_by: "opencode-team-bootstrap:auto-detected"` and `"agent-prompt-engineering:auto-detected"`. These are auto-detected completions, not real skill executions. Current agent file content is direct proof those stages were never actually run. The agents remained on the older contract.
- **Remaining verification gap:** None — agent content mismatch is the proof.

---

### REF-003 (script finding — DOWNGRADED)

- **Summary:** Audit script flagged missing `.js` imports in `.opencode/node_modules/zod/src/`
- **Severity:** advisory only (not actionable)
- **Evidence grade:** observed
- **Affected file:** `.opencode/node_modules/zod/src/index.ts`
- **What was observed:** The script scanned zod's TypeScript source files inside `node_modules` and flagged that compiled `.js` outputs referenced by those `.ts` source files don't exist in the same source directory. This is expected — zod's `.ts` source files reference compiled outputs that live in the `dist/` tree, not inside `src/`. These are not project imports and are not broken at runtime.
- **Disposition:** **Rejected as false positive.** The audit script should exclude `node_modules` from local-import resolution checks.

## Verification Gaps

None for AGENT-001 through AGENT-008. All findings are direct file-comparison observations. The REF-003 false positive has been rejected.
