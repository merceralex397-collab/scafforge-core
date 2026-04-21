from __future__ import annotations

import json
import os
import subprocess
import tempfile
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from disposition_bundle import (
    bundle_source_follow_up_codes,
    build_disposition_bundle,
    defect_label_for_class,
    evidence_grade_for_finding,
    repo_has_godot_smoke_guard,
)
from shared_verifier_types import Finding


DIAGNOSIS_REPORTS = {
    "report_1": "01-initial-codebase-review.md",
    "report_2": "02-scafforge-process-failures.md",
    "report_3": "03-scafforge-prevention-actions.md",
    "report_4": "04-live-repo-repair-plan.md",
}

# Package provenance should track package code and contract surfaces, not the
# mutable downstream repos and proof artifacts that happen to live under the
# Scafforge worktree.  Otherwise a managed-repair run against
# `livetesting/<repo>` changes the package dirty fingerprint mid-cycle even when
# no package code changed.
PACKAGE_PROVENANCE_EXCLUDES = (
    "active-audits",
    "active-plans",
    "archive",
    "livetesting",
    "reports",
)


@dataclass(frozen=True)
class AuditReportingContext:
    package_root: Path
    current_package_commit: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def normalize_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def path_is_writable(path: Path) -> bool:
    parent = path if path.exists() and path.is_dir() else path.parent
    while not parent.exists():
        parent = parent.parent
    return parent.is_dir() and os_access_writable(parent)


def os_access_writable(path: Path) -> bool:
    import os

    return os.access(path, os.W_OK)


def severity_rank(severity: str) -> int:
    return {"error": 0, "warning": 1, "info": 2}.get(severity, 3)


def findings_by_severity(findings: list[Finding]) -> dict[str, list[Finding]]:
    grouped: dict[str, list[Finding]] = {"error": [], "warning": [], "info": []}
    for finding in sorted(findings, key=lambda item: (severity_rank(item.severity), item.code)):
        grouped.setdefault(finding.severity, []).append(finding)
    return grouped


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


def infer_surface(finding: Finding) -> str:
    joined = " ".join(finding.files)
    if finding.code.startswith("SESSION"):
        return "scafforge-audit transcript chronology and causal diagnosis surfaces"
    if finding.code.startswith("REF"):
        return "generated repo reference integrity and configuration surfaces"
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
    if finding.code == "WFLOW025":
        return "Extend the target-completion contract so declared Godot Android repos always get canonical `ANDROID-001` and `RELEASE-001` backlog ownership instead of leaving Android delivery buried in generic polish work."
    if finding.code == "WFLOW033":
        return "When `issue_intake` invalidates a ticket because the accepted contract is wrong or imprecise, require `ticket_update(acceptance=[...], summary=\"...\")` for the stale canonical fields, persist an acceptance-refresh artifact, and treat missing canonical refresh as repo-owned follow-up once the installed workflow supports it."
    if finding.code == "WFLOW034":
        return "Create open-parent remediation follow-up tickets as `split_scope + parallel_independent`, keep `issue_intake` reserved for completed historical tickets, and audit the parent-FAIL plus sequential-child deadlock before live runs stall on it."
    if finding.code == "WFLOW035":
        return "Publish a canonical current-cycle handoff proof into workflow state, make restart surfaces render that proof truthfully, and reject ready/complete claims that outrun failed or missing proof."
    if finding.code == "WFLOW026":
        return "Teach the shared artifact verdict extractor to accept markdown-emphasized labels, compact `## QA PASS` / `## Review APPROVE` headings, `## Decision` headings with the verdict on the next line, and plain `**Overall**: PASS` labels, then route ticket_lookup and ticket_update through that single parser."
    if finding.code == "WFLOW027":
        return "Return verification metadata from restart-surface tools so callers can confirm what handoff and snapshot publication actually wrote."
    if finding.code == "WFLOW028":
        return "Remove the global split-scope completion invariant from workflow.ts validateTicketGraphInvariants so sequential-dependent split children can exist alongside completed parents, then install the fix via scafforge-repair."
    if finding.code == "WFLOW032":
        return "Tighten bootstrap ticket generation and review guidance so product-spine tickets cannot normalize shallow shells, justified stubs, or deferred runtime behavior."
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
    if finding.code == "SESSION008":
        return "Teach scafforge-audit to treat transcript-backed clearable pending_process_verification cleanup failures as managed workflow defects, and let ticket_update clear that flag without re-running stage-entry validation on the current ticket."
    if finding.code == "BOOT001":
        return "Make generated Python bootstrap manager-aware (`uv` or repo-local `.venv`), classify missing prerequisites accurately, and audit bootstrap deadlocks before routing source remediation."
    if finding.code == "BOOT002":
        return "Correlate `pyproject.toml`, bootstrap artifacts, and `environment_bootstrap.ts` so uv-managed repos with extras or dependency groups emit a managed bootstrap defect instead of an operator-only rerun recommendation."
    if finding.code == "SKILL001":
        return "Detect and repair leftover placeholder local skills so generated stack guidance is concrete before implementation continues."
    if finding.code == "SKILL002":
        return "Make the generated `ticket-execution` skill the canonical lifecycle explainer so weaker models do not have to reverse-engineer the state machine from tool errors."
    if finding.code == "SKILL003":
        return "When asset-pipeline metadata requires Blender-MCP, keep the required Blender skills, dedicated Blender agent, and managed `blender_agent` MCP entry aligned so the repo can actually follow the declared asset route."
    if finding.code == "MODEL001":
        return "Detect deprecated or missing model-profile surfaces, treat stale package-managed defaults as safe repair instead of preserved intent, regenerate the repo-local model operating profile, and align model metadata plus agent defaults before development resumes."
    if finding.code == "CYCLE001":
        return "Teach audit to inspect the previous diagnosis, the latest repair transaction outcome, and the final publish gate before allowing another managed-repair run to proceed."
    if finding.code == "CYCLE002":
        return "Teach audit to stop repeated diagnosis-pack churn when the repo has no newer package or process-version change; require Scafforge package work before the next subject-repo audit."
    if finding.code == "CYCLE003":
        return "Make repair verification inherit the transcript-backed diagnosis basis automatically, keep the final publish gate tied to that basis, emit the post-repair diagnosis pack from the repair runner, and refuse to call the repo clean on current-state evidence alone."
    if finding.code == "EXEC-RUNTIME-001":
        return "Detect explicit TODO, placeholder-response, and stub-integration markers in repo-owned runtime sources once tickets start closing, and require a runnable vertical slice before review, QA, or release proof can call those paths complete."
    if finding.code.startswith("EXEC"):
        return "Tighten generated review and QA guidance so runtime validation and test collection proof exist before closure."
    if finding.code.startswith("REF"):
        return "Add reference-integrity checks and keep engine, config, and local-import paths aligned with real repo files before diagnosis or handoff treats the project as runnable."
    if "ticket" in finding.code or "status" in finding.code:
        return "Keep queue state coarse, route remediation through guarded ticket flows, and validate ticket-contract wording in package checks."
    if any(token in " ".join(finding.files) for token in (".opencode/agents/", ".opencode/skills/")):
        return "Harden generated prompts so read-only roles stay read-only and repo-local review guidance remains advisory."
    return "Refresh managed workflow docs, tools, and validators together so repair replaces drift instead of layering new semantics over old ones."


