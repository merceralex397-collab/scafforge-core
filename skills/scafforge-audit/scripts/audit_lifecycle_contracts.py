from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Callable

from shared_verifier_types import Finding

_PRODUCT_SPINE_LANES: frozenset[str] = frozenset({
    "cli-surface",
    "tool-gateway",
    "agent-runtime",
    "context-engine",
    "protocol-transport",
    "llm-infrastructure",
    "mcp-integration",
    "ide-integration",
    "tui-surface",
    "core-runtime",
    "release-readiness",
})
_PRODUCT_SPINE_TICKET_ID_PREFIXES: tuple[str, ...] = (
    "CLI-",
    "TOOLS-",
    "AGENT-",
    "CTX-",
    "LLM-",
    "PROTO-",
    "IDE-",
    "MCP-",
    "TUI-",
    "CORE-",
    "REL-",
)
_DEFERRED_BEHAVIOR_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"without yet filling.+final product behavior", re.IGNORECASE),
    re.compile(r"keep .+ bodies shallow", re.IGNORECASE),
    re.compile(r"justified stubs?", re.IGNORECASE),
    re.compile(r"defer(?:red)? to (?:later|subsequent) tickets?", re.IGNORECASE),
    re.compile(r"stub(?:s|bed)? .*later", re.IGNORECASE),
)


@dataclass(frozen=True)
class LifecycleContractAuditContext:
    read_text: Callable[[Path], str]
    read_json: Callable[[Path], Any]
    normalize_path: Callable[[Path, Path], str]
    add_finding: Callable[[list[Finding], Finding], None]
    tickets_needing_process_verification: Callable[
        [dict[str, Any], dict[str, Any]], list[dict[str, Any]]
    ]
    parse_start_here_state: Callable[[str], dict[str, Any]]
    normalize_restart_surface_value: Callable[[Any], Any]


def audit_review_stage_ambiguity(
    root: Path, findings: list[Finding], ctx: LifecycleContractAuditContext
) -> None:
    workflow_doc = root / "docs" / "process" / "workflow.md"
    ticket_update = root / ".opencode" / "tools" / "ticket_update.ts"
    workflow_tool = root / ".opencode" / "lib" / "workflow.ts"
    if (
        not workflow_doc.exists()
        or not ticket_update.exists()
        or not workflow_tool.exists()
    ):
        return

    workflow_text = ctx.read_text(workflow_doc)
    workflow_tool_text = ctx.read_text(workflow_tool)
    docs_require_plan_review = "plan review" in workflow_text.lower()
    tool_blocks_review_before_impl = (
        "Cannot move to review before an implementation artifact exists."
        in workflow_tool_text
    )
    status_missing_plan_review = (
        '"plan_review"' not in workflow_tool_text
        and "`plan_review`" not in workflow_text
    )
    if not (
        docs_require_plan_review
        and tool_blocks_review_before_impl
        and status_missing_plan_review
    ):
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW003",
            severity="error",
            problem="The generated workflow contract overloads `review`, so plan review and implementation review are operationally ambiguous.",
            root_cause="Workflow docs describe a pre-implementation plan review, but the generated tool contract only allows `review` after an implementation artifact exists and does not expose a distinct `plan_review` status.",
            files=[
                ctx.normalize_path(workflow_doc, root),
                ctx.normalize_path(ticket_update, root),
                ctx.normalize_path(workflow_tool, root),
            ],
            safer_pattern="Add an explicit `plan_review` stage/status, require a planning artifact before entering it, keep `approved_plan` in workflow-state, and reserve `review` for post-implementation review only.",
            evidence=[
                f"{ctx.normalize_path(workflow_doc, root)} still documents `plan review` before implementation.",
                f"{ctx.normalize_path(workflow_tool, root)} still returns `Cannot move to review before an implementation artifact exists.`",
                f"{ctx.normalize_path(workflow_tool, root)} still omits `plan_review` from coarse status definitions.",
            ],
            provenance="script",
        ),
    )


