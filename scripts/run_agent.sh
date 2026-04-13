#!/usr/bin/env bash
# Scafforge Downstream Agent Runner
# Two modes:
#   opencode — runs ticket lifecycle work via team-leader agent
#   audit/repair — runs scafforge-audit or scafforge-repair against a repo
#
# Usage:
#   ./run_agent.sh <repo>                              # opencode ticket work
#   ./run_agent.sh <repo> --audit                      # provider-aware scafforge-audit
#   ./run_agent.sh <repo> --repair                     # provider-aware scafforge-repair
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
CODEX_REASONING="medium"
KILO_MODELS=(
  "kilo/x-ai/grok-code-fast-1:optimized:free"
  "kilo/nvidia/nemotron-3-super-120b-a12b:free"
)
KILO_VARIANT="medium"
COPILOT_MODEL="gpt-5.4"
COPILOT_REASONING="medium"
EXEC_PROVIDER="auto"
FALLBACK_EXIT=125

usage() {
  cat <<USAGE
Usage: $0 <repo> [options]

Repos: gpttalker, spinner, glitch, wvhva, wvhvb, wvhvc, wvhvd

Modes (pick one):
  (default)         Run opencode ticket lifecycle via team-leader
  --audit           Run scafforge-audit on the repo
  --repair          Run scafforge-repair on the repo

Options:
  --continue        Continue last opencode session
  --prompt "msg"    Custom prompt (opencode mode only)
  --model "p/m"     Override opencode model
  --provider "p"    audit/repair host: auto|codex|kilo|copilot (default: auto)
  --dry-run         Print command without executing

Examples:
  $0 glitch                                    # opencode ticket work
  $0 glitch --audit                            # codex -> kilo -> copilot audit
  $0 glitch --repair                           # codex -> kilo -> copilot repair
  $0 glitch --audit --provider kilo            # force Kilo headless audit
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
    --provider) EXEC_PROVIDER="$2"; shift 2 ;;
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

case "$EXEC_PROVIDER" in
  auto|codex|kilo|copilot) ;;
  *)
    echo "Error: invalid provider '${EXEC_PROVIDER}' (expected auto, codex, kilo, or copilot)"
    exit 1
    ;;
esac

run_logged_cmd() {
  local label="$1"
  shift
  local attempt_log
  attempt_log="$(mktemp)"

  {
    echo ">>> Provider attempt: ${label}"
    printf '>>> Command:'
    printf ' %q' "$@"
    printf '\n'
  } | tee -a "$LOG_FILE"

  set +e
  "$@" < /dev/null 2>&1 | tee "$attempt_log" | tee -a "$LOG_FILE"
  local exit_code=${PIPESTATUS[0]}
  set -e

  echo ">>> Exit code (${label}): ${exit_code}" | tee -a "$LOG_FILE"

  LAST_ATTEMPT_LOG="$attempt_log"
  return "$exit_code"
}

provider_failure_is_fallback_eligible() {
  local attempt_log="$1"
  grep -Eiq \
    'rate limit|quota|usage limit|insufficient quota|429|not logged in|login required|authentication|auth failed|provider not found|model not found|network error|connection refused|timed out|temporarily unavailable|command not found' \
    "$attempt_log"
}

run_codex_exec() {
  if ! command -v codex >/dev/null 2>&1; then
    echo "codex CLI not found; falling back." | tee -a "$LOG_FILE"
    return "$FALLBACK_EXIT"
  fi

  if run_logged_cmd \
    "codex" \
    codex exec "$EXEC_PROMPT" \
      -C "$SCAFFORGE_ROOT" \
      --add-dir "$REPO_PATH" \
      -m "$CODEX_MODEL" \
      -c "model_reasoning_effort=\"${CODEX_REASONING}\"" \
      -c "plan_mode_reasoning_effort=\"${CODEX_REASONING}\"" \
      --skip-git-repo-check \
      --dangerously-bypass-approvals-and-sandbox; then
    EXECUTION_PROVIDER="codex"
    rm -f "$LAST_ATTEMPT_LOG"
    return 0
  fi

  local exit_code=$?
  if provider_failure_is_fallback_eligible "$LAST_ATTEMPT_LOG"; then
    echo "codex failed for a fallback-eligible reason; trying next provider." | tee -a "$LOG_FILE"
    rm -f "$LAST_ATTEMPT_LOG"
    return "$FALLBACK_EXIT"
  fi

  rm -f "$LAST_ATTEMPT_LOG"
  return "$exit_code"
}

