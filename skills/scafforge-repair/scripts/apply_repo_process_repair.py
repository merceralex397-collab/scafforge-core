from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUNTIME_SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scafforge-pivot" / "scripts"
if str(RUNTIME_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SCRIPT_DIR))

from audit_repo_process import load_latest_previous_diagnosis, manifest_supporting_logs, supporting_log_paths
from regenerate_restart_surfaces import regenerate_restart_surfaces
from shared_verifier import audit_repo
from shared_generated_tool_runtime import run_generated_tool


# WFLOW codes that specifically indicate agent-team or prompt surface drift.
# Only these codes justify adding opencode-team-bootstrap / agent-prompt-engineering
# as required follow-on stages.  All other WFLOW codes (e.g. WFLOW029 ticket-graph,
# WFLOW025 release-gate) do NOT indicate prompt/agent drift.
_AGENT_PROMPT_WFLOW_CODES: frozenset[str] = frozenset({
    "WFLOW006",  # team-leader prompt drift
    "WFLOW011",  # bootstrap routing missing from prompts
    "WFLOW013",  # /resume trust absent from prompts
    "WFLOW014",  # coordinator artifact surface drift
    "WFLOW021",  # legacy handoff_allowed reference in prompts
})

START_HERE_MANAGED_START = "<!-- SCAFFORGE:START_HERE_BLOCK START -->"
START_HERE_MANAGED_END = "<!-- SCAFFORGE:START_HERE_BLOCK END -->"
FOLLOW_ON_TRACKING_PATH = Path(".opencode/meta/repair-follow-on-state.json")
REPAIR_ESCALATION_PATH = Path(".opencode/state/repair-escalation.json")
TRANSACTION_STATE_SURFACES = (
    Path(".opencode/state/workflow-state.json"),
    FOLLOW_ON_TRACKING_PATH,
    Path(".opencode/meta/bootstrap-provenance.json"),
    Path(".opencode/state/context-snapshot.md"),
    Path(".opencode/state/latest-handoff.md"),
)
DETERMINISTIC_PROCESS_DOCS = (
    "workflow.md",
    "tooling.md",
    "model-matrix.md",
    "git-capability.md",
)


class RepairFailure(RuntimeError):
    pass


class RepairEscalation(RuntimeError):
    def __init__(self, message: str, payload: dict[str, Any]):
        super().__init__(message)
        self.payload = payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply deterministic Scafforge process repairs to an existing repo.")
    parser.add_argument("repo_root", help="Repository root to repair.")
    parser.add_argument("--project-name", help="Override project name when provenance is missing.")
    parser.add_argument("--project-slug", help="Override project slug when provenance is missing.")
    parser.add_argument("--agent-prefix", help="Override agent prefix when provenance is missing.")
    parser.add_argument("--model-provider", help="Override model provider when provenance is missing.")
    parser.add_argument("--planner-model", help="Override planner model when provenance is missing.")
    parser.add_argument("--implementer-model", help="Override implementer model when provenance is missing.")
    parser.add_argument("--utility-model", help="Override utility model when provenance is missing.")
    parser.add_argument(
        "--model-tier",
        choices=("strong", "standard", "weak"),
        help="Override prompt-density model tier when provenance is missing.",
    )
    parser.add_argument("--stack-label", default="framework-agnostic", help="Stack label for regenerated process docs.")
    parser.add_argument(
        "--change-summary",
        default="Deterministic Scafforge managed workflow surfaces refreshed by scafforge-repair.",
        help="Summary stored in workflow-state and repair history.",
    )
    parser.add_argument(
        "--preserve-backups",
        action="store_true",
        help="Keep managed-surface backups under .opencode/state/repair-backups after a successful repair.",
    )
    parser.add_argument("--skip-verify", action="store_true", help="Skip the post-repair audit.")
    parser.add_argument("--supporting-log", action="append", default=[], help="Optional supporting session log or transcript path for post-repair verification. May be provided multiple times.")
    parser.add_argument(
        "--repair-basis-diagnosis",
        help="Optional diagnosis pack directory or manifest path that this repair run is based on. Defaults to the latest diagnosis pack in the repo.",
    )
    parser.add_argument("--fail-on", choices=("never", "warning", "error"), default="never")
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def normalize_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "project"


def list_relative_file_bytes(path: Path) -> dict[str, bytes]:
    if not path.exists():
        return {}
    if path.is_file():
        return {"": path.read_bytes()}
    payload: dict[str, bytes] = {}
    for candidate in sorted(path.rglob("*")):
        if candidate.is_file():
            payload[str(candidate.relative_to(path)).replace("\\", "/")] = candidate.read_bytes()
    return payload


def merge_diff_summaries(*summaries: dict[str, list[str]]) -> dict[str, list[str]]:
    added: set[str] = set()
    removed: set[str] = set()
    modified: set[str] = set()
    for summary in summaries:
        added.update(summary.get("files_added", []))
        removed.update(summary.get("files_removed", []))
        modified.update(summary.get("files_modified", []))
    return {
        "files_added": sorted(added),
        "files_removed": sorted(removed),
        "files_modified": sorted(modified),
    }


