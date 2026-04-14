from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scafforge-audit" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from target_completion import (
    ANDROID_EXPORT_LANE,
    ANDROID_EXPORT_TICKET_ID,
    ANDROID_RELEASE_LANE,
    ANDROID_RELEASE_TICKET_ID,
    ANDROID_SIGNING_LANE,
    ANDROID_SIGNING_TICKET_ID,
    declares_godot_android_target,
    expected_android_debug_apk_relpath,
    requires_packaged_android_product,
)

RUNTIME_SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scafforge-pivot" / "scripts"
if str(RUNTIME_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SCRIPT_DIR))

from shared_generated_tool_runtime import run_generated_tool


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalize_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def find_latest_diagnosis(repo_root: Path) -> Path:
    diagnosis_root = repo_root / "diagnosis"
    if not diagnosis_root.exists():
        raise SystemExit("No diagnosis directory exists under the target repo.")
    candidates = sorted(
        [path for path in diagnosis_root.iterdir() if path.is_dir() and (path / "manifest.json").exists()],
        key=lambda item: item.name,
    )
    if not candidates:
        raise SystemExit("No diagnosis packs with manifest.json were found under diagnosis/.")
    return candidates[-1] / "manifest.json"


def resolve_diagnosis_path(repo_root: Path, provided: str | None) -> Path:
    if not provided:
        return find_latest_diagnosis(repo_root)
    path = Path(provided).expanduser().resolve()
    if path.is_dir():
        manifest_path = path / "manifest.json"
        if manifest_path.exists():
            return manifest_path
        raise SystemExit(f"Diagnosis directory does not contain manifest.json: {path}")
    if path.is_file():
        return path
    raise SystemExit(f"Diagnosis path does not exist: {path}")


def load_ticket_recommendations(diagnosis_manifest: Path) -> list[dict[str, Any]]:
    payload = read_json(diagnosis_manifest)
    if isinstance(payload, dict):
        if isinstance(payload.get("ticket_recommendations"), list):
            return [item for item in payload["ticket_recommendations"] if isinstance(item, dict)]
        managed_repair = payload.get("managed_repair")
        if isinstance(managed_repair, dict) and isinstance(managed_repair.get("ticket_recommendations"), list):
            return [item for item in managed_repair["ticket_recommendations"] if isinstance(item, dict)]
    return []


def next_wave(manifest: dict[str, Any]) -> int:
    waves = [int(ticket.get("wave", 0)) for ticket in manifest.get("tickets", []) if isinstance(ticket, dict)]
    return (max(waves) + 1) if waves else 0


_REMEDIATION_RELEASE_EXCLUDED_LANES: frozenset[str] = frozenset(
    {"android-export", "signing-prerequisites", "release-readiness", "remediation", "reverification"}
)


def _terminal_feature_ids_from_manifest(tickets: list[Any], release_ticket_id: str) -> list[str]:
    """Return IDs of all max-wave non-infrastructure tickets in an existing manifest.

    Excludes infrastructure, remediation, reverification lanes and any ticket whose
    source_ticket_id points to the release ticket (avoids selecting RELEASE-001 descendants).
    Returns [] when no eligible candidates exist.
    """
    candidates = [
        t for t in tickets
        if isinstance(t, dict)
        and t.get("lane") not in _REMEDIATION_RELEASE_EXCLUDED_LANES
        and str(t.get("id", "")).strip() != release_ticket_id
        and str(t.get("source_ticket_id", "")).strip() != release_ticket_id
        and int(t.get("wave", 0)) > 0
    ]
    if not candidates:
        return []
    max_wave = max(int(t.get("wave", 0)) for t in candidates)
    return [str(t["id"]) for t in candidates if int(t.get("wave", 0)) == max_wave]



def active_open_ticket(manifest: dict[str, Any]) -> dict[str, Any] | None:
    active_ticket_id = manifest.get("active_ticket")
    for ticket in manifest.get("tickets", []):
        if not isinstance(ticket, dict):
            continue
        if ticket.get("id") != active_ticket_id:
            continue
        if ticket.get("status") == "done" or ticket.get("resolution_state") == "superseded":
            return None
        return ticket
    return None


def ticket_can_be_split_scope_parent(ticket: dict[str, Any] | None) -> bool:
    if not isinstance(ticket, dict):
        return False
    status = str(ticket.get("status", "")).strip().lower()
    resolution_state = str(ticket.get("resolution_state", "")).strip().lower()
    if status == "done":
        return False
    if resolution_state in {"done", "closed", "superseded"}:
        return False
    return True


IMMUTABLE_HISTORY_PREFIX = ".opencode/state/artifacts/history/"


def collect_source_files(recommendation: dict[str, Any]) -> list[str]:
    raw_source_files = recommendation.get("affected_files") or recommendation.get("source_files") or []
    if not isinstance(raw_source_files, list):
        return []
    normalized: list[str] = []
    for item in raw_source_files:
        value = str(item).strip()
        if not value or value in normalized:
            continue
        normalized.append(value)
    return normalized


def split_source_files(source_files: list[str]) -> tuple[list[str], list[str]]:
    mutable_sources: list[str] = []
    history_sources: list[str] = []
    for path in source_files:
        if path.startswith(IMMUTABLE_HISTORY_PREFIX):
            history_sources.append(path)
        else:
            mutable_sources.append(path)
    return mutable_sources, history_sources


