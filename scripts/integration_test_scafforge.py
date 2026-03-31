from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import smoke_test_scafforge as smoke


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_INDEX = ROOT / "tests" / "fixtures" / "gpttalker" / "index.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run focused end-to-end Scafforge integration coverage for greenfield, repair, and pivot flows."
    )
    parser.add_argument("--list-fixtures", action="store_true", help="Print the curated GPTTalker fixture slugs and exit.")
    return parser.parse_args()


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def run_json(command: list[str], cwd: Path, *, allow_returncodes: set[int] | None = None) -> dict[str, object]:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    allowed = allow_returncodes or {0}
    if result.returncode not in allowed:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Command did not return valid JSON: {' '.join(command)}\nSTDOUT:\n{result.stdout}") from exc


def run(command: list[str], cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


def ensure_fixture_index() -> dict[str, dict[str, object]]:
    payload = read_json(FIXTURE_INDEX)
    if not isinstance(payload, dict):
        raise RuntimeError("Fixture index must be a JSON object.")
    families = payload.get("families")
    if not isinstance(families, list):
        raise RuntimeError("Fixture index must contain a families list.")
    indexed: dict[str, dict[str, object]] = {}
    for item in families:
        if not isinstance(item, dict):
            raise RuntimeError("Fixture family entries must be JSON objects.")
        slug = item.get("slug")
        if not isinstance(slug, str) or not slug.strip():
            raise RuntimeError("Fixture family entries must have a non-empty slug.")
        notes = item.get("notes")
        if not isinstance(notes, str) or not notes.strip():
            raise RuntimeError(f"Fixture family `{slug}` is missing a notes path.")
        notes_path = FIXTURE_INDEX.parent / notes
        if not notes_path.exists():
            raise RuntimeError(f"Fixture family `{slug}` notes file is missing: {notes_path}")
        indexed[slug] = item
    expected = {
        "bootstrap-dependency-layout-drift",
        "host-tool-or-permission-blockage",
        "repeated-lifecycle-contradiction",
        "restart-surface-drift-after-repair",
        "placeholder-skill-after-refresh",
        "split-scope-and-historical-trust-reconciliation",
    }
    if set(indexed) != expected:
        raise RuntimeError(f"Fixture index slugs do not match the curated GPTTalker family set: {sorted(indexed)}")
    return indexed


def bootstrap_full(dest: Path) -> None:
    run(
        [
            sys.executable,
            str(smoke.BOOTSTRAP),
            "--dest",
            str(dest),
            "--project-name",
            "Integration Probe",
            "--project-slug",
            "integration-probe",
            "--agent-prefix",
            "integration-probe",
            "--model-provider",
            "openrouter",
            "--planner-model",
            "openrouter/openai/gpt-5-mini",
            "--implementer-model",
            "openrouter/openai/gpt-5-mini",
            "--utility-model",
            "openrouter/openai/gpt-5-mini",
            "--stack-label",
            "framework-agnostic",
            "--scope",
            "full",
            "--force",
        ],
        ROOT,
    )


def seed_prompt_drift(dest: Path) -> None:
    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    text = team_leader.read_text(encoding="utf-8")
    text = text.replace("next_action_tool", "legacy_next_action_tool")
    text = text.replace("summary-only stopping is invalid", "summary-only stopping may happen")
    team_leader.write_text(text, encoding="utf-8")


def restore_prompt_surface(dest: Path, original_text: str) -> None:
    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    team_leader.write_text(original_text, encoding="utf-8")


def write_repair_completion_artifact(dest: Path, *, stage: str, cycle_id: str) -> None:
    artifact_rel = f".opencode/state/artifacts/history/repair/{stage}-completion.md"
    artifact_path = dest / artifact_rel
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        "# Repair Follow-On Completion\n\n"
        f"- completed_stage: {stage}\n"
        f"- cycle_id: {cycle_id}\n"
        f"- completed_by: {stage}\n\n"
        "## Summary\n\n"
        f"- Completed {stage} for the current repair cycle.\n",
        encoding="utf-8",
    )


