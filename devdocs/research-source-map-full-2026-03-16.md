# Scafforge repository source inventory

This inventory groups the most relevant repository sources for workflow design, ticketing, agent prompts, and repair behavior. Paths are repo-relative so the note remains portable across machines.

## 1. Workflow orchestration and stage gates

### Direct sources

| Path | Why it matters |
| --- | --- |
| `skills/repo-process-doctor/references/safe-stage-contracts.md` | Formal stage model with proof-before-transition rules. |
| `skills/repo-scaffold-factory/references/workflow-guide.md` | Canonical generated-repo workflow sequence. |
| `skills/repo-process-doctor/references/process-smells.md` | Failure patterns that commonly break weaker-model workflows. |
| `AGENTS.md` | Package spine, default skill chain, and boundary rules. |
| `skills/repo-scaffold-factory/assets/project-template/.opencode/state/workflow-state.json` | Generated workflow-state schema, including process-version tracking. |

### Secondary but adaptable

| Path | Why it matters |
| --- | --- |
| `skills/repo-process-doctor/references/repair-playbook.md` | Retrofit and migration sequencing guidance. |
| `devdocs/research-workflows.md` | Comparative design rationale across internal references and public sources. |

## 2. Artifact and state contracts

### Direct sources

| Path | Why it matters |
| --- | --- |
| `skills/agent-prompt-engineering/references/prompt-contracts.md` | Shared artifact, proof, and routing rules used across role prompts. |
| `skills/repo-process-doctor/references/safe-stage-contracts.md` | Artifact lifecycle rules and stage-gate expectations. |
| `skills/repo-scaffold-factory/assets/project-template/.opencode/state/artifacts/registry.json` | Canonical artifact registry schema. |
| `skills/repo-scaffold-factory/assets/project-template/tickets/manifest.json` | Durable ticket queue with artifact metadata. |
| `skills/repo-scaffold-factory/assets/project-template/.opencode/state/workflow-state.json` | Transient state, approval state, and process verification flags. |

## 3. Ticket systems and queue management

### Direct sources

| Path | Why it matters |
| --- | --- |
| `skills/ticket-pack-builder/references/ticket-system.md` | Canonical v2 ticket schema and concurrency semantics. |
| `skills/repo-scaffold-factory/assets/project-template/tickets/manifest.json` | Machine-readable ticket source of truth. |
| `skills/repo-scaffold-factory/assets/project-template/tickets/BOARD.md` | Derived human board surface. |
| `skills/repo-scaffold-factory/assets/project-template/tickets/README.md` | Ticket field guide and lifecycle rules. |
| `skills/repo-scaffold-factory/assets/project-template/tickets/templates/TICKET.template.md` | Human-readable ticket document template. |
| `skills/ticket-pack-builder/SKILL.md` | Ticket-pack creation and refinement procedure. |

## 4. Prompt hardening and weak-model support

### Direct sources

| Path | Why it matters |
| --- | --- |
| `skills/agent-prompt-engineering/references/weak-model-profile.md` | Hardening rules for weaker models. |
| `skills/agent-prompt-engineering/references/prompt-contracts.md` | Role-specific prompt contract language. |
| `skills/agent-prompt-engineering/references/anti-patterns.md` | Common workflow and delegation failure modes. |
| `devdocs/research-minimax-m2-5.md` | Example model-specific hardening note. |
| `skills/agent-prompt-engineering/SKILL.md` | Procedure for model-specific prompt research and packaging. |

## 5. Agent roles and delegation boundaries

### Direct sources

| Path | Why it matters |
| --- | --- |
| `skills/opencode-team-bootstrap/references/agent-system.md` | Baseline agent taxonomy and delegation constraints. |
| `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md` | Generated team-leader contract. |
| `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-backlog-verifier.md` | Generated backlog-verifier contract. |
| `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-ticket-creator.md` | Generated migration follow-up ticket-creator contract. |
| `skills/opencode-team-bootstrap/SKILL.md` | Project-specific agent-team customization procedure. |

## 6. Tool, plugin, and host-abstraction packaging

### Direct sources

| Path | Why it matters |
| --- | --- |
| `adapters/manifest.json` | Machine-readable split between host responsibilities and core scaffold behavior. |
| `adapters/README.md` | Human explanation of host adapter boundaries. |
| `skills/opencode-team-bootstrap/references/tools-plugins-mcp.md` | Commands vs tools vs plugins vs MCP taxonomy. |
| `skills/repo-scaffold-factory/assets/project-template/opencode.jsonc` | Generated host configuration with safe defaults. |
| `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/` | Expected tool surfaces in generated repos. |
| `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/` | Expected enforcement layer for generated repos. |
| `skills/repo-scaffold-factory/assets/project-template/.opencode/commands/` | Human entrypoints and restart commands. |

## 7. Generated repo layout and restart surfaces

### Direct sources

| Path | Why it matters |
| --- | --- |
| `skills/repo-scaffold-factory/references/layout-guide.md` | Canonical generated-repo path layout. |
| `README.md` | Truth hierarchy and package-level product contract. |
| `skills/handoff-brief/SKILL.md` | Restart-surface publication procedure. |
| `skills/repo-scaffold-factory/assets/project-template/.opencode/meta/bootstrap-provenance.json` | Bootstrap and repair provenance. |
| `skills/repo-scaffold-factory/assets/project-template/.opencode/state/` | State structure for workflow and artifacts. |

## 8. Process validation and repair

### Direct sources

| Path | Why it matters |
| --- | --- |
| `skills/repo-process-doctor/SKILL.md` | Audit / propose-repair / apply-repair procedure. |
| `skills/repo-process-doctor/scripts/audit_repo_process.py` | Automated process audit checks. |
| `skills/repo-process-doctor/references/repair-playbook.md` | Managed-surface replacement and repair rules. |
| `scripts/validate_scafforge_contract.py` | Package-level contract validator. |
| `scripts/smoke_test_scafforge.py` | Package smoke test. |

## 9. Review and PR-to-ticket bridging

### Direct sources

| Path | Why it matters |
| --- | --- |
| `skills/pr-review-ticket-bridge/SKILL.md` | Host-side PR comment triage and ticket-proposal procedure. |
| `skills/pr-review-ticket-bridge/references/review-contract.md` | Ticket-proposal contract for accepted review findings. |
| `skills/skill-flow-manifest.json` | Machine-readable skill ownership and extension metadata. |

## Bottom line

The core pattern across these sources is consistent:

- one visible orchestrator
- explicit workflow state
- artifact proof before transitions
- canonical ticket and provenance surfaces
- conservative repair rules
- optional extensions kept outside the default scaffold chain

That combination is what makes Scafforge useful as a deterministic scaffold package rather than a loose collection of prompts.