def build_summary(description: str, source_files: list[str]) -> str:
    mutable_sources, history_sources = split_source_files(source_files)
    surface_display = (
        ", ".join(mutable_sources)
        if mutable_sources
        else "the current writable remediation surfaces for this finding"
    )
    parts = [
        description.strip(),
        f"Affected surfaces: {surface_display}.",
    ]
    if history_sources:
        parts.append(
            "Historical evidence sources: "
            + ", ".join(history_sources)
            + ". Treat these history paths as read-only context and record superseding current evidence on this remediation ticket instead of editing immutable history artifacts directly."
        )
    return " ".join(part for part in parts if part)


def build_acceptance(recommendation: dict[str, Any]) -> list[str]:
    code = str(recommendation.get("source_finding_code") or recommendation.get("id") or "unknown")
    summary = str(recommendation.get("summary") or recommendation.get("suggested_fix_approach") or "Re-run the relevant quality checks.")
    acceptance = [
        f"The validated finding `{code}` no longer reproduces.",
        f"Current quality checks rerun with evidence tied to the fix approach: {summary}",
    ]
    _, history_sources = split_source_files(collect_source_files(recommendation))
    if history_sources:
        acceptance.append(
            "When the finding cites `.opencode/state/artifacts/history/...`, treat those paths as read-only evidence sources and capture the fix on current writable repo surfaces or current ticket artifacts instead of mutating immutable history artifacts directly."
        )
    return acceptance


def remediation_split_kind(recommendation: dict[str, Any], source_ticket_id: str | None) -> str | None:
    if not source_ticket_id:
        return None
    finding_code = str(recommendation.get("source_finding_code") or recommendation.get("id") or "").strip()
    if finding_code == "EXEC-REMED-001":
        return "parallel_independent"
    return "sequential_dependent"


def build_ticket_record(recommendation: dict[str, Any], manifest: dict[str, Any], active_ticket: dict[str, Any] | None, wave: int) -> dict[str, Any]:
    recommendation_id = str(recommendation.get("id", "")).strip()
    active_ticket_id = str(active_ticket.get("id", "")).strip() if isinstance(active_ticket, dict) else None
    source_ticket_id = active_ticket_id if active_ticket_id and active_ticket_id != recommendation_id else None
    source_mode = "split_scope" if source_ticket_id else "net_new_scope"
    split_kind = remediation_split_kind(recommendation, source_ticket_id)
    source_files = collect_source_files(recommendation)
    description = str(recommendation.get("description") or recommendation.get("summary") or recommendation.get("title") or "")
    return {
        "id": str(recommendation["id"]),
        "title": str(recommendation.get("title") or recommendation["id"]),
        "wave": wave,
        "lane": "remediation",
        "parallel_safe": False,
        "overlap_risk": "low",
        "stage": "planning",
        "status": "todo",
        "depends_on": [],
        "summary": build_summary(description, source_files),
        "acceptance": build_acceptance(recommendation),
        "decision_blockers": [],
        "artifacts": [],
        "resolution_state": "open",
        "verification_state": "suspect",
        "finding_source": str(recommendation.get("source_finding_code") or recommendation.get("id") or ""),
        "source_ticket_id": source_ticket_id,
        "follow_up_ticket_ids": [],
        "source_mode": source_mode,
        "split_kind": split_kind,
    }


def extract_ticket_notes(existing: str) -> str:
    marker = "\n## Notes\n\n"
    if marker not in existing:
        return ""
    return existing.split(marker, 1)[1].rstrip("\n")


def render_artifact_line(artifact: dict[str, Any]) -> str:
    summary = f" - {artifact.get('summary')}" if artifact.get("summary") else ""
    trust_state = str(artifact.get("trust_state") or "current")
    trust = f" [{trust_state}]" if trust_state != "current" else ""
    return (
        f"- {artifact.get('kind', 'artifact')}: {artifact.get('path', '')} "
        f"({artifact.get('stage', '')}){trust}{summary}"
    )


def render_artifact_lines(ticket: dict[str, Any]) -> str:
    artifacts = ticket.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return "- None yet"
    return "\n".join(
        render_artifact_line(artifact)
        for artifact in artifacts
        if isinstance(artifact, dict)
    )


def render_board(manifest: dict[str, Any]) -> str:
    rows: list[str] = []
    for ticket in manifest.get("tickets", []):
        if not isinstance(ticket, dict):
            continue
        depends_on = ticket.get("depends_on") if isinstance(ticket.get("depends_on"), list) else []
        follow_ups = (
            ticket.get("follow_up_ticket_ids")
            if isinstance(ticket.get("follow_up_ticket_ids"), list)
            else []
        )
        rows.append(
            "| {wave} | {id} | {title} | {lane} | {stage} | {status} | {resolution} | {verification} | {parallel} | {overlap} | {depends_on} | {follow_ups} |".format(
                wave=ticket.get("wave", ""),
                id=ticket.get("id", ""),
                title=ticket.get("title", ""),
                lane=ticket.get("lane", ""),
                stage=ticket.get("stage", ""),
                status=ticket.get("status", ""),
                resolution=ticket.get("resolution_state", ""),
                verification=ticket.get("verification_state", ""),
                parallel="yes" if ticket.get("parallel_safe") else "no",
                overlap=ticket.get("overlap_risk", ""),
                depends_on=", ".join(str(item) for item in depends_on) if depends_on else "-",
                follow_ups=", ".join(str(item) for item in follow_ups) if follow_ups else "-",
            )
        )
    return (
        "# Ticket Board\n\n"
        "| Wave | ID | Title | Lane | Stage | Status | Resolution | Verification | Parallel Safe | Overlap Risk | Depends On | Follow-ups |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
        + "\n".join(rows)
        + "\n"
    )


