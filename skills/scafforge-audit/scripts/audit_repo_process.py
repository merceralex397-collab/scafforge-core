from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_contract_surfaces import ContractSurfaceAuditContext, run_contract_surface_audits
from audit_config_surfaces import ConfigSurfaceAuditContext, run_config_surface_audits
from audit_execution_surfaces import ExecutionSurfaceAuditContext, run_execution_surface_audits
from audit_lifecycle_contracts import LifecycleContractAuditContext, run_lifecycle_contract_audits
from audit_repair_cycles import RepairCycleAuditContext, run_repair_cycle_audits
from audit_reporting import (
    AuditReportingContext,
    DIAGNOSIS_REPORTS,
    emit_diagnosis_pack as emit_diagnosis_pack_impl,
    render_markdown,
    resolve_current_package_commit,
    select_diagnosis_destination,
)
from disposition_bundle import (
    bundle_repair_routed_codes,
    bundle_shadow_mode_deltas,
    bundle_source_follow_up_codes,
    disposition_class_for_finding,
    legacy_disposition_class_for_finding,
    load_disposition_bundle,
)
from audit_session_transcripts import SessionTranscriptAuditContext, run_session_transcript_audits
from audit_restart_surfaces import RestartSurfaceAuditContext, run_restart_surface_audits
from audit_ticket_graph import TicketGraphAuditContext, run_ticket_graph_audits
from shared_verifier_types import Finding

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None  # type: ignore[assignment]


COARSE_STATUSES = {"todo", "ready", "plan_review", "in_progress", "blocked", "review", "qa", "smoke_test", "done"}
STAGE_LIKE_STATUSES = {"planned", "approved", "archived"}
MUTATING_SHELL_TOKENS = (
    '"sed *": allow',
    '"gofmt',
    '"python *": allow',
    '"node *": allow',
    '"npm *": allow',
    '"pnpm *": allow',
    '"yarn *": allow',
    '"bun *": allow',
    '"go *": allow',
    '"cargo *": allow',
    '"uv *": allow',
    '"make *": allow',
)
WRITE_LANGUAGE = (
    "update the ticket file",
    "write the plan to the file",
    "change line",
    "edit the ticket",
)
EAGER_SKILL_LOADING_PATTERNS = (
    r"(?im)^\s*load these skills:\s*$",
    r"(?im)^\s*load this skill:\s*$",
)
ARTIFACT_REGISTER_PERSIST_PATTERNS = (
    r"persist.+through `artifact_register`",
    r"persist.+with `artifact_register`",
    r"use `artifact_register` to persist",
    r"may persist their text",
)
ARTIFACT_PATH_DRIFT_PATTERNS = (
    r"\.opencode/state/artifacts/<ticket-id>/",
    r"\.opencode/state/artifacts/<ticket-id>/(planning|implementation|review|qa|handoff)\.md",
)
DEPRECATED_WORKFLOW_TERMS = ("ready_for_planning", "code_review", "security_review")
PLACEHOLDER_SKILL_PATTERNS = (
    r"Replace this file with stack-specific rules once the real project stack is known\.",
    r"When the repo stack is finalized, rewrite this catalog so review and QA agents get the exact build, lint, reference-integrity, and test commands that belong to this project\.",
    r"When the project stack is confirmed, replace this file's Universal Standards section with stack-specific rules using the `project-skill-bootstrap` skill\.",
    r"__STACK_LABEL__",
)
HANDOFF_OVERCLAIM_PATTERNS = (
    r"\bunblocked\b",
    r"not a code defect",
    r"only blocker",
    r"tool/env mismatch",
    r"tooling issue",
)
TRANSCRIPT_STALE_STATE_PATTERNS = (
    r"stage `planning`, status `ready`",
    r"approved_plan: false",
)
TRANSCRIPT_PROGRESS_PATTERNS = (
    r"126 tests collected",
    r"import succeeds",
    r"imports cleanly",
    r"collection passes",
    r"approved_plan` is now `true`",
)
TRANSCRIPT_FULL_SUITE_RESULT_PATTERNS = (
    r"\d+ failed, \d+ passed",
    r"pytest tests/ -q --tb=no` exits `1`",
    r"pytest tests/ -q --tb=no",
)
TRANSCRIPT_LIFECYCLE_ERROR_PATTERNS = (
    r"Cannot move .* to implementation before it passes through plan_review\.",
    r"Cannot move to qa before at least one review artifact exists\.",
    r"Cannot move to review before an implementation artifact exists\.",
)
TRANSCRIPT_SOFT_BYPASS_PATTERNS = (
    r"\bclose\b.{0,40}\banyway\b",
    r"\bdone\b.{0,20}\banyway\b",
    r"\bdespite the dependency\b",
    r"\bprocess\b.{0,40}\bdespite\b.{0,20}\bdependency\b",
    r"\bstart\b.{0,40}\bdependent\b.{0,40}\bfirst\b",
    r"\bknown issue\b.{0,40}\bclose(?:out)?\b",
    r"\bclose(?:out)?\b.{0,40}\bknown issue\b",
)
TRANSCRIPT_VERIFICATION_FAILURE_PATTERNS = (
    r"Unable to run verification commands",
    r"could not be executed",
    r"bash tool is blocked by permission rules",
    r"cannot run verification",
    r"couldn't run verification",
)
TRANSCRIPT_PASS_CLAIM_PATTERNS = (
    r"Verified by running",
    r"Result:\s*PASS",
    r"scoped fix VERIFIED",
    r"Scoped pytest passes",
    r"PASS \(scoped\)",
)
TRANSCRIPT_EXECUTION_RECOVERY_PATTERNS = (
    r"\b\d+\s+passed\b",
    r"\b0 failed\b",
    r"SYNTAX OK",
)
TRANSCRIPT_BROKEN_TOOL_PATTERNS = (
    r"def\.execute is not a function",
    r"def\.execute.*undefined",
)
TRANSCRIPT_SMOKE_OVERRIDE_FAILURE_PATTERNS = (
    r"posix_spawn '[_A-Za-z][_A-Za-z0-9]*=",
    r"ENOENT: no such file or directory, posix_spawn '[_A-Za-z][_A-Za-z0-9]*=",
)
TRANSCRIPT_SMOKE_ACCEPTANCE_PATTERNS = (
    r"`[^`\n]*pytest[^`\n]*`\s+exits 0",
    r"`[^`\n]*(?:cargo test|go test|ruff check|npm run test|pnpm run test|yarn test|bun run test)[^`\n]*`\s+exits 0",
)
TRANSCRIPT_HANDOFF_LEASE_CONTRADICTION_PATTERNS = (
    r"handoff_publish.*missing_ticket_write_lease",
    r"requires active lease on closed ticket",
    r"closed ticket cannot hold a lease",
)
TRANSCRIPT_ACCEPTANCE_SCOPE_TENSION_PATTERNS = (
    r"acceptance criterion.*exits 0",
    r"acceptance criteria.*exits 0",
    r"literal acceptance criterion",
    r"creates a tension",
    r"out of .* scope",
    r"pre-existing .* scope",
    r"handled by EXEC-\d+",
)
COORDINATOR_ARTIFACT_STAGES = {"planning", "implementation", "review", "qa", "smoke-test"}
DEPRECATED_MODEL_PATTERNS = (
    r"MiniMax-M2\.5",
    r"minimax-coding-plan/MiniMax-M2\.5",
)

