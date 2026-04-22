# Skill Validation Policy

Skill-governance checks run through the existing package contract surface:

- `npm run validate:contract`
- `python3 scripts/validate_scafforge_contract.py`

This keeps skill evolution reviewable and fail-predictable instead of depending on prose alone.

## Automated checks

The contract validator must fail when any of these drift:

- `skills/skill-flow-manifest.json` is missing skill-governance metadata
- package skill owners stop being single-owner domains
- the package skill catalog grows past the approved limit
- the default local skill catalog grows past the approved limit or duplicates a lane name
- the skill-governance references disappear or stop naming distillation, provenance, rejection, and weak-model expectations
- the affected skill docs, prompt refs, and team-bootstrap refs stop matching the packaging and repair rules

## Initial thresholds

| Signal | Threshold | Failure meaning |
| --- | --- | --- |
| `max_package_skills` | 12 | A new package skill is being added without first pruning or deliberately revising the approved ceiling. |
| `max_default_local_skills` | 12 | The generated baseline pack is growing beyond the smallest navigable set for weak models. |
| Package skill owner uniqueness | exactly one manifest owner per package skill | A proposed change creates a second owner for a truth domain and must be reviewed against `authority-adr.md`. |
| Direct external import policy | always forbidden | A source is being treated as shippable output instead of research input. |

## Manual review questions

Automation cannot prove originality or good judgment by itself. Every skill-related PR must answer:

1. **Distillation quality:** Was the source material rewritten into Scafforge-owned language instead of copied verbatim?
2. **Originality vs source overlap:** Did the change merge or prune overlaps instead of creating another near-duplicate skill or role?
3. **Weak-model navigability:** Does the result make the next legal move clearer for weaker models, or did it add another ambiguous route?

## Coupled doc updates

When skill governance changes package truth, update the same change set across:

- `AGENTS.md`
- the canonical skill-governance references in `references/`
- any touched skill docs under `skills/`
- `skills/skill-flow-manifest.json`
- `scripts/validate_scafforge_contract.py`
