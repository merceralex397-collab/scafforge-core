from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any
import sys

from pivot_tracking import (
    PIVOT_STATE_PATH,
    build_downstream_refresh_state,
    build_restart_surface_inputs,
    persist_pivot_state,
    pivot_stage_metadata,
)
from publish_pivot_surfaces import publish_pivot_surfaces


SHARED_VERIFIER_PATH = Path(__file__).resolve().parents[2] / "scafforge-audit" / "scripts" / "shared_verifier.py"
# Canonical persisted pivot state path inside the subject repo: .opencode/meta/pivot-state.json
PROVENANCE_PATH = Path(".opencode/meta/bootstrap-provenance.json")
CANONICAL_BRIEF_PATH = Path("docs/spec/CANONICAL-BRIEF.md")

PIVOT_CLASSES = (
    "feature-add",
    "feature-expand",
    "design-change",
    "architecture-change",
    "workflow-change",
)

FAMILIES = (
    "repo_local_skills",
    "agent_team_and_prompts",
    "managed_workflow_tools_and_prompts",
    "ticket_graph_and_lineage",
    "restart_surfaces",
)


def load_shared_verifier():
    spec = spec_from_file_location("scafforge_pivot_shared_verifier", SHARED_VERIFIER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load shared verifier from {SHARED_VERIFIER_PATH}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SHARED_VERIFIER = load_shared_verifier()
audit_repo = SHARED_VERIFIER.audit_repo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan a Scafforge pivot by updating canonical brief truth, emitting stale-surface routing, and running post-pivot verification."
    )
    parser.add_argument("repo_root", help="Repository root to pivot.")
    parser.add_argument("--pivot-class", choices=PIVOT_CLASSES, required=True)
    parser.add_argument("--requested-change", required=True, help="Human-readable summary of the requested pivot.")
    parser.add_argument("--accepted-decision", action="append", default=[], help="Accepted decision captured by this pivot. May be provided multiple times.")
    parser.add_argument("--unresolved-follow-up", action="append", default=[], help="Unresolved follow-up introduced by this pivot. May be provided multiple times.")
    parser.add_argument("--supersede-ticket", action="append", default=[], help="Existing ticket id that should be superseded by this pivot. May be provided multiple times.")
    parser.add_argument("--reopen-ticket", action="append", default=[], help="Existing ticket id that should be reopened by this pivot. May be provided multiple times.")
    parser.add_argument("--reconcile-ticket", action="append", default=[], help="Existing ticket id whose lineage should be reconciled by this pivot. May be provided multiple times.")
    parser.add_argument(
        "--lineage-evidence",
        action="append",
        default=[],
        help="Attach runtime evidence for a pivot lineage action using <ticket-id>=<repo-relative-artifact-path>. May be provided multiple times.",
    )
    parser.add_argument(
        "--replacement-source",
        action="append",
        default=[],
        help="Attach a replacement canonical source using <ticket-id>=<replacement-source-ticket-id>. May be provided multiple times.",
    )
    parser.add_argument(
        "--replacement-source-mode",
        action="append",
        default=[],
        help="Attach a replacement source_mode using <ticket-id>=<mode>. May be provided multiple times.",
    )
    parser.add_argument(
        "--affect",
        action="append",
        choices=FAMILIES,
        default=[],
        help="Explicitly mark an affected downstream contract family. When omitted, Scafforge uses a bounded default for the selected pivot class.",
    )
    parser.add_argument("--supporting-log", action="append", default=[], help="Optional transcript or session log to include in post-pivot verification.")
    parser.add_argument("--skip-verify", action="store_true", help="Skip the post-pivot verification pass.")
    parser.add_argument("--skip-publish", action="store_true", help="Skip immediate pivot restart-surface publication.")
    parser.add_argument("--format", choices=("text", "json", "both"), default="text")
    return parser.parse_args()


def current_iso_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def resolve_supporting_logs(repo_root: Path, values: list[str]) -> list[Path]:
    resolved: list[Path] = []
    seen: set[Path] = set()
    for raw in values:
        candidate = Path(raw).expanduser()
        candidate = candidate if candidate.is_absolute() else (repo_root / candidate)
        resolved_path = candidate.resolve()
        if not resolved_path.exists() or not resolved_path.is_file():
            raise SystemExit(f"--supporting-log must resolve to an existing file inside or alongside the pivoted repo: {raw}")
        if resolved_path in seen:
            continue
        seen.add(resolved_path)
        resolved.append(resolved_path)
    return resolved