def package_has_wflow024_fix(ctx: AuditReportingContext) -> bool:
    package = ctx.package_root
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


def package_has_target_completion_fix(ctx: AuditReportingContext) -> bool:
    package = ctx.package_root
    verifier = read_text(package / "skills" / "scafforge-audit" / "scripts" / "shared_verifier.py")
    ticket_graph = read_text(package / "skills" / "scafforge-audit" / "scripts" / "audit_ticket_graph.py")
    bootstrap = read_text(package / "skills" / "repo-scaffold-factory" / "assets" / "project-template" / ".opencode" / "tools" / "environment_bootstrap.ts")
    repair_follow_up = read_text(package / "skills" / "ticket-pack-builder" / "scripts" / "apply_remediation_follow_up.py")
    return (
        "VERIFY012" in verifier
        and "WFLOW025" in ticket_graph
        and "repoTargetsGodotAndroid" in bootstrap
        and "ANDROID_EXPORT_TICKET_ID" in repair_follow_up
        and "ANDROID_RELEASE_TICKET_ID" in repair_follow_up
    )


def package_has_acceptance_refresh_fix(ctx: AuditReportingContext) -> bool:
    package = ctx.package_root
    workflow_lib = read_text(package / "skills" / "repo-scaffold-factory" / "assets" / "project-template" / ".opencode" / "lib" / "workflow.ts")
    issue_intake = read_text(package / "skills" / "repo-scaffold-factory" / "assets" / "project-template" / ".opencode" / "tools" / "issue_intake.ts")
    ticket_update = read_text(package / "skills" / "repo-scaffold-factory" / "assets" / "project-template" / ".opencode" / "tools" / "ticket_update.ts")
    team_leader = read_text(package / "skills" / "repo-scaffold-factory" / "assets" / "project-template" / ".opencode" / "agents" / "__AGENT_PREFIX__-team-leader.md")
    contract_surfaces = read_text(package / "skills" / "scafforge-audit" / "scripts" / "audit_contract_surfaces.py")
    return (
        "needs_acceptance_refresh" in workflow_lib
        and "acceptanceRefreshRequired" in issue_intake
        and "needs_acceptance_refresh" in issue_intake
        and 'kind: "acceptance-refresh"' in ticket_update
        and "needs_acceptance_refresh" in ticket_update
        and "ticket_update(acceptance=[...])" in team_leader
        and 'code="WFLOW033"' in contract_surfaces
    )


def repo_has_acceptance_refresh_fix(root: Path) -> bool:
    workflow_lib = read_text(root / ".opencode" / "lib" / "workflow.ts")
    issue_intake = read_text(root / ".opencode" / "tools" / "issue_intake.ts")
    ticket_update = read_text(root / ".opencode" / "tools" / "ticket_update.ts")
    team_leader_candidates = list((root / ".opencode" / "agents").glob("*team-leader.md"))
    team_leader = read_text(team_leader_candidates[0]) if team_leader_candidates else ""
    return (
        "needs_acceptance_refresh" in workflow_lib
        and "acceptanceRefreshRequired" in issue_intake
        and "needs_acceptance_refresh" in issue_intake
        and 'kind: "acceptance-refresh"' in ticket_update
        and "needs_acceptance_refresh" in ticket_update
        and "ticket_update(acceptance=[...])" in team_leader
    )


def package_has_verdict_parser_fix(ctx: AuditReportingContext) -> bool:
    workflow_lib = read_text(
        ctx.package_root
        / "skills"
        / "repo-scaffold-factory"
        / "assets"
        / "project-template"
        / ".opencode"
        / "lib"
        / "workflow.ts"
    )
    normalized_workflow_lib = workflow_lib.replace("\\\\", "\\")
    lifecycle_audit = read_text(ctx.package_root / "skills" / "scafforge-audit" / "scripts" / "audit_lifecycle_contracts.py")
    parser_supports_extended_verdict_labels = (
        "ARTIFACT_VERDICT_LABEL_PATTERN" in workflow_lib
        and "const labeled = plain.match(" in workflow_lib
        and "const headingInline = plain.match(" in workflow_lib
        and "const compactStageHeading = plain.match(" in workflow_lib
        and "overall(?:\\s+qa)?(?:\\s+(?:result|verdict))?" in normalized_workflow_lib
        and "qa\\s+(?:result|verdict)" in normalized_workflow_lib
        and "review\\s+(?:result|verdict)" in normalized_workflow_lib
        and "blocker\\s+or\\s+approval\\s+signal|approval\\s+signal|decision|verdict|result"
        in normalized_workflow_lib
        and "(?:(?:qa|review))\\s+(pass|fail|reject|approved?|blocked?|blocker)\\b" in normalized_workflow_lib
    )
    return parser_supports_extended_verdict_labels and "WFLOW026" in lifecycle_audit


