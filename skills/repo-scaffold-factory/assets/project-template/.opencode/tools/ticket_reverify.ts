import { tool } from "@opencode-ai/plugin"
import {
  defaultArtifactPath,
  getTicket,
  getTicketWorkflowState,
  loadArtifactRegistry,
  loadManifest,
  loadWorkflowState,
  normalizeRepoPath,
  registerArtifactSnapshot,
  saveWorkflowBundle,
  type Artifact,
  writeText,
} from "./_workflow"

function renderArtifact(args: {
  sourceTicketId: string
  evidenceTicketId: string
  evidenceArtifactPath: string
  reason: string
}): string {
  return `# Ticket Reverification

## Source Ticket

- ${args.sourceTicketId}

## Evidence

- evidence_ticket_id: ${args.evidenceTicketId}
- evidence_artifact_path: ${args.evidenceArtifactPath}

## Reason

${args.reason}

## Result

Overall Result: PASS
`
}

export default tool({
  description: "Restore trust for a completed historical ticket after follow-up remediation or backlog reverification completes.",
  args: {
    ticket_id: tool.schema.string().describe("Historical source ticket whose trust should be restored."),
    evidence_artifact_path: tool.schema.string().describe("Current artifact path proving the reverification outcome."),
    evidence_ticket_id: tool.schema.string().describe("Ticket that owns the evidence artifact. Defaults to the source ticket.").optional(),
    reason: tool.schema.string().describe("Why this evidence is sufficient to restore trust.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const sourceTicket = getTicket(manifest, args.ticket_id)
    const evidenceTicket = getTicket(manifest, args.evidence_ticket_id || sourceTicket.id)
    const evidencePath = normalizeRepoPath(args.evidence_artifact_path)
    const reason = typeof args.reason === "string" && args.reason.trim()
      ? args.reason.trim()
      : `Trust restored from ${evidenceTicket.id} using ${evidencePath}.`

    if (sourceTicket.status !== "done") {
      throw new Error(`Ticket ${sourceTicket.id} must remain historically done before it can be reverified.`)
    }
    if (
      evidenceTicket.id !== sourceTicket.id &&
      evidenceTicket.source_ticket_id !== sourceTicket.id &&
      !sourceTicket.follow_up_ticket_ids.includes(evidenceTicket.id)
    ) {
      throw new Error(`Evidence ticket ${evidenceTicket.id} is not linked to source ticket ${sourceTicket.id}.`)
    }
    if (evidenceTicket.id !== sourceTicket.id && evidenceTicket.status !== "done") {
      throw new Error(`Evidence ticket ${evidenceTicket.id} must be done before it can restore trust for ${sourceTicket.id}.`)
    }

    const evidenceArtifact = evidenceTicket.artifacts.find(
      (artifact) => artifact.path === evidencePath && artifact.trust_state === "current",
    ) as Artifact | undefined
    if (!evidenceArtifact) {
      throw new Error(`Evidence artifact ${evidencePath} is not a current artifact on ticket ${evidenceTicket.id}.`)
    }

    const registry = await loadArtifactRegistry()
    const canonicalPath = normalizeRepoPath(defaultArtifactPath(sourceTicket.id, "review", "reverification"))
    await writeText(
      canonicalPath,
      renderArtifact({
        sourceTicketId: sourceTicket.id,
        evidenceTicketId: evidenceTicket.id,
        evidenceArtifactPath: evidencePath,
        reason,
      }),
    )
    const reverificationArtifact = await registerArtifactSnapshot({
      ticket: sourceTicket,
      registry,
      source_path: canonicalPath,
      kind: "reverification",
      stage: "review",
      summary: `Trust restored using ${evidenceTicket.id}.`,
    })

    sourceTicket.verification_state = "reverified"
    getTicketWorkflowState(workflow, sourceTicket.id).needs_reverification = false

    await saveWorkflowBundle({ workflow, manifest, registry })

    return JSON.stringify(
      {
        ticket_id: sourceTicket.id,
        verification_state: sourceTicket.verification_state,
        reverification_artifact: reverificationArtifact.path,
        evidence_ticket_id: evidenceTicket.id,
        evidence_artifact_path: evidencePath,
      },
      null,
      2,
    )
  },
})
