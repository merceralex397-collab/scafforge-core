from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Callable

from shared_verifier_types import Finding


@dataclass(frozen=True)
class RestartSurfaceAuditContext:
    read_text: Callable[[Path], str]
    read_json: Callable[[Path], Any]
    normalize_path: Callable[[Path, Path], str]
    add_finding: Callable[[list[Finding], Finding], None]
    matching_lines: Callable[[str, tuple[str, ...]], list[str]]
    combine_outputs: Callable[..., str]
    active_ticket: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any] | None]
    blocked_dependents: Callable[[dict[str, Any], str], list[str]]
    expected_restart_surface_state: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any] | None]
    normalize_restart_surface_value: Callable[[Any], Any]
    parse_start_here_state: Callable[[str], dict[str, Any]]
    parse_context_snapshot_state: Callable[[str], dict[str, Any]]
    parse_invocation_log_events: Callable[[Path], list[Any]]
    is_coordinator_assistant: Callable[[str], bool]


HANDOFF_OVERCLAIM_PATTERNS = (
    r"\bunblocked\b",
    r"not a code defect",
    r"only blocker",
    r"tool/env mismatch",
    r"tooling issue",
)

COORDINATOR_ARTIFACT_STAGES = {"planning", "implementation", "review", "qa", "smoke-test"}


def audit_restart_surface_drift(root: Path, findings: list[Finding], ctx: RestartSurfaceAuditContext) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    start_here_path = root / "START-HERE.md"
    context_snapshot_path = root / ".opencode" / "state" / "context-snapshot.md"
    latest_handoff_path = root / ".opencode" / "state" / "latest-handoff.md"
    manifest = ctx.read_json(manifest_path)
    workflow = ctx.read_json(workflow_path)
    if not isinstance(manifest, dict) or not isinstance(workflow, dict):
        return

    expected = ctx.expected_restart_surface_state(manifest, workflow)
    if expected is None:
        return

    evidence: list[str] = []
    files = [
        ctx.normalize_path(manifest_path, root),
        ctx.normalize_path(workflow_path, root),
    ]

    def compare_surface(surface_label: str, observed: dict[str, Any], expected_keys: tuple[str, ...]) -> None:
        for key in expected_keys:
            observed_value = ctx.normalize_restart_surface_value(observed.get(key))
            expected_value = ctx.normalize_restart_surface_value(expected.get(key))
            if observed_value == expected_value:
                continue
            evidence.append(f"{surface_label} {key} drift: expected {expected_value!r} from canonical state, found {observed_value!r}.")

    if start_here_path.exists():
        files.append(ctx.normalize_path(start_here_path, root))
        compare_surface(
            ctx.normalize_path(start_here_path, root),
            ctx.parse_start_here_state(ctx.read_text(start_here_path)),
            (
                "ticket_id",
                "stage",
                "status",
                "handoff_status",
                "bootstrap_status",
                "bootstrap_proof",
                "pending_process_verification",
                "repair_follow_on_outcome",
                "repair_follow_on_required",
                "repair_follow_on_next_stage",
                "repair_follow_on_verification_passed",
                "split_child_tickets",
                "done_but_not_fully_trusted",
                "repair_follow_on_updated_at",
            ),
        )
    else:
        files.append(ctx.normalize_path(start_here_path, root))
        evidence.append(f"Missing derived restart surface: {ctx.normalize_path(start_here_path, root)}.")

    if context_snapshot_path.exists():
        files.append(ctx.normalize_path(context_snapshot_path, root))
        compare_surface(
            ctx.normalize_path(context_snapshot_path, root),
            ctx.parse_context_snapshot_state(ctx.read_text(context_snapshot_path)),
            (
                "ticket_id",
                "stage",
                "status",
                "open_split_children",
                "bootstrap_status",
                "bootstrap_proof",
                "pending_process_verification",
                "repair_follow_on_outcome",
                "repair_follow_on_required",
                "repair_follow_on_next_stage",
                "repair_follow_on_verification_passed",
                "repair_follow_on_updated_at",
                "state_revision",
                "has_lane_leases",
            ),
        )
    else:
        files.append(ctx.normalize_path(context_snapshot_path, root))
        evidence.append(f"Missing derived restart surface: {ctx.normalize_path(context_snapshot_path, root)}.")

    if latest_handoff_path.exists():
        files.append(ctx.normalize_path(latest_handoff_path, root))
        compare_surface(
            ctx.normalize_path(latest_handoff_path, root),
            ctx.parse_start_here_state(ctx.read_text(latest_handoff_path)),
            (
                "ticket_id",
                "stage",
                "status",
                "handoff_status",
                "bootstrap_status",
                "bootstrap_proof",
                "pending_process_verification",
                "repair_follow_on_outcome",
                "repair_follow_on_required",
                "repair_follow_on_next_stage",
                "repair_follow_on_verification_passed",
                "split_child_tickets",
                "done_but_not_fully_trusted",
                "repair_follow_on_updated_at",
            ),
        )
    else:
        files.append(ctx.normalize_path(latest_handoff_path, root))
        evidence.append(f"Missing derived restart surface: {ctx.normalize_path(latest_handoff_path, root)}.")

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW010",
            severity="error",
            problem="Derived restart surfaces disagree with canonical workflow state, so resume guidance can route work from stale or contradictory facts.",
            root_cause="`START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are not being regenerated from `tickets/manifest.json` plus `.opencode/state/workflow-state.json` after workflow mutations or managed repair, leaving bootstrap, repair-follow-on, verification, lane-lease, or active-ticket state stale.",
            files=list(dict.fromkeys(files)),
            safer_pattern="Regenerate `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` from canonical manifest/workflow state after every workflow save, compute handoff readiness from bootstrap plus repair-follow-on plus verification state in one shared contract, and fail repair verification if any derived restart surface drifts.",
            evidence=evidence[:10],
            provenance="script",
        ),
    )


