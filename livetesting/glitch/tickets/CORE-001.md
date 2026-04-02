# CORE-001: Implement the baseline player controller

## Summary

Build the stable movement baseline for Glitch, including run, jump, wall interaction, dash, coyote time, and input buffering tuned for readable mobile play.

## Wave

1

## Lane

gameplay-core

## Parallel Safety

- parallel_safe: false
- overlap_risk: medium

## Stage

closeout

## Status

done

## Trust

- resolution_state: done
- verification_state: trusted
- source_ticket_id: None
- source_mode: None

## Depends On

SETUP-001, SYSTEM-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] Player movement supports left-right movement, jump, wall slide, wall jump, and dash
- [ ] Coyote time and jump buffering are implemented or explicitly rejected with evidence
- [ ] Movement constants are centralized for later tuning
- [ ] Validation demonstrates the controller loads and runs inside the Godot project

## Artifacts

- plan: .opencode/state/artifacts/history/core-001/planning/2026-04-01T20-34-58-689Z-plan.md (planning) - Planning artifact for CORE-001 covering CharacterBody2D movement model, Input action-based input handling, centralized PlayerDefaults resource, state machine with 6 states (IDLE/RUN/JUMP/FALL/WALL_SLIDE/DASH), coyote time (100ms), jump buffering (120ms), wall slide/wall jump, dash without invincibility, and headless validation plan.
- implementation: .opencode/state/artifacts/history/core-001/implementation/2026-04-01T20-43-32-779Z-implementation.md (implementation) - Implementation of baseline player controller with CharacterBody2D, state machine (IDLE/RUN/JUMP/FALL/WALL_SLIDE/DASH), coyote time, jump buffering, wall slide, wall jump, and dash mechanics. Creates PlayerDefaults resource for centralized constants.
- review: .opencode/state/artifacts/history/core-001/review/2026-04-01T20-46-05-196Z-review.md (review) - Code review for CORE-001: baseline player controller. PASS with medium robustness recommendation on wall detection null check. All acceptance criteria met.
- qa: .opencode/state/artifacts/history/core-001/qa/2026-04-01T20-47-59-262Z-qa.md (qa) - QA artifact for CORE-001: All 6 checks passed (file existence, Godot headless startup, headless import, PlayerDefaults resource, state machine enum, coyote time and jump buffer).
- smoke-test: .opencode/state/artifacts/history/core-001/smoke-test/2026-04-01T20-48-38-034Z-smoke-test.md (smoke-test) - Deterministic smoke test passed.

## Notes


