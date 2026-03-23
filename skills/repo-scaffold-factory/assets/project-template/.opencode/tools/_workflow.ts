import { appendFile, copyFile, mkdir, readFile, stat, writeFile } from "node:fs/promises"
import { dirname, join } from "node:path"
import { createHash } from "node:crypto"

export type OverlapRisk = "low" | "medium" | "high"
export type ParallelMode = "parallel-lanes" | "sequential"
export type BootstrapStatus = "missing" | "ready" | "stale" | "failed"
export type TicketResolutionState = "open" | "done" | "reopened" | "superseded"
export type TicketVerificationState = "trusted" | "suspect" | "invalidated" | "reverified"
export type ArtifactTrustState = "current" | "superseded" | "invalidated"
export type DefectOutcome = "no_action" | "follow_up" | "invalidates_done" | "rollback_required"
export type TicketSourceMode = "process_verification" | "post_completion_issue" | "net_new_scope"

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
  source_ticket_id?: string
  follow_up_ticket_ids: string[]
  source_mode?: TicketSourceMode
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
  allowed_paths: string[]
}

export type WorkflowState = {
  active_ticket: string
  stage: string
  status: string
  approved_plan: boolean
  ticket_state: Record<string, TicketWorkflowState>
  process_version: number
  process_last_changed_at: string | null
  process_last_change_summary: string | null
  pending_process_verification: boolean
  parallel_mode: ParallelMode
  bootstrap: BootstrapState
  lane_leases: LaneLease[]
  state_revision: number
}

export type ArtifactRegistry = { version: number; artifacts: ArtifactRegistryEntry[] }

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

type StartHereOptions = { nextAction?: string; backlogVerifierAgent?: string }
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
  source_ticket_id?: string
  source_mode?: TicketSourceMode
}

const TICKET_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]*$/
const DEFAULT_PROCESS_VERSION = 5
const DEFAULT_TICKET_CONTRACT_VERSION = 3
const DEFAULT_BOOTSTRAP_STATE: BootstrapState = { status: "missing", last_verified_at: null, environment_fingerprint: null, proof_artifact: null }
const DEFAULT_TICKET_WORKFLOW_STATE: TicketWorkflowState = { approved_plan: false, reopen_count: 0, needs_reverification: false }

export const COARSE_STATUSES = new Set(["todo", "ready", "in_progress", "blocked", "review", "qa", "smoke_test", "done"])
export const ARTIFACT_REGISTRY_ROOT = ".opencode/state/artifacts"
export const LEGACY_REVIEW_STAGES = new Set(["code_review", "security_review"])
export const START_HERE_MANAGED_START = "<!-- SCAFFORGE:START_HERE_BLOCK START -->"
export const START_HERE_MANAGED_END = "<!-- SCAFFORGE:START_HERE_BLOCK END -->"
export const DEFAULT_OVERLAP_RISK: OverlapRisk = "high"
export const DEFAULT_PARALLEL_MODE: ParallelMode = "parallel-lanes"
export const MIN_EXECUTION_ARTIFACT_BYTES = 200

