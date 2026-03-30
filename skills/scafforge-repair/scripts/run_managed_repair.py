from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from apply_repo_process_repair import (
    FOLLOW_ON_TRACKING_PATH,
    apply_repair,
    build_stale_surface_map,
    detect_agent_prompt_drift,
    find_placeholder_skills,
    load_metadata,
    load_pending_process_verification,
    repair_basis_requires_causal_replay,
    resolve_repair_basis,
    run_bootstrap_render,
    verification_logs,
)
from audit_repo_process import current_package_commit, emit_diagnosis_pack, select_diagnosis_destination
from follow_on_tracking import completed_stage_names, recorded_execution_stage_names, update_follow_on_tracking_state
from shared_verifier import audit_repo
from regenerate_restart_surfaces import regenerate_restart_surfaces


EXECUTION_RECORD_PATH = Path(".opencode/meta/repair-execution.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Scafforge managed repair and emit a fail-closed execution record.")
    parser.add_argument("repo_root", help="Repository root to repair.")
    parser.add_argument("--project-name", help="Override project name when provenance is missing.")
    parser.add_argument("--project-slug", help="Override project slug when provenance is missing.")
    parser.add_argument("--agent-prefix", help="Override agent prefix when provenance is missing.")
    parser.add_argument("--model-provider", help="Override model provider when provenance is missing.")
    parser.add_argument("--planner-model", help="Override planner model when provenance is missing.")
    parser.add_argument("--implementer-model", help="Override implementer model when provenance is missing.")
    parser.add_argument("--utility-model", help="Override utility model when provenance is missing.")
    parser.add_argument("--stack-label", default="framework-agnostic", help="Stack label for regenerated process docs.")
    parser.add_argument(
        "--change-summary",
        default="Managed Scafforge repair runner refreshed deterministic workflow surfaces and evaluated downstream repair obligations.",
        help="Summary stored in workflow-state and repair history.",
    )
    parser.add_argument("--skip-deterministic-refresh", action="store_true", help="Do not rerun the deterministic replacement pass.")
    parser.add_argument("--skip-verify", action="store_true", help="Skip post-repair verification.")
    parser.add_argument("--supporting-log", action="append", default=[], help="Optional supporting transcript path. May be provided multiple times.")
    parser.add_argument(
        "--repair-basis-diagnosis",
        help="Optional diagnosis pack directory or manifest path that this repair run is based on. Defaults to the latest diagnosis pack in the repo.",
    )
    parser.add_argument("--diagnosis-output-dir", help="Optional writable path for the post-repair diagnosis pack.")
    parser.add_argument("--stage-complete", action="append", default=[], help="Mark a required follow-on stage as completed by the host skill.")
    parser.add_argument("--fail-on", choices=("never", "warning", "error"), default="never")
    return parser.parse_args()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def derive_required_follow_on_stages(
    repo_root: Path,
    findings: list[Any],
    replaced_surfaces: list[str],
    pending_process_verification: bool,
) -> list[dict[str, str]]:
    required: list[dict[str, str]] = []
    placeholder_skills = find_placeholder_skills(repo_root)
    prompt_drift = detect_agent_prompt_drift(repo_root)
    finding_codes = {getattr(finding, "code", "") for finding in findings}

    if placeholder_skills or "scaffold-managed .opencode/skills" in replaced_surfaces or any(code.startswith(("SKILL", "MODEL")) for code in finding_codes):
        required.append(
            {
                "stage": "project-skill-bootstrap",
                "reason": "Repo-local skills were replaced or still contain generic placeholder/model drift that must be regenerated with project-specific content.",
            }
        )
    if prompt_drift or any(code.startswith("WFLOW") for code in finding_codes):
        required.append(
            {
                "stage": "opencode-team-bootstrap",
                "reason": "Agent or .opencode prompt surfaces still drift from the current workflow contract and must be regenerated.",
            }
        )
        required.append(
            {
                "stage": "agent-prompt-engineering",
                "reason": "Prompt behavior changed or remains stale after repair, so the same-session hardening pass is required before handoff.",
            }
        )
    if any(code.startswith("EXEC") for code in finding_codes):
        required.append(
            {
                "stage": "ticket-pack-builder",
                "reason": "Repair left remediation or reverification follow-up that must be routed into the repo ticket system.",
            }
        )
    return required


