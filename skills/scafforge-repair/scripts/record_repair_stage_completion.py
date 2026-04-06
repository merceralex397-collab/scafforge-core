from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from audit_repo_process import current_package_commit
from apply_repo_process_repair import FOLLOW_ON_TRACKING_PATH
from follow_on_tracking import (
    completed_stage_names,
    record_follow_on_stage_completion,
    validate_follow_on_stage_name,
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

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
