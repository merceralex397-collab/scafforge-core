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

from test_support.gpttalker_fixture_builders import build_fixture_family, fixture_index_by_slug
from test_support.repo_seeders import make_stack_skill_non_placeholder, read_json, seed_failing_pytest_suite, seed_ready_bootstrap
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
    run,
    run_generated_tool,
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
    runtime_check: Callable[[Path], None] | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run focused end-to-end Scafforge integration coverage for greenfield, repair, pivot, and GPTTalker fixture families."
    )
    parser.add_argument("--list-fixtures", action="store_true", help="Print the curated GPTTalker fixture slugs and exit.")
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
        "repeated-lifecycle-contradiction",
        "restart-surface-drift-after-repair",
        "placeholder-skill-after-refresh",
        "split-scope-and-historical-trust-reconciliation",
    }
    if set(indexed) != expected:
        raise RuntimeError(f"Fixture index slugs do not match the curated GPTTalker family set: {sorted(indexed)}")
    return indexed


def bootstrap_full(dest: Path) -> None:
    bootstrap_scaffold(dest, project_name="Integration Probe", project_slug="integration-probe", agent_prefix="integration-probe", stack_label="framework-agnostic")


def bootstrap_scaffold(
    dest: Path,
    *,
    project_name: str,
    project_slug: str,
    agent_prefix: str,
    stack_label: str,
) -> None:
    run(
        [
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
        ],
        ROOT,
    )


def require_host_prerequisite(name: str, *, context: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"{context} requires `{name}` to be available on the current host.")
    return path


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_executable_wrapper(path: Path, target: str) -> None:
    write_text(path, f"#!/usr/bin/env sh\nexec {target} \"$@\"\n")
    path.chmod(path.stat().st_mode | 0o111)


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


def run_checked(command: list[str], cwd: Path, *, timeout: int = 120) -> None:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def seed_python_cli_target(dest: Path) -> None:
    replace_stack_skill_placeholder(dest, "Use repo-local Python execution and validate with `python -m pytest -q` before closeout.")
    write_executable_wrapper(dest / ".venv" / "bin" / "python", sys.executable)
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
            ]
        )
        + "\n",
    )
    write_text(dest / "requirements.txt", "# Proof target requirements are provided by pyproject.toml\n")
    write_text(dest / "src" / "__init__.py", "")
    write_text(
        dest / "src" / "proof_python_cli" / "__init__.py",
        "def format_message(name: str) -> str:\n    return f\"Hello, {name}!\"\n",
    )
    write_text(
        dest / "src" / "proof_python_cli" / "__main__.py",
        "\n".join(
            [
                "import argparse",
                "",
                "from src.proof_python_cli import format_message",
                "",
                "",
                "def main() -> int:",
                "    parser = argparse.ArgumentParser(description=\"Python CLI proof target\")",
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
        "from src.proof_python_cli import format_message\n\n\ndef test_format_message() -> None:\n    assert format_message('proof') == 'Hello, proof!'\n",
    )


def seed_node_api_target(dest: Path) -> None:
    replace_stack_skill_placeholder(dest, "Use `npm test` for validation and keep the generated HTTP entry point loadable through `node`.")
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
    replace_stack_skill_placeholder(dest, "Use `cargo test` and `cargo build` as the canonical Rust validation commands.")
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
                'use std::io::{self, Read};',
                "",
                "fn main() {",
                "    let args: Vec<String> = std::env::args().collect();",
                "    if args.iter().any(|arg| arg == \"--help\") {",
                "        println!(\"usage: proof_rust_cli [--help]\");",
                "        return;",
                "    }",
                "    let mut input = String::new();",
                "    io::stdin().read_to_string(&mut input).unwrap();",
                "    println!(\"{}\", input.trim().to_uppercase());",
                "}",
            ]
        )
        + "\n",
    )


