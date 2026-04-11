from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Callable

from shared_verifier_types import Finding


@dataclass(frozen=True)
class ContractSurfaceAuditContext:
    read_text: Callable[[Path], str]
    read_json: Callable[[Path], Any]
    normalize_path: Callable[[Path, Path], str]
    normalized_path: Callable[[Path, Path], str]
    add_finding: Callable[[list[Finding], Finding], None]
    matching_lines: Callable[[str, tuple[str, ...]], list[str]]
    load_manifest_statuses: Callable[[dict[str, Any]], list[str]]
    manifest_queue_keys: Callable[[dict[str, Any]], list[str]]
    parse_status_semantics: Callable[[str], dict[str, str]]
    ticket_markdown_status: Callable[[Path], str | None]
    extract_section_lines: Callable[[str, str], list[str]]
    read_only_shell_agent: Callable[[Path], bool]
    has_eager_skill_loading: Callable[[str], bool]
    iter_contract_paths: Callable[[Path], list[Path]]
    frontmatter_value: Callable[[str, str], str | None]
    stage_like_statuses: tuple[str, ...]
    mutating_shell_tokens: tuple[str, ...]
    write_language: tuple[str, ...]
    artifact_register_persist_patterns: tuple[str, ...]
    artifact_path_drift_patterns: tuple[str, ...]
    deprecated_workflow_terms: tuple[str, ...]
    placeholder_skill_patterns: tuple[str, ...]
    deprecated_model_patterns: tuple[str, ...]


def tool_uses_plain_object_args(text: str) -> bool:
    return bool(re.search(r"\btype:\s*\"[A-Za-z]+\"", text) or re.search(r"\brequired:\s*(true|false)\b", text))


def tool_uses_zod_args(text: str) -> bool:
    return "tool.schema." in text or bool(re.search(r"args:\s*{\s*}", text))


def audit_status_model(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    manifest = ctx.read_json(manifest_path)
    if not isinstance(manifest, dict):
        return

    statuses = sorted({status for status in ctx.load_manifest_statuses(manifest) if status})
    queue_keys = ctx.manifest_queue_keys(manifest)
    stage_like = sorted(set(statuses) & set(ctx.stage_like_statuses))
    if stage_like:
        ctx.add_finding(
            findings,
            Finding(
                code="status-stage-collision",
                severity="error",
                problem="Ticket status encodes transient workflow stage instead of coarse queue state.",
                root_cause="The backlog uses statuses like planned or approved even though transient approval should live in workflow state or explicit artifacts.",
                files=[ctx.normalize_path(manifest_path, root)],
                safer_pattern="Use coarse queue statuses only and move plan approval into workflow state plus registered stage artifacts.",
                evidence=[
                    f"Manifest statuses: {', '.join(statuses) if statuses else '(none)'}",
                    f"Queue keys: {', '.join(queue_keys) if queue_keys else '(none)'}",
                ],
                provenance="script",
            ),
        )

    if queue_keys and stage_like:
        ctx.add_finding(
            findings,
            Finding(
                code="dual-state-model",
                severity="error",
                problem="The manifest mixes queue buckets and stage-like per-ticket statuses.",
                root_cause="Two overlapping state machines encourage weaker models to infer next steps from labels instead of from verified stage proofs.",
                files=[ctx.normalize_path(manifest_path, root)],
                safer_pattern="Keep the manifest as the queue source of truth and store transient approval in workflow state.",
                evidence=[
                    f"Queue buckets present: {', '.join(queue_keys)}",
                    f"Stage-like statuses present: {', '.join(stage_like)}",
                ],
                provenance="script",
            ),
        )


def audit_status_semantics_docs(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    files = [root / "docs" / "process" / "ticketing.md", root / "tickets" / "README.md"]
    semantics = {path: ctx.parse_status_semantics(ctx.read_text(path)) for path in files if path.exists()}
    if len(semantics) < 2:
        return

    shared_keys = set.intersection(*(set(values.keys()) for values in semantics.values()))
    mismatches: list[str] = []
    for key in sorted(shared_keys):
        values = {path: mapping[key] for path, mapping in semantics.items()}
        if len(set(values.values())) > 1:
            mismatch = "; ".join(f"{ctx.normalize_path(path, root)} -> {value}" for path, value in values.items())
            mismatches.append(f"{key}: {mismatch}")

    if not mismatches:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="contradictory-status-semantics",
            severity="error",
            problem="Status terms mean different things in different ticket docs.",
            root_cause="Weaker models will follow whichever status definition they most recently read, which creates routing instability.",
            files=[ctx.normalize_path(path, root) for path in semantics],
            safer_pattern="Define each status once, keep it coarse, and align all docs to the same wording.",
            evidence=mismatches,
            provenance="script",
        ),
    )


