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
    require_contains(findings, readme, "## Truth hierarchy")
    require_contains(findings, readme, "## Skill map")
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
        template / ".opencode" / "state" / "workflow-state.json",
        template / ".opencode" / "state" / "artifacts" / "registry.json",
        template / ".opencode" / "skills" / "research-delegation" / "SKILL.md",
        template / ".opencode" / "skills" / "local-git-specialist" / "SKILL.md",
        template / ".opencode" / "skills" / "isolation-guidance" / "SKILL.md",
    ]
    for path in required:
        if not path.exists():
            add_missing(findings, path)

    require_contains(findings, template / "README.md", "## Truth hierarchy")
    require_contains(findings, template / "AGENTS.md", "## Truth hierarchy")
    require_contains(findings, template / "docs" / "spec" / "CANONICAL-BRIEF.md", "## Tooling and Model Constraints")
    require_contains(findings, template / "docs" / "spec" / "CANONICAL-BRIEF.md", "## Blocking Decisions")
    require_contains(findings, template / "docs" / "spec" / "CANONICAL-BRIEF.md", "## Backlog Readiness")


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
    validate_no_hidden_defaults(findings)

    if findings:
        for finding in findings:
            print(f"[{finding.severity.upper()}] {finding.message}")
        return 1

    print("Scafforge contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
