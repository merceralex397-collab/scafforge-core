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


def _finding(*, code: str, problem: str, root_cause: str, files: list[str], safer_pattern: str, evidence: list[str]) -> Finding:
    return Finding(
        code=code,
        severity="error",
        problem=problem,
        root_cause=root_cause,
        files=files,
        safer_pattern=safer_pattern,
        evidence=evidence,
        provenance="script",
    )


def _placeholder_skill_hits(root: Path) -> list[str]:
    skills_root = root / ".opencode" / "skills"
    if not skills_root.exists():
        return []
    hits: list[str] = []
    for path in sorted(skills_root.rglob("SKILL.md")):
        text = _read_text(path)
        if "Replace this file" in text or "TODO: replace" in text:
            hits.append(_normalize(path, root))
    return hits


def verify_greenfield_continuation(root: Path) -> list[Finding]:
    findings: list[Finding] = []

    manifest_path = root / "tickets" / "manifest.json"
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    start_here_path = root / "START-HERE.md"
    latest_handoff_path = root / ".opencode" / "state" / "latest-handoff.md"
    workflow_doc_path = root / "docs" / "process" / "workflow.md"
    ticket_lookup_path = root / ".opencode" / "tools" / "ticket_lookup.ts"
    ticket_execution_path = root / ".opencode" / "skills" / "ticket-execution" / "SKILL.md"
    team_leader_path = next((root / ".opencode" / "agents").glob("*team-leader*.md"), None)

    manifest, manifest_error = _read_json(manifest_path)
    workflow, workflow_error = _read_json(workflow_path)
    start_here = _read_text(start_here_path)
    latest_handoff = _read_text(latest_handoff_path)
    workflow_doc = _read_text(workflow_doc_path)
    ticket_lookup = _read_text(ticket_lookup_path)
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

    return findings


__all__ = ["Finding", "audit_repo", "verify_greenfield_continuation", "GREENFIELD_BOOTSTRAP_NEXT_ACTION"]
