from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from generated_tool_runtime import run_generated_tool
from pivot_tracking import (
    PIVOT_STATE_PATH,
    load_pivot_state,
    record_ticket_lineage_action_completion,
)
from publish_pivot_surfaces import publish_pivot_surfaces


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute explicit pivot ticket lineage actions through the generated repo's canonical ticket tools."
    )
    parser.add_argument("repo_root", help="Repository root whose pivot ticket lineage actions should be executed.")
    parser.add_argument(
        "--only-action",
        action="append",
        default=[],
        help="Optional lineage action label to execute. When omitted, execute every pending executable action.",
    )
    parser.add_argument(
        "--executed-by",
        default="scafforge-pivot",
        help="Operator or skill name recorded as the lineage execution owner.",
    )
    parser.add_argument(
        "--skip-publish",
        action="store_true",
        help="Do not republish pivot restart surfaces after executing lineage actions.",
    )
    return parser.parse_args()


def normalize_selected_labels(values: list[str]) -> set[str]:
    return {value.strip() for value in values if isinstance(value, str) and value.strip()}


def load_manifest(repo_root: Path) -> dict[str, Any]:
    return json.loads((repo_root / "tickets" / "manifest.json").read_text(encoding="utf-8"))


def manifest_ticket(manifest: dict[str, Any], ticket_id: str) -> dict[str, Any]:
    for ticket in manifest.get("tickets", []):
        if isinstance(ticket, dict) and str(ticket.get("id", "")).strip() == ticket_id:
            return ticket
    raise RuntimeError(f"Pivot lineage execution could not find ticket {ticket_id} in tickets/manifest.json")


def execute_action(repo_root: Path, action: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    action_type = str(action.get("action", "")).strip()
    target_ticket_id = str(action.get("target_ticket_id", "")).strip()
    reason = str(action.get("reason", "")).strip()
    evidence_artifact_path = str(action.get("evidence_artifact_path", "")).strip()
    replacement_source_ticket_id = str(action.get("replacement_source_ticket_id", "")).strip()
    replacement_source_mode = str(action.get("replacement_source_mode", "")).strip()
    ticket_spec = action.get("ticket_spec") if isinstance(action.get("ticket_spec"), dict) else None

    if action_type == "reopen":
        if not target_ticket_id or not evidence_artifact_path:
            return None, "reopen requires both target_ticket_id and evidence_artifact_path."
        return run_generated_tool(
            repo_root,
            ".opencode/tools/ticket_reopen.ts",
            {
                "ticket_id": target_ticket_id,
                "reason": reason,
                "evidence_artifact_path": evidence_artifact_path,
                "activate": True,
            },
        ), None

    if action_type == "reconcile":
        if not target_ticket_id or not evidence_artifact_path:
            return None, "reconcile requires both target_ticket_id and evidence_artifact_path."
        manifest = load_manifest(repo_root)
        target_ticket = manifest_ticket(manifest, target_ticket_id)
        source_ticket_id = str(target_ticket.get("source_ticket_id", "")).strip() or replacement_source_ticket_id
        if not source_ticket_id:
            return None, "reconcile requires a canonical source ticket or replacement source ticket."
        args: dict[str, object] = {
            "source_ticket_id": source_ticket_id,
            "target_ticket_id": target_ticket_id,
            "evidence_artifact_path": evidence_artifact_path,
            "reason": reason,
            "remove_dependency_on_source": True,
            "activate_source": True,
        }
        if replacement_source_ticket_id:
            args["replacement_source_ticket_id"] = replacement_source_ticket_id
        if replacement_source_mode:
            args["replacement_source_mode"] = replacement_source_mode
        return run_generated_tool(repo_root, ".opencode/tools/ticket_reconcile.ts", args), None

    if action_type == "supersede":
        if not target_ticket_id or not evidence_artifact_path:
            return None, "supersede requires both target_ticket_id and evidence_artifact_path."
        manifest = load_manifest(repo_root)
        target_ticket = manifest_ticket(manifest, target_ticket_id)
        source_ticket_id = str(target_ticket.get("source_ticket_id", "")).strip() or replacement_source_ticket_id
        if not source_ticket_id:
            return None, "supersede requires a canonical source ticket or replacement source ticket."
        args = {
            "source_ticket_id": source_ticket_id,
            "target_ticket_id": target_ticket_id,
            "evidence_artifact_path": evidence_artifact_path,
            "reason": reason,
            "remove_dependency_on_source": True,
            "supersede_target": True,
            "activate_source": True,
        }
        if replacement_source_ticket_id:
            args["replacement_source_ticket_id"] = replacement_source_ticket_id
        if replacement_source_mode:
            args["replacement_source_mode"] = replacement_source_mode
        return run_generated_tool(repo_root, ".opencode/tools/ticket_reconcile.ts", args), None

    if action_type == "create_follow_up" and ticket_spec:
        args = dict(ticket_spec)
        if "summary" not in args:
            args["summary"] = str(action.get("summary", "")).strip()
        if "activate" not in args:
            args["activate"] = True
        return run_generated_tool(repo_root, ".opencode/tools/ticket_create.ts", args), None

    if action_type == "create_follow_up":
        return None, "create_follow_up requires runtime ticket_spec metadata before it can execute safely."
    return None, f"{action_type or 'unknown'} is not an executable pivot lineage action."


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    payload = load_pivot_state(repo_root)
    actions = payload["ticket_lineage_plan"]["actions"]
    selected_labels = normalize_selected_labels(args.only_action)
    applied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for action in actions:
        label = str(action.get("label", "")).strip()
        if not label:
            continue
        if selected_labels and label not in selected_labels:
            continue
        if action.get("status") == "completed":
            continue
        result, skip_reason = execute_action(repo_root, action)
        if result is None:
            skipped.append(
                {
                    "label": label,
                    "reason": skip_reason or "Action is still routing-only because the pivot plan does not yet carry enough runtime metadata to execute it safely.",
                }
            )
            continue
        completion_summary = f"Executed pivot lineage action {label} through the generated repo ticket tool."
        updated_payload = record_ticket_lineage_action_completion(
            repo_root,
            label=label,
            completed_by=args.executed_by,
            summary=completion_summary,
            execution_result=result,
        )
        applied.append(
            {
                "label": label,
                "result": result,
                "restart_surface_inputs": updated_payload.get("restart_surface_inputs", {}),
            }
        )

    publication = None
    if not args.skip_publish:
        publication = publish_pivot_surfaces(repo_root, published_by=args.executed_by)
    final_payload = load_pivot_state(repo_root)
    output = {
        "repo_root": str(repo_root),
        "pivot_state_path": str(PIVOT_STATE_PATH).replace("\\", "/"),
        "applied_actions": applied,
        "skipped_actions": skipped,
        "pending_actions": final_payload["ticket_lineage_plan"]["pending_actions"],
        "completed_actions": final_payload["ticket_lineage_plan"]["completed_actions"],
        "restart_surface_inputs": final_payload.get("restart_surface_inputs", {}),
        "ticket_pack_builder_stage": final_payload["downstream_refresh_state"]["stage_records"].get("ticket-pack-builder"),
        "publication": publication,
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
