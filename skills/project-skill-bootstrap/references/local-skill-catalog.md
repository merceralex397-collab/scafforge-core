# Default Local Skill Catalog

The default full-orchestration profile should expose these lanes, but heavier packs should stay thin or lazy-activated until the project clearly needs more depth.

## project-context

- repo mission
- canonical docs
- current state

## repo-navigation

- reading order
- major directories
- common queries

## stack-standards

- framework and language rules
- testing and validation commands

## model-operating-profile

- the selected downstream model operating profile for this repo
- concrete instruction-shaping rules tied to the chosen model family
- example-led guidance when the chosen profile benefits from it

## ticket-execution

- required stage order
- bootstrap-first routing when bootstrap is not `ready`
- artifact expectations

## review-audit-bridge

- evidence-first review ordering
- code review, security review, and QA output structure
- blocker rules when required artifacts or validation are missing
- remediation-ticket recommendations tied back to current evidence
- repo-local process-log guidance for explaining workflow failures without mutating canonical queue state

## docs-and-handoff

- `START-HERE.md`
- milestone summaries
- resume guidance

## workflow-observability

- `.opencode/meta/bootstrap-provenance.json`
- `.opencode/state/invocation-log.jsonl`
- process-version and migration verification state
- unused or never-seen tool/agent/skill surfaces

## research-delegation

- read-only background research patterns
- artifact persistence for delegated findings
- compaction-safe research summaries

## local-git-specialist

- local git read/write workflow
- safe commit and branch hygiene
- explicit boundary: local git only unless the repo enables more

## isolation-guidance

- worktree or sandbox patterns for risky changes
- when to isolate versus work in-place
- lightweight default guidance for autonomous runs

## optional synthesized review extensions

- add repo-specific review references when the project has unusual security, QA, or compliance rules
- keep heavier diagnosis or remediation examples in the generated skill's `references/` folder rather than adding a package-level doctor skill back into Scafforge
