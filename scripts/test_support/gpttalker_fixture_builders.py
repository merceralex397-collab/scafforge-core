from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Callable

from test_support.repo_seeders import (
    make_stack_skill_non_placeholder,
    read_json,
    seed_closed_ticket_with_new_active_artifact_write,
    seed_bootstrap_command_layout_mismatch,
    seed_historical_reconciliation_state,
    seed_pivot_state_drift,
    seed_ready_bootstrap,
    seed_repeated_diagnosis_churn,
    seed_restart_surface_drift,
    seed_uv_python_fixture,
    seed_workflow_overclaim,
    write_json,
)
from test_support.scafforge_harness import ROOT, bootstrap_full


FIXTURE_INDEX = ROOT / "tests" / "fixtures" / "gpttalker" / "index.json"



def fixture_index_by_slug() -> dict[str, dict[str, Any]]:
    payload = read_json(FIXTURE_INDEX)
    families = payload.get("families") if isinstance(payload, dict) else None
    if not isinstance(families, list):
        raise RuntimeError("GPTTalker fixture index must define a families list.")
    indexed: dict[str, dict[str, Any]] = {}
    for item in families:
        if isinstance(item, dict) and isinstance(item.get("slug"), str):
            indexed[item["slug"]] = item
    return indexed


def write_fixture_contract(dest: Path, *, slug: str, family: dict[str, Any], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "slug": slug,
        "title": family.get("title"),
        "flow": family.get("flow"),
        "invariant_focus": family.get("invariant_focus", []),
        "expected_finding_codes": family.get("expected_finding_codes", []),
        "expected_coverage": family.get("expected_coverage", []),
        "truth_expectations": family.get("truth_expectations", {}),
        "archive_origin": family.get("archive_origin", []),
        "notes": family.get("notes"),
    }
    if extra:
        payload.update(extra)
    path = dest / ".opencode" / "meta" / "gpttalker-fixture.json"
    write_json(path, payload)
    return payload


def build_bootstrap_dependency_layout_drift(dest: Path, family: dict[str, Any]) -> dict[str, Any]:
    bootstrap_full(dest)
    make_stack_skill_non_placeholder(dest)
    seed_uv_python_fixture(dest)
    seed_bootstrap_command_layout_mismatch(dest)
    return write_fixture_contract(dest, slug="bootstrap-dependency-layout-drift", family=family)


def build_host_tool_or_permission_blockage(dest: Path, family: dict[str, Any]) -> dict[str, Any]:
    bootstrap_full(dest)
    make_stack_skill_non_placeholder(dest)
    seed_ready_bootstrap(dest)
    log_path = seed_workflow_overclaim(dest)
    return write_fixture_contract(
        dest,
        slug="host-tool-or-permission-blockage",
        family=family,
        extra={"supporting_log": str(log_path.relative_to(dest)).replace("\\", "/")},
    )


def build_repeated_lifecycle_contradiction(dest: Path, family: dict[str, Any]) -> dict[str, Any]:
    bootstrap_full(dest)
    seed_repeated_diagnosis_churn(dest)
    return write_fixture_contract(dest, slug="repeated-lifecycle-contradiction", family=family)


def build_restart_surface_drift_after_repair(dest: Path, family: dict[str, Any]) -> dict[str, Any]:
    bootstrap_full(dest)
    make_stack_skill_non_placeholder(dest)
    seed_restart_surface_drift(dest)
    return write_fixture_contract(dest, slug="restart-surface-drift-after-repair", family=family)


def build_placeholder_skill_after_refresh(dest: Path, family: dict[str, Any]) -> dict[str, Any]:
    bootstrap_full(dest)
    return write_fixture_contract(dest, slug="placeholder-skill-after-refresh", family=family)


def build_split_scope_and_historical_trust_reconciliation(dest: Path, family: dict[str, Any]) -> dict[str, Any]:
    bootstrap_full(dest)
    make_stack_skill_non_placeholder(dest)
    seed_historical_reconciliation_state(dest)
    return write_fixture_contract(dest, slug="split-scope-and-historical-trust-reconciliation", family=family)



