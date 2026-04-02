# CORE-001 Planning Artifact

## Ticket
**CORE-001**: Implement the baseline player controller

## Stage
planning

## Overview

This plan establishes the stable movement baseline for Glitch, covering left-right movement, jump, wall slide, wall jump, and dash. All movement constants are centralized for later tuning. Coyote time and jump buffering are implemented to achieve readable, forgiving mobile controls.

---

## 1. Movement Model

### Decision: CharacterBody2D

**Rationale:**
- KinematicBody2D was the Godot 3 approach and is deprecated in Godot 4.
- CharacterBody2D is Godot 4's idiomatic choice for player-controlled characters with integrated physics.
- It provides better collision integration and is the correct foundation for mobile platformer movement.

**Migration note from SYSTEM-001:**
- The existing `scenes/player/Player.tscn` uses `KinematicBody2D` (Godot 3 style).
- CORE-001 implementation will replace this node type with `CharacterBody2D`.
- The existing PlayerState autoload remains unchanged.

**Files affected:**
- `scenes/player/Player.tscn` — node type migration
- `scripts/player/PlayerController.gd` — new movement script (replaces placeholder logic)

---

## 2. Input Handling

### Decision: Input Actions + Touch Device Detection

**Chosen approach:**
- Use Godot's Input Map actions (`move_left`, `move_right`, `jump`) already defined in `project.godot`.
- Add `dash` action to Input Map for consistency.
- Detect touch device at runtime and show/hide mobile UI overlays.
- For now, keyboard fallback is sufficient since mobile UI scaffolding is handled in UX-001.

**Input actions to add:**

```ini
dash={
  "deadzone": 0.5,
  "events": [ Object(InputEventKey,"resource_local_to_scene":false,...,"scancode":16777238,...)]
}
```

**Touch handling notes:**
- Mobile joystick and buttons will be implemented in UX-001.
- The controller script will read `Input.is_action_pressed()` and `Input.is_action_just_pressed()`.
- No touch-specific logic in CORE-001; abstraction layer added for later UX-001 hook-in.

**Files affected:**
- `project.godot` — add `dash` input action

---

## 3. Movement Constants

### Decision: Centralized `PlayerDefaults` Resource

**Rationale:**
- Movement tuning must not require code changes during iteration.
- A `PlayerDefaults` resource holds all constants and can be edited in the Inspector.
- Provides a single source of truth for SPEED, JUMP_FORCE, GRAVITY, etc.

**Proposed structure:**

```gdscript
# scripts/player/PlayerDefaults.gd
extends Resource
class_name PlayerDefaults

# Movement
@export var SPEED: float = 350.0           # Horizontal run speed (px/s)
@export var JUMP_FORCE: float = -600.0     # Initial jump velocity (negative Y)
@export var GRAVITY: float = 1400.0        # Gravity acceleration (px/s²)
@export var MAX_FALL_SPEED: float = 800.0   # Terminal velocity

# Wall
@export var WALL_SLIDE_SPEED: float = 120.0  # Max fall speed when wall sliding
@export var WALL_JUMP_H_FORCE: float = 300.0 # Horizontal push on wall jump
@export var WALL_JUMP_V_FORCE: float = -500.0 # Vertical component on wall jump

# Dash
@export var DASH_SPEED: float = 700.0       # Dash velocity magnitude
@export var DASH_DURATION: float = 0.15     # Dash duration (seconds)
@export var DASH_COOLDOWN: float = 0.8      # Cooldown between dashes (seconds)

# Coyote & Buffer
@export var COYOTE_TIME: float = 0.10      # Seconds after leaving ground where jump still works
@export var JUMP_BUFFER_TIME: float = 0.12  # Seconds before landing where jump input is remembered
```

**Files affected:**
- `scripts/player/PlayerDefaults.gd` — new resource class

---

## 4. Coyote Time

### Decision: IMPLEMENT — Duration: 100ms (0.10s)

**Implementation approach:**
- Track `time_since_grounded` since last leaving the ground.
- On jump input, if `time_since_grounded <= COYOTE_TIME`, grant jump.
- Reset `time_since_grounded` on landing or wall contact.

