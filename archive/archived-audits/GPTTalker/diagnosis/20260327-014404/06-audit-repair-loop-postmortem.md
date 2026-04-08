# Audit + Repair Loop Postmortem

## Executive Summary

The repo did not spend all day blocked by one thing. It spent all day moving through three different states, and Scafforge did not converge on the right one:

1. a real Scafforge workflow defect in `smoke_test`
2. a later fixed workflow defect in smoke scope selection
3. a remaining repo-local blocker that should have been handled as ticket execution plus stale-ticket reconciliation, not more audit/repair churn

`pytest` is not the problem on this Ubuntu/WSL machine. The repo-managed command works:

- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_security.py -q --tb=no` currently runs and fails with 1 real failure
- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py -q --tb=no` currently passes
- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -q --tb=no` currently runs and fails with 6 real failures

The loop happened because Scafforge kept treating the repo as if it still needed more diagnosis or more managed-surface repair, even after the workflow blocker had narrowed to a source/ticket reconciliation problem.

## What Actually Happened

### 1. The first blocker was real Scafforge breakage

The earliest `EXEC-008` smoke artifacts show a genuine Scafforge tool defect:

- `.opencode/state/artifacts/history/exec-008/smoke-test/2026-03-26T17-58-35-000Z-smoke-test.md`
- `.opencode/state/artifacts/history/exec-008/smoke-test/2026-03-26T17-58-56-658Z-smoke-test.md`

Those runs failed before pytest started:

- `Error: ENOENT: no such file or directory, posix_spawn 'UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_security.py -q --tb=no'`
- `Error: ENOENT: no such file or directory, posix_spawn 'UV_CACHE_DIR=/tmp/uv-cache'`

That was a Scafforge bug in smoke override execution, not a repo bug and not a WSL/pytest problem.

### 2. The next blocker was still Scafforge, but different

After the override-launch bug was cleared, `smoke_test` still ran the wrong scope for `EXEC-008`:

- multiple artifacts from `2026-03-26T17-59:27Z` through `2026-03-26T22-33:31Z` ran heuristic commands like `uv run python -m pytest tests/hub/test_security.py`
- that behavior matched the repeated `WFLOW017` findings in the diagnosis packs at `20260327-003826`, `20260327-005715`, `20260327-005802`, and `20260327-005936`

This was also real Scafforge drift. The tool was not treating the ticket acceptance command as canonical smoke scope.

### 3. By 2026-03-27 04:32 UTC, the workflow defect was no longer the main blocker

The latest smoke artifacts show that `smoke_test` was finally using the ticket acceptance command:

- `.opencode/state/artifacts/history/exec-008/smoke-test/2026-03-27T04-32-02-462Z-smoke-test.md`
- `.opencode/state/artifacts/history/exec-008/smoke-test/2026-03-27T04-36-14-727Z-smoke-test.md`

Those runs executed:

- `uv run pytest tests/hub/test_security.py -q --tb=no`

and surfaced one remaining real failure:

- `tests/hub/test_security.py::TestPathTraversal::test_path_traversal_dotdot_rejected`

At that point the workflow should have converged on ordinary repo work. Instead, the system kept orbiting audits.

### 4. The remaining blocker became a stale-ticket problem

Current repo truth does not match the stale follow-up ticket split:

- `tickets/EXEC-008.md` still says the remaining path-scope follow-up is in `EXEC-012`
- `tickets/EXEC-012.md` still claims the problem is `....`, `.../...`, and `foo/./bar`
- current tests say otherwise

Current test reality:

- `tests/hub/test_contracts.py` no longer contains `foo/./bar`; `tests/hub/test_contracts.py -q --tb=no` passes
- `tests/hub/test_security.py` still includes `foo/bar/../../secrets` in the rejection set
- `src/hub/policy/path_utils.py` normalizes that path to an in-bounds repo path, so the current remaining mismatch is different from the one `EXEC-012` describes

That created the circular dependency:

- `EXEC-008` is open and cannot close until its acceptance command passes
- `EXEC-012` depends on `EXEC-008`
- but `EXEC-012` was supposed to fix the test-scope issue blocking `EXEC-008`
- then the failing case changed, yet no Scafforge flow reconciled the ticket split

## Why The Last Five Audits Went In Circles

The last five diagnosis packs were generated on `2026-03-27` at:

- `00:38:26Z` -> `diagnosis/20260327-003826`
- `00:57:15Z` -> `diagnosis/20260327-005715`
- `00:58:02Z` -> `diagnosis/20260327-005802`
- `00:59:36Z` -> `diagnosis/20260327-005936`
- `01:44:04Z` -> `diagnosis/20260327-014404`

There is no newer `repair_history` entry after `2026-03-26T03:37:12.985Z` in `.opencode/meta/bootstrap-provenance.json`. That means these five packs were created without an intervening Scafforge package/process change that would justify repeated re-auditing of the same repo.

The findings also oscillated instead of converging:

- `20260327-003826` repeated `WFLOW017` twice
- `20260327-005715` added `WFLOW010` and `WFLOW012`
- `20260327-005802` dropped `WFLOW010`
- `20260327-005936` dropped `WFLOW012`
- `20260327-014404` dropped the transcript findings and pivoted back to `WFLOW010`

That instability is the core sign of churn: the tooling kept reclassifying the same day’s situation instead of helping the operator decide one next step.

## What Is Wrong With Scafforge

### 1. The churn-stop exists in prose, but did not protect the user

`scafforge-audit` already says:

- repeated same-day diagnosis packs with no package/process change should be treated as churn
- another subject-repo audit should not be recommended in that state

That rule appears in:

- `/home/pc/.codex/skills/scafforge-audit/SKILL.md`
- `/home/pc/.codex/skills/scafforge-audit/scripts/audit_repo_process.py` as `CYCLE002`

But the repo still accumulated five same-day packs, and the latest pack did not surface `CYCLE002`. So the churn-stop is not operationally reliable. It exists on paper, but it did not prevent the loop.

### 2. Scafforge has no stale-follow-up-ticket reconciliation step

This is the biggest gap for this repo.

Scafforge can:

- create follow-up tickets
- reopen tickets
- mark `resolution_state: superseded` in the ticket contract

But there is no explicit audit/repair/ticket-builder rule saying:

- if a follow-up ticket was created from smoke evidence
- and later verification changes the remaining failing case set
- then reconcile the split immediately by superseding, collapsing, or rewriting the stale follow-up ticket

That missing rule is exactly how `EXEC-012` survived after its evidence changed.

### 3. Scafforge does not guard against parent/follow-up circular blockers

There is no enforced rule like:

- a child remediation ticket must not depend on its parent if the child owns the parent’s last remaining acceptance blocker

That should be a hard validation error in ticket creation or audit output. Without it, Scafforge created an impossible routing state:

- parent ticket cannot close until child work lands
- child cannot start until parent closes

### 4. Audit kept surfacing process-state findings after they were no longer the decision-driving issue

`WFLOW008` is real process state, but it was not the reason `EXEC-008` was stuck today. The repo correctly exposes `pending_process_verification: true`. That should have been treated as visible background state, not as a reason to keep recommending repair once managed repair had already cleared.

Similarly, the latest `WFLOW010` report did not help move the repo. Even if there was transient restart-surface drift earlier, by the time of the latest current-state review:

- `repair_follow_on.verification_passed` is `true`
- `repair_follow_on.handoff_allowed` is `true`
- restart surfaces already show `repair_follow_on_required: false`

So the high-value decision was no longer "repair the workflow again." It was "reconcile stale tickets and execute the repo tickets."

### 5. Audit output was not stable enough for repeated-use diagnosis

Across the five packs:

- one pack duplicated `WFLOW017`
- findings appeared and disappeared within minutes
- the latest pack missed the stronger repeated-churn diagnosis and instead revived a weaker restart-surface narrative

That makes the audit output poor as an iterative control system. It can produce true findings, but it did not rank or stabilize them in a way that stopped wasted work.

## What Was Missing From The Skills

### Missing safeguard 1: hard stop after repeated same-day audit churn

Needed rule:

- if same-day diagnosis packs repeat repair-routed findings and there is no newer repair history or process-version change, stop the subject-repo audit loop and require package work or direct ticket execution

Current state:

- this idea exists in `scafforge-audit`
- it is not reliably turning into the top-level outcome that stops the operator

### Missing safeguard 2: stale remediation ticket reconciliation

Needed rule:

- after any fresh smoke or full-suite verification, compare the current failing acceptance cases against any open remediation follow-up tickets created from earlier evidence
- if the evidence no longer matches, supersede or rewrite the stale follow-up before further routing

Current state:

- `ticket-pack-builder` supports `superseded`
- no skill made that the mandatory next step here

### Missing safeguard 3: circular dependency validation for remediation tickets

Needed rule:

- reject or flag any ticket graph where a child follow-up ticket depends on the still-open parent while also owning the parent’s remaining required smoke/fix scope

Current state:

- Scafforge has dependency fields
- it does not appear to validate this contradiction during remediation-follow-up creation

### Missing safeguard 4: “repair is done, resume repo work” convergence rule

Needed rule:

- once repair verification reports only `EXEC*` source work plus correctly surfaced `pending_process_verification`, stop routing to repair and resume ordinary ticket execution

Current state:

- `scafforge-repair/SKILL.md` says this in prose
- the actual day’s workflow did not converge there

### Missing safeguard 5: transcript-vs-current-state reconciliation that preserves the current blocker

Needed rule:

- when transcript findings were true earlier but later current-state verification narrows the blocker, the report must say the workflow defects were historical and the remaining blocker is now repo-local

Current state:

- audits kept alternating between transcript-heavy findings and current-state findings
- they did not consistently collapse those into one final decision

## What Needs Fixing In Scafforge

### Package-side fixes

1. Make `CYCLE002` a hard top-level diagnosis outcome.
2. Add a ticket-graph audit that detects parent/child circular blockers in remediation follow-ups.
3. Add stale-follow-up reconciliation to `ticket-pack-builder` remediation-follow-up mode.
4. Make audit compare current failing acceptance commands against open follow-up tickets created from older smoke evidence.
5. Downgrade correctly surfaced `WFLOW008` from repair-driving output to informational state when it is not the active blocker.
6. Require repeated-pack dedupe and stability so the same finding is not emitted twice or oscillate without a repo change.
7. Prefer “resume repo work now” once managed repair is complete and only source-layer tickets remain.

### Repo-side fixes

1. Collapse or supersede `EXEC-012`.
2. Update `EXEC-008` so its summary matches the current remaining failing case.
3. Finish `EXEC-008`, then `EXEC-009`, then `EXEC-010`.
4. Do not run another subject-repo audit until either:
   - Scafforge package logic changes, or
   - the repo state changes materially enough to invalidate this postmortem

## Bottom Line

This was not one endless mystery. The day broke into:

- a real Scafforge smoke-launch bug
- a real Scafforge smoke-scope bug
- then a stale-ticket circular dependency that Scafforge had no reconciliation rule for

The repo is now blocked mainly by stale ticket structure plus remaining source work, not by missing pytest support on WSL and not by an unfinished repair-follow-on state.
