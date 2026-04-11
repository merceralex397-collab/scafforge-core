# Implementation Plan — Scafforge Recovery

> Superseded as the primary live plan. Use `active-plans/fullassessment1104261519.md` for the current repo-wide assessment, scope reconciliation, downstream-status review, and Scafforge remediation plan.

Generated: 2026-04-10
Status: Historical / superseded

---

## Priority Order

### Tier 1: Template Fixes (blocks agent correctness)

1. **Fix stage-gate-enforcer.ts: Add managed_blocked enforcement**
   - Add centralized hasPendingRepairFollowOn check early in tool.execute.before
   - Block ticket_create and other lifecycle-mutating tools during managed_blocked (unless targeting allowed follow-on tickets)
   - Evidence: RC-001 in root-cause-map.md
   - Files: skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts

2. **Fix run_managed_repair.py: Remove deterministic-refresh as stage name**
   - Change from injecting into completed_stage_name_set to using an internal flag
   - Evidence: RC-002 in root-cause-map.md
   - Files: skills/scafforge-repair/scripts/run_managed_repair.py

3. **Fix reconcile_repair_follow_on.py: Deprecate asserted_completed_stages**
   - Validate that completed_stages entries are all in the persistent tracking ledger
   - Stop preserving asserted_completed_stages without re-validation
   - Evidence: RC-003 in root-cause-map.md
   - Files: skills/scafforge-repair/scripts/reconcile_repair_follow_on.py

4. **Add WFLOW031 anti-pattern guidance to team-leader template**
   - Add explicit "these states are normal" section to prevent predictive repair routing
   - States: verification_state "suspect", pending_process_verification true, source_follow_up outcome
   - Evidence: RC-005 in root-cause-map.md
   - Files: skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md

### Tier 2: Execution Harness (blocks downstream runs)

5. **Build execution harness script**
   - Resume-style opencode run with context hydration
   - Log capture to Scafforge-owned evidence locations
   - Ability to re-run after failures
   - Files: scripts/run_downstream_agent.sh or similar

### Tier 3: Downstream Validation (proves the system works)

6. **GPTTalker: Verify MCP server starts + code review**
   - Run agent for final verification / any remaining work
   - Test MCP server startup (this is just testing, not editing)
   - Run code review sub-agent

7. **Spinner: Complete RELEASE-001 (review → closeout, build APK)**
   - Run agent to continue from review stage
   - Must build APK via Godot export
   - Code review when done

8. **Glitch: Complete RELEASE-001 (qa → closeout, build APK)**
   - Run agent to continue from qa stage
   - Must build APK via Godot export
   - Code review when done

### Tier 4: Expansion (new capabilities)

9. **Blender-agent assessment and fixes**
10. **Asset pipeline design in Scafforge**
11. **Create 4 womanvshorse repos via Scafforge greenfield**
12. **Drive all 4 to completion via headless agents**

---

## Key Decisions

- **Template fixes go into the template for future repos, not into existing downstream repos directly** — downstream repos get updated via managed repair runs if needed
- **Current downstream repos are NOT in managed_blocked state** — agents can continue without template fixes
- **Execution harness uses `opencode run` with `--continue` and resume-style prompts**
- **RC-009 is already fixed** — transition guidance does check artifact verdicts in current code
- **RC-004 is working as designed** — SKILL001 correctly routes through managed_blocked
