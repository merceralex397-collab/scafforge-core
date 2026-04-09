from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from disposition_bundle import bundle_source_follow_up_codes, build_disposition_bundle, evidence_grade_for_finding
from shared_verifier_types import Finding


DIAGNOSIS_REPORTS = {
    "report_1": "01-initial-codebase-review.md",
    "report_2": "02-scafforge-process-failures.md",
    "report_3": "03-scafforge-prevention-actions.md",
    "report_4": "04-live-repo-repair-plan.md",
}


@dataclass(frozen=True)
class AuditReportingContext:
    package_root: Path
    current_package_commit: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def normalize_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


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
    if finding.code == "WFLOW026":
        return "Teach the shared artifact verdict extractor to accept markdown-emphasized labels like `**Verdict**: PASS`, then route ticket_lookup and ticket_update through that single parser."
    if finding.code == "WFLOW027":
        return "Return verification metadata from restart-surface tools so callers can confirm what handoff and snapshot publication actually wrote."
    if finding.code == "WFLOW028":
        return "Remove the global split-scope completion invariant from workflow.ts validateTicketGraphInvariants so sequential-dependent split children can exist alongside completed parents, then install the fix via scafforge-repair."
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
        return "Teach audit to inspect the previous diagnosis, the latest repair transaction outcome, and the final publish gate before allowing another managed-repair run to proceed."
    if finding.code == "CYCLE002":
        return "Teach audit to stop repeated diagnosis-pack churn when the repo has no newer package or process-version change; require Scafforge package work before the next subject-repo audit."
    if finding.code == "CYCLE003":
        return "Make repair verification inherit the transcript-backed diagnosis basis automatically, keep the final publish gate tied to that basis, emit the post-repair diagnosis pack from the repair runner, and refuse to call the repo clean on current-state evidence alone."
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
    lifecycle_audit = read_text(ctx.package_root / "skills" / "scafforge-audit" / "scripts" / "audit_lifecycle_contracts.py")
    return "(?:\\*\\*|__)?" in workflow_lib and "WFLOW026" in lifecycle_audit


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


def build_ticket_recommendations(findings: list[Finding], ctx: AuditReportingContext) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    wflow024_package_fix_available = package_has_wflow024_fix(ctx)
    target_completion_fix_available = package_has_target_completion_fix(ctx)
    verdict_parser_fix_available = package_has_verdict_parser_fix(ctx)
    split_scope_deadlock_fix_available = package_has_split_scope_deadlock_fix(ctx)
    grouped_follow_up: dict[str, list[Finding]] = {}
    next_index = 1
    for finding in sorted(findings, key=lambda item: (severity_rank(item.severity), item.code)):
        if finding.code in {"BOOT001", "BOOT002"}:
            route = "scafforge-repair"
            repair_class = "safe Scafforge package change"
        elif finding.code.startswith(("BOOT", "ENV", "EXEC", "REF", "SESSION")):
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
        recommendations.append(
            {
                "id": f"REMED-{next_index:03d}",
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
        next_index += 1

    for surface, grouped in sorted(grouped_follow_up.items(), key=lambda item: item[0]):
        all_files = sorted({path for finding in grouped for path in finding.files})
        codes = [finding.code for finding in grouped]
        recommendations.append(
            {
                "id": f"REMED-{next_index:03d}",
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
        next_index += 1
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
    # WFLOW030 = managed_blocked deadlock with only host-only stages unresolved.
    # Running repair again would re-trigger the broad WFLOW trigger and deepen
    # the deadlock.  The correct action is host intervention, not another repair.
    if any(getattr(f, "code", "") == "WFLOW030" for f in findings):
        return "host_intervention_required"
    if any(not finding.code.startswith(("BOOT", "ENV", "EXEC", "REF", "SESSION")) for finding in findings):
        return "subject_repo_repair"
    if findings:
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


def recommendation_summary_for_finding(finding: Finding) -> dict[str, Any]:
    return {
        "title": finding.problem.rstrip("."),
        "description": f"Remediate {finding.code} by correcting the validated issue and rerunning the relevant quality checks.",
        "affected_files": finding.files,
        "suggested_fix_approach": finding.safer_pattern,
        "assignee": "implementer",
    }


def validation_target_for_finding(finding: Finding) -> str:
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


def render_report_four(root: Path, findings: list[Finding], recommendations: list[dict[str, Any]]) -> str:
    safe_repairs = [item for item in recommendations if item["route"] == "scafforge-repair"]
    source_follow_up = [item for item in recommendations if item["route"] == "ticket-pack-builder"]
    manual_prerequisites = [item for item in recommendations if item["route"] == "manual-prerequisite"]
    package_first = [item for item in recommendations if item["route"] in {"scafforge-repair", "manual-prerequisite"} and "Scafforge package work required" in item.get("repair_class", "")]
    subject_repo_first = [item for item in recommendations if item["route"] == "ticket-pack-builder"]
    requires_regeneration = any(
        finding.code in {"SKILL001", "SKILL002", "MODEL001"} or any(token in " ".join(finding.files) for token in (".opencode/agents/", ".opencode/skills/"))
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
                    f"- action_type: {item['repair_class']}",
                    "- should_scafforge_repair_run: yes",
                    "- carry_diagnosis_pack_into_scafforge_first: no",
                    "- target_repo: subject repo",
                    f"- summary: {item['summary']}",
                    "",
                ]
            )
    else:
        lines.extend(["- No safe managed-surface repair was identified from the current findings.", ""])

    lines.extend(["## Ticket Follow-Up", ""])
    if source_follow_up:
        for item in source_follow_up:
            lines.extend(
                [
                    f"### {item['id']}",
                    "",
                    f"- linked_report_id: {recommendation_linked_codes(item)}",
                    "- action_type: generated-repo remediation ticket/process repair",
                    "- should_scafforge_repair_run: only after managed workflow repair converges",
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
    recommendations = build_ticket_recommendations(findings, ctx)
    next_step = recommended_next_step(findings, recommendations)
    disposition_bundle = build_disposition_bundle(
        findings,
        recommendations,
        generated_at=generated_at,
        repo_root=str(root),
        audit_package_commit=ctx.current_package_commit,
    )
    reports = {
        DIAGNOSIS_REPORTS["report_1"]: render_report_one(root, findings, generated_at, logs),
        DIAGNOSIS_REPORTS["report_2"]: render_report_two(findings),
        DIAGNOSIS_REPORTS["report_3"]: render_report_three(findings),
        DIAGNOSIS_REPORTS["report_4"]: render_report_four(root, findings, recommendations),
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
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=package_root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return "missing_provenance"
    return result.stdout.strip() or "missing_provenance"
