from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FLOW_MANIFEST = ROOT / "skills" / "skill-flow-manifest.json"
TEMPLATE_ROOT = ROOT / "skills" / "repo-scaffold-factory" / "assets" / "project-template"


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
    if not path.exists():
        add_missing(findings, path)
        return
    if needle not in read_text(path):
        findings.append(Finding("error", f"{path.relative_to(ROOT)} does not contain required text: {needle}"))


def require_absent(findings: list[Finding], path: Path, needle: str) -> None:
    if not path.exists():
        add_missing(findings, path)
        return
    if needle in read_text(path):
        findings.append(Finding("error", f"{path.relative_to(ROOT)} still contains forbidden text: {needle}"))


def require_paths(findings: list[Finding], paths: list[Path]) -> None:
    for path in paths:
        if not path.exists():
            add_missing(findings, path)


def validate_flow_manifest(findings: list[Finding]) -> None:
    if not FLOW_MANIFEST.exists():
        add_missing(findings, FLOW_MANIFEST)
        return

    manifest = read_json(FLOW_MANIFEST)
    if not isinstance(manifest, dict):
        findings.append(Finding("error", "skills/skill-flow-manifest.json is not a JSON object"))
        return

    run_types = manifest.get("run_types")
    skills = manifest.get("skills")
    if not isinstance(run_types, dict):
        findings.append(Finding("error", "skill-flow-manifest.json is missing a run_types object"))
        return
    if not isinstance(skills, dict):
        findings.append(Finding("error", "skill-flow-manifest.json is missing a skills object"))
        return

    for run_type, payload in run_types.items():
        if isinstance(payload, dict) and payload.get("entrypoint") != "scaffold-kickoff":
            findings.append(Finding("error", f"{run_type} must use scaffold-kickoff as its entrypoint"))

    for skill_name in skills:
        skill_file = ROOT / "skills" / skill_name / "SKILL.md"
        if not skill_file.exists():
            findings.append(Finding("error", f"Flow manifest references missing skill file: skills/{skill_name}/SKILL.md"))

    expected_greenfield = [
        "spec-pack-normalizer",
        "repo-scaffold-factory",
        "project-skill-bootstrap:full-greenfield-pass",
        "opencode-team-bootstrap",
        "agent-prompt-engineering",
        "ticket-pack-builder:bootstrap",
        "handoff-brief",
    ]
    greenfield = run_types.get("greenfield", {})
    greenfield_sequence = greenfield.get("sequence", [])
    if greenfield_sequence != expected_greenfield:
        findings.append(
            Finding(
                "error",
                "Greenfield sequence must exactly match the one-shot contract: "
                + " -> ".join(expected_greenfield),
            )
        )
    if any("scafforge-audit" in str(step) for step in greenfield_sequence):
        findings.append(Finding("error", "Greenfield sequence must not include scafforge-audit"))
    if any("scafforge-repair" in str(step) for step in greenfield_sequence):
        findings.append(Finding("error", "Greenfield sequence must not include scafforge-repair"))

    expected_retrofit = [
        "spec-pack-normalizer:if_needed",
        "opencode-team-bootstrap",
        "project-skill-bootstrap:repair-or-regeneration",
        "ticket-pack-builder:refine_if_needed",
        "scafforge-audit:audit_then_route_repair_if_needed",
        "handoff-brief",
    ]
    retrofit_sequence = run_types.get("retrofit", {}).get("sequence", [])
    if retrofit_sequence != expected_retrofit:
        findings.append(
            Finding(
                "error",
                "Retrofit sequence must restore `.opencode/` before project-skill-bootstrap: "
                + " -> ".join(expected_retrofit),
            )
        )

    diagnosis_sequence = run_types.get("diagnosis-review", {}).get("sequence", [])
    if "scafforge-audit:review_and_emit_diagnosis_pack" not in diagnosis_sequence:
        findings.append(Finding("error", "diagnosis-review sequence must route through scafforge-audit"))

    managed_repair_sequence = run_types.get("managed-repair", {}).get("sequence", [])
    if "scafforge-repair:apply-safe-repair" not in managed_repair_sequence:
        findings.append(Finding("error", "managed-repair sequence must route through scafforge-repair"))

    kickoff_modes = skills.get("scaffold-kickoff", {}).get("modes", [])
    for mode in ("greenfield", "retrofit", "managed-repair", "diagnosis-review"):
        if mode not in kickoff_modes:
            findings.append(Finding("error", f"scaffold-kickoff must expose {mode} mode"))
    if "refinement-routing" in kickoff_modes:
        findings.append(Finding("error", "scaffold-kickoff must not expose refinement-routing"))

    project_skill_modes = skills.get("project-skill-bootstrap", {}).get("modes", [])
    for mode in ("full-greenfield-pass", "repair-or-regeneration"):
        if mode not in project_skill_modes:
            findings.append(Finding("error", f"project-skill-bootstrap must expose {mode} mode"))

    for required_skill in ("scafforge-audit", "scafforge-repair"):
        if required_skill not in skills:
            findings.append(Finding("error", f"skill-flow-manifest.json is missing required skill: {required_skill}"))


