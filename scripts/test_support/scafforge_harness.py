from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from functools import lru_cache
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = (
    ROOT / "skills" / "repo-scaffold-factory" / "scripts" / "bootstrap_repo_scaffold.py"
)
VERIFY_GENERATED = (
    ROOT
    / "skills"
    / "repo-scaffold-factory"
    / "scripts"
    / "verify_generated_scaffold.py"
)
CHECKLIST = (
    ROOT
    / "skills"
    / "repo-scaffold-factory"
    / "references"
    / "opencode-conformance-checklist.json"
)
AUDIT = ROOT / "skills" / "scafforge-audit" / "scripts" / "audit_repo_process.py"
REPAIR = (
    ROOT / "skills" / "scafforge-repair" / "scripts" / "apply_repo_process_repair.py"
)
PUBLIC_REPAIR = (
    ROOT / "skills" / "scafforge-repair" / "scripts" / "run_managed_repair.py"
)
REGENERATE = (
    ROOT / "skills" / "scafforge-repair" / "scripts" / "regenerate_restart_surfaces.py"
)
RECONCILE_REPAIR = (
    ROOT
    / "skills"
    / "scafforge-repair"
    / "scripts"
    / "reconcile_repair_follow_on.py"
)
PIVOT = ROOT / "skills" / "scafforge-pivot" / "scripts" / "plan_pivot.py"
PIVOT_RECORD = (
    ROOT / "skills" / "scafforge-pivot" / "scripts" / "record_pivot_stage_completion.py"
)
PIVOT_PUBLISH = (
    ROOT / "skills" / "scafforge-pivot" / "scripts" / "publish_pivot_surfaces.py"
)
PIVOT_APPLY = ROOT / "skills" / "scafforge-pivot" / "scripts" / "apply_pivot_lineage.py"
RECORD_REPAIR_STAGE = (
    ROOT
    / "skills"
    / "scafforge-repair"
    / "scripts"
    / "record_repair_stage_completion.py"
)
BOOTSTRAP_INPUT_FILES = (
    "project.godot",
    "export_presets.cfg",
    "opencode.jsonc",
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
    "android/scafforge-managed.json",
    ".opencode/meta/asset-pipeline-bootstrap.json",
)
BOOTSTRAP_ENVIRONMENT_KEYS = (
    "JAVA_HOME",
    "ANDROID_HOME",
    "ANDROID_SDK_ROOT",
    "BLENDER_MCP_BLENDER_EXECUTABLE",
)
BOOTSTRAP_HOST_PATH_CANDIDATES = {
    "android_debug_keystore": (
        str(Path.home() / ".android" / "debug.keystore"),
    ),
    "godot_export_templates": (
        str(Path.home() / ".local" / "share" / "godot" / "export_templates"),
    ),
    "android_sdk_default": (
        str(Path.home() / "Android" / "Sdk"),
        str(Path.home() / "Library" / "Android" / "sdk"),
        str(Path.home() / "AppData" / "Local" / "Android" / "Sdk"),
    ),
    "java_home_default": (
        "/usr/lib/jvm/default-java",
        "/usr/lib/jvm/java-21-openjdk-amd64",
        "/usr/lib/jvm/java-17-openjdk-amd64",
        "/usr/lib/jvm/java-11-openjdk-amd64",
    ),
}


def load_python_module(path: Path, module_name: str):
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def audit_reporting_module():
    audit_scripts = ROOT / "skills" / "scafforge-audit" / "scripts"
    if str(audit_scripts) not in sys.path:
        sys.path.insert(0, str(audit_scripts))
    return load_python_module(
        audit_scripts / "audit_reporting.py",
        "scafforge_smoke_audit_reporting",
    )


def package_commit() -> str:
    return audit_reporting_module().resolve_current_package_commit(ROOT)


def resolve_command(command: list[str]) -> list[str]:
    if not command:
        return command
    executable = command[0]
    if os.path.isabs(executable) or any(sep in executable for sep in ("\\", "/")):
        return command
    if os.name == "nt" and executable in {"python", "python3"}:
        return [sys.executable, *command[1:]]
    resolved = (
        shutil.which(executable)
        or shutil.which(f"{executable}.cmd")
        or shutil.which(f"{executable}.exe")
        or shutil.which(f"{executable}.bat")
    )
    if not resolved:
        return command
    return [resolved, *command[1:]]


