import { tool } from "@opencode-ai/plugin"
import {
  createTicketRecord,
  currentRegistryArtifact,
  defaultStatusForStage,
  getTicket,
  loadArtifactRegistry,
  loadManifest,
  loadWorkflowState,
  normalizeRepoPath,
  saveWorkflowBundle,
  setPlanApprovedForTicket,
  syncWorkflowSelection,
  ticketFilePath,
  type SplitKind,
  type TicketSourceMode,
} from "../lib/workflow"

function normalizeOptional(value: string | undefined): string | undefined {
  if (typeof value !== "string") return undefined
  const normalized = value.trim()
  return normalized || undefined
}

export default tool({
  description: "Create a new ticket or linked follow-up ticket, including process-verification, post-completion issue, and open-parent split follow-up tickets.",
  args: {
    id: tool.schema.string().describe("New ticket id."),
    title: tool.schema.string().describe("New ticket title."),
    lane: tool.schema.string().describe("Owning lane or project area."),
    wave: tool.schema.number().int().describe("Execution wave number."),
    summary: tool.schema.string().describe("Ticket summary."),
    acceptance: tool.schema.array(tool.schema.string()).describe("Acceptance criteria list."),
    depends_on: tool.schema.array(tool.schema.string()).describe("Dependency ticket ids.").optional(),
    decision_blockers: tool.schema.array(tool.schema.string()).describe("Unresolved blockers for this ticket.").optional(),
    parallel_safe: tool.schema.boolean().describe("Whether the ticket can be advanced in a parallel lane when dependencies are satisfied.").optional(),
    overlap_risk: tool.schema.enum(["low", "medium", "high"]).describe("Expected overlap risk with other tickets.").optional(),
    finding_source: tool.schema.string().describe("Optional original finding code when this ticket remediates a validated issue.").optional(),
    source_ticket_id: tool.schema.string().describe("Optional source ticket that this ticket extends or remediates.").optional(),
    source_mode: tool.schema.enum(["process_verification", "post_completion_issue", "net_new_scope", "split_scope"]).describe("Why this ticket is being created.").optional(),
    split_kind: tool.schema.enum(["parallel_independent", "sequential_dependent"]).describe("For split_scope tickets: whether child can run in parallel with parent (parallel_independent) or must wait until parent-owned work is done (sequential_dependent). Required when source_mode is split_scope.").optional(),
    evidence_artifact_path: tool.schema.string().describe("Optional registered artifact path that justifies creation of this linked ticket.").optional(),
    activate: tool.schema.boolean().describe("Whether to make the new ticket active immediately.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const sourceMode: TicketSourceMode = args.source_mode || "net_new_scope"
    const sourceTicketId = normalizeOptional(args.source_ticket_id)
    const evidenceArtifactPath = normalizeOptional(args.evidence_artifact_path)
    const splitKind: SplitKind | undefined = args.split_kind as SplitKind | undefined
    const registry = await loadArtifactRegistry()

    if (manifest.tickets.some((ticket) => ticket.id === args.id.trim())) {
      throw new Error(`Ticket already exists: ${args.id.trim()}`)
    }

    const ticket = createTicketRecord({
      id: args.id,
      title: args.title,
      lane: args.lane,
      wave: args.wave,
      summary: args.summary,
      acceptance: args.acceptance,
      depends_on: args.depends_on,
      decision_blockers: args.decision_blockers,
      parallel_safe: args.parallel_safe,
      overlap_risk: args.overlap_risk,
      finding_source: normalizeOptional(args.finding_source),
      source_ticket_id: sourceTicketId,
      source_mode: sourceMode,
      split_kind: splitKind,
    })

    for (const dependency of ticket.depends_on) {
      getTicket(manifest, dependency)
    }

    let sourceTicket = undefined as ReturnType<typeof getTicket> | undefined
    if (sourceMode !== "net_new_scope") {
      if (!sourceTicketId) {
        throw new Error(`source_ticket_id is required when source_mode is ${sourceMode}.`)
      }
      sourceTicket = getTicket(manifest, sourceTicketId)
      if (ticket.depends_on.includes(sourceTicket.id)) {
        throw new Error(
          `Ticket ${ticket.id} cannot name ${sourceTicket.id} as both source_ticket_id and depends_on.`,
        )
      }

      if (sourceMode === "process_verification") {
        if (!workflow.pending_process_verification) {
          throw new Error("process_verification ticket creation is only available while pending_process_verification is true.")
        }
        if (sourceTicket.status !== "done") {
          throw new Error(`Source ticket ${sourceTicket.id} must be done before creating a process-verification follow-up ticket.`)
        }
        if (!evidenceArtifactPath) {
          throw new Error("evidence_artifact_path is required for process_verification ticket creation.")
        }
        const verificationArtifact = sourceTicket.artifacts.find(
          (artifact) =>
            artifact.path === evidenceArtifactPath &&
            artifact.stage === "review" &&
            artifact.kind === "backlog-verification" &&
            artifact.trust_state === "current",
        )
        const registryArtifact = evidenceArtifactPath ? currentRegistryArtifact(registry, normalizeRepoPath(evidenceArtifactPath)) : undefined
        if (
          !verificationArtifact &&
          !(registryArtifact && registryArtifact.stage === "review" && registryArtifact.kind === "backlog-verification")
        ) {
          throw new Error(
            `No current registered review/backlog-verification artifact exists at ${evidenceArtifactPath} for ${sourceTicket.id}.`,
          )
        }
      }

      if (sourceMode === "post_completion_issue") {
        if (sourceTicket.status !== "done" && !["done", "superseded"].includes(sourceTicket.resolution_state)) {
          throw new Error(`Source ticket ${sourceTicket.id} must already represent completed historical scope before creating a post-completion issue ticket.`)
        }
        if (!evidenceArtifactPath) {
          throw new Error("evidence_artifact_path is required for post_completion_issue ticket creation.")
        }
        const evidenceArtifact = sourceTicket.artifacts.find((artifact) => artifact.path === evidenceArtifactPath)
        const registryArtifact = currentRegistryArtifact(registry, normalizeRepoPath(evidenceArtifactPath))
        if (!evidenceArtifact && !registryArtifact) {
          throw new Error(`No current registered evidence artifact exists at ${evidenceArtifactPath} for ${sourceTicket.id}.`)
        }
      }

      if (sourceMode === "split_scope") {
        if (!splitKind) {
          throw new Error("split_kind is required when source_mode is split_scope.")
        }
        if (splitKind === "sequential_dependent" && args.activate === true) {
          throw new Error("sequential_dependent split children cannot be activated at creation time.")
        }
        if (!["open", "reopened"].includes(sourceTicket.resolution_state) || sourceTicket.status === "done") {
          throw new Error(`Source ticket ${sourceTicket.id} must remain open or reopened before creating a split-scope child ticket.`)
        }
      }
    }

    manifest.tickets.push(ticket)
    if (sourceTicket && !sourceTicket.follow_up_ticket_ids.includes(ticket.id)) {
      sourceTicket.follow_up_ticket_ids.push(ticket.id)
    }
    if (sourceTicket && sourceMode === "split_scope") {
      const splitNote = splitKind === "sequential_dependent"
        ? `Sequential split: this ticket (${sourceTicket.id}) must complete its parent-owned work before child ticket ${ticket.id} may be foregrounded.`
        : `Parallel split: scope delegated to follow-up ticket ${ticket.id}. Keep the parent open and non-foreground until the child work lands.`
      if (!sourceTicket.decision_blockers.includes(splitNote)) {
        sourceTicket.decision_blockers.push(splitNote)
      }
      if (sourceTicket.status === "blocked") {
        sourceTicket.status = defaultStatusForStage(sourceTicket.stage)
      }
    }

    setPlanApprovedForTicket(workflow, ticket.id, false)
    const allOtherTicketsClosed = manifest.tickets.every(
      (t) => t.id === ticket.id || t.status === "done" || t.resolution_state === "superseded"
    )
    // sequential_dependent children must NOT auto-activate while the parent remains open —
    // the parent owns work that must finish first.
    const isSequentialDependentChild = sourceMode === "split_scope" && splitKind === "sequential_dependent"
    const activateNewTicket = typeof args.activate === "boolean"
      ? args.activate
      : allOtherTicketsClosed || (
          sourceMode === "split_scope" &&
          !isSequentialDependentChild &&
          sourceTicket?.id === manifest.active_ticket
        )
    if (activateNewTicket) {
      manifest.active_ticket = ticket.id
    }
    syncWorkflowSelection(workflow, manifest)

    // Skip full-manifest graph validation during ticket_create to avoid deadlocks from
    // pre-existing data quality issues in the manifest. The new ticket's own relationships
    // are already validated above (depends_on targets exist, source ticket checks, etc.).
    await saveWorkflowBundle({ workflow, manifest, skipGraphValidation: true })

    return JSON.stringify(
      {
        created_ticket: ticket.id,
        path: ticketFilePath(ticket.id),
        status: ticket.status,
        finding_source: ticket.finding_source || null,
        source_ticket_id: sourceTicket?.id || null,
        source_mode: sourceMode,
        split_kind: splitKind || null,
        evidence_artifact_path: evidenceArtifactPath || null,
        activated: activateNewTicket,
      },
      null,
      2,
    )
  },
})
