from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
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
- Use the supplied PR metadata and unified diff as primary evidence.
- Use local repo context only when it materially helps interpret the diff.
- Judge only what you can support from the diff, repository context, and the plan requirements.
- Focus on correctness, regression risk, contract drift, missing validation, documentation drift, package/output boundary violations, and violations of the free-only/headless assumptions where they apply.
- Prefer a small number of high-confidence findings over broad speculation.
- If you find no material issues, say so explicitly.

Comment requirements:
- Start the comment with the exact reviewer banner `{{REVIEWER_BANNER}}`.
- Return only the final markdown body for that one PR comment. Do not include preambles, tool narration, or any text outside the comment body.
- Use this exact shape:
  `{{REVIEWER_BANNER}}`
  `Verdict: <valid | valid-with-fixes | flawed>`
  `Findings:`
  `1. ...`
  `Open Questions:`
  `- ...`
  `Residual Risk:`
  `- ...`
- If there are no material issues, still fill the structure and write `1. No material issues found.` under `Findings:`.
- Do not approve or request changes through GitHub review state; `agent-caller` will post your returned markdown as a normal top-level PR comment.
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
    try:
        args = parse_args()
        repo_root = detect_repo_root(Path(args.repo_root).resolve() if args.repo_root else Path.cwd())
        plan_dir = resolve_plan(repo_root, args.plan)
        prompt_file = Path(args.prompt_file).resolve() if args.prompt_file else plan_dir / "references" / PROMPT_PACK_NAME
        if not prompt_file.exists():
            raise AgentCallerError(f"Prompt pack not found: {prompt_file}")
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
        return result_exit_code(result)
    except (AgentCallerError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


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
    numbered = [path for path in plans_root.iterdir() if path.is_dir() and re.match(r"^\d+-", path.name)]
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
    pr_context = fetch_pr_context(owner_repo, args.pr, workdir)
    jobs = []
    for profile in selected:
        reviewer_banner = f"[planprreviewer:{profile.key}:{uuid.uuid4().hex[:8]}]"
        extra = {
            "PR_NUMBER": str(args.pr),
            "OWNER_REPO": owner_repo,
            "PR_METADATA": pr_context["metadata"],
            "PR_DIFF": pr_context["diff"],
            "REVIEWER_KEY": profile.key,
            "REVIEWER_MODEL": profile.model,
            "REVIEWER_VARIANT": profile.variant or "",
            "REVIEWER_BANNER": reviewer_banner,
            "REVIEW_METHODOLOGY": methodology,
        }
        prompt = render_section(
            f"{methodology}\n\nPR metadata:\n{{{{PR_METADATA}}}}\n\nUnified diff:\n```diff\n{{{{PR_DIFF}}}}\n```\n\n{get_required_section(sections, profile.heading)}",
            plan_variables(repo_root, plan_dir, extra=extra),
        )
        prompt_file_path = write_temp_prompt_file(prompt)
        command = [
            "opencode",
            "run",
            "Read the attached review brief and return only the final markdown PR comment body.",
            "--file",
            prompt_file_path,
            "--dir",
            str(workdir),
            "--model",
            profile.model,
        ]
        if profile.variant:
            command.extend(["--variant", profile.variant])
        jobs.append((profile, command, reviewer_banner, prompt_file_path))

    results: list[dict[str, object]] = []
    if args.sequential or args.dry_run:
        for profile, command, reviewer_banner, prompt_file_path in jobs:
            try:
                result = execute_command(profile.key, command, workdir, args.dry_run)
                if not args.dry_run:
                    publish_reviewer_comment(result, owner_repo, args.pr, reviewer_banner, workdir)
                result["reviewer"] = profile.key
                result["reviewer_banner"] = reviewer_banner
                results.append(result)
            finally:
                delete_temp_file(prompt_file_path)
    else:
        with ThreadPoolExecutor(max_workers=len(jobs)) as executor:
            future_map = {
                executor.submit(execute_command, profile.key, command, workdir, False): (profile.key, reviewer_banner, prompt_file_path)
                for profile, command, reviewer_banner, prompt_file_path in jobs
            }
            for future in as_completed(future_map):
                result = future.result()
                reviewer_key, reviewer_banner, prompt_file_path = future_map[future]
                try:
                    publish_reviewer_comment(result, owner_repo, args.pr, reviewer_banner, workdir)
                    result["reviewer"] = reviewer_key
                    result["reviewer_banner"] = reviewer_banner
                    results.append(result)
                finally:
                    delete_temp_file(prompt_file_path)
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


def fetch_pr_context(owner_repo: str, pr_number: int, cwd: Path) -> dict[str, str]:
    view_command = [
        "gh",
        "pr",
        "view",
        str(pr_number),
        "--repo",
        owner_repo,
        "--json",
        "title,body,baseRefName,headRefName,url,files",
    ]
    view = subprocess.run(
        view_command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=sanitized_env(),
    )
    if view.returncode != 0:
        raise AgentCallerError(f"Could not fetch PR metadata with gh: {view.stderr.strip()}")
    try:
        payload = json.loads(view.stdout)
    except json.JSONDecodeError as exc:
        raise AgentCallerError(f"Could not parse PR metadata JSON: {exc}") from exc

    files = payload.get("files") or []
    file_lines = []
    for file_info in files:
        path = file_info.get("path", "<unknown>")
        additions = file_info.get("additions", 0)
        deletions = file_info.get("deletions", 0)
        file_lines.append(f"- {path} (+{additions}/-{deletions})")
    metadata = "\n".join(
        [
            f"URL: {payload.get('url', '')}",
            f"Title: {payload.get('title', '')}",
            f"Base: {payload.get('baseRefName', '')}",
            f"Head: {payload.get('headRefName', '')}",
            "Body:",
            str(payload.get("body", "") or "").strip(),
            "Changed files:",
            "\n".join(file_lines) if file_lines else "- <no files listed>",
        ]
    ).strip()

    diff_command = ["gh", "pr", "diff", str(pr_number), "--repo", owner_repo]
    diff = subprocess.run(
        diff_command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=sanitized_env(),
    )
    if diff.returncode != 0:
        raise AgentCallerError(f"Could not fetch PR diff with gh: {diff.stderr.strip()}")
    diff_text = diff.stdout.strip()
    max_chars = 120_000
    if len(diff_text) > max_chars:
        diff_text = f"{diff_text[:max_chars]}\n\n[diff truncated by agent-caller]"
    return {"metadata": metadata, "diff": diff_text}


def write_temp_prompt_file(prompt: str) -> str:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".md") as handle:
        handle.write(prompt)
        return handle.name


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


