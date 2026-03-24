from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FLOW_MANIFEST = ROOT / "skills" / "skill-flow-manifest.json"


@dataclass
class Finding:
    severity: str
    message: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(read_text(path))


def add_missing(findings: list[Finding], path: Path) -> None:
    findings.append(Finding("error", f"Missing required file: {path.relative_to(ROOT)}"))


def require_contains(findings: list[Finding], path: Path, needle: str) -> None:
    if needle not in read_text(path):
        findings.append(Finding("error", f"{path.relative_to(ROOT)} does not contain required text: {needle}"))


def validate_flow_manifest(findings: list[Finding]) -> None:
    if not FLOW_MANIFEST.exists():
        add_missing(findings, FLOW_MANIFEST)
        return

    manifest = read_json(FLOW_MANIFEST)
    if not isinstance(manifest, dict):
        findings.append(Finding("error", "skills/skill-flow-manifest.json is not a JSON object"))
        return

    skills = manifest.get("skills")
    if not isinstance(skills, dict):
        findings.append(Finding("error", "skill-flow-manifest.json is missing a skills object"))
        return

    for skill_name in skills:
        skill_file = ROOT / "skills" / skill_name / "SKILL.md"
        if not skill_file.exists():
            findings.append(Finding("error", f"Flow manifest references missing skill file: skills/{skill_name}/SKILL.md"))

    greenfield = manifest.get("run_types", {}).get("greenfield", {})
    sequence = greenfield.get("sequence", [])
    expected = [
        "spec-pack-normalizer",
        "repo-scaffold-factory",
        "opencode-team-bootstrap",
        "ticket-pack-builder:bootstrap",
        "project-skill-bootstrap:foundation",
        "agent-prompt-engineering",
        "scafforge-audit:audit_then_route_repair_if_needed",
        "handoff-brief",
    ]
    for item in expected:
        if item not in sequence:
            findings.append(Finding("error", f"Greenfield sequence is missing required step: {item}"))
    if "review-audit-bridge" in sequence:
        findings.append(Finding("error", "Greenfield sequence should not include review-audit-bridge"))
    if any("repo-process-doctor" in str(item) for item in sequence):
        findings.append(Finding("error", "Greenfield sequence should not reference repo-process-doctor"))

    run_types = manifest.get("run_types", {})
    diagnosis = run_types.get("diagnosis-review", {})
    diagnosis_sequence = diagnosis.get("sequence", [])
    if "scafforge-audit:review_and_emit_diagnosis_pack" not in diagnosis_sequence:
        findings.append(Finding("error", "diagnosis-review sequence must route through scafforge-audit"))

    managed_repair = run_types.get("managed-repair", {})
    managed_repair_sequence = managed_repair.get("sequence", [])
    if "scafforge-repair:apply-safe-repair" not in managed_repair_sequence:
        findings.append(Finding("error", "managed-repair sequence must route through scafforge-repair"))

    kickoff = skills.get("scaffold-kickoff", {})
    modes = kickoff.get("modes", [])
    if "diagnosis-review" not in modes:
        findings.append(Finding("error", "scaffold-kickoff must expose diagnosis-review mode"))
    if "refinement-routing" in modes:
        findings.append(Finding("error", "scaffold-kickoff must not expose refinement-routing"))

    if "repo-process-doctor" in skills:
        findings.append(Finding("error", "skill-flow-manifest.json must not expose repo-process-doctor"))
    if "pr-review-ticket-bridge" in skills:
        findings.append(Finding("error", "skill-flow-manifest.json must not expose pr-review-ticket-bridge"))
    for required_skill in ("scafforge-audit", "scafforge-repair"):
        if required_skill not in skills:
            findings.append(Finding("error", f"skill-flow-manifest.json is missing required skill: {required_skill}"))


def validate_core_docs(findings: list[Finding]) -> None:
    readme = ROOT / "README.md"
    agents = ROOT / "AGENTS.md"
    for path in (readme, agents):
        if not path.exists():
            add_missing(findings, path)
            return
    require_contains(findings, readme, "## Truth hierarchy")
    require_contains(findings, readme, "## Default scaffold chain")
    require_contains(findings, readme, "## Generated repo-local skills")
    require_contains(findings, readme, "Weak-model first")
    require_contains(findings, agents, "## Product contract refinements")
    require_contains(findings, agents, "## Canonical generated-repo truth hierarchy")


