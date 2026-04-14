# Blocker Register — Scafforge Recovery

Generated: 2026-04-10
Status: Active — refreshed 2026-04-12

---

## Active Blockers

| ID | Description | Severity | Root Cause | Status |
|----|-------------|----------|------------|--------|
| BLK-003 | asserted_completed_stages not re-validated | MEDIUM | RC-003 | OPEN |
| BLK-005 | Python-only validation gap for Godot repos | HIGH | RC-008 | OPEN - contradictory smoke proof, missing finish-validation lanes, and weak machine-generated interactive finish bars are fixed; broader gameplay/finish validation still needed |

## Resolved Blockers

| ID | Description | Resolution |
|----|-------------|------------|
| BLK-001 | stage-gate-enforcer lacks managed_blocked check | RESOLVED in commit `906dc002`; `stage-gate-enforcer.ts` now enforces managed_blocked before lifecycle mutations, and validation-log.md records the blocker firing correctly. |
| BLK-002 | deterministic-refresh is non-catalog stage name | RESOLVED in commit `906dc002`; repair output now treats deterministic refresh as an internal-only operation instead of polluting follow-on stage state. |
| BLK-004 | WFLOW031 predictive repair trap in team-leader | RESOLVED in commit `906dc002`; team-leader guidance now distinguishes normal suspect/pending verification states from real repair triggers. |
| BLK-R01 | Transition guidance ignores verdict | ALREADY FIXED in current code (ticket_lookup.ts lines 282-393) |
| BLK-R02 | SKILL001 stage-linked blocker | WORKING AS DESIGNED |
| BLK-R03 | Blender system dependencies | FIXED — installed libsm6, libxext6, libxrender-dev |

## Downstream Repo Blockers (Not Scafforge bugs)

Use `fullassessment1104261519.md` as the live downstream snapshot. The original table here is historical and no longer trustworthy enough to drive work ordering.

Current high-signal downstream themes from the refreshed assessment:

- The previously confirmed workflow-drift set (`GPTTalker`, `spinner`, `womanvshorseVA/VB/VC/VD`, `glitch`) no longer reproduces the Scafforge-routed workflow blockers on the current package after the 2026-04-12 repair passes; their remaining queues are source-follow-up and product-surface remediation only.
- The headless runner fallback lane was briefly regressed under Codex quota exhaustion, but the 2026-04-12 control-flow fix restored the required `Codex -> Kilo -> Copilot` behavior and was validated with real Kilo-backed audits.
- `womanvshorseVA` remains the clearest false-finish example, but the structural finish-lane gap is now repairable and already validated on multiple repos: public audits `womanvshorseVA/diagnosis/20260412-034402/` and `spinner/diagnosis/20260412-034826/` emitted `FINISH003`, managed repair backfilled `FINISH-VALIDATE-001`, and follow-up public audits `womanvshorseVA/diagnosis/20260412-034655/` and `spinner/diagnosis/20260412-035103/` cleared the package-side finish-lane defect. The remaining queue is product/source follow-up, not missing Scafforge finish ownership.
- `glitch` is closest to clean closure, but embedded-repo hygiene still inflates the Scafforge worktree.
