# Scafforge Work Log

## What this file is

This is a full plain-English record of the implementation work completed for the current Scafforge roadmap.

The goal of this file is to explain, in simple terms, what was changed, why it was changed, and how it maps back to `devdocs/scafforge-implementation-plan.md`.

---

## Starting point

At the start of this implementation pass, Scafforge already had a good overall direction, but it still had an important gap:

- the long plan said what the repo should become
- the actual repo only implemented some of that contract
- several core skills and template assets still reflected the older version of the workflow

In simple terms:

Scafforge knew where it wanted to go, but parts of the real repo were still behind the plan.

---

## Step 1 - Locked the product contract into the real repo

### What I changed

I updated the main package docs and the core skill contracts so the repo clearly says the same thing everywhere about what Scafforge is.

This included changes to:

- `README.md`
- `AGENTS.md`
- `skills/scaffold-kickoff/SKILL.md`
- `skills/spec-pack-normalizer/SKILL.md`
- `skills/ticket-pack-builder/SKILL.md`
- `skills/project-skill-bootstrap/SKILL.md`
- `skills/repo-process-doctor/SKILL.md`

### Why this mattered

The plan said Scafforge should be:

- host-agnostic as a generator
- OpenCode-only as an output target for v1
- based on one full scaffold cycle
- strict about ambiguity
- explicit about truth ownership

Those ideas now live in the actual repo instructions, not only in the plan.

### Plain-English result

Scafforge now explains itself more clearly and behaves more like a real product instead of a loose collection of ideas.

---

## Step 2 - Made the generated repo truth model explicit

### What I changed

I defined, in both package docs and generated template docs, exactly which files own which kind of information.

That work touched:

- package docs (`README.md`, `AGENTS.md`)
- generated template docs (`skills/repo-scaffold-factory/assets/project-template/...`)

The generated repo now clearly says:

- `docs/spec/CANONICAL-BRIEF.md` owns durable facts and decisions
- `tickets/manifest.json` owns machine-readable queue state
- `tickets/BOARD.md` is the human-facing board
- `.opencode/state/workflow-state.json` owns transient stage and approval state
- stage-specific state directories own artifact bodies
- `.opencode/state/artifacts/registry.json` owns artifact registry metadata
- `START-HERE.md` is the derived restart surface

### Why this mattered

One of the biggest plan requirements was to stop documents from contradicting one another.

This only works if every kind of information has one clear owner.

### Plain-English result

The generated repo is now much less likely to end up with three different files all pretending to be “the real source of truth.”

---

## Step 3 - Added the missing one-cycle flow mechanics

### What I changed

I turned the intended one-cycle flow into real repo structure by:

- making `scaffold-kickoff` route through ticket generation and local skill bootstrapping during the first run
- giving `ticket-pack-builder` explicit `bootstrap` and `refine` modes
- giving `project-skill-bootstrap` explicit `foundation` and `synthesis` modes
- adding a machine-readable flow manifest at `skills/skill-flow-manifest.json`

### Why this mattered

The plan said the first scaffold should already leave behind:

- the repo structure
- the OpenCode layer
- the ticket pack
- the workflow skill pack
- the handoff surface

Before this pass, parts of that still read like “maybe later” work.

### Plain-English result

Scafforge now treats the first scaffold as a full birth of the repo, not as a half-finished starter pack.

---

## Step 4 - Improved ambiguity handling

### What I changed

I strengthened the normalization and ticketing contracts so Scafforge is much stricter about unclear inputs.

This included:

- explicit decision packets
- backlog-readiness signals
- rules that unresolved major choices must become blockers or decision tickets
- prompt rules that say “return a blocker instead of guessing”

### Why this mattered

The user requirement was very clear:

Scafforge must never quietly guess when the input leaves a meaningful choice open.

### Plain-English result

If the input is unclear in an important way, Scafforge is now much more likely to stop and say so clearly instead of pretending it knows what the user meant.

---

## Step 5 - Hardened prompts for weaker models

### What I changed

I updated the generated agent prompts so they are more structured and less likely to drift.

I strengthened:

- planner
- plan review
- implementer
- code reviewer
- security reviewer
- QA
- docs and handoff

I also added:

