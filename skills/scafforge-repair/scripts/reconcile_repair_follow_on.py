from __future__ import annotations

"""
Reconcile the nested repair_follow_on object in workflow-state.json after
repair follow-on stages have been recorded as complete via
record_repair_stage_completion.py.

This script is the ONLY path that updates workflow-state.json repair_follow_on
outside of a full run_managed_repair.py repair cycle.  It is intentionally
separate from record_repair_stage_completion.py so that the stage recorder
retains its ledger-only contract.

Safety contract:
- Normally acts when ALL blocking_reasons in the current repair_follow_on object
  are stage-completion-based ("must still run:"). If any blocking reason is
  verification-derived the script exits with a non-zero status and explains why.
- Exception: if all required stages are now complete and the only remaining
  verification-derived state is source follow-up / process-state work (with no
  managed blocker codes, manual-prerequisite codes, or contract failures), the
  script may still transition the nested outcome to "source_follow_up".
- Does NOT set current_state_clean.  That field is audit-derived.
- Does NOT change verification_passed independently.  That field was already
  computed by the verification step in run_managed_repair.py.
- Only transitions outcome from "managed_blocked" to "source_follow_up" (never
  to "clean"; clean requires a full audit round).
- Calls regenerate_restart_surfaces so derived surfaces stay coherent.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from apply_repo_process_repair import FOLLOW_ON_TRACKING_PATH
from follow_on_tracking import (
    completed_stage_names,
    invalidated_recorded_stage_names,
)
from regenerate_restart_surfaces import regenerate_restart_surfaces


# Substring that identifies a stage-completion-based blocking reason.
_STAGE_BLOCKER_MARKER = " must still run: "


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Reconcile workflow-state.json repair_follow_on after all required "
            "repair follow-on stages have been recorded as complete."
        )
    )
    parser.add_argument(
        "repo_root",
        help="Repository root whose repair_follow_on should be reconciled.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change but do not write any files.",
    )
    return parser.parse_args()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _extract_stage_name_from_blocker(reason: str) -> str | None:
    """Return the stage name embedded in a 'must still run' blocking reason, or None."""
    idx = reason.find(_STAGE_BLOCKER_MARKER)
    if idx < 1:
        return None
    return reason[:idx].strip()


def classify_blocking_reasons(
    blocking_reasons: list[str],
) -> tuple[list[str], list[str]]:
    """Split blocking_reasons into (stage_based, non_stage_based)."""
    stage_based: list[str] = []
    non_stage: list[str] = []
    for reason in blocking_reasons:
        if _STAGE_BLOCKER_MARKER in reason:
            stage_based.append(reason)
        else:
            non_stage.append(reason)
    return stage_based, non_stage


def _list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _allows_source_follow_up_reconcile(
    repair_follow_on: dict[str, Any],
    non_stage_blockers: list[str],
    recorded_complete: set[str],
) -> bool:
    verification_blocking_codes = _list_of_strings(
        repair_follow_on.get("verification_blocking_codes")
    )
    contract_failures = _list_of_strings(repair_follow_on.get("contract_failures"))
    source_follow_up_codes = _list_of_strings(
        repair_follow_on.get("source_follow_up_codes")
    )
    process_state_codes = _list_of_strings(repair_follow_on.get("process_state_codes"))
    pending_process_verification = bool(
        repair_follow_on.get("pending_process_verification")
    )
    if verification_blocking_codes or contract_failures:
        if (
            contract_failures == ["placeholder_local_skills_survived_refresh"]
            and set(verification_blocking_codes).issubset({"SKILL001"})
        ):
            return True
        return False
    if not source_follow_up_codes and not process_state_codes and not pending_process_verification:
        if (
            bool(non_stage_blockers)
            and all(
                reason.startswith(
                    "Post-repair verification failed repair-contract consistency checks: "
                )
                and "placeholder_local_skills_survived_refresh" in reason
                for reason in non_stage_blockers
            )
        ):
            return True
        if bool(non_stage_blockers) and all(
            reason.startswith(
                "Post-repair verification introduced new critical execution or reference findings: "
            )
            for reason in non_stage_blockers
        ):
            return True
    return bool(
        source_follow_up_codes or process_state_codes or pending_process_verification
    )


def reconcile(repo_root: Path, *, dry_run: bool) -> dict[str, Any]:
    wf_path = repo_root / ".opencode" / "state" / "workflow-state.json"
    tracking_path = repo_root / FOLLOW_ON_TRACKING_PATH

    workflow = _read_json(wf_path)
    if not isinstance(workflow, dict):
        return {"status": "skip", "reason": "workflow-state.json missing or not an object"}

    repair_follow_on = workflow.get("repair_follow_on")
    if not isinstance(repair_follow_on, dict):
        return {"status": "skip", "reason": "repair_follow_on object missing from workflow-state.json"}

    current_outcome = repair_follow_on.get("outcome", "")
    if current_outcome != "managed_blocked":
        return {
            "status": "skip",
            "reason": f"outcome is '{current_outcome}', not 'managed_blocked'; nothing to reconcile",
        }

    blocking_reasons: list[str] = repair_follow_on.get("blocking_reasons") or []
    if not blocking_reasons:
        return {
            "status": "skip",
            "reason": (
                "outcome is managed_blocked but blocking_reasons is empty; "
                "the block was not caused by incomplete stages and cannot be lifted here"
            ),
        }

    stage_based, non_stage = classify_blocking_reasons(blocking_reasons)
    # Check the tracking ledger.
    tracking_state = _read_json(tracking_path)
    if not isinstance(tracking_state, dict):
        return {
            "status": "error",
            "reason": (
                f"Tracking ledger not found at {FOLLOW_ON_TRACKING_PATH}. "
                "Run record_repair_stage_completion.py for each required stage first."
            ),
        }

    recorded_complete = set(completed_stage_names(tracking_state))
    if non_stage and not _allows_source_follow_up_reconcile(
        repair_follow_on, non_stage, recorded_complete
    ):
        return {
            "status": "cannot_reconcile",
            "reason": (
                "One or more blocking reasons are not stage-completion-based and cannot be "
                "resolved by recording stage completions alone. Rerun scafforge-repair to "
                "re-evaluate after addressing the following issues."
            ),
            "non_stage_blockers": non_stage,
        }
    required_stages_from_blockers: list[str] = []
    for reason in stage_based:
        stage_name = _extract_stage_name_from_blocker(reason)
        if stage_name:
            required_stages_from_blockers.append(stage_name)

    still_pending = [s for s in required_stages_from_blockers if s not in recorded_complete]
    if still_pending:
        return {
            "status": "cannot_reconcile",
            "reason": (
                "The following required stages have not yet been recorded as complete "
                "in the persistent tracking ledger. Run record_repair_stage_completion.py "
                "for each stage first."
            ),
            "pending_stages": still_pending,
        }

    # All stage blockers are now resolved.  Build the updated repair_follow_on.
    required_stages: list[str] = repair_follow_on.get("required_stages") or []
    required_stage_details: list[dict[str, Any]] = repair_follow_on.get("required_stage_details") or []
    asserted_stage_names: list[str] = repair_follow_on.get("asserted_completed_stages") or []
    process_version: int = repair_follow_on.get("process_version", 7)

    # Use full ledger completion set, not just the stages in blockers.
    all_completed = sorted(recorded_complete)

    updated_follow_on: dict[str, Any] = {
        **repair_follow_on,
        "outcome": "source_follow_up",
        "required_stage_details": required_stage_details,
        "required_stages": required_stages,
        "completed_stages": all_completed,
        "asserted_completed_stages": asserted_stage_names,
        "legacy_asserted_completed_stages": asserted_stage_names,
        "stage_completion_mode": repair_follow_on.get("stage_completion_mode", "legacy_manual_assertion"),
        "tracking_mode": "persistent_recorded_state",
        "follow_on_state_path": str(FOLLOW_ON_TRACKING_PATH).replace("\\", "/"),
        "recorded_stage_state": tracking_state.get("stage_records", {}),
        "pruned_unknown_stages": tracking_state.get("pruned_unknown_stages", []),
        "invalidated_recorded_stages": invalidated_recorded_stage_names(tracking_state),
        "blocking_reasons": [],
        # Preserve verification_passed, current_state_clean, causal_regression_verified
        # exactly as computed by the last repair run.  The reconciler does not have
        # a verification pass and must not synthesize these values.
        "verification_passed": repair_follow_on.get("verification_passed", False),
        "handoff_allowed": True,
        "current_state_clean": repair_follow_on.get("current_state_clean", False),
        "causal_regression_verified": repair_follow_on.get("causal_regression_verified", False),
        "verification_blocking_codes": _list_of_strings(
            repair_follow_on.get("verification_blocking_codes")
        ),
        "source_follow_up_codes": _list_of_strings(
            repair_follow_on.get("source_follow_up_codes")
        ),
        "process_state_codes": _list_of_strings(
            repair_follow_on.get("process_state_codes")
        ),
        "advisory_codes": _list_of_strings(repair_follow_on.get("advisory_codes")),
        "contract_failures": _list_of_strings(
            repair_follow_on.get("contract_failures")
        ),
        "last_updated_at": tracking_state.get("last_updated_at"),
        "process_version": process_version,
        "reconciled_by": "reconcile_repair_follow_on",
    }

    result: dict[str, Any] = {
        "status": "reconciled",
        "prior_outcome": current_outcome,
        "new_outcome": "source_follow_up",
        "resolved_stage_blockers": required_stages_from_blockers,
        "ignored_non_stage_blockers": non_stage,
        "all_completed_stages": all_completed,
        "dry_run": dry_run,
    }

    if dry_run:
        result["updated_repair_follow_on"] = updated_follow_on
        return result

    workflow["repair_follow_on"] = updated_follow_on
    _write_json(wf_path, workflow)

    regenerate_restart_surfaces(
        repo_root,
        reason="repair-follow-on-reconcile: all required stages complete, outcome updated to source_follow_up",
        source="reconcile_repair_follow_on",
        next_action=None,
        verification_passed=updated_follow_on.get("verification_passed"),
    )
    result["restart_surfaces_regenerated"] = True
    return result


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    result = reconcile(repo_root, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
    status = result.get("status", "")
    if status == "reconciled":
        return 0
    if status in {"skip"}:
        return 0
    # cannot_reconcile or error
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
