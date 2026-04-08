# Report 2: Scafforge Process Failures

This report maps validated issues back to Scafforge-owned skills, contracts, templates, or generated surfaces.

## WFLOW010

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are not being regenerated from `tickets/manifest.json` plus `.opencode/state/workflow-state.json` after workflow mutations or managed repair, leaving bootstrap, repair-follow-on, verification, lane-lease, or active-ticket state stale.
- Safer target pattern: Regenerate `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` from canonical manifest/workflow state after every workflow save, compute handoff readiness from bootstrap plus repair-follow-on plus verification state in one shared contract, and fail repair verification if any derived restart surface drifts.

## WFLOW008

- Surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- Root cause: The workflow contract changed, but the repo is still hiding, overstating, or deadlocking the pending backlog-verification state. That lets restart surfaces imply readiness before historical trust is restored, or leaves the workflow flag stranded after the affected done-ticket set is already empty.
- Safer target pattern: Keep `pending_process_verification` visible, route the backlog verifier across the affected done-ticket set, expose `ticket_reverify` as the legal trust-restoration path, and when that affected set is empty leave a direct legal clear path for `pending_process_verification = false` instead of implying the repo is already clean or leaving the flag stranded.

