from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Callable

from shared_verifier_types import Finding
from target_completion import declares_godot_android_target, load_manifest, missing_android_completion_ticket_ids, other_android_owner_tickets


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
        superseded_follow_up = ticket.get("status") == "done" and ticket.get("resolution_state") == "superseded"
        if not superseded_follow_up and ticket_id not in source_follow_ups:
            evidence.append(f"{ticket_id} names {source_ticket_id} as source_ticket_id, but {source_ticket_id} does not list it in follow_up_ticket_ids.")
        if ticket_id in source_follow_ups and source_ticket_id in depends_on:
            evidence.append(f"{ticket_id} is listed as a follow-up of {source_ticket_id} while still declaring {source_ticket_id} as a blocking dependency.")
    for ticket_id, ticket in tickets_by_id.items():
        source_follow_ups = [
            str(item).strip()
            for item in ticket.get("follow_up_ticket_ids", [])
            if isinstance(item, str) and str(item).strip()
        ]
        for follow_up_ticket_id in source_follow_ups:
            follow_up_ticket = tickets_by_id.get(follow_up_ticket_id)
            if follow_up_ticket is None:
                evidence.append(f"{ticket_id} lists missing follow-up ticket {follow_up_ticket_id} in follow_up_ticket_ids.")
                continue
            if str(follow_up_ticket.get("source_ticket_id", "")).strip() != ticket_id:
                evidence.append(
                    f"{ticket_id} lists {follow_up_ticket_id} in follow_up_ticket_ids, but {follow_up_ticket_id} names {follow_up_ticket.get('source_ticket_id')} as source_ticket_id."
                )
            if follow_up_ticket.get("status") == "done" and follow_up_ticket.get("resolution_state") == "superseded":
                evidence.append(f"{ticket_id} still lists superseded follow-up ticket {follow_up_ticket_id} in follow_up_ticket_ids.")
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


