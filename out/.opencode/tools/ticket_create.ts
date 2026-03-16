import { tool } from "@opencode-ai/plugin"
import {
  getTicket,
  loadManifest,
  loadWorkflowState,
  renderTicketDocument,
  saveManifest,
  saveWorkflowState,
  ticketFilePath,
  writeText,
} from "./_workflow"

export default tool({
  description: "Create a guarded follow-up ticket from a verified backlog-verifier finding during a process-verification window.",
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
    source_ticket_id: tool.schema.string().describe("Done ticket that produced the verification finding."),
    verification_artifact_path: tool.schema.string().describe("Canonical backlog-verification artifact path from the verifier."),
    activate: tool.schema.boolean().describe("Whether to make the new ticket active immediately.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()

    if (!workflow.pending_process_verification) {
      throw new Error("Guarded ticket creation is only available while post-migration verification is pending.")
    }

    if (manifest.tickets.some((ticket) => ticket.id === args.id)) {
      throw new Error(`Ticket already exists: ${args.id}`)
    }

    for (const dependency of args.depends_on || []) {
      getTicket(manifest, dependency)
    }

    const sourceTicket = getTicket(manifest, args.source_ticket_id)
    const verificationArtifact = sourceTicket.artifacts.find(
      (artifact) =>
        artifact.path === args.verification_artifact_path &&
        artifact.stage === "review" &&
        artifact.kind === "backlog-verification",
    )
    if (!verificationArtifact) {
      throw new Error("A registered backlog-verification artifact is required before creating a follow-up ticket.")
    }

    const ticket = {
      id: args.id,
      title: args.title,
      lane: args.lane,
      wave: args.wave,
      parallel_safe: args.parallel_safe ?? false,
      overlap_risk: args.overlap_risk ?? "medium",
      stage: "planning",
      status: (args.decision_blockers?.length || 0) > 0 ? "blocked" : "todo",
      depends_on: args.depends_on || [],
      summary: args.summary,
      acceptance: args.acceptance,
      decision_blockers: args.decision_blockers || [],
      artifacts: [],
    }

    manifest.tickets.push(ticket)
    if (args.activate) {
      manifest.active_ticket = ticket.id
      workflow.active_ticket = ticket.id
      workflow.stage = ticket.stage
      workflow.status = ticket.status
      workflow.approved_plan = false
      await saveWorkflowState(workflow)
    }

    await saveManifest(manifest)
    const path = ticketFilePath(ticket.id)
    await writeText(path, renderTicketDocument(ticket))

    return JSON.stringify(
      {
        created_ticket: ticket.id,
        path,
        source_ticket_id: sourceTicket.id,
        verification_artifact_path: verificationArtifact.path,
        activated: Boolean(args.activate),
      },
      null,
      2,
    )
  },
})