def render_ticket_document(ticket: dict[str, Any], notes: str = "") -> str:
    depends_on = ticket.get("depends_on") if isinstance(ticket.get("depends_on"), list) else []
    blockers = (
        ticket.get("decision_blockers")
        if isinstance(ticket.get("decision_blockers"), list)
        else []
    )
    acceptance = (
        ticket.get("acceptance") if isinstance(ticket.get("acceptance"), list) else []
    )
    follow_ups = (
        ticket.get("follow_up_ticket_ids")
        if isinstance(ticket.get("follow_up_ticket_ids"), list)
        else []
    )
    return (
        f"# {ticket.get('id', '')}: {ticket.get('title', '')}\n\n"
        "## Summary\n\n"
        f"{ticket.get('summary', '')}\n\n"
        "## Wave\n\n"
        f"{ticket.get('wave', '')}\n\n"
        "## Lane\n\n"
        f"{ticket.get('lane', '')}\n\n"
        "## Parallel Safety\n\n"
        f"- parallel_safe: {'true' if ticket.get('parallel_safe') else 'false'}\n"
        f"- overlap_risk: {ticket.get('overlap_risk', '')}\n\n"
        "## Stage\n\n"
        f"{ticket.get('stage', '')}\n\n"
        "## Status\n\n"
        f"{ticket.get('status', '')}\n\n"
        "## Trust\n\n"
        f"- resolution_state: {ticket.get('resolution_state', '')}\n"
        f"- verification_state: {ticket.get('verification_state', '')}\n"
        f"- finding_source: {ticket.get('finding_source') or 'None'}\n"
        f"- source_ticket_id: {ticket.get('source_ticket_id') or 'None'}\n"
        f"- source_mode: {ticket.get('source_mode') or 'None'}\n\n"
        "## Depends On\n\n"
        f"{', '.join(str(item) for item in depends_on) if depends_on else 'None'}\n\n"
        "## Follow-up Tickets\n\n"
        f"{chr(10).join(f'- {item}' for item in follow_ups) if follow_ups else 'None'}\n\n"
        "## Decision Blockers\n\n"
        f"{chr(10).join(f'- {item}' for item in blockers) if blockers else 'None'}\n\n"
        "## Acceptance Criteria\n\n"
        f"{chr(10).join(f'- [ ] {item}' for item in acceptance) if acceptance else 'None'}\n\n"
        "## Artifacts\n\n"
        f"{render_artifact_lines(ticket)}\n\n"
        "## Notes\n\n"
        f"{notes.rstrip() + chr(10) if notes.strip() else ''}"
    )


def save_manifest_surfaces(repo_root: Path, manifest: dict[str, Any]) -> None:
    manifest["version"] = max(int(manifest.get("version", 0) or 0), 3)
    tickets_dir = repo_root / "tickets"
    write_json(tickets_dir / "manifest.json", manifest)
    (tickets_dir / "BOARD.md").write_text(render_board(manifest), encoding="utf-8")
    for ticket in manifest.get("tickets", []):
        if not isinstance(ticket, dict):
            continue
        ticket_path = tickets_dir / f"{ticket.get('id', '')}.md"
        existing = ticket_path.read_text(encoding="utf-8") if ticket_path.exists() else ""
        ticket_path.write_text(
            render_ticket_document(ticket, extract_ticket_notes(existing)),
            encoding="utf-8",
        )


def remove_split_blockers(source_ticket: dict[str, Any], child_ticket_id: str) -> bool:
    blockers = source_ticket.get("decision_blockers")
    if not isinstance(blockers, list):
        return False
    ticket_id = str(source_ticket.get("id", "")).strip()
    sequential_note = (
        f"Sequential split: this ticket ({ticket_id}) must complete its parent-owned work before child ticket {child_ticket_id} may be foregrounded."
    )
    parallel_note = (
        f"Parallel split: scope delegated to follow-up ticket {child_ticket_id}. Keep the parent open and non-foreground until the child work lands."
    )
    updated_blockers = [
        item
        for item in blockers
        if str(item).strip() not in {sequential_note, parallel_note}
    ]
    if updated_blockers == blockers:
        return False
    source_ticket["decision_blockers"] = updated_blockers
    return True


