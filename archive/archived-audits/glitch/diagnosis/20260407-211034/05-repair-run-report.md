# Repair Run Report

## Scope

- subject repo: `/home/pc/projects/Scafforge/livetesting/glitch`
- package repo: `/home/pc/projects/Scafforge`
- package commit used for repair: `b624ca1a5a37bf99b8ff651b34fab6ba3f449c8b`
- original repair basis: `diagnosis/20260402-144600`
- report purpose: explain what happened during the full repair attempt, what was actually fixed, and why the repo still stopped in a fail-closed state

## Executive Summary

The subject repo did go through a real managed repair pass.

The repair was not a no-op:

- deterministic managed-surface refresh ran successfully
- the repo was moved onto the current Scafforge package contract
- a ticket-graph contradiction that the new workflow now rejects was corrected
- repo-local skill and prompt surfaces were refreshed
- the required repair follow-on stages were explicitly recorded for the current repair cycle

The repair still did not converge to a clean state.

The final stop condition is not "repair never ran". The final stop condition is:

- managed repair follow-on is complete for the current cycle
- post-repair verification still fails closed
- the latest diagnosis now says package-side work is required before another subject-repo repair run

That package-side blocker is `CYCLE002`.

## What Actually Happened

### 1. Initial state

The subject repo was still carrying Scafforge provenance from an older package commit:

- subject repo template commit: `d3db92630b350c6ab318b7fe0a9689655024f216`
- current package repo head during this repair: `b624ca1a5a37bf99b8ff651b34fab6ba3f449c8b`

That meant the repo needed a full managed refresh against the rewritten package contract.

### 2. First repair blocker: new workflow tool inventory

The new package repair runner failed closed because the rewritten package now expects a repo-local workflow tool that the subject repo did not have yet:

- missing tool: `.opencode/tools/repair_follow_on_refresh.ts`

That tool was added so the repair runner could continue under the current package contract.

### 3. Second repair blocker: ticket graph invariant

Once the repair runner advanced further, it failed on a repo-level invariant in the rewritten workflow library:

- `RELEASE-001` named `ANDROID-001` as both `source_ticket_id` and `depends_on`

Under the new contract, a split-scope child ticket may not also duplicate the same relationship in `depends_on`.

That contradiction was fixed in:

- `tickets/manifest.json`
- `tickets/RELEASE-001.md`

Specifically:

- `source_ticket_id: ANDROID-001` was kept
- `depends_on: ["ANDROID-001"]` was removed

### 4. Deterministic managed repair succeeded

After those blockers were cleared, the public repair runner completed the deterministic refresh phase.

That phase refreshed managed surfaces including:

- `opencode.jsonc`
- `.opencode/tools`
- `.opencode/lib`
- `.opencode/plugins`
- `.opencode/commands`
- scaffold-managed `.opencode/skills`
- `docs/process/workflow.md`
- `docs/process/tooling.md`
- `docs/process/model-matrix.md`
- `docs/process/git-capability.md`
- `START-HERE.md`
- `.opencode/state/context-snapshot.md`
- `.opencode/state/latest-handoff.md`

The runner then opened a new repair-follow-on cycle and required these stages:

- `project-skill-bootstrap`
- `opencode-team-bootstrap`
- `agent-prompt-engineering`

### 5. Follow-on regeneration was performed

Those follow-on surfaces were updated:

- repo-local skills:
  - `.opencode/skills/project-context/SKILL.md`
  - `.opencode/skills/repo-navigation/SKILL.md`
  - `.opencode/skills/stack-standards/SKILL.md`
- team and delegation surfaces:
  - `.opencode/agents/glitch-team-leader.md`
  - `.opencode/agents/glitch-implementer.md`
  - `.opencode/agents/glitch-docs-handoff.md`
  - `docs/AGENT-DELEGATION.md`

Completion artifacts were also written under:

- `.opencode/state/artifacts/history/repair/project-skill-bootstrap-completion.md`
- `.opencode/state/artifacts/history/repair/opencode-team-bootstrap-completion.md`
- `.opencode/state/artifacts/history/repair/agent-prompt-engineering-completion.md`

The three stages were then explicitly recorded with:

- `record_repair_stage_completion.py`

### 6. Why the process became confusing

Each normal rerun of the full public repair runner opened a fresh repair cycle.

That means the cycle id changed on each rerun, which caused two side effects:

- current-cycle completion artifacts immediately became stale-cycle artifacts
- follow-on tracking state was reset for the new cycle before the previously recorded completions could satisfy it

To avoid that loop, verification had to be rerun with:

- `--skip-deterministic-refresh`

That preserved the already-open repair cycle and allowed the recorded follow-on completions to be recognized.

## Final Verification Outcome

The final verification still failed closed.

The current state is:

- required repair follow-on stages: completed for the current cycle
- `repair_follow_on.outcome`: still `managed_blocked`
- `handoff_allowed`: `false`

The current canonical state files show that:

- `.opencode/state/workflow-state.json`
- `.opencode/meta/repair-follow-on-state.json`

The remaining blocker in canonical state is:

- `Post-repair verification failed repair-contract consistency checks: placeholder_local_skills_survived_refresh.`

