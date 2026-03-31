from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from test_support.scafforge_harness import AUDIT, PUBLIC_REPAIR, ROOT, run_json


DEFAULT_SOURCE_REPO = Path("/home/rowan/GPTTalker")
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "gpttalker-validation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Scafforge migration behavior against the live GPTTalker repo using a disposable temp copy."
    )
    parser.add_argument("--source-repo", type=Path, default=DEFAULT_SOURCE_REPO, help="Path to the live GPTTalker repo.")
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
        raise RuntimeError(f"Unable to read git status for {repo_root}:\n{result.stderr}")
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


def build_summary(source_repo: Path, probe_root: Path, audit_payload: dict[str, Any], repair_payload: dict[str, Any]) -> dict[str, Any]:
    execution_record = repair_payload["execution_record"]
    diagnosis_pack = repair_payload.get("diagnosis_pack", {})
    manifest = diagnosis_pack.get("manifest", {}) if isinstance(diagnosis_pack, dict) else {}
    normalized_findings = [normalize_finding(probe_root, finding) for finding in audit_payload.get("findings", []) if isinstance(finding, dict)]
    normalized_recommendations = [
        normalize_ticket_recommendation(probe_root, recommendation)
        for recommendation in manifest.get("ticket_recommendations", [])
        if isinstance(recommendation, dict)
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_repo_path": str(source_repo),
        "source_repo_git_status": git_status(source_repo),
        "audit": {
            "finding_count": audit_payload.get("finding_count"),
            "codes": [finding.get("code") for finding in normalized_findings],
            "findings": normalized_findings,
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
            "stale_surface_map": execution_record.get("stale_surface_map", {}),
            "ticket_recommendations": normalized_recommendations,
        },
    }


def write_summary_report(output_dir: Path, summary: dict[str, Any]) -> None:
    audit = summary["audit"]
    repair = summary["managed_repair"]
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
        "## Audit Findings",
        "",
        f"- finding_count: `{audit['finding_count']}`",
        f"- codes: `{', '.join(audit['codes'])}`",
        "",
        "## Managed Repair Outcome",
        "",
        f"- repair_follow_on_outcome: `{repair['repair_follow_on_outcome']}`",
        f"- handoff_allowed: `{repair['handoff_allowed']}`",
        f"- required_follow_on_stages: `{', '.join(repair['required_follow_on_stages']) or 'none'}`",
        "",
        "## Blocking Reasons",
        "",
    ]
    for reason in repair["blocking_reasons"]:
        report_lines.append(f"- {reason}")
    report_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The live GPTTalker repo does not validate cleanly yet.",
            "- The current Scafforge package does route the repo into bounded, explicit follow-on instead of a silent deadlock.",
            "- The remaining blockers are truthful and actionable: repo-local skill regeneration, ticket follow-up for live EXEC failures, and host git identity.",
        ]
    )
    write_markdown(output_dir / "latest.md", report_lines)


def main() -> int:
    args = parse_args()
    source_repo = args.source_repo.resolve()
    if not source_repo.exists():
        raise RuntimeError(f"Source repo does not exist: {source_repo}")
    summary: dict[str, Any]
    with tempfile.TemporaryDirectory(prefix="scafforge-gpttalker-validation-") as workspace_root:
        probe_root = Path(workspace_root) / source_repo.name
        shutil.copytree(source_repo, probe_root)
        audit_payload = run_json(
            [str(Path("python3")), str(AUDIT), str(probe_root), "--format", "json", "--no-diagnosis-pack"],
            ROOT,
        )
        repair_payload = run_json(
            [str(Path("python3")), str(PUBLIC_REPAIR), str(probe_root)],
            ROOT,
            allow_returncodes={0, 3},
        )
        issues = validate_invariants(audit_payload, repair_payload)
        if issues:
            raise RuntimeError("GPTTalker migration validation invariants failed:\n- " + "\n- ".join(issues))
        summary = build_summary(source_repo, probe_root, audit_payload, repair_payload)
    write_json(args.output_dir / "latest.json", summary)
    write_summary_report(args.output_dir, summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