def canonicalize_follow_up_parent_links(
    manifest: dict[str, Any],
    *,
    child_ticket_id: str,
    canonical_source_ticket_id: str | None,
) -> bool:
    tickets = manifest.get("tickets")
    if not isinstance(tickets, list):
        return False
    changed = False
    canonical_source = (canonical_source_ticket_id or "").strip()
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        follow_ups = ticket.get("follow_up_ticket_ids")
        if not isinstance(follow_ups, list):
            continue
        ticket_id = str(ticket.get("id", "")).strip()
        contains_child = any(str(item).strip() == child_ticket_id for item in follow_ups)
        if ticket_id == canonical_source:
            if not contains_child:
                follow_ups.append(child_ticket_id)
                changed = True
            continue
        if contains_child:
            ticket["follow_up_ticket_ids"] = [
                item for item in follow_ups if str(item).strip() != child_ticket_id
            ]
            changed = True
        if remove_split_blockers(ticket, child_ticket_id):
            changed = True
    return changed


def ticket_uses_candidate_only_surfaces(ticket: dict[str, Any]) -> bool:
    summary = str(ticket.get("summary", "")).strip()
    if "Affected surfaces:" not in summary:
        return False
    surface_block = summary.split("Affected surfaces:", 1)[1]
    if ". Historical evidence sources:" in surface_block:
        surface_block = surface_block.split(". Historical evidence sources:", 1)[0]
    surfaces = [part.strip().rstrip(".") for part in surface_block.split(",") if part.strip()]
    return bool(surfaces) and all(surface.startswith("/tmp/scafforge-repair-candidate-") for surface in surfaces)


def supersede_stale_remediation_tickets(
    manifest: dict[str, Any],
    *,
    recommended_ids: set[str],
    recommended_finding_codes: set[str],
) -> list[str]:
    tickets = manifest.get("tickets")
    if not isinstance(tickets, list):
        return []
    tickets_by_id = {
        str(ticket.get("id", "")).strip(): ticket
        for ticket in tickets
        if isinstance(ticket, dict) and str(ticket.get("id", "")).strip()
    }
    superseded_ids: list[str] = []
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        ticket_id = str(ticket.get("id", "")).strip()
        if not ticket_id or ticket_id in recommended_ids:
            continue
        if str(ticket.get("lane", "")).strip() != "remediation":
            continue
        resolution_state = str(ticket.get("resolution_state", "")).strip()
        already_superseded = ticket.get("status") == "done" and resolution_state == "superseded"
        if ticket.get("status") == "done" and not already_superseded:
            continue
        finding_source = str(ticket.get("finding_source", "")).strip()
        candidate_only_ticket = ticket_uses_candidate_only_surfaces(ticket)
        should_supersede = bool(
            finding_source
            and (
                finding_source in recommended_finding_codes
                or candidate_only_ticket
            )
        )
        if not should_supersede:
            continue
        if candidate_only_ticket and finding_source in recommended_finding_codes:
            continue
        if not candidate_only_ticket and finding_source not in recommended_finding_codes:
            continue
        changed = False
        if canonicalize_follow_up_parent_links(
            manifest,
            child_ticket_id=ticket_id,
            canonical_source_ticket_id=None,
        ):
            changed = True
        if not already_superseded:
            ticket["stage"] = "closeout"
            ticket["status"] = "done"
            ticket["resolution_state"] = "superseded"
            ticket["verification_state"] = "reverified"
            changed = True
        if changed:
            superseded_ids.append(ticket_id)
    return superseded_ids


def reconcile_existing_ticket(
    *,
    repo_root: Path,
    ticket_id: str,
    recommendation: dict[str, Any],
    manifest: dict[str, Any],
    active_ticket: dict[str, Any] | None,
    wave: int,
) -> bool:
    tickets = manifest.get("tickets")
    if not isinstance(tickets, list):
        return False
    refreshed = build_ticket_record(recommendation, manifest, active_ticket, wave)
    existing_ticket = next(
        (
            ticket
            for ticket in tickets
            if isinstance(ticket, dict) and str(ticket.get("id", "")).strip() == ticket_id
        ),
        None,
    )
    if not isinstance(existing_ticket, dict):
        return False
    changed = False
    previous_source_ticket_id = str(existing_ticket.get("source_ticket_id", "")).strip()
    for field in (
        "title",
        "summary",
        "acceptance",
        "decision_blockers",
        "finding_source",
        "source_ticket_id",
        "source_mode",
        "split_kind",
        "parallel_safe",
        "overlap_risk",
    ):
        if existing_ticket.get(field) != refreshed.get(field):
            existing_ticket[field] = refreshed.get(field)
            changed = True
    canonical_source_ticket_id = str(existing_ticket.get("source_ticket_id", "")).strip()
    if canonicalize_follow_up_parent_links(
        manifest,
        child_ticket_id=ticket_id,
        canonical_source_ticket_id=canonical_source_ticket_id or None,
    ):
        changed = True
    if previous_source_ticket_id and previous_source_ticket_id != canonical_source_ticket_id:
        changed = True
    if changed:
        save_manifest_surfaces(repo_root, manifest)
    return changed


