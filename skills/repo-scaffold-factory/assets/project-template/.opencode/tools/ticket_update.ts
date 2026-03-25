import { tool } from "@opencode-ai/plugin"
import {
  describeAllowedStatusesForStage,
  getTicket,
  hasArtifact,
  hasReviewArtifact,
  isPlanApprovedForTicket,
  loadManifest,
  loadWorkflowState,
  markTicketDone,
  resolveRequestedTicketProgress,
  saveWorkflowBundle,
  setPlanApprovedForTicket,
  syncWorkflowSelection,
  ticketsNeedingProcessVerification,
  validateLifecycleStageStatus,
  validateImplementationArtifactEvidence,
  validateQaArtifactEvidence,
  validateSmokeTestArtifactEvidence,
} from "./_workflow"

export default tool({
  description: "Update ticket stage, status, summary, and active ticket state.",
  args: {
    ticket_id: tool.schema.string().describe("Ticket id to update."),
    stage: tool.schema.string().describe("Optional new stage value.").optional(),
    status: tool.schema.string().describe("Optional new status value.").optional(),
    summary: tool.schema.string().describe("Optional replacement summary.").optional(),
    activate: tool.schema.boolean().describe("Whether to set this ticket as the active ticket.").optional(),
    approved_plan: tool.schema.boolean().describe("Whether this ticket's plan is approved in workflow-state.").optional(),
    pending_process_verification: tool.schema.boolean().describe("Whether post-migration backlog verification is still pending.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const ticket = getTicket(manifest, args.ticket_id)
    const wasDone = ticket.status === "done"
    const requested = resolveRequestedTicketProgress(ticket, { stage: args.stage, status: args.status })
    const targetStage = requested.stage
    const targetStatus = requested.status

    const lifecycleBlocker = validateLifecycleStageStatus(targetStage, targetStatus)
    if (lifecycleBlocker) {
      throw new Error(lifecycleBlocker)
    }

    if (wasDone && targetStatus !== "done") {
      throw new Error(`Ticket ${ticket.id} is already done. Use ticket_reopen to resume ownership instead of mutating status directly.`)
    }

    if (typeof args.approved_plan === "boolean" && args.approved_plan && !hasArtifact(ticket, { stage: "planning" })) {
      throw new Error("Cannot approve a plan before a planning artifact exists.")
    }

    if (targetStage === "plan_review") {
      if (!hasArtifact(ticket, { stage: "planning" })) {
        throw new Error("Cannot move to plan_review before a planning artifact exists.")
      }
    }

    if (targetStage === "implementation" && args.approved_plan === true && !isPlanApprovedForTicket(workflow, ticket.id)) {
      throw new Error(`Approve ${ticket.id} while it remains in plan_review first, then move it to implementation in a separate ticket_update call.`)
    }

    if (targetStage === "implementation" && !isPlanApprovedForTicket(workflow, ticket.id)) {
      throw new Error(`Cannot move ${ticket.id} to implementation before its plan is approved in workflow-state.`)
    }

    if (targetStage === "implementation" && ticket.stage !== "plan_review") {
      throw new Error(`Cannot move ${ticket.id} to implementation before it passes through plan_review.`)
    }

    if (targetStage === "review") {
      const implementationBlocker = await validateImplementationArtifactEvidence(ticket)
      if (implementationBlocker) {
        throw new Error(implementationBlocker)
      }
    }

    if (targetStage === "qa" && !hasReviewArtifact(ticket)) {
      throw new Error("Cannot move to qa before at least one review artifact exists.")
    }

    if (targetStage === "smoke-test") {
      const qaBlocker = await validateQaArtifactEvidence(ticket)
      if (qaBlocker) {
        throw new Error(qaBlocker)
      }
    }

    if (targetStage === "closeout") {
      const smokeTestBlocker = await validateSmokeTestArtifactEvidence(ticket)
      if (smokeTestBlocker) {
        throw new Error(smokeTestBlocker)
      }
    }

    ticket.stage = targetStage
    if (targetStatus === "done") {
      markTicketDone(ticket, workflow)
    } else {
      ticket.status = targetStatus
    }
    if (args.summary) ticket.summary = args.summary
    if (args.activate) manifest.active_ticket = ticket.id

    if (typeof args.approved_plan === "boolean") {
      setPlanApprovedForTicket(workflow, ticket.id, args.approved_plan)
    }
    syncWorkflowSelection(workflow, manifest)
    if (typeof args.pending_process_verification === "boolean") {
      if (args.pending_process_verification === false) {
        // Intentionally inspect post-mutation state so the clear operation validates the repo exactly as it would be persisted.
        const unverified = ticketsNeedingProcessVerification(manifest, workflow)
        if (unverified.length > 0) {
          throw new Error(
            `Cannot clear pending_process_verification: ${unverified.length} done ticket(s) still require backlog verification (${unverified.map((t) => t.id).join(", ")}). Run the backlog-verifier flow for the listed tickets, register review/backlog-verification artifacts where needed, then retry.`,
          )
        }
      }
      workflow.pending_process_verification = args.pending_process_verification
    }

    await saveWorkflowBundle({ workflow, manifest })

    return JSON.stringify(
      {
        updated_ticket: ticket,
        transition: {
          stage: targetStage,
          status: targetStatus,
          allowed_statuses_for_stage: describeAllowedStatusesForStage(targetStage),
        },
        active_ticket: manifest.active_ticket,
        workflow,
      },
      null,
      2,
    )
  },
})
