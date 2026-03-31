from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "skills" / "repo-scaffold-factory" / "scripts" / "bootstrap_repo_scaffold.py"
VERIFY_GENERATED = ROOT / "skills" / "repo-scaffold-factory" / "scripts" / "verify_generated_scaffold.py"
CHECKLIST = ROOT / "skills" / "repo-scaffold-factory" / "references" / "opencode-conformance-checklist.json"
AUDIT = ROOT / "skills" / "scafforge-audit" / "scripts" / "audit_repo_process.py"
REPAIR = ROOT / "skills" / "scafforge-repair" / "scripts" / "apply_repo_process_repair.py"
PUBLIC_REPAIR = ROOT / "skills" / "scafforge-repair" / "scripts" / "run_managed_repair.py"
REGENERATE = ROOT / "skills" / "scafforge-repair" / "scripts" / "regenerate_restart_surfaces.py"
PIVOT = ROOT / "skills" / "scafforge-pivot" / "scripts" / "plan_pivot.py"
PIVOT_RECORD = ROOT / "skills" / "scafforge-pivot" / "scripts" / "record_pivot_stage_completion.py"
PIVOT_PUBLISH = ROOT / "skills" / "scafforge-pivot" / "scripts" / "publish_pivot_surfaces.py"
PIVOT_APPLY = ROOT / "skills" / "scafforge-pivot" / "scripts" / "apply_pivot_lineage.py"
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


def run_json(
    command: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    allow_returncodes: set[int] | None = None,
) -> dict[str, Any]:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, env=env)
    allowed = allow_returncodes or {0}
    if result.returncode not in allowed:
        raise RuntimeError(f"Command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Command did not return valid JSON: {' '.join(command)}\nSTDOUT:\n{result.stdout}") from exc


def write_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | 0o111)


def node_command() -> list[str]:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js is required to execute generated TypeScript tools in Scafforge smoke and integration tests.")
    result = subprocess.run([node, "--version"], cwd=ROOT, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Unable to determine Node.js version for generated tool execution:\nSTDERR:\n{result.stderr}")
    match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", result.stdout.strip())
    if not match:
        raise RuntimeError(f"Unable to parse Node.js version output: {result.stdout.strip()!r}")
    major, minor, patch = (int(part) for part in match.groups())
    if (major, minor, patch) < (22, 6, 0):
        raise RuntimeError(
            f"Generated TypeScript tool execution requires Node.js 22.6.0 or newer for --experimental-strip-types; found {result.stdout.strip()}."
        )
    return [node, "--experimental-strip-types"]


def write_runner(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def tool_runner_lines() -> list[str]:
    return [
        'import { pathToFileURL } from "node:url"',
        "const toolPath = process.env.SCAFFORGE_TOOL_PATH",
        "if (!toolPath) throw new Error('Missing SCAFFORGE_TOOL_PATH')",
        "const mod = await import(pathToFileURL(toolPath).href)",
        "const rawArgs = process.env.SCAFFORGE_TOOL_ARGS || '{}'",
        "const payload = await mod.default.execute(JSON.parse(rawArgs))",
        "console.log(payload)",
    ]


def plugin_runner_lines() -> list[str]:
    return [
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


def compute_bootstrap_fingerprint(dest: Path) -> str:
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
    write_runner(runner, tool_runner_lines())
    env = os.environ.copy()
    env["SCAFFORGE_TOOL_PATH"] = str((dest / relative_tool_path).resolve())
    env["SCAFFORGE_TOOL_ARGS"] = json.dumps(args)
    return run_json([*node_command(), str(runner)], dest, env=env)


def run_generated_tool_error(dest: Path, relative_tool_path: str, args: dict[str, object]) -> str:
    prepare_generated_tool_runtime(dest)
    runner = dest / ".opencode" / "state" / "tool-runner.mjs"
    write_runner(runner, tool_runner_lines())
    env = os.environ.copy()
    env["SCAFFORGE_TOOL_PATH"] = str((dest / relative_tool_path).resolve())
    env["SCAFFORGE_TOOL_ARGS"] = json.dumps(args)
    result = subprocess.run(
        [*node_command(), str(runner)],
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
    write_runner(runner, plugin_runner_lines())
    env = os.environ.copy()
    env["SCAFFORGE_PLUGIN_PATH"] = str((dest / relative_plugin_path).resolve())
    env["SCAFFORGE_PLUGIN_TOOL"] = tool_name
    env["SCAFFORGE_PLUGIN_ARGS"] = json.dumps(args)
    run([*node_command(), str(runner)], dest, env=env)


def run_generated_plugin_before_error(dest: Path, relative_plugin_path: str, tool_name: str, args: dict[str, object]) -> str:
    prepare_generated_tool_runtime(dest)
    runner = dest / ".opencode" / "state" / "plugin-runner.mjs"
    write_runner(runner, plugin_runner_lines())
    env = os.environ.copy()
    env["SCAFFORGE_PLUGIN_PATH"] = str((dest / relative_plugin_path).resolve())
    env["SCAFFORGE_PLUGIN_TOOL"] = tool_name
    env["SCAFFORGE_PLUGIN_ARGS"] = json.dumps(args)
    result = subprocess.run(
        [*node_command(), str(runner)],
        cwd=dest,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode == 0:
        raise RuntimeError(f"Plugin hook unexpectedly succeeded: {relative_plugin_path} {tool_name}")
    return f"{result.stdout}\n{result.stderr}".strip()


def bootstrap_full(dest: Path) -> None:
    run(
        [
            sys.executable,
            str(BOOTSTRAP),
            "--dest",
            str(dest),
            "--project-name",
            "Integration Probe",
            "--project-slug",
            "integration-probe",
            "--agent-prefix",
            "integration-probe",
            "--model-provider",
            "openrouter",
            "--planner-model",
            "openrouter/openai/gpt-5-mini",
            "--implementer-model",
            "openrouter/openai/gpt-5-mini",
            "--utility-model",
            "openrouter/openai/gpt-5-mini",
            "--stack-label",
            "framework-agnostic",
            "--scope",
            "full",
            "--force",
        ],
        ROOT,
    )
