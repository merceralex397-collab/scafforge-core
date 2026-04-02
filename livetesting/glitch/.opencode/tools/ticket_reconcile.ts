import { tool } from "@opencode-ai/plugin"
import {
  currentRegistryArtifact,
  defaultArtifactPath,
  getTicket,
  getTicketWorkflowState,
  loadArtifactRegistry,
  loadManifest,
  loadWorkflowState,
  normalizeRepoPath,
  registerArtifactSnapshot,
  releaseLaneLease,
  saveWorkflowBundle,
  setPlanApprovedForTicket,
  syncWorkflowSelection,
  type Artifact,
  type Ticket,
  type TicketSourceMode,
  writeText,
} from "../lib/workflow"

function normalizeOptional(value: string | undefined): string | undefined {
  if (typeof value !== "string") return undefined
  const normalized = value.trim()
  return normalized || undefined
}

function isCompletedHistoricalTicket(ticket: Ticket): boolean {
  return ticket.status === "done" || ticket.resolution_state === "done" || ticket.resolution_state === "superseded"
}

function findEvidenceArtifact(
  sourceTicket: Ticket,
  targetTicket: Ticket,
  replacementSourceTicket: Ticket,
  registry: Awaited<ReturnType<typeof loadArtifactRegistry>>,
  artifactPath: string,
): Artifact | undefined {
  const normalized = normalizeRepoPath(artifactPath)
  const allowedTicketIds = new Set([sourceTicket.id, targetTicket.id, replacementSourceTicket.id])
  return [...sourceTicket.artifacts, ...targetTicket.artifacts].find(
    (artifact) => artifact.path === normalized && artifact.trust_state === "current",
  )
    ?? ((): Artifact | undefined => {
      const registryArtifact = currentRegistryArtifact(registry, normalized)
      if (!registryArtifact || !allowedTicketIds.has(registryArtifact.ticket_id)) {
        return undefined
      }
      return registryArtifact
    })()
}

function renderArtifact(args: {
  sourceTicketId: string
  targetTicketId: string
  evidenceArtifactPath: string
  reason: string
  replacementSourceTicketId: string
  replacementSourceMode: TicketSourceMode | null
  removedDependencyOnSource: boolean
  supersededTarget: boolean
}): string {
  return `# Ticket Reconciliation

## Canonical Source

- source_ticket_id: ${args.sourceTicketId}
- target_ticket_id: ${args.targetTicketId}
- replacement_source_ticket_id: ${args.replacementSourceTicketId}
- replacement_source_mode: ${args.replacementSourceMode || "unchanged"}

## Evidence

- evidence_artifact_path: ${args.evidenceArtifactPath}

## Applied Reconciliation

- removed_dependency_on_source: ${args.removedDependencyOnSource ? "true" : "false"}
- superseded_target: ${args.supersededTarget ? "true" : "false"}

## Reason

${args.reason}
`
}

