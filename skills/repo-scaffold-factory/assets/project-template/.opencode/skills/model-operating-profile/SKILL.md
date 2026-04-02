---
name: model-operating-profile
description: Apply the `__MODEL_OPERATING_PROFILE_NAME__` operating profile for the selected downstream models. Use when shaping prompts, delegation briefs, review asks, or evidence requests for this repo.
---

# Model Operating Profile

Before reading anything else, call `skill_ping` with `skill_id: "model-operating-profile"` and `scope: "project"`.

Selected runtime profile:

- model tier: `__MODEL_TIER__`
- provider: `__MODEL_PROVIDER__`
- team lead / planner / reviewers: `__FULL_PLANNER_MODEL__`
- implementer: `__FULL_IMPLEMENTER_MODEL__`
- utilities, docs, and QA helpers: `__FULL_UTILITY_MODEL__`
- operating profile: `__MODEL_OPERATING_PROFILE_NAME__`
- prompt density: `__MODEL_PROMPT_DENSITY__`

Use this profile when drafting:

- task prompts
- delegation briefs
- review requests
- handoff expectations

Profile guidance:

`__MODEL_OPERATING_PROFILE_DESCRIPTION__`

Required rules:

__MODEL_OPERATING_PROFILE_RULES__

When ambiguity is likely, prefer a concrete output shape such as:

```text
Goal
Constraints
Expected output
Evidence required
Blockers
```
