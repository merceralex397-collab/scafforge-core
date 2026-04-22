# Full Planning Report

## Executive Summary

This portfolio now has two distinct outputs:

1. a cleaned and correctly classified `active-plans/` portfolio
2. fourteen numbered implementation plans, most of which are now implemented across Scafforge and its adjacent repos

The first pass only solved the structure problem. The second pass fixed the actual planning problem by rewriting the numbered folders into implementation-grade documents with dependencies, package surfaces, phased work, validation gates, and documentation obligations.

Those numbered plans then went through a live `planchecker` pass and follow-up rewrite cycle, and the implementation loop used `agent-caller`, direct `copilot -p` recovery where needed, local validation, PR review, and merge.

A final planning-hygiene closeout pass also locked the portfolio rules in place:

- numbered folders are the canonical execution program
- plan-local support notes live under each folder's `references/`
- `_source-material/` remains active in-repo documentation and provenance, not a removal queue
- root-level files under `active-plans/` are limited to portfolio-wide navigation, policy, reporting, journal, and execution guidance
- plan-specific intake notes no longer belong at the root; the Meta-Skill-Engineering intake note now lives with plan `13`'s references

Plan `11` is now implemented as the routing layer for this documentation architecture: root docs are shorter, durable contract detail lives in references, generated-template docs were realigned, and documentation verification is now treated as standing delivery work instead of final polish.

A later source-spec audit against the moved `_source-material/` docs tightened the plans further around three areas that were still too implicit: retrieval or vector-index handling, concrete distillation of the asset-research ecosystem into route policy, and the distinction between provider, SDK, and execution-host access paths in the model-router plan.

The central program decision remains unchanged: Scafforge should not scale autonomy until it first closes the reliability, validation, and quality gaps already proven by womanvshorse and spinner. That hardening sequence is now implemented, and the final WinUI control-plane build-and-proof phase in plan `10` is now merged in its adjacent repo.

## Current Implementation Status

- Scafforge plans `01` through `12` are implemented and merged on `main`.
- The adjacent `Meta-Skill-Engineering` repo hardening from plan `13` is implemented and merged through PR `#19`.
- The adjacent `blender-agent` repo hardening from plan `14` is implemented and merged through PR `#3`.
- The adjacent `scafforge-control-plane-winui` repo from plan `10` is implemented and merged through PR `#1`.

## What This Program Is Actually Doing

The upgrade is not one mega-refactor. It is a staged convergence program with four layers:

### 1. Planning and documentation discipline

- `01-repo-hygiene-cleanup`
- `11-repository-documentation-sweep`

These plans stop the planning/docs layer from drifting into ambiguity and make the rest of the program implementable by other agents without guessing.

### 2. Package hardening before autonomy

- `02-downstream-reliability-hardening`
- `05-completion-validation-matrix`

These plans ensure that Scafforge can actually prove repo readiness and classify failures honestly before any larger autonomous loop is trusted.

### 3. Asset system repair and quality uplift

- `03-asset-pipeline-architecture`
- `04-asset-quality-and-blender-excellence`

These plans address both sides of the asset problem: how assets are sourced/generated/validated, and whether the output actually looks acceptable.

### 4. Autonomous factory expansion

- `06-spec-factory-and-intake-mcp`
- `07-autonomous-downstream-orchestration`
- `08-meta-improvement-loop`
- `09-sdk-model-router-and-provider-strategy`
- `10-viewer-control-plane-winui`
- `12-skill-system-expansion-and-meta-skill-engineering`
- `13-meta-skill-engineering-repo-hardening`
- `14-blender-agent-repo-hardening`

These plans turn the existing Scafforge package into the core of a larger autonomous factory, but only by wrapping the package with adjacent systems rather than dissolving its boundaries.

## The Most Important Decisions

### Reliability beats ambition

The current failure evidence is strong enough that autonomy cannot be the first implementation wave. Fresh scaffolds must stop producing the same trap family, and audit/repair must stop treating obviously broken repos as ambiguous generic drift.

### Validation is cross-platform, not Android-only

The source material mentioned Android tooling, but the package needs one validation answer for web, games, scripts, services, desktop, and Android. The validation matrix plan therefore broadens the proof model rather than doubling down on one platform.

### Asset quality is part of completion

The current downstream problem is not only broken imports and bad configs. The repos also look bad. That means visual quality, layout truth, and screenshot/render evidence must become part of completion gating rather than optional polish.