def audit_planned_tickets_without_artifacts(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    ticket_dir = root / "tickets"
    if not ticket_dir.exists():
        return

    has_workflow_tools = all(
        (root / relative).exists()
        for relative in (
            ".opencode/tools/artifact_write.ts",
            ".opencode/tools/ticket_lookup.ts",
            ".opencode/tools/ticket_update.ts",
            ".opencode/tools/artifact_register.ts",
            ".opencode/state/workflow-state.json",
        )
    )
    thin_planned: list[str] = []
    for path in ticket_dir.glob("*.md"):
        if path.name in {"README.md", "BOARD.md", "TEMPLATE.md"}:
            continue
        status = ctx.ticket_markdown_status(path)
        if status not in {"planned", "approved"}:
            continue
        brief_lines = ctx.extract_section_lines(ctx.read_text(path), "Implementation Brief")
        if len(brief_lines) <= 4:
            thin_planned.append(ctx.normalize_path(path, root))

    if not (thin_planned and not has_workflow_tools):
        return

    ctx.add_finding(
        findings,
        Finding(
            code="planner-status-without-proof",
            severity="error",
            problem="Tickets are marked as planned or approved without a reliable artifact layer proving planner output exists.",
            root_cause="The repo relies on raw ticket text and stage-like statuses rather than explicit planning artifacts and workflow-state gates.",
            files=thin_planned[:10],
            safer_pattern="Keep tickets in coarse queue states and require a planning artifact plus workflow approval state before plan review or implementation.",
            evidence=[
                f"Thin planned/approved tickets: {len(thin_planned)}",
                "Missing workflow tool layer: .opencode/tools/artifact_write.ts, .opencode/tools/ticket_lookup.ts, .opencode/tools/ticket_update.ts, .opencode/tools/artifact_register.ts, or .opencode/state/workflow-state.json",
            ],
            provenance="script",
        ),
    )


def audit_missing_tool_layer(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    required = [
        ".opencode/tools/artifact_write.ts",
        ".opencode/tools/ticket_lookup.ts",
        ".opencode/tools/ticket_update.ts",
        ".opencode/tools/artifact_register.ts",
        ".opencode/plugins/stage-gate-enforcer.ts",
        ".opencode/plugins/ticket-sync.ts",
        ".opencode/plugins/tool-guard.ts",
        ".opencode/state/workflow-state.json",
    ]
    missing = [path for path in required if not (root / path).exists()]
    if not missing:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="missing-workflow-tool-layer",
            severity="error",
            problem="The repo is missing the tool and plugin layer needed for explicit workflow-state control.",
            root_cause="Without ticket tools, workflow state, and guard plugins, the agent falls back to fragile raw-file stage management.",
            files=missing,
            safer_pattern="Add artifact-write/register tools, ticket tools, workflow-state, and stage/ticket guard plugins so stage control is explicit and tool-backed.",
            evidence=missing,
            provenance="script",
        ),
    )


def audit_overloaded_artifact_register(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    path = root / ".opencode" / "tools" / "artifact_register.ts"
    if not path.exists():
        return
    text = ctx.read_text(path)
    evidence: list[str] = []
    if re.search(r"\bcontent\s*:", text):
        evidence.append("artifact_register still exposes a content argument.")
    if "writeText(" in text or "writeFile(" in text:
        evidence.append("artifact_register still writes artifact body text instead of registering metadata only.")
    if not evidence:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="overloaded-artifact-register",
            severity="error",
            problem="artifact_register is still overloaded to write artifact content as well as register metadata.",
            root_cause="Weak models can pass a summary string through the register tool and overwrite the canonical artifact body.",
            files=[ctx.normalize_path(path, root)],
            safer_pattern="Split artifact persistence into `artifact_write` for the full body and register-only `artifact_register` for metadata.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_artifact_persistence_prompt_contract(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    offenders: list[str] = []
    evidence: list[str] = []
    for path in ctx.iter_contract_paths(root):
        text = ctx.read_text(path)
        hits = ctx.matching_lines(text, ctx.artifact_register_persist_patterns)
        if not hits:
            continue
        offenders.append(ctx.normalize_path(path, root))
        evidence.extend(f"{ctx.normalize_path(path, root)} -> {hit}" for hit in hits)
    if not offenders:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="artifact-persistence-through-register",
            severity="error",
            problem="Prompts or workflow docs still describe artifact_register as the tool that persists full artifact text.",
            root_cause="The prompt contract collapses writing and registration into one step, so weaker models can overwrite canonical artifacts with summaries.",
            files=offenders,
            safer_pattern="Tell stage agents to write full content with `artifact_write` and then register metadata with `artifact_register`.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_failure_recovery_contract(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    ticket_execution = root / ".opencode" / "skills" / "ticket-execution" / "SKILL.md"
    team_leader = next((path for path in (root / ".opencode" / "agents").glob("*team-leader*.md")), None)
    files: list[str] = []
    evidence: list[str] = []

    if not ticket_execution.exists():
        files.append(ctx.normalize_path(ticket_execution, root))
        evidence.append("Missing repo-local ticket execution skill, so fail-state routing is undocumented.")
    else:
        ticket_execution_text = ctx.read_text(ticket_execution)
        if "Failure recovery paths:" not in ticket_execution_text:
            files.append(ctx.normalize_path(ticket_execution, root))
            evidence.append(
                f"{ctx.normalize_path(ticket_execution, root)} does not include an explicit Failure recovery paths section."
            )

    if team_leader is None:
        files.append(".opencode/agents/*team-leader*.md")
        evidence.append("Missing team leader prompt, so no coordinator recovery-action routing can be verified.")
    else:
        team_leader_text = ctx.read_text(team_leader)
        if "ticket_lookup.transition_guidance.recovery_action" not in team_leader_text:
            files.append(ctx.normalize_path(team_leader, root))
            evidence.append(
                f"{ctx.normalize_path(team_leader, root)} does not tell the coordinator to follow recovery_action when present."
            )

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW024",
            severity="error",
            problem="Fail-state routing is still under-specified in generated prompts or workflow skills.",
            root_cause="Even if the tool contract knows how to route a FAIL verdict, weaker models still stall or advance incorrectly when the repo-local workflow explainer and coordinator prompt omit the recovery path.",
            files=list(dict.fromkeys(files)),
            safer_pattern="Document review, QA, smoke-test, and bootstrap failure recovery paths in ticket-execution, and instruct the team leader to follow transition_guidance.recovery_action whenever it is present.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_artifact_path_contract_drift(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    offenders: list[str] = []
    evidence: list[str] = []
    for path in ctx.iter_contract_paths(root):
        text = ctx.read_text(path)
        hits = ctx.matching_lines(text, ctx.artifact_path_drift_patterns)
        if not hits:
            continue
        offenders.append(ctx.normalize_path(path, root))
        evidence.extend(f"{ctx.normalize_path(path, root)} -> {hit}" for hit in hits)
    if not offenders:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="artifact-path-contract-drift",
            severity="error",
            problem="Artifact guidance still points at deprecated path conventions.",
            root_cause="Docs and prompts disagree about the canonical artifact location, which makes stage proof unreliable.",
            files=offenders,
            safer_pattern="Use the stage-specific artifact directories plus `.opencode/state/artifacts/registry.json` consistently across prompts, docs, tools, and skills.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_workflow_vocabulary_drift(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    offenders: list[str] = []
    evidence: list[str] = []
    for path in ctx.iter_contract_paths(root):
        text = ctx.read_text(path)
        allowed_terms = {"code_review", "security_review"} if ctx.normalized_path(path, root) == ".opencode/lib/workflow.ts" else set()
        hits = [term for term in ctx.deprecated_workflow_terms if term in text and term not in allowed_terms]
        if not hits:
            continue
        offenders.append(ctx.normalize_path(path, root))
        evidence.append(f"{ctx.normalize_path(path, root)} -> {', '.join(hits)}")
    if not offenders:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="workflow-vocabulary-drift",
            severity="error",
            problem="Workflow tools or docs still use deprecated status or stage vocabulary.",
            root_cause="Stage gates, workflow defaults, and artifact proofs no longer agree on the state machine terms that control execution.",
            files=offenders,
            safer_pattern="Keep workflow defaults and stage checks aligned on `todo|ready|in_progress|blocked|review|qa|done` plus `planning|implementation|review|qa` stage proof.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_artifact_brief_missing_tuple(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    team_leader = next((path for path in (root / ".opencode" / "agents").glob("*team-leader*.md")), None)
    if not team_leader:
        return
    text = ctx.read_text(team_leader)
    if "Canonical artifact path when the stage must persist text" not in text:
        return
    if "Artifact stage when the stage must persist text" in text and "Artifact kind when the stage must persist text" in text:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="artifact-brief-missing-tuple",
            severity="warning",
            problem="The team leader delegation brief does not include the artifact stage/kind tuple required by stricter artifact tools.",
            root_cause="A path alone is not enough to derive the canonical `(stage, kind)` pair for every artifact, so weaker models can guess the wrong tuple and fail path validation.",
            files=[ctx.normalize_path(team_leader, root)],
            safer_pattern="Include artifact stage, artifact kind, and canonical artifact path whenever a delegated stage must persist text.",
            evidence=[ctx.normalize_path(team_leader, root)],
            provenance="script",
        ),
    )


