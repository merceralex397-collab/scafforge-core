# Scafforge Implementation Plan

Status: Draft v4 with refinement interview decisions incorporated

This plan is intentionally long and explicit. It is designed to become the working source of truth for turning `Scafforge` from a strong-but-partially-finished scaffold concept into a reliable generator that can take a spec-only repository and output a deterministic, OpenCode-oriented autonomous development repo.

---

## 1. Problem statement

Scafforge is no longer just a personal config folder. It is trying to become a real product:

- a host-agnostic scaffold package
- consumable from multiple CLI agents
- producing an OpenCode-specific output layer
- capable of turning a spec pack into a fully prepared repo with docs, tickets, agents, tools, commands, hooks/plugins, and workflow state
- optimized for autonomous work by weaker models, not just premium models

The important nuance is this:

- the **generator** should not be Codex-specific
- the **generated output** should currently be OpenCode-specific by default
- the **generated repo** should be strong enough that an agent can enter it, read the startup surface, and continue the full delivery loop without a human repeatedly steering it

That means Scafforge is not just a template copier. It is a workflow shaper.

---

## 2. Evidence-based reading of the current state

This plan is based on the current Scafforge repo, official OpenCode docs, and the live generated repos `GPS` and `deephat`, with `GPTTalker` used as an example of a spec-only input repo.

### 2.1 What Scafforge currently claims

From `README.md` and `AGENTS.md`, Scafforge already claims the right high-level architecture:

- host layer is meant to be host-agnostic
- output layer is intentionally OpenCode-oriented
- the desired greenfield path is a one-cycle flow:
  - `scaffold-kickoff`
  - `spec-pack-normalizer`
  - `repo-scaffold-factory`
  - `ticket-pack-builder`
  - `project-skill-bootstrap`
  - `agent-prompt-engineering`
  - `repo-process-doctor`
  - `handoff-brief`

This is directionally correct and should remain the product spine.

### 2.2 What is actually true today

The repo also openly shows that the above is not fully locked in yet:

- `TASKS.md` still lists foundational work as incomplete
- `REVIEW-NOTES.md` describes the one-cycle scaffold as a goal that needs stronger contracts
- `scaffold-kickoff\SKILL.md` still leaves `ticket-pack-builder` for later expansion instead of making it a mandatory bootstrap step
- `project-skill-bootstrap\SKILL.md` talks about local skills, but does not yet encode a strong two-mode contract
- several core skill descriptions still contain host-specific "Codex" wording, which conflicts with the stated host-agnostic goal

### 2.3 What the template currently generates