def validate_template_surfaces(findings: list[Finding]) -> None:
    template = ROOT / "skills" / "repo-scaffold-factory" / "assets" / "project-template"
    required = [
        template / "README.md",
        template / "AGENTS.md",
        template / "START-HERE.md",
        template / "docs" / "spec" / "CANONICAL-BRIEF.md",
        template / "docs" / "process" / "model-matrix.md",
        template / "tickets" / "manifest.json",
        template / ".opencode" / "tools" / "ticket_create.ts",
        template / ".opencode" / "tools" / "ticket_claim.ts",
        template / ".opencode" / "tools" / "ticket_release.ts",
        template / ".opencode" / "tools" / "ticket_reopen.ts",
        template / ".opencode" / "tools" / "ticket_reverify.ts",
        template / ".opencode" / "tools" / "environment_bootstrap.ts",
        template / ".opencode" / "tools" / "issue_intake.ts",
        template / ".opencode" / "tools" / "ticket_update.ts",
        template / ".opencode" / "commands" / "bootstrap-check.md",
        template / ".opencode" / "commands" / "issue-triage.md",
        template / ".opencode" / "commands" / "plan-wave.md",
        template / ".opencode" / "commands" / "run-lane.md",
        template / ".opencode" / "commands" / "join-lanes.md",
        template / ".opencode" / "commands" / "reverify-ticket.md",
        template / ".opencode" / "state" / "workflow-state.json",
        template / ".opencode" / "state" / "artifacts" / "registry.json",
        template / ".opencode" / "agents" / "__AGENT_PREFIX__-lane-executor.md",
        template / ".opencode" / "agents" / "__AGENT_PREFIX__-backlog-verifier.md",
        template / ".opencode" / "agents" / "__AGENT_PREFIX__-ticket-creator.md",
        template / ".opencode" / "skills" / "research-delegation" / "SKILL.md",
        template / ".opencode" / "skills" / "local-git-specialist" / "SKILL.md",
        template / ".opencode" / "skills" / "isolation-guidance" / "SKILL.md",
        template / ".opencode" / "skills" / "review-audit-bridge" / "SKILL.md",
    ]
    for path in required:
        if not path.exists():
            add_missing(findings, path)

    require_contains(findings, template / "README.md", "## Truth hierarchy")
    require_contains(findings, template / "AGENTS.md", "## Truth hierarchy")
    require_contains(findings, template / "docs" / "spec" / "CANONICAL-BRIEF.md", "## Tooling and Model Constraints")
    require_contains(findings, template / "docs" / "spec" / "CANONICAL-BRIEF.md", "## Blocking Decisions")
    require_contains(findings, template / "docs" / "spec" / "CANONICAL-BRIEF.md", "## Backlog Readiness")
    require_contains(findings, template / ".opencode" / "state" / "workflow-state.json", '"process_version"')
    require_contains(findings, template / ".opencode" / "state" / "workflow-state.json", '"pending_process_verification"')
    require_contains(findings, template / ".opencode" / "state" / "workflow-state.json", '"parallel_mode"')
    require_contains(findings, template / ".opencode" / "state" / "workflow-state.json", '"ticket_state"')
    require_contains(findings, template / ".opencode" / "state" / "workflow-state.json", '"bootstrap"')
    require_contains(findings, template / ".opencode" / "state" / "workflow-state.json", '"lane_leases"')
    require_contains(findings, template / ".opencode" / "state" / "workflow-state.json", '"state_revision"')
    require_contains(findings, template / "tickets" / "manifest.json", '"wave"')
    require_contains(findings, template / "tickets" / "manifest.json", '"parallel_safe"')
    require_contains(findings, template / "tickets" / "manifest.json", '"overlap_risk"')
    require_contains(findings, template / "tickets" / "manifest.json", '"decision_blockers"')
    require_contains(findings, template / "tickets" / "manifest.json", '"resolution_state"')
    require_contains(findings, template / "tickets" / "manifest.json", '"verification_state"')