def audit_legacy_repair_gate_leak(root: Path, findings: list[Finding], ctx: RestartSurfaceAuditContext) -> None:
    candidate_paths = [
        root / "START-HERE.md",
        root / ".opencode" / "state" / "context-snapshot.md",
        root / ".opencode" / "state" / "latest-handoff.md",
        root / ".opencode" / "commands" / "resume.md",
        root / ".opencode" / "commands" / "kickoff.md",
        root / ".opencode" / "skills" / "ticket-execution" / "SKILL.md",
    ]
    team_leader = next((path for path in (root / ".opencode" / "agents").glob("*team-leader*.md")), None)
    if team_leader:
        candidate_paths.append(team_leader)

    evidence: list[str] = []
    files: list[str] = []
    for path in candidate_paths:
        if not path.exists():
            continue
        text = ctx.read_text(path)
        local_evidence: list[str] = []
        if "repair_follow_on.handoff_allowed" in text:
            local_evidence.append("still instructs agents to reason from `repair_follow_on.handoff_allowed`.")
        if "repair_follow_on_handoff_allowed" in text:
            local_evidence.append("still renders `repair_follow_on_handoff_allowed` as a public restart-surface field.")
        if re.search(r"^\s*-\s*handoff_allowed\s*:", text, re.MULTILINE):
            local_evidence.append("still renders `handoff_allowed` as a public repair-follow-on bullet.")
        if not local_evidence:
            continue
        files.append(ctx.normalize_path(path, root))
        for entry in local_evidence:
            evidence.append(f"{ctx.normalize_path(path, root)} {entry}")

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW021",
            severity="error",
            problem="Generated prompts or restart surfaces still gate workflow decisions on the legacy `handoff_allowed` flag instead of the outcome model.",
            root_cause="The package introduced `repair_follow_on.outcome`, but legacy boolean handoff gating survived in generated prompts and restart surfaces. That leaves weaker models reasoning from stale or secondary fields even when the managed outcome is already canonical.",
            files=list(dict.fromkeys(files)),
            safer_pattern="Keep backward-compatible `handoff_allowed` parsing internal only. Generated prompts, commands, and restart surfaces should route from `repair_follow_on.outcome`, `repair_follow_on_required`, `repair_follow_on_next_stage`, and truthful verification state.",
            evidence=evidence[:10],
            provenance="script",
        ),
    )


