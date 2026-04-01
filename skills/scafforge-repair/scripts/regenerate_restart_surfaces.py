from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def render_start_here(
    manifest: dict[str, Any],
    workflow: dict[str, Any],
    *,
    backlog_verifier_agent: str | None = None,
    verification_passed: bool | None = None,
    next_action: str | None = None,
    pivot_state: dict[str, Any] | None = None,
) -> str:
    ticket = get_active_ticket(manifest, workflow)
    if not isinstance(ticket, dict):
        return "# START HERE\n"

    tickets = manifest.get("tickets") if isinstance(manifest.get("tickets"), list) else []
    reopened = [item for item in tickets if isinstance(item, dict) and item.get("resolution_state") == "reopened"]
    verification_state = process_verification_state(manifest, workflow, str(ticket.get("id", "")))
    suspect_done = verification_state["done_but_not_fully_trusted"]
    reverification = [
        item
        for item in tickets
        if isinstance(item, dict) and get_ticket_state(workflow, str(item.get("id", ""))).get("needs_reverification") is True
    ]
    blocked = blocked_dependents(manifest, str(ticket.get("id", "")))
    split_children = open_split_scope_children(manifest, str(ticket.get("id", "")))
    bootstrap = workflow.get("bootstrap") if isinstance(workflow.get("bootstrap"), dict) else {}
    bootstrap_status = str(bootstrap.get("status", "")).strip() or "missing"
    bootstrap_proof = bootstrap.get("proof_artifact") if isinstance(bootstrap.get("proof_artifact"), str) and bootstrap.get("proof_artifact") else "None"
    repair_follow_on = load_repair_follow_on(workflow)
    repair_follow_on_pending = has_pending_repair_follow_on(workflow, verification_passed)
    source_follow_up_pending = repair_follow_on["outcome"] == "source_follow_up"
    repair_follow_on_next_stage = next_repair_follow_on_stage(workflow) or "none"
    pivot = pivot_state or {
        "pivot_state_path": str(PIVOT_STATE_PATH).replace("\\", "/"),
        "tracking_mode": "none",
        "restart_surface_inputs": empty_pivot_restart_surface_inputs(),
    }
    pivot_inputs = pivot.get("restart_surface_inputs") if isinstance(pivot.get("restart_surface_inputs"), dict) else empty_pivot_restart_surface_inputs()
    pivot_pending = pivot_inputs.get("pivot_in_progress") is True
    active_ticket_needs_reconciliation = ticket_needs_historical_reconciliation(ticket)
    active_ticket_trust_needs_restoration = ticket_needs_trust_restoration(ticket, workflow)
    # managed_blocked must take priority over trust-restoration short-circuits.
    # Only return "workflow verification pending" for ticket-level trust issues when
    # repair follow-on is NOT blocking; otherwise fall through to compute_handoff_status
    # so the "repair follow-up required" state is correctly reflected.
    _repair_follow_on_pending = has_pending_repair_follow_on(workflow, verification_passed)
    handoff_status = (
        "pivot follow-up required"
        if pivot_pending
        else
        "workflow verification pending"
        if (active_ticket_needs_reconciliation or active_ticket_trust_needs_restoration) and not _repair_follow_on_pending
        else compute_handoff_status(workflow, verification_passed, pivot_inputs=pivot_inputs)
    )
    recommended_action = next_action or default_next_action(
        manifest,
        workflow,
        backlog_verifier_agent,
        verification_passed,
        pivot_inputs=pivot_inputs,
    )

    risk_lines: list[str] = []
    if bootstrap_status != "ready":
        risk_lines.append("- Environment validation can fail for setup reasons until bootstrap proof exists.")
    if pivot_pending:
        pending_stages = normalize_string_items(pivot_inputs.get("pending_downstream_stages"))
        if pending_stages:
            risk_lines.append(f"- Pivot follow-up is still in progress: {', '.join(pending_stages)}.")
        else:
            risk_lines.append("- Pivot follow-up is still in progress.")
    pending_lineage = normalize_string_items(pivot_inputs.get("pending_ticket_lineage_actions"))
    if pending_lineage:
        risk_lines.append(f"- Pivot ticket lineage actions remain pending: {', '.join(pending_lineage)}.")
    if repair_follow_on_pending:
        repair_blocker = repair_follow_on_blocker(workflow)
        risk_lines.append(f"- Repair follow-on remains incomplete{': ' + repair_blocker if repair_blocker else '.'}")
    if source_follow_up_pending:
        risk_lines.append("- Managed repair converged, but source-layer follow-up still remains in the ticket graph.")
    if active_ticket_needs_reconciliation:
        risk_lines.append("- Historical lineage remains contradictory until ticket_reconcile repairs the superseded invalidated ticket graph.")
    if active_ticket_trust_needs_restoration or verification_state["pending"]:
        risk_lines.append("- Historical completion should not be treated as fully trusted until pending process verification or explicit reverification is cleared.")
    if verification_state["clearable_now"]:
        risk_lines.append("- The workflow still records pending process verification even though no done tickets remain affected; clear the workflow flag before relying on a clean-state restart narrative.")
    if suspect_done:
        risk_lines.append(f"- Some done tickets are not fully trusted yet: {summarize_ticket_ids(suspect_done)}.")
    if blocked and ticket.get("status") != "done":
        risk_lines.append(f"- Downstream tickets {summarize_ticket_ids(blocked)} remain formally blocked until {ticket.get('id')} reaches done.")
    if split_children and ticket.get("status") != "done":
        risk_lines.append(f"- {ticket.get('id')} is an open split parent; child tickets {summarize_ticket_ids(split_children)} now carry the foreground implementation lanes.")
    if verification_passed is False:
        risk_lines.append("- Post-repair audit verification has not passed yet; derived restart surfaces should remain verification-pending.")
    if not risk_lines:
        risk_lines.append("- None recorded.")

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
        "5. tickets/manifest.json\n"
        "6. tickets/BOARD.md\n\n"
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
        f"- dependent_tickets_waiting_on_current: {summarize_ticket_ids(blocked)}\n"
        f"- split_child_tickets: {summarize_ticket_ids(split_children)}\n\n"
        "## Generation Status\n\n"
        f"- handoff_status: {handoff_status}\n"
        f"- process_version: {workflow.get('process_version', 7)}\n"
        f"- parallel_mode: {workflow.get('parallel_mode', 'sequential')}\n"
        f"- pending_process_verification: {'true' if verification_state['pending'] else 'false'}\n"
        f"- repair_follow_on_outcome: {repair_follow_on['outcome']}\n"
        f"- repair_follow_on_required: {'true' if repair_follow_on_pending else 'false'}\n"
        f"- repair_follow_on_next_stage: {repair_follow_on_next_stage}\n"
        f"- repair_follow_on_verification_passed: {'true' if repair_follow_on['verification_passed'] else 'false'}\n"
        f"- repair_follow_on_updated_at: {repair_follow_on['last_updated_at'] or 'Not yet recorded.'}\n"
        f"- pivot_in_progress: {'true' if pivot_pending else 'false'}\n"
        f"- pivot_class: {pivot_inputs.get('pivot_class') or 'none'}\n"
        f"- pivot_changed_surfaces: {', '.join(normalize_string_items(pivot_inputs.get('pivot_changed_surfaces'))) or 'none'}\n"
        f"- pivot_pending_stages: {', '.join(normalize_string_items(pivot_inputs.get('pending_downstream_stages'))) or 'none'}\n"
        f"- pivot_completed_stages: {', '.join(normalize_string_items(pivot_inputs.get('completed_downstream_stages'))) or 'none'}\n"
        f"- pivot_pending_ticket_lineage_actions: {', '.join(pending_lineage) or 'none'}\n"
        f"- pivot_completed_ticket_lineage_actions: {', '.join(normalize_string_items(pivot_inputs.get('completed_ticket_lineage_actions'))) or 'none'}\n"
        f"- post_pivot_verification_passed: {'true' if pivot_inputs.get('post_pivot_verification_passed') is True else 'false'}\n"
        f"- bootstrap_status: {bootstrap_status}\n"
        f"- bootstrap_proof: {bootstrap_proof}\n\n"
        "## Post-Generation Audit Status\n\n"
        f"- audit_or_repair_follow_up: {'follow-up required' if pivot_pending or repair_follow_on_pending or source_follow_up_pending or reopened or suspect_done or reverification or verification_passed is False or verification_state['clearable_now'] else 'none recorded'}\n"
        f"- reopened_tickets: {summarize_ticket_ids(reopened)}\n"
        f"- done_but_not_fully_trusted: {summarize_ticket_ids(suspect_done)}\n"
        f"- pending_reverification: {summarize_ticket_ids(reverification)}\n"
        f"- repair_follow_on_blockers: {' | '.join(repair_follow_on['blocking_reasons']) if repair_follow_on['blocking_reasons'] else 'none'}\n"
        f"- pivot_pending_stages: {', '.join(normalize_string_items(pivot_inputs.get('pending_downstream_stages'))) or 'none'}\n"
        f"- pivot_pending_ticket_lineage_actions: {', '.join(pending_lineage) or 'none'}\n\n"
        "## Known Risks\n\n"
        f"{chr(10).join(risk_lines)}\n\n"
        "## Next Action\n\n"
        f"{recommended_action}\n"
        f"{START_HERE_MANAGED_END}\n"
    )