def audit_ticket_transition_contract(
    root: Path, findings: list[Finding], ctx: LifecycleContractAuditContext
) -> None:
    ticket_update = root / ".opencode" / "tools" / "ticket_update.ts"
    workflow_tool = root / ".opencode" / "lib" / "workflow.ts"
    stage_gate = root / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    if (
        not ticket_update.exists()
        or not workflow_tool.exists()
        or not stage_gate.exists()
    ):
        return

    ticket_text = ctx.read_text(ticket_update)
    workflow_text = ctx.read_text(workflow_tool)
    stage_gate_text = ctx.read_text(stage_gate)
    evidence: list[str] = []

    if 'ticket.status !== "plan_review"' in ticket_text:
        evidence.append(
            f"{ctx.normalize_path(ticket_update, root)} still gates implementation on `ticket.status` instead of lifecycle `ticket.stage`."
        )
    if 'ticket.status !== "plan_review"' in stage_gate_text:
        evidence.append(
            f"{ctx.normalize_path(stage_gate, root)} still preflights implementation against `ticket.status` instead of lifecycle `ticket.stage`."
        )
    if (
        "resolveRequestedTicketProgress" not in ticket_text
        or "validateLifecycleStageStatus" not in ticket_text
    ):
        evidence.append(
            f"{ctx.normalize_path(ticket_update, root)} does not resolve and validate the requested stage/status pair before mutation."
        )
    if (
        "LIFECYCLE_STAGES" not in workflow_text
        or "Unsupported ticket stage:" not in workflow_text
    ):
        evidence.append(
            f"{ctx.normalize_path(workflow_tool, root)} does not expose an explicit allowed-stage contract with an unsupported-stage error."
        )
    if (
        "resolveRequestedTicketProgress" not in stage_gate_text
        or "validateLifecycleStageStatus" not in stage_gate_text
    ):
        evidence.append(
            f"{ctx.normalize_path(stage_gate, root)} does not validate stage/status requests before tool execution."
        )

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW004",
            severity="error",
            problem="The generated ticket transition contract still keys implementation on the wrong state surface or accepts unvalidated lifecycle requests.",
            root_cause="When implementation gating depends on `status` instead of lifecycle `stage`, or unknown stages are not rejected up front, weaker models start probing the state machine instead of following it.",
            files=[
                ctx.normalize_path(ticket_update, root),
                ctx.normalize_path(workflow_tool, root),
                ctx.normalize_path(stage_gate, root),
            ],
            safer_pattern="Validate every requested stage/status pair through one explicit lifecycle contract, reject unsupported stages, and gate implementation on `ticket.stage == plan_review` plus workflow-state approval.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_verdict_aware_transition_contract(
    root: Path, findings: list[Finding], ctx: LifecycleContractAuditContext
) -> None:
    ticket_lookup = root / ".opencode" / "tools" / "ticket_lookup.ts"
    ticket_update = root / ".opencode" / "tools" / "ticket_update.ts"
    workflow_tool = root / ".opencode" / "lib" / "workflow.ts"
    if not ticket_lookup.exists() or not ticket_update.exists() or not workflow_tool.exists():
        return

    lookup_text = ctx.read_text(ticket_lookup)
    update_text = ctx.read_text(ticket_update)
    workflow_text = ctx.read_text(workflow_tool)
    evidence: list[str] = []

    if "extractArtifactVerdict" not in workflow_text:
        evidence.append(
            f"{ctx.normalize_path(workflow_tool, root)} does not expose a shared artifact verdict extractor."
        )
    if "Review found blockers. Route back to implementation" not in lookup_text:
        evidence.append(
            f"{ctx.normalize_path(ticket_lookup, root)} does not make review FAIL verdicts route back to implementation."
        )
    if "QA found issues. Route back to implementation to fix the QA findings." not in lookup_text:
        evidence.append(
            f"{ctx.normalize_path(ticket_lookup, root)} does not make QA FAIL verdicts route back to implementation."
        )
    if "Cannot advance past review — latest artifact shows FAIL verdict." not in update_text:
        evidence.append(
            f"{ctx.normalize_path(ticket_update, root)} does not block review to QA transitions on FAIL verdicts."
        )
    if "Cannot advance past qa — latest artifact shows FAIL verdict." not in update_text:
        evidence.append(
            f"{ctx.normalize_path(ticket_update, root)} does not block QA to smoke-test transitions on FAIL verdicts."
        )

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW023",
            severity="error",
            problem="The generated lifecycle contract is not verdict-aware, so FAIL review or QA artifacts can still look advanceable.",
            root_cause="Transition guidance and transition enforcement must inspect artifact verdicts, not just artifact existence. Otherwise weaker models continue on the happy path after blocker findings.",
            files=[
                ctx.normalize_path(ticket_lookup, root),
                ctx.normalize_path(ticket_update, root),
                ctx.normalize_path(workflow_tool, root),
            ],
            safer_pattern="Extract verdicts from the latest review and QA artifacts, route FAIL or BLOCKED outcomes back to implementation, and reject lifecycle transitions when the latest artifact verdict is blocking or unclear.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_deferred_product_behavior_contract(
    root: Path, findings: list[Finding], ctx: LifecycleContractAuditContext
) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    if not manifest_path.exists():
        return

    manifest = ctx.read_json(manifest_path)
    tickets = (
        manifest.get("tickets")
        if isinstance(manifest, dict) and isinstance(manifest.get("tickets"), list)
        else []
    )
    if not tickets:
        return

    evidence: list[str] = []
    files: list[str] = [ctx.normalize_path(manifest_path, root)]

    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        ticket_id = str(ticket.get("id", "")).strip().upper()
        lane = str(ticket.get("lane", "")).strip().lower()
        if lane not in _PRODUCT_SPINE_LANES and not ticket_id.startswith(_PRODUCT_SPINE_TICKET_ID_PREFIXES):
            continue

        ticket_file = root / "tickets" / f"{ticket_id}.md"
        ticket_text = ctx.read_text(ticket_file)
        if not ticket_text:
            continue

        matched_line: str | None = None
        for line in ticket_text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if any(pattern.search(stripped) for pattern in _DEFERRED_BEHAVIOR_PATTERNS):
                matched_line = stripped
                break
        if matched_line is None:
            continue

        files.append(ctx.normalize_path(ticket_file, root))
        evidence.append(
            f"{ctx.normalize_path(ticket_file, root)} normalizes deferred or stubbed runtime behavior: {matched_line}"
        )

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW032",
            severity="error",
            problem="Primary product-spine tickets explicitly permit shallow, stubbed, or deferred runtime behavior.",
            root_cause="The backlog contract is allowing user-facing or core runtime tickets to close on shell shape alone while real backend, tool, or execution behavior is deferred to unspecified later work. That makes the repo look implemented without a truthful product path.",
            files=list(dict.fromkeys(files)),
            safer_pattern="For user-facing or core runtime lanes, name the narrower scaffold-only ticket honestly or require real runnable behavior. Do not allow ticket summaries, acceptance, or notes to normalize shallow command bodies, justified stubs, or deferred product behavior on the product spine.",
            evidence=evidence[:8],
            provenance="script",
        ),
    )


