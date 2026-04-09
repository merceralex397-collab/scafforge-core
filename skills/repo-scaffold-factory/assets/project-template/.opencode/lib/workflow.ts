import { appendFile, copyFile, mkdir, readFile, stat, writeFile } from "node:fs/promises"
import { dirname, join, relative, resolve } from "node:path"
import { createHash } from "node:crypto"

export type OverlapRisk = "low" | "medium" | "high"
export type ParallelMode = "parallel-lanes" | "sequential"
export type BootstrapStatus = "missing" | "ready" | "stale" | "failed"
export type BootstrapBlocker = {
  executable: string
  reason: string
  install_command: string | null
}
export type TicketResolutionState = "open" | "done" | "reopened" | "superseded"
export type TicketVerificationState = "trusted" | "suspect" | "invalidated" | "reverified" | "smoke_verified"
export type ArtifactVerdict = "PASS" | "FAIL" | "REJECT" | "APPROVED" | "BLOCKED"
export type ArtifactVerdictInspection = {
  verdict: ArtifactVerdict | null
  verdict_unclear: boolean
  matched_line: string | null
}
export type ArtifactTrustState = "current" | "superseded" | "invalidated"
export type DefectOutcome = "no_action" | "follow_up" | "invalidates_done" | "rollback_required"
export type TicketSourceMode = "process_verification" | "post_completion_issue" | "net_new_scope" | "split_scope"
export type SplitKind = "parallel_independent" | "sequential_dependent"
export type RepairFollowOnOutcome = "managed_blocked" | "source_follow_up" | "clean"

export type Artifact = {
  kind: string
  path: string
  stage: string
  summary?: string
  created_at: string
  trust_state: ArtifactTrustState
  superseded_at?: string
  superseded_by?: string
  supersession_reason?: string
}

export type ArtifactRegistryEntry = Artifact & { ticket_id: string }

export type Ticket = {
  id: string
  title: string
  wave: number
  lane: string
  parallel_safe: boolean
  overlap_risk: OverlapRisk
  stage: string
  status: string
  depends_on: string[]
  summary: string
  acceptance: string[]
  decision_blockers: string[]
  artifacts: Artifact[]
  resolution_state: TicketResolutionState
  verification_state: TicketVerificationState
  finding_source?: string
  source_ticket_id?: string
  follow_up_ticket_ids: string[]
  source_mode?: TicketSourceMode
  split_kind?: SplitKind
}

export type Manifest = {
  version: number
  project: string
  active_ticket: string
  tickets: Ticket[]
}

export type TicketWorkflowState = {
  approved_plan: boolean
  reopen_count: number
  needs_reverification: boolean
}

export type BootstrapState = {
  status: BootstrapStatus
  last_verified_at: string | null
  environment_fingerprint: string | null
  proof_artifact: string | null
}

export type LaneLease = {
  ticket_id: string
  lane: string
  owner_agent: string
  write_lock: boolean
  claimed_at: string
  expires_at: string
  allowed_paths: string[]
}

export type RepairFollowOnState = {
  outcome: RepairFollowOnOutcome
  required_stages: string[]
  completed_stages: string[]
  blocking_reasons: string[]
  verification_passed: boolean
  handoff_allowed: boolean
  last_updated_at: string | null
  process_version: number
  // Explicit list of ticket IDs the repair cycle has authorised for lifecycle
  // progression while managed_blocked is active.  Populated by the repair
  // script from REMED ticket IDs and their source_ticket_id values.
  allowed_follow_on_tickets?: string[]
}

export type PivotDownstreamStageState = {
  stage: string
  owner: string
  category: string
  reason: string
  status: "required_not_run" | "completed"
  completion_mode: string | null
  evidence_paths: string[]
  completed_by?: string | null
  summary?: string | null
  last_updated_at?: string | null
}

export type PivotDownstreamRefreshState = {
  tracking_mode: string
  pivot_id: string
  required_stages: string[]
  pending_stages: string[]
  completed_stages: string[]
  stage_records: Record<string, PivotDownstreamStageState>
}

export type PivotRestartSurfaceInputs = {
  pivot_in_progress: boolean
  pivot_class: string | null
  pivot_changed_surfaces: string[]
  pending_downstream_stages: string[]
  completed_downstream_stages: string[]
  pending_ticket_lineage_actions: string[]
  completed_ticket_lineage_actions: string[]
  post_pivot_verification_passed: boolean
}

export type PivotState = {
  pivot_id: string | null
  pivot_class: string | null
  requested_change: string | null
  pivot_state_path: string | null
  pivot_state_owner: string | null
  downstream_refresh_state: PivotDownstreamRefreshState | null
  restart_surface_inputs: PivotRestartSurfaceInputs
}

export type WorkflowState = {
  active_ticket: string
  stage: string
  status: string
  approved_plan: boolean
  bootstrap_blockers: BootstrapBlocker[]
  ticket_state: Record<string, TicketWorkflowState>
  process_version: number
  process_last_changed_at: string | null
  process_last_change_summary: string | null
  pending_process_verification: boolean
  parallel_mode: ParallelMode
  repair_follow_on: RepairFollowOnState
  bootstrap: BootstrapState
  lane_leases: LaneLease[]
  state_revision: number
}

export type ArtifactRegistry = { version: number; artifacts: ArtifactRegistryEntry[] }
export type ArtifactPathMismatchClass = "repo_absolute" | "out_of_repo" | "history_path" | "non_canonical"

export type InvocationEvent = {
  event: string
  timestamp: string
  session_id?: string
  message_id?: string
  agent?: string
  tool?: string
  command?: string
  scope?: string
  skill_id?: string
  note?: string
  args?: unknown
  metadata?: unknown
}

type StartHereOptions = { nextAction?: string; backlogVerifierAgent?: string; handoffStatus?: string }
type SaveDerivedSurfaceOptions = { refreshDerivedSurfaces?: boolean }
type SaveValidationContext = { manifest?: Manifest; workflow?: WorkflowState; skipGraphValidation?: boolean }
type RestartSurfaceRenderInputs = {
  manifest?: Manifest
  workflow?: WorkflowState
  pivot?: PivotState
  root?: string
  contextNote?: string
  nextAction?: string
  handoffStatus?: string
}
export type ProcessVerificationState = {
  pending: boolean
  affected_done_tickets: Ticket[]
  current_ticket_requires_verification: boolean
  clearable_now: boolean
  done_but_not_fully_trusted: Ticket[]
}
export type WorkflowBlocker = {
  type: "BLOCKER"
  reason_code: string
  explanation: string
  next_action_tool: string
  next_action_args: Record<string, unknown>
}
export type NewTicketSpec = {
  id: string
  title: string
  wave: number
  lane: string
  summary: string
  acceptance: string[]
  depends_on?: string[]
  decision_blockers?: string[]
  parallel_safe?: boolean
  overlap_risk?: OverlapRisk
  finding_source?: string
  source_ticket_id?: string
  source_mode?: TicketSourceMode
  split_kind?: SplitKind
}

const TICKET_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]*$/
const DEFAULT_PROCESS_VERSION = 7
const DEFAULT_TICKET_CONTRACT_VERSION = 3
const DEFAULT_LEASE_TTL_MINUTES = 120
const DEFAULT_PIVOT_STATE_OWNER = "scafforge-pivot"
const DEFAULT_BOOTSTRAP_STATE: BootstrapState = { status: "missing", last_verified_at: null, environment_fingerprint: null, proof_artifact: null }
const DEFAULT_TICKET_WORKFLOW_STATE: TicketWorkflowState = { approved_plan: false, reopen_count: 0, needs_reverification: false }
const DEFAULT_REPAIR_FOLLOW_ON_STATE = (processVersion = DEFAULT_PROCESS_VERSION): RepairFollowOnState => ({
  outcome: "clean",
  required_stages: [],
  completed_stages: [],
  blocking_reasons: [],
  verification_passed: true,
  handoff_allowed: true,
  last_updated_at: null,
  process_version: processVersion,
  allowed_follow_on_tickets: [],
})

export const COARSE_STATUSES = new Set(["todo", "ready", "plan_review", "in_progress", "blocked", "review", "qa", "smoke_test", "done"])
export const LIFECYCLE_STAGES = new Set(["planning", "plan_review", "implementation", "review", "qa", "smoke-test", "closeout"])
export const STAGE_DEFAULT_STATUS: Record<string, string> = {
  planning: "ready",
  plan_review: "plan_review",
  implementation: "in_progress",
  review: "review",
  qa: "qa",
  "smoke-test": "smoke_test",
  closeout: "done",
}
export const STATUS_STAGE_EQUIVALENTS: Record<string, string> = {
  todo: "planning",
  plan_review: "plan_review",
  in_progress: "implementation",
  review: "review",
  qa: "qa",
  smoke_test: "smoke-test",
  done: "closeout",
}
export const STAGE_ALLOWED_STATUSES: Record<string, Set<string>> = {
  planning: new Set(["todo", "ready", "blocked"]),
  plan_review: new Set(["plan_review", "blocked"]),
  implementation: new Set(["in_progress", "blocked"]),
  review: new Set(["review", "blocked"]),
  qa: new Set(["qa", "blocked"]),
  "smoke-test": new Set(["smoke_test", "blocked"]),
  closeout: new Set(["done"]),
}
export const ARTIFACT_REGISTRY_ROOT = ".opencode/state/artifacts"
export const ARTIFACT_HISTORY_ROOT = `${ARTIFACT_REGISTRY_ROOT}/history`
export const LEGACY_REVIEW_STAGES = new Set(["code_review", "security_review"])
export const START_HERE_MANAGED_START = "<!-- SCAFFORGE:START_HERE_BLOCK START -->"
export const START_HERE_MANAGED_END = "<!-- SCAFFORGE:START_HERE_BLOCK END -->"
export const DEFAULT_OVERLAP_RISK: OverlapRisk = "high"
export const DEFAULT_PARALLEL_MODE: ParallelMode = "sequential"
export const MIN_EXECUTION_ARTIFACT_BYTES = 200

export function repoVenvExecutableCandidates(root: string, executable: string): string[] {
  const names = executable.toLowerCase().endsWith(".exe") ? [executable] : [executable, `${executable}.exe`]
  const dirs =
    process.platform === "win32"
      ? [join(root, ".venv", "Scripts"), join(root, ".venv", "bin")]
      : [join(root, ".venv", "bin"), join(root, ".venv", "Scripts")]
  const candidates: string[] = []
  for (const dir of dirs) {
    for (const name of names) {
      const candidate = join(dir, name)
      if (!candidates.includes(candidate)) {
        candidates.push(candidate)
      }
    }
  }
  return candidates
}

export function repoVenvExecutable(root: string, executable: string): string {
  return repoVenvExecutableCandidates(root, executable)[0]
}

export async function findExistingRepoVenvExecutable(root: string, executable: string): Promise<string | null> {
  for (const candidate of repoVenvExecutableCandidates(root, executable)) {
    try {
      await stat(candidate)
      return candidate
    } catch {
      continue
    }
  }
  return null
}

