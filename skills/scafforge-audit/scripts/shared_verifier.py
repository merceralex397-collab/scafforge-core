from __future__ import annotations

import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_repo_process import audit_repo
from shared_verifier_types import Finding

GREENFIELD_BOOTSTRAP_NEXT_ACTION = (
    "Run `environment_bootstrap`, register its proof artifact, rerun `ticket_lookup`, "
    "and do not continue lifecycle work until bootstrap is ready."
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _read_json(path: Path) -> tuple[object | None, str | None]:
    if not path.exists():
        return None, None
    try:
        return json.loads(_read_text(path)), None
    except json.JSONDecodeError as exc:
        return None, f"{exc.msg} at line {exc.lineno} column {exc.colno}"


def _normalize(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _finding(
    *,
    code: str,
    problem: str,
    root_cause: str,
    files: list[str],
    safer_pattern: str,
    evidence: list[str],
    remediation_action: str | None = None,
    remediation_target: str | None = None,
    is_user_action: bool = False,
) -> Finding:
    return Finding(
        code=code,
        severity="error",
        problem=problem,
        root_cause=root_cause,
        files=files,
        safer_pattern=safer_pattern,
        evidence=evidence,
        provenance="script",
        remediation_action=remediation_action or safer_pattern,
        remediation_target=remediation_target or (files[0] if files else None),
        is_user_action=is_user_action,
    )


def _placeholder_skill_hits(root: Path) -> list[str]:
    skills_root = root / ".opencode" / "skills"
    if not skills_root.exists():
        return []
    hits: list[str] = []
    for path in sorted(skills_root.rglob("SKILL.md")):
        text = _read_text(path)
        if (
            "Replace this file" in text
            or "TODO: replace" in text
            or "__STACK_LABEL__" in text
            or "When the repo stack is finalized, rewrite this catalog so review and QA agents get the exact build, lint, reference-integrity, and test commands that belong to this project." in text
            or "When the project stack is confirmed, replace this file's Universal Standards section with stack-specific rules using the `project-skill-bootstrap` skill." in text
        ):
            hits.append(_normalize(path, root))
    return hits


def _contains_all(text: str, required_snippets: tuple[str, ...]) -> bool:
    return all(snippet in text for snippet in required_snippets)


def verify_greenfield_bootstrap_lane(root: Path) -> list[Finding]:
    findings: list[Finding] = []

    manifest_path = root / "tickets" / "manifest.json"
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    start_here_path = root / "START-HERE.md"
    latest_handoff_path = root / ".opencode" / "state" / "latest-handoff.md"
    workflow_doc_path = root / "docs" / "process" / "workflow.md"
    tooling_doc_path = root / "docs" / "process" / "tooling.md"
    ticket_lookup_path = root / ".opencode" / "tools" / "ticket_lookup.ts"
    environment_bootstrap_path = root / ".opencode" / "tools" / "environment_bootstrap.ts"

    manifest, manifest_error = _read_json(manifest_path)
    workflow, workflow_error = _read_json(workflow_path)
    start_here = _read_text(start_here_path)
    latest_handoff = _read_text(latest_handoff_path)
    workflow_doc = _read_text(workflow_doc_path)
    tooling_doc = _read_text(tooling_doc_path)
    ticket_lookup = _read_text(ticket_lookup_path)
    environment_bootstrap = _read_text(environment_bootstrap_path)

    if not isinstance(manifest, dict) or not isinstance(workflow, dict):
        findings.append(
            _finding(
                code="VERIFY101",
                problem="The base scaffold is missing canonical queue or workflow state for the bootstrap lane.",
                root_cause="The earliest greenfield proof cannot validate one legal first move when manifest or workflow-state is absent or invalid immediately after scaffold generation.",
                files=[_normalize(manifest_path, root), _normalize(workflow_path, root)],
                safer_pattern="Emit tickets/manifest.json and .opencode/state/workflow-state.json as part of the scaffold render before any later specialization step begins.",
                evidence=[
                    f"{_normalize(manifest_path, root)} exists: {manifest_path.exists()}",
                    f"{_normalize(workflow_path, root)} exists: {workflow_path.exists()}",
                    f"{_normalize(manifest_path, root)} parse_error: {manifest_error or 'none'}",
                    f"{_normalize(workflow_path, root)} parse_error: {workflow_error or 'none'}",
                ],
            )
        )
        return findings

    active_ticket = workflow.get("active_ticket")
    bootstrap = workflow.get("bootstrap") if isinstance(workflow.get("bootstrap"), dict) else {}
    bootstrap_status = str(bootstrap.get("status", "")).strip()
    bootstrap_proof = str(bootstrap.get("proof_artifact", "")).strip()
    bootstrap_blockers = workflow.get("bootstrap_blockers") if isinstance(workflow.get("bootstrap_blockers"), list) else []
    tickets = manifest.get("tickets") if isinstance(manifest.get("tickets"), list) else []
    first_ticket = tickets[0] if tickets and isinstance(tickets[0], dict) else {}

    if active_ticket != manifest.get("active_ticket") or active_ticket != first_ticket.get("id"):
        findings.append(
            _finding(
                code="VERIFY102",
                problem="The base scaffold does not expose one canonical bootstrap ticket across manifest and workflow state.",
                root_cause="The first legal move becomes ambiguous before specialization even starts when manifest and workflow state disagree on the foreground bootstrap lane.",
                files=[_normalize(manifest_path, root), _normalize(workflow_path, root)],
                safer_pattern="Keep one bounded setup/bootstrap ticket aligned across tickets/manifest.json and workflow-state immediately after scaffold generation.",
                evidence=[
                    f"workflow active_ticket = {active_ticket!r}",
                    f"manifest active_ticket = {manifest.get('active_ticket')!r}",
                    f"first manifest ticket id = {first_ticket.get('id')!r}",
                ],
            )
        )

    if first_ticket.get("id") != "SETUP-001" or "Bootstrap environment" not in str(first_ticket.get("title", "")):
        findings.append(
            _finding(
                code="VERIFY103",
                problem="The base scaffold does not keep the bootstrap lane as the bounded first move.",
                root_cause="The early proof layer fails when the initial scaffold does not seed one explicit setup/bootstrap ticket as the foreground lane.",
                files=[_normalize(manifest_path, root)],
                safer_pattern="Seed SETUP-001 as the explicit bootstrap and scaffold-readiness lane before any deeper implementation or specialization work.",
                evidence=[
                    f"first manifest ticket id = {first_ticket.get('id')!r}",
                    f"first manifest ticket title = {first_ticket.get('title')!r}",
                ],
            )
        )

    if bootstrap_status not in {"missing", "failed", "ready"}:
        findings.append(
            _finding(
                code="VERIFY104",
                problem="The base scaffold records an invalid bootstrap state for the first legal move.",
                root_cause="The bootstrap-lane proof cannot route cleanly when bootstrap.status is missing or unknown immediately after scaffold generation.",
                files=[_normalize(workflow_path, root)],
                safer_pattern="Keep bootstrap.status explicit as missing, failed, or ready from the first scaffold render onward.",
                evidence=[f"bootstrap.status = {bootstrap_status!r}"],
            )
        )

    if bootstrap_status == "ready" and not bootstrap_proof:
        findings.append(
            _finding(
                code="VERIFY105",
                problem="Bootstrap is marked ready without proof in the early scaffold state.",
                root_cause="The first proof layer becomes untrustworthy when bootstrap readiness is recorded before a proof artifact path exists.",
                files=[_normalize(workflow_path, root)],
                safer_pattern="Only mark bootstrap ready when workflow-state also records the proof artifact path, even in the earliest scaffold state.",
                evidence=[f"bootstrap = {json.dumps(bootstrap, sort_keys=True)}"],
            )
        )

    missing_routing: list[str] = []
    if bootstrap_status != "ready":
        if GREENFIELD_BOOTSTRAP_NEXT_ACTION not in start_here:
            missing_routing.append(_normalize(start_here_path, root))
        if "bootstrap recovery required" not in latest_handoff:
            missing_routing.append(_normalize(latest_handoff_path, root))
        if "run `environment_bootstrap` first, then rerun `ticket_lookup` before any stage change" not in workflow_doc:
            missing_routing.append(_normalize(workflow_doc_path, root))
        if "if bootstrap is not ready it short-circuits normal lifecycle guidance and routes `environment_bootstrap` first" not in tooling_doc:
            missing_routing.append(_normalize(tooling_doc_path, root))
        if "Run environment_bootstrap first, then rerun ticket_lookup before attempting lifecycle transitions." not in ticket_lookup:
            missing_routing.append(_normalize(ticket_lookup_path, root))
    if not environment_bootstrap.strip():
        missing_routing.append(_normalize(environment_bootstrap_path, root))

    if missing_routing:
        findings.append(
            _finding(
                code="VERIFY106",
                problem="The base scaffold does not preserve one executable bootstrap-first route across its managed surfaces.",
                root_cause="The early proof layer fails when restart, workflow, and tool surfaces do not align on environment_bootstrap as the first legal move before specialization begins.",
                files=missing_routing,
                safer_pattern="Keep START-HERE, latest-handoff, workflow docs, tooling docs, ticket_lookup, and environment_bootstrap aligned on one bootstrap-first route immediately after scaffold generation.",
                evidence=[
                    f"bootstrap.status = {bootstrap_status!r}",
                    f"missing aligned bootstrap-lane surfaces: {', '.join(missing_routing)}",
                ],
            )
        )

    return findings


def verify_greenfield_continuation(root: Path) -> list[Finding]:
    findings: list[Finding] = []

    manifest_path = root / "tickets" / "manifest.json"
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    start_here_path = root / "START-HERE.md"
    latest_handoff_path = root / ".opencode" / "state" / "latest-handoff.md"
    workflow_doc_path = root / "docs" / "process" / "workflow.md"
    tooling_doc_path = root / "docs" / "process" / "tooling.md"
    tickets_readme_path = root / "tickets" / "README.md"
    ticket_lookup_path = root / ".opencode" / "tools" / "ticket_lookup.ts"
    ticket_update_path = root / ".opencode" / "tools" / "ticket_update.ts"
    smoke_test_path = root / ".opencode" / "tools" / "smoke_test.ts"
    handoff_publish_path = root / ".opencode" / "tools" / "handoff_publish.ts"
    ticket_execution_path = root / ".opencode" / "skills" / "ticket-execution" / "SKILL.md"
    team_leader_path = next((root / ".opencode" / "agents").glob("*team-leader*.md"), None)

    manifest, manifest_error = _read_json(manifest_path)
    workflow, workflow_error = _read_json(workflow_path)
    start_here = _read_text(start_here_path)
    latest_handoff = _read_text(latest_handoff_path)
    workflow_doc = _read_text(workflow_doc_path)
    tooling_doc = _read_text(tooling_doc_path)
    tickets_readme = _read_text(tickets_readme_path)
    ticket_lookup = _read_text(ticket_lookup_path)
    ticket_update = _read_text(ticket_update_path)
    smoke_test = _read_text(smoke_test_path)
    handoff_publish = _read_text(handoff_publish_path)
    ticket_execution = _read_text(ticket_execution_path)
    team_leader = _read_text(team_leader_path) if team_leader_path else ""

    if not isinstance(manifest, dict) or not isinstance(workflow, dict):
        findings.append(
            _finding(
                code="VERIFY001",
                problem="The generated repo is missing canonical queue or workflow state needed for immediate continuation.",
                root_cause="Greenfield handoff cannot prove a legal first move when manifest or workflow-state is absent or invalid.",
                files=[_normalize(manifest_path, root), _normalize(workflow_path, root)],
                safer_pattern="Publish handoff only after tickets/manifest.json and .opencode/state/workflow-state.json exist and agree on the active ticket.",
                evidence=[
                    f"{_normalize(manifest_path, root)} exists: {manifest_path.exists()}",
                    f"{_normalize(workflow_path, root)} exists: {workflow_path.exists()}",
                    f"{_normalize(manifest_path, root)} parse_error: {manifest_error or 'none'}",
                    f"{_normalize(workflow_path, root)} parse_error: {workflow_error or 'none'}",
                ],
            )
        )
        return findings

    active_ticket = workflow.get("active_ticket")
    bootstrap = workflow.get("bootstrap") if isinstance(workflow.get("bootstrap"), dict) else {}
    bootstrap_status = str(bootstrap.get("status", "")).strip()
    bootstrap_proof = str(bootstrap.get("proof_artifact", "")).strip()
    bootstrap_blockers = workflow.get("bootstrap_blockers") if isinstance(workflow.get("bootstrap_blockers"), list) else []
    tickets = manifest.get("tickets") if isinstance(manifest.get("tickets"), list) else []
    first_ticket = tickets[0] if tickets and isinstance(tickets[0], dict) else {}

    if active_ticket != manifest.get("active_ticket") or active_ticket != first_ticket.get("id"):
        findings.append(
            _finding(
                code="VERIFY002",
                problem="The generated repo does not expose one canonical first ticket across manifest and workflow state.",
                root_cause="Immediate continuation becomes ambiguous when the restart surface, manifest, and workflow state do not agree on the foreground bootstrap ticket.",
                files=[_normalize(manifest_path, root), _normalize(workflow_path, root)],
                safer_pattern="Keep one bounded bootstrap ticket as the canonical first lane and align manifest plus workflow-state on that ticket before handoff.",
                evidence=[
                    f"workflow active_ticket = {active_ticket!r}",
                    f"manifest active_ticket = {manifest.get('active_ticket')!r}",
                    f"first manifest ticket id = {first_ticket.get('id')!r}",
                ],
            )
        )

    if first_ticket.get("id") != "SETUP-001" or "Bootstrap environment" not in str(first_ticket.get("title", "")):
        findings.append(
            _finding(
                code="VERIFY003",
                problem="The generated repo does not keep the bootstrap lane as the bounded first move.",
                root_cause="Greenfield handoff loses its proof-first path when the first ticket is not explicitly the bootstrap and scaffold-readiness lane.",
                files=[_normalize(manifest_path, root)],
                safer_pattern="Seed one foreground setup/bootstrap ticket whose purpose is environment proof and scaffold readiness before deeper implementation begins.",
                evidence=[
                    f"first manifest ticket id = {first_ticket.get('id')!r}",
                    f"first manifest ticket title = {first_ticket.get('title')!r}",
                ],
            )
        )

    if bootstrap_status not in {"missing", "failed", "ready"}:
        findings.append(
            _finding(
                code="VERIFY004",
                problem="The generated repo records an invalid bootstrap state for the first continuation gate.",
                root_cause="Greenfield handoff cannot route the first legal move if bootstrap.status is missing or uses an unknown value.",
                files=[_normalize(workflow_path, root)],
                safer_pattern="Keep bootstrap.status explicit as missing, failed, or ready and drive first-move routing from that canonical state.",
                evidence=[f"bootstrap.status = {bootstrap_status!r}"],
            )
        )

    if bootstrap_status == "ready" and not bootstrap_proof:
        findings.append(
            _finding(
                code="VERIFY005",
                problem="Bootstrap is marked ready without proof.",
                root_cause="A ready bootstrap state without a proof artifact overclaims continuability and leaves the next move untrustworthy.",
                files=[_normalize(workflow_path, root)],
                safer_pattern="Only mark bootstrap ready when workflow-state also records the proof artifact path.",
                evidence=[f"bootstrap = {json.dumps(bootstrap, sort_keys=True)}"],
            )
        )

    if bootstrap_status != "ready":
        missing_routing: list[str] = []
        if GREENFIELD_BOOTSTRAP_NEXT_ACTION not in start_here:
            missing_routing.append(_normalize(start_here_path, root))
        if "bootstrap recovery required" not in latest_handoff:
            missing_routing.append(_normalize(latest_handoff_path, root))
        if "run `environment_bootstrap` first, then rerun `ticket_lookup` before any stage change" not in workflow_doc:
            missing_routing.append(_normalize(workflow_doc_path, root))
        if "Run environment_bootstrap first, then rerun ticket_lookup before attempting lifecycle transitions." not in ticket_lookup:
            missing_routing.append(_normalize(ticket_lookup_path, root))
        if "if `ticket_lookup.bootstrap.status` is not `ready`, stop normal lifecycle routing, run `environment_bootstrap`, then rerun `ticket_lookup` before any `ticket_update`" not in ticket_execution:
            missing_routing.append(_normalize(ticket_execution_path, root))
        if "If `ticket_lookup.bootstrap.status` is not `ready`, treat `environment_bootstrap` as the next required tool call" not in team_leader:
            missing_routing.append(_normalize(team_leader_path, root) if team_leader_path else ".opencode/agents/*team-leader*.md")
        if missing_routing:
            findings.append(
                _finding(
                    code="VERIFY006",
                    problem="The generated repo does not align its first bootstrap move across restart, prompt, tool, and workflow surfaces.",
                    root_cause="Immediate continuation becomes guesswork when bootstrap-first routing is missing from one or more canonical greenfield surfaces.",
                    files=missing_routing,
                    safer_pattern="Keep START-HERE, latest-handoff, workflow docs, ticket_lookup, ticket-execution, and the team-leader prompt aligned on environment_bootstrap as the first legal move until bootstrap is ready.",
                    evidence=[
                        f"bootstrap.status = {bootstrap_status!r}",
                        f"missing aligned routing surfaces: {', '.join(missing_routing)}",
                    ],
                )
            )

    placeholder_hits = _placeholder_skill_hits(root)
    if placeholder_hits:
        findings.append(
            _finding(
                code="VERIFY007",
                problem="The generated repo still contains placeholder local skills at handoff time.",
                root_cause="A scaffold with placeholder local skills is not immediately continuable because weaker models cannot trust the repo-local operating guidance.",
                files=placeholder_hits,
                safer_pattern="Run project-skill-bootstrap until scaffold placeholder text is removed from repo-local skills before treating greenfield generation as complete.",
                evidence=[f"placeholder skills: {', '.join(placeholder_hits)}"],
            )
        )

    contract_alignment_missing: list[str] = []
    if not _contains_all(
        tooling_doc,
        (
            "returns `transition_guidance` with the next legal stage move",
            "`ticket_update` changes lifecycle stage",
            "`smoke_test` runs deterministic smoke-test commands, writes the canonical smoke-test artifact itself",
            "`handoff_publish` refreshes the top-level handoff",
            "commands are human entrypoints only",
        ),
    ):
        contract_alignment_missing.append(_normalize(tooling_doc_path, root))
    if not _contains_all(
        tickets_readme,
        (
            "keep ticket `status` coarse",
            "keep ticket `stage` lifecycle-oriented",
            "use `ticket_lookup.transition_guidance` before changing a ticket stage",
        ),
    ):
        contract_alignment_missing.append(_normalize(tickets_readme_path, root))
    if not _contains_all(
        ticket_update,
        (
            "to implementation before it passes through plan_review.",
            "Cannot move to qa before at least one review artifact exists.",
            "validateSmokeTestArtifactEvidence",
        ),
    ):
        contract_alignment_missing.append(_normalize(ticket_update_path, root))
    if not _contains_all(
        smoke_test,
        (
            "Ticket acceptance criteria define an explicit smoke-test command.",
            "command_override cannot mix tokenized argv entries with multiple shell-style command strings.",
            "registerArtifactSnapshot",
        ),
    ):
        contract_alignment_missing.append(_normalize(smoke_test_path, root))
    if "const handoffBlocker = await validateHandoffNextAction" not in handoff_publish or "await refreshRestartSurfaces" not in handoff_publish:
        contract_alignment_missing.append(_normalize(handoff_publish_path, root))
    elif handoff_publish.find("const handoffBlocker = await validateHandoffNextAction") >= handoff_publish.find("await refreshRestartSurfaces"):
        contract_alignment_missing.append(_normalize(handoff_publish_path, root))

    if contract_alignment_missing:
        findings.append(
            _finding(
                code="VERIFY008",
                problem="The generated repo does not keep its workflow docs and executable tool surfaces aligned on continuation-critical lifecycle behavior.",
                root_cause="Immediate continuation becomes brittle when the proof-first gate ignores documented workflow surfaces or those surfaces drift from the executable contract.",
                files=contract_alignment_missing,
                safer_pattern="Keep tooling docs, ticket guidance docs, ticket_update, smoke_test, and handoff_publish aligned on lifecycle gating, canonical smoke ownership, transition guidance, and truthful handoff publication before greenfield handoff.",
                evidence=[f"missing or drifted contract surfaces: {', '.join(contract_alignment_missing)}"],
            )
        )

    if "bootstrap_blockers" not in workflow or not isinstance(bootstrap_blockers, list):
        findings.append(
            _finding(
                code="VERIFY009",
                problem="The generated repo does not persist bootstrap blockers in canonical workflow state.",
                root_cause="Greenfield continuation cannot reliably stop on missing host prerequisites when environment bootstrap results are not preserved across sessions.",
                files=[_normalize(workflow_path, root)],
                safer_pattern="Persist bootstrap_blockers in workflow-state and require environment_bootstrap to clear them before greenfield handoff succeeds.",
                evidence=[f"bootstrap_blockers field present: {'bootstrap_blockers' in workflow}", f"bootstrap_blockers value: {bootstrap_blockers!r}"],
                remediation_action="Regenerate or repair the workflow-state template so it persists bootstrap_blockers, then rerun the greenfield verifier.",
                remediation_target=_normalize(workflow_path, root),
            )
        )
    elif bootstrap_status == "ready" and bootstrap_blockers:
        blocker_names = [str(item.get("executable", "unknown")) for item in bootstrap_blockers if isinstance(item, dict)]
        findings.append(
            _finding(
                code="VERIFY009",
                problem="Environment bootstrap completed with unresolved blockers still recorded in workflow state.",
                root_cause="Greenfield continuation is not immediately runnable when the host dependency proof claims readiness while unresolved environment prerequisites remain.",
                files=[_normalize(workflow_path, root)],
                safer_pattern="Require environment_bootstrap to return zero unresolved blockers before marking bootstrap ready or passing the greenfield continuation gate.",
                evidence=[
                    f"bootstrap.status = {bootstrap_status!r}",
                    f"bootstrap_blockers = {json.dumps(bootstrap_blockers, sort_keys=True)}",
                    f"unresolved blocker executables = {', '.join(blocker_names) or 'none'}",
                ],
                remediation_action=f"Resolve the missing environment dependencies reported by environment_bootstrap: {', '.join(blocker_names) or 'unknown blockers'}, then rerun bootstrap proof.",
                remediation_target=_normalize(workflow_path, root),
                is_user_action=True,
            )
        )

    audit_findings = audit_repo(root)
    critical_exec_findings = [finding for finding in audit_findings if finding.code.startswith("EXEC") and finding.severity == "error"]
    if critical_exec_findings:
        findings.append(
            _finding(
                code="VERIFY010",
                problem="The generated repo still has critical execution-surface failures after the greenfield continuation gate.",
                root_cause="Immediate continuation is not truthful when stack-specific execution audit findings already show that the generated repo cannot build, validate, or load cleanly on its declared stack.",
                files=sorted({path for finding in critical_exec_findings for path in finding.files}),
                safer_pattern="Run the stack-specific execution audit as part of the greenfield continuation proof and require zero critical EXEC findings before handoff.",
                evidence=[f"{finding.code}: {finding.problem}" for finding in critical_exec_findings[:6]],
                remediation_action="Fix the reported build, load, or compile failures in the generated repo, then rerun the continuation verifier.",
                remediation_target=(critical_exec_findings[0].files[0] if critical_exec_findings and critical_exec_findings[0].files else None),
            )
        )

    critical_reference_findings = [finding for finding in audit_findings if finding.code in {"REF-001", "REF-002"}]
    if critical_reference_findings:
        findings.append(
            _finding(
                code="VERIFY011",
                problem="The generated repo still has broken reference-integrity findings after the greenfield continuation gate.",
                root_cause="Immediate continuation is not trustworthy when canonical scene or config surfaces already point at missing files or broken code references in the generated repo.",
                files=sorted({path for finding in critical_reference_findings for path in finding.files}),
                safer_pattern="Run reference-integrity audit as part of greenfield verification and require zero REF-001 or REF-002 findings before handoff.",
                evidence=[f"{finding.code}: {finding.problem}" for finding in critical_reference_findings[:6]],
                remediation_action="Repair the broken scene, config, or structural file references reported by the reference-integrity audit, then rerun the continuation verifier.",
                remediation_target=(critical_reference_findings[0].files[0] if critical_reference_findings and critical_reference_findings[0].files else None),
            )
        )

    return findings


__all__ = [
    "Finding",
    "audit_repo",
    "verify_greenfield_bootstrap_lane",
    "verify_greenfield_continuation",
    "GREENFIELD_BOOTSTRAP_NEXT_ACTION",
]