def audit_markdown_verdict_parser_mismatch(
    root: Path, findings: list[Finding], ctx: LifecycleContractAuditContext
) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    workflow_tool = root / ".opencode" / "lib" / "workflow.ts"
    if not manifest_path.exists() or not workflow_tool.exists():
        return

    manifest = ctx.read_json(manifest_path)
    tickets = manifest.get("tickets") if isinstance(manifest, dict) and isinstance(manifest.get("tickets"), list) else []
    if not tickets:
        return

    workflow_text = ctx.read_text(workflow_tool)
    normalized_workflow_text = workflow_text.replace("\\\\", "\\")
    supports_broad_labeled_verdicts = (
        "ARTIFACT_VERDICT_LABEL_PATTERN" in workflow_text
        and "const labeled = plain.match(" in workflow_text
        and "const headingInline = plain.match(" in workflow_text
        and "overall(?:\\s+qa)?(?:\\s+(?:result|verdict))?" in normalized_workflow_text
        and "qa\\s+(?:result|verdict)" in normalized_workflow_text
        and "review\\s+(?:result|verdict)" in normalized_workflow_text
    )
    supports_compact_stage_headings = (
        "const compactStageHeading = plain.match(" in workflow_text
        and "(?:(?:qa|review))\\s+(pass|fail|reject|approved?|blocked?|blocker)\\b"
        in normalized_workflow_text
    )
    if supports_broad_labeled_verdicts and supports_compact_stage_headings:
        return

    emphasized_verdict = re.compile(
        r"^(?:[-*]\s*)?(?:\*\*|__)(overall(?:\s+qa)?(?:\s+(?:result|verdict))?|qa\s+(?:result|verdict)|review\s+(?:result|verdict)|verdict|result|approval\s+signal)(?:\*\*|__)\s*:\s*(?:\*\*|__)?\s*(pass|fail|reject|approved?|blocked?|blocker)(?:\*\*|__)?\b",
        re.IGNORECASE | re.MULTILINE,
    )
    overall_verdict = re.compile(
        r"^(?:[-*]\s*)?(?:\*\*|__)?overall(?:\*\*|__)?\s*:\s*(?:\*\*|__)?\s*(pass|fail|reject|approved?|blocked?|blocker)\b",
        re.IGNORECASE | re.MULTILINE,
    )
    compact_stage_heading = re.compile(
        r"^#{1,4}\s*(?:QA|Review)\s+(?:PASS|FAIL|REJECT|APPROVED?|BLOCKED?|BLOCKER)\b",
        re.IGNORECASE | re.MULTILINE,
    )
    evidence: list[str] = []
    files = [ctx.normalize_path(workflow_tool, root), ctx.normalize_path(manifest_path, root)]

    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        for artifact in ticket.get("artifacts", []):
            if not isinstance(artifact, dict):
                continue
            if str(artifact.get("trust_state", "current")).strip() != "current":
                continue
            stage = str(artifact.get("stage", "")).strip()
            if stage not in {"review", "qa", "smoke-test"}:
                continue
            artifact_path = root / str(artifact.get("path", "")).strip()
            artifact_text = ctx.read_text(artifact_path)
            artifact_matches: list[str] = []
            if not supports_broad_labeled_verdicts:
                for pattern in (emphasized_verdict, overall_verdict):
                    match = pattern.search(artifact_text)
                    if match:
                        artifact_matches.append(match.group(0).strip())
                        break
            if not supports_compact_stage_headings:
                compact_match = compact_stage_heading.search(artifact_text)
                if compact_match:
                    artifact_matches.append(compact_match.group(0).strip())
            if not artifact_matches:
                continue
            files.append(ctx.normalize_path(artifact_path, root))
            for matched in artifact_matches:
                evidence.append(
                    f"{ctx.normalize_path(artifact_path, root)} contains `{matched}`, but {ctx.normalize_path(workflow_tool, root)} still lacks parser coverage for that explicit verdict form."
                )

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW026",
            severity="error",
            problem="Current artifacts contain explicit verdict headings or labels, but the generated verdict extractor still reports them as unclear.",
            root_cause="The repo-local workflow parser does not cover the real artifact verdict forms already present in downstream review and QA artifacts, including markdown-emphasized labels, compact stage headings such as `## QA PASS`, and plain `**Overall**: PASS` labels. Those explicit verdicts then look unparseable and block review or QA transitions even though the artifact body is clear.",
            files=list(dict.fromkeys(files)),
            safer_pattern="Keep one shared artifact verdict extractor that accepts the real artifact family in use: plain and markdown-emphasized verdict labels, compact `QA/Review + verdict` headings, and `Overall: PASS/FAIL` labels. Route ticket_lookup and ticket_update through that shared parser instead of treating explicit review or QA verdicts as unclear.",
            evidence=evidence[:8],
            provenance="script",
        ),
    )


