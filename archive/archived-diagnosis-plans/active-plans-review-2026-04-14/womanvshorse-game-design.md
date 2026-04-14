# Woman vs Horse — Game Design Document

## Concept
A simple Android action game where a woman fights waves of enemy horses. Each wave brings more and tougher horses. The player controls the woman, dodges attacks, and defeats horses to progress.

## Core Loop
1. **Spawn wave** — N horses approach from screen edges
2. **Fight** — Player attacks horses, dodges charges
3. **Survive** — Clear all horses in the wave
4. **Upgrade** — Brief pause, optional power-up pickup
5. **Next wave** — Repeat with increased difficulty

## Player Character: The Woman
- **Movement**: 8-directional, touch joystick (left side of screen)
- **Attack**: Melee swing (tap right side) + ranged throw (hold right side)
- **Health**: 3 hearts, displayed top-left
- **Speed**: Moderate, faster than horses
- **Visual**: Warrior woman with sword/spear

## Enemy: Horses
- **Behavior**: Charge toward player in straight lines
- **Variants**:
  - **Brown Horse** (basic) — slow charge, 1 hit to defeat
  - **Black Horse** (fast) — fast charge, 1 hit to defeat
  - **War Horse** (tank) — slow charge, 3 hits to defeat, has armor
  - **Boss Horse** (wave 5, 10, 15...) — large, special attack patterns
- **Spawn**: From screen edges, increasing count per wave

## Wave System
- Wave 1: 3 brown horses
- Wave 2: 5 brown horses
- Wave 3: 3 brown + 2 black
- Wave 4: 4 brown + 3 black
- Wave 5: BOSS + 2 brown escorts
- Pattern continues with war horses from wave 6+

## Controls (Touch)
- Left half: Virtual joystick for movement
- Right half tap: Melee attack (directional, toward nearest enemy)
- Right half hold+release: Ranged attack (directional throw)

## UI/HUD
- Health hearts (top-left)
- Wave counter (top-center)
- Score (top-right)
- Game Over screen with score and restart button
- Title screen: "WOMAN vs HORSE" with START button

## Art Style
- Low-poly 3D (VersionC) or 2D top-down sprites (VersionA/B)
- Flat grass arena with fence border
- Simple particle effects for hits
- Camera: Fixed top-down orthographic

## Audio
- Background music: Simple loop
- SFX: Attack hit, horse charge, damage taken, wave complete, game over

## Platform
- Android (Godot 4.6 export)
- Portrait or landscape orientation (landscape preferred)
- Touch controls only

## Technical Scope (per version)
- Single scene (arena)
- No save system needed
- No multiplayer
- No IAP
- Simple state machine: Title → Playing → GameOver → Title

## Version Differences

### VersionA (Codex-derived ideas)
- 2D top-down view
- Procedural/programmatic sprites (colored shapes, basic animations)
- Focus on clean game mechanics from Codex game-studio patterns
- Sprite pipeline from Scafforge possibleassethelp material

### VersionB (Free/open-source assets)
- 2D top-down view
- Assets sourced from Kenney.nl, OpenGameArt.org
- Proper sprite sheets, tilesets, audio from free sources
- Full provenance tracking in assets/PROVENANCE.md

### VersionC (Blender-MCP generated)
- 3D low-poly view
- Characters and props generated via blender-agent MCP
- Exported as .glb, imported into Godot
- Asset briefs drive Blender tool sequences

### VersionD (Godot tools/features)
- 2D or 2.5D view
- Assets created with Godot built-in tools
- CSG for 3D elements, particles for effects
- Shader-based procedural textures
- TileMap for arena floor
