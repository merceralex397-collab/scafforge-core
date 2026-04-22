# Scafforge User Guide

This guide is for humans operating Scafforge or a Scafforge-managed repo. Use it for routing decisions and lightweight context acquisition. Use `AGENTS.md` and the reference contracts for durable package truth.

## Lightweight context path

1. Read `README.md`.
2. Open [references/documentation-authority-map.md](references/documentation-authority-map.md).
3. Take one reference hop for the specific truth domain you need.

The current context-test evidence for this path lives in [active-plans/11-repository-documentation-sweep/references/documentation-context-tests.md](active-plans/11-repository-documentation-sweep/references/documentation-context-tests.md).

| Question | Root doc | Reference hop |
| --- | --- | --- |
| Who owns restart publication? | `AGENTS.md` | `references/authority-adr.md` |
| What is the greenfield skill chain? | `README.md` | `references/one-shot-generation-contract.md` |
| Where does the generated-repo truth hierarchy live? | `AGENTS.md` | none required |
| Where are package-versus-output boundaries defined? | `AGENTS.md` | none required |

## Choose the right route

| Need | Use | Why |
| --- | --- | --- |
| New repo, retrofit, or initial classification | `scaffold-kickoff` | Single public entrypoint that routes generation, retrofit, repair, pivot, or diagnosis |
| Read-only diagnosis or evidence validation | `scafforge-audit` | Validates findings before they become canonical and emits the diagnosis pack |
| Managed workflow repair after audit | `scafforge-repair` | Applies safe repair, regeneration follow-up, and verification routing |
| Canonical-truth change midstream | `scafforge-pivot` | Updates brief truth first, then routes affected refresh steps |
| Daily work inside a generated repo | `START-HERE.md` plus `/resume` or a plain-language equivalent | Generated repos expose the local next move directly |

## Generated-repo operator habits

- Treat generated slash commands as human entrypoints, not as the autonomous workflow engine.
- In most repos, `/resume` is the only command you need regularly.
- `/kickoff` is useful for the first generated-repo session, but plain language is usually enough if the repo is already signposted.
- The agent's real operating surfaces are `.opencode/tools/`, `.opencode/plugins/`, `.opencode/skills/`, `tickets/manifest.json`, and `.opencode/state/workflow-state.json`.

## Machine and clone changes

Bootstrap state is machine-specific. If you switch machines, clone onto a new host, or move into a new CI environment, run `environment_bootstrap` before resuming ticket work. Generated repos should report stale bootstrap truthfully instead of pretending prior proof still applies.

## Before reviewing a contract-changing package PR

1. Identify the affected root docs, references, generated-template docs, and validator checks.
2. Update those surfaces in the same change set; do not treat documentation as final polish.
3. Run the contract validator after changing validator-pinned docs, then run the wider package validation stack required by the repo instructions.
4. Record any residual drift or environment blockers explicitly instead of implying the docs are already aligned.
