from __future__ import annotations

import argparse
from collections import Counter
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

from audit_execution_surfaces import ExecutionSurfaceAuditContext, run_execution_surface_audits
from audit_lifecycle_contracts import LifecycleContractAuditContext, run_lifecycle_contract_audits
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
TRANSCRIPT_WORKAROUND_PATTERNS = (
    r'"stage"\s*:\s*"todo"',
    r"workaround",
    r"bypass",
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


def audit_status_model(root: Path, findings: list[Finding]) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        return

    statuses = sorted({status for status in load_manifest_statuses(manifest) if status})
    queue_keys = manifest_queue_keys(manifest)
    stage_like = sorted(set(statuses) & STAGE_LIKE_STATUSES)
    if stage_like:
        add_finding(
            findings,
            Finding(
                code="status-stage-collision",
                severity="error",
                problem="Ticket status encodes transient workflow stage instead of coarse queue state.",
                root_cause="The backlog uses statuses like planned or approved even though transient approval should live in workflow state or explicit artifacts.",
                files=[normalize_path(manifest_path, root)],
                safer_pattern="Use coarse queue statuses only and move plan approval into workflow state plus registered stage artifacts.",
                evidence=[
                    f"Manifest statuses: {', '.join(statuses) if statuses else '(none)'}",
                    f"Queue keys: {', '.join(queue_keys) if queue_keys else '(none)'}",
                ],
            ),
        )

    if queue_keys and stage_like:
        add_finding(
            findings,
            Finding(
                code="dual-state-model",
                severity="error",
                problem="The manifest mixes queue buckets and stage-like per-ticket statuses.",
                root_cause="Two overlapping state machines encourage weaker models to infer next steps from labels instead of from verified stage proofs.",
                files=[normalize_path(manifest_path, root)],
                safer_pattern="Keep the manifest as the queue source of truth and store transient approval in workflow state.",
                evidence=[
                    f"Queue buckets present: {', '.join(queue_keys)}",
                    f"Stage-like statuses present: {', '.join(stage_like)}",
                ],
            ),
        )


def audit_status_semantics_docs(root: Path, findings: list[Finding]) -> None:
    files = [
        root / "docs" / "process" / "ticketing.md",
        root / "tickets" / "README.md",
    ]
    semantics = {path: parse_status_semantics(read_text(path)) for path in files if path.exists()}
    if len(semantics) < 2:
        return

    shared_keys = set.intersection(*(set(values.keys()) for values in semantics.values()))
    mismatches: list[str] = []
    for key in sorted(shared_keys):
        values = {path: mapping[key] for path, mapping in semantics.items()}
        if len(set(values.values())) > 1:
            mismatch = "; ".join(f"{normalize_path(path, root)} -> {value}" for path, value in values.items())
            mismatches.append(f"{key}: {mismatch}")

    if mismatches:
        add_finding(
            findings,
            Finding(
                code="contradictory-status-semantics",
                severity="error",
                problem="Status terms mean different things in different ticket docs.",
                root_cause="Weaker models will follow whichever status definition they most recently read, which creates routing instability.",
                files=[normalize_path(path, root) for path in semantics],
                safer_pattern="Define each status once, keep it coarse, and align all docs to the same wording.",
                evidence=mismatches,
            ),
        )


def audit_planned_tickets_without_artifacts(root: Path, findings: list[Finding]) -> None:
    ticket_dir = root / "tickets"
    if not ticket_dir.exists():
        return

    has_workflow_tools = all(
        (root / relative).exists()
        for relative in (
            ".opencode/tools/artifact_write.ts",
            ".opencode/tools/ticket_lookup.ts",
            ".opencode/tools/ticket_update.ts",
            ".opencode/tools/artifact_register.ts",
            ".opencode/state/workflow-state.json",
        )
    )

    thin_planned: list[str] = []
    for path in ticket_dir.glob("*.md"):
        if path.name in {"README.md", "BOARD.md", "TEMPLATE.md"}:
            continue
        status = ticket_markdown_status(path)
        if status not in {"planned", "approved"}:
            continue
        brief_lines = extract_section_lines(read_text(path), "Implementation Brief")
        if len(brief_lines) <= 4:
            thin_planned.append(normalize_path(path, root))

    if thin_planned and not has_workflow_tools:
        add_finding(
            findings,
            Finding(
                code="planner-status-without-proof",
                severity="error",
                problem="Tickets are marked as planned or approved without a reliable artifact layer proving planner output exists.",
                root_cause="The repo relies on raw ticket text and stage-like statuses rather than explicit planning artifacts and workflow-state gates.",
                files=thin_planned[:10],
                safer_pattern="Keep tickets in coarse queue states and require a planning artifact plus workflow approval state before plan review or implementation.",
                evidence=[
                    f"Thin planned/approved tickets: {len(thin_planned)}",
                    "Missing workflow tool layer: .opencode/tools/artifact_write.ts, .opencode/tools/ticket_lookup.ts, .opencode/tools/ticket_update.ts, .opencode/tools/artifact_register.ts, or .opencode/state/workflow-state.json",
                ],
            ),
        )


def audit_missing_tool_layer(root: Path, findings: list[Finding]) -> None:
    required = [
        ".opencode/tools/artifact_write.ts",
        ".opencode/tools/ticket_lookup.ts",
        ".opencode/tools/ticket_update.ts",
        ".opencode/tools/artifact_register.ts",
        ".opencode/plugins/stage-gate-enforcer.ts",
        ".opencode/plugins/ticket-sync.ts",
        ".opencode/plugins/tool-guard.ts",
        ".opencode/state/workflow-state.json",
    ]
    missing = [path for path in required if not (root / path).exists()]
    if missing:
        add_finding(
            findings,
            Finding(
                code="missing-workflow-tool-layer",
                severity="error",
                problem="The repo is missing the tool and plugin layer needed for explicit workflow-state control.",
                root_cause="Without ticket tools, workflow state, and guard plugins, the agent falls back to fragile raw-file stage management.",
                files=missing,
                safer_pattern="Add artifact-write/register tools, ticket tools, workflow-state, and stage/ticket guard plugins so stage control is explicit and tool-backed.",
                evidence=missing,
            ),
        )


def audit_overloaded_artifact_register(root: Path, findings: list[Finding]) -> None:
    path = root / ".opencode" / "tools" / "artifact_register.ts"
    if not path.exists():
        return

    text = read_text(path)
    evidence: list[str] = []
    if re.search(r"\bcontent\s*:", text):
        evidence.append("artifact_register still exposes a content argument.")
    if "writeText(" in text or "writeFile(" in text:
        evidence.append("artifact_register still writes artifact body text instead of registering metadata only.")

    if evidence:
        add_finding(
            findings,
            Finding(
                code="overloaded-artifact-register",
                severity="error",
                problem="artifact_register is still overloaded to write artifact content as well as register metadata.",
                root_cause="Weak models can pass a summary string through the register tool and overwrite the canonical artifact body.",
                files=[normalize_path(path, root)],
                safer_pattern="Split artifact persistence into `artifact_write` for the full body and register-only `artifact_register` for metadata.",
                evidence=evidence,
            ),
        )


def audit_artifact_persistence_prompt_contract(root: Path, findings: list[Finding]) -> None:
    offenders: list[str] = []
    evidence: list[str] = []

    for path in iter_contract_paths(root):
        text = read_text(path)
        hits = matching_lines(text, ARTIFACT_REGISTER_PERSIST_PATTERNS)
        if not hits:
            continue
        offenders.append(normalize_path(path, root))
        evidence.extend(f"{normalize_path(path, root)} -> {hit}" for hit in hits)

    if offenders:
        add_finding(
            findings,
            Finding(
                code="artifact-persistence-through-register",
                severity="error",
                problem="Prompts or workflow docs still describe artifact_register as the tool that persists full artifact text.",
                root_cause="The prompt contract collapses writing and registration into one step, so weaker models can overwrite canonical artifacts with summaries.",
                files=offenders,
                safer_pattern="Tell stage agents to write full content with `artifact_write` and then register metadata with `artifact_register`.",
                evidence=evidence,
            ),
        )


def audit_artifact_path_contract_drift(root: Path, findings: list[Finding]) -> None:
    offenders: list[str] = []
    evidence: list[str] = []

    for path in iter_contract_paths(root):
        text = read_text(path)
        hits = matching_lines(text, ARTIFACT_PATH_DRIFT_PATTERNS)
        if not hits:
            continue
        offenders.append(normalize_path(path, root))
        evidence.extend(f"{normalize_path(path, root)} -> {hit}" for hit in hits)

    if offenders:
        add_finding(
            findings,
            Finding(
                code="artifact-path-contract-drift",
                severity="error",
                problem="Artifact guidance still points at deprecated path conventions.",
                root_cause="Docs and prompts disagree about the canonical artifact location, which makes stage proof unreliable.",
                files=offenders,
                safer_pattern="Use the stage-specific artifact directories plus `.opencode/state/artifacts/registry.json` consistently across prompts, docs, tools, and skills.",
                evidence=evidence,
            ),
        )


def audit_workflow_vocabulary_drift(root: Path, findings: list[Finding]) -> None:
    offenders: list[str] = []
    evidence: list[str] = []

    for path in iter_contract_paths(root):
        text = read_text(path)
        allowed_terms = {"code_review", "security_review"} if normalized_path(path, root) == ".opencode/lib/workflow.ts" else set()
        hits = [term for term in DEPRECATED_WORKFLOW_TERMS if term in text and term not in allowed_terms]
        if not hits:
            continue
        offenders.append(normalize_path(path, root))
        evidence.extend(f"{normalize_path(path, root)} -> {', '.join(hits)}" for _ in range(1))

    if offenders:
        add_finding(
            findings,
            Finding(
                code="workflow-vocabulary-drift",
                severity="error",
                problem="Workflow tools or docs still use deprecated status or stage vocabulary.",
                root_cause="Stage gates, workflow defaults, and artifact proofs no longer agree on the state machine terms that control execution.",
                files=offenders,
                safer_pattern="Keep workflow defaults and stage checks aligned on `todo|ready|in_progress|blocked|review|qa|done` plus `planning|implementation|review|qa` stage proof.",
                evidence=evidence,
            ),
        )


def audit_artifact_brief_missing_tuple(root: Path, findings: list[Finding]) -> None:
    team_leader = next((path for path in (root / ".opencode" / "agents").glob("*team-leader*.md")), None)
    if not team_leader:
        return

    text = read_text(team_leader)
    if "Canonical artifact path when the stage must persist text" not in text:
        return

    if "Artifact stage when the stage must persist text" in text and "Artifact kind when the stage must persist text" in text:
        return

    add_finding(
        findings,
        Finding(
            code="artifact-brief-missing-tuple",
            severity="warning",
            problem="The team leader delegation brief does not include the artifact stage/kind tuple required by stricter artifact tools.",
            root_cause="A path alone is not enough to derive the canonical `(stage, kind)` pair for every artifact, so weaker models can guess the wrong tuple and fail path validation.",
            files=[normalize_path(team_leader, root)],
            safer_pattern="Include artifact stage, artifact kind, and canonical artifact path whenever a delegated stage must persist text.",
            evidence=[normalize_path(team_leader, root)],
        ),
    )


def audit_workflow_state_desync(root: Path, findings: list[Finding]) -> None:
    path = root / ".opencode" / "tools" / "ticket_update.ts"
    if not path.exists():
        return

    text = read_text(path)
    if (
        "workflow.stage = ticket.stage" not in text
        and "workflow.status = ticket.status" not in text
        and ("workflow.approved_plan = args.approved_plan" not in text or "activeTicket.id === ticket.id" in text)
    ):
        return

    add_finding(
        findings,
        Finding(
            code="workflow-state-desync",
            severity="error",
            problem="ticket_update can copy a background ticket's stage or status into workflow-state without activating that ticket.",
            root_cause="The tool updates the manifest ticket record and then mirrors the edited ticket into workflow-state even when the active ticket remains different.",
            files=[normalize_path(path, root)],
            safer_pattern="Recompute the current active ticket after manifest changes and sync workflow-state from that active ticket only.",
            evidence=[normalize_path(path, root)],
        ),
    )


def audit_handoff_overwrites_start_here(root: Path, findings: list[Finding]) -> None:
    path = root / ".opencode" / "tools" / "handoff_publish.ts"
    if not path.exists():
        return

    text = read_text(path)
    if "await writeText(startHere, content)" not in text or "mergeStartHere" in text:
        return

    add_finding(
        findings,
        Finding(
            code="handoff-overwrites-start-here",
            severity="error",
            problem="handoff_publish overwrites START-HERE.md with a generic generated handoff.",
            root_cause="The closeout tool does not preserve curated repo-specific content in START-HERE, so later sessions lose the canonical read order and live risk/validation notes.",
            files=[normalize_path(path, root)],
            safer_pattern="Write the generated handoff to `.opencode/state/latest-handoff.md` and only merge the managed block into START-HERE when explicit markers are present.",
            evidence=[normalize_path(path, root)],
        ),
    )


def tool_uses_plain_object_args(text: str) -> bool:
    return bool(re.search(r"\btype:\s*\"[A-Za-z]+\"", text) or re.search(r"\brequired:\s*(true|false)\b", text))


def tool_uses_zod_args(text: str) -> bool:
    return "tool.schema." in text or bool(re.search(r"args:\s*{\s*}", text))


def audit_invalid_tool_schemas(root: Path, findings: list[Finding]) -> None:
    tools_dir = root / ".opencode" / "tools"
    if not tools_dir.exists():
        return

    offenders: list[str] = []
    evidence: list[str] = []
    for path in tools_dir.glob("*.ts"):
        text = read_text(path)
        if "export default tool(" not in text:
            continue
        normalized = normalize_path(path, root)
        if tool_uses_plain_object_args(text):
            offenders.append(normalized)
            evidence.append(f"{normalized} uses plain JSON-style tool args (`type`/`required`) instead of `tool.schema`.")
            continue
        if not tool_uses_zod_args(text):
            offenders.append(normalized)
            evidence.append(f"{normalized} does not expose a detectable `tool.schema` arg contract.")

    if offenders:
        add_finding(
            findings,
            Finding(
                code="invalid-opencode-tool-schema",
                severity="error",
                problem="Custom OpenCode tools are not using the Zod-backed `tool.schema` contract expected by the plugin runtime.",
                root_cause="The repo mixes scaffold-era plain-object arg definitions with a plugin API that converts Zod schemas to JSON schema at load time.",
                files=offenders,
                safer_pattern="Define every custom tool arg with `tool.schema.*` and reject plain `{ type, description, required }` objects.",
                evidence=evidence,
            ),
        )


def audit_missing_observability_layer(root: Path, findings: list[Finding]) -> None:
    required = [
        ".opencode/tools/skill_ping.ts",
        ".opencode/plugins/invocation-tracker.ts",
        ".opencode/meta/bootstrap-provenance.json",
        ".opencode/state/.gitignore",
    ]
    missing = [path for path in required if not (root / path).exists()]
    if missing:
        add_finding(
            findings,
            Finding(
                code="missing-observability-layer",
                severity="warning",
                problem="The repo cannot reliably explain how its OpenCode layer was generated or which local skills/tools are actually being used.",
                root_cause="Tracking surfaces for provenance and invocation logging are missing, so audits cannot distinguish never-used skills from invisible activity.",
                files=missing,
                safer_pattern="Add bootstrap provenance, invocation tracking, and a skill ping tool so usage is observable across sessions.",
                evidence=missing,
            ),
        )


def audit_process_change_tracking(root: Path, findings: list[Finding]) -> None:
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    provenance_path = root / ".opencode" / "meta" / "bootstrap-provenance.json"
    workflow = read_json(workflow_path)
    provenance = read_json(provenance_path)

    missing: list[str] = []
    evidence: list[str] = []
    affected_files: list[str] = []

    if not isinstance(workflow, dict):
        workflow_rel = normalize_path(workflow_path, root)
        missing.append(workflow_rel)
        affected_files.append(workflow_rel)
    else:
        workflow_rel = normalize_path(workflow_path, root)
        for key in ("process_version", "process_last_changed_at", "process_last_change_summary", "pending_process_verification"):
            if key not in workflow:
                evidence.append(f"{workflow_rel} is missing `{key}`.")
                if workflow_rel not in affected_files:
                    affected_files.append(workflow_rel)

    if not isinstance(provenance, dict):
        provenance_rel = normalize_path(provenance_path, root)
        missing.append(provenance_rel)
        affected_files.append(provenance_rel)
    else:
        provenance_rel = normalize_path(provenance_path, root)
        if not isinstance(provenance.get("workflow_contract"), dict):
            evidence.append(f"{provenance_rel} is missing `workflow_contract`.")
            if provenance_rel not in affected_files:
                affected_files.append(provenance_rel)
        if not isinstance(provenance.get("managed_surfaces"), dict):
            evidence.append(f"{provenance_rel} is missing `managed_surfaces`.")
            if provenance_rel not in affected_files:
                affected_files.append(provenance_rel)
        if "repair_history" not in provenance:
            evidence.append(f"{provenance_rel} is missing `repair_history`.")
            if provenance_rel not in affected_files:
                affected_files.append(provenance_rel)

    if missing or evidence:
        add_finding(
            findings,
            Finding(
                code="missing-process-change-tracking",
                severity="warning",
                problem="The repo cannot reliably tell whether its operating process was replaced or materially upgraded.",
                root_cause="Workflow state and provenance do not expose a stable process version, managed-surface ownership, and pending post-migration verification state.",
                files=affected_files,
                safer_pattern="Record process version fields in workflow state and managed-surface plus repair history data in bootstrap provenance.",
                evidence=missing + evidence,
            ),
        )


def audit_missing_post_migration_verification(root: Path, findings: list[Finding]) -> None:
    required_tool = ".opencode/tools/ticket_create.ts"
    required_agent_patterns = [
        ".opencode/agents/*backlog-verifier*.md",
        ".opencode/agents/*ticket-creator*.md",
    ]
    found_agents_dir = root / ".opencode" / "agents"
    actual_required: list[str] = []
    if found_agents_dir.exists():
        if not any("backlog-verifier" in path.name for path in found_agents_dir.glob("*.md")):
            actual_required.append(required_agent_patterns[0])
        if not any("ticket-creator" in path.name for path in found_agents_dir.glob("*.md")):
            actual_required.append(required_agent_patterns[1])
    else:
        actual_required.extend(required_agent_patterns)
    if not (root / ".opencode" / "tools" / "ticket_create.ts").exists():
        actual_required.append(required_tool)

    if actual_required:
        add_finding(
            findings,
            Finding(
                code="missing-post-migration-verification-lane",
                severity="warning",
                problem="The repo has no explicit post-migration verification and guarded follow-up ticket path.",
                root_cause="A process replacement can change workflow expectations, but the repo lacks a verifier role or tightly scoped ticket creation tool for resulting backlog repairs.",
                files=actual_required,
                safer_pattern="Add a backlog verifier, a guarded ticket creator, and a ticket creation tool that requires verification proof.",
                evidence=actual_required,
            ),
        )


def audit_partial_workflow_layer_drift(root: Path, findings: list[Finding]) -> None:
    has_core_layer = any(
        (root / path).exists()
        for path in (
            ".opencode/tools/ticket_lookup.ts",
            ".opencode/tools/ticket_update.ts",
            ".opencode/tools/artifact_register.ts",
        )
    )
    if not has_core_layer:
        return

    optional_surfaces = [
        "opencode.jsonc",
        ".opencode/commands",
        ".opencode/tools/context_snapshot.ts",
        ".opencode/tools/handoff_publish.ts",
        ".opencode/plugins/session-compactor.ts",
    ]
    missing = [path for path in optional_surfaces if not (root / path).exists()]
    if missing:
        add_finding(
            findings,
            Finding(
                code="partial-workflow-layer-drift",
                severity="warning",
                problem="The repo has a partial OpenCode workflow layer, but some non-core scaffold surfaces are missing.",
                root_cause="The repo was retrofitted or customized without keeping the restart, handoff, or human-entrypoint surfaces aligned with the tool-backed workflow.",
                files=missing,
                safer_pattern="Keep restart commands, context/handoff tools, and session automation aligned with the repo's current workflow layer.",
                evidence=missing,
            ),
        )


def audit_raw_file_state_ownership(root: Path, findings: list[Finding]) -> None:
    team_leader = next((path for path in (root / ".opencode" / "agents").glob("*team-leader*.md")), None)
    if not team_leader:
        return

    text = read_text(team_leader)
    missing_ticket_tools = not (root / ".opencode" / "tools" / "ticket_update.ts").exists()
    if missing_ticket_tools and ("ticket state" in text.lower() or "manifest.json" in text or "board.md" in text):
        add_finding(
            findings,
            Finding(
                code="raw-file-team-leader-state",
                severity="error",
                problem="The team leader owns ticket state but has no ticket-state tool layer.",
                root_cause="The workflow expects raw file choreography across ticket files, the board, and the manifest instead of using structured tools.",
                files=[normalize_path(team_leader, root)],
                safer_pattern="Give the team leader ticket lookup/update tools and make the board a derived view.",
                evidence=[
                    "Team leader references ticket state or raw tracking surfaces.",
                    "No .opencode/tools/ticket_update.ts present.",
                ],
            ),
        )


def audit_missing_artifact_gates(root: Path, findings: list[Finding]) -> None:
    team_leader = next((path for path in (root / ".opencode" / "agents").glob("*team-leader*.md")), None)
    plan_review = next((path for path in (root / ".opencode" / "agents").glob("*plan-review*.md")), None)
    if not team_leader and not plan_review:
        return

    missing: list[str] = []
    for path in (team_leader, plan_review):
        if not path:
            continue
        text = read_text(path).lower()
        if "artifact" not in text and "approved_plan" not in text and "workflow-state" not in text:
            missing.append(normalize_path(path, root))

    if missing:
        add_finding(
            findings,
            Finding(
                code="missing-artifact-gates",
                severity="error",
                problem="Stage prompts do not require canonical artifact or workflow-state proof before advancing.",
                root_cause="The workflow relies on status inference instead of explicit planning, review, or QA evidence.",
                files=missing,
                safer_pattern="Require artifact proof before plan review, implementation, review, QA, and closeout.",
                evidence=missing,
            ),
        )


def audit_read_only_shell_mutation(root: Path, findings: list[Finding]) -> None:
    agents_dir = root / ".opencode" / "agents"
    if not agents_dir.exists():
        return

    bad_agents: list[str] = []
    for path in agents_dir.glob("*.md"):
        text = read_text(path)
        if not read_only_shell_agent(path):
            continue
        if any(token in text for token in MUTATING_SHELL_TOKENS):
            bad_agents.append(normalize_path(path, root))

    if bad_agents:
        add_finding(
            findings,
            Finding(
                code="read-only-shell-mutation-loophole",
                severity="error",
                problem="Read-only shell agents still allow commands that can mutate repo-tracked files.",
                root_cause="The repo labels an agent as inspection-only while its shell allowlist still includes mutating commands.",
                files=bad_agents,
                safer_pattern="Keep read-only shell allowlists to inspection commands only and move mutation into write-capable roles.",
                evidence=bad_agents,
            ),
        )


def audit_read_only_write_language(root: Path, findings: list[Finding]) -> None:
    agents_dir = root / ".opencode" / "agents"
    if not agents_dir.exists():
        return

    offenders: list[str] = []
    for path in agents_dir.glob("*.md"):
        text = read_text(path).lower()
        if "write: false" not in text or "edit: false" not in text:
            continue
        if any(phrase in text for phrase in WRITE_LANGUAGE):
            offenders.append(normalize_path(path, root))

    if offenders:
        add_finding(
            findings,
            Finding(
                code="read-only-write-language",
                severity="warning",
                problem="Read-only agent prompts still contain direct file-update language.",
                root_cause="Weak models may hallucinate successful writes or route around missing capabilities when prompts imply they should mutate files.",
                files=offenders,
                safer_pattern="Tell read-only agents to return blockers or artifacts, not repo file edits.",
                evidence=offenders,
            ),
        )


def audit_over_scoped_commands(root: Path, findings: list[Finding]) -> None:
    commands_dir = root / ".opencode" / "commands"
    if not commands_dir.exists():
        return

    offenders: list[str] = []
    for path in commands_dir.glob("*.md"):
        text = read_text(path)
        if "## Success Output" in text and "## Follow-On Action" in text and re.search(r"## Follow-On Action\s+Invoke", text, re.IGNORECASE):
            offenders.append(normalize_path(path, root))

    if offenders:
        add_finding(
            findings,
            Finding(
                code="over-scoped-human-command",
                severity="warning",
                problem="Human entrypoint commands also instruct autonomous continuation beyond the stated success output.",
                root_cause="The command contract is mixing summary/preflight responsibilities with automatic lifecycle continuation.",
                files=offenders,
                safer_pattern="Keep commands narrow and let the team leader stop at the command's intended handoff boundary.",
                evidence=offenders,
            ),
        )


def audit_eager_skill_loading(root: Path, findings: list[Finding]) -> None:
    agents_dir = root / ".opencode" / "agents"
    if not agents_dir.exists():
        return

    offenders: list[str] = []
    for path in agents_dir.glob("*.md"):
        text = read_text(path)
        lowered = text.lower()
        if "mode: primary" not in lowered:
            continue
        if "skill:" not in lowered:
            continue
        if has_eager_skill_loading(text):
            offenders.append(normalize_path(path, root))

    if offenders:
        add_finding(
            findings,
            Finding(
                code="eager-skill-loading",
                severity="error",
                problem="A primary agent is told to load skills before it resolves workflow state.",
                root_cause="The prompt front-loads skill-tool setup, which can make weaker models issue malformed skill calls before they inspect the active ticket.",
                files=offenders,
                safer_pattern="Resolve state from ticket tools first and load one explicitly named skill only when it materially reduces ambiguity.",
                evidence=offenders,
            ),
        )


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


def audit_placeholder_local_skills(root: Path, findings: list[Finding]) -> None:
    skills_dir = root / ".opencode" / "skills"
    if not skills_dir.exists():
        return

    offenders: list[str] = []
    evidence: list[str] = []
    for path in sorted(skills_dir.rglob("SKILL.md")):
        text = read_text(path)
        hits = matching_lines(text, PLACEHOLDER_SKILL_PATTERNS)
        if not hits:
            continue
        offenders.append(normalize_path(path, root))
        evidence.extend(f"{normalize_path(path, root)} -> {hit}" for hit in hits)

    if offenders:
        add_finding(
            findings,
            Finding(
                code="SKILL001",
                severity="warning",
                problem="One or more repo-local skills still contain generic placeholder text instead of project-specific guidance.",
                root_cause="project-skill-bootstrap or later managed-surface repair left baseline local skills in a scaffold placeholder state, so agents lose concrete stack and validation guidance.",
                files=offenders,
                safer_pattern="Populate every baseline local skill with concrete repo-specific rules and validation commands; generated `.opencode/skills/` files must not retain template filler.",
                evidence=evidence,
            ),
        )


def audit_model_profile_drift(root: Path, findings: list[Finding]) -> None:
    provenance_path = root / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = read_json(provenance_path)
    runtime_models = provenance.get("runtime_models") if isinstance(provenance, dict) and isinstance(provenance.get("runtime_models"), dict) else {}
    provider = str(runtime_models.get("provider", "")).strip().lower() if isinstance(runtime_models, dict) else ""

    profile_path = root / ".opencode" / "skills" / "model-operating-profile" / "SKILL.md"
    model_matrix_path = root / "docs" / "process" / "model-matrix.md"
    canonical_brief_path = root / "docs" / "spec" / "CANONICAL-BRIEF.md"
    start_here_path = root / "START-HERE.md"
    agents_dir = root / ".opencode" / "agents"

    evidence: list[str] = []
    files: list[str] = []
    package_managed_drift = False

    if not profile_path.exists():
        files.append(normalize_path(profile_path, root))
        evidence.append(f"Missing repo-local model profile skill: {normalize_path(profile_path, root)}.")
        package_managed_drift = True
    else:
        profile_text = read_text(profile_path)
        if "__MODEL_PROVIDER__" in profile_text or "__MODEL_OPERATING_PROFILE_NAME__" in profile_text:
            files.append(normalize_path(profile_path, root))
            evidence.append(f"{normalize_path(profile_path, root)} still contains unresolved model-profile template placeholders.")
            package_managed_drift = True

    candidate_paths = [provenance_path, model_matrix_path, canonical_brief_path, start_here_path]
    if agents_dir.exists():
        candidate_paths.extend(sorted(agents_dir.glob("*.md")))

    deprecated_hits = False
    for path in candidate_paths:
        if not path.exists():
            continue
        text = read_text(path)
        hits = matching_lines(text, DEPRECATED_MODEL_PATTERNS)
        if not hits:
            continue
        deprecated_hits = True
        package_managed_drift = True
        files.append(normalize_path(path, root))
        evidence.extend(f"{normalize_path(path, root)} -> {hit}" for hit in hits)

    if agents_dir.exists():
        for path in sorted(agents_dir.glob("*.md")):
            text = read_text(path)
            model_value = frontmatter_value(text, "model")
            if not model_value or "minimax" not in model_value.lower():
                continue
            temperature = frontmatter_value(text, "temperature")
            top_p = frontmatter_value(text, "top_p")
            top_k = frontmatter_value(text, "top_k")
            if temperature == "0.2" or top_p == "0.7" or top_k is None:
                package_managed_drift = True
                files.append(normalize_path(path, root))
                evidence.append(
                    f"{normalize_path(path, root)} retains older MiniMax sampling defaults "
                    f"(temperature={temperature or 'missing'}, top_p={top_p or 'missing'}, top_k={top_k or 'missing'})."
                )

    should_flag = deprecated_hits or bool(evidence) or ("minimax" in provider and not profile_path.exists())
    if not should_flag:
        return

    add_finding(
        findings,
        Finding(
            code="MODEL001",
            severity="error" if package_managed_drift else "warning",
            problem="Repo-local model operating surfaces are missing or still pinned to deprecated MiniMax defaults.",
            root_cause="Managed repair or retrofit preserved older model/profile surfaces instead of regenerating the repo-local model profile, agent prompts, and model matrix together. Deprecated package-managed defaults such as `MiniMax-M2.5` are drift, not protected user intent, unless newer explicit accepted-decision evidence says otherwise.",
            files=list(dict.fromkeys(files)),
            safer_pattern="Treat deprecated package-managed model defaults as safe repair: regenerate `.opencode/skills/model-operating-profile/SKILL.md`, align provenance/model-matrix/agent frontmatter on the current runtime model choices, and remove deprecated `MiniMax-M2.5` surfaces before implementation continues unless newer explicit accepted-decision evidence says to keep them.",
            evidence=evidence[:10],
        ),
    )


def audit_failed_repair_cycle(root: Path, findings: list[Finding]) -> None:
    latest_previous = load_latest_previous_diagnosis(root)
    if latest_previous is None:
        return

    diagnosis_path, manifest = latest_previous
    provenance_path = root / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = read_json(provenance_path)
    repair_history = provenance.get("repair_history") if isinstance(provenance, dict) and isinstance(provenance.get("repair_history"), list) else []
    diagnosis_generated_at = parse_iso_timestamp(manifest.get("generated_at"))
    if diagnosis_generated_at is None:
        return

    repairs_after_diagnosis: list[str] = []
    for item in repair_history:
        if not isinstance(item, dict):
            continue
        repaired_at = parse_iso_timestamp(item.get("repaired_at") or item.get("timestamp"))
        if repaired_at and repaired_at > diagnosis_generated_at:
            repairs_after_diagnosis.append(str(item.get("summary", "repair run after diagnosis")).strip() or "repair run after diagnosis")

    if not repairs_after_diagnosis:
        return

    previous_codes = repair_routed_codes_from_manifest(manifest)
    if not previous_codes:
        return

    current_codes = {finding.code for finding in findings}
    repeated_codes = sorted(code for code in (previous_codes & current_codes) if code != "WFLOW008")
    if not repeated_codes:
        return

    add_finding(
        findings,
        Finding(
            code="CYCLE001",
            severity="error",
            problem="A previous audit-to-repair cycle did not clear one or more workflow-layer findings before work resumed.",
            root_cause="The repo contains a prior diagnosis pack and a later repair history entry, but the current audit still reproduces workflow-layer findings. That means the previous repair either skipped a required regeneration step, used stale package logic, or misclassified drift as protected intent.",
            files=[
                normalize_path(diagnosis_path / "manifest.json", root),
                normalize_path(provenance_path, root),
            ],
            safer_pattern="Before another repair run, compare the latest diagnosis pack against repair_history, identify which findings persisted, and treat repeated deprecated package-managed drift as a repair failure to fix rather than as preserved intent.",
            evidence=[
                f"Latest prior diagnosis pack: {normalize_path(diagnosis_path, root)}",
                f"Repairs recorded after that diagnosis: {len(repairs_after_diagnosis)}",
                f"Repeated workflow-layer findings: {', '.join(repeated_codes)}",
                *[f"Repair after diagnosis -> {summary}" for summary in repairs_after_diagnosis[:3]],
            ],
        ),
    )


def audit_repeated_diagnosis_churn(root: Path, findings: list[Finding]) -> None:
    diagnoses = load_previous_diagnoses(root)
    if len(diagnoses) < 2:
        return

    current_codes = {
        finding.code
        for finding in findings
        if not finding.code.startswith(("EXEC", "ENV"))
    }
    if not current_codes:
        return

    _, latest_path, latest_manifest = diagnoses[-1]
    latest_generated_at = parse_iso_timestamp(latest_manifest.get("generated_at"))
    if latest_generated_at is None:
        return

    same_day = [item for item in diagnoses if item[0].date() == latest_generated_at.date()]
    if len(same_day) < 2:
        return

    provenance_path = root / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = read_json(provenance_path)
    repair_history = provenance.get("repair_history") if isinstance(provenance, dict) and isinstance(provenance.get("repair_history"), list) else []
    if any(
        (repaired_at := parse_iso_timestamp(item.get("repaired_at") or item.get("timestamp"))) and repaired_at > latest_generated_at
        for item in repair_history
        if isinstance(item, dict)
    ):
        return

    repeated_codes: set[str] = set()
    compared_packs: list[str] = []
    current_package = current_package_commit()
    for _, diagnosis_path, manifest in same_day[-4:]:
        if manifest_package_commit(manifest) != current_package:
            continue
        codes = repair_routed_codes_from_manifest(manifest)
        overlap = current_codes & codes
        if overlap:
            compared_packs.append(normalize_path(diagnosis_path, root))
            repeated_codes.update(overlap)

    if not repeated_codes:
        return

    add_finding(
        findings,
        Finding(
            code="CYCLE002",
            severity="error",
            problem="Repeated diagnosis packs are re-reporting the same repair-routed findings without any intervening package or process-version change.",
            root_cause="Audit kept producing new diagnosis packs even though the repo had no later Scafforge repair or workflow-contract change after the latest diagnosis. That creates audit churn instead of new decision-making evidence.",
            files=[
                normalize_path(latest_path / "manifest.json", root),
                normalize_path(provenance_path, root),
            ],
            safer_pattern="Stop rerunning subject-repo audit until Scafforge package work changes the managed workflow contract or process version, then rerun one fresh audit against the updated package.",
            evidence=[
                f"Same-day diagnosis packs considered: {len(same_day)} on {latest_generated_at.date().isoformat()}",
                f"Latest diagnosis pack without later repair: {normalize_path(latest_path, root)}",
                f"Current audit package commit: {current_package}",
                f"Repeated repair-routed findings: {', '.join(sorted(repeated_codes))}",
                f"Compared packs: {', '.join(compared_packs[:4])}",
            ],
        ),
    )


def audit_verification_basis_regression(root: Path, findings: list[Finding]) -> None:
    diagnoses = load_previous_diagnoses(root)
    if len(diagnoses) < 2:
        return

    transcript_basis: tuple[datetime, Path, dict[str, Any], set[str]] | None = None
    false_clean_pack: tuple[datetime, Path, dict[str, Any]] | None = None

    for generated_at, diagnosis_path, manifest in diagnoses:
        logs = manifest_supporting_logs(manifest)
        repair_codes = repair_routed_codes_from_manifest(manifest)
        if logs and repair_codes:
            transcript_basis = (generated_at, diagnosis_path, manifest, repair_codes)
            false_clean_pack = None
            continue
        if transcript_basis is None:
            continue
        if generated_at <= transcript_basis[0]:
            continue
        if generated_at.date() != transcript_basis[0].date():
            continue
        if logs:
            continue
        if manifest.get("finding_count") != 0:
            continue
        if manifest_diagnosis_kind(manifest) == "initial_diagnosis":
            continue
        false_clean_pack = (generated_at, diagnosis_path, manifest)

    if transcript_basis is None or false_clean_pack is None:
        return

    basis_generated_at, basis_path, _, basis_codes = transcript_basis
    false_clean_generated_at, false_clean_path, _ = false_clean_pack
    provenance_path = root / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = read_json(provenance_path)
    repair_history = provenance.get("repair_history") if isinstance(provenance, dict) and isinstance(provenance.get("repair_history"), list) else []
    repairs_after_basis = [
        item
        for item in repair_history
        if isinstance(item, dict)
        and (repaired_at := parse_iso_timestamp(item.get("repaired_at") or item.get("timestamp")))
        and repaired_at > basis_generated_at
    ]

    add_finding(
        findings,
        Finding(
            code="CYCLE003",
            severity="error",
            problem="A later zero-finding diagnosis pack dropped the earlier transcript evidence basis, so the workflow was recorded as clean without proving the original trap was eliminated.",
            root_cause="Verification re-ran audit against current repo state only. Because the transcript-backed repair basis was not carried forward automatically, a later diagnosis pack could report zero findings without replaying the causal deadlock conditions that triggered repair.",
            files=[
                normalize_path(basis_path / "manifest.json", root),
                normalize_path(false_clean_path / "manifest.json", root),
                normalize_path(provenance_path, root),
            ],
            safer_pattern="Carry forward supporting logs automatically into repair verification, emit the post-repair diagnosis pack from the repair runner itself, and distinguish current-state cleanliness from causal-regression verification before calling the workflow clean.",
            evidence=[
                f"Transcript-backed diagnosis basis: {normalize_path(basis_path, root)}",
                f"Basis repair-routed findings: {', '.join(sorted(basis_codes))}",
                f"Later zero-finding pack without supporting logs: {normalize_path(false_clean_path, root)}",
                f"False-clean pack generated at {false_clean_generated_at.isoformat()} after transcript basis at {basis_generated_at.isoformat()}",
                f"Repairs recorded after transcript basis: {len(repairs_after_basis)}",
            ],
        ),
    )


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


def audit_session_chronology(root: Path, findings: list[Finding], logs: list[Path]) -> None:
    for path in logs:
        text = read_text(path)
        if not text:
            continue

        stale_state = any(re.search(pattern, text, re.IGNORECASE) for pattern in TRANSCRIPT_STALE_STATE_PATTERNS)
        later_progress = any(re.search(pattern, text, re.IGNORECASE) for pattern in TRANSCRIPT_PROGRESS_PATTERNS)
        overclaim = any(re.search(pattern, text, re.IGNORECASE) for pattern in HANDOFF_OVERCLAIM_PATTERNS)
        full_suite_result = any(re.search(pattern, text, re.IGNORECASE) for pattern in TRANSCRIPT_FULL_SUITE_RESULT_PATTERNS)
        if not (stale_state and later_progress and overclaim and not full_suite_result):
            continue

        evidence = []
        evidence.extend(matching_lines(text, TRANSCRIPT_STALE_STATE_PATTERNS))
        evidence.extend(matching_lines(text, TRANSCRIPT_PROGRESS_PATTERNS))
        evidence.extend(matching_lines(text, HANDOFF_OVERCLAIM_PATTERNS))
        evidence.append("No later full-suite execution result was found in the supplied session log.")

        add_finding(
            findings,
            Finding(
                code="SESSION001",
                severity="error",
                problem="The supplied session transcript shows a later reasoning failure that current-state-only diagnosis would miss.",
                root_cause="The session began from stale resume state, later gathered new implementation or QA evidence, then still published an over-broad blocker summary without a later full-suite execution result.",
                files=[normalize_path(path, root)],
                safer_pattern="When session logs are supplied, audit chronology first: separate stale resume state from later evidence, then explain any final summary that outruns the executed commands before reconciling current repo state.",
                evidence=evidence[:8],
            ),
        )


def audit_session_transition_thrash(root: Path, findings: list[Finding], logs: list[Path]) -> None:
    for path in logs:
        text = read_text(path)
        if not text:
            continue

        hits = matching_line_numbers(text, TRANSCRIPT_LIFECYCLE_ERROR_PATTERNS)
        if not hits:
            continue

        counts = Counter(line for _, line in hits)
        repeated = [(line, count) for line, count in counts.items() if count >= 2]
        if not repeated:
            continue

        evidence = [f"Repeated lifecycle blocker {count}x -> {line}" for line, count in repeated[:3]]
        add_finding(
            findings,
            Finding(
                code="SESSION002",
                severity="error",
                problem="The supplied session transcript shows repeated retries of the same rejected lifecycle transition.",
                root_cause="Instead of treating the repeated `ticket_update` rejection as a contract contradiction, the agent kept probing the state machine and burned time without acquiring new evidence.",
                files=[normalize_path(path, root)],
                safer_pattern="After the same lifecycle blocker repeats, re-run `ticket_lookup`, read `transition_guidance`, load `ticket-execution` if needed, and stop with a blocker instead of retrying the same transition.",
                evidence=evidence,
            ),
        )


def audit_session_workaround_search(root: Path, findings: list[Finding], logs: list[Path]) -> None:
    for path in logs:
        text = read_text(path)
        if not text:
            continue

        events = parse_transcript_tool_events(text)
        evidence: list[str] = []
        for event in events:
            if event.tool != "ticket_update" or not isinstance(event.args, dict):
                continue
            stage = str(event.args.get("stage", "")).strip()
            if stage and stage not in {"planning", "plan_review", "implementation", "review", "qa", "smoke-test", "closeout"}:
                evidence.append(f"Line {event.line_number}: unsupported ticket_update stage `{stage}` from {event.assistant or 'unknown assistant'}.")
        reasoning_hits = matching_assistant_reasoning_line_numbers(
            text,
            (r"\bworkaround\b", r"\bbypass\b", *TRANSCRIPT_SOFT_BYPASS_PATTERNS),
        )
        if not reasoning_hits:
            reasoning_hits = matching_non_tool_line_numbers(
                text,
                (r"\bworkaround\b", r"\bbypass\b", *TRANSCRIPT_SOFT_BYPASS_PATTERNS),
            )
        evidence.extend(f"Line {line_number}: {line}" for line_number, line in reasoning_hits[:5])
        if not evidence:
            continue

        add_finding(
            findings,
            Finding(
                code="SESSION003",
                severity="error",
                problem="The supplied session transcript shows the agent searching for workflow bypasses or soft dependency overrides instead of following the lifecycle contract.",
                root_cause="Once the lifecycle gate became confusing, the agent started trying unsupported stages, explicit workarounds, or softer 'close it anyway' / dependency-override reasoning instead of resolving the missing proof or contradictory contract.",
                files=[normalize_path(path, root)],
                safer_pattern="Reject unsupported stages and dependency overrides up front, tell the coordinator not to probe alternate transitions or close blocked tickets anyway, and return the contract contradiction as a blocker when the required proof is missing.",
                evidence=evidence,
            ),
        )


def audit_session_broken_tooling(root: Path, findings: list[Finding], logs: list[Path]) -> None:
    for path in logs:
        text = read_text(path)
        if not text:
            continue

        evidence: list[str] = []
        for event in parse_transcript_tool_events(text):
            if not event.error:
                continue
            if not any(re.search(pattern, event.error, re.IGNORECASE) for pattern in TRANSCRIPT_BROKEN_TOOL_PATTERNS):
                continue
            tool_class = "internal workflow helper" if event.tool.startswith("_workflow_") else "tool"
            error_summary = event.error.splitlines()[0].strip()
            evidence.append(f"Line {event.line_number}: {tool_class} `{event.tool}` failed with `{error_summary}`.")

        evidence.extend(
            f"Line {line_number}: {line}"
            for line_number, line in matching_line_numbers(text, (r"Available tools:.*_workflow_",))[:3]
        )
        if not evidence:
            continue

        add_finding(
            findings,
            Finding(
                code="WFLOW015",
                severity="error",
                problem="The supplied session transcript shows the runtime exposing or invoking broken workflow helper tools instead of only executable tool modules.",
                root_cause="The tool surface leaked `_workflow_*` helpers or other non-executable exports into the model-visible tool list. When the coordinator called them, the runtime failed before any workflow logic could run.",
                files=[normalize_path(path, root), ".opencode/lib/workflow.ts"],
                safer_pattern="Keep workflow helpers private under `.opencode/lib/workflow.ts`, expose only real `tool({...})` modules to the model, and make audit treat transcript-level missing-`execute` failures as managed workflow-contract defects.",
                evidence=evidence[:6],
            ),
        )


def audit_session_smoke_test_override_failure(root: Path, findings: list[Finding], logs: list[Path]) -> None:
    smoke_test = root / ".opencode" / "tools" / "smoke_test.ts"
    for path in logs:
        text = read_text(path)
        if not text:
            continue

        evidence: list[str] = []
        saw_override = False
        for event in parse_transcript_tool_events(text):
            if event.tool != "smoke_test" or not isinstance(event.args, dict):
                continue
            override = event.args.get("command_override")
            if isinstance(override, list) and override:
                saw_override = True
                if event.output and '"failure_classification": "environment"' in event.output:
                    evidence.append(
                        f"Line {event.line_number}: smoke_test with command_override returned `failure_classification: environment` before the requested override command ran."
                    )

        if not saw_override:
            continue

        evidence.extend(
            f"Line {line_number}: {line}"
            for line_number, line in matching_line_numbers(text, TRANSCRIPT_SMOKE_OVERRIDE_FAILURE_PATTERNS)[:4]
        )
        if not evidence:
            continue

        add_finding(
            findings,
            Finding(
                code="WFLOW016",
                severity="error",
                problem="The supplied session transcript shows the managed smoke-test override path failing before the requested smoke command starts.",
                root_cause="The generated `smoke_test` tool treated a shell-style environment assignment like `UV_CACHE_DIR=...` as the executable name for `spawn()`. That turns a valid explicit override command into an `ENOENT` tool failure and misclassifies the result as a runtime environment problem.",
                files=[normalize_path(path, root), normalize_path(smoke_test, root)],
                safer_pattern="Parse shell-style smoke-test overrides before execution, strip leading `KEY=VALUE` env assignments into the spawn environment, and report malformed overrides as configuration errors rather than environment failures.",
                evidence=evidence[:6],
            ),
    )


def audit_session_smoke_test_acceptance_drift(root: Path, findings: list[Finding], logs: list[Path]) -> None:
    smoke_test = root / ".opencode" / "tools" / "smoke_test.ts"
    for path in logs:
        text = read_text(path)
        if not text:
            continue

        acceptance_commands = extract_transcript_smoke_acceptance_commands(text)
        if not acceptance_commands:
            continue

        evidence: list[str] = []
        for event in parse_transcript_tool_events(text):
            if event.tool != "smoke_test":
                continue
            if not isinstance(event.args, dict):
                continue
            if isinstance(event.args.get("command_override"), list) and event.args.get("command_override"):
                continue

            payload = parse_json_object(event.output or "")
            if not payload:
                continue
            raw_commands = payload.get("commands")
            if not isinstance(raw_commands, list):
                continue
            executed_commands = [
                normalize_shell_command(str(item.get("command", "")).strip())
                for item in raw_commands
                if isinstance(item, dict) and str(item.get("command", "")).strip()
            ]
            smoke_commands = [command for command in executed_commands if re.search(r"\b(pytest|cargo test|go test|ruff check|npm run test|pnpm run test|yarn test|bun run test)\b", command, re.IGNORECASE)]
            if not smoke_commands:
                continue

            if any(command.lower() == acceptance.lower() for command in smoke_commands for acceptance in acceptance_commands):
                continue

            evidence.append(
                f"Line {event.line_number}: smoke_test ran `{smoke_commands[0]}` even though transcript acceptance criteria already specified `{acceptance_commands[0]}`."
            )
            if isinstance(event.args.get("test_paths"), list) and event.args.get("test_paths"):
                evidence.append(
                    f"Line {event.line_number}: smoke_test relied on caller-supplied test_paths instead of the ticket's explicit smoke acceptance command."
                )

        evidence.extend(
            f"Line {line_number}: {line}"
            for line_number, line in matching_line_numbers(text, TRANSCRIPT_SMOKE_ACCEPTANCE_PATTERNS)[:3]
        )
        if not any(item.startswith("Line ") and "smoke_test ran `" in item for item in evidence):
            continue

        add_finding(
            findings,
            Finding(
                code="WFLOW017",
                severity="error",
                problem="The supplied session transcript shows the smoke-test stage running a heuristic command that does not match the ticket's explicit acceptance command.",
                root_cause="The generated `smoke_test` tool fell back to repo-level pytest detection or caller-supplied `test_paths` instead of binding itself to the ticket's canonical smoke acceptance command. That can widen smoke scope to unrelated failures or narrow it away from the actual closeout requirement.",
                files=[normalize_path(path, root), normalize_path(smoke_test, root)],
                safer_pattern="Treat acceptance-backed smoke commands as canonical, let `smoke_test` infer them automatically, and reject heuristic scope changes unless the caller provides an intentional exact command override.",
                evidence=evidence[:6],
            ),
        )


def audit_session_handoff_closeout_lease_deadlock(root: Path, findings: list[Finding], logs: list[Path]) -> None:
    handoff_publish = root / ".opencode" / "tools" / "handoff_publish.ts"
    for path in logs:
        text = read_text(path)
        if not text:
            continue

        evidence: list[str] = []
        for event in parse_transcript_tool_events(text):
            if event.tool != "handoff_publish":
                continue
            if not event.error or "missing_ticket_write_lease" not in event.error:
                continue
            evidence.append(
                f"Line {event.line_number}: handoff_publish failed with `{event.error.splitlines()[0].strip()}` after closeout."
            )
        evidence.extend(
            f"Line {line_number}: {line}"
            for line_number, line in matching_line_numbers(text, TRANSCRIPT_HANDOFF_LEASE_CONTRADICTION_PATTERNS)[:4]
        )
        if not evidence:
            continue

        add_finding(
            findings,
            Finding(
                code="WFLOW022",
                severity="error",
                problem="The supplied session transcript shows restart-surface publication blocked by a closed-ticket write-lease requirement.",
                root_cause="`handoff_publish` still behaved like an ordinary lane mutation and required an active write lease after the ticket had already been closed. That leaves the workflow with no legal way to publish truthful restart surfaces during closeout.",
                files=[normalize_path(path, root), normalize_path(handoff_publish, root)],
                safer_pattern="Let `handoff_publish` update derived restart surfaces after closeout without reacquiring a normal write lease on the closed ticket, and audit transcript evidence for this contradiction explicitly.",
                evidence=evidence[:6],
            ),
        )


def audit_session_acceptance_scope_contamination(root: Path, findings: list[Finding], logs: list[Path]) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    manifest = read_json(manifest_path)
    tickets = manifest.get("tickets") if isinstance(manifest, dict) and isinstance(manifest.get("tickets"), list) else []
    tickets_by_id = {
        str(ticket.get("id")): ticket
        for ticket in tickets
        if isinstance(ticket, dict) and isinstance(ticket.get("id"), str)
    }
    for path in logs:
        text = read_text(path)
        if not text:
            continue

        acceptance_hits = matching_line_numbers(text, (r"acceptance criterion.*exits 0", r"acceptance criteria.*exits 0"))
        scope_hits = matching_line_numbers(
            text,
            (
                r"out of .* scope",
                r"pre-existing .* scope",
                r"handled by EXEC-\d+",
                r"literal acceptance criterion",
                r"creates a tension",
                r"Should .* scope items be fixed as part of .* to satisfy the literal acceptance criterion",
            ),
        )
        if not acceptance_hits or not scope_hits:
            continue

        mentioned_ids = {
            match
            for _, line in [*acceptance_hits[:2], *scope_hits[:4]]
            for match in re.findall(r"\b[A-Z]+-\d+\b", line)
        }
        dependency_encoded = False
        for ticket_id in mentioned_ids:
            ticket = tickets_by_id.get(ticket_id)
            if not isinstance(ticket, dict):
                continue
            depends_on = {str(item).strip() for item in ticket.get("depends_on", []) if isinstance(item, str) and str(item).strip()}
            if depends_on & mentioned_ids:
                dependency_encoded = True
                break
        if dependency_encoded:
            continue

        evidence = [
            f"Line {line_number}: {line}"
            for line_number, line in [*acceptance_hits[:2], *scope_hits[:4]]
        ]
        add_finding(
            findings,
            Finding(
                code="WFLOW023",
                severity="error",
                problem="The supplied session transcript shows a ticket whose literal acceptance command reaches into later-ticket scope, so the ticket cannot close without violating its own scope boundary.",
                root_cause="Ticket decomposition allowed a closeout command that still depended on work owned by a later ticket. That forced the coordinator to choose between falsifying acceptance, broadening scope, or blocking on work that the ticket explicitly said it did not own.",
                files=[normalize_path(path, root), normalize_path(manifest_path, root)],
                safer_pattern="Keep ticket acceptance scope-isolated. If the literal closeout command depends on later-ticket work, split the tickets differently or encode the dependency in the ticket structure instead of shipping a contradictory acceptance command.",
                evidence=evidence,
            ),
        )


def audit_session_evidence_free_verification(root: Path, findings: list[Finding], logs: list[Path]) -> None:
    for path in logs:
        text = read_text(path)
        if not text:
            continue

        failure_hits = matching_line_numbers(text, TRANSCRIPT_VERIFICATION_FAILURE_PATTERNS)
        pass_hits = matching_line_numbers(text, TRANSCRIPT_PASS_CLAIM_PATTERNS)
        if not failure_hits or not pass_hits:
            continue

        first_failure_line = failure_hits[0][0]
        recovery_hits = matching_line_numbers(text, TRANSCRIPT_EXECUTION_RECOVERY_PATTERNS)
        later_pass_hits = []
        for line_number, line in pass_hits:
            if line_number <= first_failure_line:
                continue
            recovered = any(first_failure_line < recovery_line < line_number for recovery_line, _ in recovery_hits)
            if not recovered:
                later_pass_hits.append((line_number, line))
        if not later_pass_hits:
            continue

        evidence = [
            f"Verification failure at line {failure_hits[0][0]} -> {failure_hits[0][1]}",
            *[f"Later PASS claim at line {line_number} -> {line}" for line_number, line in later_pass_hits[:4]],
        ]
        add_finding(
            findings,
            Finding(
                code="SESSION004",
                severity="error",
                problem="The supplied session transcript shows PASS-style implementation, QA, or smoke-test claims after validation had already failed or could not run.",
                root_cause="The coordinator substituted visual inspection or expected results for executable proof, then let artifacts claim PASS even though the earlier transcript said verification commands were unavailable.",
                files=[normalize_path(path, root)],
                safer_pattern="If validation cannot run, return a blocker; require raw command output in implementation and QA artifacts, and reserve smoke-test PASS proof to the deterministic `smoke_test` tool.",
                evidence=evidence,
            ),
        )


def audit_session_coordinator_artifact_authorship(root: Path, findings: list[Finding], logs: list[Path]) -> None:
    for path in logs:
        text = read_text(path)
        if not text:
            continue

        evidence: list[str] = []
        for event in parse_transcript_tool_events(text):
            if event.tool != "artifact_write" or not isinstance(event.args, dict):
                continue
            if not is_coordinator_assistant(event.assistant):
                continue
            stage = str(event.args.get("stage", "")).strip()
            if stage not in COORDINATOR_ARTIFACT_STAGES:
                continue
            artifact_path = str(event.args.get("path", "")).strip()
            evidence.append(
                f"Line {event.line_number}: coordinator {event.assistant} wrote `{stage}` artifact"
                + (f" at `{artifact_path}`." if artifact_path else ".")
            )
        if not evidence:
            continue

        add_finding(
            findings,
            Finding(
                code="SESSION005",
                severity="error",
                problem="The supplied session transcript shows the coordinator writing specialist stage artifacts directly instead of routing those outputs through the owning lane or deterministic tool.",
                root_cause="Once the workflow became confusing, the team leader started manufacturing implementation, review, QA, or smoke-test evidence itself instead of delegating the stage body to the assigned specialist or deterministic tool.",
                files=[normalize_path(path, root)],
                safer_pattern="Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.",
                evidence=evidence[:6],
            ),
        )


def audit_session_operator_trap(root: Path, findings: list[Finding], logs: list[Path]) -> None:
    for path in logs:
        text = read_text(path)
        if not text:
            continue

        categories: list[tuple[str, str]] = []
        repeated = matching_line_numbers(text, TRANSCRIPT_LIFECYCLE_ERROR_PATTERNS)
        if repeated:
            categories.append(("workflow thrash", f"Line {repeated[0][0]}: {repeated[0][1]}"))

        reasoning_hits = matching_assistant_reasoning_line_numbers(
            text,
            (r"\bworkaround\b", r"\bbypass\b", *TRANSCRIPT_SOFT_BYPASS_PATTERNS),
        )
        if not reasoning_hits:
            reasoning_hits = matching_non_tool_line_numbers(text, (r"\bworkaround\b", r"\bbypass\b", *TRANSCRIPT_SOFT_BYPASS_PATTERNS))
        if reasoning_hits:
            categories.append(("bypass search", f"Line {reasoning_hits[0][0]}: {reasoning_hits[0][1]}"))

        handoff_hits = matching_line_numbers(text, TRANSCRIPT_HANDOFF_LEASE_CONTRADICTION_PATTERNS)
        if handoff_hits:
            categories.append(("closeout lease contradiction", f"Line {handoff_hits[0][0]}: {handoff_hits[0][1]}"))

        acceptance_hits = matching_line_numbers(text, TRANSCRIPT_ACCEPTANCE_SCOPE_TENSION_PATTERNS)
        if acceptance_hits:
            categories.append(("acceptance scope tension", f"Line {acceptance_hits[0][0]}: {acceptance_hits[0][1]}"))

        override_hits = matching_line_numbers(text, TRANSCRIPT_SMOKE_OVERRIDE_FAILURE_PATTERNS)
        if override_hits:
            categories.append(("tool execution contradiction", f"Line {override_hits[0][0]}: {override_hits[0][1]}"))

        if len(categories) < 2:
            continue

        evidence = [f"{label}: {detail}" for label, detail in categories[:5]]
        add_finding(
            findings,
            Finding(
                code="SESSION006",
                severity="error",
                problem="The supplied session transcript shows the operator trapped between contradictory workflow rules instead of having one clear legal next move.",
                root_cause="Multiple workflow surfaces failed at once: lifecycle gates, closeout publication, acceptance scope, or deterministic tool execution disagreed about what could legally happen next. The coordinator then had to infer workarounds instead of following one competent contract path.",
                files=[normalize_path(path, root)],
                safer_pattern="Design every workflow state so it exposes one legal next action, one named owner, and one blocker return path. When transcript evidence shows a trap, audit adjacent surfaces together instead of treating each symptom as isolated noise.",
                evidence=evidence,
            ),
        )


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


def audit_repo(root: Path, logs: list[Path] | None = None) -> list[Finding]:
    findings: list[Finding] = []
    execution_ctx = execution_surface_audit_context()
    restart_ctx = restart_surface_audit_context()
    ticket_graph_ctx = ticket_graph_audit_context()
    lifecycle_ctx = lifecycle_contract_audit_context()
    audit_status_model(root, findings)
    audit_status_semantics_docs(root, findings)
    audit_planned_tickets_without_artifacts(root, findings)
    audit_missing_tool_layer(root, findings)
    audit_overloaded_artifact_register(root, findings)
    audit_artifact_persistence_prompt_contract(root, findings)
    audit_artifact_path_contract_drift(root, findings)
    audit_workflow_vocabulary_drift(root, findings)
    audit_artifact_brief_missing_tuple(root, findings)
    audit_workflow_state_desync(root, findings)
    audit_handoff_overwrites_start_here(root, findings)
    audit_invalid_tool_schemas(root, findings)
    audit_missing_observability_layer(root, findings)
    audit_process_change_tracking(root, findings)
    audit_missing_post_migration_verification(root, findings)
    audit_partial_workflow_layer_drift(root, findings)
    audit_raw_file_state_ownership(root, findings)
    audit_missing_artifact_gates(root, findings)
    audit_read_only_shell_mutation(root, findings)
    audit_read_only_write_language(root, findings)
    audit_over_scoped_commands(root, findings)
    audit_eager_skill_loading(root, findings)
    audit_placeholder_local_skills(root, findings)
    audit_model_profile_drift(root, findings)
    audit_failed_repair_cycle(root, findings)
    audit_repeated_diagnosis_churn(root, findings)
    audit_verification_basis_regression(root, findings)
    run_execution_surface_audits(root, findings, execution_ctx)
    run_restart_surface_audits(root, findings, restart_ctx)
    run_ticket_graph_audits(root, findings, ticket_graph_ctx)
    run_lifecycle_contract_audits(root, findings, lifecycle_ctx)
    audit_session_chronology(root, findings, logs or [])
    audit_session_transition_thrash(root, findings, logs or [])
    audit_session_workaround_search(root, findings, logs or [])
    audit_session_broken_tooling(root, findings, logs or [])
    audit_session_smoke_test_override_failure(root, findings, logs or [])
    audit_session_smoke_test_acceptance_drift(root, findings, logs or [])
    audit_session_handoff_closeout_lease_deadlock(root, findings, logs or [])
    audit_session_acceptance_scope_contamination(root, findings, logs or [])
    audit_session_evidence_free_verification(root, findings, logs or [])
    audit_session_coordinator_artifact_authorship(root, findings, logs or [])
    audit_session_operator_trap(root, findings, logs or [])
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