### The SDK answer is hybrid

Based on current OpenCode, AI SDK, and Apps SDK documentation:

- OpenCode remains the best fit for existing Scafforge and generated-repo execution contracts.
- AI SDK is the right fit for new service-side orchestration and provider routing.
- OpenAI Apps SDK is the right fit for ChatGPT-facing ingress and app surfaces.
- OpenCode should be treated as an execution host that can front many provider routes, not as a tiny fixed model list.
- The same model family may legitimately appear in multiple lanes, such as native MiniMax multimodal SDK use for assets and OpenCode-routed use for coding or implementation work.

That means “rewrite Scafforge around AI SDK” is the wrong move for this cycle.

### Adjacent services stay adjacent

The spec factory, model router, orchestration service, meta-improvement loop, and WinUI control plane should all be designed as adjacent systems that consume Scafforge contracts. They should not be smuggled into the package root as hidden product scope.

## Plan-by-Plan Summary

### `01-repo-hygiene-cleanup`

Defines how `active-plans/` works so plans, summaries, and supporting references stay legible. This is the portfolio hygiene plan, and its implementation locked the numbered-folder versus supporting-reference rule into the root guidance.

### `02-downstream-reliability-hardening`

Turns womanvshorse and spinner into reproducible package defect families with fixtures, stronger gates, better audit classification, and truthful repair routing.

### `03-asset-pipeline-architecture`

Replaces the current route guesswork with a capability-driven asset operating framework, including manifests, provenance, license policy, and import QA.

### `04-asset-quality-and-blender-excellence`

Adds the actual visual quality contract, screenshot/render proof, menu/layout quality standards, and a truthful Blender support matrix.

### `05-completion-validation-matrix`

Defines what “done” means per repo family and how proof artifacts flow into audit, repair, and handoff.

### `06-spec-factory-and-intake-mcp`

Designs the idea-to-approved-brief workspace and the ChatGPT/MCP ingress surface without bypassing Scafforge’s canonical brief contract.

### `07-autonomous-downstream-orchestration`

Designs the service that runs approved briefs through scaffold generation, PR-based downstream execution, review, and resume.

### `08-meta-improvement-loop`

Creates the package-side escalation path for repeated downstream failures: audit -> investigate -> package fix -> revalidate -> downstream resume.

### `09-sdk-model-router-and-provider-strategy`

Locks the provider and SDK architecture so later services do not drift across incompatible abstractions or brittle provider assumptions.

### `10-viewer-control-plane-winui`

Designs and implements the operator-facing Windows app boundary that watches and controls the autonomous factory through explicit backend contracts. The adjacent repo now includes the live client shell, WSL/SSH proof lanes, fail-closed overlay, and launch validation.

### `11-repository-documentation-sweep`

Modernizes the package docs so authority, workflow, and context are discoverable to both humans and agents. The implemented sweep now publishes an authority map, records repeatable context tests, and makes same-PR doc alignment a default expectation for later plans.

### `12-skill-system-expansion-and-meta-skill-engineering`

Defines how Scafforge should evolve its skill system from evidence and external research without turning into a random skill warehouse.

### `13-meta-skill-engineering-repo-hardening`

Hardens the separate Meta-Skill-Engineering repository into a complete, agent-usable skill-engineering suite and lifts the right evaluation techniques out of its embedded `plugin-eval` work.

### `14-blender-agent-repo-hardening`

Turns the separate `blender-agent` repository into a clearer, safer dependency by focusing on truthful contracts, QA/export evidence, and headless-ready hardening.

## Recommended Execution Sequence

1. Land planning hygiene and documentation architecture.
2. Fix reliability and cross-platform validation.
3. Repair the asset pipeline and quality bar.
4. Freeze the SDK/router decision.
5. Build spec intake and downstream orchestration on top of that decision.
6. Add the package self-improvement loop.
7. Add disciplined skill evolution and harden the adjacent Meta-Skill-Engineering and `blender-agent` repos where they underpin the program.
8. Build the WinUI control plane last, when the backend contracts are real.

## Final Recommendation

Treat these plans as the recorded implementation program, not as background notes. The implementation backlog is now closed across plans `01` through `14`; future work should either archive the completed plan folders or open new numbered folders for fresh scope rather than quietly editing the completed contracts.