The template under `skills\repo-scaffold-factory\assets\project-template\` already generates important OpenCode surfaces:

- `README.md`
- `AGENTS.md`
- `START-HERE.md`
- `opencode.jsonc`
- `.opencode\agents\`
- `.opencode\tools\`
- `.opencode\plugins\`
- `.opencode\commands\`
- `.opencode\skills\`
- `.opencode\state\workflow-state.json`
- `tickets\manifest.json`
- `tickets\BOARD.md`
- process docs

This is a strong base. The issue is not lack of direction. The issue is contract strength, portability, validation, and consistency.

### 2.4 What the live generated repos reveal

`GPS` and `deephat` are extremely valuable because they show what the generator is trying to produce in practice, not just in theory.

They confirm that the mature generated shape wants:

- a visible team leader agent
- hidden specialist planners, implementers, reviewers, QA agents, and utilities
- ticket-backed workflow state
- artifact-backed stage proofs
- strong restart surfaces
- OpenCode-local tools, commands, plugins, and skills

They also reveal the biggest current risks:

- hardcoded model/provider choices, especially `minimax-coding-plan/MiniMax-M2.5`
- stronger live prompts than the generic scaffold template
- richer artifact handling than the template fully standardizes
- repo-specific process strength that is not yet consistently encoded upstream in Scafforge

### 2.5 What GPTTalker reveals about the intended intake

`GPTTalker` is a good example of the input state Scafforge should be able to handle:

- many markdown specs
- multiple proposals
- mixed certainty levels
- unresolved options
- domain facts mixed with design alternatives

This confirms a critical requirement:

Scafforge must not just "generate a repo." It must first normalize ambiguity, classify certainty, and ask the user for decisions when multiple valid paths exist.

---

## 3. Core diagnosis

The biggest problem is not that Scafforge lacks pieces.

The biggest problem is that Scafforge currently has:

- a good architectural story
- a partially implemented scaffold engine
- stronger downstream examples than upstream guarantees
- incomplete enforcement of its own philosophy

Said more plainly:

Scafforge knows what good looks like, but it does not yet consistently force itself to produce that outcome.

That is why the roadmap below prioritizes contract hardening, validation, and consistency over flashy expansion.

---

## 4. Non-negotiable design principles for the finished product

These principles should guide all implementation work.

### 4.1 Host-agnostic generator, OpenCode-first output

Why:

This is the core product identity. If the generator becomes Codex-specific, portability dies. If the output stops being OpenCode-shaped, the current value proposition gets blurred.

Decision:

- keep Scafforge core wording and orchestration host-agnostic
- keep the v1 output profile OpenCode-specific only
- treat Copilot, Codex, and Gemini CLI as host adapters for running Scafforge, not as alternate v1 output truths

### 4.2 One orchestrated cycle is the default

Why:

Weaker models fail most often when the workflow depends on a remembered second pass.

Decision:

A greenfield run should not be "done enough" until it completes:

- normalized brief
- scaffold
- ticket pack
- OpenCode operating layer
- local skills foundation pack
- prompt hardening where needed
- audit
- restart surface

### 4.3 Never assume when the spec is ambiguous

Why:

Your requirement is explicit, and it is also correct. Silent assumptions create wrong scaffolds early, and wrong scaffolds are expensive to undo later.

Decision:

Scafforge must implement an explicit ambiguity policy:

- facts -> proceed
- preferences already stated -> preserve exactly
- unresolved alternatives with meaningful impact -> ask the user
- unresolved minor wording issues -> record as open questions, do not invent system behavior

### 4.4 Stronger rails beat longer prose

Why:

Lower-tier models do not reliably infer hidden workflow rules from elegant documentation.

Decision:

Put important behavior into:

- tools
- plugins / hooks
- structured artifacts
- explicit agent prompts
- validation scripts

Do not rely on soft wording alone.

### 4.5 Documentation must have a canonical source hierarchy

Why:

You explicitly do not want output repos where three different documents disagree.

Decision:

Each generated repo must define:

- canonical source for project facts
- canonical source for workflow rules
- canonical source for queue state
- canonical source for transient approval state
- canonical source for artifacts and proofs
- derived views that are clearly marked as derived

### 4.6 Linux-targeted output must be explicit

Why:

Scafforge is being developed on Windows, but the generated repos are intended to run mostly on headless Ubuntu.

Decision:

Generated project docs and commands should default to Linux-safe conventions unless the project brief explicitly selects another runtime target.

### 4.7 Model/provider selection must be explicit, never buried

Why:

The live repos show hardcoded Minimax usage. That may be acceptable for a specific generated repo, but not as an invisible default inside the generator.

Decision:

Scafforge should always surface:

- provider choice
- main implementation/planning model
- optional cheaper helper model
- rationale if a weak-model-optimized profile is chosen

No silent hardcoding.

---

## 5. Proposed product architecture

This is the recommended target architecture for Scafforge itself.

### 5.1 Intake and normalization layer

Purpose:

Turn messy specs into structured input before any scaffold generation happens.

Responsibilities:

- discover candidate spec files
- classify them into facts, options, constraints, non-goals, and open questions
- generate a canonical brief
- explicitly identify ambiguities requiring user confirmation

Why:

Without this layer, every downstream step inherits ambiguity and either guesses or stalls.

### 5.2 Scaffold rendering layer

Purpose:

Generate the baseline repo structure from normalized inputs.

Responsibilities:

- folder layout
- docs skeleton
- OpenCode config
- base agents, tools, commands, plugins/hooks, and state directories
- ticket pack shell

Why:

This keeps structural generation centralized and deterministic.

### 5.3 Output-profile layer

Purpose:

Separate generator logic from output-specific schemas.

Responsibilities:

- define the OpenCode output profile as the current default
- later allow alternate profiles or adapters without rewriting core orchestration

Why:

This is the cleanest way to be host-agnostic while remaining output-opinionated.

### 5.4 Workflow-state and artifact layer

Purpose:

Make autonomous operation concrete and inspectable.

Responsibilities:

- ticket queue
- transient plan approval and stage state
- canonical artifact locations
- tool-backed state transitions
- restart and handoff surfaces

Why:

Autonomy fails when state is hidden or split unclearly across docs.

### 5.5 Prompt-hardening and agent-contract layer

Purpose:

Produce prompts that weaker models can actually follow.

Responsibilities:

- planning-first enforcement
- blocker behavior
- no premature summarization
- no implementation before approval
- no workflow deviation
- explicit next specialist routing

Why:

The live repos show this matters as much as file structure.

### 5.6 Validation and drift-detection layer

Purpose:

Continuously check that what Scafforge generates still matches its docs, assets, and target runtime expectations.

Responsibilities:

- schema checks
- placeholder resolution checks
- asset existence checks
- output smoke tests
- consistency checks across generated docs
- audits against live reference fixtures

Why:

This is what turns the project from a clever setup into a real generator.

---

## 6. Detailed implementation roadmap

The roadmap below is ordered intentionally. Each phase exists to reduce downstream rework.

## Phase 0 - Lock scope, terminology, and truth model

### Step 0.1 Define the official Scafforge product contract

What to do:

- write a concise canonical product definition for Scafforge itself
- define the distinction between:
  - generator
  - host adapter
  - output profile
  - generated repo
- define current supported target: OpenCode output profile

Why:

Many later problems are identity problems. If the repo is unclear whether it is a personal config pack, Codex workflow pack, or portable generator, drift will continue.

Evidence:

- `README.md` and `AGENTS.md` mostly say the right thing
- several skills still leak Codex wording
- live repos are more OpenCode-committed than the core package wording

Deliverables:

- canonical architecture doc for Scafforge
- terminology glossary
- "what Scafforge is / is not" section adopted everywhere

### Step 0.2 Define the source-of-truth hierarchy for generated repos

What to do:

- specify canonical surfaces and derived surfaces
- document exactly which file owns:
  - project facts
  - workflow rules
  - ticket queue
  - transient approval state
  - artifact registry
  - startup state

Why:

This directly addresses your consistency requirement and prevents drift.

Deliverables:

- a canonical generated-repo information hierarchy
- matching tool contracts
- consistency checker rules

### Step 0.3 Formalize ambiguity policy

What to do:

- define a decision taxonomy:
  - fixed facts
  - user preferences
  - options requiring explicit choice
  - acceptable defaults
  - blocked unknowns
- encode "always ask when materially ambiguous"

Why:

This is one of your clearest requirements and a central behavioral contract.

Deliverables:

- ambiguity rules in `spec-pack-normalizer`
- prompts that explicitly return blockers/questions instead of guessing

## Phase 1 - Finish the one-cycle scaffold contract

### Step 1.1 Make `scaffold-kickoff` the real conductor

What to do:

- rewrite the skill contract so the full greenfield route is mandatory
- stop treating ticket generation as a later optional branch
- stop treating local skills as a late embellishment

Why:

This is the single highest-leverage correction in the repo.

Evidence:

- `scaffold-kickoff\SKILL.md` still says to leave `ticket-pack-builder` for later
- `TASKS.md` already points to this gap

Deliverables:

- updated kickoff contract
- machine-readable flow manifest
- explicit required outputs per phase

### Step 1.2 Add bootstrap mode to `ticket-pack-builder`

What to do:

- support first-pass ticket generation from the normalized brief
- distinguish bootstrap mode from later refine mode

Why:

A scaffold without a usable queue is only half-born.

Deliverables:

- bootstrap ticket generation path
- refine/regenerate path
- consistent ticket schema and templates

### Step 1.3 Add dual-mode contract to `project-skill-bootstrap`

What to do:

- foundation mode for the minimum workflow pack
- synthesis mode for project- and stack-specific skills

Why:

This prevents local skills from being either absent or uncontrolled.

Deliverables:

- explicit mode contracts
- evidence thresholds for synthesis
- minimum foundation pack guaranteed on every greenfield scaffold

### Step 1.4 Introduce a flow manifest

What to do:

- create a machine-readable manifest of skills, inputs, outputs, dependencies, and ownership

Why:

Right now the intended flow is described in prose. It should also exist in a machine-checkable form.

Deliverables:

- skill-flow manifest
- audit script that can catch orphaned or overlapping skills

## Phase 2 - Bring OpenCode conformance to 100% confidence

### Step 2.1 Audit every generated surface against official OpenCode docs

What to do:

- verify agents, tools, skills, rules, and config structure against current documentation
- treat template assets as code, not as passive text

Why:

One of your surfaced issues is that generated surfaces have not always matched true OpenCode schema.

Evidence:

- official docs confirm exact conventions for `AGENTS.md`, `SKILL.md`, config, and custom tools
- template assets look directionally correct, but they are not fully validated

Deliverables:

- OpenCode conformance checklist
- schema/shape validation rules
- doc-to-template mapping

### Step 2.2 Separate "schema validity" from "workflow quality"

What to do:

- explicitly distinguish:
  - valid OpenCode file/schema
  - good autonomous workflow design

Why:

A file can be syntactically valid and still produce a bad autonomous repo.

Deliverables:

- validation matrix with both categories

### Step 2.3 Standardize tool, plugin, command, and skill contracts

What to do:

- define required arguments, naming, lifecycle purpose, and permission expectations for generated OpenCode surfaces

Why:

This is how you avoid subtle schema drift between template and live generated repos.

Deliverables:

- contract reference docs
- generator validations
- live fixture comparison tests

## Phase 3 - Harden prompts for weaker models

### Step 3.1 Rewrite the generic agent prompts using standard prompt-engineering patterns

What to do:

- upgrade the template prompts using the stronger patterns visible in `deephat` and `GPS`
- add:
  - explicit blockers
  - explicit stage proof checks
  - explicit required output sections
  - explicit next-specialist constraints
  - explicit "do not summarize early" and "do not stop before completion" rails

Why:

The current template prompts are good but not as strong as the live generated prompts.

Evidence:

- `deephat` team leader and planners are more operationally explicit than the template
- template planner is too permissive around blocker behavior and ambiguity response

Deliverables:

- upgraded generic team leader
- upgraded planner
- upgraded plan review
- upgraded implementer
- upgraded reviewer and QA prompts

### Step 3.2 Build a weak-model prompt profile

What to do:

- define prompt conventions specifically for weaker models such as MiniMax M2.5
- keep them general enough that they improve other lower-tier models too

Why:

You explicitly care about weak-model reliability, not just premium-model elegance.

Deliverables:

- weak-model prompt heuristics
- wording standards for deterministic execution
- short-section templates

### Step 3.3 Add "return blocker, do not guess" contracts

What to do:

- ensure planners, implementers, and leaders have explicit blocker conditions
- define when agents must ask the human instead of making a hidden choice

Why:

This directly implements your "always ask" rule.

Deliverables:

- blocker taxonomy across agents
- ambiguity escalation rules

### Step 3.4 Add anti-premature-summary rules

What to do:

- teach agents not to stop with a summary when the process expects another stage
- reinforce that only approved completion criteria end the loop

Why:

You have observed agents summarizing too early. This must be treated as a workflow defect, not just a model quirk.

Deliverables:

- prompt additions
- closeout-only termination rules
- stronger handoff requirements

## Phase 4 - Standardize ticket, state, and artifact architecture

### Step 4.1 Choose and lock the canonical artifact architecture

What to do:

- adopt the chosen hybrid model:
  - stage-specific subdirectories for human discoverability
  - a machine-readable registry for tool-backed lookup and validation

Recommended concrete shape:

- `.opencode\state\plans\`
- `.opencode\state\implementations\`
- `.opencode\state\reviews\`
- `.opencode\state\qa\`
- `.opencode\state\handoffs\`
- `.opencode\state\artifacts\registry.json`

Why:

This gives the readability advantage visible in `deephat` without losing the machine-friendly lookup and consistency benefits of a registry.

Deliverables:

- canonical artifact layout
- artifact naming rules
- artifact registration contract

### Step 4.2 Ensure stage transitions are tool-backed

What to do:

- prevent raw file edits from being the default mechanism for workflow state changes
- use tools to enforce valid transitions

Why:

This is one of the strongest current ideas in the live repos and should be standardized.

Deliverables:

- tool contract updates
- plugin/hook validation
- repair/audit rules

### Step 4.3 Make restart surfaces deterministic

What to do:

- define exactly what `START-HERE.md` must contain
- ensure it is refreshed from canonical state, not hand-edited drift

Why:

This is the primary entrypoint for autonomous continuation.

Deliverables:

- stronger `START-HERE.md` template
- handoff publishing rules
- consistency tests against workflow state and tickets

## Phase 5 - Make model/provider selection explicit and portable

### Step 5.1 Remove hidden model assumptions from Scafforge core

What to do:

- eliminate generator-level silent defaults that imply one provider/model
- replace them with explicit selection flow

Why:

Right now the live examples strongly imply Minimax as a baked-in answer.

Deliverables:

- generator variables for provider/model
- prompts and docs that do not imply a hidden default

### Step 5.2 Add provider/model selection as an explicit user decision

What to do:

- require the scaffold process to ask for:
  - provider
  - primary model
  - optional cheaper helper model
- preserve exact strings in output
- repeat that question on every run, even when a previous value exists

Why:

This exactly matches your requirement and avoids stale hidden carry-over from earlier runs or partial regenerations.

Deliverables:

- normalized runtime-model section in the canonical brief
- generated `runtime-models.md` or equivalent
- model placeholders resolved only after confirmation

### Step 5.3 Support weak-model profile packs

What to do:

- create prompt and workflow presets optimized for:
  - stronger models
  - weaker models

Why:

Some projects may choose weaker models for cost or availability, and the scaffold should intentionally adapt.

Deliverables:

- profile matrix
- generated doc explanation
- agent settings mapped from selected profile

## Phase 6 - Add git and GitHub capability as a first-class option

### Step 6.1 Define git/GitHub automation scope

What to do:

- make the v1 default scope explicit:
  - local git read operations
  - local branch / commit workflows
  - no GitHub issue / PR automation in the default generated scaffold

Why:

You have observed that some agents are effectively barred from doing git functions. This is a real workflow gap.

Deliverables:

- local git capability matrix
- least-privilege default permissions

### Step 6.2 Add a dedicated git/GitHub specialist path

What to do:

- create a dedicated local git specialist path for v1:
  - a dedicated agent, or
  - a dedicated skill plus tools, or
  - both

For v1, keep this intentionally local-git-only. GitHub-specific automation can remain a later extension rather than a baseline assumption.

Why:

Treating git/GitHub operations as an afterthought causes confusion and blocked automation.

Deliverables:

- dedicated specialist contract
- safe permission profile
- docs for when and how it is used

### Step 6.3 Keep destructive operations gated

What to do:

- explicitly separate read-safe git operations from write/destructive ones
- require approval or higher-trust path for dangerous actions

Why:

Autonomy should not mean reckless repo mutation.

Deliverables:

- permission presets
- default safety rails

## Phase 7 - Improve installation and cross-CLI usability

### Step 7.1 Separate core package from host adapters

What to do:

- create a clean distinction between:
  - core Scafforge logic
  - host-specific invocation docs or wrappers

Why:

This is the best route to "installable into any CLI" without muddying the product.

Deliverables:

- adapter architecture
- host integration guide for Copilot, Codex, Gemini CLI, and OpenCode-hosted runs

### Step 7.2 Define the minimum portable packaging format

What to do:

- decide how Scafforge is installed and invoked:
  - skill pack
  - command pack
  - repo subdirectory
  - packaged release
  - bootstrap script

Why:

Portability is not just prompt wording. It also depends on packaging and install UX.

Chosen v1 scope:

Treat Scafforge as:

- a portable scaffold package repository
- with documented host adapter entrypoints
- and packaged install UX for Copilot, Codex, and Gemini in addition to OpenCode-hosted usage

Deliverables:

- install and invoke guide
- adapter-specific examples

### Step 7.3 Preserve output neutrality where it matters

What to do:

- allow any host to run Scafforge
- keep generated output explicitly OpenCode-first for now

Why:

This keeps the current vision coherent while still maximizing reach.

Deliverables:

- host adapter docs
- no host-specific wording in core generator docs

## Phase 8 - Build a real validation and regression harness

### Step 8.1 Add sample-fixture generation tests

What to do:

- render a sample repo from controlled fixture inputs
- validate required files and placeholders

Why:

This is the minimum bar for confidence.

Deliverables:

- smoke test harness
- fixture inputs
- expected-output checks

### Step 8.2 Use `GPS`, `deephat`, and `GPTTalker` as structured reference fixtures

What to do:

- use `GPTTalker` as a spec-input fixture
- use `GPS` and `deephat` as end-state comparison fixtures

Why:

These repos are the best available real-world evidence of intended behavior.

Important caveat:

They are audit fixtures, not infallible source of truth and not automatic template donors.

Scafforge should compare against them critically, not copy them blindly or treat back-porting from them as an automatic roadmap lane.

Deliverables:

- fixture comparison checklist
- divergence audit process

### Step 8.5 Upgrade `repo-process-doctor` from diagnosis-only toward full repair on in-progress repos

What to do:

- keep audit mode
- add an explicit repair / patch mode for repos already in progress
- define what the doctor is allowed to repair automatically versus what it must surface as a blocker

Why:

You specifically want in-progress generated repos to be fully patchable, not merely diagnosed. A doctor that only points at drift but does not help repair it leaves too much cleanup burden on the user and weakens the long-term value of the scaffold ecosystem.

Deliverables:

- doctor audit mode
- doctor repair mode
- repair playbook and safety boundaries

### Step 8.3 Add doc consistency tests

What to do:

- verify generated docs do not contradict each other
- check that the same field values appear consistently across:
  - canonical brief
  - startup docs
  - model docs
  - ticketing docs
  - agent catalog

Why:

This directly addresses one of your most important requirements.

Deliverables:

- doc consistency validator
- contradiction rules

### Step 8.4 Add template integrity tests

What to do:

- ensure all referenced scripts, paths, skills, and templates exist
- ensure placeholders are resolvable

Why:

Template drift is one of the easiest ways for generators to silently decay.

Deliverables:

- asset integrity checker
- placeholder audit

## Phase 9 - Unify documentation and terminology across the generator and output

### Step 9.1 Rewrite top-level Scafforge docs after the contract changes

What to do:

- update `README.md`
- update `AGENTS.md`
- update `TASKS.md` or replace with a more current roadmap once implementation begins
- update review notes if still retained

Why:

The repo currently contains good ideas and acknowledged gaps, but not a fully aligned package story.

Deliverables:

- fully aligned top-level docs

### Step 9.2 Add a terminology glossary

What to do:

- define key terms once:
  - host
  - output profile
  - generated repo
  - ticket
  - stage
  - artifact
  - approval state
  - handoff
  - foundation skills
  - synthesis skills

Why:

You explicitly want zero confusion around terms.

Deliverables:

- glossary in generator docs
- glossary mirrored or synthesized into generated repos where needed

### Step 9.3 Reduce wording drift inside templates

What to do:

- ensure templates use a shared canonical vocabulary and do not ad-lib alternative labels for the same concept

Why:

Confusing vocabulary is a silent workflow tax on weaker models.

Deliverables:

- wording reference sheet
- consistency rules for generated assets

## Phase 10 - Release the first fully functional Scafforge baseline

### Step 10.1 Define the Scafforge definition of done

Scafforge should only be considered fully functional when it can:

1. enter a spec-only repo like `GPTTalker`
2. discover the input pack
3. normalize the brief
4. ask the user about unresolved material choices
5. generate a coherent OpenCode-oriented repo
6. emit tickets, agents, tools, plugins/hooks, commands, docs, and state surfaces
7. leave a deterministic `START-HERE.md`
8. pass conformance and consistency validation
9. be runnable by an agent in OpenCode without immediate human rescue

### Step 10.2 Package and document the entrypoints

What to do:

- define how a user starts a Scafforge run from a host CLI
- define how a generated repo starts its own autonomous lifecycle

Why:

The user journey is part of the product, not an afterthought.

Deliverables:

- kickoff instructions
- host adapter instructions
- generated repo startup instructions

---

## 7. Specific responses to the issues you listed

This section maps your numbered concerns to concrete plan responses.

### Issue 1 - OpenCode schema correctness

Response:

- add an OpenCode conformance workstream
- validate agents, skills, config, tools, rules, and custom tools explicitly against official docs
- treat template assets as testable schema-bearing outputs

### Issue 2 - Weaker models get confused

Response:

- rewrite generic prompts using stronger weak-model patterns
- shorten prompts while increasing operational explicitness
- move stable procedure into tools/plugins/skills
- add blocker rules and next-specialist rules

### Issue 3 - Windows development, Linux deployment

Response:

- make generated output default to Ubuntu-safe commands and paths
- keep generator internals portable, but generated repo docs Linux-first unless specified otherwise

### Issue 4 - Agents stop and summarize instead of finishing

Response:

- add anti-premature-summary contracts
- make closeout the only valid completion surface
- enforce stage-complete proofs before stopping

### Issue 5 - Agents deviate from process

Response:

- strengthen prompts
- strengthen plugins/hooks
- strengthen tool-backed transitions
- add audit rules that flag process drift

### Issue 6 - Artifact generation uncertainty

Response:

- standardize canonical artifact layout
- compare current template against `GPS` and `deephat`
- make artifact generation explicit, not incidental

### Issue 7 - Prompt quality, especially for MiniMax M2.5

Response:

- create a weak-model prompt profile
- adopt better blocker rules, section structure, and deterministic routing
- explicitly expose model/provider choice instead of hiding Minimax assumptions

### Issue 8 - Never assume on unclear spec details

Response:

- encode this into `spec-pack-normalizer`, planner prompts, and kickoff workflow
- create explicit question generation for unresolved architectural choices

### Issue 9 - Need for git/GitHub agent or function

Response:

- define a first-class git/GitHub capability path
- likely generate a dedicated specialist contract with safe permissions

### Issue 10 - Installable to any CLI

Response:

- separate core package from host adapters
- define a portable packaging and invocation story
- keep output profile OpenCode-specific for now

### Issue 11 - Model/provider should always be asked

Response:

- make model/provider selection a mandatory normalized-input question unless explicitly specified in the source material

### Issue 12 - Documentation consistency across output

Response:

- create canonical source hierarchy
- build doc consistency validation
- regenerate derived docs from source state where possible

### Issue 13 - Terms and behavior must be clear

Response:

- add a terminology layer
- remove ambiguous labels
- define exact responsibilities and ownership boundaries

---

## 8. Recommended structural amendments to Scafforge

These are enhancements I recommend as part of the implementation program.

### 8.1 Add an explicit output-profile concept

This is the cleanest conceptual fix for the "host-agnostic generator, OpenCode-specific output" requirement.

### 8.2 Add a runtime-model document to the generated scaffold

`deephat` demonstrates the value of explicitly separating development orchestration model choices from the product runtime model.

Scafforge should generate an equivalent document or section for every repo.

### 8.3 Add a generated-repo consistency validator

This should be part of the generated stack and part of Scafforge validation.

### 8.4 Add a machine-readable manifest for skill and asset ownership

This will sharply reduce drift and confusion inside Scafforge itself.

### 8.5 Add a reference-fixture audit process

Use `GPS`, `deephat`, and future repos as living comparison fixtures.

---

## 9. Recommended implementation order

This is the order I recommend following during actual implementation:

1. define the contract and source-of-truth hierarchy
2. finish the one-cycle scaffold contract
3. make ambiguity handling explicit
4. add model/provider selection and runtime-model surfaces
5. standardize artifacts and stage proofs
6. harden prompts for weaker models
7. add git/GitHub capability path
8. separate core package from host adapters
9. build validation and regression harness
10. unify documentation and terminology
11. cut the first fully functional baseline

Why this order:

If prompt hardening or portability work is done before the underlying contract and state model are fixed, those later changes will need to be rewritten.

---

## 10. Risks and mitigations

### Risk 1 - Scafforge becomes a skill hoarder instead of a workflow shaper

Mitigation:

- keep foundation pack small
- require evidence scoring before synthesis
- reject low-value or duplicative local skills

### Risk 2 - The project stays half-host-agnostic and half-host-specific

Mitigation:

- move host details into adapters
- remove host-specific language from core docs and skills

### Risk 3 - OpenCode schema drifts again

Mitigation:

- automated conformance checks
- fixture regeneration tests

### Risk 4 - Weak-model support turns prompts into bloated walls of text

Mitigation:

- prefer shorter prompts with stronger structure
- shift stable procedure into tools/plugins/skills

### Risk 5 - Live reference repos bias the design too much

Mitigation:

- treat `GPS` and `deephat` as evidence, not law
- compare them against official docs and Scafforge’s own intended architecture

---

## 11. Notes on git initialization

The environment is currently not a git repository.

However, during planning I attempted to initialize git because your request mentioned it, and you explicitly rejected that action with "Just plan. Thats all."

So this plan treats repository initialization as:

- acknowledged
- not executed during this planning turn
- the first implementation/setup action if you later choose to proceed

---

## 12. Draft execution todos

These are the planned implementation work items that should be tracked in the session database:

- `define-product-contract`
- `define-truth-hierarchy`
- `encode-ambiguity-policy`
- `finish-one-cycle-flow`
- `add-ticket-bootstrap-mode`
- `split-skill-bootstrap-modes`
- `audit-opencode-conformance`
- `standardize-artifact-architecture`
- `harden-weak-model-prompts`
- `add-model-provider-selection`
- `add-git-github-capability`
- `separate-core-from-host-adapters`
- `build-validation-harness`
- `add-doc-consistency-checks`
- `align-top-level-docs`

---

## 13. Resolved planning decisions

The roadmap is now refined around these confirmed choices:

1. v1 output scope is **OpenCode only**
2. generated repos should support **local git read/write without GitHub** by default
3. artifact architecture should be **hybrid**, using stage-specific directories plus a registry
4. provider/model choice should **always be asked on every run**
5. `GPS` and `deephat` should be treated as **audit fixtures only**
6. Scafforge should ship **documented adapters plus packaged install UX**, with **npm package(s)** as the primary distribution channel
7. `repo-process-doctor` should **apply repairs by default unless explicitly blocked**
8. intake should use a **fully opportunistic scan of docs/notes**, not require a rigid spec-pack schema
9. the default generated scaffold should be **full orchestration by default**
10. generated repos should use a **structured machine-readable core with derived human docs**
11. the default generated baseline should include the **Safety**, **Observability**, **Compaction/context**, **Research delegation**, **Local git specialist**, and **Isolation** packs
12. project-local skill synthesis should be **moderate**, not ultra-conservative and not aggressive by default
13. the initial ticket pack should be an **implementation-ready backlog from the start**
14. v1 should optimize for **both small/medium repos and long-running autonomous programs**, using profile selection where needed

---

## 14. Interview-style challenge review and logical amendments

This section intentionally uses an interview format.

The goal is to stress-test the roadmap the way a skeptical staff engineer, product reviewer, or future maintainer would. Each question is followed by the recommended amendment and why it materially improves Scafforge.

### Interview question 1

**If v1 is OpenCode-output-only, why keep talking about output profiles at all?**

Recommended amendment:

Keep the **output-profile abstraction internally**, but only ship **one active output profile in v1: OpenCode**.

Why this improves the project:

- it preserves clean architecture without prematurely expanding scope
- it avoids baking OpenCode assumptions into every layer of the generator
- it keeps a future expansion path open without forcing multi-output complexity into v1

This is an internal design seam, not a product-scope expansion.

### Interview question 2

**How do you stop generated repos from becoming too large and cognitively heavy for weaker models?**

Recovered evidence:

- the recoverable indexed residue from the failed prior session focused heavily on `GPS`, which it described as a very large generated repo with many tickets, agents, tools, plugins, and skills
- that is useful evidence that generated repos can become structurally rich very quickly

Recommended amendment:

Add a **scaffold complexity budget** to Scafforge.

That budget should define:

- maximum default agent count
- maximum default skill count
- maximum default command count
- maximum default custom tool count
- rules for when specialization is justified

Why this improves the project:

- weaker models navigate smaller surface areas more reliably
- the generator becomes more disciplined
- large repo operating layers become a conscious decision rather than an accidental byproduct

### Interview question 3

**How will a weak model understand what each generated surface is for without reading half the repo?**

Recommended amendment:

Generate a machine-readable and human-readable **scaffold inventory manifest**.

Suggested contents:

- every generated agent
- every generated tool
- every generated plugin/hook
- every generated command
- every generated local skill
- purpose
- authority level
- whether it is template-generated, synthesized, or repaired later

Why this improves the project:

- gives agents a compact map of the operating layer
- reduces blind exploration
- makes audits and repair safer

This should likely live under something like `.opencode\meta\scaffold-manifest.json` plus a short human-facing companion doc.

### Interview question 4

**What prevents critical startup or handoff files from becoming useless pointer stubs?**

Recovered evidence:

- one prior session saved only a stub plan containing `See devdocs/opusplan.md for the full plan`
- the actual referenced file was not recoverable
- this is a small but very relevant warning: pointer-only surfaces are fragile

Recommended amendment:

Adopt a **no pointer-only critical docs** rule for generated repos.

For any critical restart or governance file such as:

- `START-HERE.md`
- generated project `AGENTS.md`
- handoff summary
- workflow-state summary surface

require all of them to contain:

- a direct executive summary
- current authoritative next action
- canonical sources of truth
- the minimum context needed to continue without needing another file just to understand what is going on

Why this improves the project:

- weak models are much less likely to stall
- missing secondary files become less catastrophic
- the restart surface becomes self-contained enough to be robust

### Interview question 5

**How will you verify prompt quality for weaker models instead of just hoping the wording is better?**

Recommended amendment:

Add a **weak-model prompt regression pack** to the validation harness.

This should test representative scenarios such as:

- ambiguous spec input
- missing approval state
- missing artifact proof
- attempt to implement before planning
- temptation to summarize early
- unresolved provider/model choice

Why this improves the project:

- turns weak-model support into something testable
- makes prompt quality measurable
- prevents regressions where prompts become prettier but less operational

### Interview question 6

**If `repo-process-doctor` is meant to fully patch in-progress repos, how do you keep it from becoming dangerous or magical?**

Recommended amendment:

Give the doctor three explicit modes:

- `audit`
- `propose-repair`
- `apply-repair`

And require repair outputs to include:

- a detected issue list
- intended patch scope
- files to change
- post-repair verification
- a repair artifact or report

Why this improves the project:

- keeps repair explicit and reviewable
- avoids silent mutation
- makes the doctor trustworthy instead of opaque

### Interview question 7

**How do you keep generated documentation consistent without manually editing six files every time something changes?**

Recommended amendment:

Move toward a **structured source pack plus derived docs** model wherever practical.

In other words:

- store core facts in machine-readable or strongly normalized sources
- derive repeated surfaces from those sources
- validate that human-facing docs match the structured sources

Why this improves the project:

- reduces documentation drift
- makes updates cheaper
- supports both audits and repairs

### Interview question 8

**How do you avoid silent assumptions without turning every scaffold run into an annoying interrogation?**

Recommended amendment:

Introduce a **batched decision interview packet** during normalization.

Instead of asking one question at a time, Scafforge should:

- collect all materially ambiguous decisions
- group them by theme
- ask them together once the spec pass is complete
- clearly mark which ones are blocking versus non-blocking

Why this improves the project:

- preserves the rule of never assuming on meaningful ambiguity
- keeps the user experience efficient
- creates a reusable decision record for the generated repo

### Interview question 9

**How do you make Scafforge installable from Copilot, Codex, and Gemini without contaminating the core package with host-specific behavior?**

Recommended amendment:

Define a strict **host adapter contract**.

The adapter layer should own:

- installation UX
- invocation examples
- host-specific startup instructions
- host-specific packaging glue

The core layer should own:

- normalization logic
- scaffold rendering
- OpenCode output truth
- validation logic

Why this improves the project:

- keeps the product coherent
- makes cross-CLI support practical
- avoids reintroducing host-specific drift into core skills

### Interview question 10

**How will future agents know which parts of a generated repo came from the initial scaffold, which came from later synthesis, and which were repaired later?**

Recommended amendment:

Standardize **bootstrap provenance** and lifecycle provenance.

That means recording:

- scaffold version
- template version
- generation date or run identifier
- generated asset list
- later synthesized assets
- later repair actions

Why this improves the project:

- makes repo evolution inspectable
- helps `repo-process-doctor` repair safely
- helps future sessions understand what is canonical versus later-added

### Interview question 11

**What is the single biggest extra improvement that is not yet explicit enough in the roadmap?**

Recommended amendment:

Add a **minimum viable generated repo contract** and a **full workflow repo contract**.

This creates two intentional levels:

- a minimum deterministic OpenCode operating layer
- a richer lane-specialized autonomous repo for bigger projects

Why this improves the project:

- avoids over-generating for small projects
- keeps the default path lighter
- gives Scafforge a cleaner scaling story from tiny spec pack to large long-running project

---

## 15. Current conclusion

Scafforge is already pointed in the right direction.

The highest-value move is not to add lots of disconnected surfaces. It is to make the existing philosophy fully real in a way that matches the refined product decisions:

- one cycle
- opportunistic intake from messy real-world notes and docs
- explicit ambiguity handling
- explicit model/provider choice
- stronger weak-model prompts
- deterministic artifacts and stage proofs
- a structured machine-readable truth core with derived docs
- audited OpenCode correctness
- portable generator, OpenCode-first output
- a full orchestration scaffold that is ready to run autonomously

If implemented in that order, Scafforge can become a genuinely strong spec-to-autonomous-repo generator rather than a promising but partially hand-tuned scaffold pack.

---

## 16. Refinement interview outcomes

The latest refinement round materially sharpened the roadmap:

- Scafforge should accept messy, real-world input repos through **fully opportunistic intake**, rather than demanding a rigid spec-pack structure up front.
- The default output should be a **full orchestration profile**, even though the architecture should still support profile selection for different project sizes.
- Generated repos should be built around a **structured machine-readable truth core**, with repeated human-facing docs derived from that state.
- `repo-process-doctor` should be powerful by default, with **repair applied unless explicitly blocked**, not merely advisory behavior.
- The default generated repo should include all six currently proposed packs:
  - safety
  - observability
  - compaction/context preservation
  - research delegation
  - local git specialist support
  - isolation
- Cross-CLI installability should be delivered primarily as **npm package(s) with documented bootstrap flows**.
- Project-local skill synthesis should be **moderate**: generate more than the bare minimum when evidence is good, but avoid indiscriminate proliferation.
- Ticket generation should start with an **implementation-ready backlog**, not just high-level milestones.
- v1 should target **both smaller repos and larger long-running autonomous projects**, with profile selection used where the shape needs to differ.

These answers make the product more opinionated, more autonomous, and more implementation-ready than the earlier draft.

## 17. Must-have v1 demonstration

The clearest proof that Scafforge is a real product should be:

> Turn a spec-only repo into an OpenCode-ready repo that can autonomously plan, execute, review, and hand off the first real ticket without human steering.

That should be treated as the baseline acceptance demo for the first functional release.
