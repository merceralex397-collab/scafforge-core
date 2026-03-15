# Git Capability

This scaffold assumes **local git read/write** is available by default.

Default scope:

- inspect status and diff state
- create local commits when the active ticket is ready
- use local history as supporting evidence during review and QA

Not assumed by default:

- GitHub issue automation
- pull request automation
- remote push or merge automation

Rules:

- keep git operations aligned with the active ticket
- treat destructive git operations as separately gated, not routine automation
- do not treat git metadata as a substitute for ticket, workflow, or artifact state
