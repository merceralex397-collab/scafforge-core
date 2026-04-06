from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from apply_repo_process_repair import (
    FOLLOW_ON_TRACKING_PATH,
    REPAIR_ESCALATION_PATH,
    RepairEscalation,
    apply_repair,
    build_stale_surface_map,
    detect_agent_prompt_drift,
    find_placeholder_skills,
    load_metadata,
    load_pending_process_verification,
    repair_basis_requires_causal_replay,
    resolve_repair_basis,
    run_bootstrap_render,
    update_latest_repair_history,
    verification_logs,
)
from audit_repo_process import (
    bundle_shadow_mode_deltas,
    bundle_source_follow_up_codes,
    current_package_commit,
    emit_diagnosis_pack,
    disposition_class_for_finding,
    repair_routed_codes_from_manifest,
    load_disposition_bundle,
    select_diagnosis_destination,
)
from follow_on_tracking import (
    auto_record_stage_completion_from_canonical_evidence,
    completed_stage_names,
    follow_on_stage_metadata,
    invalidated_recorded_stage_names,
    normalize_follow_on_stage_names,
    recorded_execution_stage_names,
    update_follow_on_tracking_state,
)
from shared_verifier import audit_repo
from regenerate_restart_surfaces import regenerate_restart_surfaces


EXECUTION_RECORD_PATH = Path(".opencode/meta/repair-execution.json")


def _repair_ticket_graph_contradictions(repo_root: Path) -> list[str]:
    """Auto-fix WFLOW019: remove deterministic contradictions from the ticket graph.

    Safe repairs only — no intent changes:
    1. Remove a ticket's own source_ticket_id from its depends_on list (ordering is already
       encoded by source_ticket_id; having both is always a contradiction).
    2. Remove a self-referencing source_ticket_id (ticket cannot be its own source).
    3. Ensure source_ticket.follow_up_ticket_ids contains the follow-up ticket id when the
       follow-up names it as source_ticket_id (bidirectional sync).
    """
    manifest_path = repo_root / "tickets" / "manifest.json"
    if not manifest_path.exists():
        return []
    try:
        manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    tickets = manifest.get("tickets") if isinstance(manifest, dict) else None
    if not isinstance(tickets, list):
        return []

    tickets_by_id: dict[str, dict[str, Any]] = {}
    for t in tickets:
        if isinstance(t, dict) and isinstance(t.get("id"), str):
            tickets_by_id[t["id"]] = t

    changes: list[str] = []
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        tid = ticket.get("id")
        source_id = ticket.get("source_ticket_id")
        if not isinstance(source_id, str) or not source_id:
            continue

        # Fix 1: self-referencing source_ticket_id
        if source_id == tid:
            del ticket["source_ticket_id"]
            changes.append(f"{tid}: removed self-referencing source_ticket_id")
            continue

        # Fix 2: source_ticket_id duplicated in depends_on for non-split follow-ups
        depends_on = ticket.get("depends_on")
        if isinstance(depends_on, list) and source_id in depends_on and str(ticket.get("source_mode", "")).strip() != "split_scope":
            ticket["depends_on"] = [d for d in depends_on if d != source_id]
            changes.append(
                f"{tid}: removed {source_id} from depends_on (source_ticket_id already encodes ordering)"
            )

        # Fix 3: source ticket missing this ticket in follow_up_ticket_ids
        source_ticket = tickets_by_id.get(source_id)
        if source_ticket is not None:
            follow_ups = source_ticket.get("follow_up_ticket_ids")
            if isinstance(follow_ups, list) and tid not in follow_ups:
                source_ticket["follow_up_ticket_ids"] = follow_ups + [tid]
                changes.append(f"{source_id}: added {tid} to follow_up_ticket_ids")

    if changes:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return changes


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
    parser.add_argument(
        "--model-tier",
        choices=("strong", "standard", "weak"),
        help="Override prompt-density model tier when provenance is missing.",
    )
    parser.add_argument("--stack-label", default="framework-agnostic", help="Stack label for regenerated process docs.")
    parser.add_argument(
        "--change-summary",
        default="Managed Scafforge repair runner refreshed deterministic workflow surfaces and evaluated downstream repair obligations.",
        help="Summary stored in workflow-state and repair history.",
    )
    parser.add_argument("--skip-deterministic-refresh", action="store_true", help="Do not rerun the deterministic replacement pass.")
    parser.add_argument(
        "--preserve-backups",
        action="store_true",
        help="Keep deterministic managed-surface backups under .opencode/state/repair-backups after a successful repair.",
    )
    parser.add_argument("--skip-verify", action="store_true", help="Skip post-repair verification.")
    parser.add_argument("--supporting-log", action="append", default=[], help="Optional supporting transcript path. May be provided multiple times.")
    parser.add_argument(
        "--repair-basis-diagnosis",
        help="Optional diagnosis pack directory or manifest path that this repair run is based on. Defaults to the latest diagnosis pack in the repo.",
    )
    parser.add_argument("--diagnosis-output-dir", help="Optional writable path for the post-repair diagnosis pack.")
    parser.add_argument("--stage-complete", action="append", default=[], help=argparse.SUPPRESS)
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

    if placeholder_skills or any(code.startswith(("SKILL", "MODEL")) for code in finding_codes):
        required.append(
            {
                **follow_on_stage_metadata("project-skill-bootstrap"),
                "stage": "project-skill-bootstrap",
                "reason": "Repo-local skills still contain generic placeholder/model drift that must be regenerated with project-specific content.",
            }
        )
    if prompt_drift or any(code.startswith("WFLOW") for code in finding_codes):
        required.append(
            {
                **follow_on_stage_metadata("opencode-team-bootstrap"),
                "stage": "opencode-team-bootstrap",
                "reason": "Agent or .opencode prompt surfaces still drift from the current workflow contract and must be regenerated.",
            }
        )
        required.append(
            {
                **follow_on_stage_metadata("agent-prompt-engineering"),
                "stage": "agent-prompt-engineering",
                "reason": "Prompt behavior changed or remains stale after repair, so the same-session hardening pass is required before handoff.",
            }
        )
    if any(code.startswith("EXEC") for code in finding_codes) or "WFLOW025" in finding_codes:
        ticket_follow_up_reason = (
            "Repair left remediation, reverification, or target-completion follow-up that must be routed into the repo ticket system."
            if "WFLOW025" in finding_codes
            else "Repair left remediation or reverification follow-up that must be routed into the repo ticket system."
        )
        required.append(
            {
                **follow_on_stage_metadata("ticket-pack-builder"),
                "stage": "ticket-pack-builder",
                "reason": ticket_follow_up_reason,
            }
        )
    return required


