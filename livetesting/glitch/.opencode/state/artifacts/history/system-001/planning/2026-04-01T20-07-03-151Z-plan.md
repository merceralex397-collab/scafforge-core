# SYSTEM-001 Planning Artifact

## Ticket
- **ID**: SYSTEM-001
- **Title**: Create the base Godot project architecture
- **Wave**: 0
- **Lane**: game-architecture
- **Stage**: planning

---

## 1. Project Location Decision

**Decision**: Create the Godot project at the repo root (`/home/pc/projects/Scafforge/livetesting/glitch/`).

**Rationale**:
- This repo IS the Glitch game project, not a wrapper repo.
- Godot 4.x allows the `.opencode/` directory to coexist at the project root alongside `project.godot` without conflict.
- The `.opencode/` folder is Git-ignored by typical Godot `.gitignore` patterns, and Godot's `project.godot` and `.import/` are Git-ignored by the Scafforge scaffold.
- This avoids an extra directory nesting level (e.g., `glitch/game/`) that would complicate Android export paths and asset references.
- Godot's `--path` flag can point to the repo root directly, matching SETUP-001's canonical validation commands.

**Project Root Contents After Implementation**:
```
glitch/                        <- repo root, also Godot project root
  .opencode/                   <- OpenCode operating layer
  project.godot               <- Godot project file (new)
  scenes/                     <- Godot scenes (new)
  scripts/                    <- GDScript files (new)
  resources/                  <- Godot resources (new)
  assets/                     <- Godot assets (new)
  docs/                       <- existing scaffold docs
  tickets/                    <- existing ticket system
  ...
```

---

## 2. Scene Tree Structure

### Base Hierarchy

```
Main (Main.tscn)
├── Player (Player.tscn)
├── LevelManager (autoload, not a scene node)
├── UI
│   ├── HUD (HUD.tscn)
│   └── GlitchWarning (GlitchWarning.tscn)
├── GlitchEffectManager (autoload)
└── LevelLoader (handles scene transitions)
```

### Scene Ownership Conventions

| Scene | Owner | Purpose |
|-------|-------|---------|
| `Main.tscn` | Root entry | Bootstrap, tree setup, initial child placement |
| `Player.tscn` | gameplay-core lane | All player logic; no hardcoded level coupling |
| `Levels/StartupSector.tscn` | level-systems lane | First playable room; no hardcoded glitch coupling |
| `UI/HUD.tscn` | mobile-ux lane | Health, glitch meter, touch zone placeholder |
| `UI/GlitchWarning.tscn` | gameplay-systems lane | Glitch telegraph overlay |

### Scene Composition Rules
- Player is instantiated as a child of Main, not embedded in a level scene.
- Levels are swapped as children of a `LevelContainer` node under Main.
- UI layer sits as a sibling to LevelContainer, always on top.
- No scene references across level boundaries except through autoloaded singletons.

---

## 3. Autoload Boundaries

### Required Autoloads

| Autoload | Variable | Purpose |
|----------|----------|---------|
| `PlayerState` | `player_state` | Player health, current abilities, checkpoint data. Notifies other systems on death/respawn. |
| `GlitchState` | `glitch_state` | Active glitch modifiers, corruption level, event cooldown timers. Separate from baseline physics. |
| `GameState` | `game_state` | Score, current level ID, checkpoint positions, session flags. Persists across respawns. |
| `LevelManager` | `level_manager` | Loads/unloads level scenes, emits `level_loaded` and `level_transition` signals. No hardcoded room logic. |

### Autoload Design Principles
- Each autoload owns exactly one concern (player, glitch, game, level).
- Autoloads communicate via signals, not direct node paths.
- Glitch modifiers do NOT live in `PlayerState` — they are separate so baseline movement is always recoverable.
- `LevelManager` has no knowledge of glitch content; it only manages scene lifetime.

### Signal Contract

```
PlayerState:
  - player_died
  - player_respawned
  - checkpoint_activated(position: Vector2)

GlitchState:
  - glitch_started(event_id: String)
  - glitch_ended(event_id: String)
  - corruption_level_changed(level: int)

GameState:
  - level_started(level_id: String)
  - level_completed(level_id: String)
  - game_saved
  - game_loaded

LevelManager:
  - level_loaded(scene_path: String)
  - transition_started
  - transition_completed
```

---

## 4. Directory Structure

```
scenes/
  Main.tscn
  Player.tscn
  UI/
    HUD.tscn
    GlitchWarning.tscn
  Levels/
    StartupSector.tscn        <- first playable room placeholder
 Hazards/
    Spike.tscn                <- placeholder hazard
  Checkpoints/
    Checkpoint.tscn           <- placeholder checkpoint

scripts/
  autoload/
    player_state.gd
    glitch_state.gd
    game_state.gd
    level_manager.gd
  player/
    player_controller.gd     <- movement, jump, dash, wall interactions
  ui/
    hud.gd
    glitch_warning.gd
  hazards/
    hazard.gd                <- base hazard interface
  levels/
    level.gd                 <- base level interface
  rooms/
    room.gd                  <- room metadata, glitch pool, hazard set

resources/
  configs/
    game_config.cfg          <- tunable constants (speeds, timings)
  glitch_pools/
    startup_sector_pool.tres <- curated glitch event IDs for first room

assets/
  sprites/
  audio/
  fonts/
```

---

## 5. Initial Scenes to Create

### Minimum Viable Set for Vertical Slice