def classify_verification_findings(findings: list[Any]) -> dict[str, list[Any]]:
    managed_blockers: list[Any] = []
    source_follow_up: list[Any] = []
    manual_prerequisites: list[Any] = []
    process_state_only: list[Any] = []
    for finding in findings:
        code = getattr(finding, "code", "")
        if code.startswith("EXEC"):
            source_follow_up.append(finding)
        elif code == "WFLOW008":
            process_state_only.append(finding)
        elif code.startswith("ENV"):
            manual_prerequisites.append(finding)
        else:
            managed_blockers.append(finding)
    return {
        "managed_blockers": managed_blockers,
        "source_follow_up": source_follow_up,
        "manual_prerequisites": manual_prerequisites,
        "process_state_only": process_state_only,
    }


def verification_contract_failures(
    findings: list[Any],
    *,
    performed: bool,
    current_state_clean: bool,
    pending_process_verification: bool,
    classes: dict[str, list[Any]],
) -> list[str]:
    codes = {getattr(finding, "code", "") for finding in findings}
    failures: list[str] = []
    if (
        performed
        and not findings
        and not current_state_clean
        and not classes["source_follow_up"]
        and not classes["process_state_only"]
        and not pending_process_verification
    ):
        failures.append("non_clean_without_findings")
    if "WFLOW010" in codes:
        failures.append("restart_surface_drift_after_repair")
    if "SKILL001" in codes:
        failures.append("placeholder_local_skills_survived_refresh")
    return failures


def summarize_verification(
    findings: list[Any],
    pending_process_verification: bool,
    performed: bool,
    supporting_logs: list[Path],
    classes: dict[str, list[Any]],
    *,
    basis_requires_causal_replay: bool,
    repair_basis_path: Path | None,
) -> dict[str, Any]:
    blocking_findings = [*classes["managed_blockers"], *classes["manual_prerequisites"]]
    managed_repair_verified = performed and not blocking_findings and (not basis_requires_causal_replay or bool(supporting_logs))
    current_state_clean = (
        managed_repair_verified
        and not classes["source_follow_up"]
        and not classes["process_state_only"]
        and not pending_process_verification
    )
    causal_regression_verified = managed_repair_verified
    contract_failures = verification_contract_failures(
        findings,
        performed=performed,
        current_state_clean=current_state_clean,
        pending_process_verification=pending_process_verification,
        classes=classes,
    )
    return {
        "performed": performed,
        "finding_count": len(findings),
        "error_count": sum(1 for finding in findings if getattr(finding, "severity", "") == "error"),
        "warning_count": sum(1 for finding in findings if getattr(finding, "severity", "") == "warning"),
        "codes": [getattr(finding, "code", "") for finding in findings],
        "blocking_codes": [getattr(finding, "code", "") for finding in blocking_findings],
        "source_follow_up_codes": [getattr(finding, "code", "") for finding in classes["source_follow_up"]],
        "process_state_codes": [getattr(finding, "code", "") for finding in classes["process_state_only"]],
        "pending_process_verification": pending_process_verification,
        "verification_basis": "transcript_backed" if basis_requires_causal_replay else "current_state_only",
        "basis_requires_causal_replay": basis_requires_causal_replay,
        "repair_basis_path": str(repair_basis_path) if repair_basis_path else None,
        "current_state_clean": current_state_clean,
        "causal_regression_verified": causal_regression_verified,
        "contract_failures": contract_failures,
        "contract_passed": not contract_failures,
        "verification_passed": causal_regression_verified and not contract_failures,
        "supporting_logs": [str(path) for path in supporting_logs],
    }


