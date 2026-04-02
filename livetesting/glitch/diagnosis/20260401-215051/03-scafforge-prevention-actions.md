# Scafforge Prevention Actions

## Package Changes Required

### ACTION-001

- source_finding: WFLOW012
- change_target: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- why_it_prevents_recurrence: Use one lease-ownership model everywhere: the team leader claims and releases ticket leases, specialists work under the active lease, and only Wave 0 setup work may claim before bootstrap is ready.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-002

- source_finding: WFLOW013
- change_target: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- why_it_prevents_recurrence: Make `/resume` trust canonical manifest plus workflow state first, keep all restart surfaces derived-only, include `.opencode/state/latest-handoff.md`, and preserve the active open ticket as the primary lane.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-003

- source_finding: read-only-shell-mutation-loophole
- change_target: project-skill-bootstrap and agent-prompt-engineering surfaces
- why_it_prevents_recurrence: Harden generated prompts so read-only roles stay read-only and repo-local review guidance remains advisory.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-004

- source_finding: WFLOW006
- change_target: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- why_it_prevents_recurrence: Harden the team leader prompt so it routes from transition guidance, stops on repeated lifecycle errors, keeps slash commands human-only, and leaves stage artifacts to specialists.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

## Validation and Test Updates

- WFLOW012: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- WFLOW013: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- read-only-shell-mutation-loophole: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- WFLOW006: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

## Documentation or Prompt Updates

- WFLOW012: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

- WFLOW013: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

- read-only-shell-mutation-loophole: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

- WFLOW006: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

## Open Decisions

- None recorded.

