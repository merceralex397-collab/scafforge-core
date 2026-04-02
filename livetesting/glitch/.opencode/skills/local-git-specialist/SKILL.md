---
name: local-git-specialist
description: Follow the repo's local Git workflow safely while keeping Glitch ticket scope and generated surfaces aligned.
---

# Local Git Specialist

Before using local Git workflow guidance, call `skill_ping` with `skill_id: "local-git-specialist"` and `scope: "project"`.

Use this lane when:

- checking local status or diff state
- preparing a local commit
- verifying what changed for the current Glitch ticket

Rules:

- treat Git work as local read/write unless the repo explicitly enables more
- keep commit scope aligned with one active ticket whenever possible
- when work touches both gameplay code and workflow surfaces, verify the ticket actually owns both
- use Git state as supporting evidence, not as a substitute for ticket, workflow-state, or artifact updates