def audit_android_target_completion_backlog(root: Path, findings: list[Finding], ctx: TicketGraphAuditContext) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    if not manifest_path.exists() or not declares_godot_android_target(root):
        return

    manifest = load_manifest(root)
    missing_ids = missing_android_completion_ticket_ids(manifest, root)
    if not missing_ids:
        return

    evidence = [
        f"{ctx.normalize_path(manifest_path, root)} is missing canonical Android target-completion tickets: {', '.join(missing_ids)}."
    ]
    generic_owners = other_android_owner_tickets(manifest)
    if generic_owners:
        evidence.append(
            f"Android export or APK work is currently being carried by non-canonical ticket(s): {', '.join(generic_owners)}."
        )

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW025",
            severity="error",
            problem="Declared Godot Android target lacks canonical backlog ownership for export surfaces and debug APK proof.",
            root_cause="The repo declares Android delivery in canonical truth, but the backlog never created the dedicated Android export, signing when required, and release lanes. That lets presentation or validation tickets absorb Android work without a real export or release-proof path.",
            files=[ctx.normalize_path(manifest_path, root), ctx.normalize_path(root / "docs" / "spec" / "CANONICAL-BRIEF.md", root)],
            safer_pattern="For Godot Android repos, always create `ANDROID-001` in lane `android-export` for repo-local export surfaces, add `SIGNING-001` when packaged delivery is required, and keep `RELEASE-001` in lane `release-readiness` for runnable and deliverable proof ownership. Do not let generic polish tickets stand in for release ownership.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_completed_parent_split_scope_children(root: Path, findings: list[Finding], ctx: TicketGraphAuditContext) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    workflow_lib_path = root / ".opencode" / "lib" / "workflow.ts"
    if not manifest_path.exists():
        return

    # Only flag deadlock if the installed workflow.ts still contains the bad throw.
    # An open split_scope child with a done parent is canonical for sequential-dependent splits
    # (ticket_update.ts explicitly requires the parent to be done before activating the child).
    # The defect is the TOOL, not the manifest state. If the tool is already fixed, this is valid state.
    if workflow_lib_path.exists():
        workflow_lib_text = ctx.read_text(workflow_lib_path)
        if "Split-scope child" not in workflow_lib_text and "cannot point at a completed source ticket" not in workflow_lib_text:
            return

    manifest = ctx.read_json(manifest_path)
    tickets = manifest.get("tickets") if isinstance(manifest, dict) and isinstance(manifest.get("tickets"), list) else []
    if not tickets:
        return

    tickets_by_id = {
        str(t.get("id")): t
        for t in tickets
        if isinstance(t, dict) and isinstance(t.get("id"), str)
    }
    evidence: list[str] = []

    for ticket_id, ticket in tickets_by_id.items():
        if str(ticket.get("source_mode", "")).strip() != "split_scope":
            continue
        source_ticket_id = str(ticket.get("source_ticket_id", "")).strip()
        if not source_ticket_id:
            continue
        source = tickets_by_id.get(source_ticket_id)
        if not isinstance(source, dict):
            continue
        source_status = str(source.get("status", "")).strip()
        source_resolution = str(source.get("resolution_state", "")).strip()
        if source_status == "done" or source_resolution == "superseded":
            child_status = str(ticket.get("status", "")).strip()
            if child_status not in {"done"}:
                evidence.append(
                    f"{ticket_id} (status={child_status}) is a split_scope child of {source_ticket_id}"
                    f" (status={source_status}, resolution_state={source_resolution or 'none'})."
                    f" The installed workflow.ts still contains the deadlock throw that blocks all manifest"
                    f" mutations whenever this state exists. Run scafforge-repair to install fixed tools."
                )

    if not evidence:
        return

    workflow = ctx.read_json(workflow_path) if workflow_path.exists() else {}
    active_ticket = str(workflow.get("active_ticket", "")).strip() if isinstance(workflow, dict) else ""
    affected_ids = [e.split(" ")[0] for e in evidence]
    if active_ticket in affected_ids:
        evidence.insert(
            0,
            f"Active ticket {active_ticket} is one of the affected split_scope children."
            f" ALL manifest mutations are currently blocked — this is a global workflow deadlock.",
        )

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW028",
            severity="error",
            problem="Installed workflow.ts blocks all manifest mutations when a split-scope child's parent ticket closes.",
            root_cause=(
                "The installed workflow.ts contains a global invariant that throws when any split_scope child ticket"
                " has a completed source ticket. This fires during every manifest write, not just for the affected ticket."
                " Sequential-dependent split children are designed to activate AFTER their parent closes (per ticket_update.ts),"
                " so this invariant contradicts the intended workflow and causes a global write deadlock."
                " The fix is to install the corrected workflow.ts via scafforge-repair."
            ),
            files=[
                ctx.normalize_path(manifest_path, root),
                ctx.normalize_path(workflow_lib_path, root),
                *(
                    [ctx.normalize_path(workflow_path, root)]
                    if workflow_path.exists()
                    else []
                ),
            ],
            safer_pattern=(
                "After scafforge-repair installs the fixed workflow.ts, the sequential-dependent split-scope pattern"
                " works correctly: split children wait while parent is open, activate after parent closes."
                " No ticket_reconcile is needed — the manifest state is valid once the tool is fixed."
                " If ticket_reconcile must be called on a split child for any other reason (evidence update, lineage"
                " repair), explicitly pass replacement_source_mode with a non-split_scope value; leaving it defaulted"
                " will cause ticket_reconcile to reject the completed source and appear to deadlock again."
            ),
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_release_feature_gate(root: Path, findings: list[Finding], ctx: TicketGraphAuditContext) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    if not manifest_path.exists() or not declares_godot_android_target(root):
        return

    manifest = load_manifest(root)
    tickets = manifest.get("tickets", []) if isinstance(manifest, dict) else []
    ticket_by_id = {str(t.get("id", "")).strip(): t for t in tickets if isinstance(t, dict)}

    release = ticket_by_id.get("RELEASE-001")
    if not release:
        return  # WFLOW025 covers the missing RELEASE-001 case

    _EXCLUDED_LANES: frozenset[str] = frozenset(
        {"android-export", "signing-prerequisites", "release-readiness", "remediation", "reverification"}
    )
    feature_ids = {
        str(t.get("id", "")).strip()
        for t in tickets
        if isinstance(t, dict)
        and t.get("lane") not in _EXCLUDED_LANES
        and int(t.get("wave", 0)) > 0
    }

    if not feature_ids:
        return  # no eligible product feature tickets exist — pure pipeline-proof repo, no gate possible

    release_deps = {str(d).strip() for d in release.get("depends_on", [])}
    if release_deps & feature_ids:
        return  # has at least one qualifying feature gate

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW029",
            severity="error",
            problem="RELEASE-001 has no depends_on edge to any product feature ticket.",
            root_cause=(
                "RELEASE-001 was generated or created without a dependency on the terminal product feature ticket(s)."
                " Wave ordering is advisory only; the workflow engine only enforces depends_on edges."
                " Without a feature gate, agents can claim RELEASE-001 and attempt to build the APK"
                " before any game features are implemented."
            ),
            files=[ctx.normalize_path(manifest_path, root)],
            safer_pattern=(
                "RELEASE-001 must declare depends_on edges to all terminal product tickets"
                " (highest-wave non-infrastructure, non-remediation tickets)."
                " source_ticket_id records split-scope lineage only and must not appear in depends_on."
            ),
            evidence=[
                f"{ctx.normalize_path(manifest_path, root)}: RELEASE-001.depends_on={release.get('depends_on', [])} "
                f"contains no qualified product feature ticket.",
                f"Qualified feature ticket candidates (highest wave among non-excluded lanes): "
                f"{sorted(feature_ids)}.",
            ],
            provenance="script",
        ),
    )


def run_ticket_graph_audits(root: Path, findings: list[Finding], ctx: TicketGraphAuditContext) -> None:
    audit_closed_ticket_follow_up_deadlock(root, findings, ctx)
    audit_stale_ticket_graph(root, findings, ctx)
    audit_historical_reconciliation_deadlock(root, findings, ctx)
    audit_open_ticket_split_routing(root, findings, ctx)
    audit_android_target_completion_backlog(root, findings, ctx)
    audit_completed_parent_split_scope_children(root, findings, ctx)
    audit_release_feature_gate(root, findings, ctx)
