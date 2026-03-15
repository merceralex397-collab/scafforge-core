import { tool } from "@opencode-ai/plugin"
import {
  mergeStartHere,
  latestHandoffPath,
  loadManifest,
  loadWorkflowState,
  renderStartHere,
  startHerePath,
  writeText,
} from "./_workflow"
import { readFile } from "node:fs/promises"

export default tool({
  description: "Publish the top-level START-HERE handoff and the latest handoff copy in .opencode/state.",
  args: {
    next_action: tool.schema.string().describe("Optional explicit next action.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const content = renderStartHere(manifest, workflow, args.next_action)

    const startHere = startHerePath()
    const handoffCopy = latestHandoffPath()
    const existingStartHere = await readFile(startHere, "utf-8").catch(() => "")
    const mergeResult = mergeStartHere(existingStartHere, content)
    await writeText(startHere, mergeResult.content)
    await writeText(handoffCopy, content)

    return JSON.stringify(
      {
        start_here: startHere,
        latest_handoff: handoffCopy,
        merged: mergeResult.merged,
        warning: mergeResult.merged
          ? undefined
          : "START-HERE.md does not contain the Scafforge-managed block, so only .opencode/state/latest-handoff.md was refreshed.",
      },
      null,
      2,
    )
  },
})