def render_context_snapshot(
    manifest: dict[str, Any],
    workflow: dict[str, Any],
    note: str | None = None,
    *,
    pivot_state: dict[str, Any] | None = None,
) -> str:
    ticket = get_active_ticket(manifest, workflow)
    if not isinstance(ticket, dict):
        return "# Context Snapshot\n"

    bootstrap = workflow.get("bootstrap") if isinstance(workflow.get("bootstrap"), dict) else {}
    repair_follow_on = load_repair_follow_on(workflow)
    ticket_state = get_ticket_state(workflow, str(ticket.get("id", "")))
    split_children = open_split_scope_children(manifest, str(ticket.get("id", "")))
    pivot = pivot_state or {
        "pivot_state_path": str(PIVOT_STATE_PATH).replace("\\", "/"),
        "tracking_mode": "none",
        "restart_surface_inputs": empty_pivot_restart_surface_inputs(),
    }
    pivot_inputs = pivot.get("restart_surface_inputs") if isinstance(pivot.get("restart_surface_inputs"), dict) else empty_pivot_restart_surface_inputs()
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
            trust = f" [{artifact.get('trust_state')}]" if artifact.get("trust_state") not in {None, 'current'} else ""
            recent_artifacts.append(f"- {artifact.get('kind')}: {artifact.get('path')} ({artifact.get('stage')}){trust}{summary}")
        artifact_lines = "\n".join(recent_artifacts) if recent_artifacts else "- No artifacts recorded yet"
    else:
        artifact_lines = "- No artifacts recorded yet"
    note_block = f"\n## Note\n\n{note}\n" if isinstance(note, str) and note.strip() else ""

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
        f"- Needs reverification: {'yes' if ticket_state.get('needs_reverification') is True else 'no'}\n"
        f"- Open split children: {summarize_ticket_ids(split_children)}\n\n"
        "## Bootstrap\n\n"
        f"- status: {bootstrap.get('status', 'missing')}\n"
        f"- last_verified_at: {bootstrap.get('last_verified_at') or 'Not yet verified.'}\n"
        f"- proof_artifact: {bootstrap.get('proof_artifact') or 'None'}\n\n"
        "## Process State\n\n"
        f"- process_version: {workflow.get('process_version', 7)}\n"
        f"- pending_process_verification: {'true' if workflow.get('pending_process_verification') is True else 'false'}\n"
        f"- parallel_mode: {workflow.get('parallel_mode', 'sequential')}\n"
        f"- state_revision: {workflow.get('state_revision', 0)}\n\n"
        "## Repair Follow-On\n\n"
        f"- outcome: {repair_follow_on['outcome']}\n"
        f"- required: {'yes' if has_pending_repair_follow_on(workflow, verification_passed=None) else 'no'}\n"
        f"- next_required_stage: {next_repair_follow_on_stage(workflow) or 'none'}\n"
        f"- verification_passed: {'true' if repair_follow_on['verification_passed'] else 'false'}\n"
        f"- last_updated_at: {repair_follow_on['last_updated_at'] or 'Not yet recorded.'}\n\n"
        "## Pivot State\n\n"
        f"- pivot_in_progress: {'true' if pivot_inputs.get('pivot_in_progress') is True else 'false'}\n"
        f"- pivot_class: {pivot_inputs.get('pivot_class') or 'none'}\n"
        f"- pivot_changed_surfaces: {', '.join(normalize_string_items(pivot_inputs.get('pivot_changed_surfaces'))) or 'none'}\n"
        f"- pending_downstream_stages: {', '.join(normalize_string_items(pivot_inputs.get('pending_downstream_stages'))) or 'none'}\n"
        f"- completed_downstream_stages: {', '.join(normalize_string_items(pivot_inputs.get('completed_downstream_stages'))) or 'none'}\n"
        f"- pending_ticket_lineage_actions: {', '.join(normalize_string_items(pivot_inputs.get('pending_ticket_lineage_actions'))) or 'none'}\n"
        f"- completed_ticket_lineage_actions: {', '.join(normalize_string_items(pivot_inputs.get('completed_ticket_lineage_actions'))) or 'none'}\n"
        f"- post_pivot_verification_passed: {'true' if pivot_inputs.get('post_pivot_verification_passed') is True else 'false'}\n"
        f"- pivot_state_path: {pivot.get('pivot_state_path') or str(PIVOT_STATE_PATH).replace('\\\\', '/')}\n"
        f"- pivot_tracking_mode: {pivot.get('tracking_mode') or 'none'}\n\n"
        "## Lane Leases\n\n"
        f"{lease_lines}\n\n"
        "## Recent Artifacts\n\n"
        f"{artifact_lines}{note_block}"
    )


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
    manifest = read_json(repo_root / "tickets" / "manifest.json")
    workflow = read_json(repo_root / ".opencode" / "state" / "workflow-state.json")
    provenance = read_json(repo_root / ".opencode" / "meta" / "bootstrap-provenance.json")
    pivot_state = load_pivot_state(repo_root)
    if not isinstance(manifest, dict) or not isinstance(workflow, dict):
        raise SystemExit("Cannot regenerate restart surfaces without tickets/manifest.json and .opencode/state/workflow-state.json.")
    if not isinstance(provenance, dict):
        provenance = {}

    backlog_verifier_agent = load_backlog_verifier_agent(provenance)
    rendered_start_here = render_start_here(
        manifest,
        workflow,
        backlog_verifier_agent=backlog_verifier_agent,
        verification_passed=verification_passed,
        next_action=next_action,
        pivot_state=pivot_state,
    )
    start_here_path = repo_root / "START-HERE.md"
    write_text(start_here_path, merge_start_here(read_text(start_here_path), rendered_start_here))
    write_text(
        repo_root / ".opencode" / "state" / "context-snapshot.md",
        render_context_snapshot(manifest, workflow, context_note, pivot_state=pivot_state),
    )
    write_text(repo_root / ".opencode" / "state" / "latest-handoff.md", rendered_start_here)

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