def audit_bootstrap_guidance_drift(root: Path, findings: list[Finding], ctx: RestartSurfaceAuditContext) -> None:
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    workflow = ctx.read_json(workflow_path)
    if not isinstance(workflow, dict):
        return

    bootstrap = workflow.get("bootstrap") if isinstance(workflow.get("bootstrap"), dict) else {}
    bootstrap_status = str(bootstrap.get("status", "")).strip()
    if bootstrap_status == "ready" or not bootstrap_status:
        return

    ticket_lookup = root / ".opencode" / "tools" / "ticket_lookup.ts"
    team_leader = next((path for path in (root / ".opencode" / "agents").glob("*team-leader*.md")), None)
    ticket_execution = root / ".opencode" / "skills" / "ticket-execution" / "SKILL.md"
    evidence: list[str] = []
    files = [ctx.normalize_path(workflow_path, root)]

    ticket_lookup_text = ctx.read_text(ticket_lookup)
    if "Run environment_bootstrap first, then rerun ticket_lookup before attempting lifecycle transitions." not in ticket_lookup_text:
        files.append(ctx.normalize_path(ticket_lookup, root))
        evidence.append(f"{ctx.normalize_path(ticket_lookup, root)} does not short-circuit lifecycle guidance to `environment_bootstrap` when bootstrap is not ready.")

    if team_leader is None:
        files.append(".opencode/agents/*team-leader*.md")
        evidence.append("Missing team leader prompt; no bootstrap-first routing guidance is available to the coordinator.")
    else:
        team_leader_text = ctx.read_text(team_leader)
        if "If `ticket_lookup.bootstrap.status` is not `ready`, treat `environment_bootstrap` as the next required tool call" not in team_leader_text:
            files.append(ctx.normalize_path(team_leader, root))
            evidence.append(f"{ctx.normalize_path(team_leader, root)} does not make bootstrap-first routing explicit when bootstrap is not ready.")

    if not ticket_execution.exists():
        files.append(ctx.normalize_path(ticket_execution, root))
        evidence.append(f"Missing repo-local workflow explainer: {ctx.normalize_path(ticket_execution, root)}.")
    else:
        ticket_execution_text = ctx.read_text(ticket_execution)
        if "if `ticket_lookup.bootstrap.status` is not `ready`, stop normal lifecycle routing, run `environment_bootstrap`, then rerun `ticket_lookup` before any `ticket_update`" not in ticket_execution_text:
            files.append(ctx.normalize_path(ticket_execution, root))
            evidence.append(f"{ctx.normalize_path(ticket_execution, root)} does not tell agents to treat bootstrap repair as the next required action.")

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW011",
            severity="error",
            problem="Bootstrap is not ready, but generated transition guidance and coordinator instructions do not make `environment_bootstrap` the first required action.",
            root_cause="The generated repo still asks the coordinator to infer bootstrap recovery from scattered hints. When bootstrap is missing, failed, or stale, weaker models keep attempting lifecycle progress or alternate transitions instead of restoring the environment first.",
            files=list(dict.fromkeys(files)),
            safer_pattern="When bootstrap is not `ready`, make `ticket_lookup.transition_guidance`, the team leader prompt, and `ticket-execution` short-circuit to `environment_bootstrap`, rerun `ticket_lookup` afterward, and stop normal lifecycle routing until bootstrap succeeds.",
            evidence=[f"{ctx.normalize_path(workflow_path, root)} records bootstrap.status = {bootstrap_status}.", *evidence[:7]],
            provenance="script",
        ),
    )


