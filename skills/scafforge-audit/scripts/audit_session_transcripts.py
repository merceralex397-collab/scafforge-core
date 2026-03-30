from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Callable

from shared_verifier_types import Finding


@dataclass(frozen=True)
class SessionTranscriptAuditContext:
    read_text: Callable[[Path], str]
    read_json: Callable[[Path], Any]
    normalize_path: Callable[[Path, Path], str]
    add_finding: Callable[[list[Finding], Finding], None]
    matching_lines: Callable[[str, tuple[str, ...]], list[str]]
    matching_line_numbers: Callable[[str, tuple[str, ...]], list[tuple[int, str]]]
    matching_assistant_reasoning_line_numbers: Callable[[str, tuple[str, ...]], list[tuple[int, str]]]
    matching_non_tool_line_numbers: Callable[[str, tuple[str, ...]], list[tuple[int, str]]]
    parse_transcript_tool_events: Callable[[str], list[Any]]
    parse_json_object: Callable[[str], dict[str, Any] | None]
    normalize_shell_command: Callable[[str], str]
    extract_transcript_smoke_acceptance_commands: Callable[[str], list[str]]
    is_coordinator_assistant: Callable[[str], bool]
    transcript_stale_state_patterns: tuple[str, ...]
    transcript_progress_patterns: tuple[str, ...]
    transcript_full_suite_result_patterns: tuple[str, ...]
    transcript_lifecycle_error_patterns: tuple[str, ...]
    transcript_soft_bypass_patterns: tuple[str, ...]
    transcript_verification_failure_patterns: tuple[str, ...]
    transcript_pass_claim_patterns: tuple[str, ...]
    transcript_execution_recovery_patterns: tuple[str, ...]
    transcript_broken_tool_patterns: tuple[str, ...]
    transcript_smoke_override_failure_patterns: tuple[str, ...]
    transcript_smoke_acceptance_patterns: tuple[str, ...]
    transcript_handoff_lease_contradiction_patterns: tuple[str, ...]
    transcript_acceptance_scope_tension_patterns: tuple[str, ...]
    handoff_overclaim_patterns: tuple[str, ...]
    coordinator_artifact_stages: tuple[str, ...]


def audit_session_chronology(root: Path, findings: list[Finding], logs: list[Path], ctx: SessionTranscriptAuditContext) -> None:
    for path in logs:
        text = ctx.read_text(path)
        if not text:
            continue
        stale_state = any(re.search(pattern, text, re.IGNORECASE) for pattern in ctx.transcript_stale_state_patterns)
        later_progress = any(re.search(pattern, text, re.IGNORECASE) for pattern in ctx.transcript_progress_patterns)
        overclaim = any(re.search(pattern, text, re.IGNORECASE) for pattern in ctx.handoff_overclaim_patterns)
        full_suite_result = any(re.search(pattern, text, re.IGNORECASE) for pattern in ctx.transcript_full_suite_result_patterns)
        if not (stale_state and later_progress and overclaim and not full_suite_result):
            continue
        evidence: list[str] = []
        evidence.extend(ctx.matching_lines(text, ctx.transcript_stale_state_patterns))
        evidence.extend(ctx.matching_lines(text, ctx.transcript_progress_patterns))
        evidence.extend(ctx.matching_lines(text, ctx.handoff_overclaim_patterns))
        evidence.append("No later full-suite execution result was found in the supplied session log.")
        ctx.add_finding(
            findings,
            Finding(
                code="SESSION001",
                severity="error",
                problem="The supplied session transcript shows a later reasoning failure that current-state-only diagnosis would miss.",
                root_cause="The session began from stale resume state, later gathered new implementation or QA evidence, then still published an over-broad blocker summary without a later full-suite execution result.",
                files=[ctx.normalize_path(path, root)],
                safer_pattern="When session logs are supplied, audit chronology first: separate stale resume state from later evidence, then explain any final summary that outruns the executed commands before reconciling current repo state.",
                evidence=evidence[:8],
                provenance="script",
            ),
        )


