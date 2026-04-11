// @ts-ignore - the generated runtime mirrors @opencode-ai/plugin during tool execution.
import { tool } from "@opencode-ai/plugin"
import {
  loadManifest,
  loadWorkflowState,
  rootPath,
  saveWorkflowState,
  syncWorkflowSelection,
} from "../lib/workflow"

function parseObjectArg(raw: string, label: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error(`${label} must encode an object.`)
    }
    return parsed as Record<string, unknown>
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    throw new Error(`Unable to parse ${label}: ${message}`)
  }
}

export default tool({
  description: "Refresh canonical workflow repair follow-on state from a managed repair run using the generated runtime persistence contract.",
  args: {
    change_summary: tool.schema.string().describe("Summary of the repair-driven workflow change."),
    process_version: tool.schema.number().int().describe("Workflow process version after the deterministic refresh.").optional(),
    parallel_mode: tool.schema.enum(["parallel-lanes", "sequential"]).describe("Parallel execution mode after the deterministic refresh.").optional(),
    repair_follow_on_json: tool.schema.string().describe("Serialized repair_follow_on payload to persist through the runtime workflow contract."),
  },
  async execute(args: { change_summary: string; process_version?: number; parallel_mode?: "parallel-lanes" | "sequential"; repair_follow_on_json: string }) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const repairFollowOn = parseObjectArg(args.repair_follow_on_json, "repair_follow_on_json")
    const changeSummary = args.change_summary.trim()
    if (!changeSummary) {
      throw new Error("change_summary must not be empty.")
    }
    const changedAt = new Date().toISOString()
    const processVersion = typeof args.process_version === "number" && args.process_version > 0
      ? Math.floor(args.process_version)
      : workflow.process_version

    syncWorkflowSelection(workflow, manifest)
    workflow.process_version = processVersion
    if (args.parallel_mode) {
      workflow.parallel_mode = args.parallel_mode
    }
    workflow.process_last_changed_at = changedAt
    workflow.process_last_change_summary = changeSummary
    workflow.pending_process_verification = true
    workflow.repair_follow_on = {
      ...(workflow.repair_follow_on as unknown as Record<string, unknown>),
      ...repairFollowOn,
      process_version: processVersion,
      last_updated_at:
        typeof repairFollowOn.last_updated_at === "string" && repairFollowOn.last_updated_at.trim()
          ? repairFollowOn.last_updated_at
          : changedAt,
    } as typeof workflow.repair_follow_on

    // Auto-resolve managed_blocked only when the cycle is fully clean.
    const rfo = workflow.repair_follow_on
    const requiredStages = Array.isArray(rfo.required_stages) ? rfo.required_stages : []
    const completedStages = Array.isArray(rfo.completed_stages) ? rfo.completed_stages : []
    if (
      rfo.outcome === "managed_blocked" &&
      requiredStages.every((stage: string) => completedStages.includes(stage)) &&
      rfo.blocking_reasons.length === 0 &&
      rfo.verification_passed === true &&
      rfo.handoff_allowed === true
    ) {
      rfo.outcome = "clean"
    }

    const expectedRevision = workflow.state_revision
    await saveWorkflowState(workflow, rootPath(), expectedRevision, { refreshDerivedSurfaces: false }, { manifest, skipGraphValidation: true })

    return JSON.stringify(
      {
        active_ticket: workflow.active_ticket,
        process_version: workflow.process_version,
        parallel_mode: workflow.parallel_mode,
        pending_process_verification: workflow.pending_process_verification,
        repair_follow_on: workflow.repair_follow_on,
        process_last_changed_at: workflow.process_last_changed_at,
        process_last_change_summary: workflow.process_last_change_summary,
      },
      null,
      2,
    )
  },
})