@dataclass
class TranscriptToolEvent:
    assistant: str
    tool: str
    line_number: int
    args: dict[str, Any] | None
    output: str | None
    error: str | None


@dataclass
class InvocationLogEvent:
    event: str
    tool: str
    agent: str
    args: dict[str, Any] | None
    line_number: int


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def normalize_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def load_manifest_statuses(manifest: dict[str, Any]) -> list[str]:
    tickets = manifest.get("tickets")
    if isinstance(tickets, dict):
        return [str(ticket.get("status", "")).strip() for ticket in tickets.values() if isinstance(ticket, dict)]
    if isinstance(tickets, list):
        return [str(ticket.get("status", "")).strip() for ticket in tickets if isinstance(ticket, dict)]
    return []


def manifest_queue_keys(manifest: dict[str, Any]) -> list[str]:
    return [key for key in ("todo", "ready", "in_progress", "blocked", "review", "qa", "done", "completed", "later") if key in manifest]


def parse_status_semantics(text: str) -> dict[str, str]:
    semantics: dict[str, str] = {}
    for match in re.finditer(r"-\s+`([^`]+)`:\s+(.+)", text):
        semantics[match.group(1).strip()] = match.group(2).strip()
    return semantics


def ticket_markdown_status(path: Path) -> str | None:
    text = read_text(path)
    match = re.search(r"^status:\s*([A-Za-z0-9_/-]+)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_section_lines(text: str, heading: str) -> list[str]:
    pattern = rf"^##\s+{re.escape(heading)}\s*$"
    start = re.search(pattern, text, re.MULTILINE)
    if not start:
        return []
    remainder = text[start.end() :]
    next_heading = re.search(r"^##\s+", remainder, re.MULTILINE)
    block = remainder[: next_heading.start()] if next_heading else remainder
    return [line.strip() for line in block.splitlines() if line.strip()]


def extract_bullet_map(text: str, heading: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in extract_section_lines(text, heading):
        match = re.match(r"^-\s+([^:]+):\s*(.+)$", line)
        if not match:
            continue
        key = match.group(1).strip().lower().replace(" ", "_")
        values[key] = match.group(2).strip()
    return values


def section_has_active_leases(text: str, heading: str) -> bool | None:
    lines = extract_section_lines(text, heading)
    if not lines:
        return None
    if any(line == "- No active lane leases" for line in lines):
        return False
    if any(line.startswith("- ") for line in lines):
        return True
    return None


def read_pyproject_payload(root: Path) -> dict[str, Any]:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return {}
    if tomllib is not None:
        try:
            payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError, ValueError):
            payload = {}
        return payload if isinstance(payload, dict) else {}
    return {}


def repo_has_dev_extra(root: Path) -> bool:
    payload = read_pyproject_payload(root)
    project = payload.get("project")
    optional = project.get("optional-dependencies") if isinstance(project, dict) else {}
    dev = optional.get("dev") if isinstance(optional, dict) else None
    if isinstance(dev, list) and bool(dev):
        return True

    pyproject = root / "pyproject.toml"
    text = read_text(pyproject)
    section = re.search(r"(?ms)^\[project\.optional-dependencies\]\s*(.*?)^(?:\[|\Z)", text)
    if not section:
        return False
    return bool(re.search(r"(?m)^\s*dev\s*=", section.group(1)))


def repo_has_dev_dependency_group(root: Path) -> bool:
    payload = read_pyproject_payload(root)
    groups = payload.get("dependency-groups")
    dev = groups.get("dev") if isinstance(groups, dict) else None
    if isinstance(dev, list) and bool(dev):
        return True

    pyproject = root / "pyproject.toml"
    text = read_text(pyproject)
    section = re.search(r"(?ms)^\[dependency-groups\]\s*(.*?)^(?:\[|\Z)", text)
    if not section:
        return False
    return bool(re.search(r"(?m)^\s*dev\s*=", section.group(1)))


def repo_has_uv_dev_dependencies(root: Path) -> bool:
    payload = read_pyproject_payload(root)
    tool = payload.get("tool")
    uv = tool.get("uv") if isinstance(tool, dict) else {}
    if isinstance(uv, dict):
        dev_dependencies = uv.get("dev-dependencies")
        if isinstance(dev_dependencies, list) and bool(dev_dependencies):
            return True
        if isinstance(dev_dependencies, dict) and bool(dev_dependencies):
            return True

    pyproject = root / "pyproject.toml"
    text = read_text(pyproject)
    return bool(re.search(r"\[tool\.uv(?:\.[^\]]+)?\][\s\S]*?^\s*dev-dependencies\s*=", text, re.MULTILINE)) or bool(
        re.search(r"\[tool\.uv\.dev-dependencies\]", text, re.MULTILINE)
    )


def expected_uv_dependency_args(root: Path) -> tuple[list[str], str | None]:
    if repo_has_dev_extra(root):
        return ["--extra", "dev"], "[project.optional-dependencies].dev"
    if repo_has_dev_dependency_group(root):
        return ["--group", "dev"], "[dependency-groups].dev"
    if repo_has_uv_dev_dependencies(root):
        return ["--all-extras"], "[tool.uv.dev-dependencies]"
    return [], None


def repo_uses_uv(root: Path, bootstrap_text: str) -> bool:
    pyvenv_text = read_text(root / ".venv" / "pyvenv.cfg")
    return (root / "uv.lock").exists() or '["uv"' in bootstrap_text or bool(re.search(r"^uv\s*=", pyvenv_text, re.MULTILINE))


def read_only_shell_agent(path: Path) -> bool:
    text = read_text(path)
    return "write: false" in text and "edit: false" in text and "bash: true" in text


def has_eager_skill_loading(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in EAGER_SKILL_LOADING_PATTERNS)


def iter_contract_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for relative in ("README.md", "AGENTS.md", "tickets/README.md"):
        path = root / relative
        if path.exists():
            paths.append(path)
    for base, pattern in (
        (root / "docs" / "process", "*.md"),
        (root / ".opencode" / "agents", "*.md"),
        (root / ".opencode" / "skills", "*.md"),
        (root / ".opencode" / "tools", "*.ts"),
        (root / ".opencode" / "state", "*.json"),
    ):
        if base.exists():
            paths.extend(sorted(base.rglob(pattern)))
    return sorted({path.resolve(): path for path in paths}.values())


def matching_lines(text: str, patterns: tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line and any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns):
            hits.append(line)
    return hits[:3]


def matching_line_numbers(text: str, patterns: tuple[str, ...]) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for index, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if line and any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns):
            hits.append((index, line))
    return hits


