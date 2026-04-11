import { tool } from "@opencode-ai/plugin"
import {
  allowsPreBootstrapWriteClaim,
  claimLaneLease,
  ensureRequiredFile,
  getTicket,
  getTicketWorkflowState,
  loadManifest,
  loadWorkflowState,
  requireBootstrapReady,
  rootPath,
  saveWorkflowState,
  ticketsManifestPath,
  workflowStatePath,
} from "../lib/workflow"

export default tool({
  description: "Claim a ticket lane lease before write-capable work begins.",
  args: {
    ticket_id: tool.schema.string().describe("Ticket id to claim."),
    owner_agent: tool.schema.string().describe("Agent name or role that will own the lease."),
    allowed_paths: tool.schema.array(tool.schema.string()).describe("Repo-relative path prefixes or glob patterns this lease may edit.").optional(),
    write_lock: tool.schema.boolean().describe("Whether this lease authorizes file edits. Defaults to true.").optional(),
  },
  async execute(args) {
    await ensureRequiredFile(ticketsManifestPath(rootPath()), "tickets/manifest.json")
    await ensureRequiredFile(workflowStatePath(rootPath()), ".opencode/state/workflow-state.json")
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const ticket = getTicket(manifest, args.ticket_id)
    const ownerAgent = args.owner_agent.trim()
    const writeLock = args.write_lock !== false

    if (!ownerAgent) {
      throw new Error("owner_agent must not be empty.")
    }
    if (ticket.decision_blockers.length > 0 && ticket.status === "blocked") {
      throw new Error(`Ticket ${ticket.id} is blocked and cannot be claimed until its decision blockers are resolved.`)
    }
    if (ticket.status === "done" || ticket.resolution_state === "superseded") {
      throw new Error(`Ticket ${ticket.id} cannot be claimed because it is already closed.`)
    }
    for (const dependency of ticket.depends_on) {
      const dependencyTicket = getTicket(manifest, dependency)
      if (dependencyTicket.status !== "done") {
        throw new Error(`Ticket ${ticket.id} cannot be claimed before dependency ${dependencyTicket.id} is done.`)
      }
      if (dependencyTicket.verification_state === "invalidated" || getTicketWorkflowState(workflow, dependencyTicket.id).needs_reverification) {
        throw new Error(`Ticket ${ticket.id} cannot be claimed because dependency ${dependencyTicket.id} is no longer trusted.`)
      }
    }
    if (writeLock && !allowsPreBootstrapWriteClaim(workflow, ticket)) {
      await requireBootstrapReady(workflow, rootPath())
    }

    const lease = claimLaneLease(workflow, ticket, ownerAgent, args.allowed_paths || [], writeLock)
    await saveWorkflowState(workflow, undefined, undefined, {}, { skipGraphValidation: true })

    return JSON.stringify(
      {
        claimed: true,
        lease,
        active_leases: workflow.lane_leases,
      },
      null,
      2,
    )
  },
})