def audit_reverification_deadlock(
    root: Path, findings: list[Finding], ctx: LifecycleContractAuditContext
) -> None:
    stage_gate = root / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    ticket_claim = root / ".opencode" / "tools" / "ticket_claim.ts"
    ticket_lookup = root / ".opencode" / "tools" / "ticket_lookup.ts"
    ticket_reverify = root / ".opencode" / "tools" / "ticket_reverify.ts"
    if (
        not stage_gate.exists()
        or not ticket_claim.exists()
        or not ticket_reverify.exists()
    ):
        return

    stage_gate_text = ctx.read_text(stage_gate)
    ticket_claim_text = ctx.read_text(ticket_claim)
    ticket_lookup_text = ctx.read_text(ticket_lookup) if ticket_lookup.exists() else ""
    evidence: list[str] = []

    ticket_reverify_block = ""
    reverify_match = re.search(
        r'if \(input\.tool === "ticket_reverify"\) \{([\s\S]*?)\n\s{6}\}',
        stage_gate_text,
    )
    if reverify_match:
        ticket_reverify_block = reverify_match.group(1)

    if "ensureTargetTicketWriteLease(ticketId)" in ticket_reverify_block:
        evidence.append(
            f"{ctx.normalize_path(stage_gate, root)} still requires a normal write lease before `ticket_reverify` can run."
        )
    if "cannot be claimed because it is already closed" in ticket_claim_text:
        evidence.append(
            f"{ctx.normalize_path(ticket_claim, root)} still forbids claiming closed tickets."
        )
    if (
        "Ticket is already closed." in ticket_lookup_text
        and "historical trust still needs restoration" not in ticket_lookup_text
        and 'next_action_tool: "ticket_reverify"' not in ticket_lookup_text
    ):
        evidence.append(
            f"{ctx.normalize_path(ticket_lookup, root)} still presents closed tickets as terminal even when process verification may still be pending."
        )

    if len(evidence) < 2:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW009",
            severity="error",
            problem="The generated backlog reverification path is structurally deadlocked for closed tickets.",
            root_cause="Closed historical tickets need reverification after a process change, but the current contract treats `ticket_reverify` like ordinary lease-bound write work while `ticket_claim` forbids claiming closed tickets. That makes trust restoration impossible without bypassing the workflow.",
            files=[
                ctx.normalize_path(stage_gate, root),
                ctx.normalize_path(ticket_claim, root),
                ctx.normalize_path(ticket_reverify, root),
                *(
                    [ctx.normalize_path(ticket_lookup, root)]
                    if ticket_lookup.exists()
                    else []
                ),
            ],
            safer_pattern="Let `ticket_reverify` mutate closed done tickets through a narrow reverification guard instead of a normal lane write lease, and expose that path in `ticket_lookup.transition_guidance` so the coordinator sees a legal trust-restoration route.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_smoke_test_artifact_bypass(
    root: Path, findings: list[Finding], ctx: LifecycleContractAuditContext
) -> None:
    artifact_write = root / ".opencode" / "tools" / "artifact_write.ts"
    artifact_register = root / ".opencode" / "tools" / "artifact_register.ts"
    stage_gate = root / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    ticket_lookup = root / ".opencode" / "tools" / "ticket_lookup.ts"
    if (
        not artifact_write.exists()
        or not artifact_register.exists()
        or not stage_gate.exists()
        or not ticket_lookup.exists()
    ):
        return

    artifact_write_text = ctx.read_text(artifact_write)
    artifact_register_text = ctx.read_text(artifact_register)
    stage_gate_text = ctx.read_text(stage_gate)
    ticket_lookup_text = ctx.read_text(ticket_lookup)
    evidence: list[str] = []

    if re.search(r'description:\s*"[^"]*smoke-test[^"]*artifact', artifact_write_text):
        evidence.append(
            f"{ctx.normalize_path(artifact_write, root)} still advertises smoke-test stages as generic artifact_write targets."
        )
    if re.search(
        r'description:\s*"[^"]*smoke-test[^"]*artifact', artifact_register_text
    ):
        evidence.append(
            f"{ctx.normalize_path(artifact_register, root)} still advertises smoke-test stages as generic artifact_register targets."
        )
    if "RESERVED_ARTIFACT_STAGES" not in stage_gate_text:
        evidence.append(
            f"{ctx.normalize_path(stage_gate, root)} does not reserve smoke-test artifacts for their owning tool."
        )
    if "Generic artifact_write is not allowed for that stage." not in stage_gate_text:
        evidence.append(
            f"{ctx.normalize_path(stage_gate, root)} does not block generic artifact_write for smoke-test stages."
        )
    if (
        "Generic artifact_register is not allowed for that stage."
        not in stage_gate_text
    ):
        evidence.append(
            f"{ctx.normalize_path(stage_gate, root)} does not block generic artifact_register for smoke-test stages."
        )
    if (
        "Do not fabricate a PASS artifact through generic artifact tools."
        not in ticket_lookup_text
    ):
        evidence.append(
            f"{ctx.normalize_path(ticket_lookup, root)} does not warn that smoke-test PASS proof must come from `smoke_test` rather than generic artifact tools."
        )

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW005",
            severity="error",
            problem="Smoke-test proof can still be fabricated through generic artifact tools instead of the owning deterministic workflow tool.",
            root_cause="If generic artifact surfaces can create smoke-test artifacts, a weaker model can bypass executed validation and publish closeout-ready proof that no deterministic tool produced.",
            files=[
                ctx.normalize_path(artifact_write, root),
                ctx.normalize_path(artifact_register, root),
                ctx.normalize_path(stage_gate, root),
                ctx.normalize_path(ticket_lookup, root),
            ],
            safer_pattern="Reserve smoke-test artifacts to `smoke_test`, and make the plugin plus transition guidance reject generic PASS-proof fabrication while keeping optional handoff artifacts consistent with docs-lane ownership.",
            evidence=evidence,
            provenance="script",
        ),
    )


def _latest_current_stage_artifact(ticket: dict[str, Any], stage: str) -> dict[str, Any] | None:
    artifacts = ticket.get("artifacts") if isinstance(ticket.get("artifacts"), list) else []
    current = [
        artifact
        for artifact in artifacts
        if isinstance(artifact, dict)
        and str(artifact.get("trust_state", "current")).strip() == "current"
        and str(artifact.get("stage", "")).strip() == stage
    ]
    if not current:
        return None
    current.sort(key=lambda artifact: str(artifact.get("created_at", "")))
    return current[-1]


def _current_stage_artifacts(ticket: dict[str, Any], stage: str) -> list[dict[str, Any]]:
    artifacts = ticket.get("artifacts") if isinstance(ticket.get("artifacts"), list) else []
    current = [
        artifact
        for artifact in artifacts
        if isinstance(artifact, dict)
        and str(artifact.get("trust_state", "current")).strip() == "current"
        and str(artifact.get("stage", "")).strip() == stage
    ]
    current.sort(key=lambda artifact: str(artifact.get("created_at", "")))
    return current


