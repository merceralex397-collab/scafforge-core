from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

from test_support.downstream_reliability_fixture_builders import (
    FIXTURE_CORPORA as DOWNSTREAM_FIXTURE_CORPORA,
    FixtureCorpus,
    build_fixture_family as build_downstream_fixture_family,
    fixture_index_by_slug as downstream_fixture_index_by_slug,
)
from test_support.asset_fixture_builders import (
    CONTRACT_PATH as ASSET_FIXTURE_CONTRACT_PATH,
    build_fixture_family as build_asset_fixture_family,
    fixture_index_by_slug as asset_fixture_index_by_slug,
)
from test_support.visual_proof_fixture_builders import (
    CONTRACT_PATH as VISUAL_PROOF_FIXTURE_CONTRACT_PATH,
    build_fixture_family as build_visual_proof_fixture_family,
    fixture_index_by_slug as visual_proof_fixture_index_by_slug,
)
from test_support.gpttalker_fixture_builders import (
    build_fixture_family,
    build_partial_transaction_edge_case,
    build_pivot_state_edge_case,
    fixture_index_by_slug,
)
from test_support.repo_seeders import (
    make_stack_skill_non_placeholder,
    read_json,
    seed_failing_pytest_suite,
    seed_godot_target as seed_curated_godot_target,
    seed_ready_bootstrap,
)
from test_support.scafforge_harness import (
    AUDIT,
    BOOTSTRAP,
    PIVOT,
    PIVOT_PUBLISH,
    PIVOT_RECORD,
    PUBLIC_REPAIR,
    RECORD_REPAIR_STAGE,
    ROOT,
    VERIFY_GENERATED,
    read_repo_json_value,
    run,
    run_generated_tool,
    run_generated_tool_error,
    run_json,
)


FIXTURE_INDEX = ROOT / "tests" / "fixtures" / "gpttalker" / "index.json"


@dataclass(frozen=True)
class ProofTarget:
    slug: str
    project_name: str
    stack_label: str
    adapter_id: str
    smoke_snippets: tuple[str, ...]
    seed: Callable[[Path], None]
    release_check: Callable[[Path], None] | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run focused end-to-end Scafforge integration coverage for greenfield, repair, pivot, and curated fixture families."
    )
    parser.add_argument(
        "--list-fixtures",
        action="store_true",
        help="Print the curated fixture slugs by corpus and exit.",
    )
    return parser.parse_args()


def ensure_fixture_index() -> dict[str, dict[str, Any]]:
    payload = read_json(FIXTURE_INDEX)
    if not isinstance(payload, dict):
        raise RuntimeError("Fixture index must be a JSON object.")
    families = payload.get("families")
    if not isinstance(families, list):
        raise RuntimeError("Fixture index must contain a families list.")
    indexed = fixture_index_by_slug()
    expected = {
        "bootstrap-dependency-layout-drift",
        "host-tool-or-permission-blockage",
        "planning-implementation-contract-drift",
        "repeated-lifecycle-contradiction",
        "restart-surface-drift-after-repair",
        "placeholder-skill-after-refresh",
        "resume-surface-drift-after-greenfield",
        "validation-verdict-routing-drift",
        "split-scope-and-historical-trust-reconciliation",
    }
    if set(indexed) != expected:
        raise RuntimeError(
            f"Fixture index slugs do not match the curated GPTTalker family set: {sorted(indexed)}"
        )
    return indexed


def ensure_downstream_fixture_indexes() -> dict[str, tuple[FixtureCorpus, dict[str, dict[str, Any]]]]:
    expected = {
        "womanvshorse": {"downstream-boot-and-config-breaker"},
        "spinner": {"layout-truth-regression"},
    }
    indexed: dict[str, tuple[FixtureCorpus, dict[str, dict[str, Any]]]] = {}
    for corpus in DOWNSTREAM_FIXTURE_CORPORA:
        fixtures = downstream_fixture_index_by_slug(corpus)
        expected_slugs = expected.get(corpus.slug)
        if expected_slugs is None:
            raise RuntimeError(f"Unexpected downstream fixture corpus registered: {corpus.slug}")
        if set(fixtures) != expected_slugs:
            raise RuntimeError(
                f"{corpus.slug} fixture index slugs do not match the curated set: {sorted(fixtures)}"
            )
        indexed[corpus.slug] = (corpus, fixtures)
    return indexed


def ensure_asset_fixture_index() -> dict[str, dict[str, Any]]:
    indexed = asset_fixture_index_by_slug()
    expected = {"mixed-asset-truth"}
    if set(indexed) != expected:
        raise RuntimeError(
            f"Asset fixture index slugs do not match the curated set: {sorted(indexed)}"
        )
    return indexed


def ensure_visual_proof_fixture_index() -> dict[str, dict[str, Any]]:
    indexed = visual_proof_fixture_index_by_slug()
    expected = {"screen-fit-and-hierarchy-regression"}
    if set(indexed) != expected:
        raise RuntimeError(
            f"Visual-proof fixture index slugs do not match the curated set: {sorted(indexed)}"
        )
    return indexed


def bootstrap_full(dest: Path) -> None:
    bootstrap_scaffold(
        dest,
        project_name="Integration Probe",
        project_slug="integration-probe",
        agent_prefix="integration-probe",
        stack_label="framework-agnostic",
    )


def bootstrap_scaffold(
    dest: Path,
    *,
    project_name: str,
    project_slug: str,
    agent_prefix: str,
    stack_label: str,
    deliverable_kind: str | None = None,
    placeholder_policy: str | None = None,
    visual_finish_target: str | None = None,
    audio_finish_target: str | None = None,
    content_source_plan: str | None = None,
    licensing_or_provenance_constraints: str | None = None,
    finish_acceptance_signals: str | None = None,
    env: dict[str, str] | None = None,
) -> None:
    command = [
        sys.executable,
        str(BOOTSTRAP),
        "--dest",
        str(dest),
        "--project-name",
        project_name,
        "--project-slug",
        project_slug,
        "--agent-prefix",
        agent_prefix,
        "--model-provider",
        "openrouter",
        "--planner-model",
        "openrouter/openai/gpt-5-mini",
        "--implementer-model",
        "openrouter/openai/gpt-5-mini",
        "--utility-model",
        "openrouter/openai/gpt-5-mini",
        "--stack-label",
        stack_label,
        "--scope",
        "full",
        "--force",
    ]
    optional_args = (
        ("--deliverable-kind", deliverable_kind),
        ("--placeholder-policy", placeholder_policy),
        ("--visual-finish-target", visual_finish_target),
        ("--audio-finish-target", audio_finish_target),
        ("--content-source-plan", content_source_plan),
        ("--licensing-or-provenance-constraints", licensing_or_provenance_constraints),
        ("--finish-acceptance-signals", finish_acceptance_signals),
    )
    for flag, value in optional_args:
        if value:
            command.extend([flag, value])
    run(command, ROOT, env=env)


