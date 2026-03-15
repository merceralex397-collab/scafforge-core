from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FLOW_MANIFEST = ROOT / "skills" / "skill-flow-manifest.json"
CHECKLIST = ROOT / "skills" / "repo-scaffold-factory" / "references" / "opencode-conformance-checklist.json"
PROFILES_DIR = ROOT / "skills" / "repo-scaffold-factory" / "profiles"
TEMPLATE_ROOT = ROOT / "skills" / "repo-scaffold-factory" / "assets" / "project-template"
CLI = ROOT / "bin" / "scafforge.mjs"


@dataclass
class Finding:
    severity: str
    message: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(read_text(path))


def iter_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return [candidate for candidate in path.rglob("*") if candidate.is_file()]


def add_missing(findings: list[Finding], path: Path) -> None:
    findings.append(Finding("error", f"Missing required file: {path.relative_to(ROOT)}"))


def require_contains(findings: list[Finding], path: Path, needle: str) -> None:
    if not path.exists():
        add_missing(findings, path)
        return
    if needle not in read_text(path):
        findings.append(Finding("error", f"{path.relative_to(ROOT)} does not contain required text: {needle}"))


def run(command: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)


def load_checklist(findings: list[Finding]) -> dict[str, object] | None:
    if not CHECKLIST.exists():
        add_missing(findings, CHECKLIST)
        return None

    checklist = read_json(CHECKLIST)
    if not isinstance(checklist, dict):
        findings.append(Finding("error", f"{CHECKLIST.relative_to(ROOT)} is not a JSON object"))
        return None

    required_list_keys = (
        "required_files",
        "generated_only_files",
        "required_directories",
        "required_skill_ids",
        "placeholder_tokens",
        "legacy_markers",
    )
    for key in required_list_keys:
        if not isinstance(checklist.get(key), list):
            findings.append(Finding("error", f"{CHECKLIST.relative_to(ROOT)} is missing a {key} list"))

    doc_template_map = checklist.get("doc_template_map")
    if not isinstance(doc_template_map, dict):
        findings.append(Finding("error", f"{CHECKLIST.relative_to(ROOT)} is missing a doc_template_map object"))

    return checklist