**Evidence for implementation:**
- Coyote time is standard practice in modern platformers (Celeste, Mario, etc.).
- Mobile controls have inherent input lag; coyote time compensates and improves forgiveness.
- Rejecting coyote time would harm mobile playability and contradicts "touch control usability outrank ornamental complexity."

**Constants:**
- `COYOTE_TIME = 0.10` — tuned for 100ms forgiveness window

---

## 5. Jump Buffering

### Decision: IMPLEMENT — Duration: 120ms (0.12s)

**Implementation approach:**
- On `jump` pressed, record `jump_buffer_time = JUMP_BUFFER_TIME`.
- Each physics frame, decrement `jump_buffer_time`.
- When grounded and `jump_buffer_time > 0`, auto-execute jump and clear buffer.

**Evidence for implementation:**
- Jump buffering is standard in modern platformers.
- Touch jump buttons have variable press timing; buffering smooths the experience.
- Same reasoning as coyote time — critical for mobile readability.

**Constants:**
- `JUMP_BUFFER_TIME = 0.12` — tuned for 120ms input window

---

## 6. Wall Interaction

### Decision: Implement Wall Slide + Wall Jump

### Wall Slide
- When `is_on_wall()` and moving toward wall and not grounded, apply reduced gravity.
- Cap fall speed at `WALL_SLIDE_SPEED` instead of `MAX_FALL_SPEED`.
- Visual telegraph: player sprite leans into wall (handled later in POLISH-001).

### Wall Jump
- When `jump` pressed while wall sliding, launch away from wall.
- Apply `WALL_JUMP_H_FORCE` in opposite direction of wall + `WALL_JUMP_V_FORCE` upward.
- Brief lockout (100ms) prevents immediate re-grab of same wall.

**Constants:**
- `WALL_SLIDE_SPEED = 120.0`
- `WALL_JUMP_H_FORCE = 300.0`
- `WALL_JUMP_V_FORCE = -500.0`

---

## 7. Dash

### Decision: Implement with cooldown, no invincibility

### Parameters:
- **Direction**: Horizontal, in facing direction (last horizontal input or last movement direction).
- **Duration**: 150ms (0.15s)
- **Cooldown**: 800ms (0.8s) — prevents spam, maintains tension
- **Invincibility**: REJECTED — dash invincibility would undermine hazard risk and glitch fairness contract

**Rationale for rejecting invincibility:**
- Glitch's core mechanic is unpredictable mutation; removing player risk during dash breaks the fairness contract.
- If dash grants invincibility, hazards become unfair because players can trivially回避 them.
- Recovery space matters as much as surprise (glitch-design-guardrails).

**Implementation:**
- During dash, velocity locked to `DASH_SPEED` in facing direction.
- Gravity and wall slide disabled during dash.
- `dash_cooldown_timer` tracks cooldown; dash unavailable when `> 0`.

**Constants:**
- `DASH_SPEED = 700.0`
- `DASH_DURATION = 0.15`
- `DASH_COOLDOWN = 0.8`

---

## 8. State Machine

### Decision: Enumerator-based state machine in PlayerController

**States (enum PlayerState):**
```
IDLE       — No horizontal movement, grounded
RUN        — Horizontal movement, grounded
JUMP       — Rising from jump (may blend with FALL depending on velocity)
FALL       — Descending or no vertical input
WALL_SLIDE — Grounded on wall, falling slowly
DASH       — Temporary dash state, overrides others
```

**State transition rules:**
```
IDLE:
  -> RUN: horizontal input != 0
  -> JUMP: jump_pressed (includes buffered jump or coyote jump)
  -> FALL: no ground contact

RUN:
  -> IDLE: no horizontal input
  -> JUMP: jump_pressed
  -> FALL: no ground contact
  -> WALL_SLIDE: is_on_wall() AND moving toward wall

JUMP:
  -> FALL: velocity.y >= 0 OR !is_on_floor()

FALL:
  -> IDLE: grounded AND no horizontal input
  -> RUN: grounded AND horizontal input != 0
  -> WALL_SLIDE: is_on_wall() AND moving toward wall

WALL_SLIDE:
  -> JUMP: jump_pressed (wall jump)
  -> FALL: moving away from wall OR !is_on_wall()

DASH:
  -> IDLE: dash duration elapsed AND grounded AND no input
  -> RUN: dash duration elapsed AND grounded AND input != 0
  -> FALL: dash duration elapsed AND !grounded
```

