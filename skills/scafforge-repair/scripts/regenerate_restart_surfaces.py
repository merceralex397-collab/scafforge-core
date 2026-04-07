from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

RUNTIME_SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scafforge-pivot" / "scripts"
if str(RUNTIME_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SCRIPT_DIR))

from shared_generated_tool_runtime import run_generated_tool


START_HERE_MANAGED_START = "<!-- SCAFFORGE:START_HERE_BLOCK START -->"
START_HERE_MANAGED_END = "<!-- SCAFFORGE:START_HERE_BLOCK END -->"
REGENERATED_SURFACES = [
    "START-HERE.md",
    ".opencode/state/context-snapshot.md",
    ".opencode/state/latest-handoff.md",
]
PIVOT_STATE_PATH = Path(".opencode/meta/pivot-state.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deterministically regenerate Scafforge restart surfaces from canonical repo state.")
    parser.add_argument("repo_root", help="Repository root whose restart surfaces should be regenerated.")
    parser.add_argument("--reason", default="Deterministic Scafforge restart-surface regeneration.", help="Why the restart surfaces are being regenerated.")
    parser.add_argument("--source", default="scafforge-repair", help="Repair or workflow source performing the regeneration.")
    parser.add_argument("--next-action", help="Optional explicit next action override.")
    parser.add_argument("--context-note", help="Optional note appended to the context snapshot.")
    parser.add_argument("--verification-passed", action="store_true", help="Mark that post-repair audit verification passed for this regeneration pass.")
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


def current_iso_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def merge_start_here(existing: str, rendered: str) -> str:
    pattern = re.compile(rf"{re.escape(START_HERE_MANAGED_START)}[\s\S]*?{re.escape(START_HERE_MANAGED_END)}", re.MULTILINE)
    rendered_match = pattern.search(rendered)
    if not rendered_match:
        return rendered
    if not existing.strip():
        return rendered
    start_index = existing.find(START_HERE_MANAGED_START)
    end_index = existing.find(START_HERE_MANAGED_END)
    if start_index == -1 and end_index == -1:
        return existing
    if start_index != -1 and end_index == -1:
        prefix = existing[:start_index].rstrip()
        return f"{prefix}\n\n{rendered_match.group(0)}\n" if prefix else f"{rendered_match.group(0)}\n"
    if start_index == -1 and end_index != -1:
        suffix = existing[end_index + len(START_HERE_MANAGED_END):].lstrip("\r\n")
        return f"{rendered_match.group(0)}\n\n{suffix}" if suffix else rendered_match.group(0)
    return pattern.sub(rendered_match.group(0), existing, count=1)


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


def open_split_scope_children(manifest: dict[str, Any], ticket_id: str) -> list[dict[str, Any]]:
    tickets = manifest.get("tickets") if isinstance(manifest.get("tickets"), list) else []
    children: list[dict[str, Any]] = []
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        if str(ticket.get("source_ticket_id", "")).strip() != ticket_id:
            continue
        if str(ticket.get("source_mode", "")).strip() != "split_scope":
            continue
        if ticket.get("status") == "done":
            continue
        if str(ticket.get("resolution_state", "open")).strip() not in {"open", "reopened"}:
            continue
        children.append(ticket)
    return children


def summarize_ticket_ids(items: list[dict[str, Any]]) -> str:
    values = [str(item.get("id", "")).strip() for item in items if isinstance(item, dict) and str(item.get("id", "")).strip()]
    return ", ".join(values) if values else "none"


def dependent_continuation_action(ticket: dict[str, Any], blocked: list[dict[str, Any]]) -> str:
    next_dependent = next((item for item in blocked if isinstance(item, dict) and str(item.get("id", "")).strip()), None)
    if not isinstance(next_dependent, dict):
        return "Continue the required internal lifecycle from the current ticket stage."
    return (
        f"Current ticket is already closed. Activate dependent ticket {next_dependent.get('id')} "
        f"and continue that lane instead of trying to mutate {ticket.get('id')} again."
    )


def normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        stripped = item.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        normalized.append(stripped)
    return normalized