def diff_surface(source: Path, target: Path, repo_relative: str, *, target_text_override: str | None = None) -> dict[str, list[str]]:
    if target_text_override is not None:
        target_exists = target.exists()
        current_text = read_text(target) if target_exists else ""
        if not target_exists:
            return {"files_added": [repo_relative], "files_removed": [], "files_modified": []}
        if current_text != target_text_override:
            return {"files_added": [], "files_removed": [], "files_modified": [repo_relative]}
        return {"files_added": [], "files_removed": [], "files_modified": []}

    source_files = list_relative_file_bytes(source)
    target_files = list_relative_file_bytes(target)
    added: list[str] = []
    removed: list[str] = []
    modified: list[str] = []
    all_keys = sorted(set(source_files) | set(target_files))
    for key in all_keys:
        repo_path = repo_relative if not key else f"{repo_relative}/{key}"
        if key not in target_files:
            added.append(repo_path)
        elif key not in source_files:
            removed.append(repo_path)
        elif source_files[key] != target_files[key]:
            modified.append(repo_path)
    return {
        "files_added": added,
        "files_removed": removed,
        "files_modified": modified,
    }


def extract_lifecycle_stages(workflow_text: str) -> set[str]:
    match = re.search(r"LIFECYCLE_STAGES\s*=\s*new Set\(\[(.*?)\]\)", workflow_text, re.DOTALL)
    if not match:
        return set()
    return {item.strip() for item in re.findall(r'"([^"]+)"', match.group(1)) if item.strip()}


def directory_entry_names(path: Path, *, suffix: str) -> set[str]:
    if not path.exists():
        return set()
    return {candidate.name for candidate in path.iterdir() if candidate.is_file() and candidate.name.endswith(suffix)}


def build_managed_surface_diff_summary(repo_root: Path, rendered_root: Path) -> dict[str, list[str]]:
    summaries = [
        diff_surface(rendered_root / "opencode.jsonc", repo_root / "opencode.jsonc", "opencode.jsonc"),
        diff_surface(rendered_root / ".opencode" / "tools", repo_root / ".opencode" / "tools", ".opencode/tools"),
        diff_surface(rendered_root / ".opencode" / "lib", repo_root / ".opencode" / "lib", ".opencode/lib"),
        diff_surface(rendered_root / ".opencode" / "plugins", repo_root / ".opencode" / "plugins", ".opencode/plugins"),
        diff_surface(rendered_root / ".opencode" / "commands", repo_root / ".opencode" / "commands", ".opencode/commands"),
    ]
    rendered_skills_root = rendered_root / ".opencode" / "skills"
    target_skills_root = repo_root / ".opencode" / "skills"
    if rendered_skills_root.exists():
        for skill_dir in sorted(rendered_skills_root.iterdir()):
            if not skill_dir.is_dir():
                continue
            summaries.append(
                diff_surface(
                    skill_dir,
                    target_skills_root / skill_dir.name,
                    f".opencode/skills/{skill_dir.name}",
                )
            )
    for filename in DETERMINISTIC_PROCESS_DOCS:
        summaries.append(
            diff_surface(
                rendered_root / "docs" / "process" / filename,
                repo_root / "docs" / "process" / filename,
                f"docs/process/{filename}",
            )
        )
    rendered_start_here = read_text(rendered_root / "START-HERE.md")
    merged_start_here = merge_start_here(read_text(repo_root / "START-HERE.md"), rendered_start_here)
    summaries.append(
        diff_surface(
            rendered_root / "START-HERE.md",
            repo_root / "START-HERE.md",
            "START-HERE.md",
            target_text_override=merged_start_here,
        )
    )
    return merge_diff_summaries(*summaries)


def detect_intent_changing_repair(repo_root: Path, rendered_root: Path) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []

    current_tool_names = directory_entry_names(repo_root / ".opencode" / "tools", suffix=".ts")
    rendered_tool_names = directory_entry_names(rendered_root / ".opencode" / "tools", suffix=".ts")
    added_tools = sorted(rendered_tool_names - current_tool_names)
    removed_tools = sorted(current_tool_names - rendered_tool_names)
    if added_tools or removed_tools:
        reasons.append(
            {
                "category": "workflow_tools",
                "why_intent_changing": "Adding or removing workflow tools changes the executable operating surface for the repo.",
                "details": {
                    "added_tools": added_tools,
                    "removed_tools": removed_tools,
                },
                "user_decision": "Approve the workflow tool inventory change or route the repo through kickoff/pivot instead of routine repair.",
            }
        )

    current_workflow_text = read_text(repo_root / ".opencode" / "lib" / "workflow.ts")
    rendered_workflow_text = read_text(rendered_root / ".opencode" / "lib" / "workflow.ts")
    current_stages = extract_lifecycle_stages(current_workflow_text)
    rendered_stages = extract_lifecycle_stages(rendered_workflow_text)
    if current_stages and rendered_stages and current_stages != rendered_stages:
        reasons.append(
            {
                "category": "ticket_lifecycle_stages",
                "why_intent_changing": "Changing the lifecycle stage set changes the repo's core execution contract.",
                "details": {
                    "before": sorted(current_stages),
                    "after": sorted(rendered_stages),
                },
                "user_decision": "Confirm the lifecycle stage change explicitly before applying it through repair.",
            }
        )

    return reasons


def write_repair_escalation(
    repo_root: Path,
    *,
    change_summary: str,
    reasons: list[dict[str, Any]],
    diff_summary: dict[str, list[str]],
) -> dict[str, Any]:
    payload = {
        "escalated_at": current_iso_timestamp(),
        "change_summary": change_summary,
        "attempted_operation": "deterministic-managed-surface-replacement",
        "reasons": reasons,
        "diff_summary": diff_summary,
        "status": "approval_required",
    }
    write_json(repo_root / REPAIR_ESCALATION_PATH, payload)
    return payload


def backup_target(target: Path, backup_root: Path, repo_root: Path) -> dict[str, Any]:
    relative_target = normalize_path(target, repo_root)
    backup_path = backup_root / relative_target
    record = {
        "target": target,
        "backup": backup_path,
        "existed": target.exists(),
        "is_dir": target.is_dir(),
    }
    if target.is_dir():
        if target.exists():
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(target, backup_path)
    elif target.exists():
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup_path)
    return record