def audit_lease_claim_guidance_drift(root: Path, findings: list[Finding], ctx: RestartSurfaceAuditContext) -> None:
    workflow_doc = root / "docs" / "process" / "workflow.md"
    ticket_readme = root / "tickets" / "README.md"
    kickoff = root / ".opencode" / "commands" / "kickoff.md"
    run_lane = root / ".opencode" / "commands" / "run-lane.md"
    ticket_execution = root / ".opencode" / "skills" / "ticket-execution" / "SKILL.md"
    team_leader = next((path for path in (root / ".opencode" / "agents").glob("*team-leader*.md")), None)
    implementer = next((path for path in (root / ".opencode" / "agents").glob("*implementer*.md")), None)
    lane_executor = next((path for path in (root / ".opencode" / "agents").glob("*lane-executor*.md")), None)
    docs_handoff = next((path for path in (root / ".opencode" / "agents").glob("*docs-handoff*.md")), None)

    evidence: list[str] = []
    files: list[str] = []
    expected_coordination = "the team leader owns `ticket_claim` and `ticket_release`"
    prebootstrap_guard = "only Wave 0 setup work may claim a write-capable lease before bootstrap is ready"

    for path in (workflow_doc, ticket_readme, kickoff, run_lane, ticket_execution):
        if not path.exists():
            files.append(ctx.normalize_path(path, root))
            evidence.append(f"Missing workflow contract surface: {ctx.normalize_path(path, root)}.")
            continue
        text = ctx.read_text(path)
        files.append(ctx.normalize_path(path, root))
        if expected_coordination not in text.lower():
            evidence.append(f"{ctx.normalize_path(path, root)} does not state that the team leader owns ticket_claim and ticket_release.")
        if prebootstrap_guard not in text:
            evidence.append(f"{ctx.normalize_path(path, root)} does not limit pre-bootstrap write claims to Wave 0 setup work.")

    if team_leader is None:
        files.append(".opencode/agents/*team-leader*.md")
        evidence.append("Missing team leader prompt; no canonical lease-owner guidance is available.")
    else:
        team_leader_text = ctx.read_text(team_leader)
        files.append(ctx.normalize_path(team_leader, root))
        if "grant a write lease with `ticket_claim` before any specialist writes planning, implementation, review, QA, or handoff artifact bodies or makes code changes" not in team_leader_text:
            evidence.append(f"{ctx.normalize_path(team_leader, root)} does not make the coordinator-owned lease model explicit before specialist work.")
        if "only Wave 0 setup work may claim a write-capable lease before bootstrap is ready" not in team_leader_text:
            evidence.append(f"{ctx.normalize_path(team_leader, root)} does not preserve the Wave 0-only pre-bootstrap claim rule.")

    worker_patterns = ("ticket_claim: allow", "ticket_release: allow", "claim the assigned ticket with `ticket_claim`", "release it with `ticket_release`")
    for path in (implementer, lane_executor, docs_handoff):
        if path is None:
            continue
        text = ctx.read_text(path)
        files.append(ctx.normalize_path(path, root))
        hits = [pattern for pattern in worker_patterns if pattern in text]
        if hits:
            evidence.append(f"{ctx.normalize_path(path, root)} still tells the specialist lane to claim or release its own lease: {', '.join(hits)}.")

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW012",
            severity="error",
            problem="The generated lease-ownership contract is split across coordinator and worker surfaces, so agents can disagree about who should claim a ticket and when bootstrap gates apply.",
            root_cause="Some workflow docs and prompts still describe worker-owned lease claims while others expect the team leader to coordinate claims. That contradiction is enough to make weaker models thrash around ticket ownership and pre-bootstrap write rules.",
            files=list(dict.fromkeys(files)),
            safer_pattern="Adopt one lease model everywhere: the team leader owns `ticket_claim` and `ticket_release`, specialists work only inside the already-active ticket lease, and only Wave 0 setup work may claim before bootstrap is ready.",
            evidence=evidence[:10],
            provenance="script",
        ),
    )