export default tool({
  description: "Reconcile stale or contradictory source/follow-up linkage using current registered evidence instead of manual manifest edits.",
  args: {
    source_ticket_id: tool.schema.string().describe("Canonical source ticket that should own the follow-up linkage."),
    target_ticket_id: tool.schema.string().describe("Follow-up ticket whose lineage or dependency graph needs reconciliation."),
    evidence_artifact_path: tool.schema.string().describe("Current registered artifact path that justifies the reconciliation."),
    reason: tool.schema.string().describe("Why the current ticket graph is stale or contradictory."),
    replacement_source_ticket_id: tool.schema.string().describe("Optional replacement source ticket. Defaults to source_ticket_id.").optional(),
    replacement_source_mode: tool.schema.enum(["process_verification", "post_completion_issue", "net_new_scope", "split_scope"]).describe("Optional replacement source mode for the target ticket.").optional(),
    remove_dependency_on_source: tool.schema.boolean().describe("Whether to remove any target dependency on the canonical source ticket.").optional(),
    supersede_target: tool.schema.boolean().describe("Whether to close the target ticket as superseded after reconciliation.").optional(),
    activate_source: tool.schema.boolean().describe("Whether to make the canonical source ticket active after reconciliation.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const sourceTicket = getTicket(manifest, args.source_ticket_id)
    const targetTicket = getTicket(manifest, args.target_ticket_id)
    const replacementSourceTicketId = normalizeOptional(args.replacement_source_ticket_id) || sourceTicket.id
    const replacementSourceTicket = getTicket(manifest, replacementSourceTicketId)
    const evidenceArtifactPath = normalizeRepoPath(args.evidence_artifact_path)
    const reason = args.reason.trim()
    const replacementSourceMode = args.replacement_source_mode || targetTicket.source_mode || null
    const removeDependencyOnSource = args.remove_dependency_on_source === true
    const supersedeTarget = args.supersede_target === true

    if (!reason) {
      throw new Error("reason must not be empty.")
    }

    const registry = await loadArtifactRegistry()
    const evidenceArtifact = findEvidenceArtifact(sourceTicket, targetTicket, replacementSourceTicket, registry, evidenceArtifactPath)
    if (!evidenceArtifact) {
      throw new Error(`No current registered evidence artifact exists at ${evidenceArtifactPath} for this reconciliation.`)
    }

    if (replacementSourceMode === "split_scope" && (!["open", "reopened"].includes(replacementSourceTicket.resolution_state) || replacementSourceTicket.status === "done")) {
      throw new Error(`split_scope reconciliation requires an open or reopened replacement source ticket. ${replacementSourceTicket.id} is not currently eligible.`)
    }
    if (replacementSourceMode === "post_completion_issue" && !isCompletedHistoricalTicket(replacementSourceTicket)) {
      throw new Error(`post_completion_issue reconciliation requires a completed historical source ticket. ${replacementSourceTicket.id} is still open.`)
    }
    if (replacementSourceMode === "process_verification" && !isCompletedHistoricalTicket(replacementSourceTicket)) {
      throw new Error(`process_verification reconciliation requires a completed historical source ticket. ${replacementSourceTicket.id} is still open.`)
    }

    const previousSourceTicketId = normalizeOptional(targetTicket.source_ticket_id)
    if (previousSourceTicketId) {
      const previousSource = manifest.tickets.find((ticket) => ticket.id === previousSourceTicketId)
      if (previousSource) {
        previousSource.follow_up_ticket_ids = previousSource.follow_up_ticket_ids.filter((candidate) => candidate !== targetTicket.id)
      }
    }

    targetTicket.source_ticket_id = replacementSourceTicket.id
    targetTicket.source_mode = replacementSourceMode ?? undefined

    if (!replacementSourceTicket.follow_up_ticket_ids.includes(targetTicket.id)) {
      replacementSourceTicket.follow_up_ticket_ids.push(targetTicket.id)
    }

    if (removeDependencyOnSource) {
      const contradictorySourceIds = new Set([sourceTicket.id, replacementSourceTicket.id, previousSourceTicketId].filter(Boolean))
      targetTicket.depends_on = targetTicket.depends_on.filter((candidate) => !contradictorySourceIds.has(candidate))
    }

    if (supersedeTarget) {
      targetTicket.stage = "closeout"
      targetTicket.status = "done"
      targetTicket.resolution_state = "superseded"
      targetTicket.verification_state = "reverified"
      getTicketWorkflowState(workflow, targetTicket.id).needs_reverification = false
      releaseLaneLease(workflow, targetTicket.id)
      setPlanApprovedForTicket(workflow, targetTicket.id, false)
      if (manifest.active_ticket === targetTicket.id) {
        manifest.active_ticket = replacementSourceTicket.id
      }
    }

    if (args.activate_source === true) {
      manifest.active_ticket = replacementSourceTicket.id
    }
    syncWorkflowSelection(workflow, manifest)

    const canonicalPath = normalizeRepoPath(defaultArtifactPath(sourceTicket.id, "review", "ticket-reconciliation"))
    await writeText(
      canonicalPath,
      renderArtifact({
        sourceTicketId: sourceTicket.id,
        targetTicketId: targetTicket.id,
        evidenceArtifactPath,
        reason,
        replacementSourceTicketId: replacementSourceTicket.id,
        replacementSourceMode,
        removedDependencyOnSource: removeDependencyOnSource,
        supersededTarget: supersedeTarget,
      }),
    )
    const reconciliationArtifact = await registerArtifactSnapshot({
      ticket: sourceTicket,
      registry,
      source_path: canonicalPath,
      kind: "ticket-reconciliation",
      stage: "review",
      summary: `Reconciled ${targetTicket.id} against ${replacementSourceTicket.id}.`,
    })

    await saveWorkflowBundle({ workflow, manifest, registry })

    return JSON.stringify(
      {
        source_ticket_id: sourceTicket.id,
        target_ticket_id: targetTicket.id,
        replacement_source_ticket_id: replacementSourceTicket.id,
        replacement_source_mode: replacementSourceMode,
        removed_dependency_on_source: removeDependencyOnSource,
        superseded_target: supersedeTarget,
        evidence_artifact_path: evidenceArtifact.path,
        reconciliation_artifact: reconciliationArtifact.path,
        active_ticket: manifest.active_ticket,
      },
      null,
      2,
    )
  },
})
