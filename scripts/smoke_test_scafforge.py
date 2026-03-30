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
PIVOT = ROOT / "skills" / "scafforge-pivot" / "scripts" / "plan_pivot.py"
RECORD_REPAIR_STAGE = ROOT / "skills" / "scafforge-repair" / "scripts" / "record_repair_stage_completion.py"
BOOTSTRAP_INPUT_FILES = (
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lock",
    "bun.lockb",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "uv.lock",
    "Cargo.toml",
    "Cargo.lock",
    "go.mod",
    "go.sum",
    "Makefile",
    "pytest.ini",
    "setup.py",
    "setup.cfg",
)


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


def write_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | 0o111)


def compute_bootstrap_fingerprint(dest: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    for relative in sorted(path for path in BOOTSTRAP_INPUT_FILES if (dest / path).is_file()):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\x00")
        digest.update((dest / relative).read_bytes())
        digest.update(b"\x00")
    return digest.hexdigest()


def prepare_generated_tool_runtime(dest: Path) -> None:
    plugin_dir = dest / "node_modules" / "@opencode-ai" / "plugin"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "package.json").write_text('{"name":"@opencode-ai/plugin","type":"module"}\n', encoding="utf-8")
    (plugin_dir / "index.js").write_text(
        "\n".join(
            [
                "function chain() {",
                "  return {",
                "    describe() { return this },",
                "    optional() { return this },",
                "    int() { return this },",
                "  }",
                "}",
                "const schema = {",
                "  string: () => chain(),",
                "  boolean: () => chain(),",
                "  enum: () => chain(),",
                "  array: () => chain(),",
                "  number: () => chain(),",
                "}",
                "export function tool(definition) {",
                "  return definition",
                "}",
                "tool.schema = schema",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    for path in list((dest / ".opencode" / "tools").glob("*.ts")) + list((dest / ".opencode" / "plugins").glob("*.ts")):
        text = path.read_text(encoding="utf-8")
        rewritten = text.replace('from "../lib/workflow"', 'from "../lib/workflow.ts"')
        if rewritten != text:
            path.write_text(rewritten, encoding="utf-8")


def run_generated_tool(dest: Path, relative_tool_path: str, args: dict[str, object]) -> dict[str, object]:
    prepare_generated_tool_runtime(dest)
    runner = dest / ".opencode" / "state" / "tool-runner.mjs"
    runner.parent.mkdir(parents=True, exist_ok=True)
    runner.write_text(
        "\n".join(
            [
                'import { pathToFileURL } from "node:url"',
                "const toolPath = process.env.SCAFFORGE_TOOL_PATH",
                "if (!toolPath) throw new Error('Missing SCAFFORGE_TOOL_PATH')",
                "const mod = await import(pathToFileURL(toolPath).href)",
                "const rawArgs = process.env.SCAFFORGE_TOOL_ARGS || '{}'",
                "const payload = await mod.default.execute(JSON.parse(rawArgs))",
                "console.log(payload)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["SCAFFORGE_TOOL_PATH"] = str((dest / relative_tool_path).resolve())
    env["SCAFFORGE_TOOL_ARGS"] = json.dumps(args)
    return run_json(
        ["node", "--experimental-strip-types", str(runner)],
        dest,
        env=env,
    )


def run_generated_tool_error(dest: Path, relative_tool_path: str, args: dict[str, object]) -> str:
    prepare_generated_tool_runtime(dest)
    runner = dest / ".opencode" / "state" / "tool-runner.mjs"
    runner.parent.mkdir(parents=True, exist_ok=True)
    runner.write_text(
        "\n".join(
            [
                'import { pathToFileURL } from "node:url"',
                "const toolPath = process.env.SCAFFORGE_TOOL_PATH",
                "if (!toolPath) throw new Error('Missing SCAFFORGE_TOOL_PATH')",
                "const mod = await import(pathToFileURL(toolPath).href)",
                "const rawArgs = process.env.SCAFFORGE_TOOL_ARGS || '{}'",
                "const payload = await mod.default.execute(JSON.parse(rawArgs))",
                "console.log(payload)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["SCAFFORGE_TOOL_PATH"] = str((dest / relative_tool_path).resolve())
    env["SCAFFORGE_TOOL_ARGS"] = json.dumps(args)
    result = subprocess.run(
        ["node", "--experimental-strip-types", str(runner)],
        cwd=dest,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode == 0:
        raise RuntimeError(f"Command unexpectedly succeeded: {relative_tool_path}")
    return f"{result.stdout}\n{result.stderr}".strip()


def run_generated_plugin_before(dest: Path, relative_plugin_path: str, tool_name: str, args: dict[str, object]) -> None:
    prepare_generated_tool_runtime(dest)
    runner = dest / ".opencode" / "state" / "plugin-runner.mjs"
    runner.parent.mkdir(parents=True, exist_ok=True)
    runner.write_text(
        "\n".join(
            [
                'import { pathToFileURL } from "node:url"',
                "const pluginPath = process.env.SCAFFORGE_PLUGIN_PATH",
                "if (!pluginPath) throw new Error('Missing SCAFFORGE_PLUGIN_PATH')",
                "const mod = await import(pathToFileURL(pluginPath).href)",
                "const factory = mod.StageGateEnforcer",
                "if (typeof factory !== 'function') throw new Error('Missing StageGateEnforcer export')",
                "const hooks = await factory()",
                'const hook = hooks["tool.execute.before"]',
                "if (typeof hook !== 'function') throw new Error('Missing tool.execute.before hook')",
                "const toolName = process.env.SCAFFORGE_PLUGIN_TOOL",
                "const rawArgs = process.env.SCAFFORGE_PLUGIN_ARGS || '{}'",
                'await hook({ tool: toolName }, { args: JSON.parse(rawArgs) })',
                'console.log(JSON.stringify({ ok: true }))',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["SCAFFORGE_PLUGIN_PATH"] = str((dest / relative_plugin_path).resolve())
    env["SCAFFORGE_PLUGIN_TOOL"] = tool_name
    env["SCAFFORGE_PLUGIN_ARGS"] = json.dumps(args)
    run(["node", "--experimental-strip-types", str(runner)], dest, env=env)


def run_generated_plugin_before_error(dest: Path, relative_plugin_path: str, tool_name: str, args: dict[str, object]) -> str:
    prepare_generated_tool_runtime(dest)
    runner = dest / ".opencode" / "state" / "plugin-runner.mjs"
    runner.parent.mkdir(parents=True, exist_ok=True)
    runner.write_text(
        "\n".join(
            [
                'import { pathToFileURL } from "node:url"',
                "const pluginPath = process.env.SCAFFORGE_PLUGIN_PATH",
                "if (!pluginPath) throw new Error('Missing SCAFFORGE_PLUGIN_PATH')",
                "const mod = await import(pathToFileURL(pluginPath).href)",
                "const factory = mod.StageGateEnforcer",
                "if (typeof factory !== 'function') throw new Error('Missing StageGateEnforcer export')",
                "const hooks = await factory()",
                'const hook = hooks["tool.execute.before"]',
                "if (typeof hook !== 'function') throw new Error('Missing tool.execute.before hook')",
                "const toolName = process.env.SCAFFORGE_PLUGIN_TOOL",
                "const rawArgs = process.env.SCAFFORGE_PLUGIN_ARGS || '{}'",
                'await hook({ tool: toolName }, { args: JSON.parse(rawArgs) })',
                'console.log(JSON.stringify({ ok: true }))',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["SCAFFORGE_PLUGIN_PATH"] = str((dest / relative_plugin_path).resolve())
    env["SCAFFORGE_PLUGIN_TOOL"] = tool_name
    env["SCAFFORGE_PLUGIN_ARGS"] = json.dumps(args)
    result = subprocess.run(
        ["node", "--experimental-strip-types", str(runner)],
        cwd=dest,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode == 0:
        raise RuntimeError(f"Plugin hook unexpectedly succeeded: {relative_plugin_path} {tool_name}")
    return f"{result.stdout}\n{result.stderr}".strip()


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


def seed_ready_bootstrap(dest: Path) -> None:
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
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
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")


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


def seed_closed_ticket_with_blocked_dependent(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    active_ticket_id = manifest["active_ticket"]
    active_ticket = next(ticket for ticket in manifest["tickets"] if ticket["id"] == active_ticket_id)
    active_ticket["stage"] = "closeout"
    active_ticket["status"] = "done"
    active_ticket["resolution_state"] = "done"
    active_ticket["verification_state"] = "reverified"
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
                "acceptance": ["Becomes the foreground lane after the source ticket closes."],
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
        "environment_fingerprint": "synthetic-ready-bootstrap",
        "proof_artifact": ".opencode/state/bootstrap/synthetic-ready-bootstrap.md",
    }
    ticket_state = workflow.get("ticket_state")
    if isinstance(ticket_state, dict):
        active_ticket_state = ticket_state.get(active_ticket_id)
        if isinstance(active_ticket_state, dict):
            active_ticket_state["needs_reverification"] = False
    proof_path = dest / ".opencode" / "state" / "bootstrap" / "synthetic-ready-bootstrap.md"
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text("# Ready Bootstrap\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")


def seed_closed_ticket_needing_explicit_reverification(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    active_ticket_id = manifest["active_ticket"]
    active_ticket = next(ticket for ticket in manifest["tickets"] if ticket["id"] == active_ticket_id)
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
        "environment_fingerprint": "synthetic-ready-bootstrap",
        "proof_artifact": ".opencode/state/bootstrap/synthetic-ready-bootstrap.md",
    }
    ticket_state = workflow.get("ticket_state")
    if isinstance(ticket_state, dict):
        active_ticket_state = ticket_state.get(active_ticket_id)
        if isinstance(active_ticket_state, dict):
            active_ticket_state["needs_reverification"] = True
    proof_path = dest / ".opencode" / "state" / "bootstrap" / "synthetic-ready-bootstrap.md"
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
    active_ticket = next(ticket for ticket in manifest["tickets"] if ticket["id"] == active_ticket_id)
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
        "environment_fingerprint": "synthetic-ready-bootstrap",
        "proof_artifact": ".opencode/state/bootstrap/synthetic-ready-bootstrap.md",
    }
    ticket_state = workflow.get("ticket_state")
    if isinstance(ticket_state, dict):
        active_ticket_state = ticket_state.get(active_ticket_id)
        if isinstance(active_ticket_state, dict):
            active_ticket_state["needs_reverification"] = False
    proof_path = dest / ".opencode" / "state" / "bootstrap" / "synthetic-ready-bootstrap.md"
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
    host_has_npm = shutil.which("npm") is not None
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
        for expected in ("host_surface_classification", "failure_classification", "blocked_by_permissions", "permission_restriction"):
            if expected not in generated_bootstrap:
                raise RuntimeError("Generated environment_bootstrap.ts should classify missing-tool and permission-restriction host failures explicitly")
        generated_smoke_test = (full_dest / ".opencode" / "tools" / "smoke_test.ts").read_text(encoding="utf-8")
        if "findExistingRepoVenvExecutable" not in generated_smoke_test:
            raise RuntimeError("Generated smoke_test.ts should support repo-local .venv Python execution across platform-specific virtualenv layouts")
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
        for expected in ("host_surface_classification", "failure_classification", "blocked_by_permissions", "permission_restriction"):
            if expected not in generated_smoke_test:
                raise RuntimeError("Generated smoke_test.ts should classify missing-tool and permission-restriction host failures explicitly")
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
        if "export function blockedDependentTickets" not in generated_workflow:
            raise RuntimeError("Generated workflow.ts should expose blocked dependent routing as a reusable canonical helper")
        if "export function dependentContinuationAction" not in generated_workflow:
            raise RuntimeError("Generated workflow.ts should expose one canonical dependent-continuation action helper for restart and lookup surfaces")
        if "export function ticketNeedsHistoricalReconciliation" not in generated_workflow:
            raise RuntimeError("Generated workflow.ts should expose explicit historical-reconciliation state for restart and lookup surfaces")
        if "export function ticketNeedsTrustRestoration" not in generated_workflow:
            raise RuntimeError("Generated workflow.ts should expose explicit closed-ticket trust-restoration state for restart and lookup surfaces")
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
        if "dependentContinuationAction" not in generated_ticket_lookup:
            raise RuntimeError("Generated ticket_lookup.ts should route closed completed tickets through the shared dependent-continuation helper instead of presenting them as terminal")
        if "ticketNeedsHistoricalReconciliation" not in generated_ticket_lookup or "ticket_reconcile" not in generated_ticket_lookup:
            raise RuntimeError("Generated ticket_lookup.ts should surface ticket_reconcile when a closed historical ticket still needs lineage repair")
        if "ticketNeedsTrustRestoration" not in generated_ticket_lookup:
            raise RuntimeError("Generated ticket_lookup.ts should detect explicit closed-ticket trust-restoration state, not only global pending process verification")
        if 'next_action_tool: "smoke_test",\n          delegate_to_agent: null,\n          required_owner: "team-leader",' not in generated_ticket_lookup:
            raise RuntimeError("Generated ticket_lookup.ts should keep smoke_test team-leader-owned instead of delegating it to tester-qa")
        generated_ticket_create = (full_dest / ".opencode" / "tools" / "ticket_create.ts").read_text(encoding="utf-8")
        if 'status = "blocked"' in generated_ticket_create:
            raise RuntimeError("Generated ticket_create.ts should not mark split-scope parents blocked")
        if "Keep the parent open and non-foreground until the child work lands." not in generated_ticket_create:
            raise RuntimeError("Generated ticket_create.ts should leave split-scope parents open and linked to their children")
        generated_ticket_reverify = (full_dest / ".opencode" / "tools" / "ticket_reverify.ts").read_text(encoding="utf-8")
        if 'if (sourceTicket.status !== "done")' not in generated_ticket_reverify:
            raise RuntimeError("Generated ticket_reverify.ts should reject attempts to restore trust on non-done tickets")
        if "ticket_reverify requires evidence_artifact_path or verification_content." not in generated_ticket_reverify:
            raise RuntimeError("Generated ticket_reverify.ts should require concrete reverification evidence")
        if 'sourceTicket.verification_state = "reverified"' not in generated_ticket_reverify:
            raise RuntimeError("Generated ticket_reverify.ts should restore the source ticket verification state to reverified")
        if "getTicketWorkflowState(workflow, sourceTicket.id).needs_reverification = false" not in generated_ticket_reverify:
            raise RuntimeError("Generated ticket_reverify.ts should clear the explicit needs_reverification flag after trust restoration")
        if 'kind: "backlog-verification"' not in generated_ticket_reverify or 'kind: "reverification"' not in generated_ticket_reverify:
            raise RuntimeError("Generated ticket_reverify.ts should register both inline backlog-verification evidence and the final reverification artifact")
        generated_ticket_reconcile = (full_dest / ".opencode" / "tools" / "ticket_reconcile.ts").read_text(encoding="utf-8")
        if "currentRegistryArtifact" not in generated_ticket_reconcile:
            raise RuntimeError("Generated ticket_reconcile.ts should allow current registered evidence to justify historical reconciliation")
        if "targetTicket.depends_on = targetTicket.depends_on.filter" not in generated_ticket_reconcile:
            raise RuntimeError("Generated ticket_reconcile.ts should remove contradictory dependencies when reconciliation repairs lineage")
        if 'targetTicket.verification_state = "reverified"' not in generated_ticket_reconcile:
            raise RuntimeError("Generated ticket_reconcile.ts should leave successfully superseded historical targets non-blocking for handoff publication")
        if 'targetTicket.resolution_state = "superseded"' not in generated_ticket_reconcile:
            raise RuntimeError("Generated ticket_reconcile.ts should explicitly mark superseded historical targets closed when requested")
        if "syncWorkflowSelection(workflow, manifest)" not in generated_ticket_reconcile:
            raise RuntimeError("Generated ticket_reconcile.ts should resync active workflow selection after lineage changes")
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
        pivot_dest = workspace / "pivot"
        shutil.copytree(full_dest, pivot_dest)
        make_stack_skill_non_placeholder(pivot_dest)
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
                "--format",
                "json",
            ],
            ROOT,
        )
        if pivot_payload["verification_status"]["verification_kind"] != "post_pivot":
            raise RuntimeError("Pivot orchestration should record a post_pivot verification result")
        if not pivot_payload["verification_status"]["verification_passed"]:
            raise RuntimeError("Pivot orchestration should pass verification on a clean generated repo")
        if pivot_payload["stale_surface_map"]["canonical_brief_and_truth_docs"]["status"] != "replace":
            raise RuntimeError("Pivot orchestration should always replace canonical brief truth surfaces")
        if pivot_payload["stale_surface_map"]["managed_workflow_tools_and_prompts"]["status"] != "replace":
            raise RuntimeError("Architecture pivots should route managed workflow drift through replacement state")
        pivot_stages = [item["stage"] for item in pivot_payload["downstream_refresh"]]
        for expected in ("project-skill-bootstrap", "opencode-team-bootstrap", "agent-prompt-engineering", "ticket-pack-builder", "scafforge-repair"):
            if expected not in pivot_stages:
                raise RuntimeError(f"Pivot orchestration should route {expected} for an architecture-change pivot")
        pivot_brief = (pivot_dest / "docs" / "spec" / "CANONICAL-BRIEF.md").read_text(encoding="utf-8")
        if "## Pivot History" not in pivot_brief or "architecture-change" not in pivot_brief:
            raise RuntimeError("Pivot orchestration should append a Pivot History section to the canonical brief")
        pivot_state_path = pivot_dest / ".opencode" / "meta" / "pivot-state.json"
        if not pivot_state_path.exists():
            raise RuntimeError("Pivot orchestration should persist .opencode/meta/pivot-state.json")
        pivot_state = json.loads(pivot_state_path.read_text(encoding="utf-8"))
        if pivot_state["pivot_state_path"] != ".opencode/meta/pivot-state.json":
            raise RuntimeError("Pivot orchestration should record the canonical pivot state path")
        pivot_provenance = json.loads((pivot_dest / ".opencode" / "meta" / "bootstrap-provenance.json").read_text(encoding="utf-8"))
        pivot_history = pivot_provenance.get("pivot_history")
        if not isinstance(pivot_history, list) or not pivot_history or pivot_history[-1]["pivot_class"] != "architecture-change":
            raise RuntimeError("Pivot orchestration should append pivot history to bootstrap provenance")
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
        manifest = json.loads((ROOT / "skills" / "skill-flow-manifest.json").read_text(encoding="utf-8"))
        greenfield_sequence = manifest["run_types"]["greenfield"]["sequence"]
        verifier_step = "repo-scaffold-factory:verify-generated-scaffold"
        if verifier_step not in greenfield_sequence:
            raise RuntimeError("Greenfield manifest sequence should include the pre-handoff verification gate")
        if greenfield_sequence.index(verifier_step) >= greenfield_sequence.index("handoff-brief"):
            raise RuntimeError("Greenfield manifest sequence should place the verification gate before handoff-brief")

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
        regenerate_module = load_python_module(REGENERATE, "scafforge_smoke_regenerate_restart_surfaces")
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
        for merge_fn in (repair_module.merge_start_here, regenerate_module.merge_start_here):
            partial_start = merge_fn("intro\n<!-- SCAFFORGE:START_HERE_BLOCK START -->\nstale managed block", rendered_block)
            if "stale managed block" in partial_start or "fresh managed block" not in partial_start:
                raise RuntimeError("Partial START marker state should be repaired by replacing the stale managed block")
            partial_end = merge_fn("stale prelude\n<!-- SCAFFORGE:START_HERE_BLOCK END -->\noutro", rendered_block)
            if "stale prelude" in partial_end or "fresh managed block" not in partial_end or "outro" not in partial_end:
                raise RuntimeError("Partial END marker state should be repaired by restoring the managed block while preserving trailing unmanaged content")

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
        if env_only_stale_surface_map["canonical_project_decisions"]["status"] != "stable":
            raise RuntimeError("Routine public repair should not emit canonical-project human-decision escalation from the stale-surface map")

        windows_venv_dest = workspace / "windows-venv-detection"
        windows_venv_dest.mkdir(parents=True, exist_ok=True)
        windows_python = windows_venv_dest / ".venv" / "Scripts" / "python.exe"
        windows_pytest = windows_venv_dest / ".venv" / "Scripts" / "pytest.exe"
        write_executable(
            windows_python,
            "#!/bin/sh\nif [ \"$1\" = \"-m\" ] && [ \"$2\" = \"pytest\" ] && [ \"$3\" = \"--version\" ]; then exit 0; fi\nif [ \"$1\" = \"--version\" ]; then exit 0; fi\nexit 1\n",
        )
        write_executable(windows_pytest, "#!/bin/sh\nexit 0\n")
        detected_python = audit_module._detect_python(windows_venv_dest)
        if detected_python != str(windows_python):
            raise RuntimeError("Audit python detection should recognize repo-local Windows-style .venv/Scripts/python.exe")
        detected_pytest = audit_module._detect_pytest_command(windows_venv_dest)
        if detected_pytest != [str(windows_python), "-m", "pytest"]:
            raise RuntimeError("Audit pytest detection should use Windows-style repo-local python when it is the available executable")

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

        closed_ticket_dependent_dest = workspace / "closed-ticket-dependent-routing"
        shutil.copytree(full_dest, closed_ticket_dependent_dest)
        seed_closed_ticket_with_blocked_dependent(closed_ticket_dependent_dest)
        run_json([sys.executable, str(REGENERATE), str(closed_ticket_dependent_dest)], ROOT)
        closed_ticket_start_here = (closed_ticket_dependent_dest / "START-HERE.md").read_text(encoding="utf-8")
        if "Current ticket is already closed. Activate dependent ticket EXEC-DEP and continue that lane instead of trying to mutate" not in closed_ticket_start_here:
            raise RuntimeError("Restart regeneration should route a closed current ticket directly to the first blocked dependent lane")
        closed_ticket_handoff = (closed_ticket_dependent_dest / ".opencode" / "state" / "latest-handoff.md").read_text(encoding="utf-8")
        if "Current ticket is already closed. Activate dependent ticket EXEC-DEP and continue that lane instead of trying to mutate" not in closed_ticket_handoff:
            raise RuntimeError("latest-handoff should stay aligned with START-HERE for closed-ticket dependent continuation")

        explicit_reverification_dest = workspace / "closed-ticket-explicit-reverification"
        shutil.copytree(full_dest, explicit_reverification_dest)
        seed_closed_ticket_needing_explicit_reverification(explicit_reverification_dest)
        run_json([sys.executable, str(REGENERATE), str(explicit_reverification_dest)], ROOT)
        explicit_reverification_start_here = (explicit_reverification_dest / "START-HERE.md").read_text(encoding="utf-8")
        if "- handoff_status: workflow verification pending" not in explicit_reverification_start_here:
            raise RuntimeError("Restart regeneration should keep handoff_status verification-pending when the active closed ticket still needs explicit reverification")
        if "run ticket_reverify on SETUP-001 instead of trying to reclaim it" not in explicit_reverification_start_here:
            raise RuntimeError("Restart regeneration should surface ticket_reverify as the next move when the active closed ticket still needs explicit trust restoration")
        explicit_reverification_handoff = (explicit_reverification_dest / ".opencode" / "state" / "latest-handoff.md").read_text(encoding="utf-8")
        if "run ticket_reverify on SETUP-001 instead of trying to reclaim it" not in explicit_reverification_handoff:
            raise RuntimeError("latest-handoff should stay aligned with START-HERE for explicit closed-ticket trust restoration")

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
        if reverification_result["ticket_id"] != "SETUP-001" or reverification_result["verification_state"] != "reverified":
            raise RuntimeError("ticket_reverify should return the restored source ticket id and reverified state")
        reverification_manifest = json.loads((executed_reverification_dest / "tickets" / "manifest.json").read_text(encoding="utf-8"))
        reverification_ticket = next(ticket for ticket in reverification_manifest["tickets"] if ticket["id"] == "SETUP-001")
        if reverification_ticket["verification_state"] != "reverified":
            raise RuntimeError("ticket_reverify should persist reverified verification_state onto the historical source ticket")
        reverification_workflow = json.loads((executed_reverification_dest / ".opencode" / "state" / "workflow-state.json").read_text(encoding="utf-8"))
        if reverification_workflow["ticket_state"]["SETUP-001"]["needs_reverification"] is not False:
            raise RuntimeError("ticket_reverify should clear needs_reverification in workflow-state")
        reverification_artifact = executed_reverification_dest / str(reverification_result["reverification_artifact"])
        if not reverification_artifact.exists():
            raise RuntimeError("ticket_reverify should write the canonical reverification artifact")
        backlog_verification_path = executed_reverification_dest / ".opencode" / "state" / "reviews" / "setup-001-review-backlog-verification.md"
        if not backlog_verification_path.exists():
            raise RuntimeError("ticket_reverify should register inline verification content as backlog-verification evidence before restoring trust")

        explicit_reconciliation_dest = workspace / "closed-ticket-explicit-reconciliation"
        shutil.copytree(full_dest, explicit_reconciliation_dest)
        seed_closed_ticket_needing_reconciliation(explicit_reconciliation_dest)
        run_json([sys.executable, str(REGENERATE), str(explicit_reconciliation_dest)], ROOT)
        explicit_reconciliation_start_here = (explicit_reconciliation_dest / "START-HERE.md").read_text(encoding="utf-8")
        if "- handoff_status: workflow verification pending" not in explicit_reconciliation_start_here:
            raise RuntimeError("Restart regeneration should keep handoff_status verification-pending when the active historical ticket still needs reconciliation")
        if "Use ticket_reconcile with current registered evidence to repair SETUP-001 instead of trying to reopen or reclaim it" not in explicit_reconciliation_start_here:
            raise RuntimeError("Restart regeneration should surface ticket_reconcile as the next move when the active historical ticket still has contradictory lineage")
        explicit_reconciliation_handoff = (explicit_reconciliation_dest / ".opencode" / "state" / "latest-handoff.md").read_text(encoding="utf-8")
        if "Use ticket_reconcile with current registered evidence to repair SETUP-001 instead of trying to reopen or reclaim it" not in explicit_reconciliation_handoff:
            raise RuntimeError("latest-handoff should stay aligned with START-HERE for explicit historical reconciliation routing")

        executed_reconciliation_dest = workspace / "executed-ticket-reconcile"
        shutil.copytree(full_dest, executed_reconciliation_dest)
        seed_closed_ticket_needing_reconciliation(executed_reconciliation_dest)
        reconcile_manifest_path = executed_reconciliation_dest / "tickets" / "manifest.json"
        reconcile_workflow_path = executed_reconciliation_dest / ".opencode" / "state" / "workflow-state.json"
        reconcile_registry_path = executed_reconciliation_dest / ".opencode" / "state" / "artifacts" / "registry.json"
        reconcile_manifest = json.loads(reconcile_manifest_path.read_text(encoding="utf-8"))
        reconcile_workflow = json.loads(reconcile_workflow_path.read_text(encoding="utf-8"))
        reconcile_registry = json.loads(reconcile_registry_path.read_text(encoding="utf-8"))
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
        source_ticket = next(ticket for ticket in reconcile_manifest["tickets"] if ticket["id"] == "SETUP-001")
        source_ticket["follow_up_ticket_ids"] = ["EXEC-RECON-TGT"]
        evidence_rel = ".opencode/state/reviews/setup-001-review-backlog-verification.md"
        evidence_path = executed_reconciliation_dest / evidence_rel
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text("# Historical Evidence\n\nCurrent evidence is registered.\n", encoding="utf-8")
        evidence_artifact = {
            "kind": "backlog-verification",
            "path": evidence_rel,
            "stage": "review",
            "summary": "Synthetic reconciliation evidence.",
            "created_at": "2026-03-30T00:00:00Z",
            "trust_state": "current",
        }
        source_ticket.setdefault("artifacts", []).append(evidence_artifact)
        reconcile_registry.setdefault("artifacts", []).append({"ticket_id": "SETUP-001", **evidence_artifact})
        reconcile_workflow["ticket_state"]["EXEC-RECON-SRC"] = {"approved_plan": False, "reopen_count": 0, "needs_reverification": False}
        reconcile_workflow["ticket_state"]["EXEC-RECON-TGT"] = {"approved_plan": False, "reopen_count": 0, "needs_reverification": False}
        reconcile_manifest_path.write_text(json.dumps(reconcile_manifest, indent=2) + "\n", encoding="utf-8")
        reconcile_workflow_path.write_text(json.dumps(reconcile_workflow, indent=2) + "\n", encoding="utf-8")
        reconcile_registry_path.write_text(json.dumps(reconcile_registry, indent=2) + "\n", encoding="utf-8")
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
        if reconciliation_result["replacement_source_ticket_id"] != "EXEC-RECON-SRC" or reconciliation_result["active_ticket"] != "EXEC-RECON-SRC":
            raise RuntimeError("ticket_reconcile should report and activate the replacement source ticket when requested")
        reconciled_manifest = json.loads(reconcile_manifest_path.read_text(encoding="utf-8"))
        reconciled_target = next(ticket for ticket in reconciled_manifest["tickets"] if ticket["id"] == "EXEC-RECON-TGT")
        if reconciled_target["source_ticket_id"] != "EXEC-RECON-SRC":
            raise RuntimeError("ticket_reconcile should rewrite the target source_ticket_id to the replacement source")
        if "SETUP-001" in reconciled_target["depends_on"]:
            raise RuntimeError("ticket_reconcile should remove contradictory dependencies on the stale canonical source when requested")
        if reconciled_manifest["active_ticket"] != "EXEC-RECON-SRC":
            raise RuntimeError("ticket_reconcile should persist the activated replacement source into manifest active_ticket")
        reconciliation_artifact = executed_reconciliation_dest / str(reconciliation_result["reconciliation_artifact"])
        if not reconciliation_artifact.exists():
            raise RuntimeError("ticket_reconcile should write the canonical reconciliation artifact")

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
                "activate": True,
            },
        )
        if split_scope_result["created_ticket"] != "EXEC-SPLIT" or split_scope_result["source_mode"] != "split_scope":
            raise RuntimeError("ticket_create should report the created split-scope child and its source_mode")
        split_scope_manifest = json.loads((executed_split_scope_dest / "tickets" / "manifest.json").read_text(encoding="utf-8"))
        split_source = next(ticket for ticket in split_scope_manifest["tickets"] if ticket["id"] == "SETUP-001")
        split_child = next(ticket for ticket in split_scope_manifest["tickets"] if ticket["id"] == "EXEC-SPLIT")
        if split_scope_manifest["active_ticket"] != "EXEC-SPLIT":
            raise RuntimeError("ticket_create should activate the split-scope child when requested")
        if split_child["source_ticket_id"] != "SETUP-001" or split_child["source_mode"] != "split_scope":
            raise RuntimeError("ticket_create should persist split-scope lineage on the created child")
        if "EXEC-SPLIT" not in split_source["follow_up_ticket_ids"]:
            raise RuntimeError("ticket_create should append split-scope children to the source follow_up_ticket_ids")
        if not any("Keep the parent open and non-foreground until the child work lands." in item for item in split_source["decision_blockers"]):
            raise RuntimeError("ticket_create should record the split-scope parent guidance on the source ticket")

        executed_process_verification_dest = workspace / "executed-ticket-create-process-verification"
        shutil.copytree(full_dest, executed_process_verification_dest)
        seed_closed_ticket_needing_explicit_reverification(executed_process_verification_dest)
        process_manifest_path = executed_process_verification_dest / "tickets" / "manifest.json"
        process_workflow_path = executed_process_verification_dest / ".opencode" / "state" / "workflow-state.json"
        process_manifest = json.loads(process_manifest_path.read_text(encoding="utf-8"))
        process_workflow = json.loads(process_workflow_path.read_text(encoding="utf-8"))
        process_workflow["pending_process_verification"] = True
        process_manifest_path.write_text(json.dumps(process_manifest, indent=2) + "\n", encoding="utf-8")
        process_workflow_path.write_text(json.dumps(process_workflow, indent=2) + "\n", encoding="utf-8")
        process_evidence_rel = ".opencode/state/reviews/setup-001-review-backlog-verification.md"
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
        if process_verification_result["created_ticket"] != "EXEC-PV" or process_verification_result["source_mode"] != "process_verification":
            raise RuntimeError("ticket_create should report process_verification follow-up creation correctly")
        process_verification_manifest = json.loads(process_manifest_path.read_text(encoding="utf-8"))
        process_follow_up = next(ticket for ticket in process_verification_manifest["tickets"] if ticket["id"] == "EXEC-PV")
        if process_follow_up["source_ticket_id"] != "SETUP-001" or process_follow_up["source_mode"] != "process_verification":
            raise RuntimeError("ticket_create should persist process-verification lineage and mode on the created follow-up")
        if process_verification_manifest["active_ticket"] != "EXEC-PV":
            raise RuntimeError("ticket_create should activate the process-verification follow-up when requested")

        executed_issue_intake_dest = workspace / "executed-issue-intake"
        shutil.copytree(full_dest, executed_issue_intake_dest)
        seed_closed_ticket_needing_explicit_reverification(executed_issue_intake_dest)
        rollback_evidence_rel = ".opencode/state/reviews/setup-001-review-existing-evidence.md"
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
        if issue_intake_result["outcome"] != "rollback_required" or issue_intake_result["created_ticket_id"] != "EXEC-ROLLBACK":
            raise RuntimeError("issue_intake should route rollback-required defects into an explicit follow-up ticket")
        issue_manifest = json.loads((executed_issue_intake_dest / "tickets" / "manifest.json").read_text(encoding="utf-8"))
        issue_workflow = json.loads((executed_issue_intake_dest / ".opencode" / "state" / "workflow-state.json").read_text(encoding="utf-8"))
        issue_source = next(ticket for ticket in issue_manifest["tickets"] if ticket["id"] == "SETUP-001")
        issue_follow_up = next(ticket for ticket in issue_manifest["tickets"] if ticket["id"] == "EXEC-ROLLBACK")
        if issue_source["verification_state"] != "invalidated":
            raise RuntimeError("issue_intake should invalidate the source ticket when rollback is required")
        if issue_workflow["ticket_state"]["SETUP-001"]["needs_reverification"] is not True:
            raise RuntimeError("issue_intake should mark the source ticket as needing reverification when rollback is required")
        if issue_manifest["active_ticket"] != "EXEC-ROLLBACK":
            raise RuntimeError("issue_intake should foreground the created rollback follow-up ticket")
        if issue_follow_up["source_ticket_id"] != "SETUP-001" or issue_follow_up["source_mode"] != "post_completion_issue":
            raise RuntimeError("issue_intake should create rollback follow-up tickets with post_completion_issue lineage")
        issue_artifact = executed_issue_intake_dest / str(issue_intake_result["issue_artifact"])
        if not issue_artifact.exists():
            raise RuntimeError("issue_intake should write the canonical issue-discovery artifact")

        executed_lookup_prebootstrap_dest = workspace / "executed-ticket-lookup-prebootstrap"
        shutil.copytree(full_dest, executed_lookup_prebootstrap_dest)
        lookup_prebootstrap = run_generated_tool(
            executed_lookup_prebootstrap_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if lookup_prebootstrap["bootstrap"]["status"] != "missing":
            raise RuntimeError("ticket_lookup should expose the missing bootstrap state on a fresh scaffold")
        prebootstrap_guidance = lookup_prebootstrap["transition_guidance"]
        if prebootstrap_guidance["next_action_tool"] != "environment_bootstrap" or prebootstrap_guidance["next_action_kind"] != "run_tool":
            raise RuntimeError("ticket_lookup should route fresh scaffolds through environment_bootstrap before lifecycle execution")

        executed_lifecycle_dest = workspace / "executed-ordinary-lifecycle"
        shutil.copytree(full_dest, executed_lifecycle_dest)
        seed_ready_bootstrap(executed_lifecycle_dest)
        lookup_without_plan = run_generated_tool(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if lookup_without_plan["bootstrap"]["status"] != "ready":
            raise RuntimeError("ticket_lookup should reflect a ready bootstrap state after bootstrap proof is seeded")
        if lookup_without_plan["transition_guidance"]["next_action_tool"] != "artifact_write":
            raise RuntimeError("ticket_lookup should require a planning artifact before plan_review on a ready planning ticket")
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
        if prebootstrap_claim_result["claimed"] is not True or prebootstrap_claim_result["lease"]["owner_agent"] != "smoke-bootstrap":
            raise RuntimeError("ticket_claim should allow the wave-0 bootstrap ticket to claim a pre-bootstrap write lease")
        prebootstrap_release_result = run_generated_tool(
            executed_lookup_prebootstrap_dest,
            ".opencode/tools/ticket_release.ts",
            {"ticket_id": "SETUP-001", "owner_agent": "smoke-bootstrap"},
        )
        if prebootstrap_release_result["released"]["ticket_id"] != "SETUP-001":
            raise RuntimeError("ticket_release should release the bootstrap lease after the pre-bootstrap claim probe")
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
        if lookup_with_plan["transition_guidance"]["next_action_tool"] != "ticket_update":
            raise RuntimeError("ticket_lookup should recommend ticket_update once a planning artifact exists")
        if lookup_with_plan["transition_guidance"]["recommended_ticket_update"]["stage"] != "plan_review":
            raise RuntimeError("ticket_lookup should recommend moving a planned ticket into plan_review next")
        direct_implementation_error = run_generated_tool_error(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "implementation", "activate": True},
        )
        if "plan is approved" not in direct_implementation_error and "passes through plan_review" not in direct_implementation_error:
            raise RuntimeError("ticket_update should block direct jumps into implementation before plan_review approval")
        plan_review_result = run_generated_tool(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "plan_review", "activate": True},
        )
        if plan_review_result["updated_ticket"]["stage"] != "plan_review":
            raise RuntimeError("ticket_update should move the ticket into plan_review when planning proof exists")
        combined_approval_error = run_generated_tool_error(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "implementation", "approved_plan": True, "activate": True},
        )
        if "Approve SETUP-001 while it remains in plan_review first" not in combined_approval_error:
            raise RuntimeError("ticket_update should require plan approval and implementation transition as separate calls")
        approval_result = run_generated_tool(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "approved_plan": True, "activate": True},
        )
        if approval_result["workflow"]["ticket_state"]["SETUP-001"]["approved_plan"] is not True:
            raise RuntimeError("ticket_update should persist approved_plan in workflow-state")
        lookup_plan_approved = run_generated_tool(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_lookup.ts",
            {},
        )
        if lookup_plan_approved["transition_guidance"]["recommended_ticket_update"]["stage"] != "implementation":
            raise RuntimeError("ticket_lookup should recommend implementation once plan_review approval is recorded")
        implementation_result = run_generated_tool(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": "SETUP-001", "stage": "implementation", "activate": True},
        )
        if implementation_result["updated_ticket"]["stage"] != "implementation":
            raise RuntimeError("ticket_update should move an approved ticket into implementation")
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
        if claim_result["claimed"] is not True or claim_result["lease"]["ticket_id"] != "SETUP-001":
            raise RuntimeError("ticket_claim should create a write-capable lane lease for the active implementation ticket")
        if claim_result["lease"]["owner_agent"] != "smoke-implementer":
            raise RuntimeError("ticket_claim should persist the requesting owner_agent on the created lease")
        release_result = run_generated_tool(
            executed_lifecycle_dest,
            ".opencode/tools/ticket_release.ts",
            {"ticket_id": "SETUP-001", "owner_agent": "smoke-implementer"},
        )
        if release_result["released"]["ticket_id"] != "SETUP-001":
            raise RuntimeError("ticket_release should release the matching active lease for the ticket")
        if release_result["active_leases"]:
            raise RuntimeError("ticket_release should leave no active leases after releasing the only lease")

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
        if "Artifact path mismatch" not in noncanonical_artifact_error or ".opencode/state/plans/setup-001-planning-plan.md" not in noncanonical_artifact_error:
            raise RuntimeError("artifact_write should reject non-canonical artifact paths")
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
            raise RuntimeError("artifact_write should persist to the canonical planning artifact path")
        if not (executed_artifact_tools_dest / plan_artifact_path).exists():
            raise RuntimeError("artifact_write should create the canonical artifact file on disk")
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
        if latest_registered_plan["stage"] != "planning" or latest_registered_plan["kind"] != "plan":
            raise RuntimeError("artifact_register should persist the stage and kind of the registered artifact")
        if not str(latest_registered_plan["path"]).startswith(".opencode/state/artifacts/history/setup-001/planning/"):
            raise RuntimeError("artifact_register should snapshot canonical artifacts into history-backed registry storage")
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
        if "Use smoke_test to create smoke-test artifacts." not in stage_gate_reserved_write_error:
            raise RuntimeError("Stage gate plugin should block generic artifact_write for reserved smoke-test artifacts")
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
        if "Use smoke_test to create smoke-test artifacts." not in stage_gate_reserved_register_error:
            raise RuntimeError("Stage gate plugin should block generic artifact_register for reserved smoke-test artifacts")
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
            raise RuntimeError("Stage gate plugin should block implementation artifact writes when no active ticket lease exists")
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
        executed_reopen_dest = workspace / "executed-ticket-reopen"
        shutil.copytree(full_dest, executed_reopen_dest)
        seed_closed_ticket_needing_explicit_reverification(executed_reopen_dest)
        reopen_evidence_rel = ".opencode/state/reviews/setup-001-review-reopen-evidence.md"
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
        reopen_workflow = json.loads(reopen_workflow_path.read_text(encoding="utf-8"))
        reopen_workflow["lane_leases"] = [
            {
                "ticket_id": "SETUP-001",
                "lane": "repo-foundation",
                "owner_agent": "smoke-implementer",
                "write_lock": True,
                "claimed_at": "2026-03-30T00:00:00Z",
                "expires_at": "2099-03-30T00:00:00Z",
                "allowed_paths": ["."],
            }
        ]
        reopen_workflow_path.write_text(json.dumps(reopen_workflow, indent=2) + "\n", encoding="utf-8")
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
        reopened_manifest = json.loads((executed_reopen_dest / "tickets" / "manifest.json").read_text(encoding="utf-8"))
        reopened_workflow = json.loads(reopen_workflow_path.read_text(encoding="utf-8"))
        reopened_ticket = next(ticket for ticket in reopened_manifest["tickets"] if ticket["id"] == "SETUP-001")
        if reopened_ticket["stage"] != "planning" or reopened_ticket["status"] != "todo":
            raise RuntimeError("ticket_reopen should return a completed ticket to planning/todo")
        if reopened_ticket["resolution_state"] != "reopened" or reopened_ticket["verification_state"] != "invalidated":
            raise RuntimeError("ticket_reopen should mark the reopened ticket as reopened and invalidated")
        if reopened_workflow["ticket_state"]["SETUP-001"]["reopen_count"] != 1 or reopened_workflow["ticket_state"]["SETUP-001"]["needs_reverification"] is not True:
            raise RuntimeError("ticket_reopen should increment reopen_count and require reverification")
        if reopened_workflow["lane_leases"]:
            raise RuntimeError("ticket_reopen should release any active lease on the reopened ticket")
        if not all(artifact["trust_state"] != "current" for artifact in reopened_ticket["artifacts"]):
            raise RuntimeError("ticket_reopen should mark prior current artifacts historical when reopening a ticket")
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
        if "## Active Ticket" not in context_snapshot_text or "Synthetic snapshot note for Phase 5 runtime coverage." not in context_snapshot_text:
            raise RuntimeError("context_snapshot should write the canonical snapshot with the requested note")
        handoff_publish_result = run_generated_tool(
            executed_context_handoff_dest,
            ".opencode/tools/handoff_publish.ts",
            {
                "next_action": "Keep SETUP-001 as the foreground ticket and continue its lifecycle from planning.",
            },
        )
        start_here_text = (executed_context_handoff_dest / "START-HERE.md").read_text(encoding="utf-8")
        latest_handoff_text = (executed_context_handoff_dest / ".opencode" / "state" / "latest-handoff.md").read_text(encoding="utf-8")
        if str(handoff_publish_result["start_here"]) != str(executed_context_handoff_dest / "START-HERE.md"):
            raise RuntimeError("handoff_publish should report the canonical START-HERE path")
        if "Keep SETUP-001 as the foreground ticket and continue its lifecycle from planning." not in start_here_text:
            raise RuntimeError("handoff_publish should publish the requested next_action into START-HERE")
        if "Keep SETUP-001 as the foreground ticket and continue its lifecycle from planning." not in latest_handoff_text:
            raise RuntimeError("handoff_publish should publish the requested next_action into the latest handoff copy")
        invalid_handoff_dest = workspace / "executed-invalid-handoff"
        shutil.copytree(full_dest, invalid_handoff_dest)
        seed_truthful_process_verification(invalid_handoff_dest)
        invalid_handoff_error = run_generated_tool_error(
            invalid_handoff_dest,
            ".opencode/tools/handoff_publish.ts",
            {"next_action": "Repo is clean and fully verified. No follow-up required."},
        )
        if "pending_process_verification" not in invalid_handoff_error:
            raise RuntimeError("handoff_publish should reject clean-state claims while pending_process_verification remains true")

        executed_environment_bootstrap_dest = workspace / "executed-environment-bootstrap"
        shutil.copytree(full_dest, executed_environment_bootstrap_dest)
        if host_has_npm:
            seed_minimal_npm_repo(executed_environment_bootstrap_dest)
        bootstrap_result = run_generated_tool(
            executed_environment_bootstrap_dest,
            ".opencode/tools/environment_bootstrap.ts",
            {"ticket_id": "SETUP-001"},
        )
        if bootstrap_result["bootstrap_status"] != "ready":
            raise RuntimeError("environment_bootstrap should record a ready bootstrap state when its detected commands succeed")
        if host_has_npm and not any(command["label"] == "npm ci" and command["exit_code"] == 0 for command in bootstrap_result["commands"]):
            raise RuntimeError("environment_bootstrap should execute npm ci for a minimal lockfile-backed Node repo")
        if host_has_npm and bootstrap_result["host_surface_classification"] != "none":
            raise RuntimeError("environment_bootstrap should not classify a successful bootstrap run as a host-surface failure")
        bootstrap_proof = executed_environment_bootstrap_dest / str(bootstrap_result["proof_artifact"])
        if not bootstrap_proof.exists():
            raise RuntimeError("environment_bootstrap should persist the canonical bootstrap proof artifact")
        bootstrap_workflow = json.loads((executed_environment_bootstrap_dest / ".opencode" / "state" / "workflow-state.json").read_text(encoding="utf-8"))
        if bootstrap_workflow["bootstrap"]["status"] != "ready":
            raise RuntimeError("environment_bootstrap should persist ready bootstrap state into workflow-state")

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
                "command_override": ["SMOKE_TOKEN=phase5 python3 scripts/mock_smoke.py"],
            },
        )
        if smoke_test_result["passed"] is not True or smoke_test_result["host_surface_classification"] is not None:
            raise RuntimeError("smoke_test should pass and avoid host-surface failure classification when its explicit command succeeds")
        if smoke_test_result["commands"][0]["command"] != "SMOKE_TOKEN=phase5 python3 scripts/mock_smoke.py":
            raise RuntimeError("smoke_test should preserve shell-style KEY=VALUE command_override parsing in the executed command record")
        smoke_test_artifact = executed_smoke_test_dest / str(smoke_test_result["smoke_test_artifact"])
        if not smoke_test_artifact.exists():
            raise RuntimeError("smoke_test should persist the canonical smoke-test artifact")
        smoke_test_artifact_body = smoke_test_artifact.read_text(encoding="utf-8")
        if "Overall Result: PASS" not in smoke_test_artifact_body or "SMOKE_TOKEN=phase5 python3 scripts/mock_smoke.py" not in smoke_test_artifact_body:
            raise RuntimeError("smoke_test should record the passing result and executed command in the smoke-test artifact")

        executed_smoke_missing_exec_dest = workspace / "executed-smoke-test-missing-exec"
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
            raise RuntimeError("smoke_test should fail when the explicit smoke command executable does not exist")
        if smoke_missing_exec_result["failure_classification"] != "environment" or smoke_missing_exec_result["host_surface_classification"] != "missing_executable":
            raise RuntimeError("smoke_test should classify missing explicit smoke executables as an environment host-surface failure")
        if smoke_missing_exec_result["commands"][0]["missing_executable"] != "definitely-missing-phase5-command":
            raise RuntimeError("smoke_test should report the missing explicit smoke executable by name")

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
            raise RuntimeError("Public managed repair runner should reject unknown follow-on stage names instead of silently recording them")
        if "Unknown repair follow-on stage" not in invalid_public_stage.stderr and "Unknown repair follow-on stage" not in invalid_public_stage.stdout:
            raise RuntimeError("Public managed repair runner should explain unknown follow-on stage rejection")
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
            raise RuntimeError("record_repair_stage_completion should reject unknown follow-on stage names instead of silently persisting them")
        if "Unknown repair follow-on stage" not in invalid_record_stage.stderr and "Unknown repair follow-on stage" not in invalid_record_stage.stdout:
            raise RuntimeError("record_repair_stage_completion should explain unknown follow-on stage rejection")

        source_follow_up_repair_dest = workspace / "source-follow-up-repair"
        shutil.copytree(full_dest, source_follow_up_repair_dest)
        make_stack_skill_non_placeholder(source_follow_up_repair_dest)
        seed_failing_pytest_suite(source_follow_up_repair_dest)
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
                raise RuntimeError("Public managed repair runner should reject known follow-on stages that are not part of the current repair cycle")
            if "not part of the current repair cycle" not in invalid_known_stage_process.stderr and "not part of the current repair cycle" not in invalid_known_stage_process.stdout:
                raise RuntimeError("Public managed repair runner should explain current-cycle rejection for known but non-required follow-on stages")
            invalid_known_evidence_rel = ".opencode/state/artifacts/history/repair/non-required-stage.md"
            invalid_known_evidence_path = source_follow_up_repair_dest / invalid_known_evidence_rel
            invalid_known_evidence_path.parent.mkdir(parents=True, exist_ok=True)
            invalid_known_evidence_path.write_text("# Non-required stage\n", encoding="utf-8")
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
                raise RuntimeError("record_repair_stage_completion should reject known follow-on stages that are not part of the current repair cycle")
            if "not part of the current repair cycle" not in invalid_known_record_stage.stderr and "not part of the current repair cycle" not in invalid_known_record_stage.stdout:
                raise RuntimeError("record_repair_stage_completion should explain current-cycle rejection for known but non-required follow-on stages")
            polluted_follow_on_state_dest = workspace / "polluted-follow-on-state"
            shutil.copytree(full_dest, polluted_follow_on_state_dest)
            make_stack_skill_non_placeholder(polluted_follow_on_state_dest)
            seed_failing_pytest_suite(polluted_follow_on_state_dest)
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
                raise RuntimeError("A repair run without any valid follow-on completion should remain blocked before polluted-state pruning is tested")
            polluted_state_path = polluted_follow_on_state_dest / ".opencode" / "meta" / "repair-follow-on-state.json"
            polluted_state = json.loads(polluted_state_path.read_text(encoding="utf-8"))
            polluted_state["required_stages"].append("bogus-stage")
            polluted_state["stage_records"]["bogus-stage"] = {
                "stage": "bogus-stage",
                "status": "completed",
                "completion_mode": "recorded_execution",
                "evidence_paths": [".opencode/state/artifacts/history/repair/bogus-stage.md"],
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
            polluted_state_path.write_text(json.dumps(polluted_state, indent=2) + "\n", encoding="utf-8")
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
                raise RuntimeError("Pruning unknown legacy follow-on stage records should not make the repair runner succeed while real ticket follow-up remains")
            pruned_follow_on_state = json.loads(pruned_follow_on_state_process.stdout)
            if "bogus-stage" in pruned_follow_on_state["execution_record"]["recorded_completed_stages"]:
                raise RuntimeError("Managed repair should prune unknown legacy follow-on stage records instead of trusting them as completed")
            if pruned_follow_on_state["execution_record"]["pruned_unknown_stages"] != ["bogus-stage"]:
                raise RuntimeError("Managed repair should report which unknown legacy follow-on stages were pruned from polluted state")
            if "bogus-stage" in pruned_follow_on_state["execution_record"]["follow_on_tracking_state"]["stage_records"]:
                raise RuntimeError("Managed repair should remove unknown legacy follow-on stage records from the persisted tracking state")
            prune_history = pruned_follow_on_state["execution_record"]["follow_on_tracking_state"].get("history", [])
            if not any(item.get("status") == "pruned_unknown_stages" and item.get("pruned_unknown_stages") == ["bogus-stage"] for item in prune_history if isinstance(item, dict)):
                raise RuntimeError("Managed repair should leave a history event when polluted unknown follow-on stages are pruned")
            if not pruned_follow_on_state["execution_record"]["blocking_reasons"]:
                raise RuntimeError("Pruning unknown legacy follow-on stage records should not clear the real ticket follow-up blocker")

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
            required_stage_details = source_follow_up_repair["execution_record"]["required_follow_on_stage_details"]
            if required_stage_details != [
                {
                    "stage": "ticket-pack-builder",
                    "owner": "ticket-pack-builder",
                    "category": "ticket_follow_up",
                    "reason": "Repair left remediation or reverification follow-up that must be routed into the repo ticket system.",
                }
            ]:
                raise RuntimeError("Public managed repair runner should expose machine-readable owner/category metadata for required follow-on stages")
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
            if source_follow_up_workflow["repair_follow_on"]["tracking_mode"] != "persistent_recorded_state":
                raise RuntimeError("Managed repair should record persistent follow-on tracking mode in workflow state")
            if source_follow_up_workflow["repair_follow_on"]["required_stage_details"] != required_stage_details:
                raise RuntimeError("Managed repair should persist machine-readable required stage details into workflow-state")
            follow_on_state_path = source_follow_up_repair_dest / ".opencode" / "meta" / "repair-follow-on-state.json"
            if not follow_on_state_path.exists():
                raise RuntimeError("Managed repair should persist follow-on stage state in repo metadata")
            follow_on_state = json.loads(follow_on_state_path.read_text(encoding="utf-8"))
            if follow_on_state["tracking_mode"] != "persistent_recorded_state":
                raise RuntimeError("Persisted follow-on stage state should record persistent tracking mode")
            if follow_on_state["stage_records"]["ticket-pack-builder"]["status"] != "asserted_completed":
                raise RuntimeError("Persisted follow-on stage state should keep asserted follow-on stage completion")
            if follow_on_state["stage_records"]["ticket-pack-builder"]["owner"] != "ticket-pack-builder" or follow_on_state["stage_records"]["ticket-pack-builder"]["category"] != "ticket_follow_up":
                raise RuntimeError("Persisted follow-on stage state should keep machine-readable owner/category metadata for canonical stages")
            if not any(
                item.get("status") == "asserted_completed"
                and item.get("stage") == "ticket-pack-builder"
                and item.get("owner") == "ticket-pack-builder"
                and item.get("category") == "ticket_follow_up"
                for item in follow_on_state.get("history", [])
                if isinstance(item, dict)
            ):
                raise RuntimeError("Persisted follow-on history should keep owner/category metadata for asserted stage completion events")

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
                raise RuntimeError("Recorded follow-on stage state should let later repair runs reuse prior asserted completion without re-passing --stage-complete")
            if source_follow_up_repair_reuse["execution_record"]["recorded_completed_stages"] != ["handoff-brief", "ticket-pack-builder"]:
                raise RuntimeError("Public managed repair runner should expose persisted recorded follow-on completions")
            if source_follow_up_repair_reuse["execution_record"]["repair_follow_on_outcome"] != "source_follow_up":
                raise RuntimeError("Reused follow-on stage state should preserve the same source_follow_up outcome")
            if not source_follow_up_repair_reuse["execution_record"]["handoff_allowed"]:
                raise RuntimeError("Reused follow-on stage state should still allow handoff when only source follow-up remains")
            recorded_stage_results = {
                item["stage"]: item["status"]
                for item in source_follow_up_repair_reuse["stage_results"]
                if item.get("status") == "recorded_completed"
            }
            if recorded_stage_results != {"handoff-brief": "recorded_completed", "ticket-pack-builder": "recorded_completed"}:
                raise RuntimeError("Managed repair should expose reused follow-on completions as recorded_completed stage results")

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
                raise RuntimeError("A repair run with unresolved ticket follow-up should fail closed before any canonical completion artifact exists")
            auto_detected_initial = json.loads(auto_detected_initial_process.stdout)
            if not auto_detected_initial["execution_record"]["blocking_reasons"]:
                raise RuntimeError("A repair run with unresolved ticket follow-up should stay blocked before any canonical completion artifact exists")
            auto_follow_on_state_path = auto_detected_follow_on_dest / ".opencode" / "meta" / "repair-follow-on-state.json"
            auto_follow_on_state = json.loads(auto_follow_on_state_path.read_text(encoding="utf-8"))
            auto_cycle_id = auto_follow_on_state["cycle_id"]
            auto_evidence_rel = ".opencode/state/artifacts/history/repair/ticket-pack-builder-completion.md"
            auto_evidence_path = auto_detected_follow_on_dest / auto_evidence_rel
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
                raise RuntimeError("Managed repair should fail closed when only a stale-cycle canonical completion artifact exists")
            wrong_cycle_auto_detect = json.loads(wrong_cycle_auto_detect_process.stdout)
            if wrong_cycle_auto_detect["execution_record"]["auto_detected_recorded_stages"]:
                raise RuntimeError("Managed repair should not auto-detect canonical stage evidence whose cycle_id does not match the current repair cycle")
            if not wrong_cycle_auto_detect["execution_record"]["blocking_reasons"]:
                raise RuntimeError("Managed repair should remain blocked when only a stale-cycle completion artifact exists")
            auto_evidence_path.write_text(
                "# Repair Follow-On Completion\n\n"
                "- completed_stage: ticket-pack-builder\n"
                f"- cycle_id: {auto_cycle_id}\n"
                "- completed_by: ticket-pack-builder\n\n"
                "## Summary\n\n"
                "- Created or updated the canonical repair follow-up tickets required by the current repair cycle.\n",
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
                raise RuntimeError("Managed repair should auto-recognize current-cycle canonical ticket-pack-builder completion evidence without a separate recording command")
            if auto_detected_reuse["execution_record"]["auto_detected_recorded_stages"] != ["ticket-pack-builder"]:
                raise RuntimeError("Managed repair should report current-cycle canonical ticket-pack-builder evidence as an auto-detected recorded stage")
            if auto_detected_reuse["execution_record"]["recorded_execution_completed_stages"] != ["ticket-pack-builder"]:
                raise RuntimeError("Auto-detected canonical ticket-pack-builder evidence should count as recorded_execution completion")
            auto_detected_state = json.loads(auto_follow_on_state_path.read_text(encoding="utf-8"))
            if auto_detected_state["stage_records"]["ticket-pack-builder"]["completed_by"] != "ticket-pack-builder:auto-detected":
                raise RuntimeError("Auto-detected canonical ticket-pack-builder evidence should persist completed_by as ticket-pack-builder:auto-detected")
            if auto_detected_state["stage_records"]["ticket-pack-builder"]["evidence_paths"] != [auto_evidence_rel]:
                raise RuntimeError("Auto-detected canonical ticket-pack-builder evidence should preserve the canonical repair artifact path")

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
                raise RuntimeError("A repair run without any follow-on completion record should remain blocked before zero-evidence pollution is tested")
            zero_evidence_state_path = zero_evidence_follow_on_dest / ".opencode" / "meta" / "repair-follow-on-state.json"
            zero_evidence_state = json.loads(zero_evidence_state_path.read_text(encoding="utf-8"))
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
            zero_evidence_state_path.write_text(json.dumps(zero_evidence_state, indent=2) + "\n", encoding="utf-8")
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
            if "ticket-pack-builder" not in zero_evidence_follow_on["execution_record"]["invalidated_recorded_stages"]:
                raise RuntimeError("Managed repair should invalidate recorded execution state that claims completion with zero evidence paths")
            if zero_evidence_follow_on["execution_record"]["recorded_execution_completed_stages"]:
                raise RuntimeError("Managed repair should not report zero-evidence recorded execution as completed work")
            if not zero_evidence_follow_on["execution_record"]["blocking_reasons"]:
                raise RuntimeError("Managed repair should block again when polluted zero-evidence recorded execution is invalidated")
            zero_evidence_follow_on_state = json.loads(zero_evidence_state_path.read_text(encoding="utf-8"))
            if zero_evidence_follow_on_state["stage_records"]["ticket-pack-builder"]["status"] != "evidence_missing":
                raise RuntimeError("Follow-on tracking should persist evidence_missing when polluted recorded execution has zero evidence paths")
            if zero_evidence_follow_on_state["stage_records"]["ticket-pack-builder"].get("evidence_validation_error") != "missing_recorded_evidence":
                raise RuntimeError("Follow-on tracking should record why zero-evidence recorded execution was invalidated")

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
            recorded_follow_on_initial = json.loads(recorded_follow_on_initial_process.stdout)
            if not recorded_follow_on_initial["execution_record"]["blocking_reasons"]:
                raise RuntimeError("A repair run without any follow-on completion record should remain blocked when ticket follow-up is still required")
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
                raise RuntimeError("record_repair_stage_completion should reject explicit recorded execution that provides zero evidence paths")
            if "requires at least one repo-relative evidence path" not in no_evidence_record_stage.stderr and "requires at least one repo-relative evidence path" not in no_evidence_record_stage.stdout:
                raise RuntimeError("record_repair_stage_completion should explain zero-evidence recorded execution rejection")
            recorded_evidence_rel = ".opencode/state/artifacts/history/repair/ticket-pack-builder-completion.md"
            recorded_evidence_path = recorded_follow_on_dest / recorded_evidence_rel
            recorded_evidence_path.parent.mkdir(parents=True, exist_ok=True)
            recorded_evidence_path.write_text("# Ticket Pack Builder Completion\n\nRecorded execution evidence.\n", encoding="utf-8")
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
                raise RuntimeError("record_repair_stage_completion should persist completed status for explicit recorded execution")
            if recorded_stage_payload["recorded_stage"]["completion_mode"] != "recorded_execution":
                raise RuntimeError("record_repair_stage_completion should mark explicit stage completion as recorded_execution")
            if recorded_stage_payload["recorded_stage"]["evidence_paths"] != [recorded_evidence_rel]:
                raise RuntimeError("record_repair_stage_completion should preserve the recorded evidence paths")
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
                raise RuntimeError("A later repair run should reuse explicit recorded stage completion without needing transitional --stage-complete input")
            if recorded_follow_on_reuse["execution_record"]["recorded_execution_completed_stages"] != ["ticket-pack-builder"]:
                raise RuntimeError("Managed repair should report explicit recorded_execution completions separately from asserted stages")
            if recorded_follow_on_reuse["execution_record"]["asserted_completed_stages"]:
                raise RuntimeError("Explicit recorded_execution follow-on completion should not populate asserted_completed_stages")
            if recorded_follow_on_reuse["execution_record"]["repair_follow_on_outcome"] != "source_follow_up":
                raise RuntimeError("Explicit recorded_execution follow-on completion should still converge to source_follow_up when only EXEC findings remain")
            recorded_follow_on_state = json.loads((recorded_follow_on_dest / ".opencode" / "meta" / "repair-follow-on-state.json").read_text(encoding="utf-8"))
            if recorded_follow_on_state["stage_records"]["ticket-pack-builder"]["completed_by"] != "ticket-pack-builder":
                raise RuntimeError("Persisted follow-on tracking should keep completed_by for explicitly recorded execution")
            if not any(
                item.get("status") == "completed"
                and item.get("stage") == "ticket-pack-builder"
                and item.get("owner") == "ticket-pack-builder"
                and item.get("category") == "ticket_follow_up"
                for item in recorded_follow_on_state.get("history", [])
                if isinstance(item, dict)
            ):
                raise RuntimeError("Persisted follow-on history should keep owner/category metadata for recorded execution events")
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
            recorded_follow_on_missing_evidence = json.loads(recorded_follow_on_missing_evidence_process.stdout)
            if "ticket-pack-builder" not in recorded_follow_on_missing_evidence["execution_record"]["invalidated_recorded_stages"]:
                raise RuntimeError("Managed repair should invalidate recorded execution reuse when the supporting evidence path disappears")
            if recorded_follow_on_missing_evidence["execution_record"]["recorded_execution_completed_stages"]:
                raise RuntimeError("Managed repair should stop reporting recorded execution completion when its evidence is missing")
            if not recorded_follow_on_missing_evidence["execution_record"]["blocking_reasons"]:
                raise RuntimeError("Managed repair should block again when required recorded execution evidence is missing")
            missing_evidence_state = json.loads((recorded_follow_on_dest / ".opencode" / "meta" / "repair-follow-on-state.json").read_text(encoding="utf-8"))
            if missing_evidence_state["stage_records"]["ticket-pack-builder"]["status"] != "evidence_missing":
                raise RuntimeError("Follow-on tracking should persist evidence_missing when recorded execution evidence disappears")

            run_managed_repair_module = load_python_module(PUBLIC_REPAIR, "scafforge_smoke_run_managed_repair")
            contract_failures = run_managed_repair_module.verification_contract_failures(
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
            if "restart_surface_drift_after_repair" not in contract_failures:
                raise RuntimeError("Repair verification contract checks should treat WFLOW010 as a hard post-repair consistency failure")

            placeholder_contract_failures = run_managed_repair_module.verification_contract_failures(
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
            if "placeholder_local_skills_survived_refresh" not in placeholder_contract_failures:
                raise RuntimeError("Repair verification contract checks should treat SKILL001 as a hard post-repair consistency failure")

            empty_non_clean_contract_failures = run_managed_repair_module.verification_contract_failures(
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
            if "non_clean_without_findings" not in empty_non_clean_contract_failures:
                raise RuntimeError("Repair verification contract checks should flag zero-finding non-clean states as a repair-contract failure")
        else:
            print("Skipping uv-dependent source-follow-up public repair assertions because `uv` is not available on this host.")

        print("Scafforge smoke test passed.")
        return 0
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
