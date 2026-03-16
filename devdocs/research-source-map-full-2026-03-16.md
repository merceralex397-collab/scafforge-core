Excellent! Now I have comprehensive knowledge. Let me compile the complete categorized source inventory:

---

# **Scafforge Repository Source Inventory**

Based on `/home/a/Scafforge/devdocs/research-workflows.md` as the heuristic, here's a categorized breakdown of relevant, directly applicable, and secondarily adaptable sources:

## **CATEGORY 1: WORKFLOW ORCHESTRATION & STAGE GATES**

### Direct Sources

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/skills/repo-process-doctor/references/safe-stage-contracts.md` | Formal stage model covering planning→review→implementation→review→QA→closeout with proof-before-transition rules | **Core**: Defines deterministic stage gates with artifact proof requirements; essential for weak-model reliability |
| `/home/a/Scafforge/skills/repo-scaffold-factory/references/workflow-guide.md` | Sequential workflow: spec intake → bootstrap → planning → review → implementation → review → QA → handoff | **Direct**: Canonical ticketed workflow sequence; no optional skipping |
| `/home/a/Scafforge/skills/repo-process-doctor/references/process-smells.md` | 14 failure patterns: stage-like statuses, contradictory semantics, raw-file control, missing workflow-state layer, overloaded tools, path drift, vocabulary drift, desync, handoff overwrites, unsafe read-only, over-scoped commands, process blindness, missing post-migration verification | **Direct**: Anti-patterns that break weaker models; guides what NOT to do |
| `/home/a/Scafforge/AGENTS.md` (lines 70–130) | Package spine defining the full skill chain sequence and two workflow modes (greenfield vs. retrofit) | **Direct**: Canonical orchestration contract for the entire scaffold lifecycle |
| `.opencode/state/workflow-state.json` template (`/home/a/Scafforge/skills/repo-scaffold-factory/assets/project-template/.opencode/state/workflow-state.json`) | State schema: `active_ticket`, `stage`, `status`, `approved_plan`, `process_version`, `pending_process_verification`, `parallel_mode` | **Core**: Generated repos use this for transient approval and process version tracking |

### Secondary but Adaptable

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/skills/repo-process-doctor/references/repair-playbook.md` | Migration order for older workflows (10-step upgrade path with safe-repair boundary) | **Adaptable**: Pattern for retrofitting workflows into older repos without breaking project intent |
| `/home/a/Scafforge/devdocs/research-workflows.md` | Comparative analysis of Scafforge vs. GPS vs. GPTTalker on lane ownership, parallelism, hierarchy, verification, ticket creation | **Secondary**: Justifies decisions but not prescriptive code |

---

## **CATEGORY 2: ARTIFACT & STATE CONTRACTS**

### Direct Sources

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/skills/agent-prompt-engineering/references/prompt-contracts.md` (§ team-leader through verifier) | Shared rules: proof before stage changes, artifact path canonicalization, output sections for consistency, tool-backed state instead of prose | **Core**: Explicit contract language that weaker models follow; referenced throughout generated output |
| `/home/a/Scafforge/skills/repo-process-doctor/references/safe-stage-contracts.md` (§ Planning-Closeout) | Artifact write-before-register pattern; planning artifact required before review; implementation artifacts record what changed + validation run; review/QA stay read-only | **Core**: Artifact lifecycle rules that prevent hallucination and enable proof-based gates |
| `.opencode/state/artifacts/registry.json` template | Schema: `version`, `artifacts[]` (minimal but extensible) | **Direct**: Canonical artifact metadata store; foundation for proof tracking |
| `tickets/manifest.json` template | Ticket fields including `artifacts: []` with stage-specific metadata | **Direct**: Artifact registration at the ticket level; gates stage transitions |
| `.opencode/state/workflow-state.json` template | Tracks `approved_plan` (transient approval state), `pending_process_verification` (process change flag) | **Core**: Separates durable state from transient stage signals |

### Secondary but Adaptable

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/skills/handoff-brief/SKILL.md` | Gathering current state and writing START-HERE.md with actual project state (not templates) | **Adaptable**: Pattern for materializing artifacts as human handoff surfaces |

---

## **CATEGORY 3: TICKET SYSTEMS & QUEUE MANAGEMENT**

