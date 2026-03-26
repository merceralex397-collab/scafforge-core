import { tool } from "@opencode-ai/plugin"
import {
  bootstrapProvenancePath,
  refreshRestartSurfaces,
  latestHandoffPath,
  loadManifest,
  loadWorkflowState,
  readJson,
  renderStartHere,
  startHerePath,
  validateHandoffNextAction,
  writeText,
} from "./_workflow"

export default tool({
  description: "Publish the top-level START-HERE handoff and the latest handoff copy in .opencode/state.",
  args: {
    next_action: tool.schema.string().describe("Optional explicit next action.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
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
    const content = renderStartHere(manifest, workflow, {
      nextAction: args.next_action,
      backlogVerifierAgent: typeof backlogVerifierAgent === "string" ? backlogVerifierAgent : undefined,
    })

    const handoffCopy = latestHandoffPath()
    await writeText(handoffCopy, content)
    await refreshRestartSurfaces({ manifest, workflow, nextAction: args.next_action })

    return JSON.stringify({ start_here: startHerePath(), latest_handoff: handoffCopy }, null, 2)
  },
})
