#!/usr/bin/env bash
# Scafforge Downstream Agent Runner
# Two modes:
#   opencode — runs ticket lifecycle work via team-leader agent
#   codex    — runs scafforge-audit or scafforge-repair against a repo
#
# Usage:
#   ./run_agent.sh <repo>                              # opencode ticket work
#   ./run_agent.sh <repo> --audit                      # codex scafforge-audit
#   ./run_agent.sh <repo> --repair                     # codex scafforge-repair
#   ./run_agent.sh <repo> --continue                   # resume opencode session
#   ./run_agent.sh <repo> --prompt "custom message"    # custom opencode prompt

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECTS_DIR="/home/pc/projects"
SCAFFORGE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${SCRIPT_DIR}/../active-plans/agent-logs"
mkdir -p "$LOG_DIR"

declare -A REPO_PATHS=(
  [gpttalker]="${PROJECTS_DIR}/GPTTalker"
  [spinner]="${PROJECTS_DIR}/spinner"
  [glitch]="${PROJECTS_DIR}/Scafforge/livetesting/glitch"
  [wvhva]="${PROJECTS_DIR}/womanvshorseVA"
  [wvhvb]="${PROJECTS_DIR}/womanvshorseVB"
  [wvhvc]="${PROJECTS_DIR}/womanvshorseVC"
  [wvhvd]="${PROJECTS_DIR}/womanvshorseVD"
)

declare -A AGENT_NAMES=(
  [gpttalker]="gpttalker-team-leader"
  [spinner]="spinner-team-leader"
  [glitch]="glitch-team-leader"
  [wvhva]="wvhva-team-leader"
  [wvhvb]="wvhvb-team-leader"
  [wvhvc]="wvhvc-team-leader"
  [wvhvd]="wvhvd-team-leader"
)

MODEL="minimax-coding-plan/MiniMax-M2.7"
CODEX_MODEL="gpt-5.4"

usage() {
  cat <<USAGE
Usage: $0 <repo> [options]

Repos: gpttalker, spinner, glitch, wvhva, wvhvb, wvhvc, wvhvd

Modes (pick one):
  (default)         Run opencode ticket lifecycle via team-leader
  --audit           Run codex scafforge-audit on the repo
  --repair          Run codex scafforge-repair on the repo

Options:
  --continue        Continue last opencode session
  --prompt "msg"    Custom prompt (opencode mode only)
  --model "p/m"     Override opencode model
  --dry-run         Print command without executing

Examples:
  $0 glitch                                    # opencode ticket work
  $0 glitch --audit                            # codex audit
  $0 glitch --repair                           # codex repair
  $0 spinner --continue                        # resume last opencode session
  $0 wvhva                                     # resume womanvshorseVA
  $0 wvhvc --prompt "Focus on MODEL-002"       # custom prompt for womanvshorseVC
  $0 glitch --prompt "Focus on CORE-002"       # custom opencode prompt
USAGE
  exit 1
}

# Parse args
REPO=""
MODE="opencode"  # opencode | audit | repair
CONTINUE_FLAG=""
CUSTOM_PROMPT=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    gpttalker|spinner|glitch|wvhva|wvhvb|wvhvc|wvhvd) REPO="$1"; shift ;;
    womanvshorseVA|womanvshorseva) REPO="wvhva"; shift ;;
    womanvshorseVB|womanvshorsevb) REPO="wvhvb"; shift ;;
    womanvshorseVC|womanvshorsevc) REPO="wvhvc"; shift ;;
    womanvshorseVD|womanvshorsevd) REPO="wvhvd"; shift ;;
    --audit)   MODE="audit";  shift ;;
    --repair)  MODE="repair"; shift ;;
    --continue) CONTINUE_FLAG="--continue"; shift ;;
    --prompt) CUSTOM_PROMPT="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown arg: $1"; usage ;;
  esac
done

[[ -z "$REPO" ]] && { echo "Error: repo name required"; usage; }

REPO_PATH="${REPO_PATHS[$REPO]}"
AGENT="${AGENT_NAMES[$REPO]}"
TIMESTAMP="$(date +%Y-%m-%dT%H-%M-%S)"
LOG_FILE="${LOG_DIR}/${REPO}-${MODE}-${TIMESTAMP}.log"

# --- Build command based on mode ---

if [[ "$MODE" == "opencode" ]]; then
  # Default resume prompt for opencode ticket work
  if [[ -z "$CUSTOM_PROMPT" ]]; then
    CUSTOM_PROMPT="You are resuming work on this project. Follow this sequence exactly:

1. Run ticket_lookup to get the current active ticket and workflow state
2. Read transition_guidance carefully — it is your executable contract
3. If pending_process_verification is true, check affected_done_tickets
4. Execute the next action specified by transition_guidance
5. Do not skip stages. Do not invent workarounds. Follow the workflow.