def greenfield_integration(fixtures: dict[str, dict[str, object]], workspace: Path) -> None:
    _ = fixtures["bootstrap-dependency-layout-drift"]
    _ = fixtures["host-tool-or-permission-blockage"]
    dest = workspace / "greenfield"
    bootstrap_full(dest)
    smoke.make_stack_skill_non_placeholder(dest)
    payload = run_json(
        [
            sys.executable,
            str(smoke.VERIFY_GENERATED),
            str(dest),
            "--format",
            "json",
        ],
        ROOT,
    )
    if payload.get("verification_kind") != "greenfield_continuation":
        raise RuntimeError("Greenfield integration should run the continuation verifier.")
    if payload.get("immediately_continuable") is not True:
        raise RuntimeError("Greenfield integration should prove the generated repo is immediately continuable once placeholder drift is removed.")
    if payload.get("finding_count") != 0:
        raise RuntimeError("Greenfield integration should not leave residual verification findings.")


def repair_integration(fixtures: dict[str, dict[str, object]], workspace: Path) -> None:
    _ = fixtures["repeated-lifecycle-contradiction"]
    _ = fixtures["restart-surface-drift-after-repair"]
    _ = fixtures["placeholder-skill-after-refresh"]
    if shutil.which("uv") is None:
        print("Skipping repair integration because `uv` is not available on this host.")
        return
    dest = workspace / "repair"
    bootstrap_full(dest)
    smoke.seed_ready_bootstrap(dest)
    smoke.seed_failing_pytest_suite(dest)
    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    original_team_leader = team_leader.read_text(encoding="utf-8")
    seed_prompt_drift(dest)
    initial = run_json(
        [
            sys.executable,
            str(smoke.PUBLIC_REPAIR),
            str(dest),
            "--skip-deterministic-refresh",
        ],
        ROOT,
        allow_returncodes={0, 3},
    )
    required = set(initial["execution_record"]["required_follow_on_stages"])
    expected_required = {
        "project-skill-bootstrap",
        "opencode-team-bootstrap",
        "agent-prompt-engineering",
        "ticket-pack-builder",
    }
    if required != expected_required:
        raise RuntimeError(f"Repair integration expected follow-on stages {sorted(expected_required)}, found {sorted(required)}")
    tracking_path = dest / ".opencode" / "meta" / "repair-follow-on-state.json"
    tracking_state = read_json(tracking_path)
    if not isinstance(tracking_state, dict):
        raise RuntimeError("Repair integration expected persistent follow-on tracking state.")
    cycle_id = tracking_state.get("cycle_id")
    if not isinstance(cycle_id, str) or not cycle_id:
        raise RuntimeError("Repair integration expected a non-empty repair cycle id.")
    for stage in sorted(expected_required | {"handoff-brief"}):
        write_repair_completion_artifact(dest, stage=stage, cycle_id=cycle_id)
    artifact_recorded = run_json(
        [
            sys.executable,
            str(smoke.PUBLIC_REPAIR),
            str(dest),
            "--skip-deterministic-refresh",
        ],
        ROOT,
        allow_returncodes={0, 3},
    )
    recorded_before_fix = set(artifact_recorded["execution_record"]["recorded_execution_completed_stages"])
    expected_recorded = expected_required | {"handoff-brief"}
    if recorded_before_fix != expected_recorded:
        raise RuntimeError(f"Repair integration expected recorded completion for {sorted(expected_recorded)}, found {sorted(recorded_before_fix)}")
    if not artifact_recorded["execution_record"]["blocking_reasons"]:
        raise RuntimeError("Repair integration should stay managed-blocked while placeholder skill and prompt drift still exist, even after canonical follow-on artifacts are recorded.")
    smoke.make_stack_skill_non_placeholder(dest)
    restore_prompt_surface(dest, original_team_leader)
    converged = run_json(
        [
            sys.executable,
            str(smoke.PUBLIC_REPAIR),
            str(dest),
            "--skip-deterministic-refresh",
        ],
        ROOT,
        allow_returncodes={0, 3},
    )
    if converged["execution_record"]["blocking_reasons"]:
        raise RuntimeError("Repair integration should converge once current-cycle canonical completion artifacts exist for every routed follow-on stage.")
    recorded = set(converged["execution_record"]["recorded_execution_completed_stages"])
    if recorded != expected_recorded:
        raise RuntimeError(f"Repair integration expected recorded completion for {sorted(expected_recorded)}, found {sorted(recorded)}")
    if converged["execution_record"]["repair_follow_on_outcome"] != "source_follow_up":
        raise RuntimeError("Repair integration should leave only source_follow_up once managed repair follow-on converges on the failing-suite fixture.")
    if converged["execution_record"]["handoff_allowed"] is not True:
        raise RuntimeError("Repair integration should allow handoff once only source follow-up remains.")


