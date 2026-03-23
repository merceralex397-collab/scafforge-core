import { tool } from "@opencode-ai/plugin"
import {
  createTicketRecord,
  defaultArtifactPath,
  getTicket,
  getTicketWorkflowState,
  loadArtifactRegistry,
  loadManifest,
  loadWorkflowState,
  markArtifactsHistorical,
  markTicketReopened,
  normalizeRepoPath,
  registerArtifactSnapshot,
  resolveDefectOutcome,
  saveWorkflowBundle,
  setPlanApprovedForTicket,
  syncWorkflowSelection,
  type DefectOutcome,
  writeText,
} from "./_workflow"

function normalizeOptional(value: string | undefined): string | undefined {
  if (typeof value !== "string") return undefined
  const normalized = value.trim()
  return normalized || undefined
}

function renderArtifact(args: {
  sourceTicketId: string
  defectClass: string
  evidenceArtifactPath: string
  outcome: DefectOutcome
  priorCompletionTrusted: boolean
  requiredNextAction: string
}): string {
  return `# Issue Discovery

## Source Ticket

- ${args.sourceTicketId}

## Defect

- defect_class: ${args.defectClass}
- evidence_artifact_path: ${args.evidenceArtifactPath}

## Trust

- prior_completion_trusted: ${args.priorCompletionTrusted ? "true" : "false"}
- required_next_action: ${args.requiredNextAction}
- outcome: ${args.outcome}
`
}

