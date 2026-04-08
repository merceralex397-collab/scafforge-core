# Live Repo Repair Plan

## Preconditions

- This diagnosis run is read-only. No product-code, workflow-state, or ticket edits were made.
- The diagnosis pack must be treated as the canonical handoff surface for next steps.
- Because package-level prevention gaps were validated, Scafforge package work must happen before any recommended managed repair run in this repo.

## Package Changes Required First

### RP-001

- Linked findings: `F-BOOT001`, `F-MODEL001`, `F-SKILL001`
- Action type: `safe Scafforge package change`
- Target repo: Scafforge package repo
- Should `scafforge-repair` run now in this repo: no
- Must the user manually carry this diagnosis pack into the Scafforge dev repo first: yes
- Required package work:
  - make bootstrap repo-manager aware for uv-managed Python repos
  - regenerate model-profile surfaces instead of preserving deprecated MiniMax defaults
  - regenerate scaffold-managed local skills so placeholder text is removed

## Post-Update Repair Actions

### RP-002

- Linked findings: `F-BOOT001`, `F-MODEL001`, `F-SKILL001`
- Action type: `generated-repo remediation ticket/process repair`
- Target repo: subject repo
- Should `scafforge-repair` run: yes, but only after the Scafforge package changes above exist
- Must the user manually carry this diagnosis pack into the Scafforge dev repo first: yes
- Repair intent: refresh managed workflow surfaces in GPTTalker without changing project scope or human-authored product intent.

### RP-003

- Linked findings: `F-EXEC001`, `F-EXEC002`
- Action type: `generated-repo remediation ticket/process repair`
- Target repo: subject repo
- Should `scafforge-repair` run: not for the source fix itself
- Must the user manually carry this diagnosis pack into the Scafforge dev repo first: no, but package-side repair should complete first so the workflow layer is corrected before new implementation evidence is produced
- Repair intent: keep these as source-layer follow-up tickets after the managed repair refresh.

## Ticket Follow-Up

- `REMED-001`: Scafforge package work for bootstrap manager detection and proof accuracy.
- `REMED-004`: Scafforge package work for model-profile regeneration and deprecated model-surface cleanup.
- `REMED-005`: Scafforge package work for project-local skill regeneration.
- `REMED-002`: subject-repo source remediation ticket for the node-agent FastAPI DI import failure.
- `REMED-003`: subject-repo source remediation ticket for restoring pytest collection and then rerunning the full suite.

## Reverification Plan

1. Manually copy `diagnosis/20260325-025744/` from this repo into the Scafforge dev repo.
2. Apply package-side prevention changes there.
3. Return to `/home/pc/projects/GPTTalker` and run `scafforge-repair` only after those package changes are available locally.
4. After managed repair, rerun the fresh audit and confirm `BOOT001`, `MODEL001`, and `SKILL001` are gone.
5. Only then execute subject-repo source remediation for `EXEC001` and `EXEC002`.
6. Re-run:
   - `.venv/bin/python -c "from src.node_agent.main import app"`
   - `.venv/bin/pytest tests/ --collect-only -q --tb=no`
   - `.venv/bin/pytest tests/ -q --tb=no`
7. Keep the current process-verification window open until the backlog verifier rechecks done tickets under the repaired workflow contract.
