from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Callable

from shared_verifier_types import Finding
from target_completion import (
    debug_apk_path,
    declares_godot_android_target,
    deliverable_proof_path,
    expected_android_debug_apk_relpath,
    has_android_export_preset,
    has_android_support_surfaces,
    has_signing_ownership,
    load_manifest,
    release_lane_started_or_done,
    repo_claims_completion,
    requires_packaged_android_product,
)

# Directories excluded from repo-owned source file walks (dependency/build trees).
SCAN_EXCLUDED_DIRS: frozenset[str] = frozenset({
    ".git",
    "node_modules",
    ".venv",
    "venv",
    ".env",
    "dist",
    "build",
    "target",
    "vendor",
    ".tox",
    "site-packages",
    "__pycache__",
    ".cache",
    ".gradle",
    ".idea",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "coverage",
    ".coverage",
    "htmlcov",
})
RUNTIME_SOURCE_SUFFIXES: frozenset[str] = frozenset({
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".rs",
    ".go",
    ".gd",
    ".cs",
    ".java",
    ".kt",
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hpp",
})
RUNTIME_SOURCE_EXCLUDED_DIRS: frozenset[str] = frozenset({
    "test",
    "tests",
    "__tests__",
    "spec",
    "specs",
    "fixture",
    "fixtures",
    "example",
    "examples",
    "docs",
    "diagnosis",
    ".opencode",
})
PLACEHOLDER_RUNTIME_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Original patterns
    re.compile(r"\bTODO:\s*Implement (?:actual|full|real)\b", re.IGNORECASE),
    re.compile(r"\bnot (?:yet )?fully implemented\b", re.IGNORECASE),
    re.compile(r"\bplaceholder (?:response|implementation)\b", re.IGNORECASE),
    re.compile(r"\bstub(?:bed)?\b.+\brequires\b.+\bintegration\b", re.IGNORECASE),
    re.compile(r"\bwould send .+ configured model\b", re.IGNORECASE),
    # Natural-language stub phrases ("For now, return/echo/use/this/just ...")
    re.compile(r"\bFor now[,\s].{0,80}\b(return|echo|use|this|just|yield|produce|give)\b", re.IGNORECASE),
    # Trailing "for now" at end of phrase ("Return X ... for now")
    re.compile(r"\b(return|returns|returning|using|use)\b.{0,60}\bfor now\b", re.IGNORECASE),
    # Placeholder without specific noun following (e.g., "return a placeholder")
    re.compile(r"\b(return|returns|returning|using)\b.{0,40}\bplaceholder\b", re.IGNORECASE),
    # JSON/struct status fields set to not_implemented
    re.compile(r'"status"\s*:\s*"not_implemented"', re.IGNORECASE),
    re.compile(r"\bnot_implemented\b", re.IGNORECASE),
    # LLM integration pending phrase
    re.compile(r"\bintegration pending\b", re.IGNORECASE),
    # Rust unimplemented / todo macros in runtime paths
    re.compile(r"\btodo!\s*\(", re.IGNORECASE),
    re.compile(r"\bunimplemented!\s*\(", re.IGNORECASE),
    # Stub comment followed by explanation
    re.compile(r"//\s*Stub\s*[-–—]", re.IGNORECASE),
    # Empty-body placeholders that explicitly say so
    re.compile(r"\bcoming soon\b", re.IGNORECASE),
    # Return empty collection with an explanatory comment
    re.compile(r"\breturn\s+(?:vec!\[\]|Vec::new\(\)|HashMap::new\(\)|BTreeMap::new\(\)|Ok\(vec!\[\]\)|Ok\(Vec::new\(\)\))\s*[;\s]*//", re.IGNORECASE),
)
RUNTIME_PLACEHOLDER_PATH_TOKENS: frozenset[str] = frozenset({
    "agent",
    "agents",
    "ask",
    "chat",
    "checkpoint",
    "cli",
    "command",
    "commands",
    "discovery",
    "dispatch",
    "edit",
    "executor",
    "handlers",
    "ide",
    "inference",
    "llm",
    "manager",
    "mcp",
    "mode",
    "protocol",
    "provider",
    "providers",
    "resilience",
    "runtime",
    "search",
    "server",
    "session",
    "skills",
    "state",
    "streaming",
    "suggest",
    "tool",
    "tools",
    "tui",
})

SMOKE_PASS_RESULT_PATTERN = re.compile(r"Overall Result:\s*PASS\b", re.IGNORECASE)
SMOKE_FAILURE_CLASSIFICATION_PATTERN = re.compile(r"^- failure_classification:\s*([a-z_]+)\s*$", re.IGNORECASE | re.MULTILINE)
SMOKE_EXIT_CODE_PATTERN = re.compile(r"^- exit_code:\s*(-?\d+)\s*$", re.MULTILINE)
SMOKE_GODOT_ERROR_PATTERN = re.compile(
    r'(?:SCRIPT ERROR:\s*)?Parse Error:|ERROR:\s*Failed to load script|syntax error|parse error|failed to load script|'
    r'not declared in the current scope|not found in base self|unexpected token|missing language argument|unterminated|unmatched quote',
    re.IGNORECASE,
)
SMOKE_PASS_SAFE_FAILURE_CLASSIFICATIONS: frozenset[str] = frozenset({"none", "null", "undefined", "n/a"})
GODOT_RESOURCE_PATH_PATTERN = re.compile(r'res://([^"\r\n]+)')
GODOT_SIGNAL_CONNECTION_METHOD_PATTERN = re.compile(r'^\[connection\s+[^\]]*method="([^"]+)"', re.MULTILINE)
GODOT_EXT_RESOURCE_PATTERN = re.compile(r'^\[ext_resource\s+[^\]]*path="res://([^"]+)"[^\]]*id=(?:"([^"]+)"|([0-9]+))', re.MULTILINE)
GODOT_SCRIPT_EXT_RESOURCE_PATTERN = re.compile(r'script\s*=\s*ExtResource\(\s*"?(?P<id>[^"\)\s]+)"?\s*\)')
GODOT_SIGNAL_HANDLER_PATTERN = re.compile(r'^\s*func\s+(_on_[A-Za-z0-9_]+)\s*\(', re.MULTILINE)
GODOT_METHOD_DEF_PATTERN = re.compile(r'^\s*func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', re.MULTILINE)
GODOT_VAR_DECL_PATTERN = re.compile(r'^\s*(?:@export\s+)?var\s+([A-Za-z_][A-Za-z0-9_]*)\b', re.MULTILINE)
GODOT_UID_WARNING_PATTERN = re.compile(r'WARNING:\s+.+invalid UID:.+using text path instead:.+', re.IGNORECASE)
GODOT_SCENE_SIGNAL_SUFFIXES: frozenset[str] = frozenset({
    "pressed",
    "released",
    "body_entered",
    "body_exited",
    "area_entered",
    "area_exited",
    "animation_finished",
    "button_down",
    "button_up",
    "timeout",
    "toggled",
    "gui_input",
    "input_event",
    "mouse_entered",
    "mouse_exited",
})
GODOT_BASE_METHOD_DISALLOWED_EXTENDS: dict[str, frozenset[str]] = {
    "draw_circle": frozenset({"CanvasLayer", "Node"}),
    "queue_redraw": frozenset({"CanvasLayer", "Node"}),
    "get_viewport_rect": frozenset({"CanvasLayer", "Node"}),
}
GODOT_UI_PATH_HINTS: tuple[str, ...] = ("/ui/", "hud", "game_over", "overlay", "status")
GODOT_SINGLETON_MUTATOR_PREFIXES: tuple[str, ...] = (
    "set_",
    "add_",
    "update_",
    "record_",
    "increment_",
    "advance_",
    "mark_",
)
BLENDER_MUTATING_TOOLS: frozenset[str] = frozenset({
    "project_initialize",
    "addon_configure",
    "scene_batch_edit",
    "modifier_stack_edit",
    "mesh_edit_batch",
    "uv_workflow",
    "material_pbr_build",
    "node_graph_build",
    "bake_maps",
    "armature_animation",
    "simulation_cache",
    "asset_publish",
    "import_asset",
    "export_asset",
    "blender_python",
})


def iter_source_files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    """Iterate repo-owned source files, skipping dependency and build trees."""
    results: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in suffixes:
            # Skip any file whose path passes through an excluded directory
            relative_parts = path.relative_to(root).parts
            if any(part in SCAN_EXCLUDED_DIRS for part in relative_parts[:-1]):
                continue
            results.append(path)
    return results


def is_runtime_source_candidate(path: Path, root: Path) -> bool:
    relative_parts = path.relative_to(root).parts
    if any(part in RUNTIME_SOURCE_EXCLUDED_DIRS for part in relative_parts[:-1]):
        return False
    lowered_name = path.name.lower()
    if (
        lowered_name.endswith("_test.go")
        or ".spec." in lowered_name
        or ".test." in lowered_name
        or lowered_name.startswith("test_")
    ):
        return False
    return path.suffix in RUNTIME_SOURCE_SUFFIXES


def runtime_placeholder_hits(root: Path, ctx: ExecutionSurfaceAuditContext) -> list[str]:
    hits: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if any(part in SCAN_EXCLUDED_DIRS for part in relative_parts[:-1]):
            continue
        if not is_runtime_source_candidate(path, root):
            continue
        lowered_parts = {part.lower() for part in relative_parts}
        lowered_name = path.name.lower()
        if not (
            lowered_parts & RUNTIME_PLACEHOLDER_PATH_TOKENS
            or lowered_name in {"main.rs", "main.py", "main.ts", "main.js", "lib.rs"}
        ):
            continue
        text = ctx.read_text(path)
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            for pattern in PLACEHOLDER_RUNTIME_PATTERNS:
                if not pattern.search(stripped):
                    continue
                hits.append(
                    f"{ctx.normalize_path(path, root)}:{line_number}: {stripped[:160]}"
                )
                break
    return hits


def iter_godot_resource_paths(text: str) -> list[str]:
    seen: set[str] = set()
    paths: list[str] = []
    for match in GODOT_RESOURCE_PATH_PATTERN.finditer(text):
        resource_path = match.group(1).strip().rstrip(",)]}")
        if not resource_path or resource_path in seen:
            continue
        seen.add(resource_path)
        paths.append(resource_path)
    return paths


def parse_godot_scene_ext_resources(text: str) -> dict[str, str]:
    resources: dict[str, str] = {}
    for match in GODOT_EXT_RESOURCE_PATTERN.finditer(text):
        resource_id = match.group(2) or match.group(3)
        if resource_id:
            resources[resource_id] = match.group(1)
    return resources


def parse_godot_autoloads(text: str) -> dict[str, str]:
    autoloads: dict[str, str] = {}
    in_autoload_section = False
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_autoload_section = stripped == "[autoload]"
            continue
        if not in_autoload_section or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        match = re.search(r'\*?res://([^"\n]+)', value)
        if match is None:
            continue
        autoloads[name.strip().strip('"')] = match.group(1).strip()
    return autoloads


def parse_godot_scene_script_paths(text: str) -> list[str]:
    ext_resources = parse_godot_scene_ext_resources(text)
    paths: list[str] = []
    seen: set[str] = set()
    for match in GODOT_SCRIPT_EXT_RESOURCE_PATTERN.finditer(text):
        resource_id = match.group("id")
        resource_path = ext_resources.get(resource_id)
        if not resource_path or resource_path in seen:
            continue
        seen.add(resource_path)
        paths.append(resource_path)
    return paths


def parse_godot_scene_connection_methods(text: str) -> set[str]:
    return {match.group(1) for match in GODOT_SIGNAL_CONNECTION_METHOD_PATTERN.finditer(text)}


def script_declared_signal_handlers(text: str) -> list[str]:
    handlers: list[str] = []
    seen: set[str] = set()
    for match in GODOT_SIGNAL_HANDLER_PATTERN.finditer(text):
        handler = match.group(1)
        if not any(handler.endswith(f"_{suffix}") for suffix in GODOT_SCENE_SIGNAL_SUFFIXES):
            continue
        if handler in seen:
            continue
        seen.add(handler)
        handlers.append(handler)
    return handlers


