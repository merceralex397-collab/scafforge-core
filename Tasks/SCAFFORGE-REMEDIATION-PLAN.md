# Scafforge Remediation Plan to Prevent GPTTalker-Class Failures

## Summary
I verified the scaffold generator directly in [Scafforge/README.md](../README.md), [Scafforge/AGENTS.md](../AGENTS.md), [Scafforge/skills/skill-flow-manifest.json](../skills/skill-flow-manifest.json), [bootstrap_repo_scaffold.py](../skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py), [project-template/opencode.jsonc](../skills/repo-scaffold-factory/assets/project-template/opencode.jsonc), [project-template/_workflow.ts](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts), [stage-gate-enforcer.ts](../skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts), [apply_repo_process_repair.py](../skills/repo-process-doctor/scripts/apply_repo_process_repair.py), and [validate_scafforge_contract.py](../scripts/validate_scafforge_contract.py).

The core finding is that Scafforge successfully generates a strong-looking workflow shell, but it still leaves several failure paths open: placeholder scaffold content can survive into generated repos, important integrations are disabled by default, validator coverage is shallow, and the workflow is still vulnerable to “artifact exists therefore pass” behavior unless runtime proof is enforced everywhere. GPTTalker appears to be a direct example of those weaknesses.

## Complete Findings
### 1. Scafforge generates the right structure, but structure is treated as stronger proof than execution
- The generator clearly intends a deterministic OpenCode repo with truth hierarchy, state, agents, tools, plugins, skills, tickets, and restart surfaces.
- That structure is real in both template and output, but GPTTalker shows that generated process surfaces can still drift into false completion while preserving the appearance of rigor.
- Evidence: [Scafforge/README.md](../README.md), `../../GPTTalker/.opencode/state/workflow-state.json`, `../../GPTTalker/.opencode/state/artifacts/registry.json`

### 2. The template still ships disabled integrations as the default operating state
- The template `opencode.jsonc` disables `browser_research`, `project_github`, and `openai_docs`.
- That makes the generated repo more isolated than its docs and workflow language suggest, and it encourages users to assume capabilities that are present in config but not active.
- Evidence: [project-template/opencode.jsonc](../skills/repo-scaffold-factory/assets/project-template/opencode.jsonc), `../../GPTTalker/opencode.jsonc`

### 3. Placeholder scaffold content is allowed to survive into “completed” repos
- The template `stack-standards` skill literally says “Replace this file with stack-specific rules once the real project stack is known.”
- GPTTalker retained that kind of scaffold residue, which means the scaffold and repair path do not guarantee replacement of generic placeholder content before a repo can be treated as complete.
- Evidence: [stack-standards template](../skills/repo-scaffold-factory/assets/project-template/.opencode/skills/stack-standards/SKILL.md), `../../GPTTalker/.opencode/skills/stack-standards/SKILL.md`

### 4. Validator coverage is mostly shape/content-string based, not behavior based
- `validate_scafforge_contract.py` checks required files and required text fragments.
- It does not verify that the generated repo’s workflow actually blocks bad progress, that artifact validators reject weak proofs, that placeholders were eliminated, that integrations were intentionally configured, or that restart surfaces reflect actual runtime truth.
- This is one of the biggest generator-level gaps.
- Evidence: [validate_scafforge_contract.py](../scripts/validate_scafforge_contract.py)

### 5. Process doctor repairs deterministic surfaces, but not semantic correctness
- `apply_repo_process_repair.py` can replace managed files and update provenance/state, but it mostly repairs surface conformance.
- It does not appear to prove that the generated repo’s product implementation works, nor that repair outputs remove stale claims from docs/handoff surfaces beyond the managed block.
- Evidence: [apply_repo_process_repair.py](../skills/repo-process-doctor/scripts/apply_repo_process_repair.py)

