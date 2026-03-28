# Scafforge User Guide

This guide is for the human operator using a Scafforge-managed repo.

## What The Generated `/commands` Are

Files under `.opencode/commands/` are human entrypoints.

They are:
- short preset prompts aimed at the generated repo's team leader
- a convenience layer for common session starts
- not the real workflow engine

The real workflow lives in:
- `.opencode/tools/`
- `.opencode/plugins/`
- `.opencode/skills/`
- `tickets/manifest.json`
- `.opencode/state/workflow-state.json`

The agent should use those surfaces directly once work begins. It should not need to call slash commands itself.

## The Short Answer

In most repos, `/resume` is the only command you will use regularly.

`/kickoff` can be useful for the first session in a newly generated repo.

Most other generated commands are optional scenario-specific entrypoints. They are not required for normal day-to-day operation, and the agent usually has the same underlying ability without them.

## What Each Command Is For

`/resume`
- Main restart entrypoint.
- Use when returning to an in-progress repo.
- High value. This is the command most users actually need.

`/kickoff`
- First-session entrypoint for a fresh repo or freshly repaired repo.
- Useful once, then usually replaced by `/resume`.
- Optional if you prefer giving the same instruction in plain language.

`/bootstrap-check`
- Focused entrypoint for environment/bootstrap problems.
- Use when the repo is blocked on missing runtime, dependencies, or stale bootstrap proof.
- Optional convenience only.

`/issue-triage`
- Focused entrypoint for defects found after a ticket was already completed.
- Use when historical work needs reopen/follow-up/rollback routing.
- Optional convenience only.

`/reverify-ticket`
- Focused entrypoint for restoring trust on a completed ticket after remediation evidence exists.
- Use when a historical ticket is `suspect`, `invalidated`, or pending reverification.
- Optional convenience only.

`/plan-wave`
- Human entrypoint for choosing the next foreground wave and possible parallel candidates.
- Mostly useful in repos that actually use the lane/parallel model.
- Usually unnecessary for a single active lane workflow.

`/run-lane`
- Human entrypoint for running one bounded leased lane.
- Only useful when you are intentionally using the parallel-lane model.
- Usually unnecessary in normal single-lane operation.

`/join-lanes`
- Human entrypoint for merging completed parallel lanes back into one foreground path.
- Only useful if parallel lanes were actually used.
- Usually unnecessary otherwise.

## Are These Commands Necessary?

Usually not.

The commands are mostly:
- operator shortcuts
- preset prompts for specific situations
- reminders about the intended workflow

They are not generally required for correctness. If the generated repo is healthy, the team leader can usually do the same work when you ask in plain language.

The important exception is practical, not architectural:
- `/resume` is worth keeping because it gives one predictable restart entrypoint.

Everything else should be judged by whether it reduces operator confusion in that repo.

## Does The Agent Have The Same Ability Without The Command?

Yes, in most cases.

The command does not grant special powers. It usually just:
- selects the team leader agent
- frames the situation
- reminds the model which canonical tools and state files to use

The actual capabilities come from the repo's tools, plugins, state, and local skills.

That means:
- a human can often say the same thing directly in chat
- the team leader can often perform the same work without a slash command
- the agent should not be telling itself to use `/resume`, `/kickoff`, or similar commands as internal workflow steps

## Recommended Minimal User Workflow

For most repos:

1. First session: use `/kickoff` or give an equivalent plain-language start instruction.
2. Ongoing sessions: use `/resume`.
3. If the repo hits a workflow blocker: use Scafforge host-side audit and repair from the Scafforge package repo, not generated-repo slash commands.

That is the normal path.

## Guidance For Scafforge Generation

Scafforge should treat generated commands as a user-facing affordance layer, not as core workflow logic.

Default recommendation:
- always generate `/resume`
- optionally generate `/kickoff`
- generate the advanced commands only when the repo genuinely benefits from them

Commands like `/plan-wave`, `/run-lane`, and `/join-lanes` are not legacy in the sense of being broken, but they are often over-provisioned. In a typical single-operator repo they add surface area faster than they add value.

## Practical Conclusion From GPTTalker

GPTTalker's command set is broader than what the operator actually uses.

That does not mean the commands are all wrong. It means Scafforge currently tends to generate more user entrypoints than many repos need.

The safer Scafforge stance is:
- keep `/resume` as the primary user command
- keep `/kickoff` as an optional first-session command
- treat the rest as advanced or situational
- never rely on slash commands as the agent's internal workflow