def fetch_issue_comments(owner_repo: str, pr_number: int, cwd: Path) -> list[dict[str, object]]:
    command = [
        "gh",
        "api",
        f"repos/{owner_repo}/issues/{pr_number}/comments",
        "--paginate",
    ]
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=sanitized_env(),
    )
    if completed.returncode != 0:
        raise AgentCallerError(f"Could not fetch PR comments with gh api: {completed.stderr.strip()}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AgentCallerError(f"Could not parse PR comments JSON: {exc}") from exc
    if not isinstance(payload, list):
        raise AgentCallerError("Unexpected PR comments payload shape from gh api")
    return payload


def publish_reviewer_comment(
    result: dict[str, object],
    owner_repo: str,
    pr_number: int,
    reviewer_banner: str,
    cwd: Path,
) -> None:
    comment_body = extract_comment_body(result, reviewer_banner)
    if not comment_body:
        stderr = str(result.get("stderr", "") or "")
        if stderr:
            stderr = f"{stderr.rstrip()}\n"
        stderr += f"Reviewer did not return a valid PR comment body starting with banner: {reviewer_banner}\n"
        result["stderr"] = stderr
        result["returncode"] = int(result.get("returncode", 0) or 0) or 1
        result["comment_verified"] = False
        return

    post_reviewer_comment(owner_repo, pr_number, comment_body, cwd)
    comments = fetch_issue_comments(owner_repo, pr_number, cwd)
    posted = any(reviewer_banner in str(comment.get("body", "")) for comment in comments)
    result["comment_verified"] = posted
    if posted:
        return
    stderr = str(result.get("stderr", "") or "")
    if stderr:
        stderr = f"{stderr.rstrip()}\n"
    stderr += f"Reviewer did not post the required PR comment banner: {reviewer_banner}\n"
    result["stderr"] = stderr
    result["returncode"] = int(result.get("returncode", 0) or 0) or 1


def extract_comment_body(result: dict[str, object], reviewer_banner: str) -> str:
    stdout = str(result.get("stdout", "") or "").strip()
    if not stdout:
        return ""
    lowered = stdout.lower()
    if "please provide the specific details" in lowered:
        return ""
    body = stdout
    if reviewer_banner in body:
        body = body[body.find(reviewer_banner):].strip()
    else:
        start_markers = [
            "Verdict:",
            "## PR Review",
            "## PR Review Summary",
            "## Review",
            "### Verdict",
            "**Verdict:**",
        ]
        for marker in start_markers:
            if marker in body:
                body = body[body.find(marker):].strip()
                break
        body = strip_tool_narration(body)
        body = f"{reviewer_banner}\n\n{body}".strip()
    body = strip_tool_narration(body)
    if reviewer_banner not in body:
        body = f"{reviewer_banner}\n\n{body}".strip()
    if len(body) < len(reviewer_banner) + 40:
        return ""
    return body


def post_reviewer_comment(owner_repo: str, pr_number: int, comment_body: str, cwd: Path) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".md") as handle:
        handle.write(comment_body)
        temp_path = handle.name
    try:
        command = [
            "gh",
            "pr",
            "comment",
            str(pr_number),
            "--repo",
            owner_repo,
            "--body-file",
            temp_path,
        ]
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env=sanitized_env(),
        )
        if completed.returncode != 0:
            raise AgentCallerError(f"Could not post reviewer comment with gh: {completed.stderr.strip()}")
    finally:
        try:
            delete_temp_file(temp_path)
        except OSError:
            pass


def strip_tool_narration(body: str) -> str:
    skip_prefixes = (
        "let me ",
        "now let me ",
        "i understand",
        "perfect!",
        "great!",
        "i'm unable",
        "i am unable",
    )
    cleaned: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and stripped.lower().startswith(skip_prefixes):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def delete_temp_file(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


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


def result_exit_code(result: dict[str, object]) -> int:
    if result.get("dry_run"):
        return 0
    if "results" in result:
        return max(int(item.get("returncode", 0) or 0) for item in result["results"])
    return int(result.get("returncode", 0) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
