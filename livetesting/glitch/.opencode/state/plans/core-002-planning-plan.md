# CORE-002 Planning Artifact

## Ticket
**CORE-002**: Build the glitch event system with fairness guardrails

## Stage
planning

## Overview

This plan establishes the glitch event runtime for Glitch, including event categories, telegraph system, warning surfaces, and the separation between baseline movement and temporary glitch modifiers. The system preserves the fairness contract: glitches are telegraphed, curated, and recoverable.

---

## 1. Glitch Categories

### Decision: Three Event Categories

| Category | Scope | Examples |
|----------|-------|----------|
| **Physics** | Player movement modifiers | Gravity flip, speed change, jump force modifier, friction loss |
| **Hazard** | Hazard behavior mutations | Hazard duplication, hazard movement, hazard type swap, timing shift |
| **Room Logic** | Environmental rule changes | Checkpoint displacement, platform timing change, wall softness, portal swap |

**Rationale:**
- Three categories align with the three core gameplay pillars: movement, survival, and navigation.
- Each category has distinct impact profiles and telegraph requirements.
- Curated pools are per-category, allowing fine-grained control over what can fire where.

### Category Details

**Physics Glitches:**
- Temporarily modify `PlayerDefaults` values or apply overlay modifiers
- Affect player velocity, acceleration, gravity, or friction
- Always recoverable by waiting for duration or finding a reset trigger

**Hazard Glitches:**
- Modify existing hazard behavior without spawning new collision geometry
- Examples: spike block shifts position slightly, moving platform reverses, static hazard gains movement
- Must not create invisible or instant-kill hazards

**Room Logic Glitches:**
- Modify room-level rules: checkpoint behavior, platform schedules, wall behavior
- Must not trap the player permanently
- Checkpoint displacement allows player to reset to a safe state

---

## 2. Telegraph System

### Decision: Two-Phase Telegraph (Warning → Active)

**Phase 1: Warning (1.5 seconds before glitch fires)**
- Corruption meter pulses and builds
- Screen flickers with chromatic aberration (subtle, 10% intensity)
- Digital static audio cue plays (low volume)
- Affected area glows with corruption color (cyan/magenta tint)

**Phase 2: Active (Glitch duration)**
- Full glitch effect applied
- Warning effects remain at reduced intensity
- Player can react and respond

**Rationale:**
- 1.5 seconds is enough for a mobile player to register the warning and adjust behavior
- Separate warning phase satisfies "glitch events must be telegraphed"
- Persistent warning during active phase keeps player informed

### Warning Constants
```gdscript
TELEGRAPH_DURATION: float = 1.5    # Seconds of warning before glitch fires
GLITCH_DURATION: float = 4.0         # Default glitch duration (seconds)
WARNING_PULSE_RATE: float = 4.0      # Pulses per second during telegraph
```

---

## 3. Warning Surface

### Decision: Layered Warning Stack

| Layer | Visual | Audio |
|-------|--------|-------|
| **Global** | Screen-wide chromatic aberration, corruption overlay | Digital static burst |
| **UI** | Corruption meter fills, warning icon pulses | None (silent alarm) |
| **Spatial** | Affected area glows with glitch color | None (visual-only) |
| **Category-Specific** | Physics=gravity distortion, Hazard=red tint, Room=platform flicker | Distinct sound per category |

**High-Impact vs Low-Impact Distinction:**

- **High-impact** (Physics: gravity flip, Hazard: hazard spawn, Room: checkpoint trap): Full warning stack, 2.0s telegraph
- **Low-impact** (Physics: speed change, Hazard: timing shift, Room: platform speed): Reduced warning, 1.0s telegraph

**Rationale:**
- High-impact events get stronger telegraphs per the design guardrails
- Layered approach prevents warning fatigue while ensuring readability
- Category-specific audio cues help players learn to recognize glitch types

### Warning Constants
```gdscript
HIGH_IMPACT_TELEGRAPH: float = 2.0   # Seconds for high-impact glitches
LOW_IMPACT_TELEGRAPH: float = 1.0    # Seconds for low-impact glitches
WARNING_INTENSITY_FULL: float = 1.0 # Active glitch warning
WARNING_INTENSITY_REDUCED: float = 0.4  # Reduced warning during active glitch
```