def audit_workflow_state_desync(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    path = root / ".opencode" / "tools" / "ticket_update.ts"
    if not path.exists():
        return
    text = ctx.read_text(path)
    if (
        "workflow.stage = ticket.stage" not in text
        and "workflow.status = ticket.status" not in text
        and ("workflow.approved_plan = args.approved_plan" not in text or "activeTicket.id === ticket.id" in text)
    ):
        return
    ctx.add_finding(
        findings,
        Finding(
            code="workflow-state-desync",
            severity="error",
            problem="ticket_update can copy a background ticket's stage or status into workflow-state without activating that ticket.",
            root_cause="The tool updates the manifest ticket record and then mirrors the edited ticket into workflow-state even when the active ticket remains different.",
            files=[ctx.normalize_path(path, root)],
            safer_pattern="Recompute the current active ticket after manifest changes and sync workflow-state from that active ticket only.",
            evidence=[ctx.normalize_path(path, root)],
            provenance="script",
        ),
    )


def audit_handoff_overwrites_start_here(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    path = root / ".opencode" / "tools" / "handoff_publish.ts"
    if not path.exists():
        return
    text = ctx.read_text(path)
    if "await writeText(startHere, content)" not in text or "mergeStartHere" in text:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="handoff-overwrites-start-here",
            severity="error",
            problem="handoff_publish overwrites START-HERE.md with a generic generated handoff.",
            root_cause="The closeout tool does not preserve curated repo-specific content in START-HERE, so later sessions lose the canonical read order and live risk/validation notes.",
            files=[ctx.normalize_path(path, root)],
            safer_pattern="Write the generated handoff to `.opencode/state/latest-handoff.md` and only merge the managed block into START-HERE when explicit markers are present.",
            evidence=[ctx.normalize_path(path, root)],
            provenance="script",
        ),
    )