def validate_core_docs(findings: list[Finding]) -> None:
    readme = ROOT / "README.md"
    agents = ROOT / "AGENTS.md"
    one_shot = ROOT / "references" / "one-shot-generation-contract.md"
    require_paths(findings, [readme, agents, one_shot])

    require_contains(findings, readme, "Scafforge is a strong-host skill bundle")
    require_contains(findings, readme, "Greenfield generation is one kickoff run.")
    require_contains(findings, readme, "one batched blocking-decision round")
    require_contains(findings, readme, "one uninterrupted same-session generation run")
    require_contains(findings, readme, "No second Scafforge generation pass is required before development begins.")
    require_contains(findings, readme, "Generation, audit, and repair are separate lifecycle stages.")
    require_contains(findings, readme, "scafforge-audit` and `scafforge-repair` are later lifecycle tools")
    require_contains(findings, readme, "model-operating-profile")

    require_contains(findings, agents, "## Product contract refinements")
    require_contains(findings, agents, "## Canonical generated-repo truth hierarchy")
    require_contains(findings, agents, "project-skill-bootstrap")
    require_contains(findings, agents, "agent-prompt-engineering")
    require_contains(findings, agents, "ticket-pack-builder")

    require_contains(findings, one_shot, "one public generation entrypoint")
    require_contains(findings, one_shot, "`scaffold-kickoff`")
    require_contains(findings, one_shot, "one batched blocking-decision round")
    require_contains(findings, one_shot, "one uninterrupted same-session generation pass")
    require_contains(findings, one_shot, "No second Scafforge generation pass is required before development begins.")
    require_contains(findings, one_shot, "Audit and repair are outside the generation cycle.")


def validate_skill_contracts(findings: list[Finding]) -> None:
    scaffold_kickoff = ROOT / "skills" / "scaffold-kickoff" / "SKILL.md"
    spec_pack = ROOT / "skills" / "spec-pack-normalizer" / "SKILL.md"
    repo_factory = ROOT / "skills" / "repo-scaffold-factory" / "SKILL.md"
    project_skill = ROOT / "skills" / "project-skill-bootstrap" / "SKILL.md"
    team_bootstrap = ROOT / "skills" / "opencode-team-bootstrap" / "SKILL.md"
    prompt_engineering = ROOT / "skills" / "agent-prompt-engineering" / "SKILL.md"
    ticket_builder = ROOT / "skills" / "ticket-pack-builder" / "SKILL.md"
    handoff = ROOT / "skills" / "handoff-brief" / "SKILL.md"

    require_paths(
        findings,
        [
            scaffold_kickoff,
            spec_pack,
            repo_factory,
            project_skill,
            team_bootstrap,
            prompt_engineering,
            ticket_builder,
            handoff,
        ],
    )

    require_contains(findings, scaffold_kickoff, "Greenfield generation has no further user-selectable submodes.")
    require_contains(findings, scaffold_kickoff, "you must complete every downstream generation skill in the same session")
    require_contains(findings, scaffold_kickoff, "Do not route the initial generation pass into `scafforge-audit` or `scafforge-repair`.")
    require_contains(findings, scaffold_kickoff, "a first-development handoff that is valid without any later audit or repair pass")
    require_contains(findings, scaffold_kickoff, "route to `opencode-team-bootstrap` to add or repair `.opencode/`, then run `project-skill-bootstrap`")

    require_contains(findings, spec_pack, "The batched decision packet is a required generation artifact.")
    require_contains(findings, spec_pack, "Blocking decisions are all resolved before greenfield generation continues")
    require_contains(findings, spec_pack, "Do not let the greenfield path proceed with unresolved blocking decisions")

    require_contains(findings, repo_factory, "Phase B is mandatory completion work, not an optional revisit.")
    require_contains(findings, repo_factory, "Complete Phase B in the same session as the scaffold render.")
    require_contains(findings, repo_factory, "No generic placeholder text or template filler may remain in any handoff surface")

    require_contains(findings, project_skill, "**greenfield full pass**")
    require_contains(findings, project_skill, "baseline skill pack and all required synthesized skills in one invocation")
    require_contains(findings, project_skill, "model-operating-profile")
    require_contains(findings, project_skill, "Every synthesized skill description must be concrete and selection-specific")
    require_contains(findings, project_skill, "If the repo is missing `.opencode/skills/`, do not start here.")
    require_contains(findings, project_skill, 'a baseline skill that still says "Replace this file..." is invalid')
    require_contains(findings, project_skill, "No generated local skill may retain scaffold placeholder text")
    require_absent(findings, project_skill, "/find-skill")

    require_contains(findings, team_bootstrap, "In retrofit mode, this skill restores `.opencode/` first")
    require_contains(findings, team_bootstrap, "`project-skill-bootstrap` then creates the repo-local skill pack")
    require_contains(findings, team_bootstrap, "the single visible coordinator")
    require_contains(findings, team_bootstrap, "keep the total agent count conservative unless the canonical brief proves genuinely disjoint domains")
    require_contains(findings, team_bootstrap, "Skill allowlists reference only skills that already exist in `.opencode/skills/`")

    require_contains(findings, prompt_engineering, "Treat these notes as read-only package reference material.")
    require_contains(findings, prompt_engineering, "Do not write back into Scafforge package files during project generation.")
    require_contains(findings, prompt_engineering, "Formatting requirements are clear and specific")
    require_contains(findings, prompt_engineering, "The reason for a requirement is stated when that extra rationale improves compliance")
    require_contains(findings, prompt_engineering, "Example-shaped outputs are included when they materially reduce ambiguity")
    require_contains(findings, prompt_engineering, "Goals are bounded one at a time unless the workflow explicitly supports safe parallel work")

    require_contains(findings, ticket_builder, "Read the finalized generation surfaces")
    require_contains(findings, ticket_builder, "The finalized repo-local validation commands and workflow surfaces")
    require_contains(findings, ticket_builder, '"parallel_mode": "sequential"')

    require_contains(findings, handoff, "**Generation Status**")
    require_contains(findings, handoff, "**Post-Generation Audit Status**")
    require_contains(findings, handoff, "The handoff is valid for immediate development even when no later audit or repair has run yet")
    require_absent(findings, handoff, "Validation Status")


