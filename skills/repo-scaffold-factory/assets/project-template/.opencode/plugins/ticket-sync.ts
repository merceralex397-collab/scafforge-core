import { type Plugin } from "@opencode-ai/plugin"
import { writeJson } from "../lib/workflow"

const SYNCED_TOOLS = new Set([
  "ticket_update",
  "artifact_write",
  "artifact_register",
  "context_snapshot",
  "handoff_publish",
  "smoke_test",
])

export const TicketSync: Plugin = async () => {
  return {
    "tool.execute.after": async (input) => {
      if (!SYNCED_TOOLS.has(input.tool)) {
        return
      }
      try {
        await writeJson(".opencode/state/last-ticket-event.json", {
          tool: input.tool,
          args: input.args,
          timestamp: new Date().toISOString(),
        })
      } catch (error) {
        console.warn(`TicketSync disabled its persistence write: ${String(error)}`)
      }
    },
  }
}
