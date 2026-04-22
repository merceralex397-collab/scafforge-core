# Default Local Skill Catalog

The default full-orchestration profile should expose these lanes, but heavier packs should stay thin or lazy-activated until the project clearly needs more depth.

## Catalog guardrails

- the default baseline pack stays at or below 12 lanes; new baseline lanes must replace or merge overlapping ones instead of only growing the catalog
- add a synthesized local skill only when it creates a genuinely distinct workflow, trigger, or truth-owner need for this repo
- if a candidate skill would share the same owner and trigger as an existing lane, extend the existing lane instead of creating a near-duplicate name

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
- team-leader ownership of `ticket_claim` / `ticket_release`
- Wave 0-only pre-bootstrap write claims
- repeated lifecycle-contradiction stop rule
- explicit failure recovery paths for review, QA, and smoke-test stages
- `ticket_lookup.transition_guidance.recovery_action` routing
- `smoke_test` as the only producer of passing smoke artifacts
- process-remediation and reverification smoke scoped only to commands that are valid at the current backlog state, not broader product boot probes that are expected to fail while prerequisite feature tickets remain open
- slash commands treated as human entrypoints only

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

## asset-workflow

- `assets/requirements.json`, `assets/pipeline.json`, and `assets/manifest.json` as the canonical asset truth stack when the repo is asset-heavy
- source-route versus pipeline-stage distinctions for weaker-model-safe asset routing
- `assets/workflows/`, `assets/previews/`, and `assets/qa/` usage for machine-checkable import and compliance proof
- `.opencode/meta/asset-provenance-lock.json` as the process-contract lock for asset truth
- visual-proof expectations for reviewable repos, including structured QA artifact fields and screenshot/render evidence
- truthful Blender usage routed through `blender-support-matrix.md` and the repo-local workflow note instead of broad DCC promises

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
