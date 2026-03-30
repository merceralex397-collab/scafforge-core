# Scafforge Blind Verification Pass

Repo: `merceralex397-collab/Scafforge`
Target baseline commit: `7e2040f817e3578c6eec2a628b84cfdc0f5cc5a8`
Verification mode: blind re-pass from repo surfaces, using the GitHub connector only.

## Scope and honesty

This pass re-verified the live workflow files, skill-flow contract, repair runner, archived diagnosis manifests, archive/log surface, and commit history without assuming the earlier review was correct.

What was fully re-checked directly:
- live package skills in `skills/`
- key live scripts in `scripts/` and `skills/*/scripts/`
- live flow manifest and kickoff contract
- representative template-side repo-local skills and tools
- archived diagnosis manifests and repeated repair-loop artifacts
- commit history for workflow / audit / repair evolution

What was **not** fully line-read byte-for-byte in one pass:
- every archived JSONL transcript and every long archived markdown log in the repo

The archive surface is too large for literal byte-level review in a single connector pass. Instead, the pass inspected the recurring archive classes, latest/representative manifests, repeated churn logs, and the files that define the current package behavior.

## Blind-pass verdict

The earlier conclusion still holds: Scafforge is stronger at generating and policing workflow structure than it is at guaranteeing smooth execution convergence.

The blind pass adds several new findings:
1. the current greenfield contract still ends in handoff without a mandatory audit gate
2. the skill graph itself has cyclic coupling between key generation stages
3. the repair runner openly encodes non-convergence by requiring follow-on regeneration stages after deterministic repair
4. the repo’s archive/log surface is now a first-order product defect because it contaminates search and retrieval
5. commit history shows rapid reactive hardening, which implies contract instability and high migration risk
6. emitted post-repair diagnosis manifests still show provenance gaps and residual placeholder drift
7. template-level governance skills add more role overlap and process narration than the package can currently carry safely

---

## Re-verified persistent findings

### 1. Greenfield still prefers conformance over proof of runnable continuation

The live `skill-flow-manifest.json` greenfield sequence is:
- `spec-pack-normalizer`
- `repo-scaffold-factory`
- `project-skill-bootstrap`
- `opencode-team-bootstrap`
- `agent-prompt-engineering`
- `ticket-pack-builder`
- `handoff-brief`

There is no explicit `scafforge-audit` stage in that greenfield sequence.

**Impact:** Scafforge still allows a repo to reach handoff before it has passed a package-grade diagnostic gate.

### 2. `scaffold-kickoff` still explicitly forbids sending initial greenfield generation into audit or repair

The live kickoff skill still says not to route the initial greenfield generation pass into `scafforge-audit` or `scafforge-repair`, and instead relies on a same-session contract-conformance check before handoff.

**Impact:** the package still treats “contract agreement across surfaces” as enough for first handoff, even though the surrounding package history shows that this is not enough to prevent deadlock, ownership confusion, or heuristic execution drift.

### 3. Repair remains multi-stage and non-convergent by design

`run_managed_repair.py` re-check confirms that deterministic refresh is only one phase. It can still require:
- `project-skill-bootstrap`
- `opencode-team-bootstrap`
- `agent-prompt-engineering`
- `ticket-pack-builder`

after refresh, depending on placeholder drift, prompt drift, workflow findings, or `EXEC*` findings.

**Impact:** Scafforge repair is not a truly self-contained repair. It is a managed repair orchestration flow that often depends on more regeneration afterward.

### 4. Archived evidence still shows the same failure classes repeating

The re-checked archived manifests still show:
- bypass-seeking / unsupported transition behavior
- coordinator ownership overreach into specialist outputs
- split lease contract across coordinator and worker surfaces
- heuristic smoke scope drifting away from ticket-defined acceptance commands
- lingering historical process verification state
- source bug routing into follow-up tickets rather than clean closure

**Impact:** the failure pattern is systemic, not anecdotal.

---

## New findings from the blind pass

### 5. The skill graph is cyclic, not merely sequential

The `skills/skill-flow-manifest.json` graph is not just a clean forward chain.

Examples:
- `opencode-team-bootstrap` lists `project-skill-bootstrap` as both upstream and downstream
- `project-skill-bootstrap` lists `opencode-team-bootstrap` as both upstream and downstream
- `repo-scaffold-factory` feeds `project-skill-bootstrap` and `scafforge-audit`
- `scafforge-repair` feeds `ticket-pack-builder` and `handoff-brief`, but repair also depends on upstream package outputs from earlier generation stages

**Why this matters:**
This is conceptual cyclic coupling. Even if the normal happy-path sequence is linear, the package semantics encourage mutual dependency between skill families. That makes it much easier for an agent to reason in loops.

**Severity:** high

### 6. The repo’s archive and log exhaust is now a product-level defect

