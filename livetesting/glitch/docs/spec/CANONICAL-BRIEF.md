# Canonical Brief

## 1. Project Summary

Glitch is a Godot-based Android 2D action-platformer set inside a collapsing digital simulation where hazards, physics, and room rules can mutate as the world corrupts. This repo exists to scaffold and execute the first playable build of that concept through a deterministic OpenCode workflow, starting with a vertical slice that proves mobile-friendly platforming, readable glitch telegraphing, and a strong corrupted-simulation identity.

## 2. Goals

- Deliver a strong core platforming experience on Android touch controls.
- Make instability and unpredictability the defining gameplay feature through a readable glitch system.
- Build a memorable visual and narrative identity around digital corruption, simulation failure, and adaptation.
- Keep random changes tense and surprising without feeling unfair or unreadable.
- Support staged implementation from core movement through content and polish waves.
- Produce a full Scafforge-generated repo that is ready for first-development handoff.

## 3. Non-Goals

- Do not build a precision speedrunning platformer tuned for extreme punishment.
- Do not scope the project as a loot-heavy roguelike with deep permanent build combinations.
- Do not turn the game into a dialogue-heavy RPG with inventory complexity.
- Do not include multiplayer.
- Do not make combat the primary verb over platforming and survival.

## 4. Constraints

- Platform target is Android.
- Engine is Godot.
- Camera and level perspective are side-on 2D.
- Core controls must stay readable and forgiving on touch devices.
- Baseline movement feel must be stable before glitch modifiers are applied.
- Glitch events must be telegraphed and curated to preserve fairness.
- Narrative framing should justify mechanics through simulation corruption, not arbitrary randomness.
- Generated repo must remain OpenCode-oriented and follow the Scafforge one-cycle greenfield workflow.
- Destination path is `/home/pc/projects/Scafforge/livetesting/glitch`.
- Project slug is `glitch`.
- Agent prefix is `glitch`.

## 5. Required Outputs

- `docs/spec/CANONICAL-BRIEF.md` with resolved blocking decisions and backlog readiness.
- Full generated scaffold including `README.md`, `AGENTS.md`, `START-HERE.md`, `opencode.jsonc`, `docs/`, `tickets/`, and `.opencode/`.
- Project-specific `.opencode/agents/`, `.opencode/skills/`, commands, and workflow docs tailored to a Godot Android platformer.
- Bootstrap-lane verification proof and final immediate-continuation verification proof from `verify_generated_scaffold.py`.
- Initial ticket backlog that starts with environment/bootstrap setup and then moves into core platforming, game-system, and content waves.
- Restart surfaces aligned with canonical workflow and ticket state.

## 6. Tooling and Model Constraints

- Engine/runtime: Godot for Android game development.
- Host workflow: Scafforge-generated OpenCode repo operating layer.
- Model provider: `minimax-coding-plan`
- Planner model: `MiniMax-M2.7`
- Implementer model: `MiniMax-M2.7`
- Utility model: `MiniMax-M2.7`
- Stack label: `godot-android-2d`
- MiniMax 2.7 guidance should prefer explicit, bounded asks with executable evidence and deterministic workflow gates.

## 7. Canonical Truth Map

- Durable project facts and scope: `docs/spec/CANONICAL-BRIEF.md`
- Machine-readable queue state: `tickets/manifest.json`
- Human-readable queue board: `tickets/BOARD.md`
- Transient workflow and bootstrap state: `.opencode/state/workflow-state.json`
- Proof and execution artifacts: `.opencode/state/artifacts/`
- Scaffold provenance: `.opencode/meta/bootstrap-provenance.json`
- Derived restart surfaces: `START-HERE.md`, `.opencode/state/context-snapshot.md`, `.opencode/state/latest-handoff.md`

## 8. Blocking Decisions

Resolved decision packet:

- Destination path: `/home/pc/projects/Scafforge/livetesting/glitch`
- Project slug: `glitch`
- Agent prefix: `glitch`
- Model provider: `minimax-coding-plan`
- Planner model: `MiniMax-M2.7`
- Implementer model: `MiniMax-M2.7`
- Utility model: `MiniMax-M2.7`

## 9. Non-Blocking Open Questions

- Exact Godot major/minor version baseline.
- Whether a later C# path is desired instead of the current GDScript assumption.
- Whether the first milestone stops at a vertical slice or includes a deeper campaign foundation.
- Whether multiple endings and richer meta-progression should remain stretch goals.
- Whether the protagonist should stay unnamed during the first playable slice.

## 10. Backlog Readiness

Backlog generation can proceed now. The design document is strong enough to define implementation-ready early waves for environment setup, Godot project architecture, baseline movement, glitch telegraphing and event pooling, room/checkpoint structure, and a Startup Sector vertical slice. The remaining open questions are real but do not block the first execution wave; they should be tracked as assumptions or later tickets instead of preventing scaffold completion.

## 11. Acceptance Signals

- The generated repo clearly identifies one legal first move: bootstrap the environment, then re-run ticket lookup.
- The scaffold verifies both the bootstrap lane and immediate continuation contract successfully.
- Generated docs, tools, prompts, and workflow surfaces agree on stage order and smoke-test ownership.
- The local skill pack and agent team are project-specific to a Godot Android platformer rather than template-generic.
- The initial backlog is implementation-ready for a vertical-slice-first development path and records unresolved design choices explicitly instead of guessing.

## 12. Assumptions

- The project title remains `Glitch`.
- GDScript is the default implementation language unless canonical truth later changes it.
- Early development should target a playable Startup Sector vertical slice before broad content expansion.
- The first implementation waves should establish reusable architecture for later zones, bosses, and advanced abilities rather than hardcoding a one-off prototype.
