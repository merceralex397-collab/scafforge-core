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


def profile_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "profiles"


def available_profiles() -> list[str]:
    return sorted(path.stem for path in profile_dir().glob("*.json"))


def load_profile(profile_name: str) -> dict[str, object]:
    path = profile_dir() / f"{profile_name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Unknown scaffold profile '{profile_name}': {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("profile_id") != profile_name:
        raise ValueError(f"Profile manifest {path} must declare profile_id '{profile_name}'")
    if not isinstance(payload.get("include"), list):
        raise ValueError(f"Profile manifest {path} must include an include list")
    if not isinstance(payload.get("exclude", []), list):
        raise ValueError(f"Profile manifest {path} must include an exclude list when present")
    return payload


def scope_roots(scope: str) -> set[str]:
    if scope == "opencode":
        return OPENCODE_SCOPE_FILES
    return FULL_SCOPE_FILES


def path_selected(relative_path: Path, selectors: set[str]) -> bool:
    relative = relative_path.as_posix()
    return any(
        selector == relative
        or selector.startswith(relative + "/")
        or relative.startswith(selector + "/")
        for selector in selectors
    )


def should_copy(relative_path: Path, scope: str, profile: dict[str, object]) -> bool:
    if not relative_path.parts or relative_path.parts[0] not in scope_roots(scope):
        return False
    if relative_path.parts[0] != ".opencode":
        return True
    if relative_path.as_posix() == ".opencode":
        return True
    selectors = {str(value) for value in profile["include"]}
    return path_selected(relative_path, selectors)


def copy_template(
    template_root: Path,
    dest_root: Path,
    replacements: dict[str, str],
    scope: str,
    profile: dict[str, object],
    force: bool,
) -> list[Path]:
    created: list[Path] = []

    for source in template_root.iterdir():
        created.extend(copy_entry(source, template_root, dest_root, replacements, scope, profile, force))
    return created


def copy_entry(
    source: Path,
    template_root: Path,
    dest_root: Path,
    replacements: dict[str, str],
    scope: str,
    profile: dict[str, object],
    force: bool,
) -> list[Path]:
    created: list[Path] = []

    relative_path = source.relative_to(template_root)
    if not should_copy(relative_path, scope, profile):
        return created

    target = dest_root / render_relative_path(relative_path, replacements)
    if source.is_dir():
        target.mkdir(parents=True, exist_ok=True)
        for child in source.iterdir():
            created.extend(copy_entry(child, template_root, dest_root, replacements, scope, profile, force))
        return created

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


def repo_relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def inventory_file_items(base_dir: Path, repo_root: Path) -> list[dict[str, str]]:
    if not base_dir.exists():
        return []

    items: list[dict[str, str]] = []
    for path in sorted((candidate for candidate in base_dir.rglob("*") if candidate.is_file()), key=lambda candidate: candidate.as_posix()):
        relative = path.relative_to(base_dir)
        items.append(
            {
                "id": relative.with_suffix("").as_posix(),
                "path": repo_relative(path, repo_root),
            }
        )
    return items


def inventory_skill_items(skills_dir: Path, repo_root: Path) -> list[dict[str, object]]:
    if not skills_dir.exists():
        return []

    items: list[dict[str, object]] = []
    for skill_dir in sorted((candidate for candidate in skills_dir.iterdir() if candidate.is_dir()), key=lambda candidate: candidate.name):
        skill_item: dict[str, object] = {
            "id": skill_dir.name,
            "path": repo_relative(skill_dir, repo_root),
            "entrypoint": repo_relative(skill_dir / "SKILL.md", repo_root),
        }
        asset_paths = [
            repo_relative(path, repo_root)
            for path in sorted(
                (candidate for candidate in skill_dir.rglob("*") if candidate.is_file() and candidate.name != "SKILL.md"),
                key=lambda candidate: candidate.as_posix(),
            )
        ]
        if asset_paths:
            skill_item["assets"] = asset_paths
        items.append(skill_item)
    return items


