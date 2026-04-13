from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from test_support.repo_seeders import (
    make_stack_skill_non_placeholder,
    seed_all_tickets_closed,
    seed_bootstrap_command_layout_mismatch,
    seed_completed_repair_follow_on_verification_block,
    seed_closed_ticket_with_new_active_artifact_write,
    seed_failing_pytest_suite,
    seed_ready_bootstrap,
    seed_repeated_diagnosis_churn,
    seed_restart_surface_drift,
    seed_uv_python_fixture,
    seed_workflow_overclaim,
    write_python_wrapper,
)
from test_support.scafforge_harness import (
    AUDIT,
    BOOTSTRAP,
    CHECKLIST,
    PIVOT,
    PIVOT_APPLY,
    PIVOT_PUBLISH,
    PIVOT_RECORD,
    PUBLIC_REPAIR,
    RECONCILE_REPAIR,
    RECORD_REPAIR_STAGE,
    REGENERATE,
    REPAIR,
    ROOT,
    VERIFY_GENERATED,
    compute_bootstrap_fingerprint,
    load_python_module,
    package_commit,
    prepare_generated_tool_runtime,
    run,
    run_generated_plugin_before,
    run_generated_plugin_before_error,
    run_generated_tool,
    run_generated_tool_error,
    run_json,
    write_executable,
)


def register_current_ticket_artifact(
    dest: Path,
    *,
    ticket_id: str,
    kind: str,
    stage: str,
    relative_path: str,
    summary: str,
    content: str,
    created_at: str = "2026-03-30T00:00:00Z",
) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    registry_path = dest / ".opencode" / "state" / "artifacts" / "registry.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    artifact_path = dest / relative_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(content, encoding="utf-8")
    artifact = {
        "kind": kind,
        "path": relative_path,
        "stage": stage,
        "summary": summary,
        "created_at": created_at,
        "trust_state": "current",
    }
    ticket = next(item for item in manifest["tickets"] if item["id"] == ticket_id)
    ticket.setdefault("artifacts", []).append(artifact)
    registry.setdefault("artifacts", []).append({"ticket_id": ticket_id, **artifact})
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


def seed_minimal_npm_repo(dest: Path) -> None:
    (dest / "package.json").write_text(
        json.dumps(
            {
                "name": "smoke-example",
                "version": "1.0.0",
                "private": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (dest / "package-lock.json").write_text(
        json.dumps(
            {
                "name": "smoke-example",
                "version": "1.0.0",
                "lockfileVersion": 3,
                "requires": True,
                "packages": {
                    "": {
                        "name": "smoke-example",
                        "version": "1.0.0",
                    }
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def seed_dependency_group_python_fixture(dest: Path) -> None:
    seed_uv_python_fixture(
        dest,
        dependency_block=[
            "[dependency-groups]",
            'dev = ["pytest>=8.0.0"]',
        ],
    )


def seed_uv_native_dev_dependency_fixture(dest: Path) -> None:
    seed_uv_python_fixture(
        dest,
        dependency_block=[
            "[tool.uv.dev-dependencies]",
            'pytest = ">=8.0.0"',
        ],
    )


def seed_bootstrap_deadlock(dest: Path) -> None:
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    artifact_rel = ".opencode/state/bootstrap/synthetic-bootstrap-deadlock.md"
    artifact_path = dest / artifact_rel
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        "\n".join(
            [
                "# Environment Bootstrap",
                "",
                "## Missing Prerequisites",
                "",
                "- None",
                "",
                "## Commands",
                "",
                "### 1. pip install editable project",
                "",
                "- command: `python3 -m pip install -e .`",
                "",
                "#### stderr",
                "",
                "~~~~text",
                "/usr/bin/python3: No module named pip",
                "~~~~",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    workflow["bootstrap"] = {
        "status": "failed",
        "last_verified_at": "2026-03-25T00:23:01Z",
        "environment_fingerprint": "synthetic-bootstrap-deadlock",
        "proof_artifact": artifact_rel,
    }
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")


def seed_legacy_bootstrap_tool(dest: Path) -> None:
    tool_path = dest / ".opencode" / "tools" / "environment_bootstrap.ts"
    tool_path.write_text(
        "\n".join(
            [
                'import { tool } from "@opencode-ai/plugin"',
                "",
                "export default tool({",
                '  description: "legacy bootstrap fixture",',
                "  args: {},",
                "  async execute() {",
                '    const command = { argv: ["python3", "-m", "pip", "install", "-e", "."] }',
                "    return JSON.stringify(command)",
                "  },",
                "})",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def seed_legacy_model_drift(dest: Path) -> None:
    legacy_minimax = "minimax-coding-plan/" + "MiniMax-M2." + "5"

    profile_dir = dest / ".opencode" / "skills" / "model-operating-profile"
    shutil.rmtree(profile_dir, ignore_errors=True)

    provenance_path = dest / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["runtime_models"] = {
        "provider": "minimax-coding-plan",
        "planner": legacy_minimax,
        "implementer": legacy_minimax,
        "utility": legacy_minimax,
    }
    provenance_path.write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )


def seed_godot_android_target(dest: Path) -> None:
    brief = "\n".join(
        [
            "# Canonical Brief",
            "",
            "## 1. Project Summary",
            "",
            "Synthetic Godot Android delivery fixture.",
            "",
            "## 2. Goals",
            "",
            "- Ship a Godot Android build.",
            "",
            "## 3. Non-Goals",
            "",
            "- None",
            "",
            "## 4. Constraints",
            "",
            "- Platform target is Android.",
            "- Engine is Godot.",
            "",
            "## 5. Required Outputs",
            "",
            "- Android export surfaces and debug APK proof.",
            "",
            "## 6. Tooling and Model Constraints",
            "",
            "- Stack label: `godot-android-2d`",
            "",
            "## 7. Canonical Truth Map",
            "",
            "- Durable facts: `docs/spec/CANONICAL-BRIEF.md`",
            "",
            "## 8. Blocking Decisions",
            "",
            "- None",
            "",
            "## 9. Non-Blocking Open Questions",
            "",
            "- None",
            "",
            "## 10. Backlog Readiness",
            "",
            "Backlog can proceed.",
            "",
            "## 11. Acceptance Signals",
            "",
            "- Android export lane and release lane exist.",
            "",
            "## 12. Assumptions",
            "",
            "- GDScript is acceptable.",
            "",
        ]
    )
    (dest / "docs" / "spec" / "CANONICAL-BRIEF.md").write_text(
        brief + "\n", encoding="utf-8"
    )
    provenance_path = dest / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["stack_label"] = "godot-android-2d"
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


def seed_minimal_godot_project(dest: Path) -> None:
    (dest / "project.godot").write_text(
        "\n".join(
            [
                "; Engine configuration file.",
                "[application]",
                'config/name="Smoke Android Fixture"',
                'run/main_scene="res://scenes/main.tscn"',
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (dest / "scenes").mkdir(parents=True, exist_ok=True)
    (dest / "scenes" / "main.tscn").write_text(
        '[gd_scene format=3]\n\n[node name="Main" type="Node2D"]\n',
        encoding="utf-8",
    )


def append_manifest_ticket(dest: Path, ticket: dict[str, Any]) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.setdefault("tickets", []).append(ticket)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def seed_spinner_like_android_gap(dest: Path) -> None:
    seed_godot_android_target(dest)
    seed_minimal_godot_project(dest)
    seed_all_tickets_closed(dest)
    (dest / "android").mkdir(parents=True, exist_ok=True)
    (dest / "android" / ".gitkeep").write_text("", encoding="utf-8")
    append_manifest_ticket(
        dest,
        {
            "id": "POLISH-001",
            "title": "Validate Android export and performance posture",
            "wave": 3,
            "lane": "polish",
            "parallel_safe": False,
            "overlap_risk": "medium",
            "stage": "closeout",
            "status": "done",
            "resolution_state": "done",
            "verification_state": "trusted",
            "depends_on": [],
            "source_ticket_id": None,
            "follow_up_ticket_ids": [],
            "summary": "Android export validation recorded only as host gaps documented: no export templates, empty android/ folder, Android SDK not verified.",
            "acceptance": [
                "Android export validation documented",
                "Performance review complete",
            ],
            "decision_blockers": [],
            "artifacts": [],
        },
    )
    manifest_path = dest / "tickets" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["active_ticket"] = "POLISH-001"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    workflow["active_ticket"] = "POLISH-001"
    workflow["stage"] = "closeout"
    workflow["status"] = "done"
    workflow["ticket_state"]["POLISH-001"] = {
        "approved_plan": True,
        "reopen_count": 0,
        "needs_reverification": False,
    }
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")


def seed_review_stage_with_verdict(dest: Path, verdict_line: str) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    ticket = manifest["tickets"][0]
    ticket["stage"] = "review"
    ticket["status"] = "review"
    manifest["active_ticket"] = ticket["id"]
    workflow["active_ticket"] = ticket["id"]
    workflow["stage"] = "review"
    workflow["status"] = "review"
    workflow["ticket_state"].setdefault(
        ticket["id"],
        {"approved_plan": True, "reopen_count": 0, "needs_reverification": False},
    )["approved_plan"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    register_current_ticket_artifact(
        dest,
        ticket_id=ticket["id"],
        kind="review",
        stage="review",
        relative_path=".opencode/state/reviews/setup-001-review.md",
        summary="Synthetic review artifact.",
        content=f"# Review\n\n{verdict_line}\n\nCommand: synthetic\n\n~~~~text\nPASS\n~~~~\n",
    )


def seed_glitch_style_remediation_review(
    dest: Path, result_line: str = "**Verdict:** PASS"
) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    ticket = manifest["tickets"][0]
    ticket["stage"] = "review"
    ticket["status"] = "review"
    ticket["lane"] = "remediation"
    ticket["finding_source"] = "EXEC-REMED-001"
    manifest["active_ticket"] = ticket["id"]
    workflow["active_ticket"] = ticket["id"]
    workflow["stage"] = "review"
    workflow["status"] = "review"
    workflow["ticket_state"].setdefault(
        ticket["id"],
        {"approved_plan": True, "reopen_count": 0, "needs_reverification": False},
    )["approved_plan"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    register_current_ticket_artifact(
        dest,
        ticket_id=ticket["id"],
        kind="review",
        stage="review",
        relative_path=".opencode/state/reviews/setup-001-review.md",
        summary="Synthetic remediation review artifact with fenced command evidence.",
        content=(
            "# Review Artifact: SETUP-001\n\n"
            "## Review Summary\n\n"
            f"{result_line}\n\n"
            "### Finding 1 - Real Command Evidence Provided\n\n"
            "**Command run:**\n"
            "```text\n"
            "godot --headless --path . --quit 2>&1 | head -50\n"
            "```\n\n"
            "**Raw output (truncated to relevant lines):**\n"
            "```text\n"
            "Godot Engine v4.6.2.stable.official.71f334935 - https://godotengine.org\n"
            "[HUD] Successfully connected to glitch_warning signal\n"
            "```\n\n"
            f"{result_line}\n"
        ),
    )


def seed_inline_exact_remediation_review(
    dest: Path, result_line: str = "Result: PASS"
) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    ticket = manifest["tickets"][0]
    ticket["stage"] = "review"
    ticket["status"] = "review"
    ticket["lane"] = "remediation"
    ticket["finding_source"] = "EXEC-REMED-001"
    manifest["active_ticket"] = ticket["id"]
    workflow["active_ticket"] = ticket["id"]
    workflow["stage"] = "review"
    workflow["status"] = "review"
    workflow["ticket_state"].setdefault(
        ticket["id"],
        {"approved_plan": True, "reopen_count": 0, "needs_reverification": False},
    )["approved_plan"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    register_current_ticket_artifact(
        dest,
        ticket_id=ticket["id"],
        kind="review",
        stage="review",
        relative_path=".opencode/state/reviews/setup-001-review.md",
        summary="Synthetic remediation review artifact with inline exact command/output evidence.",
        content=(
            "# Review Artifact: SETUP-001\n\n"
            "## Verdict: **APPROVE**\n\n"
            "**Exact command run**: `godot --headless --path . --quit`\n\n"
            "**Raw output**: `Godot Engine v4.6.2.stable.official.71f334935 - https://godotengine.org`\n\n"
            f"**{result_line}**\n"
        ),
    )


def seed_non_remediation_finding_source_review(
    dest: Path, verdict_line: str = "## Verdict: **APPROVE**"
) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    ticket = manifest["tickets"][0]
    ticket["stage"] = "review"
    ticket["status"] = "review"
    ticket["lane"] = "signing-prerequisites"
    ticket["finding_source"] = "WFLOW025"
    ticket["source_mode"] = "net_new_scope"
    manifest["active_ticket"] = ticket["id"]
    workflow["active_ticket"] = ticket["id"]
    workflow["stage"] = "review"
    workflow["status"] = "review"
    workflow["ticket_state"].setdefault(
        ticket["id"],
        {"approved_plan": True, "reopen_count": 0, "needs_reverification": False},
    )["approved_plan"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    register_current_ticket_artifact(
        dest,
        ticket_id=ticket["id"],
        kind="review",
        stage="review",
        relative_path=".opencode/state/reviews/setup-001-review.md",
        summary="Synthetic non-remediation finding-source review artifact.",
        content=(
            "# Review Artifact: SETUP-001\n\n"
            "## Review Summary\n\n"
            f"{verdict_line}\n\n"
            "**Command run:** `godot --headless --path . --quit`\n\n"
            "```text\n"
            "Godot Engine v4.6.2.stable.official.71f334935\n"
            "```\n"
        ),
    )


def seed_legacy_markdown_verdict_parser(dest: Path) -> None:
    legacy_minimax = "minimax-coding-plan/" + "MiniMax-M2." + "5"
    workflow_path = dest / ".opencode" / "lib" / "workflow.ts"
    text = workflow_path.read_text(encoding="utf-8")
    broad_plain_label = """const labeled = plain.match(
      new RegExp(
        `^(?:[-*]\\\\s*)?${ARTIFACT_VERDICT_LABEL_PATTERN}\\\\s*:\\\\s*(pass|fail|reject|approved?|blocked?|blocker)\\\\b`,
        "i",
      ),
    )"""
    legacy_plain_label = (
        r'const labeled = trimmed.match(/^(?:overall(?:\s+result)?|verdict|result|approval\s+signal)\s*:\s*(?:\*\*)?\s*(pass|fail|reject|approved?|blocked?|blocker)\b/i)'
    )
    if broad_plain_label in text:
        text = text.replace(broad_plain_label, legacy_plain_label)
    else:
        text = text.replace(
            r"/^(?:[-*]\s*)?(?:(?:\*\*|__)?(?:overall(?:\s+(?:result|verdict))?|verdict|result|approval\s+signal)(?:\*\*|__)?\s*:|(?:\*\*|__)?(?:overall(?:\s+(?:result|verdict))?|verdict|result|approval\s+signal):(?:\*\*|__)?)\s*(?:\*\*|__)?\s*(pass|fail|reject|approved?|blocked?|blocker)(?:\*\*|__)?\b/i",
            r"/^(?:overall(?:\s+result)?|verdict|result|approval\s+signal)\s*:\s*(?:\*\*)?\s*(pass|fail|reject|approved?|blocked?|blocker)\b/i",
        )
    workflow_path.write_text(text, encoding="utf-8")

    (dest / "docs" / "process" / "model-matrix.md").write_text(
        "\n".join(
            [
                "# Model Matrix",
                "",
                "- provider: `minimax-coding-plan`",
                f"- team lead / planner / reviewers: `{legacy_minimax}`",
                f"- implementer: `{legacy_minimax}`",
                f"- utilities, docs, and QA helpers: `{legacy_minimax}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (dest / "START-HERE.md").write_text(
        (dest / "START-HERE.md")
        .read_text(encoding="utf-8")
        .replace("openrouter/openai/gpt-5-mini", legacy_minimax),
        encoding="utf-8",
    )
    (dest / "docs" / "spec" / "CANONICAL-BRIEF.md").write_text(
        (dest / "docs" / "spec" / "CANONICAL-BRIEF.md")
        .read_text(encoding="utf-8")
        .replace("openrouter/openai/gpt-5-mini", legacy_minimax),
        encoding="utf-8",
    )
    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    team_text = team_leader.read_text(encoding="utf-8")
    team_text = team_text.replace("temperature: 1.0", "temperature: 0.2")
    team_text = team_text.replace("top_p: 0.95", "top_p: 0.7")
    if "top_k: 40\n" in team_text:
        team_text = team_text.replace("top_k: 40\n", "")
    team_text = team_text.replace(
        "model: openrouter/anthropic/claude-sonnet-4.5", f"model: {legacy_minimax}"
    )
    team_leader.write_text(team_text, encoding="utf-8")


def seed_failed_repair_cycle(dest: Path, diagnosis_pack: Path) -> None:
    manifest_path = diagnosis_pack / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["ticket_recommendations"] = [
        {
            "source_finding_code": "SKILL001",
            "route": "scafforge-repair",
            "title": "Regenerate placeholder repo-local skills",
        }
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    provenance_path = dest / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    repair_history = provenance.setdefault("repair_history", [])
    repair_history.append(
        {
            "repaired_at": "2099-01-01T00:00:00Z",
            "summary": "Synthetic repair pass after diagnosis that left placeholder skills in place",
        }
    )
    provenance_path.write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )


def seed_closed_ticket_with_blocked_dependent(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    active_ticket_id = manifest["active_ticket"]
    active_ticket = next(
        ticket for ticket in manifest["tickets"] if ticket["id"] == active_ticket_id
    )
    active_ticket["stage"] = "closeout"
    active_ticket["status"] = "done"
    active_ticket["resolution_state"] = "done"
    active_ticket["verification_state"] = "reverified"
    smoke_test_path = (
        dest
        / ".opencode"
        / "state"
        / "artifacts"
        / "history"
        / active_ticket_id.lower()
        / "smoke-test"
        / "2099-01-01T00-00-00Z-smoke-test.md"
    )
    smoke_test_path.parent.mkdir(parents=True, exist_ok=True)
    smoke_test_path.write_text(
        "# Smoke Test\n\n## Validation Command\n\n`npm test -- --runInBand`\n\n## Raw Output\n\n```text\nPASS tests/workflow.test.ts\n  workflow closeout convergence\n    ✓ foregrounds the next live lane after a closed active ticket is resaved\n\nTest Suites: 1 passed, 1 total\nTests:       1 passed, 1 total\nSnapshots:   0 total\nTime:        0.842 s\nRan all test suites matching /workflow/i.\n```\n\n## Notes\n\n- Synthetic PASS smoke proof used to exercise closed-ticket continuation coverage through the generated tool path.\n- Includes command output and a realistic artifact body so closeout validation sees the same surface shape as a real run.\n\n## Overall Result\n\nPASS\n",
        encoding="utf-8",
    )
    active_ticket_artifacts = active_ticket.setdefault("artifacts", [])
    if not any(
        artifact.get("stage") == "smoke-test"
        and artifact.get("kind") == "smoke-test"
        and artifact.get("trust_state") == "current"
        for artifact in active_ticket_artifacts
    ):
        active_ticket_artifacts.append(
            {
                "kind": "smoke-test",
                "stage": "smoke-test",
                "path": str(smoke_test_path.relative_to(dest)),
                "summary": "Synthetic PASS smoke proof for closed-ticket continuation coverage.",
                "created_at": "2099-01-01T00:00:00Z",
                "trust_state": "current",
            }
        )
    if not any(ticket["id"] == "EXEC-DEP" for ticket in manifest["tickets"]):
        manifest["tickets"].append(
            {
                "id": "EXEC-DEP",
                "title": "Synthetic blocked dependent",
                "wave": 42,
                "lane": "implementation",
                "parallel_safe": True,
                "overlap_risk": "low",
                "stage": "planning",
                "status": "ready",
                "depends_on": [active_ticket_id],
                "summary": "Synthetic dependent ticket to verify closed-ticket continuation routing.",
                "acceptance": [
                    "Becomes the foreground lane after the source ticket closes."
                ],
                "decision_blockers": [],
                "artifacts": [],
                "resolution_state": "open",
                "verification_state": "suspect",
                "follow_up_ticket_ids": [],
            }
        )
    workflow["stage"] = "closeout"
    workflow["status"] = "done"
    workflow["pending_process_verification"] = False
    workflow["bootstrap"] = {
        "status": "ready",
        "last_verified_at": "2026-03-26T00:00:00Z",
        "environment_fingerprint": compute_bootstrap_fingerprint(dest),
        "proof_artifact": ".opencode/state/bootstrap/synthetic-ready-bootstrap.md",
    }
    ticket_state = workflow.get("ticket_state")
    if isinstance(ticket_state, dict):
        active_ticket_state = ticket_state.get(active_ticket_id)
        if isinstance(active_ticket_state, dict):
            active_ticket_state["needs_reverification"] = False
    proof_path = (
        dest / ".opencode" / "state" / "bootstrap" / "synthetic-ready-bootstrap.md"
    )
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text("# Ready Bootstrap\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")


def seed_finish_claim_with_open_finish_ticket(dest: Path) -> None:
    seed_godot_android_target(dest)
    seed_minimal_godot_project(dest)
    brief_path = dest / "docs" / "spec" / "CANONICAL-BRIEF.md"
    brief_path.write_text(
        brief_path.read_text(encoding="utf-8")
        + "\n## 13. Product Finish Contract\n\n"
        + "- deliverable_kind: packaged mobile product\n"
        + "- placeholder_policy: no_placeholders\n"
        + "- visual_finish_target: authored production visuals required\n"
        + "- audio_finish_target: authored production audio required\n"
        + "- content_source_plan: custom authored\n"
        + "- licensing_or_provenance_constraints: project-owned assets only\n"
        + "- finish_acceptance_signals: finish ownership tickets are closed with real content proof\n",
        encoding="utf-8",
    )
    append_manifest_ticket(
        dest,
        {
            "id": "VISUAL-001",
            "title": "Integrate production visuals",
            "wave": 3,
            "lane": "visual-content",
            "parallel_safe": False,
            "overlap_risk": "medium",
            "stage": "planning",
            "status": "todo",
            "depends_on": [],
            "summary": "Replace placeholder visuals with production-ready assets.",
            "acceptance": ["Production visual assets are integrated."],
            "decision_blockers": [],
            "artifacts": [],
            "resolution_state": "open",
            "verification_state": "suspect",
            "follow_up_ticket_ids": [],
        },
    )
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    workflow["active_ticket"] = ""
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    start_here_path = dest / "START-HERE.md"
    start_here_path.write_text(
        start_here_path.read_text(encoding="utf-8")
        + "\nready for continued development\n",
        encoding="utf-8",
    )


def seed_reference_scan_exclusion_case(dest: Path) -> None:
    (dest / "src").mkdir(parents=True, exist_ok=True)
    (dest / "src" / "owned_bad.py").write_text(
        "from .missing_module import demo\n",
        encoding="utf-8",
    )
    (dest / "node_modules" / "fakepkg").mkdir(parents=True, exist_ok=True)
    (dest / "node_modules" / "fakepkg" / "index.js").write_text(
        'require("./missing-runtime")\n',
        encoding="utf-8",
    )


def seed_incomplete_finish_contract(dest: Path) -> None:
    brief_path = dest / "docs" / "spec" / "CANONICAL-BRIEF.md"
    brief_path.write_text(
        brief_path.read_text(encoding="utf-8")
        + "\n## 13. Product Finish Contract\n\n- `deliverable_kind` — playable prototype\n",
        encoding="utf-8",
    )
    (dest / "project.godot").write_text(
        "; Engine configuration file.\nconfig_version=5\n",
        encoding="utf-8",
    )


def seed_weak_generated_finish_contract(dest: Path) -> None:
    seed_godot_android_target(dest)
    seed_minimal_godot_project(dest)
    brief_path = dest / "docs" / "spec" / "CANONICAL-BRIEF.md"
    weak_signals = (
        "Release-facing milestones must confirm shipped content matches the recorded finish bar for the product."
    )
    brief_path.write_text(
        brief_path.read_text(encoding="utf-8")
        + "\n## 13. Product Finish Contract\n\n"
        + "- deliverable_kind: playable packaged game build\n"
        + "- placeholder_policy: placeholder_ok\n"
        + "- visual_finish_target: User-facing visuals must match the recorded product direction across all shipped surfaces.\n"
        + "- audio_finish_target: User-facing audio must match the recorded product direction across all shipped surfaces.\n"
        + "- content_source_plan: Use repo-authored or appropriately licensed content. Temporary implementation assets are acceptable until a later brief revision records a stricter finish bar.\n"
        + "- licensing_or_provenance_constraints: All committed visual and audio content must be repo-authored, user-supplied, or covered by a license compatible with the intended distribution path.\n"
        + f"- finish_acceptance_signals: {weak_signals}\n",
        encoding="utf-8",
    )
    manifest_path = dest / "tickets" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tickets = manifest.setdefault("tickets", [])
    existing_ids = {
        str(ticket.get("id", "")).strip()
        for ticket in tickets
        if isinstance(ticket, dict)
    }
    if "FINISH-VALIDATE-001" not in existing_ids:
        tickets.append(
            {
                "id": "FINISH-VALIDATE-001",
                "title": "Validate product finish contract",
                "wave": 4,
                "lane": "finish-validation",
                "parallel_safe": False,
                "overlap_risk": "medium",
                "stage": "planning",
                "status": "todo",
                "resolution_state": "open",
                "verification_state": "suspect",
                "depends_on": ["SETUP-001"],
                "summary": "Synthetic weak finish-validation lane.",
                "acceptance": [
                    f"Finish proof artifact explicitly maps current evidence to the declared acceptance signals: {weak_signals}",
                    "`godot4 --headless --path . --quit` succeeds so finish validation is based on a loadable product, not just exported artifacts",
                    "All finish-direction, visual, audio, or content ownership tickets required by the contract are completed before closeout",
                ],
                "decision_blockers": [],
                "artifacts": [],
                "follow_up_ticket_ids": [],
            }
        )
    release_ticket = next(
        (
            ticket
            for ticket in tickets
            if isinstance(ticket, dict) and str(ticket.get("id", "")).strip() == "RELEASE-001"
        ),
        None,
    )
    if not isinstance(release_ticket, dict):
        tickets.append(
            {
                "id": "RELEASE-001",
                "title": "Ship release build",
                "wave": 5,
                "lane": "release-readiness",
                "parallel_safe": False,
                "overlap_risk": "high",
                "stage": "planning",
                "status": "todo",
                "resolution_state": "open",
                "verification_state": "suspect",
                "depends_on": ["FINISH-VALIDATE-001"],
                "summary": "Synthetic release lane for finish-contract audit coverage.",
                "acceptance": ["Release artifacts are ready for handoff."],
                "decision_blockers": [],
                "artifacts": [],
                "follow_up_ticket_ids": [],
            }
        )
    else:
        release_dependencies = [
            str(dep).strip()
            for dep in release_ticket.get("depends_on", [])
            if isinstance(dep, str) and str(dep).strip()
        ]
        if "FINISH-VALIDATE-001" not in release_dependencies:
            release_dependencies.append("FINISH-VALIDATE-001")
            release_ticket["depends_on"] = release_dependencies
    manifest["active_ticket"] = "FINISH-VALIDATE-001"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    workflow["active_ticket"] = "FINISH-VALIDATE-001"
    workflow["stage"] = "planning"
    workflow["status"] = "planning"
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")


def seed_broken_repo_venv(dest: Path) -> None:
    (dest / "pyproject.toml").write_text(
        "[project]\nname = \"broken-venv\"\nversion = \"0.1.0\"\n",
        encoding="utf-8",
    )
    broken_python = dest / ".venv" / "bin" / "python"
    broken_python.parent.mkdir(parents=True, exist_ok=True)
    broken_python.write_text("#!/broken/python\n", encoding="utf-8")
    broken_python.chmod(0o644)


def seed_remediation_review_without_command_evidence(dest: Path) -> None:
    append_manifest_ticket(
        dest,
        {
            "id": "EXEC-001-FIX",
            "title": "Fix failing import surface",
            "wave": 2,
            "lane": "remediation",
            "parallel_safe": False,
            "overlap_risk": "medium",
            "stage": "review",
            "status": "review",
            "depends_on": [],
            "summary": "Remediate a previously validated execution finding.",
            "acceptance": ["Original failing command now passes."],
            "decision_blockers": [],
            "artifacts": [],
            "resolution_state": "open",
            "verification_state": "suspect",
            "finding_source": "EXEC001",
            "follow_up_ticket_ids": [],
        },
    )
    register_current_ticket_artifact(
        dest,
        ticket_id="EXEC-001-FIX",
        kind="review",
        stage="review",
        relative_path=".opencode/state/artifacts/history/review/EXEC-001-FIX-review.md",
        summary="APPROVED",
        content="# Review\n\n- Verdict: PASS\n- Notes: import surface looks fixed.\n",
    )


def seed_remediation_review_with_empty_output_block(dest: Path) -> None:
    append_manifest_ticket(
        dest,
        {
            "id": "EXEC-002-FIX",
            "title": "Fix broken runtime command",
            "wave": 2,
            "lane": "remediation",
            "parallel_safe": False,
            "overlap_risk": "medium",
            "stage": "review",
            "status": "review",
            "depends_on": [],
            "summary": "Remediate a validated execution finding with command evidence.",
            "acceptance": ["Original failing command now passes."],
            "decision_blockers": [],
            "artifacts": [],
            "resolution_state": "open",
            "verification_state": "suspect",
            "finding_source": "EXEC002",
            "follow_up_ticket_ids": [],
        },
    )
    register_current_ticket_artifact(
        dest,
        ticket_id="EXEC-002-FIX",
        kind="review",
        stage="review",
        relative_path=".opencode/state/artifacts/history/review/EXEC-002-FIX-review.md",
        summary="APPROVED",
        content=(
            "# Review\n\n"
            "- Command: `pytest -q tests/test_runtime.py`\n"
            "## Raw Command Output\n\n"
            "```text\n```\n\n"
            "- Result: PASS\n"
        ),
    )


def seed_stale_godot_project_config(dest: Path) -> None:
    (dest / "project.godot").write_text(
        "\n".join(
            [
                "; Engine configuration file.",
                "config_version=2",
                "",
                "[rendering]",
                'renderer/rendering_method="GLES2"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def seed_closed_ticket_needing_explicit_reverification(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    active_ticket_id = manifest["active_ticket"]
    active_ticket = next(
        ticket for ticket in manifest["tickets"] if ticket["id"] == active_ticket_id
    )
    active_ticket["stage"] = "closeout"
    active_ticket["status"] = "done"
    active_ticket["resolution_state"] = "done"
    active_ticket["verification_state"] = "suspect"
    workflow["stage"] = "closeout"
    workflow["status"] = "done"
    workflow["pending_process_verification"] = False
    workflow["bootstrap"] = {
        "status": "ready",
        "last_verified_at": "2026-03-26T00:00:00Z",
        "environment_fingerprint": compute_bootstrap_fingerprint(dest),
        "proof_artifact": ".opencode/state/bootstrap/synthetic-ready-bootstrap.md",
    }
    ticket_state = workflow.get("ticket_state")
    if isinstance(ticket_state, dict):
        active_ticket_state = ticket_state.get(active_ticket_id)
        if isinstance(active_ticket_state, dict):
            active_ticket_state["needs_reverification"] = True
    proof_path = (
        dest / ".opencode" / "state" / "bootstrap" / "synthetic-ready-bootstrap.md"
    )
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text("# Ready Bootstrap\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")


def seed_reopened_ticket_needing_explicit_reverification(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    active_ticket_id = manifest["active_ticket"]
    active_ticket = next(
        ticket for ticket in manifest["tickets"] if ticket["id"] == active_ticket_id
    )
    active_ticket["stage"] = "planning"
    active_ticket["status"] = "todo"
    active_ticket["resolution_state"] = "reopened"
    active_ticket["verification_state"] = "invalidated"
    workflow["stage"] = "planning"
    workflow["status"] = "todo"
    workflow["pending_process_verification"] = False
    workflow["bootstrap"] = {
        "status": "ready",
        "last_verified_at": "2026-03-26T00:00:00Z",
        "environment_fingerprint": compute_bootstrap_fingerprint(dest),
        "proof_artifact": ".opencode/state/bootstrap/synthetic-ready-bootstrap.md",
    }
    ticket_state = workflow.get("ticket_state")
    if isinstance(ticket_state, dict):
        active_ticket_state = ticket_state.get(active_ticket_id)
        if isinstance(active_ticket_state, dict):
            active_ticket_state["reopen_count"] = max(
                int(active_ticket_state.get("reopen_count", 0)), 1
            )
            active_ticket_state["needs_reverification"] = True
    proof_path = (
        dest / ".opencode" / "state" / "bootstrap" / "synthetic-ready-bootstrap.md"
    )
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text("# Ready Bootstrap\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")


def seed_closed_ticket_needing_reconciliation(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    active_ticket_id = manifest["active_ticket"]
    active_ticket = next(
        ticket for ticket in manifest["tickets"] if ticket["id"] == active_ticket_id
    )
    active_ticket["stage"] = "closeout"
    active_ticket["status"] = "done"
    active_ticket["resolution_state"] = "superseded"
    active_ticket["verification_state"] = "invalidated"
    workflow["stage"] = "closeout"
    workflow["status"] = "done"
    workflow["pending_process_verification"] = False
    workflow["bootstrap"] = {
        "status": "ready",
        "last_verified_at": "2026-03-26T00:00:00Z",
        "environment_fingerprint": compute_bootstrap_fingerprint(dest),
        "proof_artifact": ".opencode/state/bootstrap/synthetic-ready-bootstrap.md",
    }
    ticket_state = workflow.get("ticket_state")
    if isinstance(ticket_state, dict):
        active_ticket_state = ticket_state.get(active_ticket_id)
        if isinstance(active_ticket_state, dict):
            active_ticket_state["needs_reverification"] = False
    proof_path = (
        dest / ".opencode" / "state" / "bootstrap" / "synthetic-ready-bootstrap.md"
    )
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text("# Ready Bootstrap\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")


def seed_legacy_smoke_test_tool(dest: Path) -> None:
    tool_path = dest / ".opencode" / "tools" / "smoke_test.ts"
    tool_path.write_text(
        "\n".join(
            [
                'import { tool } from "@opencode-ai/plugin"',
                "",
                "export default tool({",
                '  description: "legacy smoke-test fixture",',
                "  args: {},",
                "  async execute() {",
                '    return JSON.stringify({ argv: ["python3", "-m", "pytest"] })',
                "  },",
                "})",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def seed_legacy_smoke_override_tool(dest: Path) -> None:
    tool_path = dest / ".opencode" / "tools" / "smoke_test.ts"
    tool_path.write_text(
        "\n".join(
            [
                'import { tool } from "@opencode-ai/plugin"',
                "",
                "type CommandSpec = {",
                "  argv: string[]",
                "}",
                "",
                "async function detectCommands(args: { command_override?: string[] }): Promise<CommandSpec[]> {",
                "  if (Array.isArray(args.command_override) && args.command_override.length > 0) {",
                "    return [{ argv: args.command_override }]",
                "  }",
                '  return [{ argv: ["uv", "run", "python", "-m", "pytest"] }]',
                "}",
                "",
                "export default tool({",
                '  description: "legacy smoke override fixture",',
                "  args: {",
                "    command_override: tool.schema.array(tool.schema.string()).optional(),",
                "  },",
                "  async execute(args) {",
                "    const commands = await detectCommands(args)",
                "    return JSON.stringify(commands)",
                "  },",
                "})",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def seed_legacy_smoke_acceptance_tool(dest: Path) -> None:
    tool_path = dest / ".opencode" / "tools" / "smoke_test.ts"
    tool_path.write_text(
        "\n".join(
            [
                'import { tool } from "@opencode-ai/plugin"',
                "",
                "type CommandSpec = {",
                "  argv: string[]",
                "}",
                "",
                "async function detectCommands(args: { test_paths?: string[] }): Promise<CommandSpec[]> {",
                "  const testTargets = Array.isArray(args.test_paths) ? args.test_paths : []",
                "  return [{ argv: ['uv', 'run', 'python', '-m', 'pytest', ...testTargets] }]",
                "}",
                "",
                "export default tool({",
                '  description: "legacy smoke acceptance fixture",',
                "  args: {",
                "    test_paths: tool.schema.array(tool.schema.string()).optional(),",
                "  },",
                "  async execute(args) {",
                "    const commands = await detectCommands(args)",
                "    return JSON.stringify(commands)",
                "  },",
                "})",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def seed_legacy_review_contract(dest: Path) -> None:
    workflow_doc = dest / "docs" / "process" / "workflow.md"
    workflow_text = workflow_doc.read_text(encoding="utf-8")
    workflow_text = workflow_text.replace(
        "`todo`, `ready`, `plan_review`, `in_progress`, `blocked`, `review`, `qa`, `smoke_test`, `done`",
        "`todo`, `ready`, `in_progress`, `blocked`, `review`, `qa`, `smoke_test`, `done`",
    )
    workflow_text = workflow_text.replace("`plan_review`", "plan review")
    workflow_text = workflow_text.replace(
        "the assigned ticket must already be in plan review and ", ""
    )
    workflow_doc.write_text(workflow_text, encoding="utf-8")
    workflow_tool = dest / ".opencode" / "lib" / "workflow.ts"
    workflow_tool.write_text(
        workflow_tool.read_text(encoding="utf-8").replace('"plan_review"', '"review"'),
        encoding="utf-8",
    )


def seed_legacy_stage_transition_contract(dest: Path) -> None:
    ticket_update = dest / ".opencode" / "tools" / "ticket_update.ts"
    ticket_text = ticket_update.read_text(encoding="utf-8")
    ticket_text = ticket_text.replace(
        'ticket.stage !== "plan_review"', 'ticket.status !== "plan_review"'
    )
    ticket_text = ticket_text.replace(
        "const requested = resolveRequestedTicketProgress(ticket, { stage: args.stage, status: args.status })",
        "const requested = { stage: args.stage || ticket.stage, status: args.status || ticket.status }",
    )
    ticket_text = ticket_text.replace(
        "    const lifecycleBlocker = validateLifecycleStageStatus(targetStage, targetStatus)\n    if (lifecycleBlocker) {\n      throw new Error(lifecycleBlocker)\n    }\n",
        "",
    )
    ticket_update.write_text(ticket_text, encoding="utf-8")

    workflow_tool = dest / ".opencode" / "lib" / "workflow.ts"
    workflow_text = workflow_tool.read_text(encoding="utf-8")
    workflow_text = workflow_text.replace(
        'export const LIFECYCLE_STAGES = new Set(["planning", "plan_review", "implementation", "review", "qa", "smoke-test", "closeout"])\n',
        "",
    )
    workflow_text = workflow_text.replace(
        "    return `Unsupported ticket stage: ${stage}. Use planning, plan_review, implementation, review, qa, smoke-test, or closeout.`\n",
        "    return null\n",
    )
    workflow_tool.write_text(workflow_text, encoding="utf-8")

    stage_gate = dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    stage_gate_text = stage_gate.read_text(encoding="utf-8")
    stage_gate_text = stage_gate_text.replace(
        'ticket.stage !== "plan_review"', 'ticket.status !== "plan_review"'
    )
    stage_gate_text = stage_gate_text.replace("resolveRequestedTicketProgress,\n", "")
    stage_gate_text = stage_gate_text.replace("validateLifecycleStageStatus,\n", "")
    stage_gate_text = stage_gate_text.replace(
        '        const requested = resolveRequestedTicketProgress(ticket, {\n          stage: typeof output.args.stage === "string" ? output.args.stage : undefined,\n          status: typeof output.args.status === "string" ? output.args.status : undefined,\n        })\n        const lifecycleBlocker = validateLifecycleStageStatus(requested.stage, requested.status)\n        if (lifecycleBlocker) {\n          throw new Error(lifecycleBlocker)\n        }\n',
        '        const requested = {\n          stage: typeof output.args.stage === "string" ? output.args.stage : ticket.stage,\n          status: typeof output.args.status === "string" ? output.args.status : ticket.status,\n        }\n',
    )
    stage_gate.write_text(stage_gate_text, encoding="utf-8")


def seed_smoke_artifact_bypass(dest: Path) -> None:
    artifact_write = dest / ".opencode" / "tools" / "artifact_write.ts"
    artifact_write.write_text(
        artifact_write.read_text(encoding="utf-8").replace(
            "Write the full body for a canonical planning, implementation, review, or QA artifact.",
            "Write the full body for a canonical planning, implementation, review, QA, or smoke-test artifact.",
        ),
        encoding="utf-8",
    )

    artifact_register = dest / ".opencode" / "tools" / "artifact_register.ts"
    artifact_register.write_text(
        artifact_register.read_text(encoding="utf-8").replace(
            "Register an existing canonical planning, implementation, review, or QA artifact.",
            "Register an existing canonical planning, implementation, review, QA, or smoke-test artifact.",
        ),
        encoding="utf-8",
    )

    stage_gate = dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    stage_gate_text = stage_gate.read_text(encoding="utf-8")
    stage_gate_text = stage_gate_text.replace(
        'const RESERVED_ARTIFACT_STAGES = new Set(["smoke-test"])\n', ""
    )
    stage_gate_text = stage_gate_text.replace(
        '        if (RESERVED_ARTIFACT_STAGES.has(stage)) {\n          const owner = stage === "smoke-test" ? "smoke_test" : "handoff_publish"\n          throw new Error(`Use ${owner} to create ${stage} artifacts. Generic artifact_register is not allowed for that stage.`)\n        }\n\n',
        "",
    )
    stage_gate_text = stage_gate_text.replace(
        '        if (RESERVED_ARTIFACT_STAGES.has(stage)) {\n          const owner = stage === "smoke-test" ? "smoke_test" : "handoff_publish"\n          throw new Error(`Use ${owner} to create ${stage} artifacts. Generic artifact_write is not allowed for that stage.`)\n        }\n',
        "",
    )
    stage_gate.write_text(stage_gate_text, encoding="utf-8")

    ticket_lookup = dest / ".opencode" / "tools" / "ticket_lookup.ts"
    ticket_lookup.write_text(
        ticket_lookup.read_text(encoding="utf-8").replace(
            "Use the smoke_test tool to produce the current smoke-test artifact. Do not fabricate a PASS artifact through generic artifact tools.",
            "Use a smoke-test artifact to record current results.",
        ),
        encoding="utf-8",
    )


def seed_handoff_ownership_conflict(dest: Path) -> None:
    stage_gate = dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    stage_gate.write_text(
        stage_gate.read_text(encoding="utf-8").replace(
            'const RESERVED_ARTIFACT_STAGES = new Set(["smoke-test"])',
            'const RESERVED_ARTIFACT_STAGES = new Set(["smoke-test", "handoff"])',
        ),
        encoding="utf-8",
    )


def seed_recovered_verification_log(dest: Path) -> Path:
    log_path = dest / "recovered-session-log.md"
    log_path.write_text(
        "\n".join(
            [
                "Unable to run verification commands — The bash tool is blocked by permission rules in this environment.",
                "Bootstrap was repaired and validation was retried.",
                "SYNTAX OK",
                "12 passed in 0.42s",
                "Result: PASS (scoped)",
                "Verified by running the recovery command above.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return log_path


def seed_coordinator_artifact_log(dest: Path) -> Path:
    log_path = dest / "coordinator-authorship-log.md"
    log_path.write_text(
        "\n".join(
            [
                "## Assistant (Smoke-Team-Leader · MiniMax-M2.7 · 5.0s)",
                "",
                "**Tool: artifact_write**",
                "",
                "**Input:**",
                "```json",
                '{"ticket_id":"EXEC-005","path":".opencode/state/implementations/exec-005-implementation-implementation.md","kind":"implementation","stage":"implementation","content":"# impl"}',
                "```",
                "",
                "## Assistant (Smoke-Team-Leader · MiniMax-M2.7 · 4.0s)",
                "",
                "**Tool: artifact_write**",
                "",
                "**Input:**",
                "```json",
                '{"ticket_id":"EXEC-005","path":".opencode/state/qa/exec-005-qa-qa.md","kind":"qa","stage":"qa","content":"# qa"}',
                "```",
                "",
                "## Assistant (Smoke-Team-Leader · MiniMax-M2.7 · 3.8s)",
                "",
                "**Tool: artifact_write**",
                "",
                "**Input:**",
                "```json",
                '{"ticket_id":"EXEC-005","path":".opencode/state/smoke-tests/exec-005-smoke-test-smoke-test.md","kind":"smoke-test","stage":"smoke-test","content":"# smoke"}',
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return log_path


def seed_missing_pytest_env(dest: Path) -> None:
    seed_uv_python_fixture(dest)
    src_pkg = dest / "src" / "smoke_pkg"
    src_pkg.mkdir(parents=True, exist_ok=True)
    (src_pkg / "__init__.py").write_text("__all__ = ['ok']\n", encoding="utf-8")
    tests_dir = dest / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_sample.py").write_text(
        "def test_smoke():\n    assert True\n", encoding="utf-8"
    )
    write_python_wrapper(dest / ".venv" / "bin" / "python", allow_pytest=False)


def seed_pyproject_only_pytest_env(dest: Path) -> None:
    seed_uv_python_fixture(dest, include_pytest_tool_config=True)
    src_pkg = dest / "src" / "smoke_pkg"
    src_pkg.mkdir(parents=True, exist_ok=True)
    (src_pkg / "__init__.py").write_text("__all__ = ['ok']\n", encoding="utf-8")
    write_python_wrapper(dest / ".venv" / "bin" / "python", allow_pytest=False)


def seed_helper_tool_exposure(dest: Path) -> None:
    helper_tool = dest / ".opencode" / "tools" / "_workflow.ts"
    helper_tool.write_text(
        "\n".join(
            [
                "export function _workflow_validateHandoffNextAction() {",
                "  return null",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def seed_helper_tool_failure_log(dest: Path) -> Path:
    log_path = dest / "helper-tool-failure-log.md"
    log_path.write_text(
        "\n".join(
            [
                "Available tools: ticket_lookup, handoff_publish, _workflow_validateHandoffNextAction",
                "",
                "## Assistant (Smoke-Team-Leader · MiniMax-M2.7 · 2.0s)",
                "",
                "**Tool: _workflow_validateHandoffNextAction**",
                "",
                "**Input:**",
                "```json",
                '{"ticket_id":"SETUP-001"}',
                "```",
                "",
                "**Error:**",
                "```text",
                "TypeError: def.execute is not a function",
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return log_path


def seed_smoke_override_failure_log(dest: Path) -> Path:
    log_path = dest / "smoke-override-failure-log.md"
    log_path.write_text(
        "\n".join(
            [
                "## Assistant (Smoke-Team-Leader · MiniMax-M2.7 · 2.1s)",
                "",
                "**Tool: smoke_test**",
                "",
                "**Input:**",
                "```json",
                '{"ticket_id":"EXEC-008","scope":"ticket","command_override":["UV_CACHE_DIR=/tmp/uv-cache","uv","run","pytest","tests/hub/test_security.py","-q","--tb=no"]}',
                "```",
                "",
                "**Output:**",
                "```json",
                '{"ticket_id":"EXEC-008","passed":false,"failure_classification":"environment","blocker":"Error: ENOENT: no such file or directory, posix_spawn \\"UV_CACHE_DIR=/tmp/uv-cache\\""}',
                "```",
                "",
                "Artifact note: Error: ENOENT: no such file or directory, posix_spawn 'UV_CACHE_DIR=/tmp/uv-cache'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return log_path


def seed_smoke_acceptance_scope_log(dest: Path) -> Path:
    log_path = dest / "smoke-acceptance-scope-log.md"
    log_path.write_text(
        "\n".join(
            [
                "Acceptance criterion:",
                "`UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_security.py -q --tb=no` exits 0.",
                "",
                "## Assistant (Smoke-Team-Leader · MiniMax-M2.7 · 5.0s)",
                "",
                "**Tool: smoke_test**",
                "",
                "**Input:**",
                "```json",
                '{"ticket_id":"EXEC-008","scope":"targeted","test_paths":["tests/hub/test_security.py"]}',
                "```",
                "",
                "**Output:**",
                "```json",
                '{"ticket_id":"EXEC-008","passed":false,"failure_classification":"ticket","commands":[{"label":"python compileall","command":"uv run python -m compileall -q -x (^|/)(\\\\.git|\\\\.opencode)(/|$) .","exit_code":0,"duration_ms":100},{"label":"pytest","command":"uv run python -m pytest tests/hub/test_security.py","exit_code":1,"duration_ms":2500}]}',
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return log_path


def write_diagnosis_manifest(
    diagnosis_dir: Path,
    *,
    generated_at: str,
    finding_count: int,
    recommendations: list[dict[str, object]] | None = None,
    supporting_logs: list[str] | None = None,
    diagnosis_kind: str = "initial_diagnosis",
    audit_package_commit: str | None = None,
) -> None:
    diagnosis_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "generated_at": generated_at,
        "repo_root": str(diagnosis_dir.parents[1]),
        "finding_count": finding_count,
        "diagnosis_kind": diagnosis_kind,
        "audit_package_commit": audit_package_commit or package_commit(),
        "ticket_recommendations": recommendations or [],
    }
    if supporting_logs:
        manifest["supporting_logs"] = supporting_logs
    (diagnosis_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def seed_false_clean_verification_history(dest: Path) -> Path:
    diagnosis_root = dest / "diagnosis"
    diagnosis_root.mkdir(parents=True, exist_ok=True)
    transcript_log = dest / "causal-session-log.md"
    transcript_log.write_text(
        "\n".join(
            [
                "## Assistant (Smoke-Team-Leader · MiniMax-M2.7 · 2.1s)",
                "",
                "**Tool: smoke_test**",
                "",
                "**Input:**",
                "```json",
                '{"ticket_id":"EXEC-008","scope":"ticket","command_override":["UV_CACHE_DIR=/tmp/uv-cache","uv","run","pytest","tests/hub/test_security.py","-q","--tb=no"]}',
                "```",
                "",
                "**Output:**",
                "```json",
                '{"ticket_id":"EXEC-008","passed":false,"failure_classification":"environment","blocker":"Error: ENOENT: no such file or directory, posix_spawn \\"UV_CACHE_DIR=/tmp/uv-cache\\""}',
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_diagnosis_manifest(
        diagnosis_root / "20260327-143940",
        generated_at="2026-03-27T14:39:40Z",
        finding_count=4,
        recommendations=[
            {
                "source_finding_code": "SESSION003",
                "route": "scafforge-repair",
                "title": "workflow bypass search",
            },
            {
                "source_finding_code": "SESSION005",
                "route": "scafforge-repair",
                "title": "coordinator artifact authorship",
            },
            {
                "source_finding_code": "WFLOW016",
                "route": "scafforge-repair",
                "title": "smoke override defect",
            },
            {
                "source_finding_code": "WFLOW017",
                "route": "scafforge-repair",
                "title": "smoke acceptance drift",
            },
        ],
        supporting_logs=[transcript_log.name],
    )
    write_diagnosis_manifest(
        diagnosis_root / "20260327-155950",
        generated_at="2026-03-27T15:59:50Z",
        finding_count=0,
        diagnosis_kind="post_repair_verification",
    )
    return transcript_log


def seed_false_clean_preceded_by_later_transcript_basis(dest: Path) -> None:
    diagnosis_root = dest / "diagnosis"
    diagnosis_root.mkdir(parents=True, exist_ok=True)
    write_diagnosis_manifest(
        diagnosis_root / "20260327-143940",
        generated_at="2026-03-27T14:39:40Z",
        finding_count=4,
        recommendations=[
            {
                "source_finding_code": "SESSION003",
                "route": "scafforge-repair",
                "title": "workflow bypass search",
            },
        ],
        supporting_logs=["causal-session-log.md"],
    )
    write_diagnosis_manifest(
        diagnosis_root / "20260327-155950",
        generated_at="2026-03-27T15:59:50Z",
        finding_count=0,
        diagnosis_kind="post_repair_verification",
    )
    write_diagnosis_manifest(
        diagnosis_root / "20260327-171300",
        generated_at="2026-03-27T17:13:00Z",
        finding_count=2,
        recommendations=[
            {
                "source_finding_code": "SESSION005",
                "route": "scafforge-repair",
                "title": "coordinator artifact authorship",
            },
        ],
        supporting_logs=["later-transcript.md"],
    )


def seed_historical_reconciliation_deadlock(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    provenance_path = dest / ".opencode" / "meta" / "bootstrap-provenance.json"
    diagnosis_root = dest / "diagnosis"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    manifest["tickets"].append(
        {
            "id": "EXEC-099",
            "title": "Synthetic historical deadlock ticket",
            "wave": 99,
            "lane": "workflow",
            "parallel_safe": False,
            "overlap_risk": "low",
            "stage": "closeout",
            "status": "done",
            "depends_on": [],
            "summary": "Synthetic superseded invalidated historical ticket.",
            "acceptance": ["Historical reconciliation is possible."],
            "decision_blockers": [],
            "artifacts": [],
            "resolution_state": "superseded",
            "verification_state": "invalidated",
            "follow_up_ticket_ids": [],
        }
    )
    manifest["active_ticket"] = "EXEC-099"
    workflow["active_ticket"] = "EXEC-099"
    workflow["stage"] = "closeout"
    workflow["status"] = "done"
    provenance["repair_history"] = []
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    if diagnosis_root.exists():
        shutil.rmtree(diagnosis_root)

    ticket_reconcile_path = dest / ".opencode" / "tools" / "ticket_reconcile.ts"
    ticket_reconcile_text = ticket_reconcile_path.read_text(encoding="utf-8")
    ticket_reconcile_text = ticket_reconcile_text.replace(
        "currentRegistryArtifact,\n", ""
    )
    ticket_reconcile_text = ticket_reconcile_text.replace(
        "function findEvidenceArtifact(sourceTicket: Ticket, targetTicket: Ticket, registry: Awaited<ReturnType<typeof loadArtifactRegistry>>, artifactPath: string): Artifact | undefined {\n"
        "  const normalized = normalizeRepoPath(artifactPath)\n"
        "  return [...sourceTicket.artifacts, ...targetTicket.artifacts].find(\n"
        '    (artifact) => artifact.path === normalized && artifact.trust_state === "current",\n'
        "  ) ?? currentRegistryArtifact(registry, normalized)\n"
        "}\n",
        "function findEvidenceArtifact(sourceTicket: Ticket, targetTicket: Ticket, artifactPath: string): Artifact | undefined {\n"
        "  const normalized = normalizeRepoPath(artifactPath)\n"
        "  return [...sourceTicket.artifacts, ...targetTicket.artifacts].find(\n"
        '    (artifact) => artifact.path === normalized && artifact.trust_state === "current",\n'
        "  )\n"
        "}\n",
    )
    ticket_reconcile_text = ticket_reconcile_text.replace(
        "    const registry = await loadArtifactRegistry()\n    const evidenceArtifact = findEvidenceArtifact(sourceTicket, targetTicket, registry, evidenceArtifactPath)\n",
        "    const registry = await loadArtifactRegistry()\n    const evidenceArtifact = findEvidenceArtifact(sourceTicket, targetTicket, evidenceArtifactPath)\n",
    )
    ticket_reconcile_text = ticket_reconcile_text.replace(
        "      throw new Error(`No current registered evidence artifact exists at ${evidenceArtifactPath} for this reconciliation.`)\n",
        "      throw new Error(`Neither ${sourceTicket.id} nor ${targetTicket.id} has a current evidence artifact at ${evidenceArtifactPath}.`)\n",
    )
    ticket_reconcile_text = ticket_reconcile_text.replace(
        '      targetTicket.verification_state = "reverified"\n',
        '      targetTicket.verification_state = "invalidated"\n',
    )
    ticket_reconcile_text = ticket_reconcile_text.replace(
        "        supersededTarget: supersedeTarget,\n", "        supersededTarget,\n"
    )
    ticket_reconcile_path.write_text(ticket_reconcile_text, encoding="utf-8")

    ticket_create_path = dest / ".opencode" / "tools" / "ticket_create.ts"
    ticket_create_text = ticket_create_path.read_text(encoding="utf-8")
    ticket_create_text = ticket_create_text.replace("  currentRegistryArtifact,\n", "")
    ticket_create_text = ticket_create_text.replace("  loadArtifactRegistry,\n", "")
    ticket_create_text = ticket_create_text.replace("  normalizeRepoPath,\n", "")
    ticket_create_text = ticket_create_text.replace(
        "    const registry = await loadArtifactRegistry()\n", ""
    )
    ticket_create_text = ticket_create_text.replace(
        "        const registryArtifact = evidenceArtifactPath ? currentRegistryArtifact(registry, normalizeRepoPath(evidenceArtifactPath)) : undefined\n"
        "        if (\n"
        "          !verificationArtifact &&\n"
        '          !(registryArtifact && registryArtifact.stage === "review" && registryArtifact.kind === "backlog-verification")\n'
        "        ) {\n",
        "        if (!verificationArtifact) {\n",
    )
    ticket_create_text = ticket_create_text.replace(
        "            `No current registered review/backlog-verification artifact exists at ${evidenceArtifactPath} for ${sourceTicket.id}.`,\n",
        "            `Source ticket ${sourceTicket.id} does not have a current review/backlog-verification artifact at ${evidenceArtifactPath}.`,\n",
    )
    ticket_create_text = ticket_create_text.replace(
        "        const registryArtifact = currentRegistryArtifact(registry, normalizeRepoPath(evidenceArtifactPath))\n"
        "        if (!evidenceArtifact && !registryArtifact) {\n"
        "          throw new Error(`No current registered evidence artifact exists at ${evidenceArtifactPath} for ${sourceTicket.id}.`)\n",
        "        if (!evidenceArtifact) {\n"
        "          throw new Error(`Source ticket ${sourceTicket.id} does not reference the evidence artifact ${evidenceArtifactPath}.`)\n",
    )
    ticket_create_path.write_text(ticket_create_text, encoding="utf-8")

    issue_intake_path = dest / ".opencode" / "tools" / "issue_intake.ts"
    issue_intake_text = issue_intake_path.read_text(encoding="utf-8")
    issue_intake_text = issue_intake_text.replace("  currentRegistryArtifact,\n", "")
    issue_intake_text = issue_intake_text.replace(
        "    const registry = await loadArtifactRegistry()\n"
        "    const evidenceArtifact = sourceTicket.artifacts.find((artifact) => artifact.path === evidenceArtifactPath)\n"
        "    const registryArtifact = currentRegistryArtifact(registry, normalizeRepoPath(evidenceArtifactPath))\n"
        "    if (!evidenceArtifact && !registryArtifact) {\n"
        "      throw new Error(`No current registered evidence artifact exists at ${evidenceArtifactPath} for ${sourceTicket.id}.`)\n"
        "    }\n",
        "    const evidenceArtifact = sourceTicket.artifacts.find((artifact) => artifact.path === evidenceArtifactPath)\n"
        "    if (!evidenceArtifact) {\n"
        "      throw new Error(`Source ticket ${sourceTicket.id} does not reference the evidence artifact ${evidenceArtifactPath}.`)\n"
        "    }\n"
        "    const registry = await loadArtifactRegistry()\n",
    )
    issue_intake_path.write_text(issue_intake_text, encoding="utf-8")


def seed_handoff_lease_contradiction_log(dest: Path) -> Path:
    log_path = dest / "handoff-lease-contradiction-log.md"
    log_path.write_text(
        "\n".join(
            [
                "## Assistant (Smoke-Team-Leader · MiniMax-M2.7 · 2.0s)",
                "",
                "**Tool: handoff_publish**",
                "",
                "**Input:**",
                "```json",
                '{"ticket_id":"EXEC-013"}',
                "```",
                "",
                "**Error:**",
                "```text",
                "missing_ticket_write_lease: closed ticket cannot hold a lease",
                "```",
                "",
                "The handoff_publish tool blocked with missing_ticket_write_lease because EXEC-013 was already closed.",
                "A closed ticket cannot hold a lease and the tool still requires active lease on closed ticket surfaces.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return log_path


def seed_acceptance_scope_tension_log(dest: Path) -> Path:
    log_path = dest / "acceptance-scope-tension-log.md"
    log_path.write_text(
        "\n".join(
            [
                "The acceptance criterion says `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/hub/services/node_health.py tests/conftest.py src/hub/services/tunnel_manager.py` exits 0.",
                "But the implementation notes the command exits 1 due to pre-existing I001 and F401 that are handled by EXEC-014.",
                "Those violations are out of EXEC-013 scope and the literal acceptance criterion creates a tension the reviewer must resolve.",
                "Should EXEC-014 scope items be fixed as part of EXEC-013 to satisfy the literal acceptance criterion?",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return log_path


def seed_operator_trap_log(dest: Path) -> Path:
    log_path = dest / "operator-trap-log.md"
    log_path.write_text(
        "\n".join(
            [
                "Cannot move to review before an implementation artifact exists.",
                "Cannot move to review before an implementation artifact exists.",
                "Trying a workaround because the workflow is blocked.",
                "The acceptance criterion says `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/hub/services/node_health.py tests/conftest.py src/hub/services/tunnel_manager.py` exits 0.",
                "Those failures are handled by EXEC-014 and are out of EXEC-013 scope, so the literal acceptance criterion creates a tension.",
                "The handoff_publish tool blocked with missing_ticket_write_lease because EXEC-013 was already closed.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return log_path


def seed_hidden_process_verification(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    ticket = manifest["tickets"][0]
    ticket["stage"] = "closeout"
    ticket["status"] = "done"
    ticket["resolution_state"] = "done"
    ticket["verification_state"] = "suspect"
    ticket["artifacts"] = [
        {
            "kind": "smoke-test",
            "stage": "smoke-test",
            "path": ".opencode/state/artifacts/history/demo/smoke-test/demo.md",
            "summary": "legacy smoke proof",
            "created_at": "2026-03-20T00:00:00Z",
            "trust_state": "current",
        }
    ]
    manifest["active_ticket"] = ticket["id"]
    workflow["active_ticket"] = ticket["id"]
    workflow["stage"] = "closeout"
    workflow["status"] = "done"
    workflow["pending_process_verification"] = True
    workflow["process_last_changed_at"] = "2026-03-25T00:00:00Z"
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def seed_truthful_process_verification(dest: Path) -> None:
    seed_hidden_process_verification(dest)
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    bootstrap_rel = ".opencode/state/bootstrap/synthetic-ready-bootstrap.md"
    bootstrap_path = dest / bootstrap_rel
    bootstrap_path.parent.mkdir(parents=True, exist_ok=True)
    bootstrap_path.write_text("# Ready Bootstrap\n", encoding="utf-8")
    workflow["bootstrap"] = {
        "status": "ready",
        "last_verified_at": "2026-03-27T01:30:00Z",
        "environment_fingerprint": compute_bootstrap_fingerprint(dest),
        "proof_artifact": bootstrap_rel,
    }
    workflow["repair_follow_on"] = {
        "outcome": "clean",
        "required_stages": [],
        "completed_stages": [],
        "blocking_reasons": [],
        "verification_passed": True,
        "handoff_allowed": True,
        "last_updated_at": "2026-03-27T01:44:04Z",
        "process_version": workflow["process_version"],
    }
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")


def seed_process_verification_clear_deadlock(
    dest: Path, *, stale_surfaces: bool
) -> None:
    seed_truthful_process_verification(dest)
    manifest_path = dest / "tickets" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    ticket = manifest["tickets"][0]
    ticket["artifacts"].append(
        {
            "kind": "backlog-verification",
            "stage": "review",
            "path": ".opencode/state/artifacts/history/demo/review/backlog-verification.md",
            "summary": "Historical trust restored under the current process contract.",
            "created_at": "2026-03-27T03:30:00Z",
            "trust_state": "current",
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    if stale_surfaces:
        start_here_path = dest / "START-HERE.md"
        latest_handoff_path = dest / ".opencode" / "state" / "latest-handoff.md"
        for surface_path in (start_here_path, latest_handoff_path):
            text = surface_path.read_text(encoding="utf-8")
            text = text.replace(
                "- handoff_status: workflow verification pending",
                "- handoff_status: ready for continued development",
            )
            text = text.replace(
                f"- done_but_not_fully_trusted: {ticket['id']}",
                "- done_but_not_fully_trusted: none",
            )
            text = re.sub(
                r"Use the team leader to route .*? across done tickets whose trust predates the current process contract\.",
                "All tickets complete and verified. Continue normal development.",
                text,
            )
            surface_path.write_text(text, encoding="utf-8")

        stage_gate_path = dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
        stage_gate_text = stage_gate_path.read_text(encoding="utf-8")
        stage_gate_text = stage_gate_text.replace(
            "        const processVerificationClearOnly = isWorkflowProcessVerificationClearOnly(output.args)\n"
            "        const processVerification = getProcessVerificationState(manifest, workflow, ticketId)\n"
            "        if (!(processVerificationClearOnly && processVerification.clearable_now)) {\n"
            "          await ensureTargetTicketWriteLease(ticketId)\n"
            "        }\n",
            "        await ensureTargetTicketWriteLease(ticketId)\n",
        )
        stage_gate_path.write_text(stage_gate_text, encoding="utf-8")


def seed_closed_follow_up_deadlock(dest: Path) -> None:
    stage_gate = dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    text = stage_gate.read_text(encoding="utf-8")
    if (
        "await ensureTargetTicketWriteLease(sourceTicketId || workflow.active_ticket)"
        not in text
    ):
        text = text.replace(
            '        if (sourceMode === "process_verification" && !workflow.pending_process_verification) {\n',
            '        await ensureTargetTicketWriteLease(sourceTicketId || workflow.active_ticket)\n        if (sourceMode === "process_verification" && !workflow.pending_process_verification) {\n',
        )
    issue_intake_marker = (
        "        const sourceTicket = getTicket(manifest, sourceTicketId)\n"
        '        if (sourceTicket.status !== "done" && sourceTicket.resolution_state !== "done" && sourceTicket.resolution_state !== "superseded") {\n'
    )
    if (
        issue_intake_marker in text
        and "        await ensureTargetTicketWriteLease(sourceTicketId)\n" not in text
    ):
        text = text.replace(
            issue_intake_marker,
            "        await ensureTargetTicketWriteLease(sourceTicketId)\n"
            + issue_intake_marker,
        )
    stage_gate.write_text(text, encoding="utf-8")


def seed_contradictory_follow_up_graph(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = manifest["tickets"][0]
    source["stage"] = "implementation"
    source["status"] = "in_progress"
    source["resolution_state"] = "open"
    child_id = "EXEC-CHILD-CONTRADICT"
    source["follow_up_ticket_ids"] = [child_id]
    manifest["tickets"].append(
        {
            "id": child_id,
            "title": "Synthetic contradictory follow-up",
            "wave": source["wave"],
            "lane": source["lane"],
            "parallel_safe": False,
            "overlap_risk": "high",
            "stage": "planning",
            "status": "todo",
            "depends_on": [source["id"]],
            "summary": "Synthetic child that both depends on and extends the same source ticket.",
            "acceptance": ["Contradictory graph is detected."],
            "decision_blockers": [],
            "artifacts": [],
            "resolution_state": "open",
            "verification_state": "suspect",
            "source_ticket_id": source["id"],
            "follow_up_ticket_ids": [],
            "source_mode": "split_scope",
            "split_kind": "sequential_dependent",
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def seed_open_parent_split_drift(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = manifest["tickets"][0]
    source["stage"] = "implementation"
    source["status"] = "in_progress"
    source["resolution_state"] = "open"
    child_id = "EXEC-CHILD-SPLIT"
    source["follow_up_ticket_ids"] = [child_id]
    manifest["tickets"].append(
        {
            "id": child_id,
            "title": "Synthetic non-canonical split child",
            "wave": source["wave"],
            "lane": source["lane"],
            "parallel_safe": False,
            "overlap_risk": "high",
            "stage": "planning",
            "status": "todo",
            "depends_on": [],
            "summary": "Synthetic child routed through the wrong source mode.",
            "acceptance": ["Open-parent split routing is detected."],
            "decision_blockers": [],
            "artifacts": [],
            "resolution_state": "open",
            "verification_state": "suspect",
            "source_ticket_id": source["id"],
            "follow_up_ticket_ids": [],
            "source_mode": "net_new_scope",
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def seed_superseded_follow_up_history(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = manifest["tickets"][0]
    child_id = "EXEC-SUPERSEDED-HISTORY"
    manifest["tickets"].append(
        {
            "id": child_id,
            "title": "Historical superseded follow-up",
            "wave": source["wave"],
            "lane": "remediation",
            "parallel_safe": False,
            "overlap_risk": "low",
            "stage": "closeout",
            "status": "done",
            "depends_on": [],
            "summary": "Synthetic superseded follow-up retained only for historical lineage.",
            "acceptance": ["Historical superseded follow-up stays closed."],
            "decision_blockers": [],
            "artifacts": [],
            "resolution_state": "superseded",
            "verification_state": "reverified",
            "finding_source": "EXEC-HISTORY-001",
            "source_ticket_id": source["id"],
            "follow_up_ticket_ids": [],
            "source_mode": "split_scope",
            "split_kind": "sequential_dependent",
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def seed_parent_retains_superseded_follow_up(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = manifest["tickets"][0]
    child_id = "EXEC-SUPERSEDED-LINK"
    source["follow_up_ticket_ids"] = [*source.get("follow_up_ticket_ids", []), child_id]
    manifest["tickets"].append(
        {
            "id": child_id,
            "title": "Superseded follow-up still linked from parent",
            "wave": source["wave"],
            "lane": "remediation",
            "parallel_safe": False,
            "overlap_risk": "low",
            "stage": "closeout",
            "status": "done",
            "depends_on": [],
            "summary": "Synthetic superseded follow-up still incorrectly listed by the parent.",
            "acceptance": ["Superseded follow-up is unlinked from the parent."],
            "decision_blockers": [],
            "artifacts": [],
            "resolution_state": "superseded",
            "verification_state": "reverified",
            "finding_source": "EXEC-HISTORY-002",
            "source_ticket_id": source["id"],
            "follow_up_ticket_ids": [],
            "source_mode": "split_scope",
            "split_kind": "sequential_dependent",
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def seed_blocked_split_parent(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = manifest["tickets"][0]
    source["stage"] = "implementation"
    source["status"] = "blocked"
    source["resolution_state"] = "open"
    child_id = "EXEC-CHILD-BLOCKED-SPLIT"
    source["follow_up_ticket_ids"] = [child_id]
    manifest["tickets"].append(
        {
            "id": child_id,
            "title": "Synthetic split child under blocked parent",
            "wave": source["wave"],
            "lane": source["lane"],
            "parallel_safe": False,
            "overlap_risk": "high",
            "stage": "planning",
            "status": "todo",
            "depends_on": [],
            "summary": "Synthetic child whose parent should remain open and non-foreground instead of blocked.",
            "acceptance": ["Blocked split parent is detected."],
            "decision_blockers": [],
            "artifacts": [],
            "resolution_state": "open",
            "verification_state": "suspect",
            "source_ticket_id": source["id"],
            "follow_up_ticket_ids": [],
            "source_mode": "split_scope",
            "split_kind": "sequential_dependent",
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def seed_bootstrap_guidance_drift(dest: Path) -> None:
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    workflow["bootstrap"] = {
        "status": "failed",
        "last_verified_at": "2026-03-25T23:02:26Z",
        "environment_fingerprint": "synthetic-bootstrap",
        "proof_artifact": ".opencode/state/bootstrap/synthetic-bootstrap-proof.md",
    }
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")

    ticket_lookup = dest / ".opencode" / "tools" / "ticket_lookup.ts"
    ticket_lookup.write_text(
        ticket_lookup.read_text(encoding="utf-8").replace(
            "Bootstrap is ${bootstrapStatus}. Run environment_bootstrap first, then rerun ticket_lookup before attempting lifecycle transitions.",
            "Bootstrap is ${bootstrapStatus}. Continue normal lifecycle routing after checking the current stage.",
        ),
        encoding="utf-8",
    )

    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    team_leader.write_text(
        team_leader.read_text(encoding="utf-8").replace(
            "If `ticket_lookup.bootstrap.status` is not `ready`, treat `environment_bootstrap` as the next required tool call, rerun `ticket_lookup` after it completes, and do not continue normal lifecycle routing until bootstrap succeeds.\n",
            "",
        ),
        encoding="utf-8",
    )

    ticket_execution = dest / ".opencode" / "skills" / "ticket-execution" / "SKILL.md"
    ticket_execution.write_text(
        ticket_execution.read_text(encoding="utf-8").replace(
            "- if `ticket_lookup.bootstrap.status` is not `ready`, stop normal lifecycle routing, run `environment_bootstrap`, then rerun `ticket_lookup` before any `ticket_update`\n",
            "",
        ),
        encoding="utf-8",
    )


def seed_split_lease_guidance(dest: Path) -> None:
    workflow_doc = dest / "docs" / "process" / "workflow.md"
    workflow_doc.write_text(
        workflow_doc.read_text(encoding="utf-8").replace(
            "- the team leader owns `ticket_claim` and `ticket_release`; planning, implementation, review, QA, and optional handoff specialists write only under the already-active ticket lease\n",
            "",
        ),
        encoding="utf-8",
    )
    implementer = next((dest / ".opencode" / "agents").glob("*implementer*.md"))
    implementer.write_text(
        implementer.read_text(encoding="utf-8")
        .replace(
            "  environment_bootstrap: allow\n",
            "  environment_bootstrap: allow\n  ticket_claim: allow\n  ticket_release: allow\n",
        )
        .replace(
            "- the team leader already owns lease claim and release; if the required ticket lease is missing, return a blocker instead of claiming it yourself\n",
            "- claim the assigned ticket with `ticket_claim` before write-capable work and release it with `ticket_release` when the bounded implementation pass is complete\n",
        ),
        encoding="utf-8",
    )


def seed_resume_truth_hierarchy_drift(dest: Path) -> None:
    latest_handoff = dest / ".opencode" / "state" / "latest-handoff.md"
    if latest_handoff.exists():
        latest_handoff.unlink()

    resume = dest / ".opencode" / "commands" / "resume.md"
    resume.write_text(
        resume.read_text(encoding="utf-8")
        .replace(
            "Resume from `tickets/manifest.json` and `.opencode/state/workflow-state.json` first. Use `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` only as derived restart surfaces that must agree with canonical state.\n",
            "Resume from `START-HERE.md` first and use the other workflow files as support when needed.\n",
        )
        .replace(
            "- Treat the active open ticket as the primary lane even when historical reverification is pending.\n",
            "",
        ),
        encoding="utf-8",
    )

    workflow_doc = dest / "docs" / "process" / "workflow.md"
    workflow_doc.write_text(
        workflow_doc.read_text(encoding="utf-8").replace(
            "- open active-ticket work remains the primary foreground lane; post-migration reverification is a follow-up path, not a reason to ignore an already-open active ticket\n",
            "",
        ),
        encoding="utf-8",
    )


def seed_legacy_repair_follow_on_gate_leak(dest: Path) -> None:
    resume = dest / ".opencode" / "commands" / "resume.md"
    resume.write_text(
        resume.read_text(encoding="utf-8").replace(
            "- Reconfirm `repair_follow_on.outcome`; only `managed_blocked` is a primary blocker for ordinary ticket lifecycle work.\n",
            "- Reconfirm `repair_follow_on.handoff_allowed`; if it is false, stop ordinary ticket lifecycle work.\n",
        ),
        encoding="utf-8",
    )
    latest_handoff = dest / ".opencode" / "state" / "latest-handoff.md"
    latest_handoff.write_text(
        latest_handoff.read_text(encoding="utf-8").replace(
            "- repair_follow_on_updated_at:",
            "- repair_follow_on_handoff_allowed: true\n- repair_follow_on_updated_at:",
        ),
        encoding="utf-8",
    )


def seed_invocation_log_coordinator_artifacts(dest: Path) -> None:
    log_path = dest / ".opencode" / "state" / "invocation-log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    events = [
        {
            "event": "tool.execute.before",
            "timestamp": "2026-03-26T00:00:00Z",
            "agent": "smoke-team-leader",
            "tool": "artifact_write",
            "args": {
                "ticket_id": "SETUP-001",
                "stage": "planning",
                "kind": "planning",
                "path": ".opencode/state/plans/setup-001-planning-plan.md",
            },
        },
        {
            "event": "tool.execute.before",
            "timestamp": "2026-03-26T00:01:00Z",
            "agent": "smoke-team-leader",
            "tool": "artifact_write",
            "args": {
                "ticket_id": "SETUP-001",
                "stage": "qa",
                "kind": "qa",
                "path": ".opencode/state/qa/setup-001-qa-qa.md",
            },
        },
    ]
    log_path.write_text(
        "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
    )


def seed_open_active_ticket_with_pending_verification(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    active_ticket = manifest["tickets"][0]
    active_ticket["stage"] = "implementation"
    active_ticket["status"] = "in_progress"
    active_ticket["resolution_state"] = "open"
    active_ticket["verification_state"] = "suspect"
    manifest["tickets"].append(
        {
            "id": "DONE-900",
            "title": "Historical done ticket requiring reverification",
            "wave": 9,
            "lane": "repo-foundation",
            "parallel_safe": False,
            "overlap_risk": "high",
            "stage": "closeout",
            "status": "done",
            "depends_on": [],
            "summary": "Historical done ticket",
            "acceptance": ["remains trusted after reverification"],
            "decision_blockers": [],
            "artifacts": [
                {
                    "kind": "smoke-test",
                    "stage": "smoke-test",
                    "path": ".opencode/state/smoke-tests/done-900-smoke-test-smoke-test.md",
                    "summary": "legacy smoke proof",
                    "created_at": "2026-03-20T00:00:00Z",
                    "trust_state": "current",
                }
            ],
            "resolution_state": "done",
            "verification_state": "suspect",
            "follow_up_ticket_ids": [],
        }
    )
    workflow["active_ticket"] = active_ticket["id"]
    workflow["stage"] = "implementation"
    workflow["status"] = "in_progress"
    workflow["pending_process_verification"] = True
    workflow["process_last_changed_at"] = "2026-03-25T00:00:00Z"
    workflow["bootstrap"] = {
        "status": "ready",
        "last_verified_at": "2026-03-26T00:00:00Z",
        "environment_fingerprint": compute_bootstrap_fingerprint(dest),
        "proof_artifact": ".opencode/state/bootstrap/synthetic-ready-bootstrap.md",
    }
    proof_path = (
        dest / ".opencode" / "state" / "bootstrap" / "synthetic-ready-bootstrap.md"
    )
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text("# Ready Bootstrap\n", encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def seed_reverification_deadlock(dest: Path) -> None:
    stage_gate = dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    text = stage_gate.read_text(encoding="utf-8")
    text = text.replace(
        '        const ticket = getTicket(manifest, ticketId)\n        if (!ticketEligibleForTrustRestoration(ticket)) {\n          throw new Error(`Ticket ${ticket.id} must still be a historical done or reopened ticket before ticket_reverify can restore trust.`)\n        }\n',
        "        await ensureTargetTicketWriteLease(ticketId)\n",
    )
    stage_gate.write_text(text, encoding="utf-8")


def seed_team_leader_workflow_drift(dest: Path) -> None:
    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    text = team_leader.read_text(encoding="utf-8")
    text = text.replace(
        "Treat `ticket_lookup.transition_guidance` as the canonical next-step summary before you call `ticket_update`.\n",
        "",
    )
    text = text.replace(
        "- do not probe alternate stage or status values when a lifecycle error repeats; re-run `ticket_lookup`, inspect `transition_guidance`, load `ticket-execution` if needed, and return a blocker instead of inventing a workaround\n",
        "",
    )
    text = text.replace(
        "- do not create planning, implementation, review, QA, or smoke-test artifacts yourself; route those bodies through the assigned specialist lane, and let `smoke_test` produce smoke-test artifacts\n",
        "",
    )
    text = text.replace("- use human slash commands only as entrypoints\n", "")
    team_leader.write_text(text, encoding="utf-8")


def seed_thin_ticket_execution(dest: Path) -> None:
    skill_path = dest / ".opencode" / "skills" / "ticket-execution" / "SKILL.md"
    skill_path.write_text(
        "\n".join(
            [
                "---",
                "name: ticket-execution",
                "description: Minimal workflow notes.",
                "---",
                "",
                "# Ticket Execution",
                "",
                "Follow the ticket workflow.",
                "",
                "1. planning",
                "2. implementation",
                "3. review",
                "4. qa",
                "5. done",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def seed_managed_blocked_deadlock(dest: Path) -> None:
    """Seed a repo into managed_blocked with only host-only required stages remaining.

    This is the deadlock state WFLOW030 must detect: repair_follow_on.outcome =
    managed_blocked, required stages are non-empty, and every unresolved stage is
    host-only (project-skill-bootstrap, opencode-team-bootstrap, or
    agent-prompt-engineering).  The ticket_update.ts guard must also be present.
    """
    import json as _json

    wf_path = dest / ".opencode" / "state" / "workflow-state.json"
    wf = _json.loads(wf_path.read_text(encoding="utf-8"))
    wf.setdefault("repair_follow_on", {})
    wf["repair_follow_on"]["outcome"] = "managed_blocked"
    wf["repair_follow_on"]["required_stages"] = [
        "opencode-team-bootstrap",
        "agent-prompt-engineering",
    ]
    wf["repair_follow_on"]["completed_stages"] = []
    wf["repair_follow_on"]["allowed_follow_on_tickets"] = []
    wf_path.write_text(_json.dumps(wf, indent=2), encoding="utf-8")


def verify_render(dest: Path, *, expect_full_repo: bool) -> None:
    checklist = json.loads(CHECKLIST.read_text(encoding="utf-8"))
    for relative in checklist["required_files"]:
        path = dest / relative
        if (
            expect_full_repo
            or str(relative).startswith(".opencode")
            or str(relative) == "opencode.jsonc"
        ):
            if not path.exists():
                raise RuntimeError(f"Missing expected file: {path}")

    for relative in checklist["required_directories"]:
        path = dest / relative
        if expect_full_repo or str(relative).startswith(".opencode"):
            if not path.exists():
                raise RuntimeError(f"Missing expected directory: {path}")

    manifest = (
        json.loads((dest / "tickets" / "manifest.json").read_text(encoding="utf-8"))
        if expect_full_repo
        else None
    )
    if manifest is not None:
        if "tickets" not in manifest:
            raise RuntimeError("tickets/manifest.json is missing a tickets key")
        if manifest.get("version") != 3:
            raise RuntimeError("tickets/manifest.json should use version 3")
        if not manifest["tickets"]:
            raise RuntimeError("tickets/manifest.json must contain at least one ticket")
        first_ticket = manifest["tickets"][0]
        for key in (
            "wave",
            "parallel_safe",
            "overlap_risk",
            "decision_blockers",
            "resolution_state",
            "verification_state",
        ):
            if key not in first_ticket:
                raise RuntimeError(
                    f"tickets/manifest.json first ticket is missing `{key}`"
                )

        workflow = json.loads(
            (dest / ".opencode" / "state" / "workflow-state.json").read_text(
                encoding="utf-8"
            )
        )
        for key in (
            "process_version",
            "pending_process_verification",
            "parallel_mode",
            "ticket_state",
            "bootstrap",
            "lane_leases",
            "state_revision",
        ):
            if key not in workflow:
                raise RuntimeError(
                    f".opencode/state/workflow-state.json is missing `{key}`"
                )
        active_ticket = manifest.get("active_ticket")
        if not isinstance(workflow.get("ticket_state"), dict):
            raise RuntimeError(
                ".opencode/state/workflow-state.json must contain a ticket_state map"
            )
        if (
            isinstance(active_ticket, str)
            and active_ticket not in workflow["ticket_state"]
        ):
            raise RuntimeError(
                "workflow-state ticket_state must contain the active ticket entry"
            )
        active_ticket_state = (
            workflow["ticket_state"].get(active_ticket, {})
            if isinstance(active_ticket, str)
            else {}
        )
        for key in ("reopen_count", "needs_reverification"):
            if key not in active_ticket_state:
                raise RuntimeError(
                    f"workflow-state active ticket entry is missing `{key}`"
                )

        agents_dir = dest / ".opencode" / "agents"
        agent_names = {path.name for path in agents_dir.glob("*.md")}
        required_agent_suffixes = checklist.get("required_agent_suffixes")
        if not required_agent_suffixes:
            raise RuntimeError(
                "opencode-conformance-checklist.json is missing required_agent_suffixes"
            )
        for suffix in required_agent_suffixes:
            if not any(name.endswith(f"{suffix}.md") for name in agent_names):
                raise RuntimeError(f"Missing expected agent with suffix `{suffix}`")

        skills_dir = dest / ".opencode" / "skills"
        required_skill_ids = checklist.get("required_skill_ids")
        if not required_skill_ids:
            raise RuntimeError(
                "opencode-conformance-checklist.json is missing required_skill_ids"
            )
        for skill_id in required_skill_ids:
            skill_file = skills_dir / skill_id / "SKILL.md"
            if not skill_file.exists():
                raise RuntimeError(f"Missing expected local skill `{skill_id}`")

        start_here = (dest / "START-HERE.md").read_text(encoding="utf-8")
        for heading in (
            "## Current Or Next Ticket",
            "## Generation Status",
            "## Post-Generation Audit Status",
        ):
            if heading not in start_here:
                raise RuntimeError(
                    f"START-HERE.md is missing required section `{heading}`"
                )
        for forbidden in ("## Process Contract", "## Current Ticket"):
            if forbidden in start_here:
                raise RuntimeError(
                    f"START-HERE.md still contains deprecated section `{forbidden}`"
                )

        context_snapshot = (
            dest / ".opencode" / "state" / "context-snapshot.md"
        ).read_text(encoding="utf-8")
        for heading in (
            "## Active Ticket",
            "## Bootstrap",
            "## Process State",
            "## Lane Leases",
        ):
            if heading not in context_snapshot:
                raise RuntimeError(
                    f"context-snapshot.md is missing required section `{heading}`"
                )


def main() -> int:
    workspace = Path(tempfile.mkdtemp(prefix="scafforge-smoke-"))
    host_has_uv = shutil.which("uv") is not None
    host_has_npm = shutil.which("npm") is not None
    try:
        if not host_has_uv:
            print(
                "Warning: uv is not available on this host; uv-dependent smoke coverage will be skipped.",
                file=sys.stderr,
            )
        full_dest = workspace / "full"
        opencode_dest = workspace / "opencode"
        strong_dest = workspace / "strong"

        common = [
            sys.executable,
            str(BOOTSTRAP),
            "--project-name",
            "Smoke Example",
            "--project-slug",
            "smoke-example",
            "--agent-prefix",
            "smoke",
            "--model-provider",
            "openrouter",
            "--planner-model",
            "openrouter/anthropic/claude-sonnet-4.5",
            "--implementer-model",
            "openrouter/openai/gpt-5-codex",
            "--utility-model",
            "openrouter/openai/gpt-5-mini",
            "--stack-label",
            "framework-agnostic",
            "--force",
        ]

        run(common + ["--dest", str(full_dest), "--scope", "full"], ROOT)
        run(common + ["--dest", str(opencode_dest), "--scope", "opencode"], ROOT)
        run(
            common
            + ["--dest", str(strong_dest), "--scope", "full", "--model-tier", "strong"],
            ROOT,
        )

        verify_render(full_dest, expect_full_repo=True)
        verify_render(opencode_dest, expect_full_repo=False)
        verify_render(strong_dest, expect_full_repo=True)

        provenance = json.loads(
            (full_dest / ".opencode" / "meta" / "bootstrap-provenance.json").read_text(
                encoding="utf-8"
            )
        )
        if provenance.get("runtime_models", {}).get("tier") != "weak":
            raise RuntimeError(
                "Generated bootstrap provenance should default the runtime model tier to weak"
            )

        strong_provenance = json.loads(
            (strong_dest / ".opencode" / "meta" / "bootstrap-provenance.json").read_text(
                encoding="utf-8"
            )
        )
        if strong_provenance.get("runtime_models", {}).get("tier") != "strong":
            raise RuntimeError(
                "Generated bootstrap provenance should record an explicit strong runtime model tier"
            )

        model_matrix = (full_dest / "docs" / "process" / "model-matrix.md").read_text(
            encoding="utf-8"
        )
        for expected in (
            "- model tier: `weak`",
            "- prompt density: `full checklists, explicit examples, and repeated truth-source reminders`",
        ):
            if expected not in model_matrix:
                raise RuntimeError(
                    f"Generated model-matrix.md is missing required model-tier detail: {expected}"
                )

        strong_model_matrix = (
            strong_dest / "docs" / "process" / "model-matrix.md"
        ).read_text(encoding="utf-8")
        if "- model tier: `strong`" not in strong_model_matrix:
            raise RuntimeError(
                "Generated model-matrix.md should reflect an explicit strong model tier"
            )

        va_finish_dest = workspace / "va-finish-contract"
        run(
            [
                sys.executable,
                str(BOOTSTRAP),
                "--project-name",
                "VA Finish Probe",
                "--project-slug",
                "va-finish-probe",
                "--agent-prefix",
                "vafinish",
                "--model-provider",
                "openrouter",
                "--planner-model",
                "openrouter/anthropic/claude-sonnet-4.5",
                "--implementer-model",
                "openrouter/openai/gpt-5-codex",
                "--utility-model",
                "openrouter/openai/gpt-5-mini",
                "--stack-label",
                "godot-3d-android-game",
                "--deliverable-kind",
                "Android APK for local testing and direct device installation",
                "--placeholder-policy",
                "Procedural/programmatic sprites acceptable. Colored shapes with basic animations. No placeholder art in final build.",
                "--visual-finish-target",
                "2D top-down view with procedural sprites. Clean, readable gameplay.",
                "--audio-finish-target",
                "Minimal: procedural/generated SFX. Background music optional.",
                "--content-source-plan",
                "Procedural generation — sprites created programmatically via GDScript. No external assets.",
                "--finish-acceptance-signals",
                "APK compiles and installs. All waves playable. Touch controls work. Score tracking functions.",
                "--dest",
                str(va_finish_dest),
                "--scope",
                "full",
                "--force",
            ],
            ROOT,
        )
        make_stack_skill_non_placeholder(va_finish_dest)
        va_finish_manifest = json.loads(
            (va_finish_dest / "tickets" / "manifest.json").read_text(encoding="utf-8")
        )
        va_finish_tickets = {
            str(ticket.get("id", "")).strip(): ticket
            for ticket in va_finish_manifest.get("tickets", [])
            if isinstance(ticket, dict)
        }
        if not {"VISUAL-001", "FINISH-VALIDATE-001", "RELEASE-001"}.issubset(
            va_finish_tickets
        ):
            raise RuntimeError(
                "Godot Android repos whose finish contract forbids placeholder output should seed finish ownership and finish validation tickets even when procedural art is allowed."
            )
        if "FINISH-VALIDATE-001" not in va_finish_tickets["RELEASE-001"].get(
            "depends_on", []
        ):
            raise RuntimeError(
                "RELEASE-001 should depend on FINISH-VALIDATE-001 when the finish contract still imposes a non-placeholder gameplay/visual finish bar."
            )
        va_finish_verify = run_json(
            [sys.executable, str(VERIFY_GENERATED), str(va_finish_dest), "--format", "json"],
            ROOT,
        )
        if (
            va_finish_verify.get("immediately_continuable") is not True
            or va_finish_verify.get("finding_count") != 0
        ):
            raise RuntimeError(
                "VA-style procedural finish contracts should pass continuation verification once finish ownership is seeded."
            )

        model_profile_skill = (
            full_dest / ".opencode" / "skills" / "model-operating-profile" / "SKILL.md"
        ).read_text(encoding="utf-8")
        for expected in (
            "- model tier: `weak`",
            "- prompt density: `full checklists, explicit examples, and repeated truth-source reminders`",
        ):
            if expected not in model_profile_skill:
                raise RuntimeError(
                    f"Generated model-operating-profile skill is missing required line: {expected}"
                )

        team_leader_prompt = next(
            (full_dest / ".opencode" / "agents").glob("*team-leader*.md")
        ).read_text(encoding="utf-8")
        for expected in (
            "Stop conditions:",
            "Advancement rules:",
            "Ticket ownership:",
            "Contradiction resolution:",
            "three consecutive attempts to advance the same ticket fail with the same error or blocker signature",
            "if the verdict is `FAIL`, `REJECT`, or `BLOCKED`",
            "when `tickets/manifest.json` and `.opencode/state/workflow-state.json` disagree about ticket stage, status, dependencies, or the active foreground ticket, trust `tickets/manifest.json`",
            "Stack-specific build, verification, or load-check commands",
        ):
            if expected not in team_leader_prompt:
                raise RuntimeError(
                    f"Generated team leader prompt is missing required hardening section: {expected}"
                )

        implementer_prompt = next(
            (full_dest / ".opencode" / "agents").glob("*implementer*.md")
        ).read_text(encoding="utf-8")
        for expected in (
            "Build verification:",
            "Scope:",
            "Stack-specific notes:",
            "SCAFFORGE:STACK_SPECIFIC_IMPLEMENTATION_NOTES START",
            "modify workflow-state, manifest, or restart-surface files unless the approved ticket explicitly targets those managed surfaces",
        ):
            if expected not in implementer_prompt:
                raise RuntimeError(
                    f"Generated implementer prompt is missing required hardening section: {expected}"
                )

        tester_qa_prompt = next(
            (full_dest / ".opencode" / "agents").glob("*tester-qa*.md")
        ).read_text(encoding="utf-8")
        for expected in (
            '"echo *": allow',
            '"test -f *": allow',
            '"[ -f *": allow',
            '"godot *": allow',
        ):
            if expected not in tester_qa_prompt:
                raise RuntimeError(
                    f"Generated tester-qa permissions should allow stack-guided safe diagnostics: {expected}"
                )

        shell_inspect_prompt = next(
            (full_dest / ".opencode" / "agents").glob("*utility-shell-inspect*.md")
        ).read_text(encoding="utf-8")
        for expected in (
            '"echo *": allow',
            '"test -f *": allow',
            '"[ -d *": allow',
            '"godot4 *": allow',
        ):
            if expected not in shell_inspect_prompt:
                raise RuntimeError(
                    f"Generated shell-inspect permissions should allow safe runtime evidence commands: {expected}"
                )

        delegation_doc = (full_dest / "docs" / "AGENT-DELEGATION.md").read_text(
            encoding="utf-8"
        )
        for expected in (
            "# Agent Delegation",
            "## Delegation Chain",
            "## Escalation Path",
            "## Restart Procedure",
        ):
            if expected not in delegation_doc:
                raise RuntimeError(
                    f"Generated AGENT-DELEGATION.md is missing required section: {expected}"
                )

        start_here = (full_dest / "START-HERE.md").read_text(encoding="utf-8")
        if "docs/AGENT-DELEGATION.md" not in start_here:
            raise RuntimeError(
                "Generated START-HERE.md should reference docs/AGENT-DELEGATION.md in the startup path"
            )

        generated_ticket_update = (
            full_dest / ".opencode" / "tools" / "ticket_update.ts"
        ).read_text(encoding="utf-8")
        if '"plan_review"' not in generated_ticket_update:
            raise RuntimeError(
                "Generated ticket_update.ts should expose the explicit plan_review status"
            )
        generated_bootstrap = (
            full_dest / ".opencode" / "tools" / "environment_bootstrap.ts"
        ).read_text(encoding="utf-8")
        for expected in (
            "[project.optional-dependencies]",
            "[dependency-groups]",
            "[tool.uv.dev-dependencies]",
            "[tool.pytest.ini_options]",
        ):
            if expected not in generated_bootstrap:
                raise RuntimeError(
                    f"Generated environment_bootstrap.ts should detect {expected} when resolving Python bootstrap inputs"
                )
        if (
            "extractTomlSectionBody" not in generated_bootstrap
            or "escapeRegExp" not in generated_bootstrap
        ):
            raise RuntimeError(
                "Generated environment_bootstrap.ts should use explicit TOML section parsing helpers for dependency-layout detection"
            )
        if "(?:\\\\n\\\\[|$)" in generated_bootstrap:
            raise RuntimeError(
                "Generated environment_bootstrap.ts should not keep the legacy multiline section regex that misses optional dependency bodies"
            )
        if (
            "defaultBootstrapProofPath" not in generated_bootstrap
            or "normalizeRepoPath" not in generated_bootstrap
        ):
            raise RuntimeError(
                "Generated environment_bootstrap.ts should persist bootstrap proof through canonical artifact-path helpers"
            )
        for expected in (
            "host_surface_classification",
            "failure_classification",
            "blocked_by_permissions",
            "permission_restriction",
        ):
            if expected not in generated_bootstrap:
                raise RuntimeError(
                    "Generated environment_bootstrap.ts should classify missing-tool and permission-restriction host failures explicitly"
                )
        for expected in (
            "SAFE_BOOTSTRAP_PATTERNS",
            'id: "godot"',
            'id: "java-android"',
            'id: "c-cpp"',
            'id: "dotnet"',
            'id: "flutter-dart"',
            'id: "swift"',
            'id: "zig"',
            'id: "ruby"',
            'id: "elixir"',
            'id: "php"',
            'id: "haskell"',
            'id: "generic-make"',
            'id: "generic-shell"',
            "workflow.bootstrap_blockers = blockers",
            "blockers,",
        ):
            if expected not in generated_bootstrap:
                raise RuntimeError(
                    "Generated environment_bootstrap.ts should expose the universal adapter registry and persist bootstrap blockers"
                )
        generated_stage_gate = (
            full_dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
        ).read_text(encoding="utf-8")
        for expected in (
            "godot(?:4)?",
            "dotnet\\s+(?:build|test|run|publish|restore|--info)",
            "flutter\\s+(?:build|test|analyze|pub\\s+get)",
            "swift\\s+(?:build|test|run|--version)",
            "mix\\s+(?:test|compile|run|deps\\.get)",
        ):
            if expected not in generated_stage_gate:
                raise RuntimeError(
                    "Generated stage-gate-enforcer.ts should allow the expanded multi-stack safe command surface"
                )
        generated_workflow_state = json.loads(
            (full_dest / ".opencode" / "state" / "workflow-state.json").read_text(
                encoding="utf-8"
            )
        )
        if generated_workflow_state.get("bootstrap_blockers") != []:
            raise RuntimeError(
                "Generated workflow-state.json should seed bootstrap_blockers as an empty persisted list"
            )
        generated_smoke_test = (
            full_dest / ".opencode" / "tools" / "smoke_test.ts"
        ).read_text(encoding="utf-8")
        if "findExistingRepoVenvExecutable" not in generated_smoke_test:
            raise RuntimeError(
                "Generated smoke_test.ts should support repo-local .venv Python execution across platform-specific virtualenv layouts"
            )
        if "[tool.pytest.ini_options]" not in generated_smoke_test:
            raise RuntimeError(
                "Generated smoke_test.ts should detect pyproject-only pytest configuration, not only tests/ or pytest.ini"
            )
        for expected in ("scope:", "test_paths:", "args.scope", "args.test_paths"):
            if expected not in generated_smoke_test:
                raise RuntimeError(
                    "Generated smoke_test.ts should expose scoped smoke inputs and thread them into execution"
                )
        for expected in (
            "godot(?:4)?\\s+--headless",
            "(?:\\./gradlew|gradle)\\s+test",
            "dotnet\\s+test",
            "flutter\\s+test",
            "swift\\s+test",
            "zig\\s+test",
            "mix\\s+test",
            "cmake\\s+--build",
        ):
            if expected not in generated_smoke_test:
                raise RuntimeError(
                    "Generated smoke_test.ts should recognize broader cross-stack smoke command patterns"
                )
        opencode_team_bootstrap_skill = (
            ROOT / "skills" / "opencode-team-bootstrap" / "SKILL.md"
        ).read_text(encoding="utf-8")
        for expected in (
            "Inject stack-specific implementation notes:",
            "docs/AGENT-DELEGATION.md",
            "The implementer prompt includes rewritten stack-specific notes instead of leaving scaffold placeholder text behind",
        ):
            if expected not in opencode_team_bootstrap_skill:
                raise RuntimeError(
                    f"opencode-team-bootstrap skill is missing phase 5 requirement: {expected}"
                )

        agent_prompt_engineering_skill = (
            ROOT / "skills" / "agent-prompt-engineering" / "SKILL.md"
        ).read_text(encoding="utf-8")
        for expected in (
            "If the tier is missing, default to `weak`",
            "Step C1: Match prompt density to the configured model tier",
            "prompt density matches the configured model tier",
        ):
            if expected not in agent_prompt_engineering_skill:
                raise RuntimeError(
                    f"agent-prompt-engineering skill is missing phase 5 requirement: {expected}"
                )

        generated_stack_standards = (
            full_dest / ".opencode" / "skills" / "stack-standards" / "SKILL.md"
        ).read_text(encoding="utf-8")
        for expected in (
            "### Quality Gate Commands",
            "Python: `ruff check .`, `mypy .` when configured, `pytest --collect-only`",
            "Node.js: `npm run lint`, `tsc --noEmit`, `npm test`",
        ):
            if expected not in generated_stack_standards:
                raise RuntimeError(
                    f"Generated stack-standards skill is missing phase 6 quality command guidance: {expected}"
                )

        generated_review_bridge = (
            full_dest / ".opencode" / "skills" / "review-audit-bridge" / "SKILL.md"
        ).read_text(encoding="utf-8")
        for expected in (
            "run the repo's build command, lint or type-check command, and reference-integrity checks",
            "the verdict must be FAIL",
            "when reviewing or validating a remediation ticket with `finding_source`",
        ):
            if expected not in generated_review_bridge:
                raise RuntimeError(
                    f"Generated review-audit-bridge skill is missing phase 6 quality-loop guidance: {expected}"
                )

        generated_ticket_execution = (
            full_dest / ".opencode" / "skills" / "ticket-execution" / "SKILL.md"
        ).read_text(encoding="utf-8")
        for expected in (
            "Remediation ticket closeout:",
            "when a remediation ticket carries `finding_source`",
            "if the finding-specific rerun still fails, do not close the ticket",
        ):
            if expected not in generated_ticket_execution:
                raise RuntimeError(
                    f"Generated ticket-execution skill is missing phase 6 remediation guidance: {expected}"
                )

        generated_workflow = (
            full_dest / ".opencode" / "lib" / "workflow.ts"
        ).read_text(encoding="utf-8")
        for expected in (
            "finding_source?: string",
            "## Code Quality Status",
            "open_remediation_tickets",
            "known_reference_integrity_issues",
        ):
            if expected not in generated_workflow:
                raise RuntimeError(
                    f"Generated workflow.ts is missing phase 6 quality-loop support: {expected}"
                )

        generated_ticket_create = (
            full_dest / ".opencode" / "tools" / "ticket_create.ts"
        ).read_text(encoding="utf-8")
        if "finding_source" not in generated_ticket_create:
            raise RuntimeError(
                "Generated ticket_create.ts should carry finding_source for remediation tickets"
            )

        generated_handoff_publish = (
            full_dest / ".opencode" / "tools" / "handoff_publish.ts"
        ).read_text(encoding="utf-8")
        if "code_quality_status" not in generated_handoff_publish:
            raise RuntimeError(
                "Generated handoff_publish.ts should expose code quality status counts"
            )

        generated_smoke_tool = (
            full_dest / ".opencode" / "tools" / "smoke_test.ts"
        ).read_text(encoding="utf-8")
        for expected in (
            "classifyCommandKind",
            "failed_command_label",
            "failed_command_kind",
            "build or quality gate command",
        ):
            if expected not in generated_smoke_tool:
                raise RuntimeError(
                    f"Generated smoke_test.ts is missing phase 6 build-failure classification detail: {expected}"
                )

        audit_reporting_script = (
            ROOT / "skills" / "scafforge-audit" / "scripts" / "audit_reporting.py"
        ).read_text(encoding="utf-8")
        for expected in (
            "recommendation_linked_codes",
            "Batch remediate",
            '"assignee": "implementer"',
            '"source_findings": [',
        ):
            if expected not in audit_reporting_script:
                raise RuntimeError(
                    f"audit_reporting.py is missing phase 6 remediation-ticket logic: {expected}"
                )

        remediation_follow_up_script_path = (
            ROOT / "skills" / "ticket-pack-builder" / "scripts" / "apply_remediation_follow_up.py"
        )
        remediation_follow_up_script = remediation_follow_up_script_path.read_text(
            encoding="utf-8"
        )
        for expected in (
            "load_ticket_recommendations",
            '"finding_source": str(recommendation.get("source_finding_code")',
            'run_generated_tool(repo_root, ".opencode/tools/ticket_create.ts", payload)',
        ):
            if expected not in remediation_follow_up_script:
                raise RuntimeError(
                    f"apply_remediation_follow_up.py is missing required phase 6 follow-up logic: {expected}"
                )

        repair_engine_script = (
            ROOT / "skills" / "scafforge-repair" / "scripts" / "apply_repo_process_repair.py"
        ).read_text(encoding="utf-8")
        for expected in (
            "class RepairEscalation",
            "build_managed_surface_diff_summary",
            "backup_target",
            "Backup for {target} is missing or corrupted",
            '"diff_summary": diff_summary',
            "REPAIR_ESCALATION_PATH",
        ):
            if expected not in repair_engine_script:
                raise RuntimeError(
                    f"apply_repo_process_repair.py is missing required phase 7 repair-safety logic: {expected}"
                )

        public_repair_script = (
            ROOT / "skills" / "scafforge-repair" / "scripts" / "run_managed_repair.py"
        ).read_text(encoding="utf-8")
        for expected in (
            "summarize_source_regressions",
            "create_remediation_follow_up_tickets",
            'code.startswith(("EXEC", "REF"))',
            '"remediation_ticket_ids":',
        ):
            if expected not in public_repair_script:
                raise RuntimeError(
                    f"run_managed_repair.py is missing required phase 7 repair-coverage logic: {expected}"
                )

        scaffold_bootstrap_script = (
            ROOT / "skills" / "repo-scaffold-factory" / "scripts" / "bootstrap_repo_scaffold.py"
        ).read_text(encoding="utf-8")
        for expected in (
            "ensure_idempotent_target",
            "validate_replacement_values",
            '"template_commit_result": template_commit_result',
        ):
            if expected not in scaffold_bootstrap_script:
                raise RuntimeError(
                    f"bootstrap_repo_scaffold.py is missing required phase 8 template-safety logic: {expected}"
                )

        generated_scaffold_verifier = (
            ROOT / "skills" / "repo-scaffold-factory" / "scripts" / "verify_generated_scaffold.py"
        ).read_text(encoding="utf-8")
        for expected in (
            "SCAFFOLD-001",
            "SCAFFOLD-002",
            "SCAFFOLD-003",
            "SCAFFOLD-004",
            "SCAFFOLD-005",
            "placeholder_findings",
            "agent_reference_findings",
        ):
            if expected not in generated_scaffold_verifier:
                raise RuntimeError(
                    f"verify_generated_scaffold.py is missing required phase 8 scaffold validation logic: {expected}"
                )

        generated_workflow = (
            ROOT
            / "skills"
            / "repo-scaffold-factory"
            / "assets"
            / "project-template"
            / ".opencode"
            / "lib"
            / "workflow.ts"
        ).read_text(encoding="utf-8")
        for expected in (
            "export async function ensureRequiredFile",
            "tickets/manifest.json not found. Run bootstrap first.",
            ".opencode/state/workflow-state.json not found. Run bootstrap first.",
            "export async function readManifest",
            "export async function writeManifest",
        ):
            if expected not in generated_workflow:
                raise RuntimeError(
                    f"workflow.ts is missing required phase 8 scaffold utility logic: {expected}"
                )

        generated_audit_execution = (
            ROOT
            / "skills"
            / "scafforge-audit"
            / "scripts"
            / "audit_execution_surfaces.py"
        ).read_text(encoding="utf-8")
        for expected in (
            "def audit_node_execution",
            "def audit_godot_execution",
            "def audit_godot_project_version",
            "def audit_reference_integrity",
            "SCAN_EXCLUDED_DIRS",
            "iter_source_files",
            "EXEC-GODOT-002",
            "EXEC-GODOT-005a",
            "EXEC-GODOT-005b",
            "PROJ-VER-001",
            'code="REF-002"',
        ):
            if expected not in generated_audit_execution:
                raise RuntimeError(
                    "Audit execution surfaces should include stack-specific execution checks and reference integrity findings"
                )
        generated_audit_contract = (
            ROOT
            / "skills"
            / "scafforge-audit"
            / "scripts"
            / "audit_contract_surfaces.py"
        ).read_text(encoding="utf-8")
        for expected in ("FINISH001", "FINISH002", "audit_product_finish_contract"):
            if expected not in generated_audit_contract:
                raise RuntimeError(
                    "Audit contract surfaces should include Product Finish Contract checks for consumer-facing repos"
                )
        spec_pack_skill = (ROOT / "skills" / "spec-pack-normalizer" / "SKILL.md").read_text(encoding="utf-8")
        if "Product Finish Contract" not in spec_pack_skill:
            raise RuntimeError(
                "spec-pack-normalizer should require Product Finish Contract handling for consumer-facing repos"
            )
        scaffold_kickoff_skill = (ROOT / "skills" / "scaffold-kickoff" / "SKILL.md").read_text(encoding="utf-8")
        if "finish contract (section 13" not in scaffold_kickoff_skill:
            raise RuntimeError(
                "scaffold-kickoff should treat the finish contract as required intake for consumer-facing repos"
            )
        ticket_pack_builder_skill = (ROOT / "skills" / "ticket-pack-builder" / "SKILL.md").read_text(encoding="utf-8")
        for expected in ("split_kind", "sequential_dependent", "SIGNING-001", "Product Finish Contract"):
            if expected not in ticket_pack_builder_skill:
                raise RuntimeError(
                    f"ticket-pack-builder should include split sequencing and finish-contract backlog guidance: {expected}"
                )
        project_skill_bootstrap_skill = (ROOT / "skills" / "project-skill-bootstrap" / "SKILL.md").read_text(encoding="utf-8")
        if "finish-pipeline skill" not in project_skill_bootstrap_skill:
            raise RuntimeError(
                "project-skill-bootstrap should synthesize finish-pipeline guidance when the brief forbids placeholders"
            )
        repair_skill = (ROOT / "skills" / "scafforge-repair" / "SKILL.md").read_text(encoding="utf-8")
        if "exact command, raw command output, and explicit PASS/FAIL result" not in repair_skill:
            raise RuntimeError(
                "scafforge-repair should require command-evidence remediation review for finding_source follow-up tickets"
            )
        reviewer_prompt_template = (
            ROOT
            / "skills"
            / "repo-scaffold-factory"
            / "assets"
            / "project-template"
            / ".opencode"
            / "agents"
            / "__AGENT_PREFIX__-reviewer-code.md"
        ).read_text(encoding="utf-8")
        if "raw command output" not in reviewer_prompt_template:
            raise RuntimeError(
                "reviewer-code agent template should require remediation command output evidence"
            )
        team_leader_template = (
            ROOT
            / "skills"
            / "repo-scaffold-factory"
            / "assets"
            / "project-template"
            / ".opencode"
            / "agents"
            / "__AGENT_PREFIX__-team-leader.md"
        ).read_text(encoding="utf-8")
        if "must not call `artifact_write` or `artifact_register`" not in team_leader_template:
            raise RuntimeError(
                "team-leader agent template should explicitly forbid coordinator-authored stage artifacts"
            )
        if (
            'do not end your response with a self-addressed "Next Steps" summary while the active ticket is still open'
            not in team_leader_template
        ):
            raise RuntimeError(
                "team-leader agent template should forbid headless self-handoff summaries before the active ticket is actually blocked or closed"
            )
        if (
            "lifecycle status map: `plan_review -> plan_review`, `review -> review`, `qa -> qa`, `smoke-test -> smoke_test`, `closeout -> done`"
            not in team_leader_template
        ):
            raise RuntimeError(
                "team-leader agent template should spell out the exact lifecycle status values, including closeout -> done"
            )
        if (
            "when `ticket_lookup.transition_guidance.next_action_kind` is `write_artifact`, do not attempt `artifact_write` or `artifact_register` yourself"
            not in team_leader_template
        ):
            raise RuntimeError(
                "team-leader agent template should route write_artifact guidance directly through the owning specialist instead of attempting coordinator artifact calls first"
            )
        if (
            "when `ticket_lookup.process_verification.clearable_now` is `true`, treat the recommended `ticket_update(..., pending_process_verification: false)` as required cleanup and execute it before any split-parent handoff or ordinary lifecycle advancement"
            not in team_leader_template
        ):
            raise RuntimeError(
                "team-leader agent template should prioritize clearable pending_process_verification cleanup before split-parent or ordinary lifecycle routing"
            )
        if (
            "a delegated specialist task is not a stop condition; wait for the task result, confirm the expected artifact or failure, then immediately re-run `ticket_lookup` and continue in the same run"
            not in team_leader_template
        ):
            raise RuntimeError(
                "team-leader agent template should keep headless runs alive across specialist delegation boundaries"
            )
        if (
            "do not restart long Goal / Instructions / Discoveries / Accomplished / Next Steps recap blocks after routine progress; if you are not reporting a blocker, keep progress narration to one or two short lines"
            not in team_leader_template
        ):
            raise RuntimeError(
                "team-leader agent template should suppress repeated recap blocks during routine progress"
            )
        generated_audit_reporting = (
            ROOT
            / "skills"
            / "scafforge-audit"
            / "scripts"
            / "audit_reporting.py"
        ).read_text(encoding="utf-8")
        for expected in (
            "## Code Quality Findings",
            'finding.code.startswith(("BOOT", "ENV", "EXEC", "REF", "SESSION"))',
            "package_first_count",
        ):
            if expected not in generated_audit_reporting:
                raise RuntimeError(
                    "Audit reporting should route code findings to subject-repo follow-up and render code quality sections"
                )
        if (
            "multiple shell-style command strings executed in order"
            not in generated_smoke_test
        ):
            raise RuntimeError(
                "Generated smoke_test.ts should document multi-command shell-style command_override input"
            )
        if (
            "command_override cannot mix tokenized argv entries with multiple shell-style command strings."
            not in generated_smoke_test
        ):
            raise RuntimeError(
                "Generated smoke_test.ts should reject malformed mixed command_override forms"
            )
        if (
            "defaultArtifactPath" not in generated_smoke_test
            or "normalizeRepoPath" not in generated_smoke_test
        ):
            raise RuntimeError(
                "Generated smoke_test.ts should persist smoke artifacts through canonical artifact-path helpers"
            )
        for expected in (
            "host_surface_classification",
            "failure_classification",
            "blocked_by_permissions",
            "permission_restriction",
        ):
            if expected not in generated_smoke_test:
                raise RuntimeError(
                    "Generated smoke_test.ts should classify missing-tool and permission-restriction host failures explicitly"
                )
        generated_stage_gate = (
            full_dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
        ).read_text(encoding="utf-8")
        if (
            'const RESERVED_ARTIFACT_STAGES = new Set(["smoke-test"])'
            not in generated_stage_gate
        ):
            raise RuntimeError(
                "Generated stage-gate-enforcer.ts should reserve smoke-test artifacts to their owning tool"
            )
        if (
            "Generic artifact_write is not allowed for that stage."
            not in generated_stage_gate
        ):
            raise RuntimeError(
                "Generated stage-gate-enforcer.ts should block generic artifact_write for smoke-test"
            )
        if (
            'type: "BLOCKER"' not in generated_stage_gate
            or "missing_write_lease" not in generated_stage_gate
        ):
            raise RuntimeError(
                "Generated stage-gate-enforcer.ts should emit structured blockers for missing lease conditions"
            )
        if (
            "await ensureTargetTicketWriteLease(targetTicket.id)"
            not in generated_stage_gate
        ):
            raise RuntimeError(
                "Generated stage-gate-enforcer.ts should require a write lease for open ticket_reconcile targets"
            )
        generated_workflow = (
            full_dest / ".opencode" / "lib" / "workflow.ts"
        ).read_text(encoding="utf-8")
        if (full_dest / ".opencode" / "tools" / "_workflow.ts").exists():
            raise RuntimeError(
                "Generated helper workflow library should stay private under .opencode/lib instead of leaking a callable _workflow.ts tool"
            )
        if "tool({" in generated_workflow:
            raise RuntimeError(
                "Generated workflow library should remain helper-only and must not expose a model-callable tool surface"
            )
        if "refreshRestartSurfaces" not in generated_workflow:
            raise RuntimeError(
                "Generated workflow.ts should refresh derived restart surfaces after workflow mutations"
            )
        if "latestHandoffPath" not in generated_workflow:
            raise RuntimeError(
                "Generated workflow.ts should own the latest-handoff restart surface"
            )
        if "export function blockedDependentTickets" not in generated_workflow:
            raise RuntimeError(
                "Generated workflow.ts should expose blocked dependent routing as a reusable canonical helper"
            )
        if "export function dependentContinuationAction" not in generated_workflow:
            raise RuntimeError(
                "Generated workflow.ts should expose one canonical dependent-continuation action helper for restart and lookup surfaces"
            )
        if (
            "export function ticketNeedsHistoricalReconciliation"
            not in generated_workflow
        ):
            raise RuntimeError(
                "Generated workflow.ts should expose explicit historical-reconciliation state for restart and lookup surfaces"
            )
        if "export function ticketNeedsTrustRestoration" not in generated_workflow:
            raise RuntimeError(
                "Generated workflow.ts should expose explicit closed-ticket trust-restoration state for restart and lookup surfaces"
            )
        if (
            "Historical done-ticket reverification stays secondary until the active open ticket is resolved."
            not in generated_workflow
        ):
            raise RuntimeError(
                "Generated workflow.ts should keep the active open ticket primary when process verification is pending"
            )
        if (
            "Cannot publish dependency-readiness claims" not in generated_workflow
            or "Cannot publish causal claims" not in generated_workflow
        ):
            raise RuntimeError(
                "Generated workflow.ts should truthfully gate handoff claims against canonical state and smoke evidence"
            )
        generated_ticket_lookup = (
            full_dest / ".opencode" / "tools" / "ticket_lookup.ts"
        ).read_text(encoding="utf-8")
        if "transition_guidance" not in generated_ticket_lookup:
            raise RuntimeError(
                "Generated ticket_lookup.ts should expose transition_guidance"
            )
        if (
            "Do not fabricate a PASS artifact through generic artifact tools."
            not in generated_ticket_lookup
        ):
            raise RuntimeError(
                "Generated ticket_lookup.ts should warn against generic PASS artifact fabrication"
            )
        if (
            "Run environment_bootstrap first, then rerun ticket_lookup before attempting lifecycle transitions."
            not in generated_ticket_lookup
        ):
            raise RuntimeError(
                "Generated ticket_lookup.ts should short-circuit lifecycle guidance to environment_bootstrap when bootstrap is not ready"
            )
        if (
            "Keep ${ticket.id} open as a split parent and foreground child ticket ${foregroundChild.id} instead of advancing the parent lane directly."
            not in generated_ticket_lookup
        ):
            raise RuntimeError(
                "Generated ticket_lookup.ts should foreground split children without marking the parent blocked"
            )
        if "dependentContinuationAction" not in generated_ticket_lookup:
            raise RuntimeError(
                "Generated ticket_lookup.ts should route closed completed tickets through the shared dependent-continuation helper instead of presenting them as terminal"
            )
        if (
            "ticketNeedsHistoricalReconciliation" not in generated_ticket_lookup
            or "ticket_reconcile" not in generated_ticket_lookup
        ):
            raise RuntimeError(
                "Generated ticket_lookup.ts should surface ticket_reconcile when a closed historical ticket still needs lineage repair"
            )
        if "ticketNeedsTrustRestoration" not in generated_ticket_lookup:
            raise RuntimeError(
                "Generated ticket_lookup.ts should detect explicit closed-ticket trust-restoration state, not only global pending process verification"
            )
        if (
            'next_action_tool: "smoke_test",\n          delegate_to_agent: null,\n          required_owner: "team-leader",'
            not in generated_ticket_lookup
        ):
            raise RuntimeError(
                "Generated ticket_lookup.ts should keep smoke_test team-leader-owned instead of delegating it to tester-qa"
            )
        generated_ticket_create = (
            full_dest / ".opencode" / "tools" / "ticket_create.ts"
        ).read_text(encoding="utf-8")
        if 'status = "blocked"' in generated_ticket_create:
            raise RuntimeError(
                "Generated ticket_create.ts should not mark split-scope parents blocked"
            )
        if (
            "Keep the parent open and non-foreground until the child work lands."
            not in generated_ticket_create
        ):
            raise RuntimeError(
                "Generated ticket_create.ts should leave split-scope parents open and linked to their children"
            )
        generated_ticket_reverify = (
            full_dest / ".opencode" / "tools" / "ticket_reverify.ts"
        ).read_text(encoding="utf-8")
        if "ticketEligibleForTrustRestoration(sourceTicket)" not in generated_ticket_reverify:
            raise RuntimeError(
                "Generated ticket_reverify.ts should gate trust restoration through the shared historical-ticket eligibility helper"
            )
        if (
            "ticket_reverify requires evidence_artifact_path or verification_content."
            not in generated_ticket_reverify
        ):
            raise RuntimeError(
                "Generated ticket_reverify.ts should require concrete reverification evidence"
            )
        if (
            'sourceTicket.verification_state = "reverified"'
            not in generated_ticket_reverify
        ):
            raise RuntimeError(
                "Generated ticket_reverify.ts should restore the source ticket verification state to reverified"
            )
        if (
            "getTicketWorkflowState(workflow, sourceTicket.id).needs_reverification = false"
            not in generated_ticket_reverify
        ):
            raise RuntimeError(
                "Generated ticket_reverify.ts should clear the explicit needs_reverification flag after trust restoration"
            )
        if (
            'kind: "backlog-verification"' not in generated_ticket_reverify
            or 'kind: "reverification"' not in generated_ticket_reverify
        ):
            raise RuntimeError(
                "Generated ticket_reverify.ts should register both inline backlog-verification evidence and the final reverification artifact"
            )
        if "markTicketDone(sourceTicket, workflow)" not in generated_ticket_reverify:
            raise RuntimeError(
                "Generated ticket_reverify.ts should restore reopened historical tickets to done before persisting reverification"
            )
        generated_ticket_reconcile = (
            full_dest / ".opencode" / "tools" / "ticket_reconcile.ts"
        ).read_text(encoding="utf-8")
        if "currentRegistryArtifact" not in generated_ticket_reconcile:
            raise RuntimeError(
                "Generated ticket_reconcile.ts should allow current registered evidence to justify historical reconciliation"
            )
        if (
            "targetTicket.depends_on = targetTicket.depends_on.filter"
            not in generated_ticket_reconcile
        ):
            raise RuntimeError(
                "Generated ticket_reconcile.ts should remove contradictory dependencies when reconciliation repairs lineage"
            )
        if (
            'targetTicket.verification_state = "reverified"'
            not in generated_ticket_reconcile
        ):
            raise RuntimeError(
                "Generated ticket_reconcile.ts should leave successfully superseded historical targets non-blocking for handoff publication"
            )
        if (
            'targetTicket.resolution_state = "superseded"'
            not in generated_ticket_reconcile
        ):
            raise RuntimeError(
                "Generated ticket_reconcile.ts should explicitly mark superseded historical targets closed when requested"
            )
        if (
            "syncWorkflowSelection(workflow, manifest)"
            not in generated_ticket_reconcile
        ):
            raise RuntimeError(
                "Generated ticket_reconcile.ts should resync active workflow selection after lineage changes"
            )
        if "supersededTarget,\n" in generated_ticket_reconcile:
            raise RuntimeError(
                "Generated ticket_reconcile.ts should not contain the legacy supersededTarget runtime typo"
            )
        generated_team_leader = next(
            (full_dest / ".opencode" / "agents").glob("*team-leader*.md")
        ).read_text(encoding="utf-8")
        if (
            "do not create planning, implementation, review, QA, or smoke-test artifacts yourself"
            not in generated_team_leader
        ):
            raise RuntimeError(
                "Generated team leader prompt should forbid coordinator-authored specialist artifacts"
            )
        if (
            "If `ticket_lookup.bootstrap.status` is not `ready`, treat `environment_bootstrap` as the next required tool call"
            not in generated_team_leader
        ):
            raise RuntimeError(
                "Generated team leader prompt should make bootstrap-first routing explicit"
            )
        if (
            "same command trace but it still contradicts the repo's declared dependency layout"
            not in generated_team_leader
        ):
            raise RuntimeError(
                "Generated team leader prompt should escalate repeated bootstrap command/layout contradictions as managed defects"
            )
        if (
            "grant a write lease with `ticket_claim` before any specialist writes planning, implementation, review, QA, or handoff artifact bodies or makes code changes"
            not in generated_team_leader
        ):
            raise RuntimeError(
                "Generated team leader prompt should own the lease claim path"
            )
        if (
            "lifecycle status map: `plan_review -> plan_review`, `review -> review`, `qa -> qa`, `smoke-test -> smoke_test`, `closeout -> done`"
            not in generated_team_leader
        ):
            raise RuntimeError(
                "Generated team leader prompt should spell out the exact lifecycle status values, including closeout -> done"
            )
        if (
            'do not end your response with a self-addressed "Next Steps" summary while the active ticket is still open'
            not in generated_team_leader
        ):
            raise RuntimeError(
                "Generated team leader prompt should keep headless runs executing instead of stopping at self-directed next-step summaries"
            )
        if (
            "keep draining ready child tickets in the same run until no writable child can advance legally or a listed stop condition fires"
            not in generated_team_leader
        ):
            raise RuntimeError(
                "Generated team leader prompt should keep remediation child batches draining within the same headless run"
            )
        if (
            "when `ticket_lookup.transition_guidance.next_action_kind` is `write_artifact`, do not attempt `artifact_write` or `artifact_register` yourself"
            not in generated_team_leader
        ):
            raise RuntimeError(
                "Generated team leader prompt should delegate write_artifact actions directly to the owning specialist"
            )
        if (
            "a delegated specialist task is not a stop condition; wait for the task result, confirm the expected artifact or failure, then immediately re-run `ticket_lookup` and continue in the same run"
            not in generated_team_leader
        ):
            raise RuntimeError(
                "Generated team leader prompt should keep running after specialist delegation completes"
            )
        if (
            "do not restart long Goal / Instructions / Discoveries / Accomplished / Next Steps recap blocks after routine progress; if you are not reporting a blocker, keep progress narration to one or two short lines"
            not in generated_team_leader
        ):
            raise RuntimeError(
                "Generated team leader prompt should suppress repeated recap blocks during normal progress"
            )
        if (
            "ticket_create: allow" not in generated_team_leader
            or "ticket_reconcile: allow" not in generated_team_leader
        ):
            raise RuntimeError(
                "Generated team leader prompt should be allowed to invoke ticket_create and ticket_reconcile"
            )
        generated_ticket_execution = (
            full_dest / ".opencode" / "skills" / "ticket-execution" / "SKILL.md"
        ).read_text(encoding="utf-8")
        if "slash commands are human entrypoints" not in generated_ticket_execution:
            raise RuntimeError(
                "Generated ticket-execution skill should mark slash commands as human entrypoints only"
            )
        if (
            "if `ticket_lookup.bootstrap.status` is not `ready`, stop normal lifecycle routing, run `environment_bootstrap`, then rerun `ticket_lookup` before any `ticket_update`"
            not in generated_ticket_execution
        ):
            raise RuntimeError(
                "Generated ticket-execution skill should treat bootstrap readiness as a pre-lifecycle gate"
            )
        if (
            "same command trace but it still omits the dependency-group or extra flags the repo layout requires"
            not in generated_ticket_execution
        ):
            raise RuntimeError(
                "Generated ticket-execution skill should stop retrying when bootstrap artifacts prove a managed command/layout mismatch"
            )
        if (
            "the team leader claims and releases write leases"
            not in generated_ticket_execution
        ):
            raise RuntimeError(
                "Generated ticket-execution skill should encode the coordinator-owned lease model"
            )
        generated_ticket_creator = next(
            (full_dest / ".opencode" / "agents").glob("*ticket-creator*.md")
        ).read_text(encoding="utf-8")
        if "ticket_reconcile: allow" not in generated_ticket_creator:
            raise RuntimeError(
                "Generated ticket creator prompt should be allowed to invoke ticket_reconcile"
            )
        generated_resume = (
            full_dest / ".opencode" / "commands" / "resume.md"
        ).read_text(encoding="utf-8")
        if (
            "Resume from `tickets/manifest.json` and `.opencode/state/workflow-state.json` first."
            not in generated_resume
        ):
            raise RuntimeError(
                "Generated /resume command should treat manifest and workflow-state as canonical"
            )
        if ".opencode/state/latest-handoff.md" not in generated_resume:
            raise RuntimeError(
                "Generated /resume command should mention latest-handoff as a derived restart surface"
            )
        if (
            "same command trace but it still contradicts the repo's declared dependency layout"
            not in generated_resume
        ):
            raise RuntimeError(
                "Generated /resume command should stop bootstrap retries when artifacts prove a managed command/layout mismatch"
            )
        if "handoff_allowed" in generated_resume:
            raise RuntimeError(
                "Generated /resume command should not route from legacy handoff_allowed fields"
            )
        generated_implementer = next(
            (full_dest / ".opencode" / "agents").glob("*implementer*.md")
        ).read_text(encoding="utf-8")
        if (
            "ticket_claim: allow" in generated_implementer
            or "ticket_release: allow" in generated_implementer
        ):
            raise RuntimeError(
                "Generated implementer should not own ticket claim or release"
            )
        latest_handoff = (
            full_dest / ".opencode" / "state" / "latest-handoff.md"
        ).read_text(encoding="utf-8")
        if "bootstrap recovery required" not in latest_handoff:
            raise RuntimeError(
                "Generated latest-handoff should be seeded from the managed restart narrative"
            )
        if (
            "- split_child_tickets: none" not in latest_handoff
            or "repair_follow_on_handoff_allowed" in latest_handoff
        ):
            raise RuntimeError(
                "Generated latest-handoff should expose split-child status and omit legacy repair handoff gating"
            )
        start_here = (full_dest / "START-HERE.md").read_text(encoding="utf-8")
        if (
            "- split_child_tickets: none" not in start_here
            or "repair_follow_on_handoff_allowed" in start_here
        ):
            raise RuntimeError(
                "Generated START-HERE should expose split-child status and omit legacy repair handoff gating"
            )
        context_snapshot = (
            full_dest / ".opencode" / "state" / "context-snapshot.md"
        ).read_text(encoding="utf-8")
        if (
            "- Open split children: none" not in context_snapshot
            or "- handoff_allowed:" in context_snapshot
        ):
            raise RuntimeError(
                "Generated context snapshot should expose split children and omit public handoff_allowed state"
            )
        pivot_dest = workspace / "pivot"
        shutil.copytree(full_dest, pivot_dest)
        make_stack_skill_non_placeholder(pivot_dest)
        seed_ready_bootstrap(pivot_dest)
        run_generated_tool(
            pivot_dest,
            ".opencode/tools/handoff_publish.ts",
            {},
        )
        pivot_payload = run_json(
            [
                sys.executable,
                str(PIVOT),
                str(pivot_dest),
                "--pivot-class",
                "architecture-change",
                "--requested-change",
                "Move from single-service layout to modular domain services with explicit workflow contract updates.",
                "--accepted-decision",
                "Adopt modular service boundaries and regenerate workflow prompts around the new topology.",
                "--unresolved-follow-up",
                "Reconcile historical tickets that still assume the old monolith execution path.",
                "--reconcile-ticket",
                "SETUP-001",
                "--format",
                "json",
            ],
            ROOT,
        )
        if pivot_payload["verification_status"]["verification_kind"] != "post_pivot":
            raise RuntimeError(
                "Pivot orchestration should record a post_pivot verification result"
            )
        if not pivot_payload["verification_status"]["verification_passed"]:
            raise RuntimeError(
                "Pivot orchestration should pass verification on a clean generated repo"
            )
        if (
            pivot_payload["stale_surface_map"]["canonical_brief_and_truth_docs"][
                "status"
            ]
            != "replace"
        ):
            raise RuntimeError(
                "Pivot orchestration should always replace canonical brief truth surfaces"
            )
        if (
            pivot_payload["stale_surface_map"]["managed_workflow_tools_and_prompts"][
                "status"
            ]
            != "replace"
        ):
            raise RuntimeError(
                "Architecture pivots should route managed workflow drift through replacement state"
            )
        pivot_stages = [item["stage"] for item in pivot_payload["downstream_refresh"]]
        for expected in (
            "project-skill-bootstrap",
            "opencode-team-bootstrap",
            "agent-prompt-engineering",
            "ticket-pack-builder",
            "scafforge-repair",
        ):
            if expected not in pivot_stages:
                raise RuntimeError(
                    f"Pivot orchestration should route {expected} for an architecture-change pivot"
                )
        pivot_brief = (pivot_dest / "docs" / "spec" / "CANONICAL-BRIEF.md").read_text(
            encoding="utf-8"
        )
        if (
            "## Pivot History" not in pivot_brief
            or "architecture-change" not in pivot_brief
        ):
            raise RuntimeError(
                "Pivot orchestration should append a Pivot History section to the canonical brief"
            )
        pivot_state_path = pivot_dest / ".opencode" / "meta" / "pivot-state.json"
        if not pivot_state_path.exists():
            raise RuntimeError(
                "Pivot orchestration should persist .opencode/meta/pivot-state.json"
            )
        pivot_state = json.loads(pivot_state_path.read_text(encoding="utf-8"))
        if pivot_state["pivot_state_path"] != ".opencode/meta/pivot-state.json":
            raise RuntimeError(
                "Pivot orchestration should record the canonical pivot state path"
            )
        if pivot_state["restart_surface_inputs"]["pivot_in_progress"] is not True:
            raise RuntimeError(
                "Pivot orchestration should mark pivot_in_progress while routed downstream work remains"
            )
        expected_changed_surfaces = {
            "canonical_brief_and_truth_docs",
            "repo_local_skills",
            "agent_team_and_prompts",
            "managed_workflow_tools_and_prompts",
            "ticket_graph_and_lineage",
            "restart_surfaces",
        }
        if (
            set(pivot_state["restart_surface_inputs"]["pivot_changed_surfaces"])
            != expected_changed_surfaces
        ):
            raise RuntimeError(
                "Pivot orchestration should expose truthful changed surfaces for restart publication"
            )
        pivot_audit_dest = workspace / "pivot-audit-drift"
        shutil.copytree(pivot_dest, pivot_audit_dest)
        pivot_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(pivot_audit_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        pivot_audit_codes = {
            finding["code"] for finding in pivot_audit.get("findings", [])
        }
        if "WFLOW010" in pivot_audit_codes:
            raise RuntimeError(
                "Pivot restart surfaces that still match the canonical pivot state should not emit WFLOW010"
            )
        pivot_audit_state_path = (
            pivot_audit_dest / ".opencode" / "meta" / "pivot-state.json"
        )
        pivot_audit_state = json.loads(
            pivot_audit_state_path.read_text(encoding="utf-8")
        )
        pivot_audit_state["restart_surface_inputs"]["pivot_class"] = "drifted"
        pivot_audit_state_path.write_text(
            json.dumps(pivot_audit_state, indent=2) + "\n", encoding="utf-8"
        )
        pivot_audit_drift = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(pivot_audit_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        pivot_audit_drift_codes = {
            finding["code"] for finding in pivot_audit_drift.get("findings", [])
        }
        if "WFLOW010" not in pivot_audit_drift_codes:
            raise RuntimeError(
                "Pivot restart surface drift should be detected when pivot-state inputs no longer match the rendered surfaces"
            )
        pivot_latest_handoff_drift_dest = workspace / "pivot-latest-handoff-drift"
        shutil.copytree(pivot_dest, pivot_latest_handoff_drift_dest)
        pivot_latest_handoff_path = (
            pivot_latest_handoff_drift_dest
            / ".opencode"
            / "state"
            / "latest-handoff.md"
        )
        pivot_latest_handoff_text = pivot_latest_handoff_path.read_text(
            encoding="utf-8"
        )
        if "- pivot_class: architecture-change" not in pivot_latest_handoff_text:
            raise RuntimeError(
                "Pivot smoke fixture should expose canonical pivot_class in latest-handoff before drift injection"
            )
        pivot_latest_handoff_path.write_text(
            pivot_latest_handoff_text.replace(
                "- pivot_class: architecture-change",
                "- pivot_class: drifted",
                1,
            ),
            encoding="utf-8",
        )
        pivot_latest_handoff_drift = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(pivot_latest_handoff_drift_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        pivot_latest_handoff_drift_codes = {
            finding["code"]
            for finding in pivot_latest_handoff_drift.get("findings", [])
        }
        if "WFLOW010" not in pivot_latest_handoff_drift_codes:
            raise RuntimeError(
                "Pivot drift isolated to latest-handoff should still emit WFLOW010"
            )
        if set(pivot_state["downstream_refresh_state"]["pending_stages"]) != set(
            pivot_stages
        ):
            raise RuntimeError(
                "Pivot orchestration should initialize downstream refresh state with all routed stages pending"
            )
        lineage_actions = pivot_state["ticket_lineage_plan"]["actions"]
        if not any(
            action["action"] == "reconcile"
            and action["target_ticket_id"] == "SETUP-001"
            for action in lineage_actions
        ):
            raise RuntimeError(
                "Pivot orchestration should record explicit reconcile actions in the ticket lineage plan"
            )
        if not any(
            action["action"] == "create_follow_up"
            and "Reconcile historical tickets" in action["summary"]
            for action in lineage_actions
        ):
            raise RuntimeError(
                "Pivot orchestration should convert unresolved follow-up into explicit follow-up ticket lineage actions"
            )
        if (
            "reconcile:SETUP-001"
            not in pivot_state["restart_surface_inputs"][
                "pending_ticket_lineage_actions"
            ]
        ):
            raise RuntimeError(
                "Pivot restart inputs should expose pending explicit ticket lineage actions"
            )
        pivot_start_here = (pivot_dest / "START-HERE.md").read_text(encoding="utf-8")
        pivot_latest_handoff = (
            pivot_dest / ".opencode" / "state" / "latest-handoff.md"
        ).read_text(encoding="utf-8")
        pivot_context_snapshot = (
            pivot_dest / ".opencode" / "state" / "context-snapshot.md"
        ).read_text(encoding="utf-8")
        if (
            "- pivot_in_progress: true" not in pivot_start_here
            or "- pivot_class: architecture-change" not in pivot_start_here
        ):
            raise RuntimeError(
                "Pivot planning should republish START-HERE immediately with truthful pivot state"
            )
        if (
            "- pivot_pending_ticket_lineage_actions: reconcile:SETUP-001, create_follow_up:Reconcile historical tickets that still assume the old monolith execution path."
            not in pivot_start_here
        ):
            raise RuntimeError(
                "Pivot planning should republish START-HERE with pending pivot ticket lineage actions"
            )
        if "- pivot_in_progress: true" not in pivot_latest_handoff:
            raise RuntimeError(
                "Pivot planning should republish latest-handoff immediately with truthful pivot state"
            )
        if (
            "- pending_ticket_lineage_actions: reconcile:SETUP-001, create_follow_up:Reconcile historical tickets that still assume the old monolith execution path."
            not in pivot_context_snapshot
        ):
            raise RuntimeError(
                "Pivot planning should republish context snapshot immediately with pending pivot ticket lineage actions"
            )
        restart_surface_publication = pivot_state.get("restart_surface_publication", {})
        if restart_surface_publication.get("status") != "published":
            raise RuntimeError(
                "Pivot planning should record restart-surface publication state"
            )
        regenerate_pivot_payload = run_json(
            [
                sys.executable,
                str(REGENERATE),
                str(pivot_dest),
                "--reason",
                "Repair-side restart regeneration should preserve pivot blockers.",
                "--source",
                "scafforge-repair",
                "--verification-passed",
            ],
            ROOT,
        )
        if (
            regenerate_pivot_payload["handoff_status"] != "pivot follow-up required"
            or regenerate_pivot_payload["pivot_in_progress"] is not True
        ):
            raise RuntimeError(
                "Repair-side restart regeneration should preserve pivot blockers while downstream pivot work remains pending"
            )
        regenerated_pivot_start_here = (pivot_dest / "START-HERE.md").read_text(
            encoding="utf-8"
        )
        regenerated_pivot_latest_handoff = (
            pivot_dest / ".opencode" / "state" / "latest-handoff.md"
        ).read_text(encoding="utf-8")
        regenerated_pivot_context_snapshot = (
            pivot_dest / ".opencode" / "state" / "context-snapshot.md"
        ).read_text(encoding="utf-8")
        if (
            "- handoff_status: pivot follow-up required"
            not in regenerated_pivot_start_here
            or "- pivot_in_progress: true" not in regenerated_pivot_start_here
        ):
            raise RuntimeError(
                "Repair-side restart regeneration should not erase pivot state from START-HERE while pivot follow-on remains pending"
            )
        if "- pivot_in_progress: true" not in regenerated_pivot_latest_handoff:
            raise RuntimeError(
                "Repair-side restart regeneration should preserve pivot state in latest-handoff while pivot follow-on remains pending"
            )
        pivot_evidence = (
            pivot_dest
            / ".opencode"
            / "state"
            / "artifacts"
            / "history"
            / "pivot-stage-completion.md"
        )
        pivot_evidence.parent.mkdir(parents=True, exist_ok=True)
        pivot_evidence.write_text("# Pivot stage completion\n", encoding="utf-8")
        record_payload = run_json(
            [
                sys.executable,
                str(PIVOT_RECORD),
                str(pivot_dest),
                "--stage",
                "scafforge-repair",
                "--completed-by",
                "scafforge-pivot-smoke",
                "--summary",
                "Managed workflow refresh completed for the pivot smoke fixture.",
                "--evidence",
                ".opencode/state/artifacts/history/pivot-stage-completion.md",
            ],
            ROOT,
        )
        if "publication" in record_payload:
            raise RuntimeError(
                "Pivot stage recording should not publish restart surfaces directly"
            )
        if "scafforge-repair" not in record_payload["completed_stage_names"]:
            raise RuntimeError(
                "Pivot stage recording should mark the completed downstream stage"
            )
        if "scafforge-repair" in record_payload["pending_stage_names"]:
            raise RuntimeError(
                "Pivot stage recording should remove the completed stage from pending downstream work"
            )
        refreshed_pivot_state = json.loads(pivot_state_path.read_text(encoding="utf-8"))
        repair_stage_record = refreshed_pivot_state["downstream_refresh_state"][
            "stage_records"
        ]["scafforge-repair"]
        if (
            repair_stage_record["status"] != "completed"
            or repair_stage_record["completion_mode"] != "recorded_execution"
        ):
            raise RuntimeError(
                "Pivot stage recording should persist recorded execution for completed stages"
            )
        if repair_stage_record["completed_by"] != "scafforge-pivot-smoke":
            raise RuntimeError(
                "Pivot stage recording should persist completed_by provenance"
            )
        pivot_start_here = (pivot_dest / "START-HERE.md").read_text(encoding="utf-8")
        pivot_latest_handoff = (
            pivot_dest / ".opencode" / "state" / "latest-handoff.md"
        ).read_text(encoding="utf-8")
        pivot_context_snapshot = (
            pivot_dest / ".opencode" / "state" / "context-snapshot.md"
        ).read_text(encoding="utf-8")
        if pivot_start_here != regenerated_pivot_start_here:
            raise RuntimeError(
                "Pivot stage recording should not republish START-HERE on its own"
            )
        if pivot_latest_handoff != regenerated_pivot_latest_handoff:
            raise RuntimeError(
                "Pivot stage recording should not republish latest-handoff on its own"
            )
        if pivot_context_snapshot != regenerated_pivot_context_snapshot:
            raise RuntimeError(
                "Pivot stage recording should not republish context snapshot on its own"
            )
        pivot_provenance = json.loads(
            (pivot_dest / ".opencode" / "meta" / "bootstrap-provenance.json").read_text(
                encoding="utf-8"
            )
        )
        pivot_history = pivot_provenance.get("pivot_history")
        if (
            not isinstance(pivot_history, list)
            or not pivot_history
            or pivot_history[-1]["pivot_class"] != "architecture-change"
        ):
            raise RuntimeError(
                "Pivot orchestration should append pivot history to bootstrap provenance"
            )

        pivot_relative_log_dest = workspace / "pivot-relative-log"
        shutil.copytree(full_dest, pivot_relative_log_dest)
        make_stack_skill_non_placeholder(pivot_relative_log_dest)
        seed_ready_bootstrap(pivot_relative_log_dest)
        run_generated_tool(
            pivot_relative_log_dest,
            ".opencode/tools/handoff_publish.ts",
            {},
        )
        relative_pivot_log = seed_operator_trap_log(pivot_relative_log_dest)
        relative_pivot_process = subprocess.run(
            [
                sys.executable,
                str(PIVOT),
                str(pivot_relative_log_dest),
                "--pivot-class",
                "workflow-change",
                "--requested-change",
                "Exercise repo-root supporting-log resolution during pivot verification.",
                "--supporting-log",
                relative_pivot_log.name,
                "--format",
                "json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if relative_pivot_process.returncode != 2:
            raise RuntimeError(
                "Pivot verification with a repo-relative supporting log should fail with transcript-backed findings, not path-resolution errors.\n"
                f"STDOUT:\n{relative_pivot_process.stdout}\nSTDERR:\n{relative_pivot_process.stderr}"
            )
        relative_pivot_payload = json.loads(relative_pivot_process.stdout)
        if "SESSION006" not in set(
            relative_pivot_payload["verification_status"]["codes"]
        ):
            raise RuntimeError(
                "Pivot verification should consume repo-relative supporting logs from the pivoted repo root"
            )
        if relative_pivot_payload["verification_status"]["supporting_logs"] != [
            str(relative_pivot_log.resolve())
        ]:
            raise RuntimeError(
                "Pivot verification should record repo-relative supporting logs as paths resolved from the pivoted repo root"
            )

        pivot_lineage_dest = workspace / "pivot-lineage-execution"
        shutil.copytree(full_dest, pivot_lineage_dest)
        make_stack_skill_non_placeholder(pivot_lineage_dest)
        seed_closed_ticket_needing_reconciliation(pivot_lineage_dest)
        lineage_manifest_path = pivot_lineage_dest / "tickets" / "manifest.json"
        lineage_workflow_path = (
            pivot_lineage_dest / ".opencode" / "state" / "workflow-state.json"
        )
        lineage_registry_path = (
            pivot_lineage_dest / ".opencode" / "state" / "artifacts" / "registry.json"
        )
        lineage_manifest = json.loads(lineage_manifest_path.read_text(encoding="utf-8"))
        lineage_workflow = json.loads(lineage_workflow_path.read_text(encoding="utf-8"))
        lineage_registry = json.loads(lineage_registry_path.read_text(encoding="utf-8"))
        lineage_manifest["tickets"].append(
            {
                "id": "EXEC-RECON-SRC",
                "title": "Synthetic replacement source ticket",
                "wave": 2,
                "lane": "implementation",
                "parallel_safe": True,
                "overlap_risk": "low",
                "stage": "implementation",
                "status": "in_progress",
                "depends_on": [],
                "summary": "Replacement source ticket for pivot lineage execution smoke coverage.",
                "acceptance": ["Replacement source remains active."],
                "decision_blockers": [],
                "artifacts": [],
                "resolution_state": "open",
                "verification_state": "trusted",
                "follow_up_ticket_ids": [],
            }
        )
        lineage_manifest["tickets"].append(
            {
                "id": "EXEC-RECON-TGT",
                "title": "Synthetic stale follow-up ticket",
                "wave": 3,
                "lane": "implementation",
                "parallel_safe": True,
                "overlap_risk": "low",
                "stage": "planning",
                "status": "ready",
                "depends_on": ["SETUP-001"],
                "summary": "Follow-up ticket with stale lineage for pivot execution smoke coverage.",
                "acceptance": ["Reconciliation succeeds."],
                "decision_blockers": [],
                "artifacts": [],
                "resolution_state": "open",
                "verification_state": "suspect",
                "source_ticket_id": "SETUP-001",
                "source_mode": "post_completion_issue",
                "follow_up_ticket_ids": [],
            }
        )
        lineage_manifest["tickets"].append(
            {
                "id": "EXEC-REOPEN",
                "title": "Synthetic completed ticket to reopen",
                "wave": 4,
                "lane": "implementation",
                "parallel_safe": True,
                "overlap_risk": "low",
                "stage": "closeout",
                "status": "done",
                "depends_on": [],
                "summary": "Completed ticket that the pivot should reopen through the generated tool.",
                "acceptance": ["Can be reopened through pivot lineage execution."],
                "decision_blockers": [],
                "artifacts": [],
                "resolution_state": "done",
                "verification_state": "trusted",
                "follow_up_ticket_ids": [],
            }
        )
        setup_ticket = next(
            ticket
            for ticket in lineage_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        setup_ticket["follow_up_ticket_ids"] = ["EXEC-RECON-TGT"]
        reconcile_evidence_rel = (
            ".opencode/state/reviews/setup-001-review-backlog-verification.md"
        )
        reconcile_evidence_path = pivot_lineage_dest / reconcile_evidence_rel
        reconcile_evidence_path.parent.mkdir(parents=True, exist_ok=True)
        reconcile_evidence_path.write_text(
            "# Historical Evidence\n\nCurrent evidence is registered.\n",
            encoding="utf-8",
        )
        reconcile_evidence_artifact = {
            "kind": "backlog-verification",
            "path": reconcile_evidence_rel,
            "stage": "review",
            "summary": "Synthetic reconciliation evidence for pivot execution.",
            "created_at": "2026-03-30T00:00:00Z",
            "trust_state": "current",
        }
        setup_ticket.setdefault("artifacts", []).append(reconcile_evidence_artifact)
        lineage_registry.setdefault("artifacts", []).append(
            {"ticket_id": "SETUP-001", **reconcile_evidence_artifact}
        )
        reopen_ticket = next(
            ticket
            for ticket in lineage_manifest["tickets"]
            if ticket["id"] == "EXEC-REOPEN"
        )
        reopen_evidence_rel = ".opencode/state/reviews/exec-reopen-review.md"
        reopen_evidence_path = pivot_lineage_dest / reopen_evidence_rel
        reopen_evidence_path.parent.mkdir(parents=True, exist_ok=True)
        reopen_evidence_path.write_text(
            "# Reopen Evidence\n\nPivot invalidated the prior completion boundary.\n",
            encoding="utf-8",
        )
        reopen_ticket.setdefault("artifacts", []).append(
            {
                "kind": "review-note",
                "path": reopen_evidence_rel,
                "stage": "review",
                "summary": "Synthetic reopen evidence for pivot execution.",
                "created_at": "2026-03-30T00:00:00Z",
                "trust_state": "current",
            }
        )
        lineage_registry.setdefault("artifacts", []).append(
            {"ticket_id": "EXEC-REOPEN", **reopen_ticket["artifacts"][0]}
        )
        lineage_workflow["ticket_state"]["EXEC-RECON-SRC"] = {
            "approved_plan": False,
            "reopen_count": 0,
            "needs_reverification": False,
        }
        lineage_workflow["ticket_state"]["EXEC-RECON-TGT"] = {
            "approved_plan": False,
            "reopen_count": 0,
            "needs_reverification": False,
        }
        lineage_workflow["ticket_state"]["EXEC-REOPEN"] = {
            "approved_plan": False,
            "reopen_count": 0,
            "needs_reverification": False,
        }
        lineage_manifest_path.write_text(
            json.dumps(lineage_manifest, indent=2) + "\n", encoding="utf-8"
        )
        lineage_workflow_path.write_text(
            json.dumps(lineage_workflow, indent=2) + "\n", encoding="utf-8"
        )
        lineage_registry_path.write_text(
            json.dumps(lineage_registry, indent=2) + "\n", encoding="utf-8"
        )
        pivot_lineage_payload = run_json(
            [
                sys.executable,
                str(PIVOT),
                str(pivot_lineage_dest),
                "--pivot-class",
                "feature-add",
                "--requested-change",
                "Rescope follow-up execution around a replacement implementation source and reopen one completed ticket.",
                "--accepted-decision",
                "Use a replacement source ticket for the stale follow-up lineage.",
                "--reconcile-ticket",
                "EXEC-RECON-TGT",
                "--reopen-ticket",
                "EXEC-REOPEN",
                "--lineage-evidence",
                f"EXEC-RECON-TGT={reconcile_evidence_rel}",
                "--replacement-source",
                "EXEC-RECON-TGT=EXEC-RECON-SRC",
                "--replacement-source-mode",
                "EXEC-RECON-TGT=split_scope",
                "--lineage-evidence",
                f"EXEC-REOPEN={reopen_evidence_rel}",
                "--skip-verify",
                "--format",
                "json",
            ],
            ROOT,
        )
        if pivot_lineage_payload["verification_status"]["performed"] is not False:
            raise RuntimeError(
                "Execution-backed pivot fixtures should be able to defer post-pivot verification until explicit lineage actions run"
            )
        if (
            pivot_lineage_payload["restart_surface_publication"]["status"]
            != "published"
        ):
            raise RuntimeError(
                "Pivot planning should publish restart surfaces for execution-backed lineage pivots"
            )
        pivot_lineage_apply = run_json(
            [
                sys.executable,
                str(PIVOT_APPLY),
                str(pivot_lineage_dest),
                "--skip-publish",
            ],
            ROOT,
        )
        if {item["label"] for item in pivot_lineage_apply["applied_actions"]} != {
            "reconcile:EXEC-RECON-TGT",
            "reopen:EXEC-REOPEN",
        }:
            raise RuntimeError(
                "Pivot lineage execution should apply the explicit runtime-ready reconcile and reopen actions"
            )
        if pivot_lineage_apply["pending_actions"]:
            raise RuntimeError(
                "Pivot lineage execution should clear pending explicit actions once all runtime-ready actions complete"
            )
        ticket_pack_builder_stage = pivot_lineage_apply["ticket_pack_builder_stage"]
        if (
            ticket_pack_builder_stage["status"] != "completed"
            or ticket_pack_builder_stage["completion_mode"] != "pivot_lineage_execution"
        ):
            raise RuntimeError(
                "Pivot lineage execution should auto-complete ticket-pack-builder when explicit actions satisfy the whole ticket lineage plan"
            )
        pivot_lineage_state = json.loads(
            (pivot_lineage_dest / ".opencode" / "meta" / "pivot-state.json").read_text(
                encoding="utf-8"
            )
        )
        if set(pivot_lineage_state["ticket_lineage_plan"]["completed_actions"]) != {
            "reconcile:EXEC-RECON-TGT",
            "reopen:EXEC-REOPEN",
        }:
            raise RuntimeError(
                "Pivot lineage execution should persist completed explicit lineage actions in pivot state"
            )
        if pivot_lineage_apply["publication"] is not None:
            raise RuntimeError(
                "Pivot lineage execution should defer restart publication when post-pivot verification is explicitly skipped"
            )
        updated_lineage_manifest = json.loads(
            lineage_manifest_path.read_text(encoding="utf-8")
        )
        updated_reopen_ticket = next(
            ticket
            for ticket in updated_lineage_manifest["tickets"]
            if ticket["id"] == "EXEC-REOPEN"
        )
        if updated_reopen_ticket["resolution_state"] != "reopened":
            raise RuntimeError(
                "Pivot lineage execution should reopen the completed ticket through the generated ticket_reopen tool"
            )
        updated_reconcile_target = next(
            ticket
            for ticket in updated_lineage_manifest["tickets"]
            if ticket["id"] == "EXEC-RECON-TGT"
        )
        if (
            updated_reconcile_target["source_ticket_id"] != "EXEC-RECON-SRC"
            or "SETUP-001" in updated_reconcile_target["depends_on"]
        ):
            raise RuntimeError(
                "Pivot lineage execution should reconcile stale target lineage through the generated ticket_reconcile tool"
            )
        post_lineage_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(pivot_lineage_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        post_lineage_codes = {
            finding["code"] for finding in post_lineage_audit.get("findings", [])
        }
        if "WFLOW019" in post_lineage_codes:
            raise RuntimeError(
                "Pivot lineage execution should remove the stale contradictory source/dependency graph for the executed reconciliation target"
            )
        invocation_tracker = (
            full_dest / ".opencode" / "plugins" / "invocation-tracker.ts"
        ).read_text(encoding="utf-8")
        if "agent: input.agent ?? null" not in invocation_tracker:
            raise RuntimeError(
                "Generated invocation-tracker.ts should record agent ownership on command and tool events"
            )
        generated_handoff_publish = (
            full_dest / ".opencode" / "tools" / "handoff_publish.ts"
        ).read_text(encoding="utf-8")
        if "validateHandoffNextAction" not in generated_handoff_publish:
            raise RuntimeError(
                "Generated handoff_publish.ts should validate custom next_action claims before publishing"
            )
        if generated_handoff_publish.find(
            "const handoffBlocker = await validateHandoffNextAction"
        ) >= generated_handoff_publish.find("await refreshRestartSurfaces"):
            raise RuntimeError(
                "Generated handoff_publish.ts should validate next_action claims before refreshing restart surfaces"
            )
        generated_artifact_write = (
            full_dest / ".opencode" / "tools" / "artifact_write.ts"
        ).read_text(encoding="utf-8")
        if (
            "expectedPath = defaultArtifactPath" not in generated_artifact_write
            or "canonicalizeRepoPath(args.path)" not in generated_artifact_write
        ):
            raise RuntimeError(
                "Generated artifact_write.ts should enforce canonical artifact paths"
            )
        generated_artifact_register = (
            full_dest / ".opencode" / "tools" / "artifact_register.ts"
        ).read_text(encoding="utf-8")
        if (
            "expectedPath = defaultArtifactPath" not in generated_artifact_register
            or "canonicalizeRepoPath(args.path)" not in generated_artifact_register
        ):
            raise RuntimeError(
                "Generated artifact_register.ts should enforce canonical artifact paths"
            )

        bootstrap_lane_gate = run_json(
            [
                sys.executable,
                str(VERIFY_GENERATED),
                str(full_dest),
                "--verification-kind",
                "bootstrap-lane",
                "--format",
                "json",
            ],
            ROOT,
        )
        if bootstrap_lane_gate.get("findings"):
            codes = ", ".join(
                item["code"] for item in bootstrap_lane_gate.get("findings", [])
            )
            raise RuntimeError(
                f"A fresh scaffold should preserve one valid bootstrap lane before specialization, but it emitted: {codes}"
            )

        broken_bootstrap_lane_dest = workspace / "greenfield-bootstrap-lane-broken"
        shutil.copytree(full_dest, broken_bootstrap_lane_dest)
        broken_start_here = broken_bootstrap_lane_dest / "START-HERE.md"
        broken_start_here.write_text(
            broken_start_here.read_text(encoding="utf-8").replace(
                "Run `environment_bootstrap`, register its proof artifact, rerun `ticket_lookup`, and do not continue lifecycle work until bootstrap is ready.",
                "Continue with normal ticket lifecycle work.",
            ),
            encoding="utf-8",
        )
        broken_bootstrap_lane_result = subprocess.run(
            [
                sys.executable,
                str(VERIFY_GENERATED),
                str(broken_bootstrap_lane_dest),
                "--verification-kind",
                "bootstrap-lane",
                "--format",
                "json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        broken_bootstrap_lane_payload = json.loads(broken_bootstrap_lane_result.stdout)
        broken_bootstrap_lane_codes = {
            finding["code"]
            for finding in broken_bootstrap_lane_payload.get("findings", [])
        }
        if broken_bootstrap_lane_result.returncode != 2:
            raise RuntimeError(
                "Bootstrap-lane verifier should fail when the rendered scaffold loses its bootstrap-first route"
            )
        if "VERIFY106" not in broken_bootstrap_lane_codes:
            raise RuntimeError(
                "Bootstrap-lane verifier should emit VERIFY106 when the base scaffold loses aligned bootstrap-first routing"
            )

        greenfield_gate_dest = workspace / "greenfield-proof-gate"
        shutil.copytree(full_dest, greenfield_gate_dest)
        make_stack_skill_non_placeholder(greenfield_gate_dest)
        greenfield_gate = run_json(
            [
                sys.executable,
                str(VERIFY_GENERATED),
                str(greenfield_gate_dest),
                "--format",
                "json",
            ],
            ROOT,
        )
        if greenfield_gate.get("findings"):
            codes = ", ".join(
                item["code"] for item in greenfield_gate.get("findings", [])
            )
            raise RuntimeError(
                f"A placeholder-free fresh scaffold should pass the shared greenfield continuation verifier, but it emitted: {codes}"
            )
        android_greenfield_dest = workspace / "greenfield-android-target-missing-lanes"
        shutil.copytree(full_dest, android_greenfield_dest)
        make_stack_skill_non_placeholder(android_greenfield_dest)
        seed_godot_android_target(android_greenfield_dest)
        android_greenfield_result = subprocess.run(
            [
                sys.executable,
                str(VERIFY_GENERATED),
                str(android_greenfield_dest),
                "--format",
                "json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        android_greenfield_payload = json.loads(android_greenfield_result.stdout)
        android_greenfield_codes = {
            finding["code"]
            for finding in android_greenfield_payload.get("findings", [])
        }
        if android_greenfield_result.returncode != 2:
            raise RuntimeError(
                "Greenfield continuation verifier should fail when a declared Godot Android target lacks canonical Android completion tickets"
            )
        if "VERIFY012" not in android_greenfield_codes:
            raise RuntimeError(
                "Greenfield continuation verifier should emit VERIFY012 for missing Android target-completion lanes"
            )
        blocked_greenfield_dest = workspace / "greenfield-proof-gate-bootstrap-blocked"
        shutil.copytree(greenfield_gate_dest, blocked_greenfield_dest)
        blocked_workflow_path = (
            blocked_greenfield_dest / ".opencode" / "state" / "workflow-state.json"
        )
        blocked_workflow = json.loads(
            blocked_workflow_path.read_text(encoding="utf-8")
        )
        blocked_workflow["bootstrap"] = {
            "status": "ready",
            "last_verified_at": "2026-04-01T00:00:00Z",
            "environment_fingerprint": compute_bootstrap_fingerprint(blocked_greenfield_dest),
            "proof_artifact": ".opencode/state/bootstrap/synthetic-ready-bootstrap.md",
        }
        blocked_workflow["bootstrap_blockers"] = [
            {
                "executable": "android-sdk",
                "reason": "Required by Android export configuration.",
                "install_command": "sdkmanager --install 'platform-tools'",
            }
        ]
        blocked_workflow_path.write_text(
            json.dumps(blocked_workflow, indent=2) + "\n", encoding="utf-8"
        )
        blocked_greenfield_result = subprocess.run(
            [
                sys.executable,
                str(VERIFY_GENERATED),
                str(blocked_greenfield_dest),
                "--format",
                "json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        blocked_greenfield_payload = json.loads(blocked_greenfield_result.stdout)
        blocked_greenfield_codes = {
            finding["code"]
            for finding in blocked_greenfield_payload.get("findings", [])
        }
        if blocked_greenfield_result.returncode != 2:
            raise RuntimeError(
                "Generated scaffold verifier should fail when bootstrap blockers remain unresolved in ready workflow state"
            )
        if "VERIFY009" not in blocked_greenfield_codes:
            raise RuntimeError(
                "Generated scaffold verifier should emit VERIFY009 when bootstrap blockers remain unresolved"
            )
        reference_broken_dest = workspace / "greenfield-proof-gate-reference-broken"
        shutil.copytree(greenfield_gate_dest, reference_broken_dest)
        (reference_broken_dest / "package.json").write_text(
            json.dumps(
                {"name": "broken-ref", "version": "1.0.0", "main": "missing-entry.js"},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        reference_broken_result = subprocess.run(
            [
                sys.executable,
                str(VERIFY_GENERATED),
                str(reference_broken_dest),
                "--format",
                "json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        reference_broken_payload = json.loads(reference_broken_result.stdout)
        reference_broken_codes = {
            finding["code"]
            for finding in reference_broken_payload.get("findings", [])
        }
        if reference_broken_result.returncode != 2:
            raise RuntimeError(
                "Generated scaffold verifier should fail when reference-integrity findings remain in the generated repo"
            )
        if "VERIFY011" not in reference_broken_codes:
            raise RuntimeError(
                "Generated scaffold verifier should emit VERIFY011 when canonical config references point at missing files"
            )
        execution_broken_dest = workspace / "greenfield-proof-gate-execution-broken"
        shutil.copytree(greenfield_gate_dest, execution_broken_dest)
        (execution_broken_dest / "package.json").write_text(
            json.dumps(
                {
                    "name": "broken-exec",
                    "version": "1.0.0",
                    "main": "index.js",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (execution_broken_dest / "index.js").write_text(
            "throw new Error('synthetic execution failure for VERIFY010')\n",
            encoding="utf-8",
        )
        execution_broken_result = subprocess.run(
            [
                sys.executable,
                str(VERIFY_GENERATED),
                str(execution_broken_dest),
                "--format",
                "json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        execution_broken_payload = json.loads(execution_broken_result.stdout)
        execution_broken_codes = {
            finding["code"]
            for finding in execution_broken_payload.get("findings", [])
        }
        if execution_broken_result.returncode != 2:
            raise RuntimeError(
                "Generated scaffold verifier should fail when critical execution audit findings remain in the generated repo"
            )
        if "VERIFY010" not in execution_broken_codes:
            raise RuntimeError(
                "Generated scaffold verifier should emit VERIFY010 when a generated entrypoint cannot load"
            )
        manifest = json.loads(
            (ROOT / "skills" / "skill-flow-manifest.json").read_text(encoding="utf-8")
        )
        greenfield_sequence = manifest["run_types"]["greenfield"]["sequence"]
        bootstrap_verifier_step = "repo-scaffold-factory:verify-bootstrap-lane"
        verifier_step = "repo-scaffold-factory:verify-generated-scaffold"
        if bootstrap_verifier_step not in greenfield_sequence:
            raise RuntimeError(
                "Greenfield manifest sequence should include the early bootstrap-lane verification gate"
            )
        if verifier_step not in greenfield_sequence:
            raise RuntimeError(
                "Greenfield manifest sequence should include the pre-handoff verification gate"
            )
        if (
            greenfield_sequence.index(bootstrap_verifier_step)
            != greenfield_sequence.index("repo-scaffold-factory") + 1
        ):
            raise RuntimeError(
                "Greenfield manifest sequence should place the bootstrap-lane verifier immediately after repo-scaffold-factory"
            )
        if greenfield_sequence.index(
            bootstrap_verifier_step
        ) >= greenfield_sequence.index("project-skill-bootstrap:full-greenfield-pass"):
            raise RuntimeError(
                "Greenfield manifest sequence should place the bootstrap-lane verifier before project-skill-bootstrap"
            )
        if greenfield_sequence.index(verifier_step) >= greenfield_sequence.index(
            "handoff-brief"
        ):
            raise RuntimeError(
                "Greenfield manifest sequence should place the verification gate before handoff-brief"
            )

        corrupt_gate_dest = workspace / "greenfield-proof-gate-corrupt"
        shutil.copytree(greenfield_gate_dest, corrupt_gate_dest)
        (corrupt_gate_dest / "tickets" / "manifest.json").write_text(
            "{\n", encoding="utf-8"
        )
        corrupt_gate_result = subprocess.run(
            [
                sys.executable,
                str(VERIFY_GENERATED),
                str(corrupt_gate_dest),
                "--format",
                "json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        corrupt_gate_payload = json.loads(corrupt_gate_result.stdout)
        corrupt_gate_codes = {
            finding["code"] for finding in corrupt_gate_payload.get("findings", [])
        }
        if corrupt_gate_result.returncode != 2:
            raise RuntimeError(
                "Generated scaffold verifier should fail with exit code 2 when canonical state is corrupt"
            )
        if "VERIFY001" not in corrupt_gate_codes:
            raise RuntimeError(
                "Generated scaffold verifier should emit VERIFY001 instead of crashing on corrupt JSON state"
            )

        workflow_contract_drift_dest = (
            workspace / "greenfield-proof-gate-workflow-contract-drift"
        )
        shutil.copytree(greenfield_gate_dest, workflow_contract_drift_dest)
        tooling_doc_path = (
            workflow_contract_drift_dest / "docs" / "process" / "tooling.md"
        )
        tooling_doc = tooling_doc_path.read_text(encoding="utf-8")
        tooling_doc_path.write_text(
            tooling_doc.replace(
                "commands are human entrypoints only",
                "commands may drive the autonomous workflow",
            ),
            encoding="utf-8",
        )
        workflow_contract_gate_result = subprocess.run(
            [
                sys.executable,
                str(VERIFY_GENERATED),
                str(workflow_contract_drift_dest),
                "--format",
                "json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        workflow_contract_gate = json.loads(workflow_contract_gate_result.stdout)
        workflow_contract_gate_codes = {
            finding["code"] for finding in workflow_contract_gate.get("findings", [])
        }
        if workflow_contract_gate_result.returncode != 2:
            raise RuntimeError(
                "Generated scaffold verifier should fail when continuation-critical workflow contract surfaces drift"
            )
        if "VERIFY008" not in workflow_contract_gate_codes:
            raise RuntimeError(
                "Generated scaffold verifier should emit VERIFY008 when tooling and execution surfaces drift from the documented greenfield contract"
            )

        repair_scripts_dir = ROOT / "skills" / "scafforge-repair" / "scripts"
        audit_scripts_dir = ROOT / "skills" / "scafforge-audit" / "scripts"
        for script_dir in (repair_scripts_dir, audit_scripts_dir):
            script_dir_str = str(script_dir)
            if script_dir_str not in sys.path:
                sys.path.insert(0, script_dir_str)
        repair_module = load_python_module(
            REPAIR, "scafforge_smoke_apply_repo_process_repair"
        )
        regenerate_module = load_python_module(
            REGENERATE, "scafforge_smoke_regenerate_restart_surfaces"
        )
        audit_module = load_python_module(AUDIT, "scafforge_smoke_audit_repo_process")

        rendered_block = "\n".join(
            [
                "# START HERE",
                "",
                "<!-- SCAFFORGE:START_HERE_BLOCK START -->",
                "fresh managed block",
                "<!-- SCAFFORGE:START_HERE_BLOCK END -->",
                "",
            ]
        )
        for merge_fn in (
            repair_module.merge_start_here,
            regenerate_module.merge_start_here,
        ):
            partial_start = merge_fn(
                "intro\n<!-- SCAFFORGE:START_HERE_BLOCK START -->\nstale managed block",
                rendered_block,
            )
            if (
                "stale managed block" in partial_start
                or "fresh managed block" not in partial_start
            ):
                raise RuntimeError(
                    "Partial START marker state should be repaired by replacing the stale managed block"
                )
            partial_end = merge_fn(
                "stale prelude\n<!-- SCAFFORGE:START_HERE_BLOCK END -->\noutro",
                rendered_block,
            )
            if (
                "stale prelude" in partial_end
                or "fresh managed block" not in partial_end
                or "outro" not in partial_end
            ):
                raise RuntimeError(
                    "Partial END marker state should be repaired by restoring the managed block while preserving trailing unmanaged content"
                )

        env_only_stale_surface_map = repair_module.build_stale_surface_map(
            ROOT,
            [],
            [SimpleNamespace(code="ENV001")],
            False,
        )
        if (
            env_only_stale_surface_map["workflow_tools_and_prompts"]["status"]
            != "stable"
        ):
            raise RuntimeError(
                "ENV-only findings should not misclassify workflow_tools_and_prompts as managed replacement drift"
            )
        if env_only_stale_surface_map["workflow_tools_and_prompts"].get(
            "finding_codes"
        ):
            raise RuntimeError(
                "ENV-only findings should not populate workflow_tools_and_prompts finding codes"
            )
        if (
            env_only_stale_surface_map["canonical_project_decisions"]["status"]
            != "stable"
        ):
            raise RuntimeError(
                "Routine public repair should not emit canonical-project human-decision escalation from the stale-surface map"
            )

        windows_venv_dest = workspace / "windows-venv-detection"
        windows_venv_dest.mkdir(parents=True, exist_ok=True)
        windows_python = windows_venv_dest / ".venv" / "Scripts" / "python.exe"
        windows_pytest = windows_venv_dest / ".venv" / "Scripts" / "pytest.exe"
        write_executable(
            windows_python,
            '#!/bin/sh\nif [ "$1" = "-m" ] && [ "$2" = "pytest" ] && [ "$3" = "--version" ]; then exit 0; fi\nif [ "$1" = "--version" ]; then exit 0; fi\nexit 1\n',
        )
        write_executable(windows_pytest, "#!/bin/sh\nexit 0\n")
        detected_python = audit_module._detect_python(windows_venv_dest)
        if detected_python != str(windows_python):
            raise RuntimeError(
                "Audit python detection should recognize repo-local Windows-style .venv/Scripts/python.exe"
            )
        detected_pytest = audit_module._detect_pytest_command(windows_venv_dest)
        if detected_pytest != [str(windows_python), "-m", "pytest"]:
            raise RuntimeError(
                "Audit pytest detection should use Windows-style repo-local python when it is the available executable"
            )

        initial_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(full_dest),
                "--format",
                "json",
                "--emit-diagnosis-pack",
            ],
            ROOT,
        )
        initial_codes = {
            finding["code"] for finding in initial_audit.get("findings", [])
        }
        if "SKILL001" not in initial_codes:
            raise RuntimeError(
                "Audit should flag placeholder repo-local skills with SKILL001 on the base scaffold output"
            )
        asset_meta_path = full_dest / ".opencode" / "meta" / "asset-pipeline-bootstrap.json"
        asset_meta_path.parent.mkdir(parents=True, exist_ok=True)
        asset_meta_path.write_text(
            json.dumps(
                {
                    "suggested_skills": ["blender-mcp-workflow"],
                    "routes": {"characters": "blender-mcp"},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        stale_blender_skill = full_dest / ".opencode" / "skills" / "blender-mcp-workflow" / "SKILL.md"
        stale_blender_skill.parent.mkdir(parents=True, exist_ok=True)
        stale_blender_skill.write_text(
            "\n".join(
                (
                    "---",
                    "name: blender-mcp-workflow",
                    "description: stale test skill",
                    "---",
                    "",
                    "# Blender-MCP Workflow",
                    "",
                    "- Requires an active Blender session via the MCP add-on",
                    "- Use blender_session_create and blender_session_checkpoint between modeling steps",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        stale_skill_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(full_dest),
                "--format",
                "json",
            ],
            ROOT,
        )
        stale_skill_evidence = [
            finding
            for finding in stale_skill_audit.get("findings", [])
            if finding.get("code") == "SKILL001"
        ]
        if not any(
            "blender-mcp-workflow/SKILL.md"
            in " ".join(finding.get("files", [])) + " " + " ".join(finding.get("evidence", []))
            for finding in stale_skill_evidence
        ):
            raise RuntimeError(
                "Audit should flag stale synthesized blender-mcp-workflow skills with SKILL001 when asset-pipeline metadata requires that skill"
            )
        diagnosis_root = full_dest / "diagnosis"
        diagnosis_dirs = (
            sorted(path for path in diagnosis_root.iterdir() if path.is_dir())
            if diagnosis_root.exists()
            else []
        )
        if not diagnosis_dirs:
            raise RuntimeError(
                "Audit should create a diagnosis/<timestamp> folder when diagnosis-pack emission is enabled"
            )
        diagnosis_pack = diagnosis_dirs[-1]
        required_reports = [
            "01-initial-codebase-review.md",
            "02-scafforge-process-failures.md",
            "03-scafforge-prevention-actions.md",
            "04-live-repo-repair-plan.md",
            "manifest.json",
        ]
        for relative in required_reports:
            if not (diagnosis_pack / relative).exists():
                raise RuntimeError(
                    f"Diagnosis pack is missing expected file: {diagnosis_pack / relative}"
                )

        diagnosis_manifest = json.loads(
            (diagnosis_pack / "manifest.json").read_text(encoding="utf-8")
        )
        if "ticket_recommendations" not in diagnosis_manifest:
            raise RuntimeError(
                "Diagnosis pack manifest should include ticket_recommendations"
            )
        if (
            diagnosis_manifest.get("report_files", {}).get("report_4")
            != "04-live-repo-repair-plan.md"
        ):
            raise RuntimeError(
                "Diagnosis pack manifest should map report_4 to 04-live-repo-repair-plan.md"
            )
        if diagnosis_manifest.get("diagnosis_kind") != "initial_diagnosis":
            raise RuntimeError(
                "Initial audit diagnosis packs should be labeled initial_diagnosis"
            )
        if not isinstance(
            diagnosis_manifest.get("audit_package_commit"), str
        ) or not diagnosis_manifest.get("audit_package_commit"):
            raise RuntimeError(
                "Diagnosis pack manifest should record the Scafforge audit package commit"
            )
        if (
            "package_work_required_first" not in diagnosis_manifest
            or "recommended_next_step" not in diagnosis_manifest
        ):
            raise RuntimeError(
                "Diagnosis pack manifest should record package-work gating and the recommended next step"
            )

        restart_surface_dest = workspace / "restart-surface-drift"
        shutil.copytree(full_dest, restart_surface_dest)
        seed_restart_surface_drift(restart_surface_dest)
        restart_surface_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(restart_surface_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        restart_surface_codes = {
            finding["code"] for finding in restart_surface_audit.get("findings", [])
        }
        if "WFLOW010" not in restart_surface_codes:
            raise RuntimeError(
                "A repo whose START-HERE or context snapshot drifts from canonical workflow state should emit WFLOW010"
            )

        bootstrap_guidance_dest = workspace / "bootstrap-guidance-drift"
        shutil.copytree(full_dest, bootstrap_guidance_dest)
        seed_bootstrap_guidance_drift(bootstrap_guidance_dest)
        make_stack_skill_non_placeholder(bootstrap_guidance_dest)
        bootstrap_guidance_gate_result = subprocess.run(
            [
                sys.executable,
                str(VERIFY_GENERATED),
                str(bootstrap_guidance_dest),
                "--format",
                "json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        bootstrap_guidance_gate = json.loads(bootstrap_guidance_gate_result.stdout)
        bootstrap_guidance_gate_codes = {
            finding["code"] for finding in bootstrap_guidance_gate.get("findings", [])
        }
        if "VERIFY006" not in bootstrap_guidance_gate_codes:
            raise RuntimeError(
                "A repo whose greenfield bootstrap routing drifted should fail the shared continuation verifier with VERIFY006"
            )
        bootstrap_guidance_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(bootstrap_guidance_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        bootstrap_guidance_codes = {
            finding["code"] for finding in bootstrap_guidance_audit.get("findings", [])
        }
        if "WFLOW011" not in bootstrap_guidance_codes:
            raise RuntimeError(
                "A repo whose workflow surfaces do not route failed bootstrap to environment_bootstrap first should emit WFLOW011"
            )

        split_lease_dest = workspace / "split-lease-guidance"
        shutil.copytree(full_dest, split_lease_dest)
        seed_split_lease_guidance(split_lease_dest)
        split_lease_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(split_lease_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        split_lease_codes = {
            finding["code"] for finding in split_lease_audit.get("findings", [])
        }
        if "WFLOW012" not in split_lease_codes:
            raise RuntimeError(
                "A repo whose prompts split lease ownership between coordinator and workers should emit WFLOW012"
            )

        resume_truth_dest = workspace / "resume-truth-hierarchy"
        shutil.copytree(full_dest, resume_truth_dest)
        seed_resume_truth_hierarchy_drift(resume_truth_dest)
        resume_truth_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(resume_truth_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        resume_truth_codes = {
            finding["code"] for finding in resume_truth_audit.get("findings", [])
        }
        if "WFLOW013" not in resume_truth_codes:
            raise RuntimeError(
                "A repo whose resume surfaces treat derived handoff text as canonical should emit WFLOW013"
            )

        legacy_gate_dest = workspace / "legacy-repair-gate"
        shutil.copytree(full_dest, legacy_gate_dest)
        seed_legacy_repair_follow_on_gate_leak(legacy_gate_dest)
        legacy_gate_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(legacy_gate_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        legacy_gate_codes = {
            finding["code"] for finding in legacy_gate_audit.get("findings", [])
        }
        if "WFLOW021" not in legacy_gate_codes:
            raise RuntimeError(
                "A repo whose prompts or restart surfaces still route from handoff_allowed should emit WFLOW021"
            )

        invocation_log_dest = workspace / "invocation-log-coordinator-artifacts"
        shutil.copytree(full_dest, invocation_log_dest)
        seed_invocation_log_coordinator_artifacts(invocation_log_dest)
        invocation_log_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(invocation_log_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        invocation_log_codes = {
            finding["code"] for finding in invocation_log_audit.get("findings", [])
        }
        if "WFLOW014" not in invocation_log_codes:
            raise RuntimeError(
                "A repo whose invocation log shows coordinator-authored specialist artifacts should emit WFLOW014"
            )

        restart_repair_dest = workspace / "restart-surface-repair"
        shutil.copytree(full_dest, restart_repair_dest)
        seed_restart_surface_drift(restart_repair_dest)
        run_json([sys.executable, str(REPAIR), str(restart_repair_dest)], ROOT)
        repaired_start_here = (restart_repair_dest / "START-HERE.md").read_text(
            encoding="utf-8"
        )
        if (
            "- bootstrap_status: failed" not in repaired_start_here
            or "- pending_process_verification: true" not in repaired_start_here
            or "- repair_follow_on_outcome: managed_blocked" not in repaired_start_here
            or "- handoff_status: bootstrap recovery required"
            not in repaired_start_here
            or "- repair_follow_on_required: true" not in repaired_start_here
            or "- split_child_tickets: none" not in repaired_start_here
        ):
            raise RuntimeError(
                "Repair should refresh START-HERE.md from canonical workflow state after managed surface replacement"
            )
        if "repair_follow_on_handoff_allowed" in repaired_start_here:
            raise RuntimeError(
                "Repair should not republish legacy repair_follow_on_handoff_allowed in START-HERE.md"
            )
        repaired_context_snapshot = (
            restart_repair_dest / ".opencode" / "state" / "context-snapshot.md"
        ).read_text(encoding="utf-8")
        if (
            "- state_revision: 123" not in repaired_context_snapshot
            or "- No active lane leases" not in repaired_context_snapshot
            or "## Repair Follow-On" not in repaired_context_snapshot
            or "- Open split children: none" not in repaired_context_snapshot
        ):
            raise RuntimeError(
                "Repair should refresh context-snapshot.md with current revision and active lane-lease facts"
            )
        if "- handoff_allowed:" in repaired_context_snapshot:
            raise RuntimeError(
                "Repair should not republish legacy handoff_allowed in context-snapshot.md"
            )
        repaired_latest_handoff = (
            restart_repair_dest / ".opencode" / "state" / "latest-handoff.md"
        ).read_text(encoding="utf-8")
        if (
            "- bootstrap_status: failed" not in repaired_latest_handoff
            or "- pending_process_verification: true" not in repaired_latest_handoff
            or "- repair_follow_on_outcome: managed_blocked"
            not in repaired_latest_handoff
            or "- handoff_status: bootstrap recovery required"
            not in repaired_latest_handoff
            or "- repair_follow_on_required: true" not in repaired_latest_handoff
            or "- split_child_tickets: none" not in repaired_latest_handoff
        ):
            raise RuntimeError(
                "Repair should refresh latest-handoff.md from canonical workflow state after managed surface replacement"
            )
        if "repair_follow_on_handoff_allowed" in repaired_latest_handoff:
            raise RuntimeError(
                "Repair should not republish legacy repair_follow_on_handoff_allowed in latest-handoff.md"
            )
        repaired_restart_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(restart_repair_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        repaired_restart_codes = {
            finding["code"] for finding in repaired_restart_audit.get("findings", [])
        }
        if "WFLOW010" in repaired_restart_codes:
            raise RuntimeError(
                "Repair should clear WFLOW010 by regenerating START-HERE.md, context-snapshot.md, and latest-handoff.md from canonical state"
            )

        public_repair_dest = workspace / "public-repair-runner"
        shutil.copytree(full_dest, public_repair_dest)
        public_repair = subprocess.run(
            [
                sys.executable,
                str(PUBLIC_REPAIR),
                str(public_repair_dest),
                "--skip-verify",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if public_repair.returncode == 0:
            raise RuntimeError(
                "Public managed repair runner should fail closed until required follow-on stages are marked complete"
            )
        public_repair_payload = json.loads(public_repair.stdout)
        if public_repair_payload["execution_record"]["handoff_allowed"]:
            raise RuntimeError(
                "Public managed repair runner must block handoff while required follow-on stages remain unexecuted"
            )
        if (
            public_repair_payload["execution_record"]["repair_follow_on_outcome"]
            != "managed_blocked"
        ):
            raise RuntimeError(
                "Public managed repair runner should classify incomplete managed follow-on as managed_blocked"
            )
        if not (
            public_repair_dest / ".opencode" / "meta" / "repair-execution.json"
        ).exists():
            raise RuntimeError(
                "Public managed repair runner should persist a machine-readable repair execution record"
            )
        public_repair_android_dest = workspace / "public-repair-android-follow-up"
        shutil.copytree(full_dest, public_repair_android_dest)
        seed_godot_android_target(public_repair_android_dest)
        seed_minimal_godot_project(public_repair_android_dest)
        seed_ready_bootstrap(public_repair_android_dest)
        public_repair_android = subprocess.run(
            [
                sys.executable,
                str(PUBLIC_REPAIR),
                str(public_repair_android_dest),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if not public_repair_android.stdout.strip():
            raise RuntimeError(
                "Public managed repair runner should always emit a JSON execution payload"
            )
        public_repair_android_manifest = json.loads(
            (public_repair_android_dest / "tickets" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        android_ticket = next(
            (
                ticket
                for ticket in public_repair_android_manifest["tickets"]
                if ticket["id"] == "ANDROID-001"
            ),
            None,
        )
        release_ticket = next(
            (
                ticket
                for ticket in public_repair_android_manifest["tickets"]
                if ticket["id"] == "RELEASE-001"
            ),
            None,
        )
        if android_ticket is None or release_ticket is None:
            raise RuntimeError(
                "Managed repair follow-on should create the canonical Android export and release tickets for Godot Android repos"
            )
        missing_repair_surfaces = [
            relative
            for relative in ("export_presets.cfg", "android/scafforge-managed.json")
            if not (public_repair_android_dest / relative).exists()
        ]
        if missing_repair_surfaces:
            raise RuntimeError(
                "Managed repair should regenerate every Scafforge-owned Android surface. "
                f"Missing: {', '.join(missing_repair_surfaces)}"
            )
        if "ANDROID-001" in release_ticket.get("depends_on", []):
            raise RuntimeError(
                "RELEASE-001 should remain a split-scope child of ANDROID-001 without blocking on its open parent"
            )
        if (
            release_ticket.get("source_ticket_id") != "ANDROID-001"
            or release_ticket.get("source_mode") != "split_scope"
            or release_ticket.get("split_kind") != "sequential_dependent"
        ):
            raise RuntimeError(
                "RELEASE-001 should preserve sequential split-scope lineage to ANDROID-001 when repair creates the Android target-completion ticket pair"
            )
        _release_infra_lanes = {"android-export", "signing-prerequisites", "release-readiness", "remediation", "reverification"}
        _feature_ticket_ids = {
            str(t.get("id", "")).strip()
            for t in public_repair_android_manifest["tickets"]
            if isinstance(t, dict)
            and t.get("lane") not in _release_infra_lanes
            and int(t.get("wave", 0)) > 0
        }
        if _feature_ticket_ids and not (set(release_ticket.get("depends_on", [])) & _feature_ticket_ids):
            raise RuntimeError(
                f"RELEASE-001 must depend on at least one product feature ticket. "
                f"Current depends_on={release_ticket.get('depends_on', [])}, "
                f"eligible feature tickets={sorted(_feature_ticket_ids)}"
            )
        android_reconcile_dest = workspace / "public-repair-android-existing-release"
        shutil.copytree(public_repair_android_dest, android_reconcile_dest)
        android_reconcile_manifest_path = android_reconcile_dest / "tickets" / "manifest.json"
        android_reconcile_manifest = json.loads(
            android_reconcile_manifest_path.read_text(encoding="utf-8")
        )
        android_reconcile_release = next(
            ticket
            for ticket in android_reconcile_manifest["tickets"]
            if ticket["id"] == "RELEASE-001"
        )
        android_reconcile_release["source_ticket_id"] = None
        android_reconcile_release["source_mode"] = None
        android_reconcile_release["split_kind"] = None
        android_reconcile_release["depends_on"] = sorted(
            set(android_reconcile_release.get("depends_on", [])) | {"ANDROID-001"}
        )
        android_reconcile_manifest_path.write_text(
            json.dumps(android_reconcile_manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        android_reconcile_diagnosis_dirs = sorted(
            path
            for path in (android_reconcile_dest / "diagnosis").iterdir()
            if path.is_dir()
        )
        android_reconcile_result = run_json(
            [
                sys.executable,
                str(
                    ROOT
                    / "skills"
                    / "ticket-pack-builder"
                    / "scripts"
                    / "apply_remediation_follow_up.py"
                ),
                str(android_reconcile_dest),
                "--diagnosis",
                str(android_reconcile_diagnosis_dirs[-1] / "manifest.json"),
            ],
            ROOT,
        )
        if "RELEASE-001" not in android_reconcile_result.get("created_tickets", []):
            raise RuntimeError(
                "Android target-completion follow-up should report existing RELEASE-001 normalization when split-scope linkage drifts"
            )
        android_reconcile_manifest = json.loads(
            android_reconcile_manifest_path.read_text(encoding="utf-8")
        )
        android_reconciled_release = next(
            ticket
            for ticket in android_reconcile_manifest["tickets"]
            if ticket["id"] == "RELEASE-001"
        )
        if "ANDROID-001" in android_reconciled_release.get("depends_on", []):
            raise RuntimeError(
                "Existing RELEASE-001 tickets should drop ANDROID-001 from depends_on when split-scope linkage is restored"
            )
        if (
            android_reconciled_release.get("source_ticket_id") != "ANDROID-001"
            or android_reconciled_release.get("source_mode") != "split_scope"
            or android_reconciled_release.get("split_kind") != "sequential_dependent"
        ):
            raise RuntimeError(
                "Existing RELEASE-001 tickets should be normalized back to ANDROID-001 split-scope lineage during Android target-completion repair"
            )

        repeat_dest = workspace / "repeat-cycle"
        shutil.copytree(full_dest, repeat_dest)
        repeat_diagnosis_root = repeat_dest / "diagnosis"
        repeat_diagnosis_dirs = sorted(
            path for path in repeat_diagnosis_root.iterdir() if path.is_dir()
        )
        seed_failed_repair_cycle(repeat_dest, repeat_diagnosis_dirs[-1])
        repeated_cycle_audit = run_json(
            [sys.executable, str(AUDIT), str(repeat_dest), "--format", "json"], ROOT
        )
        repeated_cycle_codes = {
            finding["code"] for finding in repeated_cycle_audit.get("findings", [])
        }
        if "CYCLE001" not in repeated_cycle_codes:
            raise RuntimeError(
                "A repo with a prior diagnosis pack, later repair history, and repeated workflow drift should emit CYCLE001"
            )

        repeated_diagnosis_dest = workspace / "repeated-diagnosis-churn"
        shutil.copytree(full_dest, repeated_diagnosis_dest)
        seed_repeated_diagnosis_churn(repeated_diagnosis_dest)
        repeated_diagnosis_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(repeated_diagnosis_dest),
                "--format",
                "json",
            ],
            ROOT,
        )
        repeated_diagnosis_codes = {
            finding["code"] for finding in repeated_diagnosis_audit.get("findings", [])
        }
        if "CYCLE002" not in repeated_diagnosis_codes:
            raise RuntimeError(
                "A repo with repeated same-day diagnosis packs and no later package-side change should emit CYCLE002"
            )

        repeated_diagnosis_new_package_dest = (
            workspace / "repeated-diagnosis-new-package"
        )
        shutil.copytree(repeated_diagnosis_dest, repeated_diagnosis_new_package_dest)
        for manifest_path in (repeated_diagnosis_new_package_dest / "diagnosis").glob(
            "*/manifest.json"
        ):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["audit_package_commit"] = "older-package-commit"
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
        repeated_diagnosis_new_package_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(repeated_diagnosis_new_package_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        repeated_diagnosis_new_package_codes = {
            finding["code"]
            for finding in repeated_diagnosis_new_package_audit.get("findings", [])
        }
        if "CYCLE002" in repeated_diagnosis_new_package_codes:
            raise RuntimeError(
                "A repo whose repeated diagnosis packs were generated under an older package commit should not emit CYCLE002 on a fresh post-package revalidation audit"
            )

        verification_basis_regression_dest = workspace / "verification-basis-regression"
        shutil.copytree(full_dest, verification_basis_regression_dest)
        transcript_basis_log = seed_false_clean_verification_history(
            verification_basis_regression_dest
        )
        verification_basis_regression_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(verification_basis_regression_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        verification_basis_regression_codes = {
            finding["code"]
            for finding in verification_basis_regression_audit.get("findings", [])
        }
        if "CYCLE003" not in verification_basis_regression_codes:
            raise RuntimeError(
                "A repo with a later zero-finding verification pack that dropped the earlier transcript basis should emit CYCLE003"
            )

        verification_basis_false_positive_dest = (
            workspace / "verification-basis-false-positive"
        )
        shutil.copytree(full_dest, verification_basis_false_positive_dest)
        seed_false_clean_preceded_by_later_transcript_basis(
            verification_basis_false_positive_dest
        )
        verification_basis_false_positive_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(verification_basis_false_positive_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        verification_basis_false_positive_codes = {
            finding["code"]
            for finding in verification_basis_false_positive_audit.get("findings", [])
        }
        if "CYCLE003" in verification_basis_false_positive_codes:
            raise RuntimeError(
                "A zero-finding pack that predates the later transcript-backed basis should not emit CYCLE003"
            )
        inherited_basis_repair = subprocess.run(
            [
                sys.executable,
                str(PUBLIC_REPAIR),
                str(verification_basis_regression_dest),
                "--skip-deterministic-refresh",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        inherited_basis_payload = json.loads(inherited_basis_repair.stdout)
        inherited_basis_logs = inherited_basis_payload["execution_record"][
            "verification_status"
        ]["supporting_logs"]
        if any(str(transcript_basis_log) == item for item in inherited_basis_logs):
            raise RuntimeError(
                "Public managed repair runner should not inherit transcript logs from an older diagnosis when the selected repair basis is the newer log-less pack"
            )
        if (
            inherited_basis_payload["execution_record"]["verification_status"][
                "verification_basis"
            ]
            != "current_state_only"
        ):
            raise RuntimeError(
                "Public managed repair runner should classify verification against the latest log-less diagnosis basis as current_state_only"
            )

        explicit_basis_repair = subprocess.run(
            [
                sys.executable,
                str(PUBLIC_REPAIR),
                str(verification_basis_regression_dest),
                "--skip-deterministic-refresh",
                "--repair-basis-diagnosis",
                str(
                    verification_basis_regression_dest / "diagnosis" / "20260327-143940"
                ),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        explicit_basis_payload = json.loads(explicit_basis_repair.stdout)
        explicit_basis_logs = explicit_basis_payload["execution_record"][
            "verification_status"
        ]["supporting_logs"]
        if not any(str(transcript_basis_log) == item for item in explicit_basis_logs):
            raise RuntimeError(
                "Public managed repair runner should inherit transcript logs from the selected repair basis diagnosis"
            )
        if (
            explicit_basis_payload["execution_record"]["verification_status"][
                "verification_basis"
            ]
            != "transcript_backed"
        ):
            raise RuntimeError(
                "Public managed repair runner should classify an explicitly transcript-backed repair basis as transcript_backed"
            )
        if explicit_basis_payload["execution_record"]["verification_status"][
            "repair_basis_path"
        ] != str(verification_basis_regression_dest / "diagnosis" / "20260327-143940"):
            raise RuntimeError(
                "Public managed repair runner should record the selected repair basis diagnosis path"
            )

        chronology_dest = workspace / "chronology"
        shutil.copytree(full_dest, chronology_dest)
        transcript_log = seed_workflow_overclaim(chronology_dest)
        chronology_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(chronology_dest),
                "--format",
                "json",
                "--supporting-log",
                str(transcript_log),
            ],
            ROOT,
        )
        chronology_codes = {
            finding["code"] for finding in chronology_audit.get("findings", [])
        }
        for expected in (
            "WFLOW002",
            "SESSION001",
            "SESSION002",
            "SESSION003",
            "SESSION004",
        ):
            if expected not in chronology_codes:
                raise RuntimeError(
                    f"Audit should emit {expected} when handoff overclaims and transcript chronology proves thrash, bypass-seeking, or evidence-free PASS claims"
                )
        external_chronology_log = workspace / "chronology-supporting-log.md"
        shutil.copyfile(transcript_log, external_chronology_log)
        external_chronology_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(chronology_dest),
                "--format",
                "json",
                "--emit-diagnosis-pack",
                "--supporting-log",
                str(external_chronology_log),
            ],
            ROOT,
        )
        external_chronology_codes = {
            finding["code"] for finding in external_chronology_audit.get("findings", [])
        }
        if "SESSION002" not in external_chronology_codes:
            raise RuntimeError(
                "Audit should still ingest transcript findings when the supporting log lives outside the subject repo root"
            )
        external_supporting_logs = (
            external_chronology_audit.get("diagnosis_pack", {})
            .get("manifest", {})
            .get("supporting_logs", [])
        )
        if external_supporting_logs != [str(external_chronology_log)]:
            raise RuntimeError(
                "Diagnosis packs should preserve external supporting-log paths instead of crashing on non-relative host paths"
            )

        recovered_dest = workspace / "recovered-verification"
        shutil.copytree(full_dest, recovered_dest)
        recovered_log = seed_recovered_verification_log(recovered_dest)
        recovered_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(recovered_dest),
                "--format",
                "json",
                "--supporting-log",
                str(recovered_log),
            ],
            ROOT,
        )
        recovered_codes = {
            finding["code"] for finding in recovered_audit.get("findings", [])
        }
        if "SESSION004" in recovered_codes:
            raise RuntimeError(
                "A transcript with later real recovery evidence should not emit SESSION004"
            )

        failing_suite_dest = workspace / "failing-suite"
        shutil.copytree(full_dest, failing_suite_dest)
        seed_failing_pytest_suite(failing_suite_dest)
        failing_suite_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(failing_suite_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        failing_suite_codes = {
            finding["code"] for finding in failing_suite_audit.get("findings", [])
        }
        if "EXEC003" not in failing_suite_codes:
            raise RuntimeError(
                "A repo whose tests collect successfully but fail at runtime should emit EXEC003"
            )

        missing_pytest_dest = workspace / "missing-pytest"
        shutil.copytree(full_dest, missing_pytest_dest)
        seed_missing_pytest_env(missing_pytest_dest)
        stripped_env = dict(os.environ)
        stripped_env["PATH"] = ""
        missing_pytest_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(missing_pytest_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
            env=stripped_env,
        )
        missing_pytest_codes = {
            finding["code"] for finding in missing_pytest_audit.get("findings", [])
        }
        if "ENV002" not in missing_pytest_codes:
            raise RuntimeError(
                "A Python repo with tests but no usable pytest command should emit ENV002"
            )

        hidden_pending_verification_dest = (
            workspace / "hidden-pending-process-verification"
        )
        shutil.copytree(full_dest, hidden_pending_verification_dest)
        seed_hidden_process_verification(hidden_pending_verification_dest)
        hidden_pending_verification_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(hidden_pending_verification_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        hidden_pending_verification_codes = {
            finding["code"]
            for finding in hidden_pending_verification_audit.get("findings", [])
        }
        if "WFLOW008" not in hidden_pending_verification_codes:
            raise RuntimeError(
                "A repo that hides or contradicts pending_process_verification should emit WFLOW008"
            )

        truthful_pending_verification_dest = (
            workspace / "truthful-pending-process-verification"
        )
        shutil.copytree(full_dest, truthful_pending_verification_dest)
        make_stack_skill_non_placeholder(truthful_pending_verification_dest)
        seed_truthful_process_verification(truthful_pending_verification_dest)
        run_json(
            [sys.executable, str(REGENERATE), str(truthful_pending_verification_dest)],
            ROOT,
        )
        truthful_start_here = (
            truthful_pending_verification_dest / "START-HERE.md"
        ).read_text(encoding="utf-8")
        if (
            "- handoff_status: workflow verification pending" not in truthful_start_here
            or "- pending_process_verification: true" not in truthful_start_here
            or "- repair_follow_on_outcome: clean" not in truthful_start_here
            or "- repair_follow_on_required: false" not in truthful_start_here
            or "- split_child_tickets: none" not in truthful_start_here
        ):
            raise RuntimeError(
                "Restart regeneration should truthfully expose pending process verification without inventing repair follow-on drift"
            )
        if "repair_follow_on_handoff_allowed" in truthful_start_here:
            raise RuntimeError(
                "Restart regeneration should not expose legacy repair_follow_on_handoff_allowed"
            )
        truthful_pending_verification_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(truthful_pending_verification_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        truthful_pending_verification_codes = {
            finding["code"]
            for finding in truthful_pending_verification_audit.get("findings", [])
        }
        if "WFLOW008" in truthful_pending_verification_codes:
            raise RuntimeError(
                "A repo that truthfully surfaces pending_process_verification should not emit WFLOW008"
            )
        if "WFLOW010" in truthful_pending_verification_codes:
            raise RuntimeError(
                "A repo whose restart surfaces match canonical repair-follow-on and verification state should not emit WFLOW010"
            )

        blocked_repair_follow_on_dest = (
            workspace / "restart-surface-repair-follow-on-verification-block"
        )
        shutil.copytree(full_dest, blocked_repair_follow_on_dest)
        make_stack_skill_non_placeholder(blocked_repair_follow_on_dest)
        seed_completed_repair_follow_on_verification_block(
            blocked_repair_follow_on_dest
        )
        run_json(
            [sys.executable, str(REGENERATE), str(blocked_repair_follow_on_dest)],
            ROOT,
        )
        blocked_repair_follow_on_start_here = (
            blocked_repair_follow_on_dest / "START-HERE.md"
        ).read_text(encoding="utf-8")
        if (
            "- handoff_status: repair follow-up required"
            not in blocked_repair_follow_on_start_here
            or "- repair_follow_on_outcome: managed_blocked"
            not in blocked_repair_follow_on_start_here
            or "- repair_follow_on_required: true"
            not in blocked_repair_follow_on_start_here
            or "- repair_follow_on_next_stage: none"
            not in blocked_repair_follow_on_start_here
            or "- repair_follow_on_verification_passed: false"
            not in blocked_repair_follow_on_start_here
        ):
            raise RuntimeError(
                "Restart regeneration should keep repair follow-on pending when verification remains blocked after required stages are complete"
            )
        blocked_repair_follow_on_handoff = (
            blocked_repair_follow_on_dest / ".opencode" / "state" / "latest-handoff.md"
        ).read_text(encoding="utf-8")
        if (
            "- handoff_status: repair follow-up required"
            not in blocked_repair_follow_on_handoff
            or "- repair_follow_on_required: true"
            not in blocked_repair_follow_on_handoff
        ):
            raise RuntimeError(
                "latest-handoff should stay aligned when repair follow-on remains verification-blocked"
            )

        clearable_pending_verification_dest = (
            workspace / "clearable-pending-process-verification"
        )
        shutil.copytree(full_dest, clearable_pending_verification_dest)
        make_stack_skill_non_placeholder(clearable_pending_verification_dest)
        seed_process_verification_clear_deadlock(
            clearable_pending_verification_dest, stale_surfaces=False
        )
        run_json(
            [sys.executable, str(REGENERATE), str(clearable_pending_verification_dest)],
            ROOT,
        )
        clearable_start_here = (
            clearable_pending_verification_dest / "START-HERE.md"
        ).read_text(encoding="utf-8")
        if (
            "- pending_process_verification: true" not in clearable_start_here
            or "- done_but_not_fully_trusted: none" not in clearable_start_here
            or "clear pending_process_verification now that no historical done tickets still require process verification"
            not in clearable_start_here
        ):
            raise RuntimeError(
                "Restart regeneration should expose the direct clear path when pending_process_verification remains true but the affected done-ticket set is empty"
            )
        clearable_pending_verification_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(clearable_pending_verification_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        clearable_pending_verification_codes = {
            finding["code"]
            for finding in clearable_pending_verification_audit.get("findings", [])
        }
        if "WFLOW008" in clearable_pending_verification_codes:
            raise RuntimeError(
                "A repo that truthfully exposes a clearable pending_process_verification state should not emit WFLOW008"
            )
        if "WFLOW010" in clearable_pending_verification_codes:
            raise RuntimeError(
                "A repo whose restart surfaces correctly collapse done_but_not_fully_trusted to none when the affected set is empty should not emit WFLOW010"
            )

        managed_blocked_deadlock_dest = workspace / "managed-blocked-deadlock"
        shutil.copytree(full_dest, managed_blocked_deadlock_dest)
        seed_managed_blocked_deadlock(managed_blocked_deadlock_dest)
        managed_blocked_deadlock_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(managed_blocked_deadlock_dest),
                "--format",
                "json",
            ],
            ROOT,
        )
        managed_blocked_deadlock_codes = {
            finding["code"]
            for finding in managed_blocked_deadlock_audit.get("findings", [])
        }
        if "WFLOW030" not in managed_blocked_deadlock_codes:
            raise RuntimeError(
                "A repo with managed_blocked outcome and only host-only required stages "
                "should emit WFLOW030 (managed-blocked deadlock)"
            )
        managed_blocked_deadlock_manifest = json.loads(
            Path(managed_blocked_deadlock_audit["diagnosis_pack"]["path"])
            .joinpath("manifest.json")
            .read_text(encoding="utf-8")
        )
        if (
            managed_blocked_deadlock_manifest.get("recommended_next_step")
            != "host_intervention_required"
        ):
            raise RuntimeError(
                f"WFLOW030 findings should route recommended_next_step to "
                f"'host_intervention_required', got "
                f"{managed_blocked_deadlock_manifest.get('recommended_next_step')!r}"
            )

        closed_ticket_dependent_dest = workspace / "closed-ticket-dependent-routing"
        shutil.copytree(full_dest, closed_ticket_dependent_dest)
        seed_closed_ticket_with_blocked_dependent(closed_ticket_dependent_dest)
        run_json(
            [sys.executable, str(REGENERATE), str(closed_ticket_dependent_dest)], ROOT
        )
        closed_ticket_start_here = (
            closed_ticket_dependent_dest / "START-HERE.md"
        ).read_text(encoding="utf-8")
        if (
            "Current ticket is already closed. Activate dependent ticket EXEC-DEP and continue that lane instead of trying to mutate"
            not in closed_ticket_start_here
        ):
            raise RuntimeError(
                "Restart regeneration should route a closed current ticket directly to the first blocked dependent lane"
            )
        closed_ticket_handoff = (
            closed_ticket_dependent_dest / ".opencode" / "state" / "latest-handoff.md"
        ).read_text(encoding="utf-8")
        if (
            "Current ticket is already closed. Activate dependent ticket EXEC-DEP and continue that lane instead of trying to mutate"
            not in closed_ticket_handoff
        ):
            raise RuntimeError(
                "latest-handoff should stay aligned with START-HERE for closed-ticket dependent continuation"
            )
        closed_ticket_update = run_generated_tool(
            closed_ticket_dependent_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001"},
        )
        if (
            closed_ticket_update["active_ticket"] != "EXEC-DEP"
            or closed_ticket_update["workflow"]["active_ticket"] != "EXEC-DEP"
        ):
            raise RuntimeError(
                "ticket_update should foreground the first remaining live lane after the active ticket is already closed"
            )
        if (
            closed_ticket_update["workflow"]["stage"] != "planning"
            or closed_ticket_update["workflow"]["status"] != "ready"
        ):
            raise RuntimeError(
                "ticket_update should sync workflow stage/status to the newly foregrounded live ticket after closeout convergence"
            )

        explicit_reverification_dest = (
            workspace / "closed-ticket-explicit-reverification"
        )
        shutil.copytree(full_dest, explicit_reverification_dest)
        seed_closed_ticket_needing_explicit_reverification(explicit_reverification_dest)
        run_json(
            [sys.executable, str(REGENERATE), str(explicit_reverification_dest)], ROOT
        )
        explicit_reverification_start_here = (
            explicit_reverification_dest / "START-HERE.md"
        ).read_text(encoding="utf-8")
        if (
            "- handoff_status: workflow verification pending"
            not in explicit_reverification_start_here
        ):
            raise RuntimeError(
                "Restart regeneration should keep handoff_status verification-pending when the active closed ticket still needs explicit reverification"
            )
        if (
            "run ticket_reverify on SETUP-001 instead of trying to reclaim it"
            not in explicit_reverification_start_here
        ):
            raise RuntimeError(
                "Restart regeneration should surface ticket_reverify as the next move when the active closed ticket still needs explicit trust restoration"
            )
        explicit_reverification_handoff = (
            explicit_reverification_dest / ".opencode" / "state" / "latest-handoff.md"
        ).read_text(encoding="utf-8")
        if (
            "run ticket_reverify on SETUP-001 instead of trying to reclaim it"
            not in explicit_reverification_handoff
        ):
            raise RuntimeError(
                "latest-handoff should stay aligned with START-HERE for explicit closed-ticket trust restoration"
            )

        reopened_reverification_dest = (
            workspace / "reopened-ticket-explicit-reverification"
        )
        shutil.copytree(full_dest, reopened_reverification_dest)
        seed_reopened_ticket_needing_explicit_reverification(
            reopened_reverification_dest
        )
        run_json(
            [sys.executable, str(REGENERATE), str(reopened_reverification_dest)], ROOT
        )
        reopened_reverification_start_here = (
            reopened_reverification_dest / "START-HERE.md"
        ).read_text(encoding="utf-8")
        if (
            "If current inspection disproves it, produce current evidence and run ticket_reverify on SETUP-001"
            not in reopened_reverification_start_here
        ):
            raise RuntimeError(
                "Restart regeneration should surface ticket_reverify as the stale-intake recovery path for reopened historical tickets"
            )
        run_generated_plugin_before(
            reopened_reverification_dest,
            ".opencode/plugins/stage-gate-enforcer.ts",
            "ticket_reverify",
            {
                "ticket_id": "SETUP-001",
                "verification_content": "# Backlog Verification\n\n## Result\n\nPASS\n",
                "reason": "Synthetic stale-intake recovery proof for smoke coverage.",
            },
        )
        reopened_reverification_result = run_generated_tool(
            reopened_reverification_dest,
            ".opencode/tools/ticket_reverify.ts",
            {
                "ticket_id": "SETUP-001",
                "verification_content": "# Backlog Verification\n\n## Result\n\nPASS\n",
                "reason": "Synthetic stale-intake recovery proof for smoke coverage.",
            },
        )
        reopened_reverification_manifest = json.loads(
            (reopened_reverification_dest / "tickets" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        reopened_reverification_ticket = next(
            ticket
            for ticket in reopened_reverification_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        if (
            reopened_reverification_result["verification_state"] != "reverified"
            or reopened_reverification_ticket["status"] != "done"
            or reopened_reverification_ticket["resolution_state"] != "done"
            or reopened_reverification_ticket["verification_state"] != "reverified"
        ):
            raise RuntimeError(
                "ticket_reverify should restore reopened historical tickets back to done/reverified when current evidence disproves the reopened defect"
            )
        reopened_reverification_workflow = json.loads(
            (
                reopened_reverification_dest
                / ".opencode"
                / "state"
                / "workflow-state.json"
            ).read_text(encoding="utf-8")
        )
        if (
            reopened_reverification_workflow["ticket_state"]["SETUP-001"][
                "needs_reverification"
            ]
            is not False
        ):
            raise RuntimeError(
                "ticket_reverify should clear needs_reverification after restoring a reopened historical ticket"
            )

        self_lineage_reverification_dest = (
            workspace / "self-lineage-ticket-reverification"
        )
        shutil.copytree(full_dest, self_lineage_reverification_dest)
        seed_closed_ticket_needing_explicit_reverification(
            self_lineage_reverification_dest
        )
        self_lineage_manifest_path = (
            self_lineage_reverification_dest / "tickets" / "manifest.json"
        )
        self_lineage_manifest = json.loads(
            self_lineage_manifest_path.read_text(encoding="utf-8")
        )
        self_lineage_ticket = next(
            ticket
            for ticket in self_lineage_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        self_lineage_ticket["resolution_state"] = "superseded"
        self_lineage_ticket["source_ticket_id"] = "SETUP-001"
        self_lineage_ticket["source_mode"] = "post_completion_issue"
        self_lineage_ticket["follow_up_ticket_ids"] = ["SETUP-001"]
        self_lineage_manifest_path.write_text(
            json.dumps(self_lineage_manifest, indent=2) + "\n", encoding="utf-8"
        )
        self_lineage_reverification_result = run_generated_tool(
            self_lineage_reverification_dest,
            ".opencode/tools/ticket_reverify.ts",
            {
                "ticket_id": "SETUP-001",
                "verification_content": "# Backlog Verification\n\n## Result\n\nPASS\n",
                "reason": "Synthetic self-lineage corruption repair for smoke coverage.",
            },
        )
        self_lineage_reverification_manifest = json.loads(
            self_lineage_manifest_path.read_text(encoding="utf-8")
        )
        self_lineage_reverified_ticket = next(
            ticket
            for ticket in self_lineage_reverification_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        if (
            self_lineage_reverification_result["verification_state"] != "reverified"
            or self_lineage_reverified_ticket["resolution_state"] != "done"
            or self_lineage_reverified_ticket.get("source_ticket_id") is not None
            or "SETUP-001" in self_lineage_reverified_ticket["follow_up_ticket_ids"]
        ):
            raise RuntimeError(
                "ticket_reverify should normalize self-sourced superseded lineage back to a trusted done ticket"
            )

        executed_reverification_dest = workspace / "executed-ticket-reverify"
        shutil.copytree(full_dest, executed_reverification_dest)
        seed_closed_ticket_needing_explicit_reverification(executed_reverification_dest)
        reverification_result = run_generated_tool(
            executed_reverification_dest,
            ".opencode/tools/ticket_reverify.ts",
            {
                "ticket_id": "SETUP-001",
                "verification_content": "# Backlog Verification\n\n## Result\n\nPASS\n",
                "reason": "Synthetic trust restoration proof for smoke coverage.",
            },
        )
        if (
            reverification_result["ticket_id"] != "SETUP-001"
            or reverification_result["verification_state"] != "reverified"
        ):
            raise RuntimeError(
                "ticket_reverify should return the restored source ticket id and reverified state"
            )
        reverification_manifest = json.loads(
            (executed_reverification_dest / "tickets" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        reverification_ticket = next(
            ticket
            for ticket in reverification_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        if reverification_ticket["verification_state"] != "reverified":
            raise RuntimeError(
                "ticket_reverify should persist reverified verification_state onto the historical source ticket"
            )
        reverification_workflow = json.loads(
            (
                executed_reverification_dest
                / ".opencode"
                / "state"
                / "workflow-state.json"
            ).read_text(encoding="utf-8")
        )
        if (
            reverification_workflow["ticket_state"]["SETUP-001"]["needs_reverification"]
            is not False
        ):
            raise RuntimeError(
                "ticket_reverify should clear needs_reverification in workflow-state"
            )
        reverification_artifact = executed_reverification_dest / str(
            reverification_result["reverification_artifact"]
        )
        if not reverification_artifact.exists():
            raise RuntimeError(
                "ticket_reverify should write the canonical reverification artifact"
            )
        backlog_verification_path = (
            executed_reverification_dest
            / ".opencode"
            / "state"
            / "reviews"
            / "setup-001-review-backlog-verification.md"
        )
        if not backlog_verification_path.exists():
            raise RuntimeError(
                "ticket_reverify should register inline verification content as backlog-verification evidence before restoring trust"
            )

        explicit_reconciliation_dest = (
            workspace / "closed-ticket-explicit-reconciliation"
        )
        shutil.copytree(full_dest, explicit_reconciliation_dest)
        seed_closed_ticket_needing_reconciliation(explicit_reconciliation_dest)
        run_json(
            [sys.executable, str(REGENERATE), str(explicit_reconciliation_dest)], ROOT
        )
        explicit_reconciliation_start_here = (
            explicit_reconciliation_dest / "START-HERE.md"
        ).read_text(encoding="utf-8")
        if (
            "- handoff_status: workflow verification pending"
            not in explicit_reconciliation_start_here
        ):
            raise RuntimeError(
                "Restart regeneration should keep handoff_status verification-pending when the active historical ticket still needs reconciliation"
            )
        if (
            "Use ticket_reconcile with current registered evidence to repair SETUP-001 instead of trying to reopen or reclaim it"
            not in explicit_reconciliation_start_here
        ):
            raise RuntimeError(
                "Restart regeneration should surface ticket_reconcile as the next move when the active historical ticket still has contradictory lineage"
            )
        explicit_reconciliation_handoff = (
            explicit_reconciliation_dest / ".opencode" / "state" / "latest-handoff.md"
        ).read_text(encoding="utf-8")
        if (
            "Use ticket_reconcile with current registered evidence to repair SETUP-001 instead of trying to reopen or reclaim it"
            not in explicit_reconciliation_handoff
        ):
            raise RuntimeError(
                "latest-handoff should stay aligned with START-HERE for explicit historical reconciliation routing"
            )

        executed_reconciliation_dest = workspace / "executed-ticket-reconcile"
        shutil.copytree(full_dest, executed_reconciliation_dest)
        seed_closed_ticket_needing_reconciliation(executed_reconciliation_dest)
        reconcile_manifest_path = (
            executed_reconciliation_dest / "tickets" / "manifest.json"
        )
        reconcile_workflow_path = (
            executed_reconciliation_dest / ".opencode" / "state" / "workflow-state.json"
        )
        reconcile_registry_path = (
            executed_reconciliation_dest
            / ".opencode"
            / "state"
            / "artifacts"
            / "registry.json"
        )
        reconcile_manifest = json.loads(
            reconcile_manifest_path.read_text(encoding="utf-8")
        )
        reconcile_workflow = json.loads(
            reconcile_workflow_path.read_text(encoding="utf-8")
        )
        reconcile_registry = json.loads(
            reconcile_registry_path.read_text(encoding="utf-8")
        )
        reconcile_manifest["tickets"].append(
            {
                "id": "EXEC-RECON-SRC",
                "title": "Synthetic replacement source ticket",
                "wave": 2,
                "lane": "implementation",
                "parallel_safe": True,
                "overlap_risk": "low",
                "stage": "implementation",
                "status": "in_progress",
                "depends_on": [],
                "summary": "Replacement source ticket for reconciliation smoke coverage.",
                "acceptance": ["Replacement source remains active."],
                "decision_blockers": [],
                "artifacts": [],
                "resolution_state": "open",
                "verification_state": "trusted",
                "follow_up_ticket_ids": [],
            }
        )
        reconcile_manifest["tickets"].append(
            {
                "id": "EXEC-RECON-TGT",
                "title": "Synthetic stale follow-up ticket",
                "wave": 3,
                "lane": "implementation",
                "parallel_safe": True,
                "overlap_risk": "low",
                "stage": "planning",
                "status": "ready",
                "depends_on": ["SETUP-001"],
                "summary": "Follow-up ticket with stale lineage for reconciliation smoke coverage.",
                "acceptance": ["Reconciliation succeeds."],
                "decision_blockers": [],
                "artifacts": [],
                "resolution_state": "open",
                "verification_state": "suspect",
                "source_ticket_id": "SETUP-001",
                "source_mode": "post_completion_issue",
                "follow_up_ticket_ids": [],
            }
        )
        source_ticket = next(
            ticket
            for ticket in reconcile_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        source_ticket["follow_up_ticket_ids"] = ["EXEC-RECON-TGT"]
        evidence_rel = (
            ".opencode/state/reviews/setup-001-review-backlog-verification.md"
        )
        evidence_path = executed_reconciliation_dest / evidence_rel
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(
            "# Historical Evidence\n\nCurrent evidence is registered.\n",
            encoding="utf-8",
        )
        evidence_artifact = {
            "kind": "backlog-verification",
            "path": evidence_rel,
            "stage": "review",
            "summary": "Synthetic reconciliation evidence.",
            "created_at": "2026-03-30T00:00:00Z",
            "trust_state": "current",
        }
        source_ticket.setdefault("artifacts", []).append(evidence_artifact)
        reconcile_registry.setdefault("artifacts", []).append(
            {"ticket_id": "SETUP-001", **evidence_artifact}
        )
        reconcile_workflow["ticket_state"]["EXEC-RECON-SRC"] = {
            "approved_plan": False,
            "reopen_count": 0,
            "needs_reverification": False,
        }
        reconcile_workflow["ticket_state"]["EXEC-RECON-TGT"] = {
            "approved_plan": False,
            "reopen_count": 0,
            "needs_reverification": False,
        }
        reconcile_manifest_path.write_text(
            json.dumps(reconcile_manifest, indent=2) + "\n", encoding="utf-8"
        )
        reconcile_workflow_path.write_text(
            json.dumps(reconcile_workflow, indent=2) + "\n", encoding="utf-8"
        )
        reconcile_registry_path.write_text(
            json.dumps(reconcile_registry, indent=2) + "\n", encoding="utf-8"
        )
        reconciliation_result = run_generated_tool(
            executed_reconciliation_dest,
            ".opencode/tools/ticket_reconcile.ts",
            {
                "source_ticket_id": "SETUP-001",
                "target_ticket_id": "EXEC-RECON-TGT",
                "replacement_source_ticket_id": "EXEC-RECON-SRC",
                "replacement_source_mode": "split_scope",
                "evidence_artifact_path": evidence_rel,
                "reason": "Synthetic lineage correction proof for smoke coverage.",
                "remove_dependency_on_source": True,
                "activate_source": True,
            },
        )
        if (
            reconciliation_result["replacement_source_ticket_id"] != "EXEC-RECON-SRC"
            or reconciliation_result["active_ticket"] != "EXEC-RECON-SRC"
        ):
            raise RuntimeError(
                "ticket_reconcile should report and activate the replacement source ticket when requested"
            )
        reconciled_manifest = json.loads(
            reconcile_manifest_path.read_text(encoding="utf-8")
        )
        reconciled_target = next(
            ticket
            for ticket in reconciled_manifest["tickets"]
            if ticket["id"] == "EXEC-RECON-TGT"
        )
        if reconciled_target["source_ticket_id"] != "EXEC-RECON-SRC":
            raise RuntimeError(
                "ticket_reconcile should rewrite the target source_ticket_id to the replacement source"
            )
        if "SETUP-001" in reconciled_target["depends_on"]:
            raise RuntimeError(
                "ticket_reconcile should remove contradictory dependencies on the stale canonical source when requested"
            )
        if reconciled_manifest["active_ticket"] != "EXEC-RECON-SRC":
            raise RuntimeError(
                "ticket_reconcile should persist the activated replacement source into manifest active_ticket"
            )
        reconciliation_artifact = executed_reconciliation_dest / str(
            reconciliation_result["reconciliation_artifact"]
        )
        if not reconciliation_artifact.exists():
            raise RuntimeError(
                "ticket_reconcile should write the canonical reconciliation artifact"
            )
        historical_supersede_reconcile_dest = (
            workspace / "executed-ticket-reconcile-historical-supersede"
        )
        shutil.copytree(full_dest, historical_supersede_reconcile_dest)
        historical_manifest_path = (
            historical_supersede_reconcile_dest / "tickets" / "manifest.json"
        )
        historical_workflow_path = (
            historical_supersede_reconcile_dest
            / ".opencode"
            / "state"
            / "workflow-state.json"
        )
        historical_registry_path = (
            historical_supersede_reconcile_dest
            / ".opencode"
            / "state"
            / "artifacts"
            / "registry.json"
        )
        historical_manifest = json.loads(historical_manifest_path.read_text(encoding="utf-8"))
        historical_workflow = json.loads(historical_workflow_path.read_text(encoding="utf-8"))
        historical_source = historical_manifest["tickets"][0]
        historical_source["stage"] = "closeout"
        historical_source["status"] = "done"
        historical_source["resolution_state"] = "done"
        historical_source["verification_state"] = "reverified"
        historical_target = {
            "id": "EXEC-RECON-HIST",
            "title": "Stale split child",
            "wave": historical_source["wave"] + 1,
            "lane": "execution",
            "parallel_safe": False,
            "overlap_risk": "low",
            "stage": "planning",
            "status": "todo",
            "depends_on": [],
            "summary": "Synthetic stale split child for historical supersede reconciliation coverage.",
            "acceptance": ["Historical split child can be superseded with current evidence."],
            "decision_blockers": [],
            "artifacts": [],
            "resolution_state": "open",
            "verification_state": "suspect",
            "source_ticket_id": historical_source["id"],
            "follow_up_ticket_ids": [],
            "source_mode": "split_scope",
            "split_kind": "parallel_independent",
        }
        historical_manifest["tickets"].append(historical_target)
        historical_source["follow_up_ticket_ids"] = ["EXEC-RECON-HIST"]
        historical_evidence_rel = ".opencode/state/reviews/setup-001-review-backlog-verification.md"
        register_current_ticket_artifact(
            historical_supersede_reconcile_dest,
            ticket_id=historical_source["id"],
            kind="backlog-verification",
            stage="review",
            relative_path=historical_evidence_rel,
            summary="Synthetic historical supersede reconciliation evidence.",
            content="# Historical Evidence\n\nCurrent evidence is registered.\n",
        )
        historical_workflow["ticket_state"]["EXEC-RECON-HIST"] = {
            "approved_plan": False,
            "reopen_count": 0,
            "needs_reverification": False,
        }
        historical_manifest_path.write_text(
            json.dumps(historical_manifest, indent=2) + "\n", encoding="utf-8"
        )
        historical_workflow_path.write_text(
            json.dumps(historical_workflow, indent=2) + "\n", encoding="utf-8"
        )
        historical_reconciliation_result = run_generated_tool(
            historical_supersede_reconcile_dest,
            ".opencode/tools/ticket_reconcile.ts",
            {
                "source_ticket_id": historical_source["id"],
                "target_ticket_id": "EXEC-RECON-HIST",
                "replacement_source_ticket_id": historical_source["id"],
                "replacement_source_mode": "split_scope",
                "evidence_artifact_path": historical_evidence_rel,
                "reason": "Synthetic stale split child should be superseded from a completed historical source ticket.",
                "supersede_target": True,
            },
        )
        if historical_reconciliation_result["target_ticket_id"] != "EXEC-RECON-HIST":
            raise RuntimeError(
                "ticket_reconcile should report the superseded stale historical split child"
            )
        historical_reconciled_manifest = json.loads(
            historical_manifest_path.read_text(encoding="utf-8")
        )
        historical_reconciled_target = next(
            ticket
            for ticket in historical_reconciled_manifest["tickets"]
            if ticket["id"] == "EXEC-RECON-HIST"
        )
        historical_reconciled_source = next(
            ticket
            for ticket in historical_reconciled_manifest["tickets"]
            if ticket["id"] == historical_source["id"]
        )
        if (
            historical_reconciled_target["resolution_state"] != "superseded"
            or historical_reconciled_target["status"] != "done"
            or historical_reconciled_target["verification_state"] != "reverified"
        ):
            raise RuntimeError(
                "ticket_reconcile should allow superseding stale split_scope children from a completed historical source when supersede_target is true"
            )
        if "EXEC-RECON-HIST" in historical_reconciled_source.get("follow_up_ticket_ids", []):
            raise RuntimeError(
                "ticket_reconcile should remove superseded stale children from the historical source follow_up_ticket_ids list"
            )

        default_dependency_reconcile_dest = (
            workspace / "executed-ticket-reconcile-default-dependency"
        )
        shutil.copytree(full_dest, default_dependency_reconcile_dest)
        default_reconcile_manifest_path = (
            default_dependency_reconcile_dest / "tickets" / "manifest.json"
        )
        default_reconcile_workflow_path = (
            default_dependency_reconcile_dest
            / ".opencode"
            / "state"
            / "workflow-state.json"
        )
        default_reconcile_registry_path = (
            default_dependency_reconcile_dest
            / ".opencode"
            / "state"
            / "artifacts"
            / "registry.json"
        )
        default_reconcile_manifest = json.loads(
            default_reconcile_manifest_path.read_text(encoding="utf-8")
        )
        default_reconcile_workflow = json.loads(
            default_reconcile_workflow_path.read_text(encoding="utf-8")
        )
        default_reconcile_manifest["tickets"].append(
            {
                "id": "EXEC-RECON-SRC",
                "title": "Synthetic replacement source ticket",
                "wave": 2,
                "lane": "implementation",
                "parallel_safe": True,
                "overlap_risk": "low",
                "stage": "implementation",
                "status": "in_progress",
                "depends_on": [],
                "summary": "Replacement source ticket for default dependency smoke coverage.",
                "acceptance": ["Replacement source remains active."],
                "decision_blockers": [],
                "artifacts": [],
                "resolution_state": "open",
                "verification_state": "trusted",
                "follow_up_ticket_ids": [],
            }
        )
        default_reconcile_manifest["tickets"].append(
            {
                "id": "EXEC-RECON-TGT",
                "title": "Synthetic stale follow-up ticket",
                "wave": 3,
                "lane": "implementation",
                "parallel_safe": True,
                "overlap_risk": "low",
                "stage": "planning",
                "status": "ready",
                "depends_on": ["SETUP-001"],
                "summary": "Follow-up ticket that keeps the stale dependency unless explicitly removed.",
                "acceptance": [
                    "Reconciliation succeeds without removing dependency by default."
                ],
                "decision_blockers": [],
                "artifacts": [],
                "resolution_state": "open",
                "verification_state": "suspect",
                "source_ticket_id": "SETUP-001",
                "source_mode": "post_completion_issue",
                "follow_up_ticket_ids": [],
            }
        )
        default_source_ticket = next(
            ticket
            for ticket in default_reconcile_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        default_source_ticket["follow_up_ticket_ids"] = ["EXEC-RECON-TGT"]
        default_reconcile_workflow["ticket_state"]["EXEC-RECON-SRC"] = {
            "approved_plan": False,
            "reopen_count": 0,
            "needs_reverification": False,
        }
        default_reconcile_workflow["ticket_state"]["EXEC-RECON-TGT"] = {
            "approved_plan": False,
            "reopen_count": 0,
            "needs_reverification": False,
        }
        default_reconcile_manifest_path.write_text(
            json.dumps(default_reconcile_manifest, indent=2) + "\n", encoding="utf-8"
        )
        default_reconcile_workflow_path.write_text(
            json.dumps(default_reconcile_workflow, indent=2) + "\n", encoding="utf-8"
        )
        default_reconcile_registry_path.write_text(
            json.dumps(
                json.loads(default_reconcile_registry_path.read_text(encoding="utf-8")),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        default_evidence_rel = (
            ".opencode/state/reviews/setup-001-review-default-dependency.md"
        )
        register_current_ticket_artifact(
            default_dependency_reconcile_dest,
            ticket_id="SETUP-001",
            kind="backlog-verification",
            stage="review",
            relative_path=default_evidence_rel,
            summary="Synthetic reconciliation evidence that should not remove the source dependency by default.",
            content="# Historical Evidence\n\nCurrent evidence is registered.\n",
        )
        run_generated_tool(
            default_dependency_reconcile_dest,
            ".opencode/tools/ticket_reconcile.ts",
            {
                "source_ticket_id": "SETUP-001",
                "target_ticket_id": "EXEC-RECON-TGT",
                "replacement_source_ticket_id": "EXEC-RECON-SRC",
                "replacement_source_mode": "split_scope",
                "evidence_artifact_path": default_evidence_rel,
                "reason": "Synthetic lineage correction without explicit dependency removal.",
            },
        )
        default_reconciled_manifest = json.loads(
            default_reconcile_manifest_path.read_text(encoding="utf-8")
        )
        default_reconciled_target = next(
            ticket
            for ticket in default_reconciled_manifest["tickets"]
            if ticket["id"] == "EXEC-RECON-TGT"
        )
        if "SETUP-001" not in default_reconciled_target["depends_on"]:
            raise RuntimeError(
                "ticket_reconcile should leave the source dependency intact unless remove_dependency_on_source is explicitly true"
            )

        reversed_reconcile_error = run_generated_tool_error(
            default_dependency_reconcile_dest,
            ".opencode/tools/ticket_reconcile.ts",
            {
                "source_ticket_id": "SETUP-001",
                "target_ticket_id": "EXEC-RECON-SRC",
                "replacement_source_ticket_id": "EXEC-RECON-SRC",
                "replacement_source_mode": "split_scope",
                "evidence_artifact_path": default_evidence_rel,
                "reason": "Synthetic reversed reconciliation arguments should be rejected.",
            },
        )
        if "target_ticket_id cannot equal replacement_source_ticket_id" not in reversed_reconcile_error:
            raise RuntimeError(
                "ticket_reconcile should reject reversed source/target calls where the target is also named as the replacement source"
            )

        unrelated_evidence_reconcile_dest = (
            workspace / "executed-ticket-reconcile-unrelated-evidence"
        )
        shutil.copytree(full_dest, unrelated_evidence_reconcile_dest)
        unrelated_reconcile_manifest_path = (
            unrelated_evidence_reconcile_dest / "tickets" / "manifest.json"
        )
        unrelated_reconcile_workflow_path = (
            unrelated_evidence_reconcile_dest
            / ".opencode"
            / "state"
            / "workflow-state.json"
        )
        unrelated_reconcile_manifest = json.loads(
            unrelated_reconcile_manifest_path.read_text(encoding="utf-8")
        )
        unrelated_reconcile_workflow = json.loads(
            unrelated_reconcile_workflow_path.read_text(encoding="utf-8")
        )
        unrelated_reconcile_manifest["tickets"].extend(
            [
                {
                    "id": "EXEC-RECON-SRC",
                    "title": "Synthetic replacement source ticket",
                    "wave": 2,
                    "lane": "implementation",
                    "parallel_safe": True,
                    "overlap_risk": "low",
                    "stage": "implementation",
                    "status": "in_progress",
                    "depends_on": [],
                    "summary": "Replacement source ticket for unrelated evidence smoke coverage.",
                    "acceptance": ["Replacement source remains active."],
                    "decision_blockers": [],
                    "artifacts": [],
                    "resolution_state": "open",
                    "verification_state": "trusted",
                    "follow_up_ticket_ids": [],
                },
                {
                    "id": "EXEC-RECON-TGT",
                    "title": "Synthetic stale follow-up ticket",
                    "wave": 3,
                    "lane": "implementation",
                    "parallel_safe": True,
                    "overlap_risk": "low",
                    "stage": "planning",
                    "status": "ready",
                    "depends_on": ["SETUP-001"],
                    "summary": "Follow-up ticket whose evidence must not come from an unrelated ticket.",
                    "acceptance": ["Reconciliation rejects unrelated evidence."],
                    "decision_blockers": [],
                    "artifacts": [],
                    "resolution_state": "open",
                    "verification_state": "suspect",
                    "source_ticket_id": "SETUP-001",
                    "source_mode": "post_completion_issue",
                    "follow_up_ticket_ids": [],
                },
                {
                    "id": "EXEC-OTHER-EVIDENCE",
                    "title": "Synthetic unrelated evidence owner",
                    "wave": 4,
                    "lane": "review",
                    "parallel_safe": True,
                    "overlap_risk": "low",
                    "stage": "review",
                    "status": "done",
                    "depends_on": [],
                    "summary": "Owns an unrelated evidence artifact.",
                    "acceptance": ["Evidence stays unrelated to reconciliation."],
                    "decision_blockers": [],
                    "artifacts": [],
                    "resolution_state": "done",
                    "verification_state": "reverified",
                    "follow_up_ticket_ids": [],
                },
            ]
        )
        unrelated_source_ticket = next(
            ticket
            for ticket in unrelated_reconcile_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        unrelated_source_ticket["follow_up_ticket_ids"] = ["EXEC-RECON-TGT"]
        unrelated_reconcile_workflow["ticket_state"]["EXEC-RECON-SRC"] = {
            "approved_plan": False,
            "reopen_count": 0,
            "needs_reverification": False,
        }
        unrelated_reconcile_workflow["ticket_state"]["EXEC-RECON-TGT"] = {
            "approved_plan": False,
            "reopen_count": 0,
            "needs_reverification": False,
        }
        unrelated_reconcile_workflow["ticket_state"]["EXEC-OTHER-EVIDENCE"] = {
            "approved_plan": False,
            "reopen_count": 0,
            "needs_reverification": False,
        }
        unrelated_reconcile_manifest_path.write_text(
            json.dumps(unrelated_reconcile_manifest, indent=2) + "\n", encoding="utf-8"
        )
        unrelated_reconcile_workflow_path.write_text(
            json.dumps(unrelated_reconcile_workflow, indent=2) + "\n", encoding="utf-8"
        )
        unrelated_evidence_rel = ".opencode/state/reviews/unrelated-ticket-review.md"
        register_current_ticket_artifact(
            unrelated_evidence_reconcile_dest,
            ticket_id="EXEC-OTHER-EVIDENCE",
            kind="review-note",
            stage="review",
            relative_path=unrelated_evidence_rel,
            summary="Unrelated evidence should not satisfy reconciliation requirements.",
            content="# Unrelated Evidence\n\nThis artifact belongs to another ticket.\n",
        )
        unrelated_reconcile_error = run_generated_tool_error(
            unrelated_evidence_reconcile_dest,
            ".opencode/tools/ticket_reconcile.ts",
            {
                "source_ticket_id": "SETUP-001",
                "target_ticket_id": "EXEC-RECON-TGT",
                "replacement_source_ticket_id": "EXEC-RECON-SRC",
                "replacement_source_mode": "split_scope",
                "evidence_artifact_path": unrelated_evidence_rel,
                "reason": "Synthetic attempt to use unrelated current registry evidence.",
            },
        )
        if (
            "No current registered evidence artifact exists"
            not in unrelated_reconcile_error
        ):
            raise RuntimeError(
                "ticket_reconcile should reject unrelated current registry evidence that does not belong to the source, target, or replacement source ticket"
            )

        executed_split_scope_dest = workspace / "executed-ticket-create-split-scope"
        shutil.copytree(full_dest, executed_split_scope_dest)
        split_scope_result = run_generated_tool(
            executed_split_scope_dest,
            ".opencode/tools/ticket_create.ts",
            {
                "id": "EXEC-SPLIT",
                "title": "Synthetic split-scope child",
                "lane": "implementation",
                "wave": 2,
                "summary": "Split child created through the generated ticket_create tool.",
                "acceptance": ["Child scope is tracked independently."],
                "source_ticket_id": "SETUP-001",
                "source_mode": "split_scope",
                "split_kind": "sequential_dependent",
            },
        )
        if (
            split_scope_result["created_ticket"] != "EXEC-SPLIT"
            or split_scope_result["source_mode"] != "split_scope"
            or split_scope_result["split_kind"] != "sequential_dependent"
        ):
            raise RuntimeError(
                "ticket_create should report the created split-scope child, source_mode, and split_kind"
            )
        split_scope_manifest = json.loads(
            (executed_split_scope_dest / "tickets" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        split_source = next(
            ticket
            for ticket in split_scope_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        split_child = next(
            ticket
            for ticket in split_scope_manifest["tickets"]
            if ticket["id"] == "EXEC-SPLIT"
        )
        if split_scope_manifest["active_ticket"] != "SETUP-001":
            raise RuntimeError(
                "ticket_create should keep sequential split children behind the active parent at creation time"
            )
        if (
            split_child["source_ticket_id"] != "SETUP-001"
            or split_child["source_mode"] != "split_scope"
            or split_child.get("split_kind") != "sequential_dependent"
        ):
            raise RuntimeError(
                "ticket_create should persist split-scope lineage and split_kind on the created child"
            )
        if "EXEC-SPLIT" not in split_source["follow_up_ticket_ids"]:
            raise RuntimeError(
                "ticket_create should append split-scope children to the source follow_up_ticket_ids"
            )
        if not any(
            "must complete its parent-owned work before child ticket EXEC-SPLIT may be foregrounded."
            in item
            for item in split_source["decision_blockers"]
        ):
            raise RuntimeError(
                "ticket_create should record sequential split guidance on the source ticket"
            )

        blocked_parent_split_dest = workspace / "executed-ticket-create-blocked-parent-split"
        shutil.copytree(full_dest, blocked_parent_split_dest)
        blocked_parent_manifest_path = blocked_parent_split_dest / "tickets" / "manifest.json"
        blocked_parent_manifest = json.loads(
            blocked_parent_manifest_path.read_text(encoding="utf-8")
        )
        blocked_parent_source = next(
            ticket
            for ticket in blocked_parent_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        blocked_parent_source["stage"] = "implementation"
        blocked_parent_source["status"] = "blocked"
        blocked_parent_source["resolution_state"] = "open"
        blocked_parent_manifest_path.write_text(
            json.dumps(blocked_parent_manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        run_generated_tool(
            blocked_parent_split_dest,
            ".opencode/tools/ticket_create.ts",
            {
                "id": "EXEC-SPLIT-BLOCKED-PARENT",
                "title": "Synthetic split child from blocked parent",
                "lane": "implementation",
                "wave": 2,
                "summary": "Split child created from a blocked parent through the generated ticket_create tool.",
                "acceptance": ["Parent status is normalized back to an open lifecycle state."],
                "source_ticket_id": "SETUP-001",
                "source_mode": "split_scope",
                "split_kind": "sequential_dependent",
            },
        )
        blocked_parent_split_manifest = json.loads(
            blocked_parent_manifest_path.read_text(encoding="utf-8")
        )
        blocked_parent_source = next(
            ticket
            for ticket in blocked_parent_split_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        if blocked_parent_source["status"] != "in_progress":
            raise RuntimeError(
                "ticket_create should normalize blocked split parents back to their stage-default open status"
            )

        split_scope_dependency_error = run_generated_tool_error(
            executed_split_scope_dest,
            ".opencode/tools/ticket_create.ts",
            {
                "id": "EXEC-SPLIT-BAD",
                "title": "Synthetic invalid split-scope child",
                "lane": "implementation",
                "wave": 2,
                "summary": "Invalid split child that also blocks on its source.",
                "acceptance": ["This ticket should never be created."],
                "source_ticket_id": "SETUP-001",
                "source_mode": "split_scope",
                "split_kind": "sequential_dependent",
                "depends_on": ["SETUP-001"],
            },
        )
        if "as both source_ticket_id and depends_on" not in split_scope_dependency_error:
            raise RuntimeError(
                "ticket_create should reject tickets that name the same parent in both source_ticket_id and depends_on"
            )

        executed_process_verification_dest = (
            workspace / "executed-ticket-create-process-verification"
        )
        shutil.copytree(full_dest, executed_process_verification_dest)
        seed_closed_ticket_needing_explicit_reverification(
            executed_process_verification_dest
        )
        process_manifest_path = (
            executed_process_verification_dest / "tickets" / "manifest.json"
        )
        process_workflow_path = (
            executed_process_verification_dest
            / ".opencode"
            / "state"
            / "workflow-state.json"
        )
        process_manifest = json.loads(process_manifest_path.read_text(encoding="utf-8"))
        process_workflow = json.loads(process_workflow_path.read_text(encoding="utf-8"))
        process_workflow["pending_process_verification"] = True
        process_manifest_path.write_text(
            json.dumps(process_manifest, indent=2) + "\n", encoding="utf-8"
        )
        process_workflow_path.write_text(
            json.dumps(process_workflow, indent=2) + "\n", encoding="utf-8"
        )
        process_evidence_rel = (
            ".opencode/state/reviews/setup-001-review-backlog-verification.md"
        )
        register_current_ticket_artifact(
            executed_process_verification_dest,
            ticket_id="SETUP-001",
            kind="backlog-verification",
            stage="review",
            relative_path=process_evidence_rel,
            summary="Synthetic process-verification evidence.",
            content="# Backlog Verification\n\nProcess verification evidence.\n",
        )
        process_verification_result = run_generated_tool(
            executed_process_verification_dest,
            ".opencode/tools/ticket_create.ts",
            {
                "id": "EXEC-PV",
                "title": "Synthetic process-verification follow-up",
                "lane": "workflow",
                "wave": 3,
                "summary": "Process verification follow-up created through ticket_create.",
                "acceptance": ["Process verification follow-up is tracked."],
                "source_ticket_id": "SETUP-001",
                "source_mode": "process_verification",
                "evidence_artifact_path": process_evidence_rel,
                "activate": True,
            },
        )
        if (
            process_verification_result["created_ticket"] != "EXEC-PV"
            or process_verification_result["source_mode"] != "process_verification"
        ):
            raise RuntimeError(
                "ticket_create should report process_verification follow-up creation correctly"
            )
        process_verification_manifest = json.loads(
            process_manifest_path.read_text(encoding="utf-8")
        )
        process_follow_up = next(
            ticket
            for ticket in process_verification_manifest["tickets"]
            if ticket["id"] == "EXEC-PV"
        )
        if (
            process_follow_up["source_ticket_id"] != "SETUP-001"
            or process_follow_up["source_mode"] != "process_verification"
        ):
            raise RuntimeError(
                "ticket_create should persist process-verification lineage and mode on the created follow-up"
            )
        if process_verification_manifest["active_ticket"] != "EXEC-PV":
            raise RuntimeError(
                "ticket_create should activate the process-verification follow-up when requested"
            )

        executed_issue_intake_dest = workspace / "executed-issue-intake"
        shutil.copytree(full_dest, executed_issue_intake_dest)
        seed_closed_ticket_needing_explicit_reverification(executed_issue_intake_dest)
        rollback_evidence_rel = (
            ".opencode/state/reviews/setup-001-review-existing-evidence.md"
        )
        register_current_ticket_artifact(
            executed_issue_intake_dest,
            ticket_id="SETUP-001",
            kind="backlog-verification",
            stage="review",
            relative_path=rollback_evidence_rel,
            summary="Synthetic issue-intake evidence.",
            content="# Existing Evidence\n\nRollback-required defect proof.\n",
        )
        issue_intake_result = run_generated_tool(
            executed_issue_intake_dest,
            ".opencode/tools/issue_intake.ts",
            {
                "source_ticket_id": "SETUP-001",
                "defect_class": "regression",
                "acceptance_broken": False,
                "scope_changed": True,
                "rollback_required": True,
                "evidence_artifact_path": rollback_evidence_rel,
                "follow_up_id": "EXEC-ROLLBACK",
                "follow_up_title": "Synthetic rollback follow-up",
                "follow_up_lane": "workflow",
                "follow_up_wave": 4,
                "follow_up_summary": "Rollback-required follow-up created through issue_intake.",
                "follow_up_acceptance": ["Rollback work is queued explicitly."],
            },
        )
        if (
            issue_intake_result["outcome"] != "rollback_required"
            or issue_intake_result["created_ticket_id"] != "EXEC-ROLLBACK"
        ):
            raise RuntimeError(
                "issue_intake should route rollback-required defects into an explicit follow-up ticket"
            )
        issue_manifest = json.loads(
            (executed_issue_intake_dest / "tickets" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        issue_workflow = json.loads(
            (
                executed_issue_intake_dest
                / ".opencode"
                / "state"
                / "workflow-state.json"
            ).read_text(encoding="utf-8")
        )
        issue_source = next(
            ticket
            for ticket in issue_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        issue_follow_up = next(
            ticket
            for ticket in issue_manifest["tickets"]
            if ticket["id"] == "EXEC-ROLLBACK"
        )
        if issue_source["verification_state"] != "invalidated":
            raise RuntimeError(
                "issue_intake should invalidate the source ticket when rollback is required"
            )
        if (
            issue_workflow["ticket_state"]["SETUP-001"]["needs_reverification"]
            is not True
        ):
            raise RuntimeError(
                "issue_intake should mark the source ticket as needing reverification when rollback is required"
            )
        if issue_manifest["active_ticket"] != "EXEC-ROLLBACK":
            raise RuntimeError(
                "issue_intake should foreground the created rollback follow-up ticket"
            )
        if (
            issue_follow_up["source_ticket_id"] != "SETUP-001"
            or issue_follow_up["source_mode"] != "post_completion_issue"
        ):
            raise RuntimeError(
                "issue_intake should create rollback follow-up tickets with post_completion_issue lineage"
            )
        issue_artifact = executed_issue_intake_dest / str(
            issue_intake_result["issue_artifact"]
        )
        if not issue_artifact.exists():
            raise RuntimeError(
                "issue_intake should write the canonical issue-discovery artifact"
            )

        executed_lookup_prebootstrap_dest = (
            workspace / "executed-ticket-lookup-prebootstrap"
        )
        shutil.copytree(full_dest, executed_lookup_prebootstrap_dest)
        lookup_prebootstrap = run_generated_tool(
            executed_lookup_prebootstrap_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if lookup_prebootstrap["bootstrap"]["status"] != "missing":
            raise RuntimeError(
                "ticket_lookup should expose the missing bootstrap state on a fresh scaffold"
            )
        prebootstrap_guidance = lookup_prebootstrap["transition_guidance"]
        if (
            prebootstrap_guidance["next_action_tool"] != "environment_bootstrap"
            or prebootstrap_guidance["next_action_kind"] != "run_tool"
        ):
            raise RuntimeError(
                "ticket_lookup should route fresh scaffolds through environment_bootstrap before lifecycle execution"
            )

        executed_lifecycle_dest = workspace / "executed-ordinary-lifecycle"
        shutil.copytree(full_dest, executed_lifecycle_dest)
        seed_ready_bootstrap(executed_lifecycle_dest)
        lookup_without_plan = run_generated_tool(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if lookup_without_plan["bootstrap"]["status"] != "ready":
            raise RuntimeError(
                "ticket_lookup should reflect a ready bootstrap state after bootstrap proof is seeded"
            )
        if (
            lookup_without_plan["transition_guidance"]["next_action_tool"]
            != "artifact_write"
        ):
            raise RuntimeError(
                "ticket_lookup should require a planning artifact before plan_review on a ready planning ticket"
            )
        prebootstrap_claim_result = run_generated_tool(
            executed_lookup_prebootstrap_dest,
            ".opencode/tools/ticket_claim.ts",
            {
                "ticket_id": "SETUP-001",
                "owner_agent": "smoke-bootstrap",
                "allowed_paths": ["docs"],
                "write_lock": True,
            },
        )
        if (
            prebootstrap_claim_result["claimed"] is not True
            or prebootstrap_claim_result["lease"]["owner_agent"] != "smoke-bootstrap"
        ):
            raise RuntimeError(
                "ticket_claim should allow the wave-0 bootstrap ticket to claim a pre-bootstrap write lease"
            )
        prebootstrap_release_result = run_generated_tool(
            executed_lookup_prebootstrap_dest,
            ".opencode/tools/ticket_release.ts",
            {"ticket_id": "SETUP-001", "owner_agent": "smoke-bootstrap"},
        )
        if prebootstrap_release_result["released"]["ticket_id"] != "SETUP-001":
            raise RuntimeError(
                "ticket_release should release the bootstrap lease after the pre-bootstrap claim probe"
            )
        process_clearable_dest = workspace / "executed-process-clearable"
        shutil.copytree(full_dest, process_clearable_dest)
        seed_ready_bootstrap(process_clearable_dest)
        process_manifest_path = process_clearable_dest / "tickets" / "manifest.json"
        process_workflow_path = (
            process_clearable_dest / ".opencode" / "state" / "workflow-state.json"
        )
        process_manifest = json.loads(
            process_manifest_path.read_text(encoding="utf-8")
        )
        process_workflow = json.loads(
            process_workflow_path.read_text(encoding="utf-8")
        )
        process_ticket = next(
            ticket
            for ticket in process_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        process_ticket["stage"] = "closeout"
        process_ticket["status"] = "done"
        process_ticket["resolution_state"] = "done"
        process_ticket["verification_state"] = "trusted"
        process_manifest["active_ticket"] = "SETUP-001"
        process_manifest["tickets"].append(
            {
                "id": "PROC-001",
                "title": "Synthetic writable follow-up",
                "wave": 99,
                "lane": "workflow",
                "parallel_safe": False,
                "overlap_risk": "low",
                "stage": "planning",
                "status": "todo",
                "depends_on": [],
                "summary": "Synthetic open ticket used to carry global workflow updates.",
                "acceptance": [
                    "The team leader can foreground this ticket to carry a workflow-state-only mutation."
                ],
                "decision_blockers": [],
                "artifacts": [],
                "resolution_state": "open",
                "verification_state": "suspect",
                "follow_up_ticket_ids": [],
            }
        )
        process_workflow["active_ticket"] = "SETUP-001"
        process_workflow["stage"] = "closeout"
        process_workflow["status"] = "done"
        process_workflow["approved_plan"] = True
        process_workflow["pending_process_verification"] = True
        process_workflow["process_last_changed_at"] = "2026-03-30T00:00:00Z"
        process_workflow.setdefault("ticket_state", {})
        process_workflow["ticket_state"]["SETUP-001"] = {
            "approved_plan": True,
            "reopen_count": 0,
            "needs_reverification": False,
        }
        process_workflow["ticket_state"]["PROC-001"] = {
            "approved_plan": False,
            "reopen_count": 0,
            "needs_reverification": False,
        }
        process_manifest_path.write_text(
            json.dumps(process_manifest, indent=2) + "\n", encoding="utf-8"
        )
        process_workflow_path.write_text(
            json.dumps(process_workflow, indent=2) + "\n", encoding="utf-8"
        )
        register_current_ticket_artifact(
            process_clearable_dest,
            ticket_id="SETUP-001",
            kind="smoke-test",
            stage="smoke-test",
            relative_path=".opencode/state/artifacts/history/setup-001/smoke-test/2026-04-01T00-00-00Z-synthetic-smoke.md",
            summary="Synthetic smoke proof after the process change.",
            content="# Smoke Test\n\n## Command\n\n`pytest -q`\n\n## Raw Output\n\n```text\n1 passed in 0.01s\n```\n\nOverall Result: PASS\n",
            created_at="2026-04-01T00:00:00Z",
        )
        process_clearable_lookup = run_generated_tool(
            process_clearable_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if process_clearable_lookup["process_verification"]["clearable_now"] is not True:
            raise RuntimeError(
                "ticket_lookup should report clearable_now when pending_process_verification is true and no done tickets remain affected"
            )
        process_clearable_guidance = process_clearable_lookup["transition_guidance"]
        if process_clearable_guidance["next_action_tool"] != "ticket_update":
            raise RuntimeError(
                "ticket_lookup should route clearable process verification through ticket_update even when the active ticket is already closed"
            )
        if process_clearable_guidance["recommended_ticket_update"] != {
            "ticket_id": "PROC-001",
            "activate": True,
            "pending_process_verification": False,
        }:
            raise RuntimeError(
                "ticket_lookup should foreground an open writable ticket when clearing pending_process_verification from a closed foreground ticket"
            )
        if "Foreground open ticket PROC-001" not in process_clearable_guidance[
            "recommended_action"
        ]:
            raise RuntimeError(
                "ticket_lookup should explain that the team leader must switch to an open ticket before clearing pending_process_verification"
            )
        process_clearable_open_dest = workspace / "executed-process-clearable-open"
        shutil.copytree(process_clearable_dest, process_clearable_open_dest)
        process_clearable_open_manifest_path = (
            process_clearable_open_dest / "tickets" / "manifest.json"
        )
        process_clearable_open_workflow_path = (
            process_clearable_open_dest / ".opencode" / "state" / "workflow-state.json"
        )
        process_clearable_open_manifest = json.loads(
            process_clearable_open_manifest_path.read_text(encoding="utf-8")
        )
        process_clearable_open_workflow = json.loads(
            process_clearable_open_workflow_path.read_text(encoding="utf-8")
        )
        process_clearable_open_manifest["active_ticket"] = "PROC-001"
        process_clearable_open_workflow["active_ticket"] = "PROC-001"
        process_clearable_open_workflow["stage"] = "planning"
        process_clearable_open_workflow["status"] = "todo"
        process_clearable_open_manifest_path.write_text(
            json.dumps(process_clearable_open_manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        process_clearable_open_workflow_path.write_text(
            json.dumps(process_clearable_open_workflow, indent=2) + "\n",
            encoding="utf-8",
        )
        process_clearable_open_lookup = run_generated_tool(
            process_clearable_open_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if process_clearable_open_lookup["process_verification"]["clearable_now"] is not True:
            raise RuntimeError(
                "ticket_lookup should keep reporting clearable_now when the workflow has already rotated to an open writable ticket"
            )
        process_clearable_open_guidance = process_clearable_open_lookup[
            "transition_guidance"
        ]
        if process_clearable_open_guidance["next_action_tool"] != "ticket_update":
            raise RuntimeError(
                "ticket_lookup should route stale clearable process verification through ticket_update on the current open ticket"
            )
        if process_clearable_open_guidance["recommended_ticket_update"] != {
            "ticket_id": "PROC-001",
            "activate": True,
            "pending_process_verification": False,
        }:
            raise RuntimeError(
                "ticket_lookup should clear pending_process_verification on the current open ticket once the affected done-ticket set is empty"
            )
        process_clearable_open_update = run_generated_tool(
            process_clearable_open_dest,
            ".opencode/tools/ticket_update.ts",
            process_clearable_open_guidance["recommended_ticket_update"],
        )
        if process_clearable_open_update["workflow"]["pending_process_verification"]:
            raise RuntimeError(
                "ticket_update should clear pending_process_verification when ticket_lookup routes the cleanup through the current open ticket"
            )
        register_current_ticket_artifact(
            executed_lifecycle_dest,
            ticket_id="SETUP-001",
            kind="plan",
            stage="planning",
            relative_path=".opencode/state/artifacts/history/setup-001/planning/setup-001-plan.md",
            summary="Synthetic planning artifact for ordinary lifecycle execution coverage.",
            content="# Plan\n\nCommand: rg --files\n\nPlanned bootstrap follow-through.\n",
        )
        lookup_with_plan = run_generated_tool(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if (
            lookup_with_plan["transition_guidance"]["next_action_tool"]
            != "ticket_update"
        ):
            raise RuntimeError(
                "ticket_lookup should recommend ticket_update once a planning artifact exists"
            )
        if (
            lookup_with_plan["transition_guidance"]["recommended_ticket_update"][
                "stage"
            ]
            != "plan_review"
        ):
            raise RuntimeError(
                "ticket_lookup should recommend moving a planned ticket into plan_review next"
            )
        direct_implementation_error = run_generated_tool_error(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "implementation", "activate": True},
        )
        if (
            "plan is approved" not in direct_implementation_error
            and "passes through plan_review" not in direct_implementation_error
        ):
            raise RuntimeError(
                "ticket_update should block direct jumps into implementation before plan_review approval"
            )
        plan_review_result = run_generated_tool(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "plan_review", "activate": True},
        )
        if plan_review_result["updated_ticket"]["stage"] != "plan_review":
            raise RuntimeError(
                "ticket_update should move the ticket into plan_review when planning proof exists"
            )
        combined_approval_error = run_generated_tool_error(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_update.ts",
            {
                "ticket_id": "SETUP-001",
                "stage": "implementation",
                "approved_plan": True,
                "activate": True,
            },
        )
        if (
            "Approve SETUP-001 while it remains in plan_review first"
            not in combined_approval_error
        ):
            raise RuntimeError(
                "ticket_update should require plan approval and implementation transition as separate calls"
            )
        approval_result = run_generated_tool(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "approved_plan": True, "activate": True},
        )
        if (
            approval_result["workflow"]["ticket_state"]["SETUP-001"]["approved_plan"]
            is not True
        ):
            raise RuntimeError(
                "ticket_update should persist approved_plan in workflow-state"
            )
        lookup_plan_approved = run_generated_tool(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if (
            lookup_plan_approved["transition_guidance"]["recommended_ticket_update"][
                "stage"
            ]
            != "implementation"
        ):
            raise RuntimeError(
                "ticket_lookup should recommend implementation once plan_review approval is recorded"
            )
        implementation_result = run_generated_tool(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "implementation", "activate": True},
        )
        if implementation_result["updated_ticket"]["stage"] != "implementation":
            raise RuntimeError(
                "ticket_update should move an approved ticket into implementation"
            )
        review_fail_dest = workspace / "executed-review-fail-guidance"
        shutil.copytree(full_dest, review_fail_dest)
        seed_ready_bootstrap(review_fail_dest)
        review_fail_manifest_path = review_fail_dest / "tickets" / "manifest.json"
        review_fail_manifest = json.loads(
            review_fail_manifest_path.read_text(encoding="utf-8")
        )
        review_fail_ticket = next(
            ticket for ticket in review_fail_manifest["tickets"] if ticket["id"] == "SETUP-001"
        )
        review_fail_ticket["stage"] = "review"
        review_fail_ticket["status"] = "review"
        review_fail_manifest_path.write_text(
            json.dumps(review_fail_manifest, indent=2) + "\n", encoding="utf-8"
        )
        review_fail_workflow_path = (
            review_fail_dest / ".opencode" / "state" / "workflow-state.json"
        )
        review_fail_workflow = json.loads(
            review_fail_workflow_path.read_text(encoding="utf-8")
        )
        review_fail_workflow["stage"] = "review"
        review_fail_workflow["status"] = "review"
        review_fail_workflow_path.write_text(
            json.dumps(review_fail_workflow, indent=2) + "\n", encoding="utf-8"
        )
        register_current_ticket_artifact(
            review_fail_dest,
            ticket_id="SETUP-001",
            kind="review",
            stage="review",
            relative_path=".opencode/state/reviews/setup-001-review-review.md",
            summary="Synthetic FAIL review artifact for verdict-aware routing coverage.",
            content="# Review\n\nVerdict: FAIL\n\nBlocker: fix the failing implementation path before QA.\n",
        )
        review_fail_lookup = run_generated_tool(
            review_fail_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if review_fail_lookup["transition_guidance"]["review_verdict"] != "FAIL":
            raise RuntimeError(
                "ticket_lookup should extract FAIL verdicts from the latest review artifact"
            )
        if (
            review_fail_lookup["transition_guidance"]["recommended_ticket_update"][
                "stage"
            ]
            != "implementation"
        ):
            raise RuntimeError(
                "ticket_lookup should route FAIL review verdicts back to implementation"
            )
        review_fail_update_error = run_generated_tool_error(
            review_fail_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "qa", "activate": True},
        )
        if "latest artifact shows FAIL verdict" not in review_fail_update_error:
            raise RuntimeError(
                "ticket_update should reject review-to-QA transitions when the latest review verdict is FAIL"
            )
        markdown_verdict_dest = workspace / "executed-review-markdown-verdict"
        shutil.copytree(full_dest, markdown_verdict_dest)
        seed_ready_bootstrap(markdown_verdict_dest)
        seed_review_stage_with_verdict(markdown_verdict_dest, "**Verdict**: PASS")
        markdown_lookup = run_generated_tool(
            markdown_verdict_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if markdown_lookup["transition_guidance"]["review_verdict"] != "PASS":
            raise RuntimeError(
                "ticket_lookup should extract PASS verdicts from markdown-emphasized review artifacts"
            )
        markdown_update = run_generated_tool(
            markdown_verdict_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "qa", "activate": True},
        )
        if markdown_update["updated_ticket"]["stage"] != "qa":
            raise RuntimeError(
                "ticket_update should allow review-to-QA transitions when the latest review artifact records `**Verdict**: PASS`"
            )
        overall_verdict_dest = workspace / "executed-review-overall-verdict"
        shutil.copytree(full_dest, overall_verdict_dest)
        seed_ready_bootstrap(overall_verdict_dest)
        seed_review_stage_with_verdict(
            overall_verdict_dest, "## Overall Verdict\n\n### **APPROVE**"
        )
        overall_lookup = run_generated_tool(
            overall_verdict_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if overall_lookup["transition_guidance"]["review_verdict"] != "APPROVED":
            raise RuntimeError(
                "ticket_lookup should extract APPROVED verdicts from overall-verdict headings"
            )
        overall_update = run_generated_tool(
            overall_verdict_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "qa", "activate": True},
        )
        if overall_update["updated_ticket"]["stage"] != "qa":
            raise RuntimeError(
                "ticket_update should allow review-to-QA transitions when the latest review artifact records `## Overall Verdict` followed by `### **APPROVE**`"
            )
        review_heading_dest = workspace / "executed-review-heading-verdict"
        shutil.copytree(full_dest, review_heading_dest)
        seed_ready_bootstrap(review_heading_dest)
        seed_review_stage_with_verdict(
            review_heading_dest, "## Review Verdict\n\n**APPROVE**"
        )
        review_heading_lookup = run_generated_tool(
            review_heading_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if review_heading_lookup["transition_guidance"]["review_verdict"] != "APPROVED":
            raise RuntimeError(
                "ticket_lookup should extract APPROVED verdicts from `## Review Verdict` headings"
            )
        review_heading_update = run_generated_tool(
            review_heading_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "qa", "activate": True},
        )
        if review_heading_update["updated_ticket"]["stage"] != "qa":
            raise RuntimeError(
                "ticket_update should allow review-to-QA transitions when the latest review artifact records `## Review Verdict` followed by `**APPROVE**`"
            )
        non_remediation_finding_source_dest = (
            workspace / "executed-review-non-remediation-finding-source"
        )
        shutil.copytree(full_dest, non_remediation_finding_source_dest)
        seed_ready_bootstrap(non_remediation_finding_source_dest)
        seed_non_remediation_finding_source_review(
            non_remediation_finding_source_dest
        )
        non_remediation_lookup = run_generated_tool(
            non_remediation_finding_source_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if non_remediation_lookup["transition_guidance"]["review_verdict"] != "APPROVED":
            raise RuntimeError(
                "ticket_lookup should keep extracting APPROVED verdicts for non-remediation follow-up tickets that carry finding_source"
            )
        if non_remediation_lookup["transition_guidance"]["current_state_blocker"]:
            raise RuntimeError(
                "ticket_lookup should not require remediation-only review evidence for non-remediation finding_source tickets"
            )
        non_remediation_update = run_generated_tool(
            non_remediation_finding_source_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "qa", "activate": True},
        )
        if non_remediation_update["updated_ticket"]["stage"] != "qa":
            raise RuntimeError(
                "ticket_update should allow review-to-QA transitions for non-remediation finding_source tickets when the review artifact is approved"
            )
        blocker_signal_dest = workspace / "executed-review-blocker-or-approval"
        shutil.copytree(full_dest, blocker_signal_dest)
        seed_ready_bootstrap(blocker_signal_dest)
        seed_review_stage_with_verdict(
            blocker_signal_dest, "## Blocker or Approval Signal\n\n**APPROVE**"
        )
        blocker_signal_lookup = run_generated_tool(
            blocker_signal_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if blocker_signal_lookup["transition_guidance"]["review_verdict"] != "APPROVED":
            raise RuntimeError(
                "ticket_lookup should extract APPROVED verdicts from `## Blocker or Approval Signal` headings"
            )
        blocker_signal_update = run_generated_tool(
            blocker_signal_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "qa", "activate": True},
        )
        if blocker_signal_update["updated_ticket"]["stage"] != "qa":
            raise RuntimeError(
                "ticket_update should allow review-to-QA transitions when the latest review artifact records `## Blocker or Approval Signal` followed by `**APPROVE**`"
            )
        glitch_style_remediation_dest = (
            workspace / "executed-review-glitch-style-remediation"
        )
        shutil.copytree(full_dest, glitch_style_remediation_dest)
        seed_ready_bootstrap(glitch_style_remediation_dest)
        seed_glitch_style_remediation_review(glitch_style_remediation_dest)
        glitch_style_lookup = run_generated_tool(
            glitch_style_remediation_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if glitch_style_lookup["transition_guidance"]["review_verdict"] != "PASS":
            raise RuntimeError(
                "ticket_lookup should extract PASS verdicts from remediation review artifacts that use `**Verdict:** PASS`"
            )
        glitch_style_update = run_generated_tool(
            glitch_style_remediation_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "qa", "activate": True},
        )
        if glitch_style_update["updated_ticket"]["stage"] != "qa":
            raise RuntimeError(
                "ticket_update should allow review-to-QA transitions when a remediation review artifact records `**Command run:**` plus fenced command/output blocks and `**Verdict:** PASS`"
            )
        overall_result_remediation_dest = (
            workspace / "executed-review-remediation-overall-result"
        )
        shutil.copytree(full_dest, overall_result_remediation_dest)
        seed_ready_bootstrap(overall_result_remediation_dest)
        seed_glitch_style_remediation_review(
            overall_result_remediation_dest, "Overall Result: **PASS**"
        )
        overall_result_lookup = run_generated_tool(
            overall_result_remediation_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if overall_result_lookup["transition_guidance"]["review_verdict"] != "PASS":
            raise RuntimeError(
                "ticket_lookup should extract PASS verdicts from remediation review artifacts that use `Overall Result: **PASS**`"
            )
        overall_result_update = run_generated_tool(
            overall_result_remediation_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "qa", "activate": True},
        )
        if overall_result_update["updated_ticket"]["stage"] != "qa":
            raise RuntimeError(
                "ticket_update should allow review-to-QA transitions when a remediation review artifact records `Overall Result: **PASS**` with fenced command and output evidence"
            )
        verdict_heading_remediation_dest = workspace / "executed-review-remediation-verdict-heading"
        shutil.copytree(full_dest, verdict_heading_remediation_dest)
        seed_ready_bootstrap(verdict_heading_remediation_dest)
        seed_glitch_style_remediation_review(
            verdict_heading_remediation_dest, "## Verdict\n\n**PASS**"
        )
        verdict_heading_lookup = run_generated_tool(
            verdict_heading_remediation_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if verdict_heading_lookup["transition_guidance"]["review_verdict"] != "PASS":
            raise RuntimeError(
                "ticket_lookup should extract PASS verdicts from remediation review artifacts that use `## Verdict` followed by `**PASS**`"
            )
        verdict_heading_update = run_generated_tool(
            verdict_heading_remediation_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "qa", "activate": True},
        )
        if verdict_heading_update["updated_ticket"]["stage"] != "qa":
            raise RuntimeError(
                "ticket_update should allow review-to-QA transitions when a remediation review artifact records `## Verdict` followed by `**PASS**` with fenced command and output evidence"
            )
        inline_exact_remediation_dest = (
            workspace / "executed-review-remediation-inline-exact"
        )
        shutil.copytree(full_dest, inline_exact_remediation_dest)
        seed_ready_bootstrap(inline_exact_remediation_dest)
        seed_inline_exact_remediation_review(inline_exact_remediation_dest)
        inline_exact_lookup = run_generated_tool(
            inline_exact_remediation_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if inline_exact_lookup["transition_guidance"]["review_verdict"] != "APPROVED":
            raise RuntimeError(
                "ticket_lookup should extract APPROVED verdicts from remediation review artifacts that use `Exact command run` with inline `Raw output` evidence"
            )
        inline_exact_update = run_generated_tool(
            inline_exact_remediation_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "qa", "activate": True},
        )
        if inline_exact_update["updated_ticket"]["stage"] != "qa":
            raise RuntimeError(
                "ticket_update should allow review-to-QA transitions when a remediation review artifact records `Exact command run`, inline `Raw output`, and `Result: PASS`"
            )
        qa_fail_dest = workspace / "executed-qa-fail-guidance"
        shutil.copytree(full_dest, qa_fail_dest)
        seed_ready_bootstrap(qa_fail_dest)
        qa_fail_manifest_path = qa_fail_dest / "tickets" / "manifest.json"
        qa_fail_manifest = json.loads(qa_fail_manifest_path.read_text(encoding="utf-8"))
        qa_fail_ticket = next(
            ticket for ticket in qa_fail_manifest["tickets"] if ticket["id"] == "SETUP-001"
        )
        qa_fail_ticket["stage"] = "qa"
        qa_fail_ticket["status"] = "qa"
        qa_fail_manifest_path.write_text(
            json.dumps(qa_fail_manifest, indent=2) + "\n", encoding="utf-8"
        )
        qa_fail_workflow_path = qa_fail_dest / ".opencode" / "state" / "workflow-state.json"
        qa_fail_workflow = json.loads(qa_fail_workflow_path.read_text(encoding="utf-8"))
        qa_fail_workflow["stage"] = "qa"
        qa_fail_workflow["status"] = "qa"
        qa_fail_workflow_path.write_text(
            json.dumps(qa_fail_workflow, indent=2) + "\n", encoding="utf-8"
        )
        register_current_ticket_artifact(
            qa_fail_dest,
            ticket_id="SETUP-001",
            kind="qa",
            stage="qa",
            relative_path=".opencode/state/qa/setup-001-qa-qa.md",
            summary="Synthetic FAIL QA artifact for verdict-aware routing coverage.",
            content="# QA\n\nResult: BLOCKED\n\nCommand: pytest tests/test_failure.py\n\n~~~~text\n============================= test session starts =============================\ncollected 1 item\n\ntests/test_failure.py F                                                [100%]\n\n================================== FAILURES ==================================\nAssertionError: blocker remains\nexit code: 1\n~~~~\n\nCommand output shows a blocker that must be fixed before smoke-test.\n",
        )
        qa_fail_lookup = run_generated_tool(
            qa_fail_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if qa_fail_lookup["transition_guidance"]["qa_verdict"] != "BLOCKED":
            raise RuntimeError(
                "ticket_lookup should extract BLOCKED verdicts from the latest QA artifact"
            )
        if (
            qa_fail_lookup["transition_guidance"]["recommended_ticket_update"][
                "stage"
            ]
            != "implementation"
        ):
            raise RuntimeError(
                "ticket_lookup should route FAIL or BLOCKED QA verdicts back to implementation"
            )
        qa_fail_update_error = run_generated_tool_error(
            qa_fail_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "smoke-test", "activate": True},
        )
        if "latest artifact shows FAIL verdict" not in qa_fail_update_error:
            raise RuntimeError(
                "ticket_update should reject QA-to-smoke-test transitions when the latest QA verdict is blocking"
            )
        qa_pass_dest = workspace / "executed-qa-overall-verdict"
        shutil.copytree(full_dest, qa_pass_dest)
        seed_ready_bootstrap(qa_pass_dest)
        qa_pass_manifest_path = qa_pass_dest / "tickets" / "manifest.json"
        qa_pass_manifest = json.loads(qa_pass_manifest_path.read_text(encoding="utf-8"))
        qa_pass_ticket = next(
            ticket for ticket in qa_pass_manifest["tickets"] if ticket["id"] == "SETUP-001"
        )
        qa_pass_ticket["stage"] = "qa"
        qa_pass_ticket["status"] = "qa"
        qa_pass_manifest_path.write_text(
            json.dumps(qa_pass_manifest, indent=2) + "\n", encoding="utf-8"
        )
        qa_pass_workflow_path = qa_pass_dest / ".opencode" / "state" / "workflow-state.json"
        qa_pass_workflow = json.loads(qa_pass_workflow_path.read_text(encoding="utf-8"))
        qa_pass_workflow["stage"] = "qa"
        qa_pass_workflow["status"] = "qa"
        qa_pass_workflow_path.write_text(
            json.dumps(qa_pass_workflow, indent=2) + "\n", encoding="utf-8"
        )
        register_current_ticket_artifact(
            qa_pass_dest,
            ticket_id="SETUP-001",
            kind="qa",
            stage="qa",
            relative_path=".opencode/state/qa/setup-001-qa-qa.md",
            summary="Synthetic PASS QA artifact for overall-QA-verdict coverage.",
            content="# QA\n\n## Validation Command\n\n`npm test -- --runInBand`\n\n## Raw Output\n\n```text\nPASS tests/setup.test.ts\n  setup workflow\n    ✓ keeps lifecycle routing intact (42 ms)\n\nTest Suites: 1 passed, 1 total\nTests:       1 passed, 1 total\nSnapshots:   0 total\nTime:        0.842 s\nRan all test suites matching /setup/i.\n```\n\n## Overall QA Verdict\n\n**PASS**",
        )
        qa_pass_lookup = run_generated_tool(
            qa_pass_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if qa_pass_lookup["transition_guidance"]["qa_verdict"] != "PASS":
            raise RuntimeError(
                "ticket_lookup should extract PASS verdicts from `## Overall QA Verdict` headings"
            )
        qa_pass_update = run_generated_tool(
            qa_pass_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "smoke-test", "activate": True},
        )
        if qa_pass_update["updated_ticket"]["stage"] != "smoke-test":
            raise RuntimeError(
                "ticket_update should allow QA-to-smoke-test transitions when the latest QA artifact records `## Overall QA Verdict` followed by `**PASS**`"
            )
        qa_compact_heading_dest = workspace / "executed-qa-compact-heading"
        shutil.copytree(full_dest, qa_compact_heading_dest)
        seed_ready_bootstrap(qa_compact_heading_dest)
        qa_compact_manifest_path = qa_compact_heading_dest / "tickets" / "manifest.json"
        qa_compact_manifest = json.loads(
            qa_compact_manifest_path.read_text(encoding="utf-8")
        )
        qa_compact_ticket = next(
            ticket for ticket in qa_compact_manifest["tickets"] if ticket["id"] == "SETUP-001"
        )
        qa_compact_ticket["stage"] = "qa"
        qa_compact_ticket["status"] = "qa"
        qa_compact_manifest_path.write_text(
            json.dumps(qa_compact_manifest, indent=2) + "\n", encoding="utf-8"
        )
        qa_compact_workflow_path = (
            qa_compact_heading_dest / ".opencode" / "state" / "workflow-state.json"
        )
        qa_compact_workflow = json.loads(
            qa_compact_workflow_path.read_text(encoding="utf-8")
        )
        qa_compact_workflow["stage"] = "qa"
        qa_compact_workflow["status"] = "qa"
        qa_compact_workflow_path.write_text(
            json.dumps(qa_compact_workflow, indent=2) + "\n", encoding="utf-8"
        )
        register_current_ticket_artifact(
            qa_compact_heading_dest,
            ticket_id="SETUP-001",
            kind="qa",
            stage="qa",
            relative_path=".opencode/state/qa/setup-001-qa-qa.md",
            summary="Synthetic PASS QA artifact for compact QA heading coverage.",
            content="# QA Artifact — SETUP-001\n\n## QA PASS — Both Acceptance Criteria Satisfied\n\n## Validation Command\n\n`npm test -- --runInBand`\n\n## Raw Command Output\n\n```text\n$ npm test -- --runInBand\nPASS tests/setup.test.ts\n  setup workflow\n    ✓ keeps lifecycle routing intact (42 ms)\nEXIT_CODE: 0\nRESULT: PASS ✅\n```\n\nFinding remains stale and deterministic validation passed.\n",
        )
        qa_compact_lookup = run_generated_tool(
            qa_compact_heading_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if qa_compact_lookup["transition_guidance"]["qa_verdict"] != "PASS":
            raise RuntimeError(
                "ticket_lookup should extract PASS verdicts from compact `## QA PASS` headings"
            )
        qa_compact_update = run_generated_tool(
            qa_compact_heading_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "smoke-test", "activate": True},
        )
        if qa_compact_update["updated_ticket"]["stage"] != "smoke-test":
            raise RuntimeError(
                "ticket_update should allow QA-to-smoke-test transitions when the latest QA artifact records a compact `## QA PASS` heading"
            )
        qa_overall_label_dest = workspace / "executed-qa-overall-label"
        shutil.copytree(full_dest, qa_overall_label_dest)
        seed_ready_bootstrap(qa_overall_label_dest)
        qa_overall_manifest_path = qa_overall_label_dest / "tickets" / "manifest.json"
        qa_overall_manifest = json.loads(
            qa_overall_manifest_path.read_text(encoding="utf-8")
        )
        qa_overall_ticket = next(
            ticket for ticket in qa_overall_manifest["tickets"] if ticket["id"] == "SETUP-001"
        )
        qa_overall_ticket["stage"] = "qa"
        qa_overall_ticket["status"] = "qa"
        qa_overall_manifest_path.write_text(
            json.dumps(qa_overall_manifest, indent=2) + "\n", encoding="utf-8"
        )
        qa_overall_workflow_path = (
            qa_overall_label_dest / ".opencode" / "state" / "workflow-state.json"
        )
        qa_overall_workflow = json.loads(
            qa_overall_workflow_path.read_text(encoding="utf-8")
        )
        qa_overall_workflow["stage"] = "qa"
        qa_overall_workflow["status"] = "qa"
        qa_overall_workflow_path.write_text(
            json.dumps(qa_overall_workflow, indent=2) + "\n", encoding="utf-8"
        )
        register_current_ticket_artifact(
            qa_overall_label_dest,
            ticket_id="SETUP-001",
            kind="qa",
            stage="qa",
            relative_path=".opencode/state/qa/setup-001-qa-qa.md",
            summary="Synthetic PASS QA artifact for `**Overall**: PASS` coverage.",
            content="# QA\n\n## QA Result\n\n**Overall**: PASS pending smoke test confirmation.\n\n## Validation Command\n\n`npm test -- --runInBand`\n\n## Raw Command Output\n\n```text\n$ npm test -- --runInBand\nPASS tests/setup.test.ts\n  setup workflow\n    ✓ keeps lifecycle routing intact (42 ms)\nEXIT_CODE: 0\nRESULT: PASS ✅\n```\n",
        )
        qa_overall_lookup = run_generated_tool(
            qa_overall_label_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if qa_overall_lookup["transition_guidance"]["qa_verdict"] != "PASS":
            raise RuntimeError(
                "ticket_lookup should extract PASS verdicts from `**Overall**: PASS` labels inside QA result sections"
            )
        qa_overall_update = run_generated_tool(
            qa_overall_label_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "smoke-test", "activate": True},
        )
        if qa_overall_update["updated_ticket"]["stage"] != "smoke-test":
            raise RuntimeError(
                "ticket_update should allow QA-to-smoke-test transitions when the latest QA artifact records `**Overall**: PASS`"
            )
        split_brain_dest = workspace / "ticket-lookup-requested-ticket"
        shutil.copytree(full_dest, split_brain_dest)
        split_manifest_path = split_brain_dest / "tickets" / "manifest.json"
        split_manifest = json.loads(split_manifest_path.read_text(encoding="utf-8"))
        split_manifest["tickets"].append(
            {
                "id": "SYSTEM-001",
                "title": "Synthetic non-active ticket",
                "wave": 2,
                "lane": "system",
                "parallel_safe": True,
                "overlap_risk": "low",
                "stage": "planning",
                "status": "todo",
                "depends_on": [],
                "summary": "Synthetic ticket for requested ticket lookup coverage.",
                "acceptance": [
                    "Requested-ticket lookup should not rewrite workflow active_ticket."
                ],
                "decision_blockers": [],
                "artifacts": [],
                "resolution_state": "open",
                "verification_state": "suspect",
                "follow_up_ticket_ids": [],
            }
        )
        split_manifest_path.write_text(
            json.dumps(split_manifest, indent=2) + "\n", encoding="utf-8"
        )
        split_lookup = run_generated_tool(
            split_brain_dest,
            ".opencode/tools/ticket_lookup.ts",
            {"ticket_id": "SYSTEM-001"},
        )
        if (
            split_lookup["active_ticket"] != "SETUP-001"
            or split_lookup["workflow"]["active_ticket"] != "SETUP-001"
        ):
            raise RuntimeError(
                "ticket_lookup should keep the canonical active_ticket when resolving a requested non-active ticket"
            )
        if (
            split_lookup["is_active"] is not False
            or split_lookup["requested_ticket"]["is_active"] is not False
        ):
            raise RuntimeError(
                "ticket_lookup should report whether the requested ticket is the active ticket"
            )
        claim_result = run_generated_tool(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_claim.ts",
            {
                "ticket_id": "SETUP-001",
                "owner_agent": "smoke-implementer",
                "allowed_paths": ["docs", "tickets", ".opencode/state"],
                "write_lock": True,
            },
        )
        if (
            claim_result["claimed"] is not True
            or claim_result["lease"]["ticket_id"] != "SETUP-001"
        ):
            raise RuntimeError(
                "ticket_claim should create a write-capable lane lease for the active implementation ticket"
            )
        if claim_result["lease"]["owner_agent"] != "smoke-implementer":
            raise RuntimeError(
                "ticket_claim should persist the requesting owner_agent on the created lease"
            )
        release_result = run_generated_tool(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_release.ts",
            {"ticket_id": "SETUP-001", "owner_agent": "smoke-implementer"},
        )
        if release_result["released"]["ticket_id"] != "SETUP-001":
            raise RuntimeError(
                "ticket_release should release the matching active lease for the ticket"
            )
        if release_result["active_leases"]:
            raise RuntimeError(
                "ticket_release should leave no active leases after releasing the only lease"
            )

        executed_artifact_tools_dest = workspace / "executed-artifact-tools"
        shutil.copytree(full_dest, executed_artifact_tools_dest)
        seed_ready_bootstrap(executed_artifact_tools_dest)
        noncanonical_artifact_error = run_generated_tool_error(
            executed_artifact_tools_dest,
            ".opencode/tools/artifact_write.ts",
            {
                "ticket_id": "SETUP-001",
                "path": "notes/noncanonical-plan.md",
                "kind": "plan",
                "stage": "planning",
                "content": "# Invalid Plan\n",
            },
        )
        if (
            "Artifact path mismatch" not in noncanonical_artifact_error
            or ".opencode/state/plans/setup-001-planning-plan.md"
            not in noncanonical_artifact_error
        ):
            raise RuntimeError(
                "artifact_write should reject non-canonical artifact paths"
            )
        plan_artifact_path = ".opencode/state/plans/setup-001-planning-plan.md"
        artifact_write_result = run_generated_tool(
            executed_artifact_tools_dest,
            ".opencode/tools/artifact_write.ts",
            {
                "ticket_id": "SETUP-001",
                "path": plan_artifact_path,
                "kind": "plan",
                "stage": "planning",
                "content": "# Plan\n\nCommand: rg --files\n\nCanonical planning artifact body.\n",
            },
        )
        if artifact_write_result["path"] != plan_artifact_path:
            raise RuntimeError(
                "artifact_write should persist to the canonical planning artifact path"
            )
        if not (executed_artifact_tools_dest / plan_artifact_path).exists():
            raise RuntimeError(
                "artifact_write should create the canonical artifact file on disk"
            )
        artifact_register_result = run_generated_tool(
            executed_artifact_tools_dest,
            ".opencode/tools/artifact_register.ts",
            {
                "ticket_id": "SETUP-001",
                "path": plan_artifact_path,
                "kind": "plan",
                "stage": "planning",
                "summary": "Synthetic registered plan artifact.",
            },
        )
        latest_registered_plan = artifact_register_result["latest_artifact"]
        if (
            latest_registered_plan["stage"] != "planning"
            or latest_registered_plan["kind"] != "plan"
        ):
            raise RuntimeError(
                "artifact_register should persist the stage and kind of the registered artifact"
            )
        if not str(latest_registered_plan["path"]).startswith(
            ".opencode/state/artifacts/history/setup-001/planning/"
        ):
            raise RuntimeError(
                "artifact_register should snapshot canonical artifacts into history-backed registry storage"
            )
        stage_gate_reserved_write_error = run_generated_plugin_before_error(
            executed_artifact_tools_dest,
            ".opencode/plugins/stage-gate-enforcer.ts",
            "artifact_write",
            {
                "ticket_id": "SETUP-001",
                "path": ".opencode/state/smoke-tests/setup-001-smoke-test-smoke-test.md",
                "kind": "smoke-test",
                "stage": "smoke-test",
                "content": "# Synthetic Smoke\n",
            },
        )
        if (
            "Use smoke_test to create smoke-test artifacts."
            not in stage_gate_reserved_write_error
        ):
            raise RuntimeError(
                "Stage gate plugin should block generic artifact_write for reserved smoke-test artifacts"
            )
        stage_gate_reserved_register_error = run_generated_plugin_before_error(
            executed_artifact_tools_dest,
            ".opencode/plugins/stage-gate-enforcer.ts",
            "artifact_register",
            {
                "ticket_id": "SETUP-001",
                "path": ".opencode/state/smoke-tests/setup-001-smoke-test-smoke-test.md",
                "kind": "smoke-test",
                "stage": "smoke-test",
                "summary": "Synthetic smoke summary.",
            },
        )
        if (
            "Use smoke_test to create smoke-test artifacts."
            not in stage_gate_reserved_register_error
        ):
            raise RuntimeError(
                "Stage gate plugin should block generic artifact_register for reserved smoke-test artifacts"
            )
        stage_gate_missing_lease_error = run_generated_plugin_before_error(
            executed_artifact_tools_dest,
            ".opencode/plugins/stage-gate-enforcer.ts",
            "artifact_write",
            {
                "ticket_id": "SETUP-001",
                "path": ".opencode/state/implementations/setup-001-implementation-implementation.md",
                "kind": "implementation",
                "stage": "implementation",
                "content": "# Synthetic Implementation\n",
            },
        )
        if "must hold an active write lease" not in stage_gate_missing_lease_error:
            raise RuntimeError(
                "Stage gate plugin should block implementation artifact writes when no active ticket lease exists"
            )
        run_generated_tool(
            executed_artifact_tools_dest,
            ".opencode/tools/ticket_claim.ts",
            {
                "ticket_id": "SETUP-001",
                "owner_agent": "smoke-stage-gate",
                "allowed_paths": [".opencode/state"],
                "write_lock": True,
            },
        )
        coordinator_session_id = "ses_stage_gate_team_leader"
        invocation_log_path = (
            executed_artifact_tools_dest / ".opencode" / "state" / "invocation-log.jsonl"
        )
        invocation_log_path.parent.mkdir(parents=True, exist_ok=True)
        invocation_log_path.write_text(
            json.dumps(
                {
                    "event": "chat.message",
                    "timestamp": "2026-04-12T06:00:00Z",
                    "session_id": coordinator_session_id,
                    "agent": "integration-probe-team-leader",
                    "message_id": "msg_stage_gate_team_leader",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        coordinator_artifact_write_error = run_generated_plugin_before_error(
            executed_artifact_tools_dest,
            ".opencode/plugins/stage-gate-enforcer.ts",
            "artifact_write",
            {
                "ticket_id": "SETUP-001",
                "path": ".opencode/state/plans/setup-001-planning-plan.md",
                "kind": "plan",
                "stage": "planning",
                "content": "# Coordinator Authored Plan\n",
            },
            session_id=coordinator_session_id,
        )
        if "Coordinator-authored planning artifacts are not allowed." not in coordinator_artifact_write_error:
            raise RuntimeError(
                "Stage gate plugin should resolve the team leader from invocation history and block direct planning artifact writes"
            )
        run_generated_plugin_before(
            executed_artifact_tools_dest,
            ".opencode/plugins/stage-gate-enforcer.ts",
            "artifact_write",
            {
                "ticket_id": "SETUP-001",
                "path": ".opencode/state/plans/setup-001-planning-plan.md",
                "kind": "plan",
                "stage": "planning",
                "content": "# Specialist Authored Plan\n",
            },
            agent="integration-probe-planner",
            session_id="ses_stage_gate_planner",
        )
        coordinator_artifact_register_error = run_generated_plugin_before_error(
            executed_artifact_tools_dest,
            ".opencode/plugins/stage-gate-enforcer.ts",
            "artifact_register",
            {
                "ticket_id": "SETUP-001",
                "path": ".opencode/state/plans/setup-001-planning-plan.md",
                "kind": "plan",
                "stage": "planning",
                "summary": "Coordinator tried to register the plan.",
            },
            session_id=coordinator_session_id,
        )
        if "Coordinator-authored planning artifacts are not allowed." not in coordinator_artifact_register_error:
            raise RuntimeError(
                "Stage gate plugin should resolve the team leader from invocation history and block direct planning artifact registration"
            )
        run_generated_plugin_before(
            executed_artifact_tools_dest,
            ".opencode/plugins/stage-gate-enforcer.ts",
            "artifact_write",
            {
                "ticket_id": "SETUP-001",
                "path": ".opencode/state/implementations/setup-001-implementation-implementation.md",
                "kind": "implementation",
                "stage": "implementation",
                "content": "# Synthetic Implementation\n",
            },
        )
        wildcard_lease_dest = workspace / "wildcard-write-lease"
        shutil.copytree(full_dest, wildcard_lease_dest)
        seed_ready_bootstrap(wildcard_lease_dest)
        run_generated_tool(
            wildcard_lease_dest,
            ".opencode/tools/ticket_claim.ts",
            {
                "ticket_id": "SETUP-001",
                "owner_agent": "smoke-wildcard-lease",
                "allowed_paths": [".opencode/state/plans/*.md"],
                "write_lock": True,
            },
        )
        run_generated_plugin_before(
            wildcard_lease_dest,
            ".opencode/plugins/stage-gate-enforcer.ts",
            "artifact_write",
            {
                "ticket_id": "SETUP-001",
                "path": ".opencode/state/plans/setup-001-planning-plan.md",
                "kind": "plan",
                "stage": "planning",
                "content": "# Synthetic Plan\n",
            },
        )
        # Regression test: closeout-to-new-ticket artifact write (WFLOW010)
        # Ensures ensureWriteLease accepts a target-ticket parameter so artifact tools
        # validate against the correct ticket instead of stale workflow.active_ticket.
        closeout_continuation_dest = workspace / "closeout-continuation-artifact-write"
        shutil.copytree(full_dest, closeout_continuation_dest)
        seed_closed_ticket_with_new_active_artifact_write(closeout_continuation_dest)
        run_generated_plugin_before(
            closeout_continuation_dest,
            ".opencode/plugins/stage-gate-enforcer.ts",
            "artifact_write",
            {
                "ticket_id": "TICK-002",
                "path": ".opencode/state/plans/tick-002-planning-plan.md",
                "kind": "plan",
                "stage": "planning",
                "content": "# Synthetic Plan\n",
            },
        )
        run_generated_plugin_before(
            closeout_continuation_dest,
            ".opencode/plugins/stage-gate-enforcer.ts",
            "artifact_register",
            {
                "ticket_id": "TICK-002",
                "path": ".opencode/state/plans/tick-002-planning-plan.md",
                "kind": "plan",
                "stage": "planning",
            },
        )
        # Regression test: ticket_create after all tickets closed (Spinner deadlock)
        # Ensures net_new_scope ticket creation succeeds when active_ticket points to
        # a closed ticket and no leases exist.
        all_closed_dest = workspace / "all-tickets-closed-create"
        shutil.copytree(full_dest, all_closed_dest)
        seed_all_tickets_closed(all_closed_dest)
        ticket_create_result = run_generated_tool(
            all_closed_dest,
            ".opencode/tools/ticket_create.ts",
            {
                "id": "ANDROID-001",
                "title": "Android export follow-up",
                "lane": "android-export",
                "wave": 4,
                "summary": "Set up Android export pipeline.",
                "acceptance": ["A valid APK is produced."],
                "source_mode": "net_new_scope",
                "activate": True,
            },
        )
        assert ticket_create_result["created_ticket"] == "ANDROID-001"
        assert ticket_create_result["activated"] is True
        wf_after = json.loads(
            (all_closed_dest / ".opencode" / "state" / "workflow-state.json").read_text(
                encoding="utf-8"
            )
        )
        assert wf_after["active_ticket"] == "ANDROID-001"
        manifest_after = json.loads(
            (all_closed_dest / "tickets" / "manifest.json").read_text(encoding="utf-8")
        )
        assert any(t["id"] == "ANDROID-001" for t in manifest_after["tickets"])
        executed_reopen_dest = workspace / "executed-ticket-reopen"
        shutil.copytree(full_dest, executed_reopen_dest)
        seed_closed_ticket_needing_explicit_reverification(executed_reopen_dest)
        reopen_evidence_rel = (
            ".opencode/state/reviews/setup-001-review-reopen-evidence.md"
        )
        register_current_ticket_artifact(
            executed_reopen_dest,
            ticket_id="SETUP-001",
            kind="backlog-verification",
            stage="review",
            relative_path=reopen_evidence_rel,
            summary="Synthetic reopen evidence.",
            content="# Reopen Evidence\n\nA newly discovered defect invalidates completion.\n",
        )
        reopen_workflow_path = executed_reopen_dest / ".opencode" / "state" / "workflow-state.json"
        run_generated_plugin_before(
            executed_reopen_dest,
            ".opencode/plugins/stage-gate-enforcer.ts",
            "ticket_reopen",
            {
                "ticket_id": "SETUP-001",
                "reason": "Synthetic reopened scope due to newly discovered defect.",
                "evidence_artifact_path": reopen_evidence_rel,
                "activate": True,
            },
        )
        ticket_reopen_result = run_generated_tool(
            executed_reopen_dest,
            ".opencode/tools/ticket_reopen.ts",
            {
                "ticket_id": "SETUP-001",
                "reason": "Synthetic reopened scope due to newly discovered defect.",
                "evidence_artifact_path": reopen_evidence_rel,
                "activate": True,
            },
        )
        if ticket_reopen_result["reopened_ticket"] != "SETUP-001":
            raise RuntimeError("ticket_reopen should report the reopened ticket id")
        reopened_manifest = json.loads(
            (executed_reopen_dest / "tickets" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        reopened_workflow = json.loads(reopen_workflow_path.read_text(encoding="utf-8"))
        reopened_ticket = next(
            ticket
            for ticket in reopened_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        if (
            reopened_ticket["stage"] != "planning"
            or reopened_ticket["status"] != "todo"
        ):
            raise RuntimeError(
                "ticket_reopen should return a completed ticket to planning/todo"
            )
        if (
            reopened_ticket["resolution_state"] != "reopened"
            or reopened_ticket["verification_state"] != "invalidated"
        ):
            raise RuntimeError(
                "ticket_reopen should mark the reopened ticket as reopened and invalidated"
            )
        if (
            reopened_workflow["ticket_state"]["SETUP-001"]["reopen_count"] != 1
            or reopened_workflow["ticket_state"]["SETUP-001"]["needs_reverification"]
            is not True
        ):
            raise RuntimeError(
                "ticket_reopen should increment reopen_count and require reverification"
            )
        if reopened_workflow["lane_leases"]:
            raise RuntimeError(
                "ticket_reopen should release any active lease on the reopened ticket"
            )
        if not all(
            artifact["trust_state"] != "current"
            for artifact in reopened_ticket["artifacts"]
        ):
            raise RuntimeError(
                "ticket_reopen should mark prior current artifacts historical when reopening a ticket"
            )
        executed_context_handoff_dest = workspace / "executed-context-and-handoff"
        shutil.copytree(full_dest, executed_context_handoff_dest)
        seed_ready_bootstrap(executed_context_handoff_dest)
        context_snapshot_result = run_generated_tool(
            executed_context_handoff_dest,
            ".opencode/tools/context_snapshot.ts",
            {
                "note": "Synthetic snapshot note for Phase 5 runtime coverage.",
            },
        )
        context_snapshot_path = Path(context_snapshot_result["path"])
        context_snapshot_text = context_snapshot_path.read_text(encoding="utf-8")
        if (
            "## Active Ticket" not in context_snapshot_text
            or "Synthetic snapshot note for Phase 5 runtime coverage."
            not in context_snapshot_text
        ):
            raise RuntimeError(
                "context_snapshot should write the canonical snapshot with the requested note"
            )
        if (
            context_snapshot_result["verified"] is not True
            or context_snapshot_result["active_ticket"] != "SETUP-001"
            or context_snapshot_result["snapshot_size_bytes"] <= 0
        ):
            raise RuntimeError(
                "context_snapshot should return verification metadata for the written snapshot"
            )
        handoff_publish_result = run_generated_tool(
            executed_context_handoff_dest,
            ".opencode/tools/handoff_publish.ts",
            {
                "next_action": "Keep SETUP-001 as the foreground ticket and continue its lifecycle from planning.",
            },
        )
        start_here_text = (executed_context_handoff_dest / "START-HERE.md").read_text(
            encoding="utf-8"
        )
        latest_handoff_text = (
            executed_context_handoff_dest / ".opencode" / "state" / "latest-handoff.md"
        ).read_text(encoding="utf-8")
        if str(handoff_publish_result["start_here"]) != str(
            executed_context_handoff_dest / "START-HERE.md"
        ):
            raise RuntimeError(
                "handoff_publish should report the canonical START-HERE path"
            )
        if (
            handoff_publish_result["verified"] is not True
            or handoff_publish_result["active_ticket"] != "SETUP-001"
            or handoff_publish_result["bootstrap_status"] != "ready"
            or handoff_publish_result["pending_process_verification"] is not False
        ):
            raise RuntimeError(
                "handoff_publish should return verification metadata for the published restart surfaces"
            )
        if (
            "Keep SETUP-001 as the foreground ticket and continue its lifecycle from planning."
            not in start_here_text
        ):
            raise RuntimeError(
                "handoff_publish should publish the requested next_action into START-HERE"
            )
        if (
            "Keep SETUP-001 as the foreground ticket and continue its lifecycle from planning."
            not in latest_handoff_text
        ):
            raise RuntimeError(
                "handoff_publish should publish the requested next_action into the latest handoff copy"
            )
        invalid_handoff_dest = workspace / "executed-invalid-handoff"
        shutil.copytree(full_dest, invalid_handoff_dest)
        seed_truthful_process_verification(invalid_handoff_dest)
        invalid_handoff_error = run_generated_tool_error(
            invalid_handoff_dest,
            ".opencode/tools/handoff_publish.ts",
            {"next_action": "Repo is clean and fully verified. No follow-up required."},
        )
        if "pending_process_verification" not in invalid_handoff_error:
            raise RuntimeError(
                "handoff_publish should reject clean-state claims while pending_process_verification remains true"
            )

        executed_environment_bootstrap_dest = (
            workspace / "executed-environment-bootstrap"
        )
        shutil.copytree(full_dest, executed_environment_bootstrap_dest)
        if host_has_npm:
            seed_minimal_npm_repo(executed_environment_bootstrap_dest)
        bootstrap_result = run_generated_tool(
            executed_environment_bootstrap_dest,
            ".opencode/tools/environment_bootstrap.ts",
            {"ticket_id": "SETUP-001"},
        )
        if bootstrap_result["bootstrap_status"] != "ready":
            raise RuntimeError(
                "environment_bootstrap should record a ready bootstrap state when its detected commands succeed"
            )
        if host_has_npm and not any(
            command["label"] == "npm ci" and command["exit_code"] == 0
            for command in bootstrap_result["commands"]
        ):
            raise RuntimeError(
                "environment_bootstrap should execute npm ci for a minimal lockfile-backed Node repo"
            )
        if host_has_npm and bootstrap_result["host_surface_classification"] != "none":
            raise RuntimeError(
                "environment_bootstrap should not classify a successful bootstrap run as a host-surface failure"
            )
        bootstrap_proof = executed_environment_bootstrap_dest / str(
            bootstrap_result["proof_artifact"]
        )
        if not bootstrap_proof.exists():
            raise RuntimeError(
                "environment_bootstrap should persist the canonical bootstrap proof artifact"
            )
        bootstrap_workflow = json.loads(
            (
                executed_environment_bootstrap_dest
                / ".opencode"
                / "state"
                / "workflow-state.json"
            ).read_text(encoding="utf-8")
        )
        if bootstrap_workflow["bootstrap"]["status"] != "ready":
            raise RuntimeError(
                "environment_bootstrap should persist ready bootstrap state into workflow-state"
            )
        if bootstrap_result["blockers"] != []:
            raise RuntimeError(
                "environment_bootstrap should return zero blockers for a successful bootstrap run"
            )
        if bootstrap_workflow.get("bootstrap_blockers") != []:
            raise RuntimeError(
                "environment_bootstrap should persist cleared bootstrap_blockers into workflow-state after a successful run"
            )
        android_bootstrap_dest = workspace / "executed-environment-bootstrap-android"
        shutil.copytree(full_dest, android_bootstrap_dest)
        seed_godot_android_target(android_bootstrap_dest)
        seed_minimal_godot_project(android_bootstrap_dest)
        android_bootstrap_result = run_generated_tool(
            android_bootstrap_dest,
            ".opencode/tools/environment_bootstrap.ts",
            {"ticket_id": "SETUP-001"},
        )
        android_warnings = [
            warning.lower() for warning in android_bootstrap_result.get("warnings", [])
        ]
        if not any("export_presets.cfg" in warning for warning in android_warnings):
            raise RuntimeError(
                "environment_bootstrap should warn about missing Android export presets when the canonical brief declares a Godot Android target even before export_presets.cfg exists"
            )

        executed_smoke_test_dest = workspace / "executed-smoke-test"
        shutil.copytree(full_dest, executed_smoke_test_dest)
        seed_ready_bootstrap(executed_smoke_test_dest)
        register_current_ticket_artifact(
            executed_smoke_test_dest,
            ticket_id="SETUP-001",
            kind="qa",
            stage="qa",
            relative_path=".opencode/state/artifacts/setup-001-qa-qa.md",
            summary="Synthetic QA artifact for smoke_test execution coverage.",
            content="# QA\n\nCommand: python3 -m py_compile scripts/smoke_test_scafforge.py\n\nQA evidence is current.\n",
        )
        write_executable(
            executed_smoke_test_dest / "scripts" / "mock_smoke.py",
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import os",
                    "import sys",
                    "print(f\"SMOKE_TOKEN={os.environ.get('SMOKE_TOKEN', '')}\")",
                    "sys.exit(0 if os.environ.get('SMOKE_TOKEN') == 'phase5' else 1)",
                ]
            )
            + "\n",
        )
        smoke_test_result = run_generated_tool(
            executed_smoke_test_dest,
            ".opencode/tools/smoke_test.ts",
            {
                "ticket_id": "SETUP-001",
                "command_override": [
                    "SMOKE_TOKEN=phase5 python3 scripts/mock_smoke.py"
                ],
            },
        )
        if (
            smoke_test_result["passed"] is not True
            or smoke_test_result["host_surface_classification"] is not None
        ):
            raise RuntimeError(
                "smoke_test should pass and avoid host-surface failure classification when its explicit command succeeds"
            )
        if (
            smoke_test_result["commands"][0]["command"]
            != "SMOKE_TOKEN=phase5 python3 scripts/mock_smoke.py"
        ):
            raise RuntimeError(
                "smoke_test should preserve shell-style KEY=VALUE command_override parsing in the executed command record"
            )
        smoke_verified_manifest = json.loads(
            (executed_smoke_test_dest / "tickets" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        smoke_verified_ticket = next(
            ticket
            for ticket in smoke_verified_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        if smoke_verified_ticket["verification_state"] != "smoke_verified":
            raise RuntimeError(
                "smoke_test should mark a passing in-flight ticket as smoke_verified before closeout"
            )
        smoke_test_artifact = executed_smoke_test_dest / str(
            smoke_test_result["smoke_test_artifact"]
        )
        if not smoke_test_artifact.exists():
            raise RuntimeError(
                "smoke_test should persist the canonical smoke-test artifact"
            )
        smoke_test_artifact_body = smoke_test_artifact.read_text(encoding="utf-8")
        if (
            "Overall Result: PASS" not in smoke_test_artifact_body
            or "SMOKE_TOKEN=phase5 python3 scripts/mock_smoke.py"
            not in smoke_test_artifact_body
        ):
            raise RuntimeError(
                "smoke_test should record the passing result and executed command in the smoke-test artifact"
            )
        smoke_from_qa_dest = workspace / "executed-smoke-from-qa"
        shutil.copytree(executed_smoke_test_dest, smoke_from_qa_dest)
        smoke_from_qa_registry_path = (
            smoke_from_qa_dest / ".opencode" / "state" / "artifacts" / "registry.json"
        )
        smoke_from_qa_manifest_path = smoke_from_qa_dest / "tickets" / "manifest.json"
        smoke_from_qa_registry = json.loads(
            smoke_from_qa_registry_path.read_text(encoding="utf-8")
        )
        smoke_from_qa_manifest = json.loads(
            smoke_from_qa_manifest_path.read_text(encoding="utf-8")
        )
        smoke_from_qa_ticket = next(
            ticket
            for ticket in smoke_from_qa_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        for artifact in smoke_from_qa_registry.get("artifacts", []):
            if artifact.get("ticket_id") != "SETUP-001":
                continue
            if artifact.get("stage") == "smoke-test":
                artifact["trust_state"] = "historical"
                artifact["is_current"] = False
            if artifact.get("stage") == "qa":
                artifact["path"] = ".opencode/state/qa/setup-001-qa-report.md"
                artifact["summary"] = (
                    "Synthetic QA artifact with deterministic command evidence."
                )
        for artifact in smoke_from_qa_ticket.get("artifacts", []):
            if artifact.get("stage") == "smoke-test":
                artifact["trust_state"] = "historical"
                artifact["is_current"] = False
            if artifact.get("stage") == "qa":
                artifact["path"] = ".opencode/state/qa/setup-001-qa-report.md"
                artifact["summary"] = (
                    "Synthetic QA artifact with deterministic command evidence."
                )
        smoke_from_qa_registry_path.write_text(
            json.dumps(smoke_from_qa_registry, indent=2) + "\n",
            encoding="utf-8",
        )
        smoke_from_qa_manifest_path.write_text(
            json.dumps(smoke_from_qa_manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        seed_minimal_godot_project(smoke_from_qa_dest)
        smoke_from_qa_command = (
            f"godot4 --headless --path {smoke_from_qa_dest} --quit"
        )
        (
            smoke_from_qa_dest / ".opencode" / "state" / "qa" / "setup-001-qa-report.md"
        ).write_text(
            f"""# QA Report

## Commands Executed

```json
[
  {{
    "command": "{smoke_from_qa_command}",
    "cwd": ".",
    "exit_code": 0,
    "result": "PASS"
  }}
]
```

## Raw Command Output

```
smoke from qa
```

Overall Result: PASS
""",
            encoding="utf-8",
        )
        smoke_from_qa_result = run_generated_tool(
            smoke_from_qa_dest,
            ".opencode/tools/smoke_test.ts",
            {
                "ticket_id": "SETUP-001",
                "scope": "ticket",
            },
        )
        if smoke_from_qa_result["passed"] is not True:
            raise RuntimeError(
                "smoke_test should infer deterministic commands from the current QA artifact when no explicit override is supplied"
            )
        if smoke_from_qa_result["commands"][0]["command"] != smoke_from_qa_command:
            raise RuntimeError(
                "smoke_test should execute the deterministic command extracted from the current QA artifact"
            )
        smoke_closeout_manifest_path = executed_smoke_test_dest / "tickets" / "manifest.json"
        smoke_closeout_manifest = json.loads(
            smoke_closeout_manifest_path.read_text(encoding="utf-8")
        )
        smoke_closeout_ticket = next(
            ticket
            for ticket in smoke_closeout_manifest["tickets"]
            if ticket["id"] == "SETUP-001"
        )
        smoke_closeout_ticket["stage"] = "smoke-test"
        smoke_closeout_ticket["status"] = "smoke_test"
        smoke_closeout_manifest_path.write_text(
            json.dumps(smoke_closeout_manifest, indent=2) + "\n", encoding="utf-8"
        )
        smoke_closeout_workflow_path = (
            executed_smoke_test_dest / ".opencode" / "state" / "workflow-state.json"
        )
        smoke_closeout_workflow = json.loads(
            smoke_closeout_workflow_path.read_text(encoding="utf-8")
        )
        smoke_closeout_workflow["stage"] = "smoke-test"
        smoke_closeout_workflow["status"] = "smoke_test"
        smoke_closeout_workflow_path.write_text(
            json.dumps(smoke_closeout_workflow, indent=2) + "\n", encoding="utf-8"
        )
        post_smoke_lookup = run_generated_tool(
            executed_smoke_test_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if post_smoke_lookup["transition_guidance"]["recommended_ticket_update"] != {
            "ticket_id": "SETUP-001",
            "stage": "closeout",
            "status": "done",
            "activate": True,
        }:
            raise RuntimeError(
                "ticket_lookup should recommend closeout with status done after a passing smoke test"
            )
        post_smoke_closeout = run_generated_tool(
            executed_smoke_test_dest,
            ".opencode/tools/ticket_update.ts",
            post_smoke_lookup["transition_guidance"]["recommended_ticket_update"],
        )
        if (
            post_smoke_closeout["updated_ticket"]["stage"] != "closeout"
            or post_smoke_closeout["updated_ticket"]["status"] != "done"
        ):
            raise RuntimeError(
                "ticket_update should accept the guided closeout payload after a passing smoke test"
            )

        executed_smoke_fatal_stderr_dest = workspace / "executed-smoke-test-fatal-stderr"
        shutil.copytree(full_dest, executed_smoke_fatal_stderr_dest)
        seed_ready_bootstrap(executed_smoke_fatal_stderr_dest)
        register_current_ticket_artifact(
            executed_smoke_fatal_stderr_dest,
            ticket_id="SETUP-001",
            kind="qa",
            stage="qa",
            relative_path=".opencode/state/artifacts/setup-001-qa-fatal-stderr.md",
            summary="Synthetic QA artifact for fatal stderr smoke coverage.",
            content="# QA\n\nCommand: python3 -m py_compile scripts/smoke_test_scafforge.py\n\nQA evidence is current.\n",
        )
        write_executable(
            executed_smoke_fatal_stderr_dest / "scripts" / "mock_fatal_smoke.py",
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import sys",
                    'sys.stderr.write(\'SCRIPT ERROR: Parse Error: Identifier \"EnemyBrown\" not declared in the current scope.\\n\')',
                    'sys.stderr.write(\'ERROR: Failed to load script \"res://scripts/wave_spawner.gd\" with error \"Parse error\".\\n\')',
                    "sys.exit(0)",
                ]
            )
            + "\n",
        )
        smoke_fatal_stderr_result = run_generated_tool(
            executed_smoke_fatal_stderr_dest,
            ".opencode/tools/smoke_test.ts",
            {
                "ticket_id": "SETUP-001",
                "command_override": ["python3 scripts/mock_fatal_smoke.py"],
            },
        )
        if smoke_fatal_stderr_result["passed"] is not False:
            raise RuntimeError(
                "smoke_test should fail when a command exits 0 but emits fatal parse/load diagnostics on stderr"
            )
        if (
            smoke_fatal_stderr_result["failure_classification"] != "configuration"
            or smoke_fatal_stderr_result["commands"][0]["failure_classification"]
            != "syntax_error"
        ):
            raise RuntimeError(
                "smoke_test should classify exit-0 parse/load diagnostics as a syntax/configuration blocker"
            )
        smoke_fatal_artifact = executed_smoke_fatal_stderr_dest / str(
            smoke_fatal_stderr_result["smoke_test_artifact"]
        )
        smoke_fatal_artifact_body = smoke_fatal_artifact.read_text(encoding="utf-8")
        if (
            "Overall Result: FAIL" not in smoke_fatal_artifact_body
            or "Parse Error" not in smoke_fatal_artifact_body
        ):
            raise RuntimeError(
                "smoke_test should persist fatal stderr diagnostics in a failing smoke artifact"
            )

        executed_godot_export_stderr_dest = (
            workspace / "executed-smoke-test-godot-export-stderr"
        )
        shutil.copytree(full_dest, executed_godot_export_stderr_dest)
        seed_ready_bootstrap(executed_godot_export_stderr_dest)
        register_current_ticket_artifact(
            executed_godot_export_stderr_dest,
            ticket_id="SETUP-001",
            kind="qa",
            stage="qa",
            relative_path=".opencode/state/artifacts/setup-001-qa-godot-export.md",
            summary="Synthetic QA artifact for Godot export stderr smoke coverage.",
            content="# QA\n\nCommand: python3 -m py_compile scripts/smoke_test_scafforge.py\n\nQA evidence is current.\n",
        )
        write_executable(
            executed_godot_export_stderr_dest / "scripts" / "godot4",
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import sys",
                    'sys.stderr.write(\'SCRIPT ERROR: Parse Error: Identifier \"EnemyBrown\" not declared in the current scope.\\n\')',
                    'sys.stderr.write(\'ERROR: Failed to load script \"res://scripts/wave_spawner.gd\" with error \"Parse error\".\\n\')',
                    "sys.stdout.write('Export completed successfully\\n')",
                    "sys.exit(0)",
                ]
            )
            + "\n",
        )
        godot_export_stderr_result = run_generated_tool(
            executed_godot_export_stderr_dest,
            ".opencode/tools/smoke_test.ts",
            {
                "ticket_id": "SETUP-001",
                "command_override": [
                    "./scripts/godot4 --headless --path . --export-debug 'Android Debug' build/android/setup-001-debug.apk"
                ],
            },
        )
        if godot_export_stderr_result["passed"] is not False:
            raise RuntimeError(
                "smoke_test should fail when a Godot export command records parse/load errors even if the process exits 0"
            )
        if godot_export_stderr_result["failure_classification"] != "configuration":
            raise RuntimeError(
                "smoke_test should classify Godot export parse/load stderr as a configuration failure"
            )
        if godot_export_stderr_result["commands"][0]["failure_classification"] != "syntax_error":
            raise RuntimeError(
                "smoke_test should mark the failing Godot export command with syntax_error when stderr records parse/load failures"
            )
        godot_release_guard_dest = workspace / "executed-smoke-test-godot-release-guard"
        shutil.copytree(full_dest, godot_release_guard_dest)
        seed_ready_bootstrap(godot_release_guard_dest)
        seed_godot_android_target(godot_release_guard_dest)
        seed_minimal_godot_project(godot_release_guard_dest)
        manifest_path = godot_release_guard_dest / "tickets" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["tickets"].append(
            {
                "id": "RELEASE-001",
                "title": "Synthetic release gate",
                "wave": 99,
                "lane": "release-readiness",
                "parallel_safe": False,
                "overlap_risk": "high",
                "stage": "smoke_test",
                "status": "smoke_test",
                "resolution_state": "open",
                "verification_state": "suspect",
                "depends_on": ["SETUP-001"],
                "summary": "Synthetic release ticket for Godot release smoke gating coverage.",
                "acceptance": [],
                "decision_blockers": [],
                "artifacts": [],
                "follow_up_ticket_ids": [],
            }
        )
        manifest["active_ticket"] = "RELEASE-001"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        workflow_path = godot_release_guard_dest / ".opencode" / "state" / "workflow-state.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        workflow["active_ticket"] = "RELEASE-001"
        workflow["stage"] = "smoke_test"
        workflow["status"] = "smoke_test"
        workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
        register_current_ticket_artifact(
            godot_release_guard_dest,
            ticket_id="RELEASE-001",
            kind="qa",
            stage="qa",
            relative_path=".opencode/state/artifacts/release-001-qa-godot-release.md",
            summary="Synthetic QA artifact for release-readiness Godot load validation coverage.",
            content="# QA\n\nCommand: godot4 --headless --path . --export-debug Android Debug build/android/release-001-debug.apk\n\nQA evidence is current.\n",
        )
        write_executable(
            godot_release_guard_dest / "scripts" / "godot4",
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import sys",
                    'sys.stderr.write(\'SCRIPT ERROR: Parse Error: Identifier \"EnemyBrown\" not declared in the current scope.\\n\')',
                    'sys.stderr.write(\'ERROR: Failed to load script \"res://scripts/wave_spawner.gd\" with error \"Parse error\".\\n\')',
                    "sys.stdout.write('Export completed successfully\\n')",
                    "sys.exit(0)",
                ]
            )
            + "\n",
        )
        godot_release_guard_result = run_generated_tool(
            godot_release_guard_dest,
            ".opencode/tools/smoke_test.ts",
            {
                "ticket_id": "RELEASE-001",
                "command_override": [
                    "./scripts/godot4 --headless --path . --export-debug 'Android Debug' build/android/release-001-debug.apk"
                ],
            },
        )
        if godot_release_guard_result["passed"] is True:
            raise RuntimeError(
                "smoke_test should reject release-readiness Godot export output that records parse/load errors even when the export exits 0"
            )
        if len(godot_release_guard_result.get("commands", [])) != 1:
            raise RuntimeError(
                "smoke_test should stop the release-readiness command sequence as soon as the export command records parse/load failures"
            )
        if godot_release_guard_result["commands"][0]["failure_classification"] != "syntax_error":
            raise RuntimeError(
                "Godot release-readiness export validation should classify parse/load errors as syntax_error even when export itself exits 0"
            )

        executed_smoke_missing_exec_dest = (
            workspace / "executed-smoke-test-missing-exec"
        )
        shutil.copytree(full_dest, executed_smoke_missing_exec_dest)
        seed_ready_bootstrap(executed_smoke_missing_exec_dest)
        register_current_ticket_artifact(
            executed_smoke_missing_exec_dest,
            ticket_id="SETUP-001",
            kind="qa",
            stage="qa",
            relative_path=".opencode/state/artifacts/setup-001-qa-qa.md",
            summary="Synthetic QA artifact for smoke_test failure coverage.",
            content="# QA\n\nCommand: python3 -m py_compile scripts/smoke_test_scafforge.py\n\nQA evidence is current.\n",
        )
        smoke_missing_exec_result = run_generated_tool(
            executed_smoke_missing_exec_dest,
            ".opencode/tools/smoke_test.ts",
            {
                "ticket_id": "SETUP-001",
                "command_override": ["definitely-missing-phase5-command"],
            },
        )
        if smoke_missing_exec_result["passed"] is not False:
            raise RuntimeError(
                "smoke_test should fail when the explicit smoke command executable does not exist"
            )
        if (
            smoke_missing_exec_result["failure_classification"] != "environment"
            or smoke_missing_exec_result["host_surface_classification"]
            != "missing_executable"
        ):
            raise RuntimeError(
                "smoke_test should classify missing explicit smoke executables as an environment host-surface failure"
            )
        if (
            smoke_missing_exec_result["commands"][0]["missing_executable"]
            != "definitely-missing-phase5-command"
        ):
            raise RuntimeError(
                "smoke_test should report the missing explicit smoke executable by name"
            )
        quoted_override_dest = workspace / "executed-smoke-test-quoted-override"
        shutil.copytree(full_dest, quoted_override_dest)
        seed_ready_bootstrap(quoted_override_dest)
        register_current_ticket_artifact(
            quoted_override_dest,
            ticket_id="SETUP-001",
            kind="qa",
            stage="qa",
            relative_path=".opencode/state/qa/setup-001-qa-quoted.md",
            summary="Synthetic QA artifact for quoted smoke override coverage.",
            content="# QA\n\nVerdict: PASS\n\nCommand: python3 -m py_compile scripts/smoke_test_scafforge.py\n\n~~~~text\npython3 -m py_compile scripts/smoke_test_scafforge.py\nexit code: 0\nvalidation passed\n~~~~\n\nQA evidence is current and includes command output.\n",
        )
        write_executable(
            quoted_override_dest / "scripts" / "quoted_args.py",
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import json",
                    "import sys",
                    "print(json.dumps(sys.argv[1:]))",
                ]
            )
            + "\n",
        )
        quoted_override_result = run_generated_tool(
            quoted_override_dest,
            ".opencode/tools/smoke_test.ts",
            {
                "ticket_id": "SETUP-001",
                "command_override": [
                    "python3 scripts/quoted_args.py --pattern '(PlayerState|GlitchState).*Initialized'"
                ],
            },
        )
        if quoted_override_result["passed"] is not True:
            raise RuntimeError(
                "smoke_test should keep quoted shell-style override arguments grouped into a single argv token"
            )
        quoted_override_artifact = quoted_override_dest / str(
            quoted_override_result["smoke_test_artifact"]
        )
        if "(PlayerState|GlitchState).*Initialized" not in quoted_override_artifact.read_text(encoding="utf-8"):
            raise RuntimeError(
                "smoke_test should preserve quoted regex arguments inside the recorded smoke artifact"
            )

        hidden_clearable_pending_dest = (
            workspace / "hidden-clearable-pending-process-verification"
        )
        shutil.copytree(full_dest, hidden_clearable_pending_dest)
        seed_process_verification_clear_deadlock(
            hidden_clearable_pending_dest, stale_surfaces=True
        )
        hidden_clearable_pending_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(hidden_clearable_pending_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        hidden_clearable_pending_codes = {
            finding["code"]
            for finding in hidden_clearable_pending_audit.get("findings", [])
        }
        if "WFLOW008" not in hidden_clearable_pending_codes:
            raise RuntimeError(
                "A repo that strands a clearable pending_process_verification flag behind stale restart surfaces or a closed-ticket lease should emit WFLOW008"
            )

        active_priority_dest = workspace / "active-ticket-priority"
        shutil.copytree(full_dest, active_priority_dest)
        seed_open_active_ticket_with_pending_verification(active_priority_dest)
        run_json([sys.executable, str(REGENERATE), str(active_priority_dest)], ROOT)
        active_priority_start_here = (active_priority_dest / "START-HERE.md").read_text(
            encoding="utf-8"
        )
        if (
            "Keep SETUP-001 as the foreground ticket and continue its lifecycle from implementation."
            not in active_priority_start_here
        ):
            raise RuntimeError(
                "Restart regeneration should keep an open active ticket primary even when backlog process verification is pending"
            )

        reverification_deadlock_dest = workspace / "reverification-deadlock"
        shutil.copytree(full_dest, reverification_deadlock_dest)
        seed_reverification_deadlock(reverification_deadlock_dest)
        reverification_deadlock_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(reverification_deadlock_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        reverification_deadlock_codes = {
            finding["code"]
            for finding in reverification_deadlock_audit.get("findings", [])
        }
        if "WFLOW009" not in reverification_deadlock_codes:
            raise RuntimeError(
                "A repo whose reverification contract still requires closed tickets to hold a normal write lease should emit WFLOW009"
            )

        closed_follow_up_deadlock_dest = workspace / "closed-follow-up-deadlock"
        shutil.copytree(full_dest, closed_follow_up_deadlock_dest)
        seed_closed_follow_up_deadlock(closed_follow_up_deadlock_dest)
        closed_follow_up_deadlock_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(closed_follow_up_deadlock_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        closed_follow_up_deadlock_codes = {
            finding["code"]
            for finding in closed_follow_up_deadlock_audit.get("findings", [])
        }
        if "WFLOW018" not in closed_follow_up_deadlock_codes:
            raise RuntimeError(
                "A repo whose completed-ticket follow-up routing still requires normal write leases should emit WFLOW018"
            )

        historical_reconciliation_deadlock_dest = (
            workspace / "historical-reconciliation-deadlock"
        )
        shutil.copytree(full_dest, historical_reconciliation_deadlock_dest)
        seed_historical_reconciliation_deadlock(historical_reconciliation_deadlock_dest)
        historical_reconciliation_deadlock_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(historical_reconciliation_deadlock_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        historical_reconciliation_deadlock_codes = {
            finding["code"]
            for finding in historical_reconciliation_deadlock_audit.get("findings", [])
        }
        if "WFLOW024" not in historical_reconciliation_deadlock_codes:
            raise RuntimeError(
                "A repo with no legal reconciliation path for a superseded invalidated historical ticket should emit WFLOW024"
            )
        historical_reconciliation_revalidation = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(historical_reconciliation_deadlock_dest),
                "--format",
                "json",
                "--diagnosis-kind",
                "post_package_revalidation",
            ],
            ROOT,
        )
        historical_reconciliation_manifest = json.loads(
            Path(historical_reconciliation_revalidation["diagnosis_pack"]["path"])
            .joinpath("manifest.json")
            .read_text(encoding="utf-8")
        )
        if historical_reconciliation_manifest.get("package_work_required_first"):
            raise RuntimeError(
                "A stale repo with WFLOW024 should route to subject-repo repair when the installed Scafforge template already contains the reconciliation fix"
            )
        if (
            historical_reconciliation_manifest.get("recommended_next_step")
            != "subject_repo_repair"
        ):
            raise RuntimeError(
                "A post-package revalidation pack with only stale managed-surface WFLOW024 drift should recommend subject_repo_repair"
            )
        routed_recommendations = {
            item.get("source_finding_code"): item.get("route")
            for item in historical_reconciliation_manifest.get(
                "ticket_recommendations", []
            )
            if isinstance(item, dict)
        }
        if routed_recommendations.get("WFLOW024") != "scafforge-repair":
            raise RuntimeError(
                "WFLOW024 should route to scafforge-repair once the installed package template already contains the historical reconciliation fix"
            )

        contradictory_graph_dest = workspace / "contradictory-ticket-graph"
        shutil.copytree(full_dest, contradictory_graph_dest)
        seed_contradictory_follow_up_graph(contradictory_graph_dest)
        contradictory_graph_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(contradictory_graph_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        contradictory_graph_codes = {
            finding["code"] for finding in contradictory_graph_audit.get("findings", [])
        }
        if "WFLOW019" not in contradictory_graph_codes:
            raise RuntimeError(
                "A repo whose source/follow-up lineage contradicts its dependency graph should emit WFLOW019"
            )
        superseded_history_dest = workspace / "superseded-follow-up-history"
        shutil.copytree(full_dest, superseded_history_dest)
        seed_superseded_follow_up_history(superseded_history_dest)
        superseded_history_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(superseded_history_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        superseded_history_codes = {
            finding["code"] for finding in superseded_history_audit.get("findings", [])
        }
        if "WFLOW019" in superseded_history_codes:
            raise RuntimeError(
                "A superseded historical follow-up should not emit WFLOW019 merely because the parent no longer lists it in follow_up_ticket_ids"
            )
        superseded_parent_link_dest = workspace / "superseded-parent-link"
        shutil.copytree(full_dest, superseded_parent_link_dest)
        seed_parent_retains_superseded_follow_up(superseded_parent_link_dest)
        superseded_parent_link_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(superseded_parent_link_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        superseded_parent_link_codes = {
            finding["code"] for finding in superseded_parent_link_audit.get("findings", [])
        }
        if "WFLOW019" not in superseded_parent_link_codes:
            raise RuntimeError(
                "A parent that still lists a superseded follow-up should emit WFLOW019"
            )

        split_scope_drift_dest = workspace / "split-scope-drift"
        shutil.copytree(full_dest, split_scope_drift_dest)
        seed_open_parent_split_drift(split_scope_drift_dest)
        split_scope_drift_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(split_scope_drift_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        split_scope_drift_codes = {
            finding["code"] for finding in split_scope_drift_audit.get("findings", [])
        }
        if "WFLOW020" not in split_scope_drift_codes:
            raise RuntimeError(
                "A repo whose open-parent child decomposition uses a non-canonical source mode should emit WFLOW020"
            )
        blocked_split_parent_dest = workspace / "blocked-split-parent"
        shutil.copytree(full_dest, blocked_split_parent_dest)
        seed_blocked_split_parent(blocked_split_parent_dest)
        blocked_split_parent_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(blocked_split_parent_dest),
                "--format",
                "json",
                "--no-diagnosis-pack",
            ],
            ROOT,
        )
        blocked_split_parent_codes = {
            finding["code"]
            for finding in blocked_split_parent_audit.get("findings", [])
        }
        if "WFLOW020" not in blocked_split_parent_codes:
            raise RuntimeError(
                "A repo whose split parent is still marked blocked should emit WFLOW020"
            )

        redirected_output_dest = workspace / "redirected-output"
        shutil.copytree(full_dest, redirected_output_dest)
        redirected_output_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(redirected_output_dest),
                "--format",
                "json",
                "--emit-diagnosis-pack",
                "--diagnosis-output-dir",
                "/proc/scafforge-denied-output",
            ],
            ROOT,
        )
        redirected_output_codes = {
            finding["code"] for finding in redirected_output_audit.get("findings", [])
        }
        if "ENV004" not in redirected_output_codes:
            raise RuntimeError(
                "An unwritable diagnosis output path should emit ENV004 and fall back to a writable location"
            )
        diagnosis_pack_path = redirected_output_audit.get("diagnosis_pack", {}).get(
            "path", ""
        )
        if not diagnosis_pack_path.startswith("/tmp/scafforge-diagnosis/"):
            raise RuntimeError(
                "Audit should redirect unwritable diagnosis-pack output to /tmp/scafforge-diagnosis"
            )

        repair_redirected_output_dest = workspace / "repair-redirected-output"
        shutil.copytree(full_dest, repair_redirected_output_dest)
        make_stack_skill_non_placeholder(repair_redirected_output_dest)
        repair_redirected_output_dir = workspace / "repair-diagnosis-output"
        repair_redirected_result = subprocess.run(
            [
                sys.executable,
                str(PUBLIC_REPAIR),
                str(repair_redirected_output_dest),
                "--skip-deterministic-refresh",
                "--diagnosis-output-dir",
                str(repair_redirected_output_dir),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        try:
            repair_redirected_payload = json.loads(repair_redirected_result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Public managed repair runner should emit JSON even when verification finds host-level prerequisites.\n"
                f"STDOUT:\n{repair_redirected_result.stdout}\nSTDERR:\n{repair_redirected_result.stderr}"
            ) from exc
        repair_diagnosis_pack_path = repair_redirected_payload.get(
            "diagnosis_pack", {}
        ).get("path", "")
        if repair_diagnosis_pack_path != str(repair_redirected_output_dir):
            raise RuntimeError(
                "Public managed repair runner should honor --diagnosis-output-dir for the post-repair diagnosis pack"
            )

        package_work_first_repair_dest = workspace / "package-work-first-repair"
        shutil.copytree(full_dest, package_work_first_repair_dest)
        package_work_diagnosis_root = package_work_first_repair_dest / "diagnosis"
        shutil.rmtree(package_work_diagnosis_root, ignore_errors=True)
        package_work_diagnosis_root.mkdir(parents=True, exist_ok=True)
        write_diagnosis_manifest(
            package_work_diagnosis_root / "20260328-120000",
            generated_at="2026-03-28T12:00:00Z",
            finding_count=1,
            recommendations=[
                {
                    "source_finding_code": "WFLOW024",
                    "route": "manual-prerequisite",
                    "title": "historical reconciliation deadlock",
                }
            ],
        )
        package_work_manifest_path = (
            package_work_diagnosis_root / "20260328-120000" / "manifest.json"
        )
        package_work_manifest = json.loads(
            package_work_manifest_path.read_text(encoding="utf-8")
        )
        package_work_manifest["package_work_required_first"] = True
        package_work_manifest["recommended_next_step"] = "scafforge_package_work"
        package_work_manifest_path.write_text(
            json.dumps(package_work_manifest, indent=2) + "\n", encoding="utf-8"
        )
        package_work_first_repair = subprocess.run(
            [
                sys.executable,
                str(PUBLIC_REPAIR),
                str(package_work_first_repair_dest),
                "--skip-deterministic-refresh",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if package_work_first_repair.returncode == 0:
            raise RuntimeError(
                "Public managed repair runner should refuse a repair basis that still requires package work first"
            )
        if (
            "package work first" not in package_work_first_repair.stderr
            and "package work first" not in package_work_first_repair.stdout
        ):
            raise RuntimeError(
                "Public managed repair runner should explain that package work must be cleared before subject-repo repair"
            )

        python_dest = workspace / "python-uv"
        shutil.copytree(full_dest, python_dest)
        seed_uv_python_fixture(python_dest)
        python_audit = run_json(
            [sys.executable, str(AUDIT), str(python_dest), "--format", "json"], ROOT
        )
        python_codes = {finding["code"] for finding in python_audit.get("findings", [])}
        if "BOOT001" in python_codes:
            raise RuntimeError(
                "A uv-shaped repo with the current bootstrap template should not emit BOOT001"
            )
        if "BOOT002" in python_codes:
            raise RuntimeError(
                "A uv-shaped repo with the current bootstrap template should not emit BOOT002"
            )

        legacy_smoke_dest = workspace / "legacy-smoke"
        shutil.copytree(python_dest, legacy_smoke_dest)
        seed_legacy_smoke_test_tool(legacy_smoke_dest)
        legacy_smoke_audit = run_json(
            [sys.executable, str(AUDIT), str(legacy_smoke_dest), "--format", "json"],
            ROOT,
        )
        legacy_smoke_codes = {
            finding["code"] for finding in legacy_smoke_audit.get("findings", [])
        }
        if "WFLOW001" not in legacy_smoke_codes:
            raise RuntimeError(
                "A uv-shaped repo with a legacy system-python smoke_test tool should emit WFLOW001"
            )

        legacy_smoke_override_dest = workspace / "legacy-smoke-override"
        shutil.copytree(full_dest, legacy_smoke_override_dest)
        seed_legacy_smoke_override_tool(legacy_smoke_override_dest)
        legacy_smoke_override_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(legacy_smoke_override_dest),
                "--format",
                "json",
            ],
            ROOT,
        )
        legacy_smoke_override_codes = {
            finding["code"]
            for finding in legacy_smoke_override_audit.get("findings", [])
        }
        if "WFLOW016" not in legacy_smoke_override_codes:
            raise RuntimeError(
                "A repo whose smoke_test tool passes command_override directly into argv should emit WFLOW016"
            )

        legacy_review_dest = workspace / "legacy-review"
        shutil.copytree(full_dest, legacy_review_dest)
        seed_legacy_review_contract(legacy_review_dest)
        legacy_review_audit = run_json(
            [sys.executable, str(AUDIT), str(legacy_review_dest), "--format", "json"],
            ROOT,
        )
        legacy_review_codes = {
            finding["code"] for finding in legacy_review_audit.get("findings", [])
        }
        if "WFLOW003" not in legacy_review_codes:
            raise RuntimeError(
                "A repo with plan-review docs but no explicit plan_review workflow contract should emit WFLOW003"
            )

        legacy_transition_dest = workspace / "legacy-transition"
        shutil.copytree(full_dest, legacy_transition_dest)
        seed_legacy_stage_transition_contract(legacy_transition_dest)
        legacy_transition_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(legacy_transition_dest),
                "--format",
                "json",
            ],
            ROOT,
        )
        legacy_transition_codes = {
            finding["code"] for finding in legacy_transition_audit.get("findings", [])
        }
        if "WFLOW004" not in legacy_transition_codes:
            raise RuntimeError(
                "A repo with status-gated implementation or unvalidated lifecycle stages should emit WFLOW004"
            )

        smoke_bypass_dest = workspace / "smoke-bypass"
        shutil.copytree(full_dest, smoke_bypass_dest)
        seed_smoke_artifact_bypass(smoke_bypass_dest)
        smoke_bypass_audit = run_json(
            [sys.executable, str(AUDIT), str(smoke_bypass_dest), "--format", "json"],
            ROOT,
        )
        smoke_bypass_codes = {
            finding["code"] for finding in smoke_bypass_audit.get("findings", [])
        }
        if "WFLOW005" not in smoke_bypass_codes:
            raise RuntimeError(
                "A repo that allows smoke-test proof through generic artifact tools should emit WFLOW005"
            )

        handoff_conflict_dest = workspace / "handoff-conflict"
        shutil.copytree(full_dest, handoff_conflict_dest)
        seed_handoff_ownership_conflict(handoff_conflict_dest)
        handoff_conflict_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(handoff_conflict_dest),
                "--format",
                "json",
            ],
            ROOT,
        )
        handoff_conflict_codes = {
            finding["code"] for finding in handoff_conflict_audit.get("findings", [])
        }
        if "WFLOW007" not in handoff_conflict_codes:
            raise RuntimeError(
                "A repo whose docs-handoff path conflicts with plugin enforcement should emit WFLOW007"
            )

        team_leader_dest = workspace / "team-leader-drift"
        shutil.copytree(full_dest, team_leader_dest)
        seed_team_leader_workflow_drift(team_leader_dest)
        team_leader_audit = run_json(
            [sys.executable, str(AUDIT), str(team_leader_dest), "--format", "json"],
            ROOT,
        )
        team_leader_codes = {
            finding["code"] for finding in team_leader_audit.get("findings", [])
        }
        if "WFLOW006" not in team_leader_codes:
            raise RuntimeError(
                "A repo whose team leader prompt omits transition guidance, stop rules, or command boundaries should emit WFLOW006"
            )

        helper_tool_dest = workspace / "helper-tool-exposure"
        shutil.copytree(full_dest, helper_tool_dest)
        seed_helper_tool_exposure(helper_tool_dest)
        helper_tool_log = seed_helper_tool_failure_log(helper_tool_dest)
        helper_tool_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(helper_tool_dest),
                "--format",
                "json",
                "--supporting-log",
                str(helper_tool_log),
            ],
            ROOT,
        )
        helper_tool_codes = {
            finding["code"] for finding in helper_tool_audit.get("findings", [])
        }
        if "WFLOW015" not in helper_tool_codes:
            raise RuntimeError(
                "A repo whose runtime exposes helper-only workflow internals or transcript-level missing-execute failures should emit WFLOW015"
            )

        smoke_override_log_dest = workspace / "smoke-override-log"
        shutil.copytree(full_dest, smoke_override_log_dest)
        smoke_override_log = seed_smoke_override_failure_log(smoke_override_log_dest)
        smoke_override_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(smoke_override_log_dest),
                "--format",
                "json",
                "--supporting-log",
                str(smoke_override_log),
            ],
            ROOT,
        )
        smoke_override_codes = {
            finding["code"] for finding in smoke_override_audit.get("findings", [])
        }
        if "WFLOW016" not in smoke_override_codes:
            raise RuntimeError(
                "A transcript where smoke_test treats KEY=VALUE as the executable should emit WFLOW016"
            )

        legacy_smoke_acceptance_dest = workspace / "legacy-smoke-acceptance"
        shutil.copytree(full_dest, legacy_smoke_acceptance_dest)
        seed_legacy_smoke_acceptance_tool(legacy_smoke_acceptance_dest)
        legacy_smoke_acceptance_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(legacy_smoke_acceptance_dest),
                "--format",
                "json",
            ],
            ROOT,
        )
        legacy_smoke_acceptance_codes = {
            finding["code"]
            for finding in legacy_smoke_acceptance_audit.get("findings", [])
        }
        if "WFLOW017" not in legacy_smoke_acceptance_codes:
            raise RuntimeError(
                "A repo whose smoke_test tool ignores ticket acceptance commands should emit WFLOW017"
            )

        smoke_acceptance_log_dest = workspace / "smoke-acceptance-log"
        shutil.copytree(full_dest, smoke_acceptance_log_dest)
        smoke_acceptance_log = seed_smoke_acceptance_scope_log(
            smoke_acceptance_log_dest
        )
        smoke_acceptance_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(smoke_acceptance_log_dest),
                "--format",
                "json",
                "--supporting-log",
                str(smoke_acceptance_log),
            ],
            ROOT,
        )
        smoke_acceptance_codes = {
            finding["code"] for finding in smoke_acceptance_audit.get("findings", [])
        }
        if "WFLOW017" not in smoke_acceptance_codes:
            raise RuntimeError(
                "A transcript where smoke_test ignores a ticket-defined smoke command should emit WFLOW017"
            )

        handoff_lease_dest = workspace / "handoff-lease-contradiction"
        shutil.copytree(full_dest, handoff_lease_dest)
        handoff_lease_log = seed_handoff_lease_contradiction_log(handoff_lease_dest)
        handoff_lease_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(handoff_lease_dest),
                "--format",
                "json",
                "--supporting-log",
                str(handoff_lease_log),
            ],
            ROOT,
        )
        handoff_lease_codes = {
            finding["code"] for finding in handoff_lease_audit.get("findings", [])
        }
        if "WFLOW022" not in handoff_lease_codes:
            raise RuntimeError(
                "A transcript where handoff_publish still needs a closed ticket lease should emit WFLOW022"
            )

        acceptance_tension_dest = workspace / "acceptance-scope-tension"
        shutil.copytree(full_dest, acceptance_tension_dest)
        acceptance_tension_log = seed_acceptance_scope_tension_log(
            acceptance_tension_dest
        )
        acceptance_tension_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(acceptance_tension_dest),
                "--format",
                "json",
                "--supporting-log",
                str(acceptance_tension_log),
            ],
            ROOT,
        )
        acceptance_tension_codes = {
            finding["code"] for finding in acceptance_tension_audit.get("findings", [])
        }
        if "WFLOW023" not in acceptance_tension_codes:
            raise RuntimeError(
                "A transcript where a ticket's literal acceptance command depends on later-ticket scope should emit WFLOW023"
            )

        operator_trap_dest = workspace / "operator-trap"
        shutil.copytree(full_dest, operator_trap_dest)
        operator_trap_log = seed_operator_trap_log(operator_trap_dest)
        operator_trap_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(operator_trap_dest),
                "--format",
                "json",
                "--supporting-log",
                str(operator_trap_log),
            ],
            ROOT,
        )
        operator_trap_codes = {
            finding["code"] for finding in operator_trap_audit.get("findings", [])
        }
        if "SESSION006" not in operator_trap_codes:
            raise RuntimeError(
                "A transcript with multiple contradictory blockers and workaround pressure should emit SESSION006"
            )

        coordinator_artifact_dest = workspace / "coordinator-artifacts"
        shutil.copytree(full_dest, coordinator_artifact_dest)
        coordinator_log = seed_coordinator_artifact_log(coordinator_artifact_dest)
        coordinator_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(coordinator_artifact_dest),
                "--format",
                "json",
                "--supporting-log",
                str(coordinator_log),
            ],
            ROOT,
        )
        coordinator_codes = {
            finding["code"] for finding in coordinator_audit.get("findings", [])
        }
        if "SESSION005" not in coordinator_codes:
            raise RuntimeError(
                "A transcript where the coordinator writes specialist artifacts should emit SESSION005"
            )

        thin_skill_dest = workspace / "thin-ticket-skill"
        shutil.copytree(full_dest, thin_skill_dest)
        seed_thin_ticket_execution(thin_skill_dest)
        thin_skill_audit = run_json(
            [sys.executable, str(AUDIT), str(thin_skill_dest), "--format", "json"], ROOT
        )
        thin_skill_codes = {
            finding["code"] for finding in thin_skill_audit.get("findings", [])
        }
        if "SKILL002" not in thin_skill_codes:
            raise RuntimeError(
                "A repo with a thin ticket-execution skill should emit SKILL002"
            )

        deadlock_dest = workspace / "python-deadlock"
        shutil.copytree(python_dest, deadlock_dest)
        seed_bootstrap_deadlock(deadlock_dest)
        deadlock_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(deadlock_dest),
                "--format",
                "json",
                "--emit-diagnosis-pack",
            ],
            ROOT,
        )
        deadlock_codes = {
            finding["code"] for finding in deadlock_audit.get("findings", [])
        }
        if "BOOT001" not in deadlock_codes:
            raise RuntimeError(
                "A failed bootstrap artifact with missing pip should emit BOOT001"
            )
        recommendations = (
            deadlock_audit.get("diagnosis_pack", {})
            .get("manifest", {})
            .get("ticket_recommendations", [])
        )
        if not any(
            item.get("source_finding_code") == "BOOT001"
            and item.get("route") == "scafforge-repair"
            for item in recommendations
        ):
            raise RuntimeError(
                "BOOT001 should route to scafforge-repair in the diagnosis pack"
            )

        mismatch_dest = workspace / "bootstrap-command-mismatch"
        shutil.copytree(python_dest, mismatch_dest)
        seed_bootstrap_command_layout_mismatch(mismatch_dest)
        mismatch_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(mismatch_dest),
                "--format",
                "json",
                "--emit-diagnosis-pack",
            ],
            ROOT,
        )
        mismatch_codes = {
            finding["code"] for finding in mismatch_audit.get("findings", [])
        }
        if "BOOT002" not in mismatch_codes:
            raise RuntimeError(
                "A bootstrap artifact whose uv sync command omits required dev flags should emit BOOT002"
            )
        if "ENV002" in mismatch_codes:
            raise RuntimeError(
                "A managed bootstrap command/layout mismatch should not be downgraded to ENV002"
            )
        mismatch_recommendations = (
            mismatch_audit.get("diagnosis_pack", {})
            .get("manifest", {})
            .get("ticket_recommendations", [])
        )
        if not any(
            item.get("source_finding_code") == "BOOT002"
            and item.get("route") == "scafforge-repair"
            for item in mismatch_recommendations
        ):
            raise RuntimeError(
                "BOOT002 should route to scafforge-repair in the diagnosis pack"
            )

        model_dest = workspace / "model-drift"
        shutil.copytree(full_dest, model_dest)
        seed_legacy_model_drift(model_dest)
        model_audit = run_json(
            [sys.executable, str(AUDIT), str(model_dest), "--format", "json"], ROOT
        )
        model_findings = {
            finding["code"]: finding for finding in model_audit.get("findings", [])
        }
        model_codes = set(model_findings)
        if "MODEL001" not in model_codes:
            raise RuntimeError(
                "A repo with deprecated MiniMax surfaces and no model-operating-profile should emit MODEL001"
            )
        if model_findings["MODEL001"].get("severity") != "error":
            raise RuntimeError(
                "Deprecated package-managed MiniMax drift should emit MODEL001 as an error, not a warning"
            )
        markdown_verdict_audit_dest = workspace / "markdown-verdict-audit"
        shutil.copytree(full_dest, markdown_verdict_audit_dest)
        seed_ready_bootstrap(markdown_verdict_audit_dest)
        seed_review_stage_with_verdict(markdown_verdict_audit_dest, "**Verdict**: PASS")
        seed_legacy_markdown_verdict_parser(markdown_verdict_audit_dest)
        markdown_verdict_audit = run_json(
            [sys.executable, str(AUDIT), str(markdown_verdict_audit_dest), "--format", "json"],
            ROOT,
        )
        markdown_verdict_codes = {
            finding["code"] for finding in markdown_verdict_audit.get("findings", [])
        }
        if "WFLOW026" not in markdown_verdict_codes:
            raise RuntimeError(
                "Audit should emit WFLOW026 when the repo parser still treats explicit markdown verdict labels as unclear"
            )
        audit_reporting_verdict_module = load_python_module(
            ROOT / "skills" / "scafforge-audit" / "scripts" / "audit_reporting.py",
            "scafforge_smoke_audit_reporting_wflow026_route",
        )
        markdown_verdict_recommendations = (
            audit_reporting_verdict_module.build_ticket_recommendations(
                [
                    SimpleNamespace(
                        code="WFLOW026",
                        severity="error",
                        problem="Legacy verdict parser blocks explicit QA/review verdicts.",
                        root_cause="Synthetic legacy parser smoke fixture.",
                        files=[".opencode/lib/workflow.ts"],
                        safer_pattern="Use the widened shared verdict parser.",
                        evidence=["synthetic markdown verdict evidence"],
                        provenance="script",
                    )
                ],
                audit_reporting_verdict_module.AuditReportingContext(
                    package_root=ROOT, current_package_commit="smoke"
                ),
                markdown_verdict_audit_dest,
            )
        )
        if not any(
            item.get("source_finding_code") == "WFLOW026"
            and item.get("route") == "scafforge-repair"
            for item in markdown_verdict_recommendations
            if isinstance(item, dict)
        ):
            raise RuntimeError(
                "WFLOW026 should route to scafforge-repair once the installed package template contains the widened verdict parser"
            )
        markdown_verdict_repaired_dest = workspace / "markdown-verdict-repaired"
        shutil.copytree(full_dest, markdown_verdict_repaired_dest)
        seed_ready_bootstrap(markdown_verdict_repaired_dest)
        seed_review_stage_with_verdict(markdown_verdict_repaired_dest, "**Verdict**: PASS")
        markdown_verdict_repaired_audit = run_json(
            [sys.executable, str(AUDIT), str(markdown_verdict_repaired_dest), "--format", "json"],
            ROOT,
        )
        markdown_verdict_repaired_codes = {
            finding["code"] for finding in markdown_verdict_repaired_audit.get("findings", [])
        }
        if "WFLOW026" in markdown_verdict_repaired_codes:
            raise RuntimeError(
                "Audit should not emit WFLOW026 when the current repo-local workflow parser already supports the widened verdict family"
            )

        spinner_gap_dest = workspace / "spinner-target-completion-gap"
        shutil.copytree(full_dest, spinner_gap_dest)
        make_stack_skill_non_placeholder(spinner_gap_dest)
        seed_spinner_like_android_gap(spinner_gap_dest)
        spinner_gap_audit = run_json(
            [sys.executable, str(AUDIT), str(spinner_gap_dest), "--format", "json"],
            ROOT,
        )
        spinner_gap_codes = {
            finding["code"] for finding in spinner_gap_audit.get("findings", [])
        }
        for expected_code in ("WFLOW025", "EXEC-GODOT-005a", "FINISH001"):
            if expected_code not in spinner_gap_codes:
                raise RuntimeError(
                    f"Spinner-like Android completion gaps should emit {expected_code}"
                )

        finish_claim_dest = workspace / "finish-claim-gap"
        shutil.copytree(full_dest, finish_claim_dest)
        make_stack_skill_non_placeholder(finish_claim_dest)
        seed_finish_claim_with_open_finish_ticket(finish_claim_dest)
        finish_claim_audit = run_json(
            [sys.executable, str(AUDIT), str(finish_claim_dest), "--format", "json"],
            ROOT,
        )
        finish_claim_codes = {
            finding["code"] for finding in finish_claim_audit.get("findings", [])
        }
        if "FINISH002" not in finish_claim_codes:
            raise RuntimeError(
                "Consumer-facing repos that claim ready state while finish-owning tickets remain open should emit FINISH002"
            )

        incomplete_finish_dest = workspace / "incomplete-finish-contract"
        shutil.copytree(full_dest, incomplete_finish_dest)
        make_stack_skill_non_placeholder(incomplete_finish_dest)
        seed_incomplete_finish_contract(incomplete_finish_dest)
        incomplete_finish_audit = run_json(
            [sys.executable, str(AUDIT), str(incomplete_finish_dest), "--format", "json"],
            ROOT,
        )
        incomplete_finish_findings = [
            finding
            for finding in incomplete_finish_audit.get("findings", [])
            if isinstance(finding, dict) and finding.get("code") == "FINISH001"
        ]
        if not incomplete_finish_findings:
            raise RuntimeError(
                "Consumer-facing repos with an incomplete Product Finish Contract should emit FINISH001"
            )
        incomplete_finish_evidence = "\n".join(
            line
            for finding in incomplete_finish_findings
            for line in finding.get("evidence", [])
            if isinstance(line, str)
        )
        if "missing finish-contract fields" not in incomplete_finish_evidence:
            raise RuntimeError(
                "FINISH001 should explain which Product Finish Contract fields are missing"
            )

        weak_finish_dest = workspace / "weak-generated-finish-contract"
        shutil.copytree(full_dest, weak_finish_dest)
        make_stack_skill_non_placeholder(weak_finish_dest)
        seed_weak_generated_finish_contract(weak_finish_dest)
        weak_finish_audit = run_json(
            [sys.executable, str(AUDIT), str(weak_finish_dest), "--format", "json"],
            ROOT,
        )
        weak_finish_findings = [
            finding
            for finding in weak_finish_audit.get("findings", [])
            if isinstance(finding, dict) and finding.get("code") == "FINISH004"
        ]
        if not weak_finish_findings:
            raise RuntimeError(
                "Interactive repos that still use weak machine-generated finish signals should emit FINISH004"
            )
        weak_finish_evidence = "\n".join(
            line
            for finding in weak_finish_findings
            for line in finding.get("evidence", [])
            if isinstance(line, str)
        )
        if "generic finish_acceptance_signals" not in weak_finish_evidence:
            raise RuntimeError(
                "FINISH004 should explain that the repo is still using weak machine-generated finish_acceptance_signals"
            )
        run_json([sys.executable, str(REPAIR), str(weak_finish_dest)], ROOT)
        repaired_weak_finish_brief = (
            weak_finish_dest / "docs" / "spec" / "CANONICAL-BRIEF.md"
        ).read_text(encoding="utf-8")
        if "playable shipped loop on current builds with working controls/input" not in repaired_weak_finish_brief:
            raise RuntimeError(
                "Managed repair should replace weak generated finish_acceptance_signals with stronger interactive proof text"
            )
        repaired_weak_finish_manifest = json.loads(
            (weak_finish_dest / "tickets" / "manifest.json").read_text(encoding="utf-8")
        )
        repaired_finish_validate = next(
            ticket
            for ticket in repaired_weak_finish_manifest.get("tickets", [])
            if isinstance(ticket, dict) and ticket.get("id") == "FINISH-VALIDATE-001"
        )
        repaired_finish_acceptance = [
            item
            for item in repaired_finish_validate.get("acceptance", [])
            if isinstance(item, str)
        ]
        if not any(
            "user-observable interaction evidence" in item
            for item in repaired_finish_acceptance
        ):
            raise RuntimeError(
                "Managed repair should strengthen FINISH-VALIDATE-001 acceptance for interactive repos"
            )
        weak_finish_post_repair = run_json(
            [sys.executable, str(AUDIT), str(weak_finish_dest), "--format", "json"],
            ROOT,
        )
        weak_finish_post_codes = {
            finding["code"] for finding in weak_finish_post_repair.get("findings", [])
        }
        if "FINISH004" in weak_finish_post_codes:
            raise RuntimeError(
                "FINISH004 should clear after managed repair upgrades the finish contract and finish-validation ticket"
            )

        ref_scan_dest = workspace / "reference-scan-exclusion"
        shutil.copytree(full_dest, ref_scan_dest)
        make_stack_skill_non_placeholder(ref_scan_dest)
        seed_reference_scan_exclusion_case(ref_scan_dest)
        ref_scan_audit = run_json(
            [sys.executable, str(AUDIT), str(ref_scan_dest), "--format", "json"],
            ROOT,
        )
        ref_findings = [
            finding
            for finding in ref_scan_audit.get("findings", [])
            if isinstance(finding, dict) and finding.get("code") == "REF-003"
        ]
        if not ref_findings:
            raise RuntimeError(
                "Reference-integrity audit should still emit REF-003 for repo-owned broken imports"
            )
        ref_evidence = "\n".join(
            line
            for finding in ref_findings
            for line in finding.get("evidence", [])
            if isinstance(line, str)
        )
        if "node_modules" in ref_evidence:
            raise RuntimeError(
                "Reference-integrity audit should ignore broken imports under excluded dependency trees such as node_modules"
            )

        broken_venv_dest = workspace / "broken-venv"
        shutil.copytree(full_dest, broken_venv_dest)
        make_stack_skill_non_placeholder(broken_venv_dest)
        seed_broken_repo_venv(broken_venv_dest)
        broken_venv_audit = run_json(
            [sys.executable, str(AUDIT), str(broken_venv_dest), "--format", "json"],
            ROOT,
        )
        broken_venv_codes = {
            finding["code"] for finding in broken_venv_audit.get("findings", [])
        }
        if "EXEC-ENV-001" not in broken_venv_codes:
            raise RuntimeError(
                "Audit should emit EXEC-ENV-001 when a repo-local .venv exists but its interpreter is broken"
            )

        remediation_review_dest = workspace / "remediation-review-evidence"
        shutil.copytree(full_dest, remediation_review_dest)
        make_stack_skill_non_placeholder(remediation_review_dest)
        seed_remediation_review_without_command_evidence(remediation_review_dest)
        remediation_review_audit = run_json(
            [sys.executable, str(AUDIT), str(remediation_review_dest), "--format", "json"],
            ROOT,
        )
        remediation_review_codes = {
            finding["code"] for finding in remediation_review_audit.get("findings", [])
        }
        if "EXEC-REMED-001" not in remediation_review_codes:
            raise RuntimeError(
                "Audit should emit EXEC-REMED-001 when a remediation review artifact lacks runnable command evidence"
            )
        non_remediation_review_dest = workspace / "non-remediation-review-evidence"
        shutil.copytree(full_dest, non_remediation_review_dest)
        make_stack_skill_non_placeholder(non_remediation_review_dest)
        seed_non_remediation_finding_source_review(non_remediation_review_dest)
        non_remediation_review_audit = run_json(
            [sys.executable, str(AUDIT), str(non_remediation_review_dest), "--format", "json"],
            ROOT,
        )
        non_remediation_review_findings = [
            finding
            for finding in non_remediation_review_audit.get("findings", [])
            if isinstance(finding, dict) and finding.get("code") == "EXEC-REMED-001"
        ]
        if non_remediation_review_findings:
            raise RuntimeError(
                "Audit should not emit EXEC-REMED-001 for non-remediation tickets that merely carry finding_source"
            )
        valid_remediation_dest = workspace / "remediation-review-glitch-style"
        shutil.copytree(full_dest, valid_remediation_dest)
        make_stack_skill_non_placeholder(valid_remediation_dest)
        seed_glitch_style_remediation_review(valid_remediation_dest)
        valid_remediation_audit = run_json(
            [sys.executable, str(AUDIT), str(valid_remediation_dest), "--format", "json"],
            ROOT,
        )
        valid_remediation_findings = [
            finding
            for finding in valid_remediation_audit.get("findings", [])
            if isinstance(finding, dict) and finding.get("code") == "EXEC-REMED-001"
        ]
        if valid_remediation_findings:
            raise RuntimeError(
                "Audit should accept remediation review artifacts that use bold labels with fenced command and output evidence"
            )
        valid_remediation_overall_dest = workspace / "remediation-review-overall-result"
        shutil.copytree(full_dest, valid_remediation_overall_dest)
        make_stack_skill_non_placeholder(valid_remediation_overall_dest)
        seed_glitch_style_remediation_review(
            valid_remediation_overall_dest, "Overall Result: **PASS**"
        )
        valid_remediation_overall_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(valid_remediation_overall_dest),
                "--format",
                "json",
            ],
            ROOT,
        )
        valid_remediation_overall_findings = [
            finding
            for finding in valid_remediation_overall_audit.get("findings", [])
            if isinstance(finding, dict) and finding.get("code") == "EXEC-REMED-001"
        ]
        if valid_remediation_overall_findings:
            raise RuntimeError(
                "Audit should accept remediation review artifacts that use `Overall Result: **PASS**` with fenced command and output evidence"
            )
        valid_remediation_heading_dest = workspace / "remediation-review-verdict-heading"
        shutil.copytree(full_dest, valid_remediation_heading_dest)
        make_stack_skill_non_placeholder(valid_remediation_heading_dest)
        seed_glitch_style_remediation_review(
            valid_remediation_heading_dest, "## Verdict\n\n**PASS**"
        )
        valid_remediation_heading_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(valid_remediation_heading_dest),
                "--format",
                "json",
            ],
            ROOT,
        )
        valid_remediation_heading_findings = [
            finding
            for finding in valid_remediation_heading_audit.get("findings", [])
            if isinstance(finding, dict) and finding.get("code") == "EXEC-REMED-001"
        ]
        if valid_remediation_heading_findings:
            raise RuntimeError(
                "Audit should accept remediation review artifacts that use `## Verdict` followed by `**PASS**` with fenced command and output evidence"
            )
        inline_exact_remediation_audit_dest = (
            workspace / "remediation-review-inline-exact"
        )
        shutil.copytree(full_dest, inline_exact_remediation_audit_dest)
        make_stack_skill_non_placeholder(inline_exact_remediation_audit_dest)
        seed_inline_exact_remediation_review(inline_exact_remediation_audit_dest)
        inline_exact_remediation_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(inline_exact_remediation_audit_dest),
                "--format",
                "json",
            ],
            ROOT,
        )
        inline_exact_remediation_findings = [
            finding
            for finding in inline_exact_remediation_audit.get("findings", [])
            if isinstance(finding, dict) and finding.get("code") == "EXEC-REMED-001"
        ]
        if inline_exact_remediation_findings:
            raise RuntimeError(
                "Audit should accept remediation review artifacts that use `Exact command run`, inline `Raw output`, and `Result: PASS`"
            )

        empty_remediation_dest = workspace / "remediation-review-empty-output"
        shutil.copytree(full_dest, empty_remediation_dest)
        make_stack_skill_non_placeholder(empty_remediation_dest)
        seed_remediation_review_with_empty_output_block(empty_remediation_dest)
        empty_remediation_audit = run_json(
            [sys.executable, str(AUDIT), str(empty_remediation_dest), "--format", "json"],
            ROOT,
        )
        empty_remediation_findings = [
            finding
            for finding in empty_remediation_audit.get("findings", [])
            if isinstance(finding, dict) and finding.get("code") == "EXEC-REMED-001"
        ]
        if not empty_remediation_findings:
            raise RuntimeError(
                "Audit should emit EXEC-REMED-001 when a remediation review artifact uses an empty raw-output block"
            )

        remediation_follow_up_dest = workspace / "remediation-follow-up-history-sources"
        shutil.copytree(full_dest, remediation_follow_up_dest)
        make_stack_skill_non_placeholder(remediation_follow_up_dest)
        remediation_follow_up_manifest = (
            remediation_follow_up_dest / "diagnosis" / "2099-01-01T00-00-00Z"
            / "manifest.json"
        )
        remediation_follow_up_manifest.parent.mkdir(parents=True, exist_ok=True)
        history_review_path = (
            ".opencode/state/artifacts/history/remed-010/review/"
            "2026-04-09T22-35-04-635Z-review.md"
        )
        remediation_follow_up_manifest.write_text(
            json.dumps(
                {
                    "ticket_recommendations": [
                        {
                            "id": "REMED-900",
                            "route": "ticket-pack-builder",
                            "title": "Record superseding remediation evidence",
                            "description": "Remediate EXEC-REMED-001 by recording runnable evidence for the current remediation surface.",
                            "source_finding_code": "EXEC-REMED-001",
                            "source_files": [
                                "tickets/manifest.json",
                                history_review_path,
                            ],
                        }
                    ]
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        remediation_follow_up_result = run_json(
            [
                sys.executable,
                str(
                    ROOT
                    / "skills"
                    / "ticket-pack-builder"
                    / "scripts"
                    / "apply_remediation_follow_up.py"
                ),
                str(remediation_follow_up_dest),
                "--diagnosis",
                str(remediation_follow_up_manifest),
            ],
            ROOT,
        )
        if "REMED-900" not in remediation_follow_up_result.get("created_tickets", []):
            raise RuntimeError(
                "apply_remediation_follow_up.py should create remediation tickets from diagnosis recommendations"
            )
        remediation_follow_up_ticket = next(
            ticket
            for ticket in json.loads(
                (remediation_follow_up_dest / "tickets" / "manifest.json").read_text(
                    encoding="utf-8"
                )
            )["tickets"]
            if ticket["id"] == "REMED-900"
        )
        remediation_follow_up_summary = remediation_follow_up_ticket["summary"]
        if (
            f"Affected surfaces: tickets/manifest.json, {history_review_path}."
            in remediation_follow_up_summary
        ):
            raise RuntimeError(
                "Remediation follow-up tickets must not frame immutable history artifacts as writable affected surfaces"
            )
        for expected in (
            "Affected surfaces: tickets/manifest.json.",
            f"Historical evidence sources: {history_review_path}.",
            "read-only context",
        ):
            if expected not in remediation_follow_up_summary:
                raise RuntimeError(
                    "apply_remediation_follow_up.py should preserve history paths as read-only evidence sources in the ticket summary"
                )
        if not any(
            "read-only evidence sources" in item
            for item in remediation_follow_up_ticket.get("acceptance", [])
        ):
            raise RuntimeError(
                "Remediation follow-up acceptance should tell downstream agents to produce superseding current evidence instead of editing immutable history"
            )
        if (
            remediation_follow_up_ticket.get("source_mode") != "split_scope"
            or remediation_follow_up_ticket.get("split_kind")
            != "parallel_independent"
        ):
            raise RuntimeError(
                "apply_remediation_follow_up.py should create EXEC-REMED follow-up tickets as parallel-independent split children when they extend an open parent ticket"
            )
        remediation_manifest_path = remediation_follow_up_dest / "tickets" / "manifest.json"
        remediation_manifest_data = json.loads(
            remediation_manifest_path.read_text(encoding="utf-8")
        )
        remediation_parent_ticket = next(
            ticket
            for ticket in remediation_manifest_data["tickets"]
            if ticket["id"] == remediation_follow_up_ticket["source_ticket_id"]
        )
        existing_remed_ticket = next(
            ticket
            for ticket in remediation_manifest_data["tickets"]
            if ticket["id"] == "REMED-900"
        )
        existing_remed_ticket["summary"] = (
            "Remediate EXEC-REMED-001 by recording runnable evidence for the current remediation surface. "
            f"Affected surfaces: tickets/manifest.json, {history_review_path}."
        )
        existing_remed_ticket["acceptance"] = [
            "The validated finding `EXEC-REMED-001` no longer reproduces.",
            "Current quality checks rerun with evidence tied to the fix approach.",
        ]
        remediation_manifest_data["tickets"].append(
            {
                "id": "MODEL-999",
                "title": "Stale remediation parent",
                "wave": existing_remed_ticket["wave"],
                "lane": "model-generation",
                "parallel_safe": False,
                "overlap_risk": "low",
                "stage": "review",
                "status": "review",
                "depends_on": [],
                "summary": "Synthetic stale parent for remediation follow-up reconciliation coverage.",
                "acceptance": [
                    "Stale parent no longer owns the follow-up after reconciliation."
                ],
                "decision_blockers": [],
                "artifacts": [],
                "resolution_state": "open",
                "verification_state": "suspect",
                "follow_up_ticket_ids": ["REMED-900"],
            }
        )
        existing_remed_ticket["source_ticket_id"] = "MODEL-999"
        existing_remed_ticket["split_kind"] = "sequential_dependent"
        remediation_parent_ticket.setdefault("follow_up_ticket_ids", []).append(
            "REMED-901"
        )
        remediation_parent_ticket.setdefault("decision_blockers", []).append(
            f"Sequential split: this ticket ({remediation_parent_ticket['id']}) must complete its parent-owned work before child ticket REMED-901 may be foregrounded."
        )
        remediation_manifest_data["tickets"].append(
            {
                "id": "REMED-901",
                "title": "Stale remediation ticket",
                "wave": existing_remed_ticket["wave"] + 1,
                "lane": "remediation",
                "parallel_safe": False,
                "overlap_risk": "low",
                "stage": "planning",
                "status": "todo",
                "depends_on": [],
                "summary": "Stale remediation follow-up that should be superseded.",
                "acceptance": ["Stale remediation ticket is superseded."],
                "decision_blockers": [],
                "artifacts": [],
                "resolution_state": "open",
                "verification_state": "suspect",
                "finding_source": "EXEC-REMED-001",
                "source_ticket_id": remediation_parent_ticket["id"],
                "follow_up_ticket_ids": [],
                "source_mode": "split_scope",
                "split_kind": "sequential_dependent",
            }
        )
        remediation_manifest_path.write_text(
            json.dumps(remediation_manifest_data, indent=2) + "\n",
            encoding="utf-8",
        )
        remediation_ticket_path = remediation_follow_up_dest / "tickets" / "REMED-900.md"
        remediation_ticket_path.write_text(
            "# REMED-900: Record superseding remediation evidence\n\n"
            "## Summary\n\n"
            "Remediate EXEC-REMED-001 by recording runnable evidence for the current remediation surface. "
            f"Affected surfaces: tickets/manifest.json, {history_review_path}.\n\n"
            "## Notes\n\n"
            "Keep this note.\n",
            encoding="utf-8",
        )
        remediation_follow_up_rerun = run_json(
            [
                sys.executable,
                str(
                    ROOT
                    / "skills"
                    / "ticket-pack-builder"
                    / "scripts"
                    / "apply_remediation_follow_up.py"
                ),
                str(remediation_follow_up_dest),
                "--diagnosis",
                str(remediation_follow_up_manifest),
            ],
            ROOT,
        )
        if "REMED-900" not in remediation_follow_up_rerun.get("created_tickets", []):
            raise RuntimeError(
                "apply_remediation_follow_up.py should report existing remediation tickets it reconciles from diagnosis recommendations"
            )
        if "REMED-901" not in remediation_follow_up_rerun.get(
            "superseded_tickets", []
        ):
            raise RuntimeError(
                "apply_remediation_follow_up.py should supersede stale remediation tickets that are no longer recommended by the current diagnosis"
            )
        refreshed_remediation_ticket = next(
            ticket
            for ticket in json.loads(
                remediation_manifest_path.read_text(encoding="utf-8")
            )["tickets"]
            if ticket["id"] == "REMED-900"
        )
        superseded_remediation_ticket = next(
            ticket
            for ticket in json.loads(
                remediation_manifest_path.read_text(encoding="utf-8")
            )["tickets"]
            if ticket["id"] == "REMED-901"
        )
        if (
            f"Affected surfaces: tickets/manifest.json, {history_review_path}."
            in refreshed_remediation_ticket["summary"]
        ):
            raise RuntimeError(
                "apply_remediation_follow_up.py should rewrite stale existing remediation summaries instead of preserving immutable history paths as writable affected surfaces"
            )
        if refreshed_remediation_ticket.get("split_kind") != "parallel_independent":
            raise RuntimeError(
                "apply_remediation_follow_up.py should refresh existing EXEC-REMED follow-up tickets to the current split_kind policy"
            )
        if (
            refreshed_remediation_ticket.get("source_ticket_id")
            != remediation_parent_ticket["id"]
        ):
            raise RuntimeError(
                "apply_remediation_follow_up.py should restore the canonical source_ticket_id for existing remediation follow-up tickets"
            )
        if (
            superseded_remediation_ticket.get("resolution_state") != "superseded"
            or superseded_remediation_ticket.get("status") != "done"
        ):
            raise RuntimeError(
                "apply_remediation_follow_up.py should supersede stale remediation tickets that fall out of the current diagnosis set"
            )
        refreshed_manifest_after_rerun = json.loads(
            remediation_manifest_path.read_text(encoding="utf-8")
        )
        refreshed_parent_ticket = next(
            ticket
            for ticket in refreshed_manifest_after_rerun["tickets"]
            if ticket["id"] == remediation_parent_ticket["id"]
        )
        if "REMED-901" in refreshed_parent_ticket.get("follow_up_ticket_ids", []):
            raise RuntimeError(
                "apply_remediation_follow_up.py should unlink superseded stale remediation tickets from their source parent"
            )
        refreshed_stale_parent = next(
            ticket
            for ticket in refreshed_manifest_after_rerun["tickets"]
            if ticket["id"] == "MODEL-999"
        )
        if "REMED-900" in refreshed_stale_parent.get("follow_up_ticket_ids", []):
            raise RuntimeError(
                "apply_remediation_follow_up.py should remove current remediation tickets from stale historical parents when source ownership changes"
            )
        if "REMED-900" not in refreshed_parent_ticket.get("follow_up_ticket_ids", []):
            raise RuntimeError(
                "apply_remediation_follow_up.py should ensure the canonical current parent lists the reconciled remediation ticket in follow_up_ticket_ids"
            )
        if any(
            "REMED-901" in blocker
            for blocker in refreshed_parent_ticket.get("decision_blockers", [])
        ):
            raise RuntimeError(
                "apply_remediation_follow_up.py should remove stale split-parent blocker text when a remediation ticket is superseded"
            )
        refreshed_parent_ticket.setdefault("follow_up_ticket_ids", []).append("REMED-901")
        remediation_manifest_path.write_text(
            json.dumps(refreshed_manifest_after_rerun, indent=2) + "\n",
            encoding="utf-8",
        )
        remediation_follow_up_reheal = run_json(
            [
                sys.executable,
                str(remediation_follow_up_script_path),
                str(remediation_follow_up_dest),
                "--diagnosis",
                str(remediation_follow_up_manifest),
            ],
            ROOT,
        )
        if "REMED-901" not in remediation_follow_up_reheal.get(
            "superseded_tickets", []
        ):
            raise RuntimeError(
                "apply_remediation_follow_up.py should heal stale parent linkage for already-superseded remediation tickets"
            )
        rehealed_manifest = json.loads(
            remediation_manifest_path.read_text(encoding="utf-8")
        )
        rehealed_parent_ticket = next(
            ticket
            for ticket in rehealed_manifest["tickets"]
            if ticket["id"] == remediation_parent_ticket["id"]
        )
        if "REMED-901" in rehealed_parent_ticket.get("follow_up_ticket_ids", []):
            raise RuntimeError(
                "apply_remediation_follow_up.py should unlink already-superseded remediation tickets on later reruns when stale parent linkage survives"
            )
        refreshed_ticket_doc = remediation_ticket_path.read_text(encoding="utf-8")
        for expected in (
            f"Historical evidence sources: {history_review_path}.",
            "Keep this note.",
        ):
            if expected not in refreshed_ticket_doc:
                raise RuntimeError(
                    "apply_remediation_follow_up.py should refresh existing remediation ticket files while preserving their notes"
                )

        stale_godot_dest = workspace / "stale-godot-project"
        shutil.copytree(full_dest, stale_godot_dest)
        make_stack_skill_non_placeholder(stale_godot_dest)
        seed_stale_godot_project_config(stale_godot_dest)
        stale_godot_audit = run_json(
            [sys.executable, str(AUDIT), str(stale_godot_dest), "--format", "json"],
            ROOT,
        )
        stale_godot_codes = {
            finding["code"] for finding in stale_godot_audit.get("findings", [])
        }
        if "PROJ-VER-001" not in stale_godot_codes:
            raise RuntimeError(
                "Audit should emit PROJ-VER-001 for stale Godot 4 project configuration markers"
            )

        repair_dest = workspace / "repair"
        shutil.copytree(full_dest, repair_dest)
        shutil.rmtree(repair_dest / "diagnosis", ignore_errors=True)
        (repair_dest / "docs" / "process" / "workflow.md").write_text(
            "# drifted workflow\n", encoding="utf-8"
        )
        seed_legacy_bootstrap_tool(repair_dest)
        repair_payload = run_json([sys.executable, str(REPAIR), str(repair_dest)], ROOT)
        repair_diff_summary = repair_payload.get("diff_summary", {})
        if "docs/process/workflow.md" not in repair_diff_summary.get(
            "files_modified", []
        ):
            raise RuntimeError(
                "Deterministic repair should emit a file-level diff summary for modified managed surfaces"
            )
        if repair_payload.get("verification", {}).get("clean") is True:
            raise RuntimeError(
                "Deterministic repair verification should not report clean while pending process verification or placeholder local-skill follow-up remains"
            )
        if (
            repair_payload.get("verification", {}).get("pending_process_verification")
            is not True
        ):
            raise RuntimeError(
                "Repair verification should report pending_process_verification when the workflow state reopens backlog trust checks"
            )

        repaired_workflow = json.loads(
            (repair_dest / ".opencode" / "state" / "workflow-state.json").read_text(
                encoding="utf-8"
            )
        )
        if repaired_workflow.get("process_version") != 7:
            raise RuntimeError(
                "Repair should update workflow-state to process version 7"
            )
        if repaired_workflow.get("pending_process_verification") is not True:
            raise RuntimeError("Repair should reopen post-migration verification")
        if not repaired_workflow.get("process_last_changed_at"):
            raise RuntimeError("Repair should record process_last_changed_at")
        for key in ("bootstrap", "lane_leases", "state_revision"):
            if key not in repaired_workflow:
                raise RuntimeError(f"Repair should preserve workflow key `{key}`")

        repaired_provenance = json.loads(
            (
                repair_dest / ".opencode" / "meta" / "bootstrap-provenance.json"
            ).read_text(encoding="utf-8")
        )
        if not repaired_provenance.get("repair_history"):
            raise RuntimeError("Repair should append repair_history")
        latest_repair_entry = repaired_provenance["repair_history"][-1]
        if latest_repair_entry.get("diff_summary", {}).get("files_modified") != repair_diff_summary.get(
            "files_modified", []
        ):
            raise RuntimeError(
                "Repair provenance should preserve the deterministic managed-surface diff summary"
            )
        if latest_repair_entry.get("process_version_before") is None or latest_repair_entry.get(
            "process_version_after"
        ) != 7:
            raise RuntimeError(
                "Repair provenance should record process version before and after deterministic replacement"
            )
        if latest_repair_entry.get("repair_follow_on_outcome") != repair_payload["execution_record"]["repair_follow_on_outcome"]:
            raise RuntimeError(
                "Repair history should preserve the final repair_follow_on outcome for cycle auditing"
            )
        if latest_repair_entry.get("handoff_allowed") != repair_payload["execution_record"]["handoff_allowed"]:
            raise RuntimeError(
                "Repair history should preserve the final publish-gate result for cycle auditing"
            )
        if latest_repair_entry.get("verification_passed") != repair_payload["execution_record"]["verification_status"]["verification_passed"]:
            raise RuntimeError(
                "Repair history should preserve verification_passed for cycle auditing"
            )
        if latest_repair_entry.get("blocking_reasons") != repair_payload["execution_record"]["blocking_reasons"]:
            raise RuntimeError(
                "Repair history should preserve blocking_reasons for cycle auditing"
            )
        latest_repair_verification_summary = latest_repair_entry.get("verification_summary")
        if not isinstance(latest_repair_verification_summary, dict):
            raise RuntimeError(
                "Repair history should preserve the verification_summary payload for cycle auditing"
            )
        if latest_repair_verification_summary.get("verification_basis") != repair_payload["execution_record"]["verification_status"]["verification_basis"]:
            raise RuntimeError(
                "Repair history should preserve verification_basis for cycle auditing"
            )
        if latest_repair_verification_summary.get("current_state_clean") != repair_payload["execution_record"]["verification_status"]["current_state_clean"]:
            raise RuntimeError(
                "Repair history should preserve current_state_clean for cycle auditing"
            )
        managed_surfaces = repaired_provenance.get("managed_surfaces", {})
        replace_on_retrofit = managed_surfaces.get("replace_on_retrofit", [])
        project_specific_follow_up = managed_surfaces.get(
            "project_specific_follow_up", []
        )
        if "opencode.jsonc" not in replace_on_retrofit:
            raise RuntimeError(
                "Repair provenance should list opencode.jsonc as a deterministic managed surface"
            )
        if ".opencode/skills" not in project_specific_follow_up:
            raise RuntimeError(
                "Repair provenance should mark .opencode/skills as a project-specific follow-up surface"
            )

        repaired_workflow_doc = (
            repair_dest / "docs" / "process" / "workflow.md"
        ).read_text(encoding="utf-8")
        if "# Workflow" not in repaired_workflow_doc:
            raise RuntimeError(
                "Repair should restore docs/process/workflow.md from the scaffold"
            )
        repaired_bootstrap_tool = (
            repair_dest / ".opencode" / "tools" / "environment_bootstrap.ts"
        ).read_text(encoding="utf-8")
        for expected in (
            "[project.optional-dependencies]",
            "[dependency-groups]",
            "[tool.uv.dev-dependencies]",
            "[tool.pytest.ini_options]",
        ):
            if expected not in repaired_bootstrap_tool:
                raise RuntimeError(
                    "Repair should restore the broadened environment_bootstrap surface for alternate dev layouts and pyproject-only pytest detection"
                )
        repaired_handoff = (
            repair_dest / ".opencode" / "tools" / "handoff_publish.ts"
        ).read_text(encoding="utf-8")
        if "validateHandoffNextAction" not in repaired_handoff or repaired_handoff.find(
            "const handoffBlocker = await validateHandoffNextAction"
        ) >= repaired_handoff.find("await refreshRestartSurfaces"):
            raise RuntimeError(
                "Repair should restore truthful handoff gating before restart-surface publication"
            )

        invalid_follow_on_stage_dest = workspace / "invalid-follow-on-stage"
        shutil.copytree(full_dest, invalid_follow_on_stage_dest)
        make_stack_skill_non_placeholder(invalid_follow_on_stage_dest)
        invalid_public_stage = subprocess.run(
            [
                sys.executable,
                str(PUBLIC_REPAIR),
                str(invalid_follow_on_stage_dest),
                "--skip-deterministic-refresh",
                "--stage-complete",
                "not-a-real-stage",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if invalid_public_stage.returncode == 0:
            raise RuntimeError(
                "Public managed repair runner should reject unknown follow-on stage names instead of silently recording them"
            )
        if (
            "Unknown repair follow-on stage" not in invalid_public_stage.stderr
            and "Unknown repair follow-on stage" not in invalid_public_stage.stdout
        ):
            raise RuntimeError(
                "Public managed repair runner should explain unknown follow-on stage rejection"
            )
        invalid_record_stage = subprocess.run(
            [
                sys.executable,
                str(RECORD_REPAIR_STAGE),
                str(invalid_follow_on_stage_dest),
                "--stage",
                "not-a-real-stage",
                "--completed-by",
                "tester",
                "--summary",
                "Invalid stage should fail.",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if invalid_record_stage.returncode == 0:
            raise RuntimeError(
                "record_repair_stage_completion should reject unknown follow-on stage names instead of silently persisting them"
            )
        if (
            "Unknown repair follow-on stage" not in invalid_record_stage.stderr
            and "Unknown repair follow-on stage" not in invalid_record_stage.stdout
        ):
            raise RuntimeError(
                "record_repair_stage_completion should explain unknown follow-on stage rejection"
            )

        source_follow_up_repair_dest = workspace / "source-follow-up-repair"
        shutil.copytree(full_dest, source_follow_up_repair_dest)
        make_stack_skill_non_placeholder(source_follow_up_repair_dest)
        seed_failing_pytest_suite(source_follow_up_repair_dest)
        stale_blender_skill_dir = (
            source_follow_up_repair_dest
            / ".opencode"
            / "skills"
            / "blender-mcp-workflow"
        )
        if stale_blender_skill_dir.exists():
            shutil.rmtree(stale_blender_skill_dir)
        source_follow_up_provenance_path = (
            source_follow_up_repair_dest
            / ".opencode"
            / "meta"
            / "bootstrap-provenance.json"
        )
        source_follow_up_provenance = json.loads(
            source_follow_up_provenance_path.read_text(encoding="utf-8")
        )
        source_follow_up_provenance["repair_history"] = []
        source_follow_up_provenance_path.write_text(
            json.dumps(source_follow_up_provenance, indent=2) + "\n",
            encoding="utf-8",
        )
        source_follow_up_diagnosis_root = source_follow_up_repair_dest / "diagnosis"
        if source_follow_up_diagnosis_root.exists():
            shutil.rmtree(source_follow_up_diagnosis_root)
        if host_has_uv:
            invalid_known_stage_process = subprocess.run(
                [
                    sys.executable,
                    str(PUBLIC_REPAIR),
                    str(source_follow_up_repair_dest),
                    "--skip-deterministic-refresh",
                    "--stage-complete",
                    "project-skill-bootstrap",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            if invalid_known_stage_process.returncode == 0:
                raise RuntimeError(
                    "Public managed repair runner should reject known follow-on stages that are not part of the current repair cycle"
                )
            if (
                "not part of the current repair cycle"
                not in invalid_known_stage_process.stderr
                and "not part of the current repair cycle"
                not in invalid_known_stage_process.stdout
            ):
                raise RuntimeError(
                    "Public managed repair runner should explain current-cycle rejection for known but non-required follow-on stages"
                )
            invalid_known_evidence_rel = (
                ".opencode/state/artifacts/history/repair/non-required-stage.md"
            )
            invalid_known_evidence_path = (
                source_follow_up_repair_dest / invalid_known_evidence_rel
            )
            invalid_known_evidence_path.parent.mkdir(parents=True, exist_ok=True)
            invalid_known_evidence_path.write_text(
                "# Non-required stage\n", encoding="utf-8"
            )
            invalid_known_record_stage = subprocess.run(
                [
                    sys.executable,
                    str(RECORD_REPAIR_STAGE),
                    str(source_follow_up_repair_dest),
                    "--stage",
                    "project-skill-bootstrap",
                    "--completed-by",
                    "tester",
                    "--summary",
                    "Known but non-required stage should fail.",
                    "--evidence",
                    invalid_known_evidence_rel,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            if invalid_known_record_stage.returncode == 0:
                raise RuntimeError(
                    "record_repair_stage_completion should reject known follow-on stages that are not part of the current repair cycle"
                )
            if (
                "not part of the current repair cycle"
                not in invalid_known_record_stage.stderr
                and "not part of the current repair cycle"
                not in invalid_known_record_stage.stdout
            ):
                raise RuntimeError(
                    "record_repair_stage_completion should explain current-cycle rejection for known but non-required follow-on stages"
                )
            source_follow_up_initial_process = subprocess.run(
                [
                    sys.executable,
                    str(PUBLIC_REPAIR),
                    str(source_follow_up_repair_dest),
                    "--skip-deterministic-refresh",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            if source_follow_up_initial_process.returncode not in {0, 3}:
                raise RuntimeError(
                    "Source follow-up repair probe failed unexpectedly.\n"
                    f"STDOUT:\n{source_follow_up_initial_process.stdout}\n"
                    f"STDERR:\n{source_follow_up_initial_process.stderr}"
                )
            source_follow_up_initial = json.loads(
                source_follow_up_initial_process.stdout
            )
            if not source_follow_up_initial["execution_record"]["blocking_reasons"]:
                raise RuntimeError(
                    "A source-follow-up repair fixture should remain blocked before any recorded follow-on completion exists"
                )
            placeholder_reconcile_dest = workspace / "placeholder-reconcile"
            shutil.copytree(full_dest, placeholder_reconcile_dest)
            seed_failing_pytest_suite(placeholder_reconcile_dest)
            placeholder_initial_process = subprocess.run(
                [
                    sys.executable,
                    str(PUBLIC_REPAIR),
                    str(placeholder_reconcile_dest),
                    "--skip-deterministic-refresh",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            if placeholder_initial_process.returncode not in {0, 3}:
                raise RuntimeError(
                    "Placeholder reconcile repair probe failed unexpectedly.\n"
                    f"STDOUT:\n{placeholder_initial_process.stdout}\n"
                    f"STDERR:\n{placeholder_initial_process.stderr}"
                )
            placeholder_initial = json.loads(placeholder_initial_process.stdout)
            if not any(
                "placeholder_local_skills_survived_refresh" in reason
                for reason in placeholder_initial["execution_record"]["blocking_reasons"]
            ):
                raise RuntimeError(
                    "A placeholder-skill repair fixture should preserve the placeholder_local_skills_survived_refresh blocker before follow-on completion"
                )
            placeholder_follow_on_state_path = (
                placeholder_reconcile_dest
                / ".opencode"
                / "meta"
                / "repair-follow-on-state.json"
            )
            placeholder_follow_on_state = json.loads(
                placeholder_follow_on_state_path.read_text(encoding="utf-8")
            )
            placeholder_cycle = placeholder_follow_on_state["cycle_id"]
            make_stack_skill_non_placeholder(placeholder_reconcile_dest)
            placeholder_ticket_pack_rel = (
                ".opencode/state/artifacts/history/repair/ticket-pack-builder-completion.md"
            )
            placeholder_ticket_pack_path = (
                placeholder_reconcile_dest / placeholder_ticket_pack_rel
            )
            placeholder_ticket_pack_path.parent.mkdir(parents=True, exist_ok=True)
            placeholder_ticket_pack_path.write_text(
                "# Repair Follow-On Completion\n\n"
                "- completed_stage: ticket-pack-builder\n"
                f"- cycle_id: {placeholder_cycle}\n"
                "- completed_by: ticket-pack-builder\n\n"
                "## Summary\n\n"
                "- Routed source follow-up into the ticket system after project-skill regeneration.\n",
                encoding="utf-8",
            )
            run_json(
                [
                    sys.executable,
                    str(RECORD_REPAIR_STAGE),
                    str(placeholder_reconcile_dest),
                    "--stage",
                    "project-skill-bootstrap",
                    "--completed-by",
                    "project-skill-bootstrap",
                    "--summary",
                    "Replaced placeholder stack standards with repo-specific guidance.",
                    "--evidence",
                    ".opencode/skills/stack-standards/SKILL.md",
                ],
                ROOT,
            )
            run_json(
                [
                    sys.executable,
                    str(RECORD_REPAIR_STAGE),
                    str(placeholder_reconcile_dest),
                    "--stage",
                    "ticket-pack-builder",
                    "--completed-by",
                    "ticket-pack-builder",
                    "--summary",
                    "Routed source follow-up into the ticket system after project-skill regeneration.",
                    "--evidence",
                    placeholder_ticket_pack_rel,
                ],
                ROOT,
            )
            placeholder_reconcile = run_json(
                [
                    sys.executable,
                    str(RECONCILE_REPAIR),
                    str(placeholder_reconcile_dest),
                ],
                ROOT,
            )
            if placeholder_reconcile.get("status") != "reconciled":
                raise RuntimeError(
                    "reconcile_repair_follow_on should clear placeholder_local_skills_survived_refresh once project-skill-bootstrap completed and the live repo-local skills are no longer placeholder text"
                )
            placeholder_workflow = json.loads(
                (
                    placeholder_reconcile_dest
                    / ".opencode"
                    / "state"
                    / "workflow-state.json"
                ).read_text(encoding="utf-8")
            )
            if placeholder_workflow["repair_follow_on"]["outcome"] != "source_follow_up":
                raise RuntimeError(
                    "reconcile_repair_follow_on should convert repaired placeholder-skill blockers into source_follow_up once the current cycle is complete"
                )
        polluted_follow_on_state_dest = workspace / "polluted-follow-on-state"
        shutil.copytree(full_dest, polluted_follow_on_state_dest)
        make_stack_skill_non_placeholder(polluted_follow_on_state_dest)
        seed_failing_pytest_suite(polluted_follow_on_state_dest)
        polluted_blender_skill_dir = (
            polluted_follow_on_state_dest
            / ".opencode"
            / "skills"
            / "blender-mcp-workflow"
        )
        if polluted_blender_skill_dir.exists():
            shutil.rmtree(polluted_blender_skill_dir)
        polluted_provenance_path = (
            polluted_follow_on_state_dest
            / ".opencode"
            / "meta"
            / "bootstrap-provenance.json"
        )
        polluted_provenance = json.loads(
            polluted_provenance_path.read_text(encoding="utf-8")
        )
        polluted_provenance["repair_history"] = []
        polluted_provenance_path.write_text(
            json.dumps(polluted_provenance, indent=2) + "\n",
            encoding="utf-8",
        )
        polluted_diagnosis_root = polluted_follow_on_state_dest / "diagnosis"
        if polluted_diagnosis_root.exists():
            shutil.rmtree(polluted_diagnosis_root)
        polluted_initial_process = subprocess.run(
            [
                sys.executable,
                str(PUBLIC_REPAIR),
                str(polluted_follow_on_state_dest),
                "--skip-deterministic-refresh",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        polluted_initial = json.loads(polluted_initial_process.stdout)
        if not polluted_initial["execution_record"]["blocking_reasons"]:
            raise RuntimeError(
                "A repair run without any valid follow-on completion should remain blocked before polluted-state pruning is tested"
            )
        polluted_state_path = (
            polluted_follow_on_state_dest
            / ".opencode"
            / "meta"
            / "repair-follow-on-state.json"
        )
        polluted_state = json.loads(polluted_state_path.read_text(encoding="utf-8"))
        polluted_state["required_stages"].append("bogus-stage")
        polluted_state["stage_records"]["bogus-stage"] = {
            "stage": "bogus-stage",
            "status": "completed",
            "completion_mode": "recorded_execution",
            "evidence_paths": [
                ".opencode/state/artifacts/history/repair/bogus-stage.md"
            ],
            "completed_by": "bogus-stage",
            "last_recorded_at": "2026-03-30T00:00:00Z",
            "last_checked_at": "2026-03-30T00:00:00Z",
            "last_updated_at": "2026-03-30T00:00:00Z",
        }
        polluted_state["history"].append(
            {
                "recorded_at": "2026-03-30T00:00:00Z",
                "stage": "bogus-stage",
                "status": "completed",
                "completion_mode": "recorded_execution",
            }
        )
        polluted_state_path.write_text(
            json.dumps(polluted_state, indent=2) + "\n", encoding="utf-8"
        )
        pruned_follow_on_state_process = subprocess.run(
            [
                sys.executable,
                str(PUBLIC_REPAIR),
                str(polluted_follow_on_state_dest),
                "--skip-deterministic-refresh",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if pruned_follow_on_state_process.returncode == 0:
            raise RuntimeError(
                "Pruning unknown legacy follow-on stage records should not make the repair runner succeed while real ticket follow-up remains"
            )
        pruned_follow_on_state = json.loads(pruned_follow_on_state_process.stdout)
        if (
            "bogus-stage"
            in pruned_follow_on_state["execution_record"][
                "recorded_completed_stages"
            ]
        ):
            raise RuntimeError(
                "Managed repair should prune unknown legacy follow-on stage records instead of trusting them as completed"
            )
        if pruned_follow_on_state["execution_record"]["pruned_unknown_stages"] != [
            "bogus-stage"
        ]:
            raise RuntimeError(
                "Managed repair should report which unknown legacy follow-on stages were pruned from polluted state"
            )
        if (
            "bogus-stage"
            in pruned_follow_on_state["execution_record"][
                "follow_on_tracking_state"
            ]["stage_records"]
        ):
            raise RuntimeError(
                "Managed repair should remove unknown legacy follow-on stage records from the persisted tracking state"
            )
        prune_history = pruned_follow_on_state["execution_record"][
            "follow_on_tracking_state"
        ].get("history", [])
        if not any(
            item.get("status") == "pruned_unknown_stages"
            and item.get("pruned_unknown_stages") == ["bogus-stage"]
            for item in prune_history
            if isinstance(item, dict)
        ):
            raise RuntimeError(
                "Managed repair should leave a history event when polluted unknown follow-on stages are pruned"
            )
        if not pruned_follow_on_state["execution_record"]["blocking_reasons"]:
            raise RuntimeError(
                "Pruning unknown legacy follow-on stage records should not clear the real ticket follow-up blocker"
            )

        source_follow_on_state_path = (
            source_follow_up_repair_dest
            / ".opencode"
            / "meta"
            / "repair-follow-on-state.json"
        )
        source_follow_on_state = json.loads(
            source_follow_on_state_path.read_text(encoding="utf-8")
        )
        source_follow_on_cycle = source_follow_on_state["cycle_id"]
        source_ticket_pack_rel = ".opencode/state/artifacts/history/repair/ticket-pack-builder-completion.md"
        source_ticket_pack_path = (
            source_follow_up_repair_dest / source_ticket_pack_rel
        )
        source_ticket_pack_path.parent.mkdir(parents=True, exist_ok=True)
        source_ticket_pack_path.write_text(
            "# Repair Follow-On Completion\n\n"
            "- completed_stage: ticket-pack-builder\n"
            f"- cycle_id: {source_follow_on_cycle}\n"
            "- completed_by: ticket-pack-builder\n\n"
            "## Summary\n\n"
            "- Routed source follow-up into the ticket system.\n",
            encoding="utf-8",
        )
        source_handoff_rel = (
            ".opencode/state/artifacts/history/repair/handoff-brief-completion.md"
        )
        source_handoff_path = source_follow_up_repair_dest / source_handoff_rel
        source_handoff_path.parent.mkdir(parents=True, exist_ok=True)
        source_handoff_path.write_text(
            "# Repair Follow-On Completion\n\n"
            "- completed_stage: handoff-brief\n"
            f"- cycle_id: {source_follow_on_cycle}\n"
            "- completed_by: handoff-brief\n\n"
            "## Summary\n\n"
            "- Refreshed restart surfaces after converged managed repair.\n",
            encoding="utf-8",
        )
        run_json(
            [
                sys.executable,
                str(RECORD_REPAIR_STAGE),
                str(source_follow_up_repair_dest),
                "--stage",
                "ticket-pack-builder",
                "--completed-by",
                "ticket-pack-builder",
                "--summary",
                "Routed source follow-up into the ticket system.",
                "--evidence",
                source_ticket_pack_rel,
            ],
            ROOT,
        )
        run_json(
            [
                sys.executable,
                str(RECORD_REPAIR_STAGE),
                str(source_follow_up_repair_dest),
                "--stage",
                "handoff-brief",
                "--completed-by",
                "handoff-brief",
                "--summary",
                "Refreshed restart surfaces after converged managed repair.",
                "--evidence",
                source_handoff_rel,
            ],
            ROOT,
        )
        reconcile_source_follow_up = run_json(
            [
                sys.executable,
                str(RECONCILE_REPAIR),
                str(source_follow_up_repair_dest),
            ],
            ROOT,
        )
        if reconcile_source_follow_up.get("status") != "reconciled":
            raise RuntimeError(
                "reconcile_repair_follow_on should reconcile completed current-cycle follow-on stages into source_follow_up when only EXEC findings remain"
            )
        reconciled_workflow = json.loads(
            (
                source_follow_up_repair_dest
                / ".opencode"
                / "state"
                / "workflow-state.json"
            ).read_text(encoding="utf-8")
        )
        if (
            reconciled_workflow["repair_follow_on"]["outcome"]
            != "source_follow_up"
        ):
            raise RuntimeError(
                "reconcile_repair_follow_on should update workflow-state to source_follow_up when only source follow-up remains"
            )
        if (
            reconciled_workflow["repair_follow_on"]["handoff_allowed"]
            is not True
        ):
            raise RuntimeError(
                "reconcile_repair_follow_on should allow handoff once required follow-on stages are complete and only source follow-up remains"
            )
        if reconciled_workflow["repair_follow_on"]["blocking_reasons"]:
            raise RuntimeError(
                "reconcile_repair_follow_on should clear stage-only repair blocking reasons once the current cycle is reconciled"
            )
        source_follow_up_repair = run_json(
            [
                sys.executable,
                str(PUBLIC_REPAIR),
                str(source_follow_up_repair_dest),
                "--skip-deterministic-refresh",
            ],
            ROOT,
        )
        if source_follow_up_repair["execution_record"]["blocking_reasons"]:
            raise RuntimeError(
                "Source-layer EXEC follow-up alone should not keep managed repair follow-on blocked once the required follow-on stages are complete"
            )
        if source_follow_up_repair["execution_record"]["verification_status"][
            "source_follow_up_codes"
        ] != ["EXEC003"]:
            raise RuntimeError(
                "Public managed repair runner should classify EXEC findings as source follow-up instead of managed repair blockers"
            )
        required_stage_details = source_follow_up_repair["execution_record"][
            "required_follow_on_stage_details"
        ]
        if required_stage_details != [
            {
                "stage": "ticket-pack-builder",
                "owner": "ticket-pack-builder",
                "category": "ticket_follow_up",
                "reason": "Repair left remediation or reverification follow-up that must be routed into the repo ticket system.",
            }
        ]:
            raise RuntimeError(
                "Public managed repair runner should expose machine-readable owner/category metadata for required follow-on stages"
            )
        if source_follow_up_repair["execution_record"]["verification_status"][
            "current_state_clean"
        ]:
            raise RuntimeError(
                    "Public managed repair runner should not call EXEC-only residual work current_state_clean"
                )
            if not source_follow_up_repair["execution_record"]["verification_status"][
                "causal_regression_verified"
            ]:
                raise RuntimeError(
                    "Public managed repair runner should still mark managed repair verification as satisfied when only source follow-up remains"
                )
            if (
                source_follow_up_repair["execution_record"]["repair_follow_on_outcome"]
                != "source_follow_up"
            ):
                raise RuntimeError(
                    "Public managed repair runner should classify EXEC-only residual work as source_follow_up"
                )
            if not source_follow_up_repair["execution_record"]["handoff_allowed"]:
                raise RuntimeError(
                    "Public managed repair runner should allow handoff once only source follow-up remains and the required follow-on stages are complete"
                )
            source_follow_up_workflow = json.loads(
                (
                    source_follow_up_repair_dest
                    / ".opencode"
                    / "state"
                    / "workflow-state.json"
                ).read_text(encoding="utf-8")
            )
            if (
                source_follow_up_workflow["repair_follow_on"]["handoff_allowed"]
                is not True
            ):
                raise RuntimeError(
                    "Managed repair should write a cleared repair_follow_on state when only source-layer follow-up remains"
                )
            if (
                source_follow_up_workflow["repair_follow_on"]["outcome"]
                != "source_follow_up"
            ):
                raise RuntimeError(
                    "Managed repair should record source_follow_up when only source-layer remediation remains"
                )
            if (
                source_follow_up_workflow["repair_follow_on"]["current_state_clean"]
                is not False
            ):
                raise RuntimeError(
                    "Managed repair should not record current_state_clean when source-layer remediation remains"
                )
            if (
                source_follow_up_workflow["repair_follow_on"]["tracking_mode"]
                != "persistent_recorded_state"
            ):
                raise RuntimeError(
                    "Managed repair should record persistent follow-on tracking mode in workflow state"
                )
            if (
                source_follow_up_workflow["repair_follow_on"]["required_stage_details"]
                != required_stage_details
            ):
                raise RuntimeError(
                    "Managed repair should persist machine-readable required stage details into workflow-state"
                )
            remediation_ticket_ids = source_follow_up_repair["execution_record"].get(
                "remediation_ticket_ids", []
            )
            if not remediation_ticket_ids:
                raise RuntimeError(
                    "Public managed repair runner should create remediation follow-up tickets when EXEC or REF findings remain after repair"
                )
            remediation_manifest = json.loads(
                (
                    source_follow_up_repair_dest / "tickets" / "manifest.json"
                ).read_text(encoding="utf-8")
            )
            remediation_tickets = {
                ticket["id"]: ticket
                for ticket in remediation_manifest.get("tickets", [])
                if isinstance(ticket, dict)
            }
            first_remediation_ticket = remediation_tickets.get(remediation_ticket_ids[0])
            if not first_remediation_ticket or not str(
                first_remediation_ticket.get("finding_source", "")
            ).startswith("EXEC"):
                raise RuntimeError(
                    "Auto-created repair remediation tickets should preserve the source finding code"
                )
            if not source_follow_on_state_path.exists():
                raise RuntimeError(
                    "Managed repair should persist follow-on stage state in repo metadata"
                )
            follow_on_state = json.loads(
                source_follow_on_state_path.read_text(encoding="utf-8")
            )
            if follow_on_state["tracking_mode"] != "persistent_recorded_state":
                raise RuntimeError(
                    "Persisted follow-on stage state should record persistent tracking mode"
                )
            if (
                follow_on_state["stage_records"]["ticket-pack-builder"]["status"]
                != "completed"
            ):
                raise RuntimeError(
                    "Persisted follow-on stage state should keep recorded follow-on stage completion"
                )
            if (
                follow_on_state["stage_records"]["ticket-pack-builder"]["owner"]
                != "ticket-pack-builder"
                or follow_on_state["stage_records"]["ticket-pack-builder"]["category"]
                != "ticket_follow_up"
            ):
                raise RuntimeError(
                    "Persisted follow-on stage state should keep machine-readable owner/category metadata for canonical stages"
                )
            if not any(
                item.get("status") == "completed"
                and item.get("stage") == "ticket-pack-builder"
                and item.get("owner") == "ticket-pack-builder"
                and item.get("category") == "ticket_follow_up"
                for item in follow_on_state.get("history", [])
                if isinstance(item, dict)
            ):
                raise RuntimeError(
                    "Persisted follow-on history should keep owner/category metadata for recorded stage completion events"
                )

            source_follow_up_repair_reuse = run_json(
                [
                    sys.executable,
                    str(PUBLIC_REPAIR),
                    str(source_follow_up_repair_dest),
                    "--skip-deterministic-refresh",
                ],
                ROOT,
            )
            if source_follow_up_repair_reuse["execution_record"]["blocking_reasons"]:
                raise RuntimeError(
                    "Recorded follow-on stage state should let later repair runs reuse prior explicit recorded completion without re-recording the stage"
                )
            if source_follow_up_repair_reuse["execution_record"][
                "recorded_completed_stages"
            ] != ["handoff-brief", "ticket-pack-builder"]:
                raise RuntimeError(
                    "Public managed repair runner should expose persisted recorded follow-on completions"
                )
            if (
                source_follow_up_repair_reuse["execution_record"][
                    "repair_follow_on_outcome"
                ]
                != "source_follow_up"
            ):
                raise RuntimeError(
                    "Reused follow-on stage state should preserve the same source_follow_up outcome"
                )
            if not source_follow_up_repair_reuse["execution_record"]["handoff_allowed"]:
                raise RuntimeError(
                    "Reused follow-on stage state should still allow handoff when only source follow-up remains"
                )
            recorded_stage_results = {
                item["stage"]: item["status"]
                for item in source_follow_up_repair_reuse["stage_results"]
                if item.get("status") == "recorded_completed"
            }
            if recorded_stage_results != {
                "handoff-brief": "recorded_completed",
                "ticket-pack-builder": "recorded_completed",
            }:
                raise RuntimeError(
                    "Managed repair should expose reused follow-on completions as recorded_completed stage results"
                )

            auto_detected_follow_on_dest = workspace / "auto-detected-follow-on-repair"
            shutil.copytree(full_dest, auto_detected_follow_on_dest)
            make_stack_skill_non_placeholder(auto_detected_follow_on_dest)
            seed_failing_pytest_suite(auto_detected_follow_on_dest)
            auto_detected_initial_process = subprocess.run(
                [
                    sys.executable,
                    str(PUBLIC_REPAIR),
                    str(auto_detected_follow_on_dest),
                    "--skip-deterministic-refresh",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            if auto_detected_initial_process.returncode == 0:
                raise RuntimeError(
                    "A repair run with unresolved ticket follow-up should fail closed before any canonical completion artifact exists"
                )
            auto_detected_initial = json.loads(auto_detected_initial_process.stdout)
            if not auto_detected_initial["execution_record"]["blocking_reasons"]:
                raise RuntimeError(
                    "A repair run with unresolved ticket follow-up should stay blocked before any canonical completion artifact exists"
                )
            auto_follow_on_state_path = (
                auto_detected_follow_on_dest
                / ".opencode"
                / "meta"
                / "repair-follow-on-state.json"
            )
            auto_follow_on_state = json.loads(
                auto_follow_on_state_path.read_text(encoding="utf-8")
            )
            auto_cycle_id = auto_follow_on_state["cycle_id"]
            auto_evidence_rel = ".opencode/state/artifacts/history/repair/ticket-pack-builder-completion.md"
            auto_evidence_path = auto_detected_follow_on_dest / auto_evidence_rel
            auto_handoff_evidence_rel = (
                ".opencode/state/artifacts/history/repair/handoff-brief-completion.md"
            )
            auto_handoff_evidence_path = (
                auto_detected_follow_on_dest / auto_handoff_evidence_rel
            )
            auto_evidence_path.parent.mkdir(parents=True, exist_ok=True)
            auto_evidence_path.write_text(
                "# Repair Follow-On Completion\n\n"
                "- completed_stage: ticket-pack-builder\n"
                "- cycle_id: stale-cycle\n"
                "- completed_by: ticket-pack-builder\n\n"
                "## Summary\n\n"
                "- Created or updated the canonical repair follow-up tickets required by the current repair cycle.\n",
                encoding="utf-8",
            )
            auto_handoff_evidence_path.parent.mkdir(parents=True, exist_ok=True)
            auto_handoff_evidence_path.write_text(
                "# Repair Follow-On Completion\n\n"
                "- completed_stage: handoff-brief\n"
                "- cycle_id: stale-cycle\n"
                "- completed_by: handoff-brief\n\n"
                "## Summary\n\n"
                "- Refreshed START-HERE.md, context-snapshot.md, and latest-handoff.md for the current repair cycle.\n",
                encoding="utf-8",
            )
            wrong_cycle_auto_detect_process = subprocess.run(
                [
                    sys.executable,
                    str(PUBLIC_REPAIR),
                    str(auto_detected_follow_on_dest),
                    "--skip-deterministic-refresh",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            if wrong_cycle_auto_detect_process.returncode == 0:
                raise RuntimeError(
                    "Managed repair should fail closed when only a stale-cycle canonical completion artifact exists"
                )
            wrong_cycle_auto_detect = json.loads(wrong_cycle_auto_detect_process.stdout)
            if wrong_cycle_auto_detect["execution_record"][
                "auto_detected_recorded_stages"
            ]:
                raise RuntimeError(
                    "Managed repair should not auto-detect canonical stage evidence whose cycle_id does not match the current repair cycle"
                )
            if not wrong_cycle_auto_detect["execution_record"]["blocking_reasons"]:
                raise RuntimeError(
                    "Managed repair should remain blocked when only a stale-cycle completion artifact exists"
                )
            wrong_cycle_manual_record = subprocess.run(
                [
                    sys.executable,
                    str(RECORD_REPAIR_STAGE),
                    str(auto_detected_follow_on_dest),
                    "--stage",
                    "ticket-pack-builder",
                    "--completed-by",
                    "ticket-pack-builder",
                    "--summary",
                    "Stale-cycle canonical evidence should fail.",
                    "--evidence",
                    auto_evidence_rel,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            if wrong_cycle_manual_record.returncode == 0:
                raise RuntimeError(
                    "record_repair_stage_completion should reject stale-cycle canonical repair evidence instead of trusting it as explicit recorded execution"
                )
            if (
                "must match the current repair cycle"
                not in wrong_cycle_manual_record.stderr
                and "must match the current repair cycle"
                not in wrong_cycle_manual_record.stdout
            ):
                raise RuntimeError(
                    "record_repair_stage_completion should explain stale-cycle canonical evidence rejection"
                )
            auto_evidence_path.write_text(
                "# Repair Follow-On Completion\n\n"
                "- completed_stage: ticket-pack-builder\n"
                f"- cycle_id: {auto_cycle_id}\n"
                "- completed_by: ticket-pack-builder\n\n"
                "## Summary\n\n"
                "- Created or updated the canonical repair follow-up tickets required by the current repair cycle.\n",
                encoding="utf-8",
            )
            auto_handoff_evidence_path.write_text(
                "# Repair Follow-On Completion\n\n"
                "- completed_stage: handoff-brief\n"
                f"- cycle_id: {auto_cycle_id}\n"
                "- completed_by: handoff-brief\n\n"
                "## Summary\n\n"
                "- Refreshed START-HERE.md, context-snapshot.md, and latest-handoff.md for the current repair cycle.\n",
                encoding="utf-8",
            )
            auto_detected_reuse = run_json(
                [
                    sys.executable,
                    str(PUBLIC_REPAIR),
                    str(auto_detected_follow_on_dest),
                    "--skip-deterministic-refresh",
                ],
                ROOT,
            )
            if auto_detected_reuse["execution_record"]["blocking_reasons"]:
                raise RuntimeError(
                    "Managed repair should auto-recognize current-cycle canonical ticket-pack-builder completion evidence without a separate recording command"
                )
            if auto_detected_reuse["execution_record"][
                "auto_detected_recorded_stages"
            ] != ["handoff-brief", "ticket-pack-builder"]:
                raise RuntimeError(
                    "Managed repair should report both current-cycle canonical repair artifacts as auto-detected recorded stages"
                )
            if auto_detected_reuse["execution_record"][
                "recorded_execution_completed_stages"
            ] != ["handoff-brief", "ticket-pack-builder"]:
                raise RuntimeError(
                    "Auto-detected canonical repair artifacts should count as recorded_execution completion for both stages"
                )
            auto_detected_state = json.loads(
                auto_follow_on_state_path.read_text(encoding="utf-8")
            )
            if (
                auto_detected_state["stage_records"]["ticket-pack-builder"][
                    "completed_by"
                ]
                != "ticket-pack-builder:auto-detected"
            ):
                raise RuntimeError(
                    "Auto-detected canonical ticket-pack-builder evidence should persist completed_by as ticket-pack-builder:auto-detected"
                )
            if auto_detected_state["stage_records"]["ticket-pack-builder"][
                "evidence_paths"
            ] != [auto_evidence_rel]:
                raise RuntimeError(
                    "Auto-detected canonical ticket-pack-builder evidence should preserve the canonical repair artifact path"
                )
            if (
                auto_detected_state["stage_records"]["handoff-brief"]["completed_by"]
                != "handoff-brief:auto-detected"
            ):
                raise RuntimeError(
                    "Auto-detected canonical handoff-brief evidence should persist completed_by as handoff-brief:auto-detected"
                )
            if auto_detected_state["stage_records"]["handoff-brief"][
                "evidence_paths"
            ] != [auto_handoff_evidence_rel]:
                raise RuntimeError(
                    "Auto-detected canonical handoff-brief evidence should preserve the canonical repair artifact path"
                )

            zero_evidence_follow_on_dest = workspace / "zero-evidence-follow-on-repair"
            shutil.copytree(full_dest, zero_evidence_follow_on_dest)
            make_stack_skill_non_placeholder(zero_evidence_follow_on_dest)
            seed_failing_pytest_suite(zero_evidence_follow_on_dest)
            zero_evidence_initial_process = subprocess.run(
                [
                    sys.executable,
                    str(PUBLIC_REPAIR),
                    str(zero_evidence_follow_on_dest),
                    "--skip-deterministic-refresh",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            zero_evidence_initial = json.loads(zero_evidence_initial_process.stdout)
            if not zero_evidence_initial["execution_record"]["blocking_reasons"]:
                raise RuntimeError(
                    "A repair run without any follow-on completion record should remain blocked before zero-evidence pollution is tested"
                )
            zero_evidence_state_path = (
                zero_evidence_follow_on_dest
                / ".opencode"
                / "meta"
                / "repair-follow-on-state.json"
            )
            zero_evidence_state = json.loads(
                zero_evidence_state_path.read_text(encoding="utf-8")
            )
            zero_evidence_state["stage_records"]["ticket-pack-builder"] = {
                "stage": "ticket-pack-builder",
                "owner": "ticket-pack-builder",
                "category": "ticket_follow_up",
                "status": "completed",
                "completion_mode": "recorded_execution",
                "evidence_paths": [],
                "completed_by": "ticket-pack-builder",
                "summary": "Polluted zero-evidence completion",
                "last_recorded_at": "2026-03-30T00:00:00Z",
                "last_checked_at": "2026-03-30T00:00:00Z",
                "last_updated_at": "2026-03-30T00:00:00Z",
            }
            zero_evidence_state["history"].append(
                {
                    "recorded_at": "2026-03-30T00:00:00Z",
                    "stage": "ticket-pack-builder",
                    "owner": "ticket-pack-builder",
                    "category": "ticket_follow_up",
                    "status": "completed",
                    "completion_mode": "recorded_execution",
                    "completed_by": "ticket-pack-builder",
                    "summary": "Polluted zero-evidence completion",
                    "evidence_paths": [],
                    "cycle_id": zero_evidence_state["cycle_id"],
                }
            )
            zero_evidence_state_path.write_text(
                json.dumps(zero_evidence_state, indent=2) + "\n", encoding="utf-8"
            )
            zero_evidence_follow_on_process = subprocess.run(
                [
                    sys.executable,
                    str(PUBLIC_REPAIR),
                    str(zero_evidence_follow_on_dest),
                    "--skip-deterministic-refresh",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            zero_evidence_follow_on = json.loads(zero_evidence_follow_on_process.stdout)
            if (
                "ticket-pack-builder"
                not in zero_evidence_follow_on["execution_record"][
                    "invalidated_recorded_stages"
                ]
            ):
                raise RuntimeError(
                    "Managed repair should invalidate recorded execution state that claims completion with zero evidence paths"
                )
            if zero_evidence_follow_on["execution_record"][
                "recorded_execution_completed_stages"
            ]:
                raise RuntimeError(
                    "Managed repair should not report zero-evidence recorded execution as completed work"
                )
            if not zero_evidence_follow_on["execution_record"]["blocking_reasons"]:
                raise RuntimeError(
                    "Managed repair should block again when polluted zero-evidence recorded execution is invalidated"
                )
            zero_evidence_follow_on_state = json.loads(
                zero_evidence_state_path.read_text(encoding="utf-8")
            )
            if (
                zero_evidence_follow_on_state["stage_records"]["ticket-pack-builder"][
                    "status"
                ]
                != "evidence_missing"
            ):
                raise RuntimeError(
                    "Follow-on tracking should persist evidence_missing when polluted recorded execution has zero evidence paths"
                )
            if (
                zero_evidence_follow_on_state["stage_records"][
                    "ticket-pack-builder"
                ].get("evidence_validation_error")
                != "missing_recorded_evidence"
            ):
                raise RuntimeError(
                    "Follow-on tracking should record why zero-evidence recorded execution was invalidated"
                )

            recorded_follow_on_dest = workspace / "recorded-follow-on-repair"
            shutil.copytree(full_dest, recorded_follow_on_dest)
            make_stack_skill_non_placeholder(recorded_follow_on_dest)
            seed_failing_pytest_suite(recorded_follow_on_dest)
            recorded_follow_on_initial_process = subprocess.run(
                [
                    sys.executable,
                    str(PUBLIC_REPAIR),
                    str(recorded_follow_on_dest),
                    "--skip-deterministic-refresh",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            recorded_follow_on_initial = json.loads(
                recorded_follow_on_initial_process.stdout
            )
            if not recorded_follow_on_initial["execution_record"]["blocking_reasons"]:
                raise RuntimeError(
                    "A repair run without any follow-on completion record should remain blocked when ticket follow-up is still required"
                )
            recorded_follow_on_state_path = (
                recorded_follow_on_dest
                / ".opencode"
                / "meta"
                / "repair-follow-on-state.json"
            )
            recorded_follow_on_initial_state = json.loads(
                recorded_follow_on_state_path.read_text(encoding="utf-8")
            )
            recorded_cycle_id = recorded_follow_on_initial_state["cycle_id"]
            no_evidence_record_stage = subprocess.run(
                [
                    sys.executable,
                    str(RECORD_REPAIR_STAGE),
                    str(recorded_follow_on_dest),
                    "--stage",
                    "ticket-pack-builder",
                    "--completed-by",
                    "tester",
                    "--summary",
                    "Missing evidence should fail.",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            if no_evidence_record_stage.returncode == 0:
                raise RuntimeError(
                    "record_repair_stage_completion should reject explicit recorded execution that provides zero evidence paths"
                )
            if (
                "requires at least one repo-relative evidence path"
                not in no_evidence_record_stage.stderr
                and "requires at least one repo-relative evidence path"
                not in no_evidence_record_stage.stdout
            ):
                raise RuntimeError(
                    "record_repair_stage_completion should explain zero-evidence recorded execution rejection"
                )
            manual_recorded_evidence_rel = (
                ".opencode/state/artifacts/history/repair/manual-recorded-evidence.md"
            )
            manual_recorded_evidence_path = (
                recorded_follow_on_dest / manual_recorded_evidence_rel
            )
            manual_recorded_evidence_path.parent.mkdir(parents=True, exist_ok=True)
            manual_recorded_evidence_path.write_text(
                "# Manual recorded evidence\n", encoding="utf-8"
            )
            blank_completed_by_record_stage = subprocess.run(
                [
                    sys.executable,
                    str(RECORD_REPAIR_STAGE),
                    str(recorded_follow_on_dest),
                    "--stage",
                    "ticket-pack-builder",
                    "--completed-by",
                    "   ",
                    "--summary",
                    "Blank completed_by should fail.",
                    "--evidence",
                    manual_recorded_evidence_rel,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            if blank_completed_by_record_stage.returncode == 0:
                raise RuntimeError(
                    "record_repair_stage_completion should reject explicit recorded execution with a blank completed_by value"
                )
            if (
                "requires a non-empty completed_by value"
                not in blank_completed_by_record_stage.stderr
                and "requires a non-empty completed_by value"
                not in blank_completed_by_record_stage.stdout
            ):
                raise RuntimeError(
                    "record_repair_stage_completion should explain blank completed_by rejection"
                )
            blank_summary_record_stage = subprocess.run(
                [
                    sys.executable,
                    str(RECORD_REPAIR_STAGE),
                    str(recorded_follow_on_dest),
                    "--stage",
                    "ticket-pack-builder",
                    "--completed-by",
                    "ticket-pack-builder",
                    "--summary",
                    "   ",
                    "--evidence",
                    manual_recorded_evidence_rel,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            if blank_summary_record_stage.returncode == 0:
                raise RuntimeError(
                    "record_repair_stage_completion should reject explicit recorded execution with a blank summary"
                )
            if (
                "requires a non-empty summary" not in blank_summary_record_stage.stderr
                and "requires a non-empty summary"
                not in blank_summary_record_stage.stdout
            ):
                raise RuntimeError(
                    "record_repair_stage_completion should explain blank summary rejection"
                )
            recorded_evidence_rel = ".opencode/state/artifacts/history/repair/ticket-pack-builder-completion.md"
            recorded_evidence_path = recorded_follow_on_dest / recorded_evidence_rel
            recorded_evidence_path.parent.mkdir(parents=True, exist_ok=True)
            recorded_evidence_path.write_text(
                "# Repair Follow-On Completion\n\n"
                "- completed_stage: ticket-pack-builder\n"
                f"- cycle_id: {recorded_cycle_id}\n"
                "- completed_by: ticket-pack-builder\n\n"
                "## Summary\n\n"
                "- Refined repair follow-up tickets after managed repair.\n",
                encoding="utf-8",
            )
            recorded_workflow_before_stage = json.loads(
                (
                    recorded_follow_on_dest
                    / ".opencode"
                    / "state"
                    / "workflow-state.json"
                ).read_text(encoding="utf-8")
            )
            recorded_execution_before_stage = json.loads(
                (
                    recorded_follow_on_dest
                    / ".opencode"
                    / "meta"
                    / "repair-execution.json"
                ).read_text(encoding="utf-8")
            )
            recorded_start_here_before_stage = (
                recorded_follow_on_dest / "START-HERE.md"
            ).read_text(encoding="utf-8")
            recorded_latest_handoff_before_stage = (
                recorded_follow_on_dest / ".opencode" / "state" / "latest-handoff.md"
            ).read_text(encoding="utf-8")
            recorded_stage_payload = run_json(
                [
                    sys.executable,
                    str(RECORD_REPAIR_STAGE),
                    str(recorded_follow_on_dest),
                    "--stage",
                    "ticket-pack-builder",
                    "--completed-by",
                    "ticket-pack-builder",
                    "--summary",
                    "Refined repair follow-up tickets after managed repair.",
                    "--evidence",
                    recorded_evidence_rel,
                ],
                ROOT,
            )
            if recorded_stage_payload["recorded_stage"]["status"] != "completed":
                raise RuntimeError(
                    "record_repair_stage_completion should persist completed status for explicit recorded execution"
                )
            if (
                recorded_stage_payload["recorded_stage"]["completion_mode"]
                != "recorded_execution"
            ):
                raise RuntimeError(
                    "record_repair_stage_completion should mark explicit stage completion as recorded_execution"
                )
            if recorded_stage_payload["recorded_stage"]["evidence_paths"] != [
                recorded_evidence_rel
            ]:
                raise RuntimeError(
                    "record_repair_stage_completion should preserve the recorded evidence paths"
                )
            if "publication" in recorded_stage_payload:
                raise RuntimeError(
                    "record_repair_stage_completion should not publish restart surfaces directly"
                )
            recorded_workflow_after_stage = json.loads(
                (
                    recorded_follow_on_dest
                    / ".opencode"
                    / "state"
                    / "workflow-state.json"
                ).read_text(encoding="utf-8")
            )
            if recorded_workflow_after_stage != recorded_workflow_before_stage:
                raise RuntimeError(
                    "record_repair_stage_completion should not rewrite workflow-state.json while recording completion"
                )
            recorded_execution_after_stage = json.loads(
                (
                    recorded_follow_on_dest
                    / ".opencode"
                    / "meta"
                    / "repair-execution.json"
                ).read_text(encoding="utf-8")
            )
            if recorded_execution_after_stage != recorded_execution_before_stage:
                raise RuntimeError(
                    "record_repair_stage_completion should not rewrite repair-execution.json while recording completion"
                )
            recorded_start_here_after_stage = (
                recorded_follow_on_dest / "START-HERE.md"
            ).read_text(encoding="utf-8")
            recorded_latest_handoff_after_stage = (
                recorded_follow_on_dest / ".opencode" / "state" / "latest-handoff.md"
            ).read_text(encoding="utf-8")
            if recorded_start_here_after_stage != recorded_start_here_before_stage:
                raise RuntimeError(
                    "record_repair_stage_completion should not republish START-HERE while recording completion"
                )
            if recorded_latest_handoff_after_stage != recorded_latest_handoff_before_stage:
                raise RuntimeError(
                    "record_repair_stage_completion should not republish latest-handoff while recording completion"
                )
            recorded_follow_on_reuse = run_json(
                [
                    sys.executable,
                    str(PUBLIC_REPAIR),
                    str(recorded_follow_on_dest),
                    "--skip-deterministic-refresh",
                ],
                ROOT,
            )
            if recorded_follow_on_reuse["execution_record"]["blocking_reasons"]:
                raise RuntimeError(
                    "A later repair run should reuse explicit recorded stage completion without needing transitional --stage-complete input"
                )
            if recorded_follow_on_reuse["execution_record"][
                "recorded_execution_completed_stages"
            ] != ["ticket-pack-builder"]:
                raise RuntimeError(
                    "Managed repair should report explicit recorded_execution completions separately from asserted stages"
                )
            if recorded_follow_on_reuse["execution_record"][
                "asserted_completed_stages"
            ]:
                raise RuntimeError(
                    "Explicit recorded_execution follow-on completion should not populate asserted_completed_stages"
                )
            if (
                recorded_follow_on_reuse["execution_record"]["repair_follow_on_outcome"]
                != "source_follow_up"
            ):
                raise RuntimeError(
                    "Explicit recorded_execution follow-on completion should still converge to source_follow_up when only EXEC findings remain"
                )
            recorded_follow_on_state = json.loads(
                recorded_follow_on_state_path.read_text(encoding="utf-8")
            )
            if (
                recorded_follow_on_state["stage_records"]["ticket-pack-builder"][
                    "completed_by"
                ]
                != "ticket-pack-builder"
            ):
                raise RuntimeError(
                    "Persisted follow-on tracking should keep completed_by for explicitly recorded execution"
                )
            if not any(
                item.get("status") == "completed"
                and item.get("stage") == "ticket-pack-builder"
                and item.get("owner") == "ticket-pack-builder"
                and item.get("category") == "ticket_follow_up"
                for item in recorded_follow_on_state.get("history", [])
                if isinstance(item, dict)
            ):
                raise RuntimeError(
                    "Persisted follow-on history should keep owner/category metadata for recorded execution events"
                )
            package_mismatch_state = json.loads(
                recorded_follow_on_state_path.read_text(encoding="utf-8")
            )
            package_mismatch_state["repair_package_commit"] = "stale-package-commit"
            package_mismatch_state["stage_records"]["ticket-pack-builder"][
                "repair_package_commit"
            ] = "stale-package-commit"
            recorded_follow_on_state_path.write_text(
                json.dumps(package_mismatch_state, indent=2) + "\n",
                encoding="utf-8",
            )
            recorded_follow_on_package_mismatch_process = subprocess.run(
                [
                    sys.executable,
                    str(PUBLIC_REPAIR),
                    str(recorded_follow_on_dest),
                    "--skip-deterministic-refresh",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            recorded_follow_on_package_mismatch = json.loads(
                recorded_follow_on_package_mismatch_process.stdout
            )
            if (
                "ticket-pack-builder"
                not in recorded_follow_on_package_mismatch["execution_record"][
                    "invalidated_recorded_stages"
                ]
            ):
                raise RuntimeError(
                    "Managed repair should invalidate recorded execution reuse when the recorded stage package provenance is stale"
                )
            if recorded_follow_on_package_mismatch["execution_record"][
                "recorded_execution_completed_stages"
            ]:
                raise RuntimeError(
                    "Managed repair should stop reporting recorded execution completion when its repair package provenance is stale"
                )
            package_mismatch_after_state = json.loads(
                recorded_follow_on_state_path.read_text(encoding="utf-8")
            )
            if (
                package_mismatch_after_state["stage_records"]["ticket-pack-builder"].get(
                    "evidence_validation_error"
                )
                != "repair_package_commit_mismatch"
            ):
                raise RuntimeError(
                    "Follow-on tracking should record repair_package_commit_mismatch when a recorded stage was produced by an older package commit"
                )
            run_json(
                [
                    sys.executable,
                    str(RECORD_REPAIR_STAGE),
                    str(recorded_follow_on_dest),
                    "--stage",
                    "ticket-pack-builder",
                    "--completed-by",
                    "ticket-pack-builder",
                    "--summary",
                    "Refined repair follow-up tickets after managed repair.",
                    "--evidence",
                    recorded_evidence_rel,
                ],
                ROOT,
            )
            recorded_evidence_path.write_text(
                "# Repair Follow-On Completion\n\n"
                "- completed_stage: ticket-pack-builder\n"
                "- cycle_id: stale-cycle\n"
                "- completed_by: ticket-pack-builder\n\n"
                "## Summary\n\n"
                "- Drifted canonical evidence should invalidate reuse.\n",
                encoding="utf-8",
            )
            recorded_follow_on_cycle_mismatch_process = subprocess.run(
                [
                    sys.executable,
                    str(PUBLIC_REPAIR),
                    str(recorded_follow_on_dest),
                    "--skip-deterministic-refresh",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            recorded_follow_on_cycle_mismatch = json.loads(
                recorded_follow_on_cycle_mismatch_process.stdout
            )
            if (
                "ticket-pack-builder"
                not in recorded_follow_on_cycle_mismatch["execution_record"][
                    "invalidated_recorded_stages"
                ]
            ):
                raise RuntimeError(
                    "Managed repair should invalidate recorded execution reuse when canonical repair evidence drifts to a stale cycle"
                )
            if recorded_follow_on_cycle_mismatch["execution_record"][
                "recorded_execution_completed_stages"
            ]:
                raise RuntimeError(
                    "Managed repair should stop reporting canonical recorded execution after its cycle markers drift"
                )
            drifted_evidence_state = json.loads(
                recorded_follow_on_state_path.read_text(encoding="utf-8")
            )
            if (
                drifted_evidence_state["stage_records"]["ticket-pack-builder"].get(
                    "evidence_validation_error"
                )
                != "canonical_evidence_cycle_mismatch"
            ):
                raise RuntimeError(
                    "Follow-on tracking should record canonical_evidence_cycle_mismatch when a recorded canonical artifact no longer matches the current cycle"
                )
            recorded_evidence_path.unlink()
            recorded_follow_on_missing_evidence_process = subprocess.run(
                [
                    sys.executable,
                    str(PUBLIC_REPAIR),
                    str(recorded_follow_on_dest),
                    "--skip-deterministic-refresh",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            recorded_follow_on_missing_evidence = json.loads(
                recorded_follow_on_missing_evidence_process.stdout
            )
            if (
                "ticket-pack-builder"
                not in recorded_follow_on_missing_evidence["execution_record"][
                    "invalidated_recorded_stages"
                ]
            ):
                raise RuntimeError(
                    "Managed repair should invalidate recorded execution reuse when the supporting evidence path disappears"
                )
            if recorded_follow_on_missing_evidence["execution_record"][
                "recorded_execution_completed_stages"
            ]:
                raise RuntimeError(
                    "Managed repair should stop reporting recorded execution completion when its evidence is missing"
                )
            if not recorded_follow_on_missing_evidence["execution_record"][
                "blocking_reasons"
            ]:
                raise RuntimeError(
                    "Managed repair should block again when required recorded execution evidence is missing"
                )
            missing_evidence_state = json.loads(
                (
                    recorded_follow_on_dest
                    / ".opencode"
                    / "meta"
                    / "repair-follow-on-state.json"
                ).read_text(encoding="utf-8")
            )
            if (
                missing_evidence_state["stage_records"]["ticket-pack-builder"]["status"]
                != "evidence_missing"
            ):
                raise RuntimeError(
                    "Follow-on tracking should persist evidence_missing when recorded execution evidence disappears"
                )

            run_managed_repair_module = load_python_module(
                PUBLIC_REPAIR, "scafforge_smoke_run_managed_repair"
            )
            disposition_bundle_module = load_python_module(
                ROOT / "skills" / "scafforge-audit" / "scripts" / "disposition_bundle.py",
                "scafforge_smoke_disposition_bundle",
            )
            audit_reporting_module = load_python_module(
                ROOT / "skills" / "scafforge-audit" / "scripts" / "audit_reporting.py",
                "scafforge_smoke_audit_reporting_disposition",
            )
            audit_repair_cycles_module = load_python_module(
                ROOT / "skills" / "scafforge-audit" / "scripts" / "audit_repair_cycles.py",
                "scafforge_smoke_audit_repair_cycles",
            )
            audit_repo_process_module = load_python_module(
                AUDIT, "scafforge_smoke_audit_repo_process_disposition"
            )

            synthetic_findings = [
                SimpleNamespace(
                    code="EXEC-SMOKE-001",
                    severity="error",
                    problem="Synthetic execution failure.",
                    root_cause="Synthetic execution failure for disposition-bundle smoke coverage.",
                    files=["src/main.py"],
                    safer_pattern="Run the targeted smoke command and keep execution failures out of the clean path.",
                    evidence=["synthetic exec evidence"],
                    provenance="script",
                ),
                SimpleNamespace(
                    code="BOOT001",
                    severity="error",
                    problem="Synthetic bootstrap failure.",
                    root_cause="Synthetic bootstrap failure for shadow-mode smoke coverage.",
                    files=[".opencode/tools/environment_bootstrap.ts"],
                    safer_pattern="Repair the bootstrap contract before retrying.",
                    evidence=["synthetic bootstrap evidence"],
                    provenance="script",
                ),
                SimpleNamespace(
                    code="WFLOW008",
                    severity="warning",
                    problem="Synthetic process-state-only failure.",
                    root_cause="Synthetic pending process verification state.",
                    files=["tickets/manifest.json"],
                    safer_pattern="Restore trust through canonical reverification.",
                    evidence=["synthetic process evidence"],
                    provenance="script",
                ),
                SimpleNamespace(
                    code="NOTE001",
                    severity="info",
                    problem="Synthetic advisory finding.",
                    root_cause="Synthetic advisory finding for repair classification smoke coverage.",
                    files=[],
                    safer_pattern="No repair action required.",
                    evidence=[],
                    provenance="script",
                ),
            ]
            with tempfile.TemporaryDirectory(prefix="scafforge-disposition-bundle-") as temp_dir:
                temp_root = Path(temp_dir) / "repo"
                temp_root.mkdir(parents=True, exist_ok=True)
                diagnosis_dest = Path(temp_dir) / "diagnosis"
                diagnosis_pack = audit_reporting_module.emit_diagnosis_pack(
                    temp_root,
                    synthetic_findings,
                    diagnosis_dest,
                    [],
                    ctx=audit_reporting_module.AuditReportingContext(
                        package_root=ROOT,
                        current_package_commit=package_commit(),
                    ),
                )
                if not (diagnosis_dest / "disposition-bundle.json").exists():
                    raise RuntimeError(
                        "Diagnosis-pack emission should persist disposition-bundle.json alongside the report files"
                    )
                emitted_bundle = diagnosis_pack["manifest"]["disposition_bundle"]
                emitted_classes = {
                    item["code"]: item["disposition_class"]
                    for item in emitted_bundle["findings"]
                }
                if emitted_classes != {
                    "BOOT001": "manual_prerequisite_blocker",
                    "EXEC-SMOKE-001": "source_follow_up",
                    "NOTE001": "advisory",
                    "WFLOW008": "process_state_only",
                }:
                    raise RuntimeError(
                        "Diagnosis-pack emission should persist one authoritative disposition class for every finding"
                    )
                if diagnosis_pack["manifest"]["source_findings"] != [
                    {"code": "EXEC-SMOKE-001", "severity": "error"}
                ]:
                    raise RuntimeError(
                        "Diagnosis-pack source_findings should follow the authoritative source_follow_up bundle entries"
                    )
                if diagnosis_pack["manifest"]["disposition_bundle_file"] != "disposition-bundle.json":
                    raise RuntimeError(
                        "Diagnosis-pack manifest should record the persisted disposition bundle file"
                    )
                shadow_deltas = emitted_bundle["shadow_mode_deltas"]
                if shadow_deltas != [
                    {
                        "code": "BOOT001",
                        "legacy_disposition_class": "managed_blocker",
                        "disposition_class": "manual_prerequisite_blocker",
                        "route": "scafforge-repair",
                        "reason": "Legacy prefix classification would label BOOT001 as managed_blocker, but the authoritative bundle assigns manual_prerequisite_blocker.",
                    }
                ]:
                    raise RuntimeError(
                        "Disposition shadow-mode output should surface authoritative-versus-legacy classification deltas"
                    )
                note_entry = next(
                    item for item in emitted_bundle["findings"] if item["code"] == "NOTE001"
                )
                if note_entry["evidence_grade"] != disposition_bundle_module.evidence_grade_for_finding(
                    synthetic_findings[-1]
                ):
                    raise RuntimeError(
                        "Disposition bundle should reuse the shared evidence-grade helper for advisory findings"
                    )

            advisory_classes = run_managed_repair_module.classify_verification_findings(
                [synthetic_findings[-1]]
            )
            if advisory_classes["managed_blockers"] or advisory_classes["advisory"] != [
                synthetic_findings[-1]
            ]:
                raise RuntimeError(
                    "Repair verification classification should keep advisory findings out of the managed blocker path"
                )

            authoritative_empty_bundle_manifest = {
                "disposition_bundle": {
                    "version": 1,
                    "finding_count": 0,
                    "findings": [],
                    "shadow_mode_deltas": [],
                },
                "source_findings": [{"code": "REF-001", "severity": "error"}],
                "ticket_recommendations": [
                    {"source_finding_code": "WFLOW001", "route": "scafforge-repair"}
                ],
            }
            if run_managed_repair_module.repair_basis_source_codes(
                authoritative_empty_bundle_manifest
            ):
                raise RuntimeError(
                    "Repair should trust an authoritative empty disposition bundle instead of falling back to legacy source_findings heuristics"
                )
            if audit_repo_process_module.repair_routed_codes_from_manifest(
                authoritative_empty_bundle_manifest
            ):
                raise RuntimeError(
                    "Audit-side repair routing should trust an authoritative empty disposition bundle instead of falling back to legacy recommendation heuristics"
                )

            same_second_repair = audit_repair_cycles_module.latest_repair_history_entry_after(
                [
                    {
                        "repaired_at": "2026-04-06T13:00:00Z",
                        "summary": "same-second repair",
                    }
                ],
                audit_repo_process_module.parse_iso_timestamp("2026-04-06T13:00:00Z"),
                audit_repo_process_module.parse_iso_timestamp,
            )
            if same_second_repair != {
                "repaired_at": "2026-04-06T13:00:00Z",
                "summary": "same-second repair",
            }:
                raise RuntimeError(
                    "Repair-cycle audit should retain same-second repair entries because diagnosis and repair timestamps are stored with second precision"
                )

            contract_failures = (
                run_managed_repair_module.verification_contract_failures(
                    [SimpleNamespace(code="WFLOW010")],
                    performed=True,
                    current_state_clean=False,
                    pending_process_verification=False,
                    classes={
                        "managed_blockers": [SimpleNamespace(code="WFLOW010")],
                        "source_follow_up": [],
                        "manual_prerequisites": [],
                        "process_state_only": [],
                    },
                )
            )
            if "restart_surface_drift_after_repair" not in contract_failures:
                raise RuntimeError(
                    "Repair verification contract checks should treat WFLOW010 as a hard post-repair consistency failure"
                )

            placeholder_contract_failures = (
                run_managed_repair_module.verification_contract_failures(
                    [SimpleNamespace(code="SKILL001")],
                    performed=True,
                    current_state_clean=False,
                    pending_process_verification=False,
                    classes={
                        "managed_blockers": [SimpleNamespace(code="SKILL001")],
                        "source_follow_up": [],
                        "manual_prerequisites": [],
                        "process_state_only": [],
                    },
                )
            )
            if (
                "placeholder_local_skills_survived_refresh"
                not in placeholder_contract_failures
            ):
                raise RuntimeError(
                    "Repair verification contract checks should treat SKILL001 as a hard post-repair consistency failure"
                )

            empty_non_clean_contract_failures = (
                run_managed_repair_module.verification_contract_failures(
                    [],
                    performed=True,
                    current_state_clean=False,
                    pending_process_verification=False,
                    classes={
                        "managed_blockers": [],
                        "source_follow_up": [],
                        "manual_prerequisites": [],
                        "process_state_only": [],
                    },
                )
            )
            if "non_clean_without_findings" not in empty_non_clean_contract_failures:
                raise RuntimeError(
                    "Repair verification contract checks should flag zero-finding non-clean states as a repair-contract failure"
                )
        else:
            print(
                "Skipping uv-dependent source-follow-up public repair assertions because `uv` is not available on this host."
            )

        follow_on_tracking_module = load_python_module(
            ROOT / "skills" / "scafforge-repair" / "scripts" / "follow_on_tracking.py",
            "scafforge_smoke_follow_on_tracking",
        )
        repair_module = load_python_module(
            REPAIR, "scafforge_smoke_apply_repo_process_repair_follow_on_artifacts"
        )
        artifacted_follow_on_dest = workspace / "artifacted-follow-on-auto-detect"
        shutil.copytree(full_dest, artifacted_follow_on_dest)
        repair_module.initialize_follow_on_tracking_state(
            artifacted_follow_on_dest,
            process_version=7,
            change_summary="Synthetic repair follow-on artifact auto-detection coverage.",
        )
        artifacted_tracking_path = (
            artifacted_follow_on_dest
            / ".opencode"
            / "meta"
            / "repair-follow-on-state.json"
        )
        artifacted_tracking_state = json.loads(
            artifacted_tracking_path.read_text(encoding="utf-8")
        )
        required_regeneration_stages = [
            "project-skill-bootstrap",
            "opencode-team-bootstrap",
            "agent-prompt-engineering",
        ]
        artifacted_tracking_state["required_stages"] = required_regeneration_stages
        artifacted_tracking_path.write_text(
            json.dumps(artifacted_tracking_state, indent=2) + "\n", encoding="utf-8"
        )
        artifact_cycle_id = artifacted_tracking_state["cycle_id"]
        artifact_stage_contracts = {
            "project-skill-bootstrap": {
                "relative_path": ".opencode/state/artifacts/history/repair/project-skill-bootstrap-completion.md",
                "completed_by": "project-skill-bootstrap",
                "summary": "- Regenerated the repo-local skill pack and removed scaffold placeholder or model drift for the current repair cycle.\n",
            },
            "opencode-team-bootstrap": {
                "relative_path": ".opencode/state/artifacts/history/repair/opencode-team-bootstrap-completion.md",
                "completed_by": "opencode-team-bootstrap",
                "summary": "- Regenerated the project-specific OpenCode agent team and related command/tool routing for the current repair cycle.\n",
            },
            "agent-prompt-engineering": {
                "relative_path": ".opencode/state/artifacts/history/repair/agent-prompt-engineering-completion.md",
                "completed_by": "agent-prompt-engineering",
                "summary": "- Hardened the project-specific prompts and delegation rules for the current repair cycle.\n",
            },
        }
        for stage, contract in artifact_stage_contracts.items():
            artifact_path = artifacted_follow_on_dest / contract["relative_path"]
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(
                "# Repair Follow-On Completion\n\n"
                f"- completed_stage: {stage}\n"
                "- cycle_id: stale-cycle\n"
                f"- completed_by: {contract['completed_by']}\n\n"
                "## Summary\n\n"
                f"{contract['summary']}",
                encoding="utf-8",
            )
        artifacted_state = follow_on_tracking_module.load_follow_on_tracking_state(
            artifacted_follow_on_dest
        )
        stale_artifact_state, stale_auto_recorded = (
            follow_on_tracking_module.auto_record_stage_completion_from_canonical_evidence(
                artifacted_follow_on_dest,
                artifacted_state,
                required_stage_names=required_regeneration_stages,
                repair_package_commit=package_commit(),
            )
        )
        if stale_auto_recorded:
            raise RuntimeError(
                "Auto-detection should not trust stale-cycle canonical artifacts for regeneration follow-on stages"
            )
        if follow_on_tracking_module.recorded_execution_stage_names(
            stale_artifact_state
        ):
            raise RuntimeError(
                "Stale-cycle regeneration follow-on artifacts should not be counted as recorded execution"
            )
        for stage, contract in artifact_stage_contracts.items():
            artifact_path = artifacted_follow_on_dest / contract["relative_path"]
            artifact_path.write_text(
                "# Repair Follow-On Completion\n\n"
                f"- completed_stage: {stage}\n"
                f"- cycle_id: {artifact_cycle_id}\n"
                f"- completed_by: {contract['completed_by']}\n\n"
                "## Summary\n\n"
                f"{contract['summary']}",
                encoding="utf-8",
            )
        refreshed_artifact_state = (
            follow_on_tracking_module.load_follow_on_tracking_state(
                artifacted_follow_on_dest
            )
        )
        detected_artifact_state, detected_artifact_stages = (
            follow_on_tracking_module.auto_record_stage_completion_from_canonical_evidence(
                artifacted_follow_on_dest,
                refreshed_artifact_state,
                required_stage_names=required_regeneration_stages,
                repair_package_commit=package_commit(),
            )
        )
        if detected_artifact_stages != sorted(required_regeneration_stages):
            raise RuntimeError(
                "Auto-detection should record all regeneration follow-on stages when current-cycle canonical artifacts exist"
            )
        if follow_on_tracking_module.recorded_execution_stage_names(
            detected_artifact_state
        ) != sorted(required_regeneration_stages):
            raise RuntimeError(
                "Recorded execution stage names should include all regeneration follow-on stages auto-detected from canonical artifacts"
            )
        persisted_artifact_tracking = json.loads(
            artifacted_tracking_path.read_text(encoding="utf-8")
        )
        for stage, contract in artifact_stage_contracts.items():
            record = persisted_artifact_tracking["stage_records"].get(stage, {})
            if record.get("completed_by") != f"{stage}:auto-detected":
                raise RuntimeError(
                    f"Auto-detected {stage} evidence should persist the stage-specific auto-detected completed_by value"
                )
            if record.get("evidence_paths") != [contract["relative_path"]]:
                raise RuntimeError(
                    f"Auto-detected {stage} evidence should preserve its canonical repair artifact path"
                )

        print("Scafforge smoke test passed.")
        return 0
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
