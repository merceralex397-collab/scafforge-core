# Scafforge Prevention Actions

## Package Changes Required First

Yes.

This audit identifies package defects in the managed workflow contract itself, not only subject-repo drift.
Do not run another subject-repo repair from this pack until the Scafforge dev repo is updated and a single fresh `post_package_revalidation` audit is completed afterward.

## Required Package Actions

### ACTION-001 — Allow legal workflow-level clearing of `pending_process_verification`

- Change target:
  - stage-gate enforcement for `ticket_update`
  - possibly `ticket_update` mutation ownership rules
- Problem to fix:
  - clearing `pending_process_verification` is currently modeled as a workflow-level mutation
  - the stage gate still requires a target-ticket write lease
  - the ticket claim path rejects closed tickets
  - the legal clear path can therefore become unreachable on a closed repo
- Prevention goal:
  - when a `ticket_update` call only mutates workflow-level `pending_process_verification`, and the canonical affected-done-ticket set is empty, the managed workflow must expose one reachable legal path
- Validation:
  - regression fixture where:
    - active ticket is done and closed
    - `affected_done_tickets` is empty
    - `pending_process_verification` is still true
  - require the clear operation to succeed through the supported workflow path without reopening or claiming the closed ticket

### ACTION-002 — Make `handoff_publish` reject contradictory explicit `next_action` overrides

- Change target:
  - `.opencode/lib/workflow.ts::validateHandoffNextAction`
  - `handoff_publish` contract tests
- Problem to fix:
  - explicit handoff prose currently bypasses canonical restart truth too easily
  - the validator does not reject “system is clean / all complete” claims while canonical process verification still remains pending
- Prevention goal:
  - explicit overrides must not be able to claim a cleaner state than canonical workflow state supports
- Validation:
  - fixture where `pending_process_verification: true`
  - `handoff_publish(next_action="All tickets complete and verified... clean state")`
  - require a blocker instead of publishing the override

### ACTION-003 — Recompute restart trust exposure from process-verification truth, not raw `verification_state`

- Change target:
  - `.opencode/lib/workflow.ts::renderStartHere`
  - any helper used by `START-HERE.md`, `.opencode/state/latest-handoff.md`, and `.opencode/state/context-snapshot.md`
- Problem to fix:
  - `done_but_not_fully_trusted` is currently derived from `verification_state`
  - `ticketNeedsProcessVerification()` already uses a richer rule that recognizes current backlog-verification artifacts
  - the restart surfaces therefore continue to report stale distrust after verification is already complete
- Prevention goal:
  - restart surfaces must use the same truth source as `ticket_lookup.process_verification`
- Validation:
  - fixture where 30+ done tickets still have `verification_state: suspect` but also have current `backlog-verification` artifacts
  - require restart surfaces to stop listing them as currently untrusted for process-verification purposes

### ACTION-004 — Harden transcript-backed audit detection for package-managed contradiction cycles

- Change target:
  - `scafforge-audit` script and reconciliation guidance
- Problem to fix:
  - the raw script still emitted `0 findings` on this repo
  - it missed both the restart contradiction and the package-managed recurrence pattern
- Prevention goal:
  - repeated post-repair contradiction cycles on the same process-version should be promoted to package-first findings, not re-labeled as clean
- Validation:
  - add a fixture with:
    - prior clean post-repair pack
    - no new process-version change
    - later transcript showing the same contradiction reproduced by managed tools
  - require the audit to emit a package-first diagnosis

### ACTION-005 — Tighten team-leader closeout guidance for weaker-model behavior

- Change target:
  - team-leader prompt
  - restart-surface / handoff examples
- Problem to fix:
  - weaker models still infer that restart prose may narrate around canonical blockers once “the real work” seems complete
- Prevention goal:
  - force the model toward only two legal handoff outcomes:
    - canonical flag cleared and restart surfaces say cleared
    - canonical flag still true and restart surfaces continue to say pending
- Validation:
  - add a closeout example where the agent must refuse to publish “clean state” prose while canonical pending state remains true

## Package Work Boundary

- This is no longer “package hardening would be nice.”
- This audit shows the current managed package is the mechanism that recreates the contradiction.
- Therefore `package_work_required_first` is now `true`.

## Subject Repo Boundary

- Do not run another normal `scafforge-repair` first from this pack.
- First:
  - carry this diagnosis pack into the Scafforge dev repo
  - land the package fixes above
  - return to this subject repo
  - run exactly one `post_package_revalidation` audit
- Only after that fresh revalidation should the next subject-repo repair be considered.
