from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Callable

from shared_verifier_types import Finding


@dataclass(frozen=True)
class TicketGraphAuditContext:
    read_text: Callable[[Path], str]
    read_json: Callable[[Path], Any]
    normalize_path: Callable[[Path, Path], str]
    add_finding: Callable[[list[Finding], Finding], None]


def audit_closed_ticket_follow_up_deadlock(root: Path, findings: list[Finding], ctx: TicketGraphAuditContext) -> None:
    stage_gate = root / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    ticket_create = root / ".opencode" / "tools" / "ticket_create.ts"
    issue_intake = root / ".opencode" / "tools" / "issue_intake.ts"
    if not stage_gate.exists() or not ticket_create.exists() or not issue_intake.exists():
        return

    stage_gate_text = ctx.read_text(stage_gate)
    ticket_create_text = ctx.read_text(ticket_create)
    issue_intake_text = ctx.read_text(issue_intake)
    evidence: list[str] = []

    if (
        ("process_verification" in ticket_create_text or "post_completion_issue" in ticket_create_text)
        and 'await ensureTargetTicketWriteLease(sourceTicketId || workflow.active_ticket)' in stage_gate_text
    ):
        evidence.append(
            f"{ctx.normalize_path(stage_gate, root)} still forces `ticket_create` follow-up creation through the source ticket's normal write lease even for closed historical remediation paths."
        )
    issue_block = ""
    issue_match = re.search(r'if \(input\.tool === "issue_intake"\) \{([\s\S]*?)\n\s{6}\}', stage_gate_text)
    if issue_match:
        issue_block = issue_match.group(1)
    issue_block_deadlocked = "ensureTargetTicketWriteLease(sourceTicketId)" in issue_block
    if issue_block_deadlocked:
        evidence.append(f"{ctx.normalize_path(stage_gate, root)} still requires a normal source-ticket write lease before `issue_intake` can route a completed-ticket defect.")
    if issue_block_deadlocked and "must already be complete before issue intake" in issue_intake_text and "post-completion" in issue_intake_text:
        evidence.append(f"{ctx.normalize_path(issue_intake, root)} expects completed historical sources, so the plugin lease requirement can deadlock the intended route.")

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW018",
            severity="error",
            problem="Closed-ticket remediation routing is still deadlocked by normal write-lease rules.",
            root_cause="The generated workflow allows process-verification and post-completion follow-up from completed historical tickets, but the stage-gate still treats those routes like ordinary lease-bound mutations. Closed tickets cannot satisfy that lease requirement.",
            files=[
                ctx.normalize_path(stage_gate, root),
                ctx.normalize_path(ticket_create, root),
                ctx.normalize_path(issue_intake, root),
            ],
            safer_pattern="Let `ticket_create(process_verification|post_completion_issue)` and `issue_intake` operate from current registered evidence on completed historical tickets without requiring the source ticket's normal write lease.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_stale_ticket_graph(root: Path, findings: list[Finding], ctx: TicketGraphAuditContext) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    manifest = ctx.read_json(manifest_path)
    tickets = manifest.get("tickets") if isinstance(manifest, dict) and isinstance(manifest.get("tickets"), list) else []
    if not tickets:
        return

    tickets_by_id: dict[str, dict[str, Any]] = {}
    for ticket in tickets:
        if isinstance(ticket, dict) and isinstance(ticket.get("id"), str):
            tickets_by_id[str(ticket.get("id"))] = ticket

    evidence: list[str] = []
    for ticket_id, ticket in tickets_by_id.items():
        source_ticket_id = ticket.get("source_ticket_id").strip() if isinstance(ticket.get("source_ticket_id"), str) else ""
        if not source_ticket_id:
            continue
        depends_on = [str(item).strip() for item in ticket.get("depends_on", []) if isinstance(item, str) and str(item).strip()]
        source_ticket = tickets_by_id.get(source_ticket_id)
        if source_ticket_id in depends_on:
            evidence.append(f"{ticket_id} both names {source_ticket_id} as source_ticket_id and depends_on that same ticket.")
        if source_ticket is None:
            evidence.append(f"{ticket_id} references missing source_ticket_id {source_ticket_id}.")
            continue
        source_follow_ups = [str(item).strip() for item in source_ticket.get("follow_up_ticket_ids", []) if isinstance(item, str) and str(item).strip()]
        if ticket_id not in source_follow_ups:
            evidence.append(f"{ticket_id} names {source_ticket_id} as source_ticket_id, but {source_ticket_id} does not list it in follow_up_ticket_ids.")
        if ticket_id in source_follow_ups and source_ticket_id in depends_on:
            evidence.append(f"{ticket_id} is listed as a follow-up of {source_ticket_id} while still declaring {source_ticket_id} as a blocking dependency.")
    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW019",
            severity="error",
            problem="The ticket graph contains stale or contradictory source/follow-up linkage.",
            root_cause="The repo has follow-up tickets whose lineage, dependency edges, or parent linkage no longer agree with the current manifest. Without a canonical reconciliation path, agents get trapped between stale source-follow-up history and current evidence.",
            files=[ctx.normalize_path(manifest_path, root)],
            safer_pattern="Use `ticket_reconcile` to atomically repair stale source/follow-up linkage, remove contradictory parent dependencies, and supersede invalidated follow-up tickets from current evidence.",
            evidence=evidence[:12],
            provenance="script",
        ),
    )