---

## 4. Separation of Concerns

### Decision: Modifier Overlay Pattern

**Architecture:**
```
Baseline (unchanged)           Glitch Overlay (temporary)
├── PlayerDefaults.gd         ├── GlitchPhysicsModifier.gd
│   (stable constants)         │   (multipliers on top of baseline)
├── PlayerController.gd        ├── GlitchHazardModifier.gd
│   (reads PlayerDefaults)     │   (hazard behavior deltas)
└── PlayerState.gd            └── GlitchRoomModifier.gd
                                (room rule overrides)
```

**Key principles:**
1. `PlayerDefaults` values are NEVER mutated at runtime
2. Glitch modifiers are additive/multiplicative overlays applied during active glitch
3. When glitch ends, modifier is removed and baseline resumes automatically
4. Multiple glitches can stack if they modify different properties (not same property twice)

**Modifier Application:**
```gdscript
# Example: Speed glitch modifier
var speed_multiplier: float = 1.0

func apply_speed_glitch(mult: float) -> void:
    speed_multiplier = mult
    # PlayerController reads: velocity.x = PlayerDefaults.SPEED * speed_multiplier

func end_speed_glitch() -> void:
    speed_multiplier = 1.0
    # Returns to baseline automatically
```

**Files affected:**
- `scripts/glitch/GlitchPhysicsModifier.gd` — physics overlay
- `scripts/glitch/GlitchHazardModifier.gd` — hazard overlay
- `scripts/glitch/GlitchRoomModifier.gd` — room logic overlay
- `scripts/glitch/GlitchEventManager.gd` — orchestrates modifiers and lifecycle

---

## 5. Recovery Space

### Decision: Guaranteed Escape + Duration Cap

**Recovery guarantees:**
1. **Duration cap**: No glitch lasts longer than `MAX_GLITCH_DURATION` (6.0 seconds)
2. **Escape trigger**: Player can always reach a safe zone within 2 seconds of reaction time
3. **No instant death**: Even hazard glitches require 1.5s telegraph before any hazard change
4. **Reset checkpoint**: Room logic glitches affecting checkpoints always preserve at least one safe checkpoint

**Recovery Constants:**
```gdscript
MAX_GLITCH_DURATION: float = 6.0    # Hard cap on any single glitch duration
MIN_RECOVERY_TIME: float = 2.0     # Minimum time for player to react
FORCED_CHECKPOINT_PRESERVE: bool = true  # Always keep one safe checkpoint
```

**Design Guardrail Compliance:**
- "Recovery space matters as much as surprise" — satisfied by duration caps and telegraph
- "Early-game glitches should not produce unavoidable instant deaths" — enforced by telegraph minimum
- "No full procedural randomness" — curated pools ensure only tested glitch combinations fire

---

## 6. Glitch Pool

### Decision: Room-Tagged Curated Pools

**Schema:**
```gdscript
# scripts/glitch/RoomGlitchConfig.gd
class_name RoomGlitchConfig
extends Resource

enum GlitchCategory { PHYSICS, HAZARD, ROOM_LOGIC }

@export var room_id: String
@export var allowed_categories: Array[GlitchCategory]
@export var physics_glitch_pool: Array[String]  # e.g., ["speed_down", "gravity_flip"]
@export var hazard_glitch_pool: Array[String]    # e.g., ["spike_shift", "platform_reverse"]
@export var room_logic_glitch_pool: Array[String]  # e.g., ["checkpoint_drift", "wall_soft"]
@export var max_simultaneous_glitches: int = 2
@export var min_glitch_interval: float = 8.0   # Minimum seconds between glitch events
```

**Pool Selection Logic:**
1. Room defines its `RoomGlitchConfig` resource
2. `GlitchEventManager` queries config for allowed categories and pools
3. Random selection from pool (curated, not random generation)
4. Cooldown prevents same glitch from firing twice in quick succession

**Rationale:**
- Hand-authored pools prevent unfair combinations
- Per-room configuration allows difficulty scaling
- `max_simultaneous_glitches` prevents overwhelming the player

