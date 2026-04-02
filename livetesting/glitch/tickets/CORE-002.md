# CORE-002: Build the glitch event system with fairness guardrails

## Summary

Implement the first pass of the glitch runtime so physics or level-state mutations can be triggered from curated pools with explicit telegraphs and safe recovery expectations.

## Wave

1

## Lane

gameplay-systems

## Parallel Safety

- parallel_safe: false
- overlap_risk: medium

## Stage

qa

## Status

qa

## Trust

- resolution_state: open
- verification_state: suspect
- source_ticket_id: None
- source_mode: None

## Depends On

SETUP-001, SYSTEM-001, CORE-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] At least one telegraphed glitch event from each planned category can be represented by the runtime or content schema
- [ ] The system separates baseline movement from temporary glitch modifiers
- [ ] High-impact glitch events expose a warning or anticipation surface
- [ ] Validation covers event triggering without breaking normal project startup

## Artifacts

- plan: .opencode/state/artifacts/history/core-002/planning/2026-04-01T20-53-20-558Z-plan.md (planning) - Planning artifact for CORE-002: Defines three glitch event categories (Physics/Hazard/Room Logic), two-phase telegraph system (warning + active), layered warning surfaces, modifier overlay pattern for separation of concerns, curated room-tagged glitch pools, integration with existing GlitchState autoload via signals, and validation plan covering headless startup, resource load, and modifier separation.
- implementation: .opencode/state/artifacts/history/core-002/implementation/2026-04-01T21-01-24-030Z-implementation.md (implementation) - Implemented glitch event system with telegraph phase, modifier overlay pattern, and 11 example events across 3 categories (PHYSICS/HAZARD/ROOM_LOGIC). All classes registered successfully with Godot.
- review: .opencode/state/artifacts/history/core-002/review/2026-04-01T21-06-05-655Z-review.md (review) [superseded] - Review for CORE-002: Two blockers found - modifier integration gap (PlayerController never queries modifiers) and GlitchState.glitch_warning signal never emitted. Implementation creates structure but does not affect gameplay or warn players.
- review: .opencode/state/artifacts/history/core-002/review/2026-04-01T21-18-36-460Z-review.md (review) - Updated review for CORE-002: Both blockers resolved. Physics modifier queries verified (25 refs), emit_warning() signal chain complete. PASS.
- qa: .opencode/state/artifacts/history/core-002/qa/2026-04-01T21-23-54-304Z-qa.md (qa) - QA artifact for CORE-002: Validation checks completed. FAIL - GlitchEventManager never initialized, GlitchPhysicsModifier not accessible at runtime, telegraph UI not connected.

## Notes


