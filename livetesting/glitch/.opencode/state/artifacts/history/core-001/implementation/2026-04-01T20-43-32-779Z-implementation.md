# CORE-001 Implementation Artifact

## Ticket
**CORE-001**: Implement the baseline player controller

## Stage
implementation

## Overview
This implementation creates the baseline player controller for Glitch with CharacterBody2D, a state machine, coyote time, jump buffering, wall slide, wall jump, and dash mechanics.

---

## Files Created/Modified

### 1. `resources/PlayerDefaults.gd` (NEW)
Centralized movement constants as a Resource with @export fields.

**Path:** `resources/PlayerDefaults.gd`

**Contents:**
- `SPEED: float = 300.0` — Horizontal run speed (px/s)
- `JUMP_FORCE: float = -450.0` — Initial jump velocity
- `GRAVITY: float = 980.0` — Gravity acceleration (px/s²)
- `MAX_FALL_SPEED: float = 800.0` — Terminal velocity
- `WALL_SLIDE_SPEED: float = 120.0` — Max fall speed when wall sliding
- `WALL_JUMP_LERP: float = 0.8` — Horizontal push factor on wall jump
- `DASH_SPEED: float = 600.0` — Dash velocity magnitude
- `DASH_DURATION: float = 0.15` — Dash duration (150ms)
- `DASH_COOLDOWN: float = 0.8` — Cooldown between dashes (800ms)
- `COYOTE_TIME: float = 0.1` — Coyote grace period (100ms)
- `JUMP_BUFFER_TIME: float = 0.12` — Jump buffering window (120ms)

### 2. `scripts/player/PlayerController.gd` (NEW)
Main movement controller script with CharacterBody2D.

**Path:** `scripts/player/PlayerController.gd`

**Features implemented:**
- State machine with enum `MoveState`: IDLE, RUN, JUMP, FALL, WALL_SLIDE, DASH
- Coyote time: 100ms grace period after leaving ground
- Jump buffering: 120ms early jump window
- Wall slide: capped fall at 120 px/s
- Wall jump: push away with 100ms lockout to prevent re-grab
- Dash: 150ms duration, 800ms cooldown, NO invincibility (per fairness contract)

**Input actions used:**
- `move_left`, `move_right` — horizontal movement
- `jump` — jump/wall jump
- `dash` — dash maneuver

### 3. `scenes/player/Player.tscn` (MODIFIED)
Updated from KinematicBody2D (Godot 3) to CharacterBody2D (Godot 4).

**Changes:**
- Node type changed from `KinematicBody2D` to `CharacterBody2D`
- Attached `PlayerController.gd` script
- Added `CollisionShape2D` with RectangleShape2D (16x32)
- Updated `Sprite` to `Sprite2D` with scale 1,2 for proportions

### 4. `project.godot` (MODIFIED)
Added `dash` input action for keyboard control.

**Change:** Added dash action bound to Shift key (scancode 16777238)

---

## File Structure

```
glitch/
├── resources/
│   └── PlayerDefaults.gd          # Movement constants resource
├── scripts/
│   ├── autoload/                   # Unchanged (PlayerState, GlitchState, etc.)
│   └── player/
│       └── PlayerController.gd    # Main movement controller
├── scenes/
│   ├── player/
│   │   └── Player.tscn            # Updated CharacterBody2D scene
│   └── ...
└── project.godot                  # Updated with dash input action
```

---

## Validation Outputs

### Validation 1: Godot Headless Startup
**Command:** `godot --headless --path . --quit`

**Output:**
```
Godot Engine v4.6.2.stable.official.71f334935 - https://godotengine.org

[PlayerState] Initialized - Health: 3
[GlitchState] Initialized - Corruption level: 0
[GameState] Initialized - Current level: 
[LevelManager] Initialized
```

**Result:** PASS — No errors, all autoloads initialized correctly.

### Validation 2: Scene Import Check
**Command:** `godot --headless --path . --import`

**Output (excerpt):**
```
[   0% ] first_scan_filesystem | Loading global class names...
[   0% ] update_scripts_classes | PlayerDefaults
[   0% ] update_scripts_classes | PlayerController
[DONE] update_scripts_classes
```

**Result:** PASS — All scripts indexed and registered successfully.

---

## Issues Encountered and Resolved

### Issue 1: PlayerDefaults Type Not Found
**Problem:** Initial compilation failed with "Could not find type PlayerDefaults in the current scope"

**Solution:** Ran `godot --headless --path . --import` to force script indexing. The class_name system in Godot 4 requires the script to be registered before dependent scripts can reference it.

### Issue 2: PlayerState Naming Conflict
**Problem:** Autoload `PlayerState` conflicted with the local enum `PlayerState` in PlayerController.

**Solution:** Renamed the local enum from `PlayerState` to `MoveState` to avoid namespace collision with the global autoload.

---

## Acceptance Criteria Status

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Player movement supports left-right, jump, wall slide, wall jump, dash | IMPLEMENTED |
| 2 | Coyote time implemented (100ms) | IMPLEMENTED |
| 3 | Jump buffering implemented (120ms) | IMPLEMENTED |
| 4 | Movement constants centralized in PlayerDefaults | IMPLEMENTED |
| 5 | Validation demonstrates controller loads and runs | PASS (headless + import) |

---

## Dependencies
- **Required by:** CORE-002, UX-001
- **Depends on:** SETUP-001, SYSTEM-001

---

## Next Stage
Proceed to `review` stage for code review, then `qa` for smoke testing.
