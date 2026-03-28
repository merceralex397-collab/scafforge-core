import { type Plugin } from "@opencode-ai/plugin"
import {
  allowsPreBootstrapWriteClaim,
  getTicket,
  getProcessVerificationState,
  getTicketWorkflowState,
  hasArtifact,
  hasReviewArtifact,
  hasWriteLeaseForTicketPath,
  hasWriteLeaseForTicket,
  isPlanApprovedForTicket,
  loadManifest,
  loadWorkflowState,
  resolveRequestedTicketProgress,
  ticketClaimBlockerArgs,
  throwWorkflowBlocker,
  validateLifecycleStageStatus,
  validateImplementationArtifactEvidence,
  validateQaArtifactEvidence,
  validateSmokeTestArtifactEvidence,
} from "../lib/workflow"

const SAFE_BASH = /^(pwd|ls|find|rg|grep|cat|head|tail|git status|git diff|git log)\b/i
const BOOTSTRAP_RECOVERY_BASH = /^(uv|python|python3|pytest|ruff|\.venv\/bin\/python|\.venv\/bin\/pytest|\.venv\/bin\/ruff)\b/i
const LEASED_ARTIFACT_STAGES = new Set(["implementation", "bootstrap", "handoff"])
const RESERVED_ARTIFACT_STAGES = new Set(["smoke-test"])
const HISTORICAL_VERIFICATION_KINDS = new Set(["backlog-verification", "reverification"])

function extractFilePath(args: Record<string, unknown>): string {
  const pathValue = args.filePath || args.path || args.target
  return typeof pathValue === "string" ? pathValue : ""
}

function isDocPath(pathValue: string): boolean {
  return (
    pathValue.startsWith("docs/") ||
    pathValue.startsWith("tickets/") ||
    pathValue.endsWith("README.md") ||
    pathValue.endsWith("AGENTS.md") ||
    pathValue.endsWith("START-HERE.md")
  )
}
function isBootstrapRecoveryCommand(command: string, bootstrapStatus: string): boolean {
  return bootstrapStatus !== "ready" && BOOTSTRAP_RECOVERY_BASH.test(command)
}
function isHistoricalVerificationArtifactMutation(ticket: ReturnType<typeof getTicket>, stage: string, kind: unknown): boolean {
  return ticket.status === "done" && ticket.resolution_state !== "open" && stage === "review" && typeof kind === "string" && HISTORICAL_VERIFICATION_KINDS.has(kind)
}

async function ensureBootstrapReadyForValidation() {
  const workflow = await loadWorkflowState()
  if (workflow.bootstrap.status !== "ready") {
    throwWorkflowBlocker({
      type: "BLOCKER",
      reason_code: "bootstrap_not_ready",
      explanation: `Bootstrap ${workflow.bootstrap.status}. Run environment_bootstrap before continuing lifecycle work.`,
      next_action_tool: "environment_bootstrap",
      next_action_args: {},
    })
  }
}

async function ensureWriteLease(pathValue?: string) {
  const workflow = await loadWorkflowState()
  if (!hasWriteLeaseForTicket(workflow, workflow.active_ticket)) {
    throwWorkflowBlocker({
      type: "BLOCKER",
      reason_code: "missing_write_lease",
      explanation: `Active ticket ${workflow.active_ticket} must hold an active write lease before write-capable work can proceed.`,
      next_action_tool: "ticket_claim",
      next_action_args: ticketClaimBlockerArgs(workflow.active_ticket),
    })
  }
  if (pathValue && !hasWriteLeaseForTicketPath(workflow, workflow.active_ticket, pathValue)) {
    throwWorkflowBlocker({
      type: "BLOCKER",
      reason_code: "write_path_not_covered",
      explanation: `The active write lease for ${workflow.active_ticket} does not cover ${pathValue}.`,
      next_action_tool: "ticket_claim",
      next_action_args: ticketClaimBlockerArgs(workflow.active_ticket, [pathValue]),
    })
  }
}