def _register_fixture_artifact(
    dest: Path,
    *,
    ticket_id: str,
    kind: str,
    stage: str,
    relative_path: str,
    summary: str,
    content: str,
) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    registry_path = dest / ".opencode" / "state" / "artifacts" / "registry.json"
    manifest = read_json(manifest_path)
    registry = read_json(registry_path)
    if not isinstance(manifest, dict):
        raise RuntimeError("Fixture manifest must be a JSON object.")
    if not isinstance(registry, dict):
        registry = {"artifacts": []}

    tickets = manifest.get("tickets")
    if not isinstance(tickets, list):
        raise RuntimeError("Fixture manifest must contain a tickets list.")

    ticket = next(
        (
            item
            for item in tickets
            if isinstance(item, dict) and str(item.get("id", "")).strip() == ticket_id
        ),
        None,
    )
    if not isinstance(ticket, dict):
        raise RuntimeError(f"Fixture manifest does not contain ticket `{ticket_id}`.")

    artifact_path = dest / relative_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(content, encoding="utf-8")

    artifact = {
        "kind": kind,
        "path": relative_path,
        "stage": stage,
        "summary": summary,
        "created_at": "2026-04-02T00:00:00Z",
        "trust_state": "current",
    }
    ticket.setdefault("artifacts", []).append(artifact)
    registry.setdefault("artifacts", []).append({"ticket_id": ticket_id, **artifact})
    write_json(manifest_path, manifest)
    write_json(registry_path, registry)


def build_partial_transaction_edge_case(dest: Path) -> dict[str, Any]:
    bootstrap_full(dest)
    make_stack_skill_non_placeholder(dest)
    seed_closed_ticket_with_new_active_artifact_write(dest)
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    workflow = read_json(workflow_path)
    workflow["lane_leases"] = []
    write_json(workflow_path, workflow)
    family = {
        "title": "Partial transaction with missing lease evidence",
        "flow": "repair",
        "invariant_focus": [
            "transaction-owned active ticket updates",
            "lease evidence must not disappear during a staged write",
        ],
        "expected_finding_codes": ["WFLOW010"],
        "expected_coverage": [
            "integration:repair",
            "smoke:partial-transaction lease evidence",
        ],
        "truth_expectations": {
            "convergence": "partial-transaction",
            "publish_safety": "lease-evidence-missing",
            "blocker_truth": "partial-transaction-lease-gap",
            "checks": [
                {
                    "kind": "json_equals",
                    "file": "tickets/manifest.json",
                    "path": "active_ticket",
                    "value": "TICK-002",
                },
                {
                    "kind": "json_equals",
                    "file": ".opencode/state/workflow-state.json",
                    "path": "active_ticket",
                    "value": "TICK-002",
                },
                {
                    "kind": "json_equals",
                    "file": ".opencode/state/workflow-state.json",
                    "path": "lane_leases",
                    "value": [],
                },
            ],
        },
        "archive_origin": ["synthetic-partial-transaction"],
    }
    return write_fixture_contract(dest, slug="partial-transaction-edge-case", family=family)


def build_pivot_state_edge_case(dest: Path) -> dict[str, Any]:
    bootstrap_full(dest)
    make_stack_skill_non_placeholder(dest)
    seed_pivot_state_drift(dest)
    family = {
        "title": "Pivot state drift after historical reconciliation",
        "flow": "pivot",
        "invariant_focus": [
            "pivot-state persistence",
            "restart publication must stay faithful to pivot inputs",
            "historical reconciliation must stay tied to canonical evidence",
        ],
        "expected_finding_codes": ["WFLOW024", "WFLOW010"],
        "expected_coverage": [
            "integration:pivot",
            "smoke:pivot-state drift",
        ],
        "truth_expectations": {
            "convergence": "pivot-state-drift",
            "publish_safety": "stale-pivot-publication",
            "blocker_truth": "historical-reconciliation",
            "checks": [
                {
                    "kind": "json_equals",
                    "file": ".opencode/meta/pivot-state.json",
                    "path": "pivot_state_path",
                    "value": ".opencode/meta/pivot-state.json",
                },
                {
                    "kind": "json_equals",
                    "file": ".opencode/meta/pivot-state.json",
                    "path": "restart_surface_inputs.pivot_in_progress",
                    "value": True,
                },
                {
                    "kind": "json_equals",
                    "file": ".opencode/meta/pivot-state.json",
                    "path": "restart_surface_publication.status",
                    "value": "stale",
                },
                {
                    "kind": "json_equals",
                    "file": ".opencode/meta/pivot-state.json",
                    "path": "ticket_lineage_plan.actions.0.action",
                    "value": "reconcile",
                },
            ],
        },
        "archive_origin": ["synthetic-pivot-state"],
    }
    return write_fixture_contract(dest, slug="pivot-state-edge-case", family=family)


