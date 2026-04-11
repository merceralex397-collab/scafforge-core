import { tool } from "@opencode-ai/plugin"
import {
  describeAllowedStatusesForStage,
  ensureRequiredFile,
  extractArtifactVerdict,
  getTicket,
  hasArtifact,
  hasPendingRepairFollowOn,
  hasReviewArtifact,
  isAllowedFollowOnTicket,
  isPlanApprovedForTicket,
  isBlockingArtifactVerdict,
  loadManifest,
  loadWorkflowState,
  latestArtifact,
  markTicketDone,
  nextRepairFollowOnStage,
  repairFollowOnBlockingReason,
  readArtifactContent,
  resolveRequestedTicketProgress,
  saveWorkflowBundle,
  setPlanApprovedForTicket,
  syncWorkflowSelection,
  ticketsManifestPath,
  ticketsNeedingProcessVerification,
  validateLifecycleStageStatus,
  validateImplementationArtifactEvidence,
  validateReviewArtifactEvidence,
  validateQaArtifactEvidence,
  validateSmokeTestArtifactEvidence,
  workflowStatePath,
  rootPath,
} from "../lib/workflow"

export default tool({
  description: "Update ticket stage, status, summary, and active ticket state.",
  args: {
    ticket_id: tool.schema.string().describe("Ticket id to update."),
    stage: tool.schema.string().describe("Optional new stage value.").optional(),
    status: tool.schema.string().describe("Optional new status value.").optional(),
    summary: tool.schema.string().describe("Optional replacement summary.").optional(),
    activate: tool.schema.boolean().describe("Whether to set this ticket as the active ticket.").optional(),
    approved_plan: tool.schema.boolean().describe("Whether this ticket's plan is approved in workflow-state.").optional(),
    pending_process_verification: tool.schema.boolean().describe("Whether post-migration backlog verification is still pending.").optional(),
  },
  async execute(args) {
    // Lifecycle contract: do not route a ticket to implementation before it passes through plan_review.
    await ensureRequiredFile(ticketsManifestPath(rootPath()), "tickets/manifest.json")
    await ensureRequiredFile(workflowStatePath(rootPath()), ".opencode/state/workflow-state.json")
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    if (hasPendingRepairFollowOn(workflow) && !isAllowedFollowOnTicket(workflow, args.ticket_id)) {
      const repairBlocker = repairFollowOnBlockingReason(workflow) || (
        nextRepairFollowOnStage(workflow)
          ? `Repair follow-on remains incomplete. Complete \`${nextRepairFollowOnStage(workflow)}\` before resuming normal ticket lifecycle mutations.`
          : "Repair follow-on remains incomplete. Complete the required repair stages before resuming normal ticket lifecycle mutations."
      )
      throw new Error(repairBlocker)
    }
    // Even for explicitly allowed follow-on tickets, pending_process_verification
    // is a global workflow write that must remain blocked until managed_blocked
    // is fully resolved.  Lifecycle stage/status progression is permitted; global
    // state mutations are not.
    if (hasPendingRepairFollowOn(workflow) && typeof args.pending_process_verification === "boolean") {
      throw new Error("Cannot modify pending_process_verification while repair follow-on is incomplete. Complete the required repair stages before clearing global verification state.")
    }
    const ticket = getTicket(manifest, args.ticket_id)
    const wasDone = ticket.status === "done"
    const requested = resolveRequestedTicketProgress(ticket, { stage: args.stage, status: args.status })
    const targetStage = requested.stage
    const targetStatus = requested.status

    const lifecycleBlocker = validateLifecycleStageStatus(targetStage, targetStatus)
    if (lifecycleBlocker) {
      throw new Error(lifecycleBlocker)
    }

    if (wasDone && targetStatus !== "done") {
      throw new Error(`Ticket ${ticket.id} is already done. Use ticket_reopen to resume ownership instead of mutating status directly.`)
    }

    if (typeof args.approved_plan === "boolean" && args.approved_plan && !hasArtifact(ticket, { stage: "planning" })) {
      throw new Error("Cannot approve a plan before a planning artifact exists.")
    }

    if (targetStage === "plan_review") {
      if (!hasArtifact(ticket, { stage: "planning" })) {
        throw new Error("Cannot move to plan_review before a planning artifact exists.")
      }
    }

    if (targetStage === "implementation" && args.approved_plan === true && !isPlanApprovedForTicket(workflow, ticket.id)) {
      throw new Error(`Approve ${ticket.id} while it remains in plan_review first, then move it to implementation in a separate ticket_update call.`)
    }

    if (targetStage === "implementation" && !isPlanApprovedForTicket(workflow, ticket.id)) {
      throw new Error(`Cannot move ${ticket.id} to implementation before its plan is approved in workflow-state.`)
    }

    if (targetStage === "implementation" && ticket.stage !== "plan_review") {
      if (ticket.stage !== "review" && ticket.stage !== "qa") {
        throw new Error(
          `Cannot move ${ticket.id} to implementation from ${ticket.stage}. Allowed source stages: plan_review (normal path), review or qa (on FAIL verdict only).`,
        )
      }
      const backwardStage = ticket.stage as "review" | "qa"
      if (!hasArtifact(ticket, { stage: backwardStage })) {
        throw new Error(
          `Cannot route ${ticket.id} back to implementation from ${backwardStage} — no ${backwardStage} artifact exists. Produce an artifact with a blocking verdict before routing backward.`,
        )
      }
      const latestBackwardArtifact = latestArtifact(ticket, { stage: backwardStage, trust_state: "current" })
      const backwardVerdict = extractArtifactVerdict(await readArtifactContent(latestBackwardArtifact))
      if (backwardVerdict.verdict_unclear) {
        throw new Error(
          `Cannot route ${ticket.id} back to implementation from ${backwardStage} — artifact verdict is unclear. Inspect the artifact manually before routing backward.`,
        )
      }
      if (!isBlockingArtifactVerdict(backwardVerdict.verdict)) {
        throw new Error(
          `Cannot route ${ticket.id} back to implementation from ${backwardStage} — latest artifact verdict is ${backwardVerdict.verdict}, not a blocking verdict. Only FAIL verdicts permit backward routing.`,
        )
      }
    }

    if (targetStage === "review") {
      const implementationBlocker = await validateImplementationArtifactEvidence(ticket)
      if (implementationBlocker) {
        throw new Error(implementationBlocker)
      }
    }

    if (targetStage === "qa" && !hasReviewArtifact(ticket)) {
      throw new Error("Cannot move to qa before at least one review artifact exists.")
    }

    if (targetStage === "qa") {
      const reviewBlocker = await validateReviewArtifactEvidence(ticket)
      if (reviewBlocker) {
        throw new Error(reviewBlocker)
      }
      const latestReview = latestArtifact(ticket, { stage: "review", trust_state: "current" })
      const reviewVerdict = extractArtifactVerdict(await readArtifactContent(latestReview))
      if (reviewVerdict.verdict_unclear) {
        throw new Error("Cannot advance past review — latest artifact verdict is unclear. Inspect the review artifact manually before advancing.")
      }
      if (isBlockingArtifactVerdict(reviewVerdict.verdict)) {
        throw new Error("Cannot advance past review — latest artifact shows FAIL verdict. Route back to implementation.")
      }
    }

    if (targetStage === "smoke-test") {
      const qaBlocker = await validateQaArtifactEvidence(ticket)
      if (qaBlocker) {
        throw new Error(qaBlocker)
      }
      const latestQaArtifact = latestArtifact(ticket, { stage: "qa", trust_state: "current" })
      const qaVerdict = extractArtifactVerdict(await readArtifactContent(latestQaArtifact))
      if (qaVerdict.verdict_unclear) {
        throw new Error("Cannot advance past qa — latest artifact verdict is unclear. Inspect the QA artifact manually before advancing.")
      }
      if (isBlockingArtifactVerdict(qaVerdict.verdict)) {
        throw new Error("Cannot advance past qa — latest artifact shows FAIL verdict. Route back to implementation.")
      }
    }

    if (targetStage === "closeout") {
      const smokeTestBlocker = await validateSmokeTestArtifactEvidence(ticket)
      if (smokeTestBlocker) {
        throw new Error(smokeTestBlocker)
      }
    }

    if (args.activate && ticket.source_mode === "split_scope" && ticket.split_kind === "sequential_dependent" && ticket.source_ticket_id) {
      const sourceTicket = getTicket(manifest, ticket.source_ticket_id)
      if (sourceTicket.status !== "done") {
        throw new Error(
          `Cannot activate sequential split child ${ticket.id} before source ticket ${sourceTicket.id} is done. Complete the parent-owned work first.`,
        )
      }
    }

    ticket.stage = targetStage
    if (targetStatus === "done") {
      markTicketDone(ticket, workflow)
    } else {
      ticket.status = targetStatus
    }
    if (args.summary) ticket.summary = args.summary
    if (args.activate) manifest.active_ticket = ticket.id
    if (targetStage === "implementation" && ticket.verification_state !== "invalidated") {
      ticket.verification_state = "suspect"
    }

    if (typeof args.approved_plan === "boolean") {
      setPlanApprovedForTicket(workflow, ticket.id, args.approved_plan)
    }
    syncWorkflowSelection(workflow, manifest)
    if (typeof args.pending_process_verification === "boolean") {
      if (args.pending_process_verification === false) {
        // Intentionally inspect post-mutation state so the clear operation validates the repo exactly as it would be persisted.
        const unverified = ticketsNeedingProcessVerification(manifest, workflow)
        if (unverified.length > 0) {
          throw new Error(
            `Cannot clear pending_process_verification: ${unverified.length} done ticket(s) still require backlog verification (${unverified.map((t) => t.id).join(", ")}). Run the backlog-verifier flow for the listed tickets, register review/backlog-verification artifacts where needed, then retry.`,
          )
        }
      }
      workflow.pending_process_verification = args.pending_process_verification
    }

    await saveWorkflowBundle({ workflow, manifest, skipGraphValidation: true })

    return JSON.stringify(
      {
        updated_ticket: ticket,
        transition: {
          stage: targetStage,
          status: targetStatus,
          allowed_statuses_for_stage: describeAllowedStatusesForStage(targetStage),
        },
        active_ticket: manifest.active_ticket,
        workflow,
      },
      null,
      2,
    )
  },
})