def validate_audit_repair_surfaces(findings: list[Finding]) -> None:
    audit_skill = ROOT / "skills" / "scafforge-audit"
    repair_skill = ROOT / "skills" / "scafforge-repair"
    required = [
        audit_skill / "SKILL.md",
        audit_skill / "agents" / "openai.yaml",
        audit_skill / "scripts" / "audit_repo_process.py",
        audit_skill / "references" / "four-report-templates.md",
        audit_skill / "references" / "pr-review-workflow.md",
        audit_skill / "references" / "review-contract.md",
        repair_skill / "SKILL.md",
        repair_skill / "agents" / "openai.yaml",
        repair_skill / "scripts" / "apply_repo_process_repair.py",
    ]
    for path in required:
        if not path.exists():
            add_missing(findings, path)

    runner = repair_skill / "scripts" / "apply_repo_process_repair.py"
    if runner.exists():
        require_contains(findings, runner, '"deterministic-workflow-engine-replacement"')
        require_contains(findings, runner, "scafforge-repair")

    audit_runner = audit_skill / "scripts" / "audit_repo_process.py"
    if audit_runner.exists():
        require_contains(findings, audit_runner, "01-initial-codebase-review.md")
        require_contains(findings, audit_runner, "04-live-repo-repair-plan.md")
        require_contains(findings, audit_runner, "recommended-ticket-payload.json")
        require_contains(findings, audit_runner, 'root / "diagnosis"')

    audit_doc = audit_skill / "SKILL.md"
    if audit_doc.exists():
        require_contains(findings, audit_doc, "manually copy the diagnosis pack")
        require_contains(findings, audit_doc, "Do not tell the user to go straight from report generation to repair")
        require_contains(findings, audit_doc, "references/four-report-templates.md")

    repair_doc = repair_skill / "SKILL.md"
    if repair_doc.exists():
        require_contains(findings, repair_doc, "stale package version")
        require_contains(findings, repair_doc, "manually copy that pack into the Scafforge dev repo first")

    old_skill = ROOT / "skills" / "repo-process-doctor" / "SKILL.md"
    old_bridge = ROOT / "skills" / "pr-review-ticket-bridge" / "SKILL.md"
    if old_skill.exists():
        findings.append(Finding("error", "Deprecated skill still present: skills/repo-process-doctor/SKILL.md"))
    if old_bridge.exists():
        findings.append(Finding("error", "Deprecated skill still present: skills/pr-review-ticket-bridge/SKILL.md"))

    cli = ROOT / "bin" / "scafforge.mjs"
    if cli.exists():
        findings.append(Finding("error", "Deprecated CLI wrapper should not exist: bin/scafforge.mjs"))


def validate_ticket_follow_up_contract(findings: list[Finding]) -> None:
    ticket_builder = ROOT / "skills" / "ticket-pack-builder" / "SKILL.md"
    project_skill = ROOT / "skills" / "project-skill-bootstrap" / "SKILL.md"
    template = ROOT / "skills" / "repo-scaffold-factory" / "assets" / "project-template"

    for path in (ticket_builder, project_skill):
        if not path.exists():
            add_missing(findings, path)
            return

    require_contains(findings, ticket_builder, "**remediation-follow-up**")
    require_contains(findings, ticket_builder, "diagnosis/<timestamp>")
    require_contains(findings, ticket_builder, "ticket_create")
    require_contains(findings, project_skill, "repo-local and advisory-only")
    require_contains(findings, project_skill, "diagnosis/")

    require_contains(findings, template / "docs" / "process" / "workflow.md", "diagnosis/")
    require_contains(findings, template / "docs" / "process" / "workflow.md", "create migration, remediation, or reverification follow-up tickets")
    require_contains(findings, template / "docs" / "process" / "tooling.md", "review-audit-bridge")
    require_contains(findings, template / "tickets" / "README.md", "post-audit and post-repair follow-up")
    require_contains(findings, template / ".opencode" / "skills" / "review-audit-bridge" / "SKILL.md", "does not become the canonical ticket owner")
    require_contains(findings, template / ".opencode" / "skills" / "review-audit-bridge" / "references" / "review-contract.md", "process log")


def validate_no_hidden_defaults(findings: list[Finding]) -> None:
    disallowed = [
        "minimax-coding-plan/MiniMax-M2.5",
        "--default-model",
        "__DEFAULT_MODEL__",
        "GitHub-native",
        "Use when Codex",
        "Codex or OpenCode",
    ]
    for path in ROOT.rglob("*"):
        if path.is_dir() or path.suffix not in {".md", ".py", ".ts", ".json", ".jsonc"}:
            continue
        if "devdocs" in path.parts:
            continue
        if path == Path(__file__).resolve():
            continue
        text = read_text(path)
        for needle in disallowed:
            if needle in text:
                findings.append(Finding("error", f"{path.relative_to(ROOT)} still contains disallowed legacy text: {needle}"))


def main() -> int:
    findings: list[Finding] = []
    validate_flow_manifest(findings)
    validate_core_docs(findings)
    validate_template_surfaces(findings)
    validate_audit_repair_surfaces(findings)
    validate_ticket_follow_up_contract(findings)
    validate_no_hidden_defaults(findings)

    if findings:
        for finding in findings:
            print(f"[{finding.severity.upper()}] {finding.message}")
        return 1

    print("Scafforge contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