def _current_artifact_file_path(artifact: dict[str, Any]) -> str:
    source_path = str(artifact.get("source_path", "")).strip()
    if source_path:
        return source_path
    return str(artifact.get("path", "")).strip()


def _is_remediation_ticket(ticket: dict[str, Any]) -> bool:
    ticket_id = str(ticket.get("id", "")).strip().upper()
    lane = str(ticket.get("lane", "")).strip().lower()
    return lane == "remediation" or ticket_id.startswith("REMED-")


def _referenced_evidence_paths(text: str) -> list[str]:
    matches = re.findall(
        r"(?:^|\n)\s*(?:[-*]\s*)?(?:evidence_artifact_path|artifact_path)\s*:\s*([^\n]+)",
        text,
        flags=re.IGNORECASE,
    )
    paths: list[str] = []
    for match in matches:
        candidate = match.strip().strip("`")
        if candidate:
            paths.append(candidate)
    return paths


def audit_remediation_review_evidence(
    root: Path, findings: list[Finding], ctx: LifecycleContractAuditContext
) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    if not manifest_path.exists():
        return

    manifest = ctx.read_json(manifest_path)
    tickets = manifest.get("tickets") if isinstance(manifest, dict) and isinstance(manifest.get("tickets"), list) else []
    if not tickets:
        return

    command_pattern = re.compile(
        r"(?:(?:^|\n)(?:-\s*)?(?:(?:\*\*|__)?(?:exact\s+command\s+run|command|command run)(?:\*\*|__)?\s*:|(?:\*\*|__)?(?:exact\s+command\s+run|command|command run)\s*:(?:\*\*|__)?|#{1,6}\s*(?:exact\s+command\s+run|command|command run)\s*:?)\s*)(?:`(?P<inline>[^`]+)`|```(?:[^\n]*)\n(?P<body>[\s\S]*?)```|~~~~(?:[^\n]*)\n(?P<body_alt>[\s\S]*?)~~~~)",
        re.IGNORECASE,
    )
    output_pattern = re.compile(
        r"(?:(?:^|\n)(?:-\s*)?(?:(?:\*\*|__)?(?:raw(?:\s+command)?\s+output|raw\s+output|command\s+output|raw\s+stdout|raw\s+stderr|stdout|stderr)(?:\s*\([^)]*\))?(?:\*\*|__)?\s*:|(?:\*\*|__)?(?:raw(?:\s+command)?\s+output|raw\s+output|command\s+output|raw\s+stdout|raw\s+stderr|stdout|stderr)(?:\s*\([^)]*\))?\s*:(?:\*\*|__)?|#{1,6}\s*(?:raw(?:\s+command)?\s+output|raw\s+output|command\s+output|raw\s+stdout|raw\s+stderr|stdout|stderr)(?:\s*\([^)]*\))?\s*:?)\s*)(?:`(?P<inline>[^`]+)`|```(?:[^\n]*)\n(?P<body>[\s\S]*?)```|~~~~(?:[^\n]*)\n(?P<body_alt>[\s\S]*?)~~~~)",
        re.IGNORECASE,
    )
    result_pattern = re.compile(
        r"(?:(?:^|\n)(?:-\s*)?(?:(?:\*\*|__)?(?:overall\s+result|overall\s+verdict|verdict|result|post-fix\s+result|pass/fail\s+result)(?:\*\*|__)?\s*:|(?:\*\*|__)?(?:overall\s+result|overall\s+verdict|verdict|result|post-fix\s+result|pass/fail\s+result):(?:\*\*|__)?)\s*(?:\*\*|__|`|[✅❌✔✖]\s*)*(?:PASS|PASSES|FAIL|FAILED|BLOCKED|ERROR|APPROVED|REJECT)(?:\*\*|__|`)?|(?:^|\n)#{1,6}\s*(?:overall\s+result|overall\s+verdict|review\s+verdict|verdict|result|post-fix\s+result|pass/fail\s+result|blocker\s+or\s+approval\s+signal)\s*(?:\r?\n\s*)+(?:\*\*|__|`|[✅❌✔✖]\s*)*(?:PASS|PASSES|FAIL|FAILED|BLOCKED|ERROR|APPROVED|REJECT)(?:\*\*|__|`)?)",
        re.IGNORECASE,
    )

    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        finding_source = str(ticket.get("finding_source", "")).strip()
        if not finding_source or not _is_remediation_ticket(ticket):
            continue
        review_artifacts = _current_stage_artifacts(ticket, "review")
        if not review_artifacts:
            continue
        candidate_artifacts: list[tuple[Path, str]] = []
        seen_paths: set[Path] = set()

        def append_candidate(relative_path: str) -> None:
            normalized = relative_path.strip()
            if not normalized:
                return
            artifact_path = root / normalized
            if artifact_path in seen_paths:
                return
            artifact_text = ctx.read_text(artifact_path)
            if not artifact_text:
                return
            seen_paths.add(artifact_path)
            candidate_artifacts.append((artifact_path, artifact_text))

        for artifact in review_artifacts:
            artifact_path_value = _current_artifact_file_path(artifact)
            if artifact_path_value:
                append_candidate(artifact_path_value)
        for artifact in _current_stage_artifacts(ticket, "qa"):
            artifact_path_value = _current_artifact_file_path(artifact)
            if artifact_path_value:
                append_candidate(artifact_path_value)
        for artifact in _current_stage_artifacts(ticket, "smoke-test"):
            artifact_path_value = _current_artifact_file_path(artifact)
            if artifact_path_value:
                append_candidate(artifact_path_value)
        for _, artifact_text in list(candidate_artifacts):
            for referenced_path in _referenced_evidence_paths(artifact_text):
                append_candidate(referenced_path)

        if not candidate_artifacts:
            continue
        def has_labeled_evidence(text: str, pattern: re.Pattern[str]) -> bool:
            for match in pattern.finditer(text):
                inline = (match.groupdict().get("inline") or "").strip()
                body = (match.groupdict().get("body") or match.groupdict().get("body_alt") or "").strip()
                if inline or body:
                    return True
            return False

        def artifact_has_complete_evidence(text: str) -> bool:
            return (
                has_labeled_evidence(text, command_pattern)
                and has_labeled_evidence(text, output_pattern)
                and bool(result_pattern.search(text))
            )

        if any(artifact_has_complete_evidence(text) for _, text in candidate_artifacts):
            continue

        artifact_path, artifact_text = candidate_artifacts[0]
        missing: list[str] = []
        if not has_labeled_evidence(artifact_text, command_pattern):
            missing.append("missing exact command record")
        if not has_labeled_evidence(artifact_text, output_pattern):
            missing.append("missing raw command output evidence")
        if not result_pattern.search(artifact_text):
            missing.append("missing explicit post-fix PASS/FAIL result")

        ctx.add_finding(
            findings,
            Finding(
                code="EXEC-REMED-001",
                severity="error",
                problem="Remediation review artifact does not contain runnable command evidence.",
                root_cause="A ticket created from a validated finding is being reviewed on prose alone, so the audit cannot confirm that the original failing command or canonical acceptance command was actually rerun after the fix.",
                files=[ctx.normalize_path(manifest_path, root), ctx.normalize_path(artifact_path, root)],
                safer_pattern="For remediation tickets with `finding_source`, require the review artifact to record the exact command run, include raw command output, and state the explicit PASS/FAIL result before the review counts as trustworthy closure.",
                evidence=[
                    f"ticket {ticket.get('id', '(unknown)')} carries finding_source `{finding_source}`",
                    f"review artifact: {ctx.normalize_path(artifact_path, root)}",
                    *missing,
                ],
                provenance="script",
            ),
        )


