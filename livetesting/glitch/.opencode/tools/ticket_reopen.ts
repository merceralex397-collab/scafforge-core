import { tool } from "@opencode-ai/plugin"
import {
  getTicket,
  loadManifest,
  loadWorkflowState,
  markTicketReopened,
  releaseLaneLease,
  saveWorkflowBundle,
  setPlanApprovedForTicket,
  syncWorkflowSelection,
  ticketFilePath,
} from "../lib/workflow"

export default tool({
  description: "Reopen a completed ticket when its original accepted scope is no longer true.",
  args: {
    ticket_id: tool.schema.string().describe("Ticket id to reopen."),
    reason: tool.schema.string().describe("Why the original completion can no longer be trusted."),
    evidence_artifact_path: tool.schema.string().describe("Registered artifact path that demonstrates the defect."),
    activate: tool.schema.boolean().describe("Whether to make the reopened ticket the active ticket.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const ticket = getTicket(manifest, args.ticket_id)
    const reason = args.reason.trim()
    const evidenceArtifactPath = args.evidence_artifact_path.trim()

    if (!reason) {
      throw new Error("reason must not be empty.")
    }

    if (ticket.resolution_state !== "done" && ticket.status !== "done") {
      throw new Error(`Ticket ${ticket.id} is not currently complete. Only completed tickets can be reopened.`)
    }

    const evidenceArtifact = ticket.artifacts.find((artifact) => artifact.path === evidenceArtifactPath)
    if (!evidenceArtifact) {
      throw new Error(`Ticket ${ticket.id} does not reference the evidence artifact ${evidenceArtifactPath}.`)
    }

    markTicketReopened(ticket, workflow, reason)
    releaseLaneLease(workflow, ticket.id)
    setPlanApprovedForTicket(workflow, ticket.id, false)

    if (args.activate !== false) {
      manifest.active_ticket = ticket.id
    }
    syncWorkflowSelection(workflow, manifest)

    await saveWorkflowBundle({ workflow, manifest })

    return JSON.stringify(
      {
        reopened_ticket: ticket.id,
        ticket_path: ticketFilePath(ticket.id),
        evidence_artifact_path: evidenceArtifactPath,
        reopen_count: workflow.ticket_state[ticket.id]?.reopen_count ?? 0,
        active_ticket: manifest.active_ticket,
      },
      null,
      2,
    )
  },
})
