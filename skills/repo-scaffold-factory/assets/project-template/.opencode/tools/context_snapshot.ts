import { tool } from "@opencode-ai/plugin"
import { createHash } from "node:crypto"
import { readFile } from "node:fs/promises"
import {
  contextSnapshotPath,
  getTicket,
  isPlanApprovedForTicket,
  loadManifest,
  loadPivotState,
  loadWorkflowState,
  renderContextSnapshot,
  writeText,
} from "../lib/workflow"

export default tool({
  description: "Write a concise context snapshot for the active or requested ticket.",
  args: {
    ticket_id: tool.schema.string().describe("Optional ticket id. Defaults to the active ticket.").optional(),
    note: tool.schema.string().describe("Optional note to append to the snapshot.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const pivot = await loadPivotState()
    const ticket = getTicket(manifest, args.ticket_id)

    // Use a copy for snapshot rendering to avoid mutating shared state
    const snapshotState = args.ticket_id
      ? { ...workflow, active_ticket: ticket.id, stage: ticket.stage, status: ticket.status, approved_plan: isPlanApprovedForTicket(workflow, ticket.id) }
      : workflow

    const content = renderContextSnapshot(manifest, snapshotState, pivot, args.note)
    const path = contextSnapshotPath()
    await writeText(path, content)
    const actualContent = await readFile(path, "utf-8")
    const snapshotSizeBytes = Buffer.byteLength(actualContent, "utf8")

    return JSON.stringify(
      {
        path,
        ticket_id: ticket.id,
        active_ticket: snapshotState.active_ticket,
        verified: actualContent === content,
        snapshot_size_bytes: snapshotSizeBytes,
        snapshot_sha256: createHash("sha256").update(actualContent).digest("hex"),
      },
      null,
      2,
    )
  },
})
