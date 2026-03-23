import { type Plugin } from "@opencode-ai/plugin"
import {
  allowsPreBootstrapWriteClaim,
  getTicket,
  getTicketWorkflowState,
  hasArtifact,
  hasReviewArtifact,
  hasWriteLeaseForTicketPath,
  hasWriteLeaseForTicket,
  isPlanApprovedForTicket,
  loadManifest,
  loadWorkflowState,
  requireBootstrapReady,
  validateImplementationArtifactEvidence,
  validateQaArtifactEvidence,
  validateSmokeTestArtifactEvidence,
} from "../tools/_workflow"

const SAFE_BASH = /^(pwd|ls|find|rg|grep|cat|head|tail|git status|git diff|git log)\b/i
const LEASED_ARTIFACT_STAGES = new Set(["implementation", "bootstrap", "handoff"])

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

async function ensureBootstrapReadyForValidation() {
  const workflow = await loadWorkflowState()
  await requireBootstrapReady(workflow)
}

async function ensureWriteLease(pathValue?: string) {
  const workflow = await loadWorkflowState()
  if (!hasWriteLeaseForTicket(workflow, workflow.active_ticket)) {
    throw new Error(`Active ticket ${workflow.active_ticket} must hold an active write lease before write-capable work can proceed.`)
  }
  if (pathValue && !hasWriteLeaseForTicketPath(workflow, workflow.active_ticket, pathValue)) {
    throw new Error(`The active write lease for ${workflow.active_ticket} does not cover ${pathValue}. Claim a lease with the correct allowed_paths first.`)
  }
}

async function ensureTargetTicketWriteLease(ticketId: string) {
  const workflow = await loadWorkflowState()
  if (!hasWriteLeaseForTicket(workflow, ticketId)) {
    throw new Error(`Ticket ${ticketId} must hold an active write lease before this mutation can proceed.`)
  }
}

