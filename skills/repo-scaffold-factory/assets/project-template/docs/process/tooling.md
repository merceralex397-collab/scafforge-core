# Tooling Layers

Use the project-local surfaces this way:

- `.opencode/commands/` for human entrypoints only
- `.opencode/tools/` for structured repo operations agents can call directly
- `.opencode/plugins/` for guardrails, synchronization, and compaction context
- `.opencode/skills/` for local deterministic guidance
- `mcp` in `opencode.jsonc` for external services and richer integrations

Important workflow tools:

- `ticket_lookup` resolves the active ticket and current workflow state, reports the current artifact proof, and returns `transition_guidance` with the next legal stage move, required proof, and recommended `ticket_update` call shape; if bootstrap is not ready it short-circuits normal lifecycle guidance and routes `environment_bootstrap` first
- `ticket_update` changes lifecycle stage, derives the matching coarse queue status when needed, and rejects unsupported or contradictory stage/status pairs
- `artifact_write` writes the full body for a canonical stage artifact in the stage-specific directory for that stage
- `artifact_register` records metadata for an artifact that was already written at the canonical path
- `smoke_test` runs deterministic smoke-test commands, writes the canonical smoke-test artifact itself, and reports pass/fail without delegating the stage to another agent; explicit `command_override` input may be tokenized argv for one command, one shell-style command string, or multiple shell-style command strings executed in order, but mixed tokenized-plus-multi-command forms are rejected as malformed configuration
- `environment_bootstrap` installs and verifies repo-local runtime and test dependencies using the repo's own package manager and environment contract; uv-managed Python repos must translate optional dependency layouts such as `[project.optional-dependencies].dev` or `[dependency-groups].dev` into the correct `uv sync` flags
- `context_snapshot` refreshes the compact restart surface
- `handoff_publish` refreshes the top-level handoff
- `skill_ping` records explicit local or global skill use in `.opencode/state/invocation-log.jsonl`
- `ticket_create` creates guarded follow-up tickets from current registered evidence during process verification, post-completion defect intake, open-parent split decomposition, or other approved remediation follow-up paths; `split_scope` keeps the parent open and linked instead of marking it blocked
- `ticket_reconcile` repairs stale or contradictory source/follow-up linkage from current evidence and writes a reconciliation artifact instead of requiring manual manifest surgery; `source_ticket_id` / `replacement_source_ticket_id` name the authoritative owner, and `target_ticket_id` names the stale follow-up ticket being rewritten or superseded; set `supersede_target: true` when the stale ticket should close as superseded rather than remain open with relinked lineage

Tracking surfaces:

- `tickets/manifest.json` stores queue state and registered artifact metadata for each ticket
- `.opencode/state/artifacts/registry.json` stores the cross-ticket artifact registry
- `.opencode/state/workflow-state.json` stores transient approval and current-stage state
- `.opencode/state/workflow-state.json` also owns canonical `repair_follow_on` state after managed repair; do not rely on sidecar repair records alone for restart routing
- `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are derived restart surfaces regenerated from the current manifest and workflow state
- `.opencode/state/smoke-tests/` stores canonical deterministic smoke-test artifacts
- `.opencode/plugins/invocation-tracker.ts` logs chat, command, and tool execution events
- `.opencode/meta/bootstrap-provenance.json` records how the OpenCode layer was generated or retrofitted and owns the canonical workflow-contract version metadata
- `.opencode/meta/bootstrap-provenance.json` is provenance-only; do not treat it as mutable queue or restart state
- `.opencode/state/workflow-state.json` also records the active process version and whether post-migration verification is still pending
- `.opencode/meta/repair-execution.json` is an audit trail only; restart routing must prefer `.opencode/state/workflow-state.json`
- the team leader owns `ticket_claim` and `ticket_release`; specialists write only under the active ticket lease instead of claiming their own lane

Review and diagnosis support:

- use the generated repo-local `review-audit-bridge` skill for evidence-first review output and remediation-ticket recommendations
- keep any diagnosis pack or process-log output under the repo-local `diagnosis/` path when the project uses that convention
- treat diagnosis output as an evidence surface only; canonical queue and artifact state still move through ticket and artifact tools
- do not use `.opencode/commands/` as the autonomous workflow; commands are human entrypoints only
- do not create smoke-test artifacts through `artifact_write` or `artifact_register`; use `smoke_test`
