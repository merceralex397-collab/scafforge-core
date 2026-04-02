# CORE-002 QA Artifact

## QA Execution Date
2026-04-01T21:25:00.000Z

## Active Ticket
- **ID**: CORE-002
- **Title**: Build the glitch event system with fairness guardrails
- **Stage**: qa
- **Status**: qa

---

## Validation Checks

### Check 1: Godot Headless Startup

**Command**: `godot --headless --path . --quit`

**Output**:
```
Godot Engine v4.4.2.stable.official.71f334935 - https://godotengine.org
[PlayerState] Initialized - Health: 3
[GlitchState] Initialized - Corruption level: 0
[GameState] Initialized - Current level: 
[LevelManager] Initialized
WARNING: [PlayerController] GlitchPhysicsModifier not found - physics glitches will have no effect
     at: push_warning (core/variant/variant_utility.cpp:1034)
     GDScript backtrace (most recent call first):
         [0] _ready (res://scripts/player/PlayerController.gd:66)
```

**Verdict**: ⚠️ PASS WITH WARNING

**Note**: Project starts but GlitchPhysicsModifier is inaccessible. See blockers below.

---

### Check 2: Godot Headless Import

**Command**: `godot --headless --path . --import`

**Output**:
```
[   0% ] first_scan_filesystem | Started Project initialization (5 steps)
[   0% ] first_scan_filesystem | Scanning file structure...
[  16% ] first_scan_filesystem | Loading global class names...
[  33% ] first_scan_filesystem | Verifying GDExtensions...
[  50% ] first_scan_filesystem | Creating autoload scripts...
[  66% ] first_scan_filesystem | Initializing plugins...
[  83% ] first_scan_filesystem | Starting file scan...
[  92% ] first_scan_filesystem | 
[ DONE ] first_scan_filesystem | 
[   0% ] update_scripts_classes | Started Registering global classes... (2 steps)
[   0% ] update_scripts_classes | PlayerController
[ DONE ] update_scripts_classes | 
[   0% ] loading_editor_layout | Started Loading editor (5 steps)
[   0% ] loading_editor_layout | Loading editor layout...
[  16% ] loading_editor_layout | Loading docks...
[ DONE ] loading_editor_layout | 
```

**Verdict**: ✅ PASS

---

### Check 3: Script Class Registration

**Method**: grep for `class_name` in `scripts/glitch/*.gd`

**Results**:
| Class | File | Registered |
|-------|------|------------|
| GlitchEvent | GlitchEvent.gd | ✅ |
| GlitchEventRegistry | GlitchEventRegistry.gd | ✅ |
| GlitchPhysicsModifier | GlitchPhysicsModifier.gd | ✅ |
| GlitchHazardModifier | GlitchHazardModifier.gd | ✅ |
| GlitchRoomModifier | GlitchRoomModifier.gd | ✅ |
| RoomGlitchConfig | RoomGlitchConfig.gd | ✅ |

**Verdict**: ✅ PASS

---

### Check 4: File Existence

**Command**: `ls -la scripts/glitch/ scenes/glitch/`

**Required Files**:
| File | Path | Status |
|------|------|--------|
| GlitchEvent.gd | scripts/glitch/ | ✅ EXISTS |
| GlitchEventManager.gd | scripts/glitch/ | ✅ EXISTS |
| GlitchEventRegistry.gd | scripts/glitch/ | ✅ EXISTS |
| GlitchPhysicsModifier.gd | scripts/glitch/ | ✅ EXISTS |
| GlitchHazardModifier.gd | scripts/glitch/ | ✅ EXISTS |
| GlitchRoomModifier.gd | scripts/glitch/ | ✅ EXISTS |
| RoomGlitchConfig.gd | scripts/glitch/ | ✅ EXISTS |
| GlitchEventManager.tscn | scenes/glitch/ | ✅ EXISTS |
| TelegraphEffect.tscn | scenes/glitch/ | ✅ EXISTS |

**Verdict**: ✅ PASS

---

### Check 5: GlitchState.emit_warning Existence

**Command**: `grep -n "func emit_warning" scripts/autoload/GlitchState.gd`

**Output**:
```
35:	func emit_warning(event_id: String) -> void:
36:		emit_signal("glitch_warning", event_id)
37:		print("[GlitchState] Glitch warning: %s" % event_id)
```

**Verdict**: ✅ PASS

---

### Check 6: PlayerController physics_modifier Queries

**Command**: `grep -c "physics_modifier" scripts/player/PlayerController.gd`

**Output**: 25 references confirmed

**Query locations**:
- Line 49: `var physics_modifier: GlitchPhysicsModifier = null`
- Lines 56-66: Initialization and fallback logic
- Lines 143-144: `_idle_state()` gravity query
- Lines 162-164: `_run_state()` speed and gravity queries
- Lines 186-188: `_jump_state()` queries
- Lines 206-208: `_fall_state()` queries
- Lines 234-237: `_wall_slide_state()` queries
- Lines 279-280: `_do_jump()` query
- Lines 308-310: `_do_wall_jump()` queries

