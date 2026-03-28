import { tool } from "@opencode-ai/plugin"
import { readFile } from "node:fs/promises"
import {
  currentArtifacts,
  defaultArtifactPath,
  describeAllowedStatusesForStage,
  getTicket,
  getTicketWorkflowState,
  getProcessVerificationState,
  hasArtifact,
  hasPendingRepairFollowOn,
  hasReviewArtifact,
  historicalArtifacts,
  isPlanApprovedForTicket,
  latestArtifact,
  latestReviewArtifact,
  loadManifest,
  loadWorkflowState,
  nextRepairFollowOnStage,
  openSplitScopeChildren,
  repairFollowOnBlockingReason,
  ticketNeedsProcessVerification,
  validateImplementationArtifactEvidence,
  validateLifecycleStageStatus,
  validateQaArtifactEvidence,
  validateSmokeTestArtifactEvidence,
} from "../lib/workflow"

async function buildTransitionGuidance(ticket: ReturnType<typeof getTicket>, workflow: Awaited<ReturnType<typeof loadWorkflowState>>) {
  const manifest = await loadManifest()
  const blocker = validateLifecycleStageStatus(ticket.stage, ticket.status)
  const approvedPlan = isPlanApprovedForTicket(workflow, ticket.id)
  const needsProcessVerification = ticketNeedsProcessVerification(ticket, workflow)
  const bootstrapStatus = workflow.bootstrap.status
  const repairFollowOnPending = hasPendingRepairFollowOn(workflow)
  const repairFollowOnStage = nextRepairFollowOnStage(workflow)
  const repairFollowOnBlocker = repairFollowOnBlockingReason(workflow)
  const splitChildren = openSplitScopeChildren(manifest, ticket.id)
  const base = {
    current_stage: ticket.stage,
    current_status: ticket.status,
    approved_plan: approvedPlan,
    pending_process_verification: needsProcessVerification,
    current_state_blocker: blocker,
    next_allowed_stages: [] as string[],
    required_artifacts: [] as string[],
    next_action_kind: null as string | null,
    next_action_tool: null as string | null,
    delegate_to_agent: null as string | null,
    required_owner: null as string | null,
    canonical_artifact_path: null as string | null,
    artifact_stage: null as string | null,
    artifact_kind: null as string | null,
    recommended_action: "",
    recommended_ticket_update: null as Record<string, unknown> | null,
  }

  if (bootstrapStatus !== "ready") {
    return {
      ...base,
      next_allowed_stages: [],
      required_artifacts: ["bootstrap"],
      next_action_kind: "run_tool",
      next_action_tool: "environment_bootstrap",
      delegate_to_agent: null,
      required_owner: "team-leader",
      recommended_action: `Bootstrap is ${bootstrapStatus}. Run environment_bootstrap first, then rerun ticket_lookup before attempting lifecycle transitions.`,
      current_state_blocker: blocker || `Bootstrap ${bootstrapStatus}. Lifecycle execution is blocked until environment_bootstrap succeeds.`,
    }
  }

  if (splitChildren.length > 0 && ticket.status !== "done") {
    const foregroundChild = splitChildren[0]
    return {
      ...base,
      next_allowed_stages: [foregroundChild.stage],
      required_artifacts: [],
      next_action_kind: "ticket_update",
      next_action_tool: "ticket_update",
      delegate_to_agent: null,
      required_owner: "team-leader",
      recommended_action: `Keep ${ticket.id} open as a split parent and foreground child ticket ${foregroundChild.id} instead of advancing the parent lane directly.`,
      recommended_ticket_update: { ticket_id: foregroundChild.id, activate: true },
    }
  }

  if (repairFollowOnPending) {
    const repairBlocker = repairFollowOnBlocker || (
      repairFollowOnStage
        ? `Repair follow-on remains incomplete. Complete \`${repairFollowOnStage}\` before resuming ticket lifecycle execution.`
        : "Repair follow-on remains incomplete. Complete the required repair stages before resuming ticket lifecycle execution."
    )
    return {
      ...base,
      next_allowed_stages: [],
      required_artifacts: ["repair_follow_on"],
      next_action_kind: "report_blocker",
      next_action_tool: null,
      delegate_to_agent: null,
      required_owner: "host",
      recommended_action: repairBlocker,
      current_state_blocker: repairBlocker,
    }
  }

  switch (ticket.stage) {
    case "planning":
      if (!hasArtifact(ticket, { stage: "planning" })) {
        return {
          ...base,
          next_allowed_stages: ["planning"],
          required_artifacts: ["planning"],
          next_action_kind: "write_artifact",
          next_action_tool: "artifact_write",
          delegate_to_agent: "planner",
          required_owner: "team-leader",
          canonical_artifact_path: defaultArtifactPath(ticket.id, "planning", "plan"),
          artifact_stage: "planning",
          artifact_kind: "plan",
          recommended_action: "Write and register the planning artifact before moving into plan_review.",
        }
      }
      return {
        ...base,
        next_allowed_stages: ["plan_review"],
        required_artifacts: ["planning"],
        next_action_kind: "ticket_update",
        next_action_tool: "ticket_update",
        delegate_to_agent: null,
        required_owner: "team-leader",
        recommended_action: "Move the ticket into plan_review. Do not probe implementation until plan_review is recorded first.",
        recommended_ticket_update: { ticket_id: ticket.id, stage: "plan_review", activate: true },
      }
    case "plan_review":
      if (!approvedPlan) {
        return {
          ...base,
          next_allowed_stages: ["plan_review"],
          required_artifacts: ["planning"],
          next_action_kind: "ticket_update",
          next_action_tool: "ticket_update",
          delegate_to_agent: null,
          required_owner: "team-leader",
          recommended_action: "Keep the ticket in plan_review and record approval in workflow-state first. Only move to implementation after approval is already recorded.",
          recommended_ticket_update: { ticket_id: ticket.id, stage: "plan_review", approved_plan: true, activate: true },
        }
      }
      return {
        ...base,
        next_allowed_stages: ["implementation"],
        required_artifacts: ["planning"],
        next_action_kind: "ticket_update",
        next_action_tool: "ticket_update",
        delegate_to_agent: "implementer",
        required_owner: "team-leader",
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
          next_action_kind: "write_artifact",
          next_action_tool: "artifact_write",
          delegate_to_agent: "implementer",
          required_owner: "team-leader",
          canonical_artifact_path: defaultArtifactPath(ticket.id, "implementation", "implementation"),
          artifact_stage: "implementation",
          artifact_kind: "implementation",
          recommended_action: "Stay in implementation. Produce and register the implementation artifact with real execution evidence before review.",
          current_state_blocker: implementationBlocker,
        }
      }
      return {
        ...base,
        next_allowed_stages: ["review"],
        required_artifacts: ["implementation"],
        next_action_kind: "ticket_update",
        next_action_tool: "ticket_update",
        delegate_to_agent: "reviewer-code",
        required_owner: "team-leader",
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
          next_action_kind: "write_artifact",
          next_action_tool: "artifact_write",
          delegate_to_agent: "reviewer-code",
          required_owner: "team-leader",
          canonical_artifact_path: defaultArtifactPath(ticket.id, "review", "review"),
          artifact_stage: "review",
          artifact_kind: "review",
          recommended_action: "Keep the ticket in review until at least one current review artifact exists.",
          current_state_blocker: "Review artifact missing.",
        }
      }
      return {
        ...base,
        next_allowed_stages: ["qa"],
        required_artifacts: ["review"],
        next_action_kind: "ticket_update",
        next_action_tool: "ticket_update",
        delegate_to_agent: "tester-qa",
        required_owner: "team-leader",
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
          next_action_kind: "write_artifact",
          next_action_tool: "artifact_write",
          delegate_to_agent: "tester-qa",
          required_owner: "team-leader",
          canonical_artifact_path: defaultArtifactPath(ticket.id, "qa", "qa"),
          artifact_stage: "qa",
          artifact_kind: "qa",
          recommended_action: "Keep the ticket in QA until the QA artifact includes real command output and passes size checks.",
          current_state_blocker: qaBlocker,
        }
      }
      return {
        ...base,
        next_allowed_stages: ["smoke-test"],
        required_artifacts: ["qa"],
        next_action_kind: "ticket_update",
        next_action_tool: "ticket_update",
        delegate_to_agent: "tester-qa",
        required_owner: "team-leader",
        recommended_action: "Advance to smoke-test, return control to the team leader, then use the smoke_test tool. Do not delegate smoke_test to tester-qa or write smoke-test artifacts through artifact_write or artifact_register.",
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
          next_action_kind: "run_tool",
          next_action_tool: "smoke_test",
          delegate_to_agent: null,
          required_owner: "team-leader",
          canonical_artifact_path: defaultArtifactPath(ticket.id, "smoke-test", "smoke-test"),
          artifact_stage: "smoke-test",
          artifact_kind: "smoke-test",
          recommended_action: "Use the smoke_test tool to produce the current smoke-test artifact. Do not fabricate a PASS artifact through generic artifact tools.",
          current_state_blocker: smokeBlocker,
        }
      }
      return {
        ...base,
        next_allowed_stages: ["closeout"],
        required_artifacts: ["smoke-test"],
        next_action_kind: "ticket_update",
        next_action_tool: "ticket_update",
        delegate_to_agent: null,
        required_owner: "team-leader",
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
          next_action_kind: "reverify",
          next_action_tool: "ticket_reverify",
          delegate_to_agent: "backlog-verifier",
          required_owner: "team-leader",
          canonical_artifact_path: defaultArtifactPath(ticket.id, "review", "backlog-verification"),
          artifact_stage: "review",
          artifact_kind: "backlog-verification",
          recommended_action: "Ticket is already closed, but historical trust still needs restoration. Use the backlog verifier to produce current evidence, then run ticket_reverify on this closed ticket instead of trying to reclaim it.",
          recommended_ticket_update: null,
        }
      }
      return {
        ...base,
        next_allowed_stages: [],
        required_artifacts: ["smoke-test"],
        next_action_kind: ticket.status === "done" ? "noop" : "ticket_update",
        next_action_tool: ticket.status === "done" ? null : "ticket_update",
        delegate_to_agent: null,
        required_owner: "team-leader",
        recommended_action: ticket.status === "done" ? "Ticket is already closed." : "Finish closeout and mark the ticket done.",
        recommended_ticket_update: ticket.status === "done" ? null : { ticket_id: ticket.id, stage: "closeout", activate: true },
      }
    default:
      return {
        ...base,
        next_allowed_stages: [],
        next_action_kind: "inspect",
        next_action_tool: "ticket_lookup",
        required_owner: "team-leader",
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
    const processVerification = getProcessVerificationState(manifest, workflow, ticket.id)
    const affectedDoneTickets = processVerification.affected_done_tickets.map((item) => ({
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
        repair_follow_on: workflow.repair_follow_on,
        transition_guidance: {
          ...transitionGuidance,
          allowed_statuses_for_current_stage: describeAllowedStatusesForStage(ticket.stage),
        },
        artifact_bodies: artifactBodies,
        process_verification: {
          pending: processVerification.pending,
          process_changed_at: workflow.process_last_changed_at,
          current_ticket_requires_verification: processVerification.current_ticket_requires_verification,
          clearable_now: processVerification.clearable_now,
          affected_done_tickets: affectedDoneTickets,
        },
      },
      null,
      2,
    )
  },
})
