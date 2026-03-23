import { tool } from "@opencode-ai/plugin"
import {
  createTicketRecord,
  getTicket,
  loadManifest,
  loadWorkflowState,
  saveWorkflowBundle,
  setPlanApprovedForTicket,
  syncWorkflowSelection,
  ticketFilePath,
  type TicketSourceMode,
} from "./_workflow"

function normalizeOptional(value: string | undefined): string | undefined {
  if (typeof value !== "string") return undefined
  const normalized = value.trim()
  return normalized || undefined
}

export default tool({
  description: "Create a new ticket or linked follow-up ticket, including post-completion issue remediation tickets.",
  args: {
    id: tool.schema.string().describe("New ticket id."),
    title: tool.schema.string().describe("New ticket title."),
    lane: tool.schema.string().describe("Owning lane or project area."),
    wave: tool.schema.number().int().describe("Execution wave number."),
    summary: tool.schema.string().describe("Ticket summary."),
    acceptance: tool.schema.array(tool.schema.string()).describe("Acceptance criteria list."),
    depends_on: tool.schema.array(tool.schema.string()).describe("Dependency ticket ids.").optional(),
    decision_blockers: tool.schema.array(tool.schema.string()).describe("Unresolved blockers for this ticket.").optional(),
    parallel_safe: tool.schema.boolean().describe("Whether the ticket can be advanced in a parallel lane when dependencies are satisfied.").optional(),
    overlap_risk: tool.schema.enum(["low", "medium", "high"]).describe("Expected overlap risk with other tickets.").optional(),
    source_ticket_id: tool.schema.string().describe("Optional source ticket that this ticket extends or remediates.").optional(),
    source_mode: tool.schema.enum(["process_verification", "post_completion_issue", "net_new_scope"]).describe("Why this ticket is being created.").optional(),
    evidence_artifact_path: tool.schema.string().describe("Optional registered artifact path that justifies creation of this linked ticket.").optional(),
    activate: tool.schema.boolean().describe("Whether to make the new ticket active immediately.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const sourceMode: TicketSourceMode = args.source_mode || "net_new_scope"
    const sourceTicketId = normalizeOptional(args.source_ticket_id)
    const evidenceArtifactPath = normalizeOptional(args.evidence_artifact_path)

    if (manifest.tickets.some((ticket) => ticket.id === args.id.trim())) {
      throw new Error(`Ticket already exists: ${args.id.trim()}`)
    }

    const ticket = createTicketRecord({
      id: args.id,
      title: args.title,
      lane: args.lane,
      wave: args.wave,
      summary: args.summary,
      acceptance: args.acceptance,
      depends_on: args.depends_on,
      decision_blockers: args.decision_blockers,
      parallel_safe: args.parallel_safe,
      overlap_risk: args.overlap_risk,
      source_ticket_id: sourceTicketId,
      source_mode: sourceMode,
    })

    for (const dependency of ticket.depends_on) {
      getTicket(manifest, dependency)
    }

    let sourceTicket = undefined as ReturnType<typeof getTicket> | undefined
    if (sourceMode !== "net_new_scope") {
      if (!sourceTicketId) {
        throw new Error(`source_ticket_id is required when source_mode is ${sourceMode}.`)
      }
      sourceTicket = getTicket(manifest, sourceTicketId)

      if (sourceMode === "process_verification") {
        if (!workflow.pending_process_verification) {
          throw new Error("process_verification ticket creation is only available while pending_process_verification is true.")
        }
        if (sourceTicket.status !== "done") {
          throw new Error(`Source ticket ${sourceTicket.id} must be done before creating a process-verification follow-up ticket.`)
        }
        if (!evidenceArtifactPath) {
          throw new Error("evidence_artifact_path is required for process_verification ticket creation.")
        }
        const verificationArtifact = sourceTicket.artifacts.find(
          (artifact) =>
            artifact.path === evidenceArtifactPath &&
            artifact.stage === "review" &&
            artifact.kind === "backlog-verification" &&
            artifact.trust_state === "current",
        )
        if (!verificationArtifact) {
          throw new Error(
            `Source ticket ${sourceTicket.id} does not have a current review/backlog-verification artifact at ${evidenceArtifactPath}.`,
          )
        }
      }

      if (sourceMode === "post_completion_issue") {
        if (!["done", "reopened", "superseded"].includes(sourceTicket.resolution_state)) {
          throw new Error(`Source ticket ${sourceTicket.id} must already represent completed historical scope before creating a post-completion issue ticket.`)
        }
        if (!evidenceArtifactPath) {
          throw new Error("evidence_artifact_path is required for post_completion_issue ticket creation.")
        }
        const evidenceArtifact = sourceTicket.artifacts.find((artifact) => artifact.path === evidenceArtifactPath)
        if (!evidenceArtifact) {
          throw new Error(`Source ticket ${sourceTicket.id} does not reference the evidence artifact ${evidenceArtifactPath}.`)
        }
      }
    }

    manifest.tickets.push(ticket)
    if (sourceTicket && !sourceTicket.follow_up_ticket_ids.includes(ticket.id)) {
      sourceTicket.follow_up_ticket_ids.push(ticket.id)
    }

    setPlanApprovedForTicket(workflow, ticket.id, false)
    if (args.activate) {
      manifest.active_ticket = ticket.id
    }
    syncWorkflowSelection(workflow, manifest)

    await saveWorkflowBundle({ workflow, manifest })

    return JSON.stringify(
      {
        created_ticket: ticket.id,
        path: ticketFilePath(ticket.id),
        status: ticket.status,
        source_ticket_id: sourceTicket?.id || null,
        source_mode: sourceMode,
        evidence_artifact_path: evidenceArtifactPath || null,
        activated: Boolean(args.activate),
      },
      null,
      2,
    )
  },
})
