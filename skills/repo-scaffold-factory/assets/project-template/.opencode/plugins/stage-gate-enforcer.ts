import { type Plugin } from "@opencode-ai/plugin"
import { join, posix } from "node:path"
import { getTicket, hasArtifact, loadManifest, loadWorkflowState, normalizeRepoPath, readJson, rootPath } from "../tools/_workflow"

const SAFE_BASH = /^(pwd|ls|find|rg|grep|cat|head|tail|git status|git diff|git log)\b/i
const SAFE_PREAPPROVAL_FILES = ["README.md", "AGENTS.md", "START-HERE.md", "opencode.jsonc"]
const SAFE_PREAPPROVAL_PREFIXES = ["docs/", "tickets/", ".opencode/commands/", ".opencode/meta/", ".opencode/skills/", ".opencode/state/plans/"]
const BLOCKED_PREAPPROVAL_PREFIXES = [
  ".opencode/state/artifacts/",
  ".opencode/state/handoffs/",
  ".opencode/state/implementations/",
  ".opencode/state/qa/",
  ".opencode/state/reviews/",
  ".opencode/tools/",
  ".opencode/plugins/",
]
const SAFE_PREAPPROVAL_FILE_SET = new Set(SAFE_PREAPPROVAL_FILES)

type StageGateConfig = {
  version: number
  description: string
  model_guidance: string[]
  pre_approval: {
    allowed_files: string[]
    allowed_prefixes: string[]
    blocked_prefixes: string[]
  }
}

const DEFAULT_STAGE_GATE_CONFIG: StageGateConfig = {
  version: 1,
  description: "Configure the documentation-oriented write surface that stays open before plan approval.",
  model_guidance: [
    "Treat this as the pre-approval documentation lane, not an implementation escape hatch.",
    "Only root docs, docs/, tickets/, command docs, bootstrap metadata, local skills, and planning artifacts belong in the allow lists.",
    "Implementation, review, QA, handoff, tool, plugin, and workflow-state files still require plan approval.",
  ],
  pre_approval: {
    allowed_files: SAFE_PREAPPROVAL_FILES,
    allowed_prefixes: SAFE_PREAPPROVAL_PREFIXES,
    blocked_prefixes: BLOCKED_PREAPPROVAL_PREFIXES,
  },
}

function extractFilePath(args: Record<string, unknown>): string {
  const pathValue = args.filePath || args.path || args.target
  return typeof pathValue === "string" ? pathValue : ""
}

