import { tool } from "@opencode-ai/plugin"
import { loadWorkflowState, releaseLaneLease, saveWorkflowState } from "./_workflow"

export default tool({
  description: "Release an active lane lease after a worker finishes or yields ownership.",
  args: {
    ticket_id: tool.schema.string().describe("Ticket id whose lease should be released."),
    owner_agent: tool.schema.string().describe("Owner name that must match the active lease.").optional(),
  },
  async execute(args) {
    const workflow = await loadWorkflowState()
    const ownerAgent = typeof args.owner_agent === "string" ? args.owner_agent.trim() : undefined

    if (!ownerAgent) {
      throw new Error("owner_agent is required to release a lease.")
    }

    const released = releaseLaneLease(workflow, args.ticket_id, ownerAgent)

    if (!released) {
      throw new Error(`No matching active lease found for ${args.ticket_id}.`)
    }

    await saveWorkflowState(workflow)

    return JSON.stringify(
      {
        released,
        active_leases: workflow.lane_leases,
      },
      null,
      2,
    )
  },
})
