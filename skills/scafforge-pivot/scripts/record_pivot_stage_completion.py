from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pivot_tracking import (
    PIVOT_STATE_PATH,
    completed_pivot_stage_names,
    record_pivot_stage_completion,
    validate_pivot_stage_name,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record completion of a Scafforge pivot downstream stage in persistent repo metadata."
    )
    parser.add_argument("repo_root", help="Repository root whose pivot downstream stage is being recorded.")
    parser.add_argument("--stage", required=True, help="Pivot downstream stage that completed, for example project-skill-bootstrap.")
    parser.add_argument("--completed-by", required=True, help="Skill or operator that completed the stage.")
    parser.add_argument("--summary", required=True, help="Short summary of what completed.")
    parser.add_argument(
        "--evidence",
        action="append",
        default=[],
        help="Repo-relative evidence path supporting completion. May be provided multiple times.",
    )
    parser.add_argument("--skip-publish", action="store_true", help="Retained for compatibility; publish_pivot_surfaces is owned by the publish-gate path.")
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
def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    # Record evidence-backed downstream completion into .opencode/meta/pivot-state.json.
    try:
        stage = validate_pivot_stage_name(args.stage)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    evidence_paths = normalize_evidence_paths(repo_root, args.evidence)
    try:
        payload = record_pivot_stage_completion(
            repo_root,
            stage=stage,
            completed_by=args.completed_by.strip(),
            summary=args.summary.strip(),
            evidence_paths=evidence_paths,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    downstream_state = payload["downstream_refresh_state"]
    result = {
        "repo_root": str(repo_root),
        "pivot_state_path": str(PIVOT_STATE_PATH).replace("\\", "/"),
        "stage": stage,
        "completed_by": args.completed_by.strip(),
        "summary": args.summary.strip(),
        "evidence_paths": evidence_paths,
        "completed_stage_names": completed_pivot_stage_names(payload),
        "pending_stage_names": downstream_state.get("pending_stages", []),
        "restart_surface_inputs": payload.get("restart_surface_inputs", {}),
        "recorded_stage": downstream_state["stage_records"][stage],
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