1. **`project.godot`** — Godot 4.x project file with Android export preset
2. **`scenes/Main.tscn`** — Root scene with Main node + Player child + LevelContainer + UI layer
3. **`scenes/Player.tscn`** — Player character with kinematic body, sprite, collision shape
4. **`scenes/Levels/StartupSector.tscn`** — Flat room with floor, walls, ceiling, checkpoint, spike hazard placeholder
5. **`scenes/UI/HUD.tscn`** — Minimal HUD with health display and glitch meter placeholder
6. **`scripts/autoload/`** — All four autoload scripts (empty/stub implementations)
7. **`scripts/player/player_controller.gd`** — Stub that accepts input and prints debug (full implementation in CORE-001)
8. **`resources/configs/game_config.cfg`** — Tunable constants file

### Scene Creation Order

1. `project.godot` (godot --headless --export-pack first to bootstrap)
2. Autoload scripts (foundation for all other systems)
3. `Main.tscn` (scene tree bootstrap)
4. `Player.tscn` (player entry)
5. `StartupSector.tscn` (first room)
6. `HUD.tscn` (UI entry)
7. `game_config.cfg` (centralized constants)

---

## 6. Validation Plan

### Headless Startup Verification

```bash
# Command 1: Basic headless load
godot --headless --path . --quit

# Command 2: Import and validate all resources
godot --headless --path . --import
```

Both commands must exit with code 0.

### Implementation Artifact Evidence Requirements

The implementation artifact for SYSTEM-001 must include:
- Output of `godot --headless --path . --quit` showing successful load
- Output of `godot --headless --path . --import` showing zero import errors
- Scene tree structure confirmed via Godot editor log or `--headless` output
- List of created files with paths

### Smoke Test Scope

The SYSTEM-001 smoke test validates:
- `project.godot` exists and is parseable by Godot 4.6.2
- `Main.tscn` loads as the main scene
- All four autoloads are registered and initialize without error
- No fatal script errors on startup

---

## 7. Architecture Expansion Pathways

### Adding New Zones
1. Create new scene under `scenes/Levels/` (e.g., `IndustrialZone.tscn`)
2. Add entry to `resources/configs/level_registry.cfg`
3. Register glitch pool in `resources/glitch_pools/`
4. `LevelManager` loads by ID; no code changes needed

### Adding New Abilities
1. Add ability ID to `PlayerState.abilities` array
2. Implement ability script under `scripts/player/abilities/`
3. Bind input in `PlayerController._unhandled_input()`
4. No autoload changes required

### Adding New Glitch Events
1. Add event ID to curated pool resource for the target room
2. Implement event effect in `GlitchState.apply_event(event_id)`
3. Add telegraph in `GlitchWarning` scene
4. No core autoload restructuring needed

### What This Architecture Avoids
- **No hardcoded room references in Player**: Player never calls `get_node("/root/Main/Levels/StartupSector")`
- **No glitch logic in LevelManager**: Level loading is glitch-agnostic
- **No global mutable state outside autoloads**: All modifiable game state lives in the four autoloads
- **No cross-level node paths**: Levels communicate only through autoload signals

---

## 8. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Godot project.godot conflicts with .opencode/ files | Low | Medium | Both coexist; .opencode/ is Git-ignored by Godot template |
| Autoload coupling becomes tangled | Medium | High | Strict one-concern-per-autoload rule; signal-first communication |
| Mobile performance issues from scene complexity | Low | Medium | Keep Startup Sector flat; profile before adding parallax/depth |
| Vertical slice scope creep | Medium | Medium | CORE-001+ define player controller; this ticket stops at architecture |

---

## 9. Implementation Approach

### Step 1: Create project.godot
Use Godot 4.x CLI to bootstrap:
```bash
godot --headless --path . --export-pack "Android" /dev/null  # triggers project.godot creation if missing
# Then configure android export preset
```

### Step 2: Create directory skeleton
```bash
mkdir -p scenes/Levels scenes/UI scenes/Hazards scenes/Checkpoints
mkdir -p scripts/autoload scripts/player scripts/ui scripts/hazards scripts/levels scripts/rooms
mkdir -p resources/configs resources/glitch_pools
mkdir -p assets/sprites assets/audio assets/fonts
```

### Step 3: Write stub autoloads
Implement each autoload with `_ready()` that prints a debug line and initializes empty state.

### Step 4: Create Main.tscn
Build the base scene tree with Player, LevelContainer, and UI layers.

### Step 5: Create Player.tscn
Minimal player: KinematicBody2D, CollisionShape2D, Sprite2D.

### Step 6: Create StartupSector.tscn
Flat room with: StaticBody2D floor, walls, checkpoint marker, spike hazard placeholder.

### Step 7: Create HUD.tscn
Minimal: Label for health, Label for glitch meter.

### Step 8: Create game_config.cfg
Centralized tunables.

### Step 9: Run validation
```bash
godot --headless --path . --quit
godot --headless --path . --import
```

### Step 10: Write implementation artifact with evidence

---

## 10. Decision Summary

| Question | Decision |
|----------|----------|
| Project Location | Repo root (`.`) as Godot project root |
| Scene Tree | Main → Player + LevelContainer + UI layers |
| Autoloads | PlayerState, GlitchState, GameState, LevelManager (4 total) |
| Directory Layout | scenes/, scripts/, resources/, assets/ + autoload subdirs |
| Initial Scenes | Main, Player, StartupSector, HUD, 4 autoloads, game_config |
| Validation | `godot --headless --path . --quit` + `--import` both return 0 |

---

## 11. Blocker Check

**None identified.**

- Godot 4.6.2 is available (SETUP-001 verified)
- Android SDK is present (SETUP-001 verified)
- Bootstrap status is `ready` (SETUP-001 closed)
- All acceptance criteria have clear implementation paths
- Architecture supports expansion without coupling