def restore_backup_records(records: list[dict[str, Any]]) -> None:
    for record in reversed(records):
        target = record["target"]
        backup = record["backup"]
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        if record["existed"]:
            if not backup.exists():
                raise RepairFailure(f"Backup for {target} is missing or corrupted at {backup}")
            backup.parent.mkdir(parents=True, exist_ok=True)
            if record["is_dir"]:
                shutil.copytree(backup, target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, target)


def update_latest_repair_history(repo_root: Path, repair_id: str, updates: dict[str, Any]) -> None:
    provenance_path = repo_root / ".opencode" / "meta" / "bootstrap-provenance.json"
    payload = read_json(provenance_path)
    if not isinstance(payload, dict):
        return
    history = payload.get("repair_history")
    if not isinstance(history, list) or not history:
        return
    for entry in reversed(history):
        if isinstance(entry, dict) and entry.get("repair_id") == repair_id:
            entry.update(updates)
            write_json(provenance_path, payload)
            return


def append_migration_history(repo_root: Path, migration_entry: dict[str, Any]) -> None:
    provenance_path = repo_root / ".opencode" / "meta" / "bootstrap-provenance.json"
    payload = read_json(provenance_path)
    if not isinstance(payload, dict):
        return
    history = payload.get("migration_history")
    if not isinstance(history, list):
        history = []
    payload["migration_history"] = [*history, migration_entry]
    write_json(provenance_path, payload)


def merge_start_here(existing: str, rendered: str) -> str:
    rendered_pattern = re.compile(
        rf"{re.escape(START_HERE_MANAGED_START)}[\s\S]*?{re.escape(START_HERE_MANAGED_END)}",
        re.MULTILINE,
    )
    rendered_match = rendered_pattern.search(rendered)
    if not rendered_match:
        return rendered
    if not existing.strip():
        return rendered
    start_index = existing.find(START_HERE_MANAGED_START)
    end_index = existing.find(START_HERE_MANAGED_END)
    if start_index == -1 and end_index == -1:
        return existing
    if start_index != -1 and end_index == -1:
        prefix = existing[:start_index].rstrip()
        return f"{prefix}\n\n{rendered_match.group(0)}\n" if prefix else f"{rendered_match.group(0)}\n"
    if start_index == -1 and end_index != -1:
        suffix = existing[end_index + len(START_HERE_MANAGED_END):].lstrip("\r\n")
        return f"{rendered_match.group(0)}\n\n{suffix}" if suffix else rendered_match.group(0)
    return rendered_pattern.sub(rendered_match.group(0), existing, count=1)


def package_root() -> Path:
    return Path(__file__).resolve().parents[3]


def current_package_commit() -> str:
    if os.environ.get("SCAFFORGE_FORCE_MISSING_PROVENANCE") == "1":
        return "missing_provenance"
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=package_root(),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return "missing_provenance"
    return result.stdout.strip() or "missing_provenance"


def bootstrap_script_path() -> Path:
    return Path(__file__).resolve().parents[2] / "repo-scaffold-factory" / "scripts" / "bootstrap_repo_scaffold.py"


def load_metadata(repo_root: Path, args: argparse.Namespace) -> dict[str, str]:
    provenance = read_json(repo_root / ".opencode" / "meta" / "bootstrap-provenance.json")
    manifest = read_json(repo_root / "tickets" / "manifest.json")
    runtime = provenance.get("runtime_models", {}) if isinstance(provenance, dict) else {}

    project_name = args.project_name or (provenance.get("project_name") if isinstance(provenance, dict) else None)
    if not project_name and isinstance(manifest, dict):
        raw_project = manifest.get("project")
        if isinstance(raw_project, str) and raw_project.strip():
            project_name = raw_project.strip()

    project_slug = args.project_slug or (provenance.get("project_slug") if isinstance(provenance, dict) else None)
    agent_prefix = args.agent_prefix or (provenance.get("agent_prefix") if isinstance(provenance, dict) else None)
    model_provider = args.model_provider or runtime.get("provider")
    planner_model = args.planner_model or runtime.get("planner")
    implementer_model = args.implementer_model or runtime.get("implementer")
    utility_model = args.utility_model or runtime.get("utility") or planner_model
    model_tier = args.model_tier or runtime.get("tier") or "weak"

    # Provenance may store models as "provider/model" but bootstrap_repo_scaffold
    # expects bare model names and prepends provider itself. Strip the prefix.
    if model_provider and isinstance(model_provider, str):
        prefix = model_provider.strip() + "/"
        if isinstance(planner_model, str) and planner_model.startswith(prefix):
            planner_model = planner_model[len(prefix):]
        if isinstance(implementer_model, str) and implementer_model.startswith(prefix):
            implementer_model = implementer_model[len(prefix):]
        if isinstance(utility_model, str) and utility_model.startswith(prefix):
            utility_model = utility_model[len(prefix):]

    # Recover stack_label from provenance when not explicitly overridden.
    # Without this, Godot repos would be rebuilt with framework-agnostic scaffolds.
    stack_label = args.stack_label
    if stack_label == "framework-agnostic" and isinstance(provenance, dict):
        prov_stack = provenance.get("stack_label")
        if isinstance(prov_stack, str) and prov_stack.strip():
            stack_label = prov_stack.strip()

    # Recover product_finish_contract from provenance for round-trip fidelity.
    finish_contract = {}
    if isinstance(provenance, dict):
        pfc = provenance.get("product_finish_contract")
        if isinstance(pfc, dict):
            finish_contract = pfc

    if not project_slug and project_name:
        project_slug = slugify(project_name)
    if not agent_prefix and project_slug:
        agent_prefix = project_slug

    values = {
        "project_name": project_name,
        "project_slug": project_slug,
        "agent_prefix": agent_prefix,
        "model_provider": model_provider,
        "planner_model": planner_model,
        "implementer_model": implementer_model,
        "utility_model": utility_model,
        "model_tier": model_tier,
    }
    missing = [key for key, value in values.items() if not isinstance(value, str) or not value.strip()]
    if missing:
        missing_display = ", ".join(missing)
        raise SystemExit(
            f"Missing required metadata for repair: {missing_display}. "
            "Provide overrides on the command line or ensure bootstrap provenance exists."
        )
    result = {key: value.strip() for key, value in values.items()}
    result["stack_label"] = stack_label
    result["finish_contract"] = json.dumps(finish_contract) if finish_contract else ""
    return result