---

## 7. Integration with GlitchState

### Decision: Extend, Don't Replace

**Existing GlitchState (autoload):**
```gdscript
# Already has:
- corruption_level (0-100)
- active_glitches: Array
- glitch_cooldowns: Dictionary
- Signals: glitch_started, glitch_ended, corruption_level_changed
- Methods: apply_glitch(), end_glitch(), set_corruption(), is_glitch_active()
```

**New Integration Points:**

| GlitchState Feature | GlitchEventManager Usage |
|---------------------|--------------------------|
| `glitch_started` signal | Listener triggers modifier application |
| `glitch_ended` signal | Listener triggers modifier cleanup |
| `corruption_level` | Warning intensity scales with corruption level |
| `active_glitches` | Tracks which glitches are currently affecting gameplay |
| `is_glitch_active()` | Check before applying new glitch (no duplicates) |

**Data Flow:**
```
GlitchEventManager
    ├── picks glitch from RoomGlitchConfig pool
    ├── calls GlitchState.apply_glitch(event_id)  [registers globally]
    ├── emits "glitch_telegraph_started" signal   [triggers warning UI]
    ├── after TELEGRAPH_DURATION, applies modifier via category-specific modifier
    ├── after GLITCH_DURATION, removes modifier
    └── calls GlitchState.end_glitch(event_id)    [unregisters globally]
```

**Files created/affected:**
- `scripts/glitch/GlitchEventManager.gd` — new, orchestrates lifecycle
- `scripts/glitch/RoomGlitchConfig.gd` — new, room configuration resource
- `scripts/glitch/GlitchPhysicsModifier.gd` — new, physics overlay
- `scripts/glitch/GlitchHazardModifier.gd` — new, hazard overlay  
- `scripts/glitch/GlitchRoomModifier.gd` — new, room logic overlay
- `scenes/glitch/TelegraphEffect.tscn` — new, visual warning scene
- `scripts/autoload/GlitchState.gd` — unchanged (already has needed signals)

---

## 8. Event Schema

### Decision: Data-Driven Glitch Events

```gdscript
# scripts/glitch/GlitchEvent.gd
class_name GlitchEvent
extends Resource

enum ImpactLevel { LOW, HIGH }
enum Category { PHYSICS, HAZARD, ROOM_LOGIC }

@export var event_id: String
@export var display_name: String
@export var description: String
@export var category: Category
@export var impact_level: ImpactLevel
@export var telegraph_duration: float
@export var duration: float
@export var modifier_config: Dictionary  # Category-specific parameters

# Example modifier_config for PHYSICS speed_glitch:
# { "property": "speed", "multiplier": 0.5, "affected_systems": ["player"] }
```

**Event Definitions (curated, not procedural):**
```gdscript
# resources/glitch/events/speed_down.tres
event_id = "speed_down"
display_name = "Lag Spike"
description = "Network latency simulated. Movement speed reduced."
category = Category.PHYSICS
impact_level = ImpactLevel.LOW
telegraph_duration = 1.0
duration = 4.0
modifier_config = { "property": "speed", "multiplier": 0.5 }

# resources/glitch/events/gravity_flip.tres
event_id = "gravity_flip"
display_name = "Gravity Inversion"
description = "Gravity is temporarily inverted."
category = Category.PHYSICS
impact_level = ImpactLevel.HIGH
telegraph_duration = 2.0
duration = 4.0
modifier_config = { "property": "gravity", "multiplier": -1.0 }
```

---

## 9. File Structure

```
scripts/glitch/
  GlitchEvent.gd              # Event data resource
  GlitchEventManager.gd       # Lifecycle orchestration
  GlitchPhysicsModifier.gd    # Physics overlay
  GlitchHazardModifier.gd     # Hazard overlay
  GlitchRoomModifier.gd       # Room logic overlay
  RoomGlitchConfig.gd         # Per-room configuration

scenes/glitch/
  TelegraphEffect.tscn        # Visual warning scene

resources/glitch/
  events/
    speed_down.tres
    gravity_flip.tres
    spike_shift.tres
    # ... more curated events
  room_configs/
    StartupSector.tres         # Room-specific glitch pools
```

