from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


TEXT_SUFFIXES = {
    ".md",
    ".json",
    ".jsonc",
    ".txt",
    ".ts",
    ".js",
    ".mjs",
    ".cjs",
    ".yaml",
    ".yml",
}

FULL_SCOPE_FILES = {
    "README.md",
    "AGENTS.md",
    "START-HERE.md",
    "opencode.jsonc",
    "docs",
    "tickets",
    ".opencode",
}

OPENCODE_SCOPE_FILES = {
    "opencode.jsonc",
    ".opencode",
}

PROCESS_CONTRACT_VERSION = 5
TICKET_CONTRACT_VERSION = 3
DEFAULT_PARALLEL_MODE = "sequential"


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "project"


def render_text(content: str, replacements: dict[str, str]) -> str:
    for key, value in replacements.items():
        content = content.replace(key, value)
    return content


def render_relative_path(path: Path, replacements: dict[str, str]) -> Path:
    rendered_parts = [render_text(part, replacements) for part in path.parts]
    return Path(*rendered_parts)


def build_model_operating_profile(
    *,
    model_provider: str,
    planner_model: str,
    implementer_model: str,
    utility_model: str,
) -> dict[str, str]:
    combined = " ".join((model_provider, planner_model, implementer_model, utility_model)).lower()
    if "minimax" in combined:
        return {
            "name": "Specific-instruction evidence-first profile",
            "description": (
                "Apply explicit, example-shaped, bounded instructions for the selected downstream "
                "models. Prefer direct evidence and concrete task framing over broad summaries."
            ),
            "rules": "\n".join(
                (
                    "- prefer clear and specific instructions",
                    "- state the purpose or why when it reduces ambiguity",
                    "- use example-shaped outputs when they make the expected shape concrete",
                    "- focus on one bounded goal at a time instead of broad parallel asks",
                    "- prefer direct evidence, command output, and cited repo surfaces over summaries",
                    "- stop on blockers instead of guessing or silently filling gaps",
                )
            ),
        }
    return {
        "name": "Evidence-first bounded-execution profile",
        "description": (
            "Apply explicit, scoped instructions for the selected downstream models. Keep tasks "
            "bounded, tie asks to canonical repo surfaces, and prefer evidence over narrative recap."
        ),
        "rules": "\n".join(
            (
                "- keep instructions explicit, scoped, and selection-specific",
                "- point back to canonical repo surfaces before acting on assumptions",
                "- use short example-shaped outputs when they remove ambiguity",
                "- keep each task focused on one bounded goal unless the brief proves safe separation",
                "- prefer concrete evidence and command output over narrative summaries",
                "- stop and surface blockers instead of guessing",
            )
        ),
    }


def should_copy(root_name: str, scope: str) -> bool:
    if scope == "opencode":
        return root_name in OPENCODE_SCOPE_FILES
    return root_name in FULL_SCOPE_FILES


def copy_template(template_root: Path, dest_root: Path, replacements: dict[str, str], scope: str, force: bool) -> list[Path]:
    created: list[Path] = []

    for source in template_root.iterdir():
        if not should_copy(source.name, scope):
            continue
        target = dest_root / source.name
        if source.is_dir():
            created.extend(copy_dir(source, target, replacements, force))
        else:
            write_file(source, target, replacements, force)
            created.append(target)
    return created


def copy_dir(source_dir: Path, dest_dir: Path, replacements: dict[str, str], force: bool) -> list[Path]:
    created: list[Path] = []
    dest_dir.mkdir(parents=True, exist_ok=True)
    for source in source_dir.rglob("*"):
        relative = render_relative_path(source.relative_to(source_dir), replacements)
        target = dest_dir / relative
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        write_file(source, target, replacements, force)
        created.append(target)
    return created


def write_file(source: Path, target: Path, replacements: dict[str, str], force: bool) -> None:
    if target.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing file: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix in TEXT_SUFFIXES:
        text = source.read_text(encoding="utf-8")
        target.write_text(render_text(text, replacements), encoding="utf-8")
    else:
        shutil.copy2(source, target)


def managed_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def template_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=managed_repo_root(),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip() or "unknown"