## Remaining Findings

The latest diagnosis pack still reports these findings:

### SKILL001

Meaning:

- the verifier still considers at least one repo-local skill to retain generic or placeholder guidance

Observed file:

- `.opencode/skills/stack-standards/SKILL.md`

Important detail:

- the file was rewritten during this repair run, but the package verifier still flags it
- this may be a package-side audit heuristic problem rather than a pure subject-repo content failure

### REF-003

Meaning:

- source imports still reference missing local modules

Observed file:

- `.opencode/node_modules/zod/src/index.ts`

This is a real subject-repo or vendored-surface problem and remains a source follow-up item.

### SESSION001

Meaning:

- the supplied session transcript shows a reasoning failure where later evidence was gathered but the final summary still outran what the executed commands actually proved

Observed file:

- `glitch1.md`

This is transcript-backed historical process evidence, not a new code edit made by this repair run.

### SESSION003

Meaning:

- the supplied session transcript shows bypass-seeking or soft dependency-override behavior instead of strict lifecycle handling

Observed file:

- `glitch1.md`

This is also transcript-backed historical process evidence.

### CYCLE002

This is the most important final blocker.

Meaning:

- repeated diagnosis packs are re-reporting the same repair-routed findings without any intervening package or process-version change

Why it matters:

- once this finding appears, the latest diagnosis explicitly says the next move is package-side work, not another subject-repo repair rerun

In other words:

- the system is now saying "stop rerunning repair against this repo until the package changes again"

## Why Repair Stopped

Repair stopped for the correct fail-closed reason.

The stop condition is not:

- "the repo was never refreshed"
- "the follow-on stages were never run"
- "the repair runner crashed before doing any work"

The actual stop condition is:

1. managed repair did run
2. follow-on regeneration did run
3. verification still reported residual findings
4. repeated reruns then triggered `CYCLE002`
5. `CYCLE002` changes the legal next move from "repair the subject repo again" to "do package work first"

## Exact Files Touched During This Repair Session

Direct subject-repo edits made during this repair session:

- `.opencode/tools/repair_follow_on_refresh.ts`
- `tickets/manifest.json`
- `tickets/RELEASE-001.md`
- `.opencode/skills/project-context/SKILL.md`
- `.opencode/skills/repo-navigation/SKILL.md`
- `.opencode/skills/stack-standards/SKILL.md`
- `.opencode/agents/glitch-team-leader.md`
- `.opencode/agents/glitch-implementer.md`
- `.opencode/agents/glitch-docs-handoff.md`
- `docs/AGENT-DELEGATION.md`
- `.opencode/state/artifacts/history/repair/project-skill-bootstrap-completion.md`
- `.opencode/state/artifacts/history/repair/opencode-team-bootstrap-completion.md`
- `.opencode/state/artifacts/history/repair/agent-prompt-engineering-completion.md`

Files updated by the package repair runner during deterministic refresh and verification:

- `.opencode/lib/workflow.ts`
- `.opencode/plugins/stage-gate-enforcer.ts`
- `.opencode/tools/handoff_publish.ts`
- `.opencode/tools/ticket_create.ts`
- `.opencode/meta/bootstrap-provenance.json`
- `.opencode/meta/repair-execution.json`
- `.opencode/meta/repair-follow-on-state.json`
- `.opencode/state/workflow-state.json`
- `.opencode/state/context-snapshot.md`
- `.opencode/state/latest-handoff.md`
- `START-HERE.md`
- `docs/process/model-matrix.md`

Additional generated outputs:

- `.opencode/state/repair-backups/`
- `.opencode/state/repair-escalation.json`
- `diagnosis/20260407-210653/`
- `diagnosis/20260407-210926/`
- `diagnosis/20260407-211001/`
- `diagnosis/20260407-211034/`

## Current Canonical State

The repo now truthfully says:

- active ticket: `ANDROID-001`
- stage: `planning`
- `pending_process_verification: true`
- repair follow-on stage records exist and are completed for the current cycle
- repair still remains blocked because verification did not clear the contract

See:

- `.opencode/state/workflow-state.json`
- `.opencode/meta/repair-follow-on-state.json`

## Recommended Next Move

Do not run another subject-repo repair cycle immediately.

The current latest diagnosis explicitly says the next move is package-side:

1. carry this diagnosis pack into the Scafforge package repo
2. address the package-side issue that allows repeated repair-routed findings to churn without a process-version or package change
3. likely review the audit or verification logic behind:
   - `SKILL001`
   - cycle handling that triggered `CYCLE002`
4. after package-side changes land, run one fresh audit on this subject repo
5. only then run another subject-repo repair cycle if the fresh audit still requires it

## Bottom Line

The repair did not fail because nothing happened.

It failed because:

- the repo needed a real managed refresh
- that refresh exposed and corrected one ticket-graph defect
- the rewritten package required explicit follow-on regeneration work
- that follow-on work was completed
- verification still found residual issues
- repeated reruns crossed the threshold into `CYCLE002`
- once `CYCLE002` appeared, the legal next move became package work first

That is the correct stop point under the current Scafforge contract.
