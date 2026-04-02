from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import sys


SHARED_VERIFIER_PATH = Path(__file__).resolve().parents[2] / "scafforge-audit" / "scripts" / "shared_verifier.py"
SHARED_TYPES_PATH = Path(__file__).resolve().parents[2] / "scafforge-audit" / "scripts" / "shared_verifier_types.py"
TEXT_SUFFIXES = {".md", ".json", ".jsonc", ".ts", ".js", ".txt", ".yaml", ".yml"}
PLACEHOLDER_PATTERN = re.compile(r"__[A-Z0-9_]+__")


def load_shared_verifier():
    spec = spec_from_file_location("scafforge_generated_scaffold_verifier", SHARED_VERIFIER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load shared verifier from {SHARED_VERIFIER_PATH}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_shared_types():
    spec = spec_from_file_location("scafforge_generated_scaffold_types", SHARED_TYPES_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load shared verifier types from {SHARED_TYPES_PATH}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SHARED_VERIFIER = load_shared_verifier()
SHARED_TYPES = load_shared_types()
Finding = SHARED_TYPES.Finding
verify_greenfield_bootstrap_lane = SHARED_VERIFIER.verify_greenfield_bootstrap_lane
verify_greenfield_continuation = SHARED_VERIFIER.verify_greenfield_continuation


def jsonc_to_json(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)
    return text


def normalize_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def iter_text_files(repo_root: Path):
    for path in sorted(repo_root.rglob("*")):
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            yield path


def scaffold_finding(*, code: str, problem: str, root_cause: str, files: list[str], safer_pattern: str, evidence: list[str]):
    return Finding(
        code=code,
        severity="error",
        problem=problem,
        root_cause=root_cause,
        files=files,
        safer_pattern=safer_pattern,
        evidence=evidence,
        remediation_action=safer_pattern,
        remediation_target=files[0] if files else None,
    )


def placeholder_findings(repo_root: Path) -> list[object]:
    findings: list[object] = []
    for path in iter_text_files(repo_root):
        if "tickets/templates/" in normalize_path(path, repo_root):
            continue
        text = path.read_text(encoding="utf-8")
        hits = sorted(set(PLACEHOLDER_PATTERN.findall(text)))
        if hits:
            findings.append(
                scaffold_finding(
                    code="SCAFFOLD-001",
                    problem="The generated scaffold still contains unsubstituted placeholder tokens.",
                    root_cause="Template substitution did not fully render every placeholder before verification.",
                    files=[normalize_path(path, repo_root)],
                    safer_pattern="Render every template placeholder before publishing the scaffold and fail verification when residue remains.",
                    evidence=[f"Remaining placeholders: {', '.join(hits[:6])}"],
                )
            )
    return findings


def json_validity_findings(repo_root: Path) -> list[object]:
    findings: list[object] = []
    for relative in ("tickets/manifest.json", ".opencode/state/workflow-state.json", "opencode.jsonc"):
        path = repo_root / relative
        try:
            text = path.read_text(encoding="utf-8")
            if path.suffix == ".jsonc":
                try:
                    json.loads(text)
                except json.JSONDecodeError:
                    json.loads(jsonc_to_json(text))
            else:
                json.loads(text)
        except Exception as exc:
            findings.append(
                scaffold_finding(
                    code="SCAFFOLD-002",
                    problem="A canonical generated JSON or JSONC surface is invalid.",
                    root_cause="The scaffold emitted malformed structured data into a file that downstream tools must parse.",
                    files=[relative],
                    safer_pattern="Validate generated manifest, workflow-state, and JSONC config files during scaffold verification before handoff.",
                    evidence=[str(exc)],
                )
            )
    return findings


def agent_reference_findings(repo_root: Path) -> list[object]:
    findings: list[object] = []
    tools = {path.stem for path in (repo_root / ".opencode" / "tools").glob("*.ts")}
    skills = {path.parent.name for path in (repo_root / ".opencode" / "skills").glob("*/SKILL.md")}
    tasks = {path.stem for path in (repo_root / ".opencode" / "agents").glob("*.md")}
    for path in sorted((repo_root / ".opencode" / "agents").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        missing: list[str] = []
        section: str | None = None
        for raw_line in text.splitlines():
            if raw_line.startswith("  skill:"):
                section = "skill"
                continue
            if raw_line.startswith("  task:"):
                section = "task"
                continue
            if raw_line.startswith("  bash:"):
                section = "bash"
                continue
            if raw_line.startswith("---") or not raw_line.startswith(" "):
                section = None
            top_level = re.match(r"^  ([A-Za-z0-9_.-]+): allow$", raw_line)
            nested = re.match(r'^    "?([^":]+)"?: allow$', raw_line)
            if top_level:
                name = top_level.group(1)
                if name not in {"webfetch"} and name not in tools:
                    missing.append(f"tool:{name}")
            elif nested and section == "skill":
                name = nested.group(1)
                if name != "*" and name not in skills:
                    missing.append(f"skill:{name}")
            elif nested and section == "task":
                name = nested.group(1)
                pattern = re.compile("^" + re.escape(name).replace("\\*", ".*") + "$")
                if name not in {"*", "explore"} and not any(pattern.fullmatch(task) for task in tasks):
                    missing.append(f"task:{name}")
        if missing:
            findings.append(
                scaffold_finding(
                    code="SCAFFOLD-003",
                    problem="A generated agent references a tool, skill, or task that does not exist in the scaffold.",
                    root_cause="Template allowlists drifted from the actual generated tool, skill, or agent inventory.",
                    files=[normalize_path(path, repo_root)],
                    safer_pattern="Keep agent allowlists aligned with generated tools, skills, and task agents, and fail verification when cross-references drift.",
                    evidence=[", ".join(sorted(set(missing)))],
                )
            )
    return findings


def project_name_consistency_findings(repo_root: Path) -> list[object]:
    provenance_path = repo_root / ".opencode" / "meta" / "bootstrap-provenance.json"
    if not provenance_path.exists():
        return []
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    project_name = provenance.get("project_name") if isinstance(provenance, dict) else None
    if not isinstance(project_name, str) or not project_name.strip():
        return []
    project_name = project_name.strip()
    mismatches: list[str] = []
    for relative in ("README.md", "AGENTS.md", "START-HERE.md"):
        text = (repo_root / relative).read_text(encoding="utf-8")
        if project_name not in text:
            mismatches.append(relative)
    if mismatches:
        return [
            scaffold_finding(
                code="SCAFFOLD-004",
                problem="Generated restart and overview surfaces do not consistently reference the same project name.",
                root_cause="One or more template surfaces were rendered without the canonical project name from bootstrap provenance.",
                files=mismatches,
                safer_pattern="Render README, AGENTS, START-HERE, and related overview surfaces from one canonical project name source.",
                evidence=[f"Expected project name: {project_name}"],
            )
        ]
    return []


def scaffold_content_findings(repo_root: Path) -> list[object]:
    return [
        *placeholder_findings(repo_root),
        *json_validity_findings(repo_root),
        *agent_reference_findings(repo_root),
        *project_name_consistency_findings(repo_root),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify that a generated scaffold is immediately continuable before greenfield handoff."
    )
    parser.add_argument("repo_root", help="Generated repository root to verify.")
    parser.add_argument("--format", choices=("text", "json", "both"), default="text")
    parser.add_argument(
        "--verification-kind",
        choices=("bootstrap-lane", "greenfield-continuation"),
        default="greenfield-continuation",
        help="Which greenfield proof layer to verify.",
    )
    return parser.parse_args()


def findings_payload(verification_kind: str, findings: list[object]) -> dict[str, object]:
    payload = {
        "repo_root": None,
        "verification_kind": verification_kind,
        "verification_passed": not findings,
        "finding_count": len(findings),
        "findings": [asdict(finding) for finding in findings],
    }
    if verification_kind == "greenfield_continuation":
        payload["immediately_continuable"] = not findings
    if verification_kind == "greenfield_bootstrap_lane":
        payload["bootstrap_lane_valid"] = not findings
    return payload


def render_text(repo_root: Path, verification_kind: str, findings: list[object]) -> str:
    if not findings:
        if verification_kind == "greenfield_bootstrap_lane":
            return f"PASS: {repo_root} preserves one valid bootstrap lane."
        return f"PASS: {repo_root} is immediately continuable."

    if verification_kind == "greenfield_bootstrap_lane":
        lines = [f"FAIL: {repo_root} does not preserve one valid bootstrap lane.", ""]
    else:
        lines = [f"FAIL: {repo_root} is not immediately continuable.", ""]
    for finding in findings:
        lines.append(f"[{finding.code}] {finding.problem}")
        if finding.evidence:
            lines.append(f"  Evidence: {finding.evidence[0]}")
        if getattr(finding, "remediation_action", None):
            lines.append(f"  Remediation: {finding.remediation_action}")
        if getattr(finding, "remediation_target", None):
            lines.append(f"  Target: {finding.remediation_target}")
        if getattr(finding, "is_user_action", False):
            lines.append("  User action required: yes")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    verification_kind = (
        "greenfield_bootstrap_lane"
        if args.verification_kind == "bootstrap-lane"
        else "greenfield_continuation"
    )
    findings = (
        verify_greenfield_bootstrap_lane(repo_root)
        if verification_kind == "greenfield_bootstrap_lane"
        else verify_greenfield_continuation(repo_root)
    )
    findings.extend(scaffold_content_findings(repo_root))
    payload = findings_payload(verification_kind, findings)
    payload["repo_root"] = str(repo_root)

    if args.format in {"text", "both"}:
        print(render_text(repo_root, verification_kind, findings))
    if args.format in {"json", "both"}:
        if args.format == "both":
            print()
        print(json.dumps(payload, indent=2))

    return 0 if not findings else 2


if __name__ == "__main__":
    raise SystemExit(main())