def script_dynamically_connects_handler(text: str, handler: str) -> bool:
    escaped = re.escape(handler)
    return (
        re.search(rf'Callable\(\s*self\s*,\s*"{escaped}"\s*\)', text) is not None
        or re.search(rf'connect\([^\n]*"{escaped}"', text) is not None
        or re.search(rf'connect\([^\n]*{escaped}', text) is not None
    )


def gdscript_declared_base_type(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("extends "):
            continue
        target = stripped[len("extends "):].strip()
        if not target or target.startswith('"res://'):
            return None
        return target.split(".", 1)[0]
    return None


def gdscript_declared_methods(text: str) -> set[str]:
    return {match.group(1) for match in GODOT_METHOD_DEF_PATTERN.finditer(text)}


def gdscript_declared_vars(text: str) -> set[str]:
    return {match.group(1) for match in GODOT_VAR_DECL_PATTERN.finditer(text)}


def _gdscript_without_method_definitions(text: str, method_name: str) -> str:
    return re.sub(
        rf'^\s*func\s+{re.escape(method_name)}\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:\s*$',
        "",
        text,
        flags=re.MULTILINE,
    )


def _iter_repo_files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    return iter_source_files(root, suffixes)


def _godot_method_referenced_elsewhere(
    root: Path,
    ctx: ExecutionSurfaceAuditContext,
    *,
    method_name: str,
    definition_path: Path,
) -> bool:
    token_pattern = re.compile(rf'\b{re.escape(method_name)}\s*\(')
    for path in _iter_repo_files(root, (".gd",)):
        text = ctx.read_text(path)
        if path == definition_path:
            text = _gdscript_without_method_definitions(text, method_name)
        if token_pattern.search(text):
            return True
        if re.search(rf'Callable\([^\n]*"{re.escape(method_name)}"', text) is not None:
            return True
    for path in _iter_repo_files(root, (".tscn",)):
        text = ctx.read_text(path)
        if re.search(rf'method="{re.escape(method_name)}"', text) is not None:
            return True
    return False


def _field_mutator_method_candidates(field_name: str, methods: set[str]) -> set[str]:
    candidates: set[str] = set()
    base_fields = {field_name}
    if field_name.startswith("max_") and len(field_name) > 4:
        base_fields.add(field_name[4:])
    for base in base_fields:
        for prefix in GODOT_SINGLETON_MUTATOR_PREFIXES:
            candidate = f"{prefix}{base}"
            if candidate in methods:
                candidates.add(candidate)
    return candidates


def _is_trivial_state_singleton(text: str) -> bool:
    if re.search(r'^\s*signal\s+', text, re.MULTILINE):
        return False
    if "connect(" in text or "await " in text or "yield(" in text:
        return False
    if re.search(r'^\s*func\s+_(?:process|physics_process|input|unhandled_input)\s*\(', text, re.MULTILINE):
        return False
    return True


def _godot_wave_start_gap(root: Path, ctx: ExecutionSurfaceAuditContext) -> tuple[list[str], list[Path]]:
    evidence: list[str] = []
    files: list[Path] = []
    for path in _iter_repo_files(root, (".gd",)):
        text = ctx.read_text(path)
        if re.search(r'^\s*signal\s+wave_started\b', text, re.MULTILINE) is None:
            continue
        if re.search(r'^\s*func\s+start_wave\s*\(', text, re.MULTILINE) is None:
            continue
        if _godot_method_referenced_elsewhere(root, ctx, method_name="start_wave", definition_path=path):
            continue
        files.append(path)
        evidence.append(
            f"{ctx.normalize_path(path, root)} defines signal wave_started and func start_wave(), but no runtime script or scene invokes start_wave()."
        )
    return evidence, files


def _godot_game_over_transition_gap(root: Path, ctx: ExecutionSurfaceAuditContext) -> tuple[list[str], list[Path]]:
    game_over_scenes = [
        path
        for path in _iter_repo_files(root, (".tscn",))
        if "game_over" in path.name.lower()
    ]
    if not game_over_scenes:
        return [], []
    has_game_over_transition = False
    death_reload_evidence: list[str] = []
    files: list[Path] = []
    for path in _iter_repo_files(root, (".gd",)):
        text = ctx.read_text(path)
        if re.search(r'change_scene_to_(?:file|packed)\s*\([^\n]*game_over', text, re.IGNORECASE):
            has_game_over_transition = True
        if "reload_current_scene(" not in text:
            continue
        if re.search(r'func\s+[_A-Za-z0-9]*(?:die|death|fail|defeat|lose|game_over)[A-Za-z0-9_]*\s*\(', text, re.IGNORECASE) is None and "died.emit()" not in text:
            continue
        files.append(path)
        death_reload_evidence.append(
            f"{ctx.normalize_path(path, root)} reloads the current scene from a death/fail path while a repo-local game_over scene exists."
        )
    if not death_reload_evidence or has_game_over_transition:
        return [], []
    return death_reload_evidence, [*game_over_scenes, *files]


def _godot_singleton_state_gap(root: Path, ctx: ExecutionSurfaceAuditContext, project_text: str) -> tuple[list[str], list[Path]]:
    evidence: list[str] = []
    files: list[Path] = []
    for singleton_name, rel_path in parse_godot_autoloads(project_text).items():
        singleton_path = root / rel_path
        if not singleton_path.exists():
            continue
        singleton_text = ctx.read_text(singleton_path)
        if not _is_trivial_state_singleton(singleton_text):
            continue
        fields = {field for field in gdscript_declared_vars(singleton_text) if not field.startswith("_")}
        methods = {method for method in gdscript_declared_methods(singleton_text) if not method.startswith("_")}
        if not fields or not methods:
            continue
        ui_reads: dict[str, list[str]] = {}
        direct_writes: set[str] = set()
        method_calls: set[str] = set()
        impacted_paths: list[Path] = [singleton_path]
        for path in _iter_repo_files(root, (".gd",)):
            if path == singleton_path:
                continue
            text = ctx.read_text(path)
            normalized = ctx.normalize_path(path, root)
            is_ui_surface = any(token in normalized.lower() for token in GODOT_UI_PATH_HINTS)
            for field in fields:
                if re.search(rf'\b{re.escape(singleton_name)}\.{re.escape(field)}\s*=', text):
                    direct_writes.add(field)
                if is_ui_surface and re.search(rf'\b{re.escape(singleton_name)}\.{re.escape(field)}\b', text):
                    ui_reads.setdefault(field, []).append(normalized)
                    impacted_paths.append(path)
            for method in methods:
                if re.search(rf'\b{re.escape(singleton_name)}\.{re.escape(method)}\s*\(', text):
                    method_calls.add(method)
        stale_fields: list[str] = []
        for field_name, read_locations in ui_reads.items():
            if field_name in direct_writes:
                continue
            if _field_mutator_method_candidates(field_name, methods) & method_calls:
                continue
            stale_fields.append(field_name)
            evidence.append(
                f"{singleton_name}.{field_name} is read by player-facing UI ({', '.join(read_locations[:2])}), but no runtime script updates it or calls a matching {singleton_name} mutator."
            )
        if stale_fields:
            files.extend(impacted_paths)
    return evidence, files


@dataclass(frozen=True)
class ExecutionSurfaceAuditContext:
    read_text: Callable[[Path], str]
    read_json: Callable[[Path], Any]
    normalize_path: Callable[[Path, Path], str]
    expected_uv_dependency_args: Callable[[Path], tuple[list[str], str | None]]
    add_finding: Callable[[list[Finding], Finding], None]
    matching_lines: Callable[[str, tuple[str, ...]], list[str]]
    repo_uses_uv: Callable[[Path, str], bool]
    repo_has_dev_extra: Callable[[Path], bool]
    repo_mentions_patterns: Callable[[Path, tuple[str, ...]], str | None]
    detect_python: Callable[[Path], str | None]
    detect_pytest_command: Callable[[Path], list[str] | None]
    run_command: Callable[[list[str], Path, int], tuple[int, str]]
    is_venv_broken: Callable[[Path], str | None]


def repo_venv_executable_candidates(root: Path, executable: str) -> list[Path]:
    names = [executable] if executable.lower().endswith(".exe") else [executable, f"{executable}.exe"]
    candidates: list[Path] = []
    for directory in (root / ".venv" / "bin", root / ".venv" / "Scripts"):
        for name in names:
            candidate = directory / name
            if candidate not in candidates:
                candidates.append(candidate)
    return candidates


def existing_repo_venv_executable(root: Path, executable: str) -> Path | None:
    for candidate in repo_venv_executable_candidates(root, executable):
        if candidate.exists():
            return candidate
    return None


def parse_bootstrap_artifact_commands(text: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"^- command: `([^`]+)`", text, re.MULTILINE)]


def parse_bootstrap_missing_executables(text: str) -> list[str]:
    hits = [match.group(1).strip() for match in re.finditer(r"^- missing_executable: (.+)$", text, re.MULTILINE)]
    return [value for value in hits if value and value.lower() != "none"]


def bootstrap_artifact_paths(root: Path, proof_artifact: Path | None) -> list[Path]:
    paths: list[Path] = []
    if proof_artifact and proof_artifact.exists():
        paths.append(proof_artifact)
    history_root = root / ".opencode" / "state" / "artifacts" / "history"
    if history_root.exists():
        paths.extend(sorted(history_root.rglob("*environment-bootstrap.md")))
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(path)
    return deduped


def latest_uv_sync_command(text: str) -> str | None:
    for command in parse_bootstrap_artifact_commands(text):
        if command.startswith("uv sync"):
            return command
    return None


def command_contains_expected_args(command: str, expected_args: list[str]) -> bool:
    if not expected_args:
        return True
    return all(token in command for token in expected_args)


