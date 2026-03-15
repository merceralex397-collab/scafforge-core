from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "skills" / "repo-scaffold-factory" / "scripts" / "bootstrap_repo_scaffold.py"
CHECKLIST = ROOT / "skills" / "repo-scaffold-factory" / "references" / "opencode-conformance-checklist.json"


def run(command: list[str], cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")


def verify_render(dest: Path, *, expect_full_repo: bool) -> None:
    checklist = json.loads(CHECKLIST.read_text(encoding="utf-8"))
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


def main() -> int:
    workspace = Path(tempfile.mkdtemp(prefix="scafforge-smoke-"))
    try:
        full_dest = workspace / "full"
        opencode_dest = workspace / "opencode"

        common = [
            "python",
            str(BOOTSTRAP),
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
            "--stack-label",
            "framework-agnostic",
            "--force",
        ]

        run(common + ["--dest", str(full_dest), "--scope", "full"], ROOT)
        run(common + ["--dest", str(opencode_dest), "--scope", "opencode"], ROOT)

        verify_render(full_dest, expect_full_repo=True)
        verify_render(opencode_dest, expect_full_repo=False)

        print("Scafforge smoke test passed.")
        return 0
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