def load_repair_follow_on(workflow: dict[str, Any]) -> dict[str, Any]:
    raw = workflow.get("repair_follow_on") if isinstance(workflow.get("repair_follow_on"), dict) else {}
    outcome = raw.get("outcome") if isinstance(raw.get("outcome"), str) else None
    if outcome not in {"managed_blocked", "source_follow_up", "clean"}:
        required_stages = normalize_string_list(raw.get("required_stages"))
        blocking_reasons = normalize_string_list(raw.get("blocking_reasons"))
        verification_passed = raw.get("verification_passed") is True
        handoff_allowed = raw.get("handoff_allowed") is True
        outcome = "clean" if handoff_allowed and not required_stages and not blocking_reasons and verification_passed else "managed_blocked"
    return {
        "outcome": outcome,
        "required_stages": normalize_string_list(raw.get("required_stages")),
        "completed_stages": normalize_string_list(raw.get("completed_stages")),
        "blocking_reasons": normalize_string_list(raw.get("blocking_reasons")),
        "verification_passed": raw.get("verification_passed") is True,
        "handoff_allowed": raw.get("handoff_allowed") is True,
        "last_updated_at": raw.get("last_updated_at") if isinstance(raw.get("last_updated_at"), str) and raw.get("last_updated_at") else None,
        "process_version": raw.get("process_version") if isinstance(raw.get("process_version"), int) and raw.get("process_version") > 0 else workflow.get("process_version", 7),
    }


def empty_pivot_restart_surface_inputs() -> dict[str, Any]:
    return {
        "pivot_in_progress": False,
        "pivot_class": None,
        "pivot_changed_surfaces": [],
        "pending_downstream_stages": [],
        "completed_downstream_stages": [],
        "pending_ticket_lineage_actions": [],
        "completed_ticket_lineage_actions": [],
        "post_pivot_verification_passed": False,
    }


def normalize_string_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        items.append(normalized)
    return items


def load_pivot_state(repo_root: Path) -> dict[str, Any]:
    path = repo_root / PIVOT_STATE_PATH
    payload = read_json(path)
    if not isinstance(payload, dict):
        return {
            "pivot_state_path": str(PIVOT_STATE_PATH).replace("\\", "/"),
            "tracking_mode": "none",
            "restart_surface_inputs": empty_pivot_restart_surface_inputs(),
        }
    restart_inputs_raw = payload.get("restart_surface_inputs") if isinstance(payload.get("restart_surface_inputs"), dict) else {}
    downstream_state = payload.get("downstream_refresh_state") if isinstance(payload.get("downstream_refresh_state"), dict) else {}
    return {
        "pivot_state_path": str(PIVOT_STATE_PATH).replace("\\", "/"),
        "tracking_mode": str(downstream_state.get("tracking_mode", "")).strip() or "none",
        "restart_surface_inputs": {
            "pivot_in_progress": restart_inputs_raw.get("pivot_in_progress") is True,
            "pivot_class": str(restart_inputs_raw.get("pivot_class", "")).strip() or None,
            "pivot_changed_surfaces": normalize_string_items(restart_inputs_raw.get("pivot_changed_surfaces")),
            "pending_downstream_stages": normalize_string_items(restart_inputs_raw.get("pending_downstream_stages")),
            "completed_downstream_stages": normalize_string_items(restart_inputs_raw.get("completed_downstream_stages")),
            "pending_ticket_lineage_actions": normalize_string_items(restart_inputs_raw.get("pending_ticket_lineage_actions")),
            "completed_ticket_lineage_actions": normalize_string_items(restart_inputs_raw.get("completed_ticket_lineage_actions")),
            "post_pivot_verification_passed": restart_inputs_raw.get("post_pivot_verification_passed") is True,
        },
    }


def has_pending_repair_follow_on(workflow: dict[str, Any], verification_passed: bool | None = None) -> bool:
    repair_follow_on = load_repair_follow_on(workflow)
    effective_verification = repair_follow_on["verification_passed"] if verification_passed is None else verification_passed
    if repair_follow_on["outcome"] == "managed_blocked":
        return True
    if repair_follow_on["outcome"] in {"source_follow_up", "clean"}:
        return False
    return effective_verification is False and bool(repair_follow_on["blocking_reasons"])


def next_repair_follow_on_stage(workflow: dict[str, Any]) -> str | None:
    repair_follow_on = load_repair_follow_on(workflow)
    if repair_follow_on["outcome"] != "managed_blocked":
        return None
    completed = set(repair_follow_on["completed_stages"])
    for stage in repair_follow_on["required_stages"]:
        if stage not in completed:
            return stage
    return None


