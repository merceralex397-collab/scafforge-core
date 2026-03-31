# Scafforge Deadlock Hardening Plan

## Diagnosis

The key chronology is:

- `2026-03-27 14:39:40` — transcript-backed audit at `GPTTalker/diagnosis/20260327-143940` with `bootstrap2.md` and `bootstrapfail.md` did catch major workflow defects: `BOOT002`, `SESSION003`, `SESSION005`, `WFLOW010`, `WFLOW016`, `WFLOW017`, `WFLOW021`.
- `2026-03-27 15:17:58` — clean audit at `GPTTalker/diagnosis/20260327-151758` had `finding_count: 0` and no `supporting_logs`.
- `2026-03-27 15:59:50` — another clean audit at `GPTTalker/diagnosis/20260327-155950` also had `finding_count: 0` and no `supporting_logs`.
- `2026-03-27 17:13:00` — transcript-backed audit at `GPTTalker/diagnosis/20260327-171300` with `reviewlog1.md` again found `SESSION003`, `SESSION005`, `WFLOW016`, `WFLOW017`.

So the real answer is not “audit had no detector.” It had detectors. It found them in `143940` and again in `171300`.

The real failures are these:

1. Repair verification was not deterministic enough.
   - The repair flow splits verification in two:
     - internal runner logic in `skills/scafforge-repair/scripts/run_managed_repair.py`
     - then a separate public audit step described in `skills/scafforge-repair/SKILL.md`
   - The skill text says to pass `--supporting-log` when repair basis was transcript-backed.
   - That means the final “clean” audit still depends on the operator or host remembering to carry logs forward manually.
   - That is an unacceptable Scafforge contract gap.

2. Audit taxonomy captured symptoms, not the trap itself.
   - `143940` recorded `SESSION003`, `SESSION005`, `WFLOW016`, `WFLOW017`.
   - But the deeper impossible-state contradictions were not promoted into first-class structural findings:
     - closed-ticket `handoff_publish` lease contradiction
     - ticket acceptance criteria broader than ticket scope and impossible without sibling-ticket work
   - Those are the things that create thrash.

3. Repair was allowed to verify “current state clean” instead of “causal deadlock resolved.”
   - A repo can look clean after surfaces are regenerated.
   - That does not prove the workflow no longer traps the operator under the same transcript-shaped scenario.
   - Scafforge is currently too willing to accept surface cleanliness as convergence.

4. Repeated findings were not escalated as package-level incompetence.
   - Across the week’s packs, the same families recur: `SESSION003`, `SESSION005`, `WFLOW016`, `WFLOW017`, `WFLOW008`, ticket-graph drift, and repair-gate drift.
   - Audit treats them as per-pack findings.
   - It does not promote repeated deadlock families into a higher-severity “workflow contract still not competent” diagnosis.

5. Greenfield ticketing still allows impossible acceptance.
   - The `reviewlog1.md` EXEC-013 case shows a ticket whose literal acceptance command was contaminated by EXEC-014 scope.
   - That traps the operator between “follow canonical acceptance” and “do not touch sibling-ticket scope.”
   - Scafforge should stop generating tickets like that.

## Repository-Wide Plan

### 1. Repair verification must become automatic and causal

- Replace the current “remember to run a second audit with `--supporting-log`” contract in `skills/scafforge-repair/SKILL.md`.
- Make `skills/scafforge-repair/scripts/run_managed_repair.py` emit the post-repair diagnosis pack itself.
- Always inherit transcript evidence from the repair basis automatically.
- Fail repair if the basis was transcript-backed and the post-repair diagnosis pack is not transcript-backed.
- Record two verification outcomes:
  - `current_state_clean`
  - `causal_regression_verified`
- Do not allow “repair converged” unless both are true.

### 2. Add first-class findings for impossible workflow states

Add new audit codes in `skills/scafforge-audit/scripts/audit_repo_process.py`:

- `WFLOW022`: closeout or handoff lease contradiction
  - Example: `handoff_publish` or equivalent restart-surface update still requires an active write lease on a ticket that is already closed.
- `WFLOW023`: ticket acceptance contamination
  - Example: a ticket’s canonical acceptance command includes failures owned by another open or planned ticket, so the ticket cannot pass without scope violation.
- `SESSION006`: operator trap / no-legal-next-move loop
  - Use when the transcript shows the coordinator cycling among blocked lifecycle actions, forbidden workarounds, and contradictory instructions without any legal route forward.

These must not be downgraded into generic “bypass search” or “ticket failed” findings.

### 3. Promote confusion to a package defect

Update audit and repair references so “operator confusion” is treated as evidence of contract failure when:

- the next legal move is ambiguous
- the workflow requires remembering hidden flags or extra commands
- two canonical surfaces instruct conflicting actions
- a ticket cannot satisfy acceptance without violating scope
- a deterministic tool requires impossible preconditions

This needs to be explicit in:

- `skills/scafforge-audit/SKILL.md`
- `skills/scafforge-repair/SKILL.md`
- process smell references
- repair playbooks

### 4. Add repeat-failure escalation

Add a weekly-repeat or repo-repeat escalation layer:

- if the same deadlock family recurs across diagnosis packs without a newer package or process change that should have resolved it, emit a top-level cycle finding
- not just `CYCLE002` for “stop auditing again”
- also “the repair contract is not converging on this failure family”

This should explicitly aggregate:

- `SESSION003`
- `SESSION005`
- `WFLOW016`
- `WFLOW017`
- `WFLOW022`
- `WFLOW023`

### 5. Harden greenfield ticket generation

Update `skills/ticket-pack-builder/SKILL.md`:

- acceptance commands must be owned by the ticket’s scope
- if an acceptance command is known to rely on sibling cleanup, the ticket must be split or blocked explicitly
- the acceptance command must be executable by `smoke_test` without ad hoc narrowing
- forbid tickets whose literal closeout command contradicts the stated scope boundaries

Add validation in Scafforge smoke tests so this fails package verification.

### 6. Make restart and handoff updates non-contradictory

Current template `handoff_publish.ts` is better, but audit still needs to detect the old contradiction and repair must migrate it cleanly.

Required rule:

- restart-surface publication after closeout must not depend on reacquiring a normal write lease on the closed ticket

Add transcript regression coverage from `bootstrapfail.md` and `reviewlog1.md`.

### 7. Expand package regression coverage using GPTTalker chronology

Add permanent regression fixtures for:

- `20260327-143940` as transcript-backed diagnosis basis
- `20260327-151758` and `20260327-155950` as false-clean verification failures
- `20260327-171300` as proof that the causal failures remained detectable later

Required assertions:

- a transcript-backed repair basis cannot verify clean through a log-less post-repair audit
- the old `smoke_test` override failure emits `WFLOW016`
- acceptance drift emits `WFLOW017`
- closed-ticket handoff contradiction emits `WFLOW022`
- contaminated acceptance emits `WFLOW023`
- repeated operator trap loops emit `SESSION006`
- repeated weekly recurrence escalates to a cycle-level non-convergence finding

### 8. Change the public repair contract

Public repair must become:

1. consume diagnosis basis
2. deterministic refresh
3. required prompt, skill, and agent regeneration
4. automatic transcript-backed verification diagnosis pack
5. fail closed unless causal regression is verified

Do not leave step 4 as a human-memory obligation.

## Why So Many Audits Failed In Practice

Scafforge currently allows three incompetent behaviors:

- it allows findings to stay fragmented as “session weirdness” instead of naming the underlying impossible workflow state
- it allows repair verification to pass on current-state cleanliness rather than causal replay
- it still puts crucial verification behavior behind operator memory instead of deterministic tooling

That is why the system can generate many audits without actually breaking the loop.