def build_planning_implementation_contract_drift(dest: Path, family: dict[str, Any]) -> dict[str, Any]:
    bootstrap_full(dest)
    make_stack_skill_non_placeholder(dest)

    workflow_doc_path = dest / "docs" / "process" / "workflow.md"
    workflow_doc_text = workflow_doc_path.read_text(encoding="utf-8")
    workflow_doc_text = workflow_doc_text.replace("plan_review", "plan review")
    workflow_doc_path.write_text(workflow_doc_text, encoding="utf-8")

    workflow_tool_path = dest / ".opencode" / "lib" / "workflow.ts"
    workflow_tool_text = workflow_tool_path.read_text(encoding="utf-8")
    workflow_tool_text = workflow_tool_text.replace("plan_review", "plan-check")
    workflow_tool_path.write_text(workflow_tool_text, encoding="utf-8")

    ticket_update_path = dest / ".opencode" / "tools" / "ticket_update.ts"
    ticket_update_text = ticket_update_path.read_text(encoding="utf-8")
    ticket_update_text = ticket_update_text.replace("plan_review", "plan-check")
    ticket_update_text = ticket_update_text.replace(
        'ticket.stage !== "plan-check"',
        'ticket.status !== "plan_review"',
    )
    ticket_update_path.write_text(ticket_update_text, encoding="utf-8")

    stage_gate_path = dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    stage_gate_text = stage_gate_path.read_text(encoding="utf-8")
    stage_gate_text = stage_gate_text.replace(
        'ticket.stage !== "plan_review"',
        'ticket.status !== "plan_review"',
    )
    stage_gate_path.write_text(stage_gate_text, encoding="utf-8")

    return write_fixture_contract(
        dest,
        slug="planning-implementation-contract-drift",
        family=family,
    )


def build_validation_verdict_routing_drift(dest: Path, family: dict[str, Any]) -> dict[str, Any]:
    bootstrap_full(dest)
    make_stack_skill_non_placeholder(dest)

    workflow_tool_path = dest / ".opencode" / "lib" / "workflow.ts"
    workflow_tool_text = workflow_tool_path.read_text(encoding="utf-8")
    workflow_tool_text = workflow_tool_text.replace(
        'const labeled = trimmed.match(/^(?:[-*]\\s*)?(?:\\*\\*|__)?(?:overall(?:\\s+result)?|verdict|result|approval\\s+signal)(?:\\*\\*|__)?\\s*:\\s*(?:\\*\\*|__)?\\s*(pass|fail|reject|approved?|blocked?|blocker)(?:\\*\\*|__)?\\b/i)',
        'const labeled = trimmed.match(/^(?:[-*]\\s*)?(?:overall(?:\\s+result)?|verdict|result|approval\\s+signal)\\s*:\\s*(pass|fail|reject|approved?|blocked?|blocker)\\b/i)',
    )
    workflow_tool_path.write_text(workflow_tool_text, encoding="utf-8")

    ticket_lookup_path = dest / ".opencode" / "tools" / "ticket_lookup.ts"
    ticket_lookup_text = ticket_lookup_path.read_text(encoding="utf-8")
    ticket_lookup_text = ticket_lookup_text.replace(
        "Review found blockers. Route back to implementation",
        "Review blockers need follow-up",
    )
    ticket_lookup_text = ticket_lookup_text.replace(
        "QA found issues. Route back to implementation to fix the QA findings.",
        "QA issues need follow-up.",
    )
    ticket_lookup_path.write_text(ticket_lookup_text, encoding="utf-8")

    manifest_path = dest / "tickets" / "manifest.json"
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise RuntimeError("Fixture manifest must be a JSON object.")
    active_ticket_id = str(manifest.get("active_ticket", "")).strip()
    if not active_ticket_id:
        tickets = manifest.get("tickets")
        if isinstance(tickets, list) and tickets:
            first_ticket = tickets[0]
            if isinstance(first_ticket, dict):
                active_ticket_id = str(first_ticket.get("id", "")).strip()
    if not active_ticket_id:
        raise RuntimeError("Fixture manifest must expose an active ticket for validation drift seeding.")

    _register_fixture_artifact(
        dest,
        ticket_id=active_ticket_id,
        kind="review",
        stage="review",
        relative_path=".opencode/state/reviews/greenfield-validation-review.md",
        summary="Greenfield validation verdict drift review",
        content="\n".join(
            [
                "# Review",
                "",
                "**Verdict**: FAIL",
                "",
                "Review blockers need follow-up.",
                "",
            ]
        ),
    )

    return write_fixture_contract(
        dest,
        slug="validation-verdict-routing-drift",
        family=family,
    )