def write_scaffold_manifest(
    dest_root: Path,
    *,
    project_name: str,
    project_slug: str,
    agent_prefix: str,
    scope: str,
    profile_name: str,
    profile_description: str,
    model_provider: str,
    planner_model: str,
    implementer_model: str,
    utility_model: str,
) -> None:
    inventory = {
        "agents": inventory_file_items(dest_root / ".opencode" / "agents", dest_root),
        "commands": inventory_file_items(dest_root / ".opencode" / "commands", dest_root),
        "plugins": inventory_file_items(dest_root / ".opencode" / "plugins", dest_root),
        "tools": inventory_file_items(dest_root / ".opencode" / "tools", dest_root),
        "skills": inventory_skill_items(dest_root / ".opencode" / "skills", dest_root),
    }
    payload = {
        "schema_version": 1,
        "manifest_kind": "scafforge-scaffold",
        "ownership": "generator-owned",
        "generator": {
            "package_skill": "repo-scaffold-factory",
            "template_asset_root": "skills/repo-scaffold-factory/assets/project-template",
            "template_commit": template_commit(),
            "generation_scope": scope,
            "generation_profile": {
                "name": profile_name,
                "description": profile_description,
                "manifest": f"skills/repo-scaffold-factory/profiles/{profile_name}.json",
            },
        },
        "project": {
            "name": project_name,
            "slug": project_slug,
            "agent_prefix": agent_prefix,
            "runtime_models": {
                "provider": model_provider,
                "planner": planner_model,
                "implementer": implementer_model,
                "utility": utility_model,
            },
        },
        "paths": {
            "manifest": ".opencode/meta/scaffold-manifest.json",
            "bootstrap_provenance": ".opencode/meta/bootstrap-provenance.json",
        },
        "counts": {category: len(entries) for category, entries in inventory.items()},
        "inventory": inventory,
    }

    target = dest_root / ".opencode" / "meta" / "scaffold-manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_bootstrap_provenance(
    dest_root: Path,
    *,
    project_name: str,
    project_slug: str,
    agent_prefix: str,
    scope: str,
    profile_name: str,
    profile_description: str,
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
        "generation_profile": {
            "name": profile_name,
            "description": profile_description,
            "manifest": f"skills/repo-scaffold-factory/profiles/{profile_name}.json",
        },
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
        ".opencode/state/handoffs",
        ".opencode/state/artifacts",
    ):
        (dest_root / relative).mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render the repository scaffold template.")
    profiles = available_profiles()
    if "full" not in profiles:
        raise RuntimeError("Scafforge requires a full scaffold profile manifest")
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
        "--profile",
        choices=tuple(profiles),
        default="full",
        help="Scaffold profile to render; full remains the default safe contract",
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
    profile = load_profile(args.profile)

    slug = args.project_slug or slugify(args.project_name)
    agent_prefix = args.agent_prefix or slug
    planner_model = args.planner_model
    implementer_model = args.implementer_model
    utility_model = args.utility_model or planner_model

    replacements = {
        "__PROJECT_NAME__": args.project_name,
        "__PROJECT_SLUG__": slug,
        "__AGENT_PREFIX__": agent_prefix,
        "__MODEL_PROVIDER__": args.model_provider,
        "__PLANNER_MODEL__": planner_model,
        "__IMPLEMENTER_MODEL__": implementer_model,
        "__UTILITY_MODEL__": utility_model,
        "__STACK_LABEL__": args.stack_label,
    }

    dest_root.mkdir(parents=True, exist_ok=True)
    created = copy_template(template_root, dest_root, replacements, args.scope, profile, args.force)
    ensure_state_directories(dest_root)
    write_bootstrap_provenance(
        dest_root,
        project_name=args.project_name,
        project_slug=slug,
        agent_prefix=agent_prefix,
        scope=args.scope,
        profile_name=args.profile,
        profile_description=str(profile["description"]),
        model_provider=args.model_provider,
        planner_model=planner_model,
        implementer_model=implementer_model,
        utility_model=utility_model,
    )
    write_scaffold_manifest(
        dest_root,
        project_name=args.project_name,
        project_slug=slug,
        agent_prefix=agent_prefix,
        scope=args.scope,
        profile_name=args.profile,
        profile_description=str(profile["description"]),
        model_provider=args.model_provider,
        planner_model=planner_model,
        implementer_model=implementer_model,
        utility_model=utility_model,
    )

    print(f"Rendered {len(created)} files into {dest_root} (scope={args.scope}, profile={args.profile})")
    for path in created[:20]:
        print(f"- {path}")
    if len(created) > 20:
        print(f"... and {len(created) - 20} more files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