def repair_basis_source_codes(manifest: dict[str, Any]) -> set[str]:
    bundle = load_disposition_bundle(manifest) if isinstance(manifest, dict) else None
    if bundle is not None:
        return bundle_source_follow_up_codes(bundle)
    source_findings = manifest.get("source_findings") if isinstance(manifest, dict) else None
    if isinstance(source_findings, list) and source_findings:
        return {
            str(item.get("code", "")).strip()
            for item in source_findings
            if isinstance(item, dict) and str(item.get("code", "")).strip().startswith(("EXEC", "REF"))
        }
    codes: set[str] = set()
    for item in manifest.get("ticket_recommendations", []):
        if not isinstance(item, dict):
            continue
        code = str(item.get("source_finding_code", "")).strip()
        if code.startswith(("EXEC", "REF")):
            codes.add(code)
    return codes


def summarize_source_regressions(findings: list[Any], repair_basis_manifest: dict[str, Any]) -> dict[str, Any]:
    baseline_codes = repair_basis_source_codes(repair_basis_manifest) if isinstance(repair_basis_manifest, dict) else set()
    comparison_available = bool(
        isinstance(repair_basis_manifest, dict)
        and baseline_codes
    )
    pre_existing_codes = baseline_codes if comparison_available else set()
    post_findings = [
        finding
        for finding in findings
        if getattr(finding, "code", "").startswith(("EXEC", "REF"))
    ]
    post_codes = {getattr(finding, "code", "") for finding in post_findings if getattr(finding, "code", "")}
    introduced_critical_codes = (
        sorted(
            {
                getattr(finding, "code", "")
                for finding in post_findings
                if getattr(finding, "code", "") not in pre_existing_codes
                and (
                    (getattr(finding, "code", "").startswith("EXEC") and getattr(finding, "severity", "") == "error")
                    or getattr(finding, "code", "") in {"REF-001", "REF-002"}
                )
            }
        )
        if comparison_available
        else []
    )
    return {
        "comparison_available": comparison_available,
        "pre_existing_codes": sorted(pre_existing_codes),
        "persistent_codes": sorted(pre_existing_codes & post_codes),
        "resolved_codes": sorted(pre_existing_codes - post_codes),
        "introduced_codes": sorted(post_codes - pre_existing_codes),
        "introduced_critical_codes": introduced_critical_codes,
    }


