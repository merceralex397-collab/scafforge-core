import { tool } from "@opencode-ai/plugin"
import { loadWorkflowState, pruneExpiredLeases, saveWorkflowState } from "../lib/workflow"

export default tool({
  description: "Prune expired ticket lane leases so a new session can recover from stale ownership after crashes or abandoned runs.",
  args: {},
  async execute() {
    const workflow = await loadWorkflowState()
    const released = pruneExpiredLeases(workflow)
    if (released.length > 0) {
      await saveWorkflowState(workflow)
    }
    return JSON.stringify(
      {
        released_count: released.length,
        released_leases: released,
        active_leases: workflow.lane_leases,
      },
      null,
      2,
    )
  },
})