def audit_invalid_tool_schemas(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    tools_dir = root / ".opencode" / "tools"
    if not tools_dir.exists():
        return
    offenders: list[str] = []
    evidence: list[str] = []
    for path in tools_dir.glob("*.ts"):
        text = ctx.read_text(path)
        if "export default tool(" not in text:
            continue
        normalized = ctx.normalize_path(path, root)
        if tool_uses_plain_object_args(text):
            offenders.append(normalized)
            evidence.append(f"{normalized} uses plain JSON-style tool args (`type`/`required`) instead of `tool.schema`.")
            continue
        if not tool_uses_zod_args(text):
            offenders.append(normalized)
            evidence.append(f"{normalized} does not expose a detectable `tool.schema` arg contract.")
    if not offenders:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="invalid-opencode-tool-schema",
            severity="error",
            problem="Custom OpenCode tools are not using the Zod-backed `tool.schema` contract expected by the plugin runtime.",
            root_cause="The repo mixes scaffold-era plain-object arg definitions with a plugin API that converts Zod schemas to JSON schema at load time.",
            files=offenders,
            safer_pattern="Define every custom tool arg with `tool.schema.*` and reject plain `{ type, description, required }` objects.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_missing_observability_layer(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    required = [
        ".opencode/tools/skill_ping.ts",
        ".opencode/plugins/invocation-tracker.ts",
        ".opencode/meta/bootstrap-provenance.json",
        ".opencode/state/.gitignore",
    ]
    missing = [path for path in required if not (root / path).exists()]
    if not missing:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="missing-observability-layer",
            severity="warning",
            problem="The repo cannot reliably explain how its OpenCode layer was generated or which local skills/tools are actually being used.",
            root_cause="Tracking surfaces for provenance and invocation logging are missing, so audits cannot distinguish never-used skills from invisible activity.",
            files=missing,
            safer_pattern="Add bootstrap provenance, invocation tracking, and a skill ping tool so usage is observable across sessions.",
            evidence=missing,
            provenance="script",
        ),
    )


def audit_process_change_tracking(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    provenance_path = root / ".opencode" / "meta" / "bootstrap-provenance.json"
    workflow = ctx.read_json(workflow_path)
    provenance = ctx.read_json(provenance_path)
    missing: list[str] = []
    evidence: list[str] = []
    affected_files: list[str] = []
    if not isinstance(workflow, dict):
        workflow_rel = ctx.normalize_path(workflow_path, root)
        missing.append(workflow_rel)
        affected_files.append(workflow_rel)
    else:
        workflow_rel = ctx.normalize_path(workflow_path, root)
        for key in ("process_version", "process_last_changed_at", "process_last_change_summary", "pending_process_verification"):
            if key not in workflow:
                evidence.append(f"{workflow_rel} is missing `{key}`.")
                if workflow_rel not in affected_files:
                    affected_files.append(workflow_rel)
    if not isinstance(provenance, dict):
        provenance_rel = ctx.normalize_path(provenance_path, root)
        missing.append(provenance_rel)
        affected_files.append(provenance_rel)
    else:
        provenance_rel = ctx.normalize_path(provenance_path, root)
        if not isinstance(provenance.get("workflow_contract"), dict):
            evidence.append(f"{provenance_rel} is missing `workflow_contract`.")
            if provenance_rel not in affected_files:
                affected_files.append(provenance_rel)
        if not isinstance(provenance.get("managed_surfaces"), dict):
            evidence.append(f"{provenance_rel} is missing `managed_surfaces`.")
            if provenance_rel not in affected_files:
                affected_files.append(provenance_rel)
        if "repair_history" not in provenance:
            evidence.append(f"{provenance_rel} is missing `repair_history`.")
            if provenance_rel not in affected_files:
                affected_files.append(provenance_rel)
    if not (missing or evidence):
        return
    ctx.add_finding(
        findings,
        Finding(
            code="missing-process-change-tracking",
            severity="warning",
            problem="The repo cannot reliably tell whether its operating process was replaced or materially upgraded.",
            root_cause="Workflow state and provenance do not expose a stable process version, managed-surface ownership, and pending post-migration verification state.",
            files=affected_files,
            safer_pattern="Record process version fields in workflow state and managed-surface plus repair history data in bootstrap provenance.",
            evidence=missing + evidence,
            provenance="script",
        ),
    )


def audit_missing_post_migration_verification(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    required_tool = ".opencode/tools/ticket_create.ts"
    required_agent_patterns = [".opencode/agents/*backlog-verifier*.md", ".opencode/agents/*ticket-creator*.md"]
    found_agents_dir = root / ".opencode" / "agents"
    actual_required: list[str] = []
    if found_agents_dir.exists():
        if not any("backlog-verifier" in path.name for path in found_agents_dir.glob("*.md")):
            actual_required.append(required_agent_patterns[0])
        if not any("ticket-creator" in path.name for path in found_agents_dir.glob("*.md")):
            actual_required.append(required_agent_patterns[1])
    else:
        actual_required.extend(required_agent_patterns)
    if not (root / ".opencode" / "tools" / "ticket_create.ts").exists():
        actual_required.append(required_tool)
    if not actual_required:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="missing-post-migration-verification-lane",
            severity="warning",
            problem="The repo has no explicit post-migration verification and guarded follow-up ticket path.",
            root_cause="A process replacement can change workflow expectations, but the repo lacks a verifier role or tightly scoped ticket creation tool for resulting backlog repairs.",
            files=actual_required,
            safer_pattern="Add a backlog verifier, a guarded ticket creator, and a ticket creation tool that requires verification proof.",
            evidence=actual_required,
            provenance="script",
        ),
    )