- `skills/agent-prompt-engineering/references/weak-model-profile.md`

### What changed in the prompts

The prompts now more clearly require:

- blockers instead of hidden guessing
- explicit output sections
- stage proof awareness
- no premature “summary and stop” behavior
- no moving to the next stage without the required artifact or state

### Why this mattered

The plan repeatedly emphasized that weaker models need:

- clearer rails
- shorter but more operational prompts
- less room for interpretation

### Plain-English result

The generated agents now have stronger “do the next correct step or report a blocker” behavior.

---

## Step 6 - Reworked artifact architecture into the planned hybrid model

### What I changed

I changed the generated workflow tooling so artifact handling now uses:

- stage-specific directories for readability
- a registry file for machine-readable lookup

The generated scaffold now creates and uses:

- `.opencode/state/plans/`
- `.opencode/state/implementations/`
- `.opencode/state/reviews/`
- `.opencode/state/qa/`
- `.opencode/state/handoffs/`
- `.opencode/state/artifacts/registry.json`

I updated:

- workflow tool helpers
- artifact registration behavior
- generated docs
- doctor references
- audit rules

### Why this mattered

The plan specifically called for a hybrid model:

- readable stage-specific storage
- plus a registry for reliable machine use

Before this pass, the implementation was still using a simpler single artifact-root approach.

### Plain-English result

Artifacts are now easier for both humans and tools to understand.

Humans can browse by stage.

Tools can still look things up in one machine-readable registry.

---

## Step 7 - Removed hidden model defaults

### What I changed

I removed the hardcoded MiniMax default from the scaffold scripts and made runtime-model selection explicit.

The bootstrap scripts now require:

- provider
- planner model
- implementer model

They also support:

- a separate utility/helper model

I updated:

- scaffold scripts
- OpenCode bootstrap wrapper
- template model docs
- canonical brief template
- bootstrap provenance output
- generated utility/QA/docs agent model placeholders

### Why this mattered

The plan said provider/model choice must never be silently buried.

Before this pass, the scripts still quietly defaulted to MiniMax.

### Plain-English result

Scafforge no longer secretly picks a model for the user at render time.

The runtime model choice is now something that has to be stated openly.

---

## Step 8 - Added the missing default local skill lanes

### What I changed

The refined product contract said the default full profile should expose:

- research delegation
- local git specialist guidance
- isolation guidance

Those lanes were described in the docs, but the generated template did not actually include them yet.

I fixed that by adding:

- `.opencode/skills/research-delegation/SKILL.md`
- `.opencode/skills/local-git-specialist/SKILL.md`
- `.opencode/skills/isolation-guidance/SKILL.md`

I also wired the relevant agents to be allowed to use them.

### Why this mattered

It is bad for docs to promise generated capabilities that the template does not actually ship.

### Plain-English result

The default scaffold now really includes the lanes the updated docs say it includes.

---

## Step 9 - Added a clearer local-git-only baseline

### What I changed

I added an explicit generated doc:

- `docs/process/git-capability.md`

I also updated generated repo read order so this becomes part of the normal operating context.

### Why this mattered

The plan said v1 should support local git, but not assume GitHub automation.

That needed to be written down clearly inside the generated repo.

### Plain-English result

The generated repo now explains:

- what git automation is expected
- what is allowed by default
- what is intentionally *not* assumed

---

## Step 10 - Separated core package and host adapters

### What I changed

I created a clearer adapter split by adding:

- `adapters/manifest.json`
- `adapters/README.md`

I also added:

- `package.json`
- `bin/scafforge.mjs`

### Why this mattered

The plan said the core generator and host adapters should be separate concepts.

It also said installation should move toward packaged npm-style usage.

### Plain-English result

The repo now has:

- a clearer adapter boundary
- a machine-readable adapter contract
- a basic package-style wrapper command so the repo is closer to a real installable tool

---

## Step 11 - Added OpenCode conformance and contract validation

### What I changed

I added:

- `skills/repo-scaffold-factory/references/opencode-conformance-checklist.json`
- `scripts/validate_scafforge_contract.py`

The validator checks:

- key docs exist
- key template surfaces exist
- flow manifest exists and matches the skill files
- truth hierarchy and contract sections exist where expected
- legacy hidden defaults and stale wording are not still lingering in the active repo surfaces