export default tool({
  description: "Record a post-completion defect and deterministically route it to no-action, reopen, follow-up, or rollback-required handling.",
  args: {
    source_ticket_id: tool.schema.string().describe("Completed ticket where the issue was discovered."),
    defect_class: tool.schema.string().describe("Short defect classification, for example regression, scope-gap, or environment drift."),
    acceptance_broken: tool.schema.boolean().describe("Whether the original accepted scope is now false."),
    scope_changed: tool.schema.boolean().describe("Whether the newly discovered issue expands scope beyond the original ticket."),
    rollback_required: tool.schema.boolean().describe("Whether the issue requires rollback or containment work before normal forward progress."),
    evidence_artifact_path: tool.schema.string().describe("Registered artifact path that demonstrates the issue."),
    follow_up_id: tool.schema.string().describe("New ticket id for follow-up or rollback work. Required when the intake creates a new ticket.").optional(),
    follow_up_title: tool.schema.string().describe("Title for the follow-up or rollback ticket.").optional(),
    follow_up_lane: tool.schema.string().describe("Lane for the follow-up or rollback ticket.").optional(),
    follow_up_wave: tool.schema.number().int().describe("Wave number for the follow-up or rollback ticket.").optional(),
    follow_up_summary: tool.schema.string().describe("Summary for the follow-up or rollback ticket.").optional(),
    follow_up_acceptance: tool.schema.array(tool.schema.string()).describe("Acceptance criteria for the follow-up or rollback ticket.").optional(),
    follow_up_depends_on: tool.schema.array(tool.schema.string()).describe("Dependency ticket ids for the follow-up or rollback ticket.").optional(),
    follow_up_decision_blockers: tool.schema.array(tool.schema.string()).describe("Optional blockers for the follow-up or rollback ticket.").optional(),
    follow_up_parallel_safe: tool.schema.boolean().describe("Whether the follow-up ticket is safe for a parallel lane.").optional(),
    follow_up_overlap_risk: tool.schema.enum(["low", "medium", "high"]).describe("Expected overlap risk for the follow-up ticket.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const sourceTicket = getTicket(manifest, args.source_ticket_id)
    const evidenceArtifactPath = args.evidence_artifact_path.trim()
    const defectClass = args.defect_class.trim()

    if (!defectClass) {
      throw new Error("defect_class must not be empty.")
    }
    if (sourceTicket.resolution_state !== "done" && sourceTicket.status !== "done") {
      throw new Error(`Source ticket ${sourceTicket.id} must already be complete before issue intake can route post-completion work.`)
    }

    const evidenceArtifact = sourceTicket.artifacts.find((artifact) => artifact.path === evidenceArtifactPath)
    if (!evidenceArtifact) {
      throw new Error(`Source ticket ${sourceTicket.id} does not reference the evidence artifact ${evidenceArtifactPath}.`)
    }

    const outcome = resolveDefectOutcome(sourceTicket, {
      acceptance_broken: args.acceptance_broken,
      scope_changed: args.scope_changed,
      rollback_required: args.rollback_required,
    })

    let requiredNextAction = outcome
    let createdTicketId: string | null = null
    if (outcome === "invalidates_done") {
      markTicketReopened(sourceTicket, workflow, `Issue intake invalidated prior completion: ${defectClass}`)
      setPlanApprovedForTicket(workflow, sourceTicket.id, false)
      manifest.active_ticket = sourceTicket.id
      syncWorkflowSelection(workflow, manifest)
      requiredNextAction = "reopen_source_ticket"
    } else if (outcome === "follow_up" || outcome === "rollback_required") {
      const followUpDecisionBlockers = [...(args.follow_up_decision_blockers || [])]
      if (outcome === "rollback_required") {
        followUpDecisionBlockers.unshift("Rollback or containment work is required before normal forward progress.")
        sourceTicket.verification_state = "invalidated"
        getTicketWorkflowState(workflow, sourceTicket.id).needs_reverification = true
        markArtifactsHistorical(sourceTicket, undefined, "invalidated", `Rollback required after ${defectClass} issue intake.`)
      }
      const followUp = createTicketRecord({
        id: normalizeOptional(args.follow_up_id) || "",
        title: normalizeOptional(args.follow_up_title) || "",
        lane: normalizeOptional(args.follow_up_lane) || sourceTicket.lane,
        wave: typeof args.follow_up_wave === "number" ? args.follow_up_wave : sourceTicket.wave,
        summary: normalizeOptional(args.follow_up_summary) || "",
        acceptance: args.follow_up_acceptance || [],
        depends_on: args.follow_up_depends_on,
        decision_blockers: followUpDecisionBlockers,
        parallel_safe: args.follow_up_parallel_safe,
        overlap_risk: args.follow_up_overlap_risk,
        source_ticket_id: sourceTicket.id,
        source_mode: "post_completion_issue",
      })
      if (manifest.tickets.some((ticket) => ticket.id === followUp.id)) {
        throw new Error(`Ticket already exists: ${followUp.id}`)
      }
      for (const dependency of followUp.depends_on) {
        getTicket(manifest, dependency)
      }
      manifest.tickets.push(followUp)
      if (!sourceTicket.follow_up_ticket_ids.includes(followUp.id)) {
        sourceTicket.follow_up_ticket_ids.push(followUp.id)
      }
      setPlanApprovedForTicket(workflow, followUp.id, false)
      manifest.active_ticket = followUp.id
      syncWorkflowSelection(workflow, manifest)
      createdTicketId = followUp.id
      requiredNextAction = outcome === "rollback_required" ? "create_rollback_ticket" : "create_follow_up_ticket"
    }

    const priorCompletionTrusted = outcome === "no_action" || outcome === "follow_up"
    const artifactBody = renderArtifact({
      sourceTicketId: sourceTicket.id,
      defectClass,
      evidenceArtifactPath,
      outcome,
      priorCompletionTrusted,
      requiredNextAction,
    })
    const canonicalPath = normalizeRepoPath(defaultArtifactPath(sourceTicket.id, "review", "issue-discovery"))
    await writeText(canonicalPath, artifactBody)

    const registry = await loadArtifactRegistry()
    const issueArtifact = await registerArtifactSnapshot({
      ticket: sourceTicket,
      registry,
      source_path: canonicalPath,
      kind: "issue-discovery",
      stage: "review",
      summary: `${defectClass} intake routed to ${outcome}.`,
    })

    await saveWorkflowBundle({ workflow, manifest, registry })

    return JSON.stringify(
      {
        source_ticket_id: sourceTicket.id,
        outcome,
        issue_artifact: issueArtifact.path,
        prior_completion_trusted: priorCompletionTrusted,
        created_ticket_id: createdTicketId,
        active_ticket: manifest.active_ticket,
      },
      null,
      2,
    )
  },
})
