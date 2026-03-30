from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from audit_repo_process import load_latest_previous_diagnosis, manifest_supporting_logs, supporting_log_paths
from regenerate_restart_surfaces import regenerate_restart_surfaces
from shared_verifier import audit_repo


START_HERE_MANAGED_START = "<!-- SCAFFORGE:START_HERE_BLOCK START -->"
START_HERE_MANAGED_END = "<!-- SCAFFORGE:START_HERE_BLOCK END -->"
DETERMINISTIC_PROCESS_DOCS = (
    "workflow.md",
    "tooling.md",
    "model-matrix.md",
    "git-capability.md",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply deterministic Scafforge process repairs to an existing repo.")
    parser.add_argument("repo_root", help="Repository root to repair.")
    parser.add_argument("--project-name", help="Override project name when provenance is missing.")
    parser.add_argument("--project-slug", help="Override project slug when provenance is missing.")
    parser.add_argument("--agent-prefix", help="Override agent prefix when provenance is missing.")
    parser.add_argument("--model-provider", help="Override model provider when provenance is missing.")
    parser.add_argument("--planner-model", help="Override planner model when provenance is missing.")
    parser.add_argument("--implementer-model", help="Override implementer model when provenance is missing.")
    parser.add_argument("--utility-model", help="Override utility model when provenance is missing.")
    parser.add_argument("--stack-label", default="framework-agnostic", help="Stack label for regenerated process docs.")
    parser.add_argument(
        "--change-summary",
        default="Deterministic Scafforge managed workflow surfaces refreshed by scafforge-repair.",
        help="Summary stored in workflow-state and repair history.",
    )
    parser.add_argument("--skip-verify", action="store_true", help="Skip the post-repair audit.")
    parser.add_argument("--supporting-log", action="append", default=[], help="Optional supporting session log or transcript path for post-repair verification. May be provided multiple times.")
    parser.add_argument(
        "--repair-basis-diagnosis",
        help="Optional diagnosis pack directory or manifest path that this repair run is based on. Defaults to the latest diagnosis pack in the repo.",
    )
    parser.add_argument("--fail-on", choices=("never", "warning", "error"), default="never")
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def normalize_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "project"


def merge_start_here(existing: str, rendered: str) -> str:
    rendered_pattern = re.compile(
        rf"{re.escape(START_HERE_MANAGED_START)}[\s\S]*?{re.escape(START_HERE_MANAGED_END)}",
        re.MULTILINE,
    )
    rendered_match = rendered_pattern.search(rendered)
    if not rendered_match:
        return rendered
    if not existing.strip():
        return rendered
    if START_HERE_MANAGED_START not in existing or START_HERE_MANAGED_END not in existing:
        return existing
    return rendered_pattern.sub(rendered_match.group(0), existing, count=1)


def package_root() -> Path:
    return Path(__file__).resolve().parents[3]


def current_package_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=package_root(),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip() or "unknown"


def bootstrap_script_path() -> Path:
    return Path(__file__).resolve().parents[2] / "repo-scaffold-factory" / "scripts" / "bootstrap_repo_scaffold.py"


def load_metadata(repo_root: Path, args: argparse.Namespace) -> dict[str, str]:
    provenance = read_json(repo_root / ".opencode" / "meta" / "bootstrap-provenance.json")
    manifest = read_json(repo_root / "tickets" / "manifest.json")
    runtime = provenance.get("runtime_models", {}) if isinstance(provenance, dict) else {}

    project_name = args.project_name or (provenance.get("project_name") if isinstance(provenance, dict) else None)
    if not project_name and isinstance(manifest, dict):
        raw_project = manifest.get("project")
        if isinstance(raw_project, str) and raw_project.strip():
            project_name = raw_project.strip()

    project_slug = args.project_slug or (provenance.get("project_slug") if isinstance(provenance, dict) else None)
    agent_prefix = args.agent_prefix or (provenance.get("agent_prefix") if isinstance(provenance, dict) else None)
    model_provider = args.model_provider or runtime.get("provider")
    planner_model = args.planner_model or runtime.get("planner")
    implementer_model = args.implementer_model or runtime.get("implementer")
    utility_model = args.utility_model or runtime.get("utility") or planner_model

    if not project_slug and project_name:
        project_slug = slugify(project_name)
    if not agent_prefix and project_slug:
        agent_prefix = project_slug

    values = {
        "project_name": project_name,
        "project_slug": project_slug,
        "agent_prefix": agent_prefix,
        "model_provider": model_provider,
        "planner_model": planner_model,
        "implementer_model": implementer_model,
        "utility_model": utility_model,
    }
    missing = [key for key, value in values.items() if not isinstance(value, str) or not value.strip()]
    if missing:
        missing_display = ", ".join(missing)
        raise SystemExit(
            f"Missing required metadata for repair: {missing_display}. "
            "Provide overrides on the command line or ensure bootstrap provenance exists."
        )
    return {key: value.strip() for key, value in values.items()}


def run_bootstrap_render(dest_root: Path, metadata: dict[str, str], stack_label: str) -> None:
    command = [
        sys.executable,
        str(bootstrap_script_path()),
        "--dest",
        str(dest_root),
        "--project-name",
        metadata["project_name"],
        "--project-slug",
        metadata["project_slug"],
        "--agent-prefix",
        metadata["agent_prefix"],
        "--model-provider",
        metadata["model_provider"],
        "--planner-model",
        metadata["planner_model"],
        "--implementer-model",
        metadata["implementer_model"],
        "--utility-model",
        metadata["utility_model"],
        "--stack-label",
        stack_label,
        "--scope",
        "full",
        "--force",
    ]
    result = subprocess.run(command, cwd=package_root(), check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            "Unable to render repair scaffold.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


def replace_directory(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def replace_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def normalize_ticket_state_map(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for ticket_id, ticket_state in value.items():
        if not isinstance(ticket_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", ticket_id):
            continue
        approved_plan = False
        reopen_count = 0
        needs_reverification = False
        if isinstance(ticket_state, dict) and isinstance(ticket_state.get("approved_plan"), bool):
            approved_plan = ticket_state["approved_plan"]
        if isinstance(ticket_state, dict) and isinstance(ticket_state.get("reopen_count"), int) and ticket_state["reopen_count"] >= 0:
            reopen_count = ticket_state["reopen_count"]
        if isinstance(ticket_state, dict) and isinstance(ticket_state.get("needs_reverification"), bool):
            needs_reverification = ticket_state["needs_reverification"]
        normalized[ticket_id] = {
            "approved_plan": approved_plan,
            "reopen_count": reopen_count,
            "needs_reverification": needs_reverification,
        }
    return normalized


def current_iso_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def find_placeholder_skills(repo_root: Path) -> list[str]:
    hits: list[str] = []
    skills_root = repo_root / ".opencode" / "skills"
    if not skills_root.exists():
        return hits
    for path in sorted(skills_root.rglob("SKILL.md")):
        text = read_text(path)
        if "Replace this file" in text or "TODO: replace" in text:
            hits.append(str(path.relative_to(repo_root)))
    return hits


def detect_agent_prompt_drift(repo_root: Path) -> list[str]:
    hits: list[str] = []
    agents_root = repo_root / ".opencode" / "agents"
    if not agents_root.exists():
        return hits

    team_leader = next(agents_root.glob("*team-leader*.md"), None)
    if team_leader:
        text = read_text(team_leader)
        if "next_action_tool" not in text or "summary-only stopping is invalid" not in text:
            hits.append(str(team_leader.relative_to(repo_root)))

    for pattern in ("*implementer*.md", "*lane-executor*.md", "*docs-handoff*.md"):
        for path in agents_root.glob(pattern):
            text = read_text(path)
            if "team leader already owns lease claim and release" not in text:
                hits.append(str(path.relative_to(repo_root)))
    return sorted(set(hits))


def _surface_entry(
    *,
    status: str,
    surfaces: list[str],
    reason: str,
    finding_codes: set[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "surfaces": sorted(set(surfaces)),
        "reason": reason,
    }
    if finding_codes:
        payload["finding_codes"] = sorted(finding_codes)
    return payload


def build_stale_surface_map(
    repo_root: Path,
    replaced_surfaces: list[str],
    findings: list[Any],
    pending_process_verification: bool,
    *,
    required_stage_names: set[str] | None = None,
    intent_decision_required: bool = False,
) -> dict[str, dict[str, Any]]:
    required_stage_names = required_stage_names or set()
    codes = {getattr(finding, "code", "") for finding in findings if getattr(finding, "code", "")}
    workflow_codes = {code for code in codes if code.startswith(("WFLOW", "BOOT", "CYCLE")) and code != "WFLOW008"}
    prompt_codes = {code for code in codes if code.startswith("WFLOW")}
    skill_codes = {code for code in codes if code.startswith(("SKILL", "MODEL"))}
    ticket_codes = {code for code in codes if code.startswith("EXEC") or code == "WFLOW008"}

    workflow_surfaces = [
        surface
        for surface in replaced_surfaces
        if surface in {"opencode.jsonc", ".opencode/tools", ".opencode/lib", ".opencode/plugins", ".opencode/commands"}
        or surface.startswith("docs/process/")
    ]
    restart_surfaces = [
        surface
        for surface in replaced_surfaces
        if surface in {"START-HERE.md managed block", ".opencode/state/context-snapshot.md", ".opencode/state/latest-handoff.md"}
    ]
    placeholder_skills = find_placeholder_skills(repo_root)
    prompt_drift = detect_agent_prompt_drift(repo_root)

    return {
        "workflow_tools_and_prompts": _surface_entry(
            status="replace" if workflow_surfaces or workflow_codes else "stable",
            surfaces=workflow_surfaces,
            reason="Managed workflow tools, prompts, and process docs were refreshed or still show workflow drift.",
            finding_codes=workflow_codes,
        ),
        "repo_local_skills": _surface_entry(
            status=(
                "regenerate"
                if "project-skill-bootstrap" in required_stage_names
                or "scaffold-managed .opencode/skills" in replaced_surfaces
                or placeholder_skills
                or skill_codes
                else "stable"
            ),
            surfaces=(["scaffold-managed .opencode/skills"] if "scaffold-managed .opencode/skills" in replaced_surfaces else []) + placeholder_skills,
            reason="Repo-local skills need regeneration when scaffold-managed skills were replaced or placeholder/model drift remains.",
            finding_codes=skill_codes,
        ),
        "agent_team_and_prompts": _surface_entry(
            status=(
                "regenerate"
                if {"opencode-team-bootstrap", "agent-prompt-engineering"} & required_stage_names
                or prompt_drift
                or prompt_codes
                else "stable"
            ),
            surfaces=prompt_drift,
            reason="Agent-team prompts stay stable unless drift remains after managed repair.",
            finding_codes=prompt_codes,
        ),
        "ticket_graph_and_follow_up": _surface_entry(
            status=(
                "ticket_follow_up"
                if "ticket-pack-builder" in required_stage_names or any(code.startswith("EXEC") for code in ticket_codes)
                else "stable"
            ),
            surfaces=[],
            reason=(
                "Ticket follow-up is required when source findings still need explicit routing through ticket-pack-builder."
                if "ticket-pack-builder" in required_stage_names or any(code.startswith("EXEC") for code in ticket_codes)
                else "Bare pending_process_verification remains workflow-state truth, but does not by itself force repair-side ticket follow-up."
                if pending_process_verification or "WFLOW008" in ticket_codes
                else "Ticket graph stays stable when repair did not uncover source-layer follow-up."
            ),
            finding_codes=ticket_codes,
        ),
        "restart_surfaces": _surface_entry(
            status="replace" if restart_surfaces else "stable",
            surfaces=restart_surfaces,
            reason="Restart surfaces are derived and must be regenerated whenever managed repair changes workflow state.",
        ),
        "canonical_project_decisions": _surface_entry(
            status="human_decision" if intent_decision_required else "stable",
            surfaces=["docs/spec/CANONICAL-BRIEF.md"] if intent_decision_required else [],
            reason=(
                "Repair exposed intent-changing drift; update canonical project decisions explicitly instead of treating this as routine managed repair."
                if intent_decision_required
                else "Managed repair preserves accepted project-scope decisions unless the repair basis explicitly exposes intent drift."
            ),
        ),
    }


def resolve_repair_basis(repo_root: Path, explicit_basis: str | None) -> tuple[Path, dict[str, Any]] | None:
    if not explicit_basis:
        return load_latest_previous_diagnosis(repo_root)

    candidate = Path(explicit_basis).expanduser()
    candidate = candidate if candidate.is_absolute() else (repo_root / candidate)
    candidate = candidate.resolve()
    manifest_path = candidate / "manifest.json" if candidate.is_dir() else candidate
    if manifest_path.name != "manifest.json":
        raise SystemExit("Repair basis path must be a diagnosis directory or a manifest.json file.")
    if not manifest_path.exists():
        raise SystemExit(f"Repair basis manifest not found: {manifest_path}")
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise SystemExit(f"Repair basis manifest is not valid JSON: {manifest_path}")
    return manifest_path.parent, manifest


def verification_logs(
    repo_root: Path,
    explicit_logs: list[str] | None,
    repair_basis: tuple[Path, dict[str, Any]] | None,
) -> list[Path]:
    logs = supporting_log_paths(repo_root, explicit_logs)
    if repair_basis is None:
        return logs

    _, manifest = repair_basis
    for path in supporting_log_paths(repo_root, manifest_supporting_logs(manifest)):
        if path not in logs:
            logs.append(path)
    return logs


def repair_basis_requires_causal_replay(
    repo_root: Path,
    explicit_logs: list[str] | None,
    repair_basis: tuple[Path, dict[str, Any]] | None,
) -> bool:
    if supporting_log_paths(repo_root, explicit_logs):
        return True
    if repair_basis is None:
        return False
    _, manifest = repair_basis
    return bool(manifest_supporting_logs(manifest))


def load_pending_process_verification(repo_root: Path) -> bool:
    workflow = read_json(repo_root / ".opencode" / "state" / "workflow-state.json")
    return isinstance(workflow, dict) and workflow.get("pending_process_verification") is True


def get_active_ticket(manifest: dict[str, Any], workflow: dict[str, Any]) -> dict[str, Any] | None:
    active_ticket_id = workflow.get("active_ticket") if isinstance(workflow, dict) else None
    tickets = manifest.get("tickets") if isinstance(manifest, dict) else None
    if not isinstance(active_ticket_id, str) or not isinstance(tickets, list):
        return None
    for ticket in tickets:
        if isinstance(ticket, dict) and ticket.get("id") == active_ticket_id:
            return ticket
    return None


def get_ticket_state(workflow: dict[str, Any], ticket_id: str) -> dict[str, Any]:
    ticket_state = workflow.get("ticket_state") if isinstance(workflow.get("ticket_state"), dict) else {}
    value = ticket_state.get(ticket_id) if isinstance(ticket_state, dict) else None
    return value if isinstance(value, dict) else {}


def blocked_dependents(manifest: dict[str, Any], ticket_id: str) -> list[dict[str, Any]]:
    tickets = manifest.get("tickets") if isinstance(manifest.get("tickets"), list) else []
    blocked: list[dict[str, Any]] = []
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        depends_on = ticket.get("depends_on")
        if isinstance(depends_on, list) and ticket_id in depends_on and ticket.get("status") != "done":
            blocked.append(ticket)
    return blocked


def render_start_here(manifest: dict[str, Any], workflow: dict[str, Any], backlog_verifier_agent: str | None = None) -> str:
    ticket = get_active_ticket(manifest, workflow)
    if not isinstance(ticket, dict):
        return "# START HERE\n"

    tickets = manifest.get("tickets") if isinstance(manifest.get("tickets"), list) else []
    reopened = [item for item in tickets if isinstance(item, dict) and item.get("resolution_state") == "reopened"]
    suspect_done = [
        item
        for item in tickets
        if isinstance(item, dict)
        and item.get("status") == "done"
        and item.get("verification_state") not in {"trusted", "reverified"}
    ]
    reverification = [
        item
        for item in tickets
        if isinstance(item, dict) and get_ticket_state(workflow, str(item.get("id", ""))).get("needs_reverification") is True
    ]
    blocked = blocked_dependents(manifest, str(ticket.get("id", "")))
    verifier_label = f"`{backlog_verifier_agent}`" if backlog_verifier_agent else "the backlog verifier"
    bootstrap = workflow.get("bootstrap") if isinstance(workflow.get("bootstrap"), dict) else {}
    bootstrap_status = str(bootstrap.get("status", "")).strip() or "missing"
    bootstrap_proof = bootstrap.get("proof_artifact") if isinstance(bootstrap.get("proof_artifact"), str) and bootstrap.get("proof_artifact") else "None"
    if bootstrap_status != "ready":
        recommended_action = "Run environment_bootstrap, register its proof artifact, then continue ticket execution."
    elif workflow.get("pending_process_verification") is True:
        recommended_action = f"Use the team leader to route {verifier_label} across done tickets whose trust predates the current process contract."
    elif blocked and ticket.get("status") != "done":
        blocked_ids = ", ".join(str(item.get("id", "")).strip() for item in blocked if str(item.get("id", "")).strip())
        recommended_action = f"Finish {ticket.get('id')} and its closeout proof before resuming dependent tickets: {blocked_ids}."
    else:
        recommended_action = "Continue the required internal lifecycle from the current ticket stage."

    risk_lines = []
    if bootstrap_status != "ready":
        risk_lines.append("- Environment validation can fail for setup reasons until bootstrap proof exists.")
    if workflow.get("pending_process_verification") is True:
        risk_lines.append("- Historical completion should not be treated as fully trusted until pending process verification is cleared.")
    if suspect_done:
        risk_lines.append("- Some done tickets are not fully trusted yet; use the backlog verifier before relying on earlier closeout.")
    if blocked and ticket.get("status") != "done":
        blocked_ids = ", ".join(str(item.get("id", "")).strip() for item in blocked if str(item.get("id", "")).strip())
        risk_lines.append(f"- Downstream tickets {blocked_ids} remain formally blocked until {ticket.get('id')} reaches done.")
    if not risk_lines:
        risk_lines.append("- None recorded.")

    def summarize(items: list[dict[str, Any]]) -> str:
        values = [str(item.get("id", "")).strip() for item in items if isinstance(item, dict) and str(item.get("id", "")).strip()]
        return ", ".join(values) if values else "none"

    return (
        "# START HERE\n\n"
        f"{START_HERE_MANAGED_START}\n"
        "## What This Repo Is\n\n"
        f"{manifest.get('project', 'Project')}\n\n"
        "## Current State\n\n"
        "The repo is operating under the managed OpenCode workflow. Use the canonical state files below instead of memory or raw ticket prose.\n\n"
        "## Read In This Order\n\n"
        "1. README.md\n"
        "2. AGENTS.md\n"
        "3. docs/spec/CANONICAL-BRIEF.md\n"
        "4. docs/process/workflow.md\n"
        "5. tickets/BOARD.md\n"
        "6. tickets/manifest.json\n\n"
        "## Current Or Next Ticket\n\n"
        f"- ID: {ticket.get('id')}\n"
        f"- Title: {ticket.get('title')}\n"
        f"- Wave: {ticket.get('wave')}\n"
        f"- Lane: {ticket.get('lane')}\n"
        f"- Stage: {ticket.get('stage')}\n"
        f"- Status: {ticket.get('status')}\n"
        f"- Resolution: {ticket.get('resolution_state')}\n"
        f"- Verification: {ticket.get('verification_state')}\n\n"
        "## Dependency Status\n\n"
        f"- current_ticket_done: {'yes' if ticket.get('status') == 'done' else 'no'}\n"
        f"- dependent_tickets_waiting_on_current: {summarize(blocked)}\n\n"
        "## Generation Status\n\n"
        "- handoff_status: ready for continued development\n"
        f"- process_version: {workflow.get('process_version', 7)}\n"
        f"- parallel_mode: {workflow.get('parallel_mode', 'sequential')}\n"
        f"- pending_process_verification: {'true' if workflow.get('pending_process_verification') is True else 'false'}\n"
        f"- bootstrap_status: {bootstrap_status}\n"
        f"- bootstrap_proof: {bootstrap_proof}\n\n"
        "## Post-Generation Audit Status\n\n"
        f"- audit_or_repair_follow_up: {'follow-up required' if reopened or suspect_done or reverification else 'none recorded'}\n"
        f"- reopened_tickets: {summarize(reopened)}\n"
        f"- done_but_not_fully_trusted: {summarize(suspect_done)}\n"
        f"- pending_reverification: {summarize(reverification)}\n\n"
        "## Known Risks\n\n"
        f"{chr(10).join(risk_lines)}\n\n"
        "## Next Action\n\n"
        f"{recommended_action}\n"
        f"{START_HERE_MANAGED_END}\n"
    )


def render_context_snapshot(manifest: dict[str, Any], workflow: dict[str, Any]) -> str:
    ticket = get_active_ticket(manifest, workflow)
    if not isinstance(ticket, dict):
        return "# Context Snapshot\n"

    bootstrap = workflow.get("bootstrap") if isinstance(workflow.get("bootstrap"), dict) else {}
    ticket_state = get_ticket_state(workflow, str(ticket.get("id", "")))
    lane_leases = workflow.get("lane_leases") if isinstance(workflow.get("lane_leases"), list) else []
    if lane_leases:
        lease_lines = "\n".join(
            f"- {lease.get('ticket_id')}: {lease.get('owner_agent')} ({lease.get('lane')})"
            for lease in lane_leases
            if isinstance(lease, dict)
        )
    else:
        lease_lines = "- No active lane leases"
    artifacts = ticket.get("artifacts") if isinstance(ticket.get("artifacts"), list) else []
    if artifacts:
        recent_artifacts = []
        for artifact in artifacts[-5:]:
            if not isinstance(artifact, dict):
                continue
            summary = f" - {artifact.get('summary')}" if artifact.get("summary") else ""
            trust = f" [{artifact.get('trust_state')}]" if artifact.get("trust_state") not in {None, "current"} else ""
            recent_artifacts.append(f"- {artifact.get('kind')}: {artifact.get('path')} ({artifact.get('stage')}){trust}{summary}")
        artifact_lines = "\n".join(recent_artifacts) if recent_artifacts else "- No artifacts recorded yet"
    else:
        artifact_lines = "- No artifacts recorded yet"

    return (
        "# Context Snapshot\n\n"
        "## Project\n\n"
        f"{manifest.get('project', 'Project')}\n\n"
        "## Active Ticket\n\n"
        f"- ID: {ticket.get('id')}\n"
        f"- Title: {ticket.get('title')}\n"
        f"- Stage: {ticket.get('stage')}\n"
        f"- Status: {ticket.get('status')}\n"
        f"- Resolution: {ticket.get('resolution_state')}\n"
        f"- Verification: {ticket.get('verification_state')}\n"
        f"- Approved plan: {'yes' if ticket_state.get('approved_plan') is True else 'no'}\n"
        f"- Needs reverification: {'yes' if ticket_state.get('needs_reverification') is True else 'no'}\n\n"
        "## Bootstrap\n\n"
        f"- status: {bootstrap.get('status', 'missing')}\n"
        f"- last_verified_at: {bootstrap.get('last_verified_at') or 'Not yet verified.'}\n"
        f"- proof_artifact: {bootstrap.get('proof_artifact') or 'None'}\n\n"
        "## Process State\n\n"
        f"- process_version: {workflow.get('process_version', 7)}\n"
        f"- pending_process_verification: {'true' if workflow.get('pending_process_verification') is True else 'false'}\n"
        f"- parallel_mode: {workflow.get('parallel_mode', 'sequential')}\n"
        f"- state_revision: {workflow.get('state_revision', 0)}\n\n"
        "## Lane Leases\n\n"
        f"{lease_lines}\n\n"
        "## Recent Artifacts\n\n"
        f"{artifact_lines}\n"
    )


def refresh_restart_surfaces(repo_root: Path) -> None:
    regenerate_restart_surfaces(
        repo_root,
        reason="Deterministic Scafforge restart-surface refresh.",
        source="scafforge-repair",
        verification_passed=False,
    )


def update_workflow_state(repo_root: Path, rendered_provenance: dict[str, Any], change_summary: str) -> None:
    workflow_path = repo_root / ".opencode" / "state" / "workflow-state.json"
    manifest = read_json(repo_root / "tickets" / "manifest.json")
    workflow = read_json(workflow_path)

    manifest_active_ticket = None
    manifest_stage = "planning"
    manifest_status = "todo"
    if isinstance(manifest, dict):
        raw_active = manifest.get("active_ticket")
        if isinstance(raw_active, str) and raw_active.strip():
            manifest_active_ticket = raw_active.strip()
        tickets = manifest.get("tickets")
        if isinstance(tickets, list) and manifest_active_ticket:
            for ticket in tickets:
                if not isinstance(ticket, dict):
                    continue
                if ticket.get("id") == manifest_active_ticket:
                    if isinstance(ticket.get("stage"), str) and ticket["stage"].strip():
                        manifest_stage = ticket["stage"].strip()
                    if isinstance(ticket.get("status"), str) and ticket["status"].strip():
                        manifest_status = ticket["status"].strip()
                    break

    existing_active_ticket = workflow.get("active_ticket") if isinstance(workflow, dict) else None
    active_ticket = existing_active_ticket if isinstance(existing_active_ticket, str) and existing_active_ticket.strip() else manifest_active_ticket or "UNKNOWN"
    stage = workflow.get("stage") if isinstance(workflow, dict) and isinstance(workflow.get("stage"), str) and workflow.get("stage").strip() else manifest_stage
    status = workflow.get("status") if isinstance(workflow, dict) and isinstance(workflow.get("status"), str) and workflow.get("status").strip() else manifest_status
    ticket_state = normalize_ticket_state_map(workflow.get("ticket_state") if isinstance(workflow, dict) else None)
    legacy_approved_plan = workflow.get("approved_plan") if isinstance(workflow, dict) and isinstance(workflow.get("approved_plan"), bool) else False
    if isinstance(active_ticket, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", active_ticket) and active_ticket not in ticket_state:
        ticket_state[active_ticket] = {
            "approved_plan": legacy_approved_plan,
            "reopen_count": 0,
            "needs_reverification": False,
        }
    approved_plan = ticket_state.get(active_ticket, {}).get("approved_plan", legacy_approved_plan)
    existing_bootstrap = workflow.get("bootstrap") if isinstance(workflow, dict) and isinstance(workflow.get("bootstrap"), dict) else {}
    existing_lane_leases = workflow.get("lane_leases") if isinstance(workflow, dict) and isinstance(workflow.get("lane_leases"), list) else []
    existing_state_revision = workflow.get("state_revision") if isinstance(workflow, dict) and isinstance(workflow.get("state_revision"), int) and workflow.get("state_revision") >= 0 else 0
    bootstrap_status = existing_bootstrap.get("status")
    if bootstrap_status not in {"missing", "ready", "stale", "failed"}:
        bootstrap_status = "missing"

    workflow_contract = rendered_provenance.get("workflow_contract", {}) if isinstance(rendered_provenance, dict) else {}
    process_version = workflow_contract.get("process_version", 7)
    changed_at = current_iso_timestamp()
    payload = {
        "active_ticket": active_ticket,
        "stage": stage,
        "status": status,
        "approved_plan": approved_plan,
        "ticket_state": ticket_state,
        "process_version": process_version,
        "process_last_changed_at": changed_at,
        "process_last_change_summary": change_summary,
        "pending_process_verification": True,
        "parallel_mode": workflow_contract.get("parallel_mode", "sequential"),
        "repair_follow_on": {
            "outcome": "managed_blocked",
            "required_stages": [],
            "completed_stages": [],
            "asserted_completed_stages": [],
            "stage_completion_mode": "transitional_manual_assertion",
            "blocking_reasons": [
                "Managed repair refreshed workflow surfaces. Run the full scafforge-repair follow-on flow before resuming normal ticket lifecycle execution."
            ],
            "verification_passed": False,
            "handoff_allowed": False,
            "last_updated_at": changed_at,
            "process_version": process_version,
        },
        "bootstrap": {
            "status": bootstrap_status,
            "last_verified_at": existing_bootstrap.get("last_verified_at"),
            "environment_fingerprint": existing_bootstrap.get("environment_fingerprint"),
            "proof_artifact": existing_bootstrap.get("proof_artifact"),
        },
        "lane_leases": existing_lane_leases,
        "state_revision": existing_state_revision,
    }
    write_json(workflow_path, payload)


def update_provenance(
    repo_root: Path,
    rendered_root: Path,
    replaced_surfaces: list[str],
    change_summary: str,
) -> None:
    provenance_path = repo_root / ".opencode" / "meta" / "bootstrap-provenance.json"
    existing = read_json(provenance_path)
    rendered = read_json(rendered_root / ".opencode" / "meta" / "bootstrap-provenance.json")
    payload = rendered if isinstance(rendered, dict) else {}
    history = existing.get("repair_history") if isinstance(existing, dict) and isinstance(existing.get("repair_history"), list) else []
    payload["repair_history"] = [
        *history,
        {
            "repaired_at": current_iso_timestamp(),
            "repair_kind": "deterministic-workflow-engine-replacement",
            "repair_package_commit": current_package_commit(),
            "summary": change_summary,
            "replaced_surfaces": replaced_surfaces,
            "project_specific_follow_up": (
                payload.get("managed_surfaces", {}).get("project_specific_follow_up", [])
                if isinstance(payload.get("managed_surfaces"), dict)
                else []
            ),
        },
    ]
    write_json(provenance_path, payload)


def apply_repair(repo_root: Path, rendered_root: Path, change_summary: str) -> list[str]:
    replaced_surfaces: list[str] = []

    replace_file(rendered_root / "opencode.jsonc", repo_root / "opencode.jsonc")
    replaced_surfaces.append("opencode.jsonc")

    for relative in (".opencode/tools", ".opencode/lib", ".opencode/plugins", ".opencode/commands"):
        replace_directory(rendered_root / relative, repo_root / relative)
        replaced_surfaces.append(relative)

    rendered_skills_root = rendered_root / ".opencode" / "skills"
    target_skills_root = repo_root / ".opencode" / "skills"
    target_skills_root.mkdir(parents=True, exist_ok=True)
    for skill_dir in sorted(rendered_skills_root.iterdir()):
        if not skill_dir.is_dir():
            continue
        replace_directory(skill_dir, target_skills_root / skill_dir.name)
    replaced_surfaces.append("scaffold-managed .opencode/skills")

    for filename in DETERMINISTIC_PROCESS_DOCS:
        replace_file(rendered_root / "docs" / "process" / filename, repo_root / "docs" / "process" / filename)
        replaced_surfaces.append(f"docs/process/{filename}")

    rendered_start_here = (rendered_root / "START-HERE.md").read_text(encoding="utf-8")
    target_start_here_path = repo_root / "START-HERE.md"
    existing_start_here = target_start_here_path.read_text(encoding="utf-8") if target_start_here_path.exists() else ""
    target_start_here_path.write_text(merge_start_here(existing_start_here, rendered_start_here), encoding="utf-8")
    replaced_surfaces.append("START-HERE.md managed block")

    (repo_root / ".opencode" / "state" / "bootstrap").mkdir(parents=True, exist_ok=True)

    update_provenance(repo_root, rendered_root, replaced_surfaces, change_summary)
    update_workflow_state(repo_root, read_json(rendered_root / ".opencode" / "meta" / "bootstrap-provenance.json"), change_summary)
    regenerate_restart_surfaces(
        repo_root,
        reason=change_summary,
        source="scafforge-repair",
        verification_passed=False,
    )
    replaced_surfaces.append(".opencode/state/context-snapshot.md")
    replaced_surfaces.append(".opencode/state/latest-handoff.md")
    return replaced_surfaces


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    metadata = load_metadata(repo_root, args)

    with tempfile.TemporaryDirectory(prefix="scafforge-repair-") as temp_dir:
        rendered_root = Path(temp_dir) / "rendered"
        run_bootstrap_render(rendered_root, metadata, args.stack_label)
        replaced_surfaces = apply_repair(repo_root, rendered_root, args.change_summary)

    repair_basis = resolve_repair_basis(repo_root, args.repair_basis_diagnosis)
    logs = verification_logs(repo_root, args.supporting_log, repair_basis)
    findings = [] if args.skip_verify else audit_repo(repo_root, logs=logs)
    verification_passed = False if args.skip_verify else not findings
    verification_next_action = None
    if args.skip_verify:
        verification_next_action = "Run scafforge-audit before relying on this restart narrative for continued development."
    elif not verification_passed:
        verification_next_action = "Resolve the post-repair audit findings, then rerun scafforge-audit before treating the repo as ready for continued development."
    regenerate_restart_surfaces(
        repo_root,
        reason=args.change_summary,
        source="scafforge-repair",
        next_action=verification_next_action,
        verification_passed=verification_passed,
    )
    pending_process_verification = load_pending_process_verification(repo_root)
    managed_surface_findings = [finding for finding in findings if finding.code.startswith(("WFLOW", "BOOT", "MODEL", "SKILL", "CYCLE"))]
    environment_findings = [finding for finding in findings if finding.code.startswith("ENV")]
    source_findings = [finding for finding in findings if finding.code.startswith("EXEC")]
    process_follow_up_findings = [finding for finding in findings if finding.code in {"WFLOW008", "WFLOW009"}]
    stale_surface_map = build_stale_surface_map(repo_root, replaced_surfaces, findings, pending_process_verification)
    payload = {
        "repo_root": str(repo_root),
        "replaced_surfaces": replaced_surfaces,
        "stale_surface_map": stale_surface_map,
        "verification": {
            "performed": not args.skip_verify,
            "finding_count": len(findings),
            "error_count": sum(1 for finding in findings if finding.severity == "error"),
            "warning_count": sum(1 for finding in findings if finding.severity == "warning"),
            "managed_surface_finding_count": len(managed_surface_findings),
            "environment_finding_count": len(environment_findings),
            "source_follow_up_count": len(source_findings),
            "process_follow_up_count": len(process_follow_up_findings),
            "supporting_log_count": len(logs),
            "pending_process_verification": pending_process_verification,
            "verification_passed": verification_passed,
            "clean": not findings and not pending_process_verification,
        },
    }
    if logs:
        payload["verification"]["supporting_logs"] = [str(path) for path in logs]
    print(json.dumps(payload, indent=2))

    if args.skip_verify:
        return 0
    if args.fail_on == "warning" and findings:
        return 2
    if args.fail_on == "error" and any(finding.severity == "error" for finding in findings):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