def audit_restart_tool_verification_metadata(
    root: Path, findings: list[Finding], ctx: RestartSurfaceAuditContext
) -> None:
    handoff_publish = root / ".opencode" / "tools" / "handoff_publish.ts"
    context_snapshot = root / ".opencode" / "tools" / "context_snapshot.ts"
    evidence: list[str] = []
    files: list[str] = []

    if handoff_publish.exists():
        handoff_text = ctx.read_text(handoff_publish)
        if "verified" not in handoff_text or "pending_process_verification" not in handoff_text:
            files.append(ctx.normalize_path(handoff_publish, root))
            evidence.append(
                f"{ctx.normalize_path(handoff_publish, root)} does not return verification metadata alongside published restart-surface paths."
            )
    else:
        files.append(ctx.normalize_path(handoff_publish, root))
        evidence.append("Missing handoff_publish tool, so restart-surface verification metadata cannot be emitted.")

    if context_snapshot.exists():
        snapshot_text = ctx.read_text(context_snapshot)
        if "snapshot_size_bytes" not in snapshot_text or "verified" not in snapshot_text:
            files.append(ctx.normalize_path(context_snapshot, root))
            evidence.append(
                f"{ctx.normalize_path(context_snapshot, root)} does not return verification metadata for the written snapshot."
            )
    else:
        files.append(ctx.normalize_path(context_snapshot, root))
        evidence.append("Missing context_snapshot tool, so snapshot verification metadata cannot be emitted.")

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW025",
            severity="error",
            problem="Restart-surface tools return paths without verifying what they wrote.",
            root_cause="When handoff and context tools only echo file paths, weaker models cannot tell whether the files were written correctly or still agree with canonical state after publication.",
            files=list(dict.fromkeys(files)),
            safer_pattern="Return verified flags plus current workflow metadata for published restart surfaces and include size or hash metadata for snapshots so callers can confirm what was written.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_resume_truth_hierarchy(root: Path, findings: list[Finding], ctx: RestartSurfaceAuditContext) -> None:
    resume = root / ".opencode" / "commands" / "resume.md"
    workflow_doc = root / "docs" / "process" / "workflow.md"
    tooling_doc = root / "docs" / "process" / "tooling.md"
    agents_doc = root / "AGENTS.md"
    readme = root / "README.md"
    latest_handoff = root / ".opencode" / "state" / "latest-handoff.md"
    manifest_path = root / "tickets" / "manifest.json"
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"

    evidence: list[str] = []
    files: list[str] = []
    for path in (manifest_path, workflow_path):
        if path.exists():
            files.append(ctx.normalize_path(path, root))

    if not resume.exists():
        files.append(ctx.normalize_path(resume, root))
        evidence.append(f"Missing resume command: {ctx.normalize_path(resume, root)}.")
    else:
        resume_text = ctx.read_text(resume)
        files.append(ctx.normalize_path(resume, root))
        if "Resume from `tickets/manifest.json` and `.opencode/state/workflow-state.json` first." not in resume_text:
            evidence.append(f"{ctx.normalize_path(resume, root)} does not make manifest + workflow-state the first-class resume source.")
        if ".opencode/state/latest-handoff.md" not in resume_text:
            evidence.append(f"{ctx.normalize_path(resume, root)} does not mention `.opencode/state/latest-handoff.md` as a derived restart surface.")
        if "Treat the active open ticket as the primary lane even when historical reverification is pending." not in resume_text:
            evidence.append(f"{ctx.normalize_path(resume, root)} does not preserve active open-ticket priority over backlog reverification.")

    if not latest_handoff.exists():
        files.append(ctx.normalize_path(latest_handoff, root))
        evidence.append(f"Missing derived restart surface: {ctx.normalize_path(latest_handoff, root)}.")
    else:
        files.append(ctx.normalize_path(latest_handoff, root))

    for path, required in (
        (workflow_doc, "open active-ticket work remains the primary foreground lane"),
        (tooling_doc, "`START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are derived restart surfaces"),
        (agents_doc, "`START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are derived restart surfaces"),
        (readme, "`START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are derived restart surfaces"),
    ):
        if not path.exists():
            files.append(ctx.normalize_path(path, root))
            evidence.append(f"Missing resume contract surface: {ctx.normalize_path(path, root)}.")
            continue
        text = ctx.read_text(path)
        files.append(ctx.normalize_path(path, root))
        if required not in text:
            evidence.append(f"{ctx.normalize_path(path, root)} does not encode the updated resume truth hierarchy.")

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW013",
            severity="error",
            problem="The generated resume contract still gives too much authority to derived handoff text or lets reverification obscure the active open ticket.",
            root_cause="When `/resume` and the surrounding docs do not put `tickets/manifest.json` plus `.opencode/state/workflow-state.json` first, weaker models start following stale restart text, ignore `.opencode/state/latest-handoff.md`, or abandon the active foreground ticket for historical reverification too early.",
            files=list(dict.fromkeys(files)),
            safer_pattern="Make manifest + workflow-state canonical for `/resume`, keep `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` derived-only, and preserve the active open ticket as the primary lane until it is resolved.",
            evidence=evidence[:10],
            provenance="script",
        ),
    )


