from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PIVOT_STATE_PATH = Path(".opencode/meta/pivot-state.json")
DEFAULT_PIVOT_STATE_OWNER = "scafforge-pivot"

PIVOT_STAGE_CATALOG = {
    "project-skill-bootstrap": {
        "owner": "project-skill-bootstrap",
        "category": "repo_local_skills",
    },
    "opencode-team-bootstrap": {
        "owner": "opencode-team-bootstrap",
        "category": "agent_team",
    },
    "agent-prompt-engineering": {
        "owner": "agent-prompt-engineering",
        "category": "prompt_hardening",
    },
    "ticket-pack-builder": {
        "owner": "ticket-pack-builder",
        "category": "ticket_follow_up",
    },
    "scafforge-repair": {
        "owner": "scafforge-repair",
        "category": "managed_workflow_refresh",
    },
}

TICKET_LINEAGE_ACTION_TYPES = {
    "supersede",
    "reopen",
    "reconcile",
    "create_follow_up",
}

LINEAGE_ACTION_STATUSES = {
    "planned",
    "completed",
}


def current_iso_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def validate_pivot_stage_name(stage: str) -> str:
    normalized = stage.strip()
    if normalized in PIVOT_STAGE_CATALOG:
        return normalized
    known = ", ".join(sorted(PIVOT_STAGE_CATALOG))
    raise ValueError(f"Unknown pivot downstream stage: {stage}. Known stages: {known}")


def pivot_stage_metadata(stage: str) -> dict[str, str]:
    normalized = validate_pivot_stage_name(stage)
    metadata = PIVOT_STAGE_CATALOG[normalized]
    return {
        "stage": normalized,
        "owner": str(metadata["owner"]),
        "category": str(metadata["category"]),
    }


def normalize_pivot_stage_names(stages: list[str]) -> list[str]:
    return sorted({validate_pivot_stage_name(stage) for stage in stages if isinstance(stage, str) and stage.strip()})


def validate_ticket_lineage_action_type(action_type: str) -> str:
    normalized = action_type.strip()
    if normalized in TICKET_LINEAGE_ACTION_TYPES:
        return normalized
    known = ", ".join(sorted(TICKET_LINEAGE_ACTION_TYPES))
    raise ValueError(f"Unknown pivot ticket lineage action: {action_type}. Known actions: {known}")


def normalize_ticket_lineage_status(value: Any) -> str:
    return str(value).strip() if str(value).strip() in LINEAGE_ACTION_STATUSES else "planned"


def summarize_ticket_lineage_action(action: dict[str, Any]) -> str:
    action_type = validate_ticket_lineage_action_type(str(action.get("action", "")))
    raw_target_ticket_id = action.get("target_ticket_id")
    target_ticket_id = raw_target_ticket_id.strip() if isinstance(raw_target_ticket_id, str) and raw_target_ticket_id.strip() else ""
    summary = str(action.get("summary", "")).strip()
    if target_ticket_id:
        return f"{action_type}:{target_ticket_id}"
    if summary:
        return f"{action_type}:{summary}"
    return action_type