def audit_handoff_artifact_ownership_conflict(
    root: Path, findings: list[Finding], ctx: LifecycleContractAuditContext
) -> None:
    stage_gate = root / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    docs_handoff = next(
        (path for path in (root / ".opencode" / "agents").glob("*docs-handoff*.md")),
        None,
    )
    if not stage_gate.exists() or not docs_handoff:
        return

    stage_gate_text = ctx.read_text(stage_gate)
    docs_handoff_text = ctx.read_text(docs_handoff)
    generic_handoff_instructions = (
        "canonical handoff artifact path" in docs_handoff_text
        and "artifact_write" in docs_handoff_text
        and "artifact_register" in docs_handoff_text
    )
    plugin_blocks_handoff = bool(
        re.search(
            r'RESERVED_ARTIFACT_STAGES\s*=\s*new Set\(\[[^\]]*"handoff"',
            stage_gate_text,
        )
    )
    if not (generic_handoff_instructions and plugin_blocks_handoff):
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW007",
            severity="error",
            problem="The generated handoff ownership contract is self-contradictory: docs-handoff is told to write a canonical handoff artifact, but the stage gate blocks that documented path.",
            root_cause="The package reserved `handoff` too broadly at the plugin layer while the generated docs-handoff lane still instructs agents to create optional canonical handoff artifacts through `artifact_write` and `artifact_register`.",
            files=[
                ctx.normalize_path(stage_gate, root),
                ctx.normalize_path(docs_handoff, root),
            ],
            safer_pattern="Keep `handoff_publish` as the owner of `START-HERE.md` and `.opencode/state/latest-handoff.md`, but leave optional canonical `handoff` artifacts writable by the docs-handoff lane unless a dedicated end-to-end handoff artifact tool exists.",
            evidence=[
                f"{ctx.normalize_path(docs_handoff, root)} still instructs the docs lane to write and register a canonical handoff artifact.",
                f"{ctx.normalize_path(stage_gate, root)} still blocks generic artifact_write or artifact_register for `handoff`.",
            ],
            provenance="script",
        ),
    )