const EXECUTION_EVIDENCE_PATTERNS = [
  /```(?:bash|sh|shell|console|text)?[\s\S]*?(?:npm|pnpm|yarn|bun|pytest|cargo|go test|go vet|python(?:3)? -m|node(?:\s|$)|tsc(?:\s|$)|make(?:\s|$)|exit code|passed|failed)/i,
  /(?:^|\n)(?:\$ |>|command: ).*(?:npm|pnpm|yarn|bun|pytest|cargo|go test|go vet|python(?:3)? -m|node|tsc|make)/i,
  /\b(?:exit[_ -]?code|pass(?:ed)?|fail(?:ed)?|ok)\b/i,
]
const INSPECTION_ONLY_PATTERNS = [/code inspection/i, /inspection only/i]

export function rootPath(): string { return process.cwd() }
export function normalizeRepoPath(pathValue: string): string { return pathValue.replace(/\\/g, "/").replace(/^\.\//, "").replace(/\/+/g, "/") }
function addMinutes(isoTimestamp: string, minutes: number): string {
  return new Date(Date.parse(isoTimestamp) + minutes * 60_000).toISOString()
}
function normalizeStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  const seen = new Set<string>()
  const normalized: string[] = []
  for (const item of value) {
    if (typeof item !== "string") continue
    const trimmed = item.trim()
    if (!trimmed || seen.has(trimmed)) continue
    seen.add(trimmed)
    normalized.push(trimmed)
  }
  return normalized
}
function normalizeBootstrapBlockers(value: unknown): BootstrapBlocker[] {
  if (!Array.isArray(value)) return []
  const blockers: BootstrapBlocker[] = []
  for (const item of value) {
    if (!item || typeof item !== "object" || Array.isArray(item)) continue
    const record = item as Record<string, unknown>
    const executable = normalizeNullableString(record.executable)
    const reason = normalizeNullableString(record.reason)
    if (!executable || !reason) continue
    blockers.push({
      executable,
      reason,
      install_command: normalizeNullableString(record.install_command),
    })
  }
  return blockers
}
function pathEscapesRepo(pathValue: string): boolean {
  return pathValue === ".." || pathValue.startsWith("../")
}
export function canonicalizeRepoPath(pathValue: string, root = rootPath()): { path: string; mismatch_class: ArtifactPathMismatchClass | null } {
  const trimmed = pathValue.trim()
  if (!trimmed) return { path: "", mismatch_class: "non_canonical" }
  if (/^[A-Za-z]:[\\/]/.test(trimmed) || trimmed.startsWith("/")) {
    const relativePath = normalizeRepoPath(relative(resolve(root), resolve(trimmed)))
    if (!relativePath || pathEscapesRepo(relativePath)) {
      return { path: normalizeRepoPath(trimmed), mismatch_class: "out_of_repo" }
    }
    if (relativePath.startsWith(`${ARTIFACT_HISTORY_ROOT}/`) || relativePath === ARTIFACT_HISTORY_ROOT) {
      return { path: relativePath, mismatch_class: "history_path" }
    }
    return { path: relativePath, mismatch_class: "repo_absolute" }
  }
  const normalized = normalizeRepoPath(trimmed)
  if (pathEscapesRepo(normalized)) return { path: normalized, mismatch_class: "out_of_repo" }
  if (normalized.startsWith(`${ARTIFACT_HISTORY_ROOT}/`) || normalized === ARTIFACT_HISTORY_ROOT) {
    return { path: normalized, mismatch_class: "history_path" }
  }
  return { path: normalized, mismatch_class: null }
}
export function describeArtifactPathMismatch(args: {
  provided_path: string
  expected_path: string
  mismatch_class: ArtifactPathMismatchClass
}): string {
  return `Artifact path mismatch: ${JSON.stringify(args)}`
}
export function ticketsManifestPath(root = rootPath()): string { return join(root, "tickets", "manifest.json") }
export function ticketsBoardPath(root = rootPath()): string { return join(root, "tickets", "BOARD.md") }
export function workflowStatePath(root = rootPath()): string { return join(root, ".opencode", "state", "workflow-state.json") }
export function artifactRegistryPath(root = rootPath()): string { return join(root, ".opencode", "state", "artifacts", "registry.json") }
export function invocationLogPath(root = rootPath()): string { return join(root, ".opencode", "state", "invocation-log.jsonl") }
export function bootstrapProvenancePath(root = rootPath()): string { return join(root, ".opencode", "meta", "bootstrap-provenance.json") }
export function contextSnapshotPath(root = rootPath()): string { return join(root, ".opencode", "state", "context-snapshot.md") }
export function latestHandoffPath(root = rootPath()): string { return join(root, ".opencode", "state", "latest-handoff.md") }
export function startHerePath(root = rootPath()): string { return join(root, "START-HERE.md") }
export function pivotStatePath(root = rootPath()): string { return join(root, ".opencode", "meta", "pivot-state.json") }
export function isValidTicketId(ticketId: string): boolean { return TICKET_ID_PATTERN.test(ticketId) }
export function assertValidTicketId(ticketId: string): string {
  if (!isValidTicketId(ticketId)) throw new Error(`Invalid ticket id: ${ticketId}. Use letters, numbers, hyphens, or underscores only.`)
  return ticketId
}
export function ticketFilePath(ticketId: string, root = rootPath()): string { return join(root, "tickets", `${assertValidTicketId(ticketId)}.md`) }
export function artifactStageDirectory(stage: string): string {
  const bucket = slugForPath(stage)
  if (bucket === "planning") return ".opencode/state/plans"
  if (bucket === "implementation") return ".opencode/state/implementations"
  if (bucket === "qa") return ".opencode/state/qa"
  if (bucket === "smoke-test") return ".opencode/state/smoke-tests"
  if (bucket === "handoff") return ".opencode/state/handoffs"
  if (bucket === "bootstrap") return ".opencode/state/bootstrap"
  if (bucket === "review" || LEGACY_REVIEW_STAGES.has(stage)) return ".opencode/state/reviews"
  return ".opencode/state/artifacts"
}
export function slugForPath(value: string): string { return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") }
export function isValidLifecycleStage(stage: string): boolean { return LIFECYCLE_STAGES.has(stage) }
export function stageAllowsStatus(stage: string, status: string): boolean {
  const allowed = STAGE_ALLOWED_STATUSES[stage]
  return Boolean(allowed && allowed.has(status))
}
export function describeAllowedStatusesForStage(stage: string): string {
  const allowed = STAGE_ALLOWED_STATUSES[stage]
  return allowed ? [...allowed].join(", ") : ""
}
export function stageForStatus(status: string, currentStage?: string): string {
  return STATUS_STAGE_EQUIVALENTS[status] || currentStage || "planning"
}
export function defaultStatusForStage(stage: string, currentStatus?: string): string {
  if (stage === "planning" && currentStatus && stageAllowsStatus(stage, currentStatus)) {
    return currentStatus
  }
  return STAGE_DEFAULT_STATUS[stage] || currentStatus || "ready"
}
export function resolveRequestedTicketProgress(ticket: Ticket, args: { stage?: string; status?: string }): { stage: string; status: string } {
  const requestedStage = typeof args.stage === "string" && args.stage.trim() ? args.stage.trim() : undefined
  const requestedStatus = typeof args.status === "string" && args.status.trim() ? args.status.trim() : undefined
  const stage = requestedStage || (requestedStatus ? stageForStatus(requestedStatus, ticket.stage) : ticket.stage)
  const status = requestedStatus || defaultStatusForStage(stage, ticket.status)
  return { stage, status }
}
export function validateLifecycleStageStatus(stage: string, status: string): string | null {
  if (!isValidLifecycleStage(stage)) {
    return `Unsupported ticket stage: ${stage}. Use planning, plan_review, implementation, review, qa, smoke-test, or closeout.`
  }
  if (!COARSE_STATUSES.has(status)) {
    return `Unsupported ticket status: ${status}`
  }
  if (!stageAllowsStatus(stage, status)) {
    return `Status ${status} is not valid for stage ${stage}. Allowed statuses: ${describeAllowedStatusesForStage(stage)}.`
  }
  return null
}
export function defaultArtifactPath(ticketId: string, stage: string, kind: string): string { return `${artifactStageDirectory(stage)}/${slugForPath(ticketId)}-${slugForPath(stage)}-${slugForPath(kind)}.md` }
export function defaultBootstrapProofPath(ticketId: string): string { return defaultArtifactPath(ticketId, "bootstrap", "environment-bootstrap") }

export async function readJson<T>(path: string, fallback?: T): Promise<T> {
  try { return JSON.parse(await readFile(path, "utf-8")) as T } catch (error) { if (fallback !== undefined) return fallback; throw error }
}
async function readText(path: string, fallback = ""): Promise<string> { try { return await readFile(path, "utf-8") } catch { return fallback } }
export async function writeJson(path: string, value: unknown): Promise<void> { await mkdir(dirname(path), { recursive: true }); await writeFile(path, `${JSON.stringify(value, null, 2)}\n`, "utf-8") }
export async function appendJsonl(path: string, value: unknown): Promise<void> { await mkdir(dirname(path), { recursive: true }); await appendFile(path, `${JSON.stringify(value)}\n`, "utf-8") }
export async function writeText(path: string, value: string): Promise<void> { await mkdir(dirname(path), { recursive: true }); await writeFile(path, value, "utf-8") }
// Canonical bootstrap-first examples:
// - tickets/manifest.json not found. Run bootstrap first.
// - .opencode/state/workflow-state.json not found. Run bootstrap first.
export async function ensureRequiredFile(path: string, label: string): Promise<void> {
  try {
    await stat(path)
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      throw new Error(`${label} not found. Run bootstrap first.`)
    }
    throw error
  }
}
export function formatWorkflowBlocker(blocker: WorkflowBlocker): string { return `BLOCKER ${JSON.stringify(blocker)}` }
export function throwWorkflowBlocker(blocker: WorkflowBlocker): never { throw new Error(formatWorkflowBlocker(blocker)) }
export function ticketClaimBlockerArgs(ticketId: string, allowedPaths: string[] = []): Record<string, unknown> {
  const args: Record<string, unknown> = { ticket_id: ticketId, owner_agent: "<team-leader-agent>", write_lock: true }
  if (allowedPaths.length > 0) args.allowed_paths = allowedPaths
  return args
}

function expectObject(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(`${label} must be an object.`)
  return value as Record<string, unknown>
}
function expectNonEmptyString(record: Record<string, unknown>, key: string, label: string): string {
  const value = record[key]
  if (typeof value !== "string" || !value.trim()) throw new Error(`${label} is missing required field: ${key}`)
  return value.trim()
}
function expectStringArray(record: Record<string, unknown>, key: string, label: string): string[] {
  const value = record[key]
  if (!Array.isArray(value)) throw new Error(`${label} is missing required list field: ${key}`)
  return value.map((item, index) => {
    if (typeof item !== "string" || !item.trim()) throw new Error(`${label}.${key}[${index}] must be a non-empty string`)
    return item.trim()
  })
}
function normalizeNullableString(value: unknown): string | null { if (typeof value !== "string") return null; return value.trim() || null }
function normalizeOverlapRisk(value: unknown): OverlapRisk { return value === "low" || value === "medium" || value === "high" ? value : DEFAULT_OVERLAP_RISK }
function normalizeParallelMode(value: unknown): ParallelMode { return value === "parallel-lanes" || value === "sequential" ? value : DEFAULT_PARALLEL_MODE }
function normalizeResolutionState(value: unknown, status: string): TicketResolutionState { return value === "open" || value === "done" || value === "reopened" || value === "superseded" ? value : status === "done" ? "done" : "open" }
function normalizeVerificationState(value: unknown, status: string): TicketVerificationState {
  return value === "trusted" || value === "suspect" || value === "invalidated" || value === "reverified" || value === "smoke_verified"
    ? value
    : status === "done"
      ? "trusted"
      : "suspect"
}
function normalizeArtifactTrustState(value: unknown): ArtifactTrustState { return value === "superseded" || value === "invalidated" ? value : "current" }
function normalizeTicketWorkflowState(value: unknown): TicketWorkflowState {
  if (!value || typeof value !== "object" || Array.isArray(value)) return { ...DEFAULT_TICKET_WORKFLOW_STATE }
  const state = value as Record<string, unknown>
  return {
    approved_plan: typeof state.approved_plan === "boolean" ? state.approved_plan : false,
    reopen_count: typeof state.reopen_count === "number" && state.reopen_count >= 0 ? Math.floor(state.reopen_count) : 0,
    needs_reverification: typeof state.needs_reverification === "boolean" ? state.needs_reverification : false,
  }
}
function normalizeTicketStateMap(value: unknown): Record<string, TicketWorkflowState> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {}
  const normalized: Record<string, TicketWorkflowState> = {}
  for (const [ticketId, rawState] of Object.entries(value as Record<string, unknown>)) if (isValidTicketId(ticketId)) normalized[ticketId] = normalizeTicketWorkflowState(rawState)
  return normalized
}
function normalizeLaneLease(value: unknown): LaneLease | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null
  const lease = value as Record<string, unknown>
  const ticketId = normalizeNullableString(lease.ticket_id)
  const lane = normalizeNullableString(lease.lane)
  const ownerAgent = normalizeNullableString(lease.owner_agent)
  const claimedAt = normalizeNullableString(lease.claimed_at)
  const expiresAt = normalizeNullableString(lease.expires_at)
  if (!ticketId || !isValidTicketId(ticketId) || !lane || !ownerAgent || !claimedAt) return null
  return {
    ticket_id: ticketId,
    lane,
    owner_agent: ownerAgent,
    write_lock: lease.write_lock !== false,
    claimed_at: claimedAt,
    expires_at: expiresAt || addMinutes(claimedAt, DEFAULT_LEASE_TTL_MINUTES),
    allowed_paths: normalizeStringArray(lease.allowed_paths).map(normalizeRepoPath),
  }
}
function normalizeLaneLeases(value: unknown): LaneLease[] {
  if (!Array.isArray(value)) return []
  return value.flatMap((lease) => {
    const normalized = normalizeLaneLease(lease)
    return normalized ? [normalized] : []
  })
}
function normalizeArtifact(value: unknown, index: number): Artifact {
  const artifact = expectObject(value, `ticket.artifacts[${index}]`)
  return {
    kind: expectNonEmptyString(artifact, "kind", `ticket.artifacts[${index}]`),
    path: normalizeRepoPath(expectNonEmptyString(artifact, "path", `ticket.artifacts[${index}]`)),
    stage: expectNonEmptyString(artifact, "stage", `ticket.artifacts[${index}]`),
    summary: normalizeNullableString(artifact.summary) ?? undefined,
    created_at: expectNonEmptyString(artifact, "created_at", `ticket.artifacts[${index}]`),
    trust_state: normalizeArtifactTrustState(artifact.trust_state),
    superseded_at: normalizeNullableString(artifact.superseded_at) ?? undefined,
    superseded_by: normalizeNullableString(artifact.superseded_by) ?? undefined,
    supersession_reason: normalizeNullableString(artifact.supersession_reason) ?? undefined,
  }
}
function migrateTicket(raw: unknown): Ticket {
  const ticket = expectObject(raw, "Ticket")
  const id = assertValidTicketId(expectNonEmptyString(ticket, "id", "Ticket"))
  const status = expectNonEmptyString(ticket, "status", `Ticket ${id}`)
  return {
    id,
    title: expectNonEmptyString(ticket, "title", `Ticket ${id}`),
    wave: typeof ticket.wave === "number" && Number.isInteger(ticket.wave) && ticket.wave >= 0 ? ticket.wave : 0,
    lane: expectNonEmptyString(ticket, "lane", `Ticket ${id}`),
    parallel_safe: typeof ticket.parallel_safe === "boolean" ? ticket.parallel_safe : false,
    overlap_risk: normalizeOverlapRisk(ticket.overlap_risk),
    stage: expectNonEmptyString(ticket, "stage", `Ticket ${id}`),
    status,
    depends_on: expectStringArray(ticket, "depends_on", `Ticket ${id}`),
    summary: expectNonEmptyString(ticket, "summary", `Ticket ${id}`),
    acceptance: expectStringArray(ticket, "acceptance", `Ticket ${id}`),
    decision_blockers: normalizeStringArray(ticket.decision_blockers),
    artifacts: Array.isArray(ticket.artifacts) ? ticket.artifacts.map((artifact, index) => normalizeArtifact(artifact, index)) : [],
    resolution_state: normalizeResolutionState(ticket.resolution_state, status),
    verification_state: normalizeVerificationState(ticket.verification_state, status),
    finding_source: normalizeNullableString(ticket.finding_source) ?? undefined,
    source_ticket_id: normalizeNullableString(ticket.source_ticket_id) ?? undefined,
    follow_up_ticket_ids: normalizeStringArray(ticket.follow_up_ticket_ids),
    source_mode:
      ticket.source_mode === "process_verification"
      || ticket.source_mode === "post_completion_issue"
      || ticket.source_mode === "net_new_scope"
      || ticket.source_mode === "split_scope"
        ? ticket.source_mode
        : undefined,
    split_kind:
      ticket.split_kind === "parallel_independent" || ticket.split_kind === "sequential_dependent"
        ? ticket.split_kind
        : undefined,
  }
}

function normalizeRepairFollowOnOutcome(value: unknown): RepairFollowOnOutcome | null {
  if (value === "managed_blocked" || value === "source_follow_up" || value === "clean") return value
  return null
}

function normalizePivotDownstreamStageState(stage: string, value: unknown): PivotDownstreamStageState | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null
  const record = value as Record<string, unknown>
  const normalizedStage = typeof record.stage === "string" && record.stage.trim() ? record.stage.trim() : stage
  const status = record.status === "completed" ? "completed" : "required_not_run"
  return {
    stage: normalizedStage,
    owner: typeof record.owner === "string" && record.owner.trim() ? record.owner.trim() : normalizedStage,
    category: typeof record.category === "string" && record.category.trim() ? record.category.trim() : "unknown",
    reason: typeof record.reason === "string" && record.reason.trim() ? record.reason.trim() : "",
    status,
    completion_mode: typeof record.completion_mode === "string" && record.completion_mode.trim() ? record.completion_mode.trim() : null,
    evidence_paths: normalizeStringArray(record.evidence_paths),
    completed_by: normalizeNullableString(record.completed_by),
    summary: normalizeNullableString(record.summary),
    last_updated_at: normalizeNullableString(record.last_updated_at),
  }
}

function computePivotInProgress(restartInputsRaw: Record<string, unknown> | undefined, downstreamRaw: Record<string, unknown> | undefined): boolean {
  if (!restartInputsRaw) return false
  const explicit = restartInputsRaw.pivot_in_progress
  if (typeof explicit === "boolean") {
    const pendingStages = normalizeStringArray(restartInputsRaw.pending_downstream_stages)
    const pendingLineage = normalizeStringArray(restartInputsRaw.pending_ticket_lineage_actions)
    if (pendingStages.length === 0 && pendingLineage.length === 0) {
      return false
    }
    return explicit
  }
  return false
}

function normalizePivotState(value: unknown): PivotState {
  const fallbackRestartSurfaceInputs: PivotRestartSurfaceInputs = {
    pivot_in_progress: false,
    pivot_class: null,
    pivot_changed_surfaces: [],
    pending_downstream_stages: [],
    completed_downstream_stages: [],
    pending_ticket_lineage_actions: [],
    completed_ticket_lineage_actions: [],
    post_pivot_verification_passed: false,
  }
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return {
      pivot_id: null,
      pivot_class: null,
      requested_change: null,
      pivot_state_path: null,
      pivot_state_owner: DEFAULT_PIVOT_STATE_OWNER,
      downstream_refresh_state: null,
      restart_surface_inputs: fallbackRestartSurfaceInputs,
    }
  }
  const state = value as Record<string, unknown>
  const restartInputsRaw = state.restart_surface_inputs as Record<string, unknown> | undefined
  const downstreamRaw = state.downstream_refresh_state as Record<string, unknown> | undefined
  const stageRecordsRaw = downstreamRaw?.stage_records
  const stageRecords: Record<string, PivotDownstreamStageState> = {}
  if (stageRecordsRaw && typeof stageRecordsRaw === "object" && !Array.isArray(stageRecordsRaw)) {
    for (const [stage, rawValue] of Object.entries(stageRecordsRaw)) {
      const normalized = normalizePivotDownstreamStageState(stage, rawValue)
      if (normalized) stageRecords[stage] = normalized
    }
  }
  const completedStages = normalizeStringArray(downstreamRaw?.completed_stages)
  const requiredStages = normalizeStringArray(downstreamRaw?.required_stages)
  const pendingStages = normalizeStringArray(downstreamRaw?.pending_stages)
  return {
    pivot_id: normalizeNullableString(state.pivot_id),
    pivot_class: normalizeNullableString(state.pivot_class),
    requested_change: normalizeNullableString(state.requested_change),
    pivot_state_path: normalizeNullableString(state.pivot_state_path),
    pivot_state_owner: normalizeNullableString(state.pivot_state_owner) || DEFAULT_PIVOT_STATE_OWNER,
    downstream_refresh_state: downstreamRaw
      ? {
          tracking_mode: typeof downstreamRaw.tracking_mode === "string" && downstreamRaw.tracking_mode.trim() ? downstreamRaw.tracking_mode.trim() : "persistent_recorded_state",
          pivot_id: typeof downstreamRaw.pivot_id === "string" && downstreamRaw.pivot_id.trim() ? downstreamRaw.pivot_id.trim() : "",
          required_stages: requiredStages,
          pending_stages: pendingStages,
          completed_stages: completedStages,
          stage_records: stageRecords,
        }
      : null,
    restart_surface_inputs: {
      pivot_in_progress: computePivotInProgress(restartInputsRaw, downstreamRaw),
      pivot_class: typeof restartInputsRaw?.pivot_class === "string" && restartInputsRaw.pivot_class.trim() ? restartInputsRaw.pivot_class.trim() : null,
      pivot_changed_surfaces: normalizeStringArray(restartInputsRaw?.pivot_changed_surfaces),
      pending_downstream_stages: normalizeStringArray(restartInputsRaw?.pending_downstream_stages),
      completed_downstream_stages: normalizeStringArray(restartInputsRaw?.completed_downstream_stages),
      pending_ticket_lineage_actions: normalizeStringArray(restartInputsRaw?.pending_ticket_lineage_actions),
      completed_ticket_lineage_actions: normalizeStringArray(restartInputsRaw?.completed_ticket_lineage_actions),
      post_pivot_verification_passed: restartInputsRaw?.post_pivot_verification_passed === true,
    },
  }
}

export async function loadPivotState(root = rootPath()): Promise<PivotState> {
  return normalizePivotState(await readJson<unknown>(pivotStatePath(root), null))
}

function inferLegacyRepairFollowOnOutcome(
  raw: Record<string, unknown> | undefined,
  defaults: RepairFollowOnState,
): RepairFollowOnOutcome {
  if (!raw) return defaults.outcome
  const requiredStages = normalizeStringArray(raw.required_stages)
  const blockingReasons = normalizeStringArray(raw.blocking_reasons)
  const verificationPassed = raw.verification_passed === true
  const handoffAllowed = raw.handoff_allowed === true
  return handoffAllowed && requiredStages.length === 0 && blockingReasons.length === 0 && verificationPassed ? "clean" : "managed_blocked"
}

export async function loadManifest(root = rootPath()): Promise<Manifest> {
  await ensureRequiredFile(ticketsManifestPath(root), "tickets/manifest.json")
  const manifest = expectObject(await readJson<unknown>(ticketsManifestPath(root)), "Manifest")
  if (!Array.isArray(manifest.tickets)) throw new Error("tickets/manifest.json is missing a tickets array.")
  return {
    version: typeof manifest.version === "number" && manifest.version >= DEFAULT_TICKET_CONTRACT_VERSION ? manifest.version : DEFAULT_TICKET_CONTRACT_VERSION,
    project: typeof manifest.project === "string" && manifest.project.trim() ? manifest.project.trim() : "UNKNOWN",
    active_ticket: typeof manifest.active_ticket === "string" && manifest.active_ticket.trim() ? manifest.active_ticket.trim() : "UNKNOWN",
    tickets: manifest.tickets.map((ticket) => migrateTicket(ticket)),
  }
}
export async function readManifest(root = rootPath()): Promise<Manifest> {
  return loadManifest(root)
}
export async function loadArtifactRegistry(root = rootPath()): Promise<ArtifactRegistry> { return readJson<ArtifactRegistry>(artifactRegistryPath(root), { version: 2, artifacts: [] }) }
export async function loadWorkflowState(root = rootPath()): Promise<WorkflowState> {
  await ensureRequiredFile(workflowStatePath(root), ".opencode/state/workflow-state.json")
  const fallback: WorkflowState = {
    active_ticket: "UNKNOWN", stage: "planning", status: "todo", approved_plan: false, bootstrap_blockers: [], ticket_state: {}, process_version: DEFAULT_PROCESS_VERSION,
    process_last_changed_at: null, process_last_change_summary: null, pending_process_verification: false, parallel_mode: DEFAULT_PARALLEL_MODE,
    repair_follow_on: DEFAULT_REPAIR_FOLLOW_ON_STATE(),
    bootstrap: { ...DEFAULT_BOOTSTRAP_STATE }, lane_leases: [], state_revision: 0,
  }
  const loaded = await readJson<unknown>(workflowStatePath(root), fallback)
  if (!loaded || typeof loaded !== "object" || Array.isArray(loaded)) return fallback
  const state = loaded as Record<string, unknown>
  const activeTicket = typeof state.active_ticket === "string" && state.active_ticket.trim() ? state.active_ticket.trim() : fallback.active_ticket
  const ticketState = normalizeTicketStateMap(state.ticket_state)
  const legacyApprovedPlan = typeof state.approved_plan === "boolean" ? state.approved_plan : false
  if (isValidTicketId(activeTicket) && !ticketState[activeTicket]) ticketState[activeTicket] = { ...DEFAULT_TICKET_WORKFLOW_STATE, approved_plan: legacyApprovedPlan }
  const processVersion = typeof state.process_version === "number" && state.process_version > 0 ? state.process_version : DEFAULT_PROCESS_VERSION
  const repairFollowOnRaw = state.repair_follow_on
  const repairFollowOnDefaults = DEFAULT_REPAIR_FOLLOW_ON_STATE(processVersion)
  const repairFollowOnRecord = repairFollowOnRaw as Record<string, unknown> | undefined
  const repairFollowOnProcessVersion = typeof repairFollowOnRecord?.process_version === "number" && repairFollowOnRecord.process_version > 0
    ? Math.floor(repairFollowOnRecord.process_version)
    : processVersion
  const repairFollowOn = repairFollowOnRaw && typeof repairFollowOnRaw === "object" && !Array.isArray(repairFollowOnRaw)
    ? {
        outcome: normalizeRepairFollowOnOutcome(repairFollowOnRecord?.outcome) ?? inferLegacyRepairFollowOnOutcome(repairFollowOnRecord, repairFollowOnDefaults),
        required_stages: normalizeStringArray(repairFollowOnRecord?.required_stages),
        completed_stages: normalizeStringArray(repairFollowOnRecord?.completed_stages),
        blocking_reasons: normalizeStringArray(repairFollowOnRecord?.blocking_reasons),
        verification_passed: repairFollowOnRecord?.verification_passed === true,
        handoff_allowed: repairFollowOnRecord?.handoff_allowed === true,
        last_updated_at: normalizeNullableString(repairFollowOnRecord?.last_updated_at),
        process_version: repairFollowOnProcessVersion,
      }
    : repairFollowOnDefaults
  const workflow: WorkflowState = {
    active_ticket: activeTicket,
    stage: typeof state.stage === "string" && state.stage.trim() ? state.stage.trim() : fallback.stage,
    status: typeof state.status === "string" && state.status.trim() ? state.status.trim() : fallback.status,
    approved_plan: ticketState[activeTicket]?.approved_plan ?? legacyApprovedPlan,
    bootstrap_blockers: normalizeBootstrapBlockers(state.bootstrap_blockers),
    ticket_state: ticketState,
    process_version: processVersion,
    process_last_changed_at: normalizeNullableString(state.process_last_changed_at),
    process_last_change_summary: normalizeNullableString(state.process_last_change_summary),
    pending_process_verification: state.pending_process_verification === true,
    parallel_mode: normalizeParallelMode(state.parallel_mode),
    repair_follow_on: repairFollowOn,
    bootstrap: state.bootstrap && typeof state.bootstrap === "object" && !Array.isArray(state.bootstrap)
      ? {
          status: (state.bootstrap as Record<string, unknown>).status === "ready" || (state.bootstrap as Record<string, unknown>).status === "stale" || (state.bootstrap as Record<string, unknown>).status === "failed" ? ((state.bootstrap as Record<string, unknown>).status as BootstrapStatus) : "missing",
          last_verified_at: normalizeNullableString((state.bootstrap as Record<string, unknown>).last_verified_at),
          environment_fingerprint: normalizeNullableString((state.bootstrap as Record<string, unknown>).environment_fingerprint),
          proof_artifact: normalizeNullableString((state.bootstrap as Record<string, unknown>).proof_artifact),
        }
      : { ...DEFAULT_BOOTSTRAP_STATE },
    lane_leases: normalizeLaneLeases(state.lane_leases),
    state_revision: typeof state.state_revision === "number" && state.state_revision >= 0 ? Math.floor(state.state_revision) : 0,
  }
  pruneExpiredLeases(workflow)
  workflow.bootstrap = await evaluateBootstrapState(workflow.bootstrap, root)
  return workflow
}
export async function readWorkflowState(root = rootPath()): Promise<WorkflowState> {
  return loadWorkflowState(root)
}
export async function saveWorkflowState(state: WorkflowState, root = rootPath(), expectedRevision?: number, options: SaveDerivedSurfaceOptions = {}, validationContext: SaveValidationContext = {}): Promise<void> {
  await validateWorkflowWriteState(state, root, validationContext)
  const current = await readJson<WorkflowState>(workflowStatePath(root), { ...state, state_revision: state.state_revision })
  const currentRevision = typeof current.state_revision === "number" ? current.state_revision : 0
  const expected = expectedRevision ?? state.state_revision
  if (expected !== currentRevision) throw new Error(`Workflow state changed concurrently. Expected revision ${expected}, found ${currentRevision}.`)
  state.state_revision = currentRevision + 1
  await writeJson(workflowStatePath(root), state)
  if (options.refreshDerivedSurfaces !== false) {
    await refreshRestartSurfaces({ workflow: state, root })
  }
}
export async function writeWorkflowState(state: WorkflowState, root = rootPath(), expectedRevision?: number, options: SaveDerivedSurfaceOptions = {}): Promise<void> {
  await saveWorkflowState(state, root, expectedRevision, options)
}
function ensureTicketWorkflowState(workflow: WorkflowState, ticketId: string): TicketWorkflowState {
  if (!workflow.ticket_state[ticketId]) workflow.ticket_state[ticketId] = { ...DEFAULT_TICKET_WORKFLOW_STATE }
  return workflow.ticket_state[ticketId]
}
export function getTicket(manifest: Manifest, ticketId?: string): Ticket {
  const resolvedId = ticketId || manifest.active_ticket
  const ticket = manifest.tickets.find((item) => item.id === resolvedId)
  if (!ticket) throw new Error(`Ticket not found: ${resolvedId}`)
  return ticket
}
export function isPlanApprovedForTicket(workflow: WorkflowState, ticketId: string): boolean { return ensureTicketWorkflowState(workflow, ticketId).approved_plan }
export function setPlanApprovedForTicket(workflow: WorkflowState, ticketId: string, approved: boolean): void { ensureTicketWorkflowState(workflow, ticketId).approved_plan = approved }
export function getTicketWorkflowState(workflow: WorkflowState, ticketId: string): TicketWorkflowState { return ensureTicketWorkflowState(workflow, ticketId) }
export function syncWorkflowSelection(workflow: WorkflowState, manifest: Manifest): void {
  const activeTicket = getTicket(manifest, manifest.active_ticket)
  ensureTicketWorkflowState(workflow, activeTicket.id)
  workflow.active_ticket = activeTicket.id
  workflow.stage = activeTicket.stage
  workflow.status = activeTicket.status
  workflow.approved_plan = isPlanApprovedForTicket(workflow, activeTicket.id)
}

function validateTicketLifecycleConsistency(ticket: Ticket): void {
  const lifecycleBlocker = validateLifecycleStageStatus(ticket.stage, ticket.status)
  if (lifecycleBlocker) {
    throw new Error(`Ticket ${ticket.id} has an invalid lifecycle combination: ${lifecycleBlocker}`)
  }
  if (ticket.status === "done") {
    if (ticket.stage !== "closeout") {
      throw new Error(`Ticket ${ticket.id} is done but still at stage ${ticket.stage}. Done tickets must be at closeout.`)
    }
    if (ticket.resolution_state !== "done" && ticket.resolution_state !== "superseded") {
      throw new Error(`Ticket ${ticket.id} is done but has resolution_state ${ticket.resolution_state}.`)
    }
  }
  if (ticket.status !== "done" && (ticket.resolution_state === "done" || ticket.resolution_state === "superseded")) {
    throw new Error(`Ticket ${ticket.id} cannot use resolution_state ${ticket.resolution_state} while status is ${ticket.status}.`)
  }
}

function validateTicketGraphInvariants(manifest: Manifest): void {
  const ticketsById = new Map<string, Ticket>()
  for (const ticket of manifest.tickets) {
    if (ticketsById.has(ticket.id)) {
      throw new Error(`Duplicate ticket ID detected: ${ticket.id}`)
    }
    ticketsById.set(ticket.id, ticket)
  }
  for (const ticket of manifest.tickets) {
    validateTicketLifecycleConsistency(ticket)
    const dependsOn = new Set(ticket.depends_on)
    const followUps = new Set(ticket.follow_up_ticket_ids)
    if (dependsOn.size !== ticket.depends_on.length) {
      throw new Error(`Ticket ${ticket.id} contains duplicate depends_on entries.`)
    }
    if (followUps.size !== ticket.follow_up_ticket_ids.length) {
      throw new Error(`Ticket ${ticket.id} contains duplicate follow_up_ticket_ids entries.`)
    }
    if (ticket.source_ticket_id) {
      if (ticket.source_ticket_id === ticket.id) {
        throw new Error(`Ticket ${ticket.id} cannot be its own source.`)
      }
      if (dependsOn.has(ticket.source_ticket_id)) {
        throw new Error(`Ticket ${ticket.id} cannot name ${ticket.source_ticket_id} as both source_ticket_id and depends_on.`)
      }
      const sourceTicket = ticketsById.get(ticket.source_ticket_id)
      if (!sourceTicket) {
        throw new Error(`Ticket ${ticket.id} references missing source ticket ${ticket.source_ticket_id}.`)
      }
      if (!sourceTicket.follow_up_ticket_ids.includes(ticket.id)) {
        throw new Error(`Ticket ${ticket.id} is missing symmetric follow-up linkage from ${sourceTicket.id}.`)
      }
      if (ticket.source_mode === "process_verification" && sourceTicket.status !== "done") {
        throw new Error(`Process-verification ticket ${ticket.id} must point at a done source ticket.`)
      }
      if (ticket.source_mode === "post_completion_issue" && sourceTicket.status !== "done" && sourceTicket.resolution_state !== "superseded") {
        throw new Error(`Post-completion follow-up ${ticket.id} must point at a completed historical source ticket.`)
      }
    }
    for (const followUpTicketId of followUps) {
      const followUpTicket = ticketsById.get(followUpTicketId)
      if (!followUpTicket) {
        throw new Error(`Ticket ${ticket.id} references missing follow-up ticket ${followUpTicketId}.`)
      }
      if (followUpTicket.source_ticket_id !== ticket.id) {
        throw new Error(`Ticket ${ticket.id} does not have symmetric source ownership for follow-up ticket ${followUpTicketId}.`)
      }
    }
    for (const dependencyId of dependsOn) {
      if (dependencyId === ticket.id) {
        throw new Error(`Ticket ${ticket.id} cannot depend on itself.`)
      }
      if (!ticketsById.has(dependencyId)) {
        throw new Error(`Ticket ${ticket.id} depends on missing ticket ${dependencyId}.`)
      }
    }
  }

  const visited = new Set<string>()
  const visiting = new Set<string>()
  const visit = (ticket: Ticket, trail: string[]): void => {
    if (visited.has(ticket.id)) return
    if (visiting.has(ticket.id)) {
      throw new Error(`Ticket dependency cycle detected: ${[...trail, ticket.id].join(" -> ")}`)
    }
    visiting.add(ticket.id)
    for (const dependencyId of ticket.depends_on) {
      const dependency = ticketsById.get(dependencyId)!
      visit(dependency, [...trail, ticket.id])
    }
    visiting.delete(ticket.id)
    visited.add(ticket.id)
  }
  for (const ticket of manifest.tickets) {
    visit(ticket, [])
  }
}

function validateManifestWorkflowConvergence(manifest: Manifest, workflow: WorkflowState): void {
  const activeTicket = getTicket(manifest, manifest.active_ticket)
  if (workflow.active_ticket !== activeTicket.id) {
    throw new Error(`manifest.active_ticket (${manifest.active_ticket}) does not match workflow.active_ticket (${workflow.active_ticket}).`)
  }
  if (workflow.stage !== activeTicket.stage || workflow.status !== activeTicket.status) {
    throw new Error(`Workflow selection for ${activeTicket.id} is out of sync with the manifest ticket state.`)
  }
  const activeTicketWorkflowState = workflow.ticket_state[activeTicket.id]
  if (!activeTicketWorkflowState) {
    throw new Error(`Workflow state is missing ticket_state for active ticket ${activeTicket.id}.`)
  }
  if (workflow.approved_plan !== activeTicketWorkflowState.approved_plan) {
    throw new Error(`Workflow approved_plan does not converge with the active ticket workflow state for ${activeTicket.id}.`)
  }
}

async function validateManifestWriteState(manifest: Manifest, root = rootPath(), context: SaveValidationContext = {}): Promise<void> {
  if (!context.skipGraphValidation) {
    validateTicketGraphInvariants(manifest)
  }
  const workflow = context.workflow ?? await readJson<WorkflowState | null>(workflowStatePath(root), null)
  if (workflow) {
    validateManifestWorkflowConvergence(manifest, workflow)
  }
}

async function validateWorkflowWriteState(workflow: WorkflowState, root = rootPath(), context: SaveValidationContext = {}): Promise<void> {
  const manifest = context.manifest ?? await readJson<Manifest | null>(ticketsManifestPath(root), null)
  if (manifest) {
    if (!context.skipGraphValidation) {
      validateTicketGraphInvariants(manifest)
    }
    validateManifestWorkflowConvergence(manifest, workflow)
  }
}

export function validateRestartSurfacePublication(manifest: Manifest, workflow: WorkflowState, pivot: PivotState): string | null {
  if (!pivot.pivot_state_owner || !pivot.pivot_state_owner.trim()) {
    return "Pivot state owner is missing; restart surfaces can only publish from a normalized pivot state."
  }
  const restartInputs = pivot.restart_surface_inputs
  if (!restartInputs.pivot_in_progress) {
    if (restartInputs.pivot_changed_surfaces.length > 0 && !restartInputs.post_pivot_verification_passed) {
      return "Restart surfaces can only publish from a final pivot snapshot after post-pivot verification passes."
    }
    if (restartInputs.pending_downstream_stages.length > 0) {
      return `Restart surfaces can only publish from a final pivot snapshot when no downstream stages remain pending, but pending stages remain: ${restartInputs.pending_downstream_stages.join(", ")}.`
    }
    if (restartInputs.pending_ticket_lineage_actions.length > 0) {
      return `Restart surfaces can only publish from a final pivot snapshot when no ticket lineage actions remain pending, but pending actions remain: ${restartInputs.pending_ticket_lineage_actions.join(", ")}.`
    }
  }
  const activeTicket = getTicket(manifest, manifest.active_ticket)
  if (workflow.active_ticket !== activeTicket.id) {
    return `Restart surfaces can only publish from converged active state, but manifest.active_ticket=${manifest.active_ticket} and workflow.active_ticket=${workflow.active_ticket}.`
  }
  if (workflow.stage !== activeTicket.stage || workflow.status !== activeTicket.status) {
    return `Restart surfaces can only publish from the verified post-mutation snapshot for ${activeTicket.id}.`
  }
  return null
}

type ArtifactMatcher = { kind?: string; stage?: string; trust_state?: ArtifactTrustState }
type ArtifactRegistrationSpec = { ticket: Ticket; registry: ArtifactRegistry; source_path: string; kind: string; stage: string; summary?: string }

const BOOTSTRAP_INPUT_FILES = [
  "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb",
  "pyproject.toml", "requirements.txt", "requirements-dev.txt", "poetry.lock", "Pipfile", "Pipfile.lock", "uv.lock",
  "Cargo.toml", "Cargo.lock", "go.mod", "go.sum", "Makefile", "pytest.ini", "setup.py", "setup.cfg",
]

function matchesArtifact(artifact: Artifact, options: ArtifactMatcher): boolean {
  if (options.kind && artifact.kind !== options.kind) return false
  if (options.stage && artifact.stage !== options.stage) return false
  if (options.trust_state && artifact.trust_state !== options.trust_state) return false
  return true
}

export function latestArtifact(ticket: Ticket, options: ArtifactMatcher): Artifact | undefined {
  return [...ticket.artifacts].reverse().find((artifact) => matchesArtifact(artifact, options))
}
export function currentArtifacts(ticket: Ticket, options: Omit<ArtifactMatcher, "trust_state"> = {}): Artifact[] {
  return ticket.artifacts.filter((artifact) => artifact.trust_state === "current" && matchesArtifact(artifact, options))
}
export function historicalArtifacts(ticket: Ticket, options: Omit<ArtifactMatcher, "trust_state"> = {}): Artifact[] {
  return ticket.artifacts.filter((artifact) => artifact.trust_state !== "current" && matchesArtifact(artifact, options))
}
export function currentRegistryArtifact(registry: ArtifactRegistry, artifactPath: string): ArtifactRegistryEntry | undefined {
  const normalized = normalizeRepoPath(artifactPath)
  return [...registry.artifacts].reverse().find((artifact) => artifact.path === normalized && artifact.trust_state === "current")
}
export function hasArtifact(ticket: Ticket, options: ArtifactMatcher): boolean {
  return latestArtifact(ticket, { ...options, trust_state: options.trust_state ?? "current" }) !== undefined
}
export function latestReviewArtifact(ticket: Ticket): Artifact | undefined {
  return latestArtifact(ticket, { stage: "review", trust_state: "current" }) || [...LEGACY_REVIEW_STAGES].map((stage) => latestArtifact(ticket, { stage, trust_state: "current" })).find(Boolean)
}
export function hasReviewArtifact(ticket: Ticket): boolean { return latestReviewArtifact(ticket) !== undefined }
export async function readArtifactContent(artifact: Artifact | undefined, root = rootPath()): Promise<string> {
  return artifact ? readText(join(root, normalizeRepoPath(artifact.path))) : ""
}
function normalizeArtifactVerdictToken(token: string): ArtifactVerdict | null {
  const normalized = token.trim().toUpperCase()
  if (normalized === "PASS") return "PASS"
  if (normalized === "FAIL") return "FAIL"
  if (normalized === "REJECT") return "REJECT"
  if (normalized === "APPROVED" || normalized === "APPROVE") return "APPROVED"
  if (normalized === "BLOCKED" || normalized === "BLOCKER") return "BLOCKED"
  return null
}
export function extractArtifactVerdict(content: string): ArtifactVerdictInspection {
  const lines = content.split(/\r?\n/)
  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim()
    if (!trimmed) continue
    const labeled = trimmed.match(/^(?:[-*]\s*)?(?:\*\*|__)?(?:overall(?:\s+result)?|verdict|result|approval\s+signal)(?:\*\*|__)?\s*:\s*(?:\*\*|__)?\s*(pass|fail|reject|approved?|blocked?|blocker)(?:\*\*|__)?\b/i)
    if (labeled) {
      const verdict = normalizeArtifactVerdictToken(labeled[1] || "")
      if (verdict) return { verdict, verdict_unclear: false, matched_line: trimmed }
    }
    // Heading-style verdict: ## Verdict / **APPROVE** on next non-empty line
    const headingLabel = trimmed.match(/^#{1,4}\s+(?:overall(?:\s+result)?|verdict|result|approval\s+signal)\s*$/i)
    if (headingLabel) {
      for (let j = i + 1; j < lines.length; j++) {
        const nextTrimmed = lines[j].trim()
        if (!nextTrimmed) continue
        const headingVerdict = nextTrimmed.match(/^(?:\*\*|__)?\s*(pass|fail|reject|approved?|blocked?|blocker)\s*(?:\*\*|__)?$/i)
        if (headingVerdict) {
          const verdict = normalizeArtifactVerdictToken(headingVerdict[1] || "")
          if (verdict) return { verdict, verdict_unclear: false, matched_line: nextTrimmed }
        }
        break
      }
    }
    const failureEmoji = trimmed.match(/[❌✖]\s*(?:[^A-Za-z]*)(pass|fail|reject|approved?|blocked?|blocker)\b/i)
    if (failureEmoji) {
      const verdict = normalizeArtifactVerdictToken(failureEmoji[1] || "")
      if (verdict) return { verdict, verdict_unclear: false, matched_line: trimmed }
    }
    const successEmoji = trimmed.match(/[✅✔]\s*(?:[^A-Za-z]*)(pass|fail|reject|approved?|blocked?|blocker)\b/i)
    if (successEmoji) {
      const verdict = normalizeArtifactVerdictToken(successEmoji[1] || "")
      if (verdict) return { verdict, verdict_unclear: false, matched_line: trimmed }
    }
  }
  return { verdict: null, verdict_unclear: content.trim().length > 0, matched_line: null }
}
export async function inspectArtifactVerdict(artifact: Artifact | undefined, root = rootPath()): Promise<ArtifactVerdictInspection> {
  return extractArtifactVerdict(await readArtifactContent(artifact, root))
}
export function isBlockingArtifactVerdict(verdict: ArtifactVerdict | null): boolean {
  return verdict === "FAIL" || verdict === "REJECT" || verdict === "BLOCKED"
}
export function isPassingArtifactVerdict(verdict: ArtifactVerdict | null): boolean {
  return verdict === "PASS" || verdict === "APPROVED"
}
function artifactByteLength(content: string): number { return Buffer.byteLength(content, "utf8") }
function hasExecutionEvidence(content: string): boolean { return EXECUTION_EVIDENCE_PATTERNS.some((pattern) => pattern.test(content)) }
function claimsInspectionOnly(content: string): boolean { return INSPECTION_ONLY_PATTERNS.some((pattern) => pattern.test(content)) }
export async function validateImplementationArtifactEvidence(ticket: Ticket, root = rootPath()): Promise<string | null> {
  const artifact = latestArtifact(ticket, { stage: "implementation", trust_state: "current" })
  if (!artifact) return "Cannot move to review before an implementation artifact exists."
  const content = await readArtifactContent(artifact, root)
  return hasExecutionEvidence(content) ? null : "Implementation artifact must include compile, syntax, or import-check command output before review."
}
export async function validateQaArtifactEvidence(ticket: Ticket, root = rootPath()): Promise<string | null> {
  const artifact = latestArtifact(ticket, { stage: "qa", trust_state: "current" })
  if (!artifact) return "Cannot move to smoke_test before a QA artifact exists."
  const content = await readArtifactContent(artifact, root)
  if (artifactByteLength(content) < MIN_EXECUTION_ARTIFACT_BYTES) return `QA artifact must be at least ${MIN_EXECUTION_ARTIFACT_BYTES} bytes before the smoke-test stage.`
  if (claimsInspectionOnly(content) && !hasExecutionEvidence(content)) return "QA artifact that claims validation only via code inspection is insufficient."
  return hasExecutionEvidence(content) ? null : "QA artifact must include raw command output before the smoke-test stage."
}
export async function validateSmokeTestArtifactEvidence(ticket: Ticket, root = rootPath()): Promise<string | null> {
  const artifact = latestArtifact(ticket, { stage: "smoke-test", trust_state: "current" })
  if (!artifact) return "Cannot move to done before a smoke-test artifact exists."
  const content = await readArtifactContent(artifact, root)
  if (artifactByteLength(content) < MIN_EXECUTION_ARTIFACT_BYTES) return `Smoke-test artifact must be at least ${MIN_EXECUTION_ARTIFACT_BYTES} bytes before closeout.`
  if (!hasExecutionEvidence(content)) return "Smoke-test artifact must include raw command output before closeout."
  return isPassingArtifactVerdict(extractArtifactVerdict(content).verdict) || /Overall Result:\s*PASS/i.test(content)
    ? null
    : "Smoke-test artifact must record an explicit PASS result before closeout."
}

export function blockedDependentTickets(manifest: Manifest, ticketId: string): Ticket[] {
  return manifest.tickets.filter((item) => item.depends_on.includes(ticketId) && item.status !== "done")
}
export function dependentContinuationAction(ticket: Ticket, blockedDependents: Ticket[]): string {
  const nextDependent = blockedDependents[0]
  if (!nextDependent) {
    return "Continue the required internal lifecycle from the current ticket stage."
  }
  return `Current ticket is already closed. Activate dependent ticket ${nextDependent.id} and continue that lane instead of trying to mutate ${ticket.id} again.`
}
export function splitScopeChildren(manifest: Manifest, ticketId: string): Ticket[] {
  return manifest.tickets.filter((item) => item.source_ticket_id === ticketId && item.source_mode === "split_scope")
}
export function openSplitScopeChildren(manifest: Manifest, ticketId: string): Ticket[] {
  return splitScopeChildren(manifest, ticketId).filter((item) => item.status !== "done" && item.resolution_state !== "superseded")
}
export function openSequentialSplitChildren(manifest: Manifest, ticketId: string): Ticket[] {
  return openSplitScopeChildren(manifest, ticketId).filter((item) => item.split_kind === "sequential_dependent")
}
export function openParallelSplitChildren(manifest: Manifest, ticketId: string): Ticket[] {
  return openSplitScopeChildren(manifest, ticketId).filter((item) => item.split_kind === "parallel_independent")
}

// Ordered list of lifecycle stages used for stale-stage comparison.
const ORDERED_LIFECYCLE_STAGES = ["planning", "plan_review", "implementation", "review", "qa", "smoke-test", "closeout"] as const

export type StaleStageReconciliation = {
  stale: boolean
  manifest_stage: string
  evidenced_stage: string | null
  recovery_action: string | null
}

/**
 * Determines whether the ticket's manifest stage is behind what current artifact evidence
 * would justify.  Returns a recovery action when artifact evidence and stage/state disagree.
 *
 * This helper is intentionally read-only — it never mutates manifest or workflow state.
 * The team leader must confirm and execute the recovery action explicitly.
 */
export function reconcileStaleStageIfNeeded(ticket: Ticket): StaleStageReconciliation {
  const manifestStage = ticket.stage
  const manifestIdx = ORDERED_LIFECYCLE_STAGES.indexOf(manifestStage as typeof ORDERED_LIFECYCLE_STAGES[number])

  // Walk stages in reverse order: find the highest stage with a current artifact
  let highestEvidencedStage: string | null = null
  for (let i = ORDERED_LIFECYCLE_STAGES.length - 1; i >= 0; i--) {
    const candidateStage = ORDERED_LIFECYCLE_STAGES[i]
    const artifact = latestArtifact(ticket, { stage: candidateStage, trust_state: "current" })
    if (artifact) {
      highestEvidencedStage = candidateStage
      break
    }
  }

  if (!highestEvidencedStage) {
    return { stale: false, manifest_stage: manifestStage, evidenced_stage: null, recovery_action: null }
  }

  const evidencedIdx = ORDERED_LIFECYCLE_STAGES.indexOf(highestEvidencedStage as typeof ORDERED_LIFECYCLE_STAGES[number])

  if (evidencedIdx <= manifestIdx) {
    // Artifact evidence does not outpace the manifest stage — no drift.
    return { stale: false, manifest_stage: manifestStage, evidenced_stage: highestEvidencedStage, recovery_action: null }
  }

  // Artifact evidence is ahead of the manifest stage — stale-stage condition detected.
  const expectedStatus = STAGE_DEFAULT_STATUS[highestEvidencedStage] ?? "in_progress"
  const recovery = (
    `Stale-stage drift detected: manifest stage is "${manifestStage}" but a current "${highestEvidencedStage}" artifact exists. ` +
    `Run ticket_update with { stage: "${highestEvidencedStage}", status: "${expectedStatus}" } to align the manifest with the artifact evidence before resuming lifecycle routing.`
  )
  return {
    stale: true,
    manifest_stage: manifestStage,
    evidenced_stage: highestEvidencedStage,
    recovery_action: recovery,
  }
}

export async function validateHandoffNextAction(manifest: Manifest, workflow: WorkflowState, nextAction: string, root = rootPath()): Promise<string | null> {
  const trimmed = nextAction.trim()
  if (!trimmed) return "next_action cannot be empty."

  const ticket = getTicket(manifest, workflow.active_ticket)
  const processVerification = getProcessVerificationState(manifest, workflow, ticket.id)
  const blockedDependents = blockedDependentTickets(manifest, ticket.id)
  const lower = trimmed.toLowerCase()
  const claimsDependencyReadiness = /\bunblocked\b|\bready to proceed\b|\bcan proceed\b/.test(lower)
  const claimsSingleCause = /not a code defect|only blocker|tool\/env mismatch|tooling issue/.test(lower)
  const claimsCleanState = /\bclean state\b|\brepo is clean\b|\ball (?:tickets )?complete(?: and verified)?\b|\bfully verified\b|\bno follow-up required\b/.test(lower)

  if (claimsDependencyReadiness && blockedDependents.length > 0 && ticket.status !== "done") {
    return `Cannot publish dependency-readiness claims while ${ticket.id} is not done and dependent tickets still wait on it (${blockedDependents.map((item) => item.id).join(", ")}).`
  }

  if (processVerification.pending && (claimsDependencyReadiness || claimsCleanState)) {
    const blocker = processVerification.clearable_now
      ? "pending_process_verification is still true even though the affected done-ticket set is empty. Clear the workflow flag before publishing clean-state or readiness claims."
      : `pending_process_verification is still true for done ticket(s) ${processVerification.affected_done_tickets.map((item) => item.id).join(", ")}.`
    return `Cannot publish clean-state or readiness claims while ${blocker}`
  }

  if (claimsSingleCause) {
    if (ticket.status !== "done") {
      return `Cannot publish causal claims such as "not a code defect" or "only blocker" while ${ticket.id} is still ${ticket.status}.`
    }
    const smokeTestArtifact = latestArtifact(ticket, { stage: "smoke-test", trust_state: "current" })
    const content = await readArtifactContent(smokeTestArtifact, root)
    if (!/Overall Result:\s*PASS/i.test(content)) {
      return `Cannot publish causal claims about repo readiness without a passing smoke-test artifact for ${ticket.id}.`
    }
  }

  return null
}

export async function listBootstrapInputs(root = rootPath()): Promise<string[]> {
  const hits: string[] = []
  for (const relative of BOOTSTRAP_INPUT_FILES) {
    try {
      const info = await stat(join(root, relative))
      if (info.isFile()) hits.push(relative)
    } catch {}
  }
  return hits.sort()
}
export async function computeBootstrapFingerprint(root = rootPath()): Promise<string> {
  const hash = createHash("sha256")
  for (const relative of await listBootstrapInputs(root)) {
    hash.update(relative)
    hash.update("\u0000")
    hash.update(await readFile(join(root, relative)).catch(() => Buffer.from("")))
    hash.update("\u0000")
  }
  return hash.digest("hex")
}
export async function evaluateBootstrapState(state: BootstrapState, root = rootPath()): Promise<BootstrapState> {
  const fingerprint = await computeBootstrapFingerprint(root)
  if (state.status === "ready" && state.environment_fingerprint && state.environment_fingerprint !== fingerprint) return { ...state, status: "stale", environment_fingerprint: fingerprint }
  if (state.status === "missing" && state.proof_artifact) return { ...state, status: "stale", environment_fingerprint: fingerprint }
  return { ...state, environment_fingerprint: state.environment_fingerprint ?? fingerprint }
}
export async function requireBootstrapReady(workflow: WorkflowState, root = rootPath()): Promise<BootstrapState> {
  const evaluated = await evaluateBootstrapState(workflow.bootstrap, root)
  if (evaluated.status !== "ready") throw new Error(`Bootstrap ${evaluated.status}. Run environment_bootstrap before validation or handoff.`)
  return evaluated
}

export function findTicketLease(workflow: WorkflowState, ticketId: string): LaneLease | undefined {
  return workflow.lane_leases.find((lease) => lease.ticket_id === ticketId)
}
export function leaseIsExpired(lease: LaneLease, now = Date.now()): boolean {
  const expiresAt = Date.parse(lease.expires_at)
  return Number.isFinite(expiresAt) && expiresAt <= now
}
export function pruneExpiredLeases(workflow: WorkflowState, now = Date.now()): LaneLease[] {
  const expired = workflow.lane_leases.filter((lease) => leaseIsExpired(lease, now))
  if (expired.length === 0) return []
  workflow.lane_leases = workflow.lane_leases.filter((lease) => !leaseIsExpired(lease, now))
  return expired
}
export function findConflictingLease(workflow: WorkflowState, ticket: Ticket): LaneLease | undefined {
  return workflow.lane_leases.find((lease) => lease.ticket_id !== ticket.id && lease.lane === ticket.lane && lease.write_lock)
}
export function hasWriteLeaseForTicket(workflow: WorkflowState, ticketId: string, ownerAgent?: string): boolean {
  return workflow.lane_leases.some((lease) => lease.ticket_id === ticketId && lease.write_lock && (!ownerAgent || lease.owner_agent === ownerAgent))
}
export function getWriteLeaseForTicket(workflow: WorkflowState, ticketId: string, ownerAgent?: string): LaneLease | undefined {
  return workflow.lane_leases.find((lease) => lease.ticket_id === ticketId && lease.write_lock && (!ownerAgent || lease.owner_agent === ownerAgent))
}
function pathCoveredByAllowedPath(pathValue: string, allowedPath: string): boolean {
  const normalizedPath = normalizeRepoPath(pathValue).replace(/\/+$/g, "")
  const normalizedAllowed = normalizeRepoPath(allowedPath).replace(/\/+$/g, "")
  if (!normalizedAllowed) return true
  return normalizedPath === normalizedAllowed || normalizedPath.startsWith(`${normalizedAllowed}/`)
}
export function hasWriteLeaseForPath(workflow: WorkflowState, pathValue: string, ownerAgent?: string): boolean {
  const normalized = normalizeRepoPath(pathValue)
  return workflow.lane_leases.some(
    (lease) =>
      lease.write_lock &&
      (!ownerAgent || lease.owner_agent === ownerAgent) &&
      (lease.allowed_paths.length === 0 || lease.allowed_paths.some((allowed) => pathCoveredByAllowedPath(normalized, allowed))),
  )
}
export function hasWriteLeaseForTicketPath(workflow: WorkflowState, ticketId: string, pathValue: string, ownerAgent?: string): boolean {
  const lease = getWriteLeaseForTicket(workflow, ticketId, ownerAgent)
  if (!lease) return false
  const normalized = normalizeRepoPath(pathValue)
  return lease.allowed_paths.length === 0 || lease.allowed_paths.some((allowed) => pathCoveredByAllowedPath(normalized, allowed))
}
export function allowsPreBootstrapWriteClaim(workflow: WorkflowState, ticket: Ticket): boolean {
  return ticket.wave === 0
}
export function claimLaneLease(workflow: WorkflowState, ticket: Ticket, ownerAgent: string, allowedPaths: string[], writeLock = true): LaneLease {
  pruneExpiredLeases(workflow)
  const otherLeases = workflow.lane_leases.filter((lease) => lease.ticket_id !== ticket.id)
  if (workflow.parallel_mode === "sequential" && otherLeases.length > 0) {
    throw new Error(`Workflow is in sequential mode. Release the active lease before claiming another lane for ${ticket.id}.`)
  }
  if (!ticket.parallel_safe && workflow.parallel_mode === "parallel-lanes" && otherLeases.length > 0) {
    throw new Error(`Ticket ${ticket.id} is not marked parallel_safe and cannot hold a parallel lease while other leases are active.`)
  }
  if (ticket.overlap_risk === "high" && writeLock && otherLeases.length > 0) {
    throw new Error(`Ticket ${ticket.id} cannot take a write lease with overlap_risk=high while other leases are active.`)
  }
  const conflict = findConflictingLease(workflow, ticket)
  if (conflict) throw new Error(`Lane ${ticket.lane} already has an active write lease owned by ${conflict.owner_agent}.`)
  const existingLease = findTicketLease(workflow, ticket.id)
  if (existingLease && existingLease.owner_agent !== ownerAgent.trim()) {
    throw new Error(`Ticket ${ticket.id} already has an active lease owned by ${existingLease.owner_agent}. Release it before changing owners.`)
  }
  workflow.lane_leases = workflow.lane_leases.filter((lease) => lease.ticket_id !== ticket.id)
  const claimedAt = new Date().toISOString()
  const lease: LaneLease = {
    ticket_id: ticket.id,
    lane: ticket.lane,
    owner_agent: ownerAgent.trim(),
    write_lock: writeLock,
    claimed_at: claimedAt,
    expires_at: addMinutes(claimedAt, DEFAULT_LEASE_TTL_MINUTES),
    allowed_paths: allowedPaths.map(normalizeRepoPath),
  }
  workflow.lane_leases.push(lease)
  return lease
}
export function releaseLaneLease(workflow: WorkflowState, ticketId: string, ownerAgent?: string): LaneLease | null {
  const lease = workflow.lane_leases.find((entry) => entry.ticket_id === ticketId && (!ownerAgent || entry.owner_agent === ownerAgent))
  if (!lease) return null
  workflow.lane_leases = workflow.lane_leases.filter((entry) => entry !== lease)
  return lease
}

export function markArtifactsHistorical(ticket: Ticket, stage: string | undefined, trustState: Exclude<ArtifactTrustState, "current">, reason: string): void {
  const timestamp = new Date().toISOString()
  for (const artifact of ticket.artifacts) {
    if (artifact.trust_state !== "current") continue
    if (stage && artifact.stage !== stage) continue
    artifact.trust_state = trustState
    artifact.superseded_at = timestamp
    artifact.supersession_reason = reason
  }
}
export function markTicketDone(ticket: Ticket, workflow: WorkflowState): void {
  ticket.stage = "closeout"
  ticket.status = "done"
  ticket.resolution_state = "done"
  const state = ensureTicketWorkflowState(workflow, ticket.id)
  ticket.verification_state = state.needs_reverification || state.reopen_count > 0 ? "reverified" : "trusted"
  state.needs_reverification = false
}
export function markTicketSmokeVerified(ticket: Ticket): void {
  if (ticket.status !== "done" && ticket.verification_state !== "invalidated") {
    ticket.verification_state = "smoke_verified"
  }
}
export function markTicketReopened(ticket: Ticket, workflow: WorkflowState, reason: string): void {
  ticket.status = "todo"
  ticket.stage = "planning"
  ticket.resolution_state = "reopened"
  ticket.verification_state = "invalidated"
  const state = ensureTicketWorkflowState(workflow, ticket.id)
  state.reopen_count += 1
  state.needs_reverification = true
  markArtifactsHistorical(ticket, undefined, "superseded", reason)
}
export function resolveDefectOutcome(sourceTicket: Ticket, args: { acceptance_broken: boolean; scope_changed: boolean; rollback_required: boolean }): DefectOutcome {
  if (args.rollback_required) return "rollback_required"
  if (args.acceptance_broken) return "invalidates_done"
  if (args.scope_changed) return "follow_up"
  return sourceTicket.verification_state === "trusted" ? "no_action" : "follow_up"
}
export function createTicketRecord(spec: NewTicketSpec): Ticket {
  const id = assertValidTicketId(spec.id.trim())
  const title = spec.title.trim()
  const lane = spec.lane.trim()
  const summary = spec.summary.trim()
  const acceptance = spec.acceptance.map((item) => item.trim()).filter(Boolean)
  const dependsOn = [...new Set((spec.depends_on || []).map((item) => item.trim()).filter(Boolean))]
  const decisionBlockers = (spec.decision_blockers || []).map((item) => item.trim()).filter(Boolean)

  if (!title) throw new Error("Ticket title must not be empty.")
  if (!lane) throw new Error("Ticket lane must not be empty.")
  if (!summary) throw new Error("Ticket summary must not be empty.")
  if (!Number.isInteger(spec.wave) || spec.wave < 0) throw new Error(`Ticket wave must be zero or greater: ${spec.wave}`)
  if (acceptance.length === 0) throw new Error("At least one acceptance criterion is required.")
  if (dependsOn.includes(id)) throw new Error(`Ticket ${id} cannot depend on itself.`)

  return {
    id,
    title,
    wave: spec.wave,
    lane,
    parallel_safe: spec.parallel_safe ?? false,
    overlap_risk: spec.overlap_risk ?? DEFAULT_OVERLAP_RISK,
    stage: "planning",
    status: decisionBlockers.length > 0 ? "blocked" : "todo",
    depends_on: dependsOn,
    summary,
    acceptance,
    decision_blockers: decisionBlockers,
    artifacts: [],
    resolution_state: "open",
    verification_state: "suspect",
    finding_source: spec.finding_source?.trim() || undefined,
    source_ticket_id: spec.source_ticket_id?.trim() || undefined,
    follow_up_ticket_ids: [],
    source_mode: spec.source_mode,
    split_kind: spec.split_kind,
  }
}

function snapshotArtifactPath(ticketId: string, stage: string, kind: string, createdAt: string): string {
  const stamp = createdAt.replace(/[:.]/g, "-")
  return `${ARTIFACT_REGISTRY_ROOT}/history/${slugForPath(ticketId)}/${slugForPath(stage)}/${stamp}-${slugForPath(kind)}.md`
}
export async function registerArtifactSnapshot(spec: ArtifactRegistrationSpec, root = rootPath()): Promise<Artifact> {
  const sourcePath = normalizeRepoPath(spec.source_path)
  const createdAt = new Date().toISOString()
  const snapshotPath = snapshotArtifactPath(spec.ticket.id, spec.stage, spec.kind, createdAt)
  await mkdir(dirname(join(root, snapshotPath)), { recursive: true })
  await copyFile(join(root, sourcePath), join(root, snapshotPath))
  for (const artifact of spec.ticket.artifacts) {
    if (artifact.kind === spec.kind && artifact.stage === spec.stage && artifact.trust_state === "current") {
      artifact.trust_state = "superseded"
      artifact.superseded_at = createdAt
      artifact.superseded_by = snapshotPath
      artifact.supersession_reason = `Replaced by newer ${spec.stage}/${spec.kind} artifact.`
    }
  }
  const artifact: Artifact = { kind: spec.kind, path: snapshotPath, stage: spec.stage, summary: spec.summary, created_at: createdAt, trust_state: "current" }
  spec.ticket.artifacts.push(artifact)
  spec.registry.artifacts.push({ ticket_id: spec.ticket.id, ...artifact })
  return artifact
}
function extractTicketNotes(existing: string): string {
  const match = existing.match(/\n## Notes\n\n?([\s\S]*)$/)
  return match ? match[1].trimEnd() : ""
}
function renderArtifactLine(artifact: Artifact): string {
  const summary = artifact.summary ? ` - ${artifact.summary}` : ""
  const trust = artifact.trust_state !== "current" ? ` [${artifact.trust_state}]` : ""
  return `- ${artifact.kind}: ${artifact.path} (${artifact.stage})${trust}${summary}`
}
function renderArtifactLines(ticket: Ticket): string {
  return ticket.artifacts.length > 0 ? ticket.artifacts.map(renderArtifactLine).join("\n") : "- None yet"
}
export async function syncTicketFile(ticket: Ticket, root = rootPath()): Promise<void> {
  const path = ticketFilePath(ticket.id, root)
  await writeText(path, renderTicketDocument(ticket, extractTicketNotes(await readText(path))))
}
export async function saveManifest(manifest: Manifest, root = rootPath(), options: SaveDerivedSurfaceOptions = {}, validationContext: SaveValidationContext = {}): Promise<void> {
  await validateManifestWriteState(manifest, root, validationContext)
  manifest.version = Math.max(manifest.version || 0, DEFAULT_TICKET_CONTRACT_VERSION)
  await writeJson(ticketsManifestPath(root), manifest)
  await writeText(ticketsBoardPath(root), renderBoard(manifest))
  for (const ticket of manifest.tickets) await syncTicketFile(ticket, root)
  if (options.refreshDerivedSurfaces !== false) {
    await refreshRestartSurfaces({ manifest, root })
  }
}
export async function writeManifest(manifest: Manifest, root = rootPath(), options: SaveDerivedSurfaceOptions = {}): Promise<void> {
  await saveManifest(manifest, root, options)
}
export async function saveArtifactRegistry(registry: ArtifactRegistry, root = rootPath()): Promise<void> {
  registry.version = Math.max(registry.version || 0, 2)
  await writeJson(artifactRegistryPath(root), registry)
}
type SaveWorkflowBundle = {
  workflow: WorkflowState
  manifest?: Manifest
  registry?: ArtifactRegistry
  root?: string
  expectedRevision?: number
  skipGraphValidation?: boolean
}
export async function saveWorkflowBundle(bundle: SaveWorkflowBundle): Promise<void> {
  const root = bundle.root ?? rootPath()
  const ctx: SaveValidationContext = { manifest: bundle.manifest, workflow: bundle.workflow, skipGraphValidation: bundle.skipGraphValidation }
  await saveWorkflowState(bundle.workflow, root, bundle.expectedRevision, { refreshDerivedSurfaces: false }, ctx)
  if (bundle.manifest) await saveManifest(bundle.manifest, root, { refreshDerivedSurfaces: false }, ctx)
  if (bundle.registry) await saveArtifactRegistry(bundle.registry, root)
  await refreshRestartSurfaces({ manifest: bundle.manifest, workflow: bundle.workflow, root })
}

export function ticketNeedsProcessVerification(ticket: Ticket, workflow: WorkflowState): boolean {
  if (!workflow.pending_process_verification || ticket.status !== "done") return false
  if (ticket.verification_state === "reverified") return false
  const verificationArtifact = latestArtifact(ticket, { stage: "review", kind: "backlog-verification", trust_state: "current" })
  if (verificationArtifact) return false
  const changedAt = workflow.process_last_changed_at ? Date.parse(workflow.process_last_changed_at) : NaN
  if (!Number.isFinite(changedAt)) return true
  const completionArtifact =
    latestArtifact(ticket, { stage: "smoke-test", trust_state: "current" }) ||
    latestArtifact(ticket, { stage: "qa", trust_state: "current" }) ||
    [...ticket.artifacts].reverse().find((artifact) => artifact.trust_state === "current")
  if (!completionArtifact) return true
  const completedAt = Date.parse(completionArtifact.created_at)
  return !Number.isFinite(completedAt) || completedAt < changedAt
}
export function ticketsNeedingProcessVerification(manifest: Manifest, workflow: WorkflowState): Ticket[] {
  return manifest.tickets.filter((ticket) => ticketNeedsProcessVerification(ticket, workflow))
}
export function getProcessVerificationState(manifest: Manifest, workflow: WorkflowState, currentTicketId = workflow.active_ticket): ProcessVerificationState {
  const affectedDoneTickets = ticketsNeedingProcessVerification(manifest, workflow)
  const currentTicket = manifest.tickets.find((ticket) => ticket.id === currentTicketId)
  const currentTicketRequiresVerification = currentTicket ? ticketNeedsProcessVerification(currentTicket, workflow) : false
  const pending = workflow.pending_process_verification
  const doneButNotFullyTrusted = pending
    ? affectedDoneTickets
    : manifest.tickets.filter((ticket) => ticket.status === "done" && ticket.verification_state !== "trusted" && ticket.verification_state !== "reverified")
  return {
    pending,
    affected_done_tickets: affectedDoneTickets,
    current_ticket_requires_verification: currentTicketRequiresVerification,
    clearable_now: pending && affectedDoneTickets.length === 0,
    done_but_not_fully_trusted: doneButNotFullyTrusted,
  }
}
export function ticketNeedsHistoricalReconciliation(ticket: Ticket): boolean {
  return ticket.status === "done" && ticket.resolution_state === "superseded" && ticket.verification_state === "invalidated"
}
export function ticketNeedsTrustRestoration(ticket: Ticket, workflow: WorkflowState): boolean {
  if (ticket.status !== "done") return false
  if (ticketNeedsHistoricalReconciliation(ticket)) return false
  if (ticketNeedsProcessVerification(ticket, workflow)) return true
  return getTicketWorkflowState(workflow, ticket.id).needs_reverification === true
}
export function hasPendingRepairFollowOn(workflow: WorkflowState): boolean {
  return workflow.repair_follow_on.outcome === "managed_blocked"
}
/**
 * Returns true when the repair cycle has explicitly authorised `ticketId` for
 * lifecycle progression while managed_blocked is active.  This is the correct
 * carve-out for REMED tickets and their source tickets — it is keyed to
 * explicit IDs written by the repair script, not to lane text or other
 * mutable ticket metadata.
 */
export function isAllowedFollowOnTicket(workflow: WorkflowState, ticketId: string): boolean {
  const allowed = workflow.repair_follow_on.allowed_follow_on_tickets
  return Array.isArray(allowed) && allowed.includes(ticketId)
}
export function nextRepairFollowOnStage(workflow: WorkflowState): string | null {
  if (workflow.repair_follow_on.outcome !== "managed_blocked") return null
  const completed = new Set(workflow.repair_follow_on.completed_stages)
  return workflow.repair_follow_on.required_stages.find((stage) => !completed.has(stage)) || null
}
export function repairFollowOnBlockingReason(workflow: WorkflowState): string | null {
  if (workflow.repair_follow_on.outcome !== "managed_blocked") return null
  return workflow.repair_follow_on.blocking_reasons[0] || null
}

export function renderBoard(manifest: Manifest): string {
  const rows = manifest.tickets.map((ticket) => {
    const dependsOn = ticket.depends_on.length > 0 ? ticket.depends_on.join(", ") : "-"
    const followUps = ticket.follow_up_ticket_ids.length > 0 ? ticket.follow_up_ticket_ids.join(", ") : "-"
    return `| ${ticket.wave} | ${ticket.id} | ${ticket.title} | ${ticket.lane} | ${ticket.stage} | ${ticket.status} | ${ticket.resolution_state} | ${ticket.verification_state} | ${ticket.parallel_safe ? "yes" : "no"} | ${ticket.overlap_risk} | ${dependsOn} | ${followUps} |`
  })
  return `# Ticket Board\n\n| Wave | ID | Title | Lane | Stage | Status | Resolution | Verification | Parallel Safe | Overlap Risk | Depends On | Follow-ups |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n${rows.join("\n")}\n`
}
export function renderTicketDocument(ticket: Ticket, notes = ""): string {
  const dependsOn = ticket.depends_on.length > 0 ? ticket.depends_on.join(", ") : "None"
  const blockers = ticket.decision_blockers.length > 0 ? ticket.decision_blockers.map((item) => `- ${item}`).join("\n") : "None"
  const acceptance = ticket.acceptance.length > 0 ? ticket.acceptance.map((item) => `- [ ] ${item}`).join("\n") : "None"
  const followUps = ticket.follow_up_ticket_ids.length > 0 ? ticket.follow_up_ticket_ids.map((item) => `- ${item}`).join("\n") : "None"
  return `# ${ticket.id}: ${ticket.title}

## Summary

${ticket.summary}

## Wave

${ticket.wave}

## Lane

${ticket.lane}

## Parallel Safety

- parallel_safe: ${ticket.parallel_safe ? "true" : "false"}
- overlap_risk: ${ticket.overlap_risk}

## Stage

${ticket.stage}

## Status

${ticket.status}

## Trust

- resolution_state: ${ticket.resolution_state}
- verification_state: ${ticket.verification_state}
- finding_source: ${ticket.finding_source || "None"}
- source_ticket_id: ${ticket.source_ticket_id || "None"}
- source_mode: ${ticket.source_mode || "None"}

## Depends On

${dependsOn}

## Follow-up Tickets

${followUps}

## Decision Blockers

${blockers}

## Acceptance Criteria

${acceptance}

## Artifacts

${renderArtifactLines(ticket)}

## Notes

${notes.trimEnd() ? `${notes.trimEnd()}\n` : ""}
`
}
export function renderContextSnapshot(manifest: Manifest, workflow: WorkflowState, pivot: PivotState, note?: string): string {
  const ticket = getTicket(manifest, workflow.active_ticket)
  const ticketState = getTicketWorkflowState(workflow, ticket.id)
  const leases = workflow.lane_leases.length > 0 ? workflow.lane_leases.map((lease) => `- ${lease.ticket_id}: ${lease.owner_agent} (${lease.lane})`).join("\n") : "- No active lane leases"
  const artifactLines = ticket.artifacts.length > 0 ? ticket.artifacts.slice(-5).map(renderArtifactLine).join("\n") : "- No artifacts recorded yet"
  const repairNextStage = nextRepairFollowOnStage(workflow) || "none"
  const splitChildren = openSplitScopeChildren(manifest, ticket.id)
  const pivotInputs = pivot.restart_surface_inputs
  const pivotState = pivot.downstream_refresh_state
  const noteBlock = note ? `\n## Note\n\n${note}\n` : ""
  return `# Context Snapshot\n\n## Project\n\n${manifest.project}\n\n## Active Ticket\n\n- ID: ${ticket.id}\n- Title: ${ticket.title}\n- Stage: ${ticket.stage}\n- Status: ${ticket.status}\n- Resolution: ${ticket.resolution_state}\n- Verification: ${ticket.verification_state}\n- Approved plan: ${workflow.approved_plan ? "yes" : "no"}\n- Needs reverification: ${ticketState.needs_reverification ? "yes" : "no"}\n- Open split children: ${splitChildren.length > 0 ? splitChildren.map((item) => item.id).join(", ") : "none"}\n\n## Bootstrap\n\n- status: ${workflow.bootstrap.status}\n- last_verified_at: ${workflow.bootstrap.last_verified_at || "Not yet verified."}\n- proof_artifact: ${workflow.bootstrap.proof_artifact || "None"}\n- blockers: ${workflow.bootstrap_blockers.length > 0 ? workflow.bootstrap_blockers.map((item) => `${item.executable} (${item.reason})`).join(", ") : "none"}\n\n## Process State\n\n- process_version: ${workflow.process_version}\n- pending_process_verification: ${workflow.pending_process_verification ? "true" : "false"}\n- parallel_mode: ${workflow.parallel_mode}\n- state_revision: ${workflow.state_revision}\n\n## Repair Follow-On\n\n- outcome: ${workflow.repair_follow_on.outcome}\n- required: ${hasPendingRepairFollowOn(workflow) ? "yes" : "no"}\n- next_required_stage: ${repairNextStage}\n- verification_passed: ${workflow.repair_follow_on.verification_passed ? "true" : "false"}\n- last_updated_at: ${workflow.repair_follow_on.last_updated_at || "Not yet recorded."}\n\n## Pivot State\n\n- pivot_in_progress: ${pivotInputs.pivot_in_progress ? "true" : "false"}\n- pivot_class: ${pivotInputs.pivot_class || "none"}\n- pivot_changed_surfaces: ${pivotInputs.pivot_changed_surfaces.length > 0 ? pivotInputs.pivot_changed_surfaces.join(", ") : "none"}\n- pending_downstream_stages: ${pivotInputs.pending_downstream_stages.length > 0 ? pivotInputs.pending_downstream_stages.join(", ") : "none"}\n- completed_downstream_stages: ${pivotInputs.completed_downstream_stages.length > 0 ? pivotInputs.completed_downstream_stages.join(", ") : "none"}\n- pending_ticket_lineage_actions: ${pivotInputs.pending_ticket_lineage_actions.length > 0 ? pivotInputs.pending_ticket_lineage_actions.join(", ") : "none"}\n- completed_ticket_lineage_actions: ${pivotInputs.completed_ticket_lineage_actions.length > 0 ? pivotInputs.completed_ticket_lineage_actions.join(", ") : "none"}\n- post_pivot_verification_passed: ${pivotInputs.post_pivot_verification_passed ? "true" : "false"}\n- pivot_state_path: ${pivot.pivot_state_path || ".opencode/meta/pivot-state.json"}\n- pivot_tracking_mode: ${pivotState?.tracking_mode || "none"}\n\n## Lane Leases\n\n${leases}\n\n## Recent Artifacts\n\n${artifactLines}${noteBlock}`
}
export function renderStartHere(manifest: Manifest, workflow: WorkflowState, pivot: PivotState, options: StartHereOptions = {}): string {
  const ticket = getTicket(manifest, workflow.active_ticket)
  const reopened = manifest.tickets.filter((item) => item.resolution_state === "reopened")
  const processVerification = getProcessVerificationState(manifest, workflow, ticket.id)
  const activeTicketNeedsHistoricalReconciliation = ticketNeedsHistoricalReconciliation(ticket)
  const activeTicketNeedsTrustRestoration = ticketNeedsTrustRestoration(ticket, workflow)
  const suspectDone = processVerification.done_but_not_fully_trusted
  const reverification = manifest.tickets.filter((item) => getTicketWorkflowState(workflow, item.id).needs_reverification)
  const blockedDependents = blockedDependentTickets(manifest, ticket.id)
  const splitChildren = openSplitScopeChildren(manifest, ticket.id)
  const verifierLabel = options.backlogVerifierAgent ? `\`${options.backlogVerifierAgent}\`` : "the backlog verifier"
  const repairNextStage = nextRepairFollowOnStage(workflow)
  const repairFollowOnPending = hasPendingRepairFollowOn(workflow)
  const repairBlocker = repairFollowOnBlockingReason(workflow)
  const sourceFollowUpPending = workflow.repair_follow_on.outcome === "source_follow_up"
  const pivotInputs = pivot.restart_surface_inputs
  const pivotPending = pivotInputs.pivot_in_progress
  const handoffStatus = options.handoffStatus || (
    workflow.bootstrap.status !== "ready"
      ? "bootstrap recovery required"
      : pivotPending
        ? "pivot follow-up required"
      : repairFollowOnPending
        ? "repair follow-up required"
        : processVerification.pending || activeTicketNeedsTrustRestoration || activeTicketNeedsHistoricalReconciliation
          ? "workflow verification pending"
          : "ready for continued development"
  )
  const recommendedAction = options.nextAction || (
    workflow.bootstrap.status !== "ready"
      ? "Run environment_bootstrap, register its proof artifact, rerun ticket_lookup, and do not continue lifecycle work until bootstrap is ready."
      : pivotPending
        ? (pivotInputs.pending_downstream_stages.length > 0
            ? `Continue the pivot follow-on stage${pivotInputs.pending_downstream_stages.length > 1 ? "s" : ""} ${pivotInputs.pending_downstream_stages.map((stage) => `\`${stage}\``).join(", ")} before resuming normal ticket lifecycle work.${pivotInputs.pending_ticket_lineage_actions.length > 0 ? ` Ticket lineage actions still pending: ${pivotInputs.pending_ticket_lineage_actions.join(", ")}.` : ""}`
            : "Complete the remaining pivot follow-on work and republish the restart surfaces before resuming normal ticket lifecycle work.")
      : repairFollowOnPending
        ? (repairBlocker || (repairNextStage ? `Complete the required repair follow-on stage \`${repairNextStage}\` before resuming normal ticket lifecycle work.` : "Complete the required repair follow-on stages before resuming normal ticket lifecycle work."))
        : splitChildren.length > 0
          ? `Keep ${ticket.id} open as a split parent and continue the child ticket lane${splitChildren.length > 1 ? "s" : ""}: ${splitChildren.map((item) => item.id).join(", ")}.`
          : ticket.status !== "done"
            ? `Keep ${ticket.id} as the foreground ticket and continue its lifecycle from ${ticket.stage}. Historical done-ticket reverification stays secondary until the active open ticket is resolved.`
            : activeTicketNeedsHistoricalReconciliation
              ? `Ticket is already closed, but its historical lineage is still contradictory. Use ticket_reconcile with current registered evidence to repair ${ticket.id} instead of trying to reopen or reclaim it.`
            : activeTicketNeedsTrustRestoration
              ? `Ticket is already closed, but historical trust still needs restoration. Use ${verifierLabel} to produce current evidence, then run ticket_reverify on ${ticket.id} instead of trying to reclaim it.`
              : processVerification.pending
                ? processVerification.clearable_now
                ? "Use ticket_update to clear pending_process_verification now that no historical done tickets still require process verification, then rerun ticket_lookup."
                : `Use the team leader to route ${verifierLabel} across done tickets whose trust predates the current process contract: ${processVerification.affected_done_tickets.map((item) => item.id).join(", ")}.`
                : blockedDependents.length > 0
                  ? dependentContinuationAction(ticket, blockedDependents)
                  : "Continue the required internal lifecycle from the current ticket stage."
  )
  const summarizeTickets = (items: Ticket[]) => items.length > 0 ? items.map((item) => item.id).join(", ") : "none"
  const riskLines = [
    workflow.bootstrap.status !== "ready" ? "- Environment validation can fail for setup reasons until bootstrap proof exists." : null,
    pivotPending ? `- Pivot follow-up is still in progress${pivotInputs.pending_downstream_stages.length > 0 ? `: ${pivotInputs.pending_downstream_stages.join(", ")}.` : "."}` : null,
    pivotInputs.pending_ticket_lineage_actions.length > 0 ? `- Pivot ticket lineage actions remain pending: ${pivotInputs.pending_ticket_lineage_actions.join(", ")}.` : null,
    repairFollowOnPending ? `- Repair follow-on remains incomplete${repairBlocker ? `: ${repairBlocker}` : "."}` : null,
    sourceFollowUpPending ? "- Managed repair converged, but source-layer follow-up still remains in the ticket graph." : null,
    activeTicketNeedsHistoricalReconciliation ? "- Historical lineage remains contradictory until ticket_reconcile repairs the superseded invalidated ticket graph." : null,
    activeTicketNeedsTrustRestoration || processVerification.pending ? "- Historical completion should not be treated as fully trusted until pending process verification or explicit reverification is cleared." : null,
    processVerification.clearable_now ? "- The workflow still records pending process verification even though no done tickets remain affected; clear the workflow flag before relying on a clean-state restart narrative." : null,
    suspectDone.length > 0 ? `- Some done tickets are not fully trusted yet: ${suspectDone.map((item) => item.id).join(", ")}.` : null,
    splitChildren.length > 0 ? `- ${ticket.id} is an open split parent; child ticket${splitChildren.length > 1 ? "s" : ""} ${splitChildren.map((item) => item.id).join(", ")} remain the active foreground work.` : null,
    blockedDependents.length > 0 && ticket.status !== "done" ? `- Downstream tickets ${blockedDependents.map((item) => item.id).join(", ")} remain formally blocked until ${ticket.id} reaches done.` : null,
  ].filter((line): line is string => Boolean(line)).join("\n") || "- None recorded."
  const quality = summarizeCodeQualityStatus(manifest)
  return `# START HERE\n\n${START_HERE_MANAGED_START}\n## What This Repo Is\n\n${manifest.project}\n\n## Current State\n\nThe repo is operating under the managed OpenCode workflow. Use the canonical state files below instead of memory or raw ticket prose.\n\n## Read In This Order\n\n1. README.md\n2. AGENTS.md\n3. docs/AGENT-DELEGATION.md\n4. docs/spec/CANONICAL-BRIEF.md\n5. docs/process/workflow.md\n6. tickets/manifest.json\n7. tickets/BOARD.md\n\n## Current Or Next Ticket\n\n- ID: ${ticket.id}\n- Title: ${ticket.title}\n- Wave: ${ticket.wave}\n- Lane: ${ticket.lane}\n- Stage: ${ticket.stage}\n- Status: ${ticket.status}\n- Resolution: ${ticket.resolution_state}\n- Verification: ${ticket.verification_state}\n\n## Dependency Status\n\n- current_ticket_done: ${ticket.status === "done" ? "yes" : "no"}\n- dependent_tickets_waiting_on_current: ${summarizeTickets(blockedDependents)}\n- split_child_tickets: ${summarizeTickets(splitChildren)}\n\n## Generation Status\n\n- handoff_status: ${handoffStatus}\n- process_version: ${workflow.process_version}\n- parallel_mode: ${workflow.parallel_mode}\n- pending_process_verification: ${processVerification.pending ? "true" : "false"}\n- repair_follow_on_outcome: ${workflow.repair_follow_on.outcome}\n- repair_follow_on_required: ${repairFollowOnPending ? "true" : "false"}\n- repair_follow_on_next_stage: ${repairNextStage || "none"}\n- repair_follow_on_verification_passed: ${workflow.repair_follow_on.verification_passed ? "true" : "false"}\n- repair_follow_on_updated_at: ${workflow.repair_follow_on.last_updated_at || "Not yet recorded."}\n- pivot_in_progress: ${pivotInputs.pivot_in_progress ? "true" : "false"}\n- pivot_class: ${pivotInputs.pivot_class || "none"}\n- pivot_changed_surfaces: ${pivotInputs.pivot_changed_surfaces.length > 0 ? pivotInputs.pivot_changed_surfaces.join(", ") : "none"}\n- pivot_pending_stages: ${pivotInputs.pending_downstream_stages.length > 0 ? pivotInputs.pending_downstream_stages.join(", ") : "none"}\n- pivot_completed_stages: ${pivotInputs.completed_downstream_stages.length > 0 ? pivotInputs.completed_downstream_stages.join(", ") : "none"}\n- pivot_pending_ticket_lineage_actions: ${pivotInputs.pending_ticket_lineage_actions.length > 0 ? pivotInputs.pending_ticket_lineage_actions.join(", ") : "none"}\n- pivot_completed_ticket_lineage_actions: ${pivotInputs.completed_ticket_lineage_actions.length > 0 ? pivotInputs.completed_ticket_lineage_actions.join(", ") : "none"}\n- post_pivot_verification_passed: ${pivotInputs.post_pivot_verification_passed ? "true" : "false"}\n- bootstrap_status: ${workflow.bootstrap.status}\n- bootstrap_proof: ${workflow.bootstrap.proof_artifact || "None"}\n- bootstrap_blockers: ${workflow.bootstrap_blockers.length > 0 ? workflow.bootstrap_blockers.map((item) => `${item.executable} (${item.reason})`).join(", ") : "none"}\n\n## Post-Generation Audit Status\n\n- audit_or_repair_follow_up: ${pivotPending || repairFollowOnPending || sourceFollowUpPending || reopened.length > 0 || suspectDone.length > 0 || reverification.length > 0 || processVerification.clearable_now ? "follow-up required" : "none recorded"}\n- reopened_tickets: ${summarizeTickets(reopened)}\n- done_but_not_fully_trusted: ${summarizeTickets(suspectDone)}\n- pending_reverification: ${summarizeTickets(reverification)}\n- repair_follow_on_blockers: ${workflow.repair_follow_on.blocking_reasons.length > 0 ? workflow.repair_follow_on.blocking_reasons.join(" | ") : "none"}\n- pivot_pending_stages: ${pivotInputs.pending_downstream_stages.length > 0 ? pivotInputs.pending_downstream_stages.join(", ") : "none"}\n- pivot_pending_ticket_lineage_actions: ${pivotInputs.pending_ticket_lineage_actions.length > 0 ? pivotInputs.pending_ticket_lineage_actions.join(", ") : "none"}\n\n## Code Quality Status\n\n- last_build_result: ${quality.build_result}\n- last_test_run_result: ${quality.test_result}\n- open_remediation_tickets: ${quality.open_remediation_tickets}\n- known_reference_integrity_issues: ${quality.open_reference_integrity_tickets}\n\n## Known Risks\n\n${riskLines}\n\n## Next Action\n\n${recommendedAction}\n${START_HERE_MANAGED_END}\n`
}
function escapeRegExp(value: string): string { return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") }
function inferArtifactSummaryState(summary: string | undefined): "pass" | "fail" | "unknown" {
  const normalized = (summary || "").toLowerCase()
  if (normalized.includes("passed") || normalized.includes("approved")) return "pass"
  if (normalized.includes("failed") || normalized.includes("block") || normalized.includes("reject")) return "fail"
  return "unknown"
}
function latestCurrentArtifactForStages(manifest: Manifest, stages: string[]): Artifact | undefined {
  const matches = manifest.tickets.flatMap((ticket) =>
    ticket.artifacts.filter((artifact) => artifact.trust_state === "current" && stages.includes(artifact.stage)),
  )
  return matches.sort((left, right) => right.created_at.localeCompare(left.created_at))[0]
}
function summarizeCodeQualityStatus(manifest: Manifest): {
  build_result: string
  test_result: string
  open_remediation_tickets: number
  open_reference_integrity_tickets: number
} {
  const latestBuildArtifact = latestCurrentArtifactForStages(manifest, ["implementation", "review", "smoke-test"])
  const latestTestArtifact = latestCurrentArtifactForStages(manifest, ["qa", "smoke-test"])
  const openRemediationTickets = manifest.tickets.filter(
    (ticket) => Boolean(ticket.finding_source) && ticket.status !== "done" && ticket.resolution_state !== "superseded",
  )
  const openReferenceTickets = openRemediationTickets.filter((ticket) => ticket.finding_source?.startsWith("REF"))
  const describe = (artifact: Artifact | undefined) => `${inferArtifactSummaryState(artifact?.summary)} @ ${artifact?.created_at || "Not yet recorded"}`
  return {
    build_result: describe(latestBuildArtifact),
    test_result: describe(latestTestArtifact),
    open_remediation_tickets: openRemediationTickets.length,
    open_reference_integrity_tickets: openReferenceTickets.length,
  }
}
export function mergeStartHere(existing: string, rendered: string): string {
  const pattern = new RegExp(`${escapeRegExp(START_HERE_MANAGED_START)}[\\s\\S]*?${escapeRegExp(START_HERE_MANAGED_END)}`, "m")
  const renderedBlock = rendered.match(pattern)
  if (!renderedBlock) return rendered
  if (!existing.trim()) return rendered
  if (!existing.includes(START_HERE_MANAGED_START) || !existing.includes(START_HERE_MANAGED_END)) return existing
  return existing.replace(pattern, renderedBlock[0])
}
async function loadBacklogVerifierAgent(root = rootPath()): Promise<string | undefined> {
  const provenance = await readJson<{
    workflow_contract?: {
      post_migration_verification?: {
        backlog_verifier_agent?: string
      }
    }
  } | null>(bootstrapProvenancePath(root), null)
  const backlogVerifierAgent = provenance?.workflow_contract?.post_migration_verification?.backlog_verifier_agent
  return typeof backlogVerifierAgent === "string" && backlogVerifierAgent.trim() ? backlogVerifierAgent.trim() : undefined
}
export async function refreshRestartSurfaces(inputs: RestartSurfaceRenderInputs = {}): Promise<void> {
  const root = inputs.root ?? rootPath()
  const manifest = inputs.manifest ?? await readJson<Manifest | null>(ticketsManifestPath(root), null)
  const workflow = inputs.workflow ?? await readJson<WorkflowState | null>(workflowStatePath(root), null)
  if (!manifest || !workflow) return

  const backlogVerifierAgent = await loadBacklogVerifierAgent(root)
  const pivot = inputs.pivot ?? await loadPivotState(root)
  const renderedStartHereWithPivot = renderStartHere(manifest, workflow, pivot, {
    nextAction: inputs.nextAction,
    backlogVerifierAgent,
    handoffStatus: inputs.handoffStatus,
  })
  const existingStartHere = await readText(startHerePath(root))
  await writeText(startHerePath(root), mergeStartHere(existingStartHere, renderedStartHereWithPivot))
  await writeText(contextSnapshotPath(root), renderContextSnapshot(manifest, workflow, pivot, inputs.contextNote))
  await writeText(latestHandoffPath(root), renderedStartHereWithPivot)
}
