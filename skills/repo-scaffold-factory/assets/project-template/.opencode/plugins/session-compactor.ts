import { access } from "node:fs/promises"
import { type Plugin } from "@opencode-ai/plugin"
import {
  artifactRegistryPath,
  contextSnapshotPath,
  getTicket,
  latestHandoffPath,
  loadArtifactRegistry,
  loadManifest,
  loadWorkflowState,
  startHerePath,
  ticketsManifestPath,
  workflowStatePath,
  writeJson,
  type Artifact,
  type ArtifactRegistryEntry,
} from "../tools/_workflow"

type CompactionInput = {
  sessionID?: string
  session_id?: string
}

type ArtifactReference = Pick<Artifact, "kind" | "path" | "stage" | "summary" | "created_at">
type ArtifactCandidate = ArtifactReference & { source: "ticket" | "registry" }

const MAX_RECENT_ARTIFACTS = 4

const RESTART_REFERENCES = [
  {
    path: "START-HERE.md",
    detail: "derived restart surface",
    required: true,
    absolutePath: startHerePath,
  },
  {
    path: "tickets/manifest.json",
    detail: "active ticket and registered artifact metadata",
    required: true,
    absolutePath: ticketsManifestPath,
  },
  {
    path: ".opencode/state/workflow-state.json",
    detail: "active stage, status, and approved plan flag",
    required: true,
    absolutePath: workflowStatePath,
  },
  {
    path: ".opencode/state/artifacts/registry.json",
    detail: "cross-ticket artifact registry",
    required: true,
    absolutePath: artifactRegistryPath,
  },
  {
    path: ".opencode/state/context-snapshot.md",
    detail: "latest concise ticket context",
    absolutePath: contextSnapshotPath,
  },
  {
    path: ".opencode/state/latest-handoff.md",
    detail: "latest closeout or resume handoff",
    absolutePath: latestHandoffPath,
  },
] as const

function boolLabel(value: boolean): string {
  return value ? "yes" : "no"
}

function uniqueRecentArtifacts(ticketId: string, ticketArtifacts: Artifact[], registryArtifacts: ArtifactRegistryEntry[]): ArtifactReference[] {
  const candidates: ArtifactCandidate[] = [
    ...ticketArtifacts.map((artifact) => ({ ...artifact, source: "ticket" as const })),
    ...registryArtifacts
      .filter((artifact) => artifact.ticket_id === ticketId)
      .map((artifact) => ({ ...artifact, source: "registry" as const })),
  ]
  candidates.sort((left, right) => {
    const dateDelta = Date.parse(right.created_at) - Date.parse(left.created_at)
    if (!Number.isNaN(dateDelta) && dateDelta !== 0) {
      return dateDelta
    }
    if (left.source !== right.source) {
      return left.source === "ticket" ? -1 : 1
    }
    return left.path.localeCompare(right.path)
  })

  const seen = new Set<string>()
  return candidates
    .filter((artifact) => {
      const key = `${artifact.kind}|${artifact.path}|${artifact.stage}|${artifact.created_at}`
      if (seen.has(key)) {
        return false
      }
      seen.add(key)
      return true
    })
    .slice(0, MAX_RECENT_ARTIFACTS)
    .map(({ source: _source, ...artifact }) => artifact)
}

function renderArtifactLine(artifact: ArtifactReference): string {
  const summary = artifact.summary?.trim()
  return `- ${artifact.kind}: ${artifact.path} (${artifact.stage}, ${artifact.created_at})${summary ? ` - ${summary}` : ""}`
}

function resolveActiveTicket(manifest: Awaited<ReturnType<typeof loadManifest>>, workflowActiveTicket: string) {
  try {
    return getTicket(manifest, workflowActiveTicket)
  } catch {
    return getTicket(manifest, manifest.active_ticket)
  }
}

async function referenceExists(pathFactory: () => string): Promise<boolean> {
  try {
    await access(pathFactory())
    return true
  } catch {
    return false
  }
}

