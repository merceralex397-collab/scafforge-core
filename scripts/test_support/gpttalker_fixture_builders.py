from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Callable

from test_support.repo_seeders import (
    make_stack_skill_non_placeholder,
    read_json,
    seed_bootstrap_command_layout_mismatch,
    seed_historical_reconciliation_state,
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
