from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from shared_verifier_types import Finding


@dataclass(frozen=True)
class RepairCycleAuditContext:
    read_json: Callable[[Path], Any]
    normalize_path: Callable[[Path, Path], str]
    add_finding: Callable[[list[Finding], Finding], None]
    parse_iso_timestamp: Callable[[Any], datetime | None]
    current_package_commit: Callable[[], str]
    load_latest_previous_diagnosis: Callable[[Path], tuple[Path, dict[str, Any]] | None]
    load_previous_diagnoses: Callable[[Path], list[tuple[datetime, Path, dict[str, Any]]]]
    manifest_diagnosis_kind: Callable[[dict[str, Any]], str]
    manifest_package_commit: Callable[[dict[str, Any]], str | None]
    manifest_supporting_logs: Callable[[dict[str, Any]], list[str]]
    repair_routed_codes_from_manifest: Callable[[dict[str, Any]], set[str]]


def audit_failed_repair_cycle(root: Path, findings: list[Finding], ctx: RepairCycleAuditContext) -> None:
    latest_previous = ctx.load_latest_previous_diagnosis(root)
    if latest_previous is None:
        return

    diagnosis_path, manifest = latest_previous
    provenance_path = root / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = ctx.read_json(provenance_path)
    repair_history = provenance.get("repair_history") if isinstance(provenance, dict) and isinstance(provenance.get("repair_history"), list) else []
    diagnosis_generated_at = ctx.parse_iso_timestamp(manifest.get("generated_at"))
    if diagnosis_generated_at is None:
        return

    repairs_after_diagnosis: list[str] = []
    for item in repair_history:
        if not isinstance(item, dict):
            continue
        repaired_at = ctx.parse_iso_timestamp(item.get("repaired_at") or item.get("timestamp"))
        if repaired_at and repaired_at > diagnosis_generated_at:
            repairs_after_diagnosis.append(str(item.get("summary", "repair run after diagnosis")).strip() or "repair run after diagnosis")

    if not repairs_after_diagnosis:
        return

    previous_codes = ctx.repair_routed_codes_from_manifest(manifest)
    if not previous_codes:
        return

    current_codes = {finding.code for finding in findings}
    repeated_codes = sorted(code for code in (previous_codes & current_codes) if code != "WFLOW008")
    if not repeated_codes:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="CYCLE001",
            severity="error",
            problem="A previous audit-to-repair cycle did not clear one or more workflow-layer findings before work resumed.",
            root_cause="The repo contains a prior diagnosis pack and a later repair history entry, but the current audit still reproduces workflow-layer findings. That means the previous repair either skipped a required regeneration step, used stale package logic, or misclassified drift as protected intent.",
            files=[
                ctx.normalize_path(diagnosis_path / "manifest.json", root),
                ctx.normalize_path(provenance_path, root),
            ],
            safer_pattern="Before another repair run, compare the latest diagnosis pack against repair_history, identify which findings persisted, and treat repeated deprecated package-managed drift as a repair failure to fix rather than as preserved intent.",
            evidence=[
                f"Latest prior diagnosis pack: {ctx.normalize_path(diagnosis_path, root)}",
                f"Repairs recorded after that diagnosis: {len(repairs_after_diagnosis)}",
                f"Repeated workflow-layer findings: {', '.join(repeated_codes)}",
                *[f"Repair after diagnosis -> {summary}" for summary in repairs_after_diagnosis[:3]],
            ],
            provenance="script",
        ),
    )


def audit_repeated_diagnosis_churn(root: Path, findings: list[Finding], ctx: RepairCycleAuditContext) -> None:
    diagnoses = ctx.load_previous_diagnoses(root)
    if len(diagnoses) < 2:
        return

    current_codes = {
        finding.code
        for finding in findings
        if not finding.code.startswith(("EXEC", "ENV"))
    }
    if not current_codes:
        return

    _, latest_path, latest_manifest = diagnoses[-1]
    latest_generated_at = ctx.parse_iso_timestamp(latest_manifest.get("generated_at"))
    if latest_generated_at is None:
        return

    same_day = [item for item in diagnoses if item[0].date() == latest_generated_at.date()]
    if len(same_day) < 2:
        return

    provenance_path = root / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = ctx.read_json(provenance_path)
    repair_history = provenance.get("repair_history") if isinstance(provenance, dict) and isinstance(provenance.get("repair_history"), list) else []
    if any(
        (repaired_at := ctx.parse_iso_timestamp(item.get("repaired_at") or item.get("timestamp"))) and repaired_at > latest_generated_at
        for item in repair_history
        if isinstance(item, dict)
    ):
        return

    repeated_codes: set[str] = set()
    compared_packs: list[str] = []
    current_package = ctx.current_package_commit()
    for _, diagnosis_path, manifest in same_day[-4:]:
        if ctx.manifest_package_commit(manifest) != current_package:
            continue
        codes = ctx.repair_routed_codes_from_manifest(manifest)
        overlap = current_codes & codes
        if overlap:
            compared_packs.append(ctx.normalize_path(diagnosis_path, root))
            repeated_codes.update(overlap)

    if not repeated_codes:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="CYCLE002",
            severity="error",
            problem="Repeated diagnosis packs are re-reporting the same repair-routed findings without any intervening package or process-version change.",
            root_cause="Audit kept producing new diagnosis packs even though the repo had no later Scafforge repair or workflow-contract change after the latest diagnosis. That creates audit churn instead of new decision-making evidence.",
            files=[
                ctx.normalize_path(latest_path / "manifest.json", root),
                ctx.normalize_path(provenance_path, root),
            ],
            safer_pattern="Stop rerunning subject-repo audit until Scafforge package work changes the managed workflow contract or process version, then rerun one fresh audit against the updated package.",
            evidence=[
                f"Same-day diagnosis packs considered: {len(same_day)} on {latest_generated_at.date().isoformat()}",
                f"Latest diagnosis pack without later repair: {ctx.normalize_path(latest_path, root)}",
                f"Current audit package commit: {current_package}",
                f"Repeated repair-routed findings: {', '.join(sorted(repeated_codes))}",
                f"Compared packs: {', '.join(compared_packs[:4])}",
            ],
            provenance="script",
        ),
    )