function fallbackContext(): string {
  return [
    "## Restart Preservation",
    "Use only recorded repo state. Do not invent tickets, stages, approvals, or missing artifacts.",
    "",
    "### Re-read On Resume",
    "- START-HERE.md",
    "- tickets/manifest.json",
    "- .opencode/state/workflow-state.json",
    "- .opencode/state/artifacts/registry.json",
  ].join("\n")
}

export const SessionCompactor: Plugin = async () => {
  return {
    "experimental.session.compacting": async (input: CompactionInput, output) => {
      const timestamp = new Date().toISOString()
      const sessionId = input.sessionID ?? input.session_id

      try {
        const [manifest, workflow, registry] = await Promise.all([
          loadManifest(),
          loadWorkflowState(),
          loadArtifactRegistry(),
        ])
        const ticket = resolveActiveTicket(manifest, workflow.active_ticket)
        const recentArtifacts = uniqueRecentArtifacts(ticket.id, ticket.artifacts, registry.artifacts)
        const availableReferences = await Promise.all(
          RESTART_REFERENCES.map(async (reference) => ({
            ...reference,
            available: reference.required ? true : await referenceExists(reference.absolutePath),
          })),
        )

        const workflowLines = [
          `- Active ticket: ${ticket.id}`,
          `- Ticket title: ${ticket.title}`,
          `- Workflow stage: ${workflow.stage}`,
          `- Ticket stage: ${ticket.stage}`,
          `- Workflow status: ${workflow.status}`,
          `- Ticket status: ${ticket.status}`,
          `- Approved plan: ${boolLabel(workflow.approved_plan)}`,
        ]

        if (manifest.active_ticket !== workflow.active_ticket) {
          workflowLines.push(`- Manifest active ticket: ${manifest.active_ticket}`)
        }

        const artifactLines =
          recentArtifacts.length > 0 ? recentArtifacts.map(renderArtifactLine) : ["- No recorded artifacts for the active ticket"]

        const referenceLines = availableReferences
          .filter((reference) => reference.available)
          .map((reference) => `- ${reference.path} (${reference.detail})`)

        output.context.push(
          [
            "## Restart Preservation",
            "Use only recorded repo state below. Do not invent tickets, stage approvals, or missing artifacts.",
            "",
            "### Workflow Signals",
            ...workflowLines,
            "",
            "### Active Ticket Summary",
            `- ${ticket.summary}`,
            "",
            "### Recent Artifact References",
            ...artifactLines,
            "",
            "### Restart References",
            ...referenceLines,
            "",
            "### Resume Rule",
            "- Re-read the listed files before advancing stage or ticket state after compaction.",
          ].join("\n"),
        )

        await writeJson(".opencode/state/last-compaction.json", {
          timestamp,
          session_id: sessionId,
          preserved: {
            active_ticket: ticket.id,
            ticket_title: ticket.title,
            workflow_stage: workflow.stage,
            ticket_stage: ticket.stage,
            workflow_status: workflow.status,
            ticket_status: ticket.status,
            approved_plan: workflow.approved_plan,
            recent_artifacts: recentArtifacts.map((artifact) => ({
              kind: artifact.kind,
              path: artifact.path,
              stage: artifact.stage,
              created_at: artifact.created_at,
            })),
            restart_references: referenceLines.map((line) => line.replace(/^- /, "")),
          },
        })
      } catch (error) {
        output.context.push(fallbackContext())
        await writeJson(".opencode/state/last-compaction.json", {
          timestamp,
          session_id: sessionId,
          note: "Fell back to minimal restart preservation because canonical state could not be read.",
          error: error instanceof Error ? error.message : String(error),
          preserved: {
            restart_references: [
              "START-HERE.md",
              "tickets/manifest.json",
              ".opencode/state/workflow-state.json",
              ".opencode/state/artifacts/registry.json",
            ],
          },
        })
      }
    },
  }
}