def seed_go_http_target(dest: Path) -> None:
    replace_stack_skill_placeholder(dest, "Use `go vet ./...`, `go test ./...`, and `go build ./...` as the Go proof commands.")
    write_text(dest / "go.mod", "module example.com/proof-go-http\n\ngo 1.22\n")
    write_text(
        dest / "main.go",
        "\n".join(
            [
                "package main",
                "",
                'import (',
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
    replace_stack_skill_placeholder(dest, "Use `godot --headless --check-only` and `godot --headless --script res://check.gd --quit` when Godot is available.")
    write_text(
        dest / "project.godot",
        "\n".join(
            [
                "; Engine configuration file.",
                "config_version=5",
                "",
                "[application]",
                'config/name="Proof Godot"',
                'run/main_scene="res://scenes/main.tscn"',
                "",
                "[autoload]",
                'GameState="*res://scripts/autoload/GameState.gd"',
            ]
        )
        + "\n",
    )
    write_text(dest / "scripts" / "autoload" / "GameState.gd", "extends Node\n")
    write_text(dest / "scripts" / "main.gd", "extends Node2D\n")
    write_text(
        dest / "scenes" / "main.tscn",
        "\n".join(
            [
                "[gd_scene load_steps=2 format=3]",
                "",
                "[ext_resource type=\"Script\" path=\"res://scripts/main.gd\" id=\"1\"]",
                "",
                "[node name=\"Main\" type=\"Node2D\"]",
                "script = ExtResource(\"1\")",
            ]
        )
        + "\n",
    )
    write_text(dest / "check.gd", "extends SceneTree\n\nfunc _init():\n    quit()\n")


def seed_cmake_target(dest: Path) -> None:
    replace_stack_skill_placeholder(dest, "Use `cmake -S . -B build` and `cmake --build build` as the canonical native proof commands.")
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
    write_text(dest / "src" / "lib.c", '#include "lib.h"\n\nint add(int left, int right) { return left + right; }\n')
    write_text(
        dest / "test" / "test_lib.c",
        '#include "lib.h"\n\nint main(void) { return add(1, 1) == 2 ? 0 : 1; }\n',
    )


def seed_dotnet_target(dest: Path) -> None:
    replace_stack_skill_placeholder(dest, "Use `dotnet build --no-restore`, `dotnet test --no-build --list-tests`, and `dotnet run --no-build` for .NET validation.")
    write_text(
        dest / "ProofConsole.csproj",
        "\n".join(
            [
                '<Project Sdk="Microsoft.NET.Sdk">',
                '  <PropertyGroup>',
                '    <OutputType>Exe</OutputType>',
                '    <TargetFramework>net8.0</TargetFramework>',
                '    <ImplicitUsings>enable</ImplicitUsings>',
                '    <Nullable>enable</Nullable>',
                '  </PropertyGroup>',
                '</Project>',
            ]
        )
        + "\n",
    )
    write_text(
        dest / "Program.cs",
        "using System;\n\nif (args.Length > 0 && args[0] == \"--help\")\n{\n    Console.WriteLine(\"usage: dotnet run --no-build [--help]\");\n    return;\n}\n\nConsole.WriteLine(\"proof-dotnet-ready\");\n",
    )


def seed_java_gradle_target(dest: Path) -> None:
    replace_stack_skill_placeholder(dest, "Use Gradle dry-run and build checks as the canonical Java proof commands.")
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
        "public class Main {\n    public static void main(String[] args) {\n        if (args.length > 0 && \"--help\".equals(args[0])) {\n            System.out.println(\"usage: gradle run --args=--help\");\n            return;\n        }\n        System.out.println(\"proof-java-ready\");\n    }\n}\n",
    )


def python_runtime_check(dest: Path) -> None:
    python = command_exists("python3", "python")
    if python:
        run_checked([python, "-m", "src.proof_python_cli", "--help"], dest)


def node_runtime_check(dest: Path) -> None:
    if command_exists("node"):
        run_checked(["node", "dist/index.js", "--help"], dest)


def rust_runtime_check(dest: Path) -> None:
    if command_exists("cargo"):
        run_checked(["cargo", "build"], dest, timeout=180)


def go_runtime_check(dest: Path) -> None:
    if command_exists("go"):
        run_checked(["go", "build", "."], dest, timeout=180)


def godot_runtime_check(dest: Path) -> None:
    godot = command_exists("godot4", "godot")
    if godot:
        run_checked([godot, "--headless", "--script", "res://check.gd", "--quit"], dest, timeout=180)


def cmake_runtime_check(dest: Path) -> None:
    if command_exists("cmake"):
        build_dir = dest / "build"
        run_checked(["cmake", "-S", ".", "-B", str(build_dir)], dest, timeout=180)
        run_checked(["cmake", "--build", str(build_dir)], dest, timeout=180)


def dotnet_runtime_check(dest: Path) -> None:
    if command_exists("dotnet"):
        run_checked(["dotnet", "run", "--no-build"], dest, timeout=180)


def java_runtime_check(dest: Path) -> None:
    if (dest / "gradlew").exists():
        run_checked(["./gradlew", "build"], dest, timeout=180)
    elif command_exists("gradle"):
        run_checked(["gradle", "build"], dest, timeout=180)


def multi_stack_targets() -> list[ProofTarget]:
    return [
        ProofTarget("proof-python-cli", "Proof Python CLI", "python-cli", "python", ("pytest",), seed_python_cli_target, python_runtime_check),
        ProofTarget("proof-node-api", "Proof Node API", "node-api", "node", ("npm", "test"), seed_node_api_target, node_runtime_check),
        ProofTarget("proof-rust-cli", "Proof Rust CLI", "rust-cli", "rust", ("cargo test",), seed_rust_cli_target, rust_runtime_check),
        ProofTarget("proof-go-http", "Proof Go HTTP", "go-http", "go", ("go test",), seed_go_http_target, go_runtime_check),
        ProofTarget("proof-godot", "Proof Godot", "godot", "godot", ("godot", "headless"), seed_godot_target, godot_runtime_check),
        ProofTarget("proof-cmake", "Proof CMake", "c-cpp", "c-cpp", ("cmake",), seed_cmake_target, cmake_runtime_check),
        ProofTarget("proof-dotnet", "Proof Dotnet", "dotnet", "dotnet", ("dotnet", "test\\b"), seed_dotnet_target, dotnet_runtime_check),
        ProofTarget("proof-java", "Proof Java", "java-gradle", "java-android", ("gradle",), seed_java_gradle_target, java_runtime_check),
    ]


def seed_prompt_drift(dest: Path) -> None:
    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    text = team_leader.read_text(encoding="utf-8")
    text = text.replace("next_action_tool", "legacy_next_action_tool")
    text = text.replace("summary-only stopping is invalid", "summary-only stopping may happen")
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
        raise RuntimeError("Greenfield integration should run the bootstrap-lane verifier before specialization.")
    if bootstrap_lane.get("bootstrap_lane_valid") is not True:
        raise RuntimeError("Greenfield integration should preserve one valid bootstrap lane immediately after scaffold render.")
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
        raise RuntimeError("Greenfield integration should run the continuation verifier.")
    if payload.get("immediately_continuable") is not True or payload.get("finding_count") != 0:
        raise RuntimeError("Greenfield integration should prove the generated repo is immediately continuable once placeholder drift is removed.")


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
        raise RuntimeError(f"Repair integration expected follow-on stages {sorted(expected_required)}, found {sorted(required)}")
    tracking_path = dest / ".opencode" / "meta" / "repair-follow-on-state.json"
    tracking_state = read_json(tracking_path)
    if not isinstance(tracking_state, dict):
        raise RuntimeError("Repair integration expected persistent follow-on tracking state.")
    cycle_id = tracking_state.get("cycle_id")
    if not isinstance(cycle_id, str) or not cycle_id:
        raise RuntimeError("Repair integration expected a non-empty repair cycle id.")
    provenance_evidence_rel = ".opencode/state/artifacts/history/repair/provenance-probe.md"
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
        raise RuntimeError("Repair integration should reject recorded completion when repair-package provenance is missing.")
    combined_provenance_output = f"{missing_provenance_record.stdout}\n{missing_provenance_record.stderr}"
    if "requires repair_package_commit provenance" not in combined_provenance_output or "missing_provenance" not in combined_provenance_output:
        raise RuntimeError("Repair integration should explain missing provenance when recorded completion is rejected.")
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
    recorded_before_fix = set(artifact_recorded["execution_record"]["recorded_execution_completed_stages"])
    expected_recorded = expected_required | {"handoff-brief"}
    if recorded_before_fix != expected_recorded:
        raise RuntimeError(f"Repair integration expected recorded completion for {sorted(expected_recorded)}, found {sorted(recorded_before_fix)}")
    if not artifact_recorded["execution_record"]["blocking_reasons"]:
        raise RuntimeError("Repair integration should stay managed-blocked while placeholder skill and prompt drift still exist.")
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
    if set(converged["execution_record"]["recorded_execution_completed_stages"]) != expected_recorded:
        raise RuntimeError("Repair integration should preserve recorded completion for all routed follow-on stages.")
    outcome = converged["execution_record"]["repair_follow_on_outcome"]
    if outcome not in {"managed_blocked", "source_follow_up"}:
        raise RuntimeError(f"Repair integration should classify the post-follow-on state truthfully; observed unexpected outcome `{outcome}`.")
    if outcome == "source_follow_up":
        if converged["execution_record"]["handoff_allowed"] is not True:
            raise RuntimeError("Repair integration should allow handoff once only source follow-up remains.")
    else:
        if not converged["execution_record"]["blocking_reasons"]:
            raise RuntimeError("Repair integration should preserve managed-blocked reasons when workflow findings still remain after recorded follow-on completion.")


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
        raise RuntimeError("Pivot integration should pass the post-pivot verification gate on a clean generated repo.")
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
    restart_inputs = state.get("restart_surface_inputs") if isinstance(state, dict) else None
    if not isinstance(restart_inputs, dict) or restart_inputs.get("pivot_in_progress") is not False:
        raise RuntimeError("Pivot integration should clear pivot_in_progress once all routed downstream stages are completed.")
    if restart_inputs.get("pending_downstream_stages") not in ([], None):
        raise RuntimeError("Pivot integration should not leave pending downstream stages after all recorded completions.")
    if published["restart_surface_publication"]["status"] != "published":
        raise RuntimeError("Pivot integration should republish restart surfaces after pivot completion.")


def fixture_builder_integration(fixtures: dict[str, dict[str, Any]], workspace: Path) -> None:
    fixture_root = workspace / "gpttalker-fixtures"
    for slug in sorted(fixtures):
        dest = fixture_root / slug
        contract = build_fixture_family(slug, dest)
        if contract.get("slug") != slug:
            raise RuntimeError(f"Fixture builder should persist the canonical slug for `{slug}`.")
        if not isinstance(contract.get("expected_coverage"), list) or not contract["expected_coverage"]:
            raise RuntimeError(f"Fixture builder should persist expected coverage for `{slug}`.")
        contract_path = dest / ".opencode" / "meta" / "gpttalker-fixture.json"
        if not contract_path.exists():
            raise RuntimeError(f"Fixture builder should emit .opencode/meta/gpttalker-fixture.json for `{slug}`.")
        expected_finding_codes = contract.get("expected_finding_codes")
        if not isinstance(expected_finding_codes, list) or not expected_finding_codes:
            raise RuntimeError(f"Fixture builder should persist expected_finding_codes for `{slug}`.")
        command = [sys.executable, str(AUDIT), str(dest), "--format", "json", "--no-diagnosis-pack"]
        supporting_log = contract.get("supporting_log")
        if isinstance(supporting_log, str) and supporting_log.strip():
            command.extend(["--supporting-log", str(dest / supporting_log)])
        audit_payload = run_json(
            command,
            ROOT,
        )
        if not isinstance(audit_payload.get("findings"), list) or audit_payload.get("finding_count", 0) <= 0:
            raise RuntimeError(f"Fixture `{slug}` should produce actionable audit findings, not a no-op repo.")
        audit_codes = {
            str(item.get("code", "")).strip()
            for item in audit_payload.get("findings", [])
            if isinstance(item, dict) and str(item.get("code", "")).strip()
        }
        missing_codes = [code for code in expected_finding_codes if isinstance(code, str) and code not in audit_codes]
        if missing_codes:
            raise RuntimeError(
                f"Fixture `{slug}` did not trigger its declared invariant finding codes. Missing: {', '.join(missing_codes)}; "
                f"observed: {', '.join(sorted(audit_codes)) or 'none'}"
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

        smoke_test_text = (dest / ".opencode" / "tools" / "smoke_test.ts").read_text(encoding="utf-8")
        for snippet in target.smoke_snippets:
            if snippet not in smoke_test_text:
                raise RuntimeError(f"Proof target `{target.slug}` expected smoke_test.ts to reference `{snippet}`.")

        bootstrap_result = run_generated_tool(dest, ".opencode/tools/environment_bootstrap.ts", {})
        detections = bootstrap_result.get("detections")
        if not isinstance(detections, list) or target.adapter_id not in {item.get("adapter_id") for item in detections if isinstance(item, dict)}:
            raise RuntimeError(f"Proof target `{target.slug}` should detect adapter `{target.adapter_id}` during environment bootstrap.")

        bootstrap_status = bootstrap_result.get("bootstrap_status")
        blockers = bootstrap_result.get("blockers") if isinstance(bootstrap_result.get("blockers"), list) else []
        missing = bootstrap_result.get("missing_prerequisites") if isinstance(bootstrap_result.get("missing_prerequisites"), list) else []

        if bootstrap_status == "ready":
            audit_payload = run_json(
                [sys.executable, str(AUDIT), str(dest), "--format", "json", "--no-diagnosis-pack"],
                ROOT,
            )
            verify_payload = run_json(
                [sys.executable, str(VERIFY_GENERATED), str(dest), "--format", "json"],
                ROOT,
            )
            code_quality_findings = [
                item
                for item in audit_payload.get("findings", [])
                if isinstance(item, dict) and (str(item.get("code", "")).startswith("EXEC") or str(item.get("code", "")).startswith("REF"))
            ]
            if verify_payload.get("verification_passed") is not True or verify_payload.get("finding_count") != 0:
                raise RuntimeError(f"Proof target `{target.slug}` should pass greenfield verification after successful bootstrap.")
            if code_quality_findings:
                raise RuntimeError(
                    f"Proof target `{target.slug}` should not emit EXEC/REF findings on a clean minimal target; observed {', '.join(str(item.get('code')) for item in code_quality_findings)}."
                )
            if target.runtime_check is not None:
                target.runtime_check(dest)
        else:
            if not blockers and not missing:
                raise RuntimeError(
                    f"Proof target `{target.slug}` should fail bootstrap only when it can explain the missing prerequisite or blocker."
                )


def main() -> int:
    args = parse_args()
    fixtures = ensure_fixture_index()
    if args.list_fixtures:
        print(json.dumps(sorted(fixtures), indent=2))
        return 0
    with tempfile.TemporaryDirectory(prefix="scafforge-integration-") as workspace_root:
        workspace = Path(workspace_root)
        greenfield_integration(workspace)
        repair_integration(workspace)
        pivot_integration(workspace)
        multi_stack_proof_integration(workspace)
        fixture_builder_integration(fixtures, workspace)
    print("Scafforge integration test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
