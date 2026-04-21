from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PROMPT_PACK_NAME = "agent-caller-prompts.md"
ACTIVE_PLANS_DIRNAME = "active-plans"
DEFAULT_CHECKER_MODEL = "claude-sonnet-4.6"
DEFAULT_IMPLEMENTER_MODEL = "gpt-5.4"

COMMON_PLANCHECKER = """You are reviewing plan {{PLAN_ID}} ({{PLAN_TITLE}}) at {{PLAN_README}} inside the Scafforge implementation program.

Read-only mode:
- Do not edit files.
- Do not propose speculative implementation beyond the evidence.
- Use a rubber-duck review process first: restate the plan goal, dependencies, touched surfaces, validation gates, and completion criteria to yourself before judging it.

Review rules:
- Verify claims against the plan body, adjacent references, and the real repo surfaces when needed.
- Prefer non-interactive, automation-friendly, and headless-capable implementation paths by default, but do not assume Ubuntu/Linux unless the plan explicitly requires it.
- Assume all asset, tool, and integration recommendations must be free or open-source unless the plan explicitly justifies otherwise.
- Treat package-vs-output boundary violations, missing validation, missing documentation updates, or ambiguous ownership as serious issues.

Required output:
1. Verdict: valid / valid-with-fixes / flawed
2. Findings: numbered, evidence-based only
3. Refuted concerns: anything that looked suspicious but is actually fine
4. Required plan changes before implementation
5. Optional strengthening ideas, clearly separated from blockers
"""

COMMON_PLANIMPLEMENTER = """You are implementing plan {{PLAN_ID}} ({{PLAN_TITLE}}) from {{PLAN_README}}.

Execution rules:
- Treat the plan as the scope boundary.
- Read the plan fully before changing anything.
- Touch only the repo or adjacent repo surfaces the plan actually requires.
- Keep documentation, validators, and references aligned in the same change set where the plan says they must move together.
- Prefer small, reviewable edits that preserve existing contracts.
- If the plan targets an adjacent repository, make the implementation there and only update Scafforge docs where the dependency contract changes.

Quality rules:
- Prefer non-interactive, automation-friendly, and headless-capable implementation paths by default, but do not assume Ubuntu/Linux unless this specific plan explicitly requires it.
- Use only free/open-source asset or tooling recommendations unless the plan explicitly states otherwise.
- Do not silently skip validation; run the checks the plan requires and report what could not be run.

Required output:
- concise summary of what changed
- validation run and outcome
- remaining risks or blockers
"""

COMMON_PR_REVIEW_METHODOLOGY = """You are one reviewer in a multi-model PR review swarm for a PR implementing {{PLAN_ID}} ({{PLAN_TITLE}}).

Review methodology:
- Use the GitHub CLI to inspect the PR, its changed files, and any visible CI or discussion context.
- Judge only what you can support from the diff, repository context, and the plan requirements.
- Focus on correctness, regression risk, contract drift, missing validation, documentation drift, package/output boundary violations, and violations of the free-only/headless assumptions where they apply.
- Prefer a small number of high-confidence findings over broad speculation.
- If you find no material issues, say so explicitly.

Comment requirements:
- Post exactly one top-level PR comment with `gh pr comment`.
- Start with a short reviewer banner naming the model.
- Include: verdict, numbered findings (or “no material issues found”), open questions, and any residual risk.
- Do not approve or request changes through GitHub review state; post a normal comment only.
"""


@dataclass(frozen=True)
class ReviewProfile:
    key: str
    model: str
    variant: str | None
    heading: str


REVIEW_PROFILES: tuple[ReviewProfile, ...] = (
    ReviewProfile(
        key="big-pickle",
        model="opencode/big-pickle",
        variant="max",
        heading="planprreviewer big-pickle",
    ),
    ReviewProfile(
        key="minimax-m2.7",
        model="minimax-coding-plan/MiniMax-M2.7",
        variant="high",
        heading="planprreviewer minimax-m2.7",
    ),
    ReviewProfile(
        key="devstral-2512",
        model="mistral/devstral-2512",
        variant="high",
        heading="planprreviewer devstral-2512",
    ),
    ReviewProfile(
        key="mistral-large-latest",
        model="mistral/mistral-large-latest",
        variant="high",
        heading="planprreviewer mistral-large-latest",
    ),
    ReviewProfile(
        key="kimi-k2.5-turbo",
        model="fireworks-ai/accounts/fireworks/routers/kimi-k2p5-turbo",
        variant="high",
        heading="planprreviewer kimi-k2.5-turbo",
    ),
)