def audit_invocation_log_coordinator_artifact_authorship(root: Path, findings: list[Finding], ctx: RestartSurfaceAuditContext) -> None:
    invocation_log = root / ".opencode" / "state" / "invocation-log.jsonl"
    events = ctx.parse_invocation_log_events(invocation_log)
    if not events:
        return

    evidence: list[str] = []
    for event in events:
        if getattr(event, "tool", "") != "artifact_write" or getattr(event, "event", "") != "tool.execute.before" or not isinstance(getattr(event, "args", None), dict):
            continue
        if not ctx.is_coordinator_assistant(getattr(event, "agent", "")):
            continue
        stage = str(event.args.get("stage", "")).strip()
        if stage not in COORDINATOR_ARTIFACT_STAGES:
            continue
        artifact_path = str(event.args.get("path", "")).strip()
        evidence.append(
            f"Invocation log line {getattr(event, 'line_number', '?')}: coordinator {getattr(event, 'agent', '') or 'unknown agent'} wrote `{stage}` artifact"
            + (f" at `{artifact_path}`." if artifact_path else ".")
        )

    if not evidence:
        return

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW014",
            severity="error",
            problem="The repo's current invocation log shows the coordinator writing specialist stage artifacts directly, so that stage evidence is suspect.",
            root_cause="Even after the workflow layer was generated, the coordinator still authored planning, implementation, review, QA, or smoke-test artifacts. That bypasses the specialist-lane ownership model and should not count as canonical proof of progression.",
            files=[ctx.normalize_path(invocation_log, root)],
            safer_pattern="Treat coordinator-authored specialist artifacts as suspect evidence, route remediation through the package contract and regenerated prompts, and rerun the affected stage through the owning specialist or deterministic tool.",
            evidence=evidence[:6],
            provenance="script",
        ),
    )


def audit_team_leader_workflow_contract(root: Path, findings: list[Finding], ctx: RestartSurfaceAuditContext) -> None:
    team_leader = next((path for path in (root / ".opencode" / "agents").glob("*team-leader*.md")), None)
    if not team_leader:
        return

    text = ctx.read_text(team_leader)
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

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW006",
            severity="warning",
            problem="The team leader prompt leaves workflow mechanics underspecified enough that weaker models can thrash or search for bypasses.",
            root_cause="Without explicit transition guidance, contradiction-stop behavior, artifact-ownership rules, and command boundaries, the coordinator has to infer the state machine and may start authoring artifacts or testing workaround transitions itself.",
            files=[ctx.normalize_path(team_leader, root)],
            safer_pattern="Tell the team leader to route from `ticket_lookup.transition_guidance`, stop after repeated lifecycle errors, leave stage artifacts to the owning specialist, and keep slash commands human-only.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_ticket_execution_skill_contract(root: Path, findings: list[Finding], ctx: RestartSurfaceAuditContext) -> None:
    skill_path = root / ".opencode" / "skills" / "ticket-execution" / "SKILL.md"
    if not skill_path.exists():
        return

    text = ctx.read_text(skill_path)
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

    ctx.add_finding(
        findings,
        Finding(
            code="SKILL002",
            severity="warning",
            problem="The repo-local `ticket-execution` skill is too thin to explain the actual lifecycle contract to weaker models.",
            root_cause="When the local workflow explainer omits transition guidance, contradiction-stop rules, artifact ownership, or command boundaries, agents fall back to guess-and-check against the tools.",
            files=[ctx.normalize_path(skill_path, root)],
            safer_pattern="Keep `ticket-execution` narrowly procedural: route from `ticket_lookup.transition_guidance`, stop after repeated lifecycle contradictions, reserve `smoke_test` as the only PASS producer, and keep slash commands human-only.",
            evidence=evidence,
            provenance="script",
        ),
    )


