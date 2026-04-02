import { tool } from "@opencode-ai/plugin"
import { stat } from "node:fs/promises"
import {
  canonicalizeRepoPath,
  defaultArtifactPath,
  describeArtifactPathMismatch,
  getTicket,
  loadArtifactRegistry,
  loadManifest,
  registerArtifactSnapshot,
  saveArtifactRegistry,
  saveManifest,
} from "../lib/workflow"

export default tool({
  description: "Register an existing canonical planning, implementation, review, or QA artifact.",
  args: {
    ticket_id: tool.schema.string().describe("Ticket id that owns the artifact."),
    path: tool.schema.string().describe("Repo-relative path to the artifact."),
    kind: tool.schema.string().describe("Artifact kind, for example plan, review, qa, smoke-test, handoff, or note."),
    stage: tool.schema.string().describe("Workflow stage associated with the artifact."),
    summary: tool.schema.string().describe("Short artifact summary.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const ticket = getTicket(manifest, args.ticket_id)
    const resolved = canonicalizeRepoPath(args.path)
    const expectedPath = defaultArtifactPath(ticket.id, args.stage, args.kind)

    if (resolved.path !== expectedPath) {
      throw new Error(
        describeArtifactPathMismatch({
          provided_path: args.path,
          expected_path: expectedPath,
          mismatch_class: resolved.mismatch_class || "non_canonical",
        }),
      )
    }

    const fileInfo = await stat(resolved.path).catch(() => undefined)
    if (!fileInfo?.isFile()) {
      throw new Error(`Artifact file does not exist at ${resolved.path}. Write it with artifact_write before registering it.`)
    }

    const registry = await loadArtifactRegistry()
    const artifact = await registerArtifactSnapshot({
      ticket,
      registry,
      source_path: resolved.path,
      kind: args.kind,
      stage: args.stage,
      summary: args.summary,
    })

    await saveManifest(manifest)
    await saveArtifactRegistry(registry)

    return JSON.stringify(
      {
        ticket_id: ticket.id,
        artifact_count: ticket.artifacts.length,
        registry_count: registry.artifacts.length,
        latest_artifact: ticket.artifacts[ticket.artifacts.length - 1],
      },
      null,
      2,
    )
  },
})
