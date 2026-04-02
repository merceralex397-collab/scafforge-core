---
name: godot-architecture
description: Guide scene structure, autoload boundaries, and reusable game-system design for the Glitch Godot project.
---

# Godot Architecture

Before using this skill, call `skill_ping` with `skill_id: "godot-architecture"` and `scope: "project"`.

Use this skill when planning or implementing:

- scene tree layout
- autoload singletons
- checkpoint and progression state
- reusable movement, hazard, and glitch-system modules

Rules:

- keep scene ownership explicit; avoid hidden dependencies between distant nodes
- isolate reusable systems such as glitch state, checkpoint state, and player abilities behind clear interfaces
- prefer reusable room metadata and curated event pools over hardcoded one-off room logic
- design for vertical-slice delivery first, but avoid painting later zones into an architectural corner
