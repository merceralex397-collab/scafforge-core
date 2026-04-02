import { tool } from "@opencode-ai/plugin"
import {
  bootstrapProvenancePath,
  refreshRestartSurfaces,
  latestHandoffPath,
  loadManifest,
  loadPivotState,
  loadWorkflowState,
  readJson,
  startHerePath,
  validateHandoffNextAction,
} from "../lib/workflow"

export default tool({
  description: "Publish the top-level START-HERE handoff and the latest handoff copy in .opencode/state.",
  args: {
    next_action: tool.schema.string().describe("Optional explicit next action.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const pivot = await loadPivotState()
    const provenance = await readJson<{
      workflow_contract?: {
        post_migration_verification?: {
          backlog_verifier_agent?: string
        }
      }
    }>(bootstrapProvenancePath(), {})
    const backlogVerifierAgent = provenance.workflow_contract?.post_migration_verification?.backlog_verifier_agent
    if (typeof args.next_action === "string") {
      const handoffBlocker = await validateHandoffNextAction(manifest, workflow, args.next_action)
      if (handoffBlocker) {
        throw new Error(handoffBlocker)
      }
    }
    await refreshRestartSurfaces({ manifest, workflow, pivot, nextAction: args.next_action })

    return JSON.stringify({ start_here: startHerePath(), latest_handoff: latestHandoffPath() }, null, 2)
  },
})
