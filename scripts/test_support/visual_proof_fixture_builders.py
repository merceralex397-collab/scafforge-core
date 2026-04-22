from __future__ import annotations

import base64
import shutil
from pathlib import Path
from typing import Any, Callable

from test_support.repo_seeders import (
    make_stack_skill_non_placeholder,
    read_json,
    seed_ready_bootstrap,
    write_json,
)
from test_support.scafforge_harness import ROOT, bootstrap_full


FIXTURE_INDEX = ROOT / "tests" / "fixtures" / "visual-proof" / "index.json"
CONTRACT_PATH = ".opencode/meta/visual-proof-fixture.json"
_TINY_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/a8sAAAAASUVORK5CYII="
)


def write_tiny_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_TINY_PNG_BYTES)


def fixture_index_by_slug() -> dict[str, dict[str, Any]]:
    payload = read_json(FIXTURE_INDEX)
    families = payload.get("families") if isinstance(payload, dict) else None
    if not isinstance(families, list):
        raise RuntimeError("Visual-proof fixture index must define a families list.")
    indexed: dict[str, dict[str, Any]] = {}
    for item in families:
        if isinstance(item, dict) and isinstance(item.get("slug"), str):
            indexed[item["slug"]] = item
    return indexed


def write_fixture_contract(
    dest: Path, *, slug: str, family: dict[str, Any], extra: dict[str, Any]
) -> dict[str, Any]:
    payload = {
        "slug": slug,
        "title": family.get("title"),
        "flow": family.get("flow"),
        "invariant_focus": family.get("invariant_focus", []),
        "expected_coverage": family.get("expected_coverage", []),
        "expected_gate_blocker": family.get("expected_gate_blocker"),
        "expected_rubric_blockers": family.get("expected_rubric_blockers", []),
        "notes": family.get("notes"),
        **extra,
    }
    write_json(dest / CONTRACT_PATH, payload)
    return payload


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
        "created_at": "2026-04-21T21:00:00Z",
        "trust_state": "current",
    }
    ticket.setdefault("artifacts", []).append(artifact)
    registry.setdefault("artifacts", []).append({"ticket_id": ticket_id, **artifact})
    write_json(manifest_path, manifest)
    write_json(registry_path, registry)


def build_screen_fit_and_hierarchy_regression(
    dest: Path, family: dict[str, Any]
) -> dict[str, Any]:
    if dest.exists():
        shutil.rmtree(dest)
    bootstrap_full(dest)
    make_stack_skill_non_placeholder(dest)
    seed_ready_bootstrap(dest)

    preview_paths = [
        "assets/previews/menu-overflow.png",
        "assets/previews/hud-overlap.png",
    ]
    for relative in preview_paths:
        write_tiny_png(dest / relative)

    provenance_path = dest / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = read_json(provenance_path)
    if not isinstance(provenance, dict):
        raise RuntimeError("Fixture bootstrap provenance must be a JSON object.")
    provenance["stack_label"] = "godot-android-2d"
    provenance["requires_visual_proof"] = True
    product_finish_contract = provenance.setdefault("product_finish_contract", {})
    if not isinstance(product_finish_contract, dict):
        raise RuntimeError("Fixture product_finish_contract must be a JSON object.")
    product_finish_contract["requires_visual_proof"] = True
    product_finish_contract["visual_finish_target"] = (
        "centered readable title screen, menu, and HUD with no clipped or placeholder UI"
    )
    product_finish_contract["finish_acceptance_signals"] = (
        "QA must cite screenshots proving the first screen fits, the menu hierarchy reads cleanly, and the HUD remains readable."
    )
    write_json(provenance_path, provenance)

    manifest_path = dest / "tickets" / "manifest.json"
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise RuntimeError("Fixture manifest must be a JSON object.")
    tickets = manifest.get("tickets")
    if not isinstance(tickets, list) or not tickets or not isinstance(tickets[0], dict):
        raise RuntimeError("Fixture manifest must contain at least one ticket.")
    ticket = tickets[0]
    ticket_id = str(ticket.get("id", "")).strip()
    ticket["stage"] = "qa"
    ticket["status"] = "qa"
    acceptance = ticket.get("acceptance")
    if not isinstance(acceptance, list):
        acceptance = []
        ticket["acceptance"] = acceptance
    acceptance.extend(
        [
            "The first screen fits common viewports without clipping, corner pinning, or unusable negative space.",
            "QA records structured visual proof with evidence paths and rubric disposition before smoke-test.",
        ]
    )
    write_json(manifest_path, manifest)

    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    workflow = read_json(workflow_path)
    if not isinstance(workflow, dict):
        raise RuntimeError("Fixture workflow state must be a JSON object.")
    workflow["active_ticket"] = ticket_id
    workflow["approved_plan"] = True
    workflow.setdefault("ticket_state", {}).setdefault(ticket_id, {})[
        "approved_plan"
    ] = True
    write_json(workflow_path, workflow)

    _register_fixture_artifact(
        dest,
        ticket_id=ticket_id,
        kind="review",
        stage="review",
        relative_path=".opencode/state/reviews/visual-proof-review.md",
        summary="PASS review for visual-proof fixture.",
        content=(
            "# Review\n\n"
            "Verdict: PASS\n\n"
            "Command: `godot4 --headless --path . --quit`\n\n"
            "```text\n$ godot4 --headless --path . --quit\nexit code: 0\n```\n"
        ),
    )
    qa_artifact_path = ".opencode/state/qa/visual-proof-qa.md"
    _register_fixture_artifact(
        dest,
        ticket_id=ticket_id,
        kind="qa",
        stage="qa",
        relative_path=qa_artifact_path,
        summary="PASS QA artifact missing structured visual proof.",
        content=(
            "# QA\n\n"
            "Result: PASS\n\n"
            "## Commands\n\n"
            "- command: `godot4 --headless --path . --quit`\n\n"
            "```text\n"
            "$ godot4 --headless --path . --quit\n"
            "No script errors detected.\n"
            "exit code: 0\n"
            "```\n\n"
            "## Visual Review Notes\n\n"
            "- The title screen remains corner-pinned and wastes most of the viewport.\n"
            "- The menu stack competes with the play surface instead of presenting a clear focal action.\n"
            "- Evidence draft: assets/previews/menu-overflow.png, assets/previews/hud-overlap.png.\n"
            "- Expected blocker categories: screen-fit failure, menu hierarchy failure, readability failure.\n"
        ),
    )

    return write_fixture_contract(
        dest,
        slug="screen-fit-and-hierarchy-regression",
        family=family,
        extra={
            "ticket_id": ticket_id,
            "qa_artifact_path": qa_artifact_path,
            "expected_visual_proof_paths": preview_paths,
        },
    )


BUILDERS: dict[str, Callable[[Path, dict[str, Any]], dict[str, Any]]] = {
    "screen-fit-and-hierarchy-regression": build_screen_fit_and_hierarchy_regression,
}


def build_fixture_family(slug: str, dest: Path) -> dict[str, Any]:
    family = fixture_index_by_slug().get(slug)
    if not isinstance(family, dict):
        raise RuntimeError(
            f"Visual-proof fixture index does not contain family metadata for `{slug}`."
        )
    builder = BUILDERS.get(slug)
    if builder is None:
        known = ", ".join(sorted(BUILDERS))
        raise RuntimeError(
            f"No visual-proof fixture builder exists for `{slug}`. Known builders: {known}"
        )
    builder(dest, family)
    return read_json(dest / CONTRACT_PATH)
