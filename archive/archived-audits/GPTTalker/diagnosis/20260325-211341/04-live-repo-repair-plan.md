# Report 4: Live Repo Repair Plan

- Repo: /home/pc/projects/GPTTalker
- Diagnosis remains read-only. No repo edits were made by this audit run.

## Safe repair boundary

- Route 7 workflow-layer findings into `scafforge-repair` for deterministic managed-surface repair.

- Do not stop at tool replacement: rerun project-local skill regeneration, agent-team follow-up, and prompt hardening before handoff.

- Refresh generated ticket-update, ticket-lookup, stage-gate, smoke-test, handoff, workflow-doc, and coordinator-prompt surfaces together; these findings indicate a managed workflow-contract defect, not just repo-local operator error.

- Rerun project-local skill regeneration and prompt hardening after the deterministic refresh so the repo-local `ticket-execution` skill and team-leader prompt explain the same state machine the tools enforce.

## Intent-changing boundary

- Escalate any stack, scope, provider, or curated human-decision changes instead of labeling them as safe repair.

## Ticket recommendations

### REMED-001 (error)

- Title: The supplied session transcript shows repeated retries of the same rejected lifecycle transition
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION002`
- Summary: After the same lifecycle blocker repeats, re-run `ticket_lookup`, read `transition_guidance`, load `ticket-execution` if needed, and stop with a blocker instead of retrying the same transition.

### REMED-002 (error)

- Title: The supplied session transcript shows the agent searching for workflow bypasses instead of following the lifecycle contract
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION003`
- Summary: Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.

### REMED-003 (error)

- Title: The supplied session transcript shows the coordinator writing specialist stage artifacts directly instead of routing those outputs through the owning lane or deterministic tool
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SESSION005`
- Summary: Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.

### REMED-004 (error)

- Title: The generated ticket transition contract still keys implementation on the wrong state surface or accepts unvalidated lifecycle requests
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW004`
- Summary: Validate every requested stage/status pair through one explicit lifecycle contract, reject unsupported stages, and gate implementation on `ticket.stage == plan_review` plus workflow-state approval.

### REMED-005 (error)

- Title: Smoke-test proof can still be fabricated through generic artifact tools instead of the owning deterministic workflow tool
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW005`
- Summary: Reserve smoke-test artifacts to `smoke_test`, and make the plugin plus transition guidance reject generic PASS-proof fabrication while keeping optional handoff artifacts consistent with docs-lane ownership.

### REMED-006 (warning)

- Title: The repo-local `ticket-execution` skill is too thin to explain the actual lifecycle contract to weaker models
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `SKILL002`
- Summary: Make `ticket-execution` the canonical lifecycle explainer: require transition guidance, explicit stop conditions, specialist-owned stage artifacts, `smoke_test`-only smoke proof, and blocker returns instead of fabricated PASS evidence.

### REMED-007 (warning)

- Title: The team leader prompt leaves workflow mechanics underspecified enough that weaker models can thrash or search for bypasses
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `WFLOW006`
- Summary: Tell the team leader to route from `ticket_lookup.transition_guidance`, stop after repeated lifecycle errors, leave stage artifacts to the owning specialist, and keep slash commands human-only.

