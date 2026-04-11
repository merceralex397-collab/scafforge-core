import { tool } from "@opencode-ai/plugin"
import {
  defaultArtifactPath,
  getTicket,
  getTicketWorkflowState,
  loadArtifactRegistry,
  loadManifest,
  loadWorkflowState,
  markTicketDone,
  normalizeRepoPath,
  registerArtifactSnapshot,
  saveWorkflowBundle,
  syncWorkflowSelection,
  ticketEligibleForTrustRestoration,
  type Artifact,
  writeText,
} from "../lib/workflow"

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
  description: "Restore trust for a historical ticket after follow-up remediation or backlog reverification completes. This is the legal mutation path for closed done tickets and reopened historical tickets whose current evidence disproves the defect.",
  args: {
    ticket_id: tool.schema.string().describe("Historical source ticket whose trust should be restored."),
    evidence_artifact_path: tool.schema.string().describe("Current artifact path proving the reverification outcome. Optional when verification_content is supplied and should be recorded in this same call.").optional(),
    evidence_ticket_id: tool.schema.string().describe("Ticket that owns the evidence artifact. Defaults to the source ticket.").optional(),
    verification_content: tool.schema.string().describe("Optional review/backlog-verification body to record and consume in this same call for closed-ticket reverification.").optional(),
    reason: tool.schema.string().describe("Why this evidence is sufficient to restore trust.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const sourceTicket = getTicket(manifest, args.ticket_id)
    const evidenceTicket = getTicket(manifest, args.evidence_ticket_id || sourceTicket.id)
    const evidencePath = typeof args.evidence_artifact_path === "string" && args.evidence_artifact_path.trim()
      ? normalizeRepoPath(args.evidence_artifact_path)
      : null
    const verificationContent = typeof args.verification_content === "string" && args.verification_content.trim()
      ? args.verification_content.trim()
      : null
    const reason = typeof args.reason === "string" && args.reason.trim()
      ? args.reason.trim()
      : `Trust restored from ${evidenceTicket.id} using ${evidencePath || "inline reverification content"}.`

    if (!ticketEligibleForTrustRestoration(sourceTicket)) {
      throw new Error(`Ticket ${sourceTicket.id} must still be a historical done or reopened ticket before it can be reverified.`)
    }
    if (!evidencePath && !verificationContent) {
      throw new Error("ticket_reverify requires evidence_artifact_path or verification_content.")
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

    const registry = await loadArtifactRegistry()
    let evidenceArtifact = evidencePath
      ? evidenceTicket.artifacts.find(
          (artifact) => artifact.path === evidencePath && artifact.trust_state === "current",
        ) as Artifact | undefined
      : undefined
    if (!evidenceArtifact && evidencePath) {
      throw new Error(`Evidence artifact ${evidencePath} is not a current artifact on ticket ${evidenceTicket.id}.`)
    }
    if (!evidenceArtifact && verificationContent) {
      const verificationCanonicalPath = normalizeRepoPath(defaultArtifactPath(sourceTicket.id, "review", "backlog-verification"))
      await writeText(verificationCanonicalPath, verificationContent)
      evidenceArtifact = await registerArtifactSnapshot({
        ticket: sourceTicket,
        registry,
        source_path: verificationCanonicalPath,
        kind: "backlog-verification",
        stage: "review",
        summary: `Backlog verification recorded during ticket_reverify for ${sourceTicket.id}.`,
      })
    }

    const canonicalPath = normalizeRepoPath(defaultArtifactPath(sourceTicket.id, "review", "reverification"))
    await writeText(
      canonicalPath,
      renderArtifact({
        sourceTicketId: sourceTicket.id,
        evidenceTicketId: evidenceTicket.id,
        evidenceArtifactPath: evidenceArtifact?.path || evidencePath || normalizeRepoPath(defaultArtifactPath(sourceTicket.id, "review", "backlog-verification")),
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

    if (sourceTicket.status !== "done") {
      markTicketDone(sourceTicket, workflow)
      syncWorkflowSelection(workflow, manifest)
    }
    const hasSelfLineageCorruption = (
      sourceTicket.source_ticket_id === sourceTicket.id
      || sourceTicket.follow_up_ticket_ids.includes(sourceTicket.id)
    )
    if (hasSelfLineageCorruption) {
      sourceTicket.source_ticket_id = undefined
      sourceTicket.source_mode = undefined
      sourceTicket.follow_up_ticket_ids = sourceTicket.follow_up_ticket_ids.filter((ticketId) => ticketId !== sourceTicket.id)
      if (sourceTicket.resolution_state === "superseded") {
        sourceTicket.resolution_state = "done"
      }
    }
    sourceTicket.verification_state = "reverified"
    getTicketWorkflowState(workflow, sourceTicket.id).needs_reverification = false

    await saveWorkflowBundle({ workflow, manifest, registry, skipGraphValidation: true })

    return JSON.stringify(
      {
        ticket_id: sourceTicket.id,
        verification_state: sourceTicket.verification_state,
        reverification_artifact: reverificationArtifact.path,
        evidence_ticket_id: evidenceTicket.id,
        evidence_artifact_path: evidenceArtifact?.path || evidencePath,
      },
      null,
      2,
    )
  },
})