**Notes:**
- JUMP and FALL are separate states even though both are "airborne" — they have different physics.
- WALL_SLIDE is distinct from FALL because gravity is capped.
- DASH is a temporary override; returning to previous air/ground state after duration.

---

## 9. File Structure

```
scenes/player/
  Player.tscn          — Migrate KinematicBody2D -> CharacterBody2D

scripts/player/
  PlayerDefaults.gd    — Centralized constants resource
  PlayerController.gd   — Main movement controller with state machine

scripts/autoload/       — Unchanged from SYSTEM-001
```

---

## 10. Validation Plan

### Validation 1: Godot Headless Startup
**Command:** `godot --headless --path . --quit`
**Expected:** No errors, no warnings about missing scripts or invalid nodes

### Validation 2: Scene Import Check
**Command:** `godot --headless --path . --import`
**Expected:** All scenes import without errors

### Validation 3: Player Scene Loads
**Command:** `godot --headless --path . --script scripts/player/PlayerController.gd` (or equivalent headless check)
**Alternative:** Write a minimal test scene that instantiates Player and checks it initializes without errors

### Validation 4: State Machine Smoke Test
**Proof:** A headless script that instantiates PlayerController, simulates input序列, and verifies state transitions occur without crashing

### Validation 5: Constants Resource Instantiation
**Proof:** `PlayerDefaults` can be created as a Resource and values inspected

---

## 11. Risks and Open Questions

### Risk: Touch Input Latency Compensation
- Mobile touch has inherent lag; coyote time (100ms) and jump buffer (120ms) may need tuning.
- Mitigation: Keep constants in `PlayerDefaults` for fast iteration.

### Risk: Wall Jump Edge Cases
- Wall jump lockout (100ms) must not feel unresponsive.
- Mitigation: Test with representative room from CORE-003 / CONTENT-001.

### Open Question: Facing Direction for Dash
- If no horizontal input during dash, use last movement direction.
- If standing still, dash in last faced direction (tracked via `facing_right` bool).

### Open Question: Dashing Into Wall
- If dash ends with player inside a wall, `CharacterBody2D` will resolve collision normally.
- No special handling needed unless CORE-002 glitch events require it.

---

## 12. Blockers and Required Decisions

**None for planning stage.** All decisions above are resolved:

| Decision | Resolution |
|----------|-------------|
| Movement model | CharacterBody2D |
| Input handling | Input actions + abstraction for UX-001 |
| Constants | PlayerDefaults Resource |
| Coyote time | Implement, 100ms |
| Jump buffering | Implement, 120ms |
| Wall interaction | Implement slide + wall jump |
| Dash | Implement, no invincibility |
| State machine | Enumerator-based |
| Validation | Headless startup + scene import |

---

## 13. Acceptance Criteria Checklist

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Player movement supports left-right, jump, wall slide, wall jump, dash | Plan covers all five |
| 2 | Coyote time implemented or rejected with evidence | Implemented, 100ms |
| 3 | Jump buffering implemented or rejected with evidence | Implemented, 120ms |
| 4 | Movement constants centralized | PlayerDefaults.gd |
| 5 | Validation demonstrates controller loads and runs | Headless + import checks planned |

---

## 14. Dependencies

- **Depends on**: SETUP-001 (done), SYSTEM-001 (done)
- **Blocks**: CORE-002 (glitch events need player state), UX-001 (mobile UI hooks into controller)

---

## 15. Next Stage

After plan approval and `ticket_update stage=plan_review approved_plan=true`:
- Transition to `implementation`
- Create `PlayerDefaults.gd` resource
- Migrate `Player.tscn` from KinematicBody2D to CharacterBody2D
- Write `PlayerController.gd` with full state machine
- Add `dash` input action to `project.godot`
- Run validation commands