def update_repair_follow_on_state(
    repo_root: Path,
    *,
    outcome: str,
    required_stage_names: list[str],
    completed_stage_names: list[str],
    asserted_stage_names: list[str],
    tracking_state: dict[str, Any],
    blocking_reasons: list[str],
    verification_passed: bool,
    handoff_allowed: bool,
    current_state_clean: bool,
    causal_regression_verified: bool,
) -> dict[str, Any]:
    workflow_path = repo_root / ".opencode" / "state" / "workflow-state.json"
    workflow = read_json(workflow_path)
    if not isinstance(workflow, dict):
        workflow = {}
    process_version = workflow.get("process_version") if isinstance(workflow.get("process_version"), int) and workflow.get("process_version") > 0 else 7
    repair_follow_on = {
        "outcome": outcome,
        "required_stages": required_stage_names,
        "completed_stages": completed_stage_names,
        "asserted_completed_stages": asserted_stage_names,
        "stage_completion_mode": "transitional_manual_assertion",
        "tracking_mode": "persistent_recorded_state",
        "follow_on_state_path": str(FOLLOW_ON_TRACKING_PATH).replace("\\", "/"),
        "recorded_stage_state": tracking_state.get("stage_records", {}),
        "blocking_reasons": blocking_reasons,
        "verification_passed": verification_passed,
        "handoff_allowed": handoff_allowed,
        "current_state_clean": current_state_clean,
        "causal_regression_verified": causal_regression_verified,
        "last_updated_at": tracking_state.get("last_updated_at"),
        "process_version": process_version,
    }
    workflow["repair_follow_on"] = repair_follow_on
    write_json(workflow_path, workflow)
    return repair_follow_on


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    replaced_surfaces: list[str] = []

    if not args.skip_deterministic_refresh:
        metadata = load_metadata(repo_root, args)
        with tempfile.TemporaryDirectory(prefix="scafforge-repair-") as temp_dir:
            rendered_root = Path(temp_dir) / "rendered"
            run_bootstrap_render(rendered_root, metadata, args.stack_label)
            replaced_surfaces = apply_repair(repo_root, rendered_root, args.change_summary)

    repair_basis = resolve_repair_basis(repo_root, args.repair_basis_diagnosis)
    repair_basis_path = repair_basis[0] if repair_basis else None
    repair_basis_manifest = repair_basis[1] if repair_basis else {}
    if isinstance(repair_basis_manifest, dict) and repair_basis_manifest.get("package_work_required_first") is True:
        raise SystemExit(
            "The selected repair basis still requires Scafforge package work first. "
            "Run one fresh post-package revalidation audit after the package changes land, then repair from that diagnosis pack."
        )
    basis_requires_causal_replay = repair_basis_requires_causal_replay(repo_root, args.supporting_log, repair_basis)
    logs = verification_logs(repo_root, args.supporting_log, repair_basis)
    findings = [] if args.skip_verify else audit_repo(repo_root, logs=logs)
    pending_process_verification = load_pending_process_verification(repo_root)
    finding_classes = classify_verification_findings(findings)
    verification_status = summarize_verification(
        findings,
        pending_process_verification,
        not args.skip_verify,
        logs,
        finding_classes,
        basis_requires_causal_replay=basis_requires_causal_replay,
        repair_basis_path=repair_basis_path,
    )

    if not args.skip_verify and basis_requires_causal_replay and not logs:
        verification_status["verification_passed"] = False
        verification_status["causal_regression_verified"] = False

    required_follow_on = derive_required_follow_on_stages(repo_root, findings, replaced_surfaces, pending_process_verification)
    required_stage_names = [item["stage"] for item in required_follow_on]
    stale_surface_map = build_stale_surface_map(
        repo_root,
        replaced_surfaces,
        findings,
        pending_process_verification,
        required_stage_names=set(required_stage_names),
    )
    requested_stage_names = sorted(set(args.stage_complete))
    asserted_stage_names = sorted(set(requested_stage_names))
    tracking_state = update_follow_on_tracking_state(
        repo_root,
        required_follow_on=required_follow_on,
        asserted_stage_names=asserted_stage_names,
        repair_basis_path=repair_basis_path,
        repair_package_commit=current_package_commit(),
    )
    persisted_completed_stage_names = completed_stage_names(tracking_state)
    recorded_execution_stage_list = recorded_execution_stage_names(tracking_state)
    completed_stage_name_set = set(persisted_completed_stage_names)
    if not args.skip_deterministic_refresh:
        completed_stage_name_set.add("deterministic-refresh")

    executed_stages = [{"stage": "deterministic-refresh", "status": "completed"}] if not args.skip_deterministic_refresh else []
    for stage in requested_stage_names:
        executed_stages.append({"stage": stage, "status": "asserted_completed", "completion_mode": "transitional_manual_assertion"})

    recorded_stage_results = []
    for stage in persisted_completed_stage_names:
        if stage in asserted_stage_names:
            continue
        record = tracking_state.get("stage_records", {}).get(stage, {})
        recorded_stage_results.append(
            {
                "stage": stage,
                "status": "recorded_completed",
                "completion_mode": record.get("completion_mode", "transitional_manual_assertion"),
                "recorded_at": record.get("last_recorded_at"),
            }
        )

    skipped_stages = []
    for item in required_follow_on:
        stage = item["stage"]
        if stage == "handoff-brief":
            continue
        if stage in completed_stage_name_set:
            continue
        skipped_stages.append(
            {
                "stage": stage,
                "status": "required_not_run",
                "reason": item["reason"],
            }
        )

    blocking_reasons = [f"{item['stage']} must still run: {item['reason']}" for item in skipped_stages]
    if args.skip_verify:
        blocking_reasons.append("Post-repair verification was skipped; rerun scafforge-audit before handoff.")
    elif basis_requires_causal_replay and not logs:
        blocking_reasons.append("Post-repair verification did not inherit the transcript-backed repair basis; rerun the public repair runner with the causal transcript evidence before handoff.")
    elif verification_status["contract_failures"]:
        blocking_reasons.append(
            "Post-repair verification failed repair-contract consistency checks: "
            + ", ".join(verification_status["contract_failures"])
            + "."
        )
    elif finding_classes["managed_blockers"] or finding_classes["manual_prerequisites"]:
        blocking_reasons.append("Post-repair verification still reports managed workflow or environment findings; handoff must remain blocked until they are resolved.")

    deferred_stages = []
    repair_follow_on_outcome = (
        "managed_blocked"
        if blocking_reasons or not verification_status["verification_passed"]
        else "source_follow_up"
        if verification_status["source_follow_up_codes"] or verification_status["process_state_codes"] or pending_process_verification
        else "clean"
    )
    handoff_allowed = verification_status["verification_passed"] and not blocking_reasons
    repair_follow_on_state = update_repair_follow_on_state(
        repo_root,
        outcome=repair_follow_on_outcome,
        required_stage_names=required_stage_names,
        completed_stage_names=sorted(completed_stage_name_set),
        asserted_stage_names=asserted_stage_names,
        tracking_state=tracking_state,
        blocking_reasons=blocking_reasons,
        verification_passed=verification_status["verification_passed"],
        handoff_allowed=handoff_allowed,
        current_state_clean=verification_status["current_state_clean"],
        causal_regression_verified=verification_status["causal_regression_verified"],
    )

    diagnosis_pack = None
    if not args.skip_verify:
        diagnosis_dir = select_diagnosis_destination(repo_root, args.diagnosis_output_dir, findings)
        diagnosis_pack = emit_diagnosis_pack(
            repo_root,
            findings,
            diagnosis_dir,
            logs,
            manifest_overrides={
                "verification_kind": "post_repair",
                "diagnosis_kind": "post_repair_verification",
                "repair_package_commit": current_package_commit(),
                "repair_basis_path": str(repair_basis_path) if repair_basis_path else None,
                "current_state_clean": verification_status["current_state_clean"],
                "causal_regression_verified": verification_status["causal_regression_verified"],
                "verification_basis": verification_status["verification_basis"],
            },
        )

    payload = {
        "repair_plan": {
            "repo_root": str(repo_root),
            "required_follow_on_stages": required_follow_on,
            "replaced_surfaces": replaced_surfaces,
            "stale_surface_map": stale_surface_map,
        },
        "stage_results": executed_stages + recorded_stage_results + deferred_stages + skipped_stages,
        "execution_record": {
            "repo_root": str(repo_root),
            "repair_package_commit": current_package_commit(),
            "repair_basis_path": str(repair_basis_path) if repair_basis_path else None,
            "required_follow_on_stages": required_stage_names,
            "executed_stages": executed_stages,
            "recorded_completed_stages": persisted_completed_stage_names,
            "recorded_execution_completed_stages": recorded_execution_stage_list,
            "asserted_completed_stages": asserted_stage_names,
            "stage_completion_mode": "transitional_manual_assertion",
            "follow_on_tracking_mode": "persistent_recorded_state",
            "follow_on_state_path": str(FOLLOW_ON_TRACKING_PATH).replace("\\", "/"),
            "follow_on_tracking_state": tracking_state,
            "deferred_stages": deferred_stages,
            "skipped_stages": skipped_stages,
            "blocking_reasons": blocking_reasons,
            "repair_follow_on_outcome": repair_follow_on_outcome,
            "verification_status": verification_status,
            "handoff_allowed": handoff_allowed,
            "stale_surface_map": stale_surface_map,
        },
        "repair_follow_on_state": repair_follow_on_state,
    }
    if diagnosis_pack:
        payload["diagnosis_pack"] = diagnosis_pack

    write_json(repo_root / EXECUTION_RECORD_PATH, payload)
    regenerate_restart_surfaces(
        repo_root,
        reason=args.change_summary,
        source="scafforge-repair",
        next_action=blocking_reasons[0] if blocking_reasons else None,
        verification_passed=verification_status["verification_passed"],
    )

    print(json.dumps(payload, indent=2))

    if args.fail_on == "never":
        return 0 if repair_follow_on_outcome != "managed_blocked" else 3
    if args.fail_on == "warning" and ([*finding_classes["managed_blockers"], *finding_classes["manual_prerequisites"]] or blocking_reasons):
        return 3
    if args.fail_on == "error" and any(getattr(finding, "severity", "") == "error" for finding in [*finding_classes["managed_blockers"], *finding_classes["manual_prerequisites"]]):
        return 3
    return 0 if repair_follow_on_outcome != "managed_blocked" else 3


if __name__ == "__main__":
    raise SystemExit(main())