def audit_partial_workflow_layer_drift(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    has_core_layer = any((root / path).exists() for path in (".opencode/tools/ticket_lookup.ts", ".opencode/tools/ticket_update.ts", ".opencode/tools/artifact_register.ts"))
    if not has_core_layer:
        return
    optional_surfaces = [
        "opencode.jsonc",
        ".opencode/commands",
        ".opencode/tools/context_snapshot.ts",
        ".opencode/tools/handoff_publish.ts",
        ".opencode/plugins/session-compactor.ts",
    ]
    missing = [path for path in optional_surfaces if not (root / path).exists()]
    if not missing:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="partial-workflow-layer-drift",
            severity="warning",
            problem="The repo has a partial OpenCode workflow layer, but some non-core scaffold surfaces are missing.",
            root_cause="The repo was retrofitted or customized without keeping the restart, handoff, or human-entrypoint surfaces aligned with the tool-backed workflow.",
            files=missing,
            safer_pattern="Keep restart commands, context/handoff tools, and session automation aligned with the repo's current workflow layer.",
            evidence=missing,
            provenance="script",
        ),
    )


def audit_raw_file_state_ownership(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    team_leader = next((path for path in (root / ".opencode" / "agents").glob("*team-leader*.md")), None)
    if not team_leader:
        return
    text = ctx.read_text(team_leader)
    missing_ticket_tools = not (root / ".opencode" / "tools" / "ticket_update.ts").exists()
    if not (missing_ticket_tools and ("ticket state" in text.lower() or "manifest.json" in text or "board.md" in text)):
        return
    ctx.add_finding(
        findings,
        Finding(
            code="raw-file-team-leader-state",
            severity="error",
            problem="The team leader owns ticket state but has no ticket-state tool layer.",
            root_cause="The workflow expects raw file choreography across ticket files, the board, and the manifest instead of using structured tools.",
            files=[ctx.normalize_path(team_leader, root)],
            safer_pattern="Give the team leader ticket lookup/update tools and make the board a derived view.",
            evidence=["Team leader references ticket state or raw tracking surfaces.", "No .opencode/tools/ticket_update.ts present."],
            provenance="script",
        ),
    )


def audit_missing_artifact_gates(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    team_leader = next((path for path in (root / ".opencode" / "agents").glob("*team-leader*.md")), None)
    plan_review = next((path for path in (root / ".opencode" / "agents").glob("*plan-review*.md")), None)
    if not team_leader and not plan_review:
        return
    missing: list[str] = []
    for path in (team_leader, plan_review):
        if not path:
            continue
        text = ctx.read_text(path).lower()
        if "artifact" not in text and "approved_plan" not in text and "workflow-state" not in text:
            missing.append(ctx.normalize_path(path, root))
    if not missing:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="missing-artifact-gates",
            severity="error",
            problem="Stage prompts do not require canonical artifact or workflow-state proof before advancing.",
            root_cause="The workflow relies on status inference instead of explicit planning, review, or QA evidence.",
            files=missing,
            safer_pattern="Require artifact proof before plan review, implementation, review, QA, and closeout.",
            evidence=missing,
            provenance="script",
        ),
    )


def audit_read_only_shell_mutation(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    agents_dir = root / ".opencode" / "agents"
    if not agents_dir.exists():
        return
    bad_agents: list[str] = []
    for path in agents_dir.glob("*.md"):
        text = ctx.read_text(path)
        if not ctx.read_only_shell_agent(path):
            continue
        if any(token in text for token in ctx.mutating_shell_tokens):
            bad_agents.append(ctx.normalize_path(path, root))
    if not bad_agents:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="read-only-shell-mutation-loophole",
            severity="error",
            problem="Read-only shell agents still allow commands that can mutate repo-tracked files.",
            root_cause="The repo labels an agent as inspection-only while its shell allowlist still includes mutating commands.",
            files=bad_agents,
            safer_pattern="Keep read-only shell allowlists to inspection commands only and move mutation into write-capable roles.",
            evidence=bad_agents,
            provenance="script",
        ),
    )


def audit_read_only_write_language(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    agents_dir = root / ".opencode" / "agents"
    if not agents_dir.exists():
        return
    offenders: list[str] = []
    for path in agents_dir.glob("*.md"):
        text = ctx.read_text(path).lower()
        if "write: false" not in text or "edit: false" not in text:
            continue
        if any(phrase in text for phrase in ctx.write_language):
            offenders.append(ctx.normalize_path(path, root))
    if not offenders:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="read-only-write-language",
            severity="warning",
            problem="Read-only agent prompts still contain direct file-update language.",
            root_cause="Weak models may hallucinate successful writes or route around missing capabilities when prompts imply they should mutate files.",
            files=offenders,
            safer_pattern="Tell read-only agents to return blockers or artifacts, not repo file edits.",
            evidence=offenders,
            provenance="script",
        ),
    )


def audit_over_scoped_commands(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    commands_dir = root / ".opencode" / "commands"
    if not commands_dir.exists():
        return
    offenders: list[str] = []
    for path in commands_dir.glob("*.md"):
        text = ctx.read_text(path)
        if "## Success Output" in text and "## Follow-On Action" in text and re.search(r"## Follow-On Action\s+Invoke", text, re.IGNORECASE):
            offenders.append(ctx.normalize_path(path, root))
    if not offenders:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="over-scoped-human-command",
            severity="warning",
            problem="Human entrypoint commands also instruct autonomous continuation beyond the stated success output.",
            root_cause="The command contract is mixing summary/preflight responsibilities with automatic lifecycle continuation.",
            files=offenders,
            safer_pattern="Keep commands narrow and let the team leader stop at the command's intended handoff boundary.",
            evidence=offenders,
            provenance="script",
        ),
    )


