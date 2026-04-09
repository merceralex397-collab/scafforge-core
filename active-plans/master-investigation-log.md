# Master Investigation Log

## Phase 1: Broad Investigation (Complete)

### Scafforge Internals
- **skills/**: 11 skills, orchestrated via skill-flow-manifest.json
- **scripts/**: run_agent.sh execution harness
- **tests/**: Validation harnesses (mostly structural)
- **references/**: competence-contract.md, invariant-catalog.md, authority-adr.md
- **adapters/**: manifest.json + README.md (minimal)
- **archive/**: Historical diagnosis plans, session analysis, glitch research

### Template System
- Located at skills/repo-scaffold-factory/assets/project-template/
- Placeholder system: __PROJECT_NAME__, __FULL_PLANNER_MODEL__, etc.
- Bootstrap script: bootstrap_repo_scaffold.py (CLI args lines 716-793)
- Renders provider/model at line 825

### Stage-Gate Enforcer (Critical)
- Plugin runs BEFORE every tool call in downstream repos
- If it errors, ALL tool calls fail — most critical component
- SAFE_BASH and BOOTSTRAP_RECOVERY_BASH regexes control bash access
- RC-001 enforcement added for managed_blocked

### Workflow State Machine
- workflow.ts manages ticket lifecycle
- States: planning → plan_review → implementation → review → qa → done
- hasPendingRepairFollowOn() checks for blocking repair state
- skipGraphValidation added for repair writes

### Repair Flow
- run_managed_repair.py: Copies repo, runs repairs, copies back
- apply_repo_process_repair.py: Loads provenance, renders template, replaces surfaces
- Copytree exclusions: .git, .venv*, node_modules, __pycache__
- Creates remediation follow-up tickets via ticket-pack-builder

### Audit Flow
- audit_repo_process.py: Main orchestrator
- audit_config_surfaces.py: CONFIG001-005 checks (model, agent, directory, bash, wildcards)
- disposition_bundle.py: Routes findings to correct repair paths

## Phase 2: Root Cause Investigation (Complete)

### Evidence Sources Examined
1. Stage-gate-enforcer.ts source and runtime behavior
2. workflow.ts state machine and validation
3. run_managed_repair.py repair orchestration
4. apply_repo_process_repair.py deterministic refresh
5. follow_on_tracking.py repair follow-on state
6. bootstrap_repo_scaffold.py placeholder rendering
7. Downstream workflow-state.json files (all 3 repos)
8. Agent logs from prior runs
9. Ticket manifests and board files
10. Bootstrap provenance files
11. Repair follow-on state files

### Root Causes Identified
See root-cause-map.md for full details.

| RC | Issue | Status |
|----|-------|--------|
| RC-001 | managed_blocked not enforced in stage-gate | FIXED |
| RC-002 | deterministic-refresh injected as stage name | FIXED |
| RC-003 | asserted_completed_stages not re-validated | OPEN (low priority) |
| RC-004 | SKILL001 as stage-linked blocker | WORKING AS DESIGNED |
| RC-005 | WFLOW031 predictive repair trap | FIXED |
| RC-006 | Backward routing during managed_blocked | OPEN (low priority) |
| RC-007 | Smoke test monolithic | DEFERRED |
| RC-008 | Python-only validation gap for Godot | OPEN |
| RC-009 | Transition guidance ignores verdict | ALREADY FIXED |

### Additional Issues Found During Implementation
| Issue | Status |
|-------|--------|
| Missing hasPendingRepairFollowOn import | FIXED (commit 686cc74a) |
| .venv symlinks crash copytree | FIXED (commit 6e9bb3dc) |
| Model prefix doubling in provenance | FIXED (commit 7ead92e0) |
| Provenance stack_label/finish_contract lost | FIXED (commit 03adb917) |
| REMED-RELEASE-GATE duplicate crash | FIXED (commit c8bb368f) |
| Unhelpful managed_blocked error message | FIXED (commit 9460cc63) |

## Phase 5: Downstream Validation (In Progress)

### Agent Execution Results
- GPTTalker: Agent identifies migration bug, attempting fix via implementer
- Spinner: Agent unblocked, attempting Godot export for RELEASE-001
- Glitch: Agent unblocked, working on REMED-004

### Systemic Observations
1. managed_blocked is the primary blocker pattern — agents can't work until resolved
2. Improved error messaging enabled agents to self-unblock
3. External path discovery (Godot templates, JDK) requires bash, not glob
4. Team leader → implementer delegation works but adds latency