def package_has_bootstrap_freshness_fix(ctx: AuditReportingContext) -> bool:
    workflow_lib = read_text(
        ctx.package_root
        / "skills"
        / "repo-scaffold-factory"
        / "assets"
        / "project-template"
        / ".opencode"
        / "lib"
        / "workflow.ts"
    )
    return (
        "BOOTSTRAP_ENVIRONMENT_KEYS" in workflow_lib
        and "describeBootstrapFingerprintInputs" in workflow_lib
        and "host_paths" in workflow_lib
    )


def package_has_godot_smoke_fix(ctx: AuditReportingContext) -> bool:
    smoke_tool = read_text(
        ctx.package_root
        / "skills"
        / "repo-scaffold-factory"
        / "assets"
        / "project-template"
        / ".opencode"
        / "tools"
        / "smoke_test.ts"
    )
    return (
        "Could not parse global class" in smoke_tool
        and "Could not resolve class" in smoke_tool
        and "isGodotFatalDiagnosticOutput(output) || isSyntaxErrorOutput(output)" in smoke_tool
    )


def package_has_remediation_verdict_decoration_fix(ctx: AuditReportingContext) -> bool:
    workflow_lib = read_text(
        ctx.package_root
        / "skills"
        / "repo-scaffold-factory"
        / "assets"
        / "project-template"
        / ".opencode"
        / "lib"
        / "workflow.ts"
    )
    lifecycle_audit = read_text(ctx.package_root / "skills" / "scafforge-audit" / "scripts" / "audit_lifecycle_contracts.py")
    return "✅" in workflow_lib and "✅" in lifecycle_audit


def package_has_split_scope_deadlock_fix(ctx: AuditReportingContext) -> bool:
    workflow_lib = read_text(
        ctx.package_root
        / "skills"
        / "repo-scaffold-factory"
        / "assets"
        / "project-template"
        / ".opencode"
        / "lib"
        / "workflow.ts"
    )
    ticket_graph_audit = read_text(ctx.package_root / "skills" / "scafforge-audit" / "scripts" / "audit_ticket_graph.py")
    # Fix is present when BOTH bad substrings are absent from the template AND WFLOW028 detection is present.
    # Require both substrings absent — absence of just one could be a message/comment rewrite, not a real fix.
    has_no_deadlock_throw = (
        "Split-scope child" not in workflow_lib
        and "cannot point at a completed source ticket" not in workflow_lib
    )
    has_wflow028_detection = "WFLOW028" in ticket_graph_audit
    return has_no_deadlock_throw and has_wflow028_detection