def normalize_ticket_lineage_plan(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        value = {}
    actions_raw = value.get("actions") if isinstance(value.get("actions"), list) else []
    history = value.get("history") if isinstance(value.get("history"), list) else []
    normalized_actions: list[dict[str, Any]] = []
    for item in actions_raw:
        if not isinstance(item, dict):
            continue
        action_type = validate_ticket_lineage_action_type(str(item.get("action", "")))
        raw_target_ticket_id = item.get("target_ticket_id")
        target_ticket_id = raw_target_ticket_id.strip() if isinstance(raw_target_ticket_id, str) and raw_target_ticket_id.strip() else None
        summary = str(item.get("summary", "")).strip()
        reason = str(item.get("reason", "")).strip()
        evidence_artifact_path = str(item.get("evidence_artifact_path", "")).strip() or None
        replacement_source_ticket_id = str(item.get("replacement_source_ticket_id", "")).strip() or None
        replacement_source_mode = str(item.get("replacement_source_mode", "")).strip() or None
        ticket_spec = item.get("ticket_spec") if isinstance(item.get("ticket_spec"), dict) else None
        label = summarize_ticket_lineage_action(
            {
                "action": action_type,
                "target_ticket_id": target_ticket_id,
                "summary": summary,
            }
        )
        normalized_actions.append(
            {
                "action": action_type,
                "target_ticket_id": target_ticket_id,
                "summary": summary,
                "reason": reason,
                "label": label,
                "status": normalize_ticket_lineage_status(item.get("status")),
                "completion_mode": str(item.get("completion_mode", "")).strip() or None,
                "completed_by": str(item.get("completed_by", "")).strip() or None,
                "execution_summary": str(item.get("execution_summary", "")).strip() or None,
                "execution_result": item.get("execution_result") if isinstance(item.get("execution_result"), dict) else None,
                "last_updated_at": str(item.get("last_updated_at", "")).strip() or None,
                "evidence_artifact_path": evidence_artifact_path,
                "replacement_source_ticket_id": replacement_source_ticket_id,
                "replacement_source_mode": replacement_source_mode,
                "ticket_spec": ticket_spec,
            }
        )
    return {
        "actions": normalized_actions,
        "history": history,
        "pending_actions": [item["label"] for item in normalized_actions if item["status"] != "completed"],
        "completed_actions": [item["label"] for item in normalized_actions if item["status"] == "completed"],
    }


def build_downstream_refresh_state(
    downstream_refresh: list[dict[str, str]],
    *,
    pivot_id: str,
    recorded_at: str,
) -> dict[str, Any]:
    normalized_refresh = []
    stage_records: dict[str, dict[str, Any]] = {}
    history: list[dict[str, Any]] = []
    for item in downstream_refresh:
        stage = validate_pivot_stage_name(str(item.get("stage", "")))
        reason = str(item.get("reason", "")).strip()
        normalized_item = {
            **item,
            **pivot_stage_metadata(stage),
            "reason": reason,
        }
        normalized_refresh.append(normalized_item)
        stage_records[stage] = {
            **pivot_stage_metadata(stage),
            "status": "required_not_run",
            "reason": reason,
            "completion_mode": None,
            "evidence_paths": [],
            "last_updated_at": recorded_at,
        }
        history.append(
            {
                "recorded_at": recorded_at,
                **pivot_stage_metadata(stage),
                "status": "planned",
                "reason": reason,
                "pivot_id": pivot_id,
            }
        )
    required_stages = [item["stage"] for item in normalized_refresh]
    return {
        "tracking_mode": "persistent_recorded_state",
        "pivot_id": pivot_id,
        "required_stage_details": normalized_refresh,
        "required_stages": required_stages,
        "pending_stages": list(required_stages),
        "completed_stages": [],
        "stage_records": stage_records,
        "history": history,
        "last_updated_at": recorded_at,
    }


def completed_pivot_stage_names(payload: dict[str, Any]) -> list[str]:
    downstream_state = payload.get("downstream_refresh_state")
    if not isinstance(downstream_state, dict):
        return []
    stage_records = downstream_state.get("stage_records")
    if not isinstance(stage_records, dict):
        return []
    return sorted(
        stage
        for stage, record in stage_records.items()
        if isinstance(stage, str)
        and isinstance(record, dict)
        and record.get("status") == "completed"
    )


def pending_pivot_stage_names(payload: dict[str, Any]) -> list[str]:
    downstream_state = payload.get("downstream_refresh_state")
    if not isinstance(downstream_state, dict):
        return []
    required = downstream_state.get("required_stages")
    required_stages = (
        [validate_pivot_stage_name(stage) for stage in required if isinstance(stage, str) and stage.strip()]
        if isinstance(required, list)
        else []
    )
    completed = set(completed_pivot_stage_names(payload))
    return [stage for stage in required_stages if stage not in completed]


def synchronize_lineage_with_ticket_pack_builder(payload: dict[str, Any]) -> None:
    downstream_state = payload.get("downstream_refresh_state") if isinstance(payload.get("downstream_refresh_state"), dict) else {}
    lineage_plan = payload.get("ticket_lineage_plan") if isinstance(payload.get("ticket_lineage_plan"), dict) else {}
    if not isinstance(downstream_state, dict) or not isinstance(lineage_plan, dict):
        return
    stage_records = downstream_state.get("stage_records") if isinstance(downstream_state.get("stage_records"), dict) else {}
    ticket_stage = stage_records.get("ticket-pack-builder") if isinstance(stage_records.get("ticket-pack-builder"), dict) else None
    actions = lineage_plan.get("actions") if isinstance(lineage_plan.get("actions"), list) else []
    if not ticket_stage or ticket_stage.get("status") != "completed" or not actions:
        return
    if any(isinstance(action, dict) and action.get("status") == "completed" for action in actions):
        return
    now = str(ticket_stage.get("last_updated_at") or current_iso_timestamp())
    for action in actions:
        if not isinstance(action, dict):
            continue
        action["status"] = "completed"
        action["completion_mode"] = "downstream_stage_completion"
        action["completed_by"] = str(ticket_stage.get("completed_by") or "ticket-pack-builder")
        action["execution_summary"] = str(ticket_stage.get("summary") or "Ticket lineage work completed through ticket-pack-builder.")
        action["last_updated_at"] = now
    history = lineage_plan.get("history") if isinstance(lineage_plan.get("history"), list) else []
    history.append(
        {
            "recorded_at": now,
            "event": "ticket-pack-builder:completed",
            "summary": "All explicit pivot lineage actions were satisfied by ticket-pack-builder stage completion.",
        }
    )
    lineage_plan["history"] = history


def build_restart_surface_inputs(payload: dict[str, Any]) -> dict[str, Any]:
    stale_surface_map = payload.get("stale_surface_map") if isinstance(payload.get("stale_surface_map"), dict) else {}
    verification_status = payload.get("verification_status") if isinstance(payload.get("verification_status"), dict) else {}
    pending = pending_pivot_stage_names(payload)
    completed = completed_pivot_stage_names(payload)
    ticket_lineage_plan = normalize_ticket_lineage_plan(payload.get("ticket_lineage_plan"))
    pending_ticket_lineage_actions = list(ticket_lineage_plan["pending_actions"])
    completed_ticket_lineage_actions = list(ticket_lineage_plan["completed_actions"])
    return {
        "pivot_in_progress": bool(pending) or verification_status.get("verification_passed") is not True,
        "pivot_class": payload.get("pivot_class"),
        "pivot_changed_surfaces": sorted(
            key
            for key, entry in stale_surface_map.items()
            if isinstance(key, str)
            and isinstance(entry, dict)
            and entry.get("status") != "stable"
        ),
        "pending_downstream_stages": pending,
        "completed_downstream_stages": completed,
        "pending_ticket_lineage_actions": pending_ticket_lineage_actions,
        "completed_ticket_lineage_actions": completed_ticket_lineage_actions,
        "post_pivot_verification_passed": verification_status.get("verification_passed") is True,
    }


def normalize_restart_surface_publication(value: Any) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}
    return {
        "status": str(raw.get("status", "")).strip() or "not_published",
        "published_at": str(raw.get("published_at", "")).strip() or None,
        "published_by": str(raw.get("published_by", "")).strip() or None,
        "next_action": str(raw.get("next_action", "")).strip() or None,
        "start_here": str(raw.get("start_here", "")).strip() or None,
        "latest_handoff": str(raw.get("latest_handoff", "")).strip() or None,
        "context_snapshot": str(raw.get("context_snapshot", "")).strip() or None,
    }