def summarize_disposition_shadow_mode(repair_basis_manifest: dict[str, Any]) -> dict[str, Any]:
    bundle = load_disposition_bundle(repair_basis_manifest) if isinstance(repair_basis_manifest, dict) else None
    deltas = bundle_shadow_mode_deltas(bundle)
    return {
        "bundle_available": bundle is not None,
        "bundle_version": bundle.get("version") if isinstance(bundle, dict) else None,
        "bundle_finding_count": bundle.get("finding_count") if isinstance(bundle, dict) else None,
        "delta_count": len(deltas),
        "deltas": deltas,
    }


def remediation_follow_up_script_path() -> Path:
    return Path(__file__).resolve().parents[2] / "ticket-pack-builder" / "scripts" / "apply_remediation_follow_up.py"


def create_remediation_follow_up_tickets(repo_root: Path, diagnosis_manifest_or_dir: str) -> dict[str, Any]:
    diagnosis_path = Path(diagnosis_manifest_or_dir)
    manifest_path = diagnosis_path / "manifest.json" if diagnosis_path.is_dir() else diagnosis_path
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        return {"created_tickets": []}

    result = subprocess.run(
        [
            sys.executable,
            str(remediation_follow_up_script_path()),
            str(repo_root),
            "--diagnosis",
            str(diagnosis_path),
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(
            "Unable to create repair remediation follow-up tickets.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
    payload = json.loads(result.stdout) if result.stdout.strip() else {"created_tickets": []}
    return payload if isinstance(payload, dict) else {"created_tickets": []}


def classify_verification_findings(findings: list[Any]) -> dict[str, list[Any]]:
    managed_blockers: list[Any] = []
    source_follow_up: list[Any] = []
    manual_prerequisites: list[Any] = []
    process_state_only: list[Any] = []
    advisory: list[Any] = []
    for finding in findings:
        disposition_class = disposition_class_for_finding(finding)
        if disposition_class == "source_follow_up":
            source_follow_up.append(finding)
        elif disposition_class == "process_state_only":
            process_state_only.append(finding)
        elif disposition_class == "manual_prerequisite_blocker":
            manual_prerequisites.append(finding)
        elif disposition_class == "advisory":
            advisory.append(finding)
        else:
            managed_blockers.append(finding)
    return {
        "managed_blockers": managed_blockers,
        "source_follow_up": source_follow_up,
        "manual_prerequisites": manual_prerequisites,
        "process_state_only": process_state_only,
        "advisory": advisory,
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
    regression_summary: dict[str, list[str]],
) -> dict[str, Any]:
    blocking_findings = [*classes["managed_blockers"], *classes["manual_prerequisites"]]
    managed_repair_verified = (
        performed
        and not blocking_findings
        and not regression_summary["introduced_critical_codes"]
        and (not basis_requires_causal_replay or bool(supporting_logs))
    )
    current_state_clean = (
        managed_repair_verified
        and not classes["source_follow_up"]
        and not classes["process_state_only"]
        and not pending_process_verification
    )
    causal_regression_verified = managed_repair_verified and not regression_summary["introduced_critical_codes"]
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
        "advisory_codes": [getattr(finding, "code", "") for finding in classes["advisory"]],
        "pending_process_verification": pending_process_verification,
        "verification_basis": "transcript_backed" if basis_requires_causal_replay else "current_state_only",
        "basis_requires_causal_replay": basis_requires_causal_replay,
        "repair_basis_path": str(repair_basis_path) if repair_basis_path else None,
        "current_state_clean": current_state_clean,
        "causal_regression_verified": causal_regression_verified,
        "source_regression_summary": regression_summary,
        "contract_failures": contract_failures,
        "contract_passed": not contract_failures,
        "verification_passed": causal_regression_verified and not contract_failures,
        "supporting_logs": [str(path) for path in supporting_logs],
    }


def update_repair_follow_on_state(
    repo_root: Path,
    *,
    outcome: str,
    required_stage_details: list[dict[str, Any]],
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
        "required_stage_details": required_stage_details,
        "required_stages": required_stage_names,
        "completed_stages": completed_stage_names,
        "asserted_completed_stages": asserted_stage_names,
        "legacy_asserted_completed_stages": asserted_stage_names,
        "stage_completion_mode": "legacy_manual_assertion",
        "tracking_mode": "persistent_recorded_state",
        "follow_on_state_path": str(FOLLOW_ON_TRACKING_PATH).replace("\\", "/"),
        "recorded_stage_state": tracking_state.get("stage_records", {}),
        "pruned_unknown_stages": tracking_state.get("pruned_unknown_stages", []),
        "invalidated_recorded_stages": invalidated_recorded_stage_names(tracking_state),
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
            try:
                repair_result = apply_repair(
                    repo_root,
                    rendered_root,
                    args.change_summary,
                    preserve_backups=args.preserve_backups,
                )
            except RepairEscalation as exc:
                payload = {
                    "repair_plan": {
                        "repo_root": str(repo_root),
                        "replaced_surfaces": [],
                        "stale_surface_map": {},
                    },
                    "execution_record": {
                        "repo_root": str(repo_root),
                        "repair_package_commit": current_package_commit(),
                        "repair_follow_on_outcome": "managed_blocked",
                        "blocking_reasons": [
                            "Managed repair requires operator approval before intent-changing workflow contract changes can be applied."
                        ],
                        "handoff_allowed": False,
                        "repair_escalation_path": str(REPAIR_ESCALATION_PATH).replace("\\", "/"),
                    },
                    "repair_escalation": exc.payload,
                }
                write_json(repo_root / EXECUTION_RECORD_PATH, payload)
                print(json.dumps(payload, indent=2))
                return 2
            replaced_surfaces = repair_result["replaced_surfaces"]
        # Sync restart surfaces with the initial managed_blocked workflow state before the
        # verification audit runs.  Without this early sync the audit sees the pre-repair
        # START-HERE.md and always fires WFLOW010 as a false positive.  That false positive
        # cascades into a contract_failure ("restart_surface_drift_after_repair") which forces
        # managed_blocked even when the only real drift was the transient pre-audit lag.
        regenerate_restart_surfaces(
            repo_root,
            reason=args.change_summary,
            source="scafforge-repair",
        )

    # Auto-fix deterministic ticket graph contradictions (WFLOW019) before the
    # verification audit runs.  This is a safe data-only repair: it removes the
    # source_ticket_id from depends_on when both point at the same parent
    # (ordering is already encoded by source_ticket_id), removes self-referencing
    # source_ticket_id fields, and syncs follow_up_ticket_ids bidirectionally.
    # These are always correct repairs — no intent is changed.
    _repair_ticket_graph_contradictions(repo_root)

    candidate_tempdir = None
    verification_root = repo_root
    if not args.skip_deterministic_refresh:
        candidate_tempdir = tempfile.TemporaryDirectory(prefix="scafforge-repair-candidate-")
        candidate_root = Path(candidate_tempdir.name) / "candidate"
        shutil.copytree(repo_root, candidate_root)
        regenerate_restart_surfaces(
            candidate_root,
            reason=args.change_summary,
            source="scafforge-repair",
        )
        verification_root = candidate_root

    repair_basis = resolve_repair_basis(repo_root, args.repair_basis_diagnosis)
    repair_basis_path = repair_basis[0] if repair_basis else None
    repair_basis_manifest = repair_basis[1] if repair_basis else {}
    if isinstance(repair_basis_manifest, dict) and repair_basis_manifest.get("package_work_required_first") is True:
        raise SystemExit(
            "The selected repair basis still requires Scafforge package work first. "
            "Run one fresh post-package revalidation audit after the package changes land, then repair from that diagnosis pack."
        )
    basis_requires_causal_replay = repair_basis_requires_causal_replay(repo_root, args.supporting_log, repair_basis)
    logs = verification_logs(verification_root, args.supporting_log, repair_basis)
    findings = [] if args.skip_verify else audit_repo(verification_root, logs=logs)
    pending_process_verification = load_pending_process_verification(verification_root)
    finding_classes = classify_verification_findings(findings)
    regression_summary = summarize_source_regressions(findings, repair_basis_manifest)
    disposition_shadow_mode = summarize_disposition_shadow_mode(repair_basis_manifest)
    verification_status = summarize_verification(
        findings,
        pending_process_verification,
        not args.skip_verify,
        logs,
        finding_classes,
        basis_requires_causal_replay=basis_requires_causal_replay,
        repair_basis_path=repair_basis_path,
        regression_summary=regression_summary,
    )
    verification_status["disposition_shadow_mode"] = disposition_shadow_mode

    if not args.skip_verify and basis_requires_causal_replay and not logs:
        verification_status["verification_passed"] = False
        verification_status["causal_regression_verified"] = False

    if candidate_tempdir is not None:
        candidate_tempdir.cleanup()

    try:
        required_follow_on = derive_required_follow_on_stages(repo_root, findings, replaced_surfaces, pending_process_verification)
        required_follow_on = [
            {
                **item,
                "stage": normalize_follow_on_stage_names([item["stage"]])[0],
            }
            for item in required_follow_on
        ]
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    required_stage_names = [item["stage"] for item in required_follow_on]
    stale_surface_map = build_stale_surface_map(
        repo_root,
        replaced_surfaces,
        findings,
        pending_process_verification,
        required_stage_names=set(required_stage_names),
    )
    try:
        requested_stage_names = normalize_follow_on_stage_names(args.stage_complete)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    asserted_stage_names = sorted(set(requested_stage_names))
    tracking_state = update_follow_on_tracking_state(
        repo_root,
        required_follow_on=required_follow_on,
        asserted_stage_names=asserted_stage_names,
        repair_basis_path=repair_basis_path,
        repair_package_commit=current_package_commit(),
    )
    tracking_state, auto_detected_recorded_stage_names = auto_record_stage_completion_from_canonical_evidence(
        repo_root,
        tracking_state,
        required_stage_names=required_stage_names,
        repair_package_commit=current_package_commit(),
    )
    persisted_completed_stage_names = completed_stage_names(tracking_state)
    recorded_execution_stage_list = recorded_execution_stage_names(tracking_state)
    invalidated_recorded_stage_list = invalidated_recorded_stage_names(tracking_state)
    completed_stage_name_set = set(persisted_completed_stage_names)
    if not args.skip_deterministic_refresh:
        completed_stage_name_set.add("deterministic-refresh")

    executed_stages = [{"stage": "deterministic-refresh", "status": "completed"}] if not args.skip_deterministic_refresh else []
    for stage in requested_stage_names:
        executed_stages.append({"stage": stage, "status": "asserted_completed", "completion_mode": "legacy_manual_assertion"})

    recorded_stage_results = []
    for stage in persisted_completed_stage_names:
        if stage in asserted_stage_names:
            continue
        record = tracking_state.get("stage_records", {}).get(stage, {})
        recorded_stage_results.append(
            {
                "stage": stage,
                "status": "recorded_completed",
                "completion_mode": record.get("completion_mode", "legacy_manual_assertion"),
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
    elif verification_status["source_regression_summary"]["introduced_critical_codes"]:
        blocking_reasons.append(
            "Post-repair verification introduced new critical execution or reference findings: "
            + ", ".join(verification_status["source_regression_summary"]["introduced_critical_codes"])
            + "."
        )
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
        required_stage_details=required_follow_on,
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
    remediation_follow_up: dict[str, Any] | None = None
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
        diagnosis_target = diagnosis_pack.get("path") if isinstance(diagnosis_pack, dict) else None
        if isinstance(diagnosis_target, str) and diagnosis_target.strip():
            remediation_follow_up = create_remediation_follow_up_tickets(repo_root, diagnosis_target)
            if remediation_follow_up.get("created_tickets"):
                regenerate_restart_surfaces(
                    repo_root,
                    reason="Refined repair follow-up tickets after managed repair.",
                    source="scafforge-repair",
                    verification_passed=verification_status["verification_passed"],
                )

    if not args.skip_deterministic_refresh:
        update_latest_repair_history(
            repo_root,
            repair_result["repair_id"],
            {
                "audit_findings_addressed": sorted(repair_routed_codes_from_manifest(repair_basis_manifest)) if isinstance(repair_basis_manifest, dict) else [],
                "verification_passed": verification_status["verification_passed"],
                "verification_findings": verification_status["codes"],
                "verification_summary": verification_status,
                "remediation_ticket_ids": (
                    remediation_follow_up.get("created_tickets", []) if isinstance(remediation_follow_up, dict) else []
                ),
            },
        )

    payload = {
        "repair_plan": {
            "repo_root": str(repo_root),
            "required_follow_on_stages": required_follow_on,
            "replaced_surfaces": replaced_surfaces,
            "diff_summary": repair_result.get("diff_summary", {}) if not args.skip_deterministic_refresh else {},
            "backup_path": repair_result.get("backup_path") if not args.skip_deterministic_refresh else None,
            "stale_surface_map": stale_surface_map,
        },
        "stage_results": executed_stages + recorded_stage_results + deferred_stages + skipped_stages,
        "execution_record": {
            "repo_root": str(repo_root),
            "repair_package_commit": current_package_commit(),
            "repair_basis_path": str(repair_basis_path) if repair_basis_path else None,
            "required_follow_on_stages": required_stage_names,
            "required_follow_on_stage_details": required_follow_on,
            "executed_stages": executed_stages,
            "recorded_completed_stages": persisted_completed_stage_names,
            "recorded_execution_completed_stages": recorded_execution_stage_list,
            "auto_detected_recorded_stages": auto_detected_recorded_stage_names,
            "pruned_unknown_stages": tracking_state.get("pruned_unknown_stages", []),
            "invalidated_recorded_stages": invalidated_recorded_stage_list,
            "asserted_completed_stages": asserted_stage_names,
            "legacy_asserted_completed_stages": asserted_stage_names,
            "stage_completion_mode": "legacy_manual_assertion",
            "follow_on_tracking_mode": "persistent_recorded_state",
            "follow_on_state_path": str(FOLLOW_ON_TRACKING_PATH).replace("\\", "/"),
            "follow_on_tracking_state": tracking_state,
            "deferred_stages": deferred_stages,
            "skipped_stages": skipped_stages,
            "blocking_reasons": blocking_reasons,
            "repair_follow_on_outcome": repair_follow_on_outcome,
            "verification_status": verification_status,
            "disposition_shadow_mode": disposition_shadow_mode,
            "handoff_allowed": handoff_allowed,
            "diff_summary": repair_result.get("diff_summary", {}) if not args.skip_deterministic_refresh else {},
            "backup_path": repair_result.get("backup_path") if not args.skip_deterministic_refresh else None,
            "repair_escalation_path": str(REPAIR_ESCALATION_PATH).replace("\\", "/"),
            "remediation_ticket_ids": (
                remediation_follow_up.get("created_tickets", []) if isinstance(remediation_follow_up, dict) else []
            ),
            "stale_surface_map": stale_surface_map,
        },
        "repair_follow_on_state": repair_follow_on_state,
    }
    if diagnosis_pack:
        payload["diagnosis_pack"] = diagnosis_pack
    if remediation_follow_up:
        payload["remediation_follow_up"] = remediation_follow_up

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