class AgentCallerError(RuntimeError):
    pass


def configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="agent-caller",
        description="Wrap copilot and opencode for the Scafforge active-plan workflow.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--plan", required=True, help="Plan id, folder name, or path")
    common.add_argument(
        "--repo-root",
        help="Override the Scafforge repo root. Defaults to the nearest ancestor containing active-plans/.",
    )
    common.add_argument(
        "--prompt-file",
        help="Override the prompt pack path. Defaults to references/agent-caller-prompts.md under the selected plan.",
    )
    common.add_argument(
        "--cwd",
        help="Working directory for the wrapped CLI. Defaults to the detected repo root.",
    )
    common.add_argument("--dry-run", action="store_true", help="Print commands without running them")
    common.add_argument("--json", action="store_true", help="Emit a JSON summary instead of plain text")

    checker = subparsers.add_parser("planchecker", parents=[common], help="Review a plan with Copilot in read-only mode")
    checker.add_argument("--model", default=DEFAULT_CHECKER_MODEL, help="Copilot model, default: claude-sonnet-4.6")
    checker.add_argument("--reasoning-effort", default="high", choices=["low", "medium", "high", "xhigh"])

    implementer = subparsers.add_parser("planimplementer", parents=[common], help="Implement a plan with Copilot")
    implementer.add_argument("--model", default=DEFAULT_IMPLEMENTER_MODEL, help="Copilot model, default: gpt-5.4")
    implementer.add_argument("--reasoning-effort", default="high", choices=["low", "medium", "high", "xhigh"])

    reviewer = subparsers.add_parser("planprreviewer", parents=[common], help="Run multi-model PR review through opencode")
    reviewer.add_argument("--pr", required=True, type=int, help="GitHub pull request number")
    reviewer.add_argument(
        "--owner-repo",
        help="GitHub repo in owner/name form. Defaults to gh repo view --json nameWithOwner.",
    )
    reviewer.add_argument(
        "--reviewers",
        help="Comma-separated subset of reviewers. Defaults to all: big-pickle,minimax-m2.7,devstral-2512,mistral-large-latest,kimi-k2.5-turbo",
    )
    reviewer.add_argument("--sequential", action="store_true", help="Run reviewers sequentially instead of concurrently")
    return parser.parse_args()


def main() -> int:
    configure_stdio()
    args = parse_args()
    repo_root = detect_repo_root(Path(args.repo_root).resolve() if args.repo_root else Path.cwd())
    plan_dir = resolve_plan(repo_root, args.plan)
    prompt_file = Path(args.prompt_file).resolve() if args.prompt_file else plan_dir / "references" / PROMPT_PACK_NAME
    if not prompt_file.exists():
        raise SystemExit(f"Prompt pack not found: {prompt_file}")
    workdir = Path(args.cwd).resolve() if args.cwd else repo_root

    if args.command == "planchecker":
        result = run_planchecker(repo_root, plan_dir, prompt_file, workdir, args)
    elif args.command == "planimplementer":
        result = run_planimplementer(repo_root, plan_dir, prompt_file, workdir, args)
    else:
        result = run_pr_reviewers(repo_root, plan_dir, prompt_file, workdir, args)

    if args.json:
        print(json.dumps(result, indent=2))
    elif isinstance(result, dict) and result.get("dry_run"):
        print(json.dumps(result, indent=2))
    elif isinstance(result, dict) and "stdout" in result:
        if result["stdout"]:
            print(result["stdout"], end="" if result["stdout"].endswith("\n") else "\n")
        if result.get("stderr"):
            print(result["stderr"], file=sys.stderr, end="" if result["stderr"].endswith("\n") else "\n")
    else:
        print(json.dumps(result, indent=2))
    return 0