def normalize_pivot_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Pivot state payload is missing or invalid.")
    pivot_state_owner = str(payload.get("pivot_state_owner", "")).strip() or DEFAULT_PIVOT_STATE_OWNER
    downstream_state = payload.get("downstream_refresh_state")
    if not isinstance(downstream_state, dict):
        required_details = payload.get("downstream_refresh") if isinstance(payload.get("downstream_refresh"), list) else []
        pivot_id = str(payload.get("pivot_id") or payload.get("pivot_history_entry", {}).get("recorded_at") or current_iso_timestamp())
        recorded_at = str(payload.get("pivot_history_entry", {}).get("recorded_at") or current_iso_timestamp())
        downstream_state = build_downstream_refresh_state(required_details, pivot_id=pivot_id, recorded_at=recorded_at)
    required_details = downstream_state.get("required_stage_details")
    if not isinstance(required_details, list):
        required_details = payload.get("downstream_refresh") if isinstance(payload.get("downstream_refresh"), list) else []
    normalized_details: list[dict[str, Any]] = []
    for item in required_details:
        if not isinstance(item, dict):
            continue
        stage = validate_pivot_stage_name(str(item.get("stage", "")))
        normalized_details.append(
            {
                **item,
                **pivot_stage_metadata(stage),
                "reason": str(item.get("reason", "")).strip(),
            }
        )
    downstream_state["required_stage_details"] = normalized_details
    downstream_state["required_stages"] = [item["stage"] for item in normalized_details]
    stage_records = downstream_state.get("stage_records") if isinstance(downstream_state.get("stage_records"), dict) else {}
    normalized_records: dict[str, dict[str, Any]] = {}
    for stage in downstream_state["required_stages"]:
        existing = stage_records.get(stage) if isinstance(stage_records, dict) else {}
        reason = next((item["reason"] for item in normalized_details if item["stage"] == stage), "")
        normalized_records[stage] = {
            **(existing if isinstance(existing, dict) else {}),
            **pivot_stage_metadata(stage),
            "reason": reason,
            "status": existing.get("status") if isinstance(existing, dict) and existing.get("status") in {"required_not_run", "completed"} else "required_not_run",
            "completion_mode": existing.get("completion_mode") if isinstance(existing, dict) else None,
            "evidence_paths": existing.get("evidence_paths") if isinstance(existing, dict) and isinstance(existing.get("evidence_paths"), list) else [],
            "completed_by": existing.get("completed_by") if isinstance(existing, dict) else None,
            "summary": existing.get("summary") if isinstance(existing, dict) else None,
            "last_updated_at": existing.get("last_updated_at") if isinstance(existing, dict) and isinstance(existing.get("last_updated_at"), str) else downstream_state.get("last_updated_at"),
        }
    downstream_state["stage_records"] = normalized_records
    downstream_state["completed_stages"] = completed_pivot_stage_names({"downstream_refresh_state": downstream_state})
    downstream_state["pending_stages"] = pending_pivot_stage_names({"downstream_refresh_state": downstream_state})
    downstream_state["history"] = downstream_state.get("history") if isinstance(downstream_state.get("history"), list) else []
    payload["downstream_refresh_state"] = downstream_state
    payload["pivot_state_owner"] = pivot_state_owner
    payload["ticket_lineage_plan"] = normalize_ticket_lineage_plan(payload.get("ticket_lineage_plan"))
    synchronize_lineage_with_ticket_pack_builder(payload)
    payload["ticket_lineage_plan"] = normalize_ticket_lineage_plan(payload.get("ticket_lineage_plan"))
    payload["restart_surface_publication"] = normalize_restart_surface_publication(payload.get("restart_surface_publication"))
    payload["restart_surface_inputs"] = build_restart_surface_inputs(payload)
    return payload


