import { tool } from "@opencode-ai/plugin"
import {
  COARSE_STATUSES,
  getTicket,
  hasArtifact,
  hasReviewArtifact,
  loadManifest,
  loadWorkflowState,
  saveManifest,
  saveWorkflowState,
  ticketsNeedingProcessVerification,
} from "./_workflow"

export default tool({
  description: "Update ticket stage, status, summary, and active ticket state.",
  args: {
    ticket_id: tool.schema.string().describe("Ticket id to update."),
    stage: tool.schema.string().describe("Optional new stage value.").optional(),
    status: tool.schema.string().describe("Optional new status value.").optional(),
    summary: tool.schema.string().describe("Optional replacement summary.").optional(),
    activate: tool.schema.boolean().describe("Whether to set this ticket as the active ticket.").optional(),
    approved_plan: tool.schema.boolean().describe("Whether the workflow now has an approved plan.").optional(),
    pending_process_verification: tool.schema.boolean().describe("Whether post-migration backlog verification is still pending.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const ticket = getTicket(manifest, args.ticket_id)

    if (args.status && !COARSE_STATUSES.has(args.status)) {
      throw new Error(`Unsupported ticket status: ${args.status}`)
    }

    if (typeof args.approved_plan === "boolean" && args.approved_plan && !hasArtifact(ticket, { stage: "planning" })) {
      throw new Error("Cannot approve a plan before a planning artifact exists.")
    }

    if (args.status === "in_progress" && !workflow.approved_plan && args.approved_plan !== true) {
      throw new Error("Cannot move to in_progress before the workflow has an approved plan.")
    }

    if (args.status === "review" && !hasArtifact(ticket, { stage: "implementation" })) {
      throw new Error("Cannot move to review before an implementation artifact exists.")
    }

    if (args.status === "qa" && !hasReviewArtifact(ticket)) {
      throw new Error("Cannot move to qa before at least one review artifact exists.")
    }

    if (args.status === "done" && !hasArtifact(ticket, { stage: "qa" })) {
      throw new Error("Cannot move to done before a QA artifact exists.")
    }

    if (args.stage) ticket.stage = args.stage
    if (args.status) ticket.status = args.status
    if (args.summary) ticket.summary = args.summary
    const switchingActiveTicket = Boolean(args.activate) && manifest.active_ticket !== ticket.id
    if (args.activate) manifest.active_ticket = ticket.id

    const activeTicket = getTicket(manifest, manifest.active_ticket)
    workflow.active_ticket = activeTicket.id
    workflow.stage = activeTicket.stage
    workflow.status = activeTicket.status
    if (typeof args.approved_plan === "boolean") {
      if (activeTicket.id === ticket.id) {
        workflow.approved_plan = args.approved_plan
      }
    } else if (switchingActiveTicket) {
      workflow.approved_plan = false
    }
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

    await saveManifest(manifest)
    await saveWorkflowState(workflow)

    return JSON.stringify(
      {
        updated_ticket: ticket,
        active_ticket: manifest.active_ticket,
        workflow,
      },
      null,
      2,
    )
  },
})