---

## 10. Validation Plan

### Validation 1: Godot Headless Startup
**Command:** `godot --headless --path . --quit`
**Expected:** No errors. GlitchState and GlitchEventManager initialize without warnings.

### Validation 2: Scene Import Check
**Command:** `godot --headless --path . --import`
**Expected:** All scenes import including TelegraphEffect.tscn.

### Validation 3: Event Resource Load
**Proof:** Load `speed_down.tres` resource and verify fields deserialize correctly.

### Validation 4: GlitchState Integration Smoke
**Proof:** Create GlitchEventManager in headless script, verify it connects to GlitchState signals without error.

### Validation 5: Telegraph Phase Duration
**Proof:** Trigger a test glitch event and verify telegraph_duration is respected before modifier applies.

### Validation 6: Modifier Separation
**Proof:** With speed_glitch active, verify PlayerDefaults.SPEED is unchanged but effective speed is halved.

---

## 11. Risks and Open Questions

### Risk: Modifier Stack Conflicts
- Two glitches modifying same property could conflict.
- **Mitigation:** GlitchEventManager tracks active modifiers by property; newer glitch wins or conflicts are rejected.

### Risk: Screen Effects Impact Mobile Readability
- Chromatic aberration and flicker could hurt mobile playability.
- **Mitigation:** Warning effects are subtle (10-20% intensity) and never hide collision surfaces.

### Open Question: Cooldown Per-Room or Global
- Should glitch cooldown reset when player enters new room, or persist globally?
- **Decision:** Cooldown is global (per GlitchState), preventing the same glitch from firing twice in quick succession across rooms.

### Open Question: Glitch Frequency Scaling
- Should corruption level increase glitch frequency over time?
- **Decision:** Frequency scaling is out of scope for CORE-002; CORE-003 room flow will handle difficulty progression.

---

## 12. Blockers and Required Decisions

**None for planning stage.** All decisions are resolved:

| Decision | Resolution |
|----------|-------------|
| Event categories | Physics, Hazard, Room Logic (three categories) |
| Telegraph system | Two-phase (warning → active), 1.5s default |
| Warning surface | Layered: global/UI/spatial/category-specific |
| Separation pattern | Modifier overlay, PlayerDefaults unchanged |
| Recovery guarantees | Duration cap (6s), min reaction time (2s), telegraph minimum |
| Glitch pool | Room-tagged curated pools via RoomGlitchConfig |
| GlitchState integration | Extend via signals (glitch_started, glitch_ended) |
| Validation | Headless startup + resource load + modifier separation |

---

## 13. Acceptance Criteria Checklist

| # | Criterion | Status |
|---|-----------|--------|
| 1 | At least one telegraphed glitch event from each planned category can be represented by the runtime or content schema | Plan defines GlitchEvent resource with category enum; three example events defined |
| 2 | The system separates baseline movement from temporary glitch modifiers | Modifier overlay pattern keeps PlayerDefaults unchanged |
| 3 | High-impact glitch events expose a warning or anticipation surface | Two-phase telegraph + layered warning stack for HIGH impact events |
| 4 | Validation covers event triggering without breaking normal project startup | Headless startup + import checks + modifier separation proof planned |

---

## 14. Dependencies

- **Depends on**: SETUP-001 (done), SYSTEM-001 (done), CORE-001 (done)
- **Blocks**: CORE-003 (room flow needs glitch system), CONTENT-001 (vertical slice needs glitch events)

---

## 15. Next Stage

After plan approval and `ticket_update stage=plan_review approved_plan=true`:
- Transition to `implementation`
- Create `GlitchEvent.gd` resource class
- Create `GlitchPhysicsModifier.gd`, `GlitchHazardModifier.gd`, `GlitchRoomModifier.gd`
- Create `GlitchEventManager.gd` with telegraph timer and signal integration
- Create `RoomGlitchConfig.gd` resource
- Create `TelegraphEffect.tscn` scene for visual warnings
- Create three example glitch event resources (one per category)
- Run validation commands

(End of file - total 394 lines)