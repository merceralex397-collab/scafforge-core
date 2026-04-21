# Active Plans Index

This directory is the active Scafforge implementation program.

It has two layers:

- `_source-material/` contains active supporting references, copied research, and raw inputs that justify the plans.
- Numbered plan folders contain the canonical TODO-state implementation plans.

Every numbered folder should now be treated as a real working plan, not a summary stub. Each primary `README.md` is expected to show:

- explicit `Status: TODO`
- goal and architecture
- dependencies and unblocks
- concrete package or adjacent surfaces likely to change
- phased checkbox work
- validation gates
- documentation-update obligations

## Root Files

- `WORK-JOURNAL.md` records planning decisions and corrections made during this planning cycle.
- `FULL-REPORT.md` summarizes the whole upgrade program and the reasoning behind the sequence.
- `docscleanup.md` defines how canonical plans and supporting source material coexist inside `active-plans/`.

## Implementation Order

| Order | Status | Plan | Why it lands here |
| --- | --- | --- | --- |
| 1 | TODO | `01-repo-hygiene-cleanup/` | Locks the portfolio structure so later plans do not regress into document chaos. |
| 2 | TODO | `11-repository-documentation-sweep/` | Starts immediately and continues alongside every other implementation wave. |
| 3 | TODO | `02-downstream-reliability-hardening/` | Fixes the proven womanvshorse/spinner failure families before autonomy scales them. |
| 4 | TODO | `05-completion-validation-matrix/` | Defines what “done” means across web, game, script, service, desktop, and Android repos. |
| 5 | TODO | `03-asset-pipeline-architecture/` | Replaces asset-route guesswork with a capability, provenance, and QA system. |
| 6 | TODO | `04-asset-quality-and-blender-excellence/` | Raises the visual quality bar and documents truthful Blender support. |
| 7 | TODO | `09-sdk-model-router-and-provider-strategy/` | Freezes the OpenCode vs AI SDK vs Apps SDK split before new services are built. |
| 8 | TODO | `06-spec-factory-and-intake-mcp/` | Designs the idea-to-approved-brief factory and ChatGPT/MCP ingress. |
| 9 | TODO | `07-autonomous-downstream-orchestration/` | Wraps Scafforge generation in a PR-based downstream execution service. |
| 10 | TODO | `08-meta-improvement-loop/` | Turns repeated downstream failures into package-level investigation and fix work. |
| 11 | TODO | `12-skill-system-expansion-and-meta-skill-engineering/` | Adds a disciplined path for skill evolution and external-skill distillation. |
| 12 | TODO | `10-viewer-control-plane-winui/` | Builds the operator-facing WinUI control plane after backend contracts are stable. |

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
