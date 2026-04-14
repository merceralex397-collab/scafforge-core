# Evidence Index — Scafforge Recovery

Generated: 2026-04-10
Status: Active — updated as evidence is gathered

---

## Evidence Sources Consulted

| Source | Location | Summary |
|--------|----------|---------|
| promptfile.md | active-plans/promptfile.md | 542-line master task specification, 7 phases |
| glitchresearch.md | archive/glitchresearch.md | 46KB analysis: 7 core issues, 10 bugs, 27 confusion events |
| evenmoreblockers.md | livetesting/glitch/evenmoreblockers.md | 106KB blocker evidence from glitch testing |
| competence-contract.md | references/competence-contract.md | 8 core invariants |
| invariant-catalog.md | references/invariant-catalog.md | 27-point checklist |
| skill-flow-manifest.json | skills/skill-flow-manifest.json | 12 skills, 5 run types |
| stage-gate-enforcer.ts | template .opencode/plugins/stage-gate-enforcer.ts | 432 lines, full plugin code |
| ticket_lookup.ts | template .opencode/tools/ticket_lookup.ts | Transition guidance builder — already checks verdicts |
| workflow.ts | template .opencode/lib/workflow.ts | hasPendingRepairFollowOn, isAllowedFollowOnTicket |
| reconcile_repair_follow_on.py | repair scripts | 242 lines, managed_blocked → source_follow_up transition |
| follow_on_tracking.py | repair scripts | 5-stage catalog, completion tracking |
| run_managed_repair.py | repair scripts | Main repair orchestrator |
| repair-execution.json | livetesting/glitch/.opencode/meta/ | SKILL001 routing evidence |

## Evidence Gathered (Session)

### EV-001: Downstream repo states (2026-04-10)
- GPTTalker: EDGE-004 done/closeout. repair_follow_on: source_follow_up. All original tickets done.
- Spinner: RELEASE-001 at review. repair_follow_on: source_follow_up.
- Glitch: RELEASE-001 at qa BUT out of order. 13 of 17 tickets incomplete. Agent jumped from wave 1 to waves 21-24.

### EV-002: Glitch ticket ordering failure (2026-04-10)
Agent completed SETUP-001, SYSTEM-001, CORE-001, ANDROID-001 (waves 0, 0, 1, 21) then jumped to RELEASE-001 (wave 24).
Still incomplete: CORE-002 (qa), CORE-003 (planning), UX-001 (planning), CONTENT-001 (planning), POLISH-001 (planning) — waves 1-3.
Plus 6 remediation tickets and SIGNING-001 (blocked).
This is evidence of wave/priority routing confusion in the agent, not a Scafforge template bug per se (RELEASE-001 has depends_on=[] so the dependency check wouldn't prevent it).
Root cause: ticket_create allowed ANDROID-001 and RELEASE-001 without enforcing wave ordering. Wave is informational only, not enforced.

### EV-003: RC-009 already fixed (2026-04-10)
ticket_lookup.ts lines 282-316 (review verdict) and 348-393 (QA verdict) already extract and check artifact verdicts before generating transition guidance. The issue documented in glitchresearch.md Issue 5 has been resolved in the current code.

### EV-004: managed_blocked not blocking any downstream repo (2026-04-10)
All three repos have repair_follow_on.outcome != "managed_blocked":
- GPTTalker: source_follow_up
- Spinner: source_follow_up
- Glitch: clean
This means the managed_blocked enforcement gap (RC-001) won't trap current agent runs, but should still be fixed for correctness.

### EV-005: WFLOW031 code reference (2026-04-10)
WFLOW031 is only in promptfile.md. No code implements it. The highest WFLOW code in codebase is WFLOW029. "Predictive repair trap" is a behavioral pattern, not a code bug — needs guidance fix in team-leader template.