def build_ticket_recommendations(findings: list[Finding], ctx: AuditReportingContext, root: Path) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    wflow024_package_fix_available = package_has_wflow024_fix(ctx)
    target_completion_fix_available = package_has_target_completion_fix(ctx)
    acceptance_refresh_fix_available = package_has_acceptance_refresh_fix(ctx)
    repo_acceptance_refresh_fix_available = repo_has_acceptance_refresh_fix(root)
    verdict_parser_fix_available = package_has_verdict_parser_fix(ctx)
    bootstrap_freshness_fix_available = package_has_bootstrap_freshness_fix(ctx)
    godot_smoke_fix_available = package_has_godot_smoke_fix(ctx)
    remediation_decoration_fix_available = package_has_remediation_verdict_decoration_fix(ctx)
    split_scope_deadlock_fix_available = package_has_split_scope_deadlock_fix(ctx)
    grouped_follow_up: dict[str, list[Finding]] = {}
    remediation_pool, existing_ids = _load_existing_remediation_ticket_pool(root)
    used_ids: set[str] = set()
    for finding in sorted(findings, key=lambda item: (severity_rank(item.severity), item.code)):
        if finding.code in {"BOOT001", "BOOT002"}:
            route = "scafforge-repair"
            repair_class = "safe Scafforge package change"
        elif finding.code == "BOOT003":
            if bootstrap_freshness_fix_available:
                route = "scafforge-repair"
                repair_class = "safe Scafforge package change"
            else:
                route = "manual-prerequisite"
                repair_class = "Scafforge package work required before the next subject-repo repair run"
        elif finding.code.startswith("ENV"):
            route = "manual-prerequisite"
            repair_class = "Host prerequisite or operator environment fix required before the next subject-repo run"
        elif finding.code == "EXEC-GODOT-006":
            if repo_has_godot_smoke_guard(root):
                route = "ticket-pack-builder"
                repair_class = "generated-repo remediation ticket"
            elif godot_smoke_fix_available:
                route = "scafforge-repair"
                repair_class = "safe Scafforge package change"
            else:
                route = "manual-prerequisite"
                repair_class = "Scafforge package work required before the next subject-repo repair run"
        elif finding.code == "EXEC-REMED-001":
            route = "ticket-pack-builder"
            repair_class = "generated-repo remediation ticket"
        elif finding.code.startswith(("SESSION", "SKILL", "MODEL")):
            route = "scafforge-repair"
            repair_class = "safe Scafforge package change"
        elif finding.code.startswith(("EXEC", "REF")):
            route = "ticket-pack-builder"
            repair_class = "generated-repo remediation ticket"
        elif finding.code == "WFLOW024":
            if wflow024_package_fix_available:
                route = "scafforge-repair"
                repair_class = "safe Scafforge package change"
            else:
                route = "manual-prerequisite"
                repair_class = "Scafforge package work required before the next subject-repo repair run"
        elif finding.code == "WFLOW025":
            if target_completion_fix_available:
                route = "scafforge-repair"
                repair_class = "safe Scafforge package change"
            else:
                route = "manual-prerequisite"
                repair_class = "Scafforge package work required before the next subject-repo repair run"
        elif finding.code == "WFLOW033":
            if repo_acceptance_refresh_fix_available:
                route = "ticket-pack-builder"
                repair_class = "generated-repo remediation ticket"
            elif acceptance_refresh_fix_available:
                route = "scafforge-repair"
                repair_class = "safe Scafforge package change"
            else:
                route = "manual-prerequisite"
                repair_class = "Scafforge package work required before the next subject-repo repair run"
        elif finding.code == "WFLOW026":
            if verdict_parser_fix_available:
                route = "scafforge-repair"
                repair_class = "safe Scafforge package change"
            else:
                route = "manual-prerequisite"
                repair_class = "Scafforge package work required before the next subject-repo repair run"
        elif finding.code == "WFLOW028":
            if split_scope_deadlock_fix_available:
                route = "scafforge-repair"
                repair_class = "safe Scafforge package change"
            else:
                route = "manual-prerequisite"
                repair_class = "Scafforge package work required before the next subject-repo repair run"
        elif finding.code.startswith("CYCLE"):
            route = "manual-prerequisite"
            repair_class = "Scafforge package work required before the next subject-repo run"
        else:
            route = "scafforge-repair"
            repair_class = "safe Scafforge package change"

        if route == "ticket-pack-builder" and finding.severity == "warning":
            grouped_follow_up.setdefault(infer_surface(finding), []).append(finding)
            continue

        summary = recommendation_summary_for_finding(finding)
        signature = _recommendation_signature(
            source_finding_code=finding.code,
            title=summary["title"],
            affected_files=summary["affected_files"],
        )
        reusable_ids = remediation_pool.get(signature, [])
        recommendation_id = next((ticket_id for ticket_id in reusable_ids if ticket_id not in used_ids), None)
        if recommendation_id is None:
            recommendation_id = _next_free_remed_id(existing_ids, used_ids)
        used_ids.add(recommendation_id)
        recommendations.append(
            {
                "id": recommendation_id,
                **summary,
                "source_finding_code": finding.code,
                "source_finding_codes": [finding.code],
                "severity": finding.severity,
                "route": route,
                "repair_class": repair_class,
                "summary": finding.safer_pattern,
                "source_files": finding.files,
                "affected_files": summary["affected_files"],
                "suggested_fix_approach": summary["suggested_fix_approach"],
                "assignee": summary["assignee"],
                "description": summary["description"],
            }
        )

    for surface, grouped in sorted(grouped_follow_up.items(), key=lambda item: item[0]):
        all_files = sorted({path for finding in grouped for path in finding.files})
        codes = [finding.code for finding in grouped]
        recommendation_id = _next_free_remed_id(existing_ids, used_ids)
        used_ids.add(recommendation_id)
        recommendations.append(
            {
                "id": recommendation_id,
                "title": f"Batch remediate {surface}",
                "description": f"Resolve the related validated warning-level findings for {surface} and rerun the affected quality checks together.",
                "source_finding_code": codes[0],
                "source_finding_codes": codes,
                "severity": "warning",
                "route": "ticket-pack-builder",
                "repair_class": "generated-repo remediation ticket",
                "summary": f"Batch the related warning-level findings for {surface} into one remediation ticket instead of fragmenting the queue.",
                "source_files": all_files,
                "affected_files": all_files,
                "suggested_fix_approach": "Rerun the relevant build, lint, reference-integrity, and verification commands after fixing the grouped findings.",
                "assignee": "implementer",
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


def recommended_next_step(
    findings: list[Finding],
    recommendations: list[dict[str, Any]],
    disposition_bundle: dict[str, Any] | None = None,
) -> str:
    # WFLOW030 = managed_blocked deadlock with only host-only stages unresolved.
    # Running repair again would re-trigger the broad WFLOW trigger and deepen
    # the deadlock.  The correct action is host intervention, not another repair.
    if any(getattr(f, "code", "") == "WFLOW030" for f in findings):
        return "host_intervention_required"
    if package_work_required_first(recommendations):
        return "scafforge_package_work"
    if isinstance(disposition_bundle, dict):
        bundle_findings = disposition_bundle.get("findings")
        if isinstance(bundle_findings, list):
            classes = {
                str(item.get("disposition_class", "")).strip()
                for item in bundle_findings
                if isinstance(item, dict)
            }
            if "manual_prerequisite_blocker" in classes:
                return "host_intervention_required"
            if "managed_blocker" in classes:
                return "subject_repo_repair"
            if "source_follow_up" in classes or findings:
                return "subject_repo_source_follow_up"
            return "done"
    routes = {str(item.get("route", "")).strip() for item in recommendations if isinstance(item, dict)}
    if "manual-prerequisite" in routes:
        return "host_intervention_required"
    if "scafforge-repair" in routes:
        return "subject_repo_repair"
    if "ticket-pack-builder" in routes or findings:
        return "subject_repo_source_follow_up"
    return "done"


def diagnosis_result_state(findings: list[Finding]) -> str:
    return "validated failures found" if findings else "no validated failures found"


def evidence_grade(finding: Finding) -> str:
    return evidence_grade_for_finding(finding)


def ownership_classification(finding: Finding) -> str:
    if finding.code.startswith("ENV"):
        return "host prerequisite or package boundary"
    if finding.code.startswith(("BOOT", "REF")):
        return "generated repo source and configuration surfaces"
    if finding.code.startswith("EXEC"):
        return "generated repo execution surface"
    if finding.code.startswith(("SKILL", "MODEL")):
        return "project skill or prompt surface"
    if finding.code.startswith(("SESSION", "CYCLE")):
        return "audit and lifecycle diagnosis surface"
    return "managed workflow contract surface"


def recommendation_linked_codes(item: dict[str, Any]) -> str:
    linked = item.get("source_finding_codes")
    if isinstance(linked, list) and linked:
        return ", ".join(str(code) for code in linked)
    return str(item.get("source_finding_code", "unknown"))


def recommendation_source_codes(item: dict[str, Any]) -> list[str]:
    linked = item.get("source_finding_codes")
    if isinstance(linked, list) and linked:
        return [str(code).strip() for code in linked if str(code).strip()]
    code = str(item.get("source_finding_code", "")).strip()
    return [code] if code else []


def disposition_lookup(bundle: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(bundle, dict):
        return {}
    findings = bundle.get("findings")
    if not isinstance(findings, list):
        return {}
    lookup: dict[str, str] = {}
    for item in findings:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code", "")).strip()
        disposition_class = str(item.get("disposition_class", "")).strip()
        if code and disposition_class:
            lookup[code] = disposition_class
    return lookup


def recommendation_disposition_class(item: dict[str, Any], bundle: dict[str, Any] | None) -> str:
    lookup = disposition_lookup(bundle)
    linked_classes = [lookup.get(code) for code in recommendation_source_codes(item) if lookup.get(code)]
    if "manual_prerequisite_blocker" in linked_classes:
        return "manual_prerequisite_blocker"
    if "managed_blocker" in linked_classes:
        return "managed_blocker"
    if "source_follow_up" in linked_classes:
        return "source_follow_up"
    if "process_state_only" in linked_classes:
        return "process_state_only"
    route = str(item.get("route", "")).strip()
    if route == "manual-prerequisite":
        return "manual_prerequisite_blocker"
    if route == "ticket-pack-builder":
        return "source_follow_up"
    return "managed_blocker" if route == "scafforge-repair" else "advisory"


def recommendation_defect_scope(item: dict[str, Any], bundle: dict[str, Any] | None) -> str:
    return defect_label_for_class(recommendation_disposition_class(item, bundle))


def recommendation_summary_for_finding(finding: Finding) -> dict[str, Any]:
    return {
        "title": finding.problem.rstrip("."),
        "description": f"Remediate {finding.code} by correcting the validated issue and rerunning the relevant quality checks.",
        "affected_files": finding.files,
        "suggested_fix_approach": finding.safer_pattern,
        "assignee": "implementer",
    }


_REMED_ID_RE = re.compile(r"^REMED-(\d{3,})$")
_REPAIR_CANDIDATE_RE = re.compile(r"^/tmp/scafforge-repair-candidate-[^/]+/candidate/?")


def _normalize_recommendation_surface(value: str) -> str:
    normalized = str(value).strip().replace("\\", "/")
    if not normalized:
        return ""
    return _REPAIR_CANDIDATE_RE.sub("candidate/", normalized)


def _extract_ticket_summary_surfaces(summary: str) -> tuple[str, ...]:
    marker = "Affected surfaces:"
    if marker not in summary:
        return ()
    tail = summary.split(marker, 1)[1]
    end_index = len(tail)
    for stop_marker in (". Historical evidence sources:", " Historical evidence sources:"):
        index = tail.find(stop_marker)
        if index != -1:
            end_index = min(end_index, index)
    surface_block = tail[:end_index].strip().rstrip(".")
    if not surface_block:
        return ()
    return tuple(
        item
        for item in (_normalize_recommendation_surface(part) for part in surface_block.split(","))
        if item
    )


def _load_existing_remediation_ticket_pool(root: Path) -> tuple[dict[tuple[str, str, tuple[str, ...]], list[str]], set[str]]:
    manifest_path = root / "tickets" / "manifest.json"
    if not manifest_path.exists():
        return {}, set()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}, set()
    tickets = manifest.get("tickets") if isinstance(manifest, dict) else None
    if not isinstance(tickets, list):
        return {}, set()

    pool: dict[tuple[str, str, tuple[str, ...]], list[str]] = {}
    existing_ids: set[str] = set()
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        ticket_id = str(ticket.get("id", "")).strip()
        if ticket_id:
            existing_ids.add(ticket_id)
        if str(ticket.get("lane", "")).strip() != "remediation":
            continue
        if ticket.get("status") == "done" or str(ticket.get("resolution_state", "")).strip() == "superseded":
            continue
        finding_source = str(ticket.get("finding_source", "")).strip()
        title = str(ticket.get("title", "")).strip()
        if not finding_source or not title:
            continue
        signature = (
            finding_source,
            title,
            _extract_ticket_summary_surfaces(str(ticket.get("summary", ""))),
        )
        pool.setdefault(signature, []).append(ticket_id)
    for ticket_ids in pool.values():
        ticket_ids.sort()
    return pool, existing_ids


def _recommendation_signature(
    *,
    source_finding_code: str,
    title: str,
    affected_files: list[str],
) -> tuple[str, str, tuple[str, ...]]:
    return (
        source_finding_code.strip(),
        title.strip(),
        tuple(
            item
            for item in (_normalize_recommendation_surface(path) for path in affected_files)
            if item
        ),
    )


def _next_free_remed_id(existing_ids: set[str], used_ids: set[str]) -> str:
    highest = 0
    for ticket_id in existing_ids | used_ids:
        match = _REMED_ID_RE.match(ticket_id)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"REMED-{highest + 1:03d}"


def validation_target_for_finding(finding: Finding) -> str:
    if finding.code in {"EXEC-GODOT-013", "EXEC-GODOT-014", "EXEC-GODOT-015", "WFLOW035"}:
        return "rerun contract validation, smoke, integration coverage, and the curated womanvshorse/spinner downstream fixture families"
    if finding.code.startswith("EXEC"):
        return "rerun the generated-tool execution smoke coverage plus the relevant GPTTalker fixture family"
    if finding.code.startswith("ENV"):
        return "rerun contract validation and host-sensitive smoke coverage on a host with the required prerequisites available"
    if finding.code.startswith("SESSION"):
        return "rerun transcript-backed audit coverage plus the related curated GPTTalker fixture family"
    return "rerun contract validation, smoke, and integration coverage for the affected managed surfaces"


def render_report_one(root: Path, findings: list[Finding], generated_at: str, logs: list[Path]) -> str:
    grouped = findings_by_severity(findings)
    result_state = diagnosis_result_state(findings)
    workflow_findings = [finding for finding in findings if not finding.code.startswith(("EXEC", "REF"))]
    code_quality_findings = [finding for finding in findings if finding.code.startswith(("EXEC", "REF"))]
    lines = [
        "# Initial Codebase Review",
        "",
        "## Scope",
        "",
        f"- subject repo: {root}",
        f"- diagnosis timestamp: {generated_at}",
        "- audit scope: managed workflow, restart, ticket, prompt, and execution surfaces",
        f"- verification scope: {'current repo state plus supporting logs' if logs else 'current repo state only'}",
        "",
        "## Result State",
        "",
        f"- result_state: {result_state}",
        f"- finding_count: {len(findings)}",
        f"- errors: {len(grouped.get('error', []))}",
        f"- warnings: {len(grouped.get('warning', []))}",
        "",
        "## Validated Findings",
        "",
        "### Workflow Findings",
        "",
    ]
    if not findings:
        lines.extend(
            [
                "No validated workflow, review, runtime, environment, or process findings were detected.",
                "",
                "## Verification Gaps",
                "",
                "- No additional verification gaps were identified during this diagnosis pass.",
                "",
            ]
        )
        if logs:
            lines.extend(
                [
                    "## Rejected or Outdated External Claims",
                    "",
                    "- None recorded. Supporting logs did not add any contradicted external claim beyond the validated finding set.",
                    "",
                ]
            )
        return "\n".join(lines)

    if not workflow_findings:
        lines.extend(["No validated workflow, environment, or managed-process findings were detected.", ""])
    for finding in sorted(workflow_findings, key=lambda item: (severity_rank(item.severity), item.code)):
        lines.extend(
            [
                f"### {finding.code}",
                "",
                f"- finding_id: {finding.code}",
                f"- summary: {finding.problem}",
                f"- severity: {finding.severity}",
                f"- evidence_grade: {evidence_grade(finding)}",
                f"- affected_files_or_surfaces: {', '.join(finding.files) if finding.files else '(none)'}",
                f"- observed_or_reproduced: {finding.root_cause}",
                "- evidence:",
                *([f"  - {item}" for item in finding.evidence] or ["  - No extra evidence lines were recorded beyond the validated repo state."]),
                "- remaining_verification_gap: None recorded beyond the validated finding scope.",
                "",
            ]
        )
    lines.extend(["## Code Quality Findings", ""])
    if not code_quality_findings:
        lines.extend(["No execution or reference-integrity findings were detected.", ""])
    for finding in sorted(code_quality_findings, key=lambda item: (severity_rank(item.severity), item.code)):
        severity_label = "CRITICAL" if finding.code.startswith("EXEC") and finding.severity == "error" else "HIGH" if finding.code.startswith("REF") else finding.severity.upper()
        lines.extend(
            [
                f"### {finding.code}",
                "",
                f"- finding_id: {finding.code}",
                f"- summary: {finding.problem}",
                f"- severity: {severity_label}",
                f"- evidence_grade: {evidence_grade(finding)}",
                f"- affected_files_or_surfaces: {', '.join(finding.files) if finding.files else '(none)'}",
                f"- observed_or_reproduced: {finding.root_cause}",
                "- evidence:",
                *([f"  - {item}" for item in finding.evidence] or ["  - No extra evidence lines were recorded beyond the validated repo state."]),
                "",
            ]
        )
    lines.extend(
        [
            "## Verification Gaps",
            "",
            "- The diagnosis pack validates the concrete failures above. It does not claim broader runtime-path coverage than the current audit and supporting evidence actually exercised.",
            "",
        ]
    )
    if logs:
        lines.extend(
            [
                "## Rejected or Outdated External Claims",
                "",
                "- None recorded separately. Supporting logs were incorporated into the validated findings above instead of being left as standalone unverified claims.",
                "",
            ]
        )
    return "\n".join(lines)


def render_report_two(findings: list[Finding]) -> str:
    lines = [
        "# Scafforge Process Failures",
        "",
        "## Scope",
        "",
        "- Maps each validated finding back to the Scafforge-owned workflow surface that allowed it through.",
        "",
    ]
    if not findings:
        lines.extend(["## Failure Map", "", "- No process failures were mapped from the validated finding set.", "", "## Ownership Classification", "", "- None recorded.", "", "## Root Cause Analysis", "", "- None recorded.", ""])
        return "\n".join(lines)

    lines.extend(["## Failure Map", ""])
    for finding in sorted(findings, key=lambda item: (severity_rank(item.severity), item.code)):
        lines.extend(
            [
                f"### {finding.code}",
                "",
                f"- linked_report_1_finding: {finding.code}",
                f"- implicated_surface: {infer_surface(finding)}",
                f"- ownership_class: {ownership_classification(finding)}",
                f"- workflow_failure: {finding.problem}",
                "",
            ]
        )
    lines.extend(["## Ownership Classification", ""])
    for finding in sorted(findings, key=lambda item: (ownership_classification(item), item.code)):
        lines.extend(
            [
                f"### {finding.code}",
                "",
                f"- ownership_class: {ownership_classification(finding)}",
                f"- affected_surface: {infer_surface(finding)}",
                "",
            ]
        )
    lines.extend(["## Root Cause Analysis", ""])
    for finding in sorted(findings, key=lambda item: (severity_rank(item.severity), item.code)):
        lines.extend(
            [
                f"### {finding.code}",
                "",
                f"- root_cause: {finding.root_cause}",
                f"- safer_target_pattern: {finding.safer_pattern}",
                f"- how_the_workflow_allowed_it: {finding.problem}",
                "",
            ]
        )
    return "\n".join(lines)


def render_report_three(findings: list[Finding]) -> str:
    unique_findings = []
    seen_codes: set[str] = set()
    for finding in sorted(findings, key=lambda item: (severity_rank(item.severity), item.code)):
        if finding.code in seen_codes:
            continue
        seen_codes.add(finding.code)
        unique_findings.append(finding)
    lines = [
        "# Scafforge Prevention Actions",
        "",
        "## Package Changes Required",
        "",
    ]
    if not unique_findings:
        lines.extend(["- No additional prevention actions are required beyond keeping the current contract intact.", "", "## Validation and Test Updates", "", "- None recorded.", "", "## Documentation or Prompt Updates", "", "- None recorded.", "", "## Open Decisions", "", "- None recorded.", ""])
        return "\n".join(lines)

    for index, finding in enumerate(unique_findings, start=1):
        lines.extend(
            [
                f"### ACTION-{index:03d}",
                "",
                f"- source_finding: {finding.code}",
                f"- change_target: {infer_surface(finding)}",
                f"- why_it_prevents_recurrence: {prevention_action(finding)}",
                "- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.",
                f"- validation: {validation_target_for_finding(finding)}",
                "",
            ]
        )
    lines.extend(["## Validation and Test Updates", ""])
    for finding in unique_findings:
        lines.extend([f"- {finding.code}: {validation_target_for_finding(finding)}.", ""])
    lines.extend(["## Documentation or Prompt Updates", ""])
    doc_findings = [
        finding
        for finding in unique_findings
        if finding.code.startswith(("WFLOW", "SKILL", "MODEL", "SESSION"))
        or any(token in " ".join(finding.files) for token in ("docs/", ".opencode/agents/", ".opencode/skills/"))
    ]
    if doc_findings:
        for finding in doc_findings:
            lines.extend([f"- {finding.code}: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.", ""])
    else:
        lines.extend(["- None recorded.", ""])
    lines.extend(["## Open Decisions", "", "- None recorded.", ""])
    return "\n".join(lines)


def render_report_four(
    root: Path,
    findings: list[Finding],
    recommendations: list[dict[str, Any]],
    disposition_bundle: dict[str, Any] | None = None,
) -> str:
    ownership_summary = disposition_bundle.get("ownership_summary") if isinstance(disposition_bundle, dict) and isinstance(disposition_bundle.get("ownership_summary"), dict) else {}
    safe_repairs = [
        item
        for item in recommendations
        if recommendation_disposition_class(item, disposition_bundle) == "managed_blocker"
        and item["route"] == "scafforge-repair"
    ]
    source_follow_up = [
        item
        for item in recommendations
        if recommendation_disposition_class(item, disposition_bundle) == "source_follow_up"
    ]
    manual_prerequisites = [
        item
        for item in recommendations
        if recommendation_disposition_class(item, disposition_bundle) == "manual_prerequisite_blocker"
        or item["route"] == "manual-prerequisite"
    ]
    package_first = [
        item
        for item in recommendations
        if recommendation_disposition_class(item, disposition_bundle) in {"managed_blocker", "manual_prerequisite_blocker"}
        and item["route"] in {"scafforge-repair", "manual-prerequisite"}
        and "Scafforge package work required" in item.get("repair_class", "")
    ]
    subject_repo_first = source_follow_up
    requires_regeneration = any(
        finding.code in {"SKILL001", "SKILL002", "SKILL003", "MODEL001"} or any(token in " ".join(finding.files) for token in (".opencode/agents/", ".opencode/skills/"))
        for finding in findings
    )
    repeated_cycle = next((finding for finding in findings if finding.code in {"CYCLE001", "CYCLE002", "CYCLE003"}), None)
    lines = [
        "# Live Repo Repair Plan",
        "",
        "## Preconditions",
        "",
        f"- Repo: {root}",
        "- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.",
        f"- defect_scope: {ownership_summary.get('overall', 'advisory')}",
        "",
    ]
    lines.extend([
        "## Triage Order",
        "",
        f"- package_first_count: {len(package_first)}",
        f"- subject_repo_follow_up_count: {len(subject_repo_first)}",
        f"- host_or_manual_prerequisite_count: {len(manual_prerequisites)}",
        "",
    ])
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
    lines.extend(["## Package Changes Required First", ""])
    if manual_prerequisites:
        for item in manual_prerequisites:
            lines.extend(
                [
                    f"### {item['id']}",
                    "",
                    f"- linked_report_id: {recommendation_linked_codes(item)}",
                    f"- defect_scope: {recommendation_defect_scope(item, disposition_bundle)}",
                    f"- action_type: {item['repair_class']}",
                    "- requires_scafforge_repair_afterward: no, not until the package or host prerequisite gap is resolved",
                    "- carry_diagnosis_pack_into_scafforge_first: yes",
                    f"- target_repo: {'Scafforge package repo' if 'Scafforge package work required' in item['repair_class'] else 'subject repo host environment'}",
                    f"- summary: {item['summary']}",
                    "",
                ]
            )
    else:
        lines.extend(["- None recorded.", ""])

    lines.extend(["## Post-Update Repair Actions", ""])
    if safe_repairs:
        lines.extend([f"- Route {len(safe_repairs)} workflow-layer finding(s) into `scafforge-repair` for deterministic managed-surface refresh.", ""])
        if requires_regeneration:
            lines.extend(["- After deterministic repair, rerun project-local skill regeneration, agent-team follow-up, and prompt hardening before handoff.", ""])
        for item in safe_repairs:
            lines.extend(
                [
                    f"### {item['id']}",
                    "",
                    f"- linked_report_id: {recommendation_linked_codes(item)}",
                    f"- defect_scope: {recommendation_defect_scope(item, disposition_bundle)}",
                    f"- action_type: {item['repair_class']}",
                    "- should_scafforge_repair_run: yes",
                    "- carry_diagnosis_pack_into_scafforge_first: no",
                    "- target_repo: subject repo",
                    f"- summary: {item['summary']}",
                    "",
                ]
            )
    else:
        lines.extend(["- No safe managed-surface repair is still required from the current findings.", ""])

    lines.extend(["## Ticket Follow-Up", ""])
    if source_follow_up:
        for item in source_follow_up:
            lines.extend(
                [
                    f"### {item['id']}",
                    "",
                    f"- linked_report_id: {recommendation_linked_codes(item)}",
                    f"- defect_scope: {recommendation_defect_scope(item, disposition_bundle)}",
                    "- action_type: generated-repo remediation ticket or repo-owned follow-up",
                    "- should_scafforge_repair_run: no further managed repair required before this follow-up",
                    "- carry_diagnosis_pack_into_scafforge_first: no",
                    "- target_repo: subject repo",
                    f"- summary: {item['summary']}",
                    f"- assignee: {item.get('assignee', 'implementer')}",
                    f"- suggested_fix_approach: {item.get('suggested_fix_approach', item['summary'])}",
                    "",
                ]
            )
    else:
        lines.extend(["- No subject-repo ticket follow-up was recommended from the current diagnosis run.", ""])

    lines.extend(
        [
            "## Reverification Plan",
            "",
            "- After package-side fixes land, run one fresh audit on the subject repo before applying another repair cycle.",
            "- After managed repair, rerun the public repair verifier and confirm restart surfaces, ticket routing, and any historical trust restoration paths match the current canonical state.",
            "- Do not treat restart prose alone as proof; the canonical manifest and workflow state remain the source of truth.",
            "",
        ]
    )

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
    findings.append(
        Finding(
            code="ENV004",
            severity="warning",
            problem="The requested diagnosis-pack output path is not writable from the current host workspace.",
            root_cause="Audit always emits a diagnosis pack, but the default or requested output location may live outside the host's writable roots. Without redirection, a host-side diagnosis run can fail even though repo inspection succeeded.",
            files=[],
            safer_pattern="Pass `--diagnosis-output-dir` when auditing repos outside writable roots, or let the audit fall back to a writable host-local diagnosis directory and record that redirection explicitly.",
            evidence=evidence,
        )
    )
    return fallback


def emit_diagnosis_pack(
    root: Path,
    findings: list[Finding],
    destination: Path,
    logs: list[Path],
    *,
    ctx: AuditReportingContext,
    manifest_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    destination.mkdir(parents=True, exist_ok=True)
    recommendations = build_ticket_recommendations(findings, ctx, root)
    disposition_bundle = build_disposition_bundle(
        findings,
        recommendations,
        generated_at=generated_at,
        repo_root=str(root),
        audit_package_commit=ctx.current_package_commit,
    )
    next_step = recommended_next_step(findings, recommendations, disposition_bundle)
    reports = {
        DIAGNOSIS_REPORTS["report_1"]: render_report_one(root, findings, generated_at, logs),
        DIAGNOSIS_REPORTS["report_2"]: render_report_two(findings),
        DIAGNOSIS_REPORTS["report_3"]: render_report_three(findings),
        DIAGNOSIS_REPORTS["report_4"]: render_report_four(root, findings, recommendations, disposition_bundle),
    }
    for filename, content in reports.items():
        (destination / filename).write_text(content + "\n", encoding="utf-8")
    disposition_bundle_name = "disposition-bundle.json"
    (destination / disposition_bundle_name).write_text(json.dumps(disposition_bundle, indent=2) + "\n", encoding="utf-8")

    manifest: dict[str, Any] = {
        "generated_at": generated_at,
        "repo_root": str(root),
        "finding_count": len(findings),
        "finding_codes": sorted({finding.code for finding in findings}),
        "source_findings": [
            {
                "code": finding.code,
                "severity": finding.severity,
            }
            for finding in findings
            if finding.code in bundle_source_follow_up_codes(disposition_bundle)
        ],
        "result_state": diagnosis_result_state(findings),
        "diagnosis_kind": "initial_diagnosis",
        "evidence_mode": "transcript_backed" if logs else "current_state_only",
        "audit_package_commit": ctx.current_package_commit,
        "report_files": {key: value for key, value in DIAGNOSIS_REPORTS.items()},
        "disposition_bundle_file": disposition_bundle_name,
        "disposition_bundle": disposition_bundle,
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


def resolve_current_package_commit(package_root: Path) -> str:
    if os.environ.get("SCAFFORGE_FORCE_MISSING_PROVENANCE") == "1":
        return "missing_provenance"
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=package_root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return "missing_provenance"
    if result.returncode != 0:
        return "missing_provenance"
    commit = result.stdout.strip() or "missing_provenance"
    provenance_pathspec = [".", *[f":(exclude){path}" for path in PACKAGE_PROVENANCE_EXCLUDES]]
    try:
        dirty = subprocess.run(
            ["git", "status", "--porcelain=v1", "--", *provenance_pathspec],
            cwd=package_root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return commit
    if dirty.returncode != 0:
        return commit
    dirty_state = dirty.stdout.strip()
    if not dirty_state:
        return commit
    try:
        diff = subprocess.run(
            ["git", "diff", "--no-ext-diff", "HEAD", "--", *provenance_pathspec],
            cwd=package_root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return commit
    fingerprint_source = dirty_state
    if diff.returncode == 0 and diff.stdout:
        fingerprint_source = f"{dirty_state}\n{diff.stdout}"
    fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:12]
    return f"{commit}+dirty:{fingerprint}"
