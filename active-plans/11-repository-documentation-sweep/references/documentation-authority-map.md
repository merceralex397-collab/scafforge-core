# Documentation Authority Map

This is the current source-of-truth map for Scafforge package documentation. Start here, then take one hop to the canonical surface for the truth domain you need.

## Root package docs

| Surface | Class | Owns | Use when |
| --- | --- | --- | --- |
| `README.md` | canonical root routing | What Scafforge is, what it is not, and the default lifecycle summary | You need fast orientation |
| `USERGUIDE.md` | canonical root routing | Human/operator routing, generated-repo usage habits, and lightweight context acquisition | You need the right workflow path |
| `architecture.md` | canonical root routing | Package structure, skill grouping, and adjacent-system boundaries | You need the system model |
| `AGENTS.md` | canonical root operating rules | Package-vs-output boundary discipline, authority baseline, standing doc-update rule, and generated-repo truth hierarchy | You are changing package behavior or need repo rules |

## Durable contract references

| Surface | Class | Owns |
| --- | --- | --- |
| `references/authority-adr.md` | canonical reference | Single-owner authority map |
| `references/invariant-catalog.md` | canonical reference | Invariant checklist for authority, mutation, restart, proof, and doc alignment |
| `references/competence-contract.md` | canonical reference | Package competence bar and one-legal-next-move contract |
| `references/one-shot-generation-contract.md` | canonical reference | One-shot greenfield lifecycle and publication gate |
| `references/stack-adapter-contract.md` | canonical reference | Stack detection, bootstrap, execution proof, and release-proof contract |

## Planning-layer docs

| Surface | Class | Owns | Sweep decision |
| --- | --- | --- | --- |
| `active-plans/README.md` | canonical portfolio index | Plan ordering, portfolio shape, and plan-document expectations | Updated as a reminder, not a second policy source |
| `active-plans/FULL-REPORT.md` | derived program summary | Cross-plan rationale and current program summary | Updated when plan sequencing or major program framing changes |
| `active-plans/docscleanup.md` | canonical planning-format policy | Placement and naming rules for planning docs | Keeps plan formatting aligned to the standing rule from `AGENTS.md` |
| `active-plans/WORK-JOURNAL.md` | historical provenance | Dated planning decisions and corrections | Inventoried by this sweep, intentionally out of the root routing rewrite |
| `active-plans/codexinstructions.md` | supporting reference | Execution guide for implementing the numbered plans | Inventoried by this sweep, intentionally not promoted to contract authority |

## Generated-template docs

| Surface | Class | Owns |
| --- | --- | --- |
| `skills/repo-scaffold-factory/assets/project-template/README.md` | canonical template root routing | Generated-repo startup path and top-level layout |
| `skills/repo-scaffold-factory/assets/project-template/AGENTS.md` | canonical template operating rules | Generated-repo truth hierarchy, read order, and operating rules |
| `skills/repo-scaffold-factory/assets/project-template/docs/process/*.md` | canonical template process refs | Generated workflow, tooling, agent catalog, and model matrix |
| `skills/repo-scaffold-factory/assets/project-template/docs/spec/CANONICAL-BRIEF.md` | canonical template spec owner | Durable project facts and required outputs in generated repos |
| `skills/repo-scaffold-factory/assets/project-template/.opencode/skills/*` | generated local guidance | Repo-local operating guidance derived from package truth |

## Fast context path

1. Read `README.md`.
2. Open the relevant root doc from the table above.
3. Take one hop to the canonical reference only if the root doc points you there.

## Standing rule

If a PR changes package or generated-template contract truth, update:

1. the affected root routing doc,
2. the canonical reference for that truth domain,
3. the touched generated-template doc or local-skill guidance, and
4. the validator expectation that keeps those surfaces aligned.