Repo search is saturated with:
- `out/scafforge audit archive/...`
- `scafforgechurnissue/...`
- GPTTalker churn logs
- Codex JSONL rollout logs
- archived plans and postmortems

These are not merely inert records anymore. They materially shape repo search results and can outrank or visually crowd live package files.

**Why this matters:**
For an agentic system, search surface is part of runtime behavior. If the package repo contains a large amount of historic churn, deadlock logs, postmortems, and archived plans, an agent inspecting the repo is more likely to retrieve stale diagnosis or historical design intent than the single live contract it should follow.

**Severity:** critical

### 7. Commit history shows reactive hardening rather than a settled contract

Recent commit history is dominated by messages like:
- `Route stale WFLOW024 revalidation to repair`
- `Harden audit repair loop and reconciliation contract`
- `Harden workflow contract and audit repair handling`
- `Refresh Scafforge workflow contract from GPTTalker diagnosis`
- `Fix workflow restart surface drift`
- `tighten workflow audit and repair contract`
- `Fix transcript-aware audit and workflow deadlocks`
- `Tighten Scafforge audit and repair lifecycle`
- `Improve Python bootstrap diagnosis and prevention`
- `Enforce one-shot generation contract and docs`
- `Add scafforge-audit and scafforge-repair skills`

**Why this matters:**
This pattern shows the package has been evolving mainly by absorbing new failure cases into governance, audit, repair, and contract-hardening layers.

That is not automatically wrong, but it means:
- migration burden is high
- package semantics are still moving quickly
- generated repos may age badly across package revisions
- “workflow stability” is not yet earned

**Severity:** high

### 8. Post-repair manifests still show residual placeholder drift

A re-checked post-repair verification manifest still reports `SKILL001` for generic placeholder text remaining in repo-local skills.

**Why this matters:**
This means the package can complete repair machinery and still fail one of the most basic promises of repo-local skill generation: replacing template filler with project-specific guidance.

**Severity:** high

### 9. Provenance fields can still be emitted as `unknown`

The post-repair manifest reviewed in this pass still contains `audit_package_commit: "unknown"` and `repair_package_commit: "unknown"`.

**Why this matters:**
For a package that relies so heavily on audit, repair, process-versioning, and diagnosis inheritance, weak provenance is not a cosmetic flaw. It undermines trust in package-level accountability.

**Severity:** medium-high

### 10. Governance overlap exists inside the template layer too

The generated template-side `review-audit-bridge` skill explicitly bridges review and QA lanes, can recommend follow-up tickets, and writes workflow-failure explanation or review retrospectives to repo-local process-log paths.

**Why this matters:**
Scafforge already has package-level audit, repair, restart, ticketing, and handoff machinery. Adding more bridge/governance layers inside generated repo-local skills increases the chance that:
- review commentary starts to act like audit
- process logging starts to multiply in multiple places
- repo-local skills create more procedural narration rather than more execution clarity

**Severity:** medium-high

### 11. Greenfield required outputs still emphasize contract agreement, not bootstrap proof

The current flow contract requires:
- canonical brief
- aligned workflow/ticket restart surface
- same-session contract conformance check
- valid `START-HERE.md`

But it still does **not** elevate the following to top-level greenfield success criteria:
- bootstrap proof exists
- one canonical first lane exists
- first lane validation command is runnable
- first handoff is backed by deterministic execution proof

**Why this matters:**
This is the clearest package-level sign that Scafforge still measures the wrong thing first.

**Severity:** critical

### 12. Diagnosis flow already contains a “stop rerunning the same loop” rule

The live kickoff diagnosis flow says that if repeated diagnosis packs show the same repair-routed findings and there is no newer package or process-version change, the run should stop and route back to package work instead of rerunning another subject-repo audit.

**Why this matters:**
The package explicitly knows repeated audit→repair→resume→failure loops happen often enough to require a stop rule.

That is a new blind-pass confirmation that the loop problem is a recognized design fact, not a fringe case.

**Severity:** high

### 13. Search-surface contamination likely explains part of the “logical trap” behavior by itself

This blind pass suggests a further mechanism beyond workflow complexity:

When the repo contains many archived:
- plans
- churn manifests
- postmortems
- GPTTalker logs
- rollout JSONL traces
- archived recommendations

an agent doing broad repo search can easily pull:
- historical failure narratives
- superseded repair plans
- stale naming and architecture notes
- example logs that look like live contract evidence

instead of just the live package contract.

**Why this matters:**
This means some of the trap is architectural, but some of it may be **retrieval poisoning by historical clutter inside the package repo itself**.

**Severity:** critical

---

## Consolidated issue list

### Critical
- greenfield flow still reaches handoff without mandatory audit
- success criteria still prioritize conformance over runnable bootstrap proof
- archive/log/postmortem clutter materially contaminates repo search
- retrieval contamination likely contributes directly to agent confusion and trap behavior

