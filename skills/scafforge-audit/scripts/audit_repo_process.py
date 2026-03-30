from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_contract_surfaces import ContractSurfaceAuditContext, run_contract_surface_audits
from audit_execution_surfaces import ExecutionSurfaceAuditContext, run_execution_surface_audits
from audit_lifecycle_contracts import LifecycleContractAuditContext, run_lifecycle_contract_audits
from audit_repair_cycles import RepairCycleAuditContext, run_repair_cycle_audits
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
DIAGNOSIS_REPORTS = {
    "report_1": "01-initial-codebase-review.md",
    "report_2": "02-scafforge-process-failures.md",
    "report_3": "03-scafforge-prevention-actions.md",
    "report_4": "04-live-repo-repair-plan.md",
}

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
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=package_root(),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip() or "unknown"


def manifest_supporting_logs(manifest: dict[str, Any]) -> list[str]:
    value = manifest.get("supporting_logs")
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if isinstance(item, str) and str(item).strip()]


def manifest_package_commit(manifest: dict[str, Any]) -> str:
    value = manifest.get("audit_package_commit")
    return value.strip() if isinstance(value, str) and value.strip() else "unknown"


def manifest_diagnosis_kind(manifest: dict[str, Any]) -> str:
    value = manifest.get("diagnosis_kind")
    return value.strip() if isinstance(value, str) and value.strip() else "initial_diagnosis"