def audit_active_process_verification(
    root: Path, findings: list[Finding], ctx: LifecycleContractAuditContext
) -> None:
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    manifest_path = root / "tickets" / "manifest.json"
    start_here_path = root / "START-HERE.md"
    latest_handoff_path = root / ".opencode" / "state" / "latest-handoff.md"
    ticket_lookup_path = root / ".opencode" / "tools" / "ticket_lookup.ts"
    ticket_update_path = root / ".opencode" / "tools" / "ticket_update.ts"
    stage_gate_path = root / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    workflow = ctx.read_json(workflow_path)
    manifest = ctx.read_json(manifest_path)
    if not isinstance(workflow, dict) or not isinstance(manifest, dict):
        return
    if workflow.get("pending_process_verification") is not True:
        return

    affected = ctx.tickets_needing_process_verification(manifest, workflow)

    evidence: list[str] = []
    files = [
        ctx.normalize_path(workflow_path, root),
        ctx.normalize_path(manifest_path, root),
    ]
    clean_claim_pattern = re.compile(
        r"\bclean state\b|\brepo is clean\b|\ball (?:tickets )?complete(?: and verified)?\b|\bfully verified\b|\bno follow-up required\b",
        re.IGNORECASE,
    )

    for surface_path in (start_here_path, latest_handoff_path):
        label = ctx.normalize_path(surface_path, root)
        files.append(label)
        if not surface_path.exists():
            evidence.append(
                f"Missing derived restart surface while process verification is pending: {label}."
            )
            continue
        surface_text = ctx.read_text(surface_path)
        surface = ctx.parse_start_here_state(surface_text)
        if (
            ctx.normalize_restart_surface_value(
                surface.get("pending_process_verification")
            )
            != "true"
        ):
            evidence.append(
                f"{label} does not show pending_process_verification = true while canonical workflow state does."
            )
        if (
            ctx.normalize_restart_surface_value(surface.get("handoff_status"))
            == "ready for continued development"
        ):
            evidence.append(
                f"{label} still claims ready-for-development handoff while process verification remains pending."
            )
        if clean_claim_pattern.search(surface_text):
            evidence.append(
                f"{label} includes clean-state prose even though pending_process_verification remains true."
            )

    if ticket_lookup_path.exists():
        files.append(ctx.normalize_path(ticket_lookup_path, root))
        lookup_text = ctx.read_text(ticket_lookup_path)
        if (
            "ticket_reverify" not in lookup_text
            or "process_verification" not in lookup_text
        ):
            evidence.append(
                f"{ctx.normalize_path(ticket_lookup_path, root)} does not expose the backlog-verifier or ticket_reverify path for pending process verification."
            )
        if not affected and "clearable_now" not in lookup_text:
            evidence.append(
                f"{ctx.normalize_path(ticket_lookup_path, root)} does not expose whether pending_process_verification is immediately clearable when the affected done-ticket set is empty."
            )
    else:
        files.append(ctx.normalize_path(ticket_lookup_path, root))
        evidence.append(
            f"Missing ticket lookup tool while process verification remains pending: {ctx.normalize_path(ticket_lookup_path, root)}."
        )

    if not affected:
        files.append(ctx.normalize_path(ticket_update_path, root))
        if not ticket_update_path.exists():
            evidence.append(
                f"Missing ticket_update tool while pending_process_verification still needs a clear path: {ctx.normalize_path(ticket_update_path, root)}."
            )
        files.append(ctx.normalize_path(stage_gate_path, root))
        if stage_gate_path.exists():
            stage_gate_text = ctx.read_text(stage_gate_path)
            if (
                "isWorkflowProcessVerificationClearOnly" not in stage_gate_text
                or "processVerification.clearable_now" not in stage_gate_text
            ):
                evidence.append(
                    f"{ctx.normalize_path(stage_gate_path, root)} still appears to require a normal ticket write lease even when pending_process_verification is clearable now."
                )
        else:
            evidence.append(
                f"Missing stage-gate enforcer while pending_process_verification still needs a legal clear path: {ctx.normalize_path(stage_gate_path, root)}."
            )

    if not evidence:
        return

    change_time = str(workflow.get("process_last_changed_at", "")).strip() or "unknown"
    affected_ids = [
        str(ticket.get("id", "")).strip()
        for ticket in affected
        if str(ticket.get("id", "")).strip()
    ]
    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW008",
            severity="warning",
            problem="Post-repair process verification is still pending, but the restart surfaces or legal next move contradict the canonical workflow state.",
            root_cause="The workflow contract changed, but the repo is still hiding, overstating, or deadlocking the pending backlog-verification state. That lets restart surfaces imply readiness before historical trust is restored, or leaves the workflow flag stranded after the affected done-ticket set is already empty.",
            files=list(dict.fromkeys(files)),
            safer_pattern="Keep `pending_process_verification` visible, route the backlog verifier across the affected done-ticket set, expose `ticket_reverify` as the legal trust-restoration path, and when that affected set is empty leave a direct legal clear path for `pending_process_verification = false` instead of implying the repo is already clean or leaving the flag stranded.",
            evidence=[
                *evidence[:6],
                f"{ctx.normalize_path(workflow_path, root)} records pending_process_verification = true.",
                f"Current process window started at: {change_time}",
                (
                    f"Affected done tickets: {', '.join(affected_ids[:12])}"
                    + (" ..." if len(affected_ids) > 12 else "")
                    if affected_ids
                    else "Affected done tickets: none; the workflow flag should now be directly clearable."
                ),
            ],
            provenance="script",
        ),
    )


def audit_active_ticket_drift(
    root: Path, findings: list[Finding], ctx: LifecycleContractAuditContext
) -> None:
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    manifest_path = root / "tickets" / "manifest.json"
    stage_gate_path = root / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    if not workflow_path.exists() or not manifest_path.exists():
        return

    workflow = ctx.read_json(workflow_path)
    manifest = ctx.read_json(manifest_path)
    if not isinstance(workflow, dict) or not isinstance(manifest, dict):
        return

    manifest_active = str(manifest.get("active_ticket", "")).strip()
    workflow_active = str(workflow.get("active_ticket", "")).strip()
    if not manifest_active or not workflow_active:
        return

    evidence: list[str] = []
    files = [
        ctx.normalize_path(workflow_path, root),
        ctx.normalize_path(manifest_path, root),
    ]

    if manifest_active != workflow_active:
        evidence.append(
            f"manifest.active_ticket = {manifest_active} but workflow.active_ticket = {workflow_active}."
        )
        evidence.append(
            f"Write-capable tools that check workflow.active_ticket will enforce leases against the wrong ticket."
        )

    if stage_gate_path.exists():
        files.append(ctx.normalize_path(stage_gate_path, root))
        stage_gate_text = ctx.read_text(stage_gate_path)
        if "async function ensureWriteLease(pathValue?: string)" in stage_gate_text:
            evidence.append(
                f"{ctx.normalize_path(stage_gate_path, root)} ensureWriteLease lacks an optional ticketId parameter and always checks workflow.active_ticket."
            )
        elif (
            "async function ensureWriteLease(pathValue?: string, ticketId?: string)"
            not in stage_gate_text
        ):
            evidence.append(
                f"{ctx.normalize_path(stage_gate_path, root)} ensureWriteLease does not accept a target-ticket override for artifact tools."
            )

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW010",
            severity="error" if manifest_active != workflow_active else "warning",
            problem="Active ticket drift between manifest and workflow state can cause write-lease enforcement against the wrong ticket.",
            root_cause="When manifest.active_ticket and workflow.active_ticket diverge after a ticket closeout and activation, tools that check workflow.active_ticket (such as ensureWriteLease in stage-gate-enforcer) will validate leases against the stale ticket. This blocks artifact writes for the newly active ticket even though a valid lease exists.",
            files=list(dict.fromkeys(files)),
            safer_pattern="Keep manifest.active_ticket and workflow.active_ticket synchronized through ticket_update activate calls. EnsureWriteLease should accept an optional target-ticket parameter so artifact tools can validate against the correct ticket instead of the workflow-level active ticket.",
            evidence=evidence,
            provenance="script",
        ),
    )