def run(command: list[str], cwd: Path, *, env: dict[str, str] | None = None) -> None:
    resolved_command = resolve_command(command)
    result = subprocess.run(
        resolved_command, cwd=cwd, check=False, capture_output=True, text=True, env=env
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def run_json(
    command: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    allow_returncodes: set[int] | None = None,
) -> dict[str, Any]:
    resolved_command = resolve_command(command)
    result = subprocess.run(
        resolved_command, cwd=cwd, check=False, capture_output=True, text=True, env=env
    )
    allowed = allow_returncodes or {0}
    if result.returncode not in allowed:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Command did not return valid JSON: {' '.join(command)}\nSTDOUT:\n{result.stdout}"
        ) from exc


def write_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | 0o111)


def node_command() -> list[str]:
    node = shutil.which("node")
    if not node:
        raise RuntimeError(
            "Node.js is required to execute generated TypeScript tools in Scafforge smoke and integration tests."
        )
    result = subprocess.run(
        [node, "--version"], cwd=ROOT, check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Unable to determine Node.js version for generated tool execution:\nSTDERR:\n{result.stderr}"
        )
    match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", result.stdout.strip())
    if not match:
        raise RuntimeError(
            f"Unable to parse Node.js version output: {result.stdout.strip()!r}"
        )
    major, minor, patch = (int(part) for part in match.groups())
    if (major, minor, patch) < (22, 6, 0):
        raise RuntimeError(
            f"Generated TypeScript tool execution requires Node.js 22.6.0 or newer for --experimental-strip-types; found {result.stdout.strip()}."
        )
    return [node, "--experimental-strip-types"]


def write_runner(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_repo_json_value(repo_root: Path, relative_path: str, dotted_path: str) -> Any:
    """Read a value from a JSON file using a dotted path notation.

    Supports descending into objects by key and lists by numeric index.
    Raises RuntimeError with descriptive messages for common failure modes.
    """
    full_path = repo_root / relative_path
    try:
        raw_text = full_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeError(f"JSON file not found: {relative_path}") from exc
    except PermissionError as exc:
        raise RuntimeError(
            f"Permission denied reading JSON file: {relative_path}"
        ) from exc

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON in {relative_path} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    current: Any = payload
    for segment in dotted_path.split("."):
        if isinstance(current, list):
            if not segment.isdigit():
                raise RuntimeError(
                    f"Cannot descend into list with non-numeric path segment `{segment}` in `{dotted_path}`."
                )
            index = int(segment)
            try:
                current = current[index]
            except IndexError as exc:
                raise RuntimeError(
                    f"Path `{dotted_path}` is out of range for `{relative_path}` (list index {index} exceeds length {len(current)})."
                ) from exc
            continue
        if not isinstance(current, dict):
            raise RuntimeError(
                f"Path `{dotted_path}` in `{relative_path}` cannot descend into non-dict value at segment `{segment}`."
            )
        if segment not in current:
            available = ", ".join(sorted(current.keys())[:10])
            hint = (
                f" Available keys: {available}..."
                if len(current.keys()) > 10
                else f" Available keys: {available}"
            )
            raise RuntimeError(
                f"Path `{dotted_path}` segment `{segment}` does not exist in `{relative_path}`.{hint}"
            )
        current = current[segment]
    return current


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
        "const agent = process.env.SCAFFORGE_PLUGIN_AGENT || undefined",
        "const sessionID = process.env.SCAFFORGE_PLUGIN_SESSION_ID || undefined",
        "await hook({ tool: toolName, agent, sessionID }, { args: JSON.parse(rawArgs) })",
        "console.log(JSON.stringify({ ok: true }))",
    ]


def compute_bootstrap_fingerprint(dest: Path) -> str:
    def infer_android_sdk_path() -> str | None:
        explicit = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        if explicit and Path(explicit).exists():
            return explicit
        for candidate in BOOTSTRAP_HOST_PATH_CANDIDATES["android_sdk_default"]:
            if Path(candidate).exists():
                return candidate
        return None

    def infer_java_home() -> str | None:
        explicit = os.environ.get("JAVA_HOME")
        if explicit and Path(explicit).exists():
            return explicit
        java_bin = shutil.which("java")
        if java_bin:
            java_home = Path(os.path.realpath(java_bin)).parent.parent
            if java_home.exists():
                return str(java_home)
        for candidate in BOOTSTRAP_HOST_PATH_CANDIDATES["java_home_default"]:
            if Path(candidate).exists():
                return candidate
        return None

    def normalized_bootstrap_env(key: str) -> str:
        if key == "JAVA_HOME":
            return infer_java_home() or "<unset>"
        if key in {"ANDROID_HOME", "ANDROID_SDK_ROOT"}:
            return infer_android_sdk_path() or "<unset>"
        return os.environ.get(key) or "<unset>"

    digest = hashlib.sha256()
    input_files = sorted(path for path in BOOTSTRAP_INPUT_FILES if (dest / path).is_file())
    fingerprint_inputs = {
        "input_files": input_files,
        "repo_surfaces": {
            "project_godot": (dest / "project.godot").exists(),
            "export_presets": (dest / "export_presets.cfg").exists(),
            "android_support_surface": (dest / "android" / "scafforge-managed.json").exists(),
            "asset_pipeline_metadata": (dest / ".opencode" / "meta" / "asset-pipeline-bootstrap.json").exists(),
            "opencode_config": (dest / "opencode.jsonc").exists(),
        },
        "env": {
            key: normalized_bootstrap_env(key)
            for key in BOOTSTRAP_ENVIRONMENT_KEYS
        },
        "host_paths": {
            label: next((candidate for candidate in candidates if Path(candidate).exists()), "<missing>")
            for label, candidates in BOOTSTRAP_HOST_PATH_CANDIDATES.items()
        },
    }
    fingerprint_inputs["host_paths"]["java_home_inferred"] = infer_java_home() or "<missing>"
    digest.update(
        json.dumps(fingerprint_inputs, separators=(",", ":")).encode("utf-8")
    )
    digest.update(b"\x00")
    for relative in input_files:
        digest.update(relative.encode("utf-8"))
        digest.update(b"\x00")
        digest.update((dest / relative).read_bytes())
        digest.update(b"\x00")
    return digest.hexdigest()


