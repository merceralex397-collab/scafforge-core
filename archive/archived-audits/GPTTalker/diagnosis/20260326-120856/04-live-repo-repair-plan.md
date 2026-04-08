# Live Repo Repair Plan

- Repo: `/home/pc/projects/GPTTalker`
- Diagnosis timestamp: `2026-03-26T12:08:56Z`
- Audit stayed non-mutating apart from this diagnosis pack.

## Preconditions

- Do not treat `sessionlog0458.md` as a direct instruction to rerun `scafforge-repair`; it predates the latest 2026-03-26 workflow refresh.
- Keep current repo truth anchored in `.opencode/state/workflow-state.json`, `tickets/manifest.json`, and the live source files.

## Package Changes Required First

- None confirmed.
- The historical transcript issue appears already repaired in current prompt/skill/tool surfaces, so this audit does not validate a fresh package-side defect that must be fixed before repo work continues.

## Post-Update Repair Actions

- Complete the existing source-layer remediation queue:
  - `EXEC-008`: reject raw `.` / `..` shortcut traversal patterns before normalization collapses them.
  - `EXEC-009`: replace invalid UTC timestamp usage in `OperationExecutor.list_directory()`.
  - `EXEC-010`: restore nested redaction shape preservation and max-depth sentinel behavior in `redact_sensitive()`.
- After those tickets land, rerun:
  - `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -v --tb=short`

## Ticket Follow-Up

- No new tickets are needed from this audit.
- Current failures are already mapped to the existing open tickets `EXEC-008`, `EXEC-009`, and `EXEC-010`.
- `EXEC-011` remains separate lint debt and was not part of the reproduced test-failure set from this audit.

## Reverification Plan

- Keep `pending_process_verification` set until the backlog verifier finishes the affected done-ticket set for the current process window.
- Use the backlog-verifier and `ticket_reverify` flow to restore trust on historical done tickets; do not declare the repo verification-clean before that queue is empty.
- If full-suite pytest still fails after `EXEC-008` through `EXEC-010` close, reopen diagnosis with the new executable evidence rather than reusing the historical session log alone.
