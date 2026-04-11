from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

from test_support.scafforge_harness import compute_bootstrap_fingerprint, package_commit


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def make_stack_skill_non_placeholder(dest: Path) -> None:
    skill_path = dest / ".opencode" / "skills" / "stack-standards" / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    text = text.replace("__STACK_LABEL__", "python-uv")
    replacements = (
        "Replace this file with stack-specific rules once the real project stack is known.",
        "When the repo stack is finalized, rewrite this catalog so review and QA agents get the exact build, lint, reference-integrity, and test commands that belong to this project.",
        "When the project stack is confirmed, replace this file's Universal Standards section with stack-specific rules using the `project-skill-bootstrap` skill.",
    )
    for placeholder in replacements:
        text = text.replace(
            placeholder,
            "Use `uv run pytest -q` for validation and keep Python tooling repo-local via `uv`.",
        )
    skill_path.write_text(text, encoding="utf-8")


def seed_ready_bootstrap(dest: Path) -> None:
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    workflow = read_json(workflow_path)
    bootstrap_rel = ".opencode/state/bootstrap/synthetic-ready-bootstrap.md"
    bootstrap_path = dest / bootstrap_rel
    bootstrap_path.parent.mkdir(parents=True, exist_ok=True)
    bootstrap_path.write_text("# Ready Bootstrap\n", encoding="utf-8")
    workflow["bootstrap"] = {
        "status": "ready",
        "last_verified_at": "2026-03-30T00:00:00Z",
        "environment_fingerprint": compute_bootstrap_fingerprint(dest),
        "proof_artifact": bootstrap_rel,
    }
    write_json(workflow_path, workflow)


def seed_bootstrap_command_layout_mismatch(dest: Path) -> None:
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    workflow = read_json(workflow_path)
    current_rel = ".opencode/state/artifacts/history/exec-014/bootstrap/2026-03-27T13-23-09-710Z-environment-bootstrap.md"
    previous_rel = ".opencode/state/artifacts/history/exec-014/bootstrap/2026-03-27T13-20-16-174Z-environment-bootstrap.md"
    current_path = dest / current_rel
    previous_path = dest / previous_rel
    current_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_body = (
        "\n".join(
            [
                "# Environment Bootstrap",
                "",
                "## Missing Prerequisites",
                "",
                f"- {dest / '.venv' / 'bin' / 'pytest'}",
                "",
                "## Commands",
                "",
                "### 1. uv availability",
                "",
                "- command: `uv --version`",
                "",
                "### 2. uv sync",
                "",
                "- command: `uv sync --locked`",
                "",
                "### 3. project pytest ready",
                "",
                f"- command: `{dest / '.venv' / 'bin' / 'pytest'} --version`",
                f"- missing_executable: {dest / '.venv' / 'bin' / 'pytest'}",
                "",
            ]
        )
        + "\n"
    )
    current_path.write_text(artifact_body, encoding="utf-8")
    previous_path.write_text(artifact_body, encoding="utf-8")
    workflow["bootstrap"] = {
        "status": "failed",
        "last_verified_at": "2026-03-27T13:23:09.710Z",
        "environment_fingerprint": "synthetic-bootstrap-command-mismatch",
        "proof_artifact": current_rel,
    }
    write_json(workflow_path, workflow)