def parse_transcript_tool_events(text: str) -> list[TranscriptToolEvent]:
    lines = text.splitlines()
    events: list[TranscriptToolEvent] = []
    current_assistant = ""
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        assistant_match = re.match(r"^##\s+Assistant\s+\((.+?)\)\s*$", stripped)
        if assistant_match:
            current_assistant = assistant_match.group(1).strip()
            index += 1
            continue

        tool_match = re.match(r"^\*\*Tool:\s*([^*]+)\*\*$", stripped)
        if not tool_match:
            index += 1
            continue

        tool_name = tool_match.group(1).strip()
        args: dict[str, Any] | None = None
        output: str | None = None
        error: str | None = None
        cursor = index + 1
        while cursor < len(lines):
            candidate = lines[cursor].strip()
            if candidate.startswith("## Assistant ") or candidate.startswith("**Tool:"):
                break
            if candidate in {"**Input:**", "**Output:**", "**Error:**"}:
                fence_line = cursor + 1
                if fence_line < len(lines) and lines[fence_line].strip().startswith("```"):
                    body_start = fence_line + 1
                    body_end = body_start
                    while body_end < len(lines) and lines[body_end].strip() != "```":
                        body_end += 1
                    body = "\n".join(lines[body_start:body_end]).strip()
                    if body:
                        if candidate == "**Input:**":
                            try:
                                parsed = json.loads(body)
                            except json.JSONDecodeError:
                                parsed = None
                            if isinstance(parsed, dict):
                                args = parsed
                        elif candidate == "**Output:**":
                            output = body
                        elif candidate == "**Error:**":
                            error = body
                    cursor = body_end
            cursor += 1

        events.append(
            TranscriptToolEvent(
                assistant=current_assistant,
                tool=tool_name,
                line_number=index + 1,
                args=args,
                output=output,
                error=error,
            )
        )
        index += 1
    return events


def count_transcript_input_decode_errors(text: str) -> int:
    lines = text.splitlines()
    count = 0
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if not re.match(r"^\*\*Tool:\s*([^*]+)\*\*$", stripped):
            index += 1
            continue
        cursor = index + 1
        while cursor < len(lines):
            candidate = lines[cursor].strip()
            if candidate.startswith("## Assistant ") or candidate.startswith("**Tool:"):
                break
            if candidate == "**Input:**":
                fence_line = cursor + 1
                if fence_line < len(lines) and lines[fence_line].strip().startswith("```"):
                    body_start = fence_line + 1
                    body_end = body_start
                    while body_end < len(lines) and lines[body_end].strip() != "```":
                        body_end += 1
                    body = "\n".join(lines[body_start:body_end]).strip()
                    if body:
                        try:
                            json.loads(body)
                        except json.JSONDecodeError:
                            count += 1
                    cursor = body_end
            cursor += 1
        index += 1
    return count


def parse_json_object(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def normalize_shell_command(command: str) -> str:
    return re.sub(r"\s+", " ", command.strip())


def extract_transcript_smoke_acceptance_commands(text: str) -> list[str]:
    commands: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r"`([^`\n]+)`\s+exits 0", text, re.IGNORECASE):
        command = normalize_shell_command(match.group(1))
        if not re.search(r"\b(pytest|cargo test|go test|ruff check|npm run test|pnpm run test|yarn test|bun run test)\b", command, re.IGNORECASE):
            continue
        lowered = command.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        commands.append(command)
    return commands


def matching_assistant_reasoning_line_numbers(text: str, patterns: tuple[str, ...]) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    current_section = ""
    in_fence = False
    in_tool_block = False

    for index, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if re.match(r"^##\s+Assistant\s+\(.+?\)\s*$", line):
            current_section = "assistant"
            in_tool_block = False
            continue
        if re.match(r"^##\s+User\b", line):
            current_section = "user"
            in_tool_block = False
            continue
        if line.startswith("**Tool:"):
            in_tool_block = True
            continue
        if line == "---":
            in_tool_block = False
            continue
        if current_section != "assistant" or in_tool_block or not line:
            continue
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns):
            hits.append((index, line))

    return hits


def matching_non_tool_line_numbers(text: str, patterns: tuple[str, ...]) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    in_fence = False
    in_tool_block = False

    for index, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("**Tool:"):
            in_tool_block = True
            continue
        if line == "---":
            in_tool_block = False
            continue
        if in_tool_block or not line:
            continue
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns):
            hits.append((index, line))

    return hits


def parse_invocation_log_events(path: Path) -> list[InvocationLogEvent]:
    events: list[InvocationLogEvent] = []
    if not path.exists():
        return events
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        tool = payload.get("tool")
        event = payload.get("event")
        agent = payload.get("agent")
        args = payload.get("args")
        events.append(
            InvocationLogEvent(
                event=str(event).strip() if isinstance(event, str) else "",
                tool=str(tool).strip() if isinstance(tool, str) else "",
                agent=str(agent).strip() if isinstance(agent, str) else "",
                args=args if isinstance(args, dict) else None,
                line_number=line_number,
            )
        )
    return events