def audit_verification_basis_regression(root: Path, findings: list[Finding], ctx: RepairCycleAuditContext) -> None:
    diagnoses = ctx.load_previous_diagnoses(root)
    if len(diagnoses) < 2:
        return

    transcript_basis: tuple[datetime, Path, dict[str, Any], set[str]] | None = None
    false_clean_pack: tuple[datetime, Path, dict[str, Any]] | None = None

    for generated_at, diagnosis_path, manifest in diagnoses:
        logs = ctx.manifest_supporting_logs(manifest)
        repair_codes = ctx.repair_routed_codes_from_manifest(manifest)
        if logs and repair_codes:
            transcript_basis = (generated_at, diagnosis_path, manifest, repair_codes)
            false_clean_pack = None
            continue
        if transcript_basis is None:
            continue
        if generated_at <= transcript_basis[0]:
            continue
        if generated_at.date() != transcript_basis[0].date():
            continue
        if logs:
            continue
        if manifest.get("finding_count") != 0:
            continue
        if ctx.manifest_diagnosis_kind(manifest) == "initial_diagnosis":
            continue
        false_clean_pack = (generated_at, diagnosis_path, manifest)

    if transcript_basis is None or false_clean_pack is None:
        return

    basis_generated_at, basis_path, _, basis_codes = transcript_basis
    false_clean_generated_at, false_clean_path, _ = false_clean_pack
    provenance_path = root / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = ctx.read_json(provenance_path)
    repair_history = provenance.get("repair_history") if isinstance(provenance, dict) and isinstance(provenance.get("repair_history"), list) else []
    repairs_after_basis = [
        item
        for item in repair_history
        if isinstance(item, dict)
        and (repaired_at := ctx.parse_iso_timestamp(item.get("repaired_at") or item.get("timestamp")))
        and repaired_at > basis_generated_at
    ]

    ctx.add_finding(
        findings,
        Finding(
            code="CYCLE003",
            severity="error",
            problem="A later zero-finding diagnosis pack dropped the earlier transcript evidence basis, so the workflow was recorded as clean without proving the original trap was eliminated.",
            root_cause="Verification re-ran audit against current repo state only. Because the transcript-backed repair basis was not carried forward automatically, a later diagnosis pack could report zero findings without replaying the causal deadlock conditions that triggered repair.",
            files=[
                ctx.normalize_path(basis_path / "manifest.json", root),
                ctx.normalize_path(false_clean_path / "manifest.json", root),
                ctx.normalize_path(provenance_path, root),
            ],
            safer_pattern="Carry forward supporting logs automatically into repair verification, emit the post-repair diagnosis pack from the repair runner itself, and distinguish current-state cleanliness from causal-regression verification before calling the workflow clean.",
            evidence=[
                f"Transcript-backed diagnosis basis: {ctx.normalize_path(basis_path, root)}",
                f"Basis repair-routed findings: {', '.join(sorted(basis_codes))}",
                f"Later zero-finding pack without supporting logs: {ctx.normalize_path(false_clean_path, root)}",
                f"False-clean pack generated at {false_clean_generated_at.isoformat()} after transcript basis at {basis_generated_at.isoformat()}",
                f"Repairs recorded after transcript basis: {len(repairs_after_basis)}",
            ],
            provenance="script",
        ),
    )


def run_repair_cycle_audits(root: Path, findings: list[Finding], ctx: RepairCycleAuditContext) -> None:
    audit_failed_repair_cycle(root, findings, ctx)
    audit_repeated_diagnosis_churn(root, findings, ctx)
    audit_verification_basis_regression(root, findings, ctx)
