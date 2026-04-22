# MiniMax Family Notes

These notes capture the Scafforge operating defaults and prompting guidance for MiniMax-family coding lanes.

The file path is historical. Treat the guidance here as family-level behavior guidance, not as a durable claim that one exact MiniMax model ID should remain package truth forever.

## Scafforge defaults

Use these defaults for generated agents in this scaffold pack when a MiniMax-family coding lane is chosen and no project-specific override is explicitly justified:

- `temperature: 1.0`
- `top_p: 0.95`
- `top_k: 40`

Scafforge applies this same profile to leadership, planning, implementation, review, QA, and utility agents for the selected MiniMax-family coding lane so the generated repo does not fragment into low-creativity and high-creativity subprofiles.

## Observed failure mode at low temperature

The GPTTalker audit showed that very low-temperature reviewer and QA agents tended to produce repetitive approval templates instead of independent validation. In practice, this means MiniMax-family reviewers should not be pushed into near-deterministic sampling if the goal is to catch syntax, import, or tool-registration failures.

## Prompting guidance

- Require executable evidence, not summary claims.
- Ask reviewer and QA roles to include raw command output in artifacts.
- Prefer explicit stage responsibilities and artifact contracts over open-ended prose.
- Keep prompts concrete about pass or fail signals, blocker behavior, and required outputs.

## Context guidance

- Keep the active ticket, stage, and artifact path explicit in every delegation brief.
- Prefer short, structured task packets over long conversational loops.
- When the model starts mirroring the shape of previous outputs instead of reasoning from evidence, tighten the required output contract instead of lowering sampling.

## Workflow notes

- Pair MiniMax-family lanes with deterministic workflow gates so the model cannot advance work on artifact existence alone.
- The smoke-test stage is intentionally tool-driven and should remain deterministic even when the surrounding workflow uses agents.
- Verify the exact MiniMax route and model ID at implementation time. The same family may appear through a native provider SDK, a community AI SDK adapter, or an OpenCode-compatible coding lane.
