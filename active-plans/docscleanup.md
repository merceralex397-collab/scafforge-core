# Docs Cleanup Note

## Purpose

This note defines the organization rule for planning documentation inside the Scafforge package repo.

## Boundary Rule

Keep package-owned planning here.

Keep active supporting references here too.

`active-plans/` should only keep:

- the numbered implementation plans
- root planning summaries
- current package-owned reference notes that are still being actively revised into implementation guidance
- supporting source material that still informs package decisions or future implementation work

`_source-material/` is part of the active documentation set. It is not an automatic removal queue.

## Current Supporting Material Branches

These are staged under `_source-material/` so the canonical plans stay readable, but they remain active in-repo references:

- `_source-material/autonomy/hugeupgrade/`
- `_source-material/asset-pipeline/assetsplanning/game-asset-generation-research.md`
- `_source-material/asset-pipeline/assetsplanning/research-about-video-game-art-assets-designs-and-a.md`
- `_source-material/asset-pipeline/assetsplanning/pipeline/asset-pipeline-agent-research-2026-04-14.md`
- `_source-material/asset-pipeline/assetsplanning/pipeline/minimax/`
- `_source-material/asset-pipeline/assetsplanning/pipeline/stolenfromcodex/`
- `_source-material/downstream-failures/womanvshorseissues/`
- `_source-material/repo-hygiene/docscleanup-original.md`
- `_source-material/validation/completionqualityvalidation/test-android-apps/`

## Keep Candidates

These should remain in this repo:

- all numbered plan folders under `active-plans/`
- `active-plans/README.md`
- `active-plans/WORK-JOURNAL.md`
- `active-plans/FULL-REPORT.md`
- this verified cleanup note

## Open Questions

- `toolstoimplement.md` may still be useful as an active reference until the cross-platform validation plan has been implemented.
- some vendor docs in `_source-material/` may deserve condensed summaries or plan-specific extracts so the source notes are easier to navigate.

## Next Action

Do not move anything out of `active-plans/` by default. Use the numbered plans as the canonical working set, and use `_source-material/` as the active supporting reference library for those plans. If a source note becomes outdated, replace it with a clearer pointer or condensed summary rather than assuming repo removal.