def write_bootstrap_provenance(
    dest_root: Path,
    *,
    project_name: str,
    project_slug: str,
    agent_prefix: str,
    scope: str,
    model_provider: str,
    planner_model: str,
    implementer_model: str,
    utility_model: str,
) -> None:
    steps = (
        ["repo-scaffold-factory/render-full-scaffold"]
        if scope == "full"
        else ["opencode-team-bootstrap/render-opencode-layer", "repo-scaffold-factory/render-opencode-scope"]
    )
    payload = {
        "managed_repo": str(managed_repo_root()),
        "template_commit": template_commit(),
        "template_asset_root": "skills/repo-scaffold-factory/assets/project-template",
        "project_name": project_name,
        "project_slug": project_slug,
        "agent_prefix": agent_prefix,
        "generation_scope": scope,
        "runtime_models": {
            "provider": model_provider,
            "planner": planner_model,
            "implementer": implementer_model,
            "utility": utility_model,
        },
        "bootstrap_steps": steps,
        "tracking": {
            "invocation_log": ".opencode/state/invocation-log.jsonl",
            "skill_ping_tool": "skill_ping",
            "tracker_plugin": "invocation-tracker",
        },
        "workflow_contract": {
            "process_version": PROCESS_CONTRACT_VERSION,
            "ticket_contract_version": TICKET_CONTRACT_VERSION,
            "parallel_mode": DEFAULT_PARALLEL_MODE,
            "manager_hierarchy": {
                "first_class_scaffold_profile": False,
                "advanced_customization_allowed": True,
            },
            "post_migration_verification": {
                "enabled": True,
                "backlog_verifier_agent": f"{agent_prefix}-backlog-verifier",
                "ticket_creator_agent": f"{agent_prefix}-ticket-creator",
            },
        },
        "managed_surfaces": {
            "replace_on_retrofit": [
                "opencode.jsonc",
                ".opencode/tools",
                ".opencode/plugins",
                ".opencode/commands",
                "scaffold-managed .opencode/skills",
                "docs/process/workflow.md",
                "docs/process/tooling.md",
                "docs/process/model-matrix.md",
                "docs/process/git-capability.md",
                "START-HERE.md managed block",
            ],
            "project_specific_follow_up": [
                ".opencode/agents",
                "docs/process/agent-catalog.md",
            ],
            "preserve_project_sources": [
                "docs/spec/CANONICAL-BRIEF.md",
                "tickets/manifest.json",
                "tickets/*.md",
                ".opencode/state/artifacts",
                ".opencode/state/bootstrap",
                ".opencode/state/plans",
                ".opencode/state/implementations",
                ".opencode/state/reviews",
                ".opencode/state/qa",
                ".opencode/state/smoke-tests",
                ".opencode/state/handoffs",
            ],
        },
        "repair_history": [],
    }

    target = dest_root / ".opencode" / "meta" / "bootstrap-provenance.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def ensure_state_directories(dest_root: Path) -> None:
    for relative in (
        ".opencode/state/plans",
        ".opencode/state/implementations",
        ".opencode/state/reviews",
        ".opencode/state/qa",
        ".opencode/state/smoke-tests",
        ".opencode/state/handoffs",
        ".opencode/state/artifacts",
        ".opencode/state/bootstrap",
    ):
        (dest_root / relative).mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render the repository scaffold template.")
    parser.add_argument("--dest", required=True, help="Destination repository root")
    parser.add_argument("--project-name", required=True, help="Human-facing project name")
    parser.add_argument("--project-slug", help="Slug used in filenames and defaults")
    parser.add_argument("--agent-prefix", help="OpenCode agent prefix")
    parser.add_argument(
        "--model-provider",
        required=True,
        help="Explicit provider label chosen for this scaffold run",
    )
    parser.add_argument(
        "--planner-model",
        required=True,
        help="Explicit planner/reviewer/team-lead model string",
    )
    parser.add_argument(
        "--implementer-model",
        required=True,
        help="Explicit implementer model string",
    )
    parser.add_argument(
        "--utility-model",
        help="Explicit utility/docs/QA/helper model string; defaults to planner-model when omitted",
    )
    parser.add_argument(
        "--scope",
        choices=("full", "opencode"),
        default="full",
        help="Render the full scaffold or only the OpenCode layer",
    )
    parser.add_argument(
        "--stack-label",
        default="framework-agnostic",
        help="Label used in generated docs for the current stack mode",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dest_root = Path(args.dest).expanduser().resolve()
    template_root = Path(__file__).resolve().parent.parent / "assets" / "project-template"

    slug = args.project_slug or slugify(args.project_name)
    agent_prefix = args.agent_prefix or slug
    planner_model = args.planner_model
    implementer_model = args.implementer_model
    utility_model = args.utility_model or planner_model
    model_profile = build_model_operating_profile(
        model_provider=args.model_provider,
        planner_model=planner_model,
        implementer_model=implementer_model,
        utility_model=utility_model,
    )

    replacements = {
        "__PROJECT_NAME__": args.project_name,
        "__PROJECT_SLUG__": slug,
        "__AGENT_PREFIX__": agent_prefix,
        "__MODEL_PROVIDER__": args.model_provider,
        "__PLANNER_MODEL__": planner_model,
        "__IMPLEMENTER_MODEL__": implementer_model,
        "__UTILITY_MODEL__": utility_model,
        "__MODEL_OPERATING_PROFILE_NAME__": model_profile["name"],
        "__MODEL_OPERATING_PROFILE_DESCRIPTION__": model_profile["description"],
        "__MODEL_OPERATING_PROFILE_RULES__": model_profile["rules"],
        "__STACK_LABEL__": args.stack_label,
    }

    dest_root.mkdir(parents=True, exist_ok=True)
    created = copy_template(template_root, dest_root, replacements, args.scope, args.force)
    ensure_state_directories(dest_root)
    write_bootstrap_provenance(
        dest_root,
        project_name=args.project_name,
        project_slug=slug,
        agent_prefix=agent_prefix,
        scope=args.scope,
        model_provider=args.model_provider,
        planner_model=planner_model,
        implementer_model=implementer_model,
        utility_model=utility_model,
    )

    print(f"Rendered {len(created)} files into {dest_root}")
    for path in created[:20]:
        print(f"- {path}")
    if len(created) > 20:
        print(f"... and {len(created) - 20} more files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
