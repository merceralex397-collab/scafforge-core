from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any
import sys


SHARED_VERIFIER_PATH = Path(__file__).resolve().parents[2] / "scafforge-audit" / "scripts" / "shared_verifier.py"
PIVOT_STATE_PATH = Path(".opencode/meta/pivot-state.json")
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
    parser.add_argument(
        "--affect",
        action="append",
        choices=FAMILIES,
        default=[],
        help="Explicitly mark an affected downstream contract family. When omitted, Scafforge uses a bounded default for the selected pivot class.",
    )
    parser.add_argument("--supporting-log", action="append", default=[], help="Optional transcript or session log to include in post-pivot verification.")
    parser.add_argument("--skip-verify", action="store_true", help="Skip the post-pivot verification pass.")
    parser.add_argument("--format", choices=("text", "json", "both"), default="text")
    return parser.parse_args()


def current_iso_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


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
    return sorted(set(explicit or default_affected_families(pivot_class)))


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
                "stage": "project-skill-bootstrap",
                "reason": "Pivot changed repo-local procedure or capability surfaces, so local skills need regeneration.",
            }
        )
    if "agent_team_and_prompts" in affected:
        routing.append(
            {
                "stage": "opencode-team-bootstrap",
                "reason": "Pivot changed team layout, delegation, or agent/tool boundaries.",
            }
        )
        routing.append(
            {
                "stage": "agent-prompt-engineering",
                "reason": "Pivot changed prompt behavior or delegation semantics and requires prompt hardening after regeneration.",
            }
        )
    if "ticket_graph_and_lineage" in affected:
        routing.append(
            {
                "stage": "ticket-pack-builder",
                "reason": "Pivot changed ticket lineage or introduced new work that must be superseded, reopened, reconciled, or refined.",
            }
        )
    if "managed_workflow_tools_and_prompts" in affected:
        routing.append(
            {
                "stage": "scafforge-repair",
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
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    affected_families = normalize_families(args.pivot_class, args.affect)
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
    pivot_entry = {
        "recorded_at": timestamp,
        "pivot_class": args.pivot_class,
        "requested_change": args.requested_change.strip(),
        "accepted_decisions": [item.strip() for item in args.accepted_decision if item.strip()],
        "unresolved_follow_up": [item.strip() for item in args.unresolved_follow_up if item.strip()],
        "affected_contract_families": affected_families,
    }
    update_provenance(repo_root, pivot_entry)

    supporting_logs = [Path(item).expanduser().resolve() for item in args.supporting_log]
    findings = [] if args.skip_verify else audit_repo(repo_root, logs=supporting_logs)
    verification_status = summarize_verification(findings, not args.skip_verify, supporting_logs)

    payload = {
        "repo_root": str(repo_root),
        "pivot_class": args.pivot_class,
        "requested_change": args.requested_change.strip(),
        "accepted_decisions": pivot_entry["accepted_decisions"],
        "unresolved_follow_up": pivot_entry["unresolved_follow_up"],
        "affected_contract_families": affected_families,
        "stale_surface_map": stale_surface_map,
        "downstream_refresh": downstream_refresh,
        "verification_status": verification_status,
        "pivot_history_entry": pivot_entry,
        "canonical_brief_path": str(CANONICAL_BRIEF_PATH).replace("\\", "/"),
        "pivot_state_path": str(PIVOT_STATE_PATH).replace("\\", "/"),
    }
    write_json(repo_root / PIVOT_STATE_PATH, payload)

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
