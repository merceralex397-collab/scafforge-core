from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apply_repo_process_repair import FOLLOW_ON_TRACKING_PATH

FOLLOW_ON_STAGE_CATALOG = {
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
    "handoff-brief": {
        "owner": "handoff-brief",
        "category": "restart_surface",
    },
}
CANONICAL_STAGE_EVIDENCE = {
    "ticket-pack-builder": ".opencode/state/artifacts/history/repair/ticket-pack-builder-completion.md",
}
AUTO_DETECTED_COMPLETERS = {
    "ticket-pack-builder": "ticket-pack-builder:auto-detected",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def current_iso_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def known_follow_on_stage_names() -> list[str]:
    return sorted(FOLLOW_ON_STAGE_CATALOG)


def validate_follow_on_stage_name(stage: str) -> str:
    normalized = stage.strip()
    if normalized in FOLLOW_ON_STAGE_CATALOG:
        return normalized
    known = ", ".join(known_follow_on_stage_names())
    raise ValueError(f"Unknown repair follow-on stage: {stage}. Known stages: {known}")


def normalize_follow_on_stage_names(stages: list[str]) -> list[str]:
    return sorted({validate_follow_on_stage_name(stage) for stage in stages if isinstance(stage, str) and stage.strip()})


def normalize_follow_on_tracking_state(payload: Any, *, process_version: int) -> dict[str, Any]:
    if not isinstance(payload, dict):
        payload = {}
    stage_records = payload.get("stage_records") if isinstance(payload.get("stage_records"), dict) else {}
    history = payload.get("history") if isinstance(payload.get("history"), list) else []
    timestamp = current_iso_timestamp()
    return {
        "tracking_mode": "persistent_recorded_state",
        "assertion_input_mode": "transitional_manual_assertion",
        "cycle_id": payload.get("cycle_id") if isinstance(payload.get("cycle_id"), str) and payload.get("cycle_id").strip() else timestamp,
        "created_at": payload.get("created_at") if isinstance(payload.get("created_at"), str) and payload.get("created_at").strip() else timestamp,
        "last_updated_at": payload.get("last_updated_at") if isinstance(payload.get("last_updated_at"), str) and payload.get("last_updated_at").strip() else timestamp,
        "process_version": process_version,
        "repair_package_commit": payload.get("repair_package_commit"),
        "repair_basis_path": payload.get("repair_basis_path"),
        "required_stages": sorted(
            {
                stage.strip()
                for stage in (payload.get("required_stages", []) if isinstance(payload.get("required_stages"), list) else [])
                if isinstance(stage, str) and stage.strip() in FOLLOW_ON_STAGE_CATALOG
            }
        ),
        "stage_records": {
            validate_follow_on_stage_name(stage): value
            for stage, value in stage_records.items()
            if isinstance(stage, str) and isinstance(value, dict) and stage.strip() in FOLLOW_ON_STAGE_CATALOG
        },
        "history": [
            item
            for item in history
            if isinstance(item, dict)
            and (
                not isinstance(item.get("stage"), str)
                or item.get("stage", "").strip() in FOLLOW_ON_STAGE_CATALOG
            )
        ],
    }


def load_follow_on_tracking_state(repo_root: Path) -> dict[str, Any]:
    workflow = read_json(repo_root / ".opencode" / "state" / "workflow-state.json")
    process_version = workflow.get("process_version") if isinstance(workflow, dict) and isinstance(workflow.get("process_version"), int) and workflow.get("process_version") > 0 else 7
    tracking_path = repo_root / FOLLOW_ON_TRACKING_PATH
    state = normalize_follow_on_tracking_state(read_json(tracking_path), process_version=process_version)
    write_json(tracking_path, state)
    return state


def persist_follow_on_tracking_state(repo_root: Path, state: dict[str, Any]) -> None:
    write_json(repo_root / FOLLOW_ON_TRACKING_PATH, state)


def canonical_stage_evidence_path(stage: str) -> str | None:
    value = CANONICAL_STAGE_EVIDENCE.get(stage)
    return value if isinstance(value, str) and value else None


def validate_recorded_execution_evidence(repo_root: Path, state: dict[str, Any]) -> dict[str, Any]:
    stage_records = state.get("stage_records") if isinstance(state.get("stage_records"), dict) else {}
    history = state.get("history") if isinstance(state.get("history"), list) else []
    now = current_iso_timestamp()
    for stage, record in list(stage_records.items()):
        if not isinstance(stage, str) or not isinstance(record, dict):
            continue
        if record.get("status") != "completed" or record.get("completion_mode") != "recorded_execution":
            continue
        evidence_paths = record.get("evidence_paths") if isinstance(record.get("evidence_paths"), list) else []
        missing = [
            path
            for path in evidence_paths
            if not isinstance(path, str) or not (repo_root / path).exists()
        ]
        if not missing:
            continue
        previous_missing = record.get("missing_evidence_paths") if isinstance(record.get("missing_evidence_paths"), list) else []
        stage_records[stage] = {
            **record,
            "status": "evidence_missing",
            "missing_evidence_paths": sorted(set(path for path in missing if isinstance(path, str))),
            "last_checked_at": now,
            "last_updated_at": now,
        }
        if sorted(set(path for path in missing if isinstance(path, str))) != sorted(set(path for path in previous_missing if isinstance(path, str))):
            history.append(
                {
                    "recorded_at": now,
                    "stage": stage,
                    "status": "evidence_missing",
                    "missing_evidence_paths": sorted(set(path for path in missing if isinstance(path, str))),
                    "cycle_id": state.get("cycle_id"),
                }
            )
    state["history"] = history
    state["last_updated_at"] = now
    return state


def artifact_matches_current_cycle(repo_root: Path, *, stage: str, cycle_id: str) -> tuple[bool, str | None]:
    evidence_path = canonical_stage_evidence_path(stage)
    if not evidence_path:
        return False, None
    path = repo_root / evidence_path
    if not path.exists():
        return False, evidence_path
    text = path.read_text(encoding="utf-8")
    if f"- completed_stage: {stage}" not in text:
        return False, evidence_path
    if f"- cycle_id: {cycle_id}" not in text:
        return False, evidence_path
    return True, evidence_path


def update_follow_on_tracking_state(
    repo_root: Path,
    *,
    required_follow_on: list[dict[str, str]],
    asserted_stage_names: list[str],
    repair_basis_path: Path | None,
    repair_package_commit: str,
) -> dict[str, Any]:
    asserted_stage_names = normalize_follow_on_stage_names(asserted_stage_names)
    required_follow_on = [
        {
            **item,
            "stage": validate_follow_on_stage_name(str(item.get("stage", ""))),
        }
        for item in required_follow_on
    ]
    state = load_follow_on_tracking_state(repo_root)
    state = validate_recorded_execution_evidence(repo_root, state)
    stage_records = state["stage_records"]
    required_reason_map = {item["stage"]: item["reason"] for item in required_follow_on}
    now = current_iso_timestamp()
    state["last_updated_at"] = now
    state["repair_package_commit"] = repair_package_commit
    state["repair_basis_path"] = str(repair_basis_path) if repair_basis_path else None
    state["required_stages"] = [item["stage"] for item in required_follow_on]

    for stage, record in list(stage_records.items()):
        next_record = dict(record)
        next_record["currently_required"] = stage in required_reason_map
        if stage in required_reason_map:
            next_record["reason"] = required_reason_map[stage]
        stage_records[stage] = next_record

    for stage, reason in required_reason_map.items():
        existing = stage_records.get(stage, {})
        if existing.get("status") in {"asserted_completed", "completed"}:
            stage_records[stage] = {
                **existing,
                "stage": stage,
                "reason": reason,
                "currently_required": True,
                "last_checked_at": now,
            }
            continue
        if existing.get("status") == "evidence_missing":
            stage_records[stage] = {
                **existing,
                "stage": stage,
                "reason": reason,
                "currently_required": True,
                "last_checked_at": now,
            }
            continue
        stage_records[stage] = {
            "stage": stage,
            "status": "required_not_run",
            "reason": reason,
            "currently_required": True,
            "last_checked_at": now,
            "last_updated_at": now,
        }

    for stage in asserted_stage_names:
        existing = stage_records.get(stage, {})
        if existing.get("status") == "completed":
            stage_records[stage] = {
                **existing,
                "stage": stage,
                "currently_required": stage in required_reason_map,
                "last_checked_at": now,
            }
            continue
        first_recorded_at = existing.get("first_recorded_at") if isinstance(existing.get("first_recorded_at"), str) and existing.get("first_recorded_at").strip() else now
        assertion_count = existing.get("assertion_count") if isinstance(existing.get("assertion_count"), int) and existing.get("assertion_count") >= 0 else 0
        reason = required_reason_map.get(stage)
        stage_records[stage] = {
            **existing,
            "stage": stage,
            "status": "asserted_completed",
            "reason": reason,
            "currently_required": stage in required_reason_map,
            "completion_mode": "transitional_manual_assertion",
            "first_recorded_at": first_recorded_at,
            "last_recorded_at": now,
            "last_checked_at": now,
            "last_updated_at": now,
            "assertion_count": assertion_count + 1,
        }
        state["history"].append(
            {
                "recorded_at": now,
                "stage": stage,
                "status": "asserted_completed",
                "completion_mode": "transitional_manual_assertion",
                "reason": reason,
                "repair_basis_path": str(repair_basis_path) if repair_basis_path else None,
                "repair_package_commit": repair_package_commit,
                "cycle_id": state["cycle_id"],
            }
        )

    persist_follow_on_tracking_state(repo_root, state)
    return state


def auto_record_stage_completion_from_canonical_evidence(
    repo_root: Path,
    *,
    required_stage_names: list[str],
    repair_package_commit: str,
) -> tuple[dict[str, Any], list[str]]:
    required_stage_names = normalize_follow_on_stage_names(required_stage_names)
    state = load_follow_on_tracking_state(repo_root)
    state = validate_recorded_execution_evidence(repo_root, state)
    persist_follow_on_tracking_state(repo_root, state)

    auto_recorded: list[str] = []
    cycle_id = state.get("cycle_id") if isinstance(state.get("cycle_id"), str) else ""
    if not cycle_id:
        return state, auto_recorded

    for stage in required_stage_names:
        evidence_path = canonical_stage_evidence_path(stage)
        if not evidence_path:
            continue
        existing = state.get("stage_records", {}).get(stage, {})
        if (
            isinstance(existing, dict)
            and existing.get("status") == "completed"
            and existing.get("completion_mode") == "recorded_execution"
            and evidence_path in (existing.get("evidence_paths") if isinstance(existing.get("evidence_paths"), list) else [])
        ):
            continue
        matches_cycle, detected_path = artifact_matches_current_cycle(repo_root, stage=stage, cycle_id=cycle_id)
        if not matches_cycle or not detected_path:
            continue
        state = record_follow_on_stage_completion(
            repo_root,
            stage=stage,
            completed_by=AUTO_DETECTED_COMPLETERS.get(stage, f"{stage}:auto-detected"),
            summary=f"Auto-detected canonical {stage} repair follow-on completion for cycle {cycle_id}.",
            evidence_paths=[detected_path],
            repair_package_commit=repair_package_commit,
        )
        auto_recorded.append(stage)
    return state, sorted(set(auto_recorded))


def completed_stage_names(state: dict[str, Any]) -> list[str]:
    records = state.get("stage_records") if isinstance(state.get("stage_records"), dict) else {}
    return sorted(
        stage
        for stage, record in records.items()
        if isinstance(stage, str) and isinstance(record, dict) and record.get("status") in {"asserted_completed", "completed"}
    )


def recorded_execution_stage_names(state: dict[str, Any]) -> list[str]:
    records = state.get("stage_records") if isinstance(state.get("stage_records"), dict) else {}
    return sorted(
        stage
        for stage, record in records.items()
        if isinstance(stage, str) and isinstance(record, dict) and record.get("status") == "completed"
    )


def invalidated_recorded_stage_names(state: dict[str, Any]) -> list[str]:
    records = state.get("stage_records") if isinstance(state.get("stage_records"), dict) else {}
    return sorted(
        stage
        for stage, record in records.items()
        if isinstance(stage, str) and isinstance(record, dict) and record.get("status") == "evidence_missing"
    )


def record_follow_on_stage_completion(
    repo_root: Path,
    *,
    stage: str,
    completed_by: str,
    summary: str,
    evidence_paths: list[str],
    repair_package_commit: str,
) -> dict[str, Any]:
    stage = validate_follow_on_stage_name(stage)
    state = load_follow_on_tracking_state(repo_root)
    records = state["stage_records"]
    now = current_iso_timestamp()
    existing = records.get(stage, {})
    reason = existing.get("reason")
    records[stage] = {
        **existing,
        "stage": stage,
        "status": "completed",
        "currently_required": existing.get("currently_required", False),
        "reason": reason,
        "completion_mode": "recorded_execution",
        "completed_by": completed_by,
        "summary": summary,
        "evidence_paths": evidence_paths,
        "first_recorded_at": existing.get("first_recorded_at") if isinstance(existing.get("first_recorded_at"), str) and existing.get("first_recorded_at").strip() else now,
        "last_recorded_at": now,
        "last_checked_at": now,
        "last_updated_at": now,
    }
    state["last_updated_at"] = now
    state["repair_package_commit"] = repair_package_commit
    state["history"].append(
        {
            "recorded_at": now,
            "stage": stage,
            "status": "completed",
            "completion_mode": "recorded_execution",
            "completed_by": completed_by,
            "summary": summary,
            "evidence_paths": evidence_paths,
            "repair_package_commit": repair_package_commit,
            "cycle_id": state["cycle_id"],
        }
    )
    persist_follow_on_tracking_state(repo_root, state)
    return state
