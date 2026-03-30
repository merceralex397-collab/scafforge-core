from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from audit_repo_process import current_package_commit
from apply_repo_process_repair import FOLLOW_ON_TRACKING_PATH
from follow_on_tracking import completed_stage_names, load_follow_on_tracking_state, record_follow_on_stage_completion
from regenerate_restart_surfaces import regenerate_restart_surfaces


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record completion of a Scafforge repair follow-on stage in persistent repo metadata."
    )
    parser.add_argument("repo_root", help="Repository root whose repair follow-on stage is being recorded.")
    parser.add_argument("--stage", required=True, help="Follow-on stage that completed, for example project-skill-bootstrap.")
    parser.add_argument("--completed-by", required=True, help="Skill or operator that completed the stage.")
    parser.add_argument("--summary", required=True, help="Short summary of what completed.")
    parser.add_argument("--evidence", action="append", default=[], help="Repo-relative evidence path supporting completion. May be provided multiple times.")
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


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    evidence_paths = normalize_evidence_paths(repo_root, args.evidence)
    tracking_state = record_follow_on_stage_completion(
        repo_root,
        stage=args.stage,
        completed_by=args.completed_by.strip(),
        summary=args.summary.strip(),
        evidence_paths=evidence_paths,
        repair_package_commit=current_package_commit(),
    )
    payload = {
        "repo_root": str(repo_root),
        "follow_on_state_path": str(FOLLOW_ON_TRACKING_PATH).replace("\\", "/"),
        "stage": args.stage,
        "completed_by": args.completed_by.strip(),
        "summary": args.summary.strip(),
        "evidence_paths": evidence_paths,
        "completed_stage_names": completed_stage_names(tracking_state),
        "recorded_stage": tracking_state["stage_records"][args.stage],
    }

    workflow_path = repo_root / ".opencode" / "state" / "workflow-state.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8")) if workflow_path.exists() else {}
    if isinstance(workflow, dict) and isinstance(workflow.get("repair_follow_on"), dict):
        repair_follow_on = dict(workflow["repair_follow_on"])
        repair_follow_on["completed_stages"] = completed_stage_names(tracking_state)
        repair_follow_on["recorded_stage_state"] = tracking_state.get("stage_records", {})
        repair_follow_on["follow_on_state_path"] = str(FOLLOW_ON_TRACKING_PATH).replace("\\", "/")
        repair_follow_on["tracking_mode"] = "persistent_recorded_state"
        repair_follow_on["last_updated_at"] = tracking_state.get("last_updated_at")
        workflow["repair_follow_on"] = repair_follow_on
        write_json(workflow_path, workflow)
        regenerate_restart_surfaces(
            repo_root,
            reason=args.summary.strip(),
            source="scafforge-repair",
            verification_passed=repair_follow_on.get("verification_passed", False) is True,
        )

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