def reconcile_manifest_ticket_record(
    manifest: dict[str, Any],
    *,
    ticket_id: str,
    refreshed: dict[str, Any],
) -> bool:
    tickets = manifest.get("tickets")
    if not isinstance(tickets, list):
        return False
    existing_ticket = next(
        (
            ticket
            for ticket in tickets
            if isinstance(ticket, dict) and str(ticket.get("id", "")).strip() == ticket_id
        ),
        None,
    )
    if not isinstance(existing_ticket, dict):
        return False
    changed = False
    for field in (
        "title",
        "lane",
        "parallel_safe",
        "overlap_risk",
        "depends_on",
        "summary",
        "acceptance",
        "decision_blockers",
        "finding_source",
        "source_ticket_id",
        "source_mode",
        "split_kind",
    ):
        if existing_ticket.get(field) != refreshed.get(field):
            existing_ticket[field] = refreshed.get(field)
            changed = True
    canonical_source_ticket_id = str(existing_ticket.get("source_ticket_id", "")).strip()
    if canonicalize_follow_up_parent_links(
        manifest,
        child_ticket_id=ticket_id,
        canonical_source_ticket_id=canonical_source_ticket_id or None,
    ):
        changed = True
    return changed


def create_ticket_via_runtime(repo_root: Path, ticket: dict[str, Any], *, activate: bool | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": ticket["id"],
        "title": ticket["title"],
        "lane": ticket["lane"],
        "wave": ticket["wave"],
        "summary": ticket["summary"],
        "acceptance": ticket["acceptance"],
    }
    if activate is not None:
        payload["activate"] = activate
    if ticket.get("depends_on"):
        payload["depends_on"] = ticket["depends_on"]
    if ticket.get("decision_blockers"):
        payload["decision_blockers"] = ticket["decision_blockers"]
    if ticket.get("parallel_safe") is not None:
        payload["parallel_safe"] = ticket["parallel_safe"]
    if ticket.get("overlap_risk"):
        payload["overlap_risk"] = ticket["overlap_risk"]
    if ticket.get("finding_source"):
        payload["finding_source"] = ticket["finding_source"]
    if ticket.get("source_ticket_id"):
        payload["source_ticket_id"] = ticket["source_ticket_id"]
    if ticket.get("source_mode"):
        payload["source_mode"] = ticket["source_mode"]
    if ticket.get("split_kind"):
        payload["split_kind"] = ticket["split_kind"]
    if ticket.get("evidence_artifact_path"):
        payload["evidence_artifact_path"] = ticket["evidence_artifact_path"]
    return run_generated_tool(repo_root, ".opencode/tools/ticket_create.ts", payload)


def append_unique(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)




def android_export_summary() -> str:
    return (
        "Create and validate the repo-local Android export surfaces for this Godot Android target. "
        "This includes an Android preset in `export_presets.cfg`, non-placeholder repo-local `android/` support surfaces, "
        "and a recorded canonical export command for downstream release work."
    )


def build_android_export_ticket(*, wave: int, source_ticket_id: str | None) -> dict[str, Any]:
    return {
        "id": ANDROID_EXPORT_TICKET_ID,
        "title": "Create Android export surfaces",
        "wave": wave,
        "lane": ANDROID_EXPORT_LANE,
        "parallel_safe": False,
        "overlap_risk": "medium",
        "stage": "planning",
        "status": "todo",
        "depends_on": [],
        "summary": android_export_summary(),
        "acceptance": [
            "`export_presets.cfg` exists and defines an Android export preset.",
            "The repo-local `android/` support surfaces exist and are non-placeholder.",
            "The canonical Android export command is recorded in this ticket and the repo-local skill pack.",
        ],
        "decision_blockers": [],
        "artifacts": [],
        "resolution_state": "open",
        "verification_state": "suspect",
        "finding_source": "WFLOW025",
        "source_ticket_id": source_ticket_id,
        "follow_up_ticket_ids": [],
        "source_mode": "split_scope" if source_ticket_id else "net_new_scope",
        "split_kind": "sequential_dependent" if source_ticket_id else None,
    }


def build_android_signing_ticket(*, wave: int, source_ticket_id: str | None) -> dict[str, Any]:
    return {
        "id": ANDROID_SIGNING_TICKET_ID,
        "title": "Own Android signing prerequisites",
        "wave": wave,
        "lane": ANDROID_SIGNING_LANE,
        "parallel_safe": False,
        "overlap_risk": "medium",
        "stage": "planning",
        "status": "todo",
        "depends_on": [ANDROID_EXPORT_TICKET_ID] if source_ticket_id != ANDROID_EXPORT_TICKET_ID else [],
        "summary": (
            "Establish signing ownership for packaged Android delivery. "
            "This includes declaring the release keystore path or CI secret reference, "
            "recording the alias and password ownership strategy, and verifying that the "
            "project can produce an authentic signed APK or AAB before RELEASE-001 closes. "
            "Scafforge does not generate keystores or secrets — the project team must own this surface."
        ),
        "acceptance": [
            "The signing keystore path or CI secret reference is declared in the canonical brief or project provenance.",
            "Keystore alias and password ownership is documented and accessible to the build pipeline.",
            "A signed release APK or AAB can be produced from the current export pipeline.",
        ],
        "decision_blockers": [
            "Signing key must be owned by the project team. Scafforge cannot generate or assume a keystore."
        ],
        "artifacts": [],
        "resolution_state": "open",
        "verification_state": "suspect",
        "finding_source": "WFLOW025",
        "source_ticket_id": source_ticket_id,
        "follow_up_ticket_ids": [],
        "source_mode": "split_scope" if source_ticket_id else "net_new_scope",
        "split_kind": "sequential_dependent" if source_ticket_id else None,
    }