### 6. Scafforge already documents many lessons from GPTTalker, but enforcement is incomplete
- `Tasks/recommendations.md` explicitly calls out the need for execution evidence, stronger reviewer/QA behavior, smoke-test hardening, and cross-agent trust rules.
- The important issue is that these are recorded as recommendations, not universally guaranteed invariants across generation, repair, and validation.
- Evidence: [Tasks/recommendations.md](./recommendations.md)

### 7. Stage-gate enforcement is real, but only as good as artifact validators and workflow truth
- The template stage gate blocks status changes without artifacts and plan approval.
- That is necessary, but GPTTalker demonstrates that weak artifacts, stale state, and inconsistent registry entries can still let the process tell a misleading story.
- Evidence: [stage-gate-enforcer.ts](../skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts), [project-template/_workflow.ts](../skills/repo-scaffold-factory/assets/project-template/.opencode/tools/_workflow.ts), `../../GPTTalker/.opencode/state/plans/fix-017-planning-plan.md`

### 8. GPTTalker shows artifact-stage truth was not reliably enforced in practice
- Artifact timestamps and registry ordering drifted.
- Some QA artifacts were inspection-only.
- Smoke-test artifacts could record `compileall` success while `pytest` failed.
- Some review/backlog-verification artifacts were extremely thin.
- Evidence: `../../GPTTalker/.opencode/state/artifacts/registry.json`, `../../GPTTalker/.opencode/state/qa/fix-013-qa-qa.md`, `../../GPTTalker/.opencode/state/smoke-tests/fix-015-smoke-test-smoke-test.md`, `../../GPTTalker/.opencode/state/reviews/core-001-review-backlog-verification.md`

### 9. Restart and docs surfaces can overclaim completion
- GPTTalker’s docs are internally coherent, but `START-HERE.md` and related docs overstated completion and left placeholders around validation/risk state.
- Scafforge currently does not appear to have a hard “truth regeneration” step that cross-checks restart/docs claims against test reality before marking work complete.
- Evidence: `../../GPTTalker/START-HERE.md`, `../../GPTTalker/docs/process/workflow.md`

### 10. Generated repos can retain duplicated or ambiguous authority surfaces
- GPTTalker’s `workflow-observability` skill and nested `agents/openai.yaml` duplicate part of the skill authority surface.
- This is a smaller issue, but it is another sign that scaffold synthesis and repair do not aggressively prune redundant sources of truth.
- Evidence: `../../GPTTalker/.opencode/skills/workflow-observability/SKILL.md`, `../../GPTTalker/.opencode/skills/workflow-observability/agents/openai.yaml`

## Step-by-Step Remediation for Scafforge
### Step 1. Make generated repos fail closed on unresolved scaffold placeholders
- Add a generator-level placeholder inventory and mark certain files as “must specialize before completion.”
- Extend the validator to fail if any generated repo still contains scaffold markers like “replace this file,” unresolved stack labels, template placeholders, or generic TODO language in managed workflow/skill surfaces.
- Add a dedicated “scaffold hygiene” audit in `repo-process-doctor` and require it before handoff.

### Step 2. Separate “disabled by default” from “available and ready”
- Change the template so disabled MCP integrations are explicitly labeled as inactive scaffolding, not implied capabilities.
- Require the handoff and docs surfaces to state which integrations are active, inactive, or intentionally omitted.
- Add a validator rule that rejects language implying availability when the corresponding integration remains disabled.

### Step 3. Promote executable proof from recommendation to invariant
- Keep the current artifact evidence checks in `_workflow.ts`, but extend them to all relevant stages and make them stricter.
- Require implementation, review, QA, and smoke-test artifacts to include command output, exit status, and a machine-parseable result field.
- Reject inspection-only QA/review artifacts when execution was feasible.
- Add minimum evidence schema requirements instead of only regex-based content heuristics.