def audit_session_transition_thrash(root: Path, findings: list[Finding], logs: list[Path], ctx: SessionTranscriptAuditContext) -> None:
    for path in logs:
        text = ctx.read_text(path)
        if not text:
            continue
        hits = ctx.matching_line_numbers(text, ctx.transcript_lifecycle_error_patterns)
        if not hits:
            continue
        counts: dict[str, int] = {}
        for _, line in hits:
            counts[line] = counts.get(line, 0) + 1
        repeated = [(line, count) for line, count in counts.items() if count >= 2]
        if not repeated:
            continue
        evidence = [f"Repeated lifecycle blocker {count}x -> {line}" for line, count in repeated[:3]]
        ctx.add_finding(
            findings,
            Finding(
                code="SESSION002",
                severity="error",
                problem="The supplied session transcript shows repeated retries of the same rejected lifecycle transition.",
                root_cause="Instead of treating the repeated `ticket_update` rejection as a contract contradiction, the agent kept probing the state machine and burned time without acquiring new evidence.",
                files=[ctx.normalize_path(path, root)],
                safer_pattern="After the same lifecycle blocker repeats, re-run `ticket_lookup`, read `transition_guidance`, load `ticket-execution` if needed, and stop with a blocker instead of retrying the same transition.",
                evidence=evidence,
                provenance="script",
            ),
        )


def audit_session_workaround_search(root: Path, findings: list[Finding], logs: list[Path], ctx: SessionTranscriptAuditContext) -> None:
    for path in logs:
        text = ctx.read_text(path)
        if not text:
            continue
        events = ctx.parse_transcript_tool_events(text)
        evidence: list[str] = []
        for event in events:
            if event.tool != "ticket_update" or not isinstance(event.args, dict):
                continue
            stage = str(event.args.get("stage", "")).strip()
            if stage and stage not in {"planning", "plan_review", "implementation", "review", "qa", "smoke-test", "closeout"}:
                evidence.append(f"Line {event.line_number}: unsupported ticket_update stage `{stage}` from {event.assistant or 'unknown assistant'}.")
        reasoning_hits = ctx.matching_assistant_reasoning_line_numbers(text, (r"\bworkaround\b", r"\bbypass\b", *ctx.transcript_soft_bypass_patterns))
        if not reasoning_hits:
            reasoning_hits = ctx.matching_non_tool_line_numbers(text, (r"\bworkaround\b", r"\bbypass\b", *ctx.transcript_soft_bypass_patterns))
        evidence.extend(f"Line {line_number}: {line}" for line_number, line in reasoning_hits[:5])
        if not evidence:
            continue
        ctx.add_finding(
            findings,
            Finding(
                code="SESSION003",
                severity="error",
                problem="The supplied session transcript shows the agent searching for workflow bypasses or soft dependency overrides instead of following the lifecycle contract.",
                root_cause="Once the lifecycle gate became confusing, the agent started trying unsupported stages, explicit workarounds, or softer 'close it anyway' / dependency-override reasoning instead of resolving the missing proof or contradictory contract.",
                files=[ctx.normalize_path(path, root)],
                safer_pattern="Reject unsupported stages and dependency overrides up front, tell the coordinator not to probe alternate transitions or close blocked tickets anyway, and return the contract contradiction as a blocker when the required proof is missing.",
                evidence=evidence,
                provenance="script",
            ),
        )


def audit_session_broken_tooling(root: Path, findings: list[Finding], logs: list[Path], ctx: SessionTranscriptAuditContext) -> None:
    for path in logs:
        text = ctx.read_text(path)
        if not text:
            continue
        evidence: list[str] = []
        for event in ctx.parse_transcript_tool_events(text):
            if not event.error:
                continue
            if not any(re.search(pattern, event.error, re.IGNORECASE) for pattern in ctx.transcript_broken_tool_patterns):
                continue
            tool_class = "internal workflow helper" if event.tool.startswith("_workflow_") else "tool"
            error_summary = event.error.splitlines()[0].strip()
            evidence.append(f"Line {event.line_number}: {tool_class} `{event.tool}` failed with `{error_summary}`.")
        evidence.extend(f"Line {line_number}: {line}" for line_number, line in ctx.matching_line_numbers(text, (r"Available tools:.*_workflow_",))[:3])
        if not evidence:
            continue
        ctx.add_finding(
            findings,
            Finding(
                code="WFLOW015",
                severity="error",
                problem="The supplied session transcript shows the runtime exposing or invoking broken workflow helper tools instead of only executable tool modules.",
                root_cause="The tool surface leaked `_workflow_*` helpers or other non-executable exports into the model-visible tool list. When the coordinator called them, the runtime failed before any workflow logic could run.",
                files=[ctx.normalize_path(path, root), ".opencode/lib/workflow.ts"],
                safer_pattern="Keep workflow helpers private under `.opencode/lib/workflow.ts`, expose only real `tool({...})` modules to the model, and make audit treat transcript-level missing-`execute` failures as managed workflow-contract defects.",
                evidence=evidence[:6],
                provenance="script",
            ),
        )