def repair_follow_on_blocker(workflow: dict[str, Any]) -> str | None:
    repair_follow_on = load_repair_follow_on(workflow)
    if repair_follow_on["outcome"] != "managed_blocked":
        return None
    blockers = repair_follow_on["blocking_reasons"]
    return blockers[0] if blockers else None


def load_backlog_verifier_agent(provenance: dict[str, Any]) -> str | None:
    workflow_contract = provenance.get("workflow_contract") if isinstance(provenance.get("workflow_contract"), dict) else {}
    post_migration = workflow_contract.get("post_migration_verification") if isinstance(workflow_contract.get("post_migration_verification"), dict) else {}
    value = post_migration.get("backlog_verifier_agent")
    return value.strip() if isinstance(value, str) and value.strip() else None


def latest_current_artifact(ticket: dict[str, Any], *, stage: str | None = None, kind: str | None = None) -> dict[str, Any] | None:
    artifacts = ticket.get("artifacts") if isinstance(ticket.get("artifacts"), list) else []
    for artifact in reversed(artifacts):
        if not isinstance(artifact, dict):
            continue
        if artifact.get("trust_state") not in {None, "current"}:
            continue
        if stage is not None and str(artifact.get("stage", "")).strip() != stage:
            continue
        if kind is not None and str(artifact.get("kind", "")).strip() != kind:
            continue
        return artifact
    return None


def ticket_needs_process_verification(ticket: dict[str, Any], workflow: dict[str, Any]) -> bool:
    if workflow.get("pending_process_verification") is not True:
        return False
    if ticket.get("status") != "done":
        return False
    if ticket.get("verification_state") == "reverified":
        return False
    if latest_current_artifact(ticket, stage="review", kind="backlog-verification") is not None:
        return False
    changed_at = workflow.get("process_last_changed_at")
    try:
        changed_dt = datetime.fromisoformat(str(changed_at).replace("Z", "+00:00"))
    except ValueError:
        return True
    completion_artifact = (
        latest_current_artifact(ticket, stage="smoke-test")
        or latest_current_artifact(ticket, stage="qa")
        or latest_current_artifact(ticket)
    )
    if not isinstance(completion_artifact, dict):
        return True
    try:
        completed_dt = datetime.fromisoformat(str(completion_artifact.get("created_at", "")).replace("Z", "+00:00"))
    except ValueError:
        return True
    return completed_dt < changed_dt


def process_verification_state(manifest: dict[str, Any], workflow: dict[str, Any], current_ticket_id: str | None = None) -> dict[str, Any]:
    tickets = manifest.get("tickets") if isinstance(manifest.get("tickets"), list) else []
    affected_done_tickets = [
        ticket
        for ticket in tickets
        if isinstance(ticket, dict) and ticket_needs_process_verification(ticket, workflow)
    ]
    if current_ticket_id is None:
        current_ticket_id = str(workflow.get("active_ticket", "")).strip() or None
    current_ticket = next(
        (
            ticket
            for ticket in tickets
            if isinstance(ticket, dict) and current_ticket_id and str(ticket.get("id", "")).strip() == current_ticket_id
        ),
        None,
    )
    pending = workflow.get("pending_process_verification") is True
    done_but_not_fully_trusted = (
        affected_done_tickets
        if pending
        else [
            ticket
            for ticket in tickets
            if isinstance(ticket, dict)
            and ticket.get("status") == "done"
            and ticket.get("verification_state") not in {"trusted", "reverified"}
        ]
    )
    return {
        "pending": pending,
        "affected_done_tickets": affected_done_tickets,
        "current_ticket_requires_verification": bool(current_ticket and ticket_needs_process_verification(current_ticket, workflow)),
        "clearable_now": pending and not affected_done_tickets,
        "done_but_not_fully_trusted": done_but_not_fully_trusted,
    }


def ticket_needs_trust_restoration(ticket: dict[str, Any], workflow: dict[str, Any]) -> bool:
    ticket_id = str(ticket.get("id", "")).strip()
    if ticket.get("status") != "done" or not ticket_id:
        return False
    if ticket_needs_historical_reconciliation(ticket):
        return False
    if ticket_needs_process_verification(ticket, workflow):
        return True
    return get_ticket_state(workflow, ticket_id).get("needs_reverification") is True


