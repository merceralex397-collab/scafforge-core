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
class Finding:
    code: str
    severity: str
    problem: str
    root_cause: str
    files: list[str]
    safer_pattern: str
    evidence: list[str]


@dataclass
class TranscriptToolEvent:
    assistant: str
    tool: str
    line_number: int
    args: dict[str, Any] | None


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
                            parsed = json.loads(body)
                        except json.JSONDecodeError:
                            parsed = None
                        if isinstance(parsed, dict):
                            args = parsed
                break
            cursor += 1

        events.append(TranscriptToolEvent(assistant=current_assistant, tool=tool_name, line_number=index + 1, args=args))
        index += 1
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
    diagnosis_root = root / "diagnosis"
    if not diagnosis_root.exists():
        return None

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

    if not candidates:
        return None
    _, latest_path, latest_manifest = sorted(candidates, key=lambda item: item[0])[-1]
    return latest_path, latest_manifest


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
        allowed_terms = {"code_review", "security_review"} if normalized_path(path, root) == ".opencode/tools/_workflow.ts" else set()
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
        if path.name == "_workflow.ts":
            continue
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


def audit_active_process_verification(root: Path, findings: list[Finding]) -> None:
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    manifest_path = root / "tickets" / "manifest.json"
    workflow = read_json(workflow_path)
    manifest = read_json(manifest_path)
    if not isinstance(workflow, dict) or not isinstance(manifest, dict):
        return
    if workflow.get("pending_process_verification") is not True:
        return

    affected = tickets_needing_process_verification(manifest, workflow)
    if not affected:
        return

    change_time = str(workflow.get("process_last_changed_at", "")).strip() or "unknown"
    affected_ids = [str(ticket.get("id", "")).strip() for ticket in affected if str(ticket.get("id", "")).strip()]
    add_finding(
        findings,
        Finding(
            code="WFLOW008",
            severity="warning",
            problem="Post-repair process verification is still pending for one or more historical done tickets.",
            root_cause="The workflow contract changed, but the repo still contains completed tickets whose trust predates the current process window or lacks current backlog-verification evidence. Declaring the repo clean before that reverification finishes hides unresolved process risk.",
            files=[normalize_path(workflow_path, root), normalize_path(manifest_path, root)],
            safer_pattern="Keep `pending_process_verification` visible, route the backlog verifier across the affected done-ticket set, and do not call verification clean until `ticket_reverify` or current backlog-verification evidence clears those tickets.",
            evidence=[
                f"{normalize_path(workflow_path, root)} records pending_process_verification = true.",
                f"Current process window started at: {change_time}",
                f"Affected done tickets: {', '.join(affected_ids[:12])}" + (" ..." if len(affected_ids) > 12 else ""),
            ],
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

    previous_codes = {
        str(item.get("source_finding_code", "")).strip()
        for item in manifest.get("ticket_recommendations", [])
        if isinstance(item, dict) and str(item.get("route", "")).strip() == "scafforge-repair"
    }
    if not previous_codes:
        return

    current_codes = {finding.code for finding in findings}
    repeated_codes = sorted(previous_codes & current_codes)
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


def audit_bootstrap_deadlock(root: Path, findings: list[Finding]) -> None:
    tool_path = root / ".opencode" / "tools" / "environment_bootstrap.ts"
    if not tool_path.exists():
        return

    tool_text = read_text(tool_path)
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    workflow = read_json(workflow_path)
    workflow_bootstrap = workflow.get("bootstrap") if isinstance(workflow, dict) and isinstance(workflow.get("bootstrap"), dict) else {}
    proof_artifact_value = workflow_bootstrap.get("proof_artifact") if isinstance(workflow_bootstrap, dict) else None
    proof_artifact = root / str(proof_artifact_value) if isinstance(proof_artifact_value, str) and proof_artifact_value else None
    proof_text = read_text(proof_artifact) if proof_artifact else ""

    pyvenv_text = read_text(root / ".venv" / "pyvenv.cfg")
    has_uv_lock = (root / "uv.lock").exists()
    uv_managed_venv = bool(re.search(r"^uv\s*=", pyvenv_text, re.MULTILINE))
    hardcoded_system_pip = 'argv: ["python3", "-m", "pip"' in tool_text
    pip_deadlock = "No module named pip" in proof_text
    bootstrap_failed = isinstance(workflow_bootstrap, dict) and workflow_bootstrap.get("status") == "failed"

    current_python3_pip_missing = False
    rc, output = _run(["python3", "-m", "pip", "--version"], root, timeout=10)
    if rc != 0 and "No module named pip" in output:
        current_python3_pip_missing = True

    signals = has_uv_lock or uv_managed_venv
    bootstrap_contract_mismatch = hardcoded_system_pip and (signals or current_python3_pip_missing)
    if not bootstrap_contract_mismatch and not pip_deadlock:
        return

    affected_files = [normalize_path(tool_path, root)]
    evidence: list[str] = []
    if has_uv_lock:
        evidence.append("Repo contains uv.lock, so Python bootstrap should prefer uv-managed sync.")
    if uv_managed_venv:
        evidence.append("Repo-local .venv/pyvenv.cfg records a uv-managed virtual environment.")
    if hardcoded_system_pip:
        evidence.append(f"{normalize_path(tool_path, root)} still hardcodes bare `python3 -m pip` bootstrap commands.")
    if current_python3_pip_missing:
        evidence.append("Current machine reports `python3 -m pip --version` -> No module named pip.")
    if bootstrap_failed:
        evidence.append(f"{normalize_path(workflow_path, root)} records bootstrap.status = failed.")
        affected_files.append(normalize_path(workflow_path, root))
    if pip_deadlock and proof_artifact:
        affected_files.append(normalize_path(proof_artifact, root))
        evidence.extend(
            [
                f"{normalize_path(proof_artifact, root)} shows bootstrap failed while reporting `No module named pip`.",
                *matching_lines(proof_text, (r"python3 -m pip install", r"No module named pip", r"Missing Prerequisites", r"- None")),
            ]
        )

    add_finding(
        findings,
        Finding(
            code="BOOT001",
            severity="error",
            problem="The generated bootstrap contract cannot ready this repo on the current machine, so write-capable workflow stages can deadlock before source fixes start.",
            root_cause="The managed `environment_bootstrap` surface still relies on bare `python3 -m pip` or otherwise ignores repo-local uv/.venv signals. When global pip is absent, bootstrap fails even if the repo has a usable project virtual environment or uv lockfile.",
            files=list(dict.fromkeys(affected_files)),
            safer_pattern="Prefer repo-native bootstrap (`uv sync --locked` for uv repos; otherwise repo-local `.venv` plus `.venv/bin/python -m pip`), record missing prerequisites accurately, and keep bootstrap readiness separate from source import/test failures.",
            evidence=evidence[:8],
        ),
    )


def audit_smoke_test_contract(root: Path, findings: list[Finding]) -> None:
    tool_path = root / ".opencode" / "tools" / "smoke_test.ts"
    if not tool_path.exists():
        return

    text = read_text(tool_path)
    has_repo_python = (root / "uv.lock").exists() or (root / ".venv" / "bin" / "python").exists()
    hardcoded_system_pytest = 'argv: ["python3", "-m", "pytest"]' in text
    if not (has_repo_python and hardcoded_system_pytest):
        return

    evidence = []
    if (root / "uv.lock").exists():
        evidence.append("Repo contains uv.lock, so smoke tests should prefer `uv run python -m pytest`.")
    if (root / ".venv" / "bin" / "python").exists():
        evidence.append("Repo contains .venv/bin/python, so smoke tests can use the repo-local virtualenv directly.")
    evidence.append(f"{normalize_path(tool_path, root)} still hardcodes `python3 -m pytest` for detected Python test surfaces.")

    add_finding(
        findings,
        Finding(
            code="WFLOW001",
            severity="error",
            problem="The managed smoke-test tool ignores repo-managed Python execution and can deadlock closeout on uv or .venv repos.",
            root_cause="The generated smoke-test contract still hardcodes system `python3 -m pytest` instead of selecting repo-native Python execution when `uv.lock` or `.venv` is present.",
            files=[normalize_path(tool_path, root)],
            safer_pattern="Prefer explicit project smoke-test overrides first, then `uv run python -m pytest` for uv-managed repos, then `.venv/bin/python -m pytest` for repo-local virtualenvs before falling back to system python.",
            evidence=evidence,
        ),
    )


def audit_review_stage_ambiguity(root: Path, findings: list[Finding]) -> None:
    workflow_doc = root / "docs" / "process" / "workflow.md"
    ticket_update = root / ".opencode" / "tools" / "ticket_update.ts"
    workflow_tool = root / ".opencode" / "tools" / "_workflow.ts"
    if not workflow_doc.exists() or not ticket_update.exists() or not workflow_tool.exists():
        return

    workflow_text = read_text(workflow_doc)
    ticket_text = read_text(ticket_update)
    workflow_tool_text = read_text(workflow_tool)
    docs_require_plan_review = "plan review" in workflow_text.lower()
    tool_blocks_review_before_impl = "Cannot move to review before an implementation artifact exists." in workflow_tool_text
    status_missing_plan_review = '"plan_review"' not in workflow_tool_text and "`plan_review`" not in workflow_text
    if not (docs_require_plan_review and tool_blocks_review_before_impl and status_missing_plan_review):
        return

    add_finding(
        findings,
        Finding(
            code="WFLOW003",
            severity="error",
            problem="The generated workflow contract overloads `review`, so plan review and implementation review are operationally ambiguous.",
            root_cause="Workflow docs describe a pre-implementation plan review, but the generated tool contract only allows `review` after an implementation artifact exists and does not expose a distinct `plan_review` status.",
            files=[
                normalize_path(workflow_doc, root),
                normalize_path(ticket_update, root),
                normalize_path(workflow_tool, root),
            ],
            safer_pattern="Add an explicit `plan_review` stage/status, require a planning artifact before entering it, keep `approved_plan` in workflow-state, and reserve `review` for post-implementation review only.",
            evidence=[
                f"{normalize_path(workflow_doc, root)} still documents `plan review` before implementation.",
                f"{normalize_path(workflow_tool, root)} still returns `Cannot move to review before an implementation artifact exists.`",
                f"{normalize_path(workflow_tool, root)} still omits `plan_review` from coarse status definitions.",
            ],
        ),
    )


def audit_ticket_transition_contract(root: Path, findings: list[Finding]) -> None:
    ticket_update = root / ".opencode" / "tools" / "ticket_update.ts"
    workflow_tool = root / ".opencode" / "tools" / "_workflow.ts"
    stage_gate = root / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    if not ticket_update.exists() or not workflow_tool.exists() or not stage_gate.exists():
        return

    ticket_text = read_text(ticket_update)
    workflow_text = read_text(workflow_tool)
    stage_gate_text = read_text(stage_gate)
    evidence: list[str] = []

    if 'ticket.status !== "plan_review"' in ticket_text:
        evidence.append(f"{normalize_path(ticket_update, root)} still gates implementation on `ticket.status` instead of lifecycle `ticket.stage`.")
    if 'ticket.status !== "plan_review"' in stage_gate_text:
        evidence.append(f"{normalize_path(stage_gate, root)} still preflights implementation against `ticket.status` instead of lifecycle `ticket.stage`.")
    if "resolveRequestedTicketProgress" not in ticket_text or "validateLifecycleStageStatus" not in ticket_text:
        evidence.append(f"{normalize_path(ticket_update, root)} does not resolve and validate the requested stage/status pair before mutation.")
    if "LIFECYCLE_STAGES" not in workflow_text or "Unsupported ticket stage:" not in workflow_text:
        evidence.append(f"{normalize_path(workflow_tool, root)} does not expose an explicit allowed-stage contract with an unsupported-stage error.")
    if "resolveRequestedTicketProgress" not in stage_gate_text or "validateLifecycleStageStatus" not in stage_gate_text:
        evidence.append(f"{normalize_path(stage_gate, root)} does not validate stage/status requests before tool execution.")

    if not evidence:
        return

    add_finding(
        findings,
        Finding(
            code="WFLOW004",
            severity="error",
            problem="The generated ticket transition contract still keys implementation on the wrong state surface or accepts unvalidated lifecycle requests.",
            root_cause="When implementation gating depends on `status` instead of lifecycle `stage`, or unknown stages are not rejected up front, weaker models start probing the state machine instead of following it.",
            files=[
                normalize_path(ticket_update, root),
                normalize_path(workflow_tool, root),
                normalize_path(stage_gate, root),
            ],
            safer_pattern="Validate every requested stage/status pair through one explicit lifecycle contract, reject unsupported stages, and gate implementation on `ticket.stage == plan_review` plus workflow-state approval.",
            evidence=evidence,
        ),
    )


def audit_reverification_deadlock(root: Path, findings: list[Finding]) -> None:
    stage_gate = root / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    ticket_claim = root / ".opencode" / "tools" / "ticket_claim.ts"
    ticket_lookup = root / ".opencode" / "tools" / "ticket_lookup.ts"
    ticket_reverify = root / ".opencode" / "tools" / "ticket_reverify.ts"
    if not stage_gate.exists() or not ticket_claim.exists() or not ticket_reverify.exists():
        return

    stage_gate_text = read_text(stage_gate)
    ticket_claim_text = read_text(ticket_claim)
    ticket_lookup_text = read_text(ticket_lookup) if ticket_lookup.exists() else ""
    evidence: list[str] = []

    if 'if (input.tool === "ticket_reverify")' in stage_gate_text and "ensureTargetTicketWriteLease(ticketId)" in stage_gate_text:
        evidence.append(f"{normalize_path(stage_gate, root)} still requires a normal write lease before `ticket_reverify` can run.")
    if "cannot be claimed because it is already closed" in ticket_claim_text:
        evidence.append(f"{normalize_path(ticket_claim, root)} still forbids claiming closed tickets.")
    if "Ticket is already closed." in ticket_lookup_text:
        evidence.append(f"{normalize_path(ticket_lookup, root)} still presents closed tickets as terminal even when process verification may still be pending.")

    if len(evidence) < 2:
        return

    add_finding(
        findings,
        Finding(
            code="WFLOW009",
            severity="error",
            problem="The generated backlog reverification path is structurally deadlocked for closed tickets.",
            root_cause="Closed historical tickets need reverification after a process change, but the current contract treats `ticket_reverify` like ordinary lease-bound write work while `ticket_claim` forbids claiming closed tickets. That makes trust restoration impossible without bypassing the workflow.",
            files=[
                normalize_path(stage_gate, root),
                normalize_path(ticket_claim, root),
                normalize_path(ticket_reverify, root),
                *([normalize_path(ticket_lookup, root)] if ticket_lookup.exists() else []),
            ],
            safer_pattern="Let `ticket_reverify` mutate closed done tickets through a narrow reverification guard instead of a normal lane write lease, and expose that path in `ticket_lookup.transition_guidance` so the coordinator sees a legal trust-restoration route.",
            evidence=evidence,
        ),
    )


def audit_smoke_test_artifact_bypass(root: Path, findings: list[Finding]) -> None:
    artifact_write = root / ".opencode" / "tools" / "artifact_write.ts"
    artifact_register = root / ".opencode" / "tools" / "artifact_register.ts"
    stage_gate = root / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    ticket_lookup = root / ".opencode" / "tools" / "ticket_lookup.ts"
    if not artifact_write.exists() or not artifact_register.exists() or not stage_gate.exists() or not ticket_lookup.exists():
        return

    artifact_write_text = read_text(artifact_write)
    artifact_register_text = read_text(artifact_register)
    stage_gate_text = read_text(stage_gate)
    ticket_lookup_text = read_text(ticket_lookup)
    evidence: list[str] = []

    if re.search(r'description:\s*"[^"]*smoke-test[^"]*artifact', artifact_write_text):
        evidence.append(f"{normalize_path(artifact_write, root)} still advertises smoke-test stages as generic artifact_write targets.")
    if re.search(r'description:\s*"[^"]*smoke-test[^"]*artifact', artifact_register_text):
        evidence.append(f"{normalize_path(artifact_register, root)} still advertises smoke-test stages as generic artifact_register targets.")
    if "RESERVED_ARTIFACT_STAGES" not in stage_gate_text:
        evidence.append(f"{normalize_path(stage_gate, root)} does not reserve smoke-test artifacts for their owning tool.")
    if "Generic artifact_write is not allowed for that stage." not in stage_gate_text:
        evidence.append(f"{normalize_path(stage_gate, root)} does not block generic artifact_write for smoke-test stages.")
    if "Generic artifact_register is not allowed for that stage." not in stage_gate_text:
        evidence.append(f"{normalize_path(stage_gate, root)} does not block generic artifact_register for smoke-test stages.")
    if "Do not fabricate a PASS artifact through generic artifact tools." not in ticket_lookup_text:
        evidence.append(f"{normalize_path(ticket_lookup, root)} does not warn that smoke-test PASS proof must come from `smoke_test` rather than generic artifact tools.")

    if not evidence:
        return

    add_finding(
        findings,
        Finding(
            code="WFLOW005",
            severity="error",
            problem="Smoke-test proof can still be fabricated through generic artifact tools instead of the owning deterministic workflow tool.",
            root_cause="If generic artifact surfaces can create smoke-test artifacts, a weaker model can bypass executed validation and publish closeout-ready proof that no deterministic tool produced.",
            files=[
                normalize_path(artifact_write, root),
                normalize_path(artifact_register, root),
                normalize_path(stage_gate, root),
                normalize_path(ticket_lookup, root),
            ],
            safer_pattern="Reserve smoke-test artifacts to `smoke_test`, and make the plugin plus transition guidance reject generic PASS-proof fabrication while keeping optional handoff artifacts consistent with docs-lane ownership.",
            evidence=evidence,
        ),
    )


def audit_handoff_artifact_ownership_conflict(root: Path, findings: list[Finding]) -> None:
    stage_gate = root / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    docs_handoff = next((path for path in (root / ".opencode" / "agents").glob("*docs-handoff*.md")), None)
    if not stage_gate.exists() or not docs_handoff:
        return

    stage_gate_text = read_text(stage_gate)
    docs_handoff_text = read_text(docs_handoff)
    generic_handoff_instructions = (
        "canonical handoff artifact path" in docs_handoff_text
        and "artifact_write" in docs_handoff_text
        and "artifact_register" in docs_handoff_text
    )
    plugin_blocks_handoff = bool(re.search(r'RESERVED_ARTIFACT_STAGES\s*=\s*new Set\(\[[^\]]*"handoff"', stage_gate_text))
    if not (generic_handoff_instructions and plugin_blocks_handoff):
        return

    add_finding(
        findings,
        Finding(
            code="WFLOW007",
            severity="error",
            problem="The generated handoff ownership contract is self-contradictory: docs-handoff is told to write a canonical handoff artifact, but the stage gate blocks that documented path.",
            root_cause="The package reserved `handoff` too broadly at the plugin layer while the generated docs-handoff lane still instructs agents to create optional canonical handoff artifacts through `artifact_write` and `artifact_register`.",
            files=[normalize_path(stage_gate, root), normalize_path(docs_handoff, root)],
            safer_pattern="Keep `handoff_publish` as the owner of `START-HERE.md` and `.opencode/state/latest-handoff.md`, but leave optional canonical `handoff` artifacts writable by the docs-handoff lane unless a dedicated end-to-end handoff artifact tool exists.",
            evidence=[
                f"{normalize_path(docs_handoff, root)} still instructs the docs lane to write and register a canonical handoff artifact.",
                f"{normalize_path(stage_gate, root)} still blocks generic artifact_write or artifact_register for `handoff`.",
            ],
        ),
    )


def audit_team_leader_workflow_contract(root: Path, findings: list[Finding]) -> None:
    team_leader = next((path for path in (root / ".opencode" / "agents").glob("*team-leader*.md")), None)
    if not team_leader:
        return

    text = read_text(team_leader)
    evidence: list[str] = []
    if "ticket_lookup.transition_guidance" not in text:
        evidence.append("Team leader prompt does not treat `ticket_lookup.transition_guidance` as the canonical next-step summary.")
    if "do not probe alternate stage or status values" not in text:
        evidence.append("Team leader prompt does not tell the agent to stop after repeated lifecycle contradictions.")
    if "do not create planning, implementation, review, QA, or smoke-test artifacts yourself" not in text:
        evidence.append("Team leader prompt does not forbid stage-artifact authorship overreach by the coordinator.")
    if "use human slash commands only as entrypoints" not in text:
        evidence.append("Team leader prompt does not mark slash commands as human entrypoints only.")

    if not evidence:
        return

    add_finding(
        findings,
        Finding(
            code="WFLOW006",
            severity="warning",
            problem="The team leader prompt leaves workflow mechanics underspecified enough that weaker models can thrash or search for bypasses.",
            root_cause="Without explicit transition guidance, contradiction-stop behavior, artifact-ownership rules, and command boundaries, the coordinator has to infer the state machine and may start authoring artifacts or testing workaround transitions itself.",
            files=[normalize_path(team_leader, root)],
            safer_pattern="Tell the team leader to route from `ticket_lookup.transition_guidance`, stop after repeated lifecycle errors, leave stage artifacts to the owning specialist, and keep slash commands human-only.",
            evidence=evidence,
        ),
    )


def audit_ticket_execution_skill_contract(root: Path, findings: list[Finding]) -> None:
    skill_path = root / ".opencode" / "skills" / "ticket-execution" / "SKILL.md"
    if not skill_path.exists():
        return

    text = read_text(skill_path)
    evidence: list[str] = []
    if "transition_guidance" not in text:
        evidence.append("ticket-execution does not tell agents to read `ticket_lookup.transition_guidance` before stage changes.")
    if "same lifecycle error twice" not in text and "same lifecycle error" not in text:
        evidence.append("ticket-execution does not define the stop condition for repeated lifecycle-tool contradictions.")
    if "`smoke_test` is the only legal producer of `smoke-test`" not in text:
        evidence.append("ticket-execution does not reserve smoke-test artifacts to `smoke_test`.")
    if "do not convert expected results into PASS evidence" not in text:
        evidence.append("ticket-execution does not forbid expected-results-as-PASS artifact fabrication.")
    if "slash commands are human entrypoints" not in text:
        evidence.append("ticket-execution does not clarify that slash commands are human entrypoints, not autonomous tools.")

    if not evidence:
        return

    add_finding(
        findings,
        Finding(
            code="SKILL002",
            severity="warning",
            problem="The repo-local `ticket-execution` skill is too thin to explain the actual lifecycle contract to weaker models.",
            root_cause="When the local workflow explainer omits transition guidance, contradiction-stop rules, artifact ownership, or command boundaries, agents fall back to guess-and-check against the tools.",
            files=[normalize_path(skill_path, root)],
            safer_pattern="Make `ticket-execution` the canonical lifecycle explainer: require transition guidance, explicit stop conditions, specialist-owned stage artifacts, `smoke_test`-only smoke proof, and blocker returns instead of fabricated PASS evidence.",
            evidence=evidence,
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


def audit_handoff_evidence_gap(root: Path, findings: list[Finding]) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    start_here = root / "START-HERE.md"
    latest_handoff = root / ".opencode" / "state" / "latest-handoff.md"
    manifest = read_json(manifest_path)
    workflow = read_json(workflow_path)
    if not isinstance(manifest, dict) or not isinstance(workflow, dict):
        return

    active_ticket = _active_ticket(manifest, workflow)
    if not isinstance(active_ticket, dict):
        return

    start_here_text = read_text(start_here)
    latest_handoff_text = read_text(latest_handoff)
    combined = combine_outputs(start_here_text, latest_handoff_text)
    if not any(re.search(pattern, combined, re.IGNORECASE) for pattern in HANDOFF_OVERCLAIM_PATTERNS):
        return

    blocked_dependents = _blocked_dependents(manifest, str(active_ticket.get("id", "")))
    active_status = str(active_ticket.get("status", "")).strip()
    if active_status == "done" and not blocked_dependents:
        return

    evidence = []
    if active_status and active_status != "done":
        evidence.append(f"Active ticket {active_ticket.get('id')} is still `{active_status}`, not `done`.")
    if blocked_dependents:
        evidence.append(f"Dependent tickets still waiting on the active ticket: {', '.join(blocked_dependents)}.")
    evidence.extend(matching_lines(combined, HANDOFF_OVERCLAIM_PATTERNS))

    add_finding(
        findings,
        Finding(
            code="WFLOW002",
            severity="error",
            problem="Published handoff text overstates repo readiness or root cause beyond the executed evidence and current dependency state.",
            root_cause="The handoff contract allows free-form next-action text to claim dependency unblocking or single-cause explanations even when the active ticket is not done and downstream tickets remain blocked.",
            files=[
                normalize_path(start_here, root),
                normalize_path(latest_handoff, root),
                normalize_path(manifest_path, root),
                normalize_path(workflow_path, root),
            ],
            safer_pattern="Block handoff publication when custom next-action text claims dependency readiness, `only blocker`, or `not a code defect` without matching executed evidence and current manifest/workflow state.",
            evidence=evidence[:6],
        ),
    )


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
        evidence.extend(
            f"Line {line_number}: {line}" for line_number, line in matching_line_numbers(text, (r"\bworkaround\b", r"\bbypass\b"))[:5]
        )
        if not evidence:
            continue

        add_finding(
            findings,
            Finding(
                code="SESSION003",
                severity="error",
                problem="The supplied session transcript shows the agent searching for workflow bypasses instead of following the lifecycle contract.",
                root_cause="Once the lifecycle gate became confusing, the agent started trying unsupported stages or explicit workarounds rather than resolving the missing proof or contradictory contract.",
                files=[normalize_path(path, root)],
                safer_pattern="Reject unsupported stages up front, tell the coordinator not to probe alternate transitions, and return the contract contradiction as a blocker when the required proof is missing.",
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


def _detect_python(root: Path) -> str | None:
    """Return the Python executable to use for this repo (uv run python > python3 > python)."""
    uv = root / ".venv" / "bin" / "python"
    if uv.exists():
        return str(uv)
    for candidate in ("python3", "python"):
        rc, _ = _run([candidate, "--version"], root, timeout=5)
        if rc == 0:
            return candidate
    return None


def _detect_pytest_command(root: Path) -> list[str] | None:
    """Return the pytest command to use for this repo."""
    venv_python = root / ".venv" / "bin" / "python"
    if venv_python.exists():
        rc, _ = _run([str(venv_python), "-m", "pytest", "--version"], root, timeout=5)
        if rc == 0:
            return [str(venv_python), "-m", "pytest"]
    venv_pytest = root / ".venv" / "bin" / "pytest"
    if venv_pytest.exists():
        return [str(venv_pytest)]
    rc, _ = _run(["pytest", "--version"], root, timeout=5)
    if rc == 0:
        return ["pytest"]
    return None


def audit_environment_prerequisites(root: Path, findings: list[Finding]) -> None:
    has_python_project = (root / "pyproject.toml").exists() or (root / "setup.py").exists()
    tests_dir = root / "tests"
    environment_bootstrap = root / ".opencode" / "tools" / "environment_bootstrap.ts"
    smoke_test = root / ".opencode" / "tools" / "smoke_test.ts"
    bootstrap_text = read_text(environment_bootstrap) + "\n" + read_text(smoke_test)

    if has_python_project and _detect_python(root) is None:
        add_finding(
            findings,
            Finding(
                code="ENV001",
                severity="error",
                problem="The current machine does not expose a usable Python interpreter for this repo's runtime and verification flow.",
                root_cause="The repo is Python-backed, but the host environment cannot run repo-local `.venv` Python or a system `python3`/`python`, so audit and repair cannot execute import or test verification.",
                files=[path for path in (normalize_path(environment_bootstrap, root), normalize_path(smoke_test, root)) if (root / path).exists()],
                safer_pattern="Ensure the host can run repo-local `.venv/bin/python` or a system Python before treating audit or repair verification as complete.",
                evidence=[
                    "No repo-local `.venv/bin/python` was detected.",
                    "Neither `python3 --version` nor `python --version` succeeded on this machine.",
                ],
            ),
        )

    if has_python_project and tests_dir.exists() and _detect_pytest_command(root) is None:
        add_finding(
            findings,
            Finding(
                code="ENV002",
                severity="error",
                problem="The repo has Python tests, but no usable pytest command is available on the current machine.",
                root_cause="The workflow expects test collection or suite execution, but the host cannot run repo-local `python -m pytest`, `.venv/bin/pytest`, or a global `pytest` binary. Audit would otherwise skip runtime verification and misstate repo health.",
                files=[normalize_path(tests_dir, root)],
                safer_pattern="Install or sync the repo-local test environment first, then rerun audit or repair verification with a working pytest command.",
                evidence=[
                    f"{normalize_path(tests_dir, root)} exists and requires executable test verification.",
                    "No repo-local or global pytest command could be resolved for this repo.",
                ],
            ),
        )

    if ((root / "uv.lock").exists() or 'argv: ["uv"' in bootstrap_text) and shutil.which("uv") is None:
        add_finding(
            findings,
            Finding(
                code="ENV001",
                severity="error",
                problem="The current machine is missing `uv`, but this repo's managed workflow depends on it.",
                root_cause="The repo exposes `uv.lock` or a managed bootstrap contract that uses `uv`, so bootstrap and verification cannot reproduce the intended Python environment without that executable.",
                files=[path for path in (normalize_path(environment_bootstrap, root), normalize_path(smoke_test, root)) if (root / path).exists()],
                safer_pattern="Install `uv` on the host or run the audit through an environment that already provides it before trusting bootstrap or test verification results.",
                evidence=[
                    "The repo contains `uv.lock` or generated workflow commands that invoke `uv`.",
                    "`uv --version` could not be resolved on the current machine.",
                ],
            ),
        )

    rg_reference = repo_mentions_patterns(root, (r"\brg\b", r"ripgrep"))
    if rg_reference and shutil.which("rg") is None:
        add_finding(
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
            ),
        )

    git_reference = repo_mentions_patterns(root, (r"git commit", r"recent commits?", r"recent_commits"))
    if (root / ".git").exists() and git_reference:
        name_rc, name_out = _run(["git", "config", "--get", "user.name"], root, timeout=5)
        email_rc, email_out = _run(["git", "config", "--get", "user.email"], root, timeout=5)
        if name_rc != 0 or not name_out.strip() or email_rc != 0 or not email_out.strip():
            add_finding(
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
                ),
            )


def audit_python_execution(root: Path, findings: list[Finding]) -> None:
    """Check that a Python project can actually import its main modules and collect tests.

    This catches runtime errors (NameError, FastAPIError, broken DI patterns, etc.)
    that are invisible to workflow-structure checks.
    Only runs when pyproject.toml or setup.py is present in the repo root.
    """
    if not (root / "pyproject.toml").exists() and not (root / "setup.py").exists():
        return

    python = _detect_python(root)
    if python is None:
        return

    src_candidates: list[Path] = []
    for name in ("src", "app", "lib"):
        candidate = root / name
        if candidate.is_dir():
            src_candidates.append(candidate)

    # --- Import check for each top-level package under src/ ---
    import_errors: list[str] = []
    for src_dir in src_candidates:
        for pkg in sorted(src_dir.iterdir()):
            if not pkg.is_dir() or not (pkg / "__init__.py").exists():
                continue
            module = f"{src_dir.name}.{pkg.name}"
            rc, output = _run(
                [python, "-c", f"import {module}"],
                root,
                timeout=20,
            )
            if rc != 0:
                # Trim to first error line to keep evidence compact
                first_error = next(
                    (ln for ln in output.splitlines() if "Error" in ln or "error" in ln),
                    output.splitlines()[-1] if output.splitlines() else output,
                )
                import_errors.append(f"{module}: {first_error}")

    if import_errors:
        add_finding(
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
            ),
        )

    # --- pytest --collect-only to catch test collection errors ---
    pytest_command = _detect_pytest_command(root)
    if pytest_command is None:
        return

    tests_dir = root / "tests"
    if not tests_dir.exists():
        return

    rc, output = _run(
        [*pytest_command, str(tests_dir), "--collect-only", "-q", "--tb=no"],
        root,
        timeout=60,
    )

    # pytest exits 2 on collection error, 4 if no tests found, 0/1 for pass/fail
    collection_errors = [
        ln for ln in output.splitlines()
        if "ERROR" in ln or "error" in ln.lower() and "collect" in ln.lower()
    ]
    if rc == 2 or collection_errors:
        add_finding(
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
            ),
        )

    # --- Check for failing tests after successful collection ---
    if rc in {0, 1} and not collection_errors:
        # Run with short output to count failures
        rc2, output2 = _run(
            [*pytest_command, str(tests_dir), "-q", "--tb=no", "--no-header"],
            root,
            timeout=120,
        )
        if rc2 != 0:
            summary_lines = [ln for ln in output2.splitlines() if "failed" in ln or "passed" in ln or "error" in ln]
            failed_count_match = re.search(r"(\d+) failed", output2)
            failed_count = int(failed_count_match.group(1)) if failed_count_match else "unknown"
            add_finding(
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
                ),
            )


def audit_repo(root: Path, logs: list[Path] | None = None) -> list[Finding]:
    findings: list[Finding] = []
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
    audit_active_process_verification(root, findings)
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
    audit_bootstrap_deadlock(root, findings)
    audit_smoke_test_contract(root, findings)
    audit_review_stage_ambiguity(root, findings)
    audit_ticket_transition_contract(root, findings)
    audit_reverification_deadlock(root, findings)
    audit_smoke_test_artifact_bypass(root, findings)
    audit_handoff_artifact_ownership_conflict(root, findings)
    audit_team_leader_workflow_contract(root, findings)
    audit_ticket_execution_skill_contract(root, findings)
    audit_environment_prerequisites(root, findings)
    audit_python_execution(root, findings)
    audit_handoff_evidence_gap(root, findings)
    audit_session_chronology(root, findings, logs or [])
    audit_session_transition_thrash(root, findings, logs or [])
    audit_session_workaround_search(root, findings, logs or [])
    audit_session_evidence_free_verification(root, findings, logs or [])
    audit_session_coordinator_artifact_authorship(root, findings, logs or [])
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
        return "Treat missing repo-local test executables such as pytest as explicit verification blockers so audit never reports clean health after skipping runtime checks."
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
    if finding.code == "BOOT001":
        return "Make generated Python bootstrap manager-aware (`uv` or repo-local `.venv`), classify missing prerequisites accurately, and audit bootstrap deadlocks before routing source remediation."
    if finding.code == "SKILL001":
        return "Detect and repair leftover placeholder local skills so generated stack guidance is concrete before implementation continues."
    if finding.code == "SKILL002":
        return "Make the generated `ticket-execution` skill the canonical lifecycle explainer so weaker models do not have to reverse-engineer the state machine from tool errors."
    if finding.code == "MODEL001":
        return "Detect deprecated or missing model-profile surfaces, treat stale package-managed defaults as safe repair instead of preserved intent, regenerate the repo-local model operating profile, and align model metadata plus agent defaults before development resumes."
    if finding.code == "CYCLE001":
        return "Teach audit to inspect the previous diagnosis and repair history, then force repair to explain why the prior cycle failed before another managed-repair run proceeds."
    if finding.code.startswith("EXEC"):
        return "Tighten generated review and QA guidance so runtime validation and test collection proof exist before closure."
    if "ticket" in finding.code or "status" in finding.code:
        return "Keep queue state coarse, route remediation through guarded ticket flows, and validate ticket-contract wording in package checks."
    if any(token in " ".join(finding.files) for token in (".opencode/agents/", ".opencode/skills/")):
        return "Harden generated prompts so read-only roles stay read-only and repo-local review guidance remains advisory."
    return "Refresh managed workflow docs, tools, and validators together so repair replaces drift instead of layering new semantics over old ones."


def build_ticket_recommendations(findings: list[Finding]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    for index, finding in enumerate(sorted(findings, key=lambda item: (severity_rank(item.severity), item.code)), start=1):
        if finding.code.startswith("EXEC"):
            route = "ticket-pack-builder"
            repair_class = "generated-repo remediation ticket"
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
    repeated_cycle = next((finding for finding in findings if finding.code == "CYCLE001"), None)
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
        if any(finding.code in {"SKILL002", "SESSION002", "SESSION003", "SESSION004", "SESSION005", "WFLOW007"} for finding in findings):
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
                "- The following findings are current-machine blockers. Repair may refresh workflow surfaces, but these prerequisites still need operator action or a correctly provisioned host before verification can be trusted.",
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


def emit_diagnosis_pack(root: Path, findings: list[Finding], destination: Path, logs: list[Path]) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    destination.mkdir(parents=True, exist_ok=True)
    recommendations = build_ticket_recommendations(findings)
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
        "report_files": {key: value for key, value in DIAGNOSIS_REPORTS.items()},
        "ticket_recommendations": recommendations,
    }
    if logs:
        manifest["supporting_logs"] = [normalize_path(path, root) for path in logs]
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
        diagnosis_pack = emit_diagnosis_pack(root, findings, diagnosis_dir, logs)
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
