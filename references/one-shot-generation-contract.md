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
  -> project-skill-bootstrap
  -> opencode-team-bootstrap
  -> agent-prompt-engineering
  -> ticket-pack-builder
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

## Lifecycle boundaries

- `scafforge-audit` is a later read-only lifecycle skill.
- `scafforge-repair` is a later repair lifecycle skill.
- Audit and repair are outside the initial generation cycle.
- Audit and repair are outside the generation cycle.