def load_pivot_state(repo_root: Path) -> dict[str, Any]:
    state_path = repo_root / PIVOT_STATE_PATH
    payload = normalize_pivot_payload(read_json(state_path))
    write_json(state_path, payload)
    return payload


def persist_pivot_state(repo_root: Path, payload: dict[str, Any]) -> None:
    normalized = normalize_pivot_payload(payload)
    write_json(repo_root / PIVOT_STATE_PATH, normalized)


def ensure_ticket_pack_builder_completion(payload: dict[str, Any], *, completed_by: str, summary: str) -> None:
    downstream_state = payload.get("downstream_refresh_state")
    if not isinstance(downstream_state, dict):
        return
    required_stages = downstream_state.get("required_stages") if isinstance(downstream_state.get("required_stages"), list) else []
    if "ticket-pack-builder" not in required_stages:
        return
    lineage_plan = payload.get("ticket_lineage_plan") if isinstance(payload.get("ticket_lineage_plan"), dict) else {}
    actions = lineage_plan.get("actions") if isinstance(lineage_plan.get("actions"), list) else []
    if any(isinstance(action, dict) and action.get("status") != "completed" for action in actions):
        return
    now = current_iso_timestamp()
    existing = downstream_state["stage_records"].get("ticket-pack-builder", {})
    if existing.get("status") == "completed":
        return
    downstream_state["stage_records"]["ticket-pack-builder"] = {
        **existing,
        **pivot_stage_metadata("ticket-pack-builder"),
        "status": "completed",
        "completion_mode": "pivot_lineage_execution",
        "completed_by": completed_by.strip(),
        "summary": summary.strip(),
        "evidence_paths": sorted(
            {
                str(action.get("evidence_artifact_path", "")).strip()
                for action in actions
                if isinstance(action, dict) and str(action.get("evidence_artifact_path", "")).strip()
            }
        ),
        "last_updated_at": now,
    }
    history = downstream_state.get("history") if isinstance(downstream_state.get("history"), list) else []
    history.append(
        {
            "recorded_at": now,
            **pivot_stage_metadata("ticket-pack-builder"),
            "status": "completed",
            "completion_mode": "pivot_lineage_execution",
            "completed_by": completed_by.strip(),
            "summary": summary.strip(),
            "pivot_id": downstream_state.get("pivot_id"),
        }
    )
    downstream_state["history"] = history
    downstream_state["last_updated_at"] = now
    payload["downstream_refresh_state"] = downstream_state