def audit_session_smoke_test_override_failure(root: Path, findings: list[Finding], logs: list[Path], ctx: SessionTranscriptAuditContext) -> None:
    smoke_test = root / ".opencode" / "tools" / "smoke_test.ts"
    for path in logs:
        text = ctx.read_text(path)
        if not text:
            continue
        evidence: list[str] = []
        saw_override = False
        for event in ctx.parse_transcript_tool_events(text):
            if event.tool != "smoke_test" or not isinstance(event.args, dict):
                continue
            override = event.args.get("command_override")
            if isinstance(override, list) and override:
                saw_override = True
                if event.output and '"failure_classification": "environment"' in event.output:
                    evidence.append(f"Line {event.line_number}: smoke_test with command_override returned `failure_classification: environment` before the requested override command ran.")
        if not saw_override:
            continue
        evidence.extend(f"Line {line_number}: {line}" for line_number, line in ctx.matching_line_numbers(text, ctx.transcript_smoke_override_failure_patterns)[:4])
        if not evidence:
            continue
        ctx.add_finding(
            findings,
            Finding(
                code="WFLOW016",
                severity="error",
                problem="The supplied session transcript shows the managed smoke-test override path failing before the requested smoke command starts.",
                root_cause="The generated `smoke_test` tool treated a shell-style environment assignment like `UV_CACHE_DIR=...` as the executable name for `spawn()`. That turns a valid explicit override command into an `ENOENT` tool failure and misclassifies the result as a runtime environment problem.",
                files=[ctx.normalize_path(path, root), ctx.normalize_path(smoke_test, root)],
                safer_pattern="Parse shell-style smoke-test overrides before execution, strip leading `KEY=VALUE` env assignments into the spawn environment, and report malformed overrides as configuration errors rather than environment failures.",
                evidence=evidence[:6],
                provenance="script",
            ),
        )