**Verdict**: ✅ PASS

---

## Acceptance Criteria Verification

| Criterion | Evidence | Status |
|-----------|----------|--------|
| At least one telegraphed glitch event from each planned category can be represented | 11 events across 3 categories (PHYSICS/HAZARD/ROOM_LOGIC) registered in GlitchEventRegistry | ⚠️ Schema exists, but system never initializes |
| System separates baseline movement from temporary glitch modifiers | Modifier overlay pattern implemented via GlitchPhysicsModifier | ⚠️ Code structure exists, but modifier never accessible at runtime |
| High-impact glitch events expose a warning or anticipation surface | emit_warning() signal chain complete (lines 35-37 in GlitchState.gd) | ⚠️ Signal exists but no UI connects to it |
| Validation covers event triggering without breaking normal project startup | Godot --headless --quit: PASS | ⚠️ Startup works, but GlitchSystemInitializer never runs so events cannot trigger |

---

## Summary Table

| Check | Command/Method | Result |
|-------|----------------|--------|
| Godot headless startup | `godot --headless --path . --quit` | ⚠️ PASS WITH WARNING |
| Godot import check | `godot --headless --path . --import` | ✅ PASS |
| Script class registration | grep class_name | ✅ PASS |
| File existence | ls scripts/glitch/ scenes/glitch/ | ✅ PASS |
| GlitchState.emit_warning | grep emit_warning | ✅ PASS |
| PlayerController physics_modifier | grep physics_modifier (25 refs) | ✅ PASS |

**Total**: 6 checks
- ✅ PASS: 5
- ⚠️ PASS WITH WARNING: 1

---

## QA Verdict

### ❌ FAIL - Blockers Prevent Smoke-Test Transition

### Blockers

#### Blocker 1: GlitchEventManager Never Initialized (CRITICAL)
**Issue**: `GlitchSystemInitializer.gd` exists at `scripts/glitch/GlitchSystemInitializer.gd` but is never called because:
- It is NOT registered as an autoload in `project.godot`
- It is NOT added to `Main.tscn`
- No code calls its `_ready()` method

**Impact**: `GlitchEventManager` is never added to the scene tree. The modifier nodes (`PhysicsModifier`, `HazardModifier`, `RoomModifier`) inside `GlitchEventManager.tscn` are never instantiated.

**Runtime Evidence**:
```
WARNING: [PlayerController] GlitchPhysicsModifier not found - physics glitches will have no effect
```

**Acceptance Criteria Affected**:
- Criterion 1: Events cannot trigger because GlitchEventManager never initializes
- Criterion 2: Physics modifiers never apply because GlitchPhysicsModifier is not in tree
- Criterion 4: Events cannot fire because initialization chain is broken

---

#### Blocker 2: TelegraphEffect Not Connected to Any Signal (MODERATE)
**Issue**: `TelegraphEffect.tscn` exists at `scenes/glitch/TelegraphEffect.tscn` but:
- No code connects `GlitchState.glitch_warning` signal to any UI handler
- TelegraphEffect is never added to the scene tree
- No `_process_glitch_warning()` handler exists in any scene

**Impact**: Criterion 3 ("warning or anticipation surface") cannot be validated - the warning UI exists as a scene but has no operational connection to the glitch system.

---

#### Blocker 3: No Path to GlitchPhysicsModifier Access (CRITICAL)
**Issue**: PlayerController tries to get `GlitchPhysicsModifier` via:
1. `get_node_or_null("/root/GlitchPhysicsModifier")` - fails (not autoload)
2. `event_manager.get_physics_modifier()` - fails (GlitchEventManager not in tree)

**Impact**: Physics glitches will silently have zero effect on player movement. The 25 code references to `physics_modifier` exist but all resolve to `null` at runtime.

---

## Required Fixes Before Smoke-Test

1. **Add GlitchSystemInitializer to scene tree** - Either:
   - Option A: Add `GlitchSystemInitializer.tscn` (needs to be created) to `Main.tscn`, OR
   - Option B: Register `GlitchSystemInitializer` as autoload in `project.godot`

2. **Verify telegraph UI wiring** - Connect `GlitchState.glitch_warning` signal to any warning display

3. **Re-verify physics modifier application** - After fix #1, confirm `GlitchPhysicsModifier` is accessible and applies to movement

---

## Closeout Readiness

**Current State**: NOT READY for smoke-test

**Reason**: The glitch event system has correct code structure and schema, but the initialization path is broken. GlitchEventManager never enters the scene tree, making all glitch events inert at runtime.

**Next Action**: Route back to implementation to fix initialization chain before QA can pass.