def validate_template_surfaces(findings: list[Finding]) -> None:
    required = [
        TEMPLATE_ROOT / "README.md",
        TEMPLATE_ROOT / "AGENTS.md",
        TEMPLATE_ROOT / "START-HERE.md",
        TEMPLATE_ROOT / "opencode.jsonc",
        TEMPLATE_ROOT / "docs" / "spec" / "CANONICAL-BRIEF.md",
        TEMPLATE_ROOT / "docs" / "process" / "workflow.md",
        TEMPLATE_ROOT / "docs" / "process" / "model-matrix.md",
        TEMPLATE_ROOT / "tickets" / "manifest.json",
        TEMPLATE_ROOT / ".opencode" / "state" / "workflow-state.json",
        TEMPLATE_ROOT / ".opencode" / "tools" / "_workflow.ts",
        TEMPLATE_ROOT / ".opencode" / "commands" / "kickoff.md",
        TEMPLATE_ROOT / ".opencode" / "skills" / "model-operating-profile" / "SKILL.md",
        TEMPLATE_ROOT / ".opencode" / "skills" / "review-audit-bridge" / "SKILL.md",
    ]
    require_paths(findings, required)

    require_contains(findings, TEMPLATE_ROOT / "README.md", "model-operating-profile")
    require_contains(findings, TEMPLATE_ROOT / "AGENTS.md", "one active write lane at a time")
    require_contains(findings, TEMPLATE_ROOT / "START-HERE.md", "single-lane-first execution posture")
    require_contains(findings, TEMPLATE_ROOT / "START-HERE.md", "begin the first development pass")
    require_contains(findings, TEMPLATE_ROOT / "START-HERE.md", "## Generation Status")
    require_contains(findings, TEMPLATE_ROOT / "START-HERE.md", "## Post-Generation Audit Status")
    require_absent(findings, TEMPLATE_ROOT / "START-HERE.md", "## Process Contract")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "spec" / "CANONICAL-BRIEF.md", "## Blocking Decisions")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "spec" / "CANONICAL-BRIEF.md", "## Backlog Readiness")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "process" / "workflow.md", "default to one active foreground lane at a time")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "process" / "workflow.md", "keep one visible team leader by default")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "state" / "workflow-state.json", '"parallel_mode": "sequential"')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "_workflow.ts", 'parallel_mode === "sequential"')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "_workflow.ts", "## Generation Status")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "_workflow.ts", "## Post-Generation Audit Status")
    require_absent(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "_workflow.ts", "## Workflow State")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "environment_bootstrap.ts", 'const syncArgs = ["uv", "sync", "--locked"]')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "environment_bootstrap.ts", "repo pip availability")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "environment_bootstrap.ts", "required bootstrap prerequisites are missing")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "commands" / "kickoff.md", "one active write lane")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "skills" / "model-operating-profile" / "SKILL.md", "Goal")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "skills" / "model-operating-profile" / "SKILL.md", "Evidence required")

    require_absent(findings, TEMPLATE_ROOT / "opencode.jsonc", "project_github")
    require_absent(findings, TEMPLATE_ROOT / "opencode.jsonc", "githubcopilot.com")

    local_skill_catalog = ROOT / "skills" / "project-skill-bootstrap" / "references" / "local-skill-catalog.md"
    conformance = ROOT / "skills" / "repo-scaffold-factory" / "references" / "opencode-conformance-checklist.json"
    require_contains(findings, local_skill_catalog, "## model-operating-profile")
    require_contains(findings, conformance, '".opencode/skills/model-operating-profile/SKILL.md"')
    require_contains(findings, conformance, '"model-operating-profile"')