def build_android_release_ticket(*, wave: int, source_ticket_id: str | None, repo_root: Path, feature_gate_ids: list[str] | None = None) -> dict[str, Any]:
    apk_relpath = expected_android_debug_apk_relpath(repo_root)
    export_command = f'godot --headless --path . --export-debug "Android Debug" {apk_relpath}'
    needs_deliverable = requires_packaged_android_product(repo_root)
    gate_ids: list[str] = list(feature_gate_ids) if feature_gate_ids else []
    depends_on: list[str] = ([ANDROID_SIGNING_TICKET_ID] + gate_ids) if needs_deliverable else gate_ids
    if source_ticket_id:
        depends_on = [ticket_id for ticket_id in depends_on if ticket_id != source_ticket_id]
    deliverable_acceptance = [
        "A signed release APK or AAB is produced once signing prerequisites are satisfied via SIGNING-001.",
        f"The signed artifact path is declared in canonical project truth.",
    ] if needs_deliverable else []
    return {
        "id": ANDROID_RELEASE_TICKET_ID,
        "title": "Build Android runnable proof" + (" and deliverable APK/AAB" if needs_deliverable else " (debug APK)"),
        "wave": wave,
        "lane": ANDROID_RELEASE_LANE,
        "parallel_safe": False,
        "overlap_risk": "medium",
        "stage": "planning",
        "status": "todo",
        "depends_on": depends_on,
        "summary": (
            f"Produce and validate the canonical debug APK runnable proof at `{apk_relpath}` using the repo's resolved Godot binary and Android export pipeline."
            + (
                " When signing prerequisites are satisfied, additionally produce a packaged signed release artifact as deliverable proof."
                if needs_deliverable else ""
            )
        ),
        "acceptance": [
            f"`{export_command}` succeeds or the exact resolved Godot binary equivalent is recorded with the same arguments.",
            f"The APK exists at `{apk_relpath}`.",
            f"`unzip -l {apk_relpath}` shows Android manifest and classes/resources content.",
            *deliverable_acceptance,
        ],
        "decision_blockers": [],
        "artifacts": [],
        "resolution_state": "open",
        "verification_state": "suspect",
        "finding_source": "WFLOW025",
        "source_ticket_id": source_ticket_id,
        "follow_up_ticket_ids": [],
        "source_mode": "split_scope" if source_ticket_id else "net_new_scope",
        "split_kind": "sequential_dependent" if source_ticket_id else None,
    }


