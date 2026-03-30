from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


SHARED_VERIFIER_PATH = Path(__file__).resolve().parents[2] / "scafforge-audit" / "scripts" / "shared_verifier.py"


def load_shared_verifier():
    spec = spec_from_file_location("scafforge_generated_scaffold_verifier", SHARED_VERIFIER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load shared verifier from {SHARED_VERIFIER_PATH}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SHARED_VERIFIER = load_shared_verifier()
verify_greenfield_continuation = SHARED_VERIFIER.verify_greenfield_continuation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify that a generated scaffold is immediately continuable before greenfield handoff."
    )
    parser.add_argument("repo_root", help="Generated repository root to verify.")
    parser.add_argument("--format", choices=("text", "json", "both"), default="text")
    return parser.parse_args()


def findings_payload(findings: list[object]) -> dict[str, object]:
    return {
        "repo_root": None,
        "verification_kind": "greenfield_continuation",
        "finding_count": len(findings),
        "immediately_continuable": not findings,
        "findings": [asdict(finding) for finding in findings],
    }


def render_text(repo_root: Path, findings: list[object]) -> str:
    if not findings:
        return f"PASS: {repo_root} is immediately continuable."

    lines = [f"FAIL: {repo_root} is not immediately continuable.", ""]
    for finding in findings:
        lines.append(f"[{finding.code}] {finding.problem}")
        if finding.evidence:
            lines.append(f"  Evidence: {finding.evidence[0]}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    findings = verify_greenfield_continuation(repo_root)
    payload = findings_payload(findings)
    payload["repo_root"] = str(repo_root)

    if args.format in {"text", "both"}:
        print(render_text(repo_root, findings))
    if args.format in {"json", "both"}:
        if args.format == "both":
            print()
        print(json.dumps(payload, indent=2))

    return 0 if not findings else 2


if __name__ == "__main__":
    raise SystemExit(main())