def build_resume_surface_drift_after_greenfield(dest: Path, family: dict[str, Any]) -> dict[str, Any]:
    bootstrap_full(dest)
    make_stack_skill_non_placeholder(dest)

    for relative in (
        "START-HERE.md",
        ".opencode/state/context-snapshot.md",
        ".opencode/state/latest-handoff.md",
    ):
        path = dest / relative
        text = path.read_text(encoding="utf-8")
        text = text.replace("- bootstrap_status: ready", "- bootstrap_status: failed")
        text = text.replace("- bootstrap_proof: None", "- bootstrap_proof: stale-proof")
        if relative == ".opencode/state/context-snapshot.md" and "- bootstrap_status:" not in text:
            text = text.replace(
                "## Bootstrap\n\n",
                "## Bootstrap\n\n- bootstrap_status: missing\n- bootstrap_proof: stale-proof\n\n",
            )
        path.write_text(text, encoding="utf-8")

    resume_path = dest / ".opencode" / "commands" / "resume.md"
    resume_path.parent.mkdir(parents=True, exist_ok=True)
    if resume_path.exists():
        resume_text = resume_path.read_text(encoding="utf-8")
    else:
        resume_text = ""
    resume_text = resume_text.replace(
        "Resume from `tickets/manifest.json` and `.opencode/state/workflow-state.json` first.",
        "Resume from the latest handoff first.",
    )
    resume_text = resume_text.replace(
        "Treat the active open ticket as the primary lane even when historical reverification is pending.",
        "Treat the latest handoff as the primary lane.",
    )
    if not resume_text.strip():
        resume_text = "Resume from the latest handoff first.\nTreat the latest handoff as the primary lane.\n"
    resume_path.write_text(resume_text, encoding="utf-8")

    return write_fixture_contract(
        dest,
        slug="resume-surface-drift-after-greenfield",
        family=family,
    )


FIXTURE_BUILDERS: dict[str, Callable[[Path, dict[str, Any]], dict[str, Any]]] = {
    "bootstrap-dependency-layout-drift": build_bootstrap_dependency_layout_drift,
    "host-tool-or-permission-blockage": build_host_tool_or_permission_blockage,
    "planning-implementation-contract-drift": build_planning_implementation_contract_drift,
    "validation-verdict-routing-drift": build_validation_verdict_routing_drift,
    "resume-surface-drift-after-greenfield": build_resume_surface_drift_after_greenfield,
    "repeated-lifecycle-contradiction": build_repeated_lifecycle_contradiction,
    "restart-surface-drift-after-repair": build_restart_surface_drift_after_repair,
    "placeholder-skill-after-refresh": build_placeholder_skill_after_refresh,
    "split-scope-and-historical-trust-reconciliation": build_split_scope_and_historical_trust_reconciliation,
}


def build_fixture_family(slug: str, dest: Path) -> dict[str, Any]:
    families = fixture_index_by_slug()
    if slug not in FIXTURE_BUILDERS:
        known = ", ".join(sorted(FIXTURE_BUILDERS))
        raise RuntimeError(f"No GPTTalker fixture builder exists for `{slug}`. Known builders: {known}")
    family = families.get(slug)
    if not isinstance(family, dict):
        raise RuntimeError(f"Fixture index does not contain family metadata for `{slug}`.")
    if dest.exists():
        shutil.rmtree(dest)
    FIXTURE_BUILDERS[slug](dest, family)
    return read_json(dest / ".opencode" / "meta" / "gpttalker-fixture.json")