### Why this mattered

The plan said OpenCode correctness should be checked deliberately, not trusted casually.

### Plain-English result

Scafforge now has a repeatable way to catch contract drift instead of relying on memory.

---

## Step 12 - Added a real smoke-test harness

### What I changed

I added:

- `scripts/smoke_test_scafforge.py`

This script:

1. creates temporary test repos
2. renders a full scaffold
3. renders an OpenCode-only scaffold
4. checks the important generated files and directories
5. checks the manifest structure

### Why this mattered

The plan called for real fixture generation tests.

A generator should prove it can still generate, not just claim it.

### Plain-English result

Scafforge now has a basic “does the generator still actually work?” test.

---

## Step 13 - Updated historical top-level notes so they no longer mislead

### What I changed

I updated:

- `TASKS.md`
- `REVIEW-NOTES.md`

with status notes explaining that the foundational contract hardening is now implemented.

### Why this mattered

Those files were still written as if the whole baseline was mostly future work.

That would have created unnecessary confusion.

### Plain-English result

The repo now reads more honestly.

The older review/task files are still there, but they are framed as history and rationale, not as proof that the repo is still in its old state.

---

## Validation and checks that were run

The following checks were run successfully:

- `python scripts/validate_scafforge_contract.py`
- `python scripts/smoke_test_scafforge.py`
- `node bin/scafforge.mjs validate-contract`
- `python skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py --help`
- `python skills/opencode-team-bootstrap/scripts/bootstrap_opencode_team.py --help`
- `python skills/repo-process-doctor/scripts/audit_repo_process.py --help`

These checks were useful for proving:

- the contract validator works
- the smoke test works
- the new CLI wrapper works
- the bootstrap scripts still run with the new explicit model arguments
- the doctor script still loads

---

## Cross-check against the implementation plan

This section explains how the completed work maps back to the plan.

### Phase 0 - Lock scope, terminology, and truth model

Implemented through:

- package contract updates
- truth hierarchy updates
- ambiguity handling updates

### Phase 1 - Finish the one-cycle scaffold contract

Implemented through:

- updated kickoff contract
- bootstrap/refine ticket builder modes
- foundation/synthesis skill bootstrap modes
- machine-readable flow manifest

### Phase 2 - Bring OpenCode conformance to 100% confidence

Implemented through:

- conformance checklist
- contract validator
- generated shape checks in smoke testing

### Phase 3 - Harden prompts for weaker models

Implemented through:

- stronger planner/reviewer/implementer/QA/docs prompts
- weak-model profile reference
- blocker-first wording

### Phase 4 - Standardize ticket, state, and artifact architecture

Implemented through:

- stage-specific artifact directories
- artifact registry
- updated workflow tools and docs

### Phase 5 - Make model/provider selection explicit and portable

Implemented through:

- explicit bootstrap script arguments
- model provider recorded in provenance
- updated model docs and brief template

### Phase 6 - Add git and GitHub capability as a first-class option

Implemented for the chosen v1 scope through:

- local-git specialist skill
- generated git capability doc
- local-git-only framing instead of GitHub-default assumptions

### Phase 7 - Improve installation and cross-CLI usability

Implemented through:

- adapter manifest
- adapter README
- npm-style package metadata
- CLI wrapper

### Phase 8 - Build a real validation and regression harness

Implemented through:

- contract validator
- smoke-test harness

### Phase 9 - Unify documentation and terminology

Implemented through:

- aligned README and AGENTS
- aligned generated template docs
- updated historical notes

### Phase 10 - Release the first fully functional baseline

Implemented in repo terms through:

- explicit entrypoints
- generated startup guidance
- validation checks
- step-by-step scaffold contract

---

## Final plain-English summary

Scafforge is now much closer to what it was supposed to be from the start:

- a real scaffold generator instead of a partly-remembered personal setup folder
- clearer about what it owns and what it generates
- stricter about unclear inputs
- clearer for weaker models
- more explicit about runtime-model choices
- better aligned between docs, template, tools, and validation

The most important improvement is not any single file.

The most important improvement is that the **plan, the docs, the generator scripts, the template, and the validators now say the same story much more consistently**.
