# Active Plans Index

This directory is the active Scafforge implementation program.

The current documentation source-of-truth map for the package lives in [../references/documentation-authority-map.md](../references/documentation-authority-map.md), and its one-hop context proof lives in [11-repository-documentation-sweep/references/documentation-context-tests.md](11-repository-documentation-sweep/references/documentation-context-tests.md).

`active-plans/` uses a two-layer model:

- numbered folders (`NN-kebab-case/`) are the canonical implementation program, and each folder must expose exactly one authoritative `README.md`
- supporting documentation stays in-repo: plan-local notes go in `NN-kebab-case/references/`, while shared raw inputs and copied research live under `_source-material/`

`_source-material/` is active documentation, not a disposal queue. Root-level files under `active-plans/` are reserved for portfolio-wide navigation, policy, reporting, journal, or execution guidance.

## Path Classification

| Path | Classification | Purpose |
| --- | --- | --- |
| `README.md` | root summary | canonical index for the active portfolio |
| `docscleanup.md` | root summary | placement, naming, and maintenance policy for planning surfaces |
| `FULL-REPORT.md` | root summary | cross-plan program summary and sequencing rationale |
| `WORK-JOURNAL.md` | historical provenance | dated record of planning decisions and later corrections |
| `codexinstructions.md` | supporting reference | execution guide for implementing and reviewing the numbered plans |
| `NN-kebab-case/README.md` | canonical plan | primary implementation contract for that plan |
| `NN-kebab-case/references/*.md` | supporting reference | plan-local notes, prompt packs, intake docs, and evidence that support the canonical plan |
| `_source-material/**` | supporting reference | copied research, raw notes, and source inputs that still inform package decisions |

If `_source-material/` preserves a frozen origin artifact that is only being kept for traceability, treat that file as historical provenance within the supporting library rather than as a hidden plan.

Every numbered folder should be a real working plan, not a summary stub. Its primary `README.md` is expected to show:

- explicit `Status:` (`TODO`, `IN PROGRESS`, or `DONE`)
- goal and architecture
- dependencies and unblocks
- concrete package or adjacent surfaces likely to change
- phased checkbox work
- validation gates
- a documentation impact checklist naming the docs, references, template docs, or adjacent-repo docs that must move with that plan

The plan set has also been checked back against the moved source-material specs. That follow-up pass tightened:

- retrieval or vector-index treatment in the spec-factory and archive-intelligence plans
- asset-research distillation into explicit route policy and fallback choices
- provider access-path clarity so OpenCode, native SDKs, and compatible adapters are not conflated

## Placement And Naming Rules

1. Start new implementation planning work in a new numbered folder, never as a new root-level markdown file.
2. Keep the canonical implementation body in that folder's `README.md`.
3. Put plan-specific support material in `references/` with descriptive kebab-case names such as `route-policy-notes.md`, `validation-matrix-notes.md`, or `agent-caller-prompts.md`.
4. Put copied docs, raw notes, and cross-plan research under `_source-material/` when they are still useful but would make the canonical plan noisy.
5. Reserve the `active-plans/` root for the portfolio index, policy/routing notes, reports, journals, and execution guidance that apply across multiple plans.
6. Do not leave plan-specific intake notes at the root; move them into the relevant numbered folder so readers do not mistake them for portfolio-wide authority.

## Maintenance Checklist

For any future planning edit:

1. Create or update the numbered-folder plan first.
2. Update `active-plans/README.md` if plan order, plan status, or the portfolio shape changes.
3. Update `FULL-REPORT.md` if the program summary or sequencing rationale changes.
4. Update `WORK-JOURNAL.md` when a planning rule, classification decision, or significant correction is made.
5. Keep each plan's documentation impact checklist current and make the listed doc changes in the same PR when that plan changes package or template contract truth.
6. Add new `_source-material/` or `references/` documents only when they improve traceability or prevent the canonical plan from becoming noisy.

## Documentation Sweep Reminder

`AGENTS.md` is the durable policy home for the standing doc-update rule. `active-plans/` keeps the program-level reminder:

