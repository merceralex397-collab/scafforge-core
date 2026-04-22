# Scafforge Architecture

## Overview

Scafforge is a package repo that generates and repairs OpenCode-oriented operating layers for other repositories. It is not the generated project, and it is not the adjacent services that may later schedule, visualize, or wrap package runs.

For document routing, use `README.md` for orientation, `AGENTS.md` for package boundaries and standing rules, and `references/*.md` for durable contract detail.

## SDK Layering

Scafforge uses a layering decision rather than a rewrite-first decision.

- **OpenCode** remains the execution substrate for generated repos and package contracts.
- **AI SDK** belongs in adjacent services that need provider routing, failover, tool-loop agents, or service-side orchestration.
- **OpenAI Apps SDK** stays bounded to ChatGPT-facing ingress, review, and UI surfaces.
- The executable router contract stays in an adjacent service repo; package docs describe the policy boundary but do not embed router logic in package core.

## System layers

```text
adjacent services / workspaces
  spec factory, router, orchestration, control plane
host agent
  runs Scafforge package skills
Scafforge package
  skills/, references/, scripts/, tests/, active-audits/, active-plans/
generated repo
  docs/, tickets/, .opencode/, START-HERE.md
downstream agent
  works inside the generated repo using its local operating layer
```

## Package skill layout

The package currently ships twelve skill directories:

| Group | Skills | Role |
| --- | --- | --- |
| Default greenfield spine | `scaffold-kickoff`, `spec-pack-normalizer`, `repo-scaffold-factory`, `project-skill-bootstrap`, `opencode-team-bootstrap`, `agent-prompt-engineering`, `ticket-pack-builder`, `handoff-brief` | One-shot scaffold path |
| Post-generation lifecycle | `scafforge-audit`, `scafforge-repair`, `scafforge-pivot` | Diagnosis, managed repair, and canonical-truth change |
| Optional extension | `asset-pipeline` | Asset and provenance scaffolding for game or asset-heavy repos |

The orchestration graph lives in `skills/skill-flow-manifest.json`.

## Default routes

Greenfield remains the primary package path:

```text
scaffold-kickoff
  -> spec-pack-normalizer
  -> repo-scaffold-factory
  -> repo-scaffold-factory:verify-bootstrap-lane
  -> project-skill-bootstrap
  -> opencode-team-bootstrap
  -> agent-prompt-engineering
  -> ticket-pack-builder
  -> repo-scaffold-factory:verify-generated-scaffold
  -> handoff-brief
```

The same run still allows one batched blocking-decision round, requires one uninterrupted same-session generation pass, and must finish with immediate continuation proof before handoff publication. Asset-heavy game repos may insert `asset-pipeline` between `project-skill-bootstrap` and `opencode-team-bootstrap`.

Other run types stay bounded:

| Run type | Sequence summary |
| --- | --- |
| Retrofit | `scaffold-kickoff` -> `spec-pack-normalizer` if needed -> `opencode-team-bootstrap` -> `project-skill-bootstrap` -> `ticket-pack-builder` -> `scafforge-audit` -> `handoff-brief` |
| Managed repair | `scaffold-kickoff` -> `scafforge-repair` -> bounded regeneration follow-up -> `handoff-brief` |
| Pivot | `scaffold-kickoff` -> `scafforge-pivot` -> affected refresh steps -> `handoff-brief` |
| Diagnosis or review | `scaffold-kickoff` -> `scafforge-audit` -> optional package-side follow-up -> `handoff-brief` |

## Generated repo contract surfaces

Generated repos expose a structured truth hierarchy:

| Surface | Owns |
| --- | --- |
| `docs/spec/CANONICAL-BRIEF.md` | Durable project facts and decisions |
| `tickets/manifest.json` | Machine queue state and artifact metadata |
| `.opencode/state/workflow-state.json` | Transient stage and approval state |
| `.opencode/state/artifacts/` | Canonical artifact bodies and registry state |
| `.opencode/meta/bootstrap-provenance.json` | Scaffold and repair provenance |
| `START-HERE.md` | Derived restart surface |

### Adjacent spec-factory boundary

Adjacent systems such as the spec factory, orchestration service, model router, and control plane consume Scafforge contracts without becoming hidden package authority.

The spec factory owns rough intake, drafting, review, approval, and persisted handoff bundles. Scafforge still owns package-side brief normalization and generation routing. ChatGPT or MCP ingress is therefore transport and review only, not a hidden authority layer.

### Adjacent orchestration boundary

The adjacent orchestration service wraps approved briefs, package execution, and downstream PR phases.

- It may invoke `scaffold-kickoff` only after an approved-brief bundle is persisted and addressable.
- It owns job envelopes, idempotency or retry tokens, PR automation, reviewer assignment, and operator permission modes.
- It may read generated canonical surfaces and restart outputs.
- It must stay read-only over generated canonical repo truth.

### Adjacent model-router boundary

The model router is an adjacent service concern even when it uses the AI SDK.

- Package docs may define provider categories, fallback rules, and model-update policy.
- Executable router interfaces, credentials, and runtime selection logic stay outside the package repo.
- Provider, model-family, exact model ID, and transport-path evidence belong in service or orchestration records rather than package-root long-lived truth.

### Adjacent control-plane boundary

The control plane is an adjacent operator client, not a backend substitute.

- It may render orchestration state, generated-repo truth projections, package investigations, and provider/router summaries.
- All approvals, overrides, pause/resume, retry, merge-approval, and router-policy changes stay backend-mediated.
- Ambiguous auth, trust, or connectivity must force read-only behavior instead of alternate mutation paths.
- Local shells, WSL, SSH, and GitHub transport choices must not become hidden authority bypasses.