def audit_eager_skill_loading(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    agents_dir = root / ".opencode" / "agents"
    if not agents_dir.exists():
        return
    offenders: list[str] = []
    for path in agents_dir.glob("*.md"):
        text = ctx.read_text(path)
        lowered = text.lower()
        if "mode: primary" not in lowered or "skill:" not in lowered:
            continue
        if ctx.has_eager_skill_loading(text):
            offenders.append(ctx.normalize_path(path, root))
    if not offenders:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="eager-skill-loading",
            severity="error",
            problem="A primary agent is told to load skills before it resolves workflow state.",
            root_cause="The prompt front-loads skill-tool setup, which can make weaker models issue malformed skill calls before they inspect the active ticket.",
            files=offenders,
            safer_pattern="Resolve state from ticket tools first and load one explicitly named skill only when it materially reduces ambiguity.",
            evidence=offenders,
            provenance="script",
        ),
    )


def audit_placeholder_local_skills(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    skills_dir = root / ".opencode" / "skills"
    if not skills_dir.exists():
        return
    offenders: list[str] = []
    evidence: list[str] = []
    for path in sorted(skills_dir.rglob("SKILL.md")):
        text = ctx.read_text(path)
        hits = ctx.matching_lines(text, ctx.placeholder_skill_patterns)
        if not hits:
            continue
        offenders.append(ctx.normalize_path(path, root))
        evidence.extend(f"{ctx.normalize_path(path, root)} -> {hit}" for hit in hits)
    blender_skill = skills_dir / "blender-mcp-workflow" / "SKILL.md"
    blender_text = ctx.read_text(blender_skill)
    blender_hits: list[str] = []
    if blender_text:
        lowered = blender_text.lower()
        if "blender_session_create" in lowered:
            blender_hits.append("mentions blender_session_create even though the repo workflow is stateless")
        if "blender_session_attach" in lowered:
            blender_hits.append("mentions blender_session_attach even though the repo workflow is stateless")
        if "blender_session_checkpoint" in lowered:
            blender_hits.append("mentions blender_session_checkpoint even though the repo workflow is stateless")
        if "blender_session_close" in lowered:
            blender_hits.append("mentions blender_session_close even though the repo workflow is stateless")
        if "active blender session" in lowered:
            blender_hits.append("tells agents to rely on an active Blender session instead of chained saved_blend paths")
        required_snippets = ("stateless", "input_blend", "output_blend", "persistence.saved_blend")
        for snippet in required_snippets:
            if snippet not in blender_text:
                blender_hits.append(f"missing required Blender persistence contract snippet: {snippet}")
    if blender_hits:
        offenders.append(ctx.normalize_path(blender_skill, root))
        evidence.extend(
            f"{ctx.normalize_path(blender_skill, root)} -> {hit}"
            for hit in blender_hits
        )
    if not offenders:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="SKILL001",
            severity="warning",
            problem="One or more repo-local skills still contain generic placeholder text or stale synthesized guidance instead of current project-specific procedure.",
            root_cause="project-skill-bootstrap or later managed-surface repair left repo-local skills in a placeholder or stale state, so agents lose concrete stack, validation, or asset-workflow guidance.",
            files=offenders,
            safer_pattern="Populate every required repo-local skill with concrete current rules and validation commands; generated `.opencode/skills/` files must not retain template filler or stale synthesized workflow guidance.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_model_profile_drift(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    provenance_path = root / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = ctx.read_json(provenance_path)
    runtime_models = provenance.get("runtime_models") if isinstance(provenance, dict) and isinstance(provenance.get("runtime_models"), dict) else {}
    provider = str(runtime_models.get("provider", "")).strip().lower() if isinstance(runtime_models, dict) else ""
    profile_path = root / ".opencode" / "skills" / "model-operating-profile" / "SKILL.md"
    model_matrix_path = root / "docs" / "process" / "model-matrix.md"
    canonical_brief_path = root / "docs" / "spec" / "CANONICAL-BRIEF.md"
    start_here_path = root / "START-HERE.md"
    agents_dir = root / ".opencode" / "agents"
    evidence: list[str] = []
    files: list[str] = []
    package_managed_drift = False
    if not profile_path.exists():
        files.append(ctx.normalize_path(profile_path, root))
        evidence.append(f"Missing repo-local model profile skill: {ctx.normalize_path(profile_path, root)}.")
        package_managed_drift = True
    else:
        profile_text = ctx.read_text(profile_path)
        if "__MODEL_PROVIDER__" in profile_text or "__MODEL_OPERATING_PROFILE_NAME__" in profile_text:
            files.append(ctx.normalize_path(profile_path, root))
            evidence.append(f"{ctx.normalize_path(profile_path, root)} still contains unresolved model-profile template placeholders.")
            package_managed_drift = True
    candidate_paths = [provenance_path, model_matrix_path, canonical_brief_path, start_here_path]
    if agents_dir.exists():
        candidate_paths.extend(sorted(agents_dir.glob("*.md")))
    deprecated_hits = False
    for path in candidate_paths:
        if not path.exists():
            continue
        text = ctx.read_text(path)
        hits = ctx.matching_lines(text, ctx.deprecated_model_patterns)
        if not hits:
            continue
        deprecated_hits = True
        package_managed_drift = True
        files.append(ctx.normalize_path(path, root))
        evidence.extend(f"{ctx.normalize_path(path, root)} -> {hit}" for hit in hits)
    if agents_dir.exists():
        for path in sorted(agents_dir.glob("*.md")):
            text = ctx.read_text(path)
            model_value = ctx.frontmatter_value(text, "model")
            if not model_value or "minimax" not in model_value.lower():
                continue
            temperature = ctx.frontmatter_value(text, "temperature")
            top_p = ctx.frontmatter_value(text, "top_p")
            top_k = ctx.frontmatter_value(text, "top_k")
            if temperature == "0.2" or top_p == "0.7" or top_k is None:
                package_managed_drift = True
                files.append(ctx.normalize_path(path, root))
                evidence.append(
                    f"{ctx.normalize_path(path, root)} retains older MiniMax sampling defaults "
                    f"(temperature={temperature or 'missing'}, top_p={top_p or 'missing'}, top_k={top_k or 'missing'})."
                )
    should_flag = deprecated_hits or bool(evidence) or ("minimax" in provider and not profile_path.exists())
    if not should_flag:
        return
    ctx.add_finding(
        findings,
        Finding(
            code="MODEL001",
            severity="error" if package_managed_drift else "warning",
            problem="Repo-local model operating surfaces are missing or still pinned to deprecated MiniMax defaults.",
            root_cause="Managed repair or retrofit preserved older model/profile surfaces instead of regenerating the repo-local model profile, agent prompts, and model matrix together. Deprecated package-managed defaults such as `MiniMax-M2.5` are drift, not protected user intent, unless newer explicit accepted-decision evidence says otherwise.",
            files=list(dict.fromkeys(files)),
            safer_pattern="Treat deprecated package-managed model defaults as safe repair: regenerate `.opencode/skills/model-operating-profile/SKILL.md`, align provenance/model-matrix/agent frontmatter on the current runtime model choices, and remove deprecated `MiniMax-M2.5` surfaces before implementation continues unless newer explicit accepted-decision evidence says to keep them.",
            evidence=evidence[:10],
            provenance="script",
        ),
    )


def _is_consumer_facing_repo(root: Path, ctx: ContractSurfaceAuditContext) -> bool:
    """Heuristically determine whether this is a consumer-facing repo that requires a finish contract."""
    provenance_path = root / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = ctx.read_json(provenance_path)
    if isinstance(provenance, dict):
        stack = str(provenance.get("stack_label", "")).lower()
        target = str(provenance.get("target_platform", "")).lower()
        if any(kw in stack or kw in target for kw in ("godot", "android", "ios", "mobile", "game", "unity", "unreal")):
            return True
    if (root / "project.godot").exists():
        return True
    brief_path = root / "docs" / "spec" / "CANONICAL-BRIEF.md"
    if brief_path.exists():
        brief_text = ctx.read_text(brief_path).lower()
        consumer_keywords = ("mobile app", "android app", "ios app", "game", "toddler", "consumer-facing", "store-ready", "playable", "packaged product")
        if any(kw in brief_text for kw in consumer_keywords):
            return True
    return False


def _brief_has_finish_contract(brief_text: str) -> bool:
    """Check whether the canonical brief contains a Product Finish Contract section."""
    return bool(re.search(r"##\s+13\.", brief_text) or "product finish contract" in brief_text.lower())


def _finish_contract_section(brief_text: str) -> str | None:
    match = re.search(r"(^##\s+13\.[^\n]*\n)(.*?)(?=^##\s+\d+\.|\Z)", brief_text, re.MULTILINE | re.DOTALL)
    if match:
        return match.group(2)
    if "product finish contract" not in brief_text.lower():
        return None
    return brief_text


def _missing_finish_contract_fields(brief_text: str) -> list[str]:
    section = _finish_contract_section(brief_text)
    if not section:
        return []
    required_fields = (
        "deliverable_kind",
        "placeholder_policy",
        "visual_finish_target",
        "audio_finish_target",
        "content_source_plan",
        "licensing_or_provenance_constraints",
        "finish_acceptance_signals",
    )
    lowered = section.lower()
    return [field for field in required_fields if field.lower() not in lowered]


def _finish_contract_allows_placeholders(brief_text: str) -> bool:
    """Return True when the finish contract explicitly records placeholder_ok policy."""
    placeholder_ok_patterns = (
        r"placeholder_policy[^:\n]*:.*placeholder_ok",
        r"placeholder\s+or\s+procedural\s+output\s+is\s+acceptable",
        r"procedural[- ]only\s+acceptable",
    )
    for pattern in placeholder_ok_patterns:
        if re.search(pattern, brief_text, re.IGNORECASE):
            return True
    return False


def _open_finish_lane_tickets(root: Path, ctx: ContractSurfaceAuditContext) -> list[str]:
    """Return manifest ticket IDs that are in finish-related lanes and still open."""
    manifest_path = root / "tickets" / "manifest.json"
    manifest = ctx.read_json(manifest_path)
    if not isinstance(manifest, dict):
        return []
    finish_lanes = frozenset({"finish", "finish-content", "finish-direction", "polish", "visual-content", "audio-content"})
    finish_keywords = ("finish", "polish", "visual content", "audio content", "asset production", "content production")
    open_finish: list[str] = []
    for ticket in manifest.get("tickets", []):
        if not isinstance(ticket, dict):
            continue
        resolution = str(ticket.get("resolution_state", "")).lower()
        if resolution in ("done", "superseded", "closed"):
            continue
        lane = str(ticket.get("lane", "")).lower()
        title = str(ticket.get("title", "")).lower()
        summary = str(ticket.get("summary", "")).lower()
        in_finish_lane = any(fl in lane for fl in finish_lanes)
        has_finish_keyword = any(kw in title or kw in summary for kw in finish_keywords)
        if in_finish_lane or has_finish_keyword:
            open_finish.append(str(ticket.get("id", "")))
    return open_finish


def _repo_claims_completion(root: Path, ctx: ContractSurfaceAuditContext) -> bool:
    """Return True when the repo's restart narrative or workflow state claims a finished/ready state."""
    start_here_path = root / "START-HERE.md"
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    if start_here_path.exists():
        text = ctx.read_text(start_here_path).lower()
        if any(phrase in text for phrase in ("ready for continued development", "product is finished", "release-ready", "all tickets done")):
            return True
    workflow = ctx.read_json(workflow_path)
    if isinstance(workflow, dict):
        active = workflow.get("active_ticket")
        if active is None or active == "":
            return True
    return False


def audit_product_finish_contract(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    """Audit finish-contract coverage and claim-vs-contract consistency for consumer-facing repos."""
    brief_path = root / "docs" / "spec" / "CANONICAL-BRIEF.md"
    if not brief_path.exists():
        return
    if not _is_consumer_facing_repo(root, ctx):
        return

    brief_text = ctx.read_text(brief_path)
    brief_rel = ctx.normalize_path(brief_path, root)

    if not _brief_has_finish_contract(brief_text):
        ctx.add_finding(
            findings,
            Finding(
                code="FINISH001",
                severity="warning",
                problem="Consumer-facing repo is missing a Product Finish Contract in the canonical brief.",
                root_cause="Without an explicit finish bar, audit and closeout cannot distinguish a functional prototype from an intentionally finished product, and backlog generation cannot create owned finish work.",
                files=[brief_rel],
                safer_pattern="Add a Product Finish Contract section (section 13) to the canonical brief with deliverable_kind, placeholder_policy, visual/audio finish targets, content_source_plan, and finish_acceptance_signals.",
                evidence=[f"{brief_rel} has no section 13 or Product Finish Contract heading."],
                provenance="script",
            ),
        )
        return

    missing_fields = _missing_finish_contract_fields(brief_text)
    if missing_fields:
        ctx.add_finding(
            findings,
            Finding(
                code="FINISH001",
                severity="warning",
                problem="Consumer-facing repo has an incomplete Product Finish Contract in the canonical brief.",
                root_cause="The finish section exists, but it omits required truth fields that backlog generation, audit, and closeout need to assign ownership and evaluate whether the product is actually finished.",
                files=[brief_rel],
                safer_pattern="Populate the Product Finish Contract with deliverable_kind, placeholder_policy, visual/audio finish targets, content_source_plan, licensing_or_provenance_constraints, and finish_acceptance_signals before treating the repo as consumer-ready.",
                evidence=[f"{brief_rel} is missing finish-contract fields: {', '.join(missing_fields)}"],
                provenance="script",
            ),
        )
        return

    if _finish_contract_allows_placeholders(brief_text):
        return

    open_finish = _open_finish_lane_tickets(root, ctx)
    if not open_finish:
        return

    if not _repo_claims_completion(root, ctx):
        return

    ctx.add_finding(
        findings,
        Finding(
            code="FINISH002",
            severity="error",
            problem="Repo claims ready or finished state, but the finish contract forbids placeholder output and finish-owning tickets are still open.",
            root_cause="The restart narrative or workflow state signals completion while the canonical finish contract still requires non-placeholder visuals, audio, or content proof.",
            files=[brief_rel],
            safer_pattern="Either close or supersede the open finish tickets with real content proof, or update the restart narrative to stop claiming finished-product ready state until the finish bar is met.",
            evidence=[
                f"{brief_rel} records no_placeholders policy in the finish contract.",
                f"Open finish-lane tickets: {', '.join(open_finish)}",
            ],
            provenance="script",
        ),
    )


def run_contract_surface_audits(root: Path, findings: list[Finding], ctx: ContractSurfaceAuditContext) -> None:
    audit_status_model(root, findings, ctx)
    audit_status_semantics_docs(root, findings, ctx)
    audit_planned_tickets_without_artifacts(root, findings, ctx)
    audit_missing_tool_layer(root, findings, ctx)
    audit_overloaded_artifact_register(root, findings, ctx)
    audit_artifact_persistence_prompt_contract(root, findings, ctx)
    audit_failure_recovery_contract(root, findings, ctx)
    audit_artifact_path_contract_drift(root, findings, ctx)
    audit_workflow_vocabulary_drift(root, findings, ctx)
    audit_artifact_brief_missing_tuple(root, findings, ctx)
    audit_workflow_state_desync(root, findings, ctx)
    audit_handoff_overwrites_start_here(root, findings, ctx)
    audit_invalid_tool_schemas(root, findings, ctx)
    audit_missing_observability_layer(root, findings, ctx)
    audit_process_change_tracking(root, findings, ctx)
    audit_missing_post_migration_verification(root, findings, ctx)
    audit_partial_workflow_layer_drift(root, findings, ctx)
    audit_raw_file_state_ownership(root, findings, ctx)
    audit_missing_artifact_gates(root, findings, ctx)
    audit_read_only_shell_mutation(root, findings, ctx)
    audit_read_only_write_language(root, findings, ctx)
    audit_over_scoped_commands(root, findings, ctx)
    audit_eager_skill_loading(root, findings, ctx)
    audit_placeholder_local_skills(root, findings, ctx)
    audit_model_profile_drift(root, findings, ctx)
    audit_product_finish_contract(root, findings, ctx)