### High
- cyclic coupling between core skill families
- repair is non-convergent and openly depends on follow-on regeneration stages
- commit history indicates rapid reactive hardening rather than a settled contract
- repeated diagnosis artifacts confirm the same workflow failures keep recurring
- package already needs explicit “stop rerunning the same loop” behavior
- placeholder local skill drift can survive repair passes

### Medium-high
- provenance fields can still be emitted as `unknown`
- template governance layers overlap with package governance layers

### Medium
- the package has strong diagnostics but still too many surfaces where ownership, restart, review, and process narration can overlap

---

## What Scafforge does well

This blind pass does **not** reduce Scafforge to “broken.”

The package is strong in these areas:
- it has serious diagnosis and repair machinery
- it understands transcript-backed and current-state verification as different things
- it has deterministic bootstrap and smoke-test tools
- it recognizes safe-vs-intent-changing repair boundaries
- it has explicit ticket refinement/remediation paths
- it knows repeated repair loops are dangerous and tries to stop them

Those are real strengths.

The problem is that the package keeps adding governance to compensate for a core convergence problem.

---

## Final judgement after the blind pass

### Has the earlier diagnosis changed?
No.

It has been **strengthened**.

### Strongest verified statement now

Scafforge is a package that has become highly intelligent about:
- diagnosing deadlock
- narrating deadlock
- repairing managed surfaces after deadlock
- versioning and tracking deadlock causes

but it still has not made deadlock structurally hard enough to enter in the first place.

### New strongest added statement

Scafforge’s **archive and governance sprawl** is now part of the problem.
It is no longer just a “workflow engine with too much process.”
It is also a repo whose own search surface contains enough historical churn to confuse agent retrieval and reinforce stale loops.

---

## Required package changes after this blind pass

1. **Make greenfield end in mandatory audit before handoff.**
2. **Require one bootstrap-proof lane as a first-class success condition.**
3. **Make restart validity depend on deterministic proof, not just contract agreement.**
4. **Break the cyclic coupling between `project-skill-bootstrap` and `opencode-team-bootstrap`.**
5. **Split archives, churn logs, postmortems, and rollout traces out of the main package search surface.**
6. **Treat provenance completeness as mandatory, not optional.**
7. **Reduce template-level governance overlap where review/audit/process-log roles blur.**
8. **Add a first-class `pivot-update` flow for midstream design changes instead of forcing users to compose refine + audit + repair implicitly.**
9. **Promote `environment_bootstrap` and deterministic smoke proof above handoff narration in the hierarchy of truth.**
10. **Reduce the number of package-level surfaces that can explain, summarize, bridge, review, log, or restart the same state.**

---

## Evidence map used in this pass

Live contract / flow:
- `skills/skill-flow-manifest.json`
- `skills/scaffold-kickoff/SKILL.md`
- `skills/scafforge-repair/SKILL.md`
- `skills/ticket-pack-builder/SKILL.md`
- `skills/repo-scaffold-factory/SKILL.md`
- `skills/scafforge-audit/SKILL.md`

Repair execution:
- `skills/scafforge-repair/scripts/run_managed_repair.py`
- `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
- `scripts/validate_scafforge_contract.py`
- `scripts/smoke_test_scafforge.py`

Template-side governance / execution surfaces:
- `skills/repo-scaffold-factory/assets/project-template/.opencode/skills/review-audit-bridge/SKILL.md`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/environment_bootstrap.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts`

Archived diagnosis / churn evidence:
- `scafforgechurnissue/ScafforgeAudits/20260328-131336/manifest.json`
- `out/scafforge audit archive/GPTTalker Logs and Audits/GPTTalkerChurnlogs/20260327-005802/manifest.json`
- `out/scafforge audit archive/GPTTalker Logs and Audits/GPTTalkerChurnlogs/...`
- `scafforgechurnissue/CodexLogs/...`
- `out/scafforge audit archive/Archived Plans/...`

Commit-history evidence reviewed:
- `b4a0cc22894e72caab99223eb2f83a46e2870ae0`
- `e005fba8498d4e89839322dcab93c7af0603ede7`
- `41ad746e22d192f682bf965a09afe1dbc75a09d8`
- `ee6ccf9e34aa7d86fccfb3b46d2cd54f17ca472a`
- `903c22dddff5c77906e0bc53dc90b9b1b1d8ff15`
- `227d4061229203825276fe591fb7bc153c9165f0`
- `e2af6ae5bb1455d8339e3b076818c1b3d0899522`
- `805915de7a7cf7ca0926fa3be269639a17e2815b`
- `058bb1a2b3fdf4f6ea9dfdd734213e2377112866`
- `361ca42673fccc547a149aef6ca68f97bc67dc43`
- `ad9f3f03678ace90a0d351d36b04699b573d3995`