def validate_audit_repair_surfaces(findings: list[Finding]) -> None:
    audit_skill = ROOT / "skills" / "scafforge-audit"
    repair_skill = ROOT / "skills" / "scafforge-repair"
    require_paths(
        findings,
        [
            audit_skill / "SKILL.md",
            audit_skill / "agents" / "openai.yaml",
            audit_skill / "scripts" / "audit_repo_process.py",
            audit_skill / "references" / "four-report-templates.md",
            audit_skill / "references" / "pr-review-workflow.md",
            audit_skill / "references" / "review-contract.md",
            repair_skill / "SKILL.md",
            repair_skill / "agents" / "openai.yaml",
            repair_skill / "scripts" / "apply_repo_process_repair.py",
        ],
    )

    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", "scafforge-repair")
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", 'workflow_contract.get("parallel_mode", "sequential")')
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", 'code="BOOT001"')
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", 'code="SKILL001"')
    require_contains(findings, repair_skill / "scripts" / "audit_repo_process.py", 'code="BOOT001"')
    require_contains(findings, repair_skill / "scripts" / "audit_repo_process.py", 'code="SKILL001"')
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Bootstrap deadlock (BOOT001")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Placeholder local skills (SKILL001")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "## BOOT repair actions (BOOT001)")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "## SKILL repair actions (SKILL001)")
    require_contains(findings, audit_skill / "SKILL.md", "manually copy the diagnosis pack")
    require_contains(findings, audit_skill / "SKILL.md", "Do not tell the user to go straight from report generation to repair")
    require_contains(findings, repair_skill / "SKILL.md", "manually copy that pack into the Scafforge dev repo first")

    deprecated = [
        ROOT / "skills" / "repo-process-doctor" / "SKILL.md",
        ROOT / "skills" / "pr-review-ticket-bridge" / "SKILL.md",
        ROOT / "bin" / "scafforge.mjs",
    ]
    for path in deprecated:
        if path.exists():
            findings.append(Finding("error", f"Deprecated surface should not exist: {path.relative_to(ROOT)}"))


def validate_no_hidden_defaults(findings: list[Finding]) -> None:
    disallowed_repo_wide = [
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
        for needle in disallowed_repo_wide:
            if needle in text:
                findings.append(Finding("error", f"{path.relative_to(ROOT)} still contains disallowed legacy text: {needle}"))

    branded_terms = ("Codex", "Claude", "Copilot", "GitHub Copilot", "githubcopilot.com")
    template_roots = [
        ROOT / "skills" / "repo-scaffold-factory" / "assets" / "project-template",
        ROOT / "skills" / "handoff-brief" / "assets" / "templates",
    ]
    for base in template_roots:
        for path in base.rglob("*"):
            if path.is_dir() or path.suffix not in {".md", ".json", ".jsonc", ".ts"}:
                continue
            text = read_text(path)
            for needle in branded_terms:
                if needle in text:
                    findings.append(
                        Finding(
                            "error",
                            f"{path.relative_to(ROOT)} contains host branding that should not appear in generated surfaces: {needle}",
                        )
                    )


def main() -> int:
    findings: list[Finding] = []
    validate_flow_manifest(findings)
    validate_core_docs(findings)
    validate_skill_contracts(findings)
    validate_template_surfaces(findings)
    validate_audit_repair_surfaces(findings)
    validate_no_hidden_defaults(findings)

    if findings:
        for finding in findings:
            print(f"[{finding.severity.upper()}] {finding.message}")
        return 1

    print("Scafforge contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
