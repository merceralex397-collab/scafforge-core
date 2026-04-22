# Rejected Or Quarantined Skill Sources

Use this record for external skill inputs that fail provenance, licensing, overlap, or boundary review. Quarantined sources may remain as read-only research input, but they are not package truth and they are never installable output.

| Source | Status | Blocking issue | Allowed use | Resolution path |
| --- | --- | --- | --- | --- |
| `active-plans/_source-material/asset-pipeline/assetsplanning/pipeline/stolenfromcodex/` | quarantined | copied research bundle with incomplete preserved licensing chain inside the retained snapshot, plus high overlap risk with package and repo-local skill surfaces | read-only concept extraction only after distillation review; no direct import into Scafforge or generated repos | either prove provenance and rerun the rubric before distilling a narrow concept into Scafforge-owned language, or keep the bundle quarantined and exclude it from package changes |

## Standing rule

- If provenance or license status is unclear, quarantine first.
- If overlap or weak-model navigability fails, reject the import path even when the source is technically reusable.
- Remove a source from quarantine only after the rubric is rerun and the resulting package change is fully distilled into Scafforge-owned language.

## Resolution workflow

1. Re-run the external-source rubric when provenance, license status, or overlap evidence changes.
2. If the source becomes usable, distill only the narrow accepted concept into Scafforge-owned docs, skills, or validator logic.
3. If the source remains blocked, leave the record here and treat the bundle as excluded from package implementation.