run_kilo_exec() {
  if ! command -v kilo >/dev/null 2>&1; then
    echo "kilo CLI not found; falling back." | tee -a "$LOG_FILE"
    return "$FALLBACK_EXIT"
  fi

  local kilo_model
  for kilo_model in "${KILO_MODELS[@]}"; do
    if run_logged_cmd \
      "kilo ${kilo_model}" \
      kilo run "$EXEC_PROMPT" \
        --dir "$PROJECTS_DIR" \
        --model "$kilo_model" \
        --variant "$KILO_VARIANT" \
        --auto \
        --format default; then
      EXECUTION_PROVIDER="kilo"
      rm -f "$LAST_ATTEMPT_LOG"
      return 0
    fi

    local exit_code=$?
    if provider_failure_is_fallback_eligible "$LAST_ATTEMPT_LOG"; then
      echo "kilo model ${kilo_model} failed for a fallback-eligible reason." | tee -a "$LOG_FILE"
      rm -f "$LAST_ATTEMPT_LOG"
      continue
    fi

    rm -f "$LAST_ATTEMPT_LOG"
    return "$exit_code"
  done

  return "$FALLBACK_EXIT"
}

run_copilot_exec() {
  if ! command -v copilot >/dev/null 2>&1; then
    echo "copilot CLI not found." | tee -a "$LOG_FILE"
    return 127
  fi

  if run_logged_cmd \
    "copilot" \
    copilot \
      --model "$COPILOT_MODEL" \
      --reasoning-effort "$COPILOT_REASONING" \
      --allow-all \
      --no-ask-user \
      --mode autopilot \
      --output-format text \
      --add-dir "$SCAFFORGE_ROOT" \
      --add-dir "$REPO_PATH" \
      -p "$EXEC_PROMPT"; then
    EXECUTION_PROVIDER="copilot"
    rm -f "$LAST_ATTEMPT_LOG"
    return 0
  fi

  local exit_code=$?
  rm -f "$LAST_ATTEMPT_LOG"
  return "$exit_code"
}

run_provider_exec() {
  local requested_provider="$1"
  local provider
  local -a provider_order=()

  if [[ "$requested_provider" == "auto" ]]; then
    provider_order=(codex kilo copilot)
  else
    provider_order=("$requested_provider")
  fi

  for provider in "${provider_order[@]}"; do
    case "$provider" in
      codex)
        local exit_code
        if run_codex_exec; then
          exit_code=0
        else
          exit_code=$?
        fi
        if [[ "$exit_code" -eq 0 ]]; then
          return 0
        fi
        if [[ "$exit_code" -eq "$FALLBACK_EXIT" && "$requested_provider" == "auto" ]]; then
          continue
        fi
        return "$exit_code"
        ;;
      kilo)
        local exit_code
        if run_kilo_exec; then
          exit_code=0
        else
          exit_code=$?
        fi
        if [[ "$exit_code" -eq 0 ]]; then
          return 0
        fi
        if [[ "$exit_code" -eq "$FALLBACK_EXIT" && "$requested_provider" == "auto" ]]; then
          continue
        fi
        return "$exit_code"
        ;;
      copilot)
        run_copilot_exec
        return $?
        ;;
    esac
  done

  return 1
}

# --- Build command based on mode ---

if [[ "$MODE" == "opencode" ]]; then
  # Default resume prompt for opencode ticket work
  if [[ -z "$CUSTOM_PROMPT" ]]; then
    CUSTOM_PROMPT="You are resuming work on this project. Follow this sequence exactly:

1. Run ticket_lookup to get the current active ticket and workflow state
2. Read transition_guidance carefully — it is your executable contract
3. If pending_process_verification is true, check affected_done_tickets
4. If ticket_lookup.process_verification.clearable_now is true, clear pending_process_verification on the current writable ticket immediately via the recommended ticket_update before any split-parent or other lifecycle action
5. Execute the next action specified by transition_guidance
6. Do not skip stages. Do not invent workarounds. Follow the workflow.
7. Lifecycle status map: review -> review, qa -> qa, smoke-test -> smoke_test, closeout -> done.
8. Keep narration terse. Do not emit long self-handoff sections like Goal / Instructions / Discoveries / Accomplished / Next Steps unless you are reporting a real blocker.
9. If you can name the next legal tool call, execute it in the same run instead of stopping after a summary.
10. Continue working until the active ticket reaches closeout, you hit a team-leader stop condition, or no legal next action remains.
11. For split parents, remediation batches, and stale-follow-up sweeps, keep draining ready child tickets in the same run while legal next actions remain.
12. After delegating a specialist task, wait for the result, confirm the expected artifact or failure, then rerun ticket_lookup and continue in the same run.
13. Do not restart long Goal / Instructions / Discoveries / Accomplished / Next Steps recap blocks after routine progress; use one or two terse lines unless reporting a blocker.

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

  EXEC_PROMPT="$AUDIT_PROMPT"

  echo "=== Scafforge Agent Runner (audit) ==="
  echo "Repo:    ${REPO} (${REPO_PATH})"
  echo "Provider:${EXEC_PROVIDER} (auto order: codex -> kilo -> copilot)"
  echo "Codex:   ${CODEX_MODEL} reasoning=${CODEX_REASONING}"
  echo "Kilo:    ${KILO_MODELS[0]} -> ${KILO_MODELS[1]} variant=${KILO_VARIANT}"
  echo "Copilot: ${COPILOT_MODEL} reasoning=${COPILOT_REASONING}"

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
8. Do NOT call ./scripts/run_agent.sh ${REPO} --repair (or any equivalent nested repair wrapper) from inside this repair pass. Use the underlying Scafforge repair scripts directly: run_managed_repair.py, record_repair_stage_completion.py, reconcile_repair_follow_on.py, and any required follow-on skill scripts.
9. Report whether repair converged and what managed/source follow-up still remains.

Do not hand-edit downstream product code directly."

  EXEC_PROMPT="$REPAIR_PROMPT"

  echo "=== Scafforge Agent Runner (repair) ==="
  echo "Repo:    ${REPO} (${REPO_PATH})"
  echo "Provider:${EXEC_PROVIDER} (auto order: codex -> kilo -> copilot)"
  echo "Codex:   ${CODEX_MODEL} reasoning=${CODEX_REASONING}"
  echo "Kilo:    ${KILO_MODELS[0]} -> ${KILO_MODELS[1]} variant=${KILO_VARIANT}"
  echo "Copilot: ${COPILOT_MODEL} reasoning=${COPILOT_REASONING}"

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
  if [[ "$MODE" == "opencode" ]]; then
    printf '  %s\n' "${CMD[@]}"
  else
    echo "  provider order: ${EXEC_PROVIDER}"
    echo "  codex: codex exec ... -c model_reasoning_effort=\"${CODEX_REASONING}\" ..."
    echo "  kilo:  kilo run ... --dir ${PROJECTS_DIR} --variant ${KILO_VARIANT} ..."
    echo "  copilot: copilot --reasoning-effort ${COPILOT_REASONING} -p ..."
  fi
  exit 0
fi

echo ""
echo "Starting agent... (output → ${LOG_FILE})"
echo "Press Ctrl+C to abort"
echo ""

if [[ "$MODE" == "opencode" ]]; then
  "${CMD[@]}" < /dev/null 2>&1 | tee "$LOG_FILE"
  EXIT_CODE=${PIPESTATUS[0]}
else
  : > "$LOG_FILE"
  run_provider_exec "$EXEC_PROVIDER"
  EXIT_CODE=$?
fi

echo ""
echo "=== Agent finished ==="
echo "Exit code: ${EXIT_CODE}"
echo "Log saved: ${LOG_FILE}"
if [[ "$MODE" != "opencode" ]]; then
  echo "Resolved provider: ${EXECUTION_PROVIDER:-none}"
fi

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
