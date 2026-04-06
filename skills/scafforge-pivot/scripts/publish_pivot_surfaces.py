from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from shared_generated_tool_runtime import run_generated_tool
from pivot_tracking import PIVOT_STATE_PATH, current_iso_timestamp, load_pivot_state, persist_pivot_state


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Republish generated restart surfaces so pivot state is reflected immediately after pivot planning or execution."
    )
    parser.add_argument("repo_root", help="Repository root whose pivot restart surfaces should be republished.")
    parser.add_argument("--next-action", help="Optional explicit next action to pass through handoff_publish.")
    parser.add_argument("--published-by", default="scafforge-pivot", help="Operator or stage responsible for the publication event.")
    return parser.parse_args()


def record_publication(
    repo_root: Path,
    *,
    published_by: str,
    next_action: str | None,
    publication_result: dict[str, Any],
) -> dict[str, Any]:
    payload = load_pivot_state(repo_root)
    payload["restart_surface_publication"] = {
        "status": "published",
        "published_at": current_iso_timestamp(),
        "published_by": published_by,
        "next_action": next_action,
        "start_here": publication_result.get("start_here"),
        "latest_handoff": publication_result.get("latest_handoff"),
        "context_snapshot": ".opencode/state/context-snapshot.md",
    }
    persist_pivot_state(repo_root, payload)
    return payload


def publish_pivot_surfaces(repo_root: Path, *, published_by: str, next_action: str | None = None) -> dict[str, Any]:
    payload = load_pivot_state(repo_root)
    args: dict[str, object] = {}
    if isinstance(next_action, str) and next_action.strip():
        args["next_action"] = next_action.strip()
    publication_result = run_generated_tool(repo_root, ".opencode/tools/handoff_publish.ts", args)
    payload = record_publication(
        repo_root,
        published_by=published_by.strip() or "scafforge-pivot",
        next_action=next_action.strip() if isinstance(next_action, str) and next_action.strip() else None,
        publication_result=publication_result,
    )
    return {
        "repo_root": str(repo_root),
        "pivot_state_path": str(PIVOT_STATE_PATH).replace("\\", "/"),
        "pivot_state_owner": payload.get("pivot_state_owner"),
        "publication_result": publication_result,
        "restart_surface_publication": payload.get("restart_surface_publication", {}),
        "restart_surface_inputs": payload.get("restart_surface_inputs", {}),
    }


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    result = publish_pivot_surfaces(
        repo_root,
        published_by=args.published_by,
        next_action=args.next_action,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
