# External Source Evaluation Rubric

Use this rubric before any copied skill bundle, public skill ecosystem, or adjacent repository influences Scafforge package behavior.

## Non-negotiable gates

1. Research input is never shippable output.
2. Missing or ambiguous licensing or provenance quarantines the source.
3. Distillation into Scafforge-owned language is mandatory.
4. [competence-contract.md](competence-contract.md) is the weak-model navigability bar.

## Evaluation checklist

| Dimension | Accept when | Quarantine or reject when |
| --- | --- | --- |
| Mission fit | the source helps Scafforge build, audit, repair, or hand off repos more deterministically | it is a general skill dump, personal workflow bundle, or unrelated utility catalog |
| Originality needed | the useful concept can be restated as Scafforge-owned policy, procedure, or validator logic | the only value comes from copying a prewritten skill body verbatim |
| Overlap risk | it fills a clear gap or sharpens an existing surface without creating a second owner | it mostly renames or rephrases an existing skill, prompt contract, or workflow reference |
| Weak-model navigability | it reduces ambiguity, keeps one legal next move visible, and stays short enough for weak models to route correctly | it adds umbrella jargon, giant catalogs, or overlapping triggers that make routing harder |
| Licensing and provenance | the origin, license status, and copied-material boundary are explicit enough to cite and review | the origin is vague, the license chain is missing, or the copied material cannot be safely attributed |
| Boundary fit | it respects package-vs-generated-repo-vs-adjacent-repo boundaries | it collapses those layers or implies direct import into generated repos |

## Decision outcomes

| Outcome | Meaning |
| --- | --- |
| Adopt by distillation | Keep the source as research input, then rewrite the useful concept into Scafforge-owned docs, code, or validation. |
| Quarantine | Keep the source only as read-only research input until provenance, overlap, or boundary concerns are resolved. |
| Reject | Do not use the source for package changes. |

Blind import of external skills into the package or into generated repos is forbidden in every outcome.

## Applied dispositions

| Source | Decision | Why | Allowed next step |
| --- | --- | --- | --- |
| `active-plans/_source-material/asset-pipeline/assetsplanning/pipeline/stolenfromcodex/` | Quarantine | The bundle is explicitly copied research, the top-level note only says the plugins were "stolen" and "open source", and the preserved snapshot does not carry a complete license chain inside the retained bundle. The sample skills are also large ready-made domain surfaces that would create overlap and weak-model routing bloat if imported directly. | Distill only narrow concepts into Scafforge-owned asset-pipeline or repo-local guidance after provenance review. Record the quarantine in `rejected-sources.md`. |
| Adjacent `Meta-Skill-Engineering` repository | Adopt by distillation only | The repo is a real adjacent product with its own 17-package inventory, OpenCode-focused studio flows, and separate agent/runtime contract. It is useful for comparative methodology around provenance, evaluation, packaging, and catalog curation, but importing its skill packages directly would collapse the adjacent-repo boundary and overload Scafforge's package catalog. | Reuse ideas only after rewriting them into Scafforge-owned policy, docs, or validator rules. Keep the repo itself separate. |

## Distillation expectations

- cite the source repo or bundle in the implementing plan or PR notes
- rewrite the useful idea in Scafforge terminology
- name what was intentionally not imported
- attach a validation story and any required downstream routing
- add a manual PR-review check for distillation quality because automation can verify structure but not originality on its own
