# Tooling Layers

Use the project-local surfaces this way:

- `.opencode/commands/` for human entrypoints only
- `.opencode/tools/` for structured repo operations agents can call directly
- `.opencode/plugins/` for guardrails, synchronization, and compaction context
- `.opencode/skills/` for local deterministic guidance
- `mcp` in `opencode.jsonc` for external services and richer integrations

Important workflow tools:

- `ticket_lookup` resolves the active ticket and current workflow state, reports the current artifact proof, and returns `transition_guidance` with the next legal stage move, required proof, and recommended `ticket_update` call shape
- `ticket_update` changes lifecycle stage, derives the matching coarse queue status when needed, and rejects unsupported or contradictory stage/status pairs
- `artifact_write` writes the full body for a canonical stage artifact in the stage-specific directory for that stage
- `artifact_register` records metadata for an artifact that was already written at the canonical path
- `smoke_test` runs deterministic smoke-test commands, writes the canonical smoke-test artifact itself, and reports pass/fail without delegating the stage to another agent
- `context_snapshot` refreshes the compact restart surface
- `handoff_publish` refreshes the top-level handoff
- `skill_ping` records explicit local or global skill use in `.opencode/state/invocation-log.jsonl`
- `ticket_create` creates guarded follow-up tickets from current registered evidence during process verification, post-completion defect intake, or other approved remediation follow-up paths

Tracking surfaces:

- `tickets/manifest.json` stores queue state and registered artifact metadata for each ticket
- `.opencode/state/artifacts/registry.json` stores the cross-ticket artifact registry
- `.opencode/state/workflow-state.json` stores transient approval and current-stage state
- `.opencode/state/smoke-tests/` stores canonical deterministic smoke-test artifacts
- `.opencode/plugins/invocation-tracker.ts` logs chat, command, and tool execution events
- `.opencode/meta/bootstrap-provenance.json` records how the OpenCode layer was generated or retrofitted and owns the canonical workflow-contract version metadata
- `.opencode/state/workflow-state.json` also records the active process version and whether post-migration verification is still pending

Review and diagnosis support:

- use the generated repo-local `review-audit-bridge` skill for evidence-first review output and remediation-ticket recommendations
- keep any diagnosis pack or process-log output under the repo-local `diagnosis/` path when the project uses that convention
- treat diagnosis output as an evidence surface only; canonical queue and artifact state still move through ticket and artifact tools
- do not use `.opencode/commands/` as the autonomous workflow; commands are human entrypoints only
- do not create smoke-test artifacts through `artifact_write` or `artifact_register`; use `smoke_test`