async function ensureTargetTicketWriteLease(ticketId: string) {
  const workflow = await loadWorkflowState()
  if (!hasWriteLeaseForTicket(workflow, ticketId)) {
    throwWorkflowBlocker({
      type: "BLOCKER",
      reason_code: "missing_ticket_write_lease",
      explanation: `Ticket ${ticketId} must hold an active write lease before this mutation can proceed.`,
      next_action_tool: "ticket_claim",
      next_action_args: ticketClaimBlockerArgs(ticketId),
    })
  }
}

function isWorkflowProcessVerificationClearOnly(args: Record<string, unknown>): boolean {
  return (
    args.pending_process_verification === false &&
    typeof args.stage === "undefined" &&
    typeof args.status === "undefined" &&
    typeof args.summary === "undefined" &&
    typeof args.activate === "undefined" &&
    typeof args.approved_plan === "undefined"
  )
}

export const StageGateEnforcer: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      const workflow = await loadWorkflowState().catch(() => undefined)
      if (!workflow) return

      const activeApprovedPlan = isPlanApprovedForTicket(workflow, workflow.active_ticket)

      if (input.tool === "bash") {
        const command = typeof output.args.command === "string" ? output.args.command : ""
        const bootstrapRecoveryCommand = isBootstrapRecoveryCommand(command, workflow.bootstrap.status)
        if (!activeApprovedPlan && !SAFE_BASH.test(command) && !bootstrapRecoveryCommand) {
          throw new Error("The active ticket needs an approved plan before running implementation-oriented shell commands.")
        }
        if (!SAFE_BASH.test(command) && !bootstrapRecoveryCommand) {
          await ensureWriteLease()
        }
      }

      if (input.tool === "write" || input.tool === "edit") {
        const filePath = extractFilePath(output.args)
        if (!activeApprovedPlan && (!filePath || !isDocPath(filePath))) {
          throw new Error("The active ticket needs an approved plan before editing implementation files.")
        }
        if (filePath && !isDocPath(filePath)) {
          await ensureWriteLease(filePath)
        }
      }

      if (input.tool === "ticket_claim") {
        const manifest = await loadManifest()
        const ticketId = typeof output.args.ticket_id === "string" ? output.args.ticket_id : manifest.active_ticket
        const ticket = getTicket(manifest, ticketId)
        if (ticket.status === "done" || ticket.resolution_state === "superseded") {
          throw new Error(`Ticket ${ticket.id} cannot be claimed because it is already closed.`)
        }
        if (output.args.write_lock !== false && !allowsPreBootstrapWriteClaim(workflow, ticket)) {
          await ensureBootstrapReadyForValidation()
        }
      }

      if (input.tool === "ticket_release") {
        const ticketId = typeof output.args.ticket_id === "string" ? output.args.ticket_id : workflow.active_ticket
        const ownerAgent = typeof output.args.owner_agent === "string" ? output.args.owner_agent.trim() : ""
        if (!ownerAgent) {
          throw new Error("ticket_release requires owner_agent.")
        }
        const lease = workflow.lane_leases.find((candidate) => candidate.ticket_id === ticketId && candidate.owner_agent === ownerAgent)
        if (!lease) {
          throw new Error(`Ticket ${ticketId} does not currently hold an active lease.`)
        }
      }

      if (input.tool === "ticket_create") {
        const manifest = await loadManifest()
        const sourceMode = typeof output.args.source_mode === "string" ? output.args.source_mode : "net_new_scope"
        const sourceTicketId = typeof output.args.source_ticket_id === "string" ? output.args.source_ticket_id : ""
        if (sourceMode === "process_verification" && !workflow.pending_process_verification) {
          throw new Error("process_verification follow-up creation is only available while pending_process_verification is true.")
        }
        if (sourceMode === "net_new_scope") {
          await ensureTargetTicketWriteLease(workflow.active_ticket)
        } else if (sourceMode === "split_scope") {
          if (!sourceTicketId) throw new Error("split_scope ticket creation requires source_ticket_id.")
          await ensureTargetTicketWriteLease(sourceTicketId)
          const sourceTicket = getTicket(manifest, sourceTicketId)
          if (!["open", "reopened"].includes(sourceTicket.resolution_state) || sourceTicket.status === "done") {
            throw new Error(`split_scope ticket creation requires an open or reopened source ticket. ${sourceTicket.id} is not currently eligible.`)
          }
        }
        if (sourceMode === "post_completion_issue") {
          if (!sourceTicketId) throw new Error("post_completion_issue ticket creation requires source_ticket_id.")
          if (typeof output.args.evidence_artifact_path !== "string" || !output.args.evidence_artifact_path.trim()) {
            throw new Error("post_completion_issue ticket creation requires evidence_artifact_path.")
          }
          const sourceTicket = getTicket(manifest, sourceTicketId)
          if (sourceTicket.status !== "done" && sourceTicket.resolution_state !== "done" && sourceTicket.resolution_state !== "superseded") {
            throw new Error(`Source ticket ${sourceTicket.id} is not in a completed historical state suitable for post-completion issue follow-up.`)
          }
        }
        if (sourceMode === "process_verification") {
          if (!sourceTicketId) throw new Error("process_verification ticket creation requires source_ticket_id.")
          if (typeof output.args.evidence_artifact_path !== "string" || !output.args.evidence_artifact_path.trim()) {
            throw new Error("process_verification ticket creation requires evidence_artifact_path.")
          }
          const sourceTicket = getTicket(manifest, sourceTicketId)
          if (sourceTicket.status !== "done" && sourceTicket.resolution_state !== "done" && sourceTicket.resolution_state !== "superseded") {
            throw new Error(`Source ticket ${sourceTicket.id} must already be complete before process-verification follow-up can be created.`)
          }
        }
      }

      if (input.tool === "ticket_reopen") {
        const manifest = await loadManifest()
        const ticketId = typeof output.args.ticket_id === "string" ? output.args.ticket_id : manifest.active_ticket
        await ensureTargetTicketWriteLease(ticketId)
        const ticket = getTicket(manifest, ticketId)
        if (ticket.status !== "done" && ticket.resolution_state !== "done") {
          throw new Error(`Ticket ${ticket.id} must already be done before ticket_reopen can resume it.`)
        }
        if (typeof output.args.evidence_artifact_path !== "string" || !output.args.evidence_artifact_path.trim()) {
          throw new Error("ticket_reopen requires evidence_artifact_path.")
        }
      }

      if (input.tool === "issue_intake") {
        const manifest = await loadManifest()
        const sourceTicketId = typeof output.args.source_ticket_id === "string" ? output.args.source_ticket_id : ""
        if (!sourceTicketId) {
          throw new Error("issue_intake requires source_ticket_id.")
        }
        if (typeof output.args.evidence_artifact_path !== "string" || !output.args.evidence_artifact_path.trim()) {
          throw new Error("issue_intake requires evidence_artifact_path.")
        }
        const sourceTicket = getTicket(manifest, sourceTicketId)
        if (sourceTicket.status !== "done" && sourceTicket.resolution_state !== "done" && sourceTicket.resolution_state !== "superseded") {
          throw new Error(`issue_intake can only route issues from a completed source ticket. ${sourceTicket.id} is not complete.`)
        }
      }

      if (input.tool === "ticket_reconcile") {
        const manifest = await loadManifest()
        const sourceTicketId = typeof output.args.source_ticket_id === "string" ? output.args.source_ticket_id : ""
        const targetTicketId = typeof output.args.target_ticket_id === "string" ? output.args.target_ticket_id : ""
        const replacementSourceTicketId = typeof output.args.replacement_source_ticket_id === "string" ? output.args.replacement_source_ticket_id : ""
        if (!sourceTicketId || !targetTicketId) {
          throw new Error("ticket_reconcile requires source_ticket_id and target_ticket_id.")
        }
        if (typeof output.args.evidence_artifact_path !== "string" || !output.args.evidence_artifact_path.trim()) {
          throw new Error("ticket_reconcile requires evidence_artifact_path.")
        }
        const sourceTicket = getTicket(manifest, sourceTicketId)
        const targetTicket = getTicket(manifest, targetTicketId)
        const replacementSourceTicket = replacementSourceTicketId ? getTicket(manifest, replacementSourceTicketId) : sourceTicket
        if (["open", "reopened"].includes(sourceTicket.resolution_state) && sourceTicket.status !== "done") {
          await ensureTargetTicketWriteLease(sourceTicket.id)
        }
        if (["open", "reopened"].includes(targetTicket.resolution_state) && targetTicket.status !== "done") {
          await ensureTargetTicketWriteLease(targetTicket.id)
        }
        if (
          replacementSourceTicket.id !== sourceTicket.id &&
          ["open", "reopened"].includes(replacementSourceTicket.resolution_state) &&
          replacementSourceTicket.status !== "done"
        ) {
          await ensureTargetTicketWriteLease(replacementSourceTicket.id)
        }
      }

      if (input.tool === "ticket_reverify") {
        const manifest = await loadManifest()
        const ticketId = typeof output.args.ticket_id === "string" ? output.args.ticket_id : manifest.active_ticket
        const ticket = getTicket(manifest, ticketId)
        if (ticket.status !== "done") {
          throw new Error(`Ticket ${ticket.id} must already be done before ticket_reverify can restore trust.`)
        }
        const hasEvidenceArtifactPath = typeof output.args.evidence_artifact_path === "string" && output.args.evidence_artifact_path.trim()
        const hasVerificationContent = typeof output.args.verification_content === "string" && output.args.verification_content.trim()
        if (!hasEvidenceArtifactPath && !hasVerificationContent) {
          throw new Error("ticket_reverify requires evidence_artifact_path or verification_content.")
        }
      }

      if (input.tool === "artifact_register") {
        const manifest = await loadManifest()
        const ticketId = typeof output.args.ticket_id === "string" ? output.args.ticket_id : manifest.active_ticket
        const ticket = getTicket(manifest, ticketId)
        const stage = typeof output.args.stage === "string" ? output.args.stage : ""
        const historicalVerificationMutation = isHistoricalVerificationArtifactMutation(ticket, stage, output.args.kind)
        if (RESERVED_ARTIFACT_STAGES.has(stage)) {
          const owner = stage === "smoke-test" ? "smoke_test" : "handoff_publish"
          throw new Error(`Use ${owner} to create ${stage} artifacts. Generic artifact_register is not allowed for that stage.`)
        }

        if (!historicalVerificationMutation) {
          await ensureTargetTicketWriteLease(ticketId)
        }
        if (LEASED_ARTIFACT_STAGES.has(stage) && !historicalVerificationMutation) {
          const artifactPath = typeof output.args.path === "string" ? output.args.path : ""
          await ensureWriteLease(artifactPath || undefined)
        }
        if (stage === "smoke-test" || stage === "handoff") {
          await ensureBootstrapReadyForValidation()
        }
        if (ticket.verification_state === "invalidated" && stage === "handoff") {
          throw new Error(`Ticket ${ticket.id} is invalidated and cannot publish handoff artifacts until it is reverified.`)
        }
      }

      if (input.tool === "artifact_write") {
        const manifest = await loadManifest()
        const ticketId = typeof output.args.ticket_id === "string" ? output.args.ticket_id : manifest.active_ticket
        const ticket = getTicket(manifest, ticketId)
        const stage = typeof output.args.stage === "string" ? output.args.stage : ""
        const artifactPath = typeof output.args.path === "string" ? output.args.path : ""
        const historicalVerificationMutation = isHistoricalVerificationArtifactMutation(ticket, stage, output.args.kind)
        if (RESERVED_ARTIFACT_STAGES.has(stage)) {
          const owner = stage === "smoke-test" ? "smoke_test" : "handoff_publish"
          throw new Error(`Use ${owner} to create ${stage} artifacts. Generic artifact_write is not allowed for that stage.`)
        }
        if (!historicalVerificationMutation) {
          await ensureTargetTicketWriteLease(ticketId)
        }
        if (artifactPath && !historicalVerificationMutation) {
          await ensureWriteLease(artifactPath)
        }
      }

      if (input.tool === "ticket_update") {
        const manifest = await loadManifest()
        const ticketId = typeof output.args.ticket_id === "string" ? output.args.ticket_id : manifest.active_ticket
        const processVerificationClearOnly = isWorkflowProcessVerificationClearOnly(output.args)
        const processVerification = getProcessVerificationState(manifest, workflow, ticketId)
        if (!(processVerificationClearOnly && processVerification.clearable_now)) {
          await ensureTargetTicketWriteLease(ticketId)
        }
        const ticket = getTicket(manifest, ticketId)
        const requested = resolveRequestedTicketProgress(ticket, {
          stage: typeof output.args.stage === "string" ? output.args.stage : undefined,
          status: typeof output.args.status === "string" ? output.args.status : undefined,
        })
        const lifecycleBlocker = validateLifecycleStageStatus(requested.stage, requested.status)
        if (lifecycleBlocker) {
          throwWorkflowBlocker({
            type: "BLOCKER",
            reason_code: "invalid_lifecycle_transition",
            explanation: lifecycleBlocker,
            next_action_tool: "ticket_lookup",
            next_action_args: { ticket_id: ticketId },
          })
        }
        const approving = typeof output.args.approved_plan === "boolean" ? output.args.approved_plan : undefined

        if (approving && !hasArtifact(ticket, { stage: "planning" })) {
          throw new Error("Planning artifact required before marking the workflow as approved.")
        }

        if (requested.stage === "implementation" && approving === true && !isPlanApprovedForTicket(workflow, ticket.id)) {
          throw new Error(`Approve ${ticket.id} while it remains in plan_review first, then move it to implementation in a separate ticket_update call.`)
        }

        if (requested.stage === "implementation" && !isPlanApprovedForTicket(workflow, ticket.id)) {
          throw new Error(`Approved plan required before moving ${ticket.id} to in_progress.`)
        }

        if (requested.stage === "implementation" && ticket.stage !== "plan_review") {
          throw new Error(`Cannot move ${ticket.id} to implementation before it passes through plan_review.`)
        }

        if (requested.stage === "review") {
          const implementationBlocker = await validateImplementationArtifactEvidence(ticket)
          if (implementationBlocker) throw new Error(implementationBlocker)
        }

        if (requested.stage === "qa" && !hasReviewArtifact(ticket)) {
          throw new Error("Cannot move to qa before at least one review artifact exists.")
        }

        if (requested.stage === "smoke-test") {
          const qaBlocker = await validateQaArtifactEvidence(ticket)
          if (qaBlocker) throw new Error(qaBlocker)
          await ensureBootstrapReadyForValidation()
        }

        if (requested.stage === "closeout") {
          const smokeTestBlocker = await validateSmokeTestArtifactEvidence(ticket)
          if (smokeTestBlocker) throw new Error(smokeTestBlocker)
          await ensureBootstrapReadyForValidation()
        }

        if (getTicketWorkflowState(workflow, ticket.id).needs_reverification && requested.status === "done" && ticket.resolution_state !== "reopened") {
          throw new Error(`Ticket ${ticket.id} still needs reverification and cannot be closed from a non-reopened state.`)
        }
      }

      if (input.tool === "handoff_publish") {
        const manifest = await loadManifest()
        await ensureBootstrapReadyForValidation()
        const activeTicket = getTicket(manifest, workflow.active_ticket)
        if (activeTicket.resolution_state === "reopened") {
          throw new Error(`Cannot publish handoff while the foreground ticket ${activeTicket.id} is reopened.`)
        }
        const invalidatedDoneTickets = manifest.tickets.filter((ticket) => ticket.status === "done" && ticket.verification_state === "invalidated")
        if (invalidatedDoneTickets.length > 0) {
          throw new Error(`Cannot publish handoff while done tickets remain invalidated: ${invalidatedDoneTickets.map((ticket) => ticket.id).join(", ")}.`)
        }
        const blockingReverification = manifest.tickets.filter(
          (ticket) =>
            getTicketWorkflowState(workflow, ticket.id).needs_reverification &&
            (ticket.id === workflow.active_ticket || ticket.status !== "done" || ticket.resolution_state === "reopened"),
        )
        if (blockingReverification.length > 0) {
          throw new Error(`Cannot publish handoff while active or reopened tickets still need reverification: ${blockingReverification.map((ticket) => ticket.id).join(", ")}.`)
        }
      }
    },
  }
}