### Direct Sources

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/skills/ticket-pack-builder/references/ticket-system.md` | Required fields: `id`, `title`, `wave`, `lane`, `parallel_safe`, `overlap_risk`, `stage`, `status`, `depends_on`, `summary`, `acceptance`, `artifacts`, `decision_blockers`; coarse statuses (todo, ready, in_progress, blocked, review, qa, done); concurrency rules | **Core**: Canonical ticket schema; explicit parallelism semantics instead of implied |
| `tickets/manifest.json` template | Machine-readable queue state with version tracking, per-ticket artifact metadata, dependency edges | **Direct**: Single source of truth for ticket routing |
| `tickets/BOARD.md` template | Human-readable derived board (NOT authoritative for workflow; manifest is) | **Direct**: Contractual separation of machine and human surfaces |
| `tickets/README.md` template + `tickets/templates/TICKET.template.md` | Status semantics, field guide, per-ticket artifact expectations | **Direct**: Generated repos include these; weaker models reference them |
| `/home/a/Scafforge/skills/ticket-pack-builder/SKILL.md` | Wave-based backlog building, blocking decision conversion to tickets, acceptance criteria synthesis | **Direct**: How to populate tickets without guessing or fabricating detail |

### Secondary but Adaptable

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/skills/scaffold-kickoff/SKILL.md` (step 1-2) | Decision packet collection for blocking ambiguities (project name, slug, model choices, stack) | **Adaptable**: Batched decision protocol for weaker models |

---

## **CATEGORY 4: PROMPT HARDENING & WEAK-MODEL SUPPORT**

### Direct Sources

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/skills/agent-prompt-engineering/references/weak-model-profile.md` | 8 hardening rules: short outputs, exact sections, blocker returns, proof before transitions, named next specialist, forbid premature closeout, keep procedures in tools/skills, explicit narrow parallelism rules | **Core**: Single reference for generating weak-model-safe prompts |
| `/home/a/Scafforge/skills/agent-prompt-engineering/references/prompt-contracts.md` | Detailed contract language for each role (team leader, planner, reviewer, implementer, QA, verifier, ticket creator, utilities) with explicit non-ownership and tool-backed state | **Core**: Copypasteable role definitions that include weak-model constraints |
| `/home/a/Scafforge/skills/agent-prompt-engineering/references/anti-patterns.md` | 5 anti-patterns: status-over-evidence, raw-file control, impossible read-only, broad command scope, eager skill loading | **Core**: Common failure modes and safer patterns |
| `/home/a/Scafforge/devdocs/research-minimax-m2-5.md` | MiniMax M2.5 guidance: short explicit sections, exact output schema, context/tool history preservation, low-temperature review roles | **Direct**: Model-specific hardening applicable to other weaker models (Claude, Gemini, etc.) |
| `/home/a/Scafforge/skills/agent-prompt-engineering/SKILL.md` | Procedure for web-researching chosen model's best practices and writing findings to `model-notes/` | **Direct**: How to generate model-specific documentation during scaffolding |
| `/home/a/Scafforge/skills/agent-prompt-engineering/references/examples.md` | Reference examples of hardened role prompts (likely shows actual vs. anti-pattern comparisons) | **Direct**: Concrete templates for prompt structure |

### Secondary but Adaptable

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/skills/agent-prompt-engineering/references/model-notes/` (directory) | Generated model-specific documentation (MiniMax M2.5, future models) | **Adaptable**: Pattern for discovering and packaging model-specific constraints |

---

## **CATEGORY 5: AGENT ROLES & DELEGATION BOUNDARIES**

### Direct Sources

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/skills/opencode-team-bootstrap/references/agent-system.md` | Baseline: one visible team-leader + phase specialists (planner, reviewer, implementer, QA, handoff) + utility specialists (explore, inspect, summarize, ticket audit, GitHub research, web research); delegation defaults (leader+selected roles only delegate; implementers don't fan out; utilities don't recurse) | **Core**: Canonical agent taxonomy and delegation constraints |
| `/home/a/Scafforge/skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md` | Team leader prompt template with tool/skill permissions, explicit non-ownership, stage enforcement rules, parallelism bounds, process-verification routing | **Direct**: Generated artifact; shows role constraints in real form |
| `/home/a/Scafforge/skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-backlog-verifier.md` | Backlog verifier (post-migration verification specialist): read-only, artifact-write + register capable, re-checks completed work after process upgrades | **Direct**: Role definition for restart/migration verification |
| `/home/a/Scafforge/skills/repo-scaffold-factory/assets/project-template/.opencode/agents/` (full directory of template agents) | 13 agent templates: team-leader, planner, plan-review, implementer, reviewer-code, reviewer-security, tester-qa, docs-handoff, backlog-verifier, ticket-creator, plus 3 utilities | **Direct**: Baseline role set with permissions and prompt contracts |
| `/home/a/Scafforge/skills/opencode-team-bootstrap/SKILL.md` (§ Plan the agent team) | Procedure for customizing agents based on project type (baseline always present, plus domain specialists for UI/API/infrastructure) | **Direct**: How to extend baseline roles without breaking weaker-model bounds |

### Secondary but Adaptable

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/devdocs/research-opencode-ecosystem.md` (§ Ecosystem patterns) | Optional patterns: bounded background delegation, stronger shell guards, optional observability, narrow specialists; anti-patterns: always-on orchestration, broad write-capable agents, auto-skill imports | **Adaptable**: Guidelines for extending agent team safely |