### Step 4. Introduce structured artifact schemas, not free-form markdown only
- Define a canonical frontmatter or JSON sidecar for every artifact type with required fields such as `commands_run`, `exit_codes`, `result`, `environment_notes`, and `blockers`.
- Keep the human-readable markdown body, but make the stage gate consume the structured fields first.
- Update artifact tools so registration fails if the schema is incomplete or contradicts the body.

### Step 5. Add deterministic repo-level self-tests for scaffold behavior
- Add Scafforge integration tests that generate temporary repos and verify:
  - stage-gate enforcement blocks advancement without required evidence
  - placeholder scaffold content is rejected
  - repair flow updates provenance and marks pending verification
  - restart surfaces regenerate from canonical state rather than stale narrative text
  - disabled integrations are surfaced honestly in generated docs
- This must run in Scafforge CI, not just as manual spot checks.

### Step 6. Strengthen the validator from static linter into contract verifier
- Expand `validate_scafforge_contract.py` or replace it with a test harness that does both static and dynamic checks.
- Validate generated repo behavior by creating a temporary repo from template and exercising `ticket_update`, artifact registration, stage gating, and smoke-test gating.
- Treat behavior regressions as release blockers for Scafforge.

### Step 7. Make restart and handoff surfaces derived-only
- Prevent `START-HERE.md` from carrying unconstrained free-form completion claims in managed sections.
- Regenerate its status, active ticket, validation summary, and known-risks block strictly from `workflow-state.json`, ticket state, artifact registry, and smoke-test outcomes.
- Add a validator rule that flags placeholders or unsupported “all tickets completed” style claims.

### Step 8. Harden registry integrity and ordering rules
- Add uniqueness rules for artifact registry entries by `ticket_id + stage + kind + path`.
- Add monotonic stage progression validation and reject impossible orderings unless explicitly marked as migration repairs.
- Add a repair-mode audit that reports registry anomalies rather than silently normalizing them.

### Step 9. Reduce duplicate authority surfaces
- Define one canonical source for each skill/agent metadata surface.
- If nested config like `agents/openai.yaml` is generated, document whether it is derived or authoritative and validate consistency automatically.
- Add duplicate-authority checks to the process doctor.

### Step 10. Turn GPTTalker lessons into release-gated Scafforge policy
- Convert the recommendations from [Tasks/recommendations.md](./recommendations.md) into concrete template rules, validator assertions, and generated test cases.
- Do not allow “lessons learned” to remain as advisory prose after they have been proven by a real failure case.

## Public Interface / Contract Changes
- Artifact contract: add structured required metadata for each stage artifact.
- Handoff contract: `START-HERE.md` managed section becomes derived-only from canonical state and registered proof.
- Validation contract: Scafforge release validation must include dynamic generated-repo tests, not just file presence/text checks.
- Integration contract: generated repos must explicitly classify each MCP integration as active, inactive, or unconfigured.

## Test Plan
- Generate a fresh temp repo from Scafforge and run a scaffold contract suite.
- Verify placeholder detection fails the build if generic scaffold text survives in required surfaces.
- Verify stage transitions fail without approved plans, missing artifacts, missing execution evidence, or failing smoke tests.
- Verify repair flow sets `pending_process_verification` and preserves project-specific sources while replacing managed surfaces.
- Verify `START-HERE.md` and related docs cannot claim completion when smoke tests or required artifacts are missing or failing.
- Verify disabled MCP integrations are reflected accurately in generated docs and handoff text.
- Add a regression fixture based on the GPTTalker failure pattern so future Scafforge releases are tested against the exact class of drift that occurred here.

## Assumptions and Defaults
- The goal is prevention at the scaffold-generator level, not just cleanup in one generated repo.
- GPTTalker is treated as a representative failure case for Scafforge’s current contract, not as a one-off user misuse.
- The preferred fix is stronger generation/validation/repair guarantees, not more prose guidance.
- If there is a tradeoff between generator flexibility and fail-closed workflow truth, Scafforge should choose fail-closed by default.

