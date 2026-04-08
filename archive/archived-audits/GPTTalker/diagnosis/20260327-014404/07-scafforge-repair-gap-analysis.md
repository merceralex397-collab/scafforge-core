# Scafforge Repair Gap Analysis

## Summary

`scafforge-repair` did part of the job, but not the part that actually unblocked this repo.

What it did cover:

- deterministic managed-surface refresh
- restart-surface regeneration
- provenance updates in `.opencode/meta/bootstrap-provenance.json`
- execution record updates in `.opencode/meta/repair-execution.json`
- post-repair verification

What it did not cover:

- project-specific follow-on regeneration
- stale follow-up ticket reconciliation
- the circular `EXEC-008` / `EXEC-012` dependency
- the remaining source-layer fixes in `tests/hub/test_security.py`, `src/node_agent/executor.py`, and `src/shared/logging.py`
- advancing the repo to the next real open ticket after those fixes landed

That is why the repair run exited with required follow-on stages still open, and why the repo only became green after the manual remediation execution plan was applied.

## What The Repair Skill Actually Did

The repair runner completed one stage:

- `deterministic-refresh`

It replaced managed workflow surfaces and rewrote restart surfaces, then reran verification. Its execution record reported:

- `SKILL001`
- `EXEC003`

and left:

- `repair_follow_on.verification_passed: false`
- `repair_follow_on.handoff_allowed: false`

It explicitly said these stages were still required but not run:

- `project-skill-bootstrap`
- `opencode-team-bootstrap`
- `agent-prompt-engineering`
- `ticket-pack-builder`
- `handoff-brief`

So the repair skill behaved like a deterministic workflow refresher plus verifier, not a full end-to-end repo unblocking flow.

## Why It Did Not Cover More

### 1. By contract, `scafforge-repair` is not a source-fix skill

Its own boundary is:

- repair managed workflow surfaces
- route source bugs into ticketing
- do not fix product code under the label of repair

That is why it did not touch:

- `tests/hub/test_security.py`
- `src/node_agent/executor.py`
- `src/shared/logging.py`

Those changes were necessary to get from 6 failing tests to 127 passing tests, but they are outside the repair skill's intended safe boundary.

### 2. The current runner only does deterministic refresh by itself

The skill document says a complete repair may need:

- `project-skill-bootstrap`
- `opencode-team-bootstrap`
- `agent-prompt-engineering`
- `ticket-pack-builder`
- `handoff-brief`

But the public runner did not invoke those stages automatically here. It only recorded them as `required_not_run`.

So there is a design gap between:

- what the skill narrative describes as a full repair contract

and

- what `run_managed_repair.py` actually executes in one shot

In practice, the runner is not a full repair orchestrator. It is a deterministic refresh plus verification pass that emits more required work.

### 3. It has no stale follow-up ticket reconciliation step

This repo needed:

- `EXEC-012` to be superseded
- stale references to `EXEC-012` removed from `EXEC-007`, `EXEC-008`, board, manifest, and restart surfaces

`scafforge-repair` did not do that because the current repair flow does not include a rule like:

- compare current failing acceptance cases to open remediation follow-up tickets
- if the follow-up ticket no longer matches current evidence, supersede or rewrite it immediately

Without that rule, `EXEC-012` survived even though its failure description was stale.

### 4. It did not solve the circular dependency because it only routed follow-up

The actual blocker was not just "workflow drift." It was:

- `EXEC-008` still open
- `EXEC-012` blocked behind `EXEC-008`
- `EXEC-012` supposed to own the remaining failing scope

The repair skill did not break that loop because it does not currently validate or rewrite remediation ticket graphs for contradictions like:

- child ticket depends on parent
- child ticket owns the parent's last remaining acceptance blocker

That needed manual canonical ticket surgery.

### 5. It re-blocked the restart surfaces on process follow-on instead of converging on repo work

After the deterministic refresh, the runner regenerated `START-HERE.md` and related restart surfaces to say:

- `handoff_status: repair follow-up required`
- next required stage: `project-skill-bootstrap`

That is mechanically consistent with the runner's own state, but it still did not help the repo finish `EXEC-008`, `EXEC-009`, and `EXEC-010`.

So the repair skill preserved its own incomplete-repair truth, but it did not converge on the repo's actual shortest path to green.

## What Manual Remediation Covered That Repair Did Not

The manual execution plan covered four things the repair skill left behind:

1. superseding `EXEC-012` and removing stale references
2. fixing the remaining `EXEC-008` test expectation
3. fixing the `EXEC-009` UTC timestamp bug
4. fixing the `EXEC-010` redaction semantics

After those changes:

- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_security.py -q --tb=no` passed
- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/node_agent/test_executor.py -q --tb=no` passed
- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/shared/test_logging.py -q --tb=no` passed
- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -q --tb=no` passed with `127 passed`

That result required source changes and ticket-graph reconciliation, which the repair skill did not and should not do automatically under its current contract.

## Bottom Line

`scafforge-repair` did not fail in one simple way. It stopped exactly at the edge of its current implementation and contract:

- it refreshed managed workflow surfaces
- it verified them
- it emitted more required follow-on work

What it did not do was the work this repo actually needed next:

- reconcile stale remediation tickets
- break the circular dependency
- fix remaining source failures

So the repair skill was necessary for workflow refresh, but insufficient for repo recovery. The repo only moved once manual remediation executed the source-side plan that the repair skill intentionally left out.
