from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FULL_BOOTSTRAP = ROOT / "skills" / "repo-scaffold-factory" / "scripts" / "bootstrap_repo_scaffold.py"
OPENCODE_BOOTSTRAP = ROOT / "skills" / "opencode-team-bootstrap" / "scripts" / "bootstrap_opencode_team.py"
DOCTOR = ROOT / "skills" / "repo-process-doctor" / "scripts" / "audit_repo_process.py"
CLI = ROOT / "bin" / "scafforge.mjs"
CHECKLIST = ROOT / "skills" / "repo-scaffold-factory" / "references" / "opencode-conformance-checklist.json"
PROFILES_DIR = ROOT / "skills" / "repo-scaffold-factory" / "profiles"
TEXT_SUFFIXES = {".md", ".json", ".jsonc", ".txt", ".ts", ".js", ".mjs", ".cjs", ".yaml", ".yml"}


def run(command: list[str], cwd: Path, *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, input=input_text)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
    return result


def load_checklist() -> dict[str, object]:
    checklist = json.loads(CHECKLIST.read_text(encoding="utf-8"))
    if not isinstance(checklist, dict):
        raise RuntimeError("opencode-conformance-checklist.json must be a JSON object")
    return checklist


def repo_relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def expected_file_inventory(base_dir: Path, root: Path) -> list[dict[str, str]]:
    if not base_dir.exists():
        return []

    items: list[dict[str, str]] = []
    for path in sorted((candidate for candidate in base_dir.rglob("*") if candidate.is_file()), key=lambda candidate: candidate.as_posix()):
        relative = path.relative_to(base_dir)
        items.append(
            {
                "id": relative.with_suffix("").as_posix(),
                "path": repo_relative(path, root),
            }
        )
    return items


def expected_skill_inventory(skills_dir: Path, root: Path) -> list[dict[str, object]]:
    if not skills_dir.exists():
        return []

    items: list[dict[str, object]] = []
    for skill_dir in sorted((candidate for candidate in skills_dir.iterdir() if candidate.is_dir()), key=lambda candidate: candidate.name):
        skill: dict[str, object] = {
            "id": skill_dir.name,
            "path": repo_relative(skill_dir, root),
            "entrypoint": repo_relative(skill_dir / "SKILL.md", root),
        }
        assets = [
            repo_relative(path, root)
            for path in sorted(
                (candidate for candidate in skill_dir.rglob("*") if candidate.is_file() and candidate.name != "SKILL.md"),
                key=lambda candidate: candidate.as_posix(),
            )
        ]
        if assets:
            skill["assets"] = assets
        items.append(skill)
    return items


def load_profile(profile_name: str) -> dict[str, object]:
    return json.loads((PROFILES_DIR / f"{profile_name}.json").read_text(encoding="utf-8"))


def iter_text_files(root: Path) -> list[Path]:
    return sorted(
        (
            candidate
            for candidate in root.rglob("*")
            if candidate.is_file() and candidate.suffix.lower() in TEXT_SUFFIXES
        ),
        key=lambda candidate: candidate.as_posix(),
    )


def verify_help_surfaces() -> None:
    cli_help = run(["node", str(CLI), "--help"], ROOT).stdout
    for needle in (
        "scafforge init [options]",
        "scafforge render-full [--profile full|minimum] <args...>",
        "scafforge render-opencode [--profile full|minimum] <args...>",
        "scafforge validate-contract",
    ):
        if needle not in cli_help:
            raise RuntimeError(f"CLI help is missing required text: {needle}")

    init_help = run(["node", str(CLI), "init", "--help"], ROOT).stdout
    for needle in (
        "skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py",
        "--profile <name>",
        "--scope <full|opencode>",
        "--yes",
    ):
        if needle not in init_help:
            raise RuntimeError(f"Init help is missing required text: {needle}")


