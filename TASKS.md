# Scafforge Task List

> Status note:
> The foundational baseline from this checklist is now implemented in the current repo: the one-cycle flow contract, explicit truth hierarchy, ambiguity handling, explicit model selection, host-adapter separation, local-git capability path, prompt hardening, and validation harness are in place.
>
> Read the remaining items below as **historical implementation goals and future hardening lanes**, not as a statement that the current repo is still missing the entire baseline.

This task list assumes the target state is:

- one canonical full-cycle scaffold run
- host-agnostic package behavior
- OpenCode-oriented generated output
- controlled project-local skill synthesis

## Priority 1: lock in the one-cycle workflow

### T-001 Make `scaffold-kickoff` the real conductor
Update the skill contract so `scaffold-kickoff` is the default full-cycle entrypoint and not just a signpost.

It should explicitly route through:
- `spec-pack-normalizer`
- `repo-scaffold-factory`
- `ticket-pack-builder` in bootstrap mode
- `project-skill-bootstrap` in foundation mode
- `agent-prompt-engineering` when needed
- `repo-process-doctor`
- `handoff-brief`

Acceptance:
- docs, skill text, and actual behavior all agree
- greenfield scaffold is considered incomplete until this chain finishes

### T-002 Add bootstrap mode to `ticket-pack-builder`
Change the skill wording and flow contract so ticket generation is part of the default full-cycle scaffold rather than an optional later expansion pass.

Acceptance:
- ticket generation is part of the canonical greenfield run
- standalone refine mode still exists for later use

### T-003 Add dual-mode contract to `project-skill-bootstrap`
Split the role into:
- foundation mode for immediate workflow-tightening skills
- synthesis mode for stack- and project-specific local skills

Acceptance:
- the skill contract clearly distinguishes these two modes
- full-cycle scaffolds always get the foundation pack
- synthesis runs only when enough evidence exists

### T-004 Create a machine-readable skill-flow manifest
Add a small manifest describing each skill’s:
- purpose
- inputs
- outputs
- required upstreams
- optional downstreams
- run modes
- scripts/assets/references

Acceptance:
- future audits can detect overlapping or orphaned skills quickly

## Priority 2: implement controlled skill synthesis

### T-005 Define the project-local skill synthesis ladder
Document and implement the intended order of evidence:
1. repo facts
2. scaffold defaults
3. curated internal patterns
4. project documentation
5. external public skill patterns
6. synthesis into local repo-specific skills

Acceptance:
- this order is reflected in docs and skill wording
- public discovery is not treated as direct install

### T-006 Add evidence scoring for candidate synthesized skills
Before generating a local skill, score the candidate on:
- stack fit
- domain fit
- procedural value
- duplication risk
- maintenance burden
- trust level of source material

Acceptance:
- obviously low-value or redundant skills are filtered out

### T-007 Add project-doc synthesis guidance
Teach `project-skill-bootstrap` how to derive skills from:
- framework docs
- internal architecture docs
- API specs
- deployment docs
- test setup docs

Acceptance:
- the generated result is procedural and repo-specific, not a copy-paste summary

### T-008 Add public-skill pattern mining guidance
Use public skills as pattern references only.

The package should inspect:
- workflow shape
- naming patterns
- validation patterns
- useful script/reference separation

Acceptance:
- synthesized local skills credit the pattern source where useful
- no direct random auto-installs in the default path

### T-009 Add synthesis guardrails
Reject candidate local skills when they:
- duplicate an existing local skill
- merely repeat docs
- are too generic to be repo-specific
- conflict with ticket or workflow state
- create too many tiny overlapping skills

Acceptance:
- local skill packs stay compact and sharp

## Priority 3: wording and package coherence

### T-010 Remove remaining host-specific leakage from core skills
Rewrite remaining core skill descriptions that still say "Codex" when they should say "host agent", "supported host", or similar.

Acceptance:
- core package language is host-agnostic
- adapter-specific wording stays only in adapter-specific assets

### T-011 Rewrite README, AGENTS, and review docs to match the real flow
Ensure all top-level docs describe the one-cycle contract and the controlled skill-synthesis model.

Acceptance:
- docs no longer imply a split base-pass / second-pass default workflow

### T-012 Clarify `repo-scaffold-factory` versus downstream refiners
Document exactly what the base scaffold owns versus what downstream skills refine.

Acceptance:
- no ambiguity between the scaffold root and specialist follow-on skills

## Priority 4: OpenCode conformance and validation

### T-013 Add generated-scaffold smoke test
Create a script that:
1. renders a sample repo to a temp directory
2. verifies required files and paths
3. validates config syntax where possible
4. optionally runs OpenCode smoke checks when available

Acceptance:
- package changes can be tested quickly after edits

### T-014 Add template integrity checks
Verify that:
- every path referenced by a skill exists
- every script referenced by a skill exists
- every reference file exists
- every template placeholder is resolvable
- generated `.opencode` paths land where expected

Acceptance:
- dangling references are caught automatically

### T-015 Validate tool and plugin assumptions against current OpenCode runtime
Check that the generated tools/plugins still match the current expected runtime surface.

Acceptance:
- package docs stop short of claiming runtime validity unless tested

### T-016 Audit generated output against current OpenCode conventions
Review the generated project for:
- root `AGENTS.md`
- `opencode.jsonc`
- `.opencode/agents`
- `.opencode/commands`
- `.opencode/tools`
- `.opencode/plugins`
- `.opencode/skills`
- `.opencode/state`

Acceptance:
- structure remains aligned with current OpenCode documentation

## Priority 5: template and generated-output cleanup

### T-017 Remove legacy branding markers from the generated template
Purge `CODEXSETUP` and similar legacy placeholders or markers.

Acceptance:
- generated repos do not leak package-era legacy names

### T-018 Improve generated README
Expand the generated README so it explains:
- what exists
- why it exists
- how the ticket flow works
- how the OpenCode surfaces fit together
- where a new session should start

Acceptance:
- generated repos are understandable without tribal knowledge

### T-019 Improve generated `START-HERE.md`
Make the restart surface more explicit about:
- active ticket
- current stage
- next action
- current blockers
- where to look when state files and tickets disagree

Acceptance:
- restart behavior is stronger for weaker models and future sessions

### T-020 Improve generated project `AGENTS.md`
Tighten the generated project rules so they remain short, operational, and aligned with the actual scaffold behavior.

Acceptance:
- generated rules are readable and not bloated

## Priority 6: process doctor hardening

### T-021 Teach the doctor to detect local-skill sprawl
Detect when generated repos accumulate too many overlapping local skills or contradictory workflow guidance.

Acceptance:
- the doctor can flag bloated or conflicting skill packs

### T-022 Teach the doctor to detect instruction-path drift
If config points to files that no longer exist, surface it.

Acceptance:
- broken references are caught before handoff

### T-023 Teach the doctor to detect branding leakage
Detect stale package-era branding or host-specific leakage inside generated project files.

Acceptance:
- generated repos stay project-shaped rather than package-shaped

## Priority 7: future adapter strategy

### T-024 Separate core from adapters
Introduce a clearer package distinction between:
- core scaffold logic
- host-specific adapter notes or scripts

Acceptance:
- host-specific integration assets do not dominate the core package identity

### T-025 Define adapter responsibilities
Document what belongs in a host adapter:
- installation notes
- host-specific wiring
- host-specific examples

And what does not belong there:
- core scaffold behavior
- output template truth

Acceptance:
- future adapters do not fork the product concept