def seed_workflow_overclaim(dest: Path) -> Path:
    manifest_path = dest / "tickets" / "manifest.json"
    manifest = read_json(manifest_path)
    active_ticket = manifest["active_ticket"]
    manifest["tickets"].append(
        {
            "id": "WFLOW-DEP",
            "title": "Synthetic dependent ticket",
            "wave": 99,
            "lane": "workflow",
            "parallel_safe": True,
            "overlap_risk": "low",
            "stage": "planning",
            "status": "ready",
            "depends_on": [active_ticket],
            "summary": "Synthetic dependent ticket for handoff overclaim coverage.",
            "acceptance": [
                "Dependency claim remains blocked until the active ticket is done."
            ],
            "decision_blockers": [],
            "artifacts": [],
            "resolution_state": "open",
            "verification_state": "suspect",
            "follow_up_ticket_ids": [],
        }
    )
    write_json(manifest_path, manifest)

    overclaim = (
        "Active work is only blocked by a tool/env mismatch, not a code defect. "
        "The downstream dependency is now unblocked and ready to proceed."
    )
    for relative in ("START-HERE.md", ".opencode/state/latest-handoff.md"):
        path = dest / relative
        original = (
            path.read_text(encoding="utf-8")
            if path.exists()
            else (dest / "START-HERE.md").read_text(encoding="utf-8")
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        if "## Next Action" in original:
            updated = original.replace(
                "## Next Action", f"## Next Action\n\n{overclaim}\n"
            )
        else:
            updated = original.rstrip() + f"\n\n## Next Action\n\n{overclaim}\n"
        path.write_text(updated, encoding="utf-8")

    log_path = dest / "session-log.md"
    log_path.write_text(
        "\n".join(
            [
                "Active ticket: `EXEC-001` — stage `planning`, status `ready`.",
                "`approved_plan: false`",
                "Cannot move EXEC-005 to implementation before it passes through plan_review.",
                "Cannot move EXEC-005 to implementation before it passes through plan_review.",
                'Workaround needed again — using the `todo` bypass: {"stage": "todo"}',
                "Unable to run verification commands — The bash tool is blocked by permission rules in this environment.",
                "Result: PASS (scoped)",
                "Verified by running the scoped command above",
                "Later evidence: 126 tests collected and the service imports cleanly.",
                "Final summary: tool/env mismatch, not a code defect. EXEC-002 is now unblocked.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return log_path


def seed_repeated_diagnosis_churn(dest: Path) -> None:
    diagnosis_root = dest / "diagnosis"
    baseline_candidates = (
        sorted(path for path in diagnosis_root.iterdir() if path.is_dir())
        if diagnosis_root.exists()
        else []
    )
    if baseline_candidates:
        baseline = baseline_candidates[-1]
        baseline_manifest_path = baseline / "manifest.json"
        baseline_manifest = read_json(baseline_manifest_path)
    else:
        baseline = diagnosis_root / "20260327-000001"
        baseline.mkdir(parents=True, exist_ok=True)
        baseline_manifest_path = baseline / "manifest.json"
        baseline_manifest = {
            "generated_at": "2026-03-27T00:00:01Z",
            "repo_root": str(dest),
            "finding_count": 1,
            "result_state": "validated failures found",
            "diagnosis_kind": "initial_diagnosis",
            "evidence_mode": "current_state_only",
            "audit_package_commit": package_commit(),
            "ticket_recommendations": [
                {
                    "source_finding_code": "SKILL001",
                    "route": "scafforge-repair",
                    "title": "Regenerate placeholder repo-local skills",
                }
            ],
        }
    baseline_manifest["audit_package_commit"] = package_commit()
    baseline_manifest["generated_at"] = "2026-03-27T00:03:00Z"
    baseline_manifest["ticket_recommendations"] = [
        {
            "source_finding_code": "SKILL001",
            "route": "scafforge-repair",
            "title": "Regenerate placeholder repo-local skills",
        }
    ]
    write_json(baseline_manifest_path, baseline_manifest)

    for folder_name, generated_at in (
        ("20260327-002513", "2026-03-27T00:25:13Z"),
        ("20260327-014404", "2026-03-27T01:44:04Z"),
    ):
        target = diagnosis_root / folder_name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(baseline, target)
        manifest_path = target / "manifest.json"
        manifest = read_json(manifest_path)
        manifest["generated_at"] = generated_at
        write_json(manifest_path, manifest)


def seed_restart_surface_drift(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = read_json(manifest_path)
    workflow = read_json(workflow_path)
    ticket = manifest["tickets"][0]
    proof_rel = ".opencode/state/bootstrap/synthetic-bootstrap-proof.md"
    proof_path = dest / proof_rel
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text("# Bootstrap Proof\n", encoding="utf-8")

    workflow["bootstrap"] = {
        "status": "failed",
        "last_verified_at": "2026-03-25T23:02:26Z",
        "environment_fingerprint": "synthetic-bootstrap",
        "proof_artifact": proof_rel,
    }
    workflow["pending_process_verification"] = True
    workflow["state_revision"] = 122
    workflow["lane_leases"] = [
        {
            "ticket_id": ticket["id"],
            "lane": ticket["lane"],
            "owner_agent": "synthetic-team-leader",
            "write_lock": True,
            "claimed_at": "2026-03-25T23:00:24Z",
            "allowed_paths": ["."],
        }
    ]
    write_json(workflow_path, workflow)

    (dest / "START-HERE.md").write_text(
        "\n".join(
            [
                "# START HERE",
                "",
                "<!-- SCAFFORGE:START_HERE_BLOCK START -->",
                "## What This Repo Is",
                "",
                "Smoke Example",
                "",
                "## Current Or Next Ticket",
                "",
                f"- ID: {ticket['id']}",
                f"- Title: {ticket['title']}",
                f"- Wave: {ticket['wave']}",
                f"- Lane: {ticket['lane']}",
                f"- Stage: {ticket['stage']}",
                "- Status: ready",
                f"- Resolution: {ticket['resolution_state']}",
                f"- Verification: {ticket['verification_state']}",
                "",
                "## Generation Status",
                "",
                "- handoff_status: ready for continued development",
                f"- process_version: {workflow['process_version']}",
                f"- parallel_mode: {workflow['parallel_mode']}",
                "- pending_process_verification: false",
                "- bootstrap_status: ready",
                "- bootstrap_proof: None",
                "",
                "## Post-Generation Audit Status",
                "",
                "- audit_or_repair_follow_up: none recorded",
                "- reopened_tickets: none",
                "- done_but_not_fully_trusted: none",
                "- pending_reverification: none",
                "",
                "## Known Risks",
                "",
                "- None recorded.",
                "",
                "## Next Action",
                "",
                "Continue the required internal lifecycle from the current ticket stage.",
                "<!-- SCAFFORGE:START_HERE_BLOCK END -->",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (dest / ".opencode" / "state" / "context-snapshot.md").write_text(
        "\n".join(
            [
                "# Context Snapshot",
                "",
                "## Project",
                "",
                "Smoke Example",
                "",
                "## Active Ticket",
                "",
                f"- ID: {ticket['id']}",
                f"- Title: {ticket['title']}",
                f"- Stage: {ticket['stage']}",
                "- Status: ready",
                f"- Resolution: {ticket['resolution_state']}",
                f"- Verification: {ticket['verification_state']}",
                "- Approved plan: no",
                "- Needs reverification: no",
                "",
                "## Bootstrap",
                "",
                "- status: ready",
                "- last_verified_at: 2026-03-25T22:00:00Z",
                "- proof_artifact: None",
                "",
                "## Process State",
                "",
                f"- process_version: {workflow['process_version']}",
                "- pending_process_verification: false",
                f"- parallel_mode: {workflow['parallel_mode']}",
                "- state_revision: 113",
                "",
                "## Lane Leases",
                "",
                "- No active lane leases",
                "",
                "## Recent Artifacts",
                "",
                "- No artifacts recorded yet",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (dest / ".opencode" / "state" / "latest-handoff.md").write_text(
        "\n".join(
            [
                "# START HERE",
                "",
                "<!-- SCAFFORGE:START_HERE_BLOCK START -->",
                "## What This Repo Is",
                "",
                "Smoke Example",
                "",
                "## Current Or Next Ticket",
                "",
                f"- ID: {ticket['id']}",
                f"- Title: {ticket['title']}",
                f"- Wave: {ticket['wave']}",
                f"- Lane: {ticket['lane']}",
                f"- Stage: {ticket['stage']}",
                "- Status: ready",
                f"- Resolution: {ticket['resolution_state']}",
                f"- Verification: {ticket['verification_state']}",
                "",
                "## Generation Status",
                "",
                "- handoff_status: ready for continued development",
                f"- process_version: {workflow['process_version']}",
                f"- parallel_mode: {workflow['parallel_mode']}",
                "- pending_process_verification: false",
                "- bootstrap_status: ready",
                "- bootstrap_proof: None",
                "",
                "## Post-Generation Audit Status",
                "",
                "- audit_or_repair_follow_up: none recorded",
                "- reopened_tickets: none",
                "- done_but_not_fully_trusted: none",
                "- pending_reverification: none",
                "",
                "## Known Risks",
                "",
                "- None recorded.",
                "",
                "## Next Action",
                "",
                "Continue the required internal lifecycle from the current ticket stage.",
                "<!-- SCAFFORGE:START_HERE_BLOCK END -->",
                "",
            ]
        ),
        encoding="utf-8",
    )


def seed_completed_repair_follow_on_verification_block(dest: Path) -> None:
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    workflow = read_json(workflow_path)
    proof_rel = ".opencode/state/bootstrap/synthetic-ready-bootstrap.md"
    proof_path = dest / proof_rel
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text("# Ready Bootstrap\n", encoding="utf-8")
    workflow["bootstrap"] = {
        "status": "ready",
        "last_verified_at": "2026-03-25T23:02:26Z",
        "environment_fingerprint": compute_bootstrap_fingerprint(dest),
        "proof_artifact": proof_rel,
    }
    workflow["pending_process_verification"] = True
    workflow["repair_follow_on"] = {
        **workflow.get("repair_follow_on", {}),
        "outcome": "managed_blocked",
        "required_stages": ["ticket-pack-builder"],
        "completed_stages": ["ticket-pack-builder"],
        "blocking_reasons": [
            "Post-repair verification failed repair-contract consistency checks: restart_surface_drift_after_repair."
        ],
        "verification_passed": False,
        "handoff_allowed": False,
        "current_state_clean": False,
        "contract_failures": ["restart_surface_drift_after_repair"],
        "allowed_follow_on_tickets": [],
        "last_updated_at": "2026-03-25T23:02:26Z",
    }
    write_json(workflow_path, workflow)


def seed_historical_reconciliation_state(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = read_json(manifest_path)
    workflow = read_json(workflow_path)
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
    write_json(manifest_path, manifest)
    write_json(workflow_path, workflow)


def seed_pivot_state_drift(dest: Path) -> None:
    seed_historical_reconciliation_state(dest)
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    pivot_state_path = dest / ".opencode" / "meta" / "pivot-state.json"
    manifest = read_json(manifest_path)
    workflow = read_json(workflow_path)
    active_ticket_id = manifest["active_ticket"]
    pivot_state = {
        "pivot_state_path": ".opencode/meta/pivot-state.json",
        "pivot_class": "history-reconciliation",
        "requested_change": "Synthetic pivot-state drift fixture",
        "restart_surface_inputs": {
            "pivot_in_progress": True,
            "pivot_changed_surfaces": [
                "ticket_graph_and_lineage",
                "restart_surfaces",
            ],
            "pending_ticket_lineage_actions": [f"reconcile:{active_ticket_id}"],
            "pending_downstream_stages": ["ticket-pack-builder"],
        },
        "downstream_refresh_state": {
            "pending_stages": ["ticket-pack-builder"],
            "completed_stages": [],
        },
        "ticket_lineage_plan": {
            "actions": [
                {
                    "action": "reconcile",
                    "target_ticket_id": active_ticket_id,
                    "summary": "Synthetic pivot-state reconciliation for stale lineage coverage.",
                }
            ]
        },
        "restart_surface_publication": {"status": "stale"},
        "workflow_status": workflow.get("status"),
    }
    write_json(pivot_state_path, pivot_state)


def seed_legacy_contract_state(
    dest: Path,
    *,
    process_version: int,
    repair_follow_on_process_version: int | None = None,
) -> None:
    provenance_path = dest / ".opencode" / "meta" / "bootstrap-provenance.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    provenance = read_json(provenance_path)
    workflow = read_json(workflow_path)
    if not isinstance(provenance, dict):
        raise RuntimeError("Cannot seed legacy process state without bootstrap provenance.")
    if not isinstance(workflow, dict):
        raise RuntimeError("Cannot seed legacy process state without workflow state.")

    workflow_contract = provenance.setdefault("workflow_contract", {})
    if not isinstance(workflow_contract, dict):
        raise RuntimeError("Bootstrap provenance workflow_contract must be an object.")
    workflow_contract["process_version"] = process_version
    provenance["migration_history"] = []

    workflow["process_version"] = process_version
    workflow["process_last_change_summary"] = f"Legacy contract seeded at process_version {process_version}."
    repair_follow_on = workflow.get("repair_follow_on")
    if isinstance(repair_follow_on, dict):
        repair_follow_on["process_version"] = (
            repair_follow_on_process_version if repair_follow_on_process_version is not None else process_version
        )
    workflow["pending_process_verification"] = False

    write_json(provenance_path, provenance)
    write_json(workflow_path, workflow)


def write_python_wrapper(path: Path, *, allow_pytest: bool) -> None:
    real_python = sys.executable
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import subprocess",
                "import sys",
                f"REAL_PYTHON = {real_python!r}",
                "args = sys.argv[1:]",
                f"ALLOW_PYTEST = {allow_pytest!r}",
                'if not ALLOW_PYTEST and len(args) >= 2 and args[0] == "-m" and args[1] == "pytest":',
                "    sys.exit(1)",
                "raise SystemExit(subprocess.run([REAL_PYTHON, *args], check=False).returncode)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def seed_uv_python_fixture(
    dest: Path,
    *,
    dependency_block: list[str] | None = None,
    include_pytest_tool_config: bool = False,
) -> None:
    dependency_lines = dependency_block or [
        "[project.optional-dependencies]",
        'dev = ["pytest>=8.0.0"]',
    ]
    pyproject_lines = [
        "[project]",
        'name = "smoke-python"',
        'version = "0.1.0"',
        'requires-python = ">=3.11"',
        "",
        *dependency_lines,
        "",
    ]
    if include_pytest_tool_config:
        pyproject_lines.extend(
            [
                "[tool.pytest.ini_options]",
                'pythonpath = ["src"]',
                "",
            ]
        )

    (dest / "pyproject.toml").write_text(
        "\n".join(pyproject_lines) + "\n", encoding="utf-8"
    )
    (dest / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    venv_dir = dest / ".venv"
    venv_dir.mkdir(parents=True, exist_ok=True)
    (venv_dir / "pyvenv.cfg").write_text(
        "\n".join(
            [
                "home = /usr/bin",
                "implementation = CPython",
                "uv = 0.10.12",
                "version_info = 3.12.3",
                "include-system-site-packages = false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def seed_failing_pytest_suite(dest: Path) -> None:
    seed_uv_python_fixture(dest)
    src_pkg = dest / "src" / "smoke_pkg"
    src_pkg.mkdir(parents=True, exist_ok=True)
    (src_pkg / "__init__.py").write_text("__all__ = ['ok']\n", encoding="utf-8")
    tests_dir = dest / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_sample.py").write_text(
        "def test_smoke():\n    assert False, 'synthetic runtime failure'\n", encoding="utf-8"
    )

    venv_bin = dest / ".venv" / "bin"
    venv_bin.mkdir(parents=True, exist_ok=True)
    write_python_wrapper(venv_bin / "python", allow_pytest=True)
    (venv_bin / "pytest").write_text(
        "\n".join(
            [
                f"#!{sys.executable}",
                "import sys",
                "args = sys.argv[1:]",
                'if "--version" in args:',
                '    print("pytest 8.1.0")',
                "    raise SystemExit(0)",
                'if "--collect-only" in args:',
                '    print("2 tests collected")',
                "    raise SystemExit(0)",
                'print("1 failed, 1 passed in 0.10s")',
                "raise SystemExit(1)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (venv_bin / "pytest").chmod(0o755)


def seed_closed_ticket_with_new_active_artifact_write(dest: Path) -> None:
    """Seed a scenario where ticket A is closed, ticket B is active with a lease,
    and an artifact write for B should succeed. This exercises the stage-gate-enforcer
    fix that passes the target ticket ID to ensureWriteLease instead of always checking
    workflow.active_ticket."""
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = read_json(manifest_path)
    workflow = read_json(workflow_path)

    original_active = manifest["active_ticket"]

    # Close the original ticket
    for ticket in manifest["tickets"]:
        if ticket["id"] == original_active:
            ticket["stage"] = "closeout"
            ticket["status"] = "done"
            ticket["resolution_state"] = "done"
            ticket["verification_state"] = "trusted"
            break

    # Add a new ticket and make it active
    new_ticket_id = "TICK-002"
    manifest["tickets"].append(
        {
            "id": new_ticket_id,
            "title": "New active ticket after closeout",
            "wave": 2,
            "lane": "feature",
            "parallel_safe": False,
            "overlap_risk": "medium",
            "stage": "planning",
            "status": "todo",
            "depends_on": [],
            "summary": "Synthetic ticket to test artifact write after closeout.",
            "acceptance": ["Artifact write succeeds with valid lease."],
            "decision_blockers": [],
            "artifacts": [],
            "resolution_state": "open",
            "verification_state": "suspect",
            "follow_up_ticket_ids": [],
        }
    )
    manifest["active_ticket"] = new_ticket_id

    # Workflow state: active ticket updated, lease registered for new ticket
    workflow["active_ticket"] = new_ticket_id
    workflow["stage"] = "planning"
    workflow["status"] = "todo"
    workflow["lane_leases"] = [
        {
            "ticket_id": new_ticket_id,
            "lane": "feature",
            "owner_agent": "synthetic-team-leader",
            "write_lock": True,
            "claimed_at": "2099-01-01T00:00:00Z",
            "expires_at": "2099-12-31T23:59:59Z",
            "allowed_paths": [
                ".opencode/state/plans/",
                ".opencode/state/implementations/",
            ],
        }
    ]

    write_json(manifest_path, manifest)
    write_json(workflow_path, workflow)


def seed_all_tickets_closed(dest: Path) -> None:
    """Seed a scenario where all tickets are closed and active_ticket points to a done
    ticket with no active leases. This exercises the stage-gate-enforcer fix that
    allows net_new_scope ticket creation when all tickets are closed."""
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = read_json(manifest_path)
    workflow = read_json(workflow_path)

    # Close all existing tickets
    for ticket in manifest["tickets"]:
        ticket["stage"] = "closeout"
        ticket["status"] = "done"
        ticket["resolution_state"] = "done"
        ticket["verification_state"] = "trusted"

    # Keep active_ticket pointing to the first ticket (now closed)
    manifest["active_ticket"] = manifest["tickets"][0]["id"]

    # Workflow state: active ticket points to closed ticket, no leases
    workflow["active_ticket"] = manifest["active_ticket"]
    workflow["stage"] = "closeout"
    workflow["status"] = "done"
    workflow["lane_leases"] = []

    write_json(manifest_path, manifest)
    write_json(workflow_path, workflow)