export const StageGateEnforcer: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      const workflow = await loadWorkflowState().catch(() => undefined)
      if (!workflow) return

      const activeApprovedPlan = isPlanApprovedForTicket(workflow, workflow.active_ticket)

      if (input.tool === "bash") {
        const command = typeof output.args.command === "string" ? output.args.command : ""
        if (!activeApprovedPlan && !SAFE_BASH.test(command)) {
          throw new Error("The active ticket needs an approved plan before running implementation-oriented shell commands.")
        }
        if (!SAFE_BASH.test(command)) {
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
        await ensureTargetTicketWriteLease(sourceTicketId || workflow.active_ticket)
        if (sourceMode === "post_completion_issue") {
          if (!sourceTicketId) throw new Error("post_completion_issue ticket creation requires source_ticket_id.")
          if (typeof output.args.evidence_artifact_path !== "string" || !output.args.evidence_artifact_path.trim()) {
            throw new Error("post_completion_issue ticket creation requires evidence_artifact_path.")
          }
          const sourceTicket = getTicket(manifest, sourceTicketId)
          if (sourceTicket.status !== "done" && sourceTicket.resolution_state !== "reopened" && sourceTicket.resolution_state !== "superseded") {
            throw new Error(`Source ticket ${sourceTicket.id} is not in a completed historical state suitable for post-completion issue follow-up.`)
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
        await ensureTargetTicketWriteLease(sourceTicketId)
        if (typeof output.args.evidence_artifact_path !== "string" || !output.args.evidence_artifact_path.trim()) {
          throw new Error("issue_intake requires evidence_artifact_path.")
        }
        const sourceTicket = getTicket(manifest, sourceTicketId)
        if (sourceTicket.status !== "done" && sourceTicket.resolution_state !== "done") {
          throw new Error(`issue_intake can only route issues from a completed source ticket. ${sourceTicket.id} is not complete.`)
        }
      }

      if (input.tool === "ticket_reverify") {
        const manifest = await loadManifest()
        const ticketId = typeof output.args.ticket_id === "string" ? output.args.ticket_id : manifest.active_ticket
        await ensureTargetTicketWriteLease(ticketId)
        if (typeof output.args.evidence_artifact_path !== "string" || !output.args.evidence_artifact_path.trim()) {
          throw new Error("ticket_reverify requires evidence_artifact_path.")
        }
      }

      if (input.tool === "artifact_register") {
        const manifest = await loadManifest()
        const ticketId = typeof output.args.ticket_id === "string" ? output.args.ticket_id : manifest.active_ticket
        const ticket = getTicket(manifest, ticketId)
        const stage = typeof output.args.stage === "string" ? output.args.stage : ""

        await ensureTargetTicketWriteLease(ticketId)
        if (LEASED_ARTIFACT_STAGES.has(stage)) {
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

      if (input.tool === "ticket_update") {
        const manifest = await loadManifest()
        const ticketId = typeof output.args.ticket_id === "string" ? output.args.ticket_id : manifest.active_ticket
        await ensureTargetTicketWriteLease(ticketId)
        const ticket = getTicket(manifest, ticketId)
        const nextStatus = typeof output.args.status === "string" ? output.args.status : ""
        const approving = typeof output.args.approved_plan === "boolean" ? output.args.approved_plan : undefined

        if (approving && !hasArtifact(ticket, { stage: "planning" })) {
          throw new Error("Planning artifact required before marking the workflow as approved.")
        }

        if (nextStatus === "in_progress" && !isPlanApprovedForTicket(workflow, ticket.id) && approving !== true) {
          throw new Error(`Approved plan required before moving ${ticket.id} to in_progress.`)
        }

        if (nextStatus === "review") {
          const implementationBlocker = await validateImplementationArtifactEvidence(ticket)
          if (implementationBlocker) throw new Error(implementationBlocker)
        }

        if (nextStatus === "qa" && !hasReviewArtifact(ticket)) {
          throw new Error("Cannot move to qa before at least one review artifact exists.")
        }

        if (nextStatus === "smoke_test") {
          const qaBlocker = await validateQaArtifactEvidence(ticket)
          if (qaBlocker) throw new Error(qaBlocker)
          await ensureBootstrapReadyForValidation()
        }

        if (nextStatus === "done") {
          const smokeTestBlocker = await validateSmokeTestArtifactEvidence(ticket)
          if (smokeTestBlocker) throw new Error(smokeTestBlocker)
          await ensureBootstrapReadyForValidation()
        }

        if (getTicketWorkflowState(workflow, ticket.id).needs_reverification && nextStatus === "done" && ticket.resolution_state !== "reopened") {
          throw new Error(`Ticket ${ticket.id} still needs reverification and cannot be closed from a non-reopened state.`)
        }
      }

      if (input.tool === "handoff_publish") {
        const manifest = await loadManifest()
        await ensureTargetTicketWriteLease(workflow.active_ticket)
        await ensureBootstrapReadyForValidation()
        const activeTicket = getTicket(manifest, workflow.active_ticket)
        if (activeTicket.resolution_state === "reopened") {
          throw new Error(`Cannot publish handoff while the foreground ticket ${activeTicket.id} is reopened.`)
        }
        const invalidatedDoneTickets = manifest.tickets.filter((ticket) => ticket.status === "done" && ticket.verification_state === "invalidated")
        if (invalidatedDoneTickets.length > 0) {
          throw new Error(`Cannot publish handoff while done tickets remain invalidated: ${invalidatedDoneTickets.map((ticket) => ticket.id).join(", ")}.`)
        }
        const pendingReverification = manifest.tickets.filter((ticket) => getTicketWorkflowState(workflow, ticket.id).needs_reverification)
        if (pendingReverification.length > 0) {
          throw new Error(`Cannot publish handoff while reverification is pending for: ${pendingReverification.map((ticket) => ticket.id).join(", ")}.`)
        }
      }
    },
  }
}