---

## **CATEGORY 6: TOOL/PLUGIN/MCP PACKAGING & HOST ABSTRACTION**

### Direct Sources

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/adapters/manifest.json` | Host abstraction contract: core responsibilities (normalize input, render scaffold, maintain OpenCode output, validate integrity) vs. adapter responsibilities (install guidance, invoke commands, provide host-specific startup) | **Core**: Machine-readable split of core vs. host-specific logic |
| `/home/a/Scafforge/adapters/README.md` | Human explanation of adapter contract: core handles mechanical work; adapters provide installation and invocation guidance | **Direct**: Conceptual foundation for host-agnostic design |
| `/home/a/Scafforge/skills/opencode-team-bootstrap/references/tools-plugins-mcp.md` | Layer definitions: commands (human entrypoints), tools (structured repo operations agents call), plugins (enforcement/guardrails), MCP (external services); explicit rule against slash-commands as internal workflow | **Core**: Canonical packaging taxonomy |
| `opencode.jsonc` template (`/home/a/Scafforge/skills/repo-scaffold-factory/assets/project-template/opencode.jsonc`) | Tool allowlists, bash permission matrix, MCP server declarations (optional, disabled by default), instructions ordering, permission read/write/bash rules | **Direct**: Host config contract with safe defaults (MCP opt-in, bash highly restricted) |
| `.opencode/tools/` template directory | Expected tool contracts (artifact_write, artifact_register, ticket_lookup, ticket_update, skill_ping, context_snapshot, handoff_publish, task delegation) | **Direct**: Tools agents expect to exist in a conformant repo |
| `.opencode/plugins/` template directory | Expected plugins (stage gates, tool guards, session automation, audit hooks) | **Direct**: Enforcement layer contract |
| `.opencode/commands/` template directory | Human entrypoints (e.g., `/kickoff`, `/resume`) | **Direct**: User-facing interface contract |

### Secondary but Adaptable

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/devdocs/research-opencode-ecosystem.md` (§ Official OpenCode patterns) | Links to official OpenCode docs on agents, commands, skills, plugins, custom tools, MCP | **Adaptable**: Reference for extending tool/plugin ecosystem safely |

---

## **CATEGORY 7: GENERATED REPO LAYOUT & RESTART SURFACES**

### Direct Sources

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/skills/repo-scaffold-factory/references/layout-guide.md` | Core paths: `README.md`, `AGENTS.md`, `START-HERE.md`, `docs/process/`, `docs/spec/`, `tickets/`, `.opencode/`, `opencode.jsonc`; principles: one obvious handoff entrypoint, one canonical ticket index, visible leader with hidden specialists, clear tool/plugin/skill/MCP separation | **Core**: Canonical directory contract for all generated repos |
| `/home/a/Scafforge/README.md` (§ Truth hierarchy) | Truth hierarchy table: CANONICAL-BRIEF owns facts; manifest owns queue state; workflow-state owns transient approval/process; artifacts/ owns proof; bootstrap-provenance owns scaffold history; START-HERE owns restart surface | **Core**: Single source-of-truth map for any generated repo |
| `/home/a/Scafforge/skills/handoff-brief/SKILL.md` | Procedure for creating START-HERE.md with actual project state (summary, current state, reading order, current/next ticket, validation status, known risks, next action) | **Direct**: Restart surface contract with real-content requirement (not template placeholders) |
| `.opencode/meta/bootstrap-provenance.json` template | Provenance tracking: scaffold metadata, repair history, process version change entries | **Direct**: Audit trail for process migrations and repairs |
| `.opencode/state/` template structure | Subdirectories: `workflow-state.json` (transient state), `artifacts/registry.json` (proof tracking), optional `invocation-log.jsonl` (observability) | **Direct**: State management contract |

### Secondary but Adaptable

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/skills/repo-scaffold-factory/assets/project-template/` (full asset directory) | 100+ template files ready for placeholder substitution and customization | **Adaptable**: Asset library for generating repos with different profiles/adapters |

