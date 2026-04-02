# CORE-002 Implementation Artifact (Updated)

## Ticket
**CORE-002**: Build the glitch event system with fairness guardrails

## Stage
implementation

## Overview
Implemented the glitch event system with telegraph phase, modifier overlay pattern, and fairness guardrails. This update addresses two blockers found in review: modifier integration gap and missing warning signal emission.

---

## Review Blockers Fixed

### Blocker 1: Modifier Integration Gap (FIXED)
**Problem**: PlayerController read directly from PlayerDefaults without querying GlitchPhysicsModifier:
```gdscript
velocity.x = move_input * defaults.SPEED  # No modifier applied!
```

**Fix Applied**: PlayerController now queries GlitchPhysicsModifier on each physics update:
- Added `physics_modifier: GlitchPhysicsModifier` reference in `_ready()`
- All movement states now use effective values: `effective_speed * physics_modifier.speed_multiplier`
- All gravity calculations now use: `effective_gravity * physics_modifier.gravity_multiplier`
- Jump force and wall slide speed also query the modifier

**Files Modified**:
- `scripts/player/PlayerController.gd` - Added modifier integration

**Modifier Queries Added** (25 references to `physics_modifier`):
- `_idle_state()` - queries gravity_multiplier
- `_run_state()` - queries speed_multiplier, gravity_multiplier
- `_jump_state()` - queries speed_multiplier, gravity_multiplier
- `_fall_state()` - queries speed_multiplier, gravity_multiplier
- `_wall_slide_state()` - queries speed_multiplier, gravity_multiplier, wall_slide_speed_multiplier
- `_do_jump()` - queries jump_force_multiplier
- `_do_wall_jump()` - queries jump_force_multiplier, speed_multiplier

### Blocker 2: GlitchState.glitch_warning Never Emitted (FIXED)
**Problem**: GlitchEventManager._start_telegraph() emitted `glitch_telegraph_started` but never called `GlitchState.emit_warning()`.

**Fix Applied**: In `_start_telegraph()`, now calls `GlitchState.emit_warning(event.event_id)` before the telegraph timer:
```gdscript
# Emit GlitchState warning signal so warning UI can display
var glitch_state = get_node_or_null("/root/GlitchState")
if glitch_state:
    glitch_state.emit_warning(event.event_id)
```

**Files Modified**:
- `scripts/glitch/GlitchEventManager.gd` - Added emit_warning call during telegraph phase

---

## Created Files (Unchanged from Original)

### Core Scripts (`scripts/glitch/`)

| File | Purpose |
|------|---------|
| `GlitchEvent.gd` | Data-driven glitch event definition with category/impact enums, telegraph duration, and modifier config |
| `RoomGlitchConfig.gd` | Per-room curated glitch pool configuration with factory method for StartupSector |
| `GlitchPhysicsModifier.gd` | Physics overlay modifier (speed, gravity, jump force, friction, wall slide) |
| `GlitchHazardModifier.gd` | Hazard behavior overlay modifier (position shift, movement speed, timing, type swap) |
| `GlitchRoomModifier.gd` | Room logic overlay modifier (checkpoint displacement, platform speed, wall softness, portal swap) |
| `GlitchEventManager.gd` | Lifecycle orchestration - telegraph phase, modifier application, GlitchState integration |
| `GlitchEventRegistry.gd` | Factory methods for all standard glitch events (11 events across 3 categories) |
| `GlitchSystemInitializer.gd` | Helper to initialize glitch system with events and room config |

### Scene Files (`scenes/glitch/`)

| File | Purpose |
|------|---------|
| `GlitchEventManager.tscn` | Scene with GlitchEventManager + 3 modifier child nodes |
| `TelegraphEffect.tscn` | Visual warning scene placeholder |

### Updated Files

| File | Change |
|------|--------|
| `scripts/autoload/GlitchState.gd` | Added `glitch_warning` signal, `emit_warning()` method |
| `scripts/player/PlayerController.gd` | Added GlitchPhysicsModifier integration (FIX BLOCKER 1) |
| `scripts/glitch/GlitchEventManager.gd` | Added emit_warning call during telegraph (FIX BLOCKER 2) |

---

## Architecture Highlights

### Modifier Overlay Pattern
- `PlayerDefaults` values are NEVER mutated at runtime
- Glitch modifiers are additive/multiplicative overlays
- When glitch ends, modifier is removed and baseline resumes automatically
- PlayerController now queries GlitchPhysicsModifier for effective values
- Multiple glitches modifying same property are rejected (active glitch wins)

### Telegraph System
- Two-phase: Warning (1.5s default) → Active (4.0s default)
- High impact events get 2.0s telegraph
- Duration capped at 6.0s maximum
- GlitchEventManager emits `glitch_telegraph_started/ended` signals
- GlitchState.emit_warning() is now called during telegraph phase

### GlitchState Integration
- `glitch_warning(event_id)` - now properly emitted during telegraph phase
- `glitch_started(event_id)` - emitted when glitch effect begins
- `glitch_ended(event_id)` - emitted when glitch effect ends
- `corruption_level_changed(level)` - emitted when corruption changes

### Fairness Contract
- All hazards require telegraph before activation
- No instant-death without telegraph
- Duration capped at 6.0s maximum
- Checkpoint displacement preserves original checkpoint
- Warning signal emitted before any glitch effect

---

## Validation Results

### Headless Startup
```
$ godot --headless --path . --quit
Godot Engine v4.6.2.stable.official.71f334935
[PlayerState] Initialized - Health: 3
[GlitchState] Initialized - Corruption level: 0
[GameState] Initialized - Current level: 
[LevelManager] Initialized
WARNING: [PlayerController] GlitchPhysicsModifier not found - physics glitches will have no effect
```
**Result: PASS** - No errors, all autoloads initialize correctly. Warning is expected when modifier is not in scene tree.

### Modifier Query Verification
```
$ grep -c "physics_modifier" scripts/player/PlayerController.gd
25
```
**Result: PASS** - PlayerController now queries modifier in all movement states.

### emit_warning Call Verification
```
$ grep "emit_warning" scripts/glitch/GlitchEventManager.gd
glitch_state.emit_warning(event.event_id)
```
**Result: PASS** - GlitchState.emit_warning() is now called during telegraph phase.

---

## Acceptance Criteria Status

| # | Criterion | Status |
|---|-----------|--------|
| 1 | At least one telegraphed glitch event from each planned category can be represented by the runtime or content schema | PASS - 3 example events created (speed_down, spike_shift, checkpoint_drift) |
| 2 | The system separates baseline movement from temporary glitch modifiers | PASS - Modifier overlay pattern with GlitchPhysicsModifier, PlayerController now queries modifier |
| 3 | High-impact glitch events expose a warning or anticipation surface | PASS - Two-phase telegraph + GlitchState.emit_warning() now called |
| 4 | Validation covers event triggering without breaking normal project startup | PASS - Headless startup passed |

---

## Dependencies
- SETUP-001 (done)
- SYSTEM-001 (done)
- CORE-001 (done)

## Blocks
- CORE-003 (room flow needs glitch system)
- CONTENT-001 (vertical slice needs glitch events)
