# Completion Validation Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** TODO
**Goal:** Build a cross-platform completion validation system so Scafforge can prove “done” across web apps, games, scripts, services, desktop apps, and Android repos without relying on agent self-report.

**Architecture:** Define a validation ladder per repo family and connect it to audit, repair, and handoff publication. The system should prefer the cheapest truthful check first, escalate to runtime/screenshot/network/device proof when needed, and store concise artifacts that other skills can consume.

**Tech Stack / Surfaces:** package validators, `skills/scafforge-audit/`, generated template stage-gates, stack adapter references, test fixtures, platform-specific tooling recommendations.
**Depends On:** `02-downstream-reliability-hardening` for failure families; should run alongside `11-repository-documentation-sweep`.
**Unblocks:** every autonomy and review-oriented plan, especially `07-autonomous-downstream-orchestration` and `08-meta-improvement-loop`.
**Primary Sources:** `active-plans/_source-material/validation/completionqualityvalidation/toolstoimplement.md`, current package validation commands, `references/stack-adapter-contract.md`, audit verifier scripts.

---

## Problem statement

Scafforge currently has fragmented validation hints, with too much emphasis on smoke-level checks and Android-only tooling. The system needs one coherent answer to:

- what counts as “done” for each repo family
- which proof artifacts are mandatory
- when screenshot, video, network, process, or emulator evidence is required
- how validators feed audit and restart/handoff surfaces

Without that, weak models will keep equating “agent says it works” with actual completion.

## Repo families this plan must cover

- web apps and browser-heavy interactive projects
- Godot/game repos
- CLI and script repos
- backend/service repos
- desktop apps on Windows and Linux
- Android repos

Apple/iOS/macOS validation is explicitly out of scope for this cycle.

## Required deliverables

- a validation ladder per repo family
- a tool matrix covering static, runtime, visual, network, and device/emulator proof
- a proof-artifact convention that other package skills can consume
- a machine-readable mapping where feasible
- generated-repo guidance that blocks handoff when required proof is missing

## Package surfaces likely to change during implementation

- `references/stack-adapter-contract.md`
- `adapters/manifest.json`
- `scripts/validate_scafforge_contract.py`
- `scripts/smoke_test_scafforge.py`
- `scripts/integration_test_scafforge.py`
- `skills/scafforge-audit/scripts/shared_verifier.py`
- `skills/scafforge-audit/scripts/target_completion.py`
- `skills/scafforge-audit/scripts/audit_execution_surfaces.py`
- `skills/scafforge-audit/scripts/audit_reporting.py`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`
- generated process and handoff docs in the project template
- `tests/fixtures/` with representative stack-family cases

## Proposed validation ladder

Each supported repo family should progress through some subset of:

1. static contract and config checks
2. build/install/bootstrap checks
3. runtime or process health checks
4. stack-specific behavioral checks
5. visual or artifact review checks
6. proof publication into handoff/audit surfaces

The exact ladder differs by stack. The key rule is that completion cannot skip directly from code existence to success.

## Tool bundle categories this plan should evaluate

- Web: Playwright/browser automation, HTTP probes, performance or accessibility spot checks where relevant
- Godot/Game: engine boot checks, scene/import checks, screenshot capture, input smoke coverage where feasible
- CLI/Script: command exit status, structured output comparison, log capture, environment/bootstrap checks
- Backend/Service: process startup, health endpoints, contract probes, dependency/bootstrap verification
- Desktop Windows/Linux: launch verification, window/process truth, screenshot capture when UI exists
- Android: `adb`, `logcat`, emulator workflows, Gradle, Android SDK CLI
- Shared support tools: `ffmpeg`, `ImageMagick`, `CMake`, Vulkan/toolchain checks, language servers only where they materially improve validation

## Phase plan

### Phase 1: Define the validation matrix

- [ ] Write the supported repo families and the minimum validation ladder each one must satisfy.
- [ ] Identify which proof steps are mandatory, optional, or stack-conditional.
- [ ] Decide where this mapping should live in machine-readable form so validators and generated repos can consume it.
- [ ] Make sure the matrix distinguishes between “no validator exists yet” and “proof not required.”

### Phase 2: Specify tool bundles and artifact rules

- [ ] For each repo family, choose the baseline tools Scafforge should recommend or require.
- [ ] Define the artifact outputs: logs, screenshots, HTTP traces, emulator captures, process summaries, or generated reports.
- [ ] Decide what should be committed into generated repos versus what remains ephemeral package evidence.
- [ ] Ensure proof storage stays concise and reviewable instead of turning into uncontrolled log dumps.

### Phase 3: Integrate validation with audit and handoff

- [ ] Teach audit to consume the validation ladder and report missing proof as a named issue, not a vague smell.
- [ ] Teach handoff publication to summarize which proof steps passed, failed, or were not applicable.
- [ ] Update the generated stage-gate flow so required proof blocks completion claims.
- [ ] Make sure repair flows can request the right proof rerun instead of forcing the whole pipeline to restart blindly.

### Phase 4: Seed representative fixtures

- [ ] Add or extend fixture coverage so at least one example exists for each supported family.
- [ ] Ensure a failing fixture demonstrates a real missing-proof or wrong-proof condition.
- [ ] Ensure a healthy fixture can clear the expected validation ladder without needing human interpretation.
- [ ] Use the fixtures to prove that “Android tooling” is no longer the only concrete validation story in the repo.

### Phase 5: Connect matrix language to contributor docs

- [ ] Add a concise operator-facing explanation of the validation ladder and proof categories.
- [ ] Update package docs so supported repo families and proof expectations are discoverable.
- [ ] Ensure generated repos get a lightweight explanation of their own required proof bundle.
- [ ] Cross-link the matrix into the documentation sweep plan so future contract changes keep docs aligned.

## Validation and proof requirements

- each supported repo family has an explicit proof ladder
- required proof artifacts are named, stored predictably, and consumable by audit/handoff
- generated repos cannot claim completion when mandatory proof is absent
- validation coverage is visibly broader than Android-only smoke checks

## Risks and guardrails

- Do not create one giant validator that pretends every stack is the same.
- Do not overfit to Android because the source note contained Android tools.
- Do not demand expensive browser/emulator/device checks when cheaper truthful checks already prove failure.
- Do not hide unsupported stacks behind silent skips; surface the gap clearly.

## Documentation updates required when this plan is implemented

- stack adapter and validation references
- package validation command docs
- generated process and handoff docs
- contributor/operator guidance for proof artifacts

## Completion criteria

- Scafforge has a documented validation ladder for every supported repo family
- proof artifacts are first-class completion requirements
- audit and handoff consume the same proof model
- package validation is no longer smoke-only or Android-biased
