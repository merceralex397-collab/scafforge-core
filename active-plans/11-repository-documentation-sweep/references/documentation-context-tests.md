# Documentation Context Tests

These tests verify that a newcomer or agent can answer the basic package-boundary questions from root docs with no more than one reference hop.

## Newcomer-context test

| Question | Root doc path used | Reference hop used | Answer found | Within one root-doc hop? | Result |
| --- | --- | --- | --- | --- | --- |
| Who owns restart publication? | `AGENTS.md -> Authority baseline` | `references/authority-adr.md -> Ownership Map` | `handoff-brief` owns restart publication from the verified final snapshot. | Yes | PASS |
| What is the greenfield skill chain? | `README.md -> Default lifecycle` | `references/one-shot-generation-contract.md -> Greenfield contract` | `scaffold-kickoff -> spec-pack-normalizer -> repo-scaffold-factory -> verify-bootstrap-lane -> project-skill-bootstrap -> opencode-team-bootstrap -> agent-prompt-engineering -> ticket-pack-builder -> verify-generated-scaffold -> handoff-brief`. | Yes | PASS |
| Where does the generated-repo truth hierarchy live? | `AGENTS.md -> Canonical generated-repo truth hierarchy` | none | `docs/spec/CANONICAL-BRIEF.md`, `tickets/manifest.json`, `.opencode/state/workflow-state.json`, `.opencode/state/artifacts/`, `.opencode/meta/bootstrap-provenance.json`, and derived restart surfaces. | Yes | PASS |
| Where are package-versus-output boundaries defined? | `AGENTS.md -> Repo identity` | none | The package layer, output layer, and adjacent systems are defined separately, and output-layer runtime state must not be imported into the package root. | Yes | PASS |

## Agent-context test

| Question | Root doc path used | Reference hop used | Answer found | Within one root-doc hop? | Result |
| --- | --- | --- | --- | --- | --- |
| Who owns restart publication? | `README.md -> What to read first` then `AGENTS.md -> Authority baseline` | `references/authority-adr.md -> Ownership Map` | `handoff-brief` owns restart publication; restart surfaces are derived and publish only from the verified final snapshot. | Yes | PASS |
| What is the greenfield skill chain? | `architecture.md -> Default routes` | `references/one-shot-generation-contract.md -> Greenfield contract` | The architecture summary and the one-shot contract agree on the default greenfield sequence and proof gates. | Yes | PASS |
| Where does the generated-repo truth hierarchy live? | `AGENTS.md -> Canonical generated-repo truth hierarchy` | none | The generated repo truth owners are named directly in `AGENTS.md`. | Yes | PASS |
| Where are package-versus-output boundaries defined? | `README.md -> What Scafforge ships` then `AGENTS.md -> Repo identity` | none | The package repo, generated output, and adjacent systems are explicitly separated. | Yes | PASS |

## Residual gaps

- `active-plans/WORK-JOURNAL.md` and `active-plans/codexinstructions.md` remain inventoried but intentionally non-canonical; this sweep records their classification rather than promoting them into the root routing layer.
