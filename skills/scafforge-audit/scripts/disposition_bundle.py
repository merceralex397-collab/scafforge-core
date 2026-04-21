from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from shared_verifier_types import Finding


DISPOSITION_CLASSES = (
    "managed_blocker",
    "manual_prerequisite_blocker",
    "source_follow_up",
    "process_state_only",
    "advisory",
)
PACKAGE_MANAGED_EXEC_CODES = {"EXEC-GODOT-006"}


def evidence_grade_for_finding(finding: Finding) -> str:
    code = getattr(finding, "code", "")
    if code.startswith("SESSION"):
        return "transcript-backed and repo-validated"
    if code.startswith("ENV"):
        return "host evidence plus repo-state validation"
    if getattr(finding, "evidence", []):
        return "repo-state validation"
    return "current-state validation"


def defect_label_for_class(disposition_class: str) -> str:
    if disposition_class == "managed_blocker":
        return "package defect"
    if disposition_class == "source_follow_up":
        return "repo-local defect"
    if disposition_class == "manual_prerequisite_blocker":
        return "host prerequisite"
    if disposition_class == "process_state_only":
        return "process-state follow-up"
    return "advisory"


def ownership_summary_for_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    package_codes = [
        entry["code"]
        for entry in entries
        if entry.get("disposition_class") == "managed_blocker"
    ]
    repo_codes = [
        entry["code"]
        for entry in entries
        if entry.get("disposition_class") == "source_follow_up"
    ]
    manual_codes = [
        entry["code"]
        for entry in entries
        if entry.get("disposition_class") == "manual_prerequisite_blocker"
    ]
    if package_codes and repo_codes:
        overall = "mixed defect"
    elif package_codes:
        overall = "package defect"
    elif repo_codes:
        overall = "repo-local defect"
    elif manual_codes:
        overall = "host prerequisite"
    else:
        overall = "advisory"
    return {
        "overall": overall,
        "package_defect_codes": package_codes,
        "repo_local_defect_codes": repo_codes,
        "manual_prerequisite_codes": manual_codes,
    }


def _manifest_tickets(repo_root: str | Path | None) -> list[dict[str, Any]]:
    if not repo_root:
        return []
    manifest_path = Path(repo_root) / "tickets" / "manifest.json"
    if not manifest_path.exists():
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    tickets = manifest.get("tickets") if isinstance(manifest, dict) else None
    return [ticket for ticket in tickets if isinstance(ticket, dict)] if isinstance(tickets, list) else []


def _ticket_is_open(ticket: dict[str, Any]) -> bool:
    resolution_state = str(ticket.get("resolution_state", "")).strip().lower()
    status = str(ticket.get("status", "")).strip().lower()
    return status != "done" and resolution_state not in {"done", "superseded", "closed"}


def _repo_has_open_finish_validation(repo_root: str | Path | None) -> bool:
    return any(
        str(ticket.get("id", "")).strip() == "FINISH-VALIDATE-001" and _ticket_is_open(ticket)
        for ticket in _manifest_tickets(repo_root)
    )


def _repo_has_open_remediation_ticket(repo_root: str | Path | None) -> bool:
    return any(
        _ticket_is_open(ticket)
        and (
            str(ticket.get("id", "")).strip().startswith("REMED-")
            or str(ticket.get("lane", "")).strip() == "remediation"
        )
        for ticket in _manifest_tickets(repo_root)
    )


def repo_has_godot_smoke_guard(repo_root: str | Path | None) -> bool:
    if repo_root is None:
        return False
    smoke_test_path = Path(repo_root) / ".opencode" / "tools" / "smoke_test.ts"
    if not smoke_test_path.exists():
        return False
    try:
        smoke_test = smoke_test_path.read_text(encoding="utf-8")
    except Exception:
        return False
    return (
        "tooling_parse_warning" in smoke_test
        and "commandBlocksPass" in smoke_test
        and "failed to load script" in smoke_test.lower()
    )


def _repo_supports_acceptance_refresh(repo_root: str | Path | None) -> bool:
    if repo_root is None:
        return False
    root = Path(repo_root)
    workflow_lib = (root / ".opencode" / "lib" / "workflow.ts").read_text(encoding="utf-8") if (root / ".opencode" / "lib" / "workflow.ts").exists() else ""
    issue_intake = (root / ".opencode" / "tools" / "issue_intake.ts").read_text(encoding="utf-8") if (root / ".opencode" / "tools" / "issue_intake.ts").exists() else ""
    ticket_update = (root / ".opencode" / "tools" / "ticket_update.ts").read_text(encoding="utf-8") if (root / ".opencode" / "tools" / "ticket_update.ts").exists() else ""
    team_leader_candidates = list((root / ".opencode" / "agents").glob("*team-leader.md"))
    team_leader = team_leader_candidates[0].read_text(encoding="utf-8") if team_leader_candidates else ""
    return (
        "needs_acceptance_refresh" in workflow_lib
        and "acceptanceRefreshRequired" in issue_intake
        and "needs_acceptance_refresh" in issue_intake
        and 'kind: "acceptance-refresh"' in ticket_update
        and "needs_acceptance_refresh" in ticket_update
        and "ticket_update(acceptance=[...])" in team_leader
    )


def disposition_class_for_finding(finding: Finding, repo_root: str | Path | None = None) -> str:
    code = getattr(finding, "code", "")
    severity = getattr(finding, "severity", "")
    if severity == "info":
        return "advisory"
    if code.startswith("SESSION"):
        return "advisory"
    if code.startswith("ENV"):
        return "manual_prerequisite_blocker"
    if code in PACKAGE_MANAGED_EXEC_CODES:
        if code == "EXEC-GODOT-006" and (
            _repo_has_open_finish_validation(repo_root)
            or repo_has_godot_smoke_guard(repo_root)
        ):
            return "source_follow_up"
        return "managed_blocker"
    if code.startswith(("EXEC", "REF")):
        return "source_follow_up"
    if code == "WFLOW008":
        return "process_state_only"
    if code == "WFLOW033":
        return "source_follow_up" if _repo_supports_acceptance_refresh(repo_root) else "managed_blocker"
    if code.startswith(("BOOT", "CYCLE", "SESSION", "SKILL", "MODEL", "CONFIG")):
        return "managed_blocker"
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
        disposition_class = disposition_class_for_finding(finding, repo_root=repo_root)
        legacy_class = legacy_disposition_class_for_finding(finding)
        recommendation = recommendation_map.get(code, {})
        entry = {
            "code": code,
            "severity": getattr(finding, "severity", ""),
            "disposition_class": disposition_class,
            "defect_label": defect_label_for_class(disposition_class),
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
        "ownership_summary": ownership_summary_for_entries(entries),
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