def ensure_android_target_completion_tickets(
    *,
    repo_root: Path,
    manifest: dict[str, Any],
    active_ticket: dict[str, Any] | None,
) -> list[str]:
    if not declares_godot_android_target(repo_root):
        return []

    created_or_updated: list[str] = []
    source_ticket_id = str(active_ticket.get("id", "")).strip() if isinstance(active_ticket, dict) else None
    manifest_path = repo_root / "tickets" / "manifest.json"
    current_manifest = read_json(manifest_path)
    current_tickets = current_manifest.get("tickets", []) if isinstance(current_manifest, dict) else []
    android_record = next(
        (
            item
            for item in current_tickets
            if isinstance(item, dict) and str(item.get("id", "")).strip() == ANDROID_EXPORT_TICKET_ID
        ),
        None,
    )

    if not isinstance(android_record, dict):
        android_source_ticket_id = source_ticket_id if source_ticket_id and source_ticket_id != ANDROID_EXPORT_TICKET_ID else None
        android_ticket = build_android_export_ticket(
            wave=next_wave(current_manifest if isinstance(current_manifest, dict) else manifest),
            source_ticket_id=android_source_ticket_id,
        )
        create_ticket_via_runtime(repo_root, android_ticket, activate=False if android_source_ticket_id else None)
        created_or_updated.append(ANDROID_EXPORT_TICKET_ID)
        current_manifest = read_json(manifest_path)
        current_tickets = current_manifest.get("tickets", []) if isinstance(current_manifest, dict) else []
        android_record = next(
            (
                item
                for item in current_tickets
                if isinstance(item, dict) and str(item.get("id", "")).strip() == ANDROID_EXPORT_TICKET_ID
            ),
            None,
        )

    release_exists = any(
        isinstance(item, dict) and str(item.get("id", "")).strip() == ANDROID_RELEASE_TICKET_ID
        for item in current_tickets
    )
    # Create SIGNING-001 when the brief requires a packaged Android product and the ticket
    # doesn't exist yet.  RELEASE-001 depends on SIGNING-001 in packaged-delivery mode.
    needs_deliverable = requires_packaged_android_product(repo_root)
    signing_exists = any(
        isinstance(item, dict) and str(item.get("id", "")).strip() == ANDROID_SIGNING_TICKET_ID
        for item in current_tickets
    )
    if isinstance(android_record, dict) and needs_deliverable and not signing_exists:
        signing_wave = max(
            next_wave(current_manifest if isinstance(current_manifest, dict) else manifest),
            int(android_record.get("wave", 0)) + 1,
        )
        signing_source_ticket_id = (
            ANDROID_EXPORT_TICKET_ID if ticket_can_be_split_scope_parent(android_record) else None
        )
        signing_ticket = build_android_signing_ticket(
            wave=signing_wave,
            source_ticket_id=signing_source_ticket_id,
        )
        create_ticket_via_runtime(repo_root, signing_ticket, activate=False)
        created_or_updated.append(ANDROID_SIGNING_TICKET_ID)
        current_manifest = read_json(manifest_path)
        current_tickets = current_manifest.get("tickets", []) if isinstance(current_manifest, dict) else []
        signing_exists = True

    if isinstance(android_record, dict) and release_exists:
        release_record = next(
            (
                item
                for item in current_tickets
                if isinstance(item, dict)
                and str(item.get("id", "")).strip() == ANDROID_RELEASE_TICKET_ID
            ),
            None,
        )
        if isinstance(release_record, dict):
            release_source_ticket_id = (
                ANDROID_SIGNING_TICKET_ID
                if needs_deliverable and signing_exists
                else (
                    ANDROID_EXPORT_TICKET_ID
                    if ticket_can_be_split_scope_parent(android_record)
                    else None
                )
            )
            normalized_release_ticket = build_android_release_ticket(
                wave=int(release_record.get("wave", 0)) or next_wave(current_manifest if isinstance(current_manifest, dict) else manifest),
                source_ticket_id=release_source_ticket_id,
                repo_root=repo_root,
                feature_gate_ids=_terminal_feature_ids_from_manifest(
                    current_tickets, ANDROID_RELEASE_TICKET_ID
                ),
            )
            if reconcile_manifest_ticket_record(
                current_manifest,
                ticket_id=ANDROID_RELEASE_TICKET_ID,
                refreshed=normalized_release_ticket,
            ):
                save_manifest_surfaces(repo_root, current_manifest)
                created_or_updated.append(ANDROID_RELEASE_TICKET_ID)
                current_manifest = read_json(manifest_path)
                current_tickets = (
                    current_manifest.get("tickets", [])
                    if isinstance(current_manifest, dict)
                    else []
                )

    if isinstance(android_record, dict) and not release_exists:
        release_wave = max(
            next_wave(current_manifest if isinstance(current_manifest, dict) else manifest),
            int(android_record.get("wave", 0)) + (2 if needs_deliverable and signing_exists else 1),
        )
        feature_gate_ids = _terminal_feature_ids_from_manifest(current_tickets, ANDROID_RELEASE_TICKET_ID)
        release_source_ticket_id = (
            ANDROID_EXPORT_TICKET_ID if ticket_can_be_split_scope_parent(android_record) else None
        )
        release_ticket = build_android_release_ticket(
            wave=release_wave,
            source_ticket_id=release_source_ticket_id,
            repo_root=repo_root,
            feature_gate_ids=feature_gate_ids,
        )
        create_ticket_via_runtime(repo_root, release_ticket, activate=False)
        created_or_updated.append(ANDROID_RELEASE_TICKET_ID)
    elif release_exists:
        patched = patch_release_feature_gate(repo_root=repo_root, manifest_path=manifest_path)
        created_or_updated.extend(patched)
    return created_or_updated