def audit_session_smoke_test_acceptance_drift(root: Path, findings: list[Finding], logs: list[Path], ctx: SessionTranscriptAuditContext) -> None:
    smoke_test = root / ".opencode" / "tools" / "smoke_test.ts"
    for path in logs:
        text = ctx.read_text(path)
        if not text:
            continue
        acceptance_commands = ctx.extract_transcript_smoke_acceptance_commands(text)
        if not acceptance_commands:
            continue
        evidence: list[str] = []
        for event in ctx.parse_transcript_tool_events(text):
            if event.tool != "smoke_test" or not isinstance(event.args, dict):
                continue
            if isinstance(event.args.get("command_override"), list) and event.args.get("command_override"):
                continue
            payload = ctx.parse_json_object(event.output or "")
            if not payload:
                continue
            raw_commands = payload.get("commands")
            if not isinstance(raw_commands, list):
                continue
            executed_commands = [
                ctx.normalize_shell_command(str(item.get("command", "")).strip())
                for item in raw_commands
                if isinstance(item, dict) and str(item.get("command", "")).strip()
            ]
            smoke_commands = [command for command in executed_commands if re.search(r"\b(pytest|cargo test|go test|ruff check|npm run test|pnpm run test|yarn test|bun run test)\b", command, re.IGNORECASE)]
            if not smoke_commands:
                continue
            if any(command.lower() == acceptance.lower() for command in smoke_commands for acceptance in acceptance_commands):
                continue
            evidence.append(f"Line {event.line_number}: smoke_test ran `{smoke_commands[0]}` even though transcript acceptance criteria already specified `{acceptance_commands[0]}`.")
            if isinstance(event.args.get("test_paths"), list) and event.args.get("test_paths"):
                evidence.append(f"Line {event.line_number}: smoke_test relied on caller-supplied test_paths instead of the ticket's explicit smoke acceptance command.")
        evidence.extend(f"Line {line_number}: {line}" for line_number, line in ctx.matching_line_numbers(text, ctx.transcript_smoke_acceptance_patterns)[:3])
        if not any(item.startswith("Line ") and "smoke_test ran `" in item for item in evidence):
            continue
        ctx.add_finding(
            findings,
            Finding(
                code="WFLOW017",
                severity="error",
                problem="The supplied session transcript shows the smoke-test stage running a heuristic command that does not match the ticket's explicit acceptance command.",
                root_cause="The generated `smoke_test` tool fell back to repo-level pytest detection or caller-supplied `test_paths` instead of binding itself to the ticket's canonical smoke acceptance command. That can widen smoke scope to unrelated failures or narrow it away from the actual closeout requirement.",
                files=[ctx.normalize_path(path, root), ctx.normalize_path(smoke_test, root)],
                safer_pattern="Treat acceptance-backed smoke commands as canonical, let `smoke_test` infer them automatically, and reject heuristic scope changes unless the caller provides an intentional exact command override.",
                evidence=evidence[:6],
                provenance="script",
            ),
        )


def audit_session_handoff_closeout_lease_deadlock(root: Path, findings: list[Finding], logs: list[Path], ctx: SessionTranscriptAuditContext) -> None:
    handoff_publish = root / ".opencode" / "tools" / "handoff_publish.ts"
    for path in logs:
        text = ctx.read_text(path)
        if not text:
            continue
        evidence: list[str] = []
        for event in ctx.parse_transcript_tool_events(text):
            if event.tool != "handoff_publish":
                continue
            if not event.error or "missing_ticket_write_lease" not in event.error:
                continue
            evidence.append(f"Line {event.line_number}: handoff_publish failed with `{event.error.splitlines()[0].strip()}` after closeout.")
        evidence.extend(f"Line {line_number}: {line}" for line_number, line in ctx.matching_line_numbers(text, ctx.transcript_handoff_lease_contradiction_patterns)[:4])
        if not evidence:
            continue
        ctx.add_finding(
            findings,
            Finding(
                code="WFLOW022",
                severity="error",
                problem="The supplied session transcript shows restart-surface publication blocked by a closed-ticket write-lease requirement.",
                root_cause="`handoff_publish` still behaved like an ordinary lane mutation and required an active write lease after the ticket had already been closed. That leaves the workflow with no legal way to publish truthful restart surfaces during closeout.",
                files=[ctx.normalize_path(path, root), ctx.normalize_path(handoff_publish, root)],
                safer_pattern="Let `handoff_publish` update derived restart surfaces after closeout without reacquiring a normal write lease on the closed ticket, and audit transcript evidence for this contradiction explicitly.",
                evidence=evidence[:6],
                provenance="script",
            ),
        )