---

## **CATEGORY 8: PROCESS VALIDATION & REPAIR PATTERNS**

### Direct Sources

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/skills/repo-process-doctor/SKILL.md` | 3-mode audit procedure: audit (report only), propose-repair (ask first), apply-repair (direct changes); references 21 automated audit checks; safe vs. intent-changing repair boundary | **Core**: Diagnostic and repair pattern for process drift detection |
| `/home/a/Scafforge/skills/repo-process-doctor/scripts/audit_repo_process.py` | Python script running 21 workflow-smell checks; outputs markdown + JSON reports without modifying files | **Direct**: Validation tool; generates both human and machine-readable audit reports |
| `/home/a/Scafforge/skills/repo-process-doctor/references/repair-playbook.md` | Target architecture, managed-surface replacement contract (10-step migration order), safe-repair boundary (safe: regen docs, align contracts, remove raw-file control, normalize semantics; escalate: scope changes, unresolved decisions, custom patterns) | **Core**: Migration guidance for older workflows |
| `/home/a/Scafforge/scripts/validate_scafforge_contract.py` | Package-level validation script (checks template integrity, manifest consistency, prompt structure) | **Direct**: Core validation for scaffold package itself |
| `/home/a/Scafforge/scripts/smoke_test_scafforge.py` | Smoke testing for the scaffold package | **Direct**: Package health check |

### Secondary but Adaptable

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py` | Python script for Phase A: copy 100+ template files, substitute placeholders, generate metadata | **Adaptable**: Pattern for deterministic mechanical scaffolding (agent does creative Phase B) |
| `/home/a/Scafforge/skills/opencode-team-bootstrap/scripts/bootstrap_opencode_team.py` | Agent-assistance script for team design (likely analysis helper, not fully autonomous) | **Adaptable**: Scaffolding-phase helper pattern |

---

## **CATEGORY 9: RESEARCH & DISCOVERY PATTERNS**

### Direct Sources

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/devdocs/research-workflows.md` | Comparative analysis of workflow patterns across Scafforge, GPS, GPTTalker, academic references (MetaGPT, Microsoft, AWS, LLM multi-agent survey); findings on lane ownership, parallelism, hierarchy, verification, ticket creation | **Core**: Strategic heuristic for design decisions |
| `/home/a/Scafforge/devdocs/research-opencode-ecosystem.md` | OpenCode ecosystem analysis: agent/command/skill/plugin/MCP patterns; what to adopt (bounded delegation, safety guards, optional observability) vs. avoid (always-on orchestration, broad write-capable agents, auto-imports) | **Direct**: Ecosystem integration guidance |
| `/home/a/Scafforge/devdocs/research-minimax-m2-5.md` | MiniMax M2.5-specific guidance extracted to support weaker model adaptation | **Direct**: Model-specific research discovery pattern |

### Secondary but Adaptable

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/skills/agent-prompt-engineering/SKILL.md` | Procedure for web-researching model-specific best practices and writing findings to `model-notes/` during scaffolding | **Adaptable**: Pattern for continuous discovery during scaffold execution |
| `/home/a/Scafforge/skills/spec-pack-normalizer/references/brief-schema.md` | 12-section canonical brief schema (summary, goals, non-goals, constraints, outputs, tooling, truth map, blocking decisions, open questions, backlog readiness, acceptance signals, assumptions) | **Adaptable**: Structured discovery format for project intake |

---

## **CATEGORY 10: REVIEW & PR-TO-TICKET BRIDGING**

### Direct Sources

| File Path | Contents | Why It Matters |
|-----------|----------|----------------|
| `/home/a/Scafforge/skills/pr-review-ticket-bridge/references/review-contract.md` | PR review ticket bridge contract: inputs (diff, commits, comments), outputs (separate valid/invalid findings, explain acceptance, generate tickets from valid findings only), ticket quality rules (one issue per ticket, actionable, acceptance criteria, PR link, no duplicates) | **Direct**: Guarded follow-up ticket creation pattern; prevents ad hoc ticket inflation |
| `/home/a/Scafforge/skills/pr-review-ticket-bridge/SKILL.md` | Optional extension skill for host-side PR review and comment validation with guarded ticket generation | **Direct**: Extension beyond core scaffold for mature projects |

[Output truncated. Use view_range=[201, ...] to continue reading.]
