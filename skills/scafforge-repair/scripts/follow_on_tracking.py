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
    "project-skill-bootstrap": ".opencode/state/artifacts/history/repair/project-skill-bootstrap-completion.md",
    "opencode-team-bootstrap": ".opencode/state/artifacts/history/repair/opencode-team-bootstrap-completion.md",
    "agent-prompt-engineering": ".opencode/state/artifacts/history/repair/agent-prompt-engineering-completion.md",
    "ticket-pack-builder": ".opencode/state/artifacts/history/repair/ticket-pack-builder-completion.md",
    "handoff-brief": ".opencode/state/artifacts/history/repair/handoff-brief-completion.md",
}
AUTO_DETECTED_COMPLETERS = {
    "project-skill-bootstrap": "project-skill-bootstrap:auto-detected",
    "opencode-team-bootstrap": "opencode-team-bootstrap:auto-detected",
    "agent-prompt-engineering": "agent-prompt-engineering:auto-detected",
    "ticket-pack-builder": "ticket-pack-builder:auto-detected",
    "handoff-brief": "handoff-brief:auto-detected",
}
OPTIONAL_RECORDABLE_FOLLOW_ON_STAGES = {"handoff-brief"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def current_iso_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def known_follow_on_stage_names() -> list[str]:
    return sorted(FOLLOW_ON_STAGE_CATALOG)


def follow_on_stage_metadata(stage: str) -> dict[str, str]:
    normalized = validate_follow_on_stage_name(stage)
    metadata = FOLLOW_ON_STAGE_CATALOG[normalized]
    return {
        "stage": normalized,
        "owner": str(metadata["owner"]),
        "category": str(metadata["category"]),
    }


def follow_on_stage_history_metadata(stage: str) -> dict[str, str]:
    metadata = follow_on_stage_metadata(stage)
    return {
        "stage": metadata["stage"],
        "owner": metadata["owner"],
        "category": metadata["category"],
    }


def validate_stage_allowed_for_current_cycle(state: dict[str, Any], stage: str) -> str:
    normalized = validate_follow_on_stage_name(stage)
    required_stages = {
        item.strip()
        for item in (state.get("required_stages") if isinstance(state.get("required_stages"), list) else [])
        if isinstance(item, str) and item.strip()
    }
    if normalized in required_stages or normalized in OPTIONAL_RECORDABLE_FOLLOW_ON_STAGES:
        return normalized
    allowed = sorted(required_stages | OPTIONAL_RECORDABLE_FOLLOW_ON_STAGES)
    allowed_display = ", ".join(allowed) if allowed else "none"
    raise ValueError(
        f"Repair follow-on stage `{normalized}` is not part of the current repair cycle. "
        f"Allowed stages for this cycle: {allowed_display}"
    )


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
    raw_required_stages = payload.get("required_stages", []) if isinstance(payload.get("required_stages"), list) else []
    pruned_unknown_stages = sorted(
        {
            stage.strip()
            for stage in raw_required_stages
            if isinstance(stage, str) and stage.strip() and stage.strip() not in FOLLOW_ON_STAGE_CATALOG
        }
        | {
            stage.strip()
            for stage, value in stage_records.items()
            if isinstance(stage, str) and stage.strip() and isinstance(value, dict) and stage.strip() not in FOLLOW_ON_STAGE_CATALOG
        }
        | {
            str(item.get("stage")).strip()
            for item in history
            if isinstance(item, dict)
            and isinstance(item.get("stage"), str)
            and str(item.get("stage")).strip()
            and str(item.get("stage")).strip() not in FOLLOW_ON_STAGE_CATALOG
        }
    )
    return {
        "tracking_mode": "persistent_recorded_state",
        "assertion_input_mode": "transitional_manual_assertion",
        "cycle_id": payload.get("cycle_id") if isinstance(payload.get("cycle_id"), str) and payload.get("cycle_id").strip() else timestamp,
        "created_at": payload.get("created_at") if isinstance(payload.get("created_at"), str) and payload.get("created_at").strip() else timestamp,
        "last_updated_at": payload.get("last_updated_at") if isinstance(payload.get("last_updated_at"), str) and payload.get("last_updated_at").strip() else timestamp,
        "process_version": process_version,
        "repair_package_commit": payload.get("repair_package_commit"),
        "repair_basis_path": payload.get("repair_basis_path"),
        "pruned_unknown_stages": pruned_unknown_stages,
        "required_stages": sorted(
            {
                stage.strip()
                for stage in raw_required_stages
                if isinstance(stage, str) and stage.strip() in FOLLOW_ON_STAGE_CATALOG
            }
        ),
        "stage_records": {
            validate_follow_on_stage_name(stage): {
                **value,
                **follow_on_stage_metadata(stage),
            }
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
    if state.get("pruned_unknown_stages"):
        history = state.get("history") if isinstance(state.get("history"), list) else []
        history.append(
            {
                "recorded_at": current_iso_timestamp(),
                "status": "pruned_unknown_stages",
                "pruned_unknown_stages": state["pruned_unknown_stages"],
                "cycle_id": state.get("cycle_id"),
            }
        )
        state["history"] = history
        state["last_updated_at"] = current_iso_timestamp()
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
        missing_recorded_evidence = not evidence_paths
        cycle_id = state.get("cycle_id") if isinstance(state.get("cycle_id"), str) else ""
        canonical_evidence_path = canonical_stage_evidence_path(stage)
        canonical_cycle_mismatch = False
        if canonical_evidence_path and canonical_evidence_path in evidence_paths and cycle_id:
            canonical_cycle_mismatch = not artifact_matches_current_cycle(repo_root, stage=stage, cycle_id=cycle_id)[0]
        missing = [
            path
            for path in evidence_paths
            if not isinstance(path, str) or not (repo_root / path).exists()
        ]
        if not missing and not missing_recorded_evidence and not canonical_cycle_mismatch:
            continue
        previous_missing = record.get("missing_evidence_paths") if isinstance(record.get("missing_evidence_paths"), list) else []
        evidence_validation_error = (
            "missing_recorded_evidence"
            if missing_recorded_evidence
            else "canonical_evidence_cycle_mismatch"
            if canonical_cycle_mismatch
            else None
        )
        stage_records[stage] = {
            **record,
            "status": "evidence_missing",
            "missing_evidence_paths": sorted(set(path for path in missing if isinstance(path, str))),
            "evidence_validation_error": evidence_validation_error,
            "last_checked_at": now,
            "last_updated_at": now,
        }
        current_missing = sorted(set(path for path in missing if isinstance(path, str)))
        previous_error = record.get("evidence_validation_error")
        if (
            current_missing != sorted(set(path for path in previous_missing if isinstance(path, str)))
            or evidence_validation_error != previous_error
        ):
            history.append(
                {
                    "recorded_at": now,
                    **follow_on_stage_history_metadata(stage),
                    "status": "evidence_missing",
                    "missing_evidence_paths": current_missing,
                    "evidence_validation_error": evidence_validation_error,
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
        stage_records[stage] = {
            **next_record,
            **follow_on_stage_metadata(stage),
        }

    for stage, reason in required_reason_map.items():
        existing = stage_records.get(stage, {})
        if existing.get("status") in {"asserted_completed", "completed"}:
            stage_records[stage] = {
                **existing,
                **follow_on_stage_metadata(stage),
                "stage": stage,
                "reason": reason,
                "currently_required": True,
                "last_checked_at": now,
            }
            continue
        if existing.get("status") == "evidence_missing":
            stage_records[stage] = {
                **existing,
                **follow_on_stage_metadata(stage),
                "stage": stage,
                "reason": reason,
                "currently_required": True,
                "last_checked_at": now,
            }
            continue
        stage_records[stage] = {
            **follow_on_stage_metadata(stage),
            "stage": stage,
            "status": "required_not_run",
            "reason": reason,
            "currently_required": True,
            "last_checked_at": now,
            "last_updated_at": now,
        }

    for stage in asserted_stage_names:
        validate_stage_allowed_for_current_cycle(state, stage)
        existing = stage_records.get(stage, {})
        if existing.get("status") == "completed":
            stage_records[stage] = {
                **existing,
                **follow_on_stage_metadata(stage),
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
            **follow_on_stage_metadata(stage),
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
                **follow_on_stage_history_metadata(stage),
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
    state: dict[str, Any],
    *,
    required_stage_names: list[str],
    repair_package_commit: str,
) -> tuple[dict[str, Any], list[str]]:
    candidate_stage_names = normalize_follow_on_stage_names(
        required_stage_names
        + [stage for stage in OPTIONAL_RECORDABLE_FOLLOW_ON_STAGES if canonical_stage_evidence_path(stage)]
    )
    state = validate_recorded_execution_evidence(repo_root, state)
    persist_follow_on_tracking_state(repo_root, state)

    auto_recorded: list[str] = []
    cycle_id = state.get("cycle_id") if isinstance(state.get("cycle_id"), str) else ""
    if not cycle_id:
        return state, auto_recorded

    for stage in candidate_stage_names:
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
    stage = validate_stage_allowed_for_current_cycle(state, stage)
    normalized_completed_by = completed_by.strip()
    if not normalized_completed_by:
        raise ValueError(
            f"Repair follow-on stage `{stage}` requires a non-empty completed_by value for recorded execution."
        )
    normalized_summary = summary.strip()
    if not normalized_summary:
        raise ValueError(
            f"Repair follow-on stage `{stage}` requires a non-empty summary for recorded execution."
        )
    if not any(isinstance(path, str) and path.strip() for path in evidence_paths):
        raise ValueError(
            f"Repair follow-on stage `{stage}` requires at least one repo-relative evidence path for recorded execution."
        )
    canonical_evidence_path = canonical_stage_evidence_path(stage)
    if canonical_evidence_path and canonical_evidence_path in evidence_paths:
        cycle_id = state.get("cycle_id") if isinstance(state.get("cycle_id"), str) else ""
        matches_cycle, _ = artifact_matches_current_cycle(repo_root, stage=stage, cycle_id=cycle_id)
        if not matches_cycle:
            raise ValueError(
                f"Canonical repair evidence for `{stage}` must match the current repair cycle before recorded execution can be accepted."
            )
    records = state["stage_records"]
    now = current_iso_timestamp()
    existing = records.get(stage, {})
    reason = existing.get("reason")
    records[stage] = {
        **existing,
        **follow_on_stage_metadata(stage),
        "stage": stage,
        "status": "completed",
        "currently_required": existing.get("currently_required", False),
        "reason": reason,
        "completion_mode": "recorded_execution",
        "completed_by": normalized_completed_by,
        "summary": normalized_summary,
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
            **follow_on_stage_history_metadata(stage),
            "status": "completed",
            "completion_mode": "recorded_execution",
            "completed_by": normalized_completed_by,
            "summary": normalized_summary,
            "evidence_paths": evidence_paths,
            "repair_package_commit": repair_package_commit,
            "cycle_id": state["cycle_id"],
        }
    )
    persist_follow_on_tracking_state(repo_root, state)
    return state
