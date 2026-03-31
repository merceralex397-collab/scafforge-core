# One-Shot Generation Contract

Scafforge generation is a one-shot lifecycle.

## Public entrypoint

`scaffold-kickoff` is the only public generation entrypoint.
There is one public generation entrypoint: `scaffold-kickoff`.

## Greenfield contract

A greenfield run follows this exact sequence:

```text
scaffold-kickoff
  -> spec-pack-normalizer
  -> repo-scaffold-factory
  -> repo-scaffold-factory:verify-bootstrap-lane
  -> project-skill-bootstrap
  -> opencode-team-bootstrap
  -> agent-prompt-engineering
  -> ticket-pack-builder
  -> repo-scaffold-factory:verify-generated-scaffold
  -> handoff-brief
```

## Decision handling

- Generation allows one batched blocking-decision round.
- The blocking-decision packet must be written down and resolved before generation continues past `spec-pack-normalizer`.
- The greenfield path must not proceed with unresolved blocking decisions.

## Same-session completion

- After the blocking-decision round, generation completes in one uninterrupted same-session generation pass.
- The host agent must complete every downstream greenfield generation skill in the same session.
- No second Scafforge generation pass is required before development begins.
- Greenfield completion requires immediate continuation proof, not only surface agreement.
- That proof must complete before handoff publication.

## Lifecycle boundaries

- `scafforge-audit` is a later read-only lifecycle skill.
- `scafforge-repair` is a later repair lifecycle skill.
- `scafforge-pivot` is a later change-management lifecycle skill.
- Audit and repair are outside the initial generation cycle.
- Pivot is outside the initial generation cycle.
- Audit and repair are outside the generation cycle.
- If repeated diagnosis packs report the same repair-routed findings and no newer package or process-version change exists, stop the subject-repo audit loop and fix Scafforge first.
- Managed repair may still leave `pending_process_verification` or source follow-up work behind; restart surfaces must report that truthfully instead of claiming immediate development readiness by default.
