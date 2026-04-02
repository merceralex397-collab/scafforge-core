from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Callable

from shared_verifier_types import Finding


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
    audit_reverification_deadlock(root, findings, ctx)
    audit_smoke_test_artifact_bypass(root, findings, ctx)
    audit_handoff_artifact_ownership_conflict(root, findings, ctx)
