# Four-Report Templates

Use these templates when `scafforge-audit` writes or expands a diagnosis pack under `diagnosis/<timestamp>/`.

The file names are fixed:

- `01-initial-codebase-review.md`
- `02-scafforge-process-failures.md`
- `03-scafforge-prevention-actions.md`
- `04-live-repo-repair-plan.md`
- `manifest.json`

## Common requirements

Every report should include:

- subject repo path or identifier
- diagnosis timestamp
- audit scope and verification scope
- result state: `validated failures found`, `no validated failures found`, or `inconclusive or partially verified`
- evidence grades where claims are discussed
- explicit file references or workflow-surface references

## Report 1 template

File: `01-initial-codebase-review.md`

Required sections:

- `# Initial Codebase Review`
- `## Scope`
- `## Result State`
- `## Validated Findings`
- `## Verification Gaps`
- `## Rejected or Outdated External Claims` when review evidence was supplied

Each validated finding should include:

- finding id
- summary
- severity
- evidence grade
- affected file or workflow surface
- what was observed or reproduced
- remaining verification gap, if any

## Report 2 template

File: `02-scafforge-process-failures.md`

Required sections:

- `# Scafforge Process Failures`
- `## Scope`
- `## Failure Map`
- `## Ownership Classification`
- `## Root Cause Analysis`

Each mapped issue should include:

- linked Report 1 finding id
- implicated Scafforge skill, template, script, contract, or generated surface
- ownership class
- explanation of how the workflow allowed the issue through

## Report 3 template

File: `03-scafforge-prevention-actions.md`

Required sections:

- `# Scafforge Prevention Actions`
- `## Package Changes Required`
- `## Validation and Test Updates`
- `## Documentation or Prompt Updates`
- `## Open Decisions`

Each action should include:

- action id
- change target in the Scafforge package
- why it prevents recurrence
- whether it is safe or intent-changing
- how it should be validated

## Report 4 template

File: `04-live-repo-repair-plan.md`

Required sections:

- `# Live Repo Repair Plan`
- `## Preconditions`
- `## Package Changes Required First`
- `## Post-Update Repair Actions`
- `## Ticket Follow-Up`
- `## Reverification Plan`

Each repair item should include:

- linked Report 1 or Report 2 ids
- action type:
  - `safe Scafforge package change`
  - `intent-changing package change`
  - `generated-repo remediation ticket/process repair`
- whether `scafforge-repair` should run
- whether the user must manually carry the diagnosis pack into the Scafforge dev repo first
- the target repo for the action: Scafforge package repo or subject repo

## Manifest expectations

`manifest.json` should map the fixed report filenames, summarize the result state, and list any ticket recommendations or supporting logs.
