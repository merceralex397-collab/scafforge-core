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
  -> environment bootstrap detection and blocker routing
  -> repo-scaffold-factory:verify-bootstrap-lane
  -> project-skill-bootstrap
  -> opencode-team-bootstrap
  -> agent-prompt-engineering
  -> ticket-pack-builder
  -> repo-scaffold-factory:verify-generated-scaffold
  -> handoff-brief
```

The proof layers inside that sequence are part of the same one-shot pass:

- bootstrap-lane proof must clear VERIFY009-style bootstrap blocker persistence and routing requirements before specialization continues
- continuation proof must clear VERIFY010 execution-surface failures before handoff
- continuation proof must clear VERIFY011 reference-integrity failures before handoff

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
- Environment detection and bootstrap routing are part of that same pass. If missing prerequisites remain, the pass must halt with explicit user-actionable blockers instead of continuing into specialization or handoff.

## Verification scope

- VERIFY009 proves bootstrap blocker state is persisted canonically and that bootstrap cannot be considered ready while unresolved prerequisites remain.
- VERIFY010 proves the generated repo passes the stack-specific execution audit for its detected Tier 1 stack surfaces.
- VERIFY011 proves canonical config, scene, and code reference surfaces do not point at missing files before handoff.
- These checks prove structural integrity and runnable workflow truth. They do not promise bug-free product implementation beyond the generated scaffold and current ticket scope.

## Model-tier contract

- The greenfield pass records `model_tier` as scaffold provenance and uses it to tune prompt density for generated local skills, agents, and commands.
- `model_tier` changes how explicit the prompts are, not whether the flow runs bootstrap, verification, ticketing, or handoff.

## Lifecycle boundaries

- `scafforge-audit` is a later read-only lifecycle skill.
- `scafforge-repair` is a later repair lifecycle skill.
- `scafforge-pivot` is a later change-management lifecycle skill.
- Audit and repair are outside the initial generation cycle.
- Pivot is outside the initial generation cycle.
- Audit and repair are outside the generation cycle.
- If repeated diagnosis packs report the same repair-routed findings and no newer package or process-version change exists, stop the subject-repo audit loop and fix Scafforge first.
- Managed repair may still leave `pending_process_verification` or source follow-up work behind; restart surfaces must report that truthfully instead of claiming immediate development readiness by default.
