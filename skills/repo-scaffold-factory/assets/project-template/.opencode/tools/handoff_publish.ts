import { tool } from "@opencode-ai/plugin"
import { createHash } from "node:crypto"
import { readFile } from "node:fs/promises"
import {
  bootstrapProvenancePath,
  ensureRequiredFile,
  mergeStartHere,
  refreshRestartSurfaces,
  latestHandoffPath,
  loadManifest,
  loadPivotState,
  loadWorkflowState,
  readJson,
  renderStartHere,
  rootPath,
  startHerePath,
  ticketsManifestPath,
  validateHandoffNextAction,
  workflowStatePath,
} from "../lib/workflow"

export default tool({
  description: "Publish the top-level START-HERE handoff and the latest handoff copy in .opencode/state.",
  args: {
    next_action: tool.schema.string().describe("Optional explicit next action.").optional(),
  },
  async execute(args) {
    await ensureRequiredFile(ticketsManifestPath(rootPath()), "tickets/manifest.json")
    await ensureRequiredFile(workflowStatePath(rootPath()), ".opencode/state/workflow-state.json")
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const pivot = await loadPivotState()
    const startHereBefore = await readFile(startHerePath(), "utf-8").catch(() => "")
    const provenance = await readJson<{
      workflow_contract?: {
        post_migration_verification?: {
          backlog_verifier_agent?: string
        }
      }
    }>(bootstrapProvenancePath(), {})
    const backlogVerifierAgent = provenance.workflow_contract?.post_migration_verification?.backlog_verifier_agent
    if (typeof args.next_action === "string") {
      const handoffBlocker = await validateHandoffNextAction(manifest, workflow, args.next_action)
      if (handoffBlocker) {
        throw new Error(handoffBlocker)
      }
    }
    await refreshRestartSurfaces({ manifest, workflow, pivot, nextAction: args.next_action })

    const renderedHandoff = renderStartHere(manifest, workflow, pivot, {
      nextAction: args.next_action,
      backlogVerifierAgent,
    })
    const expectedStartHere = mergeStartHere(startHereBefore, renderedHandoff)
    const actualStartHere = await readFile(startHerePath(), "utf-8")
    const actualLatestHandoff = await readFile(latestHandoffPath(), "utf-8")
    const sha256 = (value: string) => createHash("sha256").update(value).digest("hex")
    const verified = actualStartHere === expectedStartHere && actualLatestHandoff === renderedHandoff
    const openRemediationTickets = manifest.tickets.filter(
      (ticket) => Boolean(ticket.finding_source) && ticket.status !== "done" && ticket.resolution_state !== "superseded",
    )
    const knownReferenceIntegrityIssues = openRemediationTickets.filter((ticket) => ticket.finding_source?.startsWith("REF"))

    return JSON.stringify(
      {
        start_here: startHerePath(),
        latest_handoff: latestHandoffPath(),
        verified,
        active_ticket: manifest.active_ticket,
        bootstrap_status: workflow.bootstrap.status,
        pending_process_verification: workflow.pending_process_verification,
        code_quality_status: {
          open_remediation_tickets: openRemediationTickets.length,
          known_reference_integrity_issues: knownReferenceIntegrityIssues.length,
        },
        start_here_sha256: sha256(actualStartHere),
        latest_handoff_sha256: sha256(actualLatestHandoff),
      },
      null,
      2,
    )
  },
})