def audit_historical_reconciliation_deadlock(root: Path, findings: list[Finding], ctx: TicketGraphAuditContext) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    ticket_reconcile = root / ".opencode" / "tools" / "ticket_reconcile.ts"
    ticket_create = root / ".opencode" / "tools" / "ticket_create.ts"
    issue_intake = root / ".opencode" / "tools" / "issue_intake.ts"
    stage_gate = root / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    if not all(path.exists() for path in (manifest_path, workflow_path, ticket_reconcile, ticket_create, issue_intake, stage_gate)):
        return

    manifest = ctx.read_json(manifest_path)
    workflow = ctx.read_json(workflow_path)
    tickets = manifest.get("tickets") if isinstance(manifest, dict) and isinstance(manifest.get("tickets"), list) else []
    if not isinstance(workflow, dict) or not tickets:
        return

    deadlocked = [
        ticket
        for ticket in tickets
        if isinstance(ticket, dict)
        and ticket.get("status") == "done"
        and ticket.get("resolution_state") == "superseded"
        and ticket.get("verification_state") == "invalidated"
    ]
    if not deadlocked:
        return

    reconcile_text = ctx.read_text(ticket_reconcile)
    ticket_create_text = ctx.read_text(ticket_create)
    issue_intake_text = ctx.read_text(issue_intake)
    stage_gate_text = ctx.read_text(stage_gate)
    evidence: list[str] = []

    if "supersededTarget," in reconcile_text and "const supersedeTarget" in reconcile_text:
        evidence.append(f"{ctx.normalize_path(ticket_reconcile, root)} still contains the `supersededTarget`/`supersedeTarget` runtime typo.")
    if 'targetTicket.verification_state = "invalidated"' in reconcile_text:
        evidence.append(f"{ctx.normalize_path(ticket_reconcile, root)} still re-writes superseded reconciliation targets to `verification_state = invalidated`.")
    if "currentRegistryArtifact" not in reconcile_text and "Neither ${sourceTicket.id} nor ${targetTicket.id} has a current evidence artifact" in reconcile_text:
        evidence.append(f"{ctx.normalize_path(ticket_reconcile, root)} still accepts evidence only when it remains directly attached to the source or target ticket.")
    if "does not reference the evidence artifact" in ticket_create_text:
        evidence.append(f"{ctx.normalize_path(ticket_create, root)} still requires historical source tickets to directly reference the evidence artifact path.")
    if "does not reference the evidence artifact" in issue_intake_text:
        evidence.append(f"{ctx.normalize_path(issue_intake, root)} still requires historical source tickets to directly reference the evidence artifact path.")
    if 'ticket.status === "done" && ticket.verification_state === "invalidated"' in stage_gate_text:
        evidence.append(f"{ctx.normalize_path(stage_gate, root)} still blocks handoff while any done invalidated ticket remains unresolved.")

    active_ticket_id = str(workflow.get("active_ticket", "")).strip()
    active_ticket = next((ticket for ticket in deadlocked if str(ticket.get("id", "")).strip() == active_ticket_id), None)
    if active_ticket:
        evidence.append(f"workflow-state still foregrounds closed historical ticket {active_ticket_id} while it is `superseded` and `invalidated`.")
    for ticket in deadlocked[:3]:
        ticket_id = str(ticket.get("id", "")).strip()
        artifact_count = len(ticket.get("artifacts", [])) if isinstance(ticket.get("artifacts"), list) else 0
        evidence.append(f"{ticket_id} is still `done + superseded + invalidated` with {artifact_count} recorded artifacts.")

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW024",
            severity="error",
            problem="The current workflow has no legal reconciliation path for a superseded invalidated historical ticket, so closeout publication can deadlock on impossible preconditions.",
            root_cause="Historical reconciliation still assumes the relevant evidence remains directly attached to the old source/target ticket, and the supersede path leaves the target publish-blocking invalidated. That traps the repo between stale historical state and closeout publication.",
            files=[
                ctx.normalize_path(manifest_path, root),
                ctx.normalize_path(workflow_path, root),
                ctx.normalize_path(ticket_reconcile, root),
                ctx.normalize_path(ticket_create, root),
                ctx.normalize_path(issue_intake, root),
                ctx.normalize_path(stage_gate, root),
            ],
            safer_pattern="Give `ticket_reconcile`, `ticket_create(post_completion_issue|process_verification)`, and `issue_intake` one legal path that can use current registered evidence for historical tickets, and make successful supersede-through-reconciliation non-blocking for handoff publication.",
            evidence=evidence[:10],
            provenance="script",
        ),
    )