def count_invocation_log_decode_errors(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError:
            count += 1
    return count


def is_coordinator_assistant(label: str) -> bool:
    lowered = label.lower()
    return "team-leader" in lowered or "coordinator" in lowered


def frontmatter_value(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", text)
    if not match:
        return None
    return match.group(1).strip().strip('"').strip("'")


def parse_iso_timestamp(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_latest_previous_diagnosis(root: Path) -> tuple[Path, dict[str, Any]] | None:
    diagnoses = load_previous_diagnoses(root)
    if not diagnoses:
        return None
    _, latest_path, latest_manifest = diagnoses[-1]
    return latest_path, latest_manifest


def package_root() -> Path:
    return Path(__file__).resolve().parents[3]


def current_package_commit() -> str:
    return resolve_current_package_commit(package_root())


def reporting_context() -> AuditReportingContext:
    return AuditReportingContext(
        package_root=package_root(),
        current_package_commit=current_package_commit(),
    )


def manifest_supporting_logs(manifest: dict[str, Any]) -> list[str]:
    value = manifest.get("supporting_logs")
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if isinstance(item, str) and str(item).strip()]


def manifest_package_commit(manifest: dict[str, Any]) -> str:
    value = manifest.get("audit_package_commit")
    return value.strip() if isinstance(value, str) and value.strip() else "missing_provenance"


def manifest_diagnosis_kind(manifest: dict[str, Any]) -> str:
    value = manifest.get("diagnosis_kind")
    return value.strip() if isinstance(value, str) and value.strip() else "initial_diagnosis"


def repair_routed_codes_from_manifest(manifest: dict[str, Any]) -> set[str]:
    bundle = load_disposition_bundle(manifest)
    if bundle is not None:
        return bundle_repair_routed_codes(bundle)
    return {
        str(item.get("source_finding_code", "")).strip()
        for item in manifest.get("ticket_recommendations", [])
        if isinstance(item, dict) and str(item.get("route", "")).strip() == "scafforge-repair"
    }


def load_latest_previous_diagnosis_with_supporting_logs(root: Path) -> tuple[Path, dict[str, Any]] | None:
    diagnoses = load_previous_diagnoses(root)
    for _, diagnosis_path, manifest in reversed(diagnoses):
        if manifest_supporting_logs(manifest):
            return diagnosis_path, manifest
    return None


def load_previous_diagnoses(root: Path) -> list[tuple[datetime, Path, dict[str, Any]]]:
    diagnosis_root = root / "diagnosis"
    if not diagnosis_root.exists():
        return []

    candidates: list[tuple[datetime, Path, dict[str, Any]]] = []
    for path in sorted(diagnosis_root.iterdir()):
        if not path.is_dir():
            continue
        manifest_path = path / "manifest.json"
        manifest = read_json(manifest_path)
        if not isinstance(manifest, dict):
            continue
        generated_at = parse_iso_timestamp(manifest.get("generated_at"))
        if generated_at is None:
            continue
        candidates.append((generated_at, path, manifest))
    return sorted(candidates, key=lambda item: item[0])


def supporting_log_paths(root: Path, explicit_logs: list[str] | None) -> list[Path]:
    paths: list[Path] = []
    for raw_path in explicit_logs or []:
        candidate = Path(raw_path).expanduser()
        candidate = candidate if candidate.is_absolute() else (root / candidate)
        if candidate.exists() and candidate.is_file():
            paths.append(candidate.resolve())
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        deduped.append(path)
    return deduped


def existing_parent(path: Path) -> Path:
    current = path
    while not current.exists() and current != current.parent:
        current = current.parent
    return current


def path_is_writable(path: Path) -> bool:
    try:
        parent = existing_parent(path)
    except OSError:
        return False
    return os.access(parent, os.W_OK)


def combine_outputs(*parts: str) -> str:
    return "\n".join(part for part in parts if part).strip()


def normalized_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def add_finding(findings: list[Finding], finding: Finding) -> None:
    findings.append(finding)


def current_ticket_artifacts(ticket: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = ticket.get("artifacts")
    if not isinstance(artifacts, list):
        return []
    return [
        artifact
        for artifact in artifacts
        if isinstance(artifact, dict) and str(artifact.get("trust_state", "current")).strip() == "current"
    ]


def latest_ticket_artifact(ticket: dict[str, Any], *, stage: str | None = None, kind: str | None = None) -> dict[str, Any] | None:
    candidates: list[tuple[datetime | None, dict[str, Any]]] = []
    for artifact in current_ticket_artifacts(ticket):
        if stage and str(artifact.get("stage", "")).strip() != stage:
            continue
        if kind and str(artifact.get("kind", "")).strip() != kind:
            continue
        created_at = parse_iso_timestamp(str(artifact.get("created_at", "")).strip())
        candidates.append((created_at, artifact))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0] or datetime.min.replace(tzinfo=timezone.utc))
    return candidates[-1][1]


def ticket_needs_process_verification(ticket: dict[str, Any], workflow: dict[str, Any]) -> bool:
    if str(ticket.get("status", "")).strip() != "done":
        return False
    if workflow.get("pending_process_verification") is not True:
        return False
    if str(ticket.get("verification_state", "")).strip() == "reverified":
        return False
    backlog_verification = latest_ticket_artifact(ticket, stage="review", kind="backlog-verification")
    if backlog_verification:
        return False

    changed_at = parse_iso_timestamp(str(workflow.get("process_last_changed_at", "")).strip())
    if changed_at is None:
        return True

    completion_artifact = (
        latest_ticket_artifact(ticket, stage="smoke-test")
        or latest_ticket_artifact(ticket, stage="qa")
        or latest_ticket_artifact(ticket)
    )
    if completion_artifact is None:
        return True

    completed_at = parse_iso_timestamp(str(completion_artifact.get("created_at", "")).strip())
    return completed_at is None or completed_at < changed_at


def tickets_needing_process_verification(manifest: dict[str, Any], workflow: dict[str, Any]) -> list[dict[str, Any]]:
    tickets = manifest.get("tickets")
    if not isinstance(tickets, list):
        return []
    return [ticket for ticket in tickets if isinstance(ticket, dict) and ticket_needs_process_verification(ticket, workflow)]


def repo_mentions_patterns(root: Path, patterns: tuple[str, ...]) -> str | None:
    for relative in ("tests", "src", ".opencode", "docs", "README.md", "AGENTS.md"):
        base = root / relative
        if not base.exists():
            continue
        paths = [base] if base.is_file() else sorted(base.rglob("*"))
        for path in paths:
            if not path.is_file():
                continue
            if path.suffix and path.suffix.lower() not in {".py", ".ts", ".js", ".md", ".json", ".yaml", ".yml", ".txt"}:
                continue
            text = read_text(path)
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                return normalize_path(path, root)
    return None


def _run(cmd: list[str], cwd: Path, timeout: int = 30) -> tuple[int, str]:
    """Run a subprocess and return (returncode, combined output). Never raises."""
    try:
        resolved_cmd = list(cmd)
        if os.name == "nt" and resolved_cmd:
            executable = resolved_cmd[0]
            has_explicit_path = any(sep in executable for sep in ("\\", "/"))
            if not has_explicit_path:
                resolved = (
                    shutil.which(executable)
                    or shutil.which(f"{executable}.cmd")
                    or shutil.which(f"{executable}.exe")
                    or shutil.which(f"{executable}.bat")
                )
                if resolved:
                    resolved_cmd[0] = resolved
        result = subprocess.run(
            resolved_cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, f"[timeout after {timeout}s]"
    except FileNotFoundError:
        return -1, f"[command not found: {cmd[0]}]"
    except Exception as exc:  # noqa: BLE001
        return -1, f"[error: {exc}]"


def _active_ticket(manifest: dict[str, Any], workflow: dict[str, Any]) -> dict[str, Any] | None:
    active_ticket_id = workflow.get("active_ticket") if isinstance(workflow, dict) else None
    tickets = manifest.get("tickets") if isinstance(manifest, dict) else None
    if not isinstance(active_ticket_id, str) or not isinstance(tickets, list):
        return None
    for ticket in tickets:
        if isinstance(ticket, dict) and ticket.get("id") == active_ticket_id:
            return ticket
    return None


def _blocked_dependents(manifest: dict[str, Any], ticket_id: str) -> list[str]:
    tickets = manifest.get("tickets") if isinstance(manifest, dict) else None
    if not isinstance(tickets, list):
        return []
    blocked: list[str] = []
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        depends_on = ticket.get("depends_on")
        if isinstance(depends_on, list) and ticket_id in depends_on and ticket.get("status") != "done":
            blocked.append(str(ticket.get("id", "")))
    return [item for item in blocked if item]


def load_repair_follow_on_state(workflow: dict[str, Any]) -> dict[str, Any]:
    raw = workflow.get("repair_follow_on") if isinstance(workflow.get("repair_follow_on"), dict) else {}
    outcome = raw.get("outcome") if isinstance(raw.get("outcome"), str) else None
    required_stages = [item.strip() for item in raw.get("required_stages", []) if isinstance(item, str) and item.strip()]
    blocking_reasons = [item.strip() for item in raw.get("blocking_reasons", []) if isinstance(item, str) and item.strip()]
    verification_passed = raw.get("verification_passed") is True
    handoff_allowed = raw.get("handoff_allowed") is True
    if outcome not in {"managed_blocked", "source_follow_up", "clean"}:
        outcome = "clean" if handoff_allowed and not required_stages and not blocking_reasons and verification_passed else "managed_blocked"
    return {
        "outcome": outcome,
        "required_stages": required_stages,
        "completed_stages": [item.strip() for item in raw.get("completed_stages", []) if isinstance(item, str) and item.strip()],
        "blocking_reasons": blocking_reasons,
        "verification_passed": verification_passed,
        "handoff_allowed": handoff_allowed,
        "last_updated_at": raw.get("last_updated_at") if isinstance(raw.get("last_updated_at"), str) and raw.get("last_updated_at").strip() else None,
    }


def has_pending_repair_follow_on_state(workflow: dict[str, Any]) -> bool:
    repair_follow_on = load_repair_follow_on_state(workflow)
    return repair_follow_on["outcome"] == "managed_blocked"


def next_repair_follow_on_stage_state(workflow: dict[str, Any]) -> str | None:
    repair_follow_on = load_repair_follow_on_state(workflow)
    if repair_follow_on["outcome"] != "managed_blocked":
        return None
    completed = set(repair_follow_on["completed_stages"])
    for stage in repair_follow_on["required_stages"]:
        if stage not in completed:
            return stage
    return None


def load_handoff_proof_state(workflow: dict[str, Any]) -> dict[str, Any]:
    raw = workflow.get("handoff_proof") if isinstance(workflow.get("handoff_proof"), dict) else {}
    status = raw.get("status") if isinstance(raw.get("status"), str) else "missing"
    if status not in {"missing", "passed", "failed"}:
        status = "missing"
    return {
        "status": status,
        "verification_kind": raw.get("verification_kind") if isinstance(raw.get("verification_kind"), str) and raw.get("verification_kind").strip() else None,
        "verified_at": raw.get("verified_at") if isinstance(raw.get("verified_at"), str) and raw.get("verified_at").strip() else None,
        "proof_artifact": raw.get("proof_artifact") if isinstance(raw.get("proof_artifact"), str) and raw.get("proof_artifact").strip() else None,
        "blocking_codes": [item.strip() for item in raw.get("blocking_codes", []) if isinstance(item, str) and item.strip()],
        "summary": raw.get("summary") if isinstance(raw.get("summary"), str) and raw.get("summary").strip() else None,
    }


def expected_handoff_status(
    workflow: dict[str, Any],
    *,
    pivot_pending: bool = False,
    active_ticket_needs_trust_restoration: bool = False,
    active_ticket_needs_historical_reconciliation: bool = False,
) -> str:
    bootstrap = workflow.get("bootstrap") if isinstance(workflow.get("bootstrap"), dict) else {}
    handoff_proof = load_handoff_proof_state(workflow)
    if str(bootstrap.get("status", "")).strip() != "ready":
        return "bootstrap recovery required"
    if pivot_pending:
        return "pivot follow-up required"
    if has_pending_repair_follow_on_state(workflow):
        return "repair follow-up required"
    if (
        workflow.get("pending_process_verification") is True
        or active_ticket_needs_trust_restoration
        or active_ticket_needs_historical_reconciliation
    ):
        return "workflow verification pending"
    if handoff_proof["status"] == "failed":
        return "pre-handoff proof failed"
    if handoff_proof["status"] == "missing":
        return "pre-handoff proof missing"
    return "ready for continued development"


def expected_done_but_not_fully_trusted(manifest: dict[str, Any], workflow: dict[str, Any]) -> str:
    if workflow.get("pending_process_verification") is True:
        affected = tickets_needing_process_verification(manifest, workflow)
        values = [str(ticket.get("id", "")).strip() for ticket in affected if str(ticket.get("id", "")).strip()]
        return ", ".join(values) if values else "none"
    values = [
        str(ticket.get("id", "")).strip()
        for ticket in manifest.get("tickets", [])
        if isinstance(ticket, dict)
        and ticket.get("status") == "done"
        and str(ticket.get("verification_state", "")).strip() not in {"trusted", "reverified"}
        and str(ticket.get("id", "")).strip()
    ]
    return ", ".join(values) if values else "none"


def expected_restart_surface_state(root: Path, manifest: dict[str, Any], workflow: dict[str, Any]) -> dict[str, Any] | None:
    active_ticket = _active_ticket(manifest, workflow)
    if not isinstance(active_ticket, dict):
        return None
    bootstrap = workflow.get("bootstrap") if isinstance(workflow.get("bootstrap"), dict) else {}
    lane_leases = workflow.get("lane_leases") if isinstance(workflow.get("lane_leases"), list) else []
    proof_artifact = bootstrap.get("proof_artifact") if isinstance(bootstrap, dict) else None
    repair_follow_on = load_repair_follow_on_state(workflow)
    pivot_path = root / ".opencode" / "meta" / "pivot-state.json"
    pivot_payload = read_json(pivot_path)
    if isinstance(pivot_payload, dict):
        pivot_inputs_raw = pivot_payload.get("restart_surface_inputs") if isinstance(pivot_payload.get("restart_surface_inputs"), dict) else {}
        downstream_state = pivot_payload.get("downstream_refresh_state") if isinstance(pivot_payload.get("downstream_refresh_state"), dict) else {}
        pivot_state_path = str(pivot_payload.get("pivot_state_path", ".opencode/meta/pivot-state.json")).strip() or ".opencode/meta/pivot-state.json"
        pivot_tracking_mode = str(downstream_state.get("tracking_mode", "")).strip() or "none"
    else:
        pivot_inputs_raw = {}
        pivot_state_path = ".opencode/meta/pivot-state.json"
        pivot_tracking_mode = "none"

    def normalize_items(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        values: list[str] = []
        seen: set[str] = set()
        for item in value:
            if not isinstance(item, str):
                continue
            stripped = item.strip()
            if not stripped or stripped in seen:
                continue
            seen.add(stripped)
            values.append(stripped)
        return values

    pivot_in_progress = pivot_inputs_raw.get("pivot_in_progress") is True
    pivot_class = str(pivot_inputs_raw.get("pivot_class", "")).strip() or "none"
    pivot_changed_surfaces = normalize_items(pivot_inputs_raw.get("pivot_changed_surfaces"))
    pivot_pending_stages = normalize_items(pivot_inputs_raw.get("pending_downstream_stages"))
    pivot_completed_stages = normalize_items(pivot_inputs_raw.get("completed_downstream_stages"))
    pivot_pending_ticket_lineage_actions = normalize_items(pivot_inputs_raw.get("pending_ticket_lineage_actions"))
    pivot_completed_ticket_lineage_actions = normalize_items(pivot_inputs_raw.get("completed_ticket_lineage_actions"))
    pivot_post_verification_passed = pivot_inputs_raw.get("post_pivot_verification_passed") is True
    active_ticket_status = str(active_ticket.get("status", "")).strip()
    active_ticket_resolution_state = str(active_ticket.get("resolution_state", "")).strip()
    active_ticket_verification_state = str(active_ticket.get("verification_state", "")).strip()
    active_ticket_needs_historical_reconciliation = (
        active_ticket_status == "done"
        and active_ticket_resolution_state == "superseded"
        and active_ticket_verification_state == "invalidated"
    )
    active_ticket_id = str(active_ticket.get("id", "")).strip()
    active_ticket_workflow_state = workflow.get("ticket_state") if isinstance(workflow.get("ticket_state"), dict) else {}
    active_ticket_needs_trust_restoration = (
        active_ticket_status == "done"
        and not active_ticket_needs_historical_reconciliation
        and (
            ticket_needs_process_verification(active_ticket, workflow)
            or (
                isinstance(active_ticket_workflow_state.get(active_ticket_id), dict)
                and active_ticket_workflow_state[active_ticket_id].get("needs_reverification") is True
            )
        )
    )
    handoff_status = expected_handoff_status(
        workflow,
        pivot_pending=pivot_in_progress,
        active_ticket_needs_trust_restoration=active_ticket_needs_trust_restoration,
        active_ticket_needs_historical_reconciliation=active_ticket_needs_historical_reconciliation,
    )
    split_children = [
        str(ticket.get("id", "")).strip()
        for ticket in manifest.get("tickets", [])
        if isinstance(ticket, dict)
        and str(ticket.get("source_ticket_id", "")).strip() == str(active_ticket.get("id", "")).strip()
        and str(ticket.get("source_mode", "")).strip() == "split_scope"
        and ticket.get("status") != "done"
        and str(ticket.get("resolution_state", "open")).strip() in {"open", "reopened"}
        and str(ticket.get("id", "")).strip()
    ]
    return {
        "ticket_id": str(active_ticket.get("id", "")).strip(),
        "stage": str(active_ticket.get("stage", workflow.get("stage", ""))).strip(),
        "status": str(active_ticket.get("status", workflow.get("status", ""))).strip(),
        "open_split_children": ", ".join(split_children) if split_children else "none",
        "bootstrap_status": str(bootstrap.get("status", "")).strip(),
        "bootstrap_proof": str(proof_artifact).strip() if isinstance(proof_artifact, str) and proof_artifact.strip() else "None",
        "handoff_status": handoff_status,
        "pending_process_verification": "true" if workflow.get("pending_process_verification") is True else "false",
        "pivot_in_progress": "true" if pivot_in_progress else "false",
        "pivot_class": pivot_class,
        "pivot_changed_surfaces": ", ".join(pivot_changed_surfaces) if pivot_changed_surfaces else "none",
        "pivot_pending_stages": ", ".join(pivot_pending_stages) if pivot_pending_stages else "none",
        "pivot_completed_stages": ", ".join(pivot_completed_stages) if pivot_completed_stages else "none",
        "pivot_pending_ticket_lineage_actions": ", ".join(pivot_pending_ticket_lineage_actions) if pivot_pending_ticket_lineage_actions else "none",
        "pivot_completed_ticket_lineage_actions": ", ".join(pivot_completed_ticket_lineage_actions) if pivot_completed_ticket_lineage_actions else "none",
        "post_pivot_verification_passed": "true" if pivot_post_verification_passed else "false",
        "pivot_state_path": pivot_state_path,
        "pivot_tracking_mode": pivot_tracking_mode,
        "repair_follow_on_outcome": repair_follow_on["outcome"],
        "repair_follow_on_required": "true" if has_pending_repair_follow_on_state(workflow) else "false",
        "repair_follow_on_next_stage": next_repair_follow_on_stage_state(workflow) or "none",
        "repair_follow_on_verification_passed": "true" if repair_follow_on["verification_passed"] else "false",
        "split_child_tickets": ", ".join(split_children) if split_children else "none",
        "done_but_not_fully_trusted": expected_done_but_not_fully_trusted(manifest, workflow),
        "repair_follow_on_updated_at": repair_follow_on["last_updated_at"],
        "state_revision": str(workflow.get("state_revision")) if isinstance(workflow.get("state_revision"), int) else None,
        "has_lane_leases": bool(lane_leases),
    }


def parse_start_here_state(text: str) -> dict[str, Any]:
    current = extract_bullet_map(text, "Current Or Next Ticket")
    dependency = extract_bullet_map(text, "Dependency Status")
    generation = extract_bullet_map(text, "Generation Status")
    post_generation = extract_bullet_map(text, "Post-Generation Audit Status")
    return {
        "ticket_id": current.get("id"),
        "stage": current.get("stage"),
        "status": current.get("status"),
        "handoff_status": generation.get("handoff_status"),
        "bootstrap_status": generation.get("bootstrap_status"),
        "bootstrap_proof": generation.get("bootstrap_proof"),
        "pending_process_verification": generation.get("pending_process_verification"),
        "pivot_in_progress": generation.get("pivot_in_progress"),
        "pivot_class": generation.get("pivot_class"),
        "pivot_changed_surfaces": generation.get("pivot_changed_surfaces"),
        "pivot_pending_stages": generation.get("pivot_pending_stages"),
        "pivot_completed_stages": generation.get("pivot_completed_stages"),
        "pivot_pending_ticket_lineage_actions": generation.get("pivot_pending_ticket_lineage_actions"),
        "pivot_completed_ticket_lineage_actions": generation.get("pivot_completed_ticket_lineage_actions"),
        "post_pivot_verification_passed": generation.get("post_pivot_verification_passed"),
        "repair_follow_on_outcome": generation.get("repair_follow_on_outcome"),
        "repair_follow_on_required": generation.get("repair_follow_on_required"),
        "repair_follow_on_next_stage": generation.get("repair_follow_on_next_stage"),
        "repair_follow_on_verification_passed": generation.get("repair_follow_on_verification_passed"),
        "split_child_tickets": dependency.get("split_child_tickets"),
        "done_but_not_fully_trusted": post_generation.get("done_but_not_fully_trusted"),
        "repair_follow_on_updated_at": generation.get("repair_follow_on_updated_at"),
    }


def parse_context_snapshot_state(text: str) -> dict[str, Any]:
    active = extract_bullet_map(text, "Active Ticket")
    bootstrap = extract_bullet_map(text, "Bootstrap")
    process = extract_bullet_map(text, "Process State")
    repair = extract_bullet_map(text, "Repair Follow-On")
    pivot = extract_bullet_map(text, "Pivot State")
    return {
        "ticket_id": active.get("id"),
        "stage": active.get("stage"),
        "status": active.get("status"),
        "open_split_children": active.get("open_split_children"),
        "bootstrap_status": bootstrap.get("status"),
        "bootstrap_proof": bootstrap.get("proof_artifact"),
        "pending_process_verification": process.get("pending_process_verification"),
        "pivot_in_progress": pivot.get("pivot_in_progress"),
        "pivot_class": pivot.get("pivot_class"),
        "pivot_changed_surfaces": pivot.get("pivot_changed_surfaces"),
        "pivot_pending_stages": pivot.get("pending_downstream_stages"),
        "pivot_completed_stages": pivot.get("completed_downstream_stages"),
        "pivot_pending_ticket_lineage_actions": pivot.get("pending_ticket_lineage_actions"),
        "pivot_completed_ticket_lineage_actions": pivot.get("completed_ticket_lineage_actions"),
        "post_pivot_verification_passed": pivot.get("post_pivot_verification_passed"),
        "pivot_state_path": pivot.get("pivot_state_path"),
        "pivot_tracking_mode": pivot.get("pivot_tracking_mode"),
        "repair_follow_on_outcome": repair.get("outcome"),
        "repair_follow_on_required": "true" if repair.get("required") == "yes" else "false" if repair.get("required") == "no" else None,
        "repair_follow_on_next_stage": repair.get("next_required_stage"),
        "repair_follow_on_verification_passed": repair.get("verification_passed"),
        "repair_follow_on_updated_at": repair.get("last_updated_at"),
        "state_revision": process.get("state_revision"),
        "has_lane_leases": section_has_active_leases(text, "Lane Leases"),
    }


def normalize_restart_surface_value(value: Any) -> Any:
    if isinstance(value, bool) or value is None:
        return value
    text = str(value).strip()
    if not text:
        return None
    lowered = text.lower()
    if lowered in {"none", "not yet recorded", "not yet recorded.", "not yet verified.", "null"}:
        return None
    return text


def _venv_interpreter_candidates(root: Path) -> list[Path]:
    """Return ordered list of expected interpreter paths inside the repo-local venv."""
    return [
        root / ".venv" / "bin" / "python",
        root / ".venv" / "Scripts" / "python.exe",
        root / ".venv" / "Scripts" / "python",
    ]


def _check_repo_python_env_health(root: Path) -> str | None:
    """Return a descriptive error string when the repo-local `.venv` is broken, or None when healthy or absent.

    A venv is considered broken when the `.venv` directory exists but no working Python
    interpreter is found inside it. This is distinct from the venv simply not existing.
    """
    venv_dir = root / ".venv"
    if not venv_dir.exists():
        return None
    for candidate in _venv_interpreter_candidates(root):
        if candidate.exists():
            rc, output = _run([str(candidate), "--version"], root, timeout=5)
            if rc == 0:
                return None
            return (
                f".venv interpreter exists at {candidate.relative_to(root)} "
                f"but fails to execute (exit {rc}): {output.strip()[:120]}"
            )
    return (
        f".venv directory exists at {venv_dir.relative_to(root)} but no Python interpreter "
        "was found at the expected paths (bin/python, Scripts/python.exe)."
    )


def _detect_python(root: Path) -> str | None:
    """Return the Python executable to use for this repo (repo-local .venv > python3 > python).

    When the repo has a `.venv` that is broken (exists but interpreter is non-functional),
    return None instead of falling through to system Python. Callers should emit EXEC-ENV-001
    before consulting detect_python so broken-venv state is a first-class finding.
    """
    for candidate in _venv_interpreter_candidates(root):
        if candidate.exists():
            rc, _ = _run([str(candidate), "--version"], root, timeout=5)
            if rc == 0:
                return str(candidate)
            # venv interpreter is broken — do not fall through to system Python
            return None
    # No venv at all — fall through to system Python
    for candidate in ("python3", "python"):
        rc, _ = _run([candidate, "--version"], root, timeout=5)
        if rc == 0:
            return candidate
    return None


def _detect_pytest_command(root: Path) -> list[str] | None:
    """Return the pytest command to use for this repo."""
    for venv_python in _venv_interpreter_candidates(root):
        if not venv_python.exists():
            continue
        rc, _ = _run([str(venv_python), "-m", "pytest", "--version"], root, timeout=5)
        if rc == 0:
            return [str(venv_python), "-m", "pytest"]
    for venv_pytest in (
        root / ".venv" / "bin" / "pytest",
        root / ".venv" / "Scripts" / "pytest.exe",
        root / ".venv" / "Scripts" / "pytest",
    ):
        if venv_pytest.exists():
            return [str(venv_pytest)]
    rc, _ = _run(["pytest", "--version"], root, timeout=5)
    if rc == 0:
        return ["pytest"]
    return None


def execution_surface_audit_context() -> ExecutionSurfaceAuditContext:
    return ExecutionSurfaceAuditContext(
        read_text=read_text,
        read_json=read_json,
        normalize_path=normalize_path,
        expected_uv_dependency_args=expected_uv_dependency_args,
        add_finding=add_finding,
        matching_lines=matching_lines,
        repo_uses_uv=repo_uses_uv,
        repo_has_dev_extra=repo_has_dev_extra,
        repo_mentions_patterns=repo_mentions_patterns,
        detect_python=_detect_python,
        detect_pytest_command=_detect_pytest_command,
        run_command=lambda argv, cwd, timeout: _run(argv, cwd, timeout=timeout),
        is_venv_broken=_check_repo_python_env_health,
    )


def contract_surface_audit_context() -> ContractSurfaceAuditContext:
    return ContractSurfaceAuditContext(
        read_text=read_text,
        read_json=read_json,
        normalize_path=normalize_path,
        normalized_path=normalized_path,
        add_finding=add_finding,
        matching_lines=matching_lines,
        load_manifest_statuses=load_manifest_statuses,
        manifest_queue_keys=manifest_queue_keys,
        parse_status_semantics=parse_status_semantics,
        ticket_markdown_status=ticket_markdown_status,
        extract_section_lines=extract_section_lines,
        read_only_shell_agent=read_only_shell_agent,
        has_eager_skill_loading=has_eager_skill_loading,
        iter_contract_paths=iter_contract_paths,
        frontmatter_value=frontmatter_value,
        stage_like_statuses=tuple(STAGE_LIKE_STATUSES),
        mutating_shell_tokens=MUTATING_SHELL_TOKENS,
        write_language=WRITE_LANGUAGE,
        artifact_register_persist_patterns=ARTIFACT_REGISTER_PERSIST_PATTERNS,
        artifact_path_drift_patterns=ARTIFACT_PATH_DRIFT_PATTERNS,
        deprecated_workflow_terms=DEPRECATED_WORKFLOW_TERMS,
        placeholder_skill_patterns=PLACEHOLDER_SKILL_PATTERNS,
        deprecated_model_patterns=DEPRECATED_MODEL_PATTERNS,
    )


def session_transcript_audit_context() -> SessionTranscriptAuditContext:
    return SessionTranscriptAuditContext(
        read_text=read_text,
        read_json=read_json,
        normalize_path=normalize_path,
        add_finding=add_finding,
        matching_lines=matching_lines,
        matching_line_numbers=matching_line_numbers,
        matching_assistant_reasoning_line_numbers=matching_assistant_reasoning_line_numbers,
        matching_non_tool_line_numbers=matching_non_tool_line_numbers,
        parse_transcript_tool_events=parse_transcript_tool_events,
        count_transcript_input_decode_errors=count_transcript_input_decode_errors,
        count_invocation_log_decode_errors=count_invocation_log_decode_errors,
        parse_json_object=parse_json_object,
        normalize_shell_command=normalize_shell_command,
        extract_transcript_smoke_acceptance_commands=extract_transcript_smoke_acceptance_commands,
        is_coordinator_assistant=is_coordinator_assistant,
        transcript_stale_state_patterns=TRANSCRIPT_STALE_STATE_PATTERNS,
        transcript_progress_patterns=TRANSCRIPT_PROGRESS_PATTERNS,
        transcript_full_suite_result_patterns=TRANSCRIPT_FULL_SUITE_RESULT_PATTERNS,
        transcript_lifecycle_error_patterns=TRANSCRIPT_LIFECYCLE_ERROR_PATTERNS,
        transcript_soft_bypass_patterns=TRANSCRIPT_SOFT_BYPASS_PATTERNS,
        transcript_verification_failure_patterns=TRANSCRIPT_VERIFICATION_FAILURE_PATTERNS,
        transcript_pass_claim_patterns=TRANSCRIPT_PASS_CLAIM_PATTERNS,
        transcript_execution_recovery_patterns=TRANSCRIPT_EXECUTION_RECOVERY_PATTERNS,
        transcript_broken_tool_patterns=TRANSCRIPT_BROKEN_TOOL_PATTERNS,
        transcript_smoke_override_failure_patterns=TRANSCRIPT_SMOKE_OVERRIDE_FAILURE_PATTERNS,
        transcript_smoke_acceptance_patterns=TRANSCRIPT_SMOKE_ACCEPTANCE_PATTERNS,
        transcript_handoff_lease_contradiction_patterns=TRANSCRIPT_HANDOFF_LEASE_CONTRADICTION_PATTERNS,
        transcript_acceptance_scope_tension_patterns=TRANSCRIPT_ACCEPTANCE_SCOPE_TENSION_PATTERNS,
        handoff_overclaim_patterns=HANDOFF_OVERCLAIM_PATTERNS,
        coordinator_artifact_stages=tuple(COORDINATOR_ARTIFACT_STAGES),
    )


def restart_surface_audit_context() -> RestartSurfaceAuditContext:
    return RestartSurfaceAuditContext(
        read_text=read_text,
        read_json=read_json,
        normalize_path=normalize_path,
        add_finding=add_finding,
        matching_lines=matching_lines,
        combine_outputs=combine_outputs,
        active_ticket=_active_ticket,
        blocked_dependents=_blocked_dependents,
        expected_restart_surface_state=expected_restart_surface_state,
        normalize_restart_surface_value=normalize_restart_surface_value,
        parse_start_here_state=parse_start_here_state,
        parse_context_snapshot_state=parse_context_snapshot_state,
        parse_invocation_log_events=parse_invocation_log_events,
        is_coordinator_assistant=is_coordinator_assistant,
    )


def ticket_graph_audit_context() -> TicketGraphAuditContext:
    return TicketGraphAuditContext(
        read_text=read_text,
        read_json=read_json,
        normalize_path=normalize_path,
        add_finding=add_finding,
    )


def lifecycle_contract_audit_context() -> LifecycleContractAuditContext:
    return LifecycleContractAuditContext(
        read_text=read_text,
        read_json=read_json,
        normalize_path=normalize_path,
        add_finding=add_finding,
        tickets_needing_process_verification=tickets_needing_process_verification,
        parse_start_here_state=parse_start_here_state,
        normalize_restart_surface_value=normalize_restart_surface_value,
    )


def repair_cycle_audit_context() -> RepairCycleAuditContext:
    return RepairCycleAuditContext(
        read_json=read_json,
        normalize_path=normalize_path,
        add_finding=add_finding,
        parse_iso_timestamp=parse_iso_timestamp,
        current_package_commit=current_package_commit,
        load_latest_previous_diagnosis=load_latest_previous_diagnosis,
        load_previous_diagnoses=load_previous_diagnoses,
        manifest_diagnosis_kind=manifest_diagnosis_kind,
        manifest_package_commit=manifest_package_commit,
        manifest_supporting_logs=manifest_supporting_logs,
        repair_routed_codes_from_manifest=repair_routed_codes_from_manifest,
    )


def audit_repo(root: Path, logs: list[Path] | None = None) -> list[Finding]:
    findings: list[Finding] = []
    contract_ctx = contract_surface_audit_context()
    session_ctx = session_transcript_audit_context()
    execution_ctx = execution_surface_audit_context()
    restart_ctx = restart_surface_audit_context()
    ticket_graph_ctx = ticket_graph_audit_context()
    lifecycle_ctx = lifecycle_contract_audit_context()
    repair_cycle_ctx = repair_cycle_audit_context()
    config_ctx = ConfigSurfaceAuditContext(repo_root=root, findings=findings)
    run_contract_surface_audits(root, findings, contract_ctx)
    run_config_surface_audits(root, findings, config_ctx)
    run_execution_surface_audits(root, findings, execution_ctx)
    run_restart_surface_audits(root, findings, restart_ctx)
    run_ticket_graph_audits(root, findings, ticket_graph_ctx)
    run_lifecycle_contract_audits(root, findings, lifecycle_ctx)
    run_repair_cycle_audits(root, findings, repair_cycle_ctx)
    run_session_transcript_audits(root, findings, logs or [], session_ctx)
    return findings


def emit_diagnosis_pack(
    root: Path,
    findings: list[Finding],
    destination: Path,
    logs: list[Path],
    manifest_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return emit_diagnosis_pack_impl(
        root,
        findings,
        destination,
        logs,
        ctx=reporting_context(),
        manifest_overrides=manifest_overrides,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit a repo for Scafforge workflow, review, and prompt-process drift.")
    parser.add_argument("repo_root", help="Repository root to audit.")
    parser.add_argument("--supporting-log", action="append", default=[], help="Optional supporting session log or transcript path. May be provided multiple times.")
    parser.add_argument("--format", choices=("markdown", "json", "both"), default="both")
    parser.add_argument("--markdown-output", help="Optional path for markdown output.")
    parser.add_argument("--json-output", help="Optional path for JSON output.")
    parser.add_argument("--emit-diagnosis-pack", dest="emit_diagnosis_pack", action="store_true", help="Write the four-report diagnosis pack into <repo>/diagnosis/<timestamp>/. Enabled by default.")
    parser.add_argument("--no-diagnosis-pack", dest="emit_diagnosis_pack", action="store_false", help="Skip writing the diagnosis pack.")
    parser.add_argument("--diagnosis-output-dir", help="Optional diagnosis-pack directory. Defaults to <repo>/diagnosis/<YYYYMMDD-HHMMSS> when emission is enabled.")
    parser.add_argument(
        "--diagnosis-kind",
        choices=("initial_diagnosis", "post_package_revalidation", "post_repair_verification"),
        default="initial_diagnosis",
        help="Label the emitted diagnosis pack with its workflow position.",
    )
    parser.add_argument("--fail-on", choices=("never", "warning", "error"), default="never")
    parser.set_defaults(emit_diagnosis_pack=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.repo_root).expanduser().resolve()
    logs = supporting_log_paths(root, args.supporting_log)
    findings = audit_repo(root, logs=logs)

    if args.emit_diagnosis_pack or args.diagnosis_output_dir:
        diagnosis_dir = select_diagnosis_destination(root, args.diagnosis_output_dir, findings)
        diagnosis_pack = emit_diagnosis_pack(root, findings, diagnosis_dir, logs, manifest_overrides={"diagnosis_kind": args.diagnosis_kind})
    else:
        diagnosis_pack = None

    payload = {
        "repo_root": str(root),
        "finding_count": len(findings),
        "findings": [asdict(finding) for finding in findings],
    }
    if logs:
        payload["supporting_logs"] = [str(path) for path in logs]
    if diagnosis_pack:
        payload["diagnosis_pack"] = diagnosis_pack
    markdown = render_markdown(root, findings)

    if args.markdown_output:
        Path(args.markdown_output).write_text(markdown + "\n", encoding="utf-8")
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if args.format in {"markdown", "both"}:
        print(markdown)
    if args.format in {"json", "both"} and not args.json_output:
        print(json.dumps(payload, indent=2))

    if args.fail_on == "warning" and findings:
        return 2
    if args.fail_on == "error" and any(finding.severity == "error" for finding in findings):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
