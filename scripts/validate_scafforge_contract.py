from __future__ import annotations

import json
import re
import subprocess
import sys
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


def require_order(findings: list[Finding], path: Path, first: str, second: str) -> None:
    if not path.exists():
        add_missing(findings, path)
        return
    text = read_text(path)
    first_index = text.find(first)
    second_index = text.find(second)
    if first_index == -1 or second_index == -1:
        findings.append(
            Finding(
                "error",
                f"{path.relative_to(ROOT)} must contain ordered text: {first!r} before {second!r}",
            )
        )
        return
    if first_index >= second_index:
        findings.append(Finding("error", f"{path.relative_to(ROOT)} must place {first!r} before {second!r}"))


def require_not_exists(findings: list[Finding], path: Path) -> None:
    if path.exists():
        findings.append(Finding("error", f"Deprecated or private surface should not exist: {path.relative_to(ROOT)}"))


def extract_reference_codes(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return set(re.findall(r"\b(?:BOOT|SKILL|MODEL|CYCLE|WFLOW|SESSION|ENV|EXEC)\d{3}\b", read_text(path)))


def require_reference_sync(findings: list[Finding], primary: Path, secondary: Path, *, label: str) -> None:
    if not primary.exists():
        add_missing(findings, primary)
        return
    if not secondary.exists():
        add_missing(findings, secondary)
        return
    primary_codes = extract_reference_codes(primary)
    secondary_codes = extract_reference_codes(secondary)
    missing = sorted(primary_codes - secondary_codes)
    extra = sorted(secondary_codes - primary_codes)
    if missing:
        findings.append(
            Finding(
                "error",
                f"{secondary.relative_to(ROOT)} is out of sync with {primary.relative_to(ROOT)} for {label}; missing codes: {', '.join(missing)}",
            )
        )
    if extra:
        findings.append(
            Finding(
                "error",
                f"{secondary.relative_to(ROOT)} diverges from {primary.relative_to(ROOT)} for {label}; unexpected codes: {', '.join(extra)}",
            )
        )


def require_paths(findings: list[Finding], paths: list[Path]) -> None:
    for path in paths:
        if not path.exists():
            add_missing(findings, path)


def require_json_field(findings: list[Finding], path: Path, key_path: list[str], expected: object) -> None:
    if not path.exists():
        add_missing(findings, path)
        return
    data = read_json(path)
    cursor = data
    for key in key_path:
        if not isinstance(cursor, dict) or key not in cursor:
            findings.append(Finding("error", f"{path.relative_to(ROOT)} is missing JSON key path: {'.'.join(key_path)}"))
            return
        cursor = cursor[key]
    if cursor != expected:
        findings.append(Finding("error", f"{path.relative_to(ROOT)} expected {'.'.join(key_path)} == {expected!r}, found {cursor!r}"))


def require_files_equal(findings: list[Finding], left: Path, right: Path) -> None:
    if not left.exists():
        add_missing(findings, left)
        return
    if not right.exists():
        add_missing(findings, right)
        return
    if read_text(left) != read_text(right):
        findings.append(Finding("error", f"Shared reference surfaces diverged: {left.relative_to(ROOT)} != {right.relative_to(ROOT)}"))


def require_script_help_runs(findings: list[Finding], path: Path) -> None:
    if not path.exists():
        add_missing(findings, path)
        return
    result = subprocess.run(
        [sys.executable, str(path), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        summary = detail[0] if detail else "no error output"
        findings.append(
            Finding(
                "error",
                f"{path.relative_to(ROOT)} --help failed with exit code {result.returncode}: {summary}",
            )
        )


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
    contract_smells = manifest.get("contract_smells")
    if not isinstance(contract_smells, list):
        findings.append(Finding("error", "skill-flow-manifest.json is missing a contract_smells list"))
        contract_smells = []

    cycle_smell = None
    for smell in contract_smells:
        if isinstance(smell, dict) and smell.get("code") == "CYCLE001":
            cycle_smell = smell
            break
    if not isinstance(cycle_smell, dict):
        findings.append(Finding("error", "skill-flow-manifest.json must declare contract smell CYCLE001"))
    else:
        if cycle_smell.get("status") != "accepted-temporary-debt":
            findings.append(Finding("error", "CYCLE001 must remain marked as accepted-temporary-debt"))
        if cycle_smell.get("skills") != ["project-skill-bootstrap", "opencode-team-bootstrap"]:
            findings.append(Finding("error", "CYCLE001 must name project-skill-bootstrap and opencode-team-bootstrap as the affected skills"))
        if cycle_smell.get("current_order") != ["project-skill-bootstrap:full-greenfield-pass", "opencode-team-bootstrap"]:
            findings.append(Finding("error", "CYCLE001 must record the current greenfield order for the project-skill/team-bootstrap seam"))
        if "minimal-operable" not in str(cycle_smell.get("removal_condition", "")):
            findings.append(Finding("error", "CYCLE001 removal_condition must point to a minimal-operable versus specialization split"))

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
        "repo-scaffold-factory:verify-generated-scaffold",
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

    expected_managed_repair = [
        "scafforge-repair:apply-safe-repair",
        "project-skill-bootstrap:repair-or-regeneration_if_needed",
        "opencode-team-bootstrap:follow_up_if_project_specific_drift",
        "agent-prompt-engineering:repair-hardening_if_needed",
        "ticket-pack-builder:refine_if_needed",
        "handoff-brief",
    ]
    managed_repair_sequence = run_types.get("managed-repair", {}).get("sequence", [])
    if managed_repair_sequence != expected_managed_repair:
        findings.append(
            Finding(
                "error",
                "managed-repair sequence must run repair, local-skill regeneration, agent follow-up, prompt hardening, ticket follow-up, and handoff in that order: "
                + " -> ".join(expected_managed_repair),
            )
        )

    expected_pivot = [
        "scafforge-pivot:classify_and_route",
        "project-skill-bootstrap:repair-or-regeneration_if_needed",
        "opencode-team-bootstrap:follow_up_if_project_specific_drift",
        "agent-prompt-engineering:repair-hardening_if_needed",
        "ticket-pack-builder:refine_if_needed",
        "scafforge-repair:follow_up_if_managed_workflow_drift",
        "handoff-brief",
    ]
    pivot_sequence = run_types.get("pivot", {}).get("sequence", [])
    if pivot_sequence != expected_pivot:
        findings.append(
            Finding(
                "error",
                "pivot sequence must route through bounded pivot orchestration before selective downstream refresh: "
                + " -> ".join(expected_pivot),
            )
        )

    kickoff_modes = skills.get("scaffold-kickoff", {}).get("modes", [])
    for mode in ("greenfield", "retrofit", "managed-repair", "pivot", "diagnosis-review"):
        if mode not in kickoff_modes:
            findings.append(Finding("error", f"scaffold-kickoff must expose {mode} mode"))
    if "refinement-routing" in kickoff_modes:
        findings.append(Finding("error", "scaffold-kickoff must not expose refinement-routing"))

    project_skill_modes = skills.get("project-skill-bootstrap", {}).get("modes", [])
    for mode in ("full-greenfield-pass", "repair-or-regeneration"):
        if mode not in project_skill_modes:
            findings.append(Finding("error", f"project-skill-bootstrap must expose {mode} mode"))

    project_skill = skills.get("project-skill-bootstrap", {})
    team_bootstrap = skills.get("opencode-team-bootstrap", {})
    if "opencode-team-bootstrap" not in project_skill.get("downstreams", []):
        findings.append(Finding("error", "project-skill-bootstrap must flow into opencode-team-bootstrap while CYCLE001 remains active"))
    if "opencode-team-bootstrap" not in project_skill.get("upstreams", []):
        findings.append(Finding("error", "project-skill-bootstrap must record opencode-team-bootstrap as an upstream while CYCLE001 remains active"))
    if "project-skill-bootstrap" not in team_bootstrap.get("downstreams", []):
        findings.append(Finding("error", "opencode-team-bootstrap must record project-skill-bootstrap as a downstream while CYCLE001 remains active"))
    if "project-skill-bootstrap" not in team_bootstrap.get("upstreams", []):
        findings.append(Finding("error", "opencode-team-bootstrap must record project-skill-bootstrap as an upstream while CYCLE001 remains active"))

    audit_modes = skills.get("scafforge-audit", {}).get("modes", [])
    if audit_modes != ["full-diagnosis"]:
        findings.append(Finding("error", "scafforge-audit must expose only the full-diagnosis mode"))

    for required_skill in ("scafforge-audit", "scafforge-repair", "scafforge-pivot"):
        if required_skill not in skills:
            findings.append(Finding("error", f"skill-flow-manifest.json is missing required skill: {required_skill}"))

    required_output_contracts = {
        "scaffold-kickoff": 4,
        "spec-pack-normalizer": 3,
        "project-skill-bootstrap": 3,
        "opencode-team-bootstrap": 3,
        "agent-prompt-engineering": 3,
        "ticket-pack-builder": 4,
        "handoff-brief": 4,
    }
    for skill_name, minimum_count in required_output_contracts.items():
        payload = skills.get(skill_name, {})
        outputs = payload.get("required_outputs")
        if not isinstance(outputs, list) or len(outputs) < minimum_count:
            findings.append(Finding("error", f"skill-flow-manifest.json must declare at least {minimum_count} required_outputs for {skill_name}"))


def validate_core_docs(findings: list[Finding]) -> None:
    readme = ROOT / "README.md"
    agents = ROOT / "AGENTS.md"
    one_shot = ROOT / "references" / "one-shot-generation-contract.md"
    competence_contract = ROOT / "references" / "competence-contract.md"
    require_paths(findings, [readme, agents, one_shot, competence_contract])

    require_contains(findings, readme, "Scafforge is a strong-host skill bundle")
    require_contains(findings, readme, "Greenfield generation is one kickoff run.")
    require_contains(findings, readme, "one batched blocking-decision round")
    require_contains(findings, readme, "one uninterrupted same-session generation run")
    require_contains(findings, readme, "No second Scafforge generation pass is required before development begins.")
    require_contains(findings, readme, "Greenfield completion requires immediate continuation proof, not only surface agreement.")
    require_contains(findings, readme, "Generation, audit, repair, and pivot are separate lifecycle stages.")
    require_contains(findings, readme, "scafforge-audit`, `scafforge-repair`, and `scafforge-pivot` are later lifecycle tools")
    require_contains(findings, readme, "model-operating-profile")
    require_contains(findings, readme, "always validates review evidence")
    require_contains(findings, readme, "public repair contract")
    require_contains(findings, readme, "public pivot contract")
    require_contains(findings, readme, "deterministic refresh engine")
    require_contains(findings, readme, "references/competence-contract.md")
    require_contains(findings, readme, "one legal next move")
    require_contains(findings, readme, "temporary contract smell")
    require_contains(findings, readme, "minimal-operable-versus-specialization split")

    require_contains(findings, agents, "## Product contract refinements")
    require_contains(findings, agents, "## Canonical generated-repo truth hierarchy")
    require_contains(findings, agents, "project-skill-bootstrap")
    require_contains(findings, agents, "agent-prompt-engineering")
    require_contains(findings, agents, "ticket-pack-builder")
    require_contains(findings, agents, "full diagnosis-pack generation on every audit run")
    require_contains(findings, agents, "references/competence-contract.md")
    require_contains(findings, agents, "one legal next move")
    require_contains(findings, agents, "explicit temporary contract smell")
    require_contains(findings, agents, "minimal-operable-versus-specialization split")
    require_contains(findings, agents, "scafforge-pivot")
    require_contains(findings, agents, "immediately continuable")

    require_contains(findings, competence_contract, "one legal next action")
    require_contains(findings, competence_contract, "operator confusion is package evidence")
    require_contains(findings, competence_contract, "causal-regression coverage")
    require_contains(findings, competence_contract, "## Pivot expectations")

    require_contains(findings, one_shot, "one public generation entrypoint")
    require_contains(findings, one_shot, "`scaffold-kickoff`")
    require_contains(findings, one_shot, "one batched blocking-decision round")
    require_contains(findings, one_shot, "one uninterrupted same-session generation pass")
    require_contains(findings, one_shot, "No second Scafforge generation pass is required before development begins.")
    require_contains(findings, one_shot, "Greenfield completion requires immediate continuation proof, not only surface agreement.")
    require_contains(findings, one_shot, "Audit and repair are outside the generation cycle.")
    require_contains(findings, one_shot, "Pivot is outside the initial generation cycle.")
    require_contains(findings, one_shot, "`scafforge-pivot` is a later change-management lifecycle skill.")


def validate_skill_contracts(findings: list[Finding]) -> None:
    scaffold_kickoff = ROOT / "skills" / "scaffold-kickoff" / "SKILL.md"
    spec_pack = ROOT / "skills" / "spec-pack-normalizer" / "SKILL.md"
    repo_factory = ROOT / "skills" / "repo-scaffold-factory" / "SKILL.md"
    repo_factory_verify = ROOT / "skills" / "repo-scaffold-factory" / "scripts" / "verify_generated_scaffold.py"
    project_skill = ROOT / "skills" / "project-skill-bootstrap" / "SKILL.md"
    team_bootstrap = ROOT / "skills" / "opencode-team-bootstrap" / "SKILL.md"
    prompt_engineering = ROOT / "skills" / "agent-prompt-engineering" / "SKILL.md"
    ticket_builder = ROOT / "skills" / "ticket-pack-builder" / "SKILL.md"
    ticket_system_ref = ROOT / "skills" / "ticket-pack-builder" / "references" / "ticket-system.md"
    pivot_skill = ROOT / "skills" / "scafforge-pivot" / "SKILL.md"
    pivot_agent = ROOT / "skills" / "scafforge-pivot" / "agents" / "openai.yaml"
    pivot_script = ROOT / "skills" / "scafforge-pivot" / "scripts" / "plan_pivot.py"
    handoff = ROOT / "skills" / "handoff-brief" / "SKILL.md"

    require_paths(
        findings,
        [
            scaffold_kickoff,
            spec_pack,
            repo_factory,
            repo_factory_verify,
            project_skill,
            team_bootstrap,
            prompt_engineering,
            ticket_builder,
            ticket_system_ref,
            pivot_skill,
            pivot_agent,
            pivot_script,
            handoff,
        ],
    )

    require_contains(findings, scaffold_kickoff, "Greenfield generation has no further user-selectable submodes.")
    require_contains(findings, scaffold_kickoff, "you must complete every downstream generation skill in the same session")
    require_contains(findings, scaffold_kickoff, "Do not route the initial generation pass into `scafforge-audit` or `scafforge-repair`.")
    require_contains(findings, scaffold_kickoff, "a first-development handoff that is valid without any later audit or repair pass")
    require_contains(findings, scaffold_kickoff, "route to `opencode-team-bootstrap` to add or repair `.opencode/`, then run `project-skill-bootstrap`")
    require_contains(findings, scaffold_kickoff, "let it continue through any required project-specific regeneration or ticket follow-up")
    require_contains(findings, scaffold_kickoff, "same-session immediate-continuation verification gate")
    require_contains(findings, scaffold_kickoff, "verify_generated_scaffold.py <repo-root> --format both")
    require_contains(findings, scaffold_kickoff, "full non-mutating diagnosis")
    require_contains(findings, scaffold_kickoff, "redirecting the output directory")
    require_contains(findings, scaffold_kickoff, "explicit ticket acceptance smoke commands as the canonical smoke scope")
    require_contains(findings, scaffold_kickoff, "one legal first move while bootstrap proof is still missing")
    require_contains(findings, scaffold_kickoff, "## Pivot flow")
    require_contains(findings, scaffold_kickoff, "Route midstream feature and design changes through `scafforge-pivot`")
    require_absent(findings, ROOT / "skills" / "scafforge-audit" / "SKILL.md", "greenfield or retrofit flow")
    require_contains(findings, ROOT / "skills" / "scafforge-audit" / "SKILL.md", "retrofit audit step or an explicit diagnosis/review flow")
    require_contains(findings, ROOT / "skills" / "scafforge-audit" / "SKILL.md", "grouped by invariant family in code modules")
    require_contains(findings, ROOT / "skills" / "scafforge-audit" / "SKILL.md", "rule implementation plus regression coverage")

    require_contains(findings, spec_pack, "The batched decision packet is a required generation artifact.")
    require_contains(findings, spec_pack, "Blocking decisions are all resolved before greenfield generation continues")
    require_contains(findings, spec_pack, "Do not let the greenfield path proceed with unresolved blocking decisions")

    require_contains(findings, repo_factory, "Phase B is mandatory completion work, not an optional revisit.")
    require_contains(findings, repo_factory, "Complete Phase B in the same session as the scaffold render.")
    require_contains(findings, repo_factory, "No generic placeholder text or template filler may remain in any handoff surface")
    require_contains(findings, repo_factory, "A fresh scaffold must already expose one legal first move while bootstrap proof is missing")
    require_contains(findings, repo_factory, "explicit ticket acceptance smoke commands are canonical smoke scope")
    require_contains(findings, repo_factory, "verify_generated_scaffold.py")
    require_contains(findings, repo_factory_verify, "verify_greenfield_continuation")
    require_contains(findings, repo_factory_verify, '"verification_kind": "greenfield_continuation"')
    require_contains(findings, repo_factory_verify, "immediately_continuable")
    require_script_help_runs(findings, repo_factory_verify)

    require_contains(findings, project_skill, "**greenfield full pass**")
    require_contains(findings, project_skill, "baseline skill pack and all required synthesized skills in one invocation")
    require_contains(findings, project_skill, "model-operating-profile")
    require_contains(findings, project_skill, "Every synthesized skill description must be concrete and selection-specific")
    require_contains(findings, project_skill, "If the repo is missing `.opencode/skills/`, do not start here.")
    require_contains(findings, project_skill, 'a baseline skill that still says "Replace this file..." is invalid')
    require_contains(findings, project_skill, "No generated local skill may retain scaffold placeholder text")
    require_contains(findings, project_skill, "slash commands are human entrypoints")
    require_contains(findings, project_skill, "missing host prerequisites such as `uv`, `pytest`, `rg`, git identity, or service binaries are blockers")
    require_contains(findings, project_skill, "bootstrap readiness is a pre-lifecycle gate")
    require_absent(findings, project_skill, "/find-skill")

    require_contains(findings, team_bootstrap, "In retrofit mode, this skill restores `.opencode/` first")
    require_contains(findings, team_bootstrap, "`project-skill-bootstrap` then creates the repo-local skill pack")
    require_contains(findings, team_bootstrap, "the single visible coordinator")
    require_contains(findings, team_bootstrap, "keep the total agent count conservative unless the canonical brief proves genuinely disjoint domains")
    require_contains(findings, team_bootstrap, "Skill allowlists reference only skills that already exist in `.opencode/skills/`")
    require_contains(findings, team_bootstrap, "ticket_lookup.transition_guidance")
    require_contains(findings, team_bootstrap, "bootstrap-not-ready state as a hard gate")
    require_contains(findings, team_bootstrap, "Agents must not use `/kickoff`, `/resume`")

    require_contains(findings, prompt_engineering, "Treat these notes as read-only package reference material.")
    require_contains(findings, prompt_engineering, "Do not write back into Scafforge package files during project generation.")
    require_contains(findings, prompt_engineering, "Formatting requirements are clear and specific")
    require_contains(findings, prompt_engineering, "The reason for a requirement is stated when that extra rationale improves compliance")
    require_contains(findings, prompt_engineering, "Example-shaped outputs are included when they materially reduce ambiguity")
    require_contains(findings, prompt_engineering, "Goals are bounded one at a time unless the workflow explicitly supports safe parallel work")
    require_contains(findings, prompt_engineering, "Workflow thrash loops")
    require_contains(findings, prompt_engineering, "Evidence-free PASS claims")
    require_contains(findings, prompt_engineering, "Missing environment prerequisites are explicit")
    require_contains(findings, prompt_engineering, "one clear legal next move")

    require_contains(findings, ticket_builder, "Read the finalized generation surfaces")
    require_contains(findings, ticket_builder, "The finalized repo-local validation commands and workflow surfaces")
    require_contains(findings, ticket_builder, '"parallel_mode": "sequential"')
    require_contains(findings, ticket_builder, '"process_version": 7')
    require_contains(findings, ticket_builder, "`plan_review`")
    require_contains(findings, ticket_builder, "`smoke_test`")
    require_contains(findings, ticket_builder, "prefer one explicit backticked repo-local smoke command")
    require_contains(findings, ticket_builder, "`split_scope`")
    require_contains(findings, ticket_builder, "scope-isolated")
    require_contains(findings, ticket_builder, "literal acceptance command knowingly reaches into sibling-ticket or later-ticket scope")
    require_contains(findings, ticket_system_ref, "`split_scope`")
    require_contains(findings, ticket_system_ref, "scope-isolated")

    require_contains(findings, pivot_skill, "machine-readable stale-surface map")
    require_contains(findings, pivot_skill, "Pivot History")
    require_contains(findings, pivot_skill, "python3 scripts/plan_pivot.py <repo-root>")
    require_contains(findings, pivot_skill, ".opencode/meta/pivot-state.json")
    require_contains(findings, pivot_skill, "Do not let `scafforge-pivot` become a second scaffold engine or a second repair engine.")
    require_contains(findings, pivot_skill, "Use repair only for managed workflow refresh, not for product-truth changes")
    require_contains(findings, pivot_agent, 'display_name: "Scafforge Pivot"')
    require_contains(findings, pivot_script, '"verification_kind": "post_pivot"')
    require_contains(findings, pivot_script, "build_pivot_stale_surface_map")
    require_contains(findings, pivot_script, "downstream_refresh")
    require_contains(findings, pivot_script, "docs/spec/CANONICAL-BRIEF.md")
    require_contains(findings, pivot_script, ".opencode/meta/pivot-state.json")
    require_contains(findings, pivot_script, "Pivot History")
    require_script_help_runs(findings, pivot_script)

    require_contains(findings, handoff, "**Generation Status**")
    require_contains(findings, handoff, "**Post-Generation Audit Status**")
    require_contains(findings, handoff, "The handoff is a truthful restart surface bounded by current evidence")
    require_contains(findings, handoff, "The next action matches the one legal first move exposed by canonical state when bootstrap is not yet ready")
    require_contains(findings, handoff, "the handoff proves immediate continuation rather than only surface agreement")
    require_absent(findings, handoff, "Validation Status")

    for skill_file in (scaffold_kickoff, spec_pack, project_skill, team_bootstrap, prompt_engineering, ticket_builder, pivot_skill, handoff):
        require_contains(findings, skill_file, "## Output contract")


def validate_template_surfaces(findings: list[Finding]) -> None:
    workflow_lib = TEMPLATE_ROOT / ".opencode" / "lib" / "workflow.ts"
    private_workflow_tool = TEMPLATE_ROOT / ".opencode" / "tools" / "_workflow.ts"
    environment_bootstrap = TEMPLATE_ROOT / ".opencode" / "tools" / "environment_bootstrap.ts"
    smoke_test = TEMPLATE_ROOT / ".opencode" / "tools" / "smoke_test.ts"
    handoff_publish = TEMPLATE_ROOT / ".opencode" / "tools" / "handoff_publish.ts"
    artifact_write = TEMPLATE_ROOT / ".opencode" / "tools" / "artifact_write.ts"
    artifact_register = TEMPLATE_ROOT / ".opencode" / "tools" / "artifact_register.ts"
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
        TEMPLATE_ROOT / ".opencode" / "state" / "context-snapshot.md",
        TEMPLATE_ROOT / ".opencode" / "state" / "latest-handoff.md",
        workflow_lib,
        TEMPLATE_ROOT / ".opencode" / "commands" / "kickoff.md",
        TEMPLATE_ROOT / ".opencode" / "skills" / "model-operating-profile" / "SKILL.md",
        TEMPLATE_ROOT / ".opencode" / "skills" / "review-audit-bridge" / "SKILL.md",
    ]
    require_paths(findings, required)
    require_not_exists(findings, private_workflow_tool)

    require_contains(findings, TEMPLATE_ROOT / "README.md", "model-operating-profile")
    require_contains(findings, TEMPLATE_ROOT / "AGENTS.md", "one active write lane at a time")
    require_contains(findings, TEMPLATE_ROOT / "AGENTS.md", "`plan_review`")
    require_contains(findings, TEMPLATE_ROOT / "AGENTS.md", "The team leader owns `ticket_claim` and `ticket_release`.")
    require_contains(findings, TEMPLATE_ROOT / "AGENTS.md", ".opencode/state/latest-handoff.md")
    require_contains(findings, TEMPLATE_ROOT / "START-HERE.md", "single-lane-first execution posture")
    require_contains(findings, TEMPLATE_ROOT / "START-HERE.md", "environment_bootstrap")
    require_contains(findings, TEMPLATE_ROOT / "START-HERE.md", "bootstrap recovery required")
    require_contains(findings, TEMPLATE_ROOT / "START-HERE.md", "## Generation Status")
    require_contains(findings, TEMPLATE_ROOT / "START-HERE.md", "## Post-Generation Audit Status")
    require_absent(findings, TEMPLATE_ROOT / "START-HERE.md", "## Process Contract")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "spec" / "CANONICAL-BRIEF.md", "## Blocking Decisions")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "spec" / "CANONICAL-BRIEF.md", "## Backlog Readiness")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "process" / "workflow.md", "default to one active foreground lane at a time")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "process" / "workflow.md", "keep one visible team leader by default")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "process" / "workflow.md", "`plan_review`")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "process" / "workflow.md", "use `ticket_reverify` to restore trust on a closed done ticket")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "process" / "workflow.md", "run `environment_bootstrap` first, then rerun `ticket_lookup` before any stage change")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "process" / "workflow.md", "the team leader owns `ticket_claim` and `ticket_release`")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "process" / "workflow.md", "open active-ticket work remains the primary foreground lane")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "process" / "workflow.md", "`.opencode/state/latest-handoff.md`")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "state" / "workflow-state.json", '"parallel_mode": "sequential"')
    require_json_field(findings, TEMPLATE_ROOT / ".opencode" / "state" / "workflow-state.json", ["bootstrap", "status"], "missing")
    require_json_field(findings, TEMPLATE_ROOT / ".opencode" / "state" / "workflow-state.json", ["process_version"], 7)
    require_json_field(findings, TEMPLATE_ROOT / ".opencode" / "state" / "workflow-state.json", ["repair_follow_on", "outcome"], "clean")
    require_json_field(findings, TEMPLATE_ROOT / ".opencode" / "state" / "artifacts" / "registry.json", ["version"], 2)
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "state" / "context-snapshot.md", "## Process State")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "state" / "context-snapshot.md", "- state_revision: 0")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "state" / "context-snapshot.md", "- outcome: clean")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "state" / "context-snapshot.md", "- Open split children: none")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "state" / "latest-handoff.md", "bootstrap recovery required")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "state" / "latest-handoff.md", "- repair_follow_on_outcome: clean")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "state" / "latest-handoff.md", "- split_child_tickets: none")
    require_contains(findings, TEMPLATE_ROOT / "START-HERE.md", "- split_child_tickets: none")
    require_absent(findings, TEMPLATE_ROOT / "START-HERE.md", "repair_follow_on_handoff_allowed")
    require_absent(findings, TEMPLATE_ROOT / ".opencode" / "state" / "context-snapshot.md", "- handoff_allowed:")
    require_absent(findings, TEMPLATE_ROOT / ".opencode" / "state" / "latest-handoff.md", "repair_follow_on_handoff_allowed")
    require_contains(findings, workflow_lib, 'parallel_mode === "sequential"')
    require_contains(findings, workflow_lib, "## Generation Status")
    require_contains(findings, workflow_lib, "## Post-Generation Audit Status")
    require_contains(findings, workflow_lib, "dependent_tickets_waiting_on_current")
    require_contains(findings, workflow_lib, "validateHandoffNextAction")
    require_contains(findings, workflow_lib, "refreshRestartSurfaces")
    require_contains(findings, workflow_lib, "latestHandoffPath")
    require_contains(findings, workflow_lib, "WorkflowBlocker")
    require_contains(findings, workflow_lib, "throwWorkflowBlocker")
    require_contains(findings, workflow_lib, "ticketClaimBlockerArgs")
    require_contains(findings, workflow_lib, "export function blockedDependentTickets")
    require_contains(findings, workflow_lib, "export function dependentContinuationAction")
    require_contains(findings, workflow_lib, "export function ticketNeedsHistoricalReconciliation")
    require_contains(findings, workflow_lib, "export function ticketNeedsTrustRestoration")
    require_contains(findings, workflow_lib, "Historical done-ticket reverification stays secondary until the active open ticket is resolved.")
    require_contains(findings, workflow_lib, "Run environment_bootstrap, register its proof artifact, rerun ticket_lookup, and do not continue lifecycle work until bootstrap is ready.")
    require_contains(findings, workflow_lib, 'export type RepairFollowOnOutcome = "managed_blocked" | "source_follow_up" | "clean"')
    require_contains(findings, workflow_lib, 'export type TicketSourceMode = "process_verification" | "post_completion_issue" | "net_new_scope" | "split_scope"')
    require_contains(findings, workflow_lib, "repoVenvExecutableCandidates")
    require_contains(findings, workflow_lib, "repoVenvExecutable")
    require_contains(findings, workflow_lib, "findExistingRepoVenvExecutable")
    require_contains(findings, workflow_lib, "repair_follow_on_outcome")
    require_contains(findings, workflow_lib, "workflow.repair_follow_on.outcome === \"source_follow_up\"")
    require_contains(findings, workflow_lib, '"plan_review"')
    require_absent(findings, workflow_lib, "## Workflow State")
    require_absent(findings, workflow_lib, "tool({")
    require_contains(findings, environment_bootstrap, "[project.optional-dependencies]")
    require_contains(findings, environment_bootstrap, "[dependency-groups]")
    require_contains(findings, environment_bootstrap, "[tool.uv.dev-dependencies]")
    require_contains(findings, environment_bootstrap, "[tool.pytest.ini_options]")
    require_contains(findings, environment_bootstrap, "extractTomlSectionBody")
    require_contains(findings, environment_bootstrap, "escapeRegExp")
    require_contains(findings, environment_bootstrap, "repo pip availability")
    require_contains(findings, environment_bootstrap, "required bootstrap prerequisites are missing")
    require_contains(findings, environment_bootstrap, "permission_restriction")
    require_contains(findings, environment_bootstrap, "blocked_by_permissions")
    require_contains(findings, environment_bootstrap, "host_surface_classification")
    require_contains(findings, environment_bootstrap, "Fix the permission/tool policy")
    require_contains(findings, environment_bootstrap, "defaultBootstrapProofPath")
    require_contains(findings, environment_bootstrap, "normalizeRepoPath")
    require_contains(findings, environment_bootstrap, "repoVenvExecutable")
    require_contains(findings, environment_bootstrap, "findExistingRepoVenvExecutable")
    require_absent(findings, environment_bootstrap, "(?:\\\\n\\\\[|$)")
    require_contains(findings, smoke_test, 'join(root, "uv.lock")')
    require_contains(findings, smoke_test, "findExistingRepoVenvExecutable")
    require_contains(findings, smoke_test, "[tool.pytest.ini_options]")
    require_contains(findings, smoke_test, "scope:")
    require_contains(findings, smoke_test, "test_paths:")
    require_contains(findings, smoke_test, "command_override:")
    require_contains(findings, smoke_test, "args.scope")
    require_contains(findings, smoke_test, "args.test_paths")
    require_contains(findings, smoke_test, "parseCommandOverride")
    require_contains(findings, smoke_test, "tokenizeCommandString")
    require_contains(findings, smoke_test, "env_overrides")
    require_contains(findings, smoke_test, "KEY=VALUE")
    require_contains(findings, smoke_test, "multiple shell-style command strings")
    require_contains(findings, smoke_test, "command_override cannot mix tokenized argv entries with multiple shell-style command strings.")
    require_contains(findings, smoke_test, "inferAcceptanceSmokeCommands")
    require_contains(findings, smoke_test, "ticket.acceptance")
    require_contains(findings, smoke_test, "Ticket acceptance criteria define an explicit smoke-test command.")
    require_contains(findings, smoke_test, "host_surface_classification")
    require_contains(findings, smoke_test, "permission_restriction")
    require_contains(findings, smoke_test, "blocked_by_permissions")
    require_contains(findings, smoke_test, "Fix the permission/tool policy")
    require_contains(findings, smoke_test, "defaultArtifactPath")
    require_contains(findings, smoke_test, "normalizeRepoPath")
    require_contains(findings, artifact_write, "expectedPath = defaultArtifactPath")
    require_contains(findings, artifact_write, "canonicalizeRepoPath(args.path)")
    require_contains(findings, artifact_register, "expectedPath = defaultArtifactPath")
    require_contains(findings, artifact_register, "canonicalizeRepoPath(args.path)")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_update.ts", '"plan_review"')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_update.ts", "validateLifecycleStageStatus")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_lookup.ts", "transition_guidance")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_lookup.ts", "Do not fabricate a PASS artifact through generic artifact tools.")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_lookup.ts", "historical trust still needs restoration")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_lookup.ts", "ticketNeedsHistoricalReconciliation")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_lookup.ts", "ticket_reconcile")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_lookup.ts", "ticketNeedsTrustRestoration")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_lookup.ts", "Run environment_bootstrap first, then rerun ticket_lookup before attempting lifecycle transitions.")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_lookup.ts", "Keep ${ticket.id} open as a split parent and foreground child ticket ${foregroundChild.id} instead of advancing the parent lane directly.")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_lookup.ts", "dependentContinuationAction")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_lookup.ts", 'next_action_tool: "smoke_test"')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_lookup.ts", 'next_action_tool: "smoke_test",\n          delegate_to_agent: null,\n          required_owner: "team-leader",')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_reverify.ts", "legal mutation path for closed done tickets")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_reverify.ts", 'if (sourceTicket.status !== "done")')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_reverify.ts", "ticket_reverify requires evidence_artifact_path or verification_content.")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_reverify.ts", 'sourceTicket.verification_state = "reverified"')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_reverify.ts", "getTicketWorkflowState(workflow, sourceTicket.id).needs_reverification = false")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_reverify.ts", 'kind: "backlog-verification"')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_reverify.ts", 'kind: "reverification"')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_create.ts", '"split_scope"')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_create.ts", "split-scope child ticket")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_reconcile.ts", "export default tool({")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_reconcile.ts", "stale or contradictory source/follow-up linkage")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_reconcile.ts", "ticket-reconciliation")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_reconcile.ts", "removeDependencyOnSource")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_reconcile.ts", "targetTicket.depends_on = targetTicket.depends_on.filter")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_reconcile.ts", 'targetTicket.resolution_state = "superseded"')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_reconcile.ts", 'targetTicket.verification_state = "reverified"')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_reconcile.ts", "syncWorkflowSelection(workflow, manifest)")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "plugins" / "stage-gate-enforcer.ts", 'const RESERVED_ARTIFACT_STAGES = new Set(["smoke-test"])')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "plugins" / "stage-gate-enforcer.ts", "Generic artifact_write is not allowed for that stage.")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "plugins" / "stage-gate-enforcer.ts", "Generic artifact_register is not allowed for that stage.")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "plugins" / "stage-gate-enforcer.ts", 'type: "BLOCKER"')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "plugins" / "stage-gate-enforcer.ts", "missing_write_lease")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "plugins" / "stage-gate-enforcer.ts", 'sourceMode === "split_scope"')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "plugins" / "stage-gate-enforcer.ts", 'if (input.tool === "ticket_reconcile") {')
    require_absent(findings, TEMPLATE_ROOT / ".opencode" / "plugins" / "stage-gate-enforcer.ts", 'await ensureTargetTicketWriteLease(sourceTicketId || workflow.active_ticket)')
    require_absent(findings, TEMPLATE_ROOT / ".opencode" / "plugins" / "stage-gate-enforcer.ts", 'await ensureTargetTicketWriteLease(sourceTicketId)\n        if (typeof output.args.evidence_artifact_path !== "string" || !output.args.evidence_artifact_path.trim()) {\n          throw new Error("issue_intake requires evidence_artifact_path.")')
    require_absent(findings, TEMPLATE_ROOT / ".opencode" / "plugins" / "stage-gate-enforcer.ts", 'if (input.tool === "ticket_reverify") {\n        const manifest = await loadManifest()\n        const ticketId = typeof output.args.ticket_id === "string" ? output.args.ticket_id : manifest.active_ticket\n        await ensureTargetTicketWriteLease(ticketId)')
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-docs-handoff.md", "write the full handoff body with `artifact_write` and then register it with `artifact_register`")
    require_absent(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-implementer.md", "ticket_claim: allow")
    require_absent(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-implementer.md", "ticket_release: allow")
    require_absent(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-lane-executor.md", "ticket_claim: allow")
    require_absent(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-lane-executor.md", "ticket_release: allow")
    require_absent(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-docs-handoff.md", "ticket_claim: allow")
    require_absent(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-docs-handoff.md", "ticket_release: allow")
    require_contains(findings, handoff_publish, "validateHandoffNextAction")
    require_order(findings, handoff_publish, "const handoffBlocker = await validateHandoffNextAction", "await refreshRestartSurfaces")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "commands" / "kickoff.md", "one active write lane")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "commands" / "kickoff.md", "The team leader claims and releases write leases.")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "commands" / "kickoff.md", "ticket_reconcile")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "commands" / "resume.md", "Resume from `tickets/manifest.json` and `.opencode/state/workflow-state.json` first.")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "commands" / "resume.md", ".opencode/state/latest-handoff.md")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "commands" / "resume.md", "`managed_blocked`")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "commands" / "resume.md", "same command trace but it still contradicts the repo's declared dependency layout")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-team-leader.md", "ticket_lookup.transition_guidance")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-team-leader.md", "ticket_create: allow")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-team-leader.md", "ticket_reconcile: allow")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-team-leader.md", "If `ticket_lookup.bootstrap.status` is not `ready`, treat `environment_bootstrap` as the next required tool call")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-team-leader.md", "same command trace but it still contradicts the repo's declared dependency layout")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-team-leader.md", "do not create planning, implementation, review, QA, or smoke-test artifacts yourself")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-team-leader.md", "grant a write lease with `ticket_claim` before any specialist writes planning, implementation, review, QA, or handoff artifact bodies or makes code changes")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-team-leader.md", "only Wave 0 setup work may claim a write-capable lease before bootstrap is ready")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-team-leader.md", "when the ticket acceptance criteria already define executable smoke commands")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-team-leader.md", "use human slash commands only as entrypoints")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "skills" / "ticket-execution" / "SKILL.md", "transition_guidance")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "skills" / "ticket-execution" / "SKILL.md", "if `ticket_lookup.bootstrap.status` is not `ready`, stop normal lifecycle routing, run `environment_bootstrap`, then rerun `ticket_lookup` before any `ticket_update`")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "skills" / "ticket-execution" / "SKILL.md", "same command trace but it still omits the dependency-group or extra flags the repo layout requires")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "skills" / "ticket-execution" / "SKILL.md", "the team leader claims and releases write leases")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "skills" / "ticket-execution" / "SKILL.md", "`smoke_test` is the only legal producer of `smoke-test`")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "skills" / "ticket-execution" / "SKILL.md", "if the ticket acceptance criteria already define executable smoke commands")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "skills" / "ticket-execution" / "SKILL.md", "do not convert expected results into PASS evidence")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "skills" / "ticket-execution" / "SKILL.md", "slash commands are human entrypoints")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "skills" / "ticket-execution" / "SKILL.md", "`repair_follow_on.outcome` is `managed_blocked`")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "skills" / "ticket-execution" / "SKILL.md", "ticket_create(source_mode=split_scope)")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "skills" / "ticket-execution" / "SKILL.md", "`ticket_reconcile`")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-ticket-creator.md", "ticket_reconcile: allow")
    require_absent(findings, TEMPLATE_ROOT / ".opencode" / "commands" / "resume.md", "handoff_allowed")
    require_absent(findings, TEMPLATE_ROOT / ".opencode" / "commands" / "kickoff.md", "handoff_allowed")
    require_absent(findings, TEMPLATE_ROOT / ".opencode" / "skills" / "ticket-execution" / "SKILL.md", "handoff_allowed")
    require_absent(findings, TEMPLATE_ROOT / ".opencode" / "agents" / "__AGENT_PREFIX__-team-leader.md", "handoff_allowed")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "skills" / "model-operating-profile" / "SKILL.md", "Goal")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "skills" / "model-operating-profile" / "SKILL.md", "Evidence required")

    require_absent(findings, TEMPLATE_ROOT / "opencode.jsonc", "project_github")
    require_absent(findings, TEMPLATE_ROOT / "opencode.jsonc", "githubcopilot.com")

    local_skill_catalog = ROOT / "skills" / "project-skill-bootstrap" / "references" / "local-skill-catalog.md"
    conformance = ROOT / "skills" / "repo-scaffold-factory" / "references" / "opencode-conformance-checklist.json"
    require_contains(findings, local_skill_catalog, "## model-operating-profile")
    require_contains(findings, local_skill_catalog, "bootstrap-first routing when bootstrap is not `ready`")
    require_contains(findings, conformance, '".opencode/skills/model-operating-profile/SKILL.md"')
    require_contains(findings, conformance, '".opencode/state/context-snapshot.md"')
    require_contains(findings, conformance, '".opencode/state/latest-handoff.md"')
    require_contains(findings, conformance, '"model-operating-profile"')

    tool_files = sorted((TEMPLATE_ROOT / ".opencode" / "tools").glob("*.ts"))
    for tool_file in tool_files:
        require_contains(findings, tool_file, "export default tool({")
    for workflow_tool in (environment_bootstrap, smoke_test, handoff_publish, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_lookup.ts"):
        require_contains(findings, workflow_tool, "../lib/workflow")
    require_contains(findings, TEMPLATE_ROOT / "tickets" / "README.md", "mirror artifact metadata into `.opencode/state/artifacts/registry.json`")


def validate_audit_repair_surfaces(findings: list[Finding]) -> None:
    audit_skill = ROOT / "skills" / "scafforge-audit"
    repair_skill = ROOT / "skills" / "scafforge-repair"
    audit_contract_surfaces = audit_skill / "scripts" / "audit_contract_surfaces.py"
    audit_execution_surfaces = audit_skill / "scripts" / "audit_execution_surfaces.py"
    audit_lifecycle_contracts = audit_skill / "scripts" / "audit_lifecycle_contracts.py"
    audit_repair_cycles = audit_skill / "scripts" / "audit_repair_cycles.py"
    audit_session_transcripts = audit_skill / "scripts" / "audit_session_transcripts.py"
    audit_restart_surfaces = audit_skill / "scripts" / "audit_restart_surfaces.py"
    audit_ticket_graph = audit_skill / "scripts" / "audit_ticket_graph.py"
    require_paths(
        findings,
        [
            audit_skill / "SKILL.md",
            audit_skill / "agents" / "openai.yaml",
            audit_skill / "scripts" / "audit_repo_process.py",
            audit_contract_surfaces,
            audit_execution_surfaces,
            audit_lifecycle_contracts,
            audit_repair_cycles,
            audit_session_transcripts,
            audit_restart_surfaces,
            audit_ticket_graph,
            audit_skill / "scripts" / "shared_verifier.py",
            audit_skill / "scripts" / "shared_verifier_types.py",
            audit_skill / "references" / "four-report-templates.md",
            audit_skill / "references" / "pr-review-workflow.md",
            audit_skill / "references" / "review-contract.md",
            repair_skill / "SKILL.md",
            repair_skill / "agents" / "openai.yaml",
            repair_skill / "scripts" / "apply_repo_process_repair.py",
            repair_skill / "scripts" / "run_managed_repair.py",
            repair_skill / "scripts" / "regenerate_restart_surfaces.py",
            repair_skill / "scripts" / "audit_repo_process.py",
            repair_skill / "scripts" / "shared_verifier.py",
        ],
    )

    require_contains(findings, ROOT / "README.md", "run_managed_repair.py")
    require_contains(findings, audit_skill / "scripts" / "shared_verifier.py", "from audit_repo_process import audit_repo")
    require_contains(findings, audit_skill / "scripts" / "shared_verifier.py", "from shared_verifier_types import Finding")
    require_contains(findings, audit_skill / "scripts" / "shared_verifier.py", "verify_greenfield_continuation")
    require_contains(findings, audit_skill / "scripts" / "shared_verifier.py", "GREENFIELD_BOOTSTRAP_NEXT_ACTION")
    require_contains(findings, audit_skill / "scripts" / "shared_verifier.py", "tooling_doc_path")
    require_contains(findings, audit_skill / "scripts" / "shared_verifier.py", "tickets_readme_path")
    require_contains(findings, audit_skill / "scripts" / "shared_verifier.py", "ticket_update_path")
    require_contains(findings, audit_skill / "scripts" / "shared_verifier.py", "smoke_test_path")
    require_contains(findings, audit_skill / "scripts" / "shared_verifier.py", "handoff_publish_path")
    require_contains(findings, audit_skill / "scripts" / "shared_verifier.py", "VERIFY008")
    require_contains(findings, audit_skill / "scripts" / "shared_verifier_types.py", "@dataclass")
    require_contains(findings, audit_skill / "scripts" / "shared_verifier_types.py", "class Finding")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "from audit_contract_surfaces import ContractSurfaceAuditContext, run_contract_surface_audits")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "from audit_execution_surfaces import ExecutionSurfaceAuditContext, run_execution_surface_audits")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "from audit_lifecycle_contracts import LifecycleContractAuditContext, run_lifecycle_contract_audits")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "from audit_repair_cycles import RepairCycleAuditContext, run_repair_cycle_audits")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "from audit_session_transcripts import SessionTranscriptAuditContext, run_session_transcript_audits")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "from audit_restart_surfaces import RestartSurfaceAuditContext, run_restart_surface_audits")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "from audit_ticket_graph import TicketGraphAuditContext, run_ticket_graph_audits")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "contract_surface_audit_context")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "execution_surface_audit_context")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "lifecycle_contract_audit_context")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "repair_cycle_audit_context")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "session_transcript_audit_context")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "restart_surface_audit_context")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "ticket_graph_audit_context")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "run_contract_surface_audits(root, findings, contract_ctx)")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "run_execution_surface_audits(root, findings, execution_ctx)")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "run_lifecycle_contract_audits(root, findings, lifecycle_ctx)")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "run_repair_cycle_audits(root, findings, repair_cycle_ctx)")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "run_session_transcript_audits(root, findings, logs or [], session_ctx)")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "run_restart_surface_audits(root, findings, restart_ctx)")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "run_ticket_graph_audits(root, findings, ticket_graph_ctx)")
    require_contains(findings, audit_contract_surfaces, "class ContractSurfaceAuditContext")
    require_contains(findings, audit_contract_surfaces, "def run_contract_surface_audits(")
    require_contains(findings, audit_contract_surfaces, "def audit_status_model(")
    require_contains(findings, audit_contract_surfaces, "def audit_model_profile_drift(")
    require_contains(findings, audit_execution_surfaces, "class ExecutionSurfaceAuditContext")
    require_contains(findings, audit_execution_surfaces, "def run_execution_surface_audits(")
    require_contains(findings, audit_execution_surfaces, "def audit_environment_prerequisites(")
    require_contains(findings, audit_execution_surfaces, "def audit_python_execution(")
    require_contains(findings, audit_lifecycle_contracts, "class LifecycleContractAuditContext")
    require_contains(findings, audit_lifecycle_contracts, "def run_lifecycle_contract_audits(")
    require_contains(findings, audit_lifecycle_contracts, "def audit_active_process_verification(")
    require_contains(findings, audit_lifecycle_contracts, "def audit_ticket_transition_contract(")
    require_contains(findings, audit_repair_cycles, "class RepairCycleAuditContext")
    require_contains(findings, audit_repair_cycles, "def run_repair_cycle_audits(")
    require_contains(findings, audit_repair_cycles, "def audit_failed_repair_cycle(")
    require_contains(findings, audit_repair_cycles, "def audit_verification_basis_regression(")
    require_contains(findings, audit_session_transcripts, "class SessionTranscriptAuditContext")
    require_contains(findings, audit_session_transcripts, "def run_session_transcript_audits(")
    require_contains(findings, audit_session_transcripts, "def audit_session_chronology(")
    require_contains(findings, audit_session_transcripts, "def audit_session_operator_trap(")
    require_contains(findings, audit_restart_surfaces, "class RestartSurfaceAuditContext")
    require_contains(findings, audit_restart_surfaces, "def run_restart_surface_audits(")
    require_contains(findings, audit_restart_surfaces, "def audit_restart_surface_drift(")
    require_contains(findings, audit_restart_surfaces, "def audit_resume_truth_hierarchy(")
    require_contains(findings, audit_ticket_graph, "class TicketGraphAuditContext")
    require_contains(findings, audit_ticket_graph, "def run_ticket_graph_audits(")
    require_contains(findings, audit_ticket_graph, "def audit_stale_ticket_graph(")
    require_contains(findings, audit_ticket_graph, "def audit_historical_reconciliation_deadlock(")
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", "scafforge-repair")
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", "from shared_verifier import audit_repo")
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", 'workflow_contract.get("parallel_mode", "sequential")')
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", "regenerate_restart_surfaces(")
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", "build_stale_surface_map")
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", '"stale_surface_map"')
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", '"ticket_follow_up"')
    require_absent(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", '"human_decision"')
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", '"stage_completion_mode": "transitional_manual_assertion"')
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", '"tracking_mode": "persistent_recorded_state"')
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", "repair-follow-on-state.json")
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", '"asserted_completed_stages": []')
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", ".opencode/state/context-snapshot.md")
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", ".opencode/state/latest-handoff.md")
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", '"verification_passed": verification_passed')
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", '"clean": not findings and not pending_process_verification')
    require_absent(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", 'startswith(("WFLOW", "BOOT", "CYCLE", "ENV"))')
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", "resolve_repair_basis")
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", "load_latest_previous_diagnosis")
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", "manifest_supporting_logs")
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", '"repair_package_commit"')
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", "repair_basis_requires_causal_replay")
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", "verification_next_action")
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", "Run scafforge-audit before relying on this restart narrative for continued development.")
    require_contains(findings, repair_skill / "SKILL.md", "python3 scripts/run_managed_repair.py <repo-root>")
    require_contains(findings, repair_skill / "SKILL.md", "machine-readable stale-surface map")
    require_contains(findings, repair_skill / "SKILL.md", "`stable`, `replace`, `regenerate`, and `ticket_follow_up`")
    require_contains(findings, repair_skill / "SKILL.md", "The current `--stage-complete` path is transitional.")
    require_contains(findings, repair_skill / "SKILL.md", "python3 scripts/record_repair_stage_completion.py <repo-root>")
    require_contains(findings, repair_skill / "SKILL.md", ".opencode/meta/repair-follow-on-state.json")
    require_contains(findings, repair_skill / "SKILL.md", "canonical repair follow-on stage catalog")
    require_contains(findings, repair_skill / "SKILL.md", "`project-skill-bootstrap`")
    require_contains(findings, repair_skill / "SKILL.md", "`opencode-team-bootstrap`")
    require_contains(findings, repair_skill / "SKILL.md", "`agent-prompt-engineering`")
    require_contains(findings, repair_skill / "SKILL.md", "`ticket-pack-builder`")
    require_contains(findings, repair_skill / "SKILL.md", "`handoff-brief`")
    require_contains(findings, repair_skill / "SKILL.md", "not part of the current repair cycle")
    require_contains(findings, repair_skill / "SKILL.md", "ticket-pack-builder")
    require_contains(findings, repair_skill / "SKILL.md", ".opencode/state/artifacts/history/repair/ticket-pack-builder-completion.md")
    require_contains(findings, repair_skill / "SKILL.md", "- `- cycle_id: <current .opencode/meta/repair-follow-on-state.json cycle_id>`")
    require_contains(findings, repair_skill / "SKILL.md", "Recorded execution must include at least one repo-relative evidence path")
    require_contains(findings, repair_skill / "SKILL.md", "repair-contract consistency checks")
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"required_follow_on_stages"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"required_follow_on_stage_details"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", "from shared_verifier import audit_repo")
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", "from follow_on_tracking import")
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", "build_stale_surface_map")
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", "verification_contract_failures")
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"stale_surface_map"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"stage_completion_mode": "transitional_manual_assertion"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"follow_on_tracking_mode": "persistent_recorded_state"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"follow_on_state_path"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"recorded_completed_stages"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"recorded_execution_completed_stages"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"auto_detected_recorded_stages"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"pruned_unknown_stages"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"invalidated_recorded_stages"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"recorded_stage_state"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"required_stage_details"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"status": "recorded_completed"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"asserted_completed_stages"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"status": "asserted_completed"')
    require_paths(findings, [repair_skill / "scripts" / "follow_on_tracking.py", repair_skill / "scripts" / "record_repair_stage_completion.py"])
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"completion_mode": "recorded_execution"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"status": "completed"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"status": "evidence_missing"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"missing_evidence_paths"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"missing_recorded_evidence"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"project-skill-bootstrap"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"opencode-team-bootstrap"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"agent-prompt-engineering"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"ticket-pack-builder"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"handoff-brief"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"repo_local_skills"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"agent_team"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"prompt_hardening"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"ticket_follow_up"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"restart_surface"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", "follow_on_stage_history_metadata")
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", "OPTIONAL_RECORDABLE_FOLLOW_ON_STAGES")
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", "validate_stage_allowed_for_current_cycle")
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", "not part of the current repair cycle")
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", "Unknown repair follow-on stage")
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"status": "pruned_unknown_stages"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"pruned_unknown_stages"')
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", ".opencode/state/artifacts/history/repair/ticket-pack-builder-completion.md")
    require_contains(findings, repair_skill / "scripts" / "follow_on_tracking.py", '"ticket-pack-builder:auto-detected"')
    require_contains(findings, repair_skill / "scripts" / "record_repair_stage_completion.py", '"follow_on_state_path"')
    require_contains(findings, repair_skill / "scripts" / "record_repair_stage_completion.py", '"recorded_stage"')
    require_contains(findings, repair_skill / "scripts" / "record_repair_stage_completion.py", "validate_follow_on_stage_name")
    require_contains(findings, repair_skill / "scripts" / "record_repair_stage_completion.py", "Evidence path does not exist")
    require_contains(findings, repair_skill / "scripts" / "record_repair_stage_completion.py", "requires at least one repo-relative evidence path")
    require_script_help_runs(findings, repair_skill / "scripts" / "record_repair_stage_completion.py")
    require_contains(findings, ticket_pack_builder_skill := ROOT / "skills" / "ticket-pack-builder" / "SKILL.md", ".opencode/state/artifacts/history/repair/ticket-pack-builder-completion.md")
    require_contains(findings, ticket_pack_builder_skill, "- completed_stage: ticket-pack-builder")
    require_contains(findings, ticket_pack_builder_skill, "- cycle_id: <cycle_id from .opencode/meta/repair-follow-on-state.json>")
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"blocking_reasons"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"handoff_allowed"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"repair_follow_on_outcome"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"managed_blocked"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"source_follow_up"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"clean"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"current_state_clean"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"causal_regression_verified"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"contract_failures"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"contract_passed"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"non_clean_without_findings"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"restart_surface_drift_after_repair"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"placeholder_local_skills_survived_refresh"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"repair_basis_path"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"repair_package_commit"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"verification_kind": "post_repair"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", '"diagnosis_kind": "post_repair_verification"')
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", "emit_diagnosis_pack")
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", "select_diagnosis_destination")
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", "--diagnosis-output-dir")
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", "--repair-basis-diagnosis")
    require_contains(findings, repair_skill / "scripts" / "run_managed_repair.py", "package_work_required_first")
    require_contains(findings, repair_skill / "scripts" / "regenerate_restart_surfaces.py", "REGENERATED_SURFACES")
    require_contains(findings, repair_skill / "scripts" / "regenerate_restart_surfaces.py", ".opencode/state/latest-handoff.md")
    require_contains(findings, repair_skill / "scripts" / "regenerate_restart_surfaces.py", "restart_surface_regeneration_history")
    require_contains(findings, repair_skill / "scripts" / "regenerate_restart_surfaces.py", "workflow verification pending")
    require_contains(findings, repair_skill / "scripts" / "regenerate_restart_surfaces.py", "clear pending_process_verification now that no historical done tickets still require process verification")
    require_contains(findings, repair_skill / "scripts" / "regenerate_restart_surfaces.py", "process_verification_state(")
    require_contains(findings, repair_skill / "scripts" / "regenerate_restart_surfaces.py", "dependent_continuation_action(")
    require_contains(findings, repair_skill / "scripts" / "regenerate_restart_surfaces.py", "ticket_needs_historical_reconciliation(")
    require_contains(findings, repair_skill / "scripts" / "regenerate_restart_surfaces.py", "ticket_needs_trust_restoration(")
    require_contains(findings, repair_skill / "scripts" / "regenerate_restart_surfaces.py", "Current ticket is already closed. Activate dependent ticket")
    require_contains(findings, repair_skill / "scripts" / "regenerate_restart_surfaces.py", "Historical done-ticket reverification stays secondary until the active open ticket is resolved.")
    require_contains(findings, repair_skill / "scripts" / "regenerate_restart_surfaces.py", "repair_follow_on_outcome")
    require_contains(findings, repair_skill / "scripts" / "regenerate_restart_surfaces.py", "split_child_tickets")
    require_contains(findings, repair_skill / "scripts" / "regenerate_restart_surfaces.py", "Open split children")
    require_absent(findings, repair_skill / "scripts" / "regenerate_restart_surfaces.py", "repair_follow_on_handoff_allowed")
    require_contains(findings, audit_execution_surfaces, 'code="BOOT001"')
    require_contains(findings, audit_execution_surfaces, 'code="BOOT002"')
    require_contains(findings, audit_contract_surfaces, 'code="status-stage-collision"')
    require_contains(findings, audit_contract_surfaces, 'code="dual-state-model"')
    require_contains(findings, audit_contract_surfaces, 'code="artifact-persistence-through-register"')
    require_contains(findings, audit_contract_surfaces, 'code="invalid-opencode-tool-schema"')
    require_contains(findings, audit_contract_surfaces, 'code="SKILL001"')
    require_contains(findings, audit_contract_surfaces, 'code="MODEL001"')
    require_contains(findings, audit_repair_cycles, 'code="CYCLE001"')
    require_contains(findings, audit_repair_cycles, 'code="CYCLE002"')
    require_contains(findings, audit_repair_cycles, 'code="CYCLE003"')
    require_contains(findings, audit_execution_surfaces, 'code="WFLOW001"')
    require_contains(findings, audit_restart_surfaces, 'code="WFLOW002"')
    require_contains(findings, audit_lifecycle_contracts, 'code="WFLOW003"')
    require_contains(findings, audit_lifecycle_contracts, 'code="WFLOW004"')
    require_contains(findings, audit_lifecycle_contracts, 'code="WFLOW005"')
    require_contains(findings, audit_restart_surfaces, 'code="WFLOW006"')
    require_contains(findings, audit_lifecycle_contracts, 'code="WFLOW007"')
    require_contains(findings, audit_lifecycle_contracts, 'code="WFLOW008"')
    require_contains(findings, audit_lifecycle_contracts, 'code="WFLOW009"')
    require_contains(findings, audit_restart_surfaces, 'code="WFLOW010"')
    require_contains(findings, audit_lifecycle_contracts, "Affected done tickets: none; the workflow flag should now be directly clearable.")
    require_contains(findings, audit_lifecycle_contracts, "does not expose whether pending_process_verification is immediately clearable")
    require_contains(findings, audit_restart_surfaces, 'code="WFLOW011"')
    require_contains(findings, audit_restart_surfaces, 'code="WFLOW012"')
    require_contains(findings, audit_restart_surfaces, 'code="WFLOW013"')
    require_contains(findings, audit_restart_surfaces, 'code="WFLOW014"')
    require_contains(findings, audit_session_transcripts, 'code="WFLOW015"')
    require_contains(findings, audit_session_transcripts, 'code="WFLOW016"')
    require_contains(findings, audit_session_transcripts, 'code="WFLOW017"')
    require_contains(findings, audit_ticket_graph, 'code="WFLOW018"')
    require_contains(findings, audit_ticket_graph, 'code="WFLOW019"')
    require_contains(findings, audit_ticket_graph, 'code="WFLOW020"')
    require_contains(findings, audit_restart_surfaces, 'code="WFLOW021"')
    require_contains(findings, audit_session_transcripts, 'code="WFLOW022"')
    require_contains(findings, audit_session_transcripts, 'code="WFLOW023"')
    require_contains(findings, audit_ticket_graph, 'code="WFLOW024"')
    require_contains(findings, audit_execution_surfaces, 'code="ENV001"')
    require_contains(findings, audit_execution_surfaces, 'code="ENV002"')
    require_contains(findings, audit_execution_surfaces, 'code="ENV003"')
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", 'code="ENV004"')
    require_contains(findings, audit_session_transcripts, 'code="SESSION001"')
    require_contains(findings, audit_session_transcripts, 'code="SESSION002"')
    require_contains(findings, audit_session_transcripts, 'code="SESSION003"')
    require_contains(findings, audit_session_transcripts, 'code="SESSION004"')
    require_contains(findings, audit_session_transcripts, 'code="SESSION005"')
    require_contains(findings, audit_session_transcripts, 'code="SESSION006"')
    require_contains(findings, audit_restart_surfaces, 'code="SKILL002"')
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "--supporting-log")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "TRANSCRIPT_SMOKE_OVERRIDE_FAILURE_PATTERNS")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "extract_transcript_smoke_acceptance_commands")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", '"audit_package_commit"')
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", '"diagnosis_kind"')
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", '"package_work_required_first"')
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", '"recommended_next_step"')
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "--diagnosis-kind")
    require_contains(findings, audit_skill / "scripts" / "audit_repo_process.py", "current_package_commit")
    require_contains(findings, repair_skill / "scripts" / "audit_repo_process.py", "module_from_spec")
    require_contains(findings, repair_skill / "scripts" / "audit_repo_process.py", "audit_repo = AUDIT_MODULE.audit_repo")
    require_contains(findings, repair_skill / "scripts" / "shared_verifier.py", "module_from_spec")
    require_contains(findings, repair_skill / "scripts" / "shared_verifier.py", "audit_repo = VERIFIER_MODULE.audit_repo")
    require_script_help_runs(findings, repair_skill / "scripts" / "run_managed_repair.py")
    require_script_help_runs(findings, repair_skill / "scripts" / "apply_repo_process_repair.py")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Bootstrap deadlock (BOOT001")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Bootstrap command/layout mismatch (BOOT002")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Placeholder local skills (SKILL001")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Model profile drift (MODEL001")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Repeated failed repair cycle (CYCLE001")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Repeated diagnosis churn (CYCLE002")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Verification-basis regression (CYCLE003")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Smoke-test contract drift (WFLOW001")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Handoff overclaim (WFLOW002")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Review-stage ambiguity (WFLOW003")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Transition-contract mismatch (WFLOW004")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Smoke-proof bypass (WFLOW005")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Coordinator workflow overreach (WFLOW006")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Handoff ownership conflict (WFLOW007")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Hidden process-verification state (WFLOW008")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Restart-surface drift (WFLOW010")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Bootstrap-first guidance drift (WFLOW011")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Lease-ownership split (WFLOW012")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Resume truth-hierarchy drift (WFLOW013")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Invocation-log coordinator artifact authorship (WFLOW014")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Broken helper tool surface (WFLOW015")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Smoke-test override execution defect (WFLOW016")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Acceptance-command smoke drift (WFLOW017")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Closed-ticket remediation deadlock (WFLOW018")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Stale ticket-graph contradiction (WFLOW019")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Open-parent split drift (WFLOW020")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Legacy repair-gate leak (WFLOW021")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Closeout lease contradiction (WFLOW022")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Acceptance-scope contamination (WFLOW023")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Historical reconciliation deadlock (WFLOW024")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Thin workflow explainer (SKILL002")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Session chronology miss (SESSION001")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Workflow thrash loop (SESSION002")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Workflow bypass search (SESSION003")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Evidence-free PASS claims (SESSION004")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "Coordinator-authored specialist artifacts (SESSION005")
    require_contains(findings, audit_skill / "references" / "process-smells.md", "No-legal-next-move trap (SESSION006")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "## BOOT repair actions (BOOT001 / BOOT002)")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "## BOOT repair actions (BOOT001 / BOOT002)")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "## SKILL repair actions (SKILL001)")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "## Workflow-skill repair actions (SKILL002)")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "## MODEL repair actions (MODEL001)")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "## Repeated-cycle repair actions (CYCLE001)")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "## Repeated-diagnosis stop actions (CYCLE002)")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "## Verification-basis repair actions (CYCLE003)")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "WFLOW015")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "WFLOW016")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "WFLOW017")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "WFLOW018")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "WFLOW019")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "WFLOW020")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "WFLOW021")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "WFLOW022")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "WFLOW023")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "WFLOW024")
    require_contains(findings, repair_skill / "references" / "repair-playbook.md", "SESSION006")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "## Workflow repair actions (WFLOW001 / WFLOW002 / WFLOW003 / WFLOW004 / WFLOW005 / WFLOW006 / WFLOW007 / WFLOW008 / WFLOW010 / WFLOW011 / WFLOW012 / WFLOW013 / WFLOW014 / WFLOW015 / WFLOW016 / WFLOW017 / WFLOW018 / WFLOW019 / WFLOW020 / WFLOW021 / WFLOW022 / WFLOW023 / WFLOW024 / SESSION001 / SESSION002 / SESSION003 / SESSION004 / SESSION005 / SESSION006)")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "`WFLOW008`: keep `pending_process_verification` visible in restart surfaces and `ticket_lookup.transition_guidance`")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "`WFLOW010`: regenerate `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md`")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "lib" / "workflow.ts", "getProcessVerificationState")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "lib" / "workflow.ts", "clearable_now")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "lib" / "workflow.ts", "Cannot publish clean-state or readiness claims while")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "plugins" / "stage-gate-enforcer.ts", "isWorkflowProcessVerificationClearOnly")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "plugins" / "stage-gate-enforcer.ts", "processVerification.clearable_now")
    require_contains(findings, TEMPLATE_ROOT / ".opencode" / "tools" / "ticket_lookup.ts", "clearable_now: processVerification.clearable_now")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "`WFLOW011`: refresh `ticket_lookup`, the team-leader prompt, and `ticket-execution` together")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "`WFLOW012`: refresh workflow docs, resume-facing commands, and worker prompts together")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "`WFLOW013`: refresh `/resume`, repo guidance docs, and restart surfaces together")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "`WFLOW014`: treat coordinator-authored specialist artifacts from `.opencode/state/invocation-log.jsonl` as suspect evidence")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "`WFLOW015`: keep shared workflow helpers private to imports")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "`WFLOW016`: refresh `.opencode/tools/smoke_test.ts` so `command_override` accepts tokenized argv, one shell-style command string, or multiple shell-style command strings")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "`WFLOW017`: refresh `.opencode/tools/smoke_test.ts`, `ticket-execution`, and the team-leader prompt together")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "`WFLOW018`: refresh `.opencode/plugins/stage-gate-enforcer.ts`, `ticket_create`, and `issue_intake` together")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "`WFLOW019`: add or repair `ticket_reconcile`")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "`WFLOW020`: add first-class `split_scope` support")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "`WFLOW021`: keep legacy `handoff_allowed` parsing internal only")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "`WFLOW022`: keep closeout publication outside the ordinary open-ticket lease contract")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "`WFLOW023`: tighten `ticket-pack-builder`, ticket docs, and closeout guidance together")
    require_contains(findings, audit_skill / "references" / "repair-playbook.md", "`WFLOW024`: repair `ticket_reconcile`, historical evidence routing, and closeout publication together")
    require_contains(findings, audit_skill / "SKILL.md", "deterministic tool-execution defects where the tool surface itself mis-parses a valid request before the intended command starts")
    require_contains(findings, audit_skill / "SKILL.md", "Do not collapse a transcript-backed tool-execution defect into a generic test failure when the tool never launched the requested command")
    require_contains(findings, audit_skill / "SKILL.md", "whether `smoke_test` honors ticket-specific acceptance commands before falling back to generic repo-level smoke detection")
    require_contains(findings, audit_skill / "SKILL.md", "whether failed bootstrap artifacts show command traces that contradict the repo's declared dependency layout")
    require_contains(findings, audit_skill / "SKILL.md", "Do not collapse repeated incompatible bootstrap command traces into a generic `ENV002` rerun recommendation")
    require_contains(findings, audit_skill / "SKILL.md", "Do not collapse acceptance-command drift in `smoke_test` into a generic failing-test finding when the tool ran the wrong smoke scope")
    require_contains(findings, audit_skill / "SKILL.md", "operator spending time figuring out how to move forward on basic workflow")
    require_contains(findings, audit_skill / "SKILL.md", "one clear legal next move")
    require_contains(findings, audit_skill / "SKILL.md", "zero-finding verification audit as proof of repair if the earlier transcript-backed causal basis was dropped")
    require_contains(findings, repair_skill / "SKILL.md", "If the repair basis includes a transcript-backed `smoke_test` override failure, treat that as workflow-surface drift")
    require_contains(findings, repair_skill / "SKILL.md", "If the repair basis includes transcript-backed smoke-scope drift")
    require_contains(findings, audit_skill / "SKILL.md", "manually copy the diagnosis pack")
    require_contains(findings, audit_skill / "SKILL.md", "Do not tell the user to go straight from report generation to repair")
    require_contains(findings, audit_skill / "SKILL.md", "Every audit run produces the full four-report diagnosis pack.")
    require_contains(findings, audit_skill / "SKILL.md", "previous audit-to-repair cycle failed")
    require_contains(findings, audit_skill / "SKILL.md", "--supporting-log <path>")
    require_contains(findings, audit_skill / "SKILL.md", "--diagnosis-output-dir <writable-path>")
    require_contains(findings, audit_skill / "SKILL.md", "--diagnosis-kind post_package_revalidation")
    require_contains(findings, audit_skill / "SKILL.md", "full diagnostic mode")
    require_contains(findings, audit_skill / "SKILL.md", "host prerequisite blocker")
    require_contains(findings, audit_skill / "SKILL.md", "historical session truth and current repo truth")
    require_contains(findings, audit_skill / "SKILL.md", "workflow thrash")
    require_contains(findings, audit_skill / "SKILL.md", "evidence-free PASS claims")
    require_contains(findings, audit_skill / "SKILL.md", "coordinator-authored specialist artifacts")
    require_contains(findings, audit_skill / "SKILL.md", ".opencode/state/invocation-log.jsonl")
    require_absent(findings, audit_skill / "SKILL.md", "read-only skill")
    require_absent(findings, audit_skill / "agents" / "openai.yaml", "read-only diagnosis")
    require_contains(findings, repair_skill / "SKILL.md", "run `../project-skill-bootstrap/SKILL.md`")
    require_contains(findings, repair_skill / "SKILL.md", "run `../opencode-team-bootstrap/SKILL.md`")
    require_contains(findings, repair_skill / "SKILL.md", "run `../agent-prompt-engineering/SKILL.md`")
    require_contains(findings, repair_skill / "SKILL.md", "manually copy that pack into the Scafforge dev repo first")
    require_contains(findings, repair_skill / "SKILL.md", "repeat repair after a prior audit->repair attempt already failed")
    require_contains(findings, repair_skill / "SKILL.md", "Treat deprecated package-managed defaults as repair drift, not protected intent")
    require_contains(findings, repair_skill / "SKILL.md", ".opencode/skills/ticket-execution/SKILL.md")
    require_contains(findings, repair_skill / "SKILL.md", "coordinator-authored PASS artifacts")
    require_contains(findings, repair_skill / "SKILL.md", "verification failed and then later recovered with real command evidence")
    require_contains(findings, repair_skill / "SKILL.md", "--diagnosis-output-dir <writable-path>")
    require_contains(findings, repair_skill / "SKILL.md", "--repair-basis-diagnosis <diagnosis-dir-or-manifest>")
    require_contains(findings, repair_skill / "SKILL.md", "package work first")
    require_contains(findings, repair_skill / "SKILL.md", "do not call the repo clean")
    require_contains(findings, repair_skill / "SKILL.md", "automatically carry forward transcript-backed diagnosis evidence")
    require_contains(findings, repair_skill / "SKILL.md", "current-state cleanliness from causal-regression verification")
    require_contains(findings, repair_skill / "SKILL.md", ".opencode/state/latest-handoff.md")
    require_contains(findings, repair_skill / "SKILL.md", 'ready for continued development')
    require_contains(findings, repair_skill / "SKILL.md", "If `BOOT001` or `BOOT002` was part of the repair basis")
    require_contains(findings, repair_skill / "SKILL.md", "same incompatible command trace after managed refresh")
    require_absent(findings, repair_skill / "SKILL.md", "Pass `--supporting-log <path>` when the repair basis depended on transcript evidence")
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", "supporting_log")
    require_contains(findings, repair_skill / "scripts" / "apply_repo_process_repair.py", '"pending_process_verification": pending_process_verification')
    require_reference_sync(
        findings,
        audit_skill / "references" / "process-smells.md",
        repair_skill / "references" / "process-smells.md",
        label="process smell references",
    )
    require_reference_sync(
        findings,
        audit_skill / "references" / "repair-playbook.md",
        repair_skill / "references" / "repair-playbook.md",
        label="repair playbook references",
    )

    bootstrap_script = ROOT / "skills" / "repo-scaffold-factory" / "scripts" / "bootstrap_repo_scaffold.py"
    require_contains(findings, bootstrap_script, '"project_specific_follow_up": [')
    require_contains(findings, bootstrap_script, '".opencode/skills",')

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