def audit_handoff_evidence_gap(root: Path, findings: list[Finding], ctx: RestartSurfaceAuditContext) -> None:
    manifest_path = root / "tickets" / "manifest.json"
    workflow_path = root / ".opencode" / "state" / "workflow-state.json"
    start_here = root / "START-HERE.md"
    latest_handoff = root / ".opencode" / "state" / "latest-handoff.md"
    manifest = ctx.read_json(manifest_path)
    workflow = ctx.read_json(workflow_path)
    if not isinstance(manifest, dict) or not isinstance(workflow, dict):
        return

    active_ticket = ctx.active_ticket(manifest, workflow)
    if not isinstance(active_ticket, dict):
        return

    combined = ctx.combine_outputs(ctx.read_text(start_here), ctx.read_text(latest_handoff))
    if not any(re.search(pattern, combined, re.IGNORECASE) for pattern in HANDOFF_OVERCLAIM_PATTERNS):
        return

    blocked_dependents = ctx.blocked_dependents(manifest, str(active_ticket.get("id", "")))
    active_status = str(active_ticket.get("status", "")).strip()
    if active_status == "done" and not blocked_dependents:
        return

    evidence: list[str] = []
    if active_status and active_status != "done":
        evidence.append(f"Active ticket {active_ticket.get('id')} is still `{active_status}`, not `done`.")
    if blocked_dependents:
        evidence.append(f"Dependent tickets still waiting on the active ticket: {', '.join(blocked_dependents)}.")
    evidence.extend(ctx.matching_lines(combined, HANDOFF_OVERCLAIM_PATTERNS))

    ctx.add_finding(
        findings,
        Finding(
            code="WFLOW002",
            severity="error",
            problem="Published handoff text overstates repo readiness or root cause beyond the executed evidence and current dependency state.",
            root_cause="The handoff contract allows free-form next-action text to claim dependency unblocking or single-cause explanations even when the active ticket is not done and downstream tickets remain blocked.",
            files=[
                ctx.normalize_path(start_here, root),
                ctx.normalize_path(latest_handoff, root),
                ctx.normalize_path(manifest_path, root),
                ctx.normalize_path(workflow_path, root),
            ],
            safer_pattern="Block handoff publication when custom next-action text claims dependency readiness, `only blocker`, or `not a code defect` without matching executed evidence and current manifest/workflow state.",
            evidence=evidence[:6],
            provenance="script",
        ),
    )


def run_restart_surface_audits(root: Path, findings: list[Finding], ctx: RestartSurfaceAuditContext) -> None:
    audit_restart_surface_drift(root, findings, ctx)
    audit_legacy_repair_gate_leak(root, findings, ctx)
    audit_bootstrap_guidance_drift(root, findings, ctx)
    audit_restart_tool_verification_metadata(root, findings, ctx)
    audit_lease_claim_guidance_drift(root, findings, ctx)
    audit_resume_truth_hierarchy(root, findings, ctx)
    audit_invocation_log_coordinator_artifact_authorship(root, findings, ctx)
    audit_team_leader_workflow_contract(root, findings, ctx)
    audit_ticket_execution_skill_contract(root, findings, ctx)
    audit_handoff_evidence_gap(root, findings, ctx)