def verify_scaffold_manifest(dest: Path, *, expected_scope: str, expected_profile: str) -> None:
    manifest_path = dest / ".opencode" / "meta" / "scaffold-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if manifest.get("schema_version") != 1:
        raise RuntimeError("scaffold-manifest.json has an unexpected schema_version")
    if manifest.get("manifest_kind") != "scafforge-scaffold":
        raise RuntimeError("scaffold-manifest.json has an unexpected manifest_kind")
    if manifest.get("ownership") != "generator-owned":
        raise RuntimeError("scaffold-manifest.json must remain generator-owned")
    if manifest.get("generator", {}).get("generation_scope") != expected_scope:
        raise RuntimeError("scaffold-manifest.json has an unexpected generation_scope")
    if manifest.get("generator", {}).get("generation_profile", {}).get("name") != expected_profile:
        raise RuntimeError("scaffold-manifest.json has an unexpected generation_profile")

    expected_inventory = {
        "agents": expected_file_inventory(dest / ".opencode" / "agents", dest),
        "commands": expected_file_inventory(dest / ".opencode" / "commands", dest),
        "plugins": expected_file_inventory(dest / ".opencode" / "plugins", dest),
        "tools": expected_file_inventory(dest / ".opencode" / "tools", dest),
        "skills": expected_skill_inventory(dest / ".opencode" / "skills", dest),
    }
    if manifest.get("inventory") != expected_inventory:
        raise RuntimeError("scaffold-manifest.json inventory does not match rendered scaffold contents")

    expected_counts = {category: len(entries) for category, entries in expected_inventory.items()}
    if manifest.get("counts") != expected_counts:
        raise RuntimeError("scaffold-manifest.json counts do not match rendered scaffold contents")


def verify_bootstrap_provenance(dest: Path, *, expected_scope: str, expected_profile: str) -> None:
    provenance = json.loads((dest / ".opencode" / "meta" / "bootstrap-provenance.json").read_text(encoding="utf-8"))
    if provenance.get("generation_scope") != expected_scope:
        raise RuntimeError("bootstrap-provenance.json has an unexpected generation_scope")
    if provenance.get("generation_profile", {}).get("name") != expected_profile:
        raise RuntimeError("bootstrap-provenance.json has an unexpected generation_profile")


def verify_profile_selection(dest: Path, *, profile_name: str, agent_prefix: str) -> None:
    profile = load_profile(profile_name)
    for selector in profile["include"]:
        rendered_selector = selector.replace("__AGENT_PREFIX__", agent_prefix)
        if not (dest / rendered_selector).exists():
            raise RuntimeError(f"Profile {profile_name} did not render expected path: {rendered_selector}")
    for selector in profile.get("exclude", []):
        rendered_selector = selector.replace("__AGENT_PREFIX__", agent_prefix)
        if (dest / rendered_selector).exists():
            raise RuntimeError(f"Profile {profile_name} unexpectedly rendered excluded path: {rendered_selector}")


def verify_baseline_contract(dest: Path, *, agent_prefix: str) -> None:
    required_paths = [
        f".opencode/agents/{agent_prefix}-docs-handoff.md",
        f".opencode/agents/{agent_prefix}-implementer.md",
        f".opencode/agents/{agent_prefix}-plan-review.md",
        f".opencode/agents/{agent_prefix}-planner.md",
        f".opencode/agents/{agent_prefix}-reviewer-code.md",
        f".opencode/agents/{agent_prefix}-reviewer-security.md",
        f".opencode/agents/{agent_prefix}-team-leader.md",
        f".opencode/agents/{agent_prefix}-tester-qa.md",
        ".opencode/commands/kickoff.md",
        ".opencode/commands/resume.md",
        ".opencode/config/stage-gate.json",
        ".opencode/plugins/invocation-tracker.ts",
        ".opencode/plugins/session-compactor.ts",
        ".opencode/plugins/stage-gate-enforcer.ts",
        ".opencode/plugins/ticket-sync.ts",
        ".opencode/plugins/tool-guard.ts",
        ".opencode/skills/docs-and-handoff/SKILL.md",
        ".opencode/skills/project-context/SKILL.md",
        ".opencode/skills/repo-navigation/SKILL.md",
        ".opencode/skills/stack-standards/SKILL.md",
        ".opencode/skills/ticket-execution/SKILL.md",
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
    ]
    missing = [relative for relative in required_paths if not (dest / relative).exists()]
    if missing:
        raise RuntimeError("Rendered scaffold is missing baseline contract paths:\n" + "\n".join(missing))


def verify_no_unresolved_placeholders(dest: Path, checklist: dict[str, object]) -> None:
    placeholder_tokens = [str(value) for value in checklist.get("placeholder_tokens", [])]
    leaks: list[str] = []
    for path in iter_text_files(dest):
        text = path.read_text(encoding="utf-8")
        matched = [token for token in placeholder_tokens if token in text]
        if matched:
            leaks.append(f"{repo_relative(path, dest)} -> {', '.join(matched)}")
    if leaks:
        raise RuntimeError("Rendered scaffold still contains unresolved placeholders:\n" + "\n".join(leaks))


