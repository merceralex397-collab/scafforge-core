---
name: docs-and-handoff
description: Maintain Glitch restart surfaces, board views, and closeout-facing docs so the repo stays immediately continuable.
---

# Docs And Handoff

Before refreshing handoff artifacts, call `skill_ping` with `skill_id: "docs-and-handoff"` and `scope: "project"`.

Keep these artifacts fresh:

- `START-HERE.md`
- `.opencode/state/context-snapshot.md`
- `.opencode/state/latest-handoff.md`
- `tickets/BOARD.md`
- `tickets/manifest.json`

Rules:

- derive handoff state from canonical manifest and workflow-state, not memory
- keep the read order stable and truthful
- when Glitch scope changes, make sure the handoff still points to the current vertical-slice target and active dependency chain