def run_bootstrap_render(dest_root: Path, metadata: dict[str, str], stack_label: str) -> None:
    command = [
        sys.executable,
        str(bootstrap_script_path()),
        "--dest",
        str(dest_root),
        "--project-name",
        metadata["project_name"],
        "--project-slug",
        metadata["project_slug"],
        "--agent-prefix",
        metadata["agent_prefix"],
        "--model-provider",
        metadata["model_provider"],
        "--model-tier",
        metadata["model_tier"],
        "--planner-model",
        metadata["planner_model"],
        "--implementer-model",
        metadata["implementer_model"],
        "--utility-model",
        metadata["utility_model"],
        "--stack-label",
        stack_label,
        "--scope",
        "full",
        "--force",
    ]
    result = subprocess.run(command, cwd=package_root(), check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            "Unable to render repair scaffold.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


def replace_directory(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def replace_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def normalize_ticket_state_map(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for ticket_id, ticket_state in value.items():
        if not isinstance(ticket_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", ticket_id):
            continue
        approved_plan = False
        reopen_count = 0
        needs_reverification = False
        if isinstance(ticket_state, dict) and isinstance(ticket_state.get("approved_plan"), bool):
            approved_plan = ticket_state["approved_plan"]
        if isinstance(ticket_state, dict) and isinstance(ticket_state.get("reopen_count"), int) and ticket_state["reopen_count"] >= 0:
            reopen_count = ticket_state["reopen_count"]
        if isinstance(ticket_state, dict) and isinstance(ticket_state.get("needs_reverification"), bool):
            needs_reverification = ticket_state["needs_reverification"]
        normalized[ticket_id] = {
            "approved_plan": approved_plan,
            "reopen_count": reopen_count,
            "needs_reverification": needs_reverification,
        }
    return normalized


def current_iso_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def initialize_follow_on_tracking_state(
    repo_root: Path,
    *,
    process_version: int,
    change_summary: str,
) -> dict[str, Any]:
    timestamp = current_iso_timestamp()
    payload = {
        "tracking_mode": "persistent_recorded_state",
        "assertion_input_mode": "legacy_manual_assertion",
        "cycle_id": timestamp,
        "created_at": timestamp,
        "last_updated_at": timestamp,
        "process_version": process_version,
        "repair_package_commit": current_package_commit(),
        "change_summary": change_summary,
        "required_stages": [],
        "stage_records": {},
        "history": [],
    }
    write_json(repo_root / FOLLOW_ON_TRACKING_PATH, payload)
    return payload


def find_placeholder_skills(repo_root: Path) -> list[str]:
    # These patterns must stay in sync with PLACEHOLDER_SKILL_PATTERNS in
    # skills/scafforge-audit/scripts/audit_repo_process.py so that repair
    # detection agrees with audit detection.
    _PLACEHOLDER_SKILL_PATTERNS = (
        "Replace this file",
        "TODO: replace",
        "When the repo stack is finalized, rewrite this catalog",
        "When the project stack is confirmed, replace this file",
        "__STACK_LABEL__",
    )
    hits: list[str] = []
    skills_root = repo_root / ".opencode" / "skills"
    if not skills_root.exists():
        return hits
    for path in sorted(skills_root.rglob("SKILL.md")):
        text = read_text(path)
        if any(pat in text for pat in _PLACEHOLDER_SKILL_PATTERNS):
            hits.append(str(path.relative_to(repo_root)))
    return hits


def detect_agent_prompt_drift(repo_root: Path) -> list[str]:
    hits: list[str] = []
    agents_root = repo_root / ".opencode" / "agents"
    if not agents_root.exists():
        return hits

    team_leader = next(agents_root.glob("*team-leader*.md"), None)
    if team_leader:
        text = read_text(team_leader)
        if "next_action_tool" not in text or "summary-only stopping is invalid" not in text:
            hits.append(str(team_leader.relative_to(repo_root)))

    for pattern in ("*implementer*.md", "*lane-executor*.md", "*docs-handoff*.md"):
        for path in agents_root.glob(pattern):
            text = read_text(path)
            if "team leader already owns lease claim and release" not in text:
                hits.append(str(path.relative_to(repo_root)))
    return sorted(set(hits))


def _surface_entry(
    *,
    status: str,
    surfaces: list[str],
    reason: str,
    finding_codes: set[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "surfaces": sorted(set(surfaces)),
        "reason": reason,
    }
    if finding_codes:
        payload["finding_codes"] = sorted(finding_codes)
    return payload


def build_stale_surface_map(
    repo_root: Path,
    replaced_surfaces: list[str],
    findings: list[Any],
    pending_process_verification: bool,
    *,
    required_stage_names: set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    required_stage_names = required_stage_names or set()
    codes = {getattr(finding, "code", "") for finding in findings if getattr(finding, "code", "")}
    workflow_codes = {code for code in codes if code.startswith(("WFLOW", "BOOT", "CYCLE")) and code not in {"WFLOW008", "WFLOW025", "WFLOW029"}}
    prompt_codes = {code for code in codes if code in _AGENT_PROMPT_WFLOW_CODES}
    skill_codes = {code for code in codes if code.startswith(("SKILL", "MODEL"))}
    ticket_codes = {code for code in codes if code.startswith("EXEC") or code == "WFLOW008"}

    workflow_surfaces = [
        surface
        for surface in replaced_surfaces
        if surface in {"opencode.jsonc", ".opencode/tools", ".opencode/lib", ".opencode/plugins", ".opencode/commands"}
        or surface.startswith("docs/process/")
    ]
    restart_surfaces = [
        surface
        for surface in replaced_surfaces
        if surface in {"START-HERE.md managed block", ".opencode/state/context-snapshot.md", ".opencode/state/latest-handoff.md"}
    ]
    placeholder_skills = find_placeholder_skills(repo_root)
    prompt_drift = detect_agent_prompt_drift(repo_root)

    return {
        "workflow_tools_and_prompts": _surface_entry(
            status="replace" if workflow_surfaces or workflow_codes else "stable",
            surfaces=workflow_surfaces,
            reason="Managed workflow tools, prompts, and process docs were refreshed or still show workflow drift.",
            finding_codes=workflow_codes,
        ),
        "repo_local_skills": _surface_entry(
            status=(
                "regenerate"
                if "project-skill-bootstrap" in required_stage_names
                or "scaffold-managed .opencode/skills" in replaced_surfaces
                or placeholder_skills
                or skill_codes
                else "stable"
            ),
            surfaces=(["scaffold-managed .opencode/skills"] if "scaffold-managed .opencode/skills" in replaced_surfaces else []) + placeholder_skills,
            reason="Repo-local skills need regeneration when scaffold-managed skills were replaced or placeholder/model drift remains.",
            finding_codes=skill_codes,
        ),
        "agent_team_and_prompts": _surface_entry(
            status=(
                "regenerate"
                if {"opencode-team-bootstrap", "agent-prompt-engineering"} & required_stage_names
                or prompt_drift
                or prompt_codes
                else "stable"
            ),
            surfaces=prompt_drift,
            reason="Agent-team prompts stay stable unless drift remains after managed repair.",
            finding_codes=prompt_codes,
        ),
        "ticket_graph_and_follow_up": _surface_entry(
            status=(
                "ticket_follow_up"
                if "ticket-pack-builder" in required_stage_names or any(code.startswith("EXEC") for code in ticket_codes)
                else "stable"
            ),
            surfaces=[],
            reason=(
                "Ticket follow-up is required when source findings still need explicit routing through ticket-pack-builder."
                if "ticket-pack-builder" in required_stage_names or any(code.startswith("EXEC") for code in ticket_codes)
                else "Bare pending_process_verification remains workflow-state truth, but does not by itself force repair-side ticket follow-up."
                if pending_process_verification or "WFLOW008" in ticket_codes
                else "Ticket graph stays stable when repair did not uncover source-layer follow-up."
            ),
            finding_codes=ticket_codes,
        ),
        "restart_surfaces": _surface_entry(
            status="replace" if restart_surfaces else "stable",
            surfaces=restart_surfaces,
            reason="Restart surfaces are derived and must be regenerated whenever managed repair changes workflow state.",
        ),
        "canonical_project_decisions": _surface_entry(
            status="stable",
            surfaces=[],
            reason="Managed repair preserves accepted project-scope decisions. Intent-changing drift must route outside routine public repair.",
        ),
    }


def resolve_repair_basis(repo_root: Path, explicit_basis: str | None) -> tuple[Path, dict[str, Any]] | None:
    if not explicit_basis:
        return load_latest_previous_diagnosis(repo_root)

    candidate = Path(explicit_basis).expanduser()
    candidate = candidate if candidate.is_absolute() else (repo_root / candidate)
    candidate = candidate.resolve()
    manifest_path = candidate / "manifest.json" if candidate.is_dir() else candidate
    if manifest_path.name != "manifest.json":
        raise SystemExit("Repair basis path must be a diagnosis directory or a manifest.json file.")
    if not manifest_path.exists():
        raise SystemExit(f"Repair basis manifest not found: {manifest_path}")
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise SystemExit(f"Repair basis manifest is not valid JSON: {manifest_path}")
    return manifest_path.parent, manifest


def verification_logs(
    repo_root: Path,
    explicit_logs: list[str] | None,
    repair_basis: tuple[Path, dict[str, Any]] | None,
) -> list[Path]:
    logs = supporting_log_paths(repo_root, explicit_logs)
    if repair_basis is None:
        return logs

    _, manifest = repair_basis
    for path in supporting_log_paths(repo_root, manifest_supporting_logs(manifest)):
        if path not in logs:
            logs.append(path)
    return logs


def repair_basis_requires_causal_replay(
    repo_root: Path,
    explicit_logs: list[str] | None,
    repair_basis: tuple[Path, dict[str, Any]] | None,
) -> bool:
    if supporting_log_paths(repo_root, explicit_logs):
        return True
    if repair_basis is None:
        return False
    _, manifest = repair_basis
    return bool(manifest_supporting_logs(manifest))


def load_pending_process_verification(repo_root: Path) -> bool:
    workflow = read_json(repo_root / ".opencode" / "state" / "workflow-state.json")
    return isinstance(workflow, dict) and workflow.get("pending_process_verification") is True


def refresh_restart_surfaces(repo_root: Path) -> None:
    regenerate_restart_surfaces(
        repo_root,
        reason="Deterministic Scafforge restart-surface refresh.",
        source="scafforge-repair",
        verification_passed=False,
    )


def update_workflow_state(repo_root: Path, rendered_provenance: dict[str, Any], change_summary: str) -> None:
    workflow_contract = rendered_provenance.get("workflow_contract", {}) if isinstance(rendered_provenance, dict) else {}
    process_version = workflow_contract.get("process_version", 7)
    changed_at = current_iso_timestamp()
    run_generated_tool(
        repo_root,
        ".opencode/tools/repair_follow_on_refresh.ts",
        {
            "change_summary": change_summary,
            "process_version": process_version,
            "parallel_mode": workflow_contract.get("parallel_mode", "sequential"),
            "repair_follow_on_json": json.dumps(
                {
                    "outcome": "managed_blocked",
                    "required_stages": [],
                    "completed_stages": [],
                    "asserted_completed_stages": [],
                    "legacy_asserted_completed_stages": [],
                    "stage_completion_mode": "legacy_manual_assertion",
                    "tracking_mode": "persistent_recorded_state",
                    "follow_on_state_path": str(FOLLOW_ON_TRACKING_PATH).replace("\\", "/"),
                    "blocking_reasons": [
                        "Managed repair refreshed workflow surfaces. Run the full scafforge-repair follow-on flow before resuming normal ticket lifecycle execution."
                    ],
                    "verification_passed": False,
                    "handoff_allowed": False,
                    "last_updated_at": changed_at,
                    "process_version": process_version,
                }
            ),
        },
    )
    initialize_follow_on_tracking_state(
        repo_root,
        process_version=process_version,
        change_summary=change_summary,
    )


def update_provenance(
    repo_root: Path,
    rendered_root: Path,
    replaced_surfaces: list[str],
    change_summary: str,
    *,
    repair_id: str,
    diff_summary: dict[str, list[str]],
    backup_path: str | None,
    process_version_before: int | None,
    process_version_after: int | None,
) -> None:
    provenance_path = repo_root / ".opencode" / "meta" / "bootstrap-provenance.json"
    existing = read_json(provenance_path)
    rendered = read_json(rendered_root / ".opencode" / "meta" / "bootstrap-provenance.json")
    payload = rendered if isinstance(rendered, dict) else {}
    existing_migration_history = existing.get("migration_history") if isinstance(existing, dict) and isinstance(existing.get("migration_history"), list) else []
    rendered_migration_history = rendered.get("migration_history") if isinstance(rendered, dict) and isinstance(rendered.get("migration_history"), list) else []
    history = existing.get("repair_history") if isinstance(existing, dict) and isinstance(existing.get("repair_history"), list) else []
    payload["repair_history"] = [
        *history,
        {
            "repair_id": repair_id,
            "repaired_at": current_iso_timestamp(),
            "repair_type": "managed-surface-replacement",
            "repair_kind": "deterministic-workflow-engine-replacement",
            "repair_package_commit": current_package_commit(),
            "summary": change_summary,
            "surfaces_replaced": replaced_surfaces,
            "replaced_surfaces": replaced_surfaces,
            "diff_summary": diff_summary,
            "audit_findings_addressed": [],
            "verification_passed": False,
            "verification_findings": [],
            "remediation_ticket_ids": [],
            "process_version_before": process_version_before,
            "process_version_after": process_version_after,
            "backup_path": backup_path,
            "project_specific_follow_up": (
                payload.get("managed_surfaces", {}).get("project_specific_follow_up", [])
                if isinstance(payload.get("managed_surfaces"), dict)
                else []
            ),
        },
    ]
    payload["migration_history"] = existing_migration_history or rendered_migration_history
    write_json(provenance_path, payload)


def _warn_if_split_scope_deadlock_present(repo_root: Path) -> None:
    """Emit a host-side warning if the installed workflow.ts has the split-scope deadlock throw
    and the manifest contains open split_scope children with done parents.
    After managed surface replacement the deadlock will be gone and no ticket_reconcile is needed.
    """
    installed_workflow = repo_root / ".opencode" / "lib" / "workflow.ts"
    if not installed_workflow.exists():
        return
    workflow_text = installed_workflow.read_text(encoding="utf-8")
    has_deadlock_throw = (
        "Split-scope child" in workflow_text
        and "cannot point at a completed source ticket" in workflow_text
    )
    if not has_deadlock_throw:
        return
    manifest = read_json(repo_root / "tickets" / "manifest.json")
    if not isinstance(manifest, dict):
        return
    tickets = manifest.get("tickets", [])
    completed_ids = {
        t["id"] for t in tickets
        if isinstance(t, dict)
        and (t.get("status") == "done" or t.get("resolution_state") == "superseded")
    }
    blocked_children = [
        t["id"] for t in tickets
        if isinstance(t, dict)
        and t.get("source_mode") == "split_scope"
        and t.get("source_ticket_id") in completed_ids
        and t.get("status") != "done"
    ]
    if blocked_children:
        print(
            f"[scafforge-repair] NOTICE: Installed workflow.ts contains the split-scope deadlock throw. "
            f"Tickets {blocked_children} are currently blocked from all writes. "
            f"This repair will install the fixed workflow.ts that removes the erroneous invariant. "
            f"After replacement, agents can claim these tickets directly — no ticket_reconcile is needed."
        )


def apply_repair(repo_root: Path, rendered_root: Path, change_summary: str, *, preserve_backups: bool = False) -> dict[str, Any]:
    replaced_surfaces: list[str] = []
    diff_summary = build_managed_surface_diff_summary(repo_root, rendered_root)
    intent_changing_reasons = detect_intent_changing_repair(repo_root, rendered_root)
    if intent_changing_reasons:
        escalation = write_repair_escalation(
            repo_root,
            change_summary=change_summary,
            reasons=intent_changing_reasons,
            diff_summary=diff_summary,
        )
        raise RepairEscalation(
            "Deterministic managed repair would change intent-sensitive workflow contract surfaces.",
            escalation,
        )

    _warn_if_split_scope_deadlock_present(repo_root)

    workflow_before = read_json(repo_root / ".opencode" / "state" / "workflow-state.json")
    process_version_before = workflow_before.get("process_version") if isinstance(workflow_before, dict) else None
    repair_id = current_iso_timestamp()
    backup_root = (
        repo_root / ".opencode" / "state" / "repair-backups" / repair_id.replace(":", "-")
        if preserve_backups
        else Path(tempfile.mkdtemp(prefix="scafforge-repair-backup-"))
    )
    processed_records: list[dict[str, Any]] = []

    def replace_file_with_backup(source: Path, target: Path) -> None:
        processed_records.append(backup_target(target, backup_root, repo_root))
        replace_file(source, target)

    def replace_directory_with_backup(source: Path, target: Path) -> None:
        processed_records.append(backup_target(target, backup_root, repo_root))
        replace_directory(source, target)

    def write_merged_start_here_with_backup(rendered_text: str, target: Path) -> None:
        processed_records.append(backup_target(target, backup_root, repo_root))
        existing_text = target.read_text(encoding="utf-8") if target.exists() else ""
        target.write_text(merge_start_here(existing_text, rendered_text), encoding="utf-8")

    try:
        replace_file_with_backup(rendered_root / "opencode.jsonc", repo_root / "opencode.jsonc")
        replaced_surfaces.append("opencode.jsonc")

        for relative in (".opencode/tools", ".opencode/lib", ".opencode/plugins", ".opencode/commands"):
            replace_directory_with_backup(rendered_root / relative, repo_root / relative)
            replaced_surfaces.append(relative)

        rendered_skills_root = rendered_root / ".opencode" / "skills"
        target_skills_root = repo_root / ".opencode" / "skills"
        target_skills_root.mkdir(parents=True, exist_ok=True)
        for skill_dir in sorted(rendered_skills_root.iterdir()):
            if not skill_dir.is_dir():
                continue
            replace_directory_with_backup(skill_dir, target_skills_root / skill_dir.name)
        replaced_surfaces.append("scaffold-managed .opencode/skills")

        for filename in DETERMINISTIC_PROCESS_DOCS:
            replace_file_with_backup(rendered_root / "docs" / "process" / filename, repo_root / "docs" / "process" / filename)
            replaced_surfaces.append(f"docs/process/{filename}")

        rendered_start_here = (rendered_root / "START-HERE.md").read_text(encoding="utf-8")
        target_start_here_path = repo_root / "START-HERE.md"
        write_merged_start_here_with_backup(rendered_start_here, target_start_here_path)
        replaced_surfaces.append("START-HERE.md managed block")

        (repo_root / ".opencode" / "state" / "bootstrap").mkdir(parents=True, exist_ok=True)

        for relative in TRANSACTION_STATE_SURFACES:
            processed_records.append(backup_target(repo_root / relative, backup_root, repo_root))

        update_workflow_state(repo_root, read_json(rendered_root / ".opencode" / "meta" / "bootstrap-provenance.json"), change_summary)
        process_version_after = None
        workflow_after = read_json(repo_root / ".opencode" / "state" / "workflow-state.json")
        if isinstance(workflow_after, dict) and isinstance(workflow_after.get("process_version"), int):
            process_version_after = workflow_after["process_version"]
        update_provenance(
            repo_root,
            rendered_root,
            replaced_surfaces,
            change_summary,
            repair_id=repair_id,
            diff_summary=diff_summary,
            backup_path=(str(backup_root) if preserve_backups else None),
            process_version_before=process_version_before,
            process_version_after=process_version_after,
        )
        # Normalize pivot state so restart surface publication is not blocked
        # by stale pivot-in-progress flags from prior repair/pivot cycles.
        pivot_state_path = repo_root / ".opencode" / "meta" / "pivot-state.json"
        if pivot_state_path.exists():
            try:
                pivot_data = read_json(pivot_state_path)
                if isinstance(pivot_data, dict):
                    rsi = pivot_data.get("restart_surface_inputs")
                    if isinstance(rsi, dict) and (rsi.get("pivot_in_progress") or rsi.get("pivot_changed_surfaces")):
                        rsi["pivot_in_progress"] = False
                        rsi["post_pivot_verification_passed"] = True
                        rsi["pending_downstream_stages"] = []
                        rsi["pending_ticket_lineage_actions"] = []
                        if not pivot_data.get("pivot_state_owner"):
                            pivot_data["pivot_state_owner"] = "scafforge-repair"
                        write_json(pivot_state_path, pivot_data)
            except Exception:
                pass  # Non-fatal — restart surface regen will report the issue
        regenerate_restart_surfaces(
            repo_root,
            reason=change_summary,
            source="scafforge-repair",
            verification_passed=False,
        )
        replaced_surfaces.append(".opencode/state/context-snapshot.md")
        replaced_surfaces.append(".opencode/state/latest-handoff.md")
        if not preserve_backups:
            shutil.rmtree(backup_root, ignore_errors=True)
        return {
            "replaced_surfaces": replaced_surfaces,
            "diff_summary": diff_summary,
            "backup_path": str(backup_root) if preserve_backups else None,
            "repair_id": repair_id,
            "process_version_before": process_version_before,
            "process_version_after": process_version_after,
        }
    except Exception as exc:
        restore_backup_records(processed_records)
        if not preserve_backups:
            shutil.rmtree(backup_root, ignore_errors=True)
        raise RepairFailure(f"Managed surface replacement failed and was restored from backup: {exc}") from exc


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    metadata = load_metadata(repo_root, args)

    with tempfile.TemporaryDirectory(prefix="scafforge-repair-") as temp_dir:
        rendered_root = Path(temp_dir) / "rendered"
        run_bootstrap_render(rendered_root, metadata, metadata["stack_label"])
        result = apply_repair(
            repo_root,
            rendered_root,
            args.change_summary,
            preserve_backups=args.preserve_backups,
        )
        replaced_surfaces = result["replaced_surfaces"]

    repair_basis = resolve_repair_basis(repo_root, args.repair_basis_diagnosis)
    logs = verification_logs(repo_root, args.supporting_log, repair_basis)
    findings = [] if args.skip_verify else audit_repo(repo_root, logs=logs)
    verification_passed = False if args.skip_verify else not findings
    verification_next_action = None
    if args.skip_verify:
        verification_next_action = "Run scafforge-audit before relying on this restart narrative for continued development."
    elif not verification_passed:
        verification_next_action = "Resolve the post-repair audit findings, then rerun scafforge-audit before treating the repo as ready for continued development."
    regenerate_restart_surfaces(
        repo_root,
        reason=args.change_summary,
        source="scafforge-repair",
        next_action=verification_next_action,
        verification_passed=verification_passed,
    )
    pending_process_verification = load_pending_process_verification(repo_root)
    managed_surface_findings = [finding for finding in findings if finding.code.startswith(("WFLOW", "BOOT", "MODEL", "SKILL", "CYCLE"))]
    environment_findings = [finding for finding in findings if finding.code.startswith("ENV")]
    source_findings = [finding for finding in findings if finding.code.startswith("EXEC")]
    process_follow_up_findings = [finding for finding in findings if finding.code in {"WFLOW008", "WFLOW009"}]
    stale_surface_map = build_stale_surface_map(repo_root, replaced_surfaces, findings, pending_process_verification)
    workflow_after = read_json(repo_root / ".opencode" / "state" / "workflow-state.json")
    repair_follow_on_state = workflow_after.get("repair_follow_on") if isinstance(workflow_after, dict) and isinstance(workflow_after.get("repair_follow_on"), dict) else {}
    repair_follow_on_outcome = str(repair_follow_on_state.get("outcome", "")).strip() or "managed_blocked"
    handoff_allowed = repair_follow_on_state.get("handoff_allowed") is True
    blocking_reasons = [
        str(item).strip()
        for item in repair_follow_on_state.get("blocking_reasons", [])
        if isinstance(item, str) and str(item).strip()
    ]
    verification_basis = "transcript_backed" if logs else "current_state_only"
    verification_status = {
        "verification_passed": verification_passed,
        "current_state_clean": not findings and not pending_process_verification,
        "causal_regression_verified": verification_passed,
        "verification_basis": verification_basis,
        "codes": [finding.code for finding in findings],
        "supporting_logs": [str(path) for path in logs],
    }
    provenance_path = repo_root / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = read_json(provenance_path)
    if isinstance(provenance, dict):
        repair_history = provenance.get("repair_history") if isinstance(provenance.get("repair_history"), list) else []
        if repair_history and isinstance(repair_history[-1], dict):
            repair_history[-1].update(
                {
                    "repair_follow_on_outcome": repair_follow_on_outcome,
                    "handoff_allowed": handoff_allowed,
                    "blocking_reasons": blocking_reasons,
                    "verification_passed": verification_passed,
                    "verification_summary": verification_status,
                }
            )
            write_json(provenance_path, provenance)
    payload = {
        "repo_root": str(repo_root),
        "replaced_surfaces": replaced_surfaces,
        "diff_summary": result["diff_summary"],
        "backup_path": result["backup_path"],
        "repair_id": result["repair_id"],
        "stale_surface_map": stale_surface_map,
        "execution_record": {
            "repo_root": str(repo_root),
            "repair_id": result["repair_id"],
            "repair_follow_on_outcome": repair_follow_on_outcome,
            "handoff_allowed": handoff_allowed,
            "blocking_reasons": blocking_reasons,
            "verification_status": verification_status,
            "diff_summary": result["diff_summary"],
            "backup_path": result["backup_path"],
            "stale_surface_map": stale_surface_map,
        },
        "verification": {
            "performed": not args.skip_verify,
            "finding_count": len(findings),
            "error_count": sum(1 for finding in findings if finding.severity == "error"),
            "warning_count": sum(1 for finding in findings if finding.severity == "warning"),
            "managed_surface_finding_count": len(managed_surface_findings),
            "environment_finding_count": len(environment_findings),
            "source_follow_up_count": len(source_findings),
            "process_follow_up_count": len(process_follow_up_findings),
            "supporting_log_count": len(logs),
            "pending_process_verification": pending_process_verification,
            "verification_passed": verification_passed,
            "clean": not findings and not pending_process_verification,
        },
    }
    if logs:
        payload["verification"]["supporting_logs"] = [str(path) for path in logs]
    print(json.dumps(payload, indent=2))

    if args.skip_verify:
        return 0
    if args.fail_on == "warning" and findings:
        return 2
    if args.fail_on == "error" and any(finding.severity == "error" for finding in findings):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