def validate_checklist_contract(findings: list[Finding], checklist: dict[str, object]) -> None:
    required_files = {str(value) for value in checklist.get("required_files", [])}
    generated_only = {str(value) for value in checklist.get("generated_only_files", [])}
    if not generated_only <= required_files:
        missing = sorted(generated_only - required_files)
        findings.append(
            Finding(
                "error",
                f"{CHECKLIST.relative_to(ROOT)} generated_only_files must also appear in required_files: {', '.join(missing)}",
            )
        )

    duplicate_tokens = sorted(
        token
        for token in {str(value) for value in checklist.get("placeholder_tokens", [])}
        if list(checklist.get("placeholder_tokens", [])).count(token) > 1
    )
    if duplicate_tokens:
        findings.append(
            Finding(
                "error",
                f"{CHECKLIST.relative_to(ROOT)} contains duplicate placeholder tokens: {', '.join(duplicate_tokens)}",
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
        "ticket-pack-builder:bootstrap",
        "project-skill-bootstrap:foundation",
        "repo-process-doctor:audit_or_apply_safe_repair",
        "handoff-brief",
    ]
    for item in expected:
        if item not in sequence:
            findings.append(Finding("error", f"Greenfield sequence is missing required step: {item}"))


def validate_core_docs(findings: list[Finding]) -> None:
    readme = ROOT / "README.md"
    agents = ROOT / "AGENTS.md"
    for path in (readme, agents):
        if not path.exists():
            add_missing(findings, path)
            return
    require_contains(findings, readme, "## Refined v1 product contract")
    require_contains(findings, readme, "## Canonical generated-repo truth hierarchy")
    require_contains(findings, agents, "## Product contract refinements")
    require_contains(findings, agents, "## Canonical generated-repo truth hierarchy")


def validate_template_surfaces(findings: list[Finding], checklist: dict[str, object]) -> None:
    if not TEMPLATE_ROOT.exists():
        findings.append(Finding("error", f"Missing template root: {TEMPLATE_ROOT.relative_to(ROOT)}"))
        return

    generated_only = {str(value) for value in checklist.get("generated_only_files", [])}
    for relative in checklist.get("required_files", []):
        if str(relative) in generated_only:
            continue
        path = TEMPLATE_ROOT / str(relative)
        if not path.exists():
            add_missing(findings, path)

    for skill_id in checklist.get("required_skill_ids", []):
        path = TEMPLATE_ROOT / ".opencode" / "skills" / str(skill_id) / "SKILL.md"
        if not path.exists():
            add_missing(findings, path)

    require_contains(findings, TEMPLATE_ROOT / "README.md", "## Truth hierarchy")
    require_contains(findings, TEMPLATE_ROOT / "README.md", ".opencode/config/stage-gate.json")
    require_contains(findings, TEMPLATE_ROOT / "README.md", ".opencode/meta/scaffold-manifest.json")
    require_contains(findings, TEMPLATE_ROOT / "README.md", ".opencode/meta/bootstrap-provenance.json")
    require_contains(findings, TEMPLATE_ROOT / "AGENTS.md", "## Truth hierarchy")
    require_contains(findings, TEMPLATE_ROOT / "AGENTS.md", ".opencode/config/stage-gate.json")
    require_contains(findings, TEMPLATE_ROOT / "AGENTS.md", ".opencode/meta/scaffold-manifest.json")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "process" / "tooling.md", ".opencode/config/stage-gate.json")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "process" / "tooling.md", ".opencode/meta/scaffold-manifest.json")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "process" / "workflow.md", ".opencode/config/stage-gate.json")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "spec" / "CANONICAL-BRIEF.md", "## Tooling and Model Constraints")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "spec" / "CANONICAL-BRIEF.md", "## Blocking Decisions")
    require_contains(findings, TEMPLATE_ROOT / "docs" / "spec" / "CANONICAL-BRIEF.md", "## Backlog Readiness")

    manifest_path = TEMPLATE_ROOT / "tickets" / "manifest.json"
    workflow_path = TEMPLATE_ROOT / ".opencode" / "state" / "workflow-state.json"
    if not manifest_path.exists():
        add_missing(findings, manifest_path)
        return
    if not workflow_path.exists():
        add_missing(findings, workflow_path)
        return

    try:
        manifest = read_json(manifest_path)
        workflow = read_json(workflow_path)
    except json.JSONDecodeError as error:
        findings.append(Finding("error", f"Template workflow state files must be valid JSON objects: {error}"))
        return

    if not isinstance(manifest, dict) or not isinstance(workflow, dict):
        findings.append(Finding("error", "Template workflow state files must be JSON objects"))
        return

    active_ticket = manifest.get("active_ticket")
    tickets = manifest.get("tickets")
    if not isinstance(active_ticket, str) or not isinstance(tickets, list):
        findings.append(Finding("error", "Template tickets/manifest.json is missing active_ticket or tickets"))
        return

    active_entry = next((ticket for ticket in tickets if isinstance(ticket, dict) and ticket.get("id") == active_ticket), None)
    if not isinstance(active_entry, dict):
        findings.append(Finding("error", f"Template manifest active ticket is missing: {active_ticket}"))
        return

    if workflow.get("active_ticket", active_ticket) != active_ticket:
        findings.append(Finding("error", "Template workflow-state active_ticket does not match tickets/manifest.json"))

    if active_entry.get("stage") != workflow.get("stage"):
        findings.append(Finding("error", "Template workflow-state stage does not match the active manifest ticket stage"))

    if active_entry.get("status") != workflow.get("status"):
        findings.append(Finding("error", "Template workflow-state status does not match the active manifest ticket status"))