def audit_open_ticket_split_routing(root: Path, findings: list[Finding], ctx: TicketGraphAuditContext) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    ticket_create = root / ".opencode" / "tools" / "ticket_create.ts"
    workflow_tool = root / ".opencode" / "lib" / "workflow.ts"
    if not manifest_path.exists() or not ticket_create.exists() or not workflow_tool.exists():
        return

    manifest = ctx.read_json(manifest_path)
    tickets = manifest.get("tickets") if isinstance(manifest, dict) and isinstance(manifest.get("tickets"), list) else []
    if not tickets:
        return

    ticket_create_text = ctx.read_text(ticket_create)
    workflow_text = ctx.read_text(workflow_tool)
    tickets_by_id = {
        str(ticket.get("id")): ticket
        for ticket in tickets
        if isinstance(ticket, dict) and isinstance(ticket.get("id"), str)
    }
    evidence: list[str] = []

    if "split_scope" not in ticket_create_text or "split_scope" not in workflow_text:
        evidence.append("The generated ticket toolchain does not expose `split_scope` as a first-class source mode.")

    for ticket_id, ticket in tickets_by_id.items():
        source_ticket_id = ticket.get("source_ticket_id").strip() if isinstance(ticket.get("source_ticket_id"), str) else ""
        if not source_ticket_id:
            continue
        source_ticket = tickets_by_id.get(source_ticket_id)
        if not isinstance(source_ticket, dict):
            continue
        source_status = str(source_ticket.get("status", "")).strip()
        source_resolution = str(source_ticket.get("resolution_state", "open")).strip() or "open"
        if source_status == "done" or source_resolution not in {"open", "reopened"}:
            continue
        if str(ticket.get("source_mode", "")).strip() != "split_scope":
            evidence.append(
                f"{ticket_id} extends open source ticket {source_ticket_id} but uses source_mode={ticket.get('source_mode') or 'None'} instead of split_scope."
            )
        if str(ticket.get("source_mode", "")).strip() == "split_scope" and source_status == "blocked":
            evidence.append(
                f"{source_ticket_id} is still marked blocked even though split child {ticket_id} should keep the parent open and non-foreground."
            )

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW020",
            severity="error",
            problem="Open-parent ticket decomposition is missing or routed through non-canonical source modes.",
            root_cause="The workflow lacks a first-class split route for child tickets created from an open parent, or it still renders split parents as blocked, so agents encode decomposition through remediation semantics and the parent/child graph drifts.",
            files=[
                ctx.normalize_path(manifest_path, root),
                ctx.normalize_path(ticket_create, root),
                ctx.normalize_path(workflow_tool, root),
            ],
            safer_pattern="Support `ticket_create(source_mode=split_scope)` for open-parent decomposition, keep the parent open and non-foreground, and keep open-parent child tickets out of `net_new_scope` and `post_completion_issue` routing.",
            evidence=evidence,
            provenance="script",
        ),
    )


def run_ticket_graph_audits(root: Path, findings: list[Finding], ctx: TicketGraphAuditContext) -> None:
    audit_closed_ticket_follow_up_deadlock(root, findings, ctx)
    audit_stale_ticket_graph(root, findings, ctx)
    audit_historical_reconciliation_deadlock(root, findings, ctx)
    audit_open_ticket_split_routing(root, findings, ctx)