def audit_session_acceptance_scope_contamination(root: Path, findings: list[Finding], logs: list[Path], ctx: SessionTranscriptAuditContext) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    manifest = ctx.read_json(manifest_path)
    tickets = manifest.get("tickets") if isinstance(manifest, dict) and isinstance(manifest.get("tickets"), list) else []
    tickets_by_id = {str(ticket.get("id")): ticket for ticket in tickets if isinstance(ticket, dict) and isinstance(ticket.get("id"), str)}
    for path in logs:
        text = ctx.read_text(path)
        if not text:
            continue
        acceptance_hits = ctx.matching_line_numbers(text, (r"acceptance criterion.*exits 0", r"acceptance criteria.*exits 0"))
        scope_hits = ctx.matching_line_numbers(text, ctx.transcript_acceptance_scope_tension_patterns)
        if not acceptance_hits or not scope_hits:
            continue
        mentioned_ids = {match for _, line in [*acceptance_hits[:2], *scope_hits[:4]] for match in re.findall(r"\b[A-Z]+-\d+\b", line)}
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
        evidence = [f"Line {line_number}: {line}" for line_number, line in [*acceptance_hits[:2], *scope_hits[:4]]]
        ctx.add_finding(
            findings,
            Finding(
                code="WFLOW023",
                severity="error",
                problem="The supplied session transcript shows a ticket whose literal acceptance command reaches into later-ticket scope, so the ticket cannot close without violating its own scope boundary.",
                root_cause="Ticket decomposition allowed a closeout command that still depended on work owned by a later ticket. That forced the coordinator to choose between falsifying acceptance, broadening scope, or blocking on work that the ticket explicitly said it did not own.",
                files=[ctx.normalize_path(path, root), ctx.normalize_path(manifest_path, root)],
                safer_pattern="Keep ticket acceptance scope-isolated. If the literal closeout command depends on later-ticket work, split the tickets differently or encode the dependency in the ticket structure instead of shipping a contradictory acceptance command.",
                evidence=evidence,
                provenance="script",
            ),
        )


def audit_session_evidence_free_verification(root: Path, findings: list[Finding], logs: list[Path], ctx: SessionTranscriptAuditContext) -> None:
    for path in logs:
        text = ctx.read_text(path)
        if not text:
            continue
        failure_hits = ctx.matching_line_numbers(text, ctx.transcript_verification_failure_patterns)
        pass_hits = ctx.matching_line_numbers(text, ctx.transcript_pass_claim_patterns)
        if not failure_hits or not pass_hits:
            continue
        first_failure_line = failure_hits[0][0]
        recovery_hits = ctx.matching_line_numbers(text, ctx.transcript_execution_recovery_patterns)
        later_pass_hits: list[tuple[int, str]] = []
        for line_number, line in pass_hits:
            if line_number <= first_failure_line:
                continue
            recovered = any(first_failure_line < recovery_line < line_number for recovery_line, _ in recovery_hits)
            if not recovered:
                later_pass_hits.append((line_number, line))
        if not later_pass_hits:
            continue
        evidence = [f"Verification failure at line {failure_hits[0][0]} -> {failure_hits[0][1]}", *[f"Later PASS claim at line {line_number} -> {line}" for line_number, line in later_pass_hits[:4]]]
        ctx.add_finding(
            findings,
            Finding(
                code="SESSION004",
                severity="error",
                problem="The supplied session transcript shows PASS-style implementation, QA, or smoke-test claims after validation had already failed or could not run.",
                root_cause="The coordinator substituted visual inspection or expected results for executable proof, then let artifacts claim PASS even though the earlier transcript said verification commands were unavailable.",
                files=[ctx.normalize_path(path, root)],
                safer_pattern="If validation cannot run, return a blocker; require raw command output in implementation and QA artifacts, and reserve smoke-test PASS proof to the deterministic `smoke_test` tool.",
                evidence=evidence,
                provenance="script",
            ),
        )


def audit_session_coordinator_artifact_authorship(root: Path, findings: list[Finding], logs: list[Path], ctx: SessionTranscriptAuditContext) -> None:
    for path in logs:
        text = ctx.read_text(path)
        if not text:
            continue
        evidence: list[str] = []
        for event in ctx.parse_transcript_tool_events(text):
            if event.tool != "artifact_write" or not isinstance(event.args, dict):
                continue
            if not ctx.is_coordinator_assistant(event.assistant):
                continue
            stage = str(event.args.get("stage", "")).strip()
            if stage not in ctx.coordinator_artifact_stages:
                continue
            artifact_path = str(event.args.get("path", "")).strip()
            evidence.append(f"Line {event.line_number}: coordinator {event.assistant} wrote `{stage}` artifact" + (f" at `{artifact_path}`." if artifact_path else "."))
        if not evidence:
            continue
        ctx.add_finding(
            findings,
            Finding(
                code="SESSION005",
                severity="error",
                problem="The supplied session transcript shows the coordinator writing specialist stage artifacts directly instead of routing those outputs through the owning lane or deterministic tool.",
                root_cause="Once the workflow became confusing, the team leader started manufacturing implementation, review, QA, or smoke-test evidence itself instead of delegating the stage body to the assigned specialist or deterministic tool.",
                files=[ctx.normalize_path(path, root)],
                safer_pattern="Keep the coordinator on routing and stage transitions only: specialist lanes own planning, implementation, review, and QA artifacts, while `smoke_test` alone owns smoke-test proof.",
                evidence=evidence[:6],
                provenance="script",
            ),
        )