def prepare_generated_tool_runtime(dest: Path) -> None:
    plugin_dir = dest / "node_modules" / "@opencode-ai" / "plugin"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "package.json").write_text(
        '{"name":"@opencode-ai/plugin","type":"module"}\n', encoding="utf-8"
    )
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
    for path in list((dest / ".opencode" / "tools").glob("*.ts")) + list(
        (dest / ".opencode" / "plugins").glob("*.ts")
    ):
        text = path.read_text(encoding="utf-8")
        rewritten = text.replace('from "../lib/workflow"', 'from "../lib/workflow.ts"')
        if rewritten != text:
            path.write_text(rewritten, encoding="utf-8")


def run_generated_tool(
    dest: Path, relative_tool_path: str, args: dict[str, object]
) -> dict[str, object]:
    prepare_generated_tool_runtime(dest)
    runner = dest / ".opencode" / "state" / "tool-runner.mjs"
    write_runner(runner, tool_runner_lines())
    env = os.environ.copy()
    env["SCAFFORGE_TOOL_PATH"] = str((dest / relative_tool_path).resolve())
    env["SCAFFORGE_TOOL_ARGS"] = json.dumps(args)
    return run_json([*node_command(), str(runner)], dest, env=env)


def run_generated_tool_error(
    dest: Path, relative_tool_path: str, args: dict[str, object]
) -> str:
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


def run_generated_plugin_before(
    dest: Path,
    relative_plugin_path: str,
    tool_name: str,
    args: dict[str, object],
    *,
    agent: str | None = None,
    session_id: str | None = None,
) -> None:
    prepare_generated_tool_runtime(dest)
    runner = dest / ".opencode" / "state" / "plugin-runner.mjs"
    write_runner(runner, plugin_runner_lines())
    env = os.environ.copy()
    env["SCAFFORGE_PLUGIN_PATH"] = str((dest / relative_plugin_path).resolve())
    env["SCAFFORGE_PLUGIN_TOOL"] = tool_name
    env["SCAFFORGE_PLUGIN_ARGS"] = json.dumps(args)
    if agent:
        env["SCAFFORGE_PLUGIN_AGENT"] = agent
    if session_id:
        env["SCAFFORGE_PLUGIN_SESSION_ID"] = session_id
    run([*node_command(), str(runner)], dest, env=env)


def run_generated_plugin_before_error(
    dest: Path,
    relative_plugin_path: str,
    tool_name: str,
    args: dict[str, object],
    *,
    agent: str | None = None,
    session_id: str | None = None,
) -> str:
    prepare_generated_tool_runtime(dest)
    runner = dest / ".opencode" / "state" / "plugin-runner.mjs"
    write_runner(runner, plugin_runner_lines())
    env = os.environ.copy()
    env["SCAFFORGE_PLUGIN_PATH"] = str((dest / relative_plugin_path).resolve())
    env["SCAFFORGE_PLUGIN_TOOL"] = tool_name
    env["SCAFFORGE_PLUGIN_ARGS"] = json.dumps(args)
    if agent:
        env["SCAFFORGE_PLUGIN_AGENT"] = agent
    if session_id:
        env["SCAFFORGE_PLUGIN_SESSION_ID"] = session_id
    result = subprocess.run(
        [*node_command(), str(runner)],
        cwd=dest,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode == 0:
        raise RuntimeError(
            f"Plugin hook unexpectedly succeeded: {relative_plugin_path} {tool_name}"
        )
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