def verify_no_legacy_markers(dest: Path, checklist: dict[str, object]) -> None:
    legacy_markers = [str(value) for value in checklist.get("legacy_markers", [])]
    offenders: list[str] = []
    for path in iter_text_files(dest):
        text = path.read_text(encoding="utf-8")
        for marker in legacy_markers:
            if marker in text:
                offenders.append(f"{repo_relative(path, dest)} -> {marker}")
    if offenders:
        raise RuntimeError("Rendered scaffold still contains legacy markers:\n" + "\n".join(offenders))


def verify_doctor_clean(dest: Path) -> None:
    result = run(["python", str(DOCTOR), str(dest), "--format", "json", "--fail-on", "warning"], ROOT)
    payload = json.loads(result.stdout)
    if payload.get("finding_count") != 0:
        raise RuntimeError(f"repo-process-doctor reported findings for {dest}:\n{json.dumps(payload, indent=2)}")


def verify_render(dest: Path, *, expect_full_repo: bool, expected_scope: str, expected_profile: str, agent_prefix: str) -> None:
    checklist = load_checklist()
    for relative in checklist["required_files"]:
        path = dest / relative
        if expect_full_repo or str(relative).startswith(".opencode") or str(relative) == "opencode.jsonc":
            if not path.exists():
                raise RuntimeError(f"Missing expected file: {path}")

    for relative in checklist["required_directories"]:
        path = dest / relative
        if expect_full_repo or str(relative).startswith(".opencode"):
            if not path.exists():
                raise RuntimeError(f"Missing expected directory: {path}")

    manifest = json.loads((dest / "tickets" / "manifest.json").read_text(encoding="utf-8")) if expect_full_repo else None
    if manifest is not None and "tickets" not in manifest:
        raise RuntimeError("tickets/manifest.json is missing a tickets key")

    verify_profile_selection(dest, profile_name=expected_profile, agent_prefix=agent_prefix)
    verify_baseline_contract(dest, agent_prefix=agent_prefix)
    verify_bootstrap_provenance(dest, expected_scope=expected_scope, expected_profile=expected_profile)
    verify_scaffold_manifest(dest, expected_scope=expected_scope, expected_profile=expected_profile)
    verify_no_unresolved_placeholders(dest, checklist)
    verify_no_legacy_markers(dest, checklist)
    verify_doctor_clean(dest)


def common_args(dest: Path, *, profile: str) -> list[str]:
    return [
        "--dest",
        str(dest),
        "--project-name",
        "Smoke Example",
        "--project-slug",
        "smoke-example",
        "--agent-prefix",
        "smoke",
        "--model-provider",
        "openrouter",
        "--planner-model",
        "openrouter/anthropic/claude-sonnet-4.5",
        "--implementer-model",
        "openrouter/openai/gpt-5-codex",
        "--utility-model",
        "openrouter/openai/gpt-5-mini",
        "--profile",
        profile,
        "--stack-label",
        "framework-agnostic",
        "--force",
    ]


def render_case(dest: Path, *, scope: str, profile: str) -> None:
    if scope == "full" and profile == "full":
        run(["node", str(CLI), "render-full", *common_args(dest, profile=profile), "--scope", scope], ROOT)
        return

    if scope == "full":
        run(["python", str(FULL_BOOTSTRAP), *common_args(dest, profile=profile), "--scope", scope], ROOT)
        return

    if profile == "full":
        run(["node", str(CLI), "render-opencode", *common_args(dest, profile=profile)], ROOT)
        return

    run(["python", str(OPENCODE_BOOTSTRAP), *common_args(dest, profile=profile)], ROOT)


def main() -> int:
    workspace = Path(tempfile.mkdtemp(prefix="scafforge-smoke-"))
    try:
        verify_help_surfaces()

        cases = [
            ("full-full", "full", "full"),
            ("full-minimum", "full", "minimum"),
            ("opencode-full", "opencode", "full"),
            ("opencode-minimum", "opencode", "minimum"),
        ]

        for folder_name, scope, profile in cases:
            dest = workspace / folder_name
            render_case(dest, scope=scope, profile=profile)
            verify_render(
                dest,
                expect_full_repo=scope == "full",
                expected_scope=scope,
                expected_profile=profile,
                agent_prefix="smoke",
            )

        print("Scafforge smoke test passed.")
        return 0
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
