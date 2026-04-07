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
    expected_android_debug_apk_relpath,
    has_android_export_preset,
    has_android_support_surfaces,
    load_manifest,
    release_lane_started_or_done,
    repo_claims_completion,
)


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
    for match in re.finditer(r"^autoload/[^=]+=.*res://([^\n\"]+)", project_text, re.MULTILINE):
        target = root / match.group(1)
        if not target.exists():
            missing_autoloads.append(match.group(1))
    if missing_autoloads:
        _add_execution_finding(findings, ctx, code="EXEC-GODOT-001", severity="error", problem="Godot autoload registration references missing scripts.", root_cause="project.godot points at autoload paths that do not exist in the repo, so project startup will fail or load an incomplete runtime graph.", files=[project_file], safer_pattern="Validate every project.godot autoload path against the repo tree before handoff or audit closeout.", evidence=missing_autoloads, root=root)

    broken_scene_refs: list[str] = []
    for path in list(root.rglob("*.tscn")) + list(root.rglob("*.tres")):
        text = ctx.read_text(path)
        for match in re.finditer(r'res://([^"\n]+\.(?:gd|cs|tscn|tres))', text):
            target = root / match.group(1)
            if not target.exists():
                broken_scene_refs.append(f"{ctx.normalize_path(path, root)} -> res://{match.group(1)}")
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

    godot_cmd = next((candidate for candidate in ("godot4", "godot") if _command_available(candidate)), None)
    if godot_cmd:
        rc, output = ctx.run_command([godot_cmd, "--headless", "--path", ".", "--quit"], root, 120)
        if rc != 0:
            _add_execution_finding(findings, ctx, code="EXEC-GODOT-004", severity="error", problem="Godot headless validation fails.", root_cause="The project cannot complete a deterministic headless Godot load pass on the current host, indicating broken project configuration or scripts.", files=[project_file], safer_pattern="Run a deterministic `godot --headless --path . --quit` validation during audit and keep the repo blocked until it succeeds or returns an explicit environment blocker instead.", evidence=_collect_first_error_lines(output), root=root)

    manifest = load_manifest(root)
    if not declares_godot_android_target(root):
        return
    if not (release_lane_started_or_done(manifest) or repo_claims_completion(manifest)):
        return

    missing_surfaces: list[str] = []
    if not has_android_export_preset(root):
        missing_surfaces.append("export_presets.cfg Android preset")
    if not has_android_support_surfaces(root):
        missing_surfaces.append("repo-local android support surfaces")
    apk_path = debug_apk_path(root)
    if apk_path is None:
        missing_surfaces.append(f"debug APK proof at {expected_android_debug_apk_relpath(root)}")
    if not missing_surfaces:
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
    ctx.add_finding(
        findings,
        Finding(
            code="EXEC-GODOT-005",
            severity="error",
            problem="Android-targeted Godot repo still lacks export surfaces or debug APK proof while the repo claims release progress or completion.",
            root_cause="The repo treats Android delivery as complete enough to close or advance release-facing work, but the canonical export preset, repo-local Android support surfaces, or debug APK artifact proof are still missing.",
            files=list(dict.fromkeys(files)),
            safer_pattern="Keep Godot Android repos blocked on explicit export surfaces plus debug APK proof. Once release work starts or the repo claims completion, require `export_presets.cfg`, non-placeholder `android/` support surfaces, and a debug APK at the canonical build path.",
            evidence=[
                f"open_ticket_count = {open_ticket_count}",
                f"release_lane_started_or_done = {release_lane_started_or_done(manifest)}",
                f"repo_claims_completion = {repo_claims_completion(manifest)}",
                f"missing Android delivery surfaces: {', '.join(missing_surfaces)}",
            ],
            provenance="script",
        ),
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


def audit_reference_integrity(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    scene_missing: list[str] = []
    for path in list(root.rglob("*.tscn")) + list(root.rglob("*.tres")):
        text = ctx.read_text(path)
        for match in re.finditer(r'res://([^"\n]+\.(?:gd|cs))', text):
            target = root / match.group(1)
            if not target.exists():
                scene_missing.append(f"{ctx.normalize_path(path, root)} -> res://{match.group(1)}")
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
    for path in list(root.rglob("*.py")) + list(root.rglob("*.ts")) + list(root.rglob("*.tsx")) + list(root.rglob("*.js")) + list(root.rglob("*.jsx")):
        text = ctx.read_text(path)
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
    audit_smoke_test_contract(root, findings, ctx)
    audit_smoke_test_override_contract(root, findings, ctx)
    audit_smoke_test_acceptance_contract(root, findings, ctx)
    audit_environment_prerequisites(root, findings, ctx)
    audit_python_execution(root, findings, ctx)
    audit_node_execution(root, findings, ctx)
    audit_rust_execution(root, findings, ctx)
    audit_go_execution(root, findings, ctx)
    audit_godot_execution(root, findings, ctx)
    audit_java_android_execution(root, findings, ctx)
    audit_cpp_execution(root, findings, ctx)
    audit_dotnet_execution(root, findings, ctx)
    audit_reference_integrity(root, findings, ctx)
