# Docs Cleanup Note

## Purpose

This note defines the durable organization rule for planning documentation inside the Scafforge package repo.

## Boundary Rule

`active-plans/` stays in-repo and keeps both:

- the canonical implementation program
- the supporting documentation needed to justify or execute that program

The canonical-versus-supporting split is structural, not archival:

- numbered folders (`NN-kebab-case/`) are the canonical implementation program
- plan-local support material belongs in `NN-kebab-case/references/`
- `_source-material/` is the shared active reference library for copied research, raw notes, and source inputs

`_source-material/` is part of the active documentation set. It is not an automatic removal queue.

## Path-By-Path Classification

| Path | Classification | Rule |
| --- | --- | --- |
| `active-plans/README.md` | root summary | portfolio index and execution order |
| `active-plans/docscleanup.md` | root summary | placement and naming policy |
| `active-plans/FULL-REPORT.md` | root summary | cross-plan program summary |
| `active-plans/WORK-JOURNAL.md` | historical provenance | dated decision log |
| `active-plans/codexinstructions.md` | supporting reference | portfolio-wide execution guide |
| `active-plans/NN-kebab-case/README.md` | canonical plan | one authoritative implementation body per plan |
| `active-plans/NN-kebab-case/references/*.md` | supporting reference | plan-local notes, prompt packs, intake docs, or evidence |
| `active-plans/_source-material/**` | supporting reference | active research, copied docs, and raw source inputs |

If a supporting file is being kept only as an untouched origin snapshot, treat it as historical provenance inside the supporting library rather than as a second plan.

## Placement Rules

1. Start new implementation planning work in a numbered folder, not at the root.
2. Keep the canonical instruction set in that folder's `README.md`.
3. Put copied docs, research dumps, and raw notes in `_source-material/` when they support multiple plans or need to stay close to their original shape.
4. Put plan-specific support notes in the relevant folder's `references/`.
5. Keep the root of `active-plans/` for portfolio-wide navigation, policy, reporting, journal entries, and execution guidance only.

## Naming Rules

- plan folders use `NN-kebab-case/`
- the primary plan file is always `README.md`
- plan-local support notes use descriptive kebab-case names
- issue-intake or extra-scope notes belong under the relevant plan's `references/`, not at the root

## Maintenance Checklist

When editing the planning portfolio:

1. update the numbered-folder plan first
2. update `active-plans/README.md` if ordering, status, or portfolio structure changes
3. update `FULL-REPORT.md` if the program summary changes
4. update `WORK-JOURNAL.md` when a classification or policy decision changes
5. keep each numbered plan's documentation impact checklist current so doc updates stay visible and reviewable
6. add or revise `_source-material/` only when it preserves useful provenance or reduces noise in a canonical plan

## Documentation Checklist Rule

`AGENTS.md` owns the standing package rule that contract-changing PRs must update docs in the same change set. Inside `active-plans/`, the practical formatting rule is:

- every numbered plan should carry a documentation impact checklist naming the docs, references, generated-template docs, or adjacent-repo docs that move with that plan
- the checklist is a planning reminder, not a second source of authority for package policy
- if a plan changes package or template contract truth, the checklist items should be completed in the same PR instead of deferred to a final cleanup pass

## Anti-Patterns

- hidden canonical plans in `_source-material/`
- plan-specific notes stored at the root
- duplicate root summaries that shadow a numbered folder
- numbered folders without one obvious implementation `README.md`
- wording that treats `_source-material/` as temporary staging for deletion

## Current Supporting Material Branches

These remain active in-repo references because they still justify current or future implementation work:

- `_source-material/autonomy/hugeupgrade/`
- `_source-material/asset-pipeline/assetsplanning/game-asset-generation-research.md`
- `_source-material/asset-pipeline/assetsplanning/research-about-video-game-art-assets-designs-and-a.md`
- `_source-material/asset-pipeline/assetsplanning/pipeline/asset-pipeline-agent-research-2026-04-14.md`
- `_source-material/asset-pipeline/assetsplanning/pipeline/minimax/`
- `_source-material/asset-pipeline/assetsplanning/pipeline/stolenfromcodex/`
- `_source-material/downstream-failures/womanvshorseissues/`
- `_source-material/repo-hygiene/docscleanup-original.md`
- `_source-material/validation/completionqualityvalidation/test-android-apps/`

`WORK-JOURNAL.md` and `codexinstructions.md` are intentionally part of the inventory but not part of the root routing layer rewrite: the journal stays historical provenance, and the execution guide stays a supporting reference.

## Completed-Plan Exit Rule

Do not archive a plan the moment implementation starts. Keep it in `active-plans/` with explicit status while review and closeout are still live. After the implementation, validation, and root-summary updates are complete, move the numbered folder to `archive/archived-diagnosis-plans/` and leave the historical trail in `FULL-REPORT.md` and `WORK-JOURNAL.md`.
