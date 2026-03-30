from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
from typing import Any, Callable

from shared_verifier_types import Finding


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


def run_execution_surface_audits(root: Path, findings: list[Finding], ctx: ExecutionSurfaceAuditContext) -> None:
    audit_bootstrap_command_layout_mismatch(root, findings, ctx)
    audit_bootstrap_deadlock(root, findings, ctx)
    audit_smoke_test_contract(root, findings, ctx)
    audit_smoke_test_override_contract(root, findings, ctx)
    audit_smoke_test_acceptance_contract(root, findings, ctx)
    audit_environment_prerequisites(root, findings, ctx)
    audit_python_execution(root, findings, ctx)
