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


FIXTURE_BUILDERS: dict[str, Callable[[Path, dict[str, Any]], dict[str, Any]]] = {
    "bootstrap-dependency-layout-drift": build_bootstrap_dependency_layout_drift,
    "host-tool-or-permission-blockage": build_host_tool_or_permission_blockage,
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