def audit_session_operator_trap(root: Path, findings: list[Finding], logs: list[Path], ctx: SessionTranscriptAuditContext) -> None:
    for path in logs:
        text = ctx.read_text(path)
        if not text:
            continue
        categories: list[tuple[str, str]] = []
        repeated = ctx.matching_line_numbers(text, ctx.transcript_lifecycle_error_patterns)
        if repeated:
            categories.append(("workflow thrash", f"Line {repeated[0][0]}: {repeated[0][1]}"))
        reasoning_hits = ctx.matching_assistant_reasoning_line_numbers(text, (r"\bworkaround\b", r"\bbypass\b", *ctx.transcript_soft_bypass_patterns))
        if not reasoning_hits:
            reasoning_hits = ctx.matching_non_tool_line_numbers(text, (r"\bworkaround\b", r"\bbypass\b", *ctx.transcript_soft_bypass_patterns))
        if reasoning_hits:
            categories.append(("bypass search", f"Line {reasoning_hits[0][0]}: {reasoning_hits[0][1]}"))
        handoff_hits = ctx.matching_line_numbers(text, ctx.transcript_handoff_lease_contradiction_patterns)
        if handoff_hits:
            categories.append(("closeout lease contradiction", f"Line {handoff_hits[0][0]}: {handoff_hits[0][1]}"))
        acceptance_hits = ctx.matching_line_numbers(text, ctx.transcript_acceptance_scope_tension_patterns)
        if acceptance_hits:
            categories.append(("acceptance scope tension", f"Line {acceptance_hits[0][0]}: {acceptance_hits[0][1]}"))
        override_hits = ctx.matching_line_numbers(text, ctx.transcript_smoke_override_failure_patterns)
        if override_hits:
            categories.append(("tool execution contradiction", f"Line {override_hits[0][0]}: {override_hits[0][1]}"))
        if len(categories) < 2:
            continue
        evidence = [f"{label}: {detail}" for label, detail in categories[:5]]
        ctx.add_finding(
            findings,
            Finding(
                code="SESSION006",
                severity="error",
                problem="The supplied session transcript shows the operator trapped between contradictory workflow rules instead of having one clear legal next move.",
                root_cause="Multiple workflow surfaces failed at once: lifecycle gates, closeout publication, acceptance scope, or deterministic tool execution disagreed about what could legally happen next. The coordinator then had to infer workarounds instead of following one competent contract path.",
                files=[ctx.normalize_path(path, root)],
                safer_pattern="Design every workflow state so it exposes one legal next action, one named owner, and one blocker return path. When transcript evidence shows a trap, audit adjacent surfaces together instead of treating each symptom as isolated noise.",
                evidence=evidence,
                provenance="script",
            ),
        )


def run_session_transcript_audits(root: Path, findings: list[Finding], logs: list[Path], ctx: SessionTranscriptAuditContext) -> None:
    audit_session_chronology(root, findings, logs, ctx)
    audit_session_transition_thrash(root, findings, logs, ctx)
    audit_session_workaround_search(root, findings, logs, ctx)
    audit_session_broken_tooling(root, findings, logs, ctx)
    audit_session_smoke_test_override_failure(root, findings, logs, ctx)
    audit_session_smoke_test_acceptance_drift(root, findings, logs, ctx)
    audit_session_handoff_closeout_lease_deadlock(root, findings, logs, ctx)
    audit_session_acceptance_scope_contamination(root, findings, logs, ctx)
    audit_session_evidence_free_verification(root, findings, logs, ctx)
    audit_session_coordinator_artifact_authorship(root, findings, logs, ctx)
    audit_session_operator_trap(root, findings, logs, ctx)
