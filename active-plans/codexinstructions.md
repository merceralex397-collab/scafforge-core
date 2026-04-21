# Codex Implementation Instructions For Active Plans

This document is the working execution guide for implementing the numbered plans under `active-plans/`.

It is intentionally procedural. The numbered plan folders remain the canonical scope and requirements. This file defines how to execute them with `agent-caller`, how to review AI feedback, and how to move from plan review to implementation to PR review without turning those CLIs into unquestioned authority.

## Core operating rules

1. Treat each numbered plan `README.md` as the scope boundary for that plan.
2. Use `agent-caller` as a local token-saving wrapper only. It is not a product feature and does not need cross-platform packaging discipline.
3. Verify every external-model claim yourself. `planchecker` and `planprreviewer` are advisors, not sources of truth.
4. Prefer non-interactive, automation-friendly, and headless-capable workflows by default so plan execution stays cheap and agent-usable, but do not assume Ubuntu/Linux unless the plan or repo actually requires it.
5. Do not introduce paid assets or proprietary asset dependencies into the core plans. Asset recommendations and pipeline defaults must stay free or open-source unless a plan explicitly justifies an exception.
6. Keep package-repo and generated-repo boundaries intact at all times. Scafforge changes belong in this repo or in named adjacent repos; generated-repo behavior changes must come from package or template changes.
7. When a plan targets an adjacent repository such as `Meta-Skill-Engineering` or `blender-agent`, make the implementation there and update Scafforge docs only where the cross-repo contract changes.
8. Do not mark a plan complete until its validation gates, documentation updates, and residual-risk review are complete.

## Required tooling

- `copilot` CLI for `planchecker` and `planimplementer`
- `opencode` CLI for `planprreviewer`
- `gh` CLI for PR inspection and comment posting
- `uv` for installing the local `agent-caller` wrapper

Install the local wrapper from the Scafforge repo root:

```powershell
uv tool install --force --editable .\tools\agent-caller
```

Smoke-test the wrapper before starting a full cycle:

```powershell
agent-caller planchecker --plan 02 --dry-run
agent-caller planimplementer --plan 01 --dry-run
agent-caller planprreviewer --plan 02 --pr 123 --owner-repo owner/repo --dry-run
```

## Prompt packs

Each numbered plan folder should contain:

```text
active-plans/<plan-folder>/references/agent-caller-prompts.md
```

Those prompt packs are the canonical prompt surfaces for:

- `planchecker`
- `planimplementer`
- `planprreviewer methodology`
- one reviewer prompt per review model

When a plan changes materially, update its prompt pack in the same PR if the review or implementation emphasis should also change.

## Execution workflow

### Stage 1: Plan review

1. Skip `01` for formal checker use unless it becomes materially more complex.
2. Run `planchecker` on one plan at a time starting at `02`.
3. Review the findings manually against the plan text, repo state, and source references.
4. Classify each finding:
   - factual and must be fixed in the plan
   - reasonable but optional strengthening
   - incorrect or unsupported and should be ignored
5. If the checker finds a real plan defect, revise the plan before implementation begins.
6. Continue through the remaining plans one by one.

Example:

```powershell
agent-caller planchecker --plan 02
agent-caller planchecker --plan 03
agent-caller planchecker --plan 04
```

### Stage 2: Implementation

1. Begin implementation with `01`.
2. Then continue upward plan by plan, unless a plan’s own dependency section blocks immediate work.
3. Before running `planimplementer`, read the plan again yourself and confirm the target repo and validation surfaces.
4. Use `planimplementer` to execute the plan’s implementation prompt.
5. Review the resulting work directly in code and docs before preparing a PR.

Examples:

```powershell
agent-caller planimplementer --plan 01
agent-caller planimplementer --plan 02 --model gpt-5.4
agent-caller planimplementer --plan 03 --model claude-sonnet-4.6
```

### Stage 3: Local verification before PR