def audit_bootstrap_command_layout_mismatch(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    tool_path = root / ".opencode" / "tools" / "environment_bootstrap.ts"
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    pyproject_path = root / "pyproject.toml"
    if not tool_path.exists() or not workflow_path.exists() or not pyproject_path.exists():
        return

    tool_text = ctx.read_text(tool_path)
    workflow = ctx.read_json(workflow_path)
    workflow_bootstrap = workflow.get("bootstrap") if isinstance(workflow, dict) and isinstance(workflow.get("bootstrap"), dict) else {}
    proof_artifact_value = workflow_bootstrap.get("proof_artifact") if isinstance(workflow_bootstrap, dict) else None
    proof_artifact = root / str(proof_artifact_value) if isinstance(proof_artifact_value, str) and proof_artifact_value else None
    proof_text = ctx.read_text(proof_artifact) if proof_artifact else ""
    if not proof_text:
        return

    expected_args, dependency_layout = ctx.expected_uv_dependency_args(root)
    if not expected_args or not dependency_layout:
        return

    sync_command = latest_uv_sync_command(proof_text)
    if not sync_command or command_contains_expected_args(sync_command, expected_args):
        return

    missing_executables = parse_bootstrap_missing_executables(proof_text)
    missing_tool_names = {Path(path).name for path in missing_executables}
    if not ({"pytest", "ruff"} & missing_tool_names):
        return

    artifact_paths = bootstrap_artifact_paths(root, proof_artifact)
    repeated_traces = 0
    for artifact_path in artifact_paths:
        artifact_text = ctx.read_text(artifact_path)
        if latest_uv_sync_command(artifact_text) == sync_command:
            repeated_traces += 1

    affected_files = [
        ctx.normalize_path(pyproject_path, root),
        ctx.normalize_path(tool_path, root),
        ctx.normalize_path(workflow_path, root),
    ]
    if proof_artifact and proof_artifact.exists():
        affected_files.append(ctx.normalize_path(proof_artifact, root))
    legacy_section_parser = "(?:\\\\n\\\\[|$)" in tool_text and "function hasSectionValue" in tool_text
    evidence = [
        f"{ctx.normalize_path(pyproject_path, root)} declares {dependency_layout}, so uv bootstrap should include {' '.join(expected_args)}.",
        f"Latest bootstrap artifact executed `{sync_command}` instead of a dependency-layout-aware uv sync command.",
        f"{ctx.normalize_path(workflow_path, root)} records bootstrap.status = {workflow_bootstrap.get('status', 'missing')}.",
    ]
    if missing_executables:
        evidence.append(f"Latest bootstrap artifact still reports missing validation tools: {', '.join(missing_executables[:3])}.")
    if repeated_traces > 1:
        evidence.append(f"Bootstrap history repeats the same incompatible uv sync trace across {repeated_traces} artifacts.")
    if legacy_section_parser:
        evidence.append(f"{ctx.normalize_path(tool_path, root)} still uses the legacy TOML section parser that can miss multiline optional dependency sections.")

    ctx.add_finding(
        findings,
        Finding(
            code="BOOT002",
            severity="error",
            problem="The managed bootstrap tool executed a uv sync command that contradicts the repo's declared dependency layout, so validation tools remain missing after bootstrap.",
            root_cause="`environment_bootstrap` did not translate this repo's optional dependency layout into the uv flags required to install test and lint tooling. Re-running the same command trace cannot converge while the managed bootstrap surface still omits those flags.",
            files=list(dict.fromkeys(affected_files)),
            safer_pattern="Correlate `pyproject.toml`, the latest bootstrap artifact command trace, and `environment_bootstrap.ts`; if the repo layout requires `--extra dev`, `--group dev`, or `--all-extras`, treat any bootstrap run that omits those flags as a managed bootstrap defect and repair the tool before retrying.",
            evidence=evidence[:8],
            provenance="script",
        ),
    )


def audit_bootstrap_deadlock(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    tool_path = root / ".opencode" / "tools" / "environment_bootstrap.ts"
    if not tool_path.exists():
        return

    tool_text = ctx.read_text(tool_path)
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    workflow = ctx.read_json(workflow_path)
    workflow_bootstrap = workflow.get("bootstrap") if isinstance(workflow, dict) and isinstance(workflow.get("bootstrap"), dict) else {}
    proof_artifact_value = workflow_bootstrap.get("proof_artifact") if isinstance(workflow_bootstrap, dict) else None
    proof_artifact = root / str(proof_artifact_value) if isinstance(proof_artifact_value, str) and proof_artifact_value else None
    proof_text = ctx.read_text(proof_artifact) if proof_artifact else ""

    pyvenv_text = ctx.read_text(root / ".venv" / "pyvenv.cfg")
    has_uv_lock = (root / "uv.lock").exists()
    uv_managed_venv = bool(re.search(r"^uv\s*=", pyvenv_text, re.MULTILINE))
    hardcoded_system_pip = 'argv: ["python3", "-m", "pip"' in tool_text
    pip_deadlock = "No module named pip" in proof_text
    bootstrap_failed = isinstance(workflow_bootstrap, dict) and workflow_bootstrap.get("status") == "failed"

    current_python3_pip_missing = False
    rc, output = ctx.run_command(["python3", "-m", "pip", "--version"], root, 10)
    if rc != 0 and "No module named pip" in output:
        current_python3_pip_missing = True

    signals = has_uv_lock or uv_managed_venv
    bootstrap_contract_mismatch = hardcoded_system_pip and (signals or current_python3_pip_missing)
    if not bootstrap_contract_mismatch and not pip_deadlock:
        return

    affected_files = [ctx.normalize_path(tool_path, root)]
    evidence: list[str] = []
    if has_uv_lock:
        evidence.append("Repo contains uv.lock, so Python bootstrap should prefer uv-managed sync.")
    if uv_managed_venv:
        evidence.append("Repo-local .venv/pyvenv.cfg records a uv-managed virtual environment.")
    if hardcoded_system_pip:
        evidence.append(f"{ctx.normalize_path(tool_path, root)} still hardcodes bare `python3 -m pip` bootstrap commands.")
    if current_python3_pip_missing:
        evidence.append("Current machine reports `python3 -m pip --version` -> No module named pip.")
    if bootstrap_failed:
        evidence.append(f"{ctx.normalize_path(workflow_path, root)} records bootstrap.status = failed.")
        affected_files.append(ctx.normalize_path(workflow_path, root))
    if pip_deadlock and proof_artifact:
        affected_files.append(ctx.normalize_path(proof_artifact, root))
        evidence.extend(
            [
                f"{ctx.normalize_path(proof_artifact, root)} shows bootstrap failed while reporting `No module named pip`.",
                *ctx.matching_lines(proof_text, (r"python3 -m pip install", r"No module named pip", r"Missing Prerequisites", r"- None")),
            ]
        )

    ctx.add_finding(
        findings,
        Finding(
            code="BOOT001",
            severity="error",
            problem="The generated bootstrap contract cannot ready this repo on the current machine, so write-capable workflow stages can deadlock before source fixes start.",
            root_cause="The managed `environment_bootstrap` surface still relies on bare `python3 -m pip` or otherwise ignores repo-local uv/.venv signals. When global pip is absent, bootstrap fails even if the repo has a usable project virtual environment or uv lockfile.",
            files=list(dict.fromkeys(affected_files)),
            safer_pattern="Prefer repo-native bootstrap (`uv sync --locked` for uv repos; otherwise repo-local `.venv` plus its Python interpreter), record missing prerequisites accurately, and keep bootstrap readiness separate from source import/test failures.",
            evidence=evidence[:8],
            provenance="script",
        ),
    )


def audit_smoke_test_contract(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    tool_path = root / ".opencode" / "tools" / "smoke_test.ts"
    if not tool_path.exists():
        return

    text = ctx.read_text(tool_path)
    has_repo_python = (root / "uv.lock").exists() or existing_repo_venv_executable(root, "python") is not None
    hardcoded_system_pytest = 'argv: ["python3", "-m", "pytest"]' in text
    if not (has_repo_python and hardcoded_system_pytest):
        return

    evidence = []
    if (root / "uv.lock").exists():
        evidence.append("Repo contains uv.lock, so smoke tests should prefer `uv run python -m pytest`.")
    repo_python = existing_repo_venv_executable(root, "python")
    if repo_python is not None:
        evidence.append(f"Repo contains {ctx.normalize_path(repo_python, root)}, so smoke tests can use the repo-local virtualenv directly.")
    evidence.append(f"{ctx.normalize_path(tool_path, root)} still hardcodes `python3 -m pytest` for detected Python test surfaces.")

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW001",
            severity="error",
            problem="The managed smoke-test tool ignores repo-managed Python execution and can deadlock closeout on uv or .venv repos.",
            root_cause="The generated smoke-test contract still hardcodes system `python3 -m pytest` instead of selecting repo-native Python execution when `uv.lock` or `.venv` is present.",
            files=[ctx.normalize_path(tool_path, root)],
            safer_pattern="Prefer explicit project smoke-test overrides first, then `uv run python -m pytest` for uv-managed repos, then the repo-local `.venv` Python interpreter before falling back to system python.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_bootstrap_freshness_contract(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    workflow = ctx.read_json(workflow_path)
    if not isinstance(workflow, dict):
        return
    bootstrap = workflow.get("bootstrap")
    if not isinstance(bootstrap, dict):
        return
    fingerprint = str(bootstrap.get("environment_fingerprint", "")).strip()
    if fingerprint != "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855":
        return
    repo_surfaces = [
        path for path in (
            root / "project.godot",
            root / "export_presets.cfg",
            root / "opencode.jsonc",
            root / ".opencode" / "meta" / "bootstrap-provenance.json",
        )
        if path.exists()
    ]
    if not repo_surfaces:
        return
    evidence = [
        f"{ctx.normalize_path(workflow_path, root)} records bootstrap.environment_fingerprint = {fingerprint}.",
        "The recorded fingerprint is the empty-hash sentinel, which means bootstrap freshness was computed from no meaningful inputs.",
    ]
    proof_artifact = bootstrap.get("proof_artifact")
    if isinstance(proof_artifact, str) and proof_artifact.strip():
        evidence.append(f"Latest bootstrap proof artifact: {proof_artifact.strip()}.")
    evidence.extend(
        f"Repo surface present despite empty bootstrap fingerprint: {ctx.normalize_path(path, root)}"
        for path in repo_surfaces[:4]
    )
    ctx.add_finding(
        findings,
        Finding(
            code="BOOT003",
            severity="error",
            problem="The generated bootstrap freshness contract cannot detect host drift for this repo.",
            root_cause="The recorded bootstrap fingerprint is the empty-hash sentinel even though the repo exposes meaningful bootstrap surfaces. That means the generated workflow was hashing an incomplete input set and can leave bootstrap status stale after moving machines or fixing host prerequisites.",
            files=[ctx.normalize_path(workflow_path, root), *[ctx.normalize_path(path, root) for path in repo_surfaces[:3]]],
            safer_pattern="Hash stack-sensitive repo surfaces plus host-side prerequisite signals so bootstrap becomes stale when the machine setup changes, then rerun environment_bootstrap after package repair installs the stronger freshness model.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_smoke_test_override_contract(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    tool_path = root / ".opencode" / "tools" / "smoke_test.ts"
    if not tool_path.exists():
        return

    text = ctx.read_text(tool_path)
    evidence: list[str] = []
    if 'argv: args.command_override' in text:
        evidence.append(f"{ctx.normalize_path(tool_path, root)} passes command_override directly into argv without parsing shell-style overrides.")
    if "parseCommandOverride" not in text:
        evidence.append(f"{ctx.normalize_path(tool_path, root)} does not normalize one-item shell-style overrides before execution.")
    if "env_overrides" not in text:
        evidence.append(f"{ctx.normalize_path(tool_path, root)} does not peel leading KEY=VALUE tokens into spawn environment overrides.")
    if "tokenizeCommandString" not in text:
        evidence.append(f"{ctx.normalize_path(tool_path, root)} does not tokenize one-item shell-style overrides through a quote-aware parser.")
    if "syntax_error" not in text:
        evidence.append(f"{ctx.normalize_path(tool_path, root)} does not classify quote or shell-shape failures as syntax_error instead of generic command failure.")

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW016",
            severity="error",
            problem="The managed smoke-test override contract can fail before the requested smoke command even starts.",
            root_cause="The generated `smoke_test` tool passes `command_override` directly into `spawn()` argv and does not separate shell-style environment assignments like `UV_CACHE_DIR=...` from the executable. Valid repo-standard override commands can therefore misfire as `ENOENT` instead of running the intended smoke check.",
            files=[ctx.normalize_path(tool_path, root)],
            safer_pattern="Parse one-item shell-style overrides into argv, treat leading `KEY=VALUE` tokens as environment overrides, and report malformed overrides as configuration errors instead of misclassifying them as runtime environment failures.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_smoke_test_acceptance_contract(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    tool_path = root / ".opencode" / "tools" / "smoke_test.ts"
    if not tool_path.exists():
        return

    text = ctx.read_text(tool_path)
    evidence: list[str] = []
    if "inferAcceptanceSmokeCommands" not in text:
        evidence.append(f"{ctx.normalize_path(tool_path, root)} does not derive smoke commands from ticket acceptance criteria.")
    if "ticket.acceptance" not in text:
        evidence.append(f"{ctx.normalize_path(tool_path, root)} does not inspect `ticket.acceptance` before falling back to generic smoke command detection.")
    if "Ticket acceptance criteria define an explicit smoke-test command." not in text:
        evidence.append(f"{ctx.normalize_path(tool_path, root)} does not record acceptance-backed smoke commands as the canonical reason for execution.")

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW017",
            severity="error",
            problem="The managed smoke-test tool can ignore ticket-specific acceptance commands and fall back to heuristic smoke scope.",
            root_cause="The generated `smoke_test` tool does not inspect the ticket's explicit acceptance commands before falling back to generic repo-level smoke detection. That lets the coordinator run a broader full-suite command or an ad hoc narrowed subset that does not match the ticket's canonical smoke requirement.",
            files=[ctx.normalize_path(tool_path, root)],
            safer_pattern="Infer smoke commands from explicit ticket acceptance criteria first, treat those commands as canonical smoke scope, and only fall back to generic repo-level detection when no acceptance-backed smoke command exists.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_environment_prerequisites(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    has_python_project = (root / "pyproject.toml").exists() or (root / "setup.py").exists()
    tests_dir = root / "tests"
    environment_bootstrap = root / ".opencode" / "tools" / "environment_bootstrap.ts"
    smoke_test = root / ".opencode" / "tools" / "smoke_test.ts"
    bootstrap_text = ctx.read_text(environment_bootstrap) + "\n" + ctx.read_text(smoke_test)
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    workflow = ctx.read_json(workflow_path)
    workflow_bootstrap = workflow.get("bootstrap") if isinstance(workflow, dict) and isinstance(workflow.get("bootstrap"), dict) else {}

    if has_python_project and ctx.detect_python(root) is None:
        ctx.add_finding(
            findings,
            Finding(
                code="ENV001",
                severity="error",
                problem="The current machine does not expose a usable Python interpreter for this repo's runtime and verification flow.",
                root_cause="The repo is Python-backed, but the host environment cannot run repo-local `.venv` Python or a system `python3`/`python`, so audit and repair cannot execute import or test verification.",
                files=[path for path in (ctx.normalize_path(environment_bootstrap, root), ctx.normalize_path(smoke_test, root)) if (root / path).exists()],
                safer_pattern="Ensure the host can run the repo-local `.venv` Python interpreter or a system Python before treating audit or repair verification as complete.",
                evidence=[
                    "No repo-local `.venv` Python interpreter was detected.",
                    "Neither `python3 --version` nor `python --version` succeeded on this machine.",
                ],
                provenance="script",
            ),
        )

    if has_python_project and tests_dir.exists() and ctx.detect_pytest_command(root) is None:
        uv_repo = ctx.repo_uses_uv(root, bootstrap_text)
        uv_available = shutil.which("uv") is not None
        bootstrap_status = str(workflow_bootstrap.get("status", "")).strip() if isinstance(workflow_bootstrap, dict) else ""
        proof_artifact_value = workflow_bootstrap.get("proof_artifact") if isinstance(workflow_bootstrap, dict) else None
        proof_artifact = root / str(proof_artifact_value) if isinstance(proof_artifact_value, str) and proof_artifact_value else None
        pyproject_has_dev = ctx.repo_has_dev_extra(root)
        existing_bootstrap_findings = {finding.code for finding in findings if finding.code.startswith("BOOT")}
        if uv_repo and uv_available:
            if "BOOT001" in existing_bootstrap_findings or "BOOT002" in existing_bootstrap_findings:
                return
            files = [
                ctx.normalize_path(tests_dir, root),
                ctx.normalize_path(environment_bootstrap, root),
                ctx.normalize_path(workflow_path, root),
            ]
            evidence = [
                f"{ctx.normalize_path(tests_dir, root)} exists and requires executable test verification.",
                "The repo is uv-managed and `uv` is available on the current machine.",
                f"{ctx.normalize_path(workflow_path, root)} records bootstrap.status = {bootstrap_status or 'missing'}.",
                "No repo-local or global pytest command could be resolved for this repo.",
            ]
            if pyproject_has_dev:
                evidence.append("pyproject.toml defines `[project.optional-dependencies].dev`, so bootstrap should restore pytest through the repo-local dev environment.")
            if proof_artifact and proof_artifact.exists():
                files.append(ctx.normalize_path(proof_artifact, root))
                evidence.append(f"Latest bootstrap proof artifact: {ctx.normalize_path(proof_artifact, root)}.")

            ctx.add_finding(
                findings,
                Finding(
                    code="ENV002",
                    severity="error",
                    problem="The repo has Python tests, but repo-local pytest is still unavailable because bootstrap state is failed, missing, or stale.",
                    root_cause="This repo is uv-managed and the host already provides `uv`, so the missing pytest command is not primarily a host-prerequisite absence. The repo-local test environment was never successfully bootstrapped, or the recorded bootstrap state is stale after workflow changes.",
                    files=list(dict.fromkeys(files)),
                    safer_pattern="Rerun `environment_bootstrap` to restore the repo-local test environment before audit or repair verification. For uv repos with dev extras, bootstrap should sync with `uv sync --locked --extra dev`, then verify pytest from the repo-local environment.",
                    evidence=evidence,
                    provenance="script",
                ),
            )
            return

        ctx.add_finding(
            findings,
            Finding(
                code="ENV002",
                severity="error",
                problem="The repo has Python tests, but no usable pytest command is available on the current machine.",
                root_cause="The workflow expects test collection or suite execution, but the host cannot run repo-local `python -m pytest`, repo-local `.venv` pytest, or a global `pytest` binary. Audit would otherwise skip runtime verification and misstate repo health.",
                files=[ctx.normalize_path(tests_dir, root)],
                safer_pattern="Install or sync the repo-local test environment first, then rerun audit or repair verification with a working pytest command.",
                evidence=[
                    f"{ctx.normalize_path(tests_dir, root)} exists and requires executable test verification.",
                    "No repo-local or global pytest command could be resolved for this repo.",
                ],
                provenance="script",
            ),
        )

    if ((root / "uv.lock").exists() or 'argv: ["uv"' in bootstrap_text) and shutil.which("uv") is None:
        ctx.add_finding(
            findings,
            Finding(
                code="ENV001",
                severity="error",
                problem="The current machine is missing `uv`, but this repo's managed workflow depends on it.",
                root_cause="The repo exposes `uv.lock` or a managed bootstrap contract that uses `uv`, so bootstrap and verification cannot reproduce the intended Python environment without that executable.",
                files=[path for path in (ctx.normalize_path(environment_bootstrap, root), ctx.normalize_path(smoke_test, root)) if (root / path).exists()],
                safer_pattern="Install `uv` on the host or run the audit through an environment that already provides it before trusting bootstrap or test verification results.",
                evidence=[
                    "The repo contains `uv.lock` or generated workflow commands that invoke `uv`.",
                    "`uv --version` could not be resolved on the current machine.",
                ],
                provenance="script",
            ),
        )

    rg_reference = ctx.repo_mentions_patterns(root, (r"\brg\b", r"ripgrep"))
    if rg_reference and shutil.which("rg") is None:
        ctx.add_finding(
            findings,
            Finding(
                code="ENV001",
                severity="error",
                problem="The current machine is missing `rg`, but the repo workflow or tests depend on ripgrep.",
                root_cause="The generated repo or its validation surfaces expect ripgrep for search-heavy validation, but the host environment cannot execute it. Agents then hit command blockers and start searching for workflow workarounds instead of resolving the real prerequisite gap.",
                files=[rg_reference],
                safer_pattern="Install ripgrep on the host, or make the repo-local workflow document an approved fallback before treating audit or repair execution as healthy.",
                evidence=[
                    f"Repo references `rg` or ripgrep in {rg_reference}.",
                    "`rg --version` could not be resolved on the current machine.",
                ],
                provenance="script",
            ),
        )

    git_reference = ctx.repo_mentions_patterns(root, (r"git commit", r"recent commits?", r"recent_commits"))
    if (root / ".git").exists() and git_reference:
        name_rc, name_out = ctx.run_command(["git", "config", "--get", "user.name"], root, 5)
        email_rc, email_out = ctx.run_command(["git", "config", "--get", "user.email"], root, 5)
        if name_rc != 0 or not name_out.strip() or email_rc != 0 or not email_out.strip():
            ctx.add_finding(
                findings,
                Finding(
                    code="ENV003",
                    severity="warning",
                    problem="Git identity is not configured for this host, but the repo's tests or workflow expect commit-producing validation.",
                    root_cause="Some repo validations rely on creating commits or reading recent commit history. Without `user.name` and `user.email`, those checks fail for host-environment reasons and can be misread as product regressions.",
                    files=[git_reference],
                    safer_pattern="Configure git identity on the host used for audit or repair, or mark the affected verification as blocked by environment rather than as a clean or source-level result.",
                    evidence=[
                        f"Repo references git-commit validation in {git_reference}.",
                        f"`git config --get user.name` -> {name_out.strip() or 'missing'}",
                        f"`git config --get user.email` -> {email_out.strip() or 'missing'}",
                    ],
                    provenance="script",
                ),
            )


def audit_python_execution(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    if not (root / "pyproject.toml").exists() and not (root / "setup.py").exists():
        return

    broken_reason = ctx.is_venv_broken(root)
    if broken_reason is not None:
        ctx.add_finding(
            findings,
            Finding(
                code="EXEC-ENV-001",
                severity="error",
                problem="Repo-local Python virtual environment exists but is broken — the expected interpreter cannot execute.",
                root_cause=(
                    "The repo has a `.venv` directory, but the Python executable inside it is missing, "
                    "corrupt, or fails to start. Source import validation and test execution cannot be "
                    "attributed to the repo-local environment."
                ),
                files=[str(root / ".venv")],
                safer_pattern=(
                    "Delete and recreate the virtual environment (`rm -rf .venv && uv sync` or "
                    "`python3 -m venv .venv && pip install -e .`), then rerun the audit."
                ),
                evidence=[broken_reason],
                provenance="script",
            ),
        )
        return

    python = ctx.detect_python(root)
    if python is None:
        return

    src_candidates: list[Path] = []
    for name in ("src", "app", "lib"):
        candidate = root / name
        if candidate.is_dir():
            src_candidates.append(candidate)

    import_errors: list[str] = []
    for src_dir in src_candidates:
        for pkg in sorted(src_dir.iterdir()):
            if not pkg.is_dir() or not (pkg / "__init__.py").exists():
                continue
            module = f"{src_dir.name}.{pkg.name}"
            rc, output = ctx.run_command([python, "-c", f"import {module}"], root, 20)
            if rc != 0:
                first_error = next(
                    (ln for ln in output.splitlines() if "Error" in ln or "error" in ln),
                    output.splitlines()[-1] if output.splitlines() else output,
                )
                import_errors.append(f"{module}: {first_error}")

    if import_errors:
        ctx.add_finding(
            findings,
            Finding(
                code="EXEC001",
                severity="error",
                problem="One or more Python packages fail to import — the service cannot start.",
                root_cause=(
                    "Runtime errors (NameError, FastAPIError, missing dependency, broken DI pattern, etc.) "
                    "that are invisible to static analysis prevent module load. "
                    "Common causes: TYPE_CHECKING-guarded names used in runtime annotations, "
                    "FastAPI dependency functions with non-Pydantic parameter types, circular imports."
                ),
                files=[str(src_dir) for src_dir in src_candidates],
                safer_pattern=(
                    "Verify every import succeeds: `python -c 'from src.<pkg>.main import app'`. "
                    "Use string annotations (`-> \"TypeName\"`) for TYPE_CHECKING-only imports. "
                    "Use `request: Request` (not `app: FastAPI`) in FastAPI dependency functions."
                ),
                evidence=import_errors,
                provenance="script",
            ),
        )

    pytest_command = ctx.detect_pytest_command(root)
    if pytest_command is None:
        return

    tests_dir = root / "tests"
    if not tests_dir.exists():
        return

    rc, output = ctx.run_command([*pytest_command, str(tests_dir), "--collect-only", "-q", "--tb=no"], root, 60)
    collection_errors = [
        ln for ln in output.splitlines()
        if "ERROR" in ln or "error" in ln.lower() and "collect" in ln.lower()
    ]
    if rc == 2 or collection_errors:
        ctx.add_finding(
            findings,
            Finding(
                code="EXEC002",
                severity="error",
                problem="pytest cannot collect tests — at least one test file has an import or syntax error.",
                root_cause=(
                    "A test file imports a broken module (e.g. the node agent with a broken DI pattern), "
                    "preventing the entire test suite from running. "
                    "This means QA was never actually executed against these tests."
                ),
                files=[str(tests_dir)],
                safer_pattern=(
                    "Run `pytest tests/ --collect-only` and fix all collection errors before marking QA done. "
                    "A QA artifact that claims tests passed when pytest cannot even collect is invalid."
                ),
                evidence=(collection_errors or output.splitlines())[:5],
                provenance="script",
            ),
        )

    if rc in {0, 1} and not collection_errors:
        rc2, output2 = ctx.run_command([*pytest_command, str(tests_dir), "-q", "--tb=no", "--no-header"], root, 120)
        if rc2 != 0:
            summary_lines = [ln for ln in output2.splitlines() if "failed" in ln or "passed" in ln or "error" in ln]
            failed_count_match = re.search(r"(\d+) failed", output2)
            failed_count = int(failed_count_match.group(1)) if failed_count_match else "unknown"
            ctx.add_finding(
                findings,
                Finding(
                    code="EXEC003",
                    severity="warning",
                    problem=f"Test suite has failures: {failed_count} test(s) failed.",
                    root_cause=(
                        "Tests were marked done in QA artifacts without verifying the full suite passes. "
                        "Failing tests indicate incomplete implementations, broken contracts, or regressions."
                    ),
                    files=[str(tests_dir)],
                    safer_pattern=(
                        "Run `pytest tests/ -v` and fix all failures before marking a ticket done. "
                        "QA artifacts must include pytest output showing 0 failures."
                    ),
                    evidence=summary_lines[:5],
                    provenance="script",
                ),
            )


def _command_available(command: str) -> bool:
    return shutil.which(command) is not None


def _choose_node_manager(root: Path, package_json: dict[str, Any]) -> tuple[str, list[str]]:
    declared = str(package_json.get("packageManager", "")).lower()
    if declared.startswith("pnpm") or (root / "pnpm-lock.yaml").exists():
        return "pnpm", ["pnpm"]
    if declared.startswith("yarn") or (root / "yarn.lock").exists():
        return "yarn", ["yarn"]
    if declared.startswith("bun") or (root / "bun.lock").exists() or (root / "bun.lockb").exists():
        return "bun", ["bun"]
    return "npm", ["npm"]


def _package_scripts(package_json: dict[str, Any]) -> dict[str, str]:
    scripts = package_json.get("scripts")
    return scripts if isinstance(scripts, dict) else {}


def _relative_repo_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def _add_execution_finding(
    findings: list[Finding],
    ctx: ExecutionSurfaceAuditContext,
    *,
    code: str,
    severity: str,
    problem: str,
    root_cause: str,
    files: list[Path],
    safer_pattern: str,
    evidence: list[str],
    root: Path,
) -> None:
    ctx.add_finding(
        findings,
        Finding(
            code=code,
            severity=severity,
            problem=problem,
            root_cause=root_cause,
            files=[ctx.normalize_path(path, root) for path in files if path.exists()],
            safer_pattern=safer_pattern,
            evidence=evidence[:8],
            provenance="script",
        ),
    )


def _collect_first_error_lines(output: str) -> list[str]:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    interesting = [line for line in lines if any(token in line.lower() for token in ("error", "failed", "missing", "cannot", "exception"))]
    return interesting[:5] or lines[:5]


def _repo_requires_blender_mcp(root: Path, ctx: ExecutionSurfaceAuditContext) -> bool:
    metadata = ctx.read_json(root / ".opencode" / "meta" / "asset-pipeline-bootstrap.json")
    if isinstance(metadata, dict) and metadata.get("requires_blender_mcp") is True:
        return True
    pipeline = ctx.read_json(root / "assets" / "pipeline.json")
    if isinstance(pipeline, dict):
        routes = pipeline.get("routes")
        if isinstance(routes, dict):
            for value in routes.values():
                candidates: list[str] = []
                if isinstance(value, str):
                    candidates.append(value)
                elif isinstance(value, dict):
                    for key in ("primary", "fallback"):
                        candidate = value.get(key)
                        if isinstance(candidate, str):
                            candidates.append(candidate)
                if any("blender" in candidate.lower() for candidate in candidates):
                    return True
    brief = ctx.read_text(root / "docs" / "spec" / "CANONICAL-BRIEF.md").lower()
    return "blender-agent" in brief or "blender-mcp" in brief


def _iter_blender_audit_records(
    root: Path, ctx: ExecutionSurfaceAuditContext
) -> list[tuple[Path, int, dict[str, Any]]]:
    audit_root = root / ".blender-mcp" / "audit"
    if not audit_root.exists():
        return []
    records: list[tuple[Path, int, dict[str, Any]]] = []
    for path in sorted(audit_root.glob("*.jsonl")):
        text = ctx.read_text(path)
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                records.append((path, line_number, payload))
    return records


def audit_blender_mcp_execution(
    root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext
) -> None:
    if not _repo_requires_blender_mcp(root, ctx):
        return
    audit_records = _iter_blender_audit_records(root, ctx)
    metadata_path = root / ".opencode" / "meta" / "asset-pipeline-bootstrap.json"
    pipeline_path = root / "assets" / "pipeline.json"
    if not audit_records:
        _add_execution_finding(
            findings,
            ctx,
            code="AUDIT-SKIP-BLENDER",
            severity="warning",
            problem="Blender-MCP route declared but no Blender execution audit log evidence exists.",
            root_cause="The repo depends on Blender-MCP for asset work, but the audit cannot validate whether the stateless chaining contract was used because `.blender-mcp/audit/*.jsonl` is missing.",
            files=[path for path in (metadata_path, pipeline_path) if path.exists()],
            safer_pattern="When a repo routes assets through blender-agent, keep `.blender-mcp/audit/*.jsonl` as evidence and verify one saved-blend chain before treating later Blender failures as bridge defects.",
            evidence=[
                f"requires_blender_mcp = {_repo_requires_blender_mcp(root, ctx)}",
                "No files matched .blender-mcp/audit/*.jsonl",
            ],
            root=root,
        )
        return

    last_saved_output: str | None = None
    mutating_job_count = 0
    contract_breaches: list[str] = []
    evidence_files: list[Path] = [path for path in (metadata_path, pipeline_path) if path.exists()]

    for audit_path, line_number, payload in audit_records:
        event_type = str(payload.get("event_type", "")).strip()
        tool_name = str(payload.get("tool_name", "")).strip()
        if tool_name not in BLENDER_MUTATING_TOOLS:
            continue
        evidence_files.append(audit_path)
        if event_type == "job_complete":
            if payload.get("success") is True and isinstance(payload.get("output_blend"), str) and payload.get("output_blend"):
                last_saved_output = str(payload["output_blend"])
            continue
        if event_type != "job_start":
            continue
        mutating_job_count += 1
        input_blend = payload.get("input_blend")
        output_blend = payload.get("output_blend")
        rendered_location = f"{ctx.normalize_path(audit_path, root)}:{line_number}"
        if tool_name == "project_initialize":
            if not isinstance(output_blend, str) or not output_blend:
                contract_breaches.append(
                    f"{rendered_location}: project_initialize started without output_blend."
                )
            continue
        if not isinstance(output_blend, str) or not output_blend:
            contract_breaches.append(
                f"{rendered_location}: {tool_name} started without output_blend."
            )
        if last_saved_output and (not isinstance(input_blend, str) or not input_blend):
            contract_breaches.append(
                f"{rendered_location}: {tool_name} started with input_blend=null after prior saved blend {last_saved_output}."
            )

    if mutating_job_count == 0 or not contract_breaches:
        return

    _add_execution_finding(
        findings,
        ctx,
        code="EXEC-BLENDER-001",
        severity="error",
        problem="Recorded Blender-MCP mutating calls violated the stateless saved-blend chaining contract.",
        root_cause="The repo routes assets through blender-agent, but the audit log shows mutating jobs started with null `input_blend` or `output_blend`. Any later conclusion that the Blender bridge itself is broken is untrustworthy until the same step is retried with an explicit saved-blend chain.",
        files=list(dict.fromkeys(evidence_files)),
        safer_pattern="Before escalating a Blender-MCP defect, prove one correct chain: `project_initialize(output_blend=...)`, then a mutating follow-up that reuses the returned `persistence.saved_blend` as `input_blend`, and verify `.blender-mcp/audit/*.jsonl` records non-null `input_blend` / `output_blend` on the matching `job_start`.",
        evidence=[
            f"mutating_job_count = {mutating_job_count}",
            *contract_breaches[:7],
        ],
        root=root,
    )


def _latest_current_stage_artifact(ticket: dict[str, Any], stage: str) -> dict[str, Any] | None:
    artifacts = ticket.get("artifacts")
    if not isinstance(artifacts, list):
        return None
    for artifact in reversed(artifacts):
        if not isinstance(artifact, dict):
            continue
        if str(artifact.get("trust_state", "current")).strip() != "current":
            continue
        if str(artifact.get("stage", "")).strip() != stage:
            continue
        return artifact
    return None


def _smoke_artifact_pass_contradiction_evidence(text: str) -> list[str]:
    if not SMOKE_PASS_RESULT_PATTERN.search(text):
        return []
    evidence: list[str] = []
    for match in SMOKE_FAILURE_CLASSIFICATION_PATTERN.finditer(text):
        classification = (match.group(1) or "").strip().lower()
        if classification and classification not in SMOKE_PASS_SAFE_FAILURE_CLASSIFICATIONS:
            evidence.append(f"PASS artifact command block records failure_classification {classification}")
            break
    for match in SMOKE_EXIT_CODE_PATTERN.finditer(text):
        try:
            exit_code = int(match.group(1) or "0")
        except ValueError:
            continue
        if exit_code != 0:
            evidence.append(f"PASS artifact command block records non-zero exit_code {exit_code}")
            break
    for line in text.splitlines():
        if SMOKE_GODOT_ERROR_PATTERN.search(line):
            evidence.append(line.strip())
            break
    return evidence[:4]


def audit_node_execution(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    package_path = root / "package.json"
    if not package_path.exists():
        return
    package_json = ctx.read_json(package_path)
    if not isinstance(package_json, dict):
        return

    manager, manager_cmd = _choose_node_manager(root, package_json)
    node_available = _command_available("node")
    manager_available = _command_available(manager_cmd[0])
    if not node_available or not manager_available:
        evidence = []
        if not node_available:
            evidence.append("node not found on system PATH")
        if not manager_available:
            evidence.append(f"{manager_cmd[0]} not found on system PATH")

        ctx.add_finding(
            findings,
            Finding(
                code="ENV001",
                severity="error",
                problem="Node.js proof host prerequisites are missing.",
                root_cause="Node repos need Node.js plus the repo-selected package manager to run their release-proof command family, but this host cannot resolve one or more required executables.",
                files=[ctx.normalize_path(package_path, root)],
                safer_pattern="Install Node.js and the repo-selected package manager before relying on Node release proof.",
                evidence=evidence,
                provenance="script",
            ),
        )
        return

    entry_candidates = []
    for key in ("main",):
        value = package_json.get(key)
        if isinstance(value, str) and value.strip():
            entry_candidates.append(root / value)
    for candidate in (root / "index.js", root / "src" / "index.js"):
        if candidate not in entry_candidates:
            entry_candidates.append(candidate)
    entry_path = next((candidate for candidate in entry_candidates if candidate.exists()), None)
    if entry_path is not None:
        relative = f"./{_relative_repo_path(entry_path, root)}"
        rc, output = ctx.run_command(["node", "-e", f"require({json.dumps(relative)})"], root, 30)
        if rc != 0:
            _add_execution_finding(
                findings,
                ctx,
                code="EXEC-NODE-001",
                severity="error",
                problem="Node entry point cannot be required successfully.",
                root_cause="The generated or current Node entry module throws during load or points at a broken dependency chain, so the project cannot start cleanly.",
                files=[package_path, entry_path],
                safer_pattern="Keep package.json entry points aligned with real files and require-load the entry module during audit to catch runtime boot failures before handoff.",
                evidence=_collect_first_error_lines(output),
                root=root,
            )

    scripts = _package_scripts(package_json)
    if "test" in scripts:
        if manager == "yarn":
            argv = ["yarn", "test"]
        elif manager == "bun":
            argv = ["bun", "test"]
        else:
            argv = [manager_cmd[0], "test"]
        rc, output = ctx.run_command(argv, root, 90)
        if rc != 0:
            _add_execution_finding(
                findings,
                ctx,
                code="EXEC-NODE-002",
                severity="error",
                problem="Node test command exits non-zero.",
                root_cause="The repo advertises a test surface, but the managed audit can already reproduce a failing test command or broken test bootstrap.",
                files=[package_path],
                safer_pattern="Run the declared package-manager test command during audit and keep tickets blocked until it exits cleanly with executable evidence.",
                evidence=_collect_first_error_lines(output),
                root=root,
            )

    dependencies = package_json.get("dependencies") if isinstance(package_json.get("dependencies"), dict) else {}
    if dependencies and not (root / "node_modules").exists():
        _add_execution_finding(
            findings,
            ctx,
            code="EXEC-NODE-003",
            severity="error",
            problem="Node dependencies are declared but not installed.",
            root_cause="package.json lists runtime dependencies, but node_modules is absent, so entry load and test execution cannot reflect the declared runtime.",
            files=[package_path],
            safer_pattern="Bootstrap Node dependencies before audit and verify dependency installation with node_modules presence or a clean package-manager dependency listing.",
            evidence=[f"Declared dependencies: {', '.join(sorted(dependencies.keys())[:8])}", "node_modules directory is missing."],
            root=root,
        )


def audit_rust_execution(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    cargo_toml = root / "Cargo.toml"
    if not cargo_toml.exists():
        return
    if not _command_available("cargo"):
        _add_execution_finding(findings, ctx, code="AUDIT-SKIP-RUST", severity="warning", problem="Rust toolchain absent — execution audit skipped.", root_cause="Cargo.toml exists but cargo is not available on this host, so execution checks that require the Rust toolchain were not run. Zero findings here does not mean the code compiles.", files=[cargo_toml], safer_pattern="Ensure cargo is installed and on PATH before relying on a clean audit result for Rust repos.", evidence=["cargo not found on system PATH"], root=root)
        return
    rc, output = ctx.run_command(["cargo", "check"], root, 120)
    if rc != 0:
        _add_execution_finding(findings, ctx, code="EXEC-RUST-001", severity="error", problem="cargo check fails for this repo.", root_cause="Rust sources do not currently compile cleanly, so the generated project cannot build the baseline code path.", files=[cargo_toml], safer_pattern="Run cargo check during audit and keep Rust tickets blocked until the crate compiles cleanly.", evidence=_collect_first_error_lines(output), root=root)
    rc, output = ctx.run_command(["cargo", "test", "--no-run"], root, 120)
    if rc != 0:
        _add_execution_finding(findings, ctx, code="EXEC-RUST-002", severity="error", problem="Rust tests do not compile.", root_cause="Test targets fail to compile even before execution, so QA cannot treat the Rust test surface as runnable.", files=[cargo_toml], safer_pattern="Require cargo test --no-run to pass before treating Rust validation as healthy.", evidence=_collect_first_error_lines(output), root=root)


def audit_placeholder_runtime_sources(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    if not manifest_path.exists():
        return
    manifest = ctx.read_json(manifest_path)
    tickets = manifest.get("tickets") if isinstance(manifest, dict) and isinstance(manifest.get("tickets"), list) else []
    if not any(
        isinstance(ticket, dict)
        and (
            str(ticket.get("resolution_state", "")).strip() == "done"
            or str(ticket.get("verification_state", "")).strip() == "trusted"
        )
        for ticket in tickets
    ):
        return

    hits = runtime_placeholder_hits(root, ctx)
    if not hits:
        return

    impacted_files: list[Path] = []
    for hit in hits[:8]:
        location = hit.split(":", 2)[0]
        candidate = root / location
        if candidate.exists():
            impacted_files.append(candidate)

    _add_execution_finding(
        findings,
        ctx,
        code="EXEC-RUNTIME-001",
        severity="error",
        problem="Repo-owned runtime sources still contain explicit stub or placeholder implementations.",
        root_cause="Review, QA, or closeout accepted compile-shape and shallow checks while current runtime code still declares TODO-only behavior, placeholder responses, or stubbed integrations in user-facing execution paths.",
        files=impacted_files[:5],
        safer_pattern="Keep user-facing and runtime tickets blocked until TODO/stub markers are removed from the active code path and one runnable vertical-slice check proves the real backend or tool behavior.",
        evidence=hits[:8],
        root=root,
    )


def audit_go_execution(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    go_mod = root / "go.mod"
    if not go_mod.exists():
        return
    if not _command_available("go"):
        _add_execution_finding(findings, ctx, code="AUDIT-SKIP-GO", severity="warning", problem="Go toolchain absent — execution audit skipped.", root_cause="go.mod exists but go is not available on this host, so execution checks that require the Go toolchain were not run. Zero findings here does not mean the code compiles.", files=[go_mod], safer_pattern="Ensure go is installed and on PATH before relying on a clean audit result for Go repos.", evidence=["go not found on system PATH"], root=root)
        return
    for code, argv, problem, cause, pattern in (
        ("EXEC-GO-001", ["go", "vet", "./..."], "go vet reports issues.", "Static analysis already identifies broken or suspicious Go code paths.", "Require go vet ./... to pass before Go tickets can close."),
        ("EXEC-GO-002", ["go", "build", "./..."], "go build fails for this repo.", "The Go module does not compile across all packages.", "Require go build ./... to pass before Go implementation is marked complete."),
        ("EXEC-GO-003", ["go", "test", "-run", "^$", "./..."], "Go test binaries do not compile.", "The repo cannot even compile its test targets without running the tests.", "Require go test -run ^$ ./... to pass as a compile-only QA gate for Go repos."),
    ):
        rc, output = ctx.run_command(argv, root, 120)
        if rc != 0:
            _add_execution_finding(findings, ctx, code=code, severity="error", problem=problem, root_cause=cause, files=[go_mod], safer_pattern=pattern, evidence=_collect_first_error_lines(output), root=root)


def audit_godot_execution(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    project_file = root / "project.godot"
    if not project_file.exists():
        return
    project_text = ctx.read_text(project_file)
    missing_autoloads: list[str] = []
    for autoload_path in parse_godot_autoloads(project_text).values():
        target = root / autoload_path
        if not target.exists():
            missing_autoloads.append(autoload_path)
    if missing_autoloads:
        _add_execution_finding(findings, ctx, code="EXEC-GODOT-001", severity="error", problem="Godot autoload registration references missing scripts.", root_cause="project.godot points at autoload paths that do not exist in the repo, so project startup will fail or load an incomplete runtime graph.", files=[project_file], safer_pattern="Validate every project.godot autoload path against the repo tree before handoff or audit closeout.", evidence=missing_autoloads, root=root)

    broken_scene_refs: list[str] = []
    for path in list(root.rglob("*.tscn")) + list(root.rglob("*.tres")):
        text = ctx.read_text(path)
        for resource_path in iter_godot_resource_paths(text):
            target = root / resource_path
            if not target.exists():
                broken_scene_refs.append(f"{ctx.normalize_path(path, root)} -> res://{resource_path}")
    if broken_scene_refs:
        _add_execution_finding(findings, ctx, code="EXEC-GODOT-002", severity="error", problem="Godot scenes or resources reference missing files.", root_cause="Scene/resource manifests contain res:// links that no longer resolve, so the project cannot load those assets or scripts deterministically.", files=[project_file], safer_pattern="Scan Godot scene and resource manifests for res:// references and fail audit when the target file is missing.", evidence=broken_scene_refs[:8], root=root)

    broken_extends: list[str] = []
    for path in root.rglob("*.gd"):
        text = ctx.read_text(path)
        match = re.search(r'^extends\s+"res://([^"\n]+)"', text, re.MULTILINE)
        if not match:
            continue
        target = root / match.group(1)
        if not target.exists():
            broken_extends.append(f"{ctx.normalize_path(path, root)} -> res://{match.group(1)}")
    if broken_extends:
        _add_execution_finding(findings, ctx, code="EXEC-GODOT-003", severity="error", problem="GDScript extends declarations reference missing base scripts.", root_cause="At least one GDScript file extends a base script that is not present in the repo, which breaks script inheritance before runtime.", files=[project_file], safer_pattern="Check quoted GDScript extends targets during audit and keep Godot repos blocked until every referenced base script exists.", evidence=broken_extends[:8], root=root)

    unwired_handlers: list[str] = []
    unwired_files: list[Path] = []
    for path in root.rglob("*.tscn"):
        text = ctx.read_text(path)
        connection_methods = parse_godot_scene_connection_methods(text)
        for script_path in parse_godot_scene_script_paths(text):
            script_file = root / script_path
            script_text = ctx.read_text(script_file)
            handlers = script_declared_signal_handlers(script_text)
            if not handlers:
                continue
            missing = [
                handler
                for handler in handlers
                if handler not in connection_methods and not script_dynamically_connects_handler(script_text, handler)
            ]
            if not missing:
                continue
            unwired_files.extend([path, script_file])
            unwired_handlers.append(
                f"{ctx.normalize_path(path, root)} -> {script_path}: missing scene connection for {', '.join(missing[:4])}"
            )
    if unwired_handlers:
        _add_execution_finding(findings, ctx, code="EXEC-GODOT-007", severity="error", problem="Godot scene scripts declare signal-style handlers without matching scene connections.", root_cause="Scene-owned behavior is relying on `_on_*` signal handlers that are never wired in the `.tscn`, so the repo can look structurally complete while gameplay or UI interactions silently never fire.", files=[project_file, *unwired_files[:3]], safer_pattern="When a scene-owned script declares `_on_*` signal handlers, keep the corresponding `[connection ...]` entries in the scene file or connect those handlers explicitly in code instead of leaving them inert.", evidence=unwired_handlers[:8], root=root)

    incompatible_api_calls: list[str] = []
    incompatible_files: list[Path] = []
    for path in root.rglob("*.gd"):
        text = ctx.read_text(path)
        base_type = gdscript_declared_base_type(text)
        if not base_type:
            continue
        for method_name, disallowed_bases in GODOT_BASE_METHOD_DISALLOWED_EXTENDS.items():
            if base_type not in disallowed_bases:
                continue
            if re.search(rf"\b{re.escape(method_name)}\s*\(", text) is None:
                continue
            incompatible_files.append(path)
            incompatible_api_calls.append(
                f"{ctx.normalize_path(path, root)}: extends {base_type} but calls {method_name}()"
            )
    if incompatible_api_calls:
        _add_execution_finding(findings, ctx, code="EXEC-GODOT-009", severity="error", problem="GDScript calls APIs that are unavailable on the script's declared base type.", root_cause="The audit found script methods that only exist on CanvasItem-style nodes being called from scripts that extend incompatible bases such as Node or CanvasLayer, which guarantees runtime parse/load failure even before gameplay starts.", files=[project_file, *incompatible_files[:3]], safer_pattern="Validate GDScript method calls against the declared base type and move draw/redraw or viewport-rect logic onto compatible CanvasItem-derived nodes before treating headless load as trustworthy.", evidence=incompatible_api_calls[:8], root=root)

    wave_start_evidence, wave_start_files = _godot_wave_start_gap(root, ctx)
    if wave_start_evidence:
        _add_execution_finding(
            findings,
            ctx,
            code="EXEC-GODOT-010",
            severity="error",
            problem="Wave-based Godot gameplay defines a start_wave entrypoint that nothing in the runtime ever invokes.",
            root_cause="The repo can still load and even publish finish-proof prose while the core wave progression controller never starts, because no runtime script or scene actually calls the spawner's start_wave entrypoint.",
            files=[project_file, *wave_start_files[:3]],
            safer_pattern="When a gameplay controller exposes start_wave() and wave_started, make one canonical runtime owner call start_wave() so the primary progression loop actually begins on the current build.",
            evidence=wave_start_evidence[:6],
            root=root,
        )

    game_over_evidence, game_over_files = _godot_game_over_transition_gap(root, ctx)
    if game_over_evidence:
        _add_execution_finding(
            findings,
            ctx,
            code="EXEC-GODOT-011",
            severity="error",
            problem="Godot repo ships a game-over scene, but the death path only reloads the current scene instead of reaching that fail-state.",
            root_cause="A current build can look complete from load proof alone while its advertised fail-state is unreachable, because death/failure handlers restart the scene and never transition into the repo-owned game-over flow.",
            files=[project_file, *game_over_files[:4]],
            safer_pattern="If the repo ships a game-over scene or equivalent fail-state surface, route death/failure handlers into that scene instead of silently reloading the current level.",
            evidence=game_over_evidence[:6],
            root=root,
        )

    singleton_state_evidence, singleton_state_files = _godot_singleton_state_gap(root, ctx, project_text)
    if singleton_state_evidence:
        _add_execution_finding(
            findings,
            ctx,
            code="EXEC-GODOT-012",
            severity="error",
            problem="Player-facing Godot UI reads singleton gameplay state that no runtime code ever updates.",
            root_cause="The repo exposes scoreboard or progression state through autoload singletons, but current gameplay scripts never write those fields or call the singleton's mutator methods. UI and closeout can therefore report stale default state even when the game loop runs.",
            files=[project_file, *singleton_state_files[:4]],
            safer_pattern="When HUD or game-over surfaces read autoload gameplay state, ensure runtime scripts write those fields directly or call the singleton's mutator methods on the current gameplay path before claiming completion.",
            evidence=singleton_state_evidence[:6],
            root=root,
        )

    godot_cmd = next((candidate for candidate in ("godot4", "godot") if _command_available(candidate)), None)
    if godot_cmd:
        rc, output = ctx.run_command([godot_cmd, "--headless", "--path", ".", "--quit"], root, 120)
        if rc != 0:
            _add_execution_finding(findings, ctx, code="EXEC-GODOT-004", severity="error", problem="Godot headless validation fails.", root_cause="The project cannot complete a deterministic headless Godot load pass on the current host, indicating broken project configuration or scripts.", files=[project_file], safer_pattern="Run a deterministic `godot --headless --path . --quit` validation during audit and keep the repo blocked until it succeeds or returns an explicit environment blocker instead.", evidence=_collect_first_error_lines(output), root=root)
        else:
            uid_warnings = [line.strip() for line in output.splitlines() if GODOT_UID_WARNING_PATTERN.search(line)]
            if uid_warnings:
                _add_execution_finding(findings, ctx, code="EXEC-GODOT-008", severity="warning", problem="Godot headless load only succeeds by falling back from stale resource UIDs.", root_cause="The project still contains invalid `uid://...` references in scene or resource manifests, so Godot is recovering at runtime by ignoring the recorded UID and loading the text path instead.", files=[project_file], safer_pattern="Treat invalid UID fallback warnings as actionable load drift: refresh the affected scene/resource references or import metadata until `godot --headless --path . --quit` succeeds with no UID fallback warnings.", evidence=uid_warnings[:8], root=root)

    manifest = load_manifest(root)
    if not declares_godot_android_target(root):
        return
    if not (release_lane_started_or_done(manifest) or repo_claims_completion(manifest)):
        return

    manifest_tickets = manifest.get("tickets") if isinstance(manifest.get("tickets"), list) else []
    open_ticket_count = sum(
        1
        for ticket in manifest_tickets
        if isinstance(ticket, dict)
        and str(ticket.get("resolution_state", "open")).strip() in {"open", "reopened"}
        and str(ticket.get("status", "")).strip() != "done"
    )
    files = [ctx.normalize_path(project_file, root)]
    export_presets = root / "export_presets.cfg"
    if export_presets.exists():
        files.append(ctx.normalize_path(export_presets, root))
    android_dir = root / "android"
    if android_dir.exists():
        files.append(ctx.normalize_path(android_dir, root))
    build_dir = root / "build" / "android"
    if build_dir.exists():
        files.append(ctx.normalize_path(build_dir, root))

    # --- EXEC-GODOT-005a: missing export surfaces or runnable proof (debug APK) ---
    missing_runnable: list[str] = []
    if not has_android_export_preset(root):
        missing_runnable.append("export_presets.cfg Android preset")
    if not has_android_support_surfaces(root):
        missing_runnable.append("repo-local android support surfaces")
    apk_path = debug_apk_path(root)
    if apk_path is None:
        missing_runnable.append(f"debug APK runnable proof at {expected_android_debug_apk_relpath(root)}")
    if missing_runnable:
        ctx.add_finding(
            findings,
            Finding(
                code="EXEC-GODOT-005a",
                severity="error",
                problem="Android-targeted Godot repo is missing export surfaces or debug APK runnable proof.",
                root_cause=(
                    "The repo has started or closed Android release work but is still missing the "
                    "repo-managed export preset, android/ support surfaces, or the canonical debug APK. "
                    "Runnable proof requires export_presets.cfg, non-placeholder android/ surfaces, "
                    "and a debug APK at the canonical build path."
                ),
                files=list(dict.fromkeys(files)),
                safer_pattern=(
                    "Emit export_presets.cfg and android/ surfaces at scaffold time. "
                    "Block RELEASE-001 closeout until debug APK runnable proof exists at the canonical path."
                ),
                evidence=[
                    f"open_ticket_count = {open_ticket_count}",
                    f"release_lane_started_or_done = {release_lane_started_or_done(manifest)}",
                    f"repo_claims_completion = {repo_claims_completion(manifest)}",
                    f"missing runnable surfaces: {', '.join(missing_runnable)}",
                ],
                provenance="script",
            ),
        )

    contradictory_smoke_files: list[Path] = []
    contradictory_smoke_evidence: list[str] = []
    for ticket in manifest_tickets:
        if not isinstance(ticket, dict):
            continue
        ticket_id = str(ticket.get("id", "")).strip()
        lane = str(ticket.get("lane", "")).strip()
        if ticket_id != "RELEASE-001" and lane != "finish-validation":
            continue
        artifact = _latest_current_stage_artifact(ticket, "smoke-test")
        if artifact is None:
            continue
        artifact_path_value = str(artifact.get("path", "")).strip()
        if not artifact_path_value:
            continue
        artifact_path = root / artifact_path_value
        artifact_text = ctx.read_text(artifact_path)
        evidence = _smoke_artifact_pass_contradiction_evidence(artifact_text)
        if not evidence:
            continue
        contradictory_smoke_files.append(artifact_path)
        contradictory_smoke_evidence.extend(f"{ticket_id}: {item}" for item in evidence)
    if contradictory_smoke_evidence:
        _add_execution_finding(
            findings,
            ctx,
            code="EXEC-GODOT-006",
            severity="error",
            problem="Godot release smoke artifact reports PASS despite recorded runtime or command-failure evidence.",
            root_cause=(
                "The repo is treating a contradictory smoke artifact as release proof. A Godot export or release-validation run can "
                "record parse/script-load failures or command-level failure markers while the artifact still says PASS, which lets a "
                "broken runtime state look releasable."
            ),
            files=list(dict.fromkeys([project_file, *contradictory_smoke_files])),
            safer_pattern=(
                "Make smoke_test fail when Godot export/load output contains parse or script-load errors, and reject PASS smoke artifacts "
                "whose command blocks record non-zero exit codes or non-`none` failure classifications before release closeout."
            ),
            evidence=[
                f"release_lane_started_or_done = {release_lane_started_or_done(manifest)}",
                f"repo_claims_completion = {repo_claims_completion(manifest)}",
                *contradictory_smoke_evidence[:6],
            ],
            root=root,
        )

    # --- EXEC-GODOT-005b: missing deliverable proof when packaged product is required ---
    if requires_packaged_android_product(root):
        missing_deliverable: list[str] = []
        d_path = deliverable_proof_path(root)
        if d_path and not (root / d_path).exists():
            missing_deliverable.append(f"signed release artifact at {d_path}")
        if not has_signing_ownership(root):
            missing_deliverable.append("signing prerequisites (SIGNING-001 not closed or keystore not declared)")
        if missing_deliverable:
            ctx.add_finding(
                findings,
                Finding(
                    code="EXEC-GODOT-005b",
                    severity="error",
                    problem="Godot Android repo with packaged-product requirement is missing deliverable proof or signing ownership.",
                    root_cause=(
                        "The canonical brief requires a packaged Android deliverable, but a signed release APK/AAB "
                        "or signing ownership has not been established. Debug APK proof alone is insufficient "
                        "when the brief declares a packaged Android product goal."
                    ),
                    files=list(dict.fromkeys(files)),
                    safer_pattern=(
                        "Create SIGNING-001 to own signing prerequisites before RELEASE-001 closes. "
                        "Require a signed release APK or AAB as deliverable proof when the brief mandates packaged delivery."
                    ),
                    evidence=[
                        f"requires_packaged_android_product = True",
                        f"repo_claims_completion = {repo_claims_completion(manifest)}",
                        f"missing deliverable surfaces: {', '.join(missing_deliverable)}",
                    ],
                    provenance="script",
                ),
            )


def audit_godot_project_version(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    project_file = root / "project.godot"
    if not project_file.exists():
        return
    project_text = ctx.read_text(project_file)
    stale_markers: list[str] = []
    if re.search(r"^config_version\s*=\s*2\b", project_text, re.MULTILINE):
        stale_markers.append("project.godot still declares config_version=2")
    if re.search(r"GLES2", project_text, re.IGNORECASE):
        stale_markers.append("project.godot still references deprecated GLES2 renderer settings")
    if not stale_markers:
        return
    _add_execution_finding(
        findings,
        ctx,
        code="PROJ-VER-001",
        severity="error",
        problem="Godot project configuration contains clearly stale pre-Godot-4 settings.",
        root_cause="The repo declares Godot 4-era project surfaces, but project.godot still contains stale config_version or renderer values that belong to older project formats and can invalidate execution or packaging assumptions.",
        files=[project_file],
        safer_pattern="Keep project.godot on current Godot 4.x configuration values and reject stale config_version=2 or GLES2-era renderer references before claiming the repo is clean.",
        evidence=stale_markers,
        root=root,
    )


def audit_godot_android_export_readiness(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    """Check that Godot projects targeting Android have correct export configuration."""
    project_file = root / "project.godot"
    export_presets_file = root / "export_presets.cfg"
    if not project_file.exists():
        return
    project_text = ctx.read_text(project_file)
    issues: list[str] = []

    # Check for ETC2/ASTC texture compression (required for Android export on Linux hosts)
    if export_presets_file.exists():
        presets_text = ctx.read_text(export_presets_file)
        if 'platform="Android"' in presets_text:
            if "textures/vram_compression/import_etc2_astc" not in project_text:
                issues.append("project.godot missing textures/vram_compression/import_etc2_astc=true under [rendering] (required for Android export on non-mobile hosts)")
            # Check preset name matches expected format
            if 'name="Android Debug"' not in presets_text and 'name="Android"' in presets_text:
                issues.append("export_presets.cfg uses preset name 'Android' instead of 'Android Debug' — headless export command must match exactly")

    if not issues:
        return
    _add_execution_finding(
        findings,
        ctx,
        code="GODOT-ANDROID-001",
        severity="error",
        problem="Godot Android export configuration is incomplete.",
        root_cause="Android APK export requires ETC2/ASTC texture compression enabled in project.godot and correctly named export presets. Without these, headless export fails with empty 'configuration errors'.",
        files=[project_file, export_presets_file],
        safer_pattern="Ensure project.godot includes [rendering] textures/vram_compression/import_etc2_astc=true and export_presets.cfg uses 'Android Debug' as the preset name.",
        evidence=issues,
        root=root,
    )


def audit_java_android_execution(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    indicators = [path for path in (root / "build.gradle", root / "build.gradle.kts", root / "pom.xml") if path.exists()]
    if not indicators:
        return
    if (root / "gradlew").exists():
        rc, output = ctx.run_command(["./gradlew", "check", "--dry-run"], root, 120)
        if rc != 0:
            _add_execution_finding(findings, ctx, code="EXEC-JAVA-001", severity="error", problem="Gradle build script fails even under dry-run validation.", root_cause="The Gradle build configuration is invalid or refers to missing build inputs, so Java or Android builds are not trustworthy.", files=indicators, safer_pattern="Dry-run Gradle check during audit and keep Java or Android repos blocked until the build graph resolves cleanly.", evidence=_collect_first_error_lines(output), root=root)
    elif (root / "pom.xml").exists() and _command_available("mvn"):
        rc, output = ctx.run_command(["mvn", "-q", "-DskipTests", "validate"], root, 120)
        if rc != 0:
            _add_execution_finding(findings, ctx, code="EXEC-JAVA-001", severity="error", problem="Maven project validation fails.", root_cause="The Maven project model is invalid or incomplete, so downstream Java execution is already broken at the build-script level.", files=indicators, safer_pattern="Run a non-mutating Maven validation step during audit before trusting Java handoff state.", evidence=_collect_first_error_lines(output), root=root)
    elif _command_available("javac"):
        sample = next((path for path in root.rglob("*.java") if "build" not in path.parts), None)
        if sample is not None:
            rc, output = ctx.run_command(["javac", str(sample)], root, 60)
            if rc != 0:
                _add_execution_finding(findings, ctx, code="EXEC-JAVA-002", severity="error", problem="Sample Java source file fails to compile.", root_cause="The repo contains Java sources that do not compile even in a simple single-file check.", files=[sample], safer_pattern="Compile a representative Java source during audit when no build tool exists, and fail closeout on compile errors.", evidence=_collect_first_error_lines(output), root=root)
    else:
        _add_execution_finding(findings, ctx, code="AUDIT-SKIP-JAVA", severity="warning", problem="Java build toolchain absent — execution audit skipped.", root_cause="Java/Android project indicators exist but none of gradlew, mvn, or javac are available on this host, so execution checks were not run. Zero findings here does not mean the code builds.", files=indicators[:1], safer_pattern="Ensure at least one Java build tool (gradlew, mvn, or javac) is available before relying on a clean audit result for Java repos.", evidence=["gradlew: not found", "mvn: not found on PATH", "javac: not found on PATH"], root=root)

    combined_text = "\n".join(ctx.read_text(path) for path in indicators)
    if "com.android" in combined_text or (root / "AndroidManifest.xml").exists():
        local_properties = root / "local.properties"
        sdk_dir = re.search(r"^sdk\.dir=(.+)$", ctx.read_text(local_properties), re.MULTILINE) if local_properties.exists() else None
        sdk_path = Path(sdk_dir.group(1).strip()) if sdk_dir else None
        if sdk_path is None or not sdk_path.exists():
            _add_execution_finding(findings, ctx, code="EXEC-JAVA-003", severity="error", problem="Android SDK path is missing or invalid.", root_cause="Android build surfaces are present, but local.properties does not point at a valid SDK installation.", files=[local_properties if local_properties.exists() else indicators[0]], safer_pattern="Validate Android sdk.dir or equivalent SDK configuration during audit before treating Android repos as runnable.", evidence=[f"local.properties present: {local_properties.exists()}", f"sdk.dir value: {sdk_dir.group(1).strip() if sdk_dir else 'missing'}"], root=root)


def audit_cpp_execution(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    cmake_lists = root / "CMakeLists.txt"
    makefile = root / "Makefile"
    if cmake_lists.exists() and _command_available("cmake"):
        with tempfile.TemporaryDirectory(prefix="scafforge-cmake-check-") as temp_dir:
            rc, output = ctx.run_command(["cmake", "-S", ".", "-B", temp_dir], root, 120)
        if rc != 0:
            _add_execution_finding(findings, ctx, code="EXEC-CPP-001", severity="error", problem="CMake configuration fails.", root_cause="The CMake project cannot even configure a build tree, so the current native build contract is already broken.", files=[cmake_lists], safer_pattern="Run cmake -S . -B <temp-build-dir> during audit and fail native closeout when configuration errors persist.", evidence=_collect_first_error_lines(output), root=root)
    elif cmake_lists.exists():
        _add_execution_finding(findings, ctx, code="AUDIT-SKIP-CPP-CMAKE", severity="warning", problem="CMake toolchain absent — CMake execution audit skipped.", root_cause="CMakeLists.txt exists but cmake is not available on this host, so CMake configuration checks were not run. Zero findings here does not mean the project configures cleanly.", files=[cmake_lists], safer_pattern="Ensure cmake is installed and on PATH before relying on a clean audit result for CMake repos.", evidence=["cmake not found on system PATH"], root=root)
    if makefile.exists() and _command_available("make"):
        rc, output = ctx.run_command(["make", "-n"], root, 60)
        if rc != 0:
            _add_execution_finding(findings, ctx, code="EXEC-CPP-002", severity="error", problem="Make dry-run fails.", root_cause="The Make-based native build surface cannot even resolve its dry-run command graph without errors.", files=[makefile], safer_pattern="Require make -n to succeed during audit before treating Make-based repos as buildable.", evidence=_collect_first_error_lines(output), root=root)
    elif makefile.exists():
        _add_execution_finding(findings, ctx, code="AUDIT-SKIP-CPP-MAKE", severity="warning", problem="Make toolchain absent — Make execution audit skipped.", root_cause="Makefile exists but make is not available on this host, so Makefile dry-run checks were not run. Zero findings here does not mean the build resolves cleanly.", files=[makefile], safer_pattern="Ensure make is installed and on PATH before relying on a clean audit result for Make-based repos.", evidence=["make not found on system PATH"], root=root)


def audit_dotnet_execution(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    indicators = list(root.glob("*.csproj")) + list(root.glob("*.fsproj")) + list(root.glob("*.sln"))
    if not indicators:
        return
    if not _command_available("dotnet"):
        _add_execution_finding(findings, ctx, code="AUDIT-SKIP-DOTNET", severity="warning", problem=".NET toolchain absent — execution audit skipped.", root_cause=".NET project indicators exist but dotnet is not available on this host, so execution checks that require the .NET SDK were not run. Zero findings here does not mean the code builds.", files=indicators[:1], safer_pattern="Ensure the .NET SDK is installed and dotnet is on PATH before relying on a clean audit result for .NET repos.", evidence=["dotnet not found on system PATH"], root=root)
        return
    rc, output = ctx.run_command(["dotnet", "build", "--no-restore"], root, 180)
    if rc != 0:
        _add_execution_finding(findings, ctx, code="EXEC-DOTNET-001", severity="error", problem="dotnet build fails.", root_cause="The .NET solution does not currently compile cleanly even without restore, so the generated code path is not executable.", files=indicators, safer_pattern="Require dotnet build --no-restore during audit once dependencies are bootstrapped.", evidence=_collect_first_error_lines(output), root=root)
    rc, output = ctx.run_command(["dotnet", "test", "--no-build", "--list-tests"], root, 180)
    if rc != 0:
        _add_execution_finding(findings, ctx, code="EXEC-DOTNET-002", severity="error", problem="dotnet test cannot discover tests.", root_cause="The .NET test surface is not currently buildable or discoverable, so QA cannot trust the declared test lane.", files=indicators, safer_pattern="Require dotnet test --no-build --list-tests to succeed during audit when a .NET test surface exists.", evidence=_collect_first_error_lines(output), root=root)


def _resolve_relative_import_path(base_file: Path, value: str) -> list[Path]:
    if value.startswith(".") and not value.startswith("./") and not value.startswith("../"):
        return _resolve_relative_python_import_path(base_file, value)

    base = (base_file.parent / value).resolve()
    candidates = [base]
    if base.suffix:
        return candidates
    for suffix in (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
        candidates.append(Path(f"{base}{suffix}"))
    candidates.append(base / "__init__.py")
    candidates.append(base / "index.ts")
    candidates.append(base / "index.tsx")
    candidates.append(base / "index.js")
    return candidates


def _resolve_relative_python_import_path(base_file: Path, value: str) -> list[Path]:
    level = len(value) - len(value.lstrip("."))
    module_path = value[level:].replace(".", "/")
    anchor = base_file.parent
    for _ in range(max(level - 1, 0)):
        anchor = anchor.parent
    base = (anchor / module_path).resolve() if module_path else anchor.resolve()
    candidates = [base]
    if base.suffix:
        return candidates
    candidates.append(Path(f"{base}.py"))
    candidates.append(base / "__init__.py")
    return candidates


def audit_reference_integrity(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    scene_missing: list[str] = []
    for path in list(root.rglob("*.tscn")) + list(root.rglob("*.tres")):
        text = ctx.read_text(path)
        for resource_path in iter_godot_resource_paths(text):
            if Path(resource_path).suffix not in {".gd", ".cs"}:
                continue
            target = root / resource_path
            if not target.exists():
                scene_missing.append(f"{ctx.normalize_path(path, root)} -> res://{resource_path}")
    if scene_missing:
        _add_execution_finding(findings, ctx, code="REF-001", severity="error", problem="Scene or resource files reference missing script files.", root_cause="Engine-managed scene and resource surfaces contain file references that do not resolve in the repo tree.", files=[root / path.split(" -> ", 1)[0] for path in scene_missing[:1] if " -> " in path], safer_pattern="Audit scene and resource manifests for referenced scripts and fail when the referenced file is absent.", evidence=scene_missing[:8], root=root)

    config_missing: list[str] = []
    package_json = ctx.read_json(root / "package.json") if (root / "package.json").exists() else None
    if isinstance(package_json, dict):
        for key in ("main", "module", "types"):
            value = package_json.get(key)
            if isinstance(value, str) and value.strip() and not (root / value).exists():
                config_missing.append(f"package.json {key} -> {value}")
    project_text = ctx.read_text(root / "project.godot")
    for match in re.finditer(r"^autoload/[^=]+=.*res://([^\n\"]+)", project_text, re.MULTILINE):
        target = root / match.group(1)
        if not target.exists():
            config_missing.append(f"project.godot autoload -> res://{match.group(1)}")
    if config_missing:
        _add_execution_finding(findings, ctx, code="REF-002", severity="error", problem="Configuration surfaces reference missing code or asset files.", root_cause="A canonical config surface points at files that do not exist, so runtime setup and package entrypoints drift from repo truth.", files=[path for path in (root / "package.json", root / "project.godot") if path.exists()], safer_pattern="Audit config-managed code and asset paths and keep config surfaces aligned with real files before handoff.", evidence=config_missing[:8], root=root)

    import_missing: list[str] = []
    source_suffixes = (".py", ".ts", ".tsx", ".js", ".jsx")
    for path in iter_source_files(root, source_suffixes):
        text = ctx.read_text(path)
        for match in re.finditer(r"from\s+(\.{1,}[A-Za-z0-9_\.]*)\s+import\b", text):
            if any(candidate.exists() for candidate in _resolve_relative_import_path(path, match.group(1))):
                continue
            import_missing.append(f"{ctx.normalize_path(path, root)} -> {match.group(1)}")
        for match in re.finditer(r"(?:from|import)\s+[\"'](\.[^\"']+)[\"']", text):
            if any(candidate.exists() for candidate in _resolve_relative_import_path(path, match.group(1))):
                continue
            import_missing.append(f"{ctx.normalize_path(path, root)} -> {match.group(1)}")
        for match in re.finditer(r"require\([\"'](\.[^\"']+)[\"']\)", text):
            if any(candidate.exists() for candidate in _resolve_relative_import_path(path, match.group(1))):
                continue
            import_missing.append(f"{ctx.normalize_path(path, root)} -> {match.group(1)}")
    if import_missing:
        _add_execution_finding(findings, ctx, code="REF-003", severity="error", problem="Source imports reference missing local modules.", root_cause="At least one local import or require path no longer resolves to a file in the repo, so the runtime graph is internally inconsistent.", files=[root / import_missing[0].split(" -> ", 1)[0]], safer_pattern="Audit local relative import paths and fail when the referenced module file is missing.", evidence=import_missing[:8], root=root)


def run_execution_surface_audits(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    audit_bootstrap_command_layout_mismatch(root, findings, ctx)
    audit_bootstrap_deadlock(root, findings, ctx)
    audit_bootstrap_freshness_contract(root, findings, ctx)
    audit_smoke_test_contract(root, findings, ctx)
    audit_smoke_test_override_contract(root, findings, ctx)
    audit_smoke_test_acceptance_contract(root, findings, ctx)
    audit_environment_prerequisites(root, findings, ctx)
    audit_blender_mcp_execution(root, findings, ctx)
    audit_python_execution(root, findings, ctx)
    audit_node_execution(root, findings, ctx)
    audit_rust_execution(root, findings, ctx)
    audit_go_execution(root, findings, ctx)
    audit_godot_execution(root, findings, ctx)
    audit_godot_project_version(root, findings, ctx)
    audit_godot_android_export_readiness(root, findings, ctx)
    audit_java_android_execution(root, findings, ctx)
    audit_cpp_execution(root, findings, ctx)
    audit_dotnet_execution(root, findings, ctx)
    audit_placeholder_runtime_sources(root, findings, ctx)
    audit_reference_integrity(root, findings, ctx)