def run_lifecycle_contract_audits(
    root: Path, findings: list[Finding], ctx: LifecycleContractAuditContext
) -> None:
    audit_active_ticket_drift(root, findings, ctx)
    audit_active_process_verification(root, findings, ctx)
    audit_review_stage_ambiguity(root, findings, ctx)
    audit_ticket_transition_contract(root, findings, ctx)
    audit_verdict_aware_transition_contract(root, findings, ctx)
    audit_deferred_product_behavior_contract(root, findings, ctx)
    audit_markdown_verdict_parser_mismatch(root, findings, ctx)
    audit_reverification_deadlock(root, findings, ctx)
    audit_smoke_test_artifact_bypass(root, findings, ctx)
    audit_remediation_review_evidence(root, findings, ctx)
    audit_handoff_artifact_ownership_conflict(root, findings, ctx)
    audit_managed_blocked_deadlock(root, findings, ctx)


# WFLOW codes that represent legitimate host-only follow-on stages.
# When managed_blocked requires only these stages and none of them are
# completable by the local agent, the repo has zero legal moves — a
# direct contract violation.
_HOST_ONLY_FOLLOW_ON_STAGES: frozenset[str] = frozenset({
    "project-skill-bootstrap",
    "opencode-team-bootstrap",
    "agent-prompt-engineering",
})


def audit_managed_blocked_deadlock(
    root: Path, findings: list[Finding], ctx: LifecycleContractAuditContext
) -> None:
    """WFLOW030 — managed_blocked deadlock: no legal move exists for the local agent.

    Fires when all of the following are true:
    1. repair_follow_on.outcome == "managed_blocked"
    2. At least one required stage is not yet in completed_stages
    3. All unresolved required stages are host-only (project-skill-bootstrap,
       opencode-team-bootstrap, agent-prompt-engineering)
    4. ticket_update.ts contains the hasPendingRepairFollowOn guard (confirms
       the lifecycle block is active in the installed runtime)

    The combination means the local agent cannot advance any ticket AND cannot
    complete any required follow-on stage — a zero-legal-moves deadlock.
    """
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    ticket_update_path = root / ".opencode" / "tools" / "ticket_update.ts"

    if not workflow_path.exists():
        return

    workflow = ctx.read_json(workflow_path)
    if not isinstance(workflow, dict):
        return

    repair_follow_on = workflow.get("repair_follow_on")
    if not isinstance(repair_follow_on, dict):
        return

    if repair_follow_on.get("outcome") != "managed_blocked":
        return

    required: list[str] = [
        str(s) for s in repair_follow_on.get("required_stages", [])
        if isinstance(s, str) and s.strip()
    ]
    completed: set[str] = {
        str(s) for s in repair_follow_on.get("completed_stages", [])
        if isinstance(s, str) and s.strip()
    }
    unresolved = [s for s in required if s not in completed]
    if not unresolved:
        return

    host_only_unresolved = [s for s in unresolved if s in _HOST_ONLY_FOLLOW_ON_STAGES]
    non_host_unresolved = [s for s in unresolved if s not in _HOST_ONLY_FOLLOW_ON_STAGES]

    # Only fire WFLOW030 when ALL unresolved stages are host-only.
    # If a local-agent stage (e.g. ticket-pack-builder) is still unresolved,
    # the agent has at least one legal move.
    if non_host_unresolved:
        return
    if not host_only_unresolved:
        return

    # Confirm the lifecycle block guard is actually installed in the runtime.
    tool_has_guard = (
        ticket_update_path.exists()
        and "hasPendingRepairFollowOn" in ctx.read_text(ticket_update_path)
    )
    if not tool_has_guard:
        return

    evidence: list[str] = [
        f"repair_follow_on.outcome = managed_blocked",
        f"required_stages = {required}",
        f"completed_stages = {sorted(completed)}",
        f"unresolved host-only stages = {host_only_unresolved}",
        f"ticket_update.ts contains hasPendingRepairFollowOn guard — lifecycle mutations are blocked for all tickets.",
    ]

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW030",
            severity="error",
            problem="Repo is in managed_blocked deadlock: all unresolved required follow-on stages are host-only, so the local agent has zero legal moves.",
            root_cause=(
                "The repair cycle left managed_blocked active with only host-only required stages "
                "(project-skill-bootstrap, opencode-team-bootstrap, or agent-prompt-engineering) "
                "still incomplete, while ticket_update.ts blocks ALL ticket lifecycle mutations "
                "when managed_blocked is set. The local agent cannot complete host-only stages "
                "and cannot advance any ticket. This is a direct violation of the Scafforge "
                "contract: the repo must always expose one legal next move with one named owner."
            ),
            files=[
                ctx.normalize_path(workflow_path, root),
                ctx.normalize_path(ticket_update_path, root),
            ],
            safer_pattern=(
                "Host-operator must: (1) run the required host-only stages "
                "(project-skill-bootstrap via Scafforge), (2) update "
                "repair_follow_on.completed_stages in workflow-state.json, and "
                "(3) set outcome to 'clean' or 'source_follow_up' once all stages "
                "are done. After that the local agent regains ticket mutation access."
            ),
            evidence=evidence,
            provenance="script",
        ),
    )
