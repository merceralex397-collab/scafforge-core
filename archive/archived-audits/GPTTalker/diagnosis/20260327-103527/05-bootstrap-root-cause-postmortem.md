# Bootstrap Root-Cause Postmortem

## Summary

The `scafforge-audit` and `scafforge-repair` flows did not identify or fix the real bootstrap defect in this repo.

They correctly observed the symptom as `ENV002` (`pytest` missing from `.venv/bin/pytest`), but they misclassified the cause as a repo-local/operator bootstrap prerequisite instead of a managed workflow/tooling defect inside `.opencode/tools/environment_bootstrap.ts`.

The result was:

- audit routed the problem as "rerun `environment_bootstrap`" instead of surfacing a package-managed tool bug
- repair refreshed other managed surfaces, then preserved `ENV002` as a remaining blocker
- repeated bootstrap runs in the same repo on the same machine kept executing the same broken `uv sync --locked` path

## Confirmed Defect

The current `environment_bootstrap` tool contains logic that appears to support `--extra dev`, but the section parser it relies on is broken.

Relevant code:

- [environment_bootstrap.ts](/home/pc/projects/GPTTalker/.opencode/tools/environment_bootstrap.ts#L73)
- [environment_bootstrap.ts](/home/pc/projects/GPTTalker/.opencode/tools/environment_bootstrap.ts#L97)
- [environment_bootstrap.ts](/home/pc/projects/GPTTalker/.opencode/tools/environment_bootstrap.ts#L141)
- [pyproject.toml](/home/pc/projects/GPTTalker/pyproject.toml#L16)

The bug is in `hasSectionValue()`:

```ts
const blockMatch = text.match(new RegExp(`\\[${section.replace(".", "\\.")}\\]([\\s\\S]*?)(?:\\n\\[|$)`, "m"))
```

With the `m` flag, `$` matches the end of the header line itself. For `[project.optional-dependencies]`, that causes the captured section body to be empty. As a result:

- `hasPyprojectDevExtra()` returns `false`
- `detectUvSyncDependencyArgs()` returns `[]`
- the bootstrap command stays `uv sync --locked`
- `pytest` is never installed from the `dev` extra

I reproduced that parser behavior locally against this repo's `pyproject.toml`: the section match succeeded but returned an empty body, and `dev_match` was `false`.

## Live Evidence That The Bug Is Real

This is not just a stale transcript claim. The newest bootstrap artifacts in this same repo still show the broken command path:

- [2026-03-27T13-20-16-174Z-environment-bootstrap.md](/home/pc/projects/GPTTalker/.opencode/state/artifacts/history/exec-014/bootstrap/2026-03-27T13-20-16-174Z-environment-bootstrap.md#L45)
- [2026-03-27T13-23-09-710Z-environment-bootstrap.md](/home/pc/projects/GPTTalker/.opencode/state/artifacts/history/exec-014/bootstrap/2026-03-27T13-23-09-710Z-environment-bootstrap.md#L45)

Both artifacts show:

- command: `uv sync --locked`
- missing prerequisite: `/home/pc/projects/GPTTalker/.venv/bin/pytest`

Those artifacts were produced after the repo-local provenance entry that claimed bootstrap had been made "uv-aware":

- [bootstrap-provenance.json](/home/pc/projects/GPTTalker/.opencode/meta/bootstrap-provenance.json#L127)

So the repo contains an intended fix, but not a working fix.

## How Audit Missed It

The original diagnosis pack treated this as a repo-local/operator follow-up instead of a managed-surface defect:

- [04-live-repo-repair-plan.md](/home/pc/projects/GPTTalker/diagnosis/20260327-103527/04-live-repo-repair-plan.md#L85)
- [04-live-repo-repair-plan.md](/home/pc/projects/GPTTalker/diagnosis/20260327-103527/04-live-repo-repair-plan.md#L121)

Specifically, it said:

- rerun `environment_bootstrap`
- do not continue lifecycle verification until repo-local `pytest` and `ruff` are available
- create or route an operator follow-up

That diagnosis was incomplete because it did not do the critical correlation step:

1. read the failing bootstrap artifact
2. inspect the actual `environment_bootstrap.ts` implementation
3. verify whether the implementation really supports the repo's dependency layout

If audit had performed that correlation, it would have found:

- repo uses `[project.optional-dependencies].dev`
- bootstrap artifacts still show plain `uv sync --locked`
- current tool source depends on a parser helper
- that parser helper is faulty for multiline TOML sections

So the correct classification was not "manual prerequisite" or "operator follow-up." It was "managed workflow tool defect in `environment_bootstrap.ts`."

## How Repair Missed It

The repair skill requires rerunning bootstrap and verification when bootstrap issues are part of the repair basis:

- [scafforge-repair SKILL.md](/home/pc/.codex/skills/scafforge-repair/SKILL.md#L155)
- [scafforge-repair SKILL.md](/home/pc/.codex/skills/scafforge-repair/SKILL.md#L166)

But in practice the repair flow still missed the defect for two reasons:

### 1. Repair basis inherited audit's misclassification

Because the diagnosis pack framed `ENV002` as a repo-local bootstrap prerequisite rather than a tool bug, repair treated it as a remaining blocker instead of a repair target.

### 2. Repair accepted repeated failing bootstrap artifacts at face value

The repair flow reran verification and preserved `ENV002`, but it did not perform the additional root-cause check required after repeated identical failures:

- compare the newest bootstrap artifact command list with the current tool source
- verify that the intended fix path is actually reachable in code
- treat repeated identical command traces as evidence that the managed tool path is still defective

Instead, repair converged to "managed repair completed; bootstrap still failed," which was only partially correct. The managed workflow layer was still defective in one important place.

## Why This Is A Glaring Flaw

This was not a subtle infrastructure issue. The failure pattern was direct and repetitive:

- same missing executable every time: `.venv/bin/pytest`
- same command every time: `uv sync --locked`
- same repo layout every time: `pytest` in `dev` optional dependencies
- same contradiction every time: tool intended to support extras, artifact proves extras were not applied

Once multiple bootstrap artifacts showed the exact same command trace, the audit and repair flows should have escalated from "environment blocked" to "bootstrap tool path is still broken."

## What The Skills Should Have Done

### `scafforge-audit`

For `ENV002` in uv-managed repos, audit should:

1. read the latest bootstrap artifact command list
2. read `pyproject.toml`
3. read `.opencode/tools/environment_bootstrap.ts`
4. compare expected dependency-group detection with the actual recorded bootstrap command
5. emit a managed-surface finding when the tool should have included extras/groups but did not

### `scafforge-repair`

When the repair basis includes repeated bootstrap failures with identical command traces, repair should:

1. treat the bootstrap tool as a managed-surface candidate, not only as an execution prerequisite
2. inspect whether the repaired code path is actually reachable for the repo's pyproject layout
3. patch the managed tool if the root cause is in scaffold-managed code
4. rerun bootstrap after the patch
5. only leave an operator/environment blocker if the bootstrap still fails for a non-tool reason

## Corrected Diagnosis

The real defect is:

- managed tool bug in `.opencode/tools/environment_bootstrap.ts`
- specifically in TOML section parsing for optional dependency detection

The real consequence is:

- `environment_bootstrap` cannot honor this repo's `dev` dependency layout
- repeated bootstrap retries are doomed until the parser is fixed

The correct repair class is:

- safe managed-surface repair
- not merely operator/bootstrap rerun guidance

## Recommended Follow-Up

1. Patch `hasSectionValue()` so it captures TOML section bodies correctly.
2. Rerun `environment_bootstrap` and confirm the artifact records `uv sync --locked --extra dev`.
3. Re-run audit and verify `ENV002` clears.
4. Update `scafforge-audit` so `ENV002` checks correlate bootstrap artifacts with tool source before classifying the issue as operator-only.
5. Update `scafforge-repair` so repeated bootstrap failures with unchanged command traces trigger managed-tool inspection instead of passive blocker carry-forward.

## Bottom Line

The audit and repair skills did not just "leave bootstrap failing." They failed to identify that the bootstrap failure itself was still caused by a Scafforge-managed tool defect. That is the gap that allowed the same broken bootstrap command to be retried and reclassified multiple times without the actual root cause being repaired.