def pivot_integration(fixtures: dict[str, dict[str, object]], workspace: Path) -> None:
    _ = fixtures["split-scope-and-historical-trust-reconciliation"]
    dest = workspace / "pivot"
    bootstrap_full(dest)
    smoke.make_stack_skill_non_placeholder(dest)
    smoke.seed_ready_bootstrap(dest)
    smoke.run_generated_tool(dest, ".opencode/tools/handoff_publish.ts", {})
    payload = run_json(
        [
            sys.executable,
            str(smoke.PIVOT),
            str(dest),
            "--pivot-class",
            "architecture-change",
            "--requested-change",
            "Move from a single service layout to modular domain services with a refreshed workflow contract.",
            "--accepted-decision",
            "Regenerate workflow prompts, skills, and ticket routing around the modular topology.",
            "--format",
            "json",
        ],
        ROOT,
    )
    if payload["verification_status"]["verification_passed"] is not True:
        raise RuntimeError("Pivot integration should pass the post-pivot verification gate on a clean generated repo.")
    pending = payload["downstream_refresh_state"]["pending_stages"]
    if not isinstance(pending, list) or not pending:
        raise RuntimeError("Pivot integration expected routed downstream stages.")
    for stage in pending:
        evidence_rel = f".opencode/state/artifacts/history/pivot/{stage}-completion.md"
        evidence_path = dest / evidence_rel
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(f"# {stage} completion\n", encoding="utf-8")
        run_json(
            [
                sys.executable,
                str(smoke.PIVOT_RECORD),
                str(dest),
                "--stage",
                stage,
                "--completed-by",
                stage,
                "--summary",
                f"Completed {stage} during integration coverage.",
                "--evidence",
                evidence_rel,
            ],
            ROOT,
        )
    published = run_json(
        [
            sys.executable,
            str(smoke.PIVOT_PUBLISH),
            str(dest),
            "--published-by",
            "integration-test",
        ],
        ROOT,
    )
    state = read_json(dest / ".opencode" / "meta" / "pivot-state.json")
    if not isinstance(state, dict):
        raise RuntimeError("Pivot integration expected persisted pivot state.")
    restart_inputs = state.get("restart_surface_inputs")
    if not isinstance(restart_inputs, dict) or restart_inputs.get("pivot_in_progress") is not False:
        raise RuntimeError("Pivot integration should clear pivot_in_progress once all routed downstream stages are completed.")
    if restart_inputs.get("pending_downstream_stages") not in ([], None):
        raise RuntimeError("Pivot integration should not leave pending downstream stages after all recorded completions.")
    if published["restart_surface_publication"]["status"] != "published":
        raise RuntimeError("Pivot integration should republish restart surfaces after pivot completion.")


def main() -> int:
    args = parse_args()
    fixtures = ensure_fixture_index()
    if args.list_fixtures:
        print(json.dumps(sorted(fixtures), indent=2))
        return 0
    with tempfile.TemporaryDirectory(prefix="scafforge-integration-") as workspace_root:
        workspace = Path(workspace_root)
        greenfield_integration(fixtures, workspace)
        repair_integration(fixtures, workspace)
        pivot_integration(fixtures, workspace)
    print("Scafforge integration test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
