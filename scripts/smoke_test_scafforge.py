from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "skills" / "repo-scaffold-factory" / "scripts" / "bootstrap_repo_scaffold.py"
VERIFY_GENERATED = ROOT / "skills" / "repo-scaffold-factory" / "scripts" / "verify_generated_scaffold.py"
CHECKLIST = ROOT / "skills" / "repo-scaffold-factory" / "references" / "opencode-conformance-checklist.json"
AUDIT = ROOT / "skills" / "scafforge-audit" / "scripts" / "audit_repo_process.py"
REPAIR = ROOT / "skills" / "scafforge-repair" / "scripts" / "apply_repo_process_repair.py"
PUBLIC_REPAIR = ROOT / "skills" / "scafforge-repair" / "scripts" / "run_managed_repair.py"
REGENERATE = ROOT / "skills" / "scafforge-repair" / "scripts" / "regenerate_restart_surfaces.py"


def load_python_module(path: Path, module_name: str):
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def package_commit() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Unable to resolve package commit for smoke tests:\nSTDERR:\n{result.stderr}")
    return result.stdout.strip()


def run(command: list[str], cwd: Path, *, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")


def run_json(command: list[str], cwd: Path, *, env: dict[str, str] | None = None) -> dict:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Command did not return valid JSON: {' '.join(command)}\nSTDOUT:\n{result.stdout}") from exc


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
        "\n".join(pyproject_lines) + "\n",
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


def seed_bootstrap_command_layout_mismatch(dest: Path) -> None:
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    current_rel = ".opencode/state/artifacts/history/exec-014/bootstrap/2026-03-27T13-23-09-710Z-environment-bootstrap.md"
    previous_rel = ".opencode/state/artifacts/history/exec-014/bootstrap/2026-03-27T13-20-16-174Z-environment-bootstrap.md"
    current_path = dest / current_rel
    previous_path = dest / previous_rel
    current_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_body = "\n".join(
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
    ) + "\n"
    current_path.write_text(artifact_body, encoding="utf-8")
    previous_path.write_text(artifact_body, encoding="utf-8")
    workflow["bootstrap"] = {
        "status": "failed",
        "last_verified_at": "2026-03-27T13:23:09.710Z",
        "environment_fingerprint": "synthetic-bootstrap-command-mismatch",
        "proof_artifact": current_rel,
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
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")

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
        (dest / "START-HERE.md").read_text(encoding="utf-8").replace("openrouter/openai/gpt-5-mini", legacy_minimax),
        encoding="utf-8",
    )
    (dest / "docs" / "spec" / "CANONICAL-BRIEF.md").write_text(
        (dest / "docs" / "spec" / "CANONICAL-BRIEF.md").read_text(encoding="utf-8").replace("openrouter/openai/gpt-5-mini", legacy_minimax),
        encoding="utf-8",
    )
    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    team_text = team_leader.read_text(encoding="utf-8")
    team_text = team_text.replace("temperature: 1.0", "temperature: 0.2")
    team_text = team_text.replace("top_p: 0.95", "top_p: 0.7")
    if "top_k: 40\n" in team_text:
        team_text = team_text.replace("top_k: 40\n", "")
    team_text = team_text.replace("model: openrouter/anthropic/claude-sonnet-4.5", f"model: {legacy_minimax}")
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
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


def seed_repeated_diagnosis_churn(dest: Path) -> None:
    diagnosis_root = dest / "diagnosis"
    baseline = sorted(path for path in diagnosis_root.iterdir() if path.is_dir())[-1]
    baseline_manifest_path = baseline / "manifest.json"
    baseline_manifest = json.loads(baseline_manifest_path.read_text(encoding="utf-8"))
    baseline_manifest["generated_at"] = "2026-03-27T00:03:00Z"
    baseline_manifest["ticket_recommendations"] = [
        {
            "source_finding_code": "SKILL001",
            "route": "scafforge-repair",
            "title": "Regenerate placeholder repo-local skills",
        }
    ]
    baseline_manifest_path.write_text(json.dumps(baseline_manifest, indent=2) + "\n", encoding="utf-8")

    for folder_name, generated_at in (
        ("20260327-002513", "2026-03-27T00:25:13Z"),
        ("20260327-014404", "2026-03-27T01:44:04Z"),
    ):
        target = diagnosis_root / folder_name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(baseline, target)
        manifest_path = target / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["generated_at"] = generated_at
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def make_stack_skill_non_placeholder(dest: Path) -> None:
    skill_path = dest / ".opencode" / "skills" / "stack-standards" / "SKILL.md"
    skill_path.write_text(
        skill_path.read_text(encoding="utf-8").replace(
            "Replace this file with stack-specific rules once the real project stack is known.",
            "Use `uv run pytest -q` for validation and keep Python tooling repo-local via `uv`.",
        ),
        encoding="utf-8",
    )


def seed_workflow_overclaim(dest: Path) -> Path:
    manifest_path = dest / "tickets" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
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
            "acceptance": ["Dependency claim remains blocked until the active ticket is done."],
            "decision_blockers": [],
            "artifacts": [],
            "resolution_state": "open",
            "verification_state": "suspect",
            "follow_up_ticket_ids": [],
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    overclaim = (
        "Active work is only blocked by a tool/env mismatch, not a code defect. "
        "The downstream dependency is now unblocked and ready to proceed."
    )
    for relative in ("START-HERE.md", ".opencode/state/latest-handoff.md"):
        path = dest / relative
        original = path.read_text(encoding="utf-8") if path.exists() else (dest / "START-HERE.md").read_text(encoding="utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        if "## Next Action" in original:
            updated = original.replace("## Next Action", f"## Next Action\n\n{overclaim}\n")
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
                '    return JSON.stringify({ argv: [\"python3\", \"-m\", \"pytest\"] })',
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
    workflow_text = workflow_text.replace("`todo`, `ready`, `plan_review`, `in_progress`, `blocked`, `review`, `qa`, `smoke_test`, `done`", "`todo`, `ready`, `in_progress`, `blocked`, `review`, `qa`, `smoke_test`, `done`")
    workflow_text = workflow_text.replace("`plan_review`", "plan review")
    workflow_text = workflow_text.replace("the assigned ticket must already be in plan review and ", "")
    workflow_doc.write_text(workflow_text, encoding="utf-8")
    workflow_tool = dest / ".opencode" / "lib" / "workflow.ts"
    workflow_tool.write_text(workflow_tool.read_text(encoding="utf-8").replace('"plan_review"', '"review"'), encoding="utf-8")


def seed_legacy_stage_transition_contract(dest: Path) -> None:
    ticket_update = dest / ".opencode" / "tools" / "ticket_update.ts"
    ticket_text = ticket_update.read_text(encoding="utf-8")
    ticket_text = ticket_text.replace('ticket.stage !== "plan_review"', 'ticket.status !== "plan_review"')
    ticket_text = ticket_text.replace("const requested = resolveRequestedTicketProgress(ticket, { stage: args.stage, status: args.status })", "const requested = { stage: args.stage || ticket.stage, status: args.status || ticket.status }")
    ticket_text = ticket_text.replace(
        "    const lifecycleBlocker = validateLifecycleStageStatus(targetStage, targetStatus)\n    if (lifecycleBlocker) {\n      throw new Error(lifecycleBlocker)\n    }\n",
        "",
    )
    ticket_update.write_text(ticket_text, encoding="utf-8")

    workflow_tool = dest / ".opencode" / "lib" / "workflow.ts"
    workflow_text = workflow_tool.read_text(encoding="utf-8")
    workflow_text = workflow_text.replace('export const LIFECYCLE_STAGES = new Set(["planning", "plan_review", "implementation", "review", "qa", "smoke-test", "closeout"])\n', "")
    workflow_text = workflow_text.replace(
        '    return `Unsupported ticket stage: ${stage}. Use planning, plan_review, implementation, review, qa, smoke-test, or closeout.`\n',
        "    return null\n",
    )
    workflow_tool.write_text(workflow_text, encoding="utf-8")

    stage_gate = dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    stage_gate_text = stage_gate.read_text(encoding="utf-8")
    stage_gate_text = stage_gate_text.replace('ticket.stage !== "plan_review"', 'ticket.status !== "plan_review"')
    stage_gate_text = stage_gate_text.replace("resolveRequestedTicketProgress,\n", "")
    stage_gate_text = stage_gate_text.replace("validateLifecycleStageStatus,\n", "")
    stage_gate_text = stage_gate_text.replace(
        "        const requested = resolveRequestedTicketProgress(ticket, {\n          stage: typeof output.args.stage === \"string\" ? output.args.stage : undefined,\n          status: typeof output.args.status === \"string\" ? output.args.status : undefined,\n        })\n        const lifecycleBlocker = validateLifecycleStageStatus(requested.stage, requested.status)\n        if (lifecycleBlocker) {\n          throw new Error(lifecycleBlocker)\n        }\n",
        "        const requested = {\n          stage: typeof output.args.stage === \"string\" ? output.args.stage : ticket.stage,\n          status: typeof output.args.status === \"string\" ? output.args.status : ticket.status,\n        }\n",
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
    stage_gate_text = stage_gate_text.replace('const RESERVED_ARTIFACT_STAGES = new Set(["smoke-test"])\n', "")
    stage_gate_text = stage_gate_text.replace(
        "        if (RESERVED_ARTIFACT_STAGES.has(stage)) {\n          const owner = stage === \"smoke-test\" ? \"smoke_test\" : \"handoff_publish\"\n          throw new Error(`Use ${owner} to create ${stage} artifacts. Generic artifact_register is not allowed for that stage.`)\n        }\n\n",
        "",
    )
    stage_gate_text = stage_gate_text.replace(
        "        if (RESERVED_ARTIFACT_STAGES.has(stage)) {\n          const owner = stage === \"smoke-test\" ? \"smoke_test\" : \"handoff_publish\"\n          throw new Error(`Use ${owner} to create ${stage} artifacts. Generic artifact_write is not allowed for that stage.`)\n        }\n",
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


def write_python_wrapper(path: Path, *, allow_pytest: bool) -> None:
    real_python = sys.executable
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"#!{real_python}",
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


def seed_failing_pytest_suite(dest: Path) -> None:
    seed_uv_python_fixture(dest)
    src_pkg = dest / "src" / "smoke_pkg"
    src_pkg.mkdir(parents=True, exist_ok=True)
    (src_pkg / "__init__.py").write_text("__all__ = ['ok']\n", encoding="utf-8")
    tests_dir = dest / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_sample.py").write_text("def test_smoke():\n    assert True\n", encoding="utf-8")

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


def seed_missing_pytest_env(dest: Path) -> None:
    seed_uv_python_fixture(dest)
    src_pkg = dest / "src" / "smoke_pkg"
    src_pkg.mkdir(parents=True, exist_ok=True)
    (src_pkg / "__init__.py").write_text("__all__ = ['ok']\n", encoding="utf-8")
    tests_dir = dest / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_sample.py").write_text("def test_smoke():\n    assert True\n", encoding="utf-8")
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
                'export function _workflow_validateHandoffNextAction() {',
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
    (diagnosis_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


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
            {"source_finding_code": "SESSION003", "route": "scafforge-repair", "title": "workflow bypass search"},
            {"source_finding_code": "SESSION005", "route": "scafforge-repair", "title": "coordinator artifact authorship"},
            {"source_finding_code": "WFLOW016", "route": "scafforge-repair", "title": "smoke override defect"},
            {"source_finding_code": "WFLOW017", "route": "scafforge-repair", "title": "smoke acceptance drift"},
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
            {"source_finding_code": "SESSION003", "route": "scafforge-repair", "title": "workflow bypass search"},
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
            {"source_finding_code": "SESSION005", "route": "scafforge-repair", "title": "coordinator artifact authorship"},
        ],
        supporting_logs=["later-transcript.md"],
    )


def seed_historical_reconciliation_deadlock(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
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
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")

    ticket_reconcile_path = dest / ".opencode" / "tools" / "ticket_reconcile.ts"
    ticket_reconcile_text = ticket_reconcile_path.read_text(encoding="utf-8")
    ticket_reconcile_text = ticket_reconcile_text.replace("currentRegistryArtifact,\n", "")
    ticket_reconcile_text = ticket_reconcile_text.replace(
        "function findEvidenceArtifact(sourceTicket: Ticket, targetTicket: Ticket, registry: Awaited<ReturnType<typeof loadArtifactRegistry>>, artifactPath: string): Artifact | undefined {\n"
        "  const normalized = normalizeRepoPath(artifactPath)\n"
        "  return [...sourceTicket.artifacts, ...targetTicket.artifacts].find(\n"
        "    (artifact) => artifact.path === normalized && artifact.trust_state === \"current\",\n"
        "  ) ?? currentRegistryArtifact(registry, normalized)\n"
        "}\n",
        "function findEvidenceArtifact(sourceTicket: Ticket, targetTicket: Ticket, artifactPath: string): Artifact | undefined {\n"
        "  const normalized = normalizeRepoPath(artifactPath)\n"
        "  return [...sourceTicket.artifacts, ...targetTicket.artifacts].find(\n"
        "    (artifact) => artifact.path === normalized && artifact.trust_state === \"current\",\n"
        "  )\n"
        "}\n",
    )
    ticket_reconcile_text = ticket_reconcile_text.replace(
        "    const registry = await loadArtifactRegistry()\n    const evidenceArtifact = findEvidenceArtifact(sourceTicket, targetTicket, registry, evidenceArtifactPath)\n",
        "    const registry = await loadArtifactRegistry()\n    const evidenceArtifact = findEvidenceArtifact(sourceTicket, targetTicket, evidenceArtifactPath)\n",
    )
    ticket_reconcile_text = ticket_reconcile_text.replace(
        '      throw new Error(`No current registered evidence artifact exists at ${evidenceArtifactPath} for this reconciliation.`)\n',
        '      throw new Error(`Neither ${sourceTicket.id} nor ${targetTicket.id} has a current evidence artifact at ${evidenceArtifactPath}.`)\n',
    )
    ticket_reconcile_text = ticket_reconcile_text.replace('      targetTicket.verification_state = "reverified"\n', '      targetTicket.verification_state = "invalidated"\n')
    ticket_reconcile_text = ticket_reconcile_text.replace("        supersededTarget: supersedeTarget,\n", "        supersededTarget,\n")
    ticket_reconcile_path.write_text(ticket_reconcile_text, encoding="utf-8")

    ticket_create_path = dest / ".opencode" / "tools" / "ticket_create.ts"
    ticket_create_text = ticket_create_path.read_text(encoding="utf-8")
    ticket_create_text = ticket_create_text.replace("  currentRegistryArtifact,\n", "")
    ticket_create_text = ticket_create_text.replace("  loadArtifactRegistry,\n", "")
    ticket_create_text = ticket_create_text.replace("  normalizeRepoPath,\n", "")
    ticket_create_text = ticket_create_text.replace("    const registry = await loadArtifactRegistry()\n", "")
    ticket_create_text = ticket_create_text.replace(
        "        const registryArtifact = evidenceArtifactPath ? currentRegistryArtifact(registry, normalizeRepoPath(evidenceArtifactPath)) : undefined\n"
        "        if (\n"
        "          !verificationArtifact &&\n"
        "          !(registryArtifact && registryArtifact.stage === \"review\" && registryArtifact.kind === \"backlog-verification\")\n"
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
        "environment_fingerprint": "synthetic-ready-bootstrap",
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


def seed_process_verification_clear_deadlock(dest: Path, *, stale_surfaces: bool) -> None:
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
            text = text.replace("- handoff_status: workflow verification pending", "- handoff_status: ready for continued development")
            text = text.replace(f"- done_but_not_fully_trusted: {ticket['id']}", "- done_but_not_fully_trusted: none")
            text = re.sub(
                r"Use the team leader to route .*? across done tickets whose trust predates the current process contract\.",
                "All tickets complete and verified. Continue normal development.",
                text,
            )
            surface_path.write_text(text, encoding="utf-8")

        stage_gate_path = dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
        stage_gate_text = stage_gate_path.read_text(encoding="utf-8")
        stage_gate_text = stage_gate_text.replace(
            '        const processVerificationClearOnly = isWorkflowProcessVerificationClearOnly(output.args)\n'
            '        const processVerification = getProcessVerificationState(manifest, workflow, ticketId)\n'
            '        if (!(processVerificationClearOnly && processVerification.clearable_now)) {\n'
            '          await ensureTargetTicketWriteLease(ticketId)\n'
            '        }\n',
            '        await ensureTargetTicketWriteLease(ticketId)\n',
        )
        stage_gate_path.write_text(stage_gate_text, encoding="utf-8")


def seed_closed_follow_up_deadlock(dest: Path) -> None:
    stage_gate = dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    text = stage_gate.read_text(encoding="utf-8")
    if 'await ensureTargetTicketWriteLease(sourceTicketId || workflow.active_ticket)' not in text:
        text = text.replace(
            '        if (sourceMode === "process_verification" && !workflow.pending_process_verification) {\n',
            '        await ensureTargetTicketWriteLease(sourceTicketId || workflow.active_ticket)\n        if (sourceMode === "process_verification" && !workflow.pending_process_verification) {\n',
        )
    issue_intake_marker = (
        '        const sourceTicket = getTicket(manifest, sourceTicketId)\n'
        '        if (sourceTicket.status !== "done" && sourceTicket.resolution_state !== "done" && sourceTicket.resolution_state !== "superseded") {\n'
    )
    if issue_intake_marker in text and '        await ensureTargetTicketWriteLease(sourceTicketId)\n' not in text:
        text = text.replace(
            issue_intake_marker,
            '        await ensureTargetTicketWriteLease(sourceTicketId)\n' + issue_intake_marker,
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
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def seed_restart_surface_drift(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
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
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")

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
        implementer.read_text(encoding="utf-8").replace(
            "  environment_bootstrap: allow\n",
            "  environment_bootstrap: allow\n  ticket_claim: allow\n  ticket_release: allow\n",
        ).replace(
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
        resume.read_text(encoding="utf-8").replace(
            "Resume from `tickets/manifest.json` and `.opencode/state/workflow-state.json` first. Use `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` only as derived restart surfaces that must agree with canonical state.\n",
            "Resume from `START-HERE.md` first and use the other workflow files as support when needed.\n",
        ).replace(
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
    log_path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")


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
        "environment_fingerprint": "synthetic-ready-bootstrap",
        "proof_artifact": ".opencode/state/bootstrap/synthetic-ready-bootstrap.md",
    }
    proof_path = dest / ".opencode" / "state" / "bootstrap" / "synthetic-ready-bootstrap.md"
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text("# Ready Bootstrap\n", encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def seed_reverification_deadlock(dest: Path) -> None:
    stage_gate = dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    text = stage_gate.read_text(encoding="utf-8")
    text = text.replace(
        '        const ticket = getTicket(manifest, ticketId)\n        if (ticket.status !== "done") {\n          throw new Error(`Ticket ${ticket.id} must already be done before ticket_reverify can restore trust.`)\n        }\n',
        '        await ensureTargetTicketWriteLease(ticketId)\n',
    )
    stage_gate.write_text(text, encoding="utf-8")


def seed_team_leader_workflow_drift(dest: Path) -> None:
    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    text = team_leader.read_text(encoding="utf-8")
    text = text.replace("Treat `ticket_lookup.transition_guidance` as the canonical next-step summary before you call `ticket_update`.\n", "")
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

        context_snapshot = (dest / ".opencode" / "state" / "context-snapshot.md").read_text(encoding="utf-8")
        for heading in ("## Active Ticket", "## Bootstrap", "## Process State", "## Lane Leases"):
            if heading not in context_snapshot:
                raise RuntimeError(f"context-snapshot.md is missing required section `{heading}`")


def main() -> int:
    workspace = Path(tempfile.mkdtemp(prefix="scafforge-smoke-"))
    host_has_uv = shutil.which("uv") is not None
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

        generated_ticket_update = (full_dest / ".opencode" / "tools" / "ticket_update.ts").read_text(encoding="utf-8")
        if '"plan_review"' not in generated_ticket_update:
            raise RuntimeError("Generated ticket_update.ts should expose the explicit plan_review status")
        generated_bootstrap = (full_dest / ".opencode" / "tools" / "environment_bootstrap.ts").read_text(encoding="utf-8")
        for expected in ("[project.optional-dependencies]", "[dependency-groups]", "[tool.uv.dev-dependencies]", "[tool.pytest.ini_options]"):
            if expected not in generated_bootstrap:
                raise RuntimeError(f"Generated environment_bootstrap.ts should detect {expected} when resolving Python bootstrap inputs")
        if "extractTomlSectionBody" not in generated_bootstrap or "escapeRegExp" not in generated_bootstrap:
            raise RuntimeError("Generated environment_bootstrap.ts should use explicit TOML section parsing helpers for dependency-layout detection")
        if "(?:\\\\n\\\\[|$)" in generated_bootstrap:
            raise RuntimeError("Generated environment_bootstrap.ts should not keep the legacy multiline section regex that misses optional dependency bodies")
        if "defaultBootstrapProofPath" not in generated_bootstrap or "normalizeRepoPath" not in generated_bootstrap:
            raise RuntimeError("Generated environment_bootstrap.ts should persist bootstrap proof through canonical artifact-path helpers")
        generated_smoke_test = (full_dest / ".opencode" / "tools" / "smoke_test.ts").read_text(encoding="utf-8")
        if 'join(root, ".venv", "bin", "python")' not in generated_smoke_test:
            raise RuntimeError("Generated smoke_test.ts should support repo-local .venv Python execution")
        if "[tool.pytest.ini_options]" not in generated_smoke_test:
            raise RuntimeError("Generated smoke_test.ts should detect pyproject-only pytest configuration, not only tests/ or pytest.ini")
        for expected in ("scope:", "test_paths:", "args.scope", "args.test_paths"):
            if expected not in generated_smoke_test:
                raise RuntimeError("Generated smoke_test.ts should expose scoped smoke inputs and thread them into execution")
        if "multiple shell-style command strings executed in order" not in generated_smoke_test:
            raise RuntimeError("Generated smoke_test.ts should document multi-command shell-style command_override input")
        if "command_override cannot mix tokenized argv entries with multiple shell-style command strings." not in generated_smoke_test:
            raise RuntimeError("Generated smoke_test.ts should reject malformed mixed command_override forms")
        if "defaultArtifactPath" not in generated_smoke_test or "normalizeRepoPath" not in generated_smoke_test:
            raise RuntimeError("Generated smoke_test.ts should persist smoke artifacts through canonical artifact-path helpers")
        generated_stage_gate = (full_dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts").read_text(encoding="utf-8")
        if 'const RESERVED_ARTIFACT_STAGES = new Set(["smoke-test"])' not in generated_stage_gate:
            raise RuntimeError("Generated stage-gate-enforcer.ts should reserve smoke-test artifacts to their owning tool")
        if "Generic artifact_write is not allowed for that stage." not in generated_stage_gate:
            raise RuntimeError("Generated stage-gate-enforcer.ts should block generic artifact_write for smoke-test")
        if 'type: "BLOCKER"' not in generated_stage_gate or "missing_write_lease" not in generated_stage_gate:
            raise RuntimeError("Generated stage-gate-enforcer.ts should emit structured blockers for missing lease conditions")
        if 'await ensureTargetTicketWriteLease(targetTicket.id)' not in generated_stage_gate:
            raise RuntimeError("Generated stage-gate-enforcer.ts should require a write lease for open ticket_reconcile targets")
        generated_workflow = (full_dest / ".opencode" / "lib" / "workflow.ts").read_text(encoding="utf-8")
        if (full_dest / ".opencode" / "tools" / "_workflow.ts").exists():
            raise RuntimeError("Generated helper workflow library should stay private under .opencode/lib instead of leaking a callable _workflow.ts tool")
        if "tool({" in generated_workflow:
            raise RuntimeError("Generated workflow library should remain helper-only and must not expose a model-callable tool surface")
        if "refreshRestartSurfaces" not in generated_workflow:
            raise RuntimeError("Generated workflow.ts should refresh derived restart surfaces after workflow mutations")
        if "latestHandoffPath" not in generated_workflow:
            raise RuntimeError("Generated workflow.ts should own the latest-handoff restart surface")
        if "Historical done-ticket reverification stays secondary until the active open ticket is resolved." not in generated_workflow:
            raise RuntimeError("Generated workflow.ts should keep the active open ticket primary when process verification is pending")
        if "Cannot publish dependency-readiness claims" not in generated_workflow or "Cannot publish causal claims" not in generated_workflow:
            raise RuntimeError("Generated workflow.ts should truthfully gate handoff claims against canonical state and smoke evidence")
        generated_ticket_lookup = (full_dest / ".opencode" / "tools" / "ticket_lookup.ts").read_text(encoding="utf-8")
        if "transition_guidance" not in generated_ticket_lookup:
            raise RuntimeError("Generated ticket_lookup.ts should expose transition_guidance")
        if "Do not fabricate a PASS artifact through generic artifact tools." not in generated_ticket_lookup:
            raise RuntimeError("Generated ticket_lookup.ts should warn against generic PASS artifact fabrication")
        if "Run environment_bootstrap first, then rerun ticket_lookup before attempting lifecycle transitions." not in generated_ticket_lookup:
            raise RuntimeError("Generated ticket_lookup.ts should short-circuit lifecycle guidance to environment_bootstrap when bootstrap is not ready")
        if "Keep ${ticket.id} open as a split parent and foreground child ticket ${foregroundChild.id} instead of advancing the parent lane directly." not in generated_ticket_lookup:
            raise RuntimeError("Generated ticket_lookup.ts should foreground split children without marking the parent blocked")
        if 'next_action_tool: "smoke_test",\n          delegate_to_agent: null,\n          required_owner: "team-leader",' not in generated_ticket_lookup:
            raise RuntimeError("Generated ticket_lookup.ts should keep smoke_test team-leader-owned instead of delegating it to tester-qa")
        generated_ticket_create = (full_dest / ".opencode" / "tools" / "ticket_create.ts").read_text(encoding="utf-8")
        if 'status = "blocked"' in generated_ticket_create:
            raise RuntimeError("Generated ticket_create.ts should not mark split-scope parents blocked")
        if "Keep the parent open and non-foreground until the child work lands." not in generated_ticket_create:
            raise RuntimeError("Generated ticket_create.ts should leave split-scope parents open and linked to their children")
        generated_ticket_reconcile = (full_dest / ".opencode" / "tools" / "ticket_reconcile.ts").read_text(encoding="utf-8")
        if "currentRegistryArtifact" not in generated_ticket_reconcile:
            raise RuntimeError("Generated ticket_reconcile.ts should allow current registered evidence to justify historical reconciliation")
        if 'targetTicket.verification_state = "reverified"' not in generated_ticket_reconcile:
            raise RuntimeError("Generated ticket_reconcile.ts should leave successfully superseded historical targets non-blocking for handoff publication")
        if "supersededTarget,\n" in generated_ticket_reconcile:
            raise RuntimeError("Generated ticket_reconcile.ts should not contain the legacy supersededTarget runtime typo")
        generated_team_leader = next((full_dest / ".opencode" / "agents").glob("*team-leader*.md")).read_text(encoding="utf-8")
        if "do not create planning, implementation, review, QA, or smoke-test artifacts yourself" not in generated_team_leader:
            raise RuntimeError("Generated team leader prompt should forbid coordinator-authored specialist artifacts")
        if "If `ticket_lookup.bootstrap.status` is not `ready`, treat `environment_bootstrap` as the next required tool call" not in generated_team_leader:
            raise RuntimeError("Generated team leader prompt should make bootstrap-first routing explicit")
        if "same command trace but it still contradicts the repo's declared dependency layout" not in generated_team_leader:
            raise RuntimeError("Generated team leader prompt should escalate repeated bootstrap command/layout contradictions as managed defects")
        if "grant a write lease with `ticket_claim` before any specialist writes planning, implementation, review, QA, or handoff artifact bodies or makes code changes" not in generated_team_leader:
            raise RuntimeError("Generated team leader prompt should own the lease claim path")
        if "ticket_create: allow" not in generated_team_leader or "ticket_reconcile: allow" not in generated_team_leader:
            raise RuntimeError("Generated team leader prompt should be allowed to invoke ticket_create and ticket_reconcile")
        generated_ticket_execution = (full_dest / ".opencode" / "skills" / "ticket-execution" / "SKILL.md").read_text(encoding="utf-8")
        if "slash commands are human entrypoints" not in generated_ticket_execution:
            raise RuntimeError("Generated ticket-execution skill should mark slash commands as human entrypoints only")
        if "if `ticket_lookup.bootstrap.status` is not `ready`, stop normal lifecycle routing, run `environment_bootstrap`, then rerun `ticket_lookup` before any `ticket_update`" not in generated_ticket_execution:
            raise RuntimeError("Generated ticket-execution skill should treat bootstrap readiness as a pre-lifecycle gate")
        if "same command trace but it still omits the dependency-group or extra flags the repo layout requires" not in generated_ticket_execution:
            raise RuntimeError("Generated ticket-execution skill should stop retrying when bootstrap artifacts prove a managed command/layout mismatch")
        if "the team leader claims and releases write leases" not in generated_ticket_execution:
            raise RuntimeError("Generated ticket-execution skill should encode the coordinator-owned lease model")
        generated_ticket_creator = next((full_dest / ".opencode" / "agents").glob("*ticket-creator*.md")).read_text(encoding="utf-8")
        if "ticket_reconcile: allow" not in generated_ticket_creator:
            raise RuntimeError("Generated ticket creator prompt should be allowed to invoke ticket_reconcile")
        generated_resume = (full_dest / ".opencode" / "commands" / "resume.md").read_text(encoding="utf-8")
        if "Resume from `tickets/manifest.json` and `.opencode/state/workflow-state.json` first." not in generated_resume:
            raise RuntimeError("Generated /resume command should treat manifest and workflow-state as canonical")
        if ".opencode/state/latest-handoff.md" not in generated_resume:
            raise RuntimeError("Generated /resume command should mention latest-handoff as a derived restart surface")
        if "same command trace but it still contradicts the repo's declared dependency layout" not in generated_resume:
            raise RuntimeError("Generated /resume command should stop bootstrap retries when artifacts prove a managed command/layout mismatch")
        if "handoff_allowed" in generated_resume:
            raise RuntimeError("Generated /resume command should not route from legacy handoff_allowed fields")
        generated_implementer = next((full_dest / ".opencode" / "agents").glob("*implementer*.md")).read_text(encoding="utf-8")
        if "ticket_claim: allow" in generated_implementer or "ticket_release: allow" in generated_implementer:
            raise RuntimeError("Generated implementer should not own ticket claim or release")
        latest_handoff = (full_dest / ".opencode" / "state" / "latest-handoff.md").read_text(encoding="utf-8")
        if "bootstrap recovery required" not in latest_handoff:
            raise RuntimeError("Generated latest-handoff should be seeded from the managed restart narrative")
        if "- split_child_tickets: none" not in latest_handoff or "repair_follow_on_handoff_allowed" in latest_handoff:
            raise RuntimeError("Generated latest-handoff should expose split-child status and omit legacy repair handoff gating")
        start_here = (full_dest / "START-HERE.md").read_text(encoding="utf-8")
        if "- split_child_tickets: none" not in start_here or "repair_follow_on_handoff_allowed" in start_here:
            raise RuntimeError("Generated START-HERE should expose split-child status and omit legacy repair handoff gating")
        context_snapshot = (full_dest / ".opencode" / "state" / "context-snapshot.md").read_text(encoding="utf-8")
        if "- Open split children: none" not in context_snapshot or "- handoff_allowed:" in context_snapshot:
            raise RuntimeError("Generated context snapshot should expose split children and omit public handoff_allowed state")
        invocation_tracker = (full_dest / ".opencode" / "plugins" / "invocation-tracker.ts").read_text(encoding="utf-8")
        if "agent: input.agent ?? null" not in invocation_tracker:
            raise RuntimeError("Generated invocation-tracker.ts should record agent ownership on command and tool events")
        generated_handoff_publish = (full_dest / ".opencode" / "tools" / "handoff_publish.ts").read_text(encoding="utf-8")
        if "validateHandoffNextAction" not in generated_handoff_publish:
            raise RuntimeError("Generated handoff_publish.ts should validate custom next_action claims before publishing")
        if generated_handoff_publish.find("const handoffBlocker = await validateHandoffNextAction") >= generated_handoff_publish.find("await refreshRestartSurfaces"):
            raise RuntimeError("Generated handoff_publish.ts should validate next_action claims before refreshing restart surfaces")
        generated_artifact_write = (full_dest / ".opencode" / "tools" / "artifact_write.ts").read_text(encoding="utf-8")
        if "expectedPath = defaultArtifactPath" not in generated_artifact_write or "canonicalizeRepoPath(args.path)" not in generated_artifact_write:
            raise RuntimeError("Generated artifact_write.ts should enforce canonical artifact paths")
        generated_artifact_register = (full_dest / ".opencode" / "tools" / "artifact_register.ts").read_text(encoding="utf-8")
        if "expectedPath = defaultArtifactPath" not in generated_artifact_register or "canonicalizeRepoPath(args.path)" not in generated_artifact_register:
            raise RuntimeError("Generated artifact_register.ts should enforce canonical artifact paths")

        greenfield_gate_dest = workspace / "greenfield-proof-gate"
        shutil.copytree(full_dest, greenfield_gate_dest)
        make_stack_skill_non_placeholder(greenfield_gate_dest)
        greenfield_gate = run_json([sys.executable, str(VERIFY_GENERATED), str(greenfield_gate_dest), "--format", "json"], ROOT)
        if greenfield_gate.get("findings"):
            codes = ", ".join(item["code"] for item in greenfield_gate.get("findings", []))
            raise RuntimeError(f"A placeholder-free fresh scaffold should pass the shared greenfield continuation verifier, but it emitted: {codes}")

        corrupt_gate_dest = workspace / "greenfield-proof-gate-corrupt"
        shutil.copytree(greenfield_gate_dest, corrupt_gate_dest)
        (corrupt_gate_dest / "tickets" / "manifest.json").write_text("{\n", encoding="utf-8")
        corrupt_gate_result = subprocess.run(
            [sys.executable, str(VERIFY_GENERATED), str(corrupt_gate_dest), "--format", "json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        corrupt_gate_payload = json.loads(corrupt_gate_result.stdout)
        corrupt_gate_codes = {finding["code"] for finding in corrupt_gate_payload.get("findings", [])}
        if corrupt_gate_result.returncode != 2:
            raise RuntimeError("Generated scaffold verifier should fail with exit code 2 when canonical state is corrupt")
        if "VERIFY001" not in corrupt_gate_codes:
            raise RuntimeError("Generated scaffold verifier should emit VERIFY001 instead of crashing on corrupt JSON state")

        workflow_contract_drift_dest = workspace / "greenfield-proof-gate-workflow-contract-drift"
        shutil.copytree(greenfield_gate_dest, workflow_contract_drift_dest)
        tooling_doc_path = workflow_contract_drift_dest / "docs" / "process" / "tooling.md"
        tooling_doc = tooling_doc_path.read_text(encoding="utf-8")
        tooling_doc_path.write_text(
            tooling_doc.replace("commands are human entrypoints only", "commands may drive the autonomous workflow"),
            encoding="utf-8",
        )
        workflow_contract_gate_result = subprocess.run(
            [sys.executable, str(VERIFY_GENERATED), str(workflow_contract_drift_dest), "--format", "json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        workflow_contract_gate = json.loads(workflow_contract_gate_result.stdout)
        workflow_contract_gate_codes = {finding["code"] for finding in workflow_contract_gate.get("findings", [])}
        if workflow_contract_gate_result.returncode != 2:
            raise RuntimeError("Generated scaffold verifier should fail when continuation-critical workflow contract surfaces drift")
        if "VERIFY008" not in workflow_contract_gate_codes:
            raise RuntimeError("Generated scaffold verifier should emit VERIFY008 when tooling and execution surfaces drift from the documented greenfield contract")

        repair_scripts_dir = ROOT / "skills" / "scafforge-repair" / "scripts"
        audit_scripts_dir = ROOT / "skills" / "scafforge-audit" / "scripts"
        for script_dir in (repair_scripts_dir, audit_scripts_dir):
            script_dir_str = str(script_dir)
            if script_dir_str not in sys.path:
                sys.path.insert(0, script_dir_str)
        repair_module = load_python_module(REPAIR, "scafforge_smoke_apply_repo_process_repair")
        env_only_stale_surface_map = repair_module.build_stale_surface_map(
            ROOT,
            [],
            [SimpleNamespace(code="ENV001")],
            False,
        )
        if env_only_stale_surface_map["workflow_tools_and_prompts"]["status"] != "stable":
            raise RuntimeError("ENV-only findings should not misclassify workflow_tools_and_prompts as managed replacement drift")
        if env_only_stale_surface_map["workflow_tools_and_prompts"].get("finding_codes"):
            raise RuntimeError("ENV-only findings should not populate workflow_tools_and_prompts finding codes")

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
        if diagnosis_manifest.get("diagnosis_kind") != "initial_diagnosis":
            raise RuntimeError("Initial audit diagnosis packs should be labeled initial_diagnosis")
        if not isinstance(diagnosis_manifest.get("audit_package_commit"), str) or not diagnosis_manifest.get("audit_package_commit"):
            raise RuntimeError("Diagnosis pack manifest should record the Scafforge audit package commit")
        if "package_work_required_first" not in diagnosis_manifest or "recommended_next_step" not in diagnosis_manifest:
            raise RuntimeError("Diagnosis pack manifest should record package-work gating and the recommended next step")

        restart_surface_dest = workspace / "restart-surface-drift"
        shutil.copytree(full_dest, restart_surface_dest)
        seed_restart_surface_drift(restart_surface_dest)
        restart_surface_audit = run_json([sys.executable, str(AUDIT), str(restart_surface_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        restart_surface_codes = {finding["code"] for finding in restart_surface_audit.get("findings", [])}
        if "WFLOW010" not in restart_surface_codes:
            raise RuntimeError("A repo whose START-HERE or context snapshot drifts from canonical workflow state should emit WFLOW010")

        bootstrap_guidance_dest = workspace / "bootstrap-guidance-drift"
        shutil.copytree(full_dest, bootstrap_guidance_dest)
        seed_bootstrap_guidance_drift(bootstrap_guidance_dest)
        make_stack_skill_non_placeholder(bootstrap_guidance_dest)
        bootstrap_guidance_gate_result = subprocess.run(
            [sys.executable, str(VERIFY_GENERATED), str(bootstrap_guidance_dest), "--format", "json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        bootstrap_guidance_gate = json.loads(bootstrap_guidance_gate_result.stdout)
        bootstrap_guidance_gate_codes = {finding["code"] for finding in bootstrap_guidance_gate.get("findings", [])}
        if "VERIFY006" not in bootstrap_guidance_gate_codes:
            raise RuntimeError("A repo whose greenfield bootstrap routing drifted should fail the shared continuation verifier with VERIFY006")
        bootstrap_guidance_audit = run_json([sys.executable, str(AUDIT), str(bootstrap_guidance_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        bootstrap_guidance_codes = {finding["code"] for finding in bootstrap_guidance_audit.get("findings", [])}
        if "WFLOW011" not in bootstrap_guidance_codes:
            raise RuntimeError("A repo whose workflow surfaces do not route failed bootstrap to environment_bootstrap first should emit WFLOW011")

        split_lease_dest = workspace / "split-lease-guidance"
        shutil.copytree(full_dest, split_lease_dest)
        seed_split_lease_guidance(split_lease_dest)
        split_lease_audit = run_json([sys.executable, str(AUDIT), str(split_lease_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        split_lease_codes = {finding["code"] for finding in split_lease_audit.get("findings", [])}
        if "WFLOW012" not in split_lease_codes:
            raise RuntimeError("A repo whose prompts split lease ownership between coordinator and workers should emit WFLOW012")

        resume_truth_dest = workspace / "resume-truth-hierarchy"
        shutil.copytree(full_dest, resume_truth_dest)
        seed_resume_truth_hierarchy_drift(resume_truth_dest)
        resume_truth_audit = run_json([sys.executable, str(AUDIT), str(resume_truth_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        resume_truth_codes = {finding["code"] for finding in resume_truth_audit.get("findings", [])}
        if "WFLOW013" not in resume_truth_codes:
            raise RuntimeError("A repo whose resume surfaces treat derived handoff text as canonical should emit WFLOW013")

        legacy_gate_dest = workspace / "legacy-repair-gate"
        shutil.copytree(full_dest, legacy_gate_dest)
        seed_legacy_repair_follow_on_gate_leak(legacy_gate_dest)
        legacy_gate_audit = run_json([sys.executable, str(AUDIT), str(legacy_gate_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        legacy_gate_codes = {finding["code"] for finding in legacy_gate_audit.get("findings", [])}
        if "WFLOW021" not in legacy_gate_codes:
            raise RuntimeError("A repo whose prompts or restart surfaces still route from handoff_allowed should emit WFLOW021")

        invocation_log_dest = workspace / "invocation-log-coordinator-artifacts"
        shutil.copytree(full_dest, invocation_log_dest)
        seed_invocation_log_coordinator_artifacts(invocation_log_dest)
        invocation_log_audit = run_json([sys.executable, str(AUDIT), str(invocation_log_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        invocation_log_codes = {finding["code"] for finding in invocation_log_audit.get("findings", [])}
        if "WFLOW014" not in invocation_log_codes:
            raise RuntimeError("A repo whose invocation log shows coordinator-authored specialist artifacts should emit WFLOW014")

        restart_repair_dest = workspace / "restart-surface-repair"
        shutil.copytree(full_dest, restart_repair_dest)
        seed_restart_surface_drift(restart_repair_dest)
        run_json([sys.executable, str(REPAIR), str(restart_repair_dest)], ROOT)
        repaired_start_here = (restart_repair_dest / "START-HERE.md").read_text(encoding="utf-8")
        if (
            "- bootstrap_status: failed" not in repaired_start_here
            or "- pending_process_verification: true" not in repaired_start_here
            or "- repair_follow_on_outcome: managed_blocked" not in repaired_start_here
            or "- handoff_status: bootstrap recovery required" not in repaired_start_here
            or "- repair_follow_on_required: true" not in repaired_start_here
            or "- split_child_tickets: none" not in repaired_start_here
        ):
            raise RuntimeError("Repair should refresh START-HERE.md from canonical workflow state after managed surface replacement")
        if "repair_follow_on_handoff_allowed" in repaired_start_here:
            raise RuntimeError("Repair should not republish legacy repair_follow_on_handoff_allowed in START-HERE.md")
        repaired_context_snapshot = (restart_repair_dest / ".opencode" / "state" / "context-snapshot.md").read_text(encoding="utf-8")
        if (
            "- state_revision: 122" not in repaired_context_snapshot
            or "synthetic-team-leader" not in repaired_context_snapshot
            or "## Repair Follow-On" not in repaired_context_snapshot
            or "- Open split children: none" not in repaired_context_snapshot
        ):
            raise RuntimeError("Repair should refresh context-snapshot.md with current revision and active lane-lease facts")
        if "- handoff_allowed:" in repaired_context_snapshot:
            raise RuntimeError("Repair should not republish legacy handoff_allowed in context-snapshot.md")
        repaired_latest_handoff = (restart_repair_dest / ".opencode" / "state" / "latest-handoff.md").read_text(encoding="utf-8")
        if (
            "- bootstrap_status: failed" not in repaired_latest_handoff
            or "- pending_process_verification: true" not in repaired_latest_handoff
            or "- repair_follow_on_outcome: managed_blocked" not in repaired_latest_handoff
            or "- handoff_status: bootstrap recovery required" not in repaired_latest_handoff
            or "- repair_follow_on_required: true" not in repaired_latest_handoff
            or "- split_child_tickets: none" not in repaired_latest_handoff
        ):
            raise RuntimeError("Repair should refresh latest-handoff.md from canonical workflow state after managed surface replacement")
        if "repair_follow_on_handoff_allowed" in repaired_latest_handoff:
            raise RuntimeError("Repair should not republish legacy repair_follow_on_handoff_allowed in latest-handoff.md")
        repaired_restart_audit = run_json([sys.executable, str(AUDIT), str(restart_repair_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        repaired_restart_codes = {finding["code"] for finding in repaired_restart_audit.get("findings", [])}
        if "WFLOW010" in repaired_restart_codes:
            raise RuntimeError("Repair should clear WFLOW010 by regenerating START-HERE.md, context-snapshot.md, and latest-handoff.md from canonical state")

        public_repair_dest = workspace / "public-repair-runner"
        shutil.copytree(full_dest, public_repair_dest)
        public_repair = subprocess.run(
            [sys.executable, str(PUBLIC_REPAIR), str(public_repair_dest), "--skip-verify"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if public_repair.returncode == 0:
            raise RuntimeError("Public managed repair runner should fail closed until required follow-on stages are marked complete")
        public_repair_payload = json.loads(public_repair.stdout)
        if public_repair_payload["execution_record"]["handoff_allowed"]:
            raise RuntimeError("Public managed repair runner must block handoff while required follow-on stages remain unexecuted")
        if public_repair_payload["execution_record"]["repair_follow_on_outcome"] != "managed_blocked":
            raise RuntimeError("Public managed repair runner should classify incomplete managed follow-on as managed_blocked")
        if not (public_repair_dest / ".opencode" / "meta" / "repair-execution.json").exists():
            raise RuntimeError("Public managed repair runner should persist a machine-readable repair execution record")

        repeat_dest = workspace / "repeat-cycle"
        shutil.copytree(full_dest, repeat_dest)
        repeat_diagnosis_root = repeat_dest / "diagnosis"
        repeat_diagnosis_dirs = sorted(path for path in repeat_diagnosis_root.iterdir() if path.is_dir())
        seed_failed_repair_cycle(repeat_dest, repeat_diagnosis_dirs[-1])
        repeated_cycle_audit = run_json([sys.executable, str(AUDIT), str(repeat_dest), "--format", "json"], ROOT)
        repeated_cycle_codes = {finding["code"] for finding in repeated_cycle_audit.get("findings", [])}
        if "CYCLE001" not in repeated_cycle_codes:
            raise RuntimeError("A repo with a prior diagnosis pack, later repair history, and repeated workflow drift should emit CYCLE001")

        repeated_diagnosis_dest = workspace / "repeated-diagnosis-churn"
        shutil.copytree(full_dest, repeated_diagnosis_dest)
        seed_repeated_diagnosis_churn(repeated_diagnosis_dest)
        repeated_diagnosis_audit = run_json([sys.executable, str(AUDIT), str(repeated_diagnosis_dest), "--format", "json"], ROOT)
        repeated_diagnosis_codes = {finding["code"] for finding in repeated_diagnosis_audit.get("findings", [])}
        if "CYCLE002" not in repeated_diagnosis_codes:
            raise RuntimeError("A repo with repeated same-day diagnosis packs and no later package-side change should emit CYCLE002")

        repeated_diagnosis_new_package_dest = workspace / "repeated-diagnosis-new-package"
        shutil.copytree(repeated_diagnosis_dest, repeated_diagnosis_new_package_dest)
        for manifest_path in (repeated_diagnosis_new_package_dest / "diagnosis").glob("*/manifest.json"):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["audit_package_commit"] = "older-package-commit"
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        repeated_diagnosis_new_package_audit = run_json([sys.executable, str(AUDIT), str(repeated_diagnosis_new_package_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        repeated_diagnosis_new_package_codes = {finding["code"] for finding in repeated_diagnosis_new_package_audit.get("findings", [])}
        if "CYCLE002" in repeated_diagnosis_new_package_codes:
            raise RuntimeError("A repo whose repeated diagnosis packs were generated under an older package commit should not emit CYCLE002 on a fresh post-package revalidation audit")

        verification_basis_regression_dest = workspace / "verification-basis-regression"
        shutil.copytree(full_dest, verification_basis_regression_dest)
        transcript_basis_log = seed_false_clean_verification_history(verification_basis_regression_dest)
        verification_basis_regression_audit = run_json(
            [sys.executable, str(AUDIT), str(verification_basis_regression_dest), "--format", "json", "--no-diagnosis-pack"],
            ROOT,
        )
        verification_basis_regression_codes = {finding["code"] for finding in verification_basis_regression_audit.get("findings", [])}
        if "CYCLE003" not in verification_basis_regression_codes:
            raise RuntimeError("A repo with a later zero-finding verification pack that dropped the earlier transcript basis should emit CYCLE003")

        verification_basis_false_positive_dest = workspace / "verification-basis-false-positive"
        shutil.copytree(full_dest, verification_basis_false_positive_dest)
        seed_false_clean_preceded_by_later_transcript_basis(verification_basis_false_positive_dest)
        verification_basis_false_positive_audit = run_json(
            [sys.executable, str(AUDIT), str(verification_basis_false_positive_dest), "--format", "json", "--no-diagnosis-pack"],
            ROOT,
        )
        verification_basis_false_positive_codes = {finding["code"] for finding in verification_basis_false_positive_audit.get("findings", [])}
        if "CYCLE003" in verification_basis_false_positive_codes:
            raise RuntimeError("A zero-finding pack that predates the later transcript-backed basis should not emit CYCLE003")
        inherited_basis_repair = subprocess.run(
            [
                sys.executable,
                str(PUBLIC_REPAIR),
                str(verification_basis_regression_dest),
                "--skip-deterministic-refresh",
                "--stage-complete",
                "ticket-pack-builder",
                "--stage-complete",
                "handoff-brief",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        inherited_basis_payload = json.loads(inherited_basis_repair.stdout)
        inherited_basis_logs = inherited_basis_payload["execution_record"]["verification_status"]["supporting_logs"]
        if any(str(transcript_basis_log) == item for item in inherited_basis_logs):
            raise RuntimeError("Public managed repair runner should not inherit transcript logs from an older diagnosis when the selected repair basis is the newer log-less pack")
        if inherited_basis_payload["execution_record"]["verification_status"]["verification_basis"] != "current_state_only":
            raise RuntimeError("Public managed repair runner should classify verification against the latest log-less diagnosis basis as current_state_only")

        explicit_basis_repair = subprocess.run(
            [
                sys.executable,
                str(PUBLIC_REPAIR),
                str(verification_basis_regression_dest),
                "--skip-deterministic-refresh",
                "--repair-basis-diagnosis",
                str(verification_basis_regression_dest / "diagnosis" / "20260327-143940"),
                "--stage-complete",
                "ticket-pack-builder",
                "--stage-complete",
                "handoff-brief",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        explicit_basis_payload = json.loads(explicit_basis_repair.stdout)
        explicit_basis_logs = explicit_basis_payload["execution_record"]["verification_status"]["supporting_logs"]
        if not any(str(transcript_basis_log) == item for item in explicit_basis_logs):
            raise RuntimeError("Public managed repair runner should inherit transcript logs from the selected repair basis diagnosis")
        if explicit_basis_payload["execution_record"]["verification_status"]["verification_basis"] != "transcript_backed":
            raise RuntimeError("Public managed repair runner should classify an explicitly transcript-backed repair basis as transcript_backed")
        if explicit_basis_payload["execution_record"]["verification_status"]["repair_basis_path"] != str(verification_basis_regression_dest / "diagnosis" / "20260327-143940"):
            raise RuntimeError("Public managed repair runner should record the selected repair basis diagnosis path")

        chronology_dest = workspace / "chronology"
        shutil.copytree(full_dest, chronology_dest)
        transcript_log = seed_workflow_overclaim(chronology_dest)
        chronology_audit = run_json(
            [sys.executable, str(AUDIT), str(chronology_dest), "--format", "json", "--supporting-log", str(transcript_log)],
            ROOT,
        )
        chronology_codes = {finding["code"] for finding in chronology_audit.get("findings", [])}
        for expected in ("WFLOW002", "SESSION001", "SESSION002", "SESSION003", "SESSION004"):
            if expected not in chronology_codes:
                raise RuntimeError(f"Audit should emit {expected} when handoff overclaims and transcript chronology proves thrash, bypass-seeking, or evidence-free PASS claims")

        recovered_dest = workspace / "recovered-verification"
        shutil.copytree(full_dest, recovered_dest)
        recovered_log = seed_recovered_verification_log(recovered_dest)
        recovered_audit = run_json(
            [sys.executable, str(AUDIT), str(recovered_dest), "--format", "json", "--supporting-log", str(recovered_log)],
            ROOT,
        )
        recovered_codes = {finding["code"] for finding in recovered_audit.get("findings", [])}
        if "SESSION004" in recovered_codes:
            raise RuntimeError("A transcript with later real recovery evidence should not emit SESSION004")

        failing_suite_dest = workspace / "failing-suite"
        shutil.copytree(full_dest, failing_suite_dest)
        seed_failing_pytest_suite(failing_suite_dest)
        failing_suite_audit = run_json([sys.executable, str(AUDIT), str(failing_suite_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        failing_suite_codes = {finding["code"] for finding in failing_suite_audit.get("findings", [])}
        if "EXEC003" not in failing_suite_codes:
            raise RuntimeError("A repo whose tests collect successfully but fail at runtime should emit EXEC003")

        missing_pytest_dest = workspace / "missing-pytest"
        shutil.copytree(full_dest, missing_pytest_dest)
        seed_missing_pytest_env(missing_pytest_dest)
        stripped_env = dict(os.environ)
        stripped_env["PATH"] = ""
        missing_pytest_audit = run_json(
            [sys.executable, str(AUDIT), str(missing_pytest_dest), "--format", "json", "--no-diagnosis-pack"],
            ROOT,
            env=stripped_env,
        )
        missing_pytest_codes = {finding["code"] for finding in missing_pytest_audit.get("findings", [])}
        if "ENV002" not in missing_pytest_codes:
            raise RuntimeError("A Python repo with tests but no usable pytest command should emit ENV002")

        hidden_pending_verification_dest = workspace / "hidden-pending-process-verification"
        shutil.copytree(full_dest, hidden_pending_verification_dest)
        seed_hidden_process_verification(hidden_pending_verification_dest)
        hidden_pending_verification_audit = run_json([sys.executable, str(AUDIT), str(hidden_pending_verification_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        hidden_pending_verification_codes = {finding["code"] for finding in hidden_pending_verification_audit.get("findings", [])}
        if "WFLOW008" not in hidden_pending_verification_codes:
            raise RuntimeError("A repo that hides or contradicts pending_process_verification should emit WFLOW008")

        truthful_pending_verification_dest = workspace / "truthful-pending-process-verification"
        shutil.copytree(full_dest, truthful_pending_verification_dest)
        make_stack_skill_non_placeholder(truthful_pending_verification_dest)
        seed_truthful_process_verification(truthful_pending_verification_dest)
        run_json([sys.executable, str(REGENERATE), str(truthful_pending_verification_dest)], ROOT)
        truthful_start_here = (truthful_pending_verification_dest / "START-HERE.md").read_text(encoding="utf-8")
        if (
            "- handoff_status: workflow verification pending" not in truthful_start_here
            or "- pending_process_verification: true" not in truthful_start_here
            or "- repair_follow_on_outcome: clean" not in truthful_start_here
            or "- repair_follow_on_required: false" not in truthful_start_here
            or "- split_child_tickets: none" not in truthful_start_here
        ):
            raise RuntimeError("Restart regeneration should truthfully expose pending process verification without inventing repair follow-on drift")
        if "repair_follow_on_handoff_allowed" in truthful_start_here:
            raise RuntimeError("Restart regeneration should not expose legacy repair_follow_on_handoff_allowed")
        truthful_pending_verification_audit = run_json([sys.executable, str(AUDIT), str(truthful_pending_verification_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        truthful_pending_verification_codes = {finding["code"] for finding in truthful_pending_verification_audit.get("findings", [])}
        if "WFLOW008" in truthful_pending_verification_codes:
            raise RuntimeError("A repo that truthfully surfaces pending_process_verification should not emit WFLOW008")
        if "WFLOW010" in truthful_pending_verification_codes:
            raise RuntimeError("A repo whose restart surfaces match canonical repair-follow-on and verification state should not emit WFLOW010")

        clearable_pending_verification_dest = workspace / "clearable-pending-process-verification"
        shutil.copytree(full_dest, clearable_pending_verification_dest)
        make_stack_skill_non_placeholder(clearable_pending_verification_dest)
        seed_process_verification_clear_deadlock(clearable_pending_verification_dest, stale_surfaces=False)
        run_json([sys.executable, str(REGENERATE), str(clearable_pending_verification_dest)], ROOT)
        clearable_start_here = (clearable_pending_verification_dest / "START-HERE.md").read_text(encoding="utf-8")
        if (
            "- pending_process_verification: true" not in clearable_start_here
            or "- done_but_not_fully_trusted: none" not in clearable_start_here
            or "clear pending_process_verification now that no historical done tickets still require process verification" not in clearable_start_here
        ):
            raise RuntimeError("Restart regeneration should expose the direct clear path when pending_process_verification remains true but the affected done-ticket set is empty")
        clearable_pending_verification_audit = run_json([sys.executable, str(AUDIT), str(clearable_pending_verification_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        clearable_pending_verification_codes = {finding["code"] for finding in clearable_pending_verification_audit.get("findings", [])}
        if "WFLOW008" in clearable_pending_verification_codes:
            raise RuntimeError("A repo that truthfully exposes a clearable pending_process_verification state should not emit WFLOW008")
        if "WFLOW010" in clearable_pending_verification_codes:
            raise RuntimeError("A repo whose restart surfaces correctly collapse done_but_not_fully_trusted to none when the affected set is empty should not emit WFLOW010")

        hidden_clearable_pending_dest = workspace / "hidden-clearable-pending-process-verification"
        shutil.copytree(full_dest, hidden_clearable_pending_dest)
        seed_process_verification_clear_deadlock(hidden_clearable_pending_dest, stale_surfaces=True)
        hidden_clearable_pending_audit = run_json([sys.executable, str(AUDIT), str(hidden_clearable_pending_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        hidden_clearable_pending_codes = {finding["code"] for finding in hidden_clearable_pending_audit.get("findings", [])}
        if "WFLOW008" not in hidden_clearable_pending_codes:
            raise RuntimeError("A repo that strands a clearable pending_process_verification flag behind stale restart surfaces or a closed-ticket lease should emit WFLOW008")

        active_priority_dest = workspace / "active-ticket-priority"
        shutil.copytree(full_dest, active_priority_dest)
        seed_open_active_ticket_with_pending_verification(active_priority_dest)
        run_json([sys.executable, str(REGENERATE), str(active_priority_dest)], ROOT)
        active_priority_start_here = (active_priority_dest / "START-HERE.md").read_text(encoding="utf-8")
        if "Keep SETUP-001 as the foreground ticket and continue its lifecycle from implementation." not in active_priority_start_here:
            raise RuntimeError("Restart regeneration should keep an open active ticket primary even when backlog process verification is pending")

        reverification_deadlock_dest = workspace / "reverification-deadlock"
        shutil.copytree(full_dest, reverification_deadlock_dest)
        seed_reverification_deadlock(reverification_deadlock_dest)
        reverification_deadlock_audit = run_json([sys.executable, str(AUDIT), str(reverification_deadlock_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        reverification_deadlock_codes = {finding["code"] for finding in reverification_deadlock_audit.get("findings", [])}
        if "WFLOW009" not in reverification_deadlock_codes:
            raise RuntimeError("A repo whose reverification contract still requires closed tickets to hold a normal write lease should emit WFLOW009")

        closed_follow_up_deadlock_dest = workspace / "closed-follow-up-deadlock"
        shutil.copytree(full_dest, closed_follow_up_deadlock_dest)
        seed_closed_follow_up_deadlock(closed_follow_up_deadlock_dest)
        closed_follow_up_deadlock_audit = run_json([sys.executable, str(AUDIT), str(closed_follow_up_deadlock_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        closed_follow_up_deadlock_codes = {finding["code"] for finding in closed_follow_up_deadlock_audit.get("findings", [])}
        if "WFLOW018" not in closed_follow_up_deadlock_codes:
            raise RuntimeError("A repo whose completed-ticket follow-up routing still requires normal write leases should emit WFLOW018")

        historical_reconciliation_deadlock_dest = workspace / "historical-reconciliation-deadlock"
        shutil.copytree(full_dest, historical_reconciliation_deadlock_dest)
        seed_historical_reconciliation_deadlock(historical_reconciliation_deadlock_dest)
        historical_reconciliation_deadlock_audit = run_json([sys.executable, str(AUDIT), str(historical_reconciliation_deadlock_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        historical_reconciliation_deadlock_codes = {finding["code"] for finding in historical_reconciliation_deadlock_audit.get("findings", [])}
        if "WFLOW024" not in historical_reconciliation_deadlock_codes:
            raise RuntimeError("A repo with no legal reconciliation path for a superseded invalidated historical ticket should emit WFLOW024")
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
            Path(historical_reconciliation_revalidation["diagnosis_pack"]["path"]).joinpath("manifest.json").read_text(encoding="utf-8")
        )
        if historical_reconciliation_manifest.get("package_work_required_first"):
            raise RuntimeError("A stale repo with WFLOW024 should route to subject-repo repair when the installed Scafforge template already contains the reconciliation fix")
        if historical_reconciliation_manifest.get("recommended_next_step") != "subject_repo_repair":
            raise RuntimeError("A post-package revalidation pack with only stale managed-surface WFLOW024 drift should recommend subject_repo_repair")
        routed_recommendations = {
            item.get("source_finding_code"): item.get("route")
            for item in historical_reconciliation_manifest.get("ticket_recommendations", [])
            if isinstance(item, dict)
        }
        if routed_recommendations.get("WFLOW024") != "scafforge-repair":
            raise RuntimeError("WFLOW024 should route to scafforge-repair once the installed package template already contains the historical reconciliation fix")

        contradictory_graph_dest = workspace / "contradictory-ticket-graph"
        shutil.copytree(full_dest, contradictory_graph_dest)
        seed_contradictory_follow_up_graph(contradictory_graph_dest)
        contradictory_graph_audit = run_json([sys.executable, str(AUDIT), str(contradictory_graph_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        contradictory_graph_codes = {finding["code"] for finding in contradictory_graph_audit.get("findings", [])}
        if "WFLOW019" not in contradictory_graph_codes:
            raise RuntimeError("A repo whose source/follow-up lineage contradicts its dependency graph should emit WFLOW019")

        split_scope_drift_dest = workspace / "split-scope-drift"
        shutil.copytree(full_dest, split_scope_drift_dest)
        seed_open_parent_split_drift(split_scope_drift_dest)
        split_scope_drift_audit = run_json([sys.executable, str(AUDIT), str(split_scope_drift_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        split_scope_drift_codes = {finding["code"] for finding in split_scope_drift_audit.get("findings", [])}
        if "WFLOW020" not in split_scope_drift_codes:
            raise RuntimeError("A repo whose open-parent child decomposition uses a non-canonical source mode should emit WFLOW020")
        blocked_split_parent_dest = workspace / "blocked-split-parent"
        shutil.copytree(full_dest, blocked_split_parent_dest)
        seed_blocked_split_parent(blocked_split_parent_dest)
        blocked_split_parent_audit = run_json([sys.executable, str(AUDIT), str(blocked_split_parent_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        blocked_split_parent_codes = {finding["code"] for finding in blocked_split_parent_audit.get("findings", [])}
        if "WFLOW020" not in blocked_split_parent_codes:
            raise RuntimeError("A repo whose split parent is still marked blocked should emit WFLOW020")

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
        redirected_output_codes = {finding["code"] for finding in redirected_output_audit.get("findings", [])}
        if "ENV004" not in redirected_output_codes:
            raise RuntimeError("An unwritable diagnosis output path should emit ENV004 and fall back to a writable location")
        diagnosis_pack_path = redirected_output_audit.get("diagnosis_pack", {}).get("path", "")
        if not diagnosis_pack_path.startswith("/tmp/scafforge-diagnosis/"):
            raise RuntimeError("Audit should redirect unwritable diagnosis-pack output to /tmp/scafforge-diagnosis")

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
        repair_diagnosis_pack_path = repair_redirected_payload.get("diagnosis_pack", {}).get("path", "")
        if repair_diagnosis_pack_path != str(repair_redirected_output_dir):
            raise RuntimeError("Public managed repair runner should honor --diagnosis-output-dir for the post-repair diagnosis pack")

        package_work_first_repair_dest = workspace / "package-work-first-repair"
        shutil.copytree(full_dest, package_work_first_repair_dest)
        package_work_diagnosis_root = package_work_first_repair_dest / "diagnosis"
        shutil.rmtree(package_work_diagnosis_root, ignore_errors=True)
        package_work_diagnosis_root.mkdir(parents=True, exist_ok=True)
        write_diagnosis_manifest(
            package_work_diagnosis_root / "20260328-120000",
            generated_at="2026-03-28T12:00:00Z",
            finding_count=1,
            recommendations=[{"source_finding_code": "WFLOW024", "route": "manual-prerequisite", "title": "historical reconciliation deadlock"}],
        )
        package_work_manifest_path = package_work_diagnosis_root / "20260328-120000" / "manifest.json"
        package_work_manifest = json.loads(package_work_manifest_path.read_text(encoding="utf-8"))
        package_work_manifest["package_work_required_first"] = True
        package_work_manifest["recommended_next_step"] = "scafforge_package_work"
        package_work_manifest_path.write_text(json.dumps(package_work_manifest, indent=2) + "\n", encoding="utf-8")
        package_work_first_repair = subprocess.run(
            [sys.executable, str(PUBLIC_REPAIR), str(package_work_first_repair_dest), "--skip-deterministic-refresh"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if package_work_first_repair.returncode == 0:
            raise RuntimeError("Public managed repair runner should refuse a repair basis that still requires package work first")
        if "package work first" not in package_work_first_repair.stderr and "package work first" not in package_work_first_repair.stdout:
            raise RuntimeError("Public managed repair runner should explain that package work must be cleared before subject-repo repair")

        python_dest = workspace / "python-uv"
        shutil.copytree(full_dest, python_dest)
        seed_uv_python_fixture(python_dest)
        python_audit = run_json([sys.executable, str(AUDIT), str(python_dest), "--format", "json"], ROOT)
        python_codes = {finding["code"] for finding in python_audit.get("findings", [])}
        if "BOOT001" in python_codes:
            raise RuntimeError("A uv-shaped repo with the current bootstrap template should not emit BOOT001")
        if "BOOT002" in python_codes:
            raise RuntimeError("A uv-shaped repo with the current bootstrap template should not emit BOOT002")

        legacy_smoke_dest = workspace / "legacy-smoke"
        shutil.copytree(python_dest, legacy_smoke_dest)
        seed_legacy_smoke_test_tool(legacy_smoke_dest)
        legacy_smoke_audit = run_json([sys.executable, str(AUDIT), str(legacy_smoke_dest), "--format", "json"], ROOT)
        legacy_smoke_codes = {finding["code"] for finding in legacy_smoke_audit.get("findings", [])}
        if "WFLOW001" not in legacy_smoke_codes:
            raise RuntimeError("A uv-shaped repo with a legacy system-python smoke_test tool should emit WFLOW001")

        legacy_smoke_override_dest = workspace / "legacy-smoke-override"
        shutil.copytree(full_dest, legacy_smoke_override_dest)
        seed_legacy_smoke_override_tool(legacy_smoke_override_dest)
        legacy_smoke_override_audit = run_json([sys.executable, str(AUDIT), str(legacy_smoke_override_dest), "--format", "json"], ROOT)
        legacy_smoke_override_codes = {finding["code"] for finding in legacy_smoke_override_audit.get("findings", [])}
        if "WFLOW016" not in legacy_smoke_override_codes:
            raise RuntimeError("A repo whose smoke_test tool passes command_override directly into argv should emit WFLOW016")

        legacy_review_dest = workspace / "legacy-review"
        shutil.copytree(full_dest, legacy_review_dest)
        seed_legacy_review_contract(legacy_review_dest)
        legacy_review_audit = run_json([sys.executable, str(AUDIT), str(legacy_review_dest), "--format", "json"], ROOT)
        legacy_review_codes = {finding["code"] for finding in legacy_review_audit.get("findings", [])}
        if "WFLOW003" not in legacy_review_codes:
            raise RuntimeError("A repo with plan-review docs but no explicit plan_review workflow contract should emit WFLOW003")

        legacy_transition_dest = workspace / "legacy-transition"
        shutil.copytree(full_dest, legacy_transition_dest)
        seed_legacy_stage_transition_contract(legacy_transition_dest)
        legacy_transition_audit = run_json([sys.executable, str(AUDIT), str(legacy_transition_dest), "--format", "json"], ROOT)
        legacy_transition_codes = {finding["code"] for finding in legacy_transition_audit.get("findings", [])}
        if "WFLOW004" not in legacy_transition_codes:
            raise RuntimeError("A repo with status-gated implementation or unvalidated lifecycle stages should emit WFLOW004")

        smoke_bypass_dest = workspace / "smoke-bypass"
        shutil.copytree(full_dest, smoke_bypass_dest)
        seed_smoke_artifact_bypass(smoke_bypass_dest)
        smoke_bypass_audit = run_json([sys.executable, str(AUDIT), str(smoke_bypass_dest), "--format", "json"], ROOT)
        smoke_bypass_codes = {finding["code"] for finding in smoke_bypass_audit.get("findings", [])}
        if "WFLOW005" not in smoke_bypass_codes:
            raise RuntimeError("A repo that allows smoke-test proof through generic artifact tools should emit WFLOW005")

        handoff_conflict_dest = workspace / "handoff-conflict"
        shutil.copytree(full_dest, handoff_conflict_dest)
        seed_handoff_ownership_conflict(handoff_conflict_dest)
        handoff_conflict_audit = run_json([sys.executable, str(AUDIT), str(handoff_conflict_dest), "--format", "json"], ROOT)
        handoff_conflict_codes = {finding["code"] for finding in handoff_conflict_audit.get("findings", [])}
        if "WFLOW007" not in handoff_conflict_codes:
            raise RuntimeError("A repo whose docs-handoff path conflicts with plugin enforcement should emit WFLOW007")

        team_leader_dest = workspace / "team-leader-drift"
        shutil.copytree(full_dest, team_leader_dest)
        seed_team_leader_workflow_drift(team_leader_dest)
        team_leader_audit = run_json([sys.executable, str(AUDIT), str(team_leader_dest), "--format", "json"], ROOT)
        team_leader_codes = {finding["code"] for finding in team_leader_audit.get("findings", [])}
        if "WFLOW006" not in team_leader_codes:
            raise RuntimeError("A repo whose team leader prompt omits transition guidance, stop rules, or command boundaries should emit WFLOW006")

        helper_tool_dest = workspace / "helper-tool-exposure"
        shutil.copytree(full_dest, helper_tool_dest)
        seed_helper_tool_exposure(helper_tool_dest)
        helper_tool_log = seed_helper_tool_failure_log(helper_tool_dest)
        helper_tool_audit = run_json(
            [sys.executable, str(AUDIT), str(helper_tool_dest), "--format", "json", "--supporting-log", str(helper_tool_log)],
            ROOT,
        )
        helper_tool_codes = {finding["code"] for finding in helper_tool_audit.get("findings", [])}
        if "WFLOW015" not in helper_tool_codes:
            raise RuntimeError("A repo whose runtime exposes helper-only workflow internals or transcript-level missing-execute failures should emit WFLOW015")

        smoke_override_log_dest = workspace / "smoke-override-log"
        shutil.copytree(full_dest, smoke_override_log_dest)
        smoke_override_log = seed_smoke_override_failure_log(smoke_override_log_dest)
        smoke_override_audit = run_json(
            [sys.executable, str(AUDIT), str(smoke_override_log_dest), "--format", "json", "--supporting-log", str(smoke_override_log)],
            ROOT,
        )
        smoke_override_codes = {finding["code"] for finding in smoke_override_audit.get("findings", [])}
        if "WFLOW016" not in smoke_override_codes:
            raise RuntimeError("A transcript where smoke_test treats KEY=VALUE as the executable should emit WFLOW016")

        legacy_smoke_acceptance_dest = workspace / "legacy-smoke-acceptance"
        shutil.copytree(full_dest, legacy_smoke_acceptance_dest)
        seed_legacy_smoke_acceptance_tool(legacy_smoke_acceptance_dest)
        legacy_smoke_acceptance_audit = run_json([sys.executable, str(AUDIT), str(legacy_smoke_acceptance_dest), "--format", "json"], ROOT)
        legacy_smoke_acceptance_codes = {finding["code"] for finding in legacy_smoke_acceptance_audit.get("findings", [])}
        if "WFLOW017" not in legacy_smoke_acceptance_codes:
            raise RuntimeError("A repo whose smoke_test tool ignores ticket acceptance commands should emit WFLOW017")

        smoke_acceptance_log_dest = workspace / "smoke-acceptance-log"
        shutil.copytree(full_dest, smoke_acceptance_log_dest)
        smoke_acceptance_log = seed_smoke_acceptance_scope_log(smoke_acceptance_log_dest)
        smoke_acceptance_audit = run_json(
            [sys.executable, str(AUDIT), str(smoke_acceptance_log_dest), "--format", "json", "--supporting-log", str(smoke_acceptance_log)],
            ROOT,
        )
        smoke_acceptance_codes = {finding["code"] for finding in smoke_acceptance_audit.get("findings", [])}
        if "WFLOW017" not in smoke_acceptance_codes:
            raise RuntimeError("A transcript where smoke_test ignores a ticket-defined smoke command should emit WFLOW017")

        handoff_lease_dest = workspace / "handoff-lease-contradiction"
        shutil.copytree(full_dest, handoff_lease_dest)
        handoff_lease_log = seed_handoff_lease_contradiction_log(handoff_lease_dest)
        handoff_lease_audit = run_json(
            [sys.executable, str(AUDIT), str(handoff_lease_dest), "--format", "json", "--supporting-log", str(handoff_lease_log)],
            ROOT,
        )
        handoff_lease_codes = {finding["code"] for finding in handoff_lease_audit.get("findings", [])}
        if "WFLOW022" not in handoff_lease_codes:
            raise RuntimeError("A transcript where handoff_publish still needs a closed ticket lease should emit WFLOW022")

        acceptance_tension_dest = workspace / "acceptance-scope-tension"
        shutil.copytree(full_dest, acceptance_tension_dest)
        acceptance_tension_log = seed_acceptance_scope_tension_log(acceptance_tension_dest)
        acceptance_tension_audit = run_json(
            [sys.executable, str(AUDIT), str(acceptance_tension_dest), "--format", "json", "--supporting-log", str(acceptance_tension_log)],
            ROOT,
        )
        acceptance_tension_codes = {finding["code"] for finding in acceptance_tension_audit.get("findings", [])}
        if "WFLOW023" not in acceptance_tension_codes:
            raise RuntimeError("A transcript where a ticket's literal acceptance command depends on later-ticket scope should emit WFLOW023")

        operator_trap_dest = workspace / "operator-trap"
        shutil.copytree(full_dest, operator_trap_dest)
        operator_trap_log = seed_operator_trap_log(operator_trap_dest)
        operator_trap_audit = run_json(
            [sys.executable, str(AUDIT), str(operator_trap_dest), "--format", "json", "--supporting-log", str(operator_trap_log)],
            ROOT,
        )
        operator_trap_codes = {finding["code"] for finding in operator_trap_audit.get("findings", [])}
        if "SESSION006" not in operator_trap_codes:
            raise RuntimeError("A transcript with multiple contradictory blockers and workaround pressure should emit SESSION006")

        coordinator_artifact_dest = workspace / "coordinator-artifacts"
        shutil.copytree(full_dest, coordinator_artifact_dest)
        coordinator_log = seed_coordinator_artifact_log(coordinator_artifact_dest)
        coordinator_audit = run_json(
            [sys.executable, str(AUDIT), str(coordinator_artifact_dest), "--format", "json", "--supporting-log", str(coordinator_log)],
            ROOT,
        )
        coordinator_codes = {finding["code"] for finding in coordinator_audit.get("findings", [])}
        if "SESSION005" not in coordinator_codes:
            raise RuntimeError("A transcript where the coordinator writes specialist artifacts should emit SESSION005")

        thin_skill_dest = workspace / "thin-ticket-skill"
        shutil.copytree(full_dest, thin_skill_dest)
        seed_thin_ticket_execution(thin_skill_dest)
        thin_skill_audit = run_json([sys.executable, str(AUDIT), str(thin_skill_dest), "--format", "json"], ROOT)
        thin_skill_codes = {finding["code"] for finding in thin_skill_audit.get("findings", [])}
        if "SKILL002" not in thin_skill_codes:
            raise RuntimeError("A repo with a thin ticket-execution skill should emit SKILL002")

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

        mismatch_dest = workspace / "bootstrap-command-mismatch"
        shutil.copytree(python_dest, mismatch_dest)
        seed_bootstrap_command_layout_mismatch(mismatch_dest)
        mismatch_audit = run_json([sys.executable, str(AUDIT), str(mismatch_dest), "--format", "json", "--emit-diagnosis-pack"], ROOT)
        mismatch_codes = {finding["code"] for finding in mismatch_audit.get("findings", [])}
        if "BOOT002" not in mismatch_codes:
            raise RuntimeError("A bootstrap artifact whose uv sync command omits required dev flags should emit BOOT002")
        if "ENV002" in mismatch_codes:
            raise RuntimeError("A managed bootstrap command/layout mismatch should not be downgraded to ENV002")
        mismatch_recommendations = (
            mismatch_audit.get("diagnosis_pack", {})
            .get("manifest", {})
            .get("ticket_recommendations", [])
        )
        if not any(item.get("source_finding_code") == "BOOT002" and item.get("route") == "scafforge-repair" for item in mismatch_recommendations):
            raise RuntimeError("BOOT002 should route to scafforge-repair in the diagnosis pack")

        model_dest = workspace / "model-drift"
        shutil.copytree(full_dest, model_dest)
        seed_legacy_model_drift(model_dest)
        model_audit = run_json([sys.executable, str(AUDIT), str(model_dest), "--format", "json"], ROOT)
        model_findings = {finding["code"]: finding for finding in model_audit.get("findings", [])}
        model_codes = set(model_findings)
        if "MODEL001" not in model_codes:
            raise RuntimeError("A repo with deprecated MiniMax surfaces and no model-operating-profile should emit MODEL001")
        if model_findings["MODEL001"].get("severity") != "error":
            raise RuntimeError("Deprecated package-managed MiniMax drift should emit MODEL001 as an error, not a warning")

        repair_dest = workspace / "repair"
        shutil.copytree(full_dest, repair_dest)
        shutil.rmtree(repair_dest / "diagnosis", ignore_errors=True)
        (repair_dest / "docs" / "process" / "workflow.md").write_text("# drifted workflow\n", encoding="utf-8")
        seed_legacy_bootstrap_tool(repair_dest)
        repair_payload = run_json([sys.executable, str(REPAIR), str(repair_dest)], ROOT)
        if repair_payload.get("verification", {}).get("clean") is True:
            raise RuntimeError("Deterministic repair verification should not report clean while pending process verification or placeholder local-skill follow-up remains")
        if repair_payload.get("verification", {}).get("pending_process_verification") is not True:
            raise RuntimeError("Repair verification should report pending_process_verification when the workflow state reopens backlog trust checks")

        repaired_workflow = json.loads((repair_dest / ".opencode" / "state" / "workflow-state.json").read_text(encoding="utf-8"))
        if repaired_workflow.get("process_version") != 7:
            raise RuntimeError("Repair should update workflow-state to process version 7")
        if repaired_workflow.get("pending_process_verification") is not True:
            raise RuntimeError("Repair should reopen post-migration verification")
        if not repaired_workflow.get("process_last_changed_at"):
            raise RuntimeError("Repair should record process_last_changed_at")
        for key in ("bootstrap", "lane_leases", "state_revision"):
            if key not in repaired_workflow:
                raise RuntimeError(f"Repair should preserve workflow key `{key}`")

        repaired_provenance = json.loads((repair_dest / ".opencode" / "meta" / "bootstrap-provenance.json").read_text(encoding="utf-8"))
        if not repaired_provenance.get("repair_history"):
            raise RuntimeError("Repair should append repair_history")
        managed_surfaces = repaired_provenance.get("managed_surfaces", {})
        replace_on_retrofit = managed_surfaces.get("replace_on_retrofit", [])
        project_specific_follow_up = managed_surfaces.get("project_specific_follow_up", [])
        if "opencode.jsonc" not in replace_on_retrofit:
            raise RuntimeError("Repair provenance should list opencode.jsonc as a deterministic managed surface")
        if ".opencode/skills" not in project_specific_follow_up:
            raise RuntimeError("Repair provenance should mark .opencode/skills as a project-specific follow-up surface")

        repaired_workflow_doc = (repair_dest / "docs" / "process" / "workflow.md").read_text(encoding="utf-8")
        if "# Workflow" not in repaired_workflow_doc:
            raise RuntimeError("Repair should restore docs/process/workflow.md from the scaffold")
        repaired_bootstrap_tool = (repair_dest / ".opencode" / "tools" / "environment_bootstrap.ts").read_text(encoding="utf-8")
        for expected in ("[project.optional-dependencies]", "[dependency-groups]", "[tool.uv.dev-dependencies]", "[tool.pytest.ini_options]"):
            if expected not in repaired_bootstrap_tool:
                raise RuntimeError("Repair should restore the broadened environment_bootstrap surface for alternate dev layouts and pyproject-only pytest detection")
        repaired_handoff = (repair_dest / ".opencode" / "tools" / "handoff_publish.ts").read_text(encoding="utf-8")
        if "validateHandoffNextAction" not in repaired_handoff or repaired_handoff.find("const handoffBlocker = await validateHandoffNextAction") >= repaired_handoff.find("await refreshRestartSurfaces"):
            raise RuntimeError("Repair should restore truthful handoff gating before restart-surface publication")

        source_follow_up_repair_dest = workspace / "source-follow-up-repair"
        shutil.copytree(full_dest, source_follow_up_repair_dest)
        make_stack_skill_non_placeholder(source_follow_up_repair_dest)
        seed_failing_pytest_suite(source_follow_up_repair_dest)
        if host_has_uv:
            source_follow_up_repair = run_json(
                [
                    sys.executable,
                    str(PUBLIC_REPAIR),
                    str(source_follow_up_repair_dest),
                    "--skip-deterministic-refresh",
                    "--stage-complete",
                    "ticket-pack-builder",
                    "--stage-complete",
                    "handoff-brief",
                ],
                ROOT,
            )
            if source_follow_up_repair["execution_record"]["blocking_reasons"]:
                raise RuntimeError("Source-layer EXEC follow-up alone should not keep managed repair follow-on blocked once the required follow-on stages are complete")
            if source_follow_up_repair["execution_record"]["verification_status"]["source_follow_up_codes"] != ["EXEC003"]:
                raise RuntimeError("Public managed repair runner should classify EXEC findings as source follow-up instead of managed repair blockers")
            if source_follow_up_repair["execution_record"]["verification_status"]["current_state_clean"]:
                raise RuntimeError("Public managed repair runner should not call EXEC-only residual work current_state_clean")
            if not source_follow_up_repair["execution_record"]["verification_status"]["causal_regression_verified"]:
                raise RuntimeError("Public managed repair runner should still mark managed repair verification as satisfied when only source follow-up remains")
            if source_follow_up_repair["execution_record"]["repair_follow_on_outcome"] != "source_follow_up":
                raise RuntimeError("Public managed repair runner should classify EXEC-only residual work as source_follow_up")
            if not source_follow_up_repair["execution_record"]["handoff_allowed"]:
                raise RuntimeError("Public managed repair runner should allow handoff once only source follow-up remains and the required follow-on stages are complete")
            source_follow_up_workflow = json.loads((source_follow_up_repair_dest / ".opencode" / "state" / "workflow-state.json").read_text(encoding="utf-8"))
            if source_follow_up_workflow["repair_follow_on"]["handoff_allowed"] is not True:
                raise RuntimeError("Managed repair should write a cleared repair_follow_on state when only source-layer follow-up remains")
            if source_follow_up_workflow["repair_follow_on"]["outcome"] != "source_follow_up":
                raise RuntimeError("Managed repair should record source_follow_up when only source-layer remediation remains")
            if source_follow_up_workflow["repair_follow_on"]["current_state_clean"] is not False:
                raise RuntimeError("Managed repair should not record current_state_clean when source-layer remediation remains")
        else:
            print("Skipping uv-dependent source-follow-up public repair assertions because `uv` is not available on this host.")

        print("Scafforge smoke test passed.")
        return 0
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
