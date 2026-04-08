# Scafforge Prevention Actions

## Package Changes Required

### PA-001

- Change target: Scafforge bootstrap manager detection and generated `environment_bootstrap` surface
- Linked findings: `F-BOOT001`, `PF-BOOT001`
- Why it prevents recurrence: repos with `uv.lock` or uv-managed `.venv` stop deadlocking on machines that do not ship global `pip`.
- Safe or intent-changing: safe
- Validation: generate a Python repo with `uv.lock`, run bootstrap on a machine without global `pip`, and confirm the proof artifact records the correct prerequisite state and a successful repo-native path.

### PA-002

- Change target: Scafforge agent prompt templates for implementer and tester/QA roles
- Linked findings: `F-EXEC001`, `F-EXEC002`, `PF-EXEC001`, `PF-EXEC002`
- Why it prevents recurrence: import checks, collection checks, and full test proof become mandatory before closeout evidence is accepted.
- Safe or intent-changing: safe
- Validation: rerun scaffolded implementation/QA flows in a repo with a deliberate import bug and confirm the artifact is rejected until command output shows a clean import and passing collection.

### PA-003

- Change target: model-profile regeneration surfaces in managed skills, provenance, model matrix, and agent prompts
- Linked findings: `F-MODEL001`, `PF-MODEL001`
- Why it prevents recurrence: all managed model surfaces move together instead of leaving stale MiniMax defaults behind.
- Safe or intent-changing: safe if the repo is still on package-managed defaults; escalate if the repo is intentionally human-pinned.
- Validation: regenerate a repo-local model profile, confirm `.opencode/skills/model-operating-profile/SKILL.md` exists, and scan managed surfaces for deprecated `MiniMax-M2.7` references.

### PA-004

- Change target: project-skill-bootstrap output for scaffold-managed local skills
- Linked findings: `F-SKILL001`, `PF-SKILL001`
- Why it prevents recurrence: baseline stack skills become concrete repo guidance instead of placeholder text.
- Safe or intent-changing: safe
- Validation: run skill regeneration and confirm no scaffold-managed `.opencode/skills/*.md` file still contains placeholder filler such as `Replace this file...`.

## Validation and Test Updates

- Add an audit assertion that flags `python3 -m pip` bootstrap commands when the subject repo contains `uv.lock` or a uv-managed `.venv`.
- Add a managed-surface check that fails if `.opencode/skills/model-operating-profile/SKILL.md` is missing in a repo expected to have current model guidance.
- Add a managed-skill check that fails if scaffold placeholder text remains in `.opencode/skills/`.
- Add prompt-level regression coverage so implementer/QA artifacts are rejected when they lack raw command output for import checks and test execution.

## Documentation or Prompt Updates

- Update bootstrap docs so repo-native package managers are explicit and reflected in proof artifacts.
- Update managed agent prompts to say that code inspection is not validation and that `pytest --collect-only` is required when a Python test suite exists.
- Update managed repair docs so model-profile and local-skill regeneration are treated as part of workflow refresh, not optional follow-up.

## Open Decisions

- If GPTTalker is intentionally pinned by a human to `minimax-coding-plan/MiniMax-M2.7`, the model drift is an intent choice and should be documented rather than silently replaced.
- If not intentionally pinned, the deprecated model/profile surfaces should be refreshed as part of the next Scafforge package update before further managed repair runs here.