def validate_profile_manifests(findings: list[Finding]) -> None:
    baseline_includes = {
        ".opencode/agents/__AGENT_PREFIX__-docs-handoff.md",
        ".opencode/agents/__AGENT_PREFIX__-implementer.md",
        ".opencode/agents/__AGENT_PREFIX__-plan-review.md",
        ".opencode/agents/__AGENT_PREFIX__-planner.md",
        ".opencode/agents/__AGENT_PREFIX__-reviewer-code.md",
        ".opencode/agents/__AGENT_PREFIX__-reviewer-security.md",
        ".opencode/agents/__AGENT_PREFIX__-team-leader.md",
        ".opencode/agents/__AGENT_PREFIX__-tester-qa.md",
        ".opencode/commands/kickoff.md",
        ".opencode/commands/resume.md",
        ".opencode/config/stage-gate.json",
        ".opencode/plugins/invocation-tracker.ts",
        ".opencode/plugins/session-compactor.ts",
        ".opencode/plugins/stage-gate-enforcer.ts",
        ".opencode/plugins/ticket-sync.ts",
        ".opencode/plugins/tool-guard.ts",
        ".opencode/skills/docs-and-handoff",
        ".opencode/skills/project-context",
        ".opencode/skills/repo-navigation",
        ".opencode/skills/stack-standards",
        ".opencode/skills/ticket-execution",
        ".opencode/state/.gitignore",
        ".opencode/state/artifacts/registry.json",
        ".opencode/state/workflow-state.json",
        ".opencode/tools/_workflow.ts",
        ".opencode/tools/artifact_register.ts",
        ".opencode/tools/artifact_write.ts",
        ".opencode/tools/context_snapshot.ts",
        ".opencode/tools/handoff_publish.ts",
        ".opencode/tools/skill_ping.ts",
        ".opencode/tools/ticket_lookup.ts",
        ".opencode/tools/ticket_update.ts",
    }
    expected_profiles = {
        "full": {
            "must_include": baseline_includes
            | {
                ".opencode/skills/isolation-guidance",
                ".opencode/skills/local-git-specialist",
                ".opencode/skills/research-delegation",
                ".opencode/skills/workflow-observability",
                ".opencode/agents/__AGENT_PREFIX__-utility-explore.md",
                ".opencode/agents/__AGENT_PREFIX__-utility-github-research.md",
                ".opencode/agents/__AGENT_PREFIX__-utility-shell-inspect.md",
                ".opencode/agents/__AGENT_PREFIX__-utility-summarize.md",
                ".opencode/agents/__AGENT_PREFIX__-utility-ticket-audit.md",
                ".opencode/agents/__AGENT_PREFIX__-utility-web-research.md",
            },
            "must_exclude": set(),
        },
        "minimum": {
            "must_include": baseline_includes,
            "must_exclude": {
                ".opencode/skills/isolation-guidance",
                ".opencode/skills/local-git-specialist",
                ".opencode/skills/research-delegation",
                ".opencode/skills/workflow-observability",
                ".opencode/agents/__AGENT_PREFIX__-utility-explore.md",
                ".opencode/agents/__AGENT_PREFIX__-utility-github-research.md",
                ".opencode/agents/__AGENT_PREFIX__-utility-shell-inspect.md",
                ".opencode/agents/__AGENT_PREFIX__-utility-summarize.md",
                ".opencode/agents/__AGENT_PREFIX__-utility-ticket-audit.md",
                ".opencode/agents/__AGENT_PREFIX__-utility-web-research.md",
            },
        },
    }

    discovered_profiles = sorted(PROFILES_DIR.glob("*.json"))
    if not discovered_profiles:
        findings.append(Finding("error", f"No profile manifests found under {PROFILES_DIR.relative_to(ROOT)}"))
        return

    if not any(path.stem == "full" for path in discovered_profiles):
        add_missing(findings, PROFILES_DIR / "full.json")

    for path in discovered_profiles:
        profile_name = path.stem
        expectations = expected_profiles.get(profile_name, {"must_include": baseline_includes, "must_exclude": set()})

        payload = read_json(path)
        if not isinstance(payload, dict):
            findings.append(Finding("error", f"{path.relative_to(ROOT)} is not a JSON object"))
            continue

        if payload.get("profile_id") != profile_name:
            findings.append(Finding("error", f"{path.relative_to(ROOT)} must declare profile_id '{profile_name}'"))

        include = payload.get("include")
        exclude = payload.get("exclude", [])
        if not isinstance(include, list) or not isinstance(exclude, list):
            findings.append(Finding("error", f"{path.relative_to(ROOT)} must declare include/exclude lists"))
            continue

        include_set = {str(value) for value in include}
        exclude_set = {str(value) for value in exclude}

        missing_includes = sorted(expectations["must_include"] - include_set)
        if missing_includes:
            findings.append(
                Finding(
                    "error",
                    f"{path.relative_to(ROOT)} is missing required selectors: {', '.join(missing_includes)}",
                )
            )

        missing_excludes = sorted(expectations["must_exclude"] - exclude_set)
        if missing_excludes:
            findings.append(
                Finding(
                    "error",
                    f"{path.relative_to(ROOT)} is missing required exclusions: {', '.join(missing_excludes)}",
                )
            )

        overlap = sorted(include_set & exclude_set)
        if overlap:
            findings.append(
                Finding(
                    "error",
                    f"{path.relative_to(ROOT)} overlaps include/exclude selectors: {', '.join(overlap)}",
                )
            )

        for selector in sorted(include_set | exclude_set):
            selector_path = TEMPLATE_ROOT / selector
            if not selector_path.exists():
                findings.append(Finding("error", f"{path.relative_to(ROOT)} references missing template selector: {selector}"))


