import { tool } from "@opencode-ai/plugin"
import { readFile } from "node:fs/promises"
import {
  currentArtifacts,
  describeAllowedStatusesForStage,
  getTicket,
  getTicketWorkflowState,
  hasArtifact,
  hasReviewArtifact,
  historicalArtifacts,
  isPlanApprovedForTicket,
  latestArtifact,
  latestReviewArtifact,
  loadManifest,
  loadWorkflowState,
  ticketNeedsProcessVerification,
  ticketsNeedingProcessVerification,
  validateImplementationArtifactEvidence,
  validateLifecycleStageStatus,
  validateQaArtifactEvidence,
  validateSmokeTestArtifactEvidence,
} from "./_workflow"

async function buildTransitionGuidance(ticket: ReturnType<typeof getTicket>, workflow: Awaited<ReturnType<typeof loadWorkflowState>>) {
  const blocker = validateLifecycleStageStatus(ticket.stage, ticket.status)
  const approvedPlan = isPlanApprovedForTicket(workflow, ticket.id)
  const needsProcessVerification = ticketNeedsProcessVerification(ticket, workflow)
  const base = {
    current_stage: ticket.stage,
    current_status: ticket.status,
    approved_plan: approvedPlan,
    pending_process_verification: needsProcessVerification,
    current_state_blocker: blocker,
    next_allowed_stages: [] as string[],
    required_artifacts: [] as string[],
    recommended_action: "",
    recommended_ticket_update: null as Record<string, unknown> | null,
  }

  switch (ticket.stage) {
    case "planning":
      if (!hasArtifact(ticket, { stage: "planning" })) {
        return {
          ...base,
          next_allowed_stages: ["planning"],
          required_artifacts: ["planning"],
          recommended_action: "Write and register the planning artifact before moving into plan_review.",
        }
      }
      return {
        ...base,
        next_allowed_stages: ["plan_review"],
        required_artifacts: ["planning"],
        recommended_action: "Move the ticket into plan_review. Do not probe implementation until plan_review is recorded first.",
        recommended_ticket_update: { ticket_id: ticket.id, stage: "plan_review", activate: true },
      }
    case "plan_review":
      if (!approvedPlan) {
        return {
          ...base,
          next_allowed_stages: ["plan_review"],
          required_artifacts: ["planning"],
          recommended_action: "Keep the ticket in plan_review and record approval in workflow-state first. Only move to implementation after approval is already recorded.",
          recommended_ticket_update: { ticket_id: ticket.id, stage: "plan_review", approved_plan: true, activate: true },
        }
      }
      return {
        ...base,
        next_allowed_stages: ["implementation"],
        required_artifacts: ["planning"],
        recommended_action: "Move the ticket into implementation, then delegate the write-capable implementation lane.",
        recommended_ticket_update: { ticket_id: ticket.id, stage: "implementation", activate: true },
      }
    case "implementation": {
      const implementationBlocker = await validateImplementationArtifactEvidence(ticket)
      if (implementationBlocker) {
        return {
          ...base,
          next_allowed_stages: ["implementation"],
          required_artifacts: ["implementation"],
          recommended_action: "Stay in implementation. Produce and register the implementation artifact with real execution evidence before review.",
          current_state_blocker: implementationBlocker,
        }
      }
      return {
        ...base,
        next_allowed_stages: ["review"],
        required_artifacts: ["implementation"],
        recommended_action: "Move the ticket into review once the implementation artifact is current.",
        recommended_ticket_update: { ticket_id: ticket.id, stage: "review", activate: true },
      }
    }
    case "review":
      if (!hasReviewArtifact(ticket)) {
        return {
          ...base,
          next_allowed_stages: ["review"],
          required_artifacts: ["review"],
          recommended_action: "Keep the ticket in review until at least one current review artifact exists.",
          current_state_blocker: "Review artifact missing.",
        }
      }
      return {
        ...base,
        next_allowed_stages: ["qa"],
        required_artifacts: ["review"],
        recommended_action: "Move the ticket into QA after review approval is registered.",
        recommended_ticket_update: { ticket_id: ticket.id, stage: "qa", activate: true },
      }
    case "qa": {
      const qaBlocker = await validateQaArtifactEvidence(ticket)
      if (qaBlocker) {
        return {
          ...base,
          next_allowed_stages: ["qa"],
          required_artifacts: ["qa"],
          recommended_action: "Keep the ticket in QA until the QA artifact includes real command output and passes size checks.",
          current_state_blocker: qaBlocker,
        }
      }
      return {
        ...base,
        next_allowed_stages: ["smoke-test"],
        required_artifacts: ["qa"],
        recommended_action: "Advance to smoke-test, then use the smoke_test tool. Do not write smoke-test artifacts through artifact_write or artifact_register.",
        recommended_ticket_update: { ticket_id: ticket.id, stage: "smoke-test", activate: true },
      }
    }
    case "smoke-test": {
      const smokeBlocker = await validateSmokeTestArtifactEvidence(ticket)
      if (smokeBlocker) {
        return {
          ...base,
          next_allowed_stages: ["smoke-test"],
          required_artifacts: ["smoke-test"],
          recommended_action: "Use the smoke_test tool to produce the current smoke-test artifact. Do not fabricate a PASS artifact through generic artifact tools.",
          current_state_blocker: smokeBlocker,
        }
      }
      return {
        ...base,
        next_allowed_stages: ["closeout"],
        required_artifacts: ["smoke-test"],
        recommended_action: "Move the ticket into closeout/done now that a passing smoke-test artifact exists.",
        recommended_ticket_update: { ticket_id: ticket.id, stage: "closeout", activate: true },
      }
    }
    case "closeout":
      if (ticket.status === "done" && needsProcessVerification) {
        return {
          ...base,
          next_allowed_stages: [],
          required_artifacts: ["review/backlog-verification or linked follow-up evidence"],
          recommended_action: "Ticket is already closed, but historical trust still needs restoration. Use the backlog verifier to produce current evidence, then run ticket_reverify on this closed ticket instead of trying to reclaim it.",
          recommended_ticket_update: null,
        }
      }
      return {
        ...base,
        next_allowed_stages: [],
        required_artifacts: ["smoke-test"],
        recommended_action: ticket.status === "done" ? "Ticket is already closed." : "Finish closeout and mark the ticket done.",
        recommended_ticket_update: ticket.status === "done" ? null : { ticket_id: ticket.id, stage: "closeout", activate: true },
      }
    default:
      return {
        ...base,
        next_allowed_stages: [],
        recommended_action: "Current stage is invalid. Repair the workflow contract before continuing.",
      }
  }
}