function canonicalizeRepoPath(pathValue: string): string {
  const normalized = posix.normalize(normalizeRepoPath(pathValue).replace(/^\/+/, "")).replace(/^\.\//, "")
  if (!normalized || normalized === "." || normalized.startsWith("../")) return ""
  return normalized
}

function normalizePathList(value: unknown, kind: "file" | "prefix"): string[] | undefined {
  if (!Array.isArray(value)) return undefined
  return [...new Set(value
    .filter((entry): entry is string => typeof entry === "string")
    .map((entry) => canonicalizeRepoPath(entry).trim())
    .filter((entry) => entry.length > 0)
    .map((entry) => (kind === "prefix" && !entry.endsWith("/") ? `${entry}/` : entry))
  )]
}

function isWithinSafePreApprovalEnvelope(pathValue: string): boolean {
  const normalized = canonicalizeRepoPath(pathValue)
  if (!normalized) return false
  if (normalized === ".opencode/state/workflow-state.json") return false
  if (BLOCKED_PREAPPROVAL_PREFIXES.some((prefix) => normalized.startsWith(prefix))) return false
  if (SAFE_PREAPPROVAL_FILE_SET.has(normalized)) return true
  return SAFE_PREAPPROVAL_PREFIXES.some((prefix) => normalized.startsWith(prefix))
}

function sanitizeStageGateConfig(raw: unknown): StageGateConfig {
  const config = raw && typeof raw === "object" ? (raw as Partial<StageGateConfig>) : {}
  // Config can narrow the planning lane or add extra blocked paths, but it cannot open paths outside the safe envelope.
  const preApproval =
    config.pre_approval && typeof config.pre_approval === "object"
      ? (config.pre_approval as Partial<StageGateConfig["pre_approval"]>)
      : {}
  const allowedFiles = normalizePathList(preApproval.allowed_files, "file")
  const allowedPrefixes = normalizePathList(preApproval.allowed_prefixes, "prefix")
  const blockedPrefixes = normalizePathList(preApproval.blocked_prefixes, "prefix") ?? []

  return {
    version: DEFAULT_STAGE_GATE_CONFIG.version,
    description: typeof config.description === "string" ? config.description : DEFAULT_STAGE_GATE_CONFIG.description,
    model_guidance: Array.isArray(config.model_guidance)
      ? config.model_guidance.filter((entry): entry is string => typeof entry === "string")
      : DEFAULT_STAGE_GATE_CONFIG.model_guidance,
    pre_approval: {
      allowed_files: (allowedFiles ?? DEFAULT_STAGE_GATE_CONFIG.pre_approval.allowed_files).filter(isWithinSafePreApprovalEnvelope),
      allowed_prefixes: (allowedPrefixes ?? DEFAULT_STAGE_GATE_CONFIG.pre_approval.allowed_prefixes).filter(isWithinSafePreApprovalEnvelope),
      blocked_prefixes: [...new Set([...DEFAULT_STAGE_GATE_CONFIG.pre_approval.blocked_prefixes, ...blockedPrefixes])],
    },
  }
}

async function loadStageGateConfig(): Promise<StageGateConfig> {
  const configPath = join(rootPath(), ".opencode", "config", "stage-gate.json")
  const config = await readJson<StageGateConfig>(configPath, DEFAULT_STAGE_GATE_CONFIG)
  return sanitizeStageGateConfig(config)
}

function isPreApprovalWritePath(pathValue: string, config: StageGateConfig): boolean {
  const normalized = canonicalizeRepoPath(pathValue)
  if (!normalized) return false
  if (normalized === ".opencode/state/workflow-state.json") return false
  if (config.pre_approval.blocked_prefixes.some((prefix) => normalized.startsWith(prefix))) return false
  if (config.pre_approval.allowed_files.includes(normalized)) return true
  return config.pre_approval.allowed_prefixes.some((prefix) => normalized.startsWith(prefix))
}

export const StageGateEnforcer: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      const workflow = await loadWorkflowState().catch(() => undefined)
      if (!workflow || workflow.approved_plan) {
        return
      }
      const stageGateConfig = await loadStageGateConfig()

      if (input.tool === "bash") {
        const command = typeof output.args.command === "string" ? output.args.command : ""
        if (!SAFE_BASH.test(command)) {
          throw new Error("Plan approval required before running implementation-oriented shell commands.")
        }
      }

      if (input.tool === "write" || input.tool === "edit") {
        const filePath = extractFilePath(output.args)
        if (!filePath || !isPreApprovalWritePath(filePath, stageGateConfig)) {
          throw new Error("Plan approval required before editing implementation-stage or runtime state files.")
        }
      }

      if (input.tool === "ticket_update") {
        const manifest = await loadManifest()
        const ticketId = typeof output.args.ticket_id === "string" ? output.args.ticket_id : manifest.active_ticket
        const ticket = getTicket(manifest, ticketId)
        const nextStatus = typeof output.args.status === "string" ? output.args.status : ""
        const approving = typeof output.args.approved_plan === "boolean" ? output.args.approved_plan : undefined

        if (approving && !hasArtifact(ticket, { stage: "planning" })) {
          throw new Error("Planning artifact required before marking the workflow as approved.")
        }

        if (nextStatus === "in_progress" && !workflow.approved_plan && approving !== true) {
          throw new Error("Approved plan required before moving a ticket to in_progress.")
        }
      }
    },
  }
}