def validate_no_hidden_defaults(findings: list[Finding], checklist: dict[str, object]) -> None:
    disallowed = [str(value) for value in checklist.get("legacy_markers", [])] + ["devdocs/research report.md", "research report.md"]
    scan_roots = [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "bin", ROOT / "scripts", ROOT / "skills", ROOT / "adapters"]
    skipped_files = {
        Path(__file__).resolve(),
        CHECKLIST.resolve(),
    }
    for scan_root in scan_roots:
        for path in iter_files(scan_root):
            if path.suffix not in {".md", ".mjs", ".py", ".ts", ".json", ".jsonc"}:
                continue
            if path.resolve() in skipped_files:
                continue
            text = read_text(path)
            for needle in disallowed:
                if needle in text:
                    findings.append(Finding("error", f"{path.relative_to(ROOT)} still contains disallowed legacy text: {needle}"))


def validate_cli_help_surfaces(findings: list[Finding]) -> None:
    if not CLI.exists():
        add_missing(findings, CLI)
        return

    cli_help = run(["node", str(CLI), "--help"])
    if cli_help.returncode != 0:
        findings.append(
            Finding(
                "error",
                f"node bin/scafforge.mjs --help failed with exit code {cli_help.returncode}: {cli_help.stderr.strip() or cli_help.stdout.strip()}",
            )
        )
    else:
        stdout = cli_help.stdout
        for needle in (
            "scafforge init [options]",
            "scafforge render-full [--profile full|minimum] <args...>",
            "scafforge render-opencode [--profile full|minimum] <args...>",
            "scafforge validate-contract",
        ):
            if needle not in stdout:
                findings.append(Finding("error", f"CLI help is missing required text: {needle}"))

    init_help = run(["node", str(CLI), "init", "--help"])
    if init_help.returncode != 0:
        findings.append(
            Finding(
                "error",
                f"node bin/scafforge.mjs init --help failed with exit code {init_help.returncode}: {init_help.stderr.strip() or init_help.stdout.strip()}",
            )
        )
    else:
        stdout = init_help.stdout
        for needle in (
            "skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py",
            "--profile <name>",
            "--scope <full|opencode>",
            "--yes",
        ):
            if needle not in stdout:
                findings.append(Finding("error", f"Init help is missing required text: {needle}"))


def main() -> int:
    findings: list[Finding] = []
    checklist = load_checklist(findings)
    if checklist is not None:
        validate_checklist_contract(findings, checklist)
    validate_flow_manifest(findings)
    validate_core_docs(findings)
    if checklist is not None:
        validate_template_surfaces(findings, checklist)
        validate_no_hidden_defaults(findings, checklist)
    validate_profile_manifests(findings)
    validate_cli_help_surfaces(findings)

    if findings:
        for finding in findings:
            print(f"[{finding.severity.upper()}] {finding.message}")
        return 1

    print("Scafforge contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