def patch_release_feature_gate(*, repo_root: Path, manifest_path: Path) -> list[str]:
    """Ensure an existing RELEASE-001 has at least one product feature ticket in depends_on.

    For early-stage tickets (planning / plan_review): patches depends_on directly in manifest.json.
    For later-stage tickets: creates a REMED ticket documenting the lifecycle state mismatch and
    the stale QA evidence that must be reviewed before RELEASE-001 can legitimately close.

    Returns a list of ticket IDs that were created or updated.
    """
    current_manifest = read_json(manifest_path)
    current_tickets: list[Any] = current_manifest.get("tickets", []) if isinstance(current_manifest, dict) else []

    release_record = next(
        (t for t in current_tickets if isinstance(t, dict) and str(t.get("id", "")).strip() == ANDROID_RELEASE_TICKET_ID),
        None,
    )
    if not isinstance(release_record, dict):
        return []

    terminal_ids = _terminal_feature_ids_from_manifest(current_tickets, ANDROID_RELEASE_TICKET_ID)
    if not terminal_ids:
        return []

    existing_deps = {str(d).strip() for d in release_record.get("depends_on", [])}
    qualified_feature_ids = set(terminal_ids)
    if existing_deps & qualified_feature_ids:
        return []  # already has a qualifying feature gate

    release_stage = str(release_record.get("stage", "planning")).strip()
    early_stages = {"planning", "plan_review"}

    if release_stage in early_stages:
        # Safe to patch directly: ticket has not yet produced execution evidence
        new_deps = sorted(existing_deps | qualified_feature_ids)
        for ticket in current_tickets:
            if isinstance(ticket, dict) and str(ticket.get("id", "")).strip() == ANDROID_RELEASE_TICKET_ID:
                ticket["depends_on"] = new_deps
                break
        manifest_path.write_text(
            json.dumps(current_manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return [ANDROID_RELEASE_TICKET_ID]

    # Ticket has already advanced past planning — patching depends_on alone is not safe
    # because execution artifacts were produced before the feature gate existed.
    # Create a REMED ticket so the operator can review the lifecycle state mismatch.
    wave = next_wave(current_manifest if isinstance(current_manifest, dict) else {})
    remed_id = "REMED-RELEASE-GATE"

    # Skip if this remediation ticket already exists (idempotent on re-run).
    remed_exists = any(
        isinstance(t, dict) and str(t.get("id", "")).strip() == remed_id
        for t in current_tickets
    )
    if remed_exists:
        return [remed_id]

    remed_ticket: dict[str, Any] = {
        "id": remed_id,
        "title": "Review and reset RELEASE-001: executed before feature gate was enforced",
        "wave": wave,
        "lane": "remediation",
        "parallel_safe": False,
        "overlap_risk": "high",
        "stage": "planning",
        "status": "todo",
        "depends_on": [],
        "summary": (
            f"RELEASE-001 is at stage '{release_stage}' but has no product feature ticket in its depends_on. "
            "Its execution and QA artifacts were produced before the feature gate was in place and may be stale. "
            f"The operator must decide whether to reset RELEASE-001 to planning/todo (adding {sorted(qualified_feature_ids)} to depends_on) "
            "or supersede it with a new release ticket after the terminal feature tickets are done."
        ),
        "acceptance": [
            f"RELEASE-001.depends_on includes at least one terminal product feature ticket from: {sorted(qualified_feature_ids)}.",
            "All execution and QA artifacts produced before the feature gate was in place are invalidated or re-confirmed.",
            "RELEASE-001 lifecycle stage accurately reflects whether terminal product feature tickets are done.",
        ],
        "decision_blockers": [],
        "artifacts": [],
        "resolution_state": "open",
        "verification_state": "suspect",
        "finding_source": "WFLOW029",
        "source_ticket_id": ANDROID_RELEASE_TICKET_ID,
        "follow_up_ticket_ids": [],
        "source_mode": "split_scope",
        "split_kind": "sequential_dependent",
    }
    create_ticket_via_runtime(repo_root, remed_ticket, activate=False)
    return [remed_id]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create remediation follow-up tickets from diagnosis recommendations.")
    parser.add_argument("repo_root", help="Path to the generated repo to update.")
    parser.add_argument("--diagnosis", help="Diagnosis pack directory or manifest path. Defaults to the latest diagnosis/ pack.")
    parser.add_argument("--activate-new-ticket", action="store_true", help="Make the first created remediation ticket active immediately.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    diagnosis_manifest = resolve_diagnosis_path(repo_root, args.diagnosis)
    recommendations = [
        item
        for item in load_ticket_recommendations(diagnosis_manifest)
        if str(item.get("route", "")).strip() == "ticket-pack-builder"
    ]

    manifest_path = repo_root / "tickets" / "manifest.json"
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        manifest = {"tickets": []}
    existing_ids = {str(ticket.get("id")) for ticket in manifest.get("tickets", []) if isinstance(ticket, dict)}
    created_ids: list[str] = []
    superseded_ids: list[str] = []
    active_ticket = active_open_ticket(manifest)
    wave = next_wave(manifest)

    for recommendation in recommendations:
        ticket_id = str(recommendation.get("id", "")).strip()
        if not ticket_id:
            continue
        if ticket_id in existing_ids:
            reconcile_existing_ticket(
                repo_root=repo_root,
                ticket_id=ticket_id,
                recommendation=recommendation,
                manifest=manifest,
                active_ticket=active_ticket,
                wave=wave,
            )
            manifest = read_json(manifest_path)
            append_unique(created_ids, ticket_id)
            continue
        ticket = build_ticket_record(recommendation, manifest, active_ticket, wave)
        create_ticket_via_runtime(repo_root, ticket, activate=bool(args.activate_new_ticket and not created_ids))
        created_ids.append(ticket_id)
        existing_ids.add(ticket_id)
        manifest = read_json(manifest_path)
        active_ticket = active_open_ticket(manifest)
        wave = next_wave(manifest)

    android_follow_up_ids = ensure_android_target_completion_tickets(
        repo_root=repo_root,
        manifest=read_json(manifest_path) or {"tickets": []},
        active_ticket=active_ticket,
    )
    for ticket_id in android_follow_up_ids:
        append_unique(created_ids, ticket_id)

    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        manifest = {"tickets": []}
    recommendation_ids = {
        str(item.get("id", "")).strip()
        for item in recommendations
        if str(item.get("id", "")).strip()
    }
    recommendation_codes = {
        str(item.get("source_finding_code") or item.get("id") or "").strip()
        for item in recommendations
        if str(item.get("source_finding_code") or item.get("id") or "").strip()
    }
    superseded_ids = supersede_stale_remediation_tickets(
        manifest,
        recommended_ids=recommendation_ids,
        recommended_finding_codes=recommendation_codes,
    )
    if superseded_ids:
        save_manifest_surfaces(repo_root, manifest)

    if not created_ids and not superseded_ids:
        return 0

    print(
        json.dumps(
            {
                "created_tickets": created_ids,
                "superseded_tickets": superseded_ids,
                "diagnosis_manifest": normalize_path(diagnosis_manifest, repo_root) if diagnosis_manifest.is_relative_to(repo_root) else str(diagnosis_manifest),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