const EXECUTION_EVIDENCE_PATTERNS = [
  /```(?:bash|sh|shell|console|text)?[\s\S]*?(?:npm|pnpm|yarn|bun|pytest|cargo|go test|go vet|python(?:3)? -m|node(?:\s|$)|tsc(?:\s|$)|make(?:\s|$)|exit code|passed|failed)/i,
  /(?:^|\n)(?:\$ |>|command: ).*(?:npm|pnpm|yarn|bun|pytest|cargo|go test|go vet|python(?:3)? -m|node|tsc|make)/i,
  /\b(?:exit[_ -]?code|pass(?:ed)?|fail(?:ed)?|ok)\b/i,
]
const INSPECTION_ONLY_PATTERNS = [/code inspection/i, /inspection only/i]

export function rootPath(): string { return process.cwd() }
export function normalizeRepoPath(pathValue: string): string { return pathValue.replace(/\\/g, "/").replace(/^\.\//, "") }
export function ticketsManifestPath(root = rootPath()): string { return join(root, "tickets", "manifest.json") }
export function ticketsBoardPath(root = rootPath()): string { return join(root, "tickets", "BOARD.md") }
export function workflowStatePath(root = rootPath()): string { return join(root, ".opencode", "state", "workflow-state.json") }
export function artifactRegistryPath(root = rootPath()): string { return join(root, ".opencode", "state", "artifacts", "registry.json") }
export function invocationLogPath(root = rootPath()): string { return join(root, ".opencode", "state", "invocation-log.jsonl") }
export function bootstrapProvenancePath(root = rootPath()): string { return join(root, ".opencode", "meta", "bootstrap-provenance.json") }
export function contextSnapshotPath(root = rootPath()): string { return join(root, ".opencode", "state", "context-snapshot.md") }
export function latestHandoffPath(root = rootPath()): string { return join(root, ".opencode", "state", "latest-handoff.md") }
export function startHerePath(root = rootPath()): string { return join(root, "START-HERE.md") }
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
export function defaultArtifactPath(ticketId: string, stage: string, kind: string): string { return `${artifactStageDirectory(stage)}/${slugForPath(ticketId)}-${slugForPath(stage)}-${slugForPath(kind)}.md` }
export function defaultBootstrapProofPath(ticketId: string): string { return defaultArtifactPath(ticketId, "bootstrap", "environment-bootstrap") }

export async function readJson<T>(path: string, fallback?: T): Promise<T> {
  try { return JSON.parse(await readFile(path, "utf-8")) as T } catch (error) { if (fallback !== undefined) return fallback; throw error }
}
async function readText(path: string, fallback = ""): Promise<string> { try { return await readFile(path, "utf-8") } catch { return fallback } }
export async function writeJson(path: string, value: unknown): Promise<void> { await mkdir(dirname(path), { recursive: true }); await writeFile(path, `${JSON.stringify(value, null, 2)}\n`, "utf-8") }
export async function appendJsonl(path: string, value: unknown): Promise<void> { await mkdir(dirname(path), { recursive: true }); await appendFile(path, `${JSON.stringify(value)}\n`, "utf-8") }
export async function writeText(path: string, value: string): Promise<void> { await mkdir(dirname(path), { recursive: true }); await writeFile(path, value, "utf-8") }

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
function normalizeStringArray(value: unknown): string[] { return Array.isArray(value) ? value.flatMap((item) => typeof item === "string" && item.trim() ? [item.trim()] : []) : [] }
function normalizeNullableString(value: unknown): string | null { if (typeof value !== "string") return null; return value.trim() || null }
function normalizeOverlapRisk(value: unknown): OverlapRisk { return value === "low" || value === "medium" || value === "high" ? value : DEFAULT_OVERLAP_RISK }
function normalizeParallelMode(value: unknown): ParallelMode { return value === "parallel-lanes" || value === "sequential" ? value : DEFAULT_PARALLEL_MODE }
function normalizeResolutionState(value: unknown, status: string): TicketResolutionState { return value === "open" || value === "done" || value === "reopened" || value === "superseded" ? value : status === "done" ? "done" : "open" }
function normalizeVerificationState(value: unknown, status: string): TicketVerificationState { return value === "trusted" || value === "suspect" || value === "invalidated" || value === "reverified" ? value : status === "done" ? "trusted" : "suspect" }
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
  if (!ticketId || !isValidTicketId(ticketId) || !lane || !ownerAgent || !claimedAt) return null
  return {
    ticket_id: ticketId,
    lane,
    owner_agent: ownerAgent,
    write_lock: lease.write_lock !== false,
    claimed_at: claimedAt,
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
    source_ticket_id: normalizeNullableString(ticket.source_ticket_id) ?? undefined,
    follow_up_ticket_ids: normalizeStringArray(ticket.follow_up_ticket_ids),
    source_mode: ticket.source_mode === "process_verification" || ticket.source_mode === "post_completion_issue" || ticket.source_mode === "net_new_scope" ? ticket.source_mode : undefined,
  }
}

export async function loadManifest(root = rootPath()): Promise<Manifest> {
  const manifest = expectObject(await readJson<unknown>(ticketsManifestPath(root)), "Manifest")
  if (!Array.isArray(manifest.tickets)) throw new Error("tickets/manifest.json is missing a tickets array.")
  return {
    version: typeof manifest.version === "number" && manifest.version >= DEFAULT_TICKET_CONTRACT_VERSION ? manifest.version : DEFAULT_TICKET_CONTRACT_VERSION,
    project: typeof manifest.project === "string" && manifest.project.trim() ? manifest.project.trim() : "UNKNOWN",
    active_ticket: typeof manifest.active_ticket === "string" && manifest.active_ticket.trim() ? manifest.active_ticket.trim() : "UNKNOWN",
    tickets: manifest.tickets.map((ticket) => migrateTicket(ticket)),
  }
}
export async function loadArtifactRegistry(root = rootPath()): Promise<ArtifactRegistry> { return readJson<ArtifactRegistry>(artifactRegistryPath(root), { version: 2, artifacts: [] }) }
export async function loadWorkflowState(root = rootPath()): Promise<WorkflowState> {
  const fallback: WorkflowState = {
    active_ticket: "UNKNOWN", stage: "planning", status: "todo", approved_plan: false, ticket_state: {}, process_version: DEFAULT_PROCESS_VERSION,
    process_last_changed_at: null, process_last_change_summary: null, pending_process_verification: false, parallel_mode: DEFAULT_PARALLEL_MODE,
    bootstrap: { ...DEFAULT_BOOTSTRAP_STATE }, lane_leases: [], state_revision: 0,
  }
  const loaded = await readJson<unknown>(workflowStatePath(root), fallback)
  if (!loaded || typeof loaded !== "object" || Array.isArray(loaded)) return fallback
  const state = loaded as Record<string, unknown>
  const activeTicket = typeof state.active_ticket === "string" && state.active_ticket.trim() ? state.active_ticket.trim() : fallback.active_ticket
  const ticketState = normalizeTicketStateMap(state.ticket_state)
  const legacyApprovedPlan = typeof state.approved_plan === "boolean" ? state.approved_plan : false
  if (isValidTicketId(activeTicket) && !ticketState[activeTicket]) ticketState[activeTicket] = { ...DEFAULT_TICKET_WORKFLOW_STATE, approved_plan: legacyApprovedPlan }
  const workflow: WorkflowState = {
    active_ticket: activeTicket,
    stage: typeof state.stage === "string" && state.stage.trim() ? state.stage.trim() : fallback.stage,
    status: typeof state.status === "string" && state.status.trim() ? state.status.trim() : fallback.status,
    approved_plan: ticketState[activeTicket]?.approved_plan ?? legacyApprovedPlan,
    ticket_state: ticketState,
    process_version: typeof state.process_version === "number" && state.process_version > 0 ? state.process_version : DEFAULT_PROCESS_VERSION,
    process_last_changed_at: normalizeNullableString(state.process_last_changed_at),
    process_last_change_summary: normalizeNullableString(state.process_last_change_summary),
    pending_process_verification: state.pending_process_verification === true,
    parallel_mode: normalizeParallelMode(state.parallel_mode),
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
  workflow.bootstrap = await evaluateBootstrapState(workflow.bootstrap, root)
  return workflow
}
export async function saveWorkflowState(state: WorkflowState, root = rootPath(), expectedRevision?: number): Promise<void> {
  const current = await readJson<WorkflowState>(workflowStatePath(root), { ...state, state_revision: state.state_revision })
  const currentRevision = typeof current.state_revision === "number" ? current.state_revision : 0
  const expected = expectedRevision ?? state.state_revision
  if (expected !== currentRevision) throw new Error(`Workflow state changed concurrently. Expected revision ${expected}, found ${currentRevision}.`)
  state.state_revision = currentRevision + 1
  await writeJson(workflowStatePath(root), state)
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
  return /Overall Result:\s*PASS/i.test(content) ? null : "Smoke-test artifact must record an explicit PASS result before closeout."
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
  return workflow.bootstrap.status !== "ready" && workflow.lane_leases.length === 0 && ticket.wave === 0
}
export function claimLaneLease(workflow: WorkflowState, ticket: Ticket, ownerAgent: string, allowedPaths: string[], writeLock = true): LaneLease {
  const otherLeases = workflow.lane_leases.filter((lease) => lease.ticket_id !== ticket.id)
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
  const lease: LaneLease = { ticket_id: ticket.id, lane: ticket.lane, owner_agent: ownerAgent.trim(), write_lock: writeLock, claimed_at: new Date().toISOString(), allowed_paths: allowedPaths.map(normalizeRepoPath) }
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
  ticket.status = "done"
  ticket.resolution_state = "done"
  const state = ensureTicketWorkflowState(workflow, ticket.id)
  ticket.verification_state = state.needs_reverification || state.reopen_count > 0 ? "reverified" : "trusted"
  state.needs_reverification = false
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
    source_ticket_id: spec.source_ticket_id?.trim() || undefined,
    follow_up_ticket_ids: [],
    source_mode: spec.source_mode,
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
export async function saveManifest(manifest: Manifest, root = rootPath()): Promise<void> {
  manifest.version = Math.max(manifest.version || 0, DEFAULT_TICKET_CONTRACT_VERSION)
  await writeJson(ticketsManifestPath(root), manifest)
  await writeText(ticketsBoardPath(root), renderBoard(manifest))
  for (const ticket of manifest.tickets) await syncTicketFile(ticket, root)
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
}
export async function saveWorkflowBundle(bundle: SaveWorkflowBundle): Promise<void> {
  const root = bundle.root ?? rootPath()
  await saveWorkflowState(bundle.workflow, root, bundle.expectedRevision)
  if (bundle.manifest) await saveManifest(bundle.manifest, root)
  if (bundle.registry) await saveArtifactRegistry(bundle.registry, root)
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
export function renderContextSnapshot(manifest: Manifest, workflow: WorkflowState, note?: string): string {
  const ticket = getTicket(manifest, workflow.active_ticket)
  const ticketState = getTicketWorkflowState(workflow, ticket.id)
  const leases = workflow.lane_leases.length > 0 ? workflow.lane_leases.map((lease) => `- ${lease.ticket_id}: ${lease.owner_agent} (${lease.lane})`).join("\n") : "- No active lane leases"
  const artifactLines = ticket.artifacts.length > 0 ? ticket.artifacts.slice(-5).map(renderArtifactLine).join("\n") : "- No artifacts recorded yet"
  const noteBlock = note ? `\n## Note\n\n${note}\n` : ""
  return `# Context Snapshot\n\n## Project\n\n${manifest.project}\n\n## Active Ticket\n\n- ID: ${ticket.id}\n- Title: ${ticket.title}\n- Stage: ${ticket.stage}\n- Status: ${ticket.status}\n- Resolution: ${ticket.resolution_state}\n- Verification: ${ticket.verification_state}\n- Approved plan: ${workflow.approved_plan ? "yes" : "no"}\n- Needs reverification: ${ticketState.needs_reverification ? "yes" : "no"}\n\n## Bootstrap\n\n- status: ${workflow.bootstrap.status}\n- last_verified_at: ${workflow.bootstrap.last_verified_at || "Not yet verified."}\n- proof_artifact: ${workflow.bootstrap.proof_artifact || "None"}\n\n## Process State\n\n- process_version: ${workflow.process_version}\n- pending_process_verification: ${workflow.pending_process_verification ? "true" : "false"}\n- parallel_mode: ${workflow.parallel_mode}\n- state_revision: ${workflow.state_revision}\n\n## Lane Leases\n\n${leases}\n\n## Recent Artifacts\n\n${artifactLines}${noteBlock}`
}
export function renderStartHere(manifest: Manifest, workflow: WorkflowState, options: StartHereOptions = {}): string {
  const ticket = getTicket(manifest, workflow.active_ticket)
  const reopened = manifest.tickets.filter((item) => item.resolution_state === "reopened")
  const suspectDone = manifest.tickets.filter((item) => item.status === "done" && item.verification_state !== "trusted" && item.verification_state !== "reverified")
  const reverification = manifest.tickets.filter((item) => getTicketWorkflowState(workflow, item.id).needs_reverification)
  const verifierLabel = options.backlogVerifierAgent ? `\`${options.backlogVerifierAgent}\`` : "the backlog verifier"
  const recommendedAction = options.nextAction || (workflow.pending_process_verification ? `Use the team leader to route ${verifierLabel} across done tickets whose trust predates the current process contract.` : workflow.bootstrap.status !== "ready" ? "Run environment_bootstrap, register its proof artifact, then continue ticket execution." : "Continue the required internal lifecycle from the current ticket stage.")
  const lines = (items: Ticket[]) => items.length > 0 ? items.map((item) => `- ${item.id}: ${item.title}`).join("\n") : "- None"
  return `# START HERE\n\n${START_HERE_MANAGED_START}\n## Project\n\n${manifest.project}\n\n## Workflow State\n\n- process_version: ${workflow.process_version}\n- parallel_mode: ${workflow.parallel_mode}\n- pending_process_verification: ${workflow.pending_process_verification ? "true" : "false"}\n- bootstrap_status: ${workflow.bootstrap.status}\n- bootstrap_proof: ${workflow.bootstrap.proof_artifact || "None"}\n\n## Current Ticket\n\n- ID: ${ticket.id}\n- Title: ${ticket.title}\n- Wave: ${ticket.wave}\n- Lane: ${ticket.lane}\n- Stage: ${ticket.stage}\n- Status: ${ticket.status}\n- Resolution: ${ticket.resolution_state}\n- Verification: ${ticket.verification_state}\n\n## Reopened Tickets\n\n${lines(reopened)}\n\n## Done But Not Fully Trusted\n\n${lines(suspectDone)}\n\n## Pending Reverification\n\n${lines(reverification)}\n\n## Read In This Order\n\n1. README.md\n2. AGENTS.md\n3. docs/spec/CANONICAL-BRIEF.md\n4. docs/process/workflow.md\n5. tickets/BOARD.md\n6. tickets/manifest.json\n\n## Next Action\n\n${recommendedAction}\n${START_HERE_MANAGED_END}\n`
}
function escapeRegExp(value: string): string { return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") }
export function mergeStartHere(existing: string, rendered: string): string {
  const pattern = new RegExp(`${escapeRegExp(START_HERE_MANAGED_START)}[\\s\\S]*?${escapeRegExp(START_HERE_MANAGED_END)}`, "m")
  const renderedBlock = rendered.match(pattern)
  if (!renderedBlock) return rendered
  if (!existing.trim()) return rendered
  if (!existing.includes(START_HERE_MANAGED_START) || !existing.includes(START_HERE_MANAGED_END)) return existing
  return existing.replace(pattern, renderedBlock[0])
}
