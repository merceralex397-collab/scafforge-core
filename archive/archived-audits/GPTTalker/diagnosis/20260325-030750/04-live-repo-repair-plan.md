# Report 4: Live Repo Repair Plan

- Repo: /home/pc/projects/GPTTalker
- Diagnosis remains read-only. No repo edits were made by this audit run.

## Safe repair boundary

- Route 2 workflow-layer findings into `scafforge-repair` for deterministic managed-surface repair.

- Do not stop at tool replacement: rerun project-local skill regeneration, agent-team follow-up, and prompt hardening before handoff.

## Intent-changing boundary

- Escalate any stack, scope, provider, or curated human-decision changes instead of labeling them as safe repair.

## Ticket recommendations

### REMED-001 (error)

- Title: The generated bootstrap contract cannot ready this repo on the current machine, so write-capable workflow stages can deadlock before source fixes start
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `BOOT001`
- Summary: Prefer repo-native bootstrap (`uv sync --locked` for uv repos; otherwise repo-local `.venv` plus `.venv/bin/python -m pip`), record missing prerequisites accurately, and keep bootstrap readiness separate from source import/test failures.

### REMED-002 (error)

- Title: One or more Python packages fail to import — the service cannot start
- Route: `ticket-pack-builder`
- Repair class: generated-repo remediation ticket
- Source finding: `EXEC001`
- Summary: Verify every import succeeds: `python -c 'from src.<pkg>.main import app'`. Use string annotations (`-> "TypeName"`) for TYPE_CHECKING-only imports. Use `request: Request` (not `app: FastAPI`) in FastAPI dependency functions.

### REMED-003 (error)

- Title: pytest cannot collect tests — at least one test file has an import or syntax error
- Route: `ticket-pack-builder`
- Repair class: generated-repo remediation ticket
- Source finding: `EXEC002`
- Summary: Run `pytest tests/ --collect-only` and fix all collection errors before marking QA done. A QA artifact that claims tests passed when pytest cannot even collect is invalid.

### REMED-004 (warning)

- Title: Repo-local model operating surfaces are missing or still pinned to deprecated MiniMax defaults
- Route: `scafforge-repair`
- Repair class: safe Scafforge package change
- Source finding: `MODEL001`
- Summary: Regenerate `.opencode/skills/model-operating-profile/SKILL.md`, align provenance/model-matrix/agent frontmatter on the current runtime model choices, and remove deprecated `MiniMax-M2.7` surfaces before implementation continues.

## Post-repair follow-up

- Route 2 source-layer remediation item(s) through `ticket-pack-builder` and any generated repo guarded ticket surfaces after workflow repair is complete.

