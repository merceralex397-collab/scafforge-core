from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from test_support.gpttalker_fixture_builders import build_fixture_family
from test_support.scafforge_harness import AUDIT, PUBLIC_REPAIR, ROOT, run_json
from test_support.repo_seeders import seed_legacy_contract_state


DEFAULT_FIXTURE_SLUG = "restart-surface-drift-after-repair"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "gpttalker-validation"
LEGACY_MIGRATION_STAGE = "legacy-contract-migration"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Scafforge migration behavior against a disposable GPTTalker fixture or an explicit source repo."
    )
    parser.add_argument(
        "--source-repo",
        type=Path,
        help="Optional path to a GPTTalker-style source repo. Defaults to a freshly built curated fixture.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the committed validation summary and markdown report will be written.",
    )
    return parser.parse_args()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def write_markdown(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def git_status(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "status", "--short", "--branch"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"git status unavailable for {repo_root}: {result.stderr.strip()}"
    return result.stdout.strip()


def relative_to_repo(repo_root: Path, path_text: str | None) -> str | None:
    if not path_text:
        return None
    path = Path(path_text)
    try:
        return str(path.relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        return path_text


def normalize_path_list(repo_root: Path, values: list[Any]) -> list[Any]:
    normalized: list[Any] = []
    for value in values:
        if isinstance(value, str):
            normalized.append(relative_to_repo(repo_root, value))
        else:
            normalized.append(value)
    return normalized


def normalize_finding(repo_root: Path, finding: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(finding)
    files = normalized.get("files")
    if isinstance(files, list):
        normalized["files"] = normalize_path_list(repo_root, files)
    evidence = normalized.get("evidence")
    if isinstance(evidence, list):
        normalized["evidence"] = [item.replace(str(repo_root) + "/", "") if isinstance(item, str) else item for item in evidence]
    return normalized


def normalize_ticket_recommendation(repo_root: Path, recommendation: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(recommendation)
    source_files = normalized.get("source_files")
    if isinstance(source_files, list):
        normalized["source_files"] = normalize_path_list(repo_root, source_files)
    return normalized


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def capture_repo_state(repo_root: Path) -> dict[str, Any]:
    provenance = read_json(repo_root / ".opencode" / "meta" / "bootstrap-provenance.json")
    workflow = read_json(repo_root / ".opencode" / "state" / "workflow-state.json")
    migration_history = provenance.get("migration_history") if isinstance(provenance, dict) and isinstance(provenance.get("migration_history"), list) else []
    repair_history = provenance.get("repair_history") if isinstance(provenance, dict) and isinstance(provenance.get("repair_history"), list) else []
    provenance_contract = provenance.get("workflow_contract") if isinstance(provenance, dict) and isinstance(provenance.get("workflow_contract"), dict) else {}
    repair_follow_on = workflow.get("repair_follow_on") if isinstance(workflow, dict) and isinstance(workflow.get("repair_follow_on"), dict) else {}
    start_here = read_text(repo_root / "START-HERE.md")
    context_snapshot = read_text(repo_root / ".opencode" / "state" / "context-snapshot.md")
    latest_handoff = read_text(repo_root / ".opencode" / "state" / "latest-handoff.md")
    return {
        "provenance": provenance,
        "workflow": workflow,
        "provenance_process_version": provenance_contract.get("process_version") if isinstance(provenance_contract.get("process_version"), int) else None,
        "workflow_process_version": workflow.get("process_version") if isinstance(workflow, dict) and isinstance(workflow.get("process_version"), int) else None,
        "repair_follow_on_process_version": repair_follow_on.get("process_version") if isinstance(repair_follow_on.get("process_version"), int) else None,
        "migration_history_count": len(migration_history),
        "migration_history_latest": migration_history[-1] if migration_history else None,
        "repair_history_count": len(repair_history),
        "repair_history_latest": repair_history[-1] if repair_history else None,
        "restart_truth": {
            "start_here_process_version_7": "- process_version: 7" in start_here,
            "start_here_pending_process_verification": "- pending_process_verification: true" in start_here,
            "context_process_version_7": "- process_version: 7" in context_snapshot,
            "context_pending_process_verification": "- pending_process_verification: true" in context_snapshot,
            "latest_handoff_process_version_7": "- process_version: 7" in latest_handoff,
            "latest_handoff_pending_process_verification": "- pending_process_verification: true" in latest_handoff,
        },
    }


def run_validation_cycle(
    source_repo: Path,
    scenario_name: str,
    *,
    mutate: Callable[[Path], None] | None = None,
    allow_returncodes: set[int] | None = None,
) -> dict[str, Any]:
    allowed = allow_returncodes or {0, 3}
    with tempfile.TemporaryDirectory(prefix=f"scafforge-gpttalker-validation-{scenario_name}-") as workspace_root:
        probe_root = Path(workspace_root) / source_repo.name
        shutil.copytree(source_repo, probe_root)
        if mutate is not None:
            mutate(probe_root)
        before_state = capture_repo_state(probe_root)
        audit_payload = run_json(
            [str(Path("python3")), str(AUDIT), str(probe_root), "--format", "json", "--no-diagnosis-pack"],
            ROOT,
        )
        repair_payload = run_json(
            [str(Path("python3")), str(PUBLIC_REPAIR), str(probe_root)],
            ROOT,
            allow_returncodes=allowed,
        )
        after_state = capture_repo_state(probe_root)
        return {
            "scenario": scenario_name,
            "probe_root": str(probe_root),
            "before": before_state,
            "after": after_state,
            "audit": audit_payload,
            "repair": repair_payload,
        }


def resolve_source_repo(source_repo: Path | None) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if source_repo is not None:
        resolved = source_repo.resolve()
        if not resolved.exists():
            raise RuntimeError(f"Source repo does not exist: {resolved}")
        return resolved, None

    fixture_workspace = tempfile.TemporaryDirectory(prefix="scafforge-gpttalker-fixture-")
    fixture_root = Path(fixture_workspace.name) / DEFAULT_FIXTURE_SLUG
    build_fixture_family(DEFAULT_FIXTURE_SLUG, fixture_root)
    return fixture_root, fixture_workspace


def validate_invariants(audit_payload: dict[str, Any], repair_payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    findings = audit_payload.get("findings")
    if not isinstance(findings, list) or not findings:
        issues.append("GPTTalker audit did not produce actionable findings.")
    execution_record = repair_payload.get("execution_record")
    if not isinstance(execution_record, dict):
        issues.append("Managed repair did not emit a structured execution_record.")
        return issues
    stale_surface_map = execution_record.get("stale_surface_map")
    if not isinstance(stale_surface_map, dict):
        issues.append("Managed repair did not emit a stale-surface map.")
    required_stage_details = execution_record.get("required_follow_on_stage_details")
    if not isinstance(required_stage_details, list):
        issues.append("Managed repair did not emit required_follow_on_stage_details.")
    blocking_reasons = execution_record.get("blocking_reasons")
    if not isinstance(blocking_reasons, list):
        issues.append("Managed repair did not emit blocking_reasons.")
    handoff_allowed = execution_record.get("handoff_allowed")
    if blocking_reasons and handoff_allowed is not False:
        issues.append("Managed repair reported blockers but still allowed handoff.")

    audit_codes = {item.get("code") for item in findings if isinstance(item, dict)}
    required_stages = set(execution_record.get("required_follow_on_stages", []))
    if "SKILL001" in audit_codes and "project-skill-bootstrap" not in required_stages:
        issues.append("SKILL001 was present but managed repair did not route project-skill-bootstrap.")
    exec_codes = {code for code in audit_codes if isinstance(code, str) and code.startswith("EXEC")}
    if exec_codes and "ticket-pack-builder" not in required_stages:
        issues.append("EXEC* findings were present but managed repair did not route ticket-pack-builder.")
    if required_stages and execution_record.get("repair_follow_on_outcome") == "clean":
        issues.append("Managed repair reported required follow-on stages but still emitted a clean outcome.")
    return issues


def validate_control_scenario(result: dict[str, Any]) -> list[str]:
    issues = validate_invariants(result["audit"], result["repair"])
    migration_stage = result["repair"].get("execution_record", {}).get("migration_stage", {})
    if migration_stage.get("state") not in {"current", "migrated"}:
        issues.append("Control scenario did not report a current or migrated migration state.")
    return issues


def validate_safe_upgrade_scenario(result: dict[str, Any]) -> list[str]:
    issues = validate_invariants(result["audit"], result["repair"])
    execution_record = result["repair"].get("execution_record", {})
    migration_stage = execution_record.get("migration_stage", {})
    before = result["before"]
    after = result["after"]
    if migration_stage.get("policy") != "safe_auto_upgrade":
        issues.append("Safe legacy scenario did not classify as a safe auto-upgrade.")
    if migration_stage.get("state") != "migrated":
        issues.append("Safe legacy scenario did not finish in migrated state.")
    if migration_stage.get("migration_history_recorded") is not True:
        issues.append("Safe legacy scenario did not record migration history.")
    expected_target = migration_stage.get("target_process_version")
    if after.get("provenance_process_version") != expected_target:
        issues.append(f"Safe legacy scenario did not persist the target provenance process version {expected_target}.")
    if after.get("workflow_process_version") != expected_target:
        issues.append(f"Safe legacy scenario did not persist the target workflow process version {expected_target}.")
    if after.get("repair_follow_on_process_version") != expected_target:
        issues.append(f"Safe legacy scenario did not persist the target repair_follow_on process version {expected_target}.")
    if after.get("migration_history_count") != before.get("migration_history_count", 0) + 1:
        issues.append("Safe legacy scenario did not append exactly one migration-history entry.")
    if after.get("repair_history_count") != before.get("repair_history_count", 0) + 1:
        issues.append("Safe legacy scenario did not append exactly one repair-history entry.")
    if not all(after.get("restart_truth", {}).values()):
        issues.append("Safe legacy scenario did not truthfully republish the restart surfaces after upgrade.")
    latest_migration = after.get("migration_history_latest")
    if not isinstance(latest_migration, dict):
        issues.append("Safe legacy scenario did not persist a migration-history entry.")
    else:
        if latest_migration.get("repair_id") != execution_record.get("repair_id"):
            issues.append("Safe legacy migration history did not link back to the repair run.")
        if latest_migration.get("state") != "migrated":
            issues.append("Safe legacy migration history did not record migrated state.")
        if latest_migration.get("process_version_before") != 6 or latest_migration.get("process_version_after") != expected_target:
            issues.append("Safe legacy migration history did not preserve the expected version transition.")
    return issues


def validate_blocked_scenario(result: dict[str, Any], *, expected_policy: str) -> list[str]:
    issues = []
    repair_payload = result["repair"]
    execution_record = repair_payload.get("execution_record")
    escalation = repair_payload.get("repair_escalation")
    before = result["before"]
    after = result["after"]
    if not isinstance(execution_record, dict):
        issues.append("Blocked migration scenario did not emit an execution_record.")
        return issues
    migration_stage = execution_record.get("migration_stage", {})
    if not isinstance(escalation, dict):
        issues.append("Blocked migration scenario did not emit a repair escalation payload.")
    if execution_record.get("repair_follow_on_outcome") != "managed_blocked":
        issues.append("Blocked migration scenario did not fail closed as managed_blocked.")
    if migration_stage.get("state") != "blocked":
        issues.append("Blocked migration scenario did not report blocked migration state.")
    if migration_stage.get("policy") != expected_policy:
        issues.append(f"Blocked migration scenario did not classify as {expected_policy}.")
    if not migration_stage.get("reasons"):
        issues.append("Blocked migration scenario did not record any migration reasons.")
    if not escalation or escalation.get("attempted_operation") != LEGACY_MIGRATION_STAGE:
        issues.append("Blocked migration scenario did not record the legacy migration escalation path.")
    if after.get("migration_history_count") != before.get("migration_history_count", 0):
        issues.append("Blocked migration scenario unexpectedly changed migration history.")
    if after.get("repair_history_count") != before.get("repair_history_count", 0):
        issues.append("Blocked migration scenario unexpectedly changed repair history.")
    if after.get("provenance_process_version") != before.get("provenance_process_version"):
        issues.append("Blocked migration scenario unexpectedly changed the bootstrap provenance process version.")
    if after.get("workflow_process_version") != before.get("workflow_process_version"):
        issues.append("Blocked migration scenario unexpectedly changed the workflow process version.")
    if after.get("restart_truth") != before.get("restart_truth"):
        issues.append("Blocked migration scenario unexpectedly changed the restart surfaces.")
    return issues


def scenario_summary(result: dict[str, Any]) -> dict[str, Any]:
    probe_root = Path(result["probe_root"])
    audit_payload = result["audit"]
    repair_payload = result["repair"]
    execution_record = repair_payload.get("execution_record", {})
    diagnosis_pack = repair_payload.get("diagnosis_pack", {})
    manifest = diagnosis_pack.get("manifest", {}) if isinstance(diagnosis_pack, dict) else {}
    normalized_findings = [normalize_finding(probe_root, finding) for finding in audit_payload.get("findings", []) if isinstance(finding, dict)]
    normalized_recommendations = [
        normalize_ticket_recommendation(probe_root, recommendation)
        for recommendation in manifest.get("ticket_recommendations", [])
        if isinstance(recommendation, dict)
    ]
    before = result["before"]
    after = result["after"]
    return {
        "scenario": result["scenario"],
        "probe_root": result["probe_root"],
        "audit": {
            "finding_count": audit_payload.get("finding_count"),
            "codes": [finding.get("code") for finding in normalized_findings],
            "findings": normalized_findings,
        },
        "migration": {
            "before": {
                "provenance_process_version": before.get("provenance_process_version"),
                "migration_history_count": before.get("migration_history_count"),
                "repair_history_count": before.get("repair_history_count"),
                "workflow_process_version": before.get("workflow_process_version"),
                "repair_follow_on_process_version": before.get("repair_follow_on_process_version"),
            },
            "after": {
                "provenance_process_version": after.get("provenance_process_version"),
                "workflow_process_version": after.get("workflow_process_version"),
                "repair_follow_on_process_version": after.get("repair_follow_on_process_version"),
                "migration_history_count": after.get("migration_history_count"),
                "repair_history_count": after.get("repair_history_count"),
                "migration_history_latest": after.get("migration_history_latest"),
                "repair_history_latest": after.get("repair_history_latest"),
                "restart_truth": after.get("restart_truth", {}),
            },
            "stage": execution_record.get("migration_stage", {}),
            "repair_escalation": repair_payload.get("repair_escalation"),
        },
        "managed_repair": {
            "repair_package_commit": execution_record.get("repair_package_commit"),
            "repair_basis_path": relative_to_repo(probe_root, execution_record.get("repair_basis_path")),
            "required_follow_on_stages": execution_record.get("required_follow_on_stages", []),
            "required_follow_on_stage_details": execution_record.get("required_follow_on_stage_details", []),
            "blocking_reasons": execution_record.get("blocking_reasons", []),
            "repair_follow_on_outcome": execution_record.get("repair_follow_on_outcome"),
            "handoff_allowed": execution_record.get("handoff_allowed"),
            "verification_status": {
                **execution_record.get("verification_status", {}),
                "repair_basis_path": relative_to_repo(
                    probe_root,
                    execution_record.get("verification_status", {}).get("repair_basis_path"),
                ),
                "supporting_logs": normalize_path_list(
                    probe_root,
                    execution_record.get("verification_status", {}).get("supporting_logs", []),
                ),
            },
            "migration_stage": execution_record.get("migration_stage", {}),
            "stale_surface_map": execution_record.get("stale_surface_map", {}),
            "ticket_recommendations": normalized_recommendations,
        },
    }


def build_summary(source_repo: Path, scenario_results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_repo_path": str(source_repo),
        "source_repo_git_status": git_status(source_repo),
        "scenarios": [scenario_summary(result) for result in scenario_results],
    }


def write_summary_report(output_dir: Path, summary: dict[str, Any]) -> None:
    report_lines = [
        "# GPTTalker Migration Validation",
        "",
        f"- generated_at: `{summary['generated_at']}`",
        f"- source_repo_path: `{summary['source_repo_path']}`",
        "",
        "## Source Repo State",
        "",
        "```text",
        summary["source_repo_git_status"],
        "```",
        "",
    ]

    for scenario in summary["scenarios"]:
        migration = scenario["migration"]
        managed_repair = scenario["managed_repair"]
        report_lines.extend(
            [
                f"## Scenario: {scenario['scenario']}",
                "",
                f"- migration_policy: `{migration['stage'].get('policy')}`",
                f"- migration_state: `{migration['stage'].get('state')}`",
                f"- repair_follow_on_outcome: `{managed_repair['repair_follow_on_outcome']}`",
                f"- handoff_allowed: `{managed_repair['handoff_allowed']}`",
                f"- migration_history_count_before: `{migration['before']['migration_history_count']}`",
                f"- migration_history_count_after: `{migration['after']['migration_history_count']}`",
                f"- repair_history_count_before: `{migration['before']['repair_history_count']}`",
                f"- repair_history_count_after: `{migration['after']['repair_history_count']}`",
                f"- provenance_process_version_after: `{migration['after']['provenance_process_version']}`",
                f"- workflow_process_version_after: `{migration['after']['workflow_process_version']}`",
                f"- pending_process_verification_after: `{migration['after']['restart_truth'].get('start_here_pending_process_verification')}`",
                f"- restart_surface_truth: `{', '.join(f'{key}={value}' for key, value in migration['after']['restart_truth'].items())}`",
                f"- audit_codes: `{', '.join(scenario['audit']['codes'])}`",
            ]
        )
        if managed_repair["blocking_reasons"]:
            report_lines.append("")
            report_lines.append("### Blocking Reasons")
            for reason in managed_repair["blocking_reasons"]:
                report_lines.append(f"- {reason}")
        if migration.get("repair_escalation"):
            report_lines.append("")
            report_lines.append("### Escalation")
            report_lines.append(f"- attempted_operation: `{migration['repair_escalation'].get('attempted_operation')}`")
            for reason in migration["repair_escalation"].get("reasons", []):
                report_lines.append(f"- {reason}")
        report_lines.append("")

    report_lines.extend(
        [
            "## Interpretation",
            "",
            "- Control and safe-legacy scenarios validate the current migration path and the upgrade proof trail.",
            "- Blocked scenarios demonstrate that too-old or structurally inconsistent legacy repos fail closed before ordinary repair mutation.",
            "- Safe upgrades record migration history separately from repair history so later repair runs can distinguish migrated repos from untouched legacy ones.",
        ]
    )
    write_markdown(output_dir / "latest.md", report_lines)


def main() -> int:
    args = parse_args()
    source_repo, fixture_workspace = resolve_source_repo(args.source_repo)
    try:
        control_result = run_validation_cycle(source_repo, "control")
        safe_legacy_result = run_validation_cycle(
            source_repo,
            "safe-legacy-upgrade",
            mutate=lambda repo_root: seed_legacy_contract_state(repo_root, process_version=6),
        )
        too_old_result = run_validation_cycle(
            source_repo,
            "too-old-escalation",
            mutate=lambda repo_root: seed_legacy_contract_state(repo_root, process_version=5),
            allow_returncodes={2},
        )
        structural_mismatch_result = run_validation_cycle(
            source_repo,
            "structural-mismatch-escalation",
            mutate=lambda repo_root: seed_legacy_contract_state(
                repo_root,
                process_version=6,
                repair_follow_on_process_version=5,
            ),
            allow_returncodes={2},
        )

        issues: list[str] = []
        issues.extend(validate_control_scenario(control_result))
        issues.extend(validate_safe_upgrade_scenario(safe_legacy_result))
        issues.extend(validate_blocked_scenario(too_old_result, expected_policy="too_old"))
        issues.extend(validate_blocked_scenario(structural_mismatch_result, expected_policy="structurally_unsafe"))
        if issues:
            raise RuntimeError("GPTTalker migration validation invariants failed:\n- " + "\n- ".join(issues))

        summary = build_summary(source_repo, [control_result, safe_legacy_result, too_old_result, structural_mismatch_result])
        write_json(args.output_dir / "latest.json", summary)
        write_summary_report(args.output_dir, summary)
        print(json.dumps(summary, indent=2))
        return 0
    finally:
        if fixture_workspace is not None:
            fixture_workspace.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
