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
LOG_DIR="${SCRIPT_DIR}/../active-plans/agent-logs"
mkdir -p "$LOG_DIR"

declare -A REPO_PATHS=(
  [gpttalker]="${PROJECTS_DIR}/GPTTalker"
  [spinner]="${PROJECTS_DIR}/spinner"
  [glitch]="${PROJECTS_DIR}/Scafforge/livetesting/glitch"
)

declare -A AGENT_NAMES=(
  [gpttalker]="gpttalker-team-leader"
  [spinner]="spinner-team-leader"
  [glitch]="glitch-team-leader"
)

MODEL="minimax-coding-plan/MiniMax-M2.7"
CODEX_MODEL="gpt-5.4"

usage() {
  cat <<USAGE
Usage: $0 <repo> [options]

Repos: gpttalker, spinner, glitch

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
    gpttalker|spinner|glitch) REPO="$1"; shift ;;
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
  AUDIT_PROMPT="You are a Scafforge auditor. Use the scafforge-audit skill to run a full diagnosis on this repository at ${REPO_PATH}.

Produce the four-report diagnosis pack:
1. Workflow health report
2. Contract compliance report
3. Process smell report
4. Recommendation report with evidence-backed ticket suggestions

Write all reports to the repo's diagnosis/ directory.
Do not modify any source code or ticket state."

  CMD=(codex exec "$AUDIT_PROMPT"
    -C "$REPO_PATH"
    -m "$CODEX_MODEL"
    --full-auto
  )

  echo "=== Scafforge Agent Runner (codex audit) ==="
  echo "Repo:    ${REPO} (${REPO_PATH})"
  echo "Model:   ${CODEX_MODEL}"

elif [[ "$MODE" == "repair" ]]; then
  REPAIR_PROMPT="You are a Scafforge repair operator. Use the scafforge-repair skill to apply managed repair to this repository at ${REPO_PATH}.

1. Read the latest diagnosis pack from diagnosis/
2. Apply the repair flow with full provenance
3. Record all stage completions with evidence paths
4. Do not skip follow-on stages

Write repair artifacts and update workflow state as the repair skill directs."

  CMD=(codex exec "$REPAIR_PROMPT"
    -C "$REPO_PATH"
    -m "$CODEX_MODEL"
    --full-auto
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
