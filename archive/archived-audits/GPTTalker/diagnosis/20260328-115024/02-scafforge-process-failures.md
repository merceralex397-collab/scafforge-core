# Scafforge Process Failures

## Scope

- Subject repo: `/home/pc/projects/GPTTalker`
- Diagnosis timestamp: `2026-03-28T11:50:24Z`
- Diagnosis kind: `post_package_revalidation`
- Failure map reconciled from:
  - current repo-managed workflow surfaces
  - installed Scafforge template surfaces under `/home/pc/.codex/skills/repo-scaffold-factory/assets/project-template/`
  - canonical state in `tickets/manifest.json`, `.opencode/state/workflow-state.json`, and `.opencode/meta/bootstrap-provenance.json`
  - supplied transcript `sessionlog2703.md`

## Failure Map

### CURR-001 -> WFLOW024 carry-forward drift

- Linked Report 1 finding id: `CURR-001`
- Implicated generated surfaces:
  - repo-local `.opencode/tools/ticket_reconcile.ts`
  - repo-local `.opencode/tools/ticket_create.ts`
  - repo-local `.opencode/tools/issue_intake.ts`
  - repo-local `.opencode/plugins/stage-gate-enforcer.ts`
  - `tickets/manifest.json`
- Cross-check package template surfaces:
  - `/home/pc/.codex/skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_reconcile.ts`
  - `/home/pc/.codex/skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_create.ts`
  - `/home/pc/.codex/skills/repo-scaffold-factory/assets/project-template/.opencode/tools/issue_intake.ts`
- Ownership class: `generated-repo managed-surface drift`
- How the workflow allowed the issue through:
  - The subject repo still carries the older historical-reconciliation contract, including the `supersededTarget` typo, direct-artifact-only evidence lookup, and publish-blocking `invalidated` supersede outcome.
  - The installed package template already contains the safer target pattern, so the live repo failure is no longer "package work missing" in the abstract. The repo simply has not been refreshed onto the newer deterministic managed surfaces.
  - Because `EXEC-012` remains `done + superseded + invalidated` with no direct artifacts, `handoff_publish` can still deadlock on a state the repaired package is meant to resolve.

## Ownership Classification

- `CURR-001`: `generated-repo managed-surface drift`
- Historical transcript basis (`SESSION002`, `SESSION004`, `SESSION005`, `SESSION006`): `Scafforge package defect`, but already reflected in the installed package template and current repo-local prompt/skill hardening

## Root Cause Analysis

- The earlier transcript-backed failures from `sessionlog2703.md` were genuine package-level defects at the time they occurred.
- The installed package template now shows those fixes have been made:
  - historical reconciliation now accepts registry-backed evidence
  - supersede-through-reconciliation no longer leaves a publish-blocking invalidated ticket
  - the lifecycle explainer now stops on repeated contradictions and forbids evidence-free PASS claims
- The subject repo still exposes one live blocker because its repo-local managed copies predate those package-side changes.
- This is the expected failure mode for a post-package revalidation that happens before the subject repo has been refreshed with `scafforge-repair`: the package is ready, but the repo is still on stale generated surfaces.