If you encounter a blocker you cannot resolve after 3 attempts, stop and report it clearly with the exact error and what you tried."
  fi

  CMD=(opencode run "$CUSTOM_PROMPT"
    --dir "$REPO_PATH"
    --model "$MODEL"
    --agent "$AGENT"
    $CONTINUE_FLAG
  )

  echo "=== Scafforge Agent Runner (opencode) ==="
  echo "Repo:    ${REPO} (${REPO_PATH})"
  echo "Agent:   ${AGENT}"
  echo "Model:   ${MODEL}"

elif [[ "$MODE" == "audit" ]]; then
  AUDIT_PROMPT="You are a Scafforge auditor operating from the Scafforge package repo.

Run the canonical shipped audit flow against ${REPO_PATH} using Scafforge-owned scripts under ${SCAFFORGE_ROOT}.

Required behavior:
1. Read the latest diagnosis state in ${REPO_PATH}/diagnosis/ and current workflow metadata.
2. Run the canonical Scafforge audit command for the downstream repo.
3. Emit the four-report diagnosis pack into the downstream repo's diagnosis/ directory.
4. Do not modify source code, ticket state, or workflow state.

Use command-backed evidence only and avoid improvised package-root wrappers."

  CMD=(codex exec "$AUDIT_PROMPT"
    -C "$SCAFFORGE_ROOT"
    --add-dir "$REPO_PATH"
    -m "$CODEX_MODEL"
    --skip-git-repo-check
    --dangerously-bypass-approvals-and-sandbox
  )

  echo "=== Scafforge Agent Runner (codex audit) ==="
  echo "Repo:    ${REPO} (${REPO_PATH})"
  echo "Model:   ${CODEX_MODEL}"

elif [[ "$MODE" == "repair" ]]; then
  REPAIR_PROMPT="You are a Scafforge repair operator operating from the Scafforge package repo.

Run the canonical shipped repair flow against ${REPO_PATH} using Scafforge-owned scripts under ${SCAFFORGE_ROOT}.

Required behavior:
1. Read the latest diagnosis pack from ${REPO_PATH}/diagnosis/.
2. Confirm the latest diagnosis does not require package_work_required_first.
3. Run the canonical managed repair runner with full provenance.
4. If the repair cycle declares required follow-on stages like project-skill-bootstrap, opencode-team-bootstrap, agent-prompt-engineering, or ticket-pack-builder, continue into those stages using the shipped Scafforge skill instructions and emit/record the canonical completion evidence for the current cycle.
5. After the last required follow-on stage is recorded, run the canonical reconciler to update workflow-state.json and restart surfaces.
6. If you need a verification rerun after follow-on completion, use the managed repair runner with --skip-deterministic-refresh so you verify the current cycle without reopening a fresh deterministic refresh cycle.
7. Do NOT rerun the full public repair runner after follow-on completion unless you are intentionally starting a brand-new repair cycle from new diagnosis evidence. A full rerun after follow-on completion can recreate placeholder-skill drift and managed_blocked state.
8. Report whether repair converged and what managed/source follow-up still remains.

Do not hand-edit downstream product code directly."

  CMD=(codex exec "$REPAIR_PROMPT"
    -C "$SCAFFORGE_ROOT"
    --add-dir "$REPO_PATH"
    -m "$CODEX_MODEL"
    --skip-git-repo-check
    --dangerously-bypass-approvals-and-sandbox
  )

  echo "=== Scafforge Agent Runner (codex repair) ==="
  echo "Repo:    ${REPO} (${REPO_PATH})"
  echo "Model:   ${CODEX_MODEL}"

else
  echo "Error: unknown mode '$MODE'"
  exit 1
fi

echo "Log:     ${LOG_FILE}"
echo "Time:    ${TIMESTAMP}"
echo "==============================="

if $DRY_RUN; then
  echo ""
  echo "DRY RUN — would execute:"
  printf '  %s\n' "${CMD[@]}"
  exit 0
fi

echo ""
echo "Starting agent... (output → ${LOG_FILE})"
echo "Press Ctrl+C to abort"
echo ""

"${CMD[@]}" < /dev/null 2>&1 | tee "$LOG_FILE"
EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "=== Agent finished ==="
echo "Exit code: ${EXIT_CODE}"
echo "Log saved: ${LOG_FILE}"

# Post-run ticket state check (only for repos with manifests)
if [[ -f "${REPO_PATH}/tickets/manifest.json" ]]; then
  echo ""
  echo "=== Post-run ticket state ==="
  python3 -c "
import json
m = json.load(open('${REPO_PATH}/tickets/manifest.json'))
done = sum(1 for t in m['tickets'] if t['status'] == 'done')
total = len(m['tickets'])
print(f'Tickets: {done}/{total} done')
print(f'Active: {m[\"active_ticket\"]}')
for t in m['tickets']:
    if t['status'] != 'done':
        print(f'  {t[\"id\"]:25s} stage={t[\"stage\"]:15s} status={t[\"status\"]}')
" 2>/dev/null || true
fi

exit $EXIT_CODE