def detect_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ACTIVE_PLANS_DIRNAME).is_dir():
            return candidate
    raise AgentCallerError(f"Could not find {ACTIVE_PLANS_DIRNAME}/ above {start}")


def resolve_plan(repo_root: Path, plan_ref: str) -> Path:
    candidate = Path(plan_ref)
    if candidate.exists():
        return candidate if candidate.is_dir() else candidate.parent
    plans_root = repo_root / ACTIVE_PLANS_DIRNAME
    if not plans_root.exists():
        raise AgentCallerError(f"Missing {plans_root}")
    normalized = plan_ref.strip().lower()
    numbered = [path for path in plans_root.iterdir() if path.is_dir() and re.match(r"^\d{2}-", path.name)]
    if normalized.isdigit():
        prefix = f"{int(normalized):02d}-"
        for path in numbered:
            if path.name.startswith(prefix):
                return path
    for path in numbered:
        if path.name.lower() == normalized:
            return path
    for path in numbered:
        if normalized in path.name.lower():
            return path
    raise AgentCallerError(f"Could not resolve plan: {plan_ref}")


def load_sections(prompt_file: Path) -> dict[str, str]:
    text = prompt_file.read_text(encoding="utf-8")
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        title = match.group(1).strip().lower()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()
    return sections


def render_section(section: str, variables: dict[str, str]) -> str:
    rendered = section
    for _ in range(3):
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def plan_variables(repo_root: Path, plan_dir: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    readme_path = plan_dir / "README.md"
    title = first_heading(readme_path)
    plan_id = plan_dir.name.split("-", 1)[0]
    variables = {
        "PLAN_ID": plan_id,
        "PLAN_FOLDER": plan_dir.name,
        "PLAN_TITLE": title,
        "PLAN_PATH": str(plan_dir),
        "PLAN_README": str(readme_path),
        "PLAN_REFERENCES": str(plan_dir / "references"),
        "REPO_ROOT": str(repo_root),
        "FREE_ONLY_NOTE": "Assume all asset, tooling, and integration recommendations must be free or open-source unless the plan already states otherwise.",
        "HEADLESS_LINUX_NOTE": "Prefer non-interactive, automation-friendly, and headless-capable execution paths by default, but do not assume Ubuntu/Linux unless the plan explicitly requires it.",
        "COMMON_PLANCHECKER": COMMON_PLANCHECKER,
        "COMMON_PLANIMPLEMENTER": COMMON_PLANIMPLEMENTER,
        "COMMON_PR_REVIEW_METHODOLOGY": COMMON_PR_REVIEW_METHODOLOGY,
    }
    if extra:
        variables.update(extra)
    return variables


def first_heading(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def run_planchecker(repo_root: Path, plan_dir: Path, prompt_file: Path, workdir: Path, args: argparse.Namespace) -> dict[str, object]:
    sections = load_sections(prompt_file)
    prompt = render_section(
        get_required_section(sections, "planchecker"),
        plan_variables(repo_root, plan_dir),
    )
    command = [
        "copilot",
        "-p",
        prompt,
        "--model",
        args.model,
        "--reasoning-effort",
        args.reasoning_effort,
        "--add-dir",
        str(repo_root),
        "--available-tools=view,grep,glob",
        "--allow-all-tools",
        "--no-ask-user",
        "--stream",
        "off",
        "-s",
    ]
    return execute_command("planchecker", command, workdir, args.dry_run)


def run_planimplementer(repo_root: Path, plan_dir: Path, prompt_file: Path, workdir: Path, args: argparse.Namespace) -> dict[str, object]:
    sections = load_sections(prompt_file)
    prompt = render_section(
        get_required_section(sections, "planimplementer"),
        plan_variables(repo_root, plan_dir),
    )
    command = [
        "copilot",
        "-p",
        prompt,
        "--model",
        args.model,
        "--reasoning-effort",
        args.reasoning_effort,
        "--add-dir",
        str(repo_root),
        "--allow-all",
        "--no-ask-user",
        "--stream",
        "off",
        "-s",
    ]
    return execute_command("planimplementer", command, workdir, args.dry_run)


def run_pr_reviewers(repo_root: Path, plan_dir: Path, prompt_file: Path, workdir: Path, args: argparse.Namespace) -> dict[str, object]:
    sections = load_sections(prompt_file)
    owner_repo = args.owner_repo or infer_owner_repo(workdir)
    selected = select_reviewers(args.reviewers)
    methodology = get_required_section(sections, "planprreviewer methodology")
    jobs = []
    for profile in selected:
        extra = {
            "PR_NUMBER": str(args.pr),
            "OWNER_REPO": owner_repo,
            "REVIEWER_KEY": profile.key,
            "REVIEWER_MODEL": profile.model,
            "REVIEWER_VARIANT": profile.variant or "",
            "REVIEW_METHODOLOGY": methodology,
        }
        prompt = render_section(
            f"{methodology}\n\n{get_required_section(sections, profile.heading)}",
            plan_variables(repo_root, plan_dir, extra=extra),
        )
        command = [
            "opencode",
            "run",
            prompt,
            "--dir",
            str(workdir),
            "--model",
            profile.model,
        ]
        if profile.variant:
            command.extend(["--variant", profile.variant])
        jobs.append((profile, command))

    results: list[dict[str, object]] = []
    if args.sequential or args.dry_run:
        for profile, command in jobs:
            result = execute_command(profile.key, command, workdir, args.dry_run)
            result["reviewer"] = profile.key
            results.append(result)
    else:
        with ThreadPoolExecutor(max_workers=len(jobs)) as executor:
            future_map = {
                executor.submit(execute_command, profile.key, command, workdir, False): profile.key
                for profile, command in jobs
            }
            for future in as_completed(future_map):
                result = future.result()
                result["reviewer"] = future_map[future]
                results.append(result)
    return {
        "command": "planprreviewer",
        "owner_repo": owner_repo,
        "pr": args.pr,
        "results": results,
    }


def select_reviewers(raw: str | None) -> list[ReviewProfile]:
    if not raw:
        return list(REVIEW_PROFILES)
    requested = {part.strip().lower() for part in raw.split(",") if part.strip()}
    profiles = [profile for profile in REVIEW_PROFILES if profile.key in requested]
    if not profiles:
        raise AgentCallerError(f"No matching reviewers in: {raw}")
    return profiles


def infer_owner_repo(workdir: Path) -> str:
    command = ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]
    result = subprocess.run(
        command,
        cwd=workdir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise AgentCallerError(f"Could not infer owner/repo with gh: {result.stderr.strip()}")
    value = result.stdout.strip()
    if not value:
        raise AgentCallerError("gh repo view returned an empty nameWithOwner")
    return value


def get_required_section(sections: dict[str, str], key: str) -> str:
    normalized = key.lower()
    if normalized not in sections:
        known = ", ".join(sorted(sections))
        raise AgentCallerError(f"Prompt section not found: {key}. Known sections: {known}")
    return sections[normalized]


def execute_command(label: str, command: Iterable[str], cwd: Path, dry_run: bool) -> dict[str, object]:
    command_list = resolve_command_executable(list(command))
    if dry_run:
        return {
            "label": label,
            "cwd": str(cwd),
            "command": command_list,
            "dry_run": True,
            "stdout": "",
            "stderr": "",
            "returncode": 0,
        }
    completed = subprocess.run(
        command_list,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=sanitized_env(),
    )
    return {
        "label": label,
        "cwd": str(cwd),
        "command": command_list,
        "dry_run": False,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
    }


def sanitized_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def resolve_command_executable(command: list[str]) -> list[str]:
    if not command:
        return command
    executable = command[0]
    if os.name == "nt" and executable.lower() == "opencode":
        resolved = shutil.which("opencode.cmd") or shutil.which("opencode.exe") or shutil.which(executable)
        if resolved:
            command[0] = resolved
    return command


if __name__ == "__main__":
    raise SystemExit(main())
