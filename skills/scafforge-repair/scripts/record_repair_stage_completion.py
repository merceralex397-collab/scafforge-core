from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from audit_repo_process import current_package_commit
from apply_repo_process_repair import FOLLOW_ON_TRACKING_PATH
from follow_on_tracking import (
    completed_stage_names,
    invalidated_recorded_stage_names,
    load_follow_on_tracking_state,
    record_follow_on_stage_completion,
    recorded_execution_stage_names,
    validate_follow_on_stage_name,
)
from regenerate_restart_surfaces import regenerate_restart_surfaces


KNOWN_STAGE_BLOCKER_PREFIXES = tuple(
    f"{name} must still run:" for name in (
        "project-skill-bootstrap",
        "opencode-team-bootstrap",
        "agent-prompt-engineering",
        "ticket-pack-builder",
        "handoff-brief",
    )
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record completion of a Scafforge repair follow-on stage in persistent repo metadata."
    )
    parser.add_argument("repo_root", help="Repository root whose repair follow-on stage is being recorded.")
    parser.add_argument("--stage", required=True, help="Follow-on stage that completed, for example project-skill-bootstrap.")
    parser.add_argument("--completed-by", required=True, help="Skill or operator that completed the stage.")
    parser.add_argument("--summary", required=True, help="Short summary of what completed.")
    parser.add_argument(
        "--evidence",
        action="append",
        default=[],
        help=(
            "Repo-relative evidence path supporting completion. "
            "May be provided multiple times. Recorded execution requires at least one repo-relative evidence path."
        ),
    )
    return parser.parse_args()


def normalize_evidence_paths(repo_root: Path, evidence: list[str]) -> list[str]:
    normalized: list[str] = []
    for raw in evidence:
        candidate = Path(raw)
        resolved = candidate if candidate.is_absolute() else (repo_root / candidate)
        resolved = resolved.resolve()
        if not resolved.exists():
            raise SystemExit(f"Evidence path does not exist: {raw}")
        try:
            relative = resolved.relative_to(repo_root)
        except ValueError as exc:
            raise SystemExit(f"Evidence path must stay inside the repo root: {raw}") from exc
        normalized.append(str(relative).replace("\\", "/"))
    return sorted(set(normalized))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def rebuild_repair_follow_on_state(
    workflow: dict[str, Any],
    tracking_state: dict[str, Any],
) -> dict[str, Any] | None:
    raw = workflow.get("repair_follow_on")
    if not isinstance(raw, dict):
        return None

    repair_follow_on = dict(raw)
    required_stage_details = repair_follow_on.get("required_stage_details")
    if not isinstance(required_stage_details, list):
        required_stage_details = []
    completed = completed_stage_names(tracking_state)
    completed_set = set(completed)
    remaining_stage_blockers: list[str] = []
    for item in required_stage_details:
        if not isinstance(item, dict):
            continue
        stage = str(item.get("stage", "")).strip()
        reason = str(item.get("reason", "")).strip()
        if not stage or stage in completed_set or stage == "handoff-brief":
            continue
        remaining_stage_blockers.append(f"{stage} must still run: {reason}")

    preserved_non_stage_blockers = [
        reason
        for reason in raw.get("blocking_reasons", [])
        if isinstance(reason, str)
        and reason.strip()
        and not reason.startswith(KNOWN_STAGE_BLOCKER_PREFIXES)
    ]
    blocking_reasons = remaining_stage_blockers + preserved_non_stage_blockers
    verification_passed = raw.get("verification_passed") is True
    current_state_clean = raw.get("current_state_clean") is True
    handoff_allowed = verification_passed and not blocking_reasons
    if blocking_reasons or not verification_passed:
        outcome = "managed_blocked"
    elif current_state_clean:
        outcome = "clean"
    else:
        outcome = "source_follow_up"

    repair_follow_on["outcome"] = outcome
    repair_follow_on["required_stages"] = [
        str(item.get("stage", "")).strip()
        for item in required_stage_details
        if isinstance(item, dict) and str(item.get("stage", "")).strip()
    ]
    repair_follow_on["completed_stages"] = completed
    repair_follow_on["recorded_completed_stages"] = completed
    repair_follow_on["recorded_execution_completed_stages"] = recorded_execution_stage_names(tracking_state)
    repair_follow_on["invalidated_recorded_stages"] = invalidated_recorded_stage_names(tracking_state)
    repair_follow_on["recorded_stage_state"] = tracking_state.get("stage_records", {})
    repair_follow_on["pruned_unknown_stages"] = tracking_state.get("pruned_unknown_stages", [])
    repair_follow_on["blocking_reasons"] = blocking_reasons
    repair_follow_on["handoff_allowed"] = handoff_allowed
    repair_follow_on["last_updated_at"] = tracking_state.get("last_updated_at")
    repair_follow_on["tracking_mode"] = "persistent_recorded_state"
    repair_follow_on["follow_on_state_path"] = str(FOLLOW_ON_TRACKING_PATH).replace("\\", "/")
    return repair_follow_on


