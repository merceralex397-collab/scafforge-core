# Skill Evolution Policy

Scafforge learns from failures, research, and adjacent repositories through a bounded package lifecycle. This policy keeps that lifecycle explicit so package skill evolution does not turn into random catalog growth.

## Scope

- package skills live under `skills/`
- repo-local synthesized skills live only in generated repos under `.opencode/skills/`
- copied bundles, public skill ecosystems, and adjacent repos are research inputs, not shippable output

Use [authority-adr.md](authority-adr.md) for owner boundaries and [competence-contract.md](competence-contract.md) for the weak-model navigability bar.

## Skill-gap intake path

This policy starts only after a candidate is already accepted as package work.

| Candidate source | Minimum evidence before classification | Lives here while awaiting evaluation | Notes |
| --- | --- | --- | --- |
| Audit-origin package signal | `package-evidence-bundle.json`, `active-audits/<repo>/evidence-manifest.json`, and the investigator sidecar | `active-audits/<repo>/` | `scafforge-audit` and the active-audit sidecars decide whether the repo issue becomes package work at all. |
| Review, investigation, or operator note | concrete symptom, affected package surfaces, proof that the current package leaves no clear legal next move, and a bounded change hypothesis | the relevant numbered `active-plans/<plan>/references/` folder until a package change is scoped | Do not create package-root runtime queues for this work. |
| External source research | source identity, provenance or license note, concept summary, overlap analysis, and a rubric result | the relevant numbered `active-plans/<plan>/references/` folder until the distilled package artifact exists | The research source is input only. |

## Classification lanes

Every accepted skill-gap candidate must be classified before work starts:

- `prompt-contract-gap` -> adjust `agent-prompt-engineering` guidance when the failure is wording, routing, or stop-condition ambiguity
- `workflow-boundary-gap` -> fix root docs, reference contracts, or template workflow surfaces when the failure is ownership or process-boundary confusion
- `missing-capability-gap` -> extend `project-skill-bootstrap`, `opencode-team-bootstrap`, or a new dedicated package skill only when a distinct reusable workflow is actually missing
- `non-skill-package-work` -> route to the right package surface when the problem is not best solved by a skill change

If the issue can be fixed by sharpening an existing skill, prompt contract, or reference, do that instead of creating a new package skill.

## External research and distillation rules

- Run every external input through [external-source-evaluation-rubric.md](external-source-evaluation-rubric.md).
- Blind import of external skills into the package or generated repos is forbidden.
- Distill useful ideas into Scafforge-owned language that matches current package contracts and terminology.
- Keep copied or researched source bundles under `_source-material/` or an adjacent repo; do not promote them into package truth verbatim.
- Record failed provenance or license checks in [rejected-sources.md](rejected-sources.md).

## Packaging rules for new or revised package skills

Use the narrowest package surface that resolves the proven gap:

1. extend an existing package skill when the owner and workflow are already present
2. extend `project-skill-bootstrap` when the gap is about repo-local skill synthesis rules
3. extend `opencode-team-bootstrap` when the gap is about generated agent, tool, or command topology
4. extend `agent-prompt-engineering` when the gap is about prompt wording, weak-model shaping, or stop conditions
5. create a new dedicated package skill only when none of the above owns the workflow cleanly

Every new or materially re-scoped package skill must include:

- Scafforge-owned purpose and boundary text
- provenance notes for any external concept that informed the change
- explicit validation expectations
- registration in `skills/skill-flow-manifest.json`
- linked updates to `AGENTS.md`, the canonical reference docs, and any touched generated-template or repo-local guidance

Package skills must stay pruned enough for weak models to navigate. Merge overlaps instead of adding near-duplicate names.

## Downstream injection and repair policy

- Greenfield repos receive package skill improvements only through the normal scaffold flow.
- Existing repos receive skill-related changes only through explicit routing, usually `scafforge-repair` follow-on stages such as `project-skill-bootstrap`, `opencode-team-bootstrap`, or `agent-prompt-engineering`.
- Do not silently mutate downstream repos just because a package skill improved.
- Repo-local skill refresh provenance must stay tied to the existing repair completion artifact family rather than a second parallel format. At minimum, the completion summary should say whether the work synthesized, repaired, or refreshed repo-local skills or agent surfaces and what current repair-cycle or repo-local evidence triggered it.

## Guardrails

- package-wide skill evolution does not create authority outside the existing owner map
- repo-local synthesized skills do not become package skills automatically
- adjacent repos such as `Meta-Skill-Engineering` remain adjacent products even when their concepts inform Scafforge policy
- a future meta-skill engineer role is not created by this policy; it would need manifest registration, owner review, and validator updates first