1. Run the validation commands named by the plan.
2. Check changed docs, references, and prompts for contract drift.
3. Review the diff yourself with a findings-first mindset.
4. Fix obvious defects before asking GitHub reviewers to spend time on the PR.
5. Do not open a PR that still fails its own stated gates unless the failure is a named blocker recorded in the PR body.

### Stage 4: PR creation

1. Create a focused PR for the plan that was just implemented.
2. The PR description should name:
   - the plan ID and title
   - the touched repo or repos
   - the validation that passed
   - any remaining bounded risks
3. Keep one plan per PR unless the plan itself explicitly bundles multiple repos or contract surfaces that must land together.

### Stage 5: Multi-model PR review

After the PR exists, run:

```powershell
agent-caller planprreviewer --plan 02 --pr 123 --owner-repo owner/repo
```

Default reviewer set:

- `big-pickle`
- `minimax-m2.7`
- `devstral-2512`
- `mistral-large-latest`
- `kimi-k2.5-turbo`

Rules:

1. Each reviewer produces exactly one top-level PR comment body, and `agent-caller` posts it with `gh pr comment`.
2. These comments are advisory only.
3. Reviewers should focus on high-confidence, evidence-backed findings.
4. If a reviewer cannot support a claim from the diff and repo context, that claim should not drive changes.

## Reviewer triage method

For each model comment:

1. Extract the concrete claim.
2. Check the actual diff, changed files, tests, docs, and plan requirements.
3. Mark the claim as:
   - verified defect
   - open question needing more evidence
   - false or irrelevant concern
4. Fix verified defects.
5. Reply or document why rejected concerns were not adopted when useful for review traceability.

Do not let “five models agreed” substitute for proof.

## Completion loop per plan

The intended loop is:

1. `planchecker` reviews plans one by one, starting at `02`
2. plan fixes are applied if the findings are real
3. `planimplementer` implements the next plan in sequence
4. direct self-review and validation happen locally
5. PR is opened
6. `planprreviewer` runs the five-model review swarm
7. comments are verified manually
8. verified issues are fixed
9. PR is merged only after the plan’s real gates pass
10. move to the next plan

## Plan-order guidance

There are two valid orderings to keep in mind:

- review order: `02` through `14`, with `01` skipped for initial checker use
- implementation queue: start at `01`, then continue upward unless an unmet dependency in the plan explicitly forces a reorder

If the numeric queue and the dependency graph conflict, the dependency graph wins and the reason must be documented.

## Adjacent repository rules

Plans `13` and `14` target separate repositories:

- `Meta-Skill-Engineering`
- `blender-agent`

When working those plans:

1. create or switch to a branch in the adjacent repo
2. implement the work there
3. validate there
4. open the PR there
5. update Scafforge references only where the external contract or program status changes

Do not fake completion in Scafforge for work that still has not landed in the adjacent repo.

## Documentation obligations

Every implemented plan must also update:

- any directly affected root docs
- affected reference docs
- any generated-template docs whose contract changed
- the relevant plan prompt pack if the review emphasis changed
- `active-plans/README.md` and `FULL-REPORT.md` when ordering, program assumptions, or cross-plan status materially change

## Failure and blocker handling

Stop and record a blocker when:

- the plan depends on an unmet prior contract
- the CLI output is contradictory or clearly hallucinated
- a required validator cannot run for an environmental reason
- adjacent repo state conflicts with the plan’s assumptions
- the PR reviewer claims cannot be verified from evidence

A blocker record should name:

- the plan
- the exact blocked step
- the evidence
- the next required action

## Definition of done for one plan cycle

One plan cycle is done only when:

- the plan is still accurate after implementation
- the code and docs match the plan’s stated contract
- required validations have passed or the remaining blocker is explicitly recorded
- the PR has been reviewed and verified
- reviewer findings have been triaged rather than blindly accepted
- the repo truth surfaces are updated

This file is the operating guide. The numbered plan folders remain the actual implementation contracts.