1. Every contract-changing plan must name its affected docs explicitly.
2. Documentation updates are part of delivery, not a closeout-only cleanup step.
3. When implementation order or architecture decisions change, update the relevant plan, this index, and `FULL-REPORT.md` together.

## Anti-Patterns

- hidden canonical instructions inside `_source-material/` or `references/`
- plan-specific notes left at the root where they look portfolio-wide
- duplicate summaries that restate a numbered folder without adding routing value
- numbered folders with no actionable `README.md`
- wording that implies `_source-material/` is an automatic removal queue

## Completion And Archival

Keep plan status explicit. A plan may remain in `active-plans/` with `Status: DONE` during implementation review and closeout, but once validation, root index updates, and reporting updates are complete, move the numbered folder to `archive/archived-diagnosis-plans/` and leave the historical context in the report and journal.

## Implementation Order

| Order | Status | Plan | Why it lands here |
| --- | --- | --- | --- |
| 1 | DONE | `01-repo-hygiene-cleanup/` | Locks the portfolio structure so later plans do not regress into document chaos. |
| 2 | DONE | `11-repository-documentation-sweep/` | Rebuilt the package doc routing layer, published the authority map and context tests, and turned documentation updates into a standing delivery rule. |
| 3 | TODO | `02-downstream-reliability-hardening/` | Fixes the proven womanvshorse/spinner failure families before autonomy scales them. |
| 4 | TODO | `05-completion-validation-matrix/` | Defines what “done” means across web, game, script, service, desktop, and Android repos. |
| 5 | TODO | `03-asset-pipeline-architecture/` | Replaces asset-route guesswork with a capability, provenance, and QA system. |
| 6 | TODO | `04-asset-quality-and-blender-excellence/` | Raises the visual quality bar and documents truthful Blender support. |
| 7 | DONE | `09-sdk-model-router-and-provider-strategy/` | Freezes the OpenCode vs AI SDK vs Apps SDK split before new services are built. |
| 8 | TODO | `06-spec-factory-and-intake-mcp/` | Designs the idea-to-approved-brief factory and ChatGPT/MCP ingress. |
| 9 | TODO | `07-autonomous-downstream-orchestration/` | Wraps Scafforge generation in a PR-based downstream execution service. |
| 10 | TODO | `08-meta-improvement-loop/` | Turns repeated downstream failures into package-level investigation and fix work. |
| 11 | DONE | `12-skill-system-expansion-and-meta-skill-engineering/` | Adds a disciplined path for Scafforge’s own skill evolution and external-skill distillation. |
| 12 | TODO | `13-meta-skill-engineering-repo-hardening/` | Hardens the separate Meta-Skill-Engineering repo into a fully agent-usable suite with a complete CLI surface. |
| 13 | TODO | `14-blender-agent-repo-hardening/` | Hardens the separate blender-agent repo so Scafforge can rely on it truthfully. |
| 14 | IN PROGRESS | `10-viewer-control-plane-winui/` | Locks the WinUI client boundary and operator workflows while Phase 6 stays blocked on live backend/event surfaces. |

## Program-Level Decisions

1. Reliability and completion proof land before large-scale autonomy.
2. Asset work is split into architecture/provenance and quality/review because both are currently failing.
3. The SDK answer is hybrid: OpenCode stays the execution substrate, AI SDK wraps new services, and Apps SDK is for ChatGPT-facing ingress/UI only.
4. Adjacent systems such as the spec factory, orchestration service, model router, and WinUI control plane stay outside the package core.
5. Every implemented plan must update docs, validators, and references in the same PR where its contract changes land.

## Source Material Layout

Supporting material is grouped under:

- `_source-material/repo-hygiene/`
- `_source-material/downstream-failures/`
- `_source-material/asset-pipeline/`
- `_source-material/validation/`
- `_source-material/autonomy/`

These are active in-repo references, not an automatic removal queue. If a source note becomes superseded, replace it with a pointer or condensed successor rather than assuming it should leave the repo.
