from __future__ import annotations

from collections import Counter
from typing import Any

from shared_verifier_types import Finding


DISPOSITION_CLASSES = (
    "managed_blocker",
    "manual_prerequisite_blocker",
    "source_follow_up",
    "process_state_only",
    "advisory",
)


def evidence_grade_for_finding(finding: Finding) -> str:
    code = getattr(finding, "code", "")
    if code.startswith("SESSION"):
        return "transcript-backed and repo-validated"
    if code.startswith("ENV"):
        return "host evidence plus repo-state validation"
    if getattr(finding, "evidence", []):
        return "repo-state validation"
    return "current-state validation"


def disposition_class_for_finding(finding: Finding) -> str:
    code = getattr(finding, "code", "")
    severity = getattr(finding, "severity", "")
    if severity == "info":
        return "advisory"
    if code.startswith(("EXEC", "REF")):
        return "source_follow_up"
    if code == "WFLOW008":
        return "process_state_only"
    if code.startswith(("ENV", "BOOT", "CYCLE", "SESSION", "SKILL", "MODEL")):
        return "manual_prerequisite_blocker"
    if code.startswith("WFLOW"):
        return "managed_blocker"
    return "managed_blocker" if severity in {"error", "warning"} else "advisory"


def legacy_disposition_class_for_finding(finding: Finding) -> str:
    code = getattr(finding, "code", "")
    severity = getattr(finding, "severity", "")
    if severity == "info":
        return "advisory"
    if code.startswith(("EXEC", "REF")):
        return "source_follow_up"
    if code == "WFLOW008":
        return "process_state_only"
    if code.startswith("ENV"):
        return "manual_prerequisite_blocker"
    return "managed_blocker" if severity in {"error", "warning"} else "advisory"


def recommendation_lookup(recommendations: list[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for recommendation in recommendations or []:
        if not isinstance(recommendation, dict):
            continue
        linked_codes = recommendation.get("source_finding_codes")
        if isinstance(linked_codes, list) and linked_codes:
            codes = [str(code).strip() for code in linked_codes if str(code).strip()]
        else:
            code = str(recommendation.get("source_finding_code", "")).strip()
            codes = [code] if code else []
        for code in codes:
            lookup[code] = recommendation
    return lookup


def build_disposition_bundle(
    findings: list[Finding],
    recommendations: list[dict[str, Any]] | None,
    *,
    generated_at: str,
    repo_root: str,
    audit_package_commit: str,
) -> dict[str, Any]:
    recommendation_map = recommendation_lookup(recommendations)
    entries: list[dict[str, Any]] = []
    deltas: list[dict[str, Any]] = []
    for finding in findings:
        code = getattr(finding, "code", "")
        disposition_class = disposition_class_for_finding(finding)
        legacy_class = legacy_disposition_class_for_finding(finding)
        recommendation = recommendation_map.get(code, {})
        entry = {
            "code": code,
            "severity": getattr(finding, "severity", ""),
            "disposition_class": disposition_class,
            "legacy_disposition_class": legacy_class,
            "route": recommendation.get("route"),
            "repair_class": recommendation.get("repair_class"),
            "evidence_grade": evidence_grade_for_finding(finding),
            "source_files": list(getattr(finding, "files", [])),
            "provenance": getattr(finding, "provenance", "script"),
        }
        entries.append(entry)
        if disposition_class != legacy_class:
            deltas.append(
                {
                    "code": code,
                    "legacy_disposition_class": legacy_class,
                    "disposition_class": disposition_class,
                    "route": entry["route"],
                    "reason": (
                        f"Legacy prefix classification would label {code} as {legacy_class}, but the authoritative bundle assigns {disposition_class}."
                    ),
                }
            )

    counts = Counter(entry["disposition_class"] for entry in entries)
    return {
        "version": 1,
        "generated_at": generated_at,
        "repo_root": repo_root,
        "audit_package_commit": audit_package_commit,
        "allowed_classes": list(DISPOSITION_CLASSES),
        "finding_count": len(entries),
        "findings": entries,
        "counts": {name: counts.get(name, 0) for name in DISPOSITION_CLASSES},
        "shadow_mode_deltas": deltas,
    }


def load_disposition_bundle(manifest: dict[str, Any]) -> dict[str, Any] | None:
    bundle = manifest.get("disposition_bundle")
    return bundle if isinstance(bundle, dict) else None


def bundle_source_follow_up_codes(bundle: dict[str, Any] | None) -> set[str]:
    if not isinstance(bundle, dict):
        return set()
    findings = bundle.get("findings") if isinstance(bundle.get("findings"), list) else []
    return {
        str(item.get("code", "")).strip()
        for item in findings
        if isinstance(item, dict)
        and str(item.get("code", "")).strip()
        and str(item.get("disposition_class", "")).strip() == "source_follow_up"
    }


def bundle_repair_routed_codes(bundle: dict[str, Any] | None) -> set[str]:
    if not isinstance(bundle, dict):
        return set()
    findings = bundle.get("findings") if isinstance(bundle.get("findings"), list) else []
    return {
        str(item.get("code", "")).strip()
        for item in findings
        if isinstance(item, dict)
        and str(item.get("code", "")).strip()
        and str(item.get("route", "")).strip() == "scafforge-repair"
    }


def bundle_shadow_mode_deltas(bundle: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(bundle, dict):
        return []
    deltas = bundle.get("shadow_mode_deltas")
    return [item for item in deltas if isinstance(item, dict)] if isinstance(deltas, list) else []
