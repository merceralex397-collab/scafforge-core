from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "skills" / "repo-scaffold-factory" / "scripts" / "bootstrap_repo_scaffold.py"
CHECKLIST = ROOT / "skills" / "repo-scaffold-factory" / "references" / "opencode-conformance-checklist.json"
AUDIT = ROOT / "skills" / "scafforge-audit" / "scripts" / "audit_repo_process.py"
REPAIR = ROOT / "skills" / "scafforge-repair" / "scripts" / "apply_repo_process_repair.py"


def run(command: list[str], cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")


def run_json(command: list[str], cwd: Path) -> dict:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Command did not return valid JSON: {' '.join(command)}\nSTDOUT:\n{result.stdout}") from exc


def seed_uv_python_fixture(dest: Path) -> None:
    (dest / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "smoke-python"',
                'version = "0.1.0"',
                'requires-python = ">=3.11"',
                "",
                "[project.optional-dependencies]",
                'dev = ["pytest>=8.0.0"]',
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
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


def verify_render(dest: Path, *, expect_full_repo: bool) -> None:
    checklist = json.loads(CHECKLIST.read_text(encoding="utf-8"))
    for relative in checklist["required_files"]:
        path = dest / relative
        if expect_full_repo or str(relative).startswith(".opencode") or str(relative) == "opencode.jsonc":
            if not path.exists():
                raise RuntimeError(f"Missing expected file: {path}")

    for relative in checklist["required_directories"]:
        path = dest / relative
        if expect_full_repo or str(relative).startswith(".opencode"):
            if not path.exists():
                raise RuntimeError(f"Missing expected directory: {path}")

    manifest = json.loads((dest / "tickets" / "manifest.json").read_text(encoding="utf-8")) if expect_full_repo else None
    if manifest is not None:
        if "tickets" not in manifest:
            raise RuntimeError("tickets/manifest.json is missing a tickets key")
        if manifest.get("version") != 3:
            raise RuntimeError("tickets/manifest.json should use version 3")
        if not manifest["tickets"]:
            raise RuntimeError("tickets/manifest.json must contain at least one ticket")
        first_ticket = manifest["tickets"][0]
        for key in ("wave", "parallel_safe", "overlap_risk", "decision_blockers", "resolution_state", "verification_state"):
            if key not in first_ticket:
                raise RuntimeError(f"tickets/manifest.json first ticket is missing `{key}`")

        workflow = json.loads((dest / ".opencode" / "state" / "workflow-state.json").read_text(encoding="utf-8"))
        for key in ("process_version", "pending_process_verification", "parallel_mode", "ticket_state", "bootstrap", "lane_leases", "state_revision"):
            if key not in workflow:
                raise RuntimeError(f".opencode/state/workflow-state.json is missing `{key}`")
        active_ticket = manifest.get("active_ticket")
        if not isinstance(workflow.get("ticket_state"), dict):
            raise RuntimeError(".opencode/state/workflow-state.json must contain a ticket_state map")
        if isinstance(active_ticket, str) and active_ticket not in workflow["ticket_state"]:
            raise RuntimeError("workflow-state ticket_state must contain the active ticket entry")
        active_ticket_state = workflow["ticket_state"].get(active_ticket, {}) if isinstance(active_ticket, str) else {}
        for key in ("reopen_count", "needs_reverification"):
            if key not in active_ticket_state:
                raise RuntimeError(f"workflow-state active ticket entry is missing `{key}`")

        agents_dir = dest / ".opencode" / "agents"
        agent_names = {path.name for path in agents_dir.glob("*.md")}
        required_agent_suffixes = checklist.get("required_agent_suffixes")
        if not required_agent_suffixes:
            raise RuntimeError("opencode-conformance-checklist.json is missing required_agent_suffixes")
        for suffix in required_agent_suffixes:
            if not any(name.endswith(f"{suffix}.md") for name in agent_names):
                raise RuntimeError(f"Missing expected agent with suffix `{suffix}`")

        skills_dir = dest / ".opencode" / "skills"
        required_skill_ids = checklist.get("required_skill_ids")
        if not required_skill_ids:
            raise RuntimeError("opencode-conformance-checklist.json is missing required_skill_ids")
        for skill_id in required_skill_ids:
            skill_file = skills_dir / skill_id / "SKILL.md"
            if not skill_file.exists():
                raise RuntimeError(f"Missing expected local skill `{skill_id}`")

        start_here = (dest / "START-HERE.md").read_text(encoding="utf-8")
        for heading in ("## Current Or Next Ticket", "## Generation Status", "## Post-Generation Audit Status"):
            if heading not in start_here:
                raise RuntimeError(f"START-HERE.md is missing required section `{heading}`")
        for forbidden in ("## Process Contract", "## Current Ticket"):
            if forbidden in start_here:
                raise RuntimeError(f"START-HERE.md still contains deprecated section `{forbidden}`")


def main() -> int:
    workspace = Path(tempfile.mkdtemp(prefix="scafforge-smoke-"))
    try:
        full_dest = workspace / "full"
        opencode_dest = workspace / "opencode"

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

        verify_render(full_dest, expect_full_repo=True)
        verify_render(opencode_dest, expect_full_repo=False)

        initial_audit = run_json([sys.executable, str(AUDIT), str(full_dest), "--format", "json", "--emit-diagnosis-pack"], ROOT)
        initial_codes = {finding["code"] for finding in initial_audit.get("findings", [])}
        if "SKILL001" not in initial_codes:
            raise RuntimeError("Audit should flag placeholder repo-local skills with SKILL001 on the base scaffold output")
        diagnosis_root = full_dest / "diagnosis"
        diagnosis_dirs = sorted(path for path in diagnosis_root.iterdir() if path.is_dir()) if diagnosis_root.exists() else []
        if not diagnosis_dirs:
            raise RuntimeError("Audit should create a diagnosis/<timestamp> folder when diagnosis-pack emission is enabled")
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
                raise RuntimeError(f"Diagnosis pack is missing expected file: {diagnosis_pack / relative}")

        diagnosis_manifest = json.loads((diagnosis_pack / "manifest.json").read_text(encoding="utf-8"))
        if "ticket_recommendations" not in diagnosis_manifest:
            raise RuntimeError("Diagnosis pack manifest should include ticket_recommendations")
        if diagnosis_manifest.get("report_files", {}).get("report_4") != "04-live-repo-repair-plan.md":
            raise RuntimeError("Diagnosis pack manifest should map report_4 to 04-live-repo-repair-plan.md")

        python_dest = workspace / "python-uv"
        shutil.copytree(full_dest, python_dest)
        seed_uv_python_fixture(python_dest)
        python_audit = run_json([sys.executable, str(AUDIT), str(python_dest), "--format", "json"], ROOT)
        python_codes = {finding["code"] for finding in python_audit.get("findings", [])}
        if "BOOT001" in python_codes:
            raise RuntimeError("A uv-shaped repo with the current bootstrap template should not emit BOOT001")

        deadlock_dest = workspace / "python-deadlock"
        shutil.copytree(python_dest, deadlock_dest)
        seed_bootstrap_deadlock(deadlock_dest)
        deadlock_audit = run_json([sys.executable, str(AUDIT), str(deadlock_dest), "--format", "json", "--emit-diagnosis-pack"], ROOT)
        deadlock_codes = {finding["code"] for finding in deadlock_audit.get("findings", [])}
        if "BOOT001" not in deadlock_codes:
            raise RuntimeError("A failed bootstrap artifact with missing pip should emit BOOT001")
        recommendations = (
            deadlock_audit.get("diagnosis_pack", {})
            .get("manifest", {})
            .get("ticket_recommendations", [])
        )
        if not any(item.get("source_finding_code") == "BOOT001" and item.get("route") == "scafforge-repair" for item in recommendations):
            raise RuntimeError("BOOT001 should route to scafforge-repair in the diagnosis pack")

        (full_dest / "docs" / "process" / "workflow.md").write_text("# drifted workflow\n", encoding="utf-8")
        run([sys.executable, str(REPAIR), str(full_dest), "--fail-on", "error"], ROOT)

        repaired_workflow = json.loads((full_dest / ".opencode" / "state" / "workflow-state.json").read_text(encoding="utf-8"))
        if repaired_workflow.get("process_version") != 5:
            raise RuntimeError("Repair should update workflow-state to process version 5")
        if repaired_workflow.get("pending_process_verification") is not True:
            raise RuntimeError("Repair should reopen post-migration verification")
        if not repaired_workflow.get("process_last_changed_at"):
            raise RuntimeError("Repair should record process_last_changed_at")
        for key in ("bootstrap", "lane_leases", "state_revision"):
            if key not in repaired_workflow:
                raise RuntimeError(f"Repair should preserve workflow key `{key}`")

        repaired_provenance = json.loads((full_dest / ".opencode" / "meta" / "bootstrap-provenance.json").read_text(encoding="utf-8"))
        if not repaired_provenance.get("repair_history"):
            raise RuntimeError("Repair should append repair_history")
        managed_surfaces = repaired_provenance.get("managed_surfaces", {})
        replace_on_retrofit = managed_surfaces.get("replace_on_retrofit", [])
        if "opencode.jsonc" not in replace_on_retrofit:
            raise RuntimeError("Repair provenance should list opencode.jsonc as a deterministic managed surface")

        repaired_workflow_doc = (full_dest / "docs" / "process" / "workflow.md").read_text(encoding="utf-8")
        if "# Workflow" not in repaired_workflow_doc:
            raise RuntimeError("Repair should restore docs/process/workflow.md from the scaffold")

        print("Scafforge smoke test passed.")
        return 0
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