def sync_repair_execution_record(repo_root: Path, repair_follow_on: dict[str, Any], tracking_state: dict[str, Any]) -> None:
    execution_path = repo_root / ".opencode" / "meta" / "repair-execution.json"
    if not execution_path.exists():
        return
    payload = json.loads(execution_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return
    execution_record = payload.get("execution_record")
    if not isinstance(execution_record, dict):
        return
    execution_record["recorded_completed_stages"] = completed_stage_names(tracking_state)
    execution_record["recorded_execution_completed_stages"] = recorded_execution_stage_names(tracking_state)
    execution_record["invalidated_recorded_stages"] = invalidated_recorded_stage_names(tracking_state)
    execution_record["follow_on_tracking_state"] = tracking_state
    execution_record["blocking_reasons"] = repair_follow_on.get("blocking_reasons", [])
    execution_record["repair_follow_on_outcome"] = repair_follow_on.get("outcome")
    execution_record["handoff_allowed"] = repair_follow_on.get("handoff_allowed") is True
    payload["execution_record"] = execution_record
    payload["repair_follow_on_state"] = repair_follow_on
    write_json(execution_path, payload)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    try:
        stage = validate_follow_on_stage_name(args.stage)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    evidence_paths = normalize_evidence_paths(repo_root, args.evidence)
    try:
        tracking_state = record_follow_on_stage_completion(
            repo_root,
            stage=stage,
            completed_by=args.completed_by.strip(),
            summary=args.summary.strip(),
            evidence_paths=evidence_paths,
            repair_package_commit=current_package_commit(),
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    payload = {
        "repo_root": str(repo_root),
        "follow_on_state_path": str(FOLLOW_ON_TRACKING_PATH).replace("\\", "/"),
        "stage": stage,
        "completed_by": args.completed_by.strip(),
        "summary": args.summary.strip(),
        "evidence_paths": evidence_paths,
        "completed_stage_names": completed_stage_names(tracking_state),
        "recorded_stage": tracking_state["stage_records"][stage],
    }

    workflow_path = repo_root / ".opencode" / "state" / "workflow-state.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8")) if workflow_path.exists() else {}
    if isinstance(workflow, dict):
        repair_follow_on = rebuild_repair_follow_on_state(workflow, tracking_state)
        if isinstance(repair_follow_on, dict):
            workflow["repair_follow_on"] = repair_follow_on
            sync_repair_execution_record(repo_root, repair_follow_on, tracking_state)
        write_json(workflow_path, workflow)
        regenerate_restart_surfaces(
            repo_root,
            reason=args.summary.strip(),
            source="scafforge-repair",
            verification_passed=repair_follow_on.get("verification_passed", False) is True if isinstance(repair_follow_on, dict) else False,
        )

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
