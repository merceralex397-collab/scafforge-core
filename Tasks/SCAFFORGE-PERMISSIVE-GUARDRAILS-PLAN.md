# Scafforge Remediation Plan for Permissive Execution with Enforced Quality Guardrails

## Summary
The target is not to make Scafforge conservative or low-autonomy. The target is to keep OpenCode's permissive, high-agency operating model and make the process layer strong enough that permissive agents still produce trustworthy outcomes.

That changes the design direction in one important way: Scafforge should not primarily tighten tool access to compensate for weak process. It should preserve broad capability, but enforce quality through capability-aware workflow tools, transactional state, structured proof, adversarial validation, and clearer alignment with OpenCode's native repo-local model.

The GPTTalker-class failure came from permissive agents operating inside a workflow shell that looked strict but had bypasses, weak proof semantics, split authority surfaces, and no concurrency safety. The fix is stronger enforcement and better generated infrastructure, not a retreat from permissiveness.

## Core Findings
- The current process can still be bypassed. `artifact_write`, `artifact_register`, and `handoff_publish` can be used to fabricate forward progress because the gate only intercepts part of the workflow surface.
- Shared workflow truth is too weak for a permissive multi-agent system. Parallel lanes are declared, but state mutation is plain file-based read-modify-write without locking, versions, or atomic coordination.
- Proof is too soft. Markdown artifacts are treated as evidence by regex and size heuristics instead of structured, machine-verifiable execution results.
- Repair is too blunt. Managed-surface replacement can overwrite repo-specific hardening or local extensions, which is dangerous in a system intended to be customized by powerful agents.
- Scafforge currently generates more external process scaffolding than OpenCode naturally centers. That is acceptable only if the extra layer is clearly authoritative, machine-enforced, and simpler than the failure modes it introduces.

## Remediation Changes
### 1. Preserve permissive agents, move strictness into workflow capabilities
- Keep broad tool access available for implementation-oriented agents.
- Do not rely on restrictive permissions as the primary quality mechanism.
- Make every workflow-mutating tool enforce:
  - active ticket identity
  - allowed current stage
  - predecessor proof requirements
  - provenance of who/what produced the artifact
  - consistency with existing workflow state
- Treat workflow mutation as privileged even in a permissive repo. Agents can do broad work, but they cannot claim progress unless the workflow engine accepts the evidence.

### 2. Replace narrative proof with structured proof
- Change implementation, review, QA, and smoke-test artifacts from markdown-first evidence to structured-first evidence.
- Each artifact should carry machine-readable fields for:
  - stage
  - ticket
  - commands run
  - exit codes
  - timestamp
  - actor/agent
  - result
  - linked raw output
- Keep markdown as the human-readable view, but have gates read the structured envelope.
- Reject contradictory artifacts automatically. A PASS artifact with failing commands or missing command output should never be registrable.

### 3. Make workflow state transactional
- Replace or harden the current JSON-file state layer so parallel lanes are real rather than aspirational.
- Minimum acceptable behavior:
  - atomic temp-and-rename writes
  - optimistic version checks
  - locking around state mutation
  - duplicate/artifact idempotency checks
- Better option:
  - move workflow state, artifact registry, approvals, and handoff publication to a transactional store
- Derived surfaces like `BOARD.md` and `START-HERE.md` should be regenerated from source state, never treated as writable truth.

### 4. Close every false-completion path
- Extend stage-gate enforcement to `artifact_write`, `artifact_register`, `handoff_publish`, and any other tool that mutates workflow truth.
- Prevent future-stage artifacts unless the current stage and predecessor evidence permit them.
- Prevent handoff publication unless the ticket is genuinely closeout-eligible.
- Prevent artifact registration for the wrong active ticket unless explicitly allowed by a parallel-lane policy with ownership checks.
- Add invariant checks that fail if artifact chronology, stage progression, or status transitions are impossible.

### 5. Rework repair into a managed merge system
- Keep the concept of scaffold-managed surfaces, but stop replacing entire directories blindly.
- Define extension seams for managed tools, plugins, commands, and skills.
- Repair should:
  - merge deterministic managed files
  - preserve declared local extensions
  - stop with a conflict report if local changes overlap managed blocks
  - mark the repo as requiring verification after any repair
- Collapse `START-HERE` generation to one canonical derived path so weak agents see one truth surface only.

### 6. Align the generated repo with OpenCode's real model
- Generate repos that assume:
  - Git-native operation
  - repo-local `AGENTS.md`
  - modes and permissions as real runtime controls
  - plugins/custom tools as the enforcement layer
  - LSP/formatter/IDE/TUI conventions as first-class
- Keep permissive execution where intended, but generate explicit policy around:
  - external directories
  - sharing
  - MCP enablement
  - model/provider defaults
  - custom command naming and precedence
- Avoid duplicated state or documentation that competes with repo-local truth unless it is clearly derived.

### 7. Harden generation and release validation
- Add post-render integrity checks for unresolved tokens, scaffold placeholders, and accidental replacement collisions.
- Add adversarial tests for:
  - fabricated future-stage artifacts
  - fake PASS smoke-test artifacts
  - concurrent ticket/artifact updates
  - illegal stage jumps
  - repair over locally customized managed surfaces
  - split authority in restart/handoff surfaces
- Generate a temp repo in CI and exercise the actual workflow tools, not just file presence and text patterns.
- Add a regression fixture based on the GPTTalker failure mode and require it to stay green before Scafforge changes ship.

## OpenCode Alignment Rules
- OpenCode is permissive by default, so Scafforge must generate explicit process enforcement instead of assuming prompts will hold.
- OpenCode uses layered config and "last match wins," so generated configs must be minimal, explicit, and tested for precedence drift.
- OpenCode is repo-local and Git-native, so Scafforge should avoid building a separate control plane that fights Git history, repo-local instructions, or built-in modes.
- Plugins and custom tools are the correct place for quality guardrails in a permissive environment. That is where Scafforge should invest most of its enforcement logic.

## Test Plan
- Generated-repo integration tests must verify:
  - permissive implementation actions remain possible
  - workflow claims are blocked without valid structured evidence
  - artifact fabrication fails
  - race conditions do not corrupt ticket or artifact state
  - repair preserves declared local extensions or stops with a conflict
  - `START-HERE` and similar handoff surfaces are derived-only
- Add explicit red-team tests where a simulated weak or sloppy agent tries to:
  - skip stages
  - register fake proof
  - publish handoff early
  - overwrite managed surfaces with inconsistent state
  - exploit config precedence to disable policy accidentally

## Assumptions and Defaults
- Scafforge should remain a high-autonomy scaffold for permissive agents.
- The goal is not "restrict the agent until it cannot fail." The goal is "let the agent act broadly, but only let the workflow accept correct, evidenced progress."
- GPTTalker is treated as a representative failure mode for Scafforge's current enforcement design, not as an isolated misuse case.
- When there is a tradeoff between permissive action and trustworthy workflow state, permissive action can stay broad, but workflow acceptance must fail closed.
