import { tool } from "@opencode-ai/plugin"
import { canonicalizeRepoPath, currentStageArtifactForAlias, defaultArtifactPath, describeArtifactPathMismatch, getTicket, loadManifest, writeText } from "../lib/workflow"

export default tool({
  description: "Write the full body for a canonical planning, implementation, review, or QA artifact.",
  args: {
    ticket_id: tool.schema.string().describe("Ticket id that owns the artifact."),
    path: tool.schema.string().describe("Repo-relative canonical artifact path."),
    kind: tool.schema.string().describe("Artifact kind, for example plan, review, qa, smoke-test, handoff, or note."),
    stage: tool.schema.string().describe("Workflow stage associated with the artifact."),
    content: tool.schema.string().describe("Full markdown or text body to persist at the canonical artifact path."),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const ticket = getTicket(manifest, args.ticket_id)
    const resolved = canonicalizeRepoPath(args.path)
    const expectedPath = defaultArtifactPath(ticket.id, args.stage, args.kind)
    const aliasedCurrentArtifact = currentStageArtifactForAlias(ticket, args.stage, args.kind, resolved.path)

    if (resolved.path !== expectedPath && !(resolved.mismatch_class === "history_path" && aliasedCurrentArtifact?.source_path === expectedPath)) {
      throw new Error(
        describeArtifactPathMismatch({
          provided_path: args.path,
          expected_path: expectedPath,
          mismatch_class: resolved.mismatch_class || "non_canonical",
        }),
      )
    }

    await writeText(expectedPath, args.content)

    return JSON.stringify(
      {
        ticket_id: ticket.id,
        path: expectedPath,
        bytes: Buffer.byteLength(args.content, "utf8"),
      },
      null,
      2,
    )
  },
})