def repair_routed_codes_from_manifest(manifest: dict[str, Any]) -> set[str]:
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
        result = subprocess.run(
            cmd,
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


def expected_handoff_status(workflow: dict[str, Any]) -> str:
    bootstrap = workflow.get("bootstrap") if isinstance(workflow.get("bootstrap"), dict) else {}
    if str(bootstrap.get("status", "")).strip() != "ready":
        return "bootstrap recovery required"
    if has_pending_repair_follow_on_state(workflow):
        return "repair follow-up required"
    repair_follow_on = load_repair_follow_on_state(workflow)
    if repair_follow_on["verification_passed"] is False or workflow.get("pending_process_verification") is True:
        return "workflow verification pending"
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


def expected_restart_surface_state(manifest: dict[str, Any], workflow: dict[str, Any]) -> dict[str, Any] | None:
    active_ticket = _active_ticket(manifest, workflow)
    if not isinstance(active_ticket, dict):
        return None
    bootstrap = workflow.get("bootstrap") if isinstance(workflow.get("bootstrap"), dict) else {}
    lane_leases = workflow.get("lane_leases") if isinstance(workflow.get("lane_leases"), list) else []
    proof_artifact = bootstrap.get("proof_artifact") if isinstance(bootstrap, dict) else None
    repair_follow_on = load_repair_follow_on_state(workflow)
    handoff_status = expected_handoff_status(workflow)
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
    return {
        "ticket_id": active.get("id"),
        "stage": active.get("stage"),
        "status": active.get("status"),
        "open_split_children": active.get("open_split_children"),
        "bootstrap_status": bootstrap.get("status"),
        "bootstrap_proof": bootstrap.get("proof_artifact"),
        "pending_process_verification": process.get("pending_process_verification"),
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


def _detect_python(root: Path) -> str | None:
    """Return the Python executable to use for this repo (repo-local .venv > python3 > python)."""
    for candidate in (
        root / ".venv" / "bin" / "python",
        root / ".venv" / "Scripts" / "python.exe",
        root / ".venv" / "Scripts" / "python",
    ):
        if candidate.exists():
            return str(candidate)
    for candidate in ("python3", "python"):
        rc, _ = _run([candidate, "--version"], root, timeout=5)
        if rc == 0:
            return candidate
    return None


def _detect_pytest_command(root: Path) -> list[str] | None:
    """Return the pytest command to use for this repo."""
    for venv_python in (
        root / ".venv" / "bin" / "python",
        root / ".venv" / "Scripts" / "python.exe",
        root / ".venv" / "Scripts" / "python",
    ):
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
    run_contract_surface_audits(root, findings, contract_ctx)
    run_repair_cycle_audits(root, findings, repair_cycle_ctx)
    run_execution_surface_audits(root, findings, execution_ctx)
    run_restart_surface_audits(root, findings, restart_ctx)
    run_ticket_graph_audits(root, findings, ticket_graph_ctx)
    run_lifecycle_contract_audits(root, findings, lifecycle_ctx)
    run_session_transcript_audits(root, findings, logs or [], session_ctx)
    return findings


def render_markdown(root: Path, findings: list[Finding]) -> str:
    lines = [
        "# Repo Process Audit",
        "",
        f"- Repo: {root}",
        f"- Findings: {len(findings)}",
        "",
    ]
    if not findings:
        lines.extend(["No blocking workflow smells found.", ""])
        return "\n".join(lines)

    lines.append("## Findings")
    lines.append("")
    for finding in findings:
        lines.extend(
            [
                f"### [{finding.severity}] {finding.code}",
                "",
                f"Problem: {finding.problem}",
                f"Root cause: {finding.root_cause}",
                "Files:",
                *[f"- {path}" for path in finding.files],
                f"Target safer pattern: {finding.safer_pattern}",
                "Evidence:",
                *[f"- {item}" for item in finding.evidence],
                "",
            ]
        )
    return "\n".join(lines)


def severity_rank(severity: str) -> int:
    return {"error": 0, "warning": 1, "info": 2}.get(severity, 3)


def findings_by_severity(findings: list[Finding]) -> dict[str, list[Finding]]:
    grouped: dict[str, list[Finding]] = {"error": [], "warning": [], "info": []}
    for finding in sorted(findings, key=lambda item: (severity_rank(item.severity), item.code)):
        grouped.setdefault(finding.severity, []).append(finding)
    return grouped


def infer_surface(finding: Finding) -> str:
    joined = " ".join(finding.files)
    if finding.code.startswith("SESSION"):
        return "scafforge-audit transcript chronology and causal diagnosis surfaces"
    if finding.code.startswith("BOOT"):
        return "managed bootstrap tool and bootstrap-facing workflow guidance"
    if finding.code.startswith("ENV"):
        return "scafforge-audit and scafforge-repair host verification plus prerequisite-classification surfaces"
    if finding.code.startswith("WFLOW"):
        return "repo-scaffold-factory generated workflow, handoff, and tool contract surfaces"
    if any(token in joined for token in (".opencode/tools/", ".opencode/commands/", "docs/process/", ".opencode/state/")):
        return "repo-scaffold-factory managed template surfaces"
    if any(token in joined for token in (".opencode/agents/", ".opencode/skills/")):
        return "project-skill-bootstrap and agent-prompt-engineering surfaces"
    if "tickets/" in joined or "status" in finding.code or "ticket" in finding.code:
        return "ticket-pack-builder and ticket contract surfaces"
    if finding.code.startswith("EXEC"):
        return "generated repo implementation and validation surfaces"
    return "scafforge-audit diagnosis contract"


def prevention_action(finding: Finding) -> str:
    if finding.code == "ENV001":
        return "Add first-class environment prerequisite findings so missing host executables like `uv`, `rg`, or Python runtimes are surfaced explicitly instead of being treated as silent skips."
    if finding.code == "ENV002":
        return "Treat missing repo-local test executables such as pytest as explicit verification blockers, and distinguish stale or failed repo bootstrap from missing host prerequisites when uv-managed repos already have `uv` available."
    if finding.code == "ENV003":
        return "Classify host misconfiguration such as missing git identity as environment blockers when repo validations depend on commit-producing checks."
    if finding.code == "ENV004":
        return "Let audit emit its diagnosis pack to a writable host-selected location and record redirected-output cases instead of failing when the subject repo path is not writable."
    if finding.code == "WFLOW001":
        return "Make generated smoke-test tools repo-manager-aware so uv and .venv Python repos do not deadlock on system-python pytest."
    if finding.code == "WFLOW002":
        return "Make generated handoff publication reject readiness or causal claims that outrun executed evidence or current dependency state."
    if finding.code == "WFLOW003":
        return "Split plan review from implementation review in generated workflow contracts so docs, tools, and prompts use the same stage semantics."
    if finding.code == "WFLOW004":
        return "Validate requested stage/status pairs through one lifecycle contract, reject unsupported stages, and gate implementation on lifecycle stage rather than queue labels."
    if finding.code == "WFLOW005":
        return "Reserve smoke-test proof to `smoke_test` and keep generic artifact ownership aligned with the documented handoff path so closeout evidence cannot be fabricated."
    if finding.code == "WFLOW006":
        return "Harden the team leader prompt so it routes from transition guidance, stops on repeated lifecycle errors, keeps slash commands human-only, and leaves stage artifacts to specialists."
    if finding.code == "WFLOW007":
        return "Keep handoff ownership consistent across prompts and plugins so optional docs-lane handoff artifacts remain writable while `handoff_publish` still owns restart surfaces."
    if finding.code == "WFLOW008":
        return "Teach audit and repair to treat pending backlog process verification as a first-class verification state so repaired repos are not declared clean while historical done tickets remain untrusted."
    if finding.code == "WFLOW009":
        return "Make `ticket_reverify` the legal trust-restoration path for closed done tickets instead of binding it to the normal closed-ticket lease rules."
    if finding.code == "WFLOW010":
        return "Regenerate derived restart surfaces from canonical manifest and workflow state after every workflow mutation so resume guidance never contradicts active bootstrap, ticket, or lease facts."
    if finding.code == "WFLOW011":
        return "Make bootstrap-first routing explicit across ticket lookup, the team leader prompt, and the repo-local workflow skill so failed or stale bootstrap short-circuits normal lifecycle guidance."
    if finding.code == "WFLOW012":
        return "Use one lease-ownership model everywhere: the team leader claims and releases ticket leases, specialists work under the active lease, and only Wave 0 setup work may claim before bootstrap is ready."
    if finding.code == "WFLOW013":
        return "Make `/resume` trust canonical manifest plus workflow state first, keep all restart surfaces derived-only, include `.opencode/state/latest-handoff.md`, and preserve the active open ticket as the primary lane."
    if finding.code == "WFLOW014":
        return "Teach audit, repair, and generated prompts to treat coordinator-authored specialist artifacts in invocation logs as suspect evidence that requires remediation and stage reruns through the owning specialist."
    if finding.code == "WFLOW015":
        return "Audit transcript tool errors directly, keep `_workflow_*` helpers out of the model-visible tool surface, and fail package verification when internal helper exports can be selected like executable tools."
    if finding.code == "WFLOW016":
        return "Make `smoke_test` parse shell-style override commands correctly, treat leading `KEY=VALUE` tokens as environment overrides, and detect transcript-level `ENOENT` override failures as workflow-surface defects instead of generic test failures."
    if finding.code == "WFLOW017":
        return "Make `smoke_test` infer explicit acceptance-backed smoke commands before generic test-surface detection, and detect transcript runs where smoke scope drifted away from the ticket's canonical acceptance command."
    if finding.code == "WFLOW018":
        return "Let closed-ticket process-verification and post-completion follow-up routes use current registered evidence without requiring the source ticket's normal write lease."
    if finding.code == "WFLOW019":
        return "Add a canonical ticket-graph reconciliation path so stale source/follow-up linkage and contradictory dependencies are repaired atomically instead of by manual manifest edits."
    if finding.code == "WFLOW020":
        return "Add first-class `split_scope` routing for child tickets created from open parents so decomposition does not drift into non-canonical source modes and split parents do not revert to blocked status."
    if finding.code == "WFLOW021":
        return "Keep legacy `handoff_allowed` parsing internal only, and regenerate prompts plus restart surfaces so weaker models route from `repair_follow_on.outcome` instead of stale boolean handoff gates."
    if finding.code == "WFLOW022":
        return "Keep closeout publication outside the ordinary open-ticket lease contract so `handoff_publish` can update derived restart surfaces after a ticket closes."
    if finding.code == "WFLOW023":
        return "Make ticket acceptance criteria scope-isolated: if the literal closeout command depends on later-ticket work, split the backlog differently or encode the dependency explicitly instead of shipping contradictory acceptance."
    if finding.code == "WFLOW024":
        return "Give historical reconciliation one legal evidence-backed path so superseded invalidated tickets can be repaired without depending on impossible direct-artifact or closeout assumptions."
    if finding.code == "SESSION001":
        return "Teach scafforge-audit to treat supplied session logs as first-class temporal evidence and explain final reasoning failures before reconciling current repo state."
    if finding.code == "SESSION002":
        return "Teach scafforge-audit and generated prompts to flag repeated lifecycle retries as contract thrash instead of ordinary transient error handling."
    if finding.code == "SESSION003":
        return "Reject unsupported stage probing and explicit workflow bypass attempts in both generated tools and prompt hardening."
    if finding.code == "SESSION004":
        return "Detect and block evidence-free PASS artifacts when verification could not run, and keep smoke-test proof tool-owned."
    if finding.code == "SESSION005":
        return "Teach audit and generated coordinator prompts to treat coordinator-authored specialist artifacts as a workflow defect that requires prompt plus local-skill regeneration."
    if finding.code == "SESSION006":
        return "Treat operator confusion itself as workflow evidence when the transcript shows no single legal next move, and audit adjacent surfaces together until one competent route exists."
    if finding.code == "BOOT001":
        return "Make generated Python bootstrap manager-aware (`uv` or repo-local `.venv`), classify missing prerequisites accurately, and audit bootstrap deadlocks before routing source remediation."
    if finding.code == "BOOT002":
        return "Correlate `pyproject.toml`, bootstrap artifacts, and `environment_bootstrap.ts` so uv-managed repos with extras or dependency groups emit a managed bootstrap defect instead of an operator-only rerun recommendation."
    if finding.code == "SKILL001":
        return "Detect and repair leftover placeholder local skills so generated stack guidance is concrete before implementation continues."
    if finding.code == "SKILL002":
        return "Make the generated `ticket-execution` skill the canonical lifecycle explainer so weaker models do not have to reverse-engineer the state machine from tool errors."
    if finding.code == "MODEL001":
        return "Detect deprecated or missing model-profile surfaces, treat stale package-managed defaults as safe repair instead of preserved intent, regenerate the repo-local model operating profile, and align model metadata plus agent defaults before development resumes."
    if finding.code == "CYCLE001":
        return "Teach audit to inspect the previous diagnosis and repair history, then force repair to explain why the prior cycle failed before another managed-repair run proceeds."
    if finding.code == "CYCLE002":
        return "Teach audit to stop repeated diagnosis-pack churn when the repo has no newer package or process-version change; require Scafforge package work before the next subject-repo audit."
    if finding.code == "CYCLE003":
        return "Make repair verification inherit the transcript-backed diagnosis basis automatically, emit the post-repair diagnosis pack from the repair runner, and refuse to call the repo clean on current-state evidence alone."
    if finding.code.startswith("EXEC"):
        return "Tighten generated review and QA guidance so runtime validation and test collection proof exist before closure."
    if "ticket" in finding.code or "status" in finding.code:
        return "Keep queue state coarse, route remediation through guarded ticket flows, and validate ticket-contract wording in package checks."
    if any(token in " ".join(finding.files) for token in (".opencode/agents/", ".opencode/skills/")):
        return "Harden generated prompts so read-only roles stay read-only and repo-local review guidance remains advisory."
    return "Refresh managed workflow docs, tools, and validators together so repair replaces drift instead of layering new semantics over old ones."


def package_has_wflow024_fix() -> bool:
    package = package_root()
    ticket_reconcile = read_text(package / "skills" / "repo-scaffold-factory" / "assets" / "project-template" / ".opencode" / "tools" / "ticket_reconcile.ts")
    ticket_create = read_text(package / "skills" / "repo-scaffold-factory" / "assets" / "project-template" / ".opencode" / "tools" / "ticket_create.ts")
    issue_intake = read_text(package / "skills" / "repo-scaffold-factory" / "assets" / "project-template" / ".opencode" / "tools" / "issue_intake.ts")
    workflow_lib = read_text(package / "skills" / "repo-scaffold-factory" / "assets" / "project-template" / ".opencode" / "lib" / "workflow.ts")
    return (
        "currentRegistryArtifact" in workflow_lib
        and "currentRegistryArtifact" in ticket_reconcile
        and 'verification_state = "reverified"' in ticket_reconcile
        and "supersededTarget: supersedeTarget" in ticket_reconcile
        and "currentRegistryArtifact" in ticket_create
        and "currentRegistryArtifact" in issue_intake
    )


def build_ticket_recommendations(findings: list[Finding]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    wflow024_package_fix_available = package_has_wflow024_fix()
    for index, finding in enumerate(sorted(findings, key=lambda item: (severity_rank(item.severity), item.code)), start=1):
        if finding.code.startswith("EXEC"):
            route = "ticket-pack-builder"
            repair_class = "generated-repo remediation ticket"
        elif finding.code == "WFLOW024":
            if wflow024_package_fix_available:
                route = "scafforge-repair"
                repair_class = "safe Scafforge package change"
            else:
                route = "manual-prerequisite"
                repair_class = "Scafforge package work required before the next subject-repo repair run"
        elif finding.code.startswith("CYCLE"):
            route = "manual-prerequisite"
            repair_class = "Scafforge package work required before the next subject-repo run"
        elif finding.code.startswith("ENV"):
            route = "manual-prerequisite"
            repair_class = "host prerequisite or operator follow-up"
        else:
            route = "scafforge-repair"
            repair_class = "safe Scafforge package change"
        recommendations.append(
            {
                "id": f"REMED-{index:03d}",
                "title": finding.problem.rstrip("."),
                "source_finding_code": finding.code,
                "severity": finding.severity,
                "route": route,
                "repair_class": repair_class,
                "summary": finding.safer_pattern,
                "source_files": finding.files,
            }
        )
    return recommendations


def package_work_required_first(recommendations: list[dict[str, Any]]) -> bool:
    return any(
        isinstance(item, dict)
        and str(item.get("route", "")).strip() == "manual-prerequisite"
        and "Scafforge package work required" in str(item.get("repair_class", ""))
        for item in recommendations
    )


def recommended_next_step(findings: list[Finding], recommendations: list[dict[str, Any]]) -> str:
    if package_work_required_first(recommendations):
        return "scafforge_package_work"
    if any(not finding.code.startswith("EXEC") and not finding.code.startswith("ENV") for finding in findings):
        return "subject_repo_repair"
    if findings:
        return "subject_repo_source_follow_up"
    return "done"


def render_report_one(root: Path, findings: list[Finding], generated_at: str, logs: list[Path]) -> str:
    grouped = findings_by_severity(findings)
    lines = [
        "# Report 1: Initial Codebase Review",
        "",
        f"- Repo: {root}",
        f"- Generated at: {generated_at}",
        f"- Finding count: {len(findings)}",
        f"- Errors: {len(grouped.get('error', []))}",
        f"- Warnings: {len(grouped.get('warning', []))}",
        "",
        "## Validated findings",
        "",
    ]
    if not findings:
        lines.extend(
            [
                "No validated workflow, review, runtime, environment, or process findings were detected.",
                "",
                "## Verification gaps",
                "",
                "- No additional verification gaps were identified during this diagnosis pass.",
                "",
            ]
        )
        return "\n".join(lines)

    if logs:
        lines.extend(
            [
                "## Supporting session evidence",
                "",
                *[f"- {normalize_path(path, root)}" for path in logs],
                "",
            ]
        )

    for finding in sorted(findings, key=lambda item: (severity_rank(item.severity), item.code)):
        lines.extend(
            [
                f"### [{finding.severity}] {finding.code}",
                "",
                f"Problem: {finding.problem}",
                f"Files: {', '.join(finding.files) if finding.files else '(none)'}",
                "Verification gaps:",
                *([f"- {item}" for item in finding.evidence] or ["- No extra verification gaps captured."]),
                "",
            ]
        )
    return "\n".join(lines)


def render_report_two(findings: list[Finding]) -> str:
    lines = [
        "# Report 2: Scafforge Process Failures",
        "",
        "This report maps validated issues back to Scafforge-owned skills, contracts, templates, or generated surfaces.",
        "",
    ]
    if not findings:
        lines.extend(["No process failures were mapped from the validated finding set.", ""])
        return "\n".join(lines)

    for finding in sorted(findings, key=lambda item: (severity_rank(item.severity), item.code)):
        lines.extend(
            [
                f"## {finding.code}",
                "",
                f"- Surface: {infer_surface(finding)}",
                f"- Root cause: {finding.root_cause}",
                f"- Safer target pattern: {finding.safer_pattern}",
                "",
            ]
        )
    return "\n".join(lines)


def render_report_three(findings: list[Finding]) -> str:
    lines = [
        "# Report 3: Scafforge Prevention Actions",
        "",
        "These actions describe package-side changes that prevent the same failures from reappearing in future generated repos.",
        "",
    ]
    if not findings:
        lines.extend(["No additional prevention actions are required beyond keeping the current contract intact.", ""])
        return "\n".join(lines)

    seen: set[str] = set()
    for finding in sorted(findings, key=lambda item: (severity_rank(item.severity), item.code)):
        action = prevention_action(finding)
        if action in seen:
            continue
        seen.add(action)
        lines.extend([f"- {action}", ""])
    return "\n".join(lines)


def render_report_four(root: Path, findings: list[Finding], recommendations: list[dict[str, Any]]) -> str:
    safe_repairs = [item for item in recommendations if item["route"] == "scafforge-repair"]
    source_follow_up = [item for item in recommendations if item["route"] == "ticket-pack-builder"]
    manual_prerequisites = [item for item in recommendations if item["route"] == "manual-prerequisite"]
    requires_regeneration = any(
        finding.code in {"SKILL001", "SKILL002", "MODEL001"} or any(token in " ".join(finding.files) for token in (".opencode/agents/", ".opencode/skills/"))
        for finding in findings
    )
    repeated_cycle = next((finding for finding in findings if finding.code in {"CYCLE001", "CYCLE002", "CYCLE003"}), None)
    lines = [
        "# Report 4: Live Repo Repair Plan",
        "",
        f"- Repo: {root}",
        "- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.",
        "",
    ]
    if repeated_cycle:
        lines.extend(
            [
                "## Repeated Failure Note",
                "",
                "- This repo has already gone through at least one audit-to-repair cycle and still reproduces workflow-layer findings.",
                "- Before another repair run, compare the latest previous diagnosis pack against repair history and explain why those findings survived.",
                "- Do not keep rerunning subject-repo audit until a Scafforge package or process-version change exists.",
                "",
            ]
        )
    lines.extend(
        [
        "## Safe repair boundary",
        "",
        ]
    )
    if safe_repairs:
        lines.extend([f"- Route {len(safe_repairs)} workflow-layer findings into `scafforge-repair` for deterministic managed-surface repair.", ""])
        if requires_regeneration:
            lines.extend(
                [
                    "- Do not stop at tool replacement: rerun project-local skill regeneration, agent-team follow-up, and prompt hardening before handoff.",
                    "",
                ]
            )
        if any(finding.code.startswith("WFLOW") for finding in findings):
            lines.extend(
                [
                    "- Refresh generated ticket-update, ticket-lookup, stage-gate, smoke-test, handoff, workflow-doc, and coordinator-prompt surfaces together; these findings indicate a managed workflow-contract defect, not just repo-local operator error.",
                    "",
                ]
            )
        if any(finding.code in {"SKILL002", "SESSION002", "SESSION003", "SESSION004", "SESSION005", "SESSION006", "WFLOW007", "WFLOW012", "WFLOW013", "WFLOW014", "WFLOW015", "WFLOW016", "WFLOW017", "WFLOW022", "WFLOW023"} for finding in findings):
            lines.extend(
                [
                    "- Rerun project-local skill regeneration and prompt hardening after the deterministic refresh so the repo-local `ticket-execution` skill and team-leader prompt explain the same state machine the tools enforce.",
                    "",
                ]
            )
        if any(finding.code == "MODEL001" for finding in findings):
            lines.extend(
                [
                    "- Deprecated package-managed model defaults such as `MiniMax-M2.5` must be repaired; do not preserve them as protected intent unless newer explicit accepted-decision evidence exists.",
                    "",
                ]
            )
    else:
        lines.extend(["- No safe managed-surface repair was identified from the current findings.", ""])

    lines.extend(["## Intent-changing boundary", "", "- Escalate any stack, scope, provider, or curated human-decision changes instead of labeling them as safe repair.", "", "## Ticket recommendations", ""])

    if recommendations:
        for item in recommendations:
            lines.extend(
                [
                    f"### {item['id']} ({item['severity']})",
                    "",
                    f"- Title: {item['title']}",
                    f"- Route: `{item['route']}`",
                    f"- Repair class: {item['repair_class']}",
                    f"- Source finding: `{item['source_finding_code']}`",
                    f"- Summary: {item['summary']}",
                    "",
                ]
            )
    else:
        lines.extend(["- No follow-up tickets are recommended from the current diagnosis run.", ""])

    if source_follow_up:
        lines.extend(
            [
                "## Post-repair follow-up",
                "",
                f"- Route {len(source_follow_up)} source-layer remediation item(s) through `ticket-pack-builder` and any generated repo guarded ticket surfaces after workflow repair is complete.",
                "",
            ]
        )

    if manual_prerequisites:
        lines.extend(
            [
                "## Host Prerequisites",
                "",
                "- The following findings are current-machine blockers or package stop conditions. Repair may refresh workflow surfaces, but these items still need operator action or Scafforge package work before verification can be trusted.",
                "",
            ]
        )
        for item in manual_prerequisites:
            lines.extend(
                [
                    f"- `{item['source_finding_code']}`: {item['summary']}",
                ]
            )
        lines.append("")

    return "\n".join(lines)


def select_diagnosis_destination(root: Path, explicit_destination: str | None, findings: list[Finding]) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    requested = Path(explicit_destination).expanduser().resolve() if explicit_destination else root / "diagnosis" / timestamp
    if path_is_writable(requested):
        return requested

    fallback = Path(tempfile.gettempdir()) / "scafforge-diagnosis" / root.name / timestamp
    evidence = [
        f"Requested diagnosis output path was not writable: {requested}",
        f"Audit redirected diagnosis-pack emission to: {fallback}",
    ]
    add_finding(
        findings,
        Finding(
            code="ENV004",
            severity="warning",
            problem="The requested diagnosis-pack output path is not writable from the current host workspace.",
            root_cause="Audit always emits a diagnosis pack, but the default or requested output location may live outside the host's writable roots. Without redirection, a host-side diagnosis run can fail even though repo inspection succeeded.",
            files=[],
            safer_pattern="Pass `--diagnosis-output-dir` when auditing repos outside writable roots, or let the audit fall back to a writable host-local diagnosis directory and record that redirection explicitly.",
            evidence=evidence,
        ),
    )
    return fallback


def emit_diagnosis_pack(
    root: Path,
    findings: list[Finding],
    destination: Path,
    logs: list[Path],
    manifest_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    destination.mkdir(parents=True, exist_ok=True)
    recommendations = build_ticket_recommendations(findings)
    next_step = recommended_next_step(findings, recommendations)
    reports = {
        DIAGNOSIS_REPORTS["report_1"]: render_report_one(root, findings, generated_at, logs),
        DIAGNOSIS_REPORTS["report_2"]: render_report_two(findings),
        DIAGNOSIS_REPORTS["report_3"]: render_report_three(findings),
        DIAGNOSIS_REPORTS["report_4"]: render_report_four(root, findings, recommendations),
    }
    for filename, content in reports.items():
        (destination / filename).write_text(content + "\n", encoding="utf-8")

    manifest: dict[str, Any] = {
        "generated_at": generated_at,
        "repo_root": str(root),
        "finding_count": len(findings),
        "result_state": "validated failures found" if findings else "clean",
        "diagnosis_kind": "initial_diagnosis",
        "evidence_mode": "transcript_backed" if logs else "current_state_only",
        "audit_package_commit": current_package_commit(),
        "report_files": {key: value for key, value in DIAGNOSIS_REPORTS.items()},
        "ticket_recommendations": recommendations,
        "package_work_required_first": package_work_required_first(recommendations),
        "recommended_next_step": next_step,
    }
    if logs:
        manifest["supporting_logs"] = [normalize_path(path, root) for path in logs]
    if manifest_overrides:
        manifest.update(manifest_overrides)
    if recommendations:
        payload_name = "recommended-ticket-payload.json"
        manifest["recommended_ticket_payload"] = payload_name
        (destination / payload_name).write_text(json.dumps(recommendations, indent=2) + "\n", encoding="utf-8")

    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {
        "path": str(destination),
        "report_count": len(reports),
        "manifest": manifest,
    }


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