def require_host_prerequisite(name: str, *, context: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(
            f"{context} requires `{name}` to be available on the current host."
        )
    return path


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_executable_wrapper(path: Path, target: str) -> None:
    write_text(path, f'#!/usr/bin/env sh\nexec {target} "$@"\n')
    path.chmod(path.stat().st_mode | 0o111)


def repo_python_interpreter_path(dest: Path) -> Path:
    return dest / ".venv" / "Scripts" / "python.exe" if os.name == "nt" else dest / ".venv" / "bin" / "python"


def fake_blender_host_env(workspace: Path) -> dict[str, str]:
    host_root = workspace / "fake-blender-host"
    bin_dir = host_root / "bin"
    mcp_dir = host_root / "blender-agent" / "mcp-server"
    write_executable_wrapper(bin_dir / "blender", "/bin/true")
    write_text(mcp_dir / "pyproject.toml", "[project]\nname = \"fake-blender-mcp\"\nversion = \"0.0.0\"\n")
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    env["BLENDER_MCP_PROJECT"] = str(mcp_dir)
    return env


def strip_jsonc_comments(text: str) -> str:
    result_chars: list[str] = []
    i = 0
    in_string = False
    while i < len(text):
        char = text[i]
        if in_string:
            result_chars.append(char)
            if char == "\\" and i + 1 < len(text):
                i += 1
                result_chars.append(text[i])
            elif char == '"':
                in_string = False
            i += 1
            continue
        if char == '"':
            in_string = True
            result_chars.append(char)
            i += 1
            continue
        if char == "/" and i + 1 < len(text) and text[i + 1] == "/":
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        if char == "/" and i + 1 < len(text) and text[i + 1] == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        result_chars.append(char)
        i += 1
    return re.sub(r",\s*([}\]])", r"\1", "".join(result_chars))


def load_opencode_config(repo_root: Path) -> dict[str, Any]:
    payload = json.loads(strip_jsonc_comments((repo_root / "opencode.jsonc").read_text(encoding="utf-8")))
    if not isinstance(payload, dict):
        raise RuntimeError("Expected opencode.jsonc to parse as a configuration object.")
    return payload


def replace_stack_skill_placeholder(dest: Path, replacement: str) -> None:
    skill_path = dest / ".opencode" / "skills" / "stack-standards" / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    text = text.replace("__STACK_LABEL__", "proof-target")
    placeholders = (
        "When the repo stack is finalized, rewrite this catalog so review and QA agents get the exact build, lint, reference-integrity, and test commands that belong to this project.",
        "When the project stack is confirmed, replace this file's Universal Standards section with stack-specific rules using the `project-skill-bootstrap` skill.",
    )
    replaced = False
    for placeholder in placeholders:
        if placeholder in text:
            text = text.replace(placeholder, replacement)
            replaced = True
    if replaced:
        skill_path.write_text(text, encoding="utf-8")
        return
    skill_path.write_text(text + "\n\n" + replacement + "\n", encoding="utf-8")


def seed_placeholder_stack_skill(dest: Path) -> None:
    skill_path = dest / ".opencode" / "skills" / "stack-standards" / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    text = text.replace("proof-target", "__STACK_LABEL__")
    current_line = "When the project stack is confirmed, replace this file's Universal Standards section with stack-specific rules using the `project-skill-bootstrap` skill."
    if current_line in text:
        skill_path.write_text(text, encoding="utf-8")
        return
    updated = re.sub(
        r"When the repo stack is finalized, rewrite this catalog so review and QA agents get the exact build, lint, reference-integrity, and test commands that belong to this project\.",
        current_line,
        text,
    )
    skill_path.write_text(updated, encoding="utf-8")


def command_exists(*candidates: str) -> str | None:
    for candidate in candidates:
        path = shutil.which(candidate)
        if path:
            return path
    return None


def resolve_windows_command(command: list[str]) -> list[str]:
    if os.name != "nt" or not command:
        return command
    executable = command[0]
    if os.path.isabs(executable) or any(sep in executable for sep in ("\\", "/")):
        return command
    resolved = (
        shutil.which(executable)
        or shutil.which(f"{executable}.cmd")
        or shutil.which(f"{executable}.exe")
        or shutil.which(f"{executable}.bat")
    )
    if not resolved:
        return command
    return [resolved, *command[1:]]


def run_checked(command: list[str], cwd: Path, *, timeout: int = 120) -> None:
    resolved_command = resolve_windows_command(command)
    result = subprocess.run(
        resolved_command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def seed_python_cli_target(dest: Path) -> None:
    replace_stack_skill_placeholder(
        dest,
        "Use repo-local Python execution and validate with `python -m pytest -q` before closeout.",
    )
    interpreter_path = repo_python_interpreter_path(dest)
    if os.name == "nt":
        interpreter_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(sys.executable, interpreter_path)
    else:
        write_executable_wrapper(interpreter_path, sys.executable)
    write_text(
        dest / "pyproject.toml",
        "\n".join(
            [
                "[build-system]",
                'requires = ["setuptools>=68"]',
                'build-backend = "setuptools.build_meta"',
                "",
                "[project]",
                'name = "proof-python-cli"',
                'version = "0.1.0"',
                'description = "Minimal Python CLI proof target"',
                "",
                "[tool.setuptools.packages.find]",
                'where = ["src"]',
                "",
                "[tool.pytest.ini_options]",
                'pythonpath = ["src"]',
            ]
        )
        + "\n",
    )
    write_text(
        dest / "requirements.txt",
        "# Proof target requirements are provided by pyproject.toml\n",
    )
    write_text(
        dest / "pytest.py",
        "\n".join(
            [
                "import importlib.util",
                "import inspect",
                "import sys",
                "from pathlib import Path",
                "",
                "",
                "def main() -> int:",
                "    root = Path(__file__).resolve().parent",
                "    sys.path.insert(0, str(root))",
                "    sys.path.insert(0, str(root / 'src'))",
                "    passed = 0",
                "    failures: list[str] = []",
                "    for test_file in sorted((root / 'tests').glob('test_*.py')):",
                "        spec = importlib.util.spec_from_file_location(test_file.stem, test_file)",
                "        if spec is None or spec.loader is None:",
                "            failures.append(f'{test_file.name}::load: unable to load test module')",
                "            continue",
                "        module = importlib.util.module_from_spec(spec)",
                "        spec.loader.exec_module(module)",
                "        for name, fn in inspect.getmembers(module, inspect.isfunction):",
                "            if not name.startswith('test_'):",
                "                continue",
                "            try:",
                "                fn()",
                "                passed += 1",
                "            except Exception as exc:  # pragma: no cover - proof shim failure path",
                "                failures.append(f'{test_file.name}::{name}: {exc}')",
                "    if failures:",
                "        for failure in failures:",
                "            print(failure, file=sys.stderr)",
                "        print(f'{len(failures)} failed, {passed} passed in 0.01s')",
                "        return 1",
                "    print(f'{passed} passed in 0.01s')",
                "    return 0",
                "",
                "",
                "if __name__ == '__main__':",
                "    raise SystemExit(main())",
            ]
        )
        + "\n",
    )
    write_text(dest / "src" / "__init__.py", "")
    write_text(
        dest / "src" / "proof_python_cli" / "__init__.py",
        'def format_message(name: str) -> str:\n    return f"Hello, {name}!"\n',
    )
    write_text(
        dest / "src" / "proof_python_cli" / "__main__.py",
        "\n".join(
            [
                "import argparse",
                "",
                "from . import format_message",
                "",
                "",
                "def main() -> int:",
                '    parser = argparse.ArgumentParser(description="Python CLI proof target")',
                "    parser.add_argument('name', nargs='?', default='world')",
                "    args = parser.parse_args()",
                "    print(format_message(args.name))",
                "    return 0",
                "",
                "",
                "if __name__ == '__main__':",
                "    raise SystemExit(main())",
            ]
        )
        + "\n",
    )
    write_text(
        dest / "tests" / "test_cli.py",
        "from proof_python_cli import format_message\n\n\ndef test_format_message() -> None:\n    assert format_message('proof') == 'Hello, proof!'\n",
    )


def seed_node_api_target(dest: Path) -> None:
    replace_stack_skill_placeholder(
        dest,
        "Use `npm test` for validation and keep the generated HTTP entry point loadable through `node`.",
    )
    write_text(
        dest / "package.json",
        json.dumps(
            {
                "name": "proof-node-api",
                "version": "1.0.0",
                "private": True,
                "main": "dist/index.js",
                "scripts": {
                    "test": "node --test",
                    "start": "node dist/index.js",
                },
            },
            indent=2,
        )
        + "\n",
    )
    write_text(
        dest / "tsconfig.json",
        json.dumps(
            {
                "compilerOptions": {
                    "target": "ES2020",
                    "module": "commonjs",
                    "outDir": "dist",
                    "rootDir": "src",
                    "strict": True,
                },
                "include": ["src/**/*.ts"],
            },
            indent=2,
        )
        + "\n",
    )
    write_text(
        dest / "src" / "index.ts",
        "\n".join(
            [
                'import http from "node:http"',
                "",
                "export function buildResponse() {",
                "  return JSON.stringify({ status: 'ok' })",
                "}",
                "",
                "export function createServer() {",
                "  return http.createServer((_req, res) => {",
                "    res.writeHead(200, { 'content-type': 'application/json' })",
                "    res.end(buildResponse())",
                "  })",
                "}",
            ]
        )
        + "\n",
    )
    write_text(
        dest / "dist" / "index.js",
        "\n".join(
            [
                'const http = require("node:http")',
                "",
                "function buildResponse() {",
                "  return JSON.stringify({ status: 'ok' })",
                "}",
                "",
                "function createServer() {",
                "  return http.createServer((_req, res) => {",
                "    res.writeHead(200, { 'content-type': 'application/json' })",
                "    res.end(buildResponse())",
                "  })",
                "}",
                "",
                "if (require.main === module) {",
                "  if (process.argv.includes('--help')) {",
                "    console.log('usage: node dist/index.js [--help]')",
                "    process.exit(0)",
                "  }",
                "  const server = createServer()",
                "  server.listen(0, () => {",
                "    console.log('server-ready')",
                "    server.close(() => process.exit(0))",
                "  })",
                "}",
                "",
                "module.exports = { buildResponse, createServer }",
            ]
        )
        + "\n",
    )
    write_text(
        dest / "tests" / "api.test.js",
        "\n".join(
            [
                "const test = require('node:test')",
                "const assert = require('node:assert/strict')",
                "const { buildResponse } = require('../dist/index.js')",
                "",
                "test('buildResponse returns ok payload', () => {",
                "  assert.equal(buildResponse(), JSON.stringify({ status: 'ok' }))",
                "})",
            ]
        )
        + "\n",
    )


def seed_rust_cli_target(dest: Path) -> None:
    replace_stack_skill_placeholder(
        dest,
        "Use `cargo test` and `cargo build` as the canonical Rust validation commands.",
    )
    write_text(
        dest / "Cargo.toml",
        "\n".join(
            [
                "[package]",
                'name = "proof_rust_cli"',
                'version = "0.1.0"',
                'edition = "2021"',
            ]
        )
        + "\n",
    )
    write_text(
        dest / "src" / "main.rs",
        "\n".join(
            [
                "use std::io::{self, Read};",
                "",
                "fn main() {",
                "    let args: Vec<String> = std::env::args().collect();",
                '    if args.iter().any(|arg| arg == "--help") {',
                '        println!("usage: proof_rust_cli [--help]");',
                "        return;",
                "    }",
                "    let mut input = String::new();",
                "    io::stdin().read_to_string(&mut input).unwrap();",
                '    println!("{}", input.trim().to_uppercase());',
                "}",
            ]
        )
        + "\n",
    )


def seed_go_http_target(dest: Path) -> None:
    replace_stack_skill_placeholder(
        dest,
        "Use `go vet ./...`, `go test ./...`, and `go build ./...` as the Go proof commands.",
    )
    write_text(dest / "go.mod", "module example.com/proof-go-http\n\ngo 1.22\n")
    write_text(
        dest / "main.go",
        "\n".join(
            [
                "package main",
                "",
                "import (",
                '    "fmt"',
                '    "net/http"',
                '    "os"',
                ")",
                "",
                "func handler(w http.ResponseWriter, _ *http.Request) {",
                '    _, _ = fmt.Fprintln(w, `{"status":"ok"}`)',
                "}",
                "",
                "func main() {",
                '    if len(os.Args) > 1 && os.Args[1] == "--help" {',
                '        fmt.Println("usage: proof-go-http [--help]")',
                "        return",
                "    }",
                '    http.HandleFunc("/status", handler)',
                '    fmt.Println("proof-go-http-ready")',
                "}",
            ]
        )
        + "\n",
    )


def seed_godot_target(dest: Path) -> None:
    seed_curated_godot_target(dest, project_name="Proof Godot")


def seed_godot_android_contract(dest: Path) -> None:
    brief_path = dest / "docs" / "spec" / "CANONICAL-BRIEF.md"
    brief = brief_path.read_text(encoding="utf-8")
    brief = re.sub(r"- Stack label: `[^`]+`", "- Stack label: `godot-android-2d`", brief, count=1)
    if "Platform target is Android." not in brief:
        brief += "\n- Platform target is Android."
    if "Engine is Godot." not in brief:
        brief += "\n- Engine is Godot."
    brief_path.write_text(brief.rstrip() + "\n", encoding="utf-8")

    provenance_path = dest / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = read_json(provenance_path)
    if not isinstance(provenance, dict):
        raise RuntimeError("Godot Android contract seed expected bootstrap provenance.")
    provenance["stack_label"] = "godot-android-2d"
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


def seed_cmake_target(dest: Path) -> None:
    replace_stack_skill_placeholder(
        dest,
        "Use `cmake -S . -B build` and `cmake --build build` as the canonical native proof commands.",
    )
    write_text(
        dest / "CMakeLists.txt",
        "\n".join(
            [
                "cmake_minimum_required(VERSION 3.16)",
                "project(proof_c_library C)",
                "add_library(proof STATIC src/lib.c)",
                "target_include_directories(proof PUBLIC include)",
                "add_executable(proof_test test/test_lib.c)",
                "target_link_libraries(proof_test PRIVATE proof)",
            ]
        )
        + "\n",
    )
    write_text(dest / "include" / "lib.h", "int add(int left, int right);\n")
    write_text(
        dest / "src" / "lib.c",
        '#include "lib.h"\n\nint add(int left, int right) { return left + right; }\n',
    )
    write_text(
        dest / "test" / "test_lib.c",
        '#include "lib.h"\n\nint main(void) { return add(1, 1) == 2 ? 0 : 1; }\n',
    )


def seed_dotnet_target(dest: Path) -> None:
    replace_stack_skill_placeholder(
        dest,
        "Use `dotnet build --no-restore`, `dotnet test --no-build --list-tests`, and `dotnet run --no-build` for .NET validation.",
    )
    write_text(
        dest / "ProofConsole.csproj",
        "\n".join(
            [
                '<Project Sdk="Microsoft.NET.Sdk">',
                "  <PropertyGroup>",
                "    <OutputType>Exe</OutputType>",
                "    <TargetFramework>net8.0</TargetFramework>",
                "    <ImplicitUsings>enable</ImplicitUsings>",
                "    <Nullable>enable</Nullable>",
                "  </PropertyGroup>",
                "</Project>",
            ]
        )
        + "\n",
    )
    write_text(
        dest / "Program.cs",
        'using System;\n\nif (args.Length > 0 && args[0] == "--help")\n{\n    Console.WriteLine("usage: dotnet run --no-build [--help]");\n    return;\n}\n\nConsole.WriteLine("proof-dotnet-ready");\n',
    )


def seed_java_gradle_target(dest: Path) -> None:
    replace_stack_skill_placeholder(
        dest,
        "Use Gradle dry-run and build checks as the canonical Java proof commands.",
    )
    write_text(dest / "settings.gradle", "rootProject.name = 'proof-java-cli'\n")
    write_text(
        dest / "build.gradle",
        "\n".join(
            [
                "plugins {",
                "    id 'application'",
                "}",
                "",
                "repositories {",
                "    mavenCentral()",
                "}",
                "",
                "application {",
                "    mainClass = 'Main'",
                "}",
            ]
        )
        + "\n",
    )
    write_text(
        dest / "src" / "main" / "java" / "Main.java",
        'public class Main {\n    public static void main(String[] args) {\n        if (args.length > 0 && "--help".equals(args[0])) {\n            System.out.println("usage: gradle run --args=--help");\n            return;\n        }\n        System.out.println("proof-java-ready");\n    }\n}\n',
    )


def python_release_check(dest: Path) -> None:
    run_checked([sys.executable, "-m", "pytest", "-q"], dest)


def node_release_check(dest: Path) -> None:
    if command_exists("npm"):
        run_checked(["npm", "test"], dest)


def rust_release_check(dest: Path) -> None:
    if command_exists("cargo"):
        run_checked(["cargo", "test"], dest, timeout=180)


def go_release_check(dest: Path) -> None:
    if command_exists("go"):
        run_checked(["go", "test", "./..."], dest, timeout=180)


def godot_release_check(dest: Path) -> None:
    godot = command_exists("godot4", "godot")
    if godot:
        run_checked([godot, "--headless", "--quit", "--path", "."], dest, timeout=180)


def cmake_release_check(dest: Path) -> None:
    if command_exists("cmake"):
        build_dir = dest / "build"
        run_checked(["cmake", "-S", ".", "-B", str(build_dir)], dest, timeout=180)
        run_checked(["cmake", "--build", str(build_dir)], dest, timeout=180)


def dotnet_release_check(dest: Path) -> None:
    if command_exists("dotnet"):
        run_checked(["dotnet", "build"], dest, timeout=180)


def java_release_check(dest: Path) -> None:
    if (dest / "gradlew").exists():
        run_checked(["./gradlew", "build"], dest, timeout=180)
    elif command_exists("gradle"):
        run_checked(["gradle", "build"], dest, timeout=180)
    elif command_exists("javac"):
        run_checked(["javac", str(dest / "src" / "main" / "java" / "Main.java")], dest, timeout=180)


def multi_stack_targets() -> list[ProofTarget]:
    return [
        ProofTarget(
            "proof-python-cli",
            "Proof Python CLI",
            "python-cli",
            "python",
            ("pytest",),
            seed_python_cli_target,
            python_release_check,
        ),
        ProofTarget(
            "proof-node-api",
            "Proof Node API",
            "node-api",
            "node",
            ("npm", "test"),
            seed_node_api_target,
            node_release_check,
        ),
        ProofTarget(
            "proof-rust-cli",
            "Proof Rust CLI",
            "rust-cli",
            "rust",
            ("cargo test",),
            seed_rust_cli_target,
            rust_release_check,
        ),
        ProofTarget(
            "proof-go-http",
            "Proof Go HTTP",
            "go-http",
            "go",
            ("go test",),
            seed_go_http_target,
            go_release_check,
        ),
        ProofTarget(
            "proof-godot",
            "Proof Godot",
            "godot-android-2d",
            "godot",
            ("godot", "headless"),
            seed_godot_target,
            godot_release_check,
        ),
        ProofTarget(
            "proof-cmake",
            "Proof CMake",
            "c-cpp",
            "c-cpp",
            ("cmake",),
            seed_cmake_target,
            cmake_release_check,
        ),
        ProofTarget(
            "proof-dotnet",
            "Proof Dotnet",
            "dotnet",
            "dotnet",
            ("dotnet", "test\\b"),
            seed_dotnet_target,
            dotnet_release_check,
        ),
        ProofTarget(
            "proof-java",
            "Proof Java",
            "java-gradle",
            "java-android",
            ("gradle",),
            seed_java_gradle_target,
            java_release_check,
        ),
    ]


def seed_prompt_drift(dest: Path) -> None:
    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    text = team_leader.read_text(encoding="utf-8")
    text = text.replace("next_action_tool", "legacy_next_action_tool")
    text = text.replace(
        "summary-only stopping is invalid", "summary-only stopping may happen"
    )
    team_leader.write_text(text, encoding="utf-8")


def restore_prompt_surface(dest: Path, original_text: str) -> None:
    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    team_leader.write_text(original_text, encoding="utf-8")


def write_repair_completion_artifact(dest: Path, *, stage: str, cycle_id: str) -> None:
    artifact_rel = f".opencode/state/artifacts/history/repair/{stage}-completion.md"
    artifact_path = dest / artifact_rel
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        "# Repair Follow-On Completion\n\n"
        f"- completed_stage: {stage}\n"
        f"- cycle_id: {cycle_id}\n"
        f"- completed_by: {stage}\n\n"
        "## Summary\n\n"
        f"- Completed {stage} for the current repair cycle.\n",
        encoding="utf-8",
    )


def greenfield_integration(workspace: Path) -> None:
    dest = workspace / "greenfield"
    bootstrap_full(dest)
    bootstrap_lane = run_json(
        [
            sys.executable,
            str(VERIFY_GENERATED),
            str(dest),
            "--verification-kind",
            "bootstrap-lane",
            "--format",
            "json",
        ],
        ROOT,
    )
    if bootstrap_lane.get("verification_kind") != "greenfield_bootstrap_lane":
        raise RuntimeError(
            "Greenfield integration should run the bootstrap-lane verifier before specialization."
        )
    if bootstrap_lane.get("bootstrap_lane_valid") is not True:
        raise RuntimeError(
            "Greenfield integration should preserve one valid bootstrap lane immediately after scaffold render."
        )
    make_stack_skill_non_placeholder(dest)
    payload = run_json(
        [
            sys.executable,
            str(VERIFY_GENERATED),
            str(dest),
            "--format",
            "json",
        ],
        ROOT,
    )
    if payload.get("verification_kind") != "greenfield_continuation":
        raise RuntimeError(
            "Greenfield integration should run the continuation verifier."
        )
    if (
        payload.get("immediately_continuable") is not True
        or payload.get("finding_count") != 0
    ):
        raise RuntimeError(
            "Greenfield integration should prove the generated repo is immediately continuable once placeholder drift is removed."
        )

    packaged_android_dest = workspace / "greenfield-packaged-android"
    bootstrap_scaffold(
        packaged_android_dest,
        project_name="Packaged Android Probe",
        project_slug="packaged-android-probe",
        agent_prefix="packaged-android-probe",
        stack_label="godot-android-2d",
        deliverable_kind="release_apk",
        finish_acceptance_signals="Signed release artifact is recorded alongside runnable-proof evidence.",
    )
    seed_godot_target(packaged_android_dest)
    make_stack_skill_non_placeholder(packaged_android_dest)
    packaged_manifest = read_json(packaged_android_dest / "tickets" / "manifest.json")
    if not isinstance(packaged_manifest, dict):
        raise RuntimeError("Packaged Android greenfield integration expected a manifest.")
    packaged_tickets = {
        ticket["id"]: ticket
        for ticket in packaged_manifest.get("tickets", [])
        if isinstance(ticket, dict) and isinstance(ticket.get("id"), str)
    }
    required_packaged_ids = {"ANDROID-001", "SIGNING-001", "RELEASE-001"}
    if not required_packaged_ids.issubset(packaged_tickets):
        raise RuntimeError(
            "Packaged Android greenfield integration should seed ANDROID-001, SIGNING-001, and RELEASE-001 during bootstrap."
        )
    release_acceptance = " ".join(
        item
        for item in packaged_tickets["RELEASE-001"].get("acceptance", [])
        if isinstance(item, str)
    ).lower()
    if "signed release" not in release_acceptance and "signed" not in release_acceptance:
        raise RuntimeError(
            "Packaged Android greenfield integration should encode signed deliverable-proof ownership on RELEASE-001."
        )
    packaged_verify = run_json(
        [sys.executable, str(VERIFY_GENERATED), str(packaged_android_dest), "--format", "json"],
        ROOT,
    )
    if (
        packaged_verify.get("immediately_continuable") is not True
        or packaged_verify.get("finding_count") != 0
    ):
        raise RuntimeError(
            "Packaged Android greenfield integration should pass continuation verification once the stack skill placeholder is removed."
        )

    finish_dest = workspace / "greenfield-finish-contract"
    bootstrap_scaffold(
        finish_dest,
        project_name="Finish Contract Probe",
        project_slug="finish-contract-probe",
        agent_prefix="finish-contract-probe",
        stack_label="framework-agnostic",
        placeholder_policy="no_placeholders",
        visual_finish_target="ship-ready visual direction with no placeholder UI or placeholder artwork",
        audio_finish_target="no audio bar applies",
        content_source_plan="authored visual content only",
        finish_acceptance_signals="Finish review confirms that all user-facing visuals are ship-ready and no placeholder assets remain.",
    )
    make_stack_skill_non_placeholder(finish_dest)
    finish_manifest = read_json(finish_dest / "tickets" / "manifest.json")
    if not isinstance(finish_manifest, dict):
        raise RuntimeError("Finish-contract greenfield integration expected a manifest.")
    finish_ticket_ids = {
        str(ticket.get("id", "")).strip()
        for ticket in finish_manifest.get("tickets", [])
        if isinstance(ticket, dict)
    }
    if not {"VISUAL-001", "FINISH-VALIDATE-001"}.issubset(finish_ticket_ids):
        raise RuntimeError(
            "Finish-contract greenfield integration should seed explicit finish ownership when placeholder_policy=no_placeholders."
        )
    finish_verify = run_json(
        [sys.executable, str(VERIFY_GENERATED), str(finish_dest), "--format", "json"],
        ROOT,
    )
    if (
        finish_verify.get("immediately_continuable") is not True
        or finish_verify.get("finding_count") != 0
    ):
        raise RuntimeError(
            "Finish-contract greenfield integration should pass continuation verification after seeding explicit finish ownership."
        )

    asset_pipeline_dest = workspace / "greenfield-asset-pipeline"
    blender_host_env = fake_blender_host_env(workspace)
    bootstrap_scaffold(
        asset_pipeline_dest,
        project_name="Asset Pipeline Probe",
        project_slug="asset-pipeline-probe",
        agent_prefix="asset-pipeline-probe",
        stack_label="godot-3d-android-game",
        deliverable_kind="android apk with authored or licensed game content",
        placeholder_policy="no_placeholders",
        visual_finish_target="ship-ready low-poly visuals with no placeholder character or arena art",
        audio_finish_target="licensed UI and battle audio only",
        content_source_plan="dcc-assembly for characters and props, procedural-2d for VFX and UI themes, source-open-curated audio/fonts",
        licensing_or_provenance_constraints="Allow CC0, CC-BY, MIT, and OFL only; every generated or sourced asset must be logged.",
        finish_acceptance_signals="Release proof requires a debug APK plus complete asset provenance coverage for every committed asset.",
        env=blender_host_env,
    )
    make_stack_skill_non_placeholder(asset_pipeline_dest)
    pipeline_manifest = read_json(asset_pipeline_dest / "assets" / "pipeline.json")
    if not isinstance(pipeline_manifest, dict):
        raise RuntimeError("Asset-pipeline integration expected assets/pipeline.json to be valid JSON.")
    routes = pipeline_manifest.get("routes")
    if not isinstance(routes, dict):
        raise RuntimeError("Asset-pipeline integration expected pipeline routes to be recorded.")
    characters = routes.get("characters")
    if not isinstance(characters, dict) or characters.get("primary") != "dcc-assembly":
        raise RuntimeError(
            "Asset-pipeline integration should infer dcc-assembly as the primary character route when the content plan names Blender or DCC assembly."
        )
    bootstrap_meta = read_json(asset_pipeline_dest / ".opencode" / "meta" / "asset-pipeline-bootstrap.json")
    if not isinstance(bootstrap_meta, dict):
        raise RuntimeError("Asset-pipeline integration expected asset bootstrap metadata to exist.")
    required_agents = bootstrap_meta.get("required_agents")
    if not isinstance(required_agents, list) or "blender-asset-creator" not in required_agents:
        raise RuntimeError(
            "Asset-pipeline integration should require a blender asset subagent when the seeded routes include dcc-assembly."
        )
    required_skills = bootstrap_meta.get("required_skills")
    if not isinstance(required_skills, list) or sorted(required_skills) != ["asset-description", "blender-mcp-workflow"]:
        raise RuntimeError(
            "Asset-pipeline integration should require the Blender local workflow skills when the seeded routes include dcc-assembly."
        )
    required_mcp_servers = bootstrap_meta.get("required_mcp_servers")
    if not isinstance(required_mcp_servers, list) or required_mcp_servers != ["blender_agent"]:
        raise RuntimeError(
            "Asset-pipeline integration should require the managed blender_agent MCP server when the seeded routes include dcc-assembly."
        )
    suggested_agents = bootstrap_meta.get("suggested_agents")
    if not isinstance(suggested_agents, list) or "blender-asset-creator" not in suggested_agents:
        raise RuntimeError(
            "Asset-pipeline integration should suggest a blender asset subagent when the seeded routes include dcc-assembly."
        )
    blender_skill_path = asset_pipeline_dest / ".opencode" / "skills" / "blender-mcp-workflow" / "SKILL.md"
    if not blender_skill_path.exists():
        raise RuntimeError(
            "Asset-pipeline integration should materialize the repo-local blender-mcp-workflow skill when Blender-MCP is required."
        )
    blender_skill_text = blender_skill_path.read_text(encoding="utf-8")
    for required_snippet in ("stateless", "input_blend", "output_blend", "persistence.saved_blend", "blender_agent"):
        if required_snippet not in blender_skill_text:
            raise RuntimeError(
                "Asset-pipeline integration should render blender-mcp-workflow with the managed MCP and saved-blend chaining contract."
            )
    asset_description_path = asset_pipeline_dest / ".opencode" / "skills" / "asset-description" / "SKILL.md"
    if not asset_description_path.exists():
        raise RuntimeError(
            "Asset-pipeline integration should materialize the repo-local asset-description skill when Blender-MCP is required."
        )
    blender_agent_path = asset_pipeline_dest / ".opencode" / "agents" / "asset-pipeline-probe-blender-asset-creator.md"
    if not blender_agent_path.exists():
        raise RuntimeError(
            "Asset-pipeline integration should render a dedicated blender asset subagent when Blender-MCP is required."
        )
    blender_agent_text = blender_agent_path.read_text(encoding="utf-8")
    for required_snippet in (
        "asset-description",
        "blender-mcp-workflow",
        "blender_agent",
        "assets/briefs",
        "assets/models",
        ".blender-mcp/audit",
        "ticket_lookup: allow",
        "artifact_write: allow",
        "artifact_register: allow",
        "context_snapshot: allow",
        "blender_agent_project_initialize: allow",
        "blender_agent_scene_batch_edit: allow",
    ):
        if required_snippet not in blender_agent_text:
            raise RuntimeError(
                "Asset-pipeline integration should wire the blender asset subagent to the repo-local skills, managed MCP entry, and audit-backed asset paths."
            )
    opencode_config = load_opencode_config(asset_pipeline_dest)
    blender_agent = opencode_config.get("mcp", {}).get("blender_agent", {})
    if not isinstance(blender_agent, dict) or blender_agent.get("enabled") is not True:
        raise RuntimeError(
            "Asset-pipeline integration should enable blender_agent when the route requires Blender-MCP and the host provides Blender paths."
        )
    provenance_text = (asset_pipeline_dest / "assets" / "PROVENANCE.md").read_text(encoding="utf-8")
    if "| asset_path | source_or_workflow | license | author | acquired_or_generated_on | notes |" not in provenance_text:
        raise RuntimeError("Asset-pipeline integration expected a canonical provenance table header.")
    for relative in (
        "assets/requirements.json",
        "assets/manifest.json",
        "assets/ATTRIBUTION.md",
        "assets/workflows",
        "assets/previews",
        "assets/workfiles",
        "assets/licenses",
        "assets/qa/import-report.json",
        "assets/qa/license-report.json",
        ".opencode/meta/asset-provenance-lock.json",
    ):
        if not (asset_pipeline_dest / relative).exists():
            raise RuntimeError(f"Asset-pipeline integration expected starter surface `{relative}` to exist.")
    run_checked(
        [sys.executable, str(ROOT / "skills" / "asset-pipeline" / "scripts" / "validate_provenance.py"), str(asset_pipeline_dest)],
        ROOT,
    )
    asset_verify = run_json(
        [sys.executable, str(VERIFY_GENERATED), str(asset_pipeline_dest), "--format", "json"],
        ROOT,
    )
    if (
        asset_verify.get("immediately_continuable") is not True
        or asset_verify.get("finding_count") != 0
    ):
        raise RuntimeError(
            "Asset-pipeline greenfield integration should pass continuation verification after seeding game asset surfaces."
        )

    non_blender_asset_dest = workspace / "greenfield-non-blender-asset-pipeline"
    bootstrap_scaffold(
        non_blender_asset_dest,
        project_name="Sourced Asset Probe",
        project_slug="sourced-asset-probe",
        agent_prefix="sourced-asset-probe",
        stack_label="godot-2d-android-game",
        deliverable_kind="android apk with licensed or repo-authored 2d game content",
        placeholder_policy="no_placeholders",
        visual_finish_target="ship-ready sourced sprite sheets and UI with no placeholder art",
        audio_finish_target="licensed or repo-authored audio only",
        content_source_plan="Kenney sprites, OpenGameArt props, Freesound audio, and Godot-native UI themes",
        licensing_or_provenance_constraints="Allow CC0 and CC-BY only; track every asset in provenance.",
        finish_acceptance_signals="Release proof requires runnable Android builds plus provenance coverage for all committed assets.",
        env=blender_host_env,
    )
    make_stack_skill_non_placeholder(non_blender_asset_dest)
    sourced_config = load_opencode_config(non_blender_asset_dest)
    sourced_blender_agent = sourced_config.get("mcp", {}).get("blender_agent", {})
    if not isinstance(sourced_blender_agent, dict) or sourced_blender_agent.get("enabled") is not False:
        raise RuntimeError(
            "Non-Blender asset routes should keep blender_agent disabled even when Blender is available on the current host."
        )
    sourced_pipeline = read_json(non_blender_asset_dest / "assets" / "pipeline.json")
    if not isinstance(sourced_pipeline, dict):
        raise RuntimeError("Non-Blender asset integration expected assets/pipeline.json to exist.")
    sourced_routes = sourced_pipeline.get("routes")
    if not isinstance(sourced_routes, dict):
        raise RuntimeError("Non-Blender asset integration expected recorded route metadata.")
    if any(
        isinstance(choice, dict) and choice.get("primary") == "dcc-assembly"
        for choice in sourced_routes.values()
    ):
        raise RuntimeError(
            "Sourced asset routes should not silently seed dcc-assembly primary routes."
        )

    godot_native_asset_dest = workspace / "greenfield-godot-native-asset-pipeline"
    bootstrap_scaffold(
        godot_native_asset_dest,
        project_name="Godot Native Asset Probe",
        project_slug="godot-native-asset-probe",
        agent_prefix="godot-native-asset-probe",
        stack_label="godot-3d-android-game",
        deliverable_kind="android apk showcasing Godot-native visuals only",
        placeholder_policy="No external assets. Godot features are the final art style.",
        visual_finish_target="Godot-authored characters, shaders, particles, and UI only.",
        audio_finish_target="Procedural AudioStreamGenerator SFX or intentional silence.",
        content_source_plan="100% Godot engine features, shader materials, particles, tilemaps, and AudioStreamGenerator.",
        licensing_or_provenance_constraints="No external assets. Nothing to track beyond the active Godot-native route.",
        finish_acceptance_signals="APK compiles and the Godot-native visual stack renders cleanly on device.",
        env=blender_host_env,
    )
    make_stack_skill_non_placeholder(godot_native_asset_dest)
    godot_native_config = load_opencode_config(godot_native_asset_dest)
    godot_native_blender_agent = godot_native_config.get("mcp", {}).get("blender_agent", {})
    if not isinstance(godot_native_blender_agent, dict) or godot_native_blender_agent.get("enabled") is not False:
        raise RuntimeError(
            "Godot-native no-external-asset routes should keep blender_agent disabled even on Blender-capable hosts."
        )
    godot_native_pipeline = read_json(godot_native_asset_dest / "assets" / "pipeline.json")
    if not isinstance(godot_native_pipeline, dict):
        raise RuntimeError("Godot-native asset integration expected assets/pipeline.json to exist.")
    if "procedural" not in godot_native_pipeline.get("route_families", []):
        raise RuntimeError(
            "Godot-native no-external-asset routes should record procedural route families."
        )
    native_routes = godot_native_pipeline.get("routes")
    if not isinstance(native_routes, dict):
        raise RuntimeError("Godot-native asset integration expected recorded route metadata.")
    if any(
        isinstance(choice, dict) and choice.get("primary") == "dcc-assembly"
        for choice in native_routes.values()
    ):
        raise RuntimeError(
            "Godot-native no-external-asset routes should not collapse into dcc-assembly primaries just because the stack is 3D-capable."
        )


def repair_integration(workspace: Path) -> None:
    require_host_prerequisite("uv", context="Scafforge repair integration")
    dest = workspace / "repair"
    bootstrap_full(dest)
    seed_ready_bootstrap(dest)
    seed_failing_pytest_suite(dest)
    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    original_team_leader = team_leader.read_text(encoding="utf-8")
    seed_prompt_drift(dest)
    initial = run_json(
        [
            sys.executable,
            str(PUBLIC_REPAIR),
            str(dest),
            "--skip-deterministic-refresh",
        ],
        ROOT,
        allow_returncodes={0, 3},
    )
    required = set(initial["execution_record"]["required_follow_on_stages"])
    expected_required = {
        "project-skill-bootstrap",
        "opencode-team-bootstrap",
        "agent-prompt-engineering",
        "ticket-pack-builder",
    }
    if required != expected_required:
        raise RuntimeError(
            f"Repair integration expected follow-on stages {sorted(expected_required)}, found {sorted(required)}"
        )
    tracking_path = dest / ".opencode" / "meta" / "repair-follow-on-state.json"
    tracking_state = read_json(tracking_path)
    if not isinstance(tracking_state, dict):
        raise RuntimeError(
            "Repair integration expected persistent follow-on tracking state."
        )
    cycle_id = tracking_state.get("cycle_id")
    if not isinstance(cycle_id, str) or not cycle_id:
        raise RuntimeError("Repair integration expected a non-empty repair cycle id.")
    provenance_evidence_rel = (
        ".opencode/state/artifacts/history/repair/provenance-probe.md"
    )
    provenance_evidence_path = dest / provenance_evidence_rel
    provenance_evidence_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_evidence_path.write_text("# Provenance probe\n", encoding="utf-8")
    missing_provenance_env = os.environ.copy()
    missing_provenance_env["SCAFFORGE_FORCE_MISSING_PROVENANCE"] = "1"
    missing_provenance_record = subprocess.run(
        [
            sys.executable,
            str(RECORD_REPAIR_STAGE),
            str(dest),
            "--stage",
            "ticket-pack-builder",
            "--completed-by",
            "ticket-pack-builder",
            "--summary",
            "This should fail when repair-package provenance is missing.",
            "--evidence",
            provenance_evidence_rel,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=missing_provenance_env,
    )
    if missing_provenance_record.returncode == 0:
        raise RuntimeError(
            "Repair integration should reject recorded completion when repair-package provenance is missing."
        )
    combined_provenance_output = (
        f"{missing_provenance_record.stdout}\n{missing_provenance_record.stderr}"
    )
    if (
        "requires repair_package_commit provenance" not in combined_provenance_output
        or "missing_provenance" not in combined_provenance_output
    ):
        raise RuntimeError(
            "Repair integration should explain missing provenance when recorded completion is rejected."
        )
    for stage in sorted(expected_required | {"handoff-brief"}):
        write_repair_completion_artifact(dest, stage=stage, cycle_id=cycle_id)
    artifact_recorded = run_json(
        [
            sys.executable,
            str(PUBLIC_REPAIR),
            str(dest),
            "--skip-deterministic-refresh",
        ],
        ROOT,
        allow_returncodes={0, 3},
    )
    recorded_before_fix = set(
        artifact_recorded["execution_record"]["recorded_execution_completed_stages"]
    )
    expected_recorded = expected_required | {"handoff-brief"}
    if recorded_before_fix != expected_recorded:
        raise RuntimeError(
            f"Repair integration expected recorded completion for {sorted(expected_recorded)}, found {sorted(recorded_before_fix)}"
        )
    if not artifact_recorded["execution_record"]["blocking_reasons"]:
        raise RuntimeError(
            "Repair integration should stay managed-blocked while placeholder skill and prompt drift still exist."
        )
    make_stack_skill_non_placeholder(dest)
    restore_prompt_surface(dest, original_team_leader)
    converged = run_json(
        [
            sys.executable,
            str(PUBLIC_REPAIR),
            str(dest),
            "--skip-deterministic-refresh",
        ],
        ROOT,
        allow_returncodes={0, 3},
    )
    if (
        set(converged["execution_record"]["recorded_execution_completed_stages"])
        != expected_recorded
    ):
        raise RuntimeError(
            "Repair integration should preserve recorded completion for all routed follow-on stages."
        )
    outcome = converged["execution_record"]["repair_follow_on_outcome"]
    if outcome not in {"managed_blocked", "source_follow_up"}:
        raise RuntimeError(
            f"Repair integration should classify the post-follow-on state truthfully; observed unexpected outcome `{outcome}`."
        )
    if outcome == "source_follow_up":
        if converged["execution_record"]["handoff_allowed"] is not True:
            raise RuntimeError(
                "Repair integration should allow handoff once only source follow-up remains."
            )
    else:
        if not converged["execution_record"]["blocking_reasons"]:
            raise RuntimeError(
                "Repair integration should preserve managed-blocked reasons when workflow findings still remain after recorded follow-on completion."
            )

    android_dest = workspace / "repair-android-surfaces"
    bootstrap_full(android_dest)
    seed_godot_android_contract(android_dest)
    seed_godot_target(android_dest)
    make_stack_skill_non_placeholder(android_dest)
    seed_ready_bootstrap(android_dest)
    original_project_godot = (android_dest / "project.godot").read_text(encoding="utf-8")
    source_snapshots = {
        relative: (android_dest / relative).read_text(encoding="utf-8")
        for relative in ("scripts/main.gd", "scenes/main.tscn")
    }
    (android_dest / "export_presets.cfg").unlink(missing_ok=True)
    shutil.rmtree(android_dest / "android", ignore_errors=True)
    android_repair = run_json(
        [sys.executable, str(PUBLIC_REPAIR), str(android_dest)],
        ROOT,
        allow_returncodes={0, 3},
    )
    android_surface_result = android_repair.get("execution_record", {}).get("android_surface_result")
    if not isinstance(android_surface_result, dict) or android_surface_result.get("performed") is not True:
        raise RuntimeError(
            "Repair integration should regenerate missing Scafforge-owned Android export surfaces without requiring manual source edits."
        )
    missing_repair_surfaces = [
        relative
        for relative in ("export_presets.cfg", "android/scafforge-managed.json")
        if not (android_dest / relative).exists()
    ]
    if missing_repair_surfaces:
        raise RuntimeError(
            "Repair integration should restore all managed Android export surfaces. "
            f"Missing: {', '.join(missing_repair_surfaces)}"
        )
    repaired_project_godot = (android_dest / "project.godot").read_text(encoding="utf-8")
    if "textures/vram_compression/import_etc2_astc=true" not in repaired_project_godot:
        raise RuntimeError(
            "Repair integration should restore the Godot Android ETC2 setting in project.godot."
        )
    if repaired_project_godot == original_project_godot:
        raise RuntimeError(
            "Repair integration should materially update project.godot when the Android ETC2 setting is missing."
        )
    for relative, original in source_snapshots.items():
        current = (android_dest / relative).read_text(encoding="utf-8")
        if current != original:
            raise RuntimeError(
                "Repair integration should not mutate repo-owned Godot source files while regenerating managed Android export surfaces."
            )


def pivot_integration(workspace: Path) -> None:
    dest = workspace / "pivot"
    bootstrap_full(dest)
    make_stack_skill_non_placeholder(dest)
    seed_ready_bootstrap(dest)
    run_generated_tool(dest, ".opencode/tools/handoff_publish.ts", {})
    payload = run_json(
        [
            sys.executable,
            str(PIVOT),
            str(dest),
            "--pivot-class",
            "architecture-change",
            "--requested-change",
            "Move from a single service layout to modular domain services with a refreshed workflow contract.",
            "--accepted-decision",
            "Regenerate workflow prompts, skills, and ticket routing around the modular topology.",
            "--format",
            "json",
        ],
        ROOT,
    )
    if payload["verification_status"]["verification_passed"] is not True:
        raise RuntimeError(
            "Pivot integration should pass the post-pivot verification gate on a clean generated repo."
        )
    pending = payload["downstream_refresh_state"]["pending_stages"]
    if not isinstance(pending, list) or not pending:
        raise RuntimeError("Pivot integration expected routed downstream stages.")
    for stage in pending:
        evidence_rel = f".opencode/state/artifacts/history/pivot/{stage}-completion.md"
        evidence_path = dest / evidence_rel
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(f"# {stage} completion\n", encoding="utf-8")
        run_json(
            [
                sys.executable,
                str(PIVOT_RECORD),
                str(dest),
                "--stage",
                stage,
                "--completed-by",
                stage,
                "--summary",
                f"Completed {stage} during integration coverage.",
                "--evidence",
                evidence_rel,
            ],
            ROOT,
        )
    published = run_json(
        [
            sys.executable,
            str(PIVOT_PUBLISH),
            str(dest),
            "--published-by",
            "integration-test",
        ],
        ROOT,
    )
    state = read_json(dest / ".opencode" / "meta" / "pivot-state.json")
    restart_inputs = (
        state.get("restart_surface_inputs") if isinstance(state, dict) else None
    )
    if (
        not isinstance(restart_inputs, dict)
        or restart_inputs.get("pivot_in_progress") is not False
    ):
        raise RuntimeError(
            "Pivot integration should clear pivot_in_progress once all routed downstream stages are completed."
        )
    if restart_inputs.get("pending_downstream_stages") not in ([], None):
        raise RuntimeError(
            "Pivot integration should not leave pending downstream stages after all recorded completions."
        )
    if published["restart_surface_publication"]["status"] != "published":
        raise RuntimeError(
            "Pivot integration should republish restart surfaces after pivot completion."
        )


def _load_diagnosis_manifest(audit_payload: dict[str, Any]) -> dict[str, Any]:
    diagnosis_pack = audit_payload.get("diagnosis_pack")
    if not isinstance(diagnosis_pack, dict):
        raise RuntimeError("Curated fixture audit should emit a diagnosis pack.")
    diagnosis_path = diagnosis_pack.get("path")
    if not isinstance(diagnosis_path, str) or not diagnosis_path.strip():
        raise RuntimeError("Diagnosis pack payload is missing its path.")
    manifest_path = Path(diagnosis_path) / "manifest.json"
    payload = read_json(manifest_path)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Diagnosis manifest must be a JSON object: {manifest_path}")
    return payload


def assert_expected_repair_posture(
    slug: str,
    contract: dict[str, Any],
    audit_payload: dict[str, Any],
) -> None:
    expected_next_step = contract.get("expected_recommended_next_step")
    expected_routes = contract.get("expected_ticket_routes")
    if expected_next_step is None and expected_routes is None:
        return
    diagnosis_manifest = _load_diagnosis_manifest(audit_payload)
    if isinstance(expected_next_step, str) and diagnosis_manifest.get("recommended_next_step") != expected_next_step:
        raise RuntimeError(
            f"Fixture `{slug}` expected recommended_next_step={expected_next_step!r}, "
            f"observed {diagnosis_manifest.get('recommended_next_step')!r}."
        )
    if isinstance(expected_routes, list) and expected_routes:
        recommendations = diagnosis_manifest.get("ticket_recommendations")
        if not isinstance(recommendations, list):
            raise RuntimeError(f"Fixture `{slug}` expected ticket recommendations in the diagnosis manifest.")
        observed_routes = {
            str(item.get("route", "")).strip()
            for item in recommendations
            if isinstance(item, dict) and str(item.get("route", "")).strip()
        }
        missing_routes = [
            route for route in expected_routes if isinstance(route, str) and route not in observed_routes
        ]
        if missing_routes:
            raise RuntimeError(
                f"Fixture `{slug}` expected repair routes {missing_routes}, observed {sorted(observed_routes)}."
            )


def fixture_builder_integration(
    *,
    corpus_name: str,
    fixtures: dict[str, dict[str, Any]],
    workspace: Path,
    build_fixture: Callable[[str, Path], dict[str, Any]],
    contract_path: str,
) -> None:
    fixture_root = workspace / f"{corpus_name}-fixtures"
    for slug in sorted(fixtures):
        dest = fixture_root / slug
        contract = build_fixture(slug, dest)
        if contract.get("slug") != slug:
            raise RuntimeError(
                f"Fixture builder should persist the canonical slug for `{slug}`."
            )
        if (
            not isinstance(contract.get("expected_coverage"), list)
            or not contract["expected_coverage"]
        ):
            raise RuntimeError(
                f"Fixture builder should persist expected coverage for `{slug}`."
            )
        contract_file = dest / contract_path
        if not contract_file.exists():
            raise RuntimeError(
                f"Fixture builder should emit {contract_path} for `{slug}`."
            )
        expected_finding_codes = contract.get("expected_finding_codes")
        if not isinstance(expected_finding_codes, list) or not expected_finding_codes:
            raise RuntimeError(
                f"Fixture builder should persist expected_finding_codes for `{slug}`."
            )
        command = [
            sys.executable,
            str(AUDIT),
            str(dest),
            "--format",
            "json",
        ]
        supporting_log = contract.get("supporting_log")
        if isinstance(supporting_log, str) and supporting_log.strip():
            command.extend(["--supporting-log", str(dest / supporting_log)])
        audit_payload = run_json(
            command,
            ROOT,
        )
        if (
            not isinstance(audit_payload.get("findings"), list)
            or audit_payload.get("finding_count", 0) <= 0
        ):
            raise RuntimeError(
                f"Fixture `{slug}` should produce actionable audit findings, not a no-op repo."
            )
        assert_expected_audit_codes(slug, expected_finding_codes, audit_payload)
        truth_expectations = contract.get("truth_expectations")
        if not isinstance(truth_expectations, dict):
            raise RuntimeError(
                f"Fixture `{slug}` should persist truth_expectations in its contract payload."
            )
        assert_fixture_truth_checks(dest, slug, truth_expectations)


def asset_fixture_integration(
    *,
    fixtures: dict[str, dict[str, Any]],
    workspace: Path,
) -> None:
    fixture_root = workspace / "asset-fixtures"
    validator = ROOT / "skills" / "asset-pipeline" / "scripts" / "validate_provenance.py"
    for slug in sorted(fixtures):
        dest = fixture_root / slug
        contract = build_asset_fixture_family(slug, dest)
        if contract.get("slug") != slug:
            raise RuntimeError(
                f"Asset fixture builder should persist the canonical slug for `{slug}`."
            )
        contract_file = dest / ASSET_FIXTURE_CONTRACT_PATH
        if not contract_file.exists():
            raise RuntimeError(
                f"Asset fixture builder should emit {ASSET_FIXTURE_CONTRACT_PATH} for `{slug}`."
            )
        result = subprocess.run(
            [sys.executable, str(validator), str(dest)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Asset fixture `{slug}` should pass validate_provenance.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        manifest = read_json(dest / "assets" / "manifest.json")
        if not isinstance(manifest, dict):
            raise RuntimeError(f"Asset fixture `{slug}` should persist assets/manifest.json.")
        assets = manifest.get("assets")
        if not isinstance(assets, list):
            raise RuntimeError(f"Asset fixture `{slug}` should persist manifest assets.")
        expected_asset_count = contract.get("expected_asset_count")
        if expected_asset_count != len(assets):
            raise RuntimeError(
                f"Asset fixture `{slug}` expected {expected_asset_count} assets, found {len(assets)}."
            )
        observed_routes = sorted(
            {
                str(entry.get("source_route", "")).strip()
                for entry in assets
                if isinstance(entry, dict) and str(entry.get("source_route", "")).strip()
            }
        )
        expected_routes = sorted(contract.get("expected_source_routes", []))
        if observed_routes != expected_routes:
            raise RuntimeError(
                f"Asset fixture `{slug}` expected source routes {expected_routes}, found {observed_routes}."
            )


def visual_proof_fixture_integration(
    *,
    fixtures: dict[str, dict[str, Any]],
    workspace: Path,
) -> None:
    fixture_root = workspace / "visual-proof-fixtures"
    for slug in sorted(fixtures):
        dest = fixture_root / slug
        contract = build_visual_proof_fixture_family(slug, dest)
        if contract.get("slug") != slug:
            raise RuntimeError(
                f"Visual-proof fixture builder should persist the canonical slug for `{slug}`."
            )
        contract_file = dest / VISUAL_PROOF_FIXTURE_CONTRACT_PATH
        if not contract_file.exists():
            raise RuntimeError(
                f"Visual-proof fixture builder should emit {VISUAL_PROOF_FIXTURE_CONTRACT_PATH} for `{slug}`."
            )
        blocker = contract.get("expected_gate_blocker")
        if not isinstance(blocker, str) or not blocker.strip():
            raise RuntimeError(
                f"Visual-proof fixture `{slug}` should persist an expected_gate_blocker."
            )
        ticket_id = contract.get("ticket_id")
        qa_artifact_path = contract.get("qa_artifact_path")
        evidence_paths = contract.get("expected_visual_proof_paths")
        rubric_blockers = contract.get("expected_rubric_blockers")
        if not isinstance(ticket_id, str) or not ticket_id.strip():
            raise RuntimeError(f"Visual-proof fixture `{slug}` should persist ticket_id.")
        if not isinstance(qa_artifact_path, str) or not qa_artifact_path.strip():
            raise RuntimeError(
                f"Visual-proof fixture `{slug}` should persist qa_artifact_path."
            )
        if not isinstance(evidence_paths, list) or not evidence_paths:
            raise RuntimeError(
                f"Visual-proof fixture `{slug}` should persist expected_visual_proof_paths."
            )
        if not isinstance(rubric_blockers, list) or not rubric_blockers:
            raise RuntimeError(
                f"Visual-proof fixture `{slug}` should persist expected_rubric_blockers."
            )
        missing_evidence_files = [
            str(dest / item) for item in evidence_paths if not (dest / item).is_file()
        ]
        if missing_evidence_files:
            raise RuntimeError(
                f"Visual-proof fixture `{slug}` should create real evidence files before QA records them.\nMissing:\n"
                + "\n".join(missing_evidence_files)
            )

        stage_error = run_generated_tool_error(
            dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": ticket_id, "stage": "smoke-test"},
        )
        if blocker not in stage_error:
            raise RuntimeError(
                f"Visual-proof fixture `{slug}` should block smoke-test routing on structured visual proof.\nObserved:\n{stage_error}"
            )
        lookup_payload = run_generated_tool(
            dest,
            ".opencode/tools/ticket_lookup.ts",
            {"ticket_id": ticket_id},
        )
        transition_guidance = (
            lookup_payload.get("transition_guidance")
            if isinstance(lookup_payload, dict)
            else None
        )
        current_state_blocker = (
            transition_guidance.get("current_state_blocker")
            if isinstance(transition_guidance, dict)
            else None
        )
        if not isinstance(current_state_blocker, str) or blocker not in current_state_blocker:
            raise RuntimeError(
                f"Visual-proof fixture `{slug}` should surface the structured visual-proof blocker in ticket_lookup."
            )

        qa_path = dest / qa_artifact_path
        qa_path.write_text(
            qa_path.read_text(encoding="utf-8")
            + "\n## Visual Proof\n\n"
            + "- visual_proof_status: PASS\n"
            + f"- visual_proof_evidence: {', '.join(str(item) for item in evidence_paths)}\n"
            + "- visual_proof_surfaces: title-screen, main-menu, HUD\n"
            + "- visual_rubric_blockers: none\n"
            + "- visual_style_note: Bright flat-color toy-box styling is intentional; the review judges readability, screen fit, hierarchy, and finish rather than realism.\n",
            encoding="utf-8",
        )
        update_result = run_generated_tool(
            dest,
            ".opencode/tools/ticket_update.ts",
            {"ticket_id": ticket_id, "stage": "smoke-test"},
        )
        if update_result["updated_ticket"]["stage"] != "smoke-test":
            raise RuntimeError(
                f"Visual-proof fixture `{slug}` should advance once structured visual proof is present."
            )


def assert_fixture_truth_checks(
    dest: Path, slug: str, truth_expectations: dict[str, Any]
) -> None:
    """Assert fixture truth expectations using a dispatcher pattern for maintainability."""
    checks = truth_expectations.get("checks")
    if not isinstance(checks, list) or not checks:
        raise RuntimeError(f"Fixture `{slug}` must define truth_expectations.checks.")

    # Dispatcher pattern: map check kinds to their handler functions
    check_handlers: dict[str, Callable[[Path, str, dict[str, Any]], None]] = {
        "json_equals": _check_json_equals,
        "file_contains": _check_file_contains,
        "file_exists": _check_file_exists,
    }

    for check in checks:
        if not isinstance(check, dict):
            raise RuntimeError(f"Fixture `{slug}` truth check entries must be objects.")
        kind = check.get("kind")
        handler = check_handlers.get(kind)
        if handler is None:
            supported = ", ".join(sorted(check_handlers.keys()))
            raise RuntimeError(
                f"Fixture `{slug}` has unsupported truth check kind: {kind!r}. "
                f"Supported kinds: {supported}."
            )
        handler(dest, slug, check)


def _check_json_equals(dest: Path, slug: str, check: dict[str, Any]) -> None:
    """Verify a JSON value at a dotted path equals the expected value."""
    file_path = check.get("file")
    dotted_path = check.get("path")
    if (
        not isinstance(file_path, str)
        or not isinstance(dotted_path, str)
        or "value" not in check
    ):
        raise RuntimeError(
            f"Fixture `{slug}` json_equals checks must define file, path, and value."
        )
    expected = check["value"]
    try:
        observed = read_repo_json_value(dest, file_path, dotted_path)
    except RuntimeError as exc:
        raise RuntimeError(
            f"Fixture `{slug}` failed to read JSON value at {file_path}:{dotted_path}: {exc}"
        ) from exc
    if observed != expected:
        raise RuntimeError(
            f"Fixture `{slug}` expected {file_path}:{dotted_path} to equal {expected!r}, observed {observed!r}."
        )


def extract_audit_codes(audit_payload: dict[str, Any]) -> set[str]:
    findings = audit_payload.get("findings")
    if not isinstance(findings, list):
        return set()
    return {
        str(item.get("code", "")).strip()
        for item in findings
        if isinstance(item, dict) and str(item.get("code", "")).strip()
    }


def assert_expected_audit_codes(
    slug: str, expected_finding_codes: list[Any], audit_payload: dict[str, Any]
) -> None:
    audit_codes = extract_audit_codes(audit_payload)
    missing_codes = [
        code
        for code in expected_finding_codes
        if isinstance(code, str) and code not in audit_codes
    ]
    if missing_codes:
        raise RuntimeError(
            f"Fixture `{slug}` did not trigger its declared invariant finding codes. Missing: {', '.join(missing_codes)}; "
            f"observed: {', '.join(sorted(audit_codes)) or 'none'}"
        )


def _check_file_contains(dest: Path, slug: str, check: dict[str, Any]) -> None:
    """Verify a file contains the expected string."""
    file_path = check.get("file")
    needle = check.get("needle")
    if not isinstance(file_path, str) or not isinstance(needle, str):
        raise RuntimeError(
            f"Fixture `{slug}` file_contains checks must define file and needle."
        )
    full_path = dest / file_path
    try:
        text = full_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Fixture `{slug}` expected file to exist for file_contains check: {file_path}."
        ) from exc
    except UnicodeDecodeError as exc:
        raise RuntimeError(
            f"Fixture `{slug}` file {file_path} could not be read as UTF-8 text."
        ) from exc
    if needle not in text:
        raise RuntimeError(
            f"Fixture `{slug}` expected {file_path} to contain {needle!r}."
        )


def _check_file_exists(dest: Path, slug: str, check: dict[str, Any]) -> None:
    """Verify a file exists."""
    file_path = check.get("file")
    if not isinstance(file_path, str):
        raise RuntimeError(f"Fixture `{slug}` file_exists checks must define file.")
    if not (dest / file_path).exists():
        raise RuntimeError(f"Fixture `{slug}` expected file to exist: {file_path}.")


def synthetic_edge_case_integration(workspace: Path) -> None:
    partial_transaction_dest = workspace / "partial-transaction-edge-case"
    partial_contract = build_partial_transaction_edge_case(partial_transaction_dest)
    assert_fixture_truth_checks(
        partial_transaction_dest,
        partial_contract["slug"],
        partial_contract["truth_expectations"],
    )
    partial_expected_finding_codes = partial_contract.get("expected_finding_codes")
    if (
        not isinstance(partial_expected_finding_codes, list)
        or not partial_expected_finding_codes
    ):
        raise RuntimeError(
            "Partial-transaction synthetic fixture should persist expected_finding_codes."
        )
    partial_audit = run_json(
        [
            sys.executable,
            str(AUDIT),
            str(partial_transaction_dest),
            "--format",
            "json",
            "--no-diagnosis-pack",
        ],
        ROOT,
    )
    assert_expected_audit_codes(
        partial_contract["slug"],
        partial_expected_finding_codes,
        partial_audit,
    )

    pivot_state_dest = workspace / "pivot-state-edge-case"
    pivot_contract = build_pivot_state_edge_case(pivot_state_dest)
    assert_fixture_truth_checks(
        pivot_state_dest,
        pivot_contract["slug"],
        pivot_contract["truth_expectations"],
    )
    pivot_expected_finding_codes = pivot_contract.get("expected_finding_codes")
    if not isinstance(pivot_expected_finding_codes, list) or not pivot_expected_finding_codes:
        raise RuntimeError(
            "Pivot-state synthetic fixture should persist expected_finding_codes."
        )
    pivot_audit = run_json(
        [
            sys.executable,
            str(AUDIT),
            str(pivot_state_dest),
            "--format",
            "json",
            "--no-diagnosis-pack",
        ],
        ROOT,
    )
    assert_expected_audit_codes(
        pivot_contract["slug"],
        pivot_expected_finding_codes,
        pivot_audit,
    )


def multi_stack_proof_integration(workspace: Path) -> None:
    proof_root = workspace / "multi-stack-proof"
    for target in multi_stack_targets():
        dest = proof_root / target.slug
        bootstrap_scaffold(
            dest,
            project_name=target.project_name,
            project_slug=target.slug,
            agent_prefix=target.slug,
            stack_label=target.stack_label,
        )
        target.seed(dest)

        smoke_test_text = (dest / ".opencode" / "tools" / "smoke_test.ts").read_text(
            encoding="utf-8"
        )
        for snippet in target.smoke_snippets:
            if snippet not in smoke_test_text:
                raise RuntimeError(
                    f"Proof target `{target.slug}` expected smoke_test.ts to reference `{snippet}`."
                )

        bootstrap_result = run_generated_tool(
            dest, ".opencode/tools/environment_bootstrap.ts", {}
        )
        detections = bootstrap_result.get("detections")
        if not isinstance(detections, list) or target.adapter_id not in {
            item.get("adapter_id") for item in detections if isinstance(item, dict)
        }:
            raise RuntimeError(
                f"Proof target `{target.slug}` should detect adapter `{target.adapter_id}` during environment bootstrap."
            )

        bootstrap_status = bootstrap_result.get("bootstrap_status")
        blockers = (
            bootstrap_result.get("blockers")
            if isinstance(bootstrap_result.get("blockers"), list)
            else []
        )
        missing = (
            bootstrap_result.get("missing_prerequisites")
            if isinstance(bootstrap_result.get("missing_prerequisites"), list)
            else []
        )

        if target.slug == "proof-godot":
            missing_android_surfaces = [
                relative
                for relative in ("export_presets.cfg", "android/scafforge-managed.json")
                if not (dest / relative).exists()
            ]
            if missing_android_surfaces:
                raise RuntimeError(
                    "Godot Android proof targets should scaffold all repo-managed Android surfaces. "
                    f"Missing: {', '.join(missing_android_surfaces)}"
                )

        if bootstrap_status == "ready":
            if target.slug == "proof-node-api":
                with tempfile.TemporaryDirectory(prefix="scafforge-node-missing-") as tool_dir:
                    tool_path = Path(tool_dir)
                    git_path = shutil.which("git")
                    if git_path is not None:
                        (tool_path / "git").symlink_to(git_path)
                    node_missing_env = os.environ.copy()
                    node_missing_env["PATH"] = str(tool_path)
                    node_missing_audit = run_json(
                        [
                            sys.executable,
                            str(AUDIT),
                            str(dest),
                            "--format",
                            "json",
                            "--no-diagnosis-pack",
                        ],
                        ROOT,
                        env=node_missing_env,
                    )
                    node_missing_findings = [
                        item
                        for item in node_missing_audit.get("findings", [])
                        if isinstance(item, dict)
                    ]
                    if not any(item.get("code") == "ENV001" for item in node_missing_findings):
                        raise RuntimeError(
                            f"Proof target `{target.slug}` should report a truthful environment blocker when Node.js is missing from PATH."
                        )

            audit_payload = run_json(
                [
                    sys.executable,
                    str(AUDIT),
                    str(dest),
                    "--format",
                    "json",
                    "--no-diagnosis-pack",
                ],
                ROOT,
            )
            verify_payload = run_json(
                [sys.executable, str(VERIFY_GENERATED), str(dest), "--format", "json"],
                ROOT,
            )
            code_quality_findings = [
                item
                for item in audit_payload.get("findings", [])
                if isinstance(item, dict)
                and (
                    str(item.get("code", "")).startswith("EXEC")
                    or str(item.get("code", "")).startswith("REF")
                )
            ]
            if (
                verify_payload.get("verification_passed") is not True
                or verify_payload.get("finding_count") != 0
            ):
                raise RuntimeError(
                    f"Proof target `{target.slug}` should pass greenfield verification after successful bootstrap."
                )
            if code_quality_findings:
                raise RuntimeError(
                    f"Proof target `{target.slug}` should not emit EXEC/REF findings on a clean minimal target; observed {', '.join(str(item.get('code')) for item in code_quality_findings)}."
                )
            if target.release_check is not None:
                target.release_check(dest)
        else:
            if not blockers and not missing:
                raise RuntimeError(
                    f"Proof target `{target.slug}` should fail bootstrap only when it can explain the missing prerequisite or blocker."
                )


def contract_edge_case_integration(workspace: Path) -> None:
    remediation_dest = workspace / "remediation-review-contract"
    bootstrap_full(remediation_dest)

    manifest_path = remediation_dest / "tickets" / "manifest.json"
    registry_path = remediation_dest / ".opencode" / "state" / "artifacts" / "registry.json"
    manifest = read_json(manifest_path)
    registry = read_json(registry_path)
    if not isinstance(manifest, dict) or not isinstance(registry, dict):
        raise RuntimeError("Contract edge-case integration expected scaffolded manifest and artifact registry.")

    manifest.setdefault("tickets", []).append(
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
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

    _register_ticket_artifact(
        remediation_dest,
        ticket_id="EXEC-001-FIX",
        kind="review",
        stage="review",
        relative_path=".opencode/state/artifacts/history/review/EXEC-001-FIX-review.md",
        summary="APPROVED",
        content="# Review\n\n- Verdict: PASS\n- Notes: import surface looks fixed.\n",
    )
    remediation_audit = run_json(
        [
            sys.executable,
            str(AUDIT),
            str(remediation_dest),
            "--format",
            "json",
            "--no-diagnosis-pack",
        ],
        ROOT,
    )
    remediation_codes = extract_audit_codes(remediation_audit)
    if "EXEC-REMED-001" not in remediation_codes:
        raise RuntimeError(
            "Integration audit should flag remediation review artifacts that lack command/output/result evidence."
        )

    broken_venv_dest = workspace / "broken-venv-contract"
    bootstrap_full(broken_venv_dest)
    seed_python_cli_target(broken_venv_dest)
    broken_python = repo_python_interpreter_path(broken_venv_dest)
    broken_python.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        broken_python.write_bytes(b"")
    else:
        broken_python.write_text("#!/usr/bin/env sh\nexit 127\n", encoding="utf-8")
        broken_python.chmod(broken_python.stat().st_mode | 0o111)
    broken_venv_audit = run_json(
        [
            sys.executable,
            str(AUDIT),
            str(broken_venv_dest),
            "--format",
            "json",
            "--no-diagnosis-pack",
        ],
        ROOT,
    )
    broken_venv_codes = extract_audit_codes(broken_venv_audit)
    if "EXEC-ENV-001" not in broken_venv_codes:
        raise RuntimeError(
            "Integration audit should classify a broken repo-local Python virtual environment as EXEC-ENV-001."
        )
    unexpected_exec_codes = sorted(
        code for code in broken_venv_codes if code.startswith("EXEC") and code != "EXEC-ENV-001"
    )
    if unexpected_exec_codes:
        raise RuntimeError(
            "Broken-venv integration should stop at environment classification before emitting other EXEC findings; "
            f"observed {', '.join(unexpected_exec_codes)}"
        )


def _register_ticket_artifact(
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
        "created_at": "2026-04-02T00:00:00Z",
        "trust_state": "current",
    }
    ticket = next(item for item in manifest["tickets"] if item["id"] == ticket_id)
    ticket.setdefault("artifacts", []).append(artifact)
    registry.setdefault("artifacts", []).append({"ticket_id": ticket_id, **artifact})
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


def _stage_ticket_and_approve_plan(dest: Path, ticket_id: str, stage: str) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    ticket = next(item for item in manifest["tickets"] if item["id"] == ticket_id)
    ticket["stage"] = stage
    ticket["status"] = stage
    workflow.setdefault("ticket_state", {}).setdefault(ticket_id, {})[
        "approved_plan"
    ] = True
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")


def backward_transition_integration(workspace: Path) -> None:
    base = workspace / "backward-transition-base"
    bootstrap_full(base)
    manifest = json.loads(
        (base / "tickets" / "manifest.json").read_text(encoding="utf-8")
    )
    ticket_id = manifest["tickets"][0]["id"]
    slug = ticket_id.lower().replace("-", "")

    # --- review FAIL -> implementation: must be ALLOWED ---
    review_fail_dest = workspace / "backward-review-fail"
    shutil.copytree(base, review_fail_dest)
    _stage_ticket_and_approve_plan(review_fail_dest, ticket_id, "review")
    _register_ticket_artifact(
        review_fail_dest,
        ticket_id=ticket_id,
        kind="review",
        stage="review",
        relative_path=f".opencode/state/reviews/{slug}-review.md",
        summary="FAIL review for backward routing coverage.",
        content="# Review\n\nVerdict: FAIL\n\nBlocker: implementation defect must be fixed before re-review.\n",
    )
    review_fail_result = run_generated_tool(
        review_fail_dest,
        ".opencode/tools/ticket_update.ts",
        {"ticket_id": ticket_id, "stage": "implementation"},
    )
    if review_fail_result["updated_ticket"]["stage"] != "implementation":
        raise RuntimeError(
            "ticket_update should allow backward routing from review to implementation when latest verdict is FAIL"
        )

    # --- review PASS -> implementation: must be BLOCKED ---
    review_pass_dest = workspace / "backward-review-pass"
    shutil.copytree(base, review_pass_dest)
    _stage_ticket_and_approve_plan(review_pass_dest, ticket_id, "review")
    _register_ticket_artifact(
        review_pass_dest,
        ticket_id=ticket_id,
        kind="review",
        stage="review",
        relative_path=f".opencode/state/reviews/{slug}-review.md",
        summary="PASS review — backward routing should be blocked.",
        content="# Review\n\nVerdict: PASS\n\nAll review criteria satisfied.\n",
    )
    review_pass_error = run_generated_tool_error(
        review_pass_dest,
        ".opencode/tools/ticket_update.ts",
        {"ticket_id": ticket_id, "stage": "implementation"},
    )
    if "not a blocking verdict" not in review_pass_error:
        raise RuntimeError(
            "ticket_update should block backward routing from review to implementation when verdict is PASS"
        )

    # --- qa BLOCKED -> implementation: must be ALLOWED ---
    qa_fail_dest = workspace / "backward-qa-fail"
    shutil.copytree(base, qa_fail_dest)
    _stage_ticket_and_approve_plan(qa_fail_dest, ticket_id, "qa")
    _register_ticket_artifact(
        qa_fail_dest,
        ticket_id=ticket_id,
        kind="qa",
        stage="qa",
        relative_path=f".opencode/state/qa/{slug}-qa.md",
        summary="BLOCKED QA verdict for backward routing coverage.",
        content="# QA\n\nResult: BLOCKED\n\nCommand: pytest tests/\n\n~~~~text\nAssertionError: test failure\n~~~~\n\nBlocker must be fixed before smoke-test.\n",
    )
    qa_fail_result = run_generated_tool(
        qa_fail_dest,
        ".opencode/tools/ticket_update.ts",
        {"ticket_id": ticket_id, "stage": "implementation"},
    )
    if qa_fail_result["updated_ticket"]["stage"] != "implementation":
        raise RuntimeError(
            "ticket_update should allow backward routing from qa to implementation when verdict is BLOCKED"
        )

    # --- qa PASS -> implementation: must be BLOCKED ---
    qa_pass_dest = workspace / "backward-qa-pass"
    shutil.copytree(base, qa_pass_dest)
    _stage_ticket_and_approve_plan(qa_pass_dest, ticket_id, "qa")
    _register_ticket_artifact(
        qa_pass_dest,
        ticket_id=ticket_id,
        kind="qa",
        stage="qa",
        relative_path=f".opencode/state/qa/{slug}-qa.md",
        summary="PASS QA verdict — backward routing should be blocked.",
        content="# QA\n\nResult: PASS\n\nAll QA criteria satisfied.\n",
    )
    qa_pass_error = run_generated_tool_error(
        qa_pass_dest,
        ".opencode/tools/ticket_update.ts",
        {"ticket_id": ticket_id, "stage": "implementation"},
    )
    if "not a blocking verdict" not in qa_pass_error:
        raise RuntimeError(
            "ticket_update should block backward routing from qa to implementation when verdict is PASS"
        )


def main() -> int:
    args = parse_args()
    fixtures = ensure_fixture_index()
    downstream_fixtures = ensure_downstream_fixture_indexes()
    asset_fixtures = ensure_asset_fixture_index()
    visual_proof_fixtures = ensure_visual_proof_fixture_index()
    if args.list_fixtures:
        listing = {"gpttalker": sorted(fixtures)}
        for corpus_slug, (_, corpus_fixtures) in downstream_fixtures.items():
            listing[corpus_slug] = sorted(corpus_fixtures)
        listing["assets"] = sorted(asset_fixtures)
        listing["visual-proof"] = sorted(visual_proof_fixtures)
        print(json.dumps(listing, indent=2))
        return 0
    with tempfile.TemporaryDirectory(prefix="scafforge-integration-") as workspace_root:
        workspace = Path(workspace_root)
        greenfield_integration(workspace)
        repair_integration(workspace)
        pivot_integration(workspace)
        multi_stack_proof_integration(workspace)
        contract_edge_case_integration(workspace)
        backward_transition_integration(workspace)
        fixture_builder_integration(
            corpus_name="gpttalker",
            fixtures=fixtures,
            workspace=workspace,
            build_fixture=build_fixture_family,
            contract_path=".opencode/meta/gpttalker-fixture.json",
        )
        for corpus_slug, (corpus, corpus_fixtures) in downstream_fixtures.items():
            fixture_builder_integration(
                corpus_name=corpus_slug,
                fixtures=corpus_fixtures,
                workspace=workspace,
                build_fixture=lambda slug, dest, corpus_slug=corpus_slug: build_downstream_fixture_family(corpus_slug, slug, dest),
                contract_path=corpus.contract_path,
            )
        asset_fixture_integration(
            fixtures=asset_fixtures,
            workspace=workspace,
        )
        visual_proof_fixture_integration(
            fixtures=visual_proof_fixtures,
            workspace=workspace,
        )
        synthetic_edge_case_integration(workspace)
    print("Scafforge integration test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
