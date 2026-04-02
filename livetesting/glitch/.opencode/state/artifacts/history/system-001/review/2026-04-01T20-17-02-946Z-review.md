# SYSTEM-001 Review Artifact

## Ticket
- **ID**: SYSTEM-001
- **Title**: Create the base Godot project architecture
- **Stage**: review

---

## 1. Acceptance Criteria Validation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Runnable Godot project scaffold exists | ✅ PASS | project.godot at repo root, all scenes present, headless startup succeeds |
| Scene and autoload boundaries documented | ⚠️ PARTIAL | Boundaries are documented in implementation artifact, but architecture has a defect (see Finding 1) |
| Headless Godot startup succeeds | ✅ PASS | `godot --headless --path . --quit` exits cleanly with autoload initialization |
| Architecture supports expansion | ✅ PASS | Directory structure allows new zones/abilities/glitches without coupling |

---

## 2. Implementation Evidence Verification

### Files Verified Against Artifact

| File | Artifact Claim | Actual State | Match |
|------|---------------|-------------|-------|
| project.godot | Godot 4.6.2, 4 autoloads, input actions, 1280x720 | ✅ All present | ✅ |
| PlayerState.gd | Signals: player_died, player_respawned, checkpoint_activated | ✅ All present | ✅ |
| GlitchState.gd | Signals: glitch_started, glitch_ended, corruption_level_changed | ✅ All present | ✅ |
| GameState.gd | Signals: level_started, level_completed, game_saved, game_loaded | ✅ All present | ✅ |
| LevelManager.gd | Signals: level_loaded, transition_started, transition_completed | ✅ All present | ✅ |
| Main.tscn | Node2D root, LevelContainer, Player | ✅ All present | ✅ |
| Player.tscn | KinematicBody2D, CollisionShape2D, Sprite | ✅ All present | ✅ |
| StartupSector.tscn | Node2D with floor StaticBody2D | ✅ All present | ✅ |
| HUD.tscn | CanvasLayer, HealthLabel, GlitchLabel | ✅ All present | ✅ |

### Validation Commands Verified

**Command 1**: `godot --headless --path . --quit`
- **Artifact claim**: PASS - All autoloads initialized, clean exit
- **Actual output**: Godot v4.6.2 starts, all 4 autoloads initialize twice (printed twice each), exits cleanly
- **Result**: ✅ PASS - Command succeeds as reported

**Command 2**: `godot --headless --path . --import`
- **Artifact claim**: PASS - All resources imported successfully, no errors
- **Actual output**: Project initialization completes, icon.svg imported, no errors
- **Result**: ✅ PASS - Command succeeds as reported

---

## 3. Findings

### BLOCKER: Duplicate Autoload Instances (Architecture Defect)

**Severity**: High

**Problem**: The 4 autoloads (PlayerState, GlitchState, GameState, LevelManager) are registered in `project.godot` AND included as child nodes in `Main.tscn`. This causes each autoload to initialize twice on startup, as confirmed by the double print output:

```
[PlayerState] Initialized - Health: 3
[GlitchState] Initialized - Corruption level: 0
[GameState] Initialized - Current level: 
[LevelManager] Initialized
[PlayerState] Initialized - Health: 3   ← duplicate
[GlitchState] Initialized - Corruption level: 0  ← duplicate
[GameState] Initialized - Current level:   ← duplicate
[LevelManager] Initialized  ← duplicate
```

**Root Cause**: In Godot, autoloads specified in project.godot are added to the scene tree as singleton children of `/root/` BEFORE the main scene loads. When `Main.tscn` also contains nodes named `PlayerState`, `GlitchState`, `GameState`, `LevelManager` with the same scripts attached, they become separate instances under `Main`, not references to the singletons.

**Impact**: 
- Signal emissions from one instance will not be received by the other
- State stored in the singleton autoloads (e.g., `PlayerState.health`) is separate from the duplicate nodes in `Main`
- This breaks the intended architecture where all code references the autoload singletons

**Required Fix**: Remove the 4 autoload nodes from `Main.tscn`. The singletons are already available via `/root/PlayerState`, `/root/GlitchState`, etc. The scene should only contain non-autoload nodes: `LevelContainer` and `Player`.

---

## 4. Regression Risks

1. **State synchronization bug**: The duplicate autoload instances mean code using `PlayerState.health` from different contexts may see different values. Any signal connected from gameplay code to the "wrong" instance will fail silently.

2. **Memory overhead**: Small but unnecessary duplication of 4 Node objects.

3. **Confusion for future developers**: The pattern suggests the implementer was unsure whether autoloads should be in the scene tree, leading to both approaches being combined.

---

## 5. Validation Gaps

1. **No actual player controller logic** - Player.tscn is a placeholder with only a KinematicBody2D, CollisionShape2D, and Sprite. No movement code exists yet. This is expected per the ticket scope (architecture only), but the dependency chain (CORE-001) should track this.

2. **LevelManager assumes specific scene tree** - The `level_container_path` hardcodes `NodePath("/root/Main/LevelContainer")`. If the scene tree structure changes, this path breaks. No validation that this path exists at runtime.

3. **No actual level loading tested** - StartupSector.tscn exists but was not loaded in the headless test. Only Main.tscn (the main scene) was validated.

---

## 6. Positive Observations

1. **Signal contracts are well-defined**: Each autoload has clear signals with typed parameters matching the documented contract.

2. **Directory structure is sound**: `scenes/player/`, `scenes/levels/`, `scenes/ui/`, `scripts/autoload/` separation supports the stated expansion pathways.

3. **Input actions are registered**: Keyboard input actions (move_left, move_right, jump) exist for future player controller implementation.

4. **GDScript typing is used**: Functions use return type hints (`-> void`, `-> bool`) which is good practice.

---

## 7. Summary

**Verdict**: ❌ FAIL - Blocker Found

The implementation creates duplicate autoload instances which breaks the singleton architecture. This must be fixed before CORE-001, CORE-002, and CORE-003 can rely on the autoload signal contracts working correctly.

**Required Action**: Remove PlayerState, GlitchState, GameState, and LevelManager nodes from Main.tscn. The autoloads are already registered in project.godot and available as singletons.

**Can Advance To**: This ticket cannot advance to QA until the duplicate autoload issue is resolved in the implementation and re-verified.
