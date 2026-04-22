# OpenCode Agent System

The default generated system contains:

- a visible `team-leader`
- phase specialists for planning, review, implementation, QA, and handoff
- utility specialists for exploration, shell inspection, summarization, ticket auditing, GitHub research, and web research

Delegation defaults:

- only the leader and selected planner/reviewer roles delegate
- implementers do not fan out
- utility agents do not recurse
- keep the default set conservative enough that weaker models can choose the right role without browsing a crowded roster
- add a new generated agent only when it owns a distinct workflow or truth-domain concern; otherwise merge the guidance into an existing role or repo-local skill
- package-level skill evolution remains separate from generated repo-local agent design