def ticket_needs_historical_reconciliation(ticket: dict[str, Any]) -> bool:
    return (
        ticket.get("status") == "done"
        and ticket.get("resolution_state") == "superseded"
        and ticket.get("verification_state") == "invalidated"
    )


def compute_handoff_status(
    workflow: dict[str, Any],
    verification_passed: bool | None = None,
    *,
    pivot_inputs: dict[str, Any] | None = None,
) -> str:
    bootstrap = workflow.get("bootstrap") if isinstance(workflow.get("bootstrap"), dict) else {}
    bootstrap_status = str(bootstrap.get("status", "")).strip() or "missing"
    pivot_restart_inputs = pivot_inputs or empty_pivot_restart_surface_inputs()
    if bootstrap_status != "ready":
        return "bootstrap recovery required"
    if pivot_restart_inputs.get("pivot_in_progress") is True:
        return "pivot follow-up required"
    if has_pending_repair_follow_on(workflow, verification_passed):
        return "repair follow-up required"
    if verification_passed is False:
        return "workflow verification pending"
    if workflow.get("pending_process_verification") is True:
        return "workflow verification pending"
    return "ready for continued development"


def default_next_action(
    manifest: dict[str, Any],
    workflow: dict[str, Any],
    backlog_verifier_agent: str | None,
    verification_passed: bool | None,
    *,
    pivot_inputs: dict[str, Any] | None = None,
) -> str:
    ticket = get_active_ticket(manifest, workflow)
    if not isinstance(ticket, dict):
        return "Resolve the canonical manifest and workflow-state mismatch before resuming autonomous work."

    verification_state = process_verification_state(manifest, workflow, str(ticket.get("id", "")))
    ticket_needs_reconciliation = ticket_needs_historical_reconciliation(ticket)
    ticket_trust_needs_restoration = ticket_needs_trust_restoration(ticket, workflow)
    bootstrap = workflow.get("bootstrap") if isinstance(workflow.get("bootstrap"), dict) else {}
    bootstrap_status = str(bootstrap.get("status", "")).strip() or "missing"
    blocked = blocked_dependents(manifest, str(ticket.get("id", "")))
    split_children = open_split_scope_children(manifest, str(ticket.get("id", "")))
    verifier_label = f"`{backlog_verifier_agent}`" if backlog_verifier_agent else "the backlog verifier"
    pivot_restart_inputs = pivot_inputs or empty_pivot_restart_surface_inputs()
    pivot_pending_stages = normalize_string_items(pivot_restart_inputs.get("pending_downstream_stages"))
    pivot_pending_lineage = normalize_string_items(pivot_restart_inputs.get("pending_ticket_lineage_actions"))

    if bootstrap_status != "ready":
        return "Run environment_bootstrap, register its proof artifact, rerun ticket_lookup, and do not continue lifecycle work until bootstrap is ready."
    if pivot_restart_inputs.get("pivot_in_progress") is True:
        if pivot_pending_stages:
            stage_text = ", ".join(f"`{item}`" for item in pivot_pending_stages)
            lineage_suffix = f" Ticket lineage actions still pending: {', '.join(pivot_pending_lineage)}." if pivot_pending_lineage else ""
            plurality = "s" if len(pivot_pending_stages) > 1 else ""
            return f"Continue the pivot follow-on stage{plurality} {stage_text} before resuming normal ticket lifecycle work.{lineage_suffix}"
        return "Complete the remaining pivot follow-on work and republish the restart surfaces before resuming normal ticket lifecycle work."
    if has_pending_repair_follow_on(workflow, verification_passed):
        return repair_follow_on_blocker(workflow) or (
            f"Complete the required repair follow-on stage `{next_repair_follow_on_stage(workflow)}` before resuming normal ticket lifecycle work."
            if next_repair_follow_on_stage(workflow)
            else "Complete the required repair follow-on stages before resuming normal ticket lifecycle work."
        )
    if verification_passed is False and workflow.get("pending_process_verification") is not True:
        return "Resolve the post-repair audit blockers and rerun scafforge-audit before treating the restart narrative as ready for continued development."
    if ticket_needs_reconciliation:
        return (
            f"Ticket is already closed, but its historical lineage is still contradictory. Use ticket_reconcile with "
            f"current registered evidence to repair {ticket.get('id')} instead of trying to reopen or reclaim it."
        )
    if ticket_trust_needs_restoration:
        return (
            f"Ticket is already closed, but historical trust still needs restoration. Use {verifier_label} to produce "
            f"current evidence, then run ticket_reverify on {ticket.get('id')} instead of trying to reclaim it."
        )
    if split_children and ticket.get("status") != "done":
        return (
            f"Keep {ticket.get('id')} open as a split parent and continue the child ticket lane"
            f"{'s' if len(split_children) > 1 else ''}: {summarize_ticket_ids(split_children)}."
        )
    if ticket.get("status") != "done":
        return f"Keep {ticket.get('id')} as the foreground ticket and continue its lifecycle from {ticket.get('stage')}. Historical done-ticket reverification stays secondary until the active open ticket is resolved."
    if verification_state["pending"]:
        if verification_state["clearable_now"]:
            return "Use ticket_update to clear pending_process_verification now that no historical done tickets still require process verification, then rerun ticket_lookup."
        return (
            f"Use the team leader to route {verifier_label} across done tickets whose trust predates the current "
            f"process contract: {summarize_ticket_ids(verification_state['affected_done_tickets'])}."
        )
    if blocked:
        return dependent_continuation_action(ticket, blocked)
    return "Continue the required internal lifecycle from the current ticket stage."