def default_affected_families(pivot_class: str) -> list[str]:
    mapping = {
        "feature-add": ["ticket_graph_and_lineage", "restart_surfaces"],
        "feature-expand": ["ticket_graph_and_lineage", "restart_surfaces"],
        "design-change": ["repo_local_skills", "agent_team_and_prompts", "ticket_graph_and_lineage", "restart_surfaces"],
        "architecture-change": ["repo_local_skills", "agent_team_and_prompts", "managed_workflow_tools_and_prompts", "ticket_graph_and_lineage", "restart_surfaces"],
        "workflow-change": ["managed_workflow_tools_and_prompts", "agent_team_and_prompts", "restart_surfaces"],
    }
    return mapping[pivot_class]


def normalize_families(pivot_class: str, explicit: list[str]) -> list[str]:
    return sorted(set(default_affected_families(pivot_class)) | set(explicit))


def load_manifest(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "tickets" / "manifest.json"
    return read_json(path) if path.exists() else {}


def parse_assignment_map(values: list[str], *, flag: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw in values:
        if not isinstance(raw, str) or "=" not in raw:
            raise SystemExit(f"{flag} entries must use <ticket-id>=<value>: {raw}")
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise SystemExit(f"{flag} entries must use <ticket-id>=<value>: {raw}")
        parsed[key] = value
    return parsed


def validate_manifest_ticket_ids(manifest: dict[str, Any], ticket_ids: list[str], *, flag: str) -> list[str]:
    tickets = manifest.get("tickets") if isinstance(manifest.get("tickets"), list) else []
    known_ids = {
        str(ticket.get("id", "")).strip()
        for ticket in tickets
        if isinstance(ticket, dict) and str(ticket.get("id", "")).strip()
    }
    normalized: list[str] = []
    for raw in ticket_ids:
        ticket_id = raw.strip()
        if not ticket_id:
            continue
        if ticket_id not in known_ids:
            raise SystemExit(f"{flag} references unknown ticket id: {ticket_id}")
        normalized.append(ticket_id)
    return sorted(set(normalized))


def validate_assignment_ticket_keys(manifest: dict[str, Any], mapping: dict[str, str], *, flag: str) -> dict[str, str]:
    validate_manifest_ticket_ids(manifest, list(mapping.keys()), flag=flag)
    return mapping


def build_ticket_lineage_plan(
    repo_root: Path,
    *,
    supersede_tickets: list[str],
    reopen_tickets: list[str],
    reconcile_tickets: list[str],
    unresolved_follow_up: list[str],
    evidence_by_ticket: dict[str, str],
    replacement_source_by_ticket: dict[str, str],
    replacement_source_mode_by_ticket: dict[str, str],
) -> dict[str, Any]:
    manifest = load_manifest(repo_root)
    actions: list[dict[str, str | None]] = []
    for ticket_id in validate_manifest_ticket_ids(manifest, supersede_tickets, flag="--supersede-ticket"):
        actions.append(
            {
                "action": "supersede",
                "target_ticket_id": ticket_id,
                "summary": f"Supersede {ticket_id} because its acceptance no longer matches the pivoted brief.",
                "reason": "Pivot invalidated the prior acceptance or completion claim for this ticket.",
                "evidence_artifact_path": evidence_by_ticket.get(ticket_id),
                "replacement_source_ticket_id": replacement_source_by_ticket.get(ticket_id),
                "replacement_source_mode": replacement_source_mode_by_ticket.get(ticket_id),
            }
        )
    for ticket_id in validate_manifest_ticket_ids(manifest, reopen_tickets, flag="--reopen-ticket"):
        actions.append(
            {
                "action": "reopen",
                "target_ticket_id": ticket_id,
                "summary": f"Reopen {ticket_id} because it remains relevant but is no longer complete under the pivot.",
                "reason": "Pivot kept the underlying work valid but changed the completion boundary.",
                "evidence_artifact_path": evidence_by_ticket.get(ticket_id),
            }
        )
    for ticket_id in validate_manifest_ticket_ids(manifest, reconcile_tickets, flag="--reconcile-ticket"):
        actions.append(
            {
                "action": "reconcile",
                "target_ticket_id": ticket_id,
                "summary": f"Reconcile stale lineage for {ticket_id} under the pivoted design.",
                "reason": "Pivot changed ticket lineage or source/follow-up relationships that no longer reflect the current design.",
                "evidence_artifact_path": evidence_by_ticket.get(ticket_id),
                "replacement_source_ticket_id": replacement_source_by_ticket.get(ticket_id),
                "replacement_source_mode": replacement_source_mode_by_ticket.get(ticket_id),
            }
        )
    for follow_up in [item.strip() for item in unresolved_follow_up if item.strip()]:
        actions.append(
            {
                "action": "create_follow_up",
                "target_ticket_id": None,
                "summary": follow_up,
                "reason": "Pivot introduced explicit follow-up work that should become a new ticket instead of staying implicit.",
            }
        )
    return {"actions": actions}


def render_list(items: list[str], *, empty_label: str) -> str:
    cleaned = [item.strip() for item in items if isinstance(item, str) and item.strip()]
    if not cleaned:
        return f"- {empty_label}"
    return "\n".join(f"- {item}" for item in cleaned)


def append_pivot_history(canonical_brief_path: Path, *, timestamp: str, pivot_class: str, requested_change: str, accepted_decisions: list[str], unresolved_follow_up: list[str], affected_families: list[str]) -> None:
    existing = canonical_brief_path.read_text(encoding="utf-8") if canonical_brief_path.exists() else "# Canonical Brief\n"
    entry = (
        f"### {timestamp} — {pivot_class}\n\n"
        f"- Requested change: {requested_change.strip()}\n"
        "- Accepted decisions:\n"
        f"{render_list(accepted_decisions, empty_label='None recorded.')}\n"
        "- Unresolved follow-up:\n"
        f"{render_list(unresolved_follow_up, empty_label='None recorded.')}\n"
        "- Affected contract families:\n"
        f"{render_list(affected_families, empty_label='canonical brief only')}\n"
    )

    if "## Pivot History" not in existing:
        updated = existing.rstrip() + "\n\n## Pivot History\n\n" + entry
    else:
        updated = existing.rstrip() + "\n\n" + entry
    canonical_brief_path.write_text(updated.rstrip() + "\n", encoding="utf-8")


def stale_surface_entry(status: str, surfaces: list[str], reason: str) -> dict[str, Any]:
    return {
        "status": status,
        "surfaces": surfaces,
        "reason": reason,
    }


def build_pivot_stale_surface_map(affected_families: list[str]) -> dict[str, dict[str, Any]]:
    affected = set(affected_families)
    return {
        "canonical_brief_and_truth_docs": stale_surface_entry(
            "replace",
            ["docs/spec/CANONICAL-BRIEF.md"],
            "Pivot work always updates canonical brief truth before any derived refresh.",
        ),
        "repo_local_skills": stale_surface_entry(
            "regenerate" if "repo_local_skills" in affected else "stable",
            [".opencode/skills"] if "repo_local_skills" in affected else [],
            "Repo-local skills regenerate only when the pivot changes local procedure or project-specific capability surfaces.",
        ),
        "agent_team_and_prompts": stale_surface_entry(
            "regenerate" if "agent_team_and_prompts" in affected else "stable",
            [".opencode/agents", "docs/process/agent-catalog.md"] if "agent_team_and_prompts" in affected else [],
            "Agent-team prompts regenerate only when the pivot changes delegation, team layout, or prompt semantics.",
        ),
        "managed_workflow_tools_and_prompts": stale_surface_entry(
            "replace" if "managed_workflow_tools_and_prompts" in affected else "stable",
            [".opencode/tools", ".opencode/lib", ".opencode/plugins", ".opencode/commands", "docs/process/workflow.md"] if "managed_workflow_tools_and_prompts" in affected else [],
            "Managed workflow surfaces route through scafforge-repair only when the pivot changes workflow contract behavior.",
        ),
        "ticket_graph_and_lineage": stale_surface_entry(
            "ticket_follow_up" if "ticket_graph_and_lineage" in affected else "stable",
            ["tickets/manifest.json", "tickets/BOARD.md"] if "ticket_graph_and_lineage" in affected else [],
            "Ticket graph changes should be routed through ticket-pack-builder so supersede, reopen, and follow-up lineage stay explicit.",
        ),
        "restart_surfaces": stale_surface_entry(
            "replace" if "restart_surfaces" in affected else "stable",
            ["START-HERE.md", ".opencode/state/context-snapshot.md", ".opencode/state/latest-handoff.md"] if "restart_surfaces" in affected else [],
            "Restart surfaces must be republished when the pivot changes what the repo is doing next.",
        ),
    }


def build_downstream_refresh(affected_families: list[str]) -> list[dict[str, str]]:
    affected = set(affected_families)
    routing: list[dict[str, str]] = []
    if "repo_local_skills" in affected:
        routing.append(
            {
                **pivot_stage_metadata("project-skill-bootstrap"),
                "reason": "Pivot changed repo-local procedure or capability surfaces, so local skills need regeneration.",
            }
        )
    if "agent_team_and_prompts" in affected:
        routing.append(
            {
                **pivot_stage_metadata("opencode-team-bootstrap"),
                "reason": "Pivot changed team layout, delegation, or agent/tool boundaries.",
            }
        )
        routing.append(
            {
                **pivot_stage_metadata("agent-prompt-engineering"),
                "reason": "Pivot changed prompt behavior or delegation semantics and requires prompt hardening after regeneration.",
            }
        )
    if "ticket_graph_and_lineage" in affected:
        routing.append(
            {
                **pivot_stage_metadata("ticket-pack-builder"),
                "reason": "Pivot changed ticket lineage or introduced new work that must be superseded, reopened, reconciled, or refined.",
            }
        )
    if "managed_workflow_tools_and_prompts" in affected:
        routing.append(
            {
                **pivot_stage_metadata("scafforge-repair"),
                "reason": "Pivot changed managed workflow contract surfaces and requires safe managed refresh instead of ad hoc edits.",
            }
        )
    return routing


def update_provenance(repo_root: Path, entry: dict[str, Any]) -> None:
    provenance_path = repo_root / PROVENANCE_PATH
    provenance = read_json(provenance_path)
    if not isinstance(provenance, dict):
        provenance = {}
    history = provenance.get("pivot_history") if isinstance(provenance.get("pivot_history"), list) else []
    provenance["pivot_history"] = [*history, entry]
    provenance["last_pivot_at"] = entry["recorded_at"]
    provenance["last_pivot_class"] = entry["pivot_class"]
    write_json(provenance_path, provenance)


def summarize_verification(findings: list[Any], performed: bool, supporting_logs: list[Path]) -> dict[str, Any]:
    return {
        "performed": performed,
        "verification_kind": "post_pivot",
        "finding_count": len(findings),
        "verification_passed": not findings if performed else False,
        "codes": [getattr(finding, "code", "") for finding in findings],
        "supporting_logs": [str(path) for path in supporting_logs],
        "findings": [asdict(finding) for finding in findings],
    }


def render_text(payload: dict[str, Any]) -> str:
    if payload["verification_status"]["verification_passed"]:
        verdict = "PASS"
        summary = "pivot plan recorded and post-pivot verification passed."
    elif payload["verification_status"]["performed"]:
        verdict = "FAIL"
        summary = "pivot plan recorded but post-pivot verification found blocking issues."
    else:
        verdict = "PENDING"
        summary = "pivot plan recorded without post-pivot verification."
    lines = [
        f"{verdict}: {payload['repo_root']} {summary}",
        f"Pivot class: {payload['pivot_class']}",
        f"Requested change: {payload['requested_change']}",
        "Downstream refresh:",
    ]
    if payload["downstream_refresh"]:
        lines.extend(f"- {item['stage']}: {item['reason']}" for item in payload["downstream_refresh"])
    else:
        lines.append("- None beyond handoff-brief.")
    ticket_lineage_plan = payload.get("ticket_lineage_plan")
    if isinstance(ticket_lineage_plan, dict) and isinstance(ticket_lineage_plan.get("actions"), list):
        lines.append("Ticket lineage plan:")
        actions = ticket_lineage_plan["actions"]
        if actions:
            lines.extend(
                f"- {item['action']}: {item.get('target_ticket_id') or item.get('summary')}"
                for item in actions
                if isinstance(item, dict)
            )
        else:
            lines.append("- None.")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    lineage_requires_ticket_follow_up = any(
        item.strip()
        for group in (args.supersede_ticket, args.reopen_ticket, args.reconcile_ticket, args.unresolved_follow_up)
        for item in group
        if isinstance(item, str)
    )
    explicit_families = list(args.affect)
    if lineage_requires_ticket_follow_up and "ticket_graph_and_lineage" not in explicit_families:
        explicit_families.append("ticket_graph_and_lineage")
    affected_families = normalize_families(args.pivot_class, explicit_families)
    timestamp = current_iso_timestamp()
    canonical_brief_path = repo_root / CANONICAL_BRIEF_PATH
    canonical_brief_path.parent.mkdir(parents=True, exist_ok=True)
    append_pivot_history(
        canonical_brief_path,
        timestamp=timestamp,
        pivot_class=args.pivot_class,
        requested_change=args.requested_change,
        accepted_decisions=args.accepted_decision,
        unresolved_follow_up=args.unresolved_follow_up,
        affected_families=affected_families,
    )

    stale_surface_map = build_pivot_stale_surface_map(affected_families)
    downstream_refresh = build_downstream_refresh(affected_families)
    manifest = load_manifest(repo_root)
    evidence_by_ticket = validate_assignment_ticket_keys(
        manifest,
        parse_assignment_map(args.lineage_evidence, flag="--lineage-evidence"),
        flag="--lineage-evidence",
    )
    replacement_source_by_ticket = validate_assignment_ticket_keys(
        manifest,
        parse_assignment_map(args.replacement_source, flag="--replacement-source"),
        flag="--replacement-source",
    )
    replacement_source_mode_by_ticket = validate_assignment_ticket_keys(
        manifest,
        parse_assignment_map(args.replacement_source_mode, flag="--replacement-source-mode"),
        flag="--replacement-source-mode",
    )
    validate_manifest_ticket_ids(manifest, list(replacement_source_by_ticket.values()), flag="--replacement-source")
    ticket_lineage_plan = build_ticket_lineage_plan(
        repo_root,
        supersede_tickets=args.supersede_ticket,
        reopen_tickets=args.reopen_ticket,
        reconcile_tickets=args.reconcile_ticket,
        unresolved_follow_up=args.unresolved_follow_up,
        evidence_by_ticket=evidence_by_ticket,
        replacement_source_by_ticket=replacement_source_by_ticket,
        replacement_source_mode_by_ticket=replacement_source_mode_by_ticket,
    )
    pivot_entry = {
        "recorded_at": timestamp,
        "pivot_id": timestamp,
        "pivot_class": args.pivot_class,
        "requested_change": args.requested_change.strip(),
        "accepted_decisions": [item.strip() for item in args.accepted_decision if item.strip()],
        "unresolved_follow_up": [item.strip() for item in args.unresolved_follow_up if item.strip()],
        "affected_contract_families": affected_families,
    }
    update_provenance(repo_root, pivot_entry)

    supporting_logs = resolve_supporting_logs(repo_root, args.supporting_log)
    findings = [] if args.skip_verify else audit_repo(repo_root, logs=supporting_logs)
    verification_status = summarize_verification(findings, not args.skip_verify, supporting_logs)

    payload = {
        "repo_root": str(repo_root),
        "pivot_id": timestamp,
        "pivot_class": args.pivot_class,
        "requested_change": args.requested_change.strip(),
        "accepted_decisions": pivot_entry["accepted_decisions"],
        "unresolved_follow_up": pivot_entry["unresolved_follow_up"],
        "affected_contract_families": affected_families,
        "stale_surface_map": stale_surface_map,
        "downstream_refresh": downstream_refresh,
        "ticket_lineage_plan": ticket_lineage_plan,
        "verification_status": verification_status,
        "pivot_history_entry": pivot_entry,
        "canonical_brief_path": str(CANONICAL_BRIEF_PATH).replace("\\", "/"),
        "pivot_state_path": str(PIVOT_STATE_PATH).replace("\\", "/"),
        "pivot_state_owner": "scafforge-pivot",
    }
    payload["downstream_refresh_state"] = build_downstream_refresh_state(
        downstream_refresh,
        pivot_id=timestamp,
        recorded_at=timestamp,
    )
    payload["restart_surface_inputs"] = build_restart_surface_inputs(payload)
    persist_pivot_state(repo_root, payload)
    if not args.skip_publish:
        publication = publish_pivot_surfaces(repo_root, published_by="scafforge-pivot")
        payload["restart_surface_publication"] = publication.get("restart_surface_publication", {})
        payload["restart_surface_inputs"] = publication.get("restart_surface_inputs", payload["restart_surface_inputs"])
        payload = read_json(repo_root / PIVOT_STATE_PATH)

    if args.format in {"text", "both"}:
        print(render_text(payload))
    if args.format in {"json", "both"}:
        if args.format == "both":
            print()
        print(json.dumps(payload, indent=2))

    if args.skip_verify:
        return 0
    return 0 if verification_status["verification_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
