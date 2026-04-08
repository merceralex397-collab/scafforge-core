# Report 4: Live Repo Repair Plan

- Repo: /home/pc/projects/GPTTalker
- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.

## Safe repair boundary

- Route 8 workflow-layer findings into `scafforge-repair` for deterministic managed-surface repair.

- Refresh generated ticket-update, ticket-lookup, stage-gate, smoke-test, handoff, workflow-doc, and coordinator-prompt surfaces together; these findings indicate a managed workflow-contract defect, not just repo-local operator error.

- Rerun project-local skill regeneration and prompt hardening after the deterministic refresh so the repo-local `ticket-execution` skill and team-leader prompt explain the same state machine the tools enforce.

## Intent-changing boundary

- Escalate any stack, scope, provider, or curated human-decision changes instead of labeling them as safe repair.

## Ticket recommendations

### REMED-001 (error)

- Title: The managed bootstrap tool executed a uv sync command that contradicts the repo's declared dependency layout, so validation tools remain missing after bootstrap
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `BOOT002`
- Summary: Correlate `pyproject.toml`, the latest bootstrap artifact command trace, and `environment_bootstrap.ts`; if the repo layout requires `--extra dev`, `--group dev`, or `--all-extras`, treat any bootstrap run that omits those flags as a managed bootstrap defect and repair the tool before retrying.

### REMED-002 (error)

- Title: The supplied session transcript shows the agent searching for workflow bypasses or soft dependency overrides instead of following the lifecycle contract
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION003`
- Summary: Reject unsupported stages and dependency overrides up front, tell the coordinator not to probe alternate transitions or close blocked tickets anyway, and return the contract contradiction as a blocker when the required proof is missing.

### REMED-003 (error)

- Title: The supplied session transcript shows the agent searching for workflow bypasses or soft dependency overrides instead of following the lifecycle contract
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION003`
- Summary: Reject unsupported stages and dependency overrides up front, tell the coordinator not to probe alternate transitions or close blocked tickets anyway, and return the contract contradiction as a blocker when the required proof is missing.

### REMED-004 (error)

- Title: The supplied session transcript shows the coordinator writing specialist stage artifacts directly instead of routing those outputs through the owning lane or deterministic tool
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION005`
- Summary: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

### REMED-005 (error)

- Title: Derived restart surfaces disagree with canonical workflow state, so resume guidance can route work from stale or contradictory facts
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW010`
- Summary: Regenerate `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` from canonical manifest/workflow state after every workflow save, compute handoff readiness from bootstrap plus repair-follow-on plus verification state in one shared contract, and fail repair verification if any derived restart surface drifts.

### REMED-006 (error)

- Title: The supplied session transcript shows the managed smoke-test override path failing before the requested smoke command starts
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW016`
- Summary: Parse shell-style smoke-test overrides before execution, strip leading `KEY=VALUE` env assignments into the spawn environment, and report malformed overrides as configuration errors rather than environment failures.

### REMED-007 (error)

- Title: The supplied session transcript shows the smoke-test stage running a heuristic command that does not match the ticket's explicit acceptance command
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW017`
- Summary: Treat acceptance-backed smoke commands as canonical, let `smoke_test` infer them automatically, and reject heuristic scope changes unless the caller provides an intentional exact command override.

### REMED-008 (error)

- Title: Generated prompts or restart surfaces still gate workflow decisions on the legacy `handoff_allowed` flag instead of the outcome model
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW021`
- Summary: Keep backward-compatible `handoff_allowed` parsing internal only. Generated prompts, commands, and restart surfaces should route from `repair_follow_on.outcome`, `repair_follow_on_required`, `repair_follow_on_next_stage`, and truthful verification state.

