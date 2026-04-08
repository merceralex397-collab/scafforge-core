# Live Repo Repair Plan

## Preconditions

- Audit scope stayed non-mutating with respect to product code and workflow state.
- Only the diagnosis pack under `diagnosis/20260328-135857/` is being written.
- This report reconciles the raw script output against:
  - current repo truth
  - `session4.md`
  - current managed workflow implementation
  - prior diagnosis/repair history

## Package Changes Required First

Yes.

Reason:

- the current contradiction is being recreated by the managed package itself
- a new subject-repo repair on the same package would not be durable
- this repo has already completed the “audit -> repair -> verify” loop on the same process-version and still reproduced the same class of weak-agent blockage

## Why Subject-Repo Repair Must Wait

The visible contradiction in this repo is real, but it is downstream of current package defects:

1. `ticket_update` clearing of `pending_process_verification` is blocked by closed-ticket lease enforcement
2. `handoff_publish` still permits explicit contradictory “clean state” overrides
3. restart rendering still lists currently verified tickets as not fully trusted because it does not share `ticket_lookup`'s process-verification truth source

If another repo-local repair ran now, it would only paper over the generated outputs again.

## Safe Repo Repair Actions After Package Work Lands

After Scafforge package fixes are implemented and one fresh `post_package_revalidation` audit confirms the repaired package:

1. refresh the managed workflow surfaces in this subject repo
2. regenerate:
   - `START-HERE.md`
   - `.opencode/state/latest-handoff.md`
   - `.opencode/state/context-snapshot.md`
3. if the package now supports the legal clear path, clear `pending_process_verification` through the supported workflow mutation
4. verify the restart surfaces no longer:
   - claim clean state while canonical pending state remains true
   - list already-verified done tickets as still not fully trusted
5. verify weaker-model restart routing now exposes one legal next move instead of a narration gap

## Unsafe / Intent-Changing Boundary

Do not:

- hand-edit `workflow-state.json`
- hand-edit `tickets/manifest.json`
- perform another custom subject-repo-only patch to the restart prose
- call this repo “clean” based only on empty `affected_done_tickets` while the managed package still republishes contradictory guidance

Those would hide the package defect instead of fixing it.

## Ticket Recommendations

No source-layer follow-up tickets are recommended from this diagnosis run.

The next workspace is the Scafforge dev repo, not this subject repo’s ticket graph.

## Required Next Step

- Manually carry `diagnosis/20260328-135857/` into the Scafforge dev repo.
- Implement the package fixes described in Report 3.
- Return here and run exactly one fresh `post_package_revalidation` audit.
- Only if that revalidation shows package work is no longer the next blocker should `scafforge-repair` be run again.