export default tool({
  description: "Resolve the active ticket or a requested ticket from tickets/manifest.json.",
  args: {
    ticket_id: tool.schema.string().describe("Optional ticket id to resolve. Defaults to the active ticket.").optional(),
    include_artifact_contents: tool.schema.boolean().describe("Whether to include the latest artifact bodies for the resolved ticket.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const ticket = getTicket(manifest, args.ticket_id)
    const resolvedWorkflow = args.ticket_id
      ? {
          ...workflow,
          active_ticket: ticket.id,
          stage: ticket.stage,
          status: ticket.status,
          approved_plan: isPlanApprovedForTicket(workflow, ticket.id),
        }
      : workflow
    const latestPlan = latestArtifact(ticket, { stage: "planning" }) || null
    const latestImplementation = latestArtifact(ticket, { stage: "implementation" }) || null
    const latestReview = latestReviewArtifact(ticket) || null
    const latestBacklogVerification = latestArtifact(ticket, { stage: "review", kind: "backlog-verification" }) || null
    const latestQa = latestArtifact(ticket, { stage: "qa" }) || null
    const latestSmokeTest = latestArtifact(ticket, { stage: "smoke-test" }) || null
    const transitionGuidance = await buildTransitionGuidance(ticket, resolvedWorkflow)

    const artifactSummary = {
      current_valid_artifacts: currentArtifacts(ticket),
      historical_artifacts: historicalArtifacts(ticket),
      has_plan: hasArtifact(ticket, { stage: "planning" }),
      has_implementation: hasArtifact(ticket, { stage: "implementation" }),
      has_review: hasReviewArtifact(ticket),
      has_qa: hasArtifact(ticket, { stage: "qa" }),
      has_smoke_test: hasArtifact(ticket, { stage: "smoke-test" }),
      latest_plan: latestPlan,
      latest_implementation: latestImplementation,
      latest_review: latestReview,
      latest_backlog_verification: latestBacklogVerification,
      latest_qa: latestQa,
      latest_smoke_test: latestSmokeTest,
    }
    const affectedDoneTickets = ticketsNeedingProcessVerification(manifest, workflow).map((item) => ({
      id: item.id,
      title: item.title,
      latest_qa: latestArtifact(item, { stage: "qa" }) || null,
      latest_smoke_test: latestArtifact(item, { stage: "smoke-test" }) || null,
      latest_backlog_verification: latestArtifact(item, { stage: "review", kind: "backlog-verification" }) || null,
    }))
    const artifactBodies = args.include_artifact_contents
      ? {
          latest_plan: latestPlan
            ? { ...latestPlan, content: await readFile(latestPlan.path, "utf-8").catch(() => null) }
            : null,
          latest_implementation: latestImplementation
            ? { ...latestImplementation, content: await readFile(latestImplementation.path, "utf-8").catch(() => null) }
            : null,
          latest_review: latestReview
            ? { ...latestReview, content: await readFile(latestReview.path, "utf-8").catch(() => null) }
            : null,
          latest_backlog_verification: latestBacklogVerification
            ? { ...latestBacklogVerification, content: await readFile(latestBacklogVerification.path, "utf-8").catch(() => null) }
            : null,
          latest_qa: latestQa
            ? { ...latestQa, content: await readFile(latestQa.path, "utf-8").catch(() => null) }
            : null,
          latest_smoke_test: latestSmokeTest
            ? { ...latestSmokeTest, content: await readFile(latestSmokeTest.path, "utf-8").catch(() => null) }
            : null,
        }
      : undefined

    return JSON.stringify(
      {
        project: manifest.project,
        active_ticket: manifest.active_ticket,
        workflow: resolvedWorkflow,
        ticket,
        artifact_summary: artifactSummary,
        trust: {
          resolution_state: ticket.resolution_state,
          verification_state: ticket.verification_state,
          needs_reverification: getTicketWorkflowState(workflow, ticket.id).needs_reverification,
          reopen_count: getTicketWorkflowState(workflow, ticket.id).reopen_count,
        },
        lineage: {
          source_ticket_id: ticket.source_ticket_id || null,
          follow_up_ticket_ids: ticket.follow_up_ticket_ids,
        },
        bootstrap: workflow.bootstrap,
        transition_guidance: {
          ...transitionGuidance,
          allowed_statuses_for_current_stage: describeAllowedStatusesForStage(ticket.stage),
        },
        artifact_bodies: artifactBodies,
        process_verification: {
          pending: workflow.pending_process_verification,
          process_changed_at: workflow.process_last_changed_at,
          current_ticket_requires_verification: ticketNeedsProcessVerification(ticket, workflow),
          affected_done_tickets: affectedDoneTickets,
        },
      },
      null,
      2,
    )
  },
})