def update_restart_surface_provenance(
    repo_root: Path,
    *,
    reason: str,
    source: str,
    verification_passed: bool | None,
) -> None:
    provenance_path = repo_root / ".opencode" / "meta" / "bootstrap-provenance.json"
    payload = read_json(provenance_path)
    if not isinstance(payload, dict):
        payload = {}

    entry: dict[str, Any] = {
        "generated_at": current_iso_timestamp(),
        "source": source,
        "reason": reason,
        "regenerated": list(REGENERATED_SURFACES),
    }
    if verification_passed is True:
        entry["verification"] = "passed"
    elif verification_passed is False:
        entry["verification"] = "pending_or_failed"

    history = payload.get("restart_surface_regeneration_history")
    if not isinstance(history, list):
        history = []
    history.append(entry)
    payload["restart_surface_regeneration_history"] = history
    payload["last_restart_surface_regeneration"] = entry
    write_json(provenance_path, payload)


def regenerate_restart_surfaces(
    repo_root: Path,
    *,
    reason: str,
    source: str,
    next_action: str | None = None,
    context_note: str | None = None,
    verification_passed: bool | None = None,
    update_provenance_entry: bool = True,
) -> dict[str, Any]:
    publication = run_generated_tool(
        repo_root,
        ".opencode/tools/handoff_publish.ts",
        {"next_action": next_action} if isinstance(next_action, str) and next_action.strip() else {},
    )
    manifest = read_json(repo_root / "tickets" / "manifest.json")
    workflow = read_json(repo_root / ".opencode" / "state" / "workflow-state.json")
    pivot_state = load_pivot_state(repo_root)
    provenance = read_json(repo_root / ".opencode" / "meta" / "bootstrap-provenance.json")
    if not isinstance(provenance, dict):
        provenance = {}

    if update_provenance_entry:
        update_restart_surface_provenance(
            repo_root,
            reason=reason,
            source=source,
            verification_passed=verification_passed,
        )

    return {
        "repo_root": str(repo_root),
        "surfaces": list(REGENERATED_SURFACES),
        "publication": publication,
        "handoff_status": compute_handoff_status(
            workflow,
            verification_passed,
            pivot_inputs=pivot_state.get("restart_surface_inputs") if isinstance(pivot_state, dict) else None,
        ),
        "verification_passed": verification_passed,
        "pivot_in_progress": pivot_state.get("restart_surface_inputs", {}).get("pivot_in_progress") is True if isinstance(pivot_state, dict) else False,
    }


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    payload = regenerate_restart_surfaces(
        repo_root,
        reason=args.reason,
        source=args.source,
        next_action=args.next_action,
        context_note=args.context_note,
        verification_passed=True if args.verification_passed else None,
    )
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