def record_ticket_lineage_action_completion(
    repo_root: Path,
    *,
    label: str,
    completed_by: str,
    summary: str,
    execution_result: dict[str, Any],
) -> dict[str, Any]:
    payload = load_pivot_state(repo_root)
    lineage_plan = payload["ticket_lineage_plan"]
    actions = lineage_plan["actions"]
    target_action = next((item for item in actions if item.get("label") == label), None)
    if not isinstance(target_action, dict):
        raise ValueError(f"Pivot ticket lineage action not found: {label}")
    now = current_iso_timestamp()
    target_action["status"] = "completed"
    target_action["completion_mode"] = "generated_tool_execution"
    target_action["completed_by"] = completed_by.strip()
    target_action["execution_summary"] = summary.strip()
    target_action["execution_result"] = execution_result
    target_action["last_updated_at"] = now
    history = lineage_plan.get("history") if isinstance(lineage_plan.get("history"), list) else []
    history.append(
        {
            "recorded_at": now,
            "event": "ticket_lineage_action:completed",
            "label": label,
            "completed_by": completed_by.strip(),
            "summary": summary.strip(),
        }
    )
    lineage_plan["history"] = history
    payload["ticket_lineage_plan"] = lineage_plan
    ensure_ticket_pack_builder_completion(
        payload,
        completed_by=completed_by,
        summary="Explicit pivot lineage actions completed through generated repo ticket tools.",
    )
    payload["restart_surface_inputs"] = build_restart_surface_inputs(payload)
    persist_pivot_state(repo_root, payload)
    return payload


def record_pivot_stage_completion(
    repo_root: Path,
    *,
    stage: str,
    completed_by: str,
    summary: str,
    evidence_paths: list[str],
) -> dict[str, Any]:
    payload = load_pivot_state(repo_root)
    downstream_state = payload["downstream_refresh_state"]
    normalized_stage = validate_pivot_stage_name(stage)
    if normalized_stage not in downstream_state.get("required_stages", []):
        allowed = ", ".join(downstream_state.get("required_stages", [])) or "none"
        raise ValueError(
            f"Pivot downstream stage `{normalized_stage}` is not part of the current pivot plan. "
            f"Allowed stages for this pivot: {allowed}"
        )
    if not evidence_paths:
        raise ValueError("Pivot downstream recorded execution requires at least one repo-relative evidence path.")
    if not completed_by.strip():
        raise ValueError("Pivot downstream recorded execution requires a non-empty completed_by value.")
    if not summary.strip():
        raise ValueError("Pivot downstream recorded execution requires a non-empty summary.")
    now = current_iso_timestamp()
    existing = downstream_state["stage_records"].get(normalized_stage, {})
    downstream_state["stage_records"][normalized_stage] = {
        **existing,
        **pivot_stage_metadata(normalized_stage),
        "status": "completed",
        "completion_mode": "recorded_execution",
        "completed_by": completed_by.strip(),
        "summary": summary.strip(),
        "evidence_paths": sorted(set(path for path in evidence_paths if isinstance(path, str) and path.strip())),
        "last_updated_at": now,
    }
    downstream_state["history"].append(
        {
            "recorded_at": now,
            **pivot_stage_metadata(normalized_stage),
            "status": "completed",
            "completion_mode": "recorded_execution",
            "completed_by": completed_by.strip(),
            "summary": summary.strip(),
            "evidence_paths": sorted(set(path for path in evidence_paths if isinstance(path, str) and path.strip())),
            "pivot_id": downstream_state.get("pivot_id"),
        }
    )
    downstream_state["last_updated_at"] = now
    payload["downstream_refresh_state"] = downstream_state
    payload["restart_surface_inputs"] = build_restart_surface_inputs(payload)
    persist_pivot_state(repo_root, payload)
    return payload
