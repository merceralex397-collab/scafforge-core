import { tool } from "@opencode-ai/plugin"
import { spawn } from "node:child_process"
import { existsSync } from "node:fs"
import { access, readFile } from "node:fs/promises"
import { basename, join } from "node:path"
import {
  currentArtifacts,
  defaultArtifactPath,
  findExistingRepoVenvExecutable,
  getTicket,
  latestArtifact,
  loadArtifactRegistry,
  loadManifest,
  loadWorkflowState,
  markTicketSmokeVerified,
  normalizeRepoPath,
  registerArtifactSnapshot,
  requireBootstrapReady,
  rootPath,
  saveArtifactRegistry,
  saveManifest,
  saveWorkflowBundle,
  writeText,
} from "../lib/workflow"

type PackageJson = {
  packageManager?: string
  scripts?: Record<string, string>
}

type CommandSpec = {
  label: string
  argv: string[]
  reason: string
  env_overrides?: Record<string, string>
}

type CommandResult = CommandSpec & {
  exit_code: number
  duration_ms: number
  stdout: string
  stderr: string
  missing_executable?: string
  failure_classification?: "missing_executable" | "permission_restriction" | "syntax_error" | "test_failure" | "configuration_error" | "command_error"
  blocked_by_permissions?: boolean
}

type PythonRunner = {
  label: string
  argv: string[]
  reason: string
}
type SmokeArgs = {
  ticket_id?: string
  scope?: string
  test_paths?: string[]
  command_override?: string[]
}

const SMOKE_STAGE = "smoke-test"
const SMOKE_KIND = "smoke-test"
const ENV_ASSIGNMENT_PATTERN = /^[A-Za-z_][A-Za-z0-9_]*=.*/
const SMOKE_COMMAND_PATTERNS = [
  /\bpytest\b/i,
  /\bpython(?:3)?\s+-m\s+pytest\b/i,
  /\b(?:uv\s+run\s+)?ruff\s+check\b/i,
  /\bcargo\s+test\b/i,
  /\bgo\s+test\b/i,
  /\b(?:npm|pnpm)\s+run\s+(?:test|check)\b/i,
  /\byarn\s+(?:test|check)\b/i,
  /\bbun\s+run\s+(?:test|check)\b/i,
  /\bgodot(?:4)?\s+--headless\b/i,
  // Gradle smoke detection includes `(?:\./gradlew|gradle)\s+test`.
  /\b(?:\.\/gradlew|gradle)\s+test\b/i,
  /\bmvn\s+test\b/i,
  /\bdotnet\s+test\b/i,
  /\bflutter\s+test\b/i,
  /\bswift\s+test\b/i,
  /\bxcodebuild\s+test\b/i,
  /\bzig\s+test\b/i,
  /\bmake\s+(?:test|check)\b/i,
  /\b(?:ruby|rspec|rake\s+test)\b/i,
  /\bmix\s+test\b/i,
  /\b(?:phpunit|php\s+[^\n]*test)\b/i,
  /\bcmake\s+--build\b/i,
  /\b(?:gcc|g\+\+|clang|clang\+\+)\b[\s\S]*&&\s*\.\/a\.out\b/i,
]

async function exists(path: string): Promise<boolean> {
  try {
    await access(path)
    return true
  } catch {
    return false
  }
}

async function readJson<T>(path: string): Promise<T | undefined> {
  try {
    return JSON.parse(await readFile(path, "utf-8")) as T
  } catch {
    return undefined
  }
}
async function readText(path: string): Promise<string> {
  try {
    return await readFile(path, "utf-8")
  } catch {
    return ""
  }
}
function hasSectionValue(text: string, section: string, key: string): boolean {
  const blockMatch = text.match(new RegExp(`\\[${section.replace(".", "\\.")}\\]([\\s\\S]*?)(?:\\n\\[|$)`, "m"))
  if (!blockMatch) return false
  return new RegExp(`^\\s*${key.replace("-", "\\-")}\\s*=\\s*(?:\\[|\\{)`, "m").test(blockMatch[1] || "")
}
// Mirror bootstrap detection for [tool.pytest.ini_options] so pyproject-only pytest repos are not skipped.
function hasPyprojectPytestConfig(pyprojectText: string): boolean {
  return /\[tool\.pytest\.ini_options\]/m.test(pyprojectText)
}
function hasPyprojectDevExtra(pyprojectText: string): boolean {
  return hasSectionValue(pyprojectText, "project.optional-dependencies", "dev")
}
function hasPyprojectDevDependencyGroup(pyprojectText: string): boolean {
  return hasSectionValue(pyprojectText, "dependency-groups", "dev")
}
function hasPyprojectUvDevDependencies(pyprojectText: string): boolean {
  return /\[tool\.uv(?:\.[^\]]+)?\][\s\S]*?^\s*dev-dependencies\s*=/m.test(pyprojectText) || /\[tool\.uv\.dev-dependencies\]/m.test(pyprojectText)
}
function detectUvRunDependencyArgs(pyprojectText: string): string[] {
  if (hasPyprojectDevExtra(pyprojectText)) return ["--extra", "dev"]
  if (hasPyprojectDevDependencyGroup(pyprojectText)) return ["--group", "dev"]
  if (hasPyprojectUvDevDependencies(pyprojectText)) return ["--all-extras"]
  return []
}

function choosePackageManager(root: string, packageJson: PackageJson | undefined): "npm" | "pnpm" | "yarn" | "bun" {
  const declared = packageJson?.packageManager?.toLowerCase() || ""
  if (declared.startsWith("pnpm")) return "pnpm"
  if (declared.startsWith("yarn")) return "yarn"
  if (declared.startsWith("bun")) return "bun"
  if (declared.startsWith("npm")) return "npm"
  if (existsSync(join(root, "pnpm-lock.yaml"))) return "pnpm"
  if (existsSync(join(root, "yarn.lock"))) return "yarn"
  if (existsSync(join(root, "bun.lock")) || existsSync(join(root, "bun.lockb"))) return "bun"
  return "npm"
}

function packageCommand(manager: "npm" | "pnpm" | "yarn" | "bun", script: string): string[] {
  if (manager === "yarn") return ["yarn", script]
  if (manager === "bun") return ["bun", "run", script]
  if (manager === "pnpm") return ["pnpm", "run", script]
  return ["npm", "run", script]
}

async function detectNodeCommands(root: string): Promise<CommandSpec[]> {
  const packagePath = join(root, "package.json")
  if (!(await exists(packagePath))) {
    return []
  }

  const packageJson = await readJson<PackageJson>(packagePath)
  const scripts = packageJson?.scripts || {}
  const manager = choosePackageManager(root, packageJson)

  for (const explicit of ["smoke-test", "smoke_test"]) {
    if (scripts[explicit]) {
      return [
        {
          label: `package script ${explicit}`,
          argv: packageCommand(manager, explicit),
          reason: "Project-defined smoke-test override",
        },
      ]
    }
  }

  const commands: CommandSpec[] = []
  for (const script of ["check", "build", "test"]) {
    if (!scripts[script]) continue
    commands.push({
      label: `package script ${script}`,
      argv: packageCommand(manager, script),
      reason: `Detected ${script} script in package.json`,
    })
  }
  return commands
}

function extractBacktickedCommands(text: string): string[] {
  return Array.from(text.matchAll(/`([^`\n]+)`/g), (match) => match[1]?.trim() || "").filter(Boolean)
}

function looksLikeSmokeCommand(command: string): boolean {
  return SMOKE_COMMAND_PATTERNS.some((pattern) => pattern.test(command))
}

function renderCommand(command: Pick<CommandSpec, "argv" | "env_overrides">): string {
  const envPrefix = command.env_overrides
    ? Object.entries(command.env_overrides)
        .map(([key, value]) => `${key}=${value}`)
        .join(" ")
    : ""
  return `${envPrefix ? `${envPrefix} ` : ""}${command.argv.join(" ")}`.trim()
}

function isPermissionRestrictionOutput(output: string): boolean {
  return /permission denied|operation not permitted|EACCES|EPERM|blocked by permission rules/i.test(output)
}

function inferAcceptanceSmokeCommands(ticket: { acceptance?: unknown }): CommandSpec[] {
  const commands: CommandSpec[] = []
  const seen = new Set<string>()
  const acceptanceItems = Array.isArray(ticket.acceptance) ? ticket.acceptance : []

  for (const item of acceptanceItems) {
    if (typeof item !== "string") continue
    for (const candidate of extractBacktickedCommands(item)) {
      if (!looksLikeSmokeCommand(candidate)) continue
      const normalized = candidate.trim().toLowerCase()
      if (seen.has(normalized)) continue
      const parsed = parseCommandOverride([candidate])[0]
      commands.push({
        ...parsed,
        label: `acceptance command ${commands.length + 1}`,
        reason: "Ticket acceptance criteria define an explicit smoke-test command.",
      })
      seen.add(normalized)
    }
  }

  return commands
}

async function detectPythonRunner(root: string, pyprojectText: string): Promise<PythonRunner> {
  if (await exists(join(root, "uv.lock"))) {
    return {
      label: "uv-managed python",
      argv: ["uv", "run", ...detectUvRunDependencyArgs(pyprojectText), "python"],
      reason: "Detected uv.lock; using repo-managed uv runtime",
    }
  }

  const repoVenvPython = await findExistingRepoVenvExecutable(root, "python")
  if (repoVenvPython) {
    return {
      label: "repo-local python",
      argv: [repoVenvPython],
      reason: "Detected repo-local .venv; using project virtualenv interpreter",
    }
  }

  return {
    label: "system python",
    argv: ["python3"],
    reason: "No repo-managed Python runtime detected; falling back to system python",
  }
}

async function detectPythonCompileCommand(root: string, pyprojectText?: string): Promise<CommandSpec | null> {
  const pythonSignals = ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"]
  const hasPythonProject = await Promise.all(pythonSignals.map((name) => exists(join(root, name)))).then((hits) => hits.some(Boolean))
  if (!hasPythonProject) {
    return null
  }
  const resolvedPyprojectText = pyprojectText ?? await readText(join(root, "pyproject.toml"))
  const pythonRunner = await detectPythonRunner(root, resolvedPyprojectText)

  return {
    label: "python compileall",
    argv: [
      ...pythonRunner.argv,
      "-m",
      "compileall",
      "-q",
      "-x",
      "(^|/)(\\.git|\\.opencode|node_modules|dist|build|out|venv|\\.venv|__pycache__)(/|$)",
      ".",
    ],
    reason: `${pythonRunner.reason}; generic Python syntax smoke check`,
  }
}

async function detectPythonCommands(root: string, args: SmokeArgs): Promise<CommandSpec[]> {
  const pythonSignals = ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"]
  const hasPythonProject = await Promise.all(pythonSignals.map((name) => exists(join(root, name)))).then((hits) => hits.some(Boolean))
  if (!hasPythonProject) {
    return []
  }
  const pyprojectText = await readText(join(root, "pyproject.toml"))
  const pythonRunner = await detectPythonRunner(root, pyprojectText)
  const compileCommand = await detectPythonCompileCommand(root, pyprojectText)
  const commands: CommandSpec[] = compileCommand ? [compileCommand] : []

  const hasPytestSurface = (await exists(join(root, "tests"))) || (await exists(join(root, "pytest.ini"))) || hasPyprojectPytestConfig(pyprojectText)
  if (hasPytestSurface) {
    const testTargets = Array.isArray(args.test_paths) && args.test_paths.length > 0 ? args.test_paths : []
    commands.push({
      label: "pytest",
      argv: [...pythonRunner.argv, "-m", "pytest", ...testTargets],
      reason: testTargets.length > 0
        ? `${pythonRunner.reason}; running ticket-scoped Python tests`
        : `${pythonRunner.reason}; detected Python test surface`,
    })
  }

  return commands
}

async function detectAcceptanceCommands(root: string, ticket: { acceptance?: unknown }): Promise<CommandSpec[]> {
  const acceptanceCommands = inferAcceptanceSmokeCommands(ticket)
  if (acceptanceCommands.length === 0) {
    return []
  }
  const seen = new Set<string>()
  return acceptanceCommands.filter((command) => {
    const key = renderCommand(command)
    if (seen.has(key)) {
      return false
    }
    seen.add(key)
    return true
  })
}

async function augmentGodotReleaseCommands(
  root: string,
  ticket: { id?: unknown, lane?: unknown },
  commands: CommandSpec[],
): Promise<CommandSpec[]> {
  if (!(await exists(join(root, "project.godot")))) {
    return commands
  }
  const ticketId = typeof ticket.id === "string" ? ticket.id.trim().toUpperCase() : ""
  const lane = typeof ticket.lane === "string" ? ticket.lane.trim().toLowerCase() : ""
  const isReleaseValidationTicket = (
    ticketId === "RELEASE-001"
    || ticketId === "FINISH-VALIDATE-001"
    || lane === "release-readiness"
    || lane === "finish-validation"
  )
  if (!isReleaseValidationTicket) {
    return commands
  }
  const exportCommand = commands.find((command) => isGodotExportCommand(command.argv))
  if (!exportCommand) {
    return commands
  }
  const loadValidation: CommandSpec = {
    label: "godot load validation",
    argv: [exportCommand.argv[0] ?? "godot4", "--headless", "--path", ".", "--quit"],
    reason: "Godot release/finish proof must also confirm the project loads cleanly, not just that export exits successfully.",
    env_overrides: exportCommand.env_overrides,
  }
  const signature = renderCommand(loadValidation).toLowerCase()
  if (commands.some((command) => renderCommand(command).toLowerCase() === signature)) {
    return commands
  }
  return [...commands, loadValidation]
}

async function detectRustCommands(root: string): Promise<CommandSpec[]> {
  if (!(await exists(join(root, "Cargo.toml")))) {
    return []
  }

  return [
    { label: "cargo check", argv: ["cargo", "check"], reason: "Rust compile smoke check" },
    { label: "cargo test", argv: ["cargo", "test"], reason: "Rust test suite" },
  ]
}

async function detectGoCommands(root: string): Promise<CommandSpec[]> {
  if (!(await exists(join(root, "go.mod")))) {
    return []
  }

  return [{ label: "go test ./...", argv: ["go", "test", "./..."], reason: "Go test suite" }]
}

async function detectMakeSmokeTarget(root: string): Promise<CommandSpec[]> {
  for (const fileName of ["Makefile", "makefile", "GNUmakefile"]) {
    const path = join(root, fileName)
    if (!(await exists(path))) continue
    const content = await readFile(path, "utf-8").catch(() => "")
    if (/^smoke-test\s*:/m.test(content)) {
      return [{ label: "make smoke-test", argv: ["make", "smoke-test"], reason: `${fileName} override target` }]
    }
    if (/^smoke_test\s*:/m.test(content)) {
      return [{ label: "make smoke_test", argv: ["make", "smoke_test"], reason: `${fileName} override target` }]
    }
  }
  return []
}

function looksLikeShellStyleOverride(command: string): boolean {
  return /\s|["'`;&|]/.test(command.trim())
}

function tokenizeCommandString(command: string): string[] {
  const tokens: string[] = []
  let current = ""
  let quote: '"' | "'" | null = null
  let escaped = false

  for (const char of command) {
    if (quote === "'") {
      if (char === quote) {
        quote = null
      } else {
        current += char
      }
      continue
    }
    if (escaped) {
      current += char
      escaped = false
      continue
    }
    if (char === "\\") {
      escaped = true
      continue
    }
    if (quote) {
      if (char === quote) {
        quote = null
      } else {
        current += char
      }
      continue
    }
    if (char === '"' || char === "'") {
      quote = char
      continue
    }
    if (/\s/.test(char)) {
      if (current) {
        tokens.push(current)
        current = ""
      }
      continue
    }
    current += char
  }

  if (escaped) {
    current += "\\"
  }
  if (quote) {
    throw new Error("command_override contains an unmatched quote.")
  }
  if (current) {
    tokens.push(current)
  }
  return tokens
}

function parseOverrideTokens(tokens: string[], label: string): CommandSpec {
  const env_overrides: Record<string, string> = {}

  while (tokens.length > 0 && ENV_ASSIGNMENT_PATTERN.test(tokens[0] ?? "")) {
    const assignment = tokens.shift() ?? ""
    const separator = assignment.indexOf("=")
    if (separator <= 0) {
      break
    }
    env_overrides[assignment.slice(0, separator)] = assignment.slice(separator + 1)
  }

  if (tokens.length === 0) {
    throw new Error("command_override must include an executable after any leading KEY=VALUE environment assignments.")
  }

  return {
    label,
    argv: tokens,
    reason: "Explicit smoke-test command override supplied by the caller.",
    env_overrides: Object.keys(env_overrides).length > 0 ? env_overrides : undefined,
  }
}

function isSyntaxErrorOutput(output: string): boolean {
  return /syntax error|parse error|failed to load script|not declared in the current scope|not found in base self|unexpected token|missing language argument|unterminated|unmatched quote/i.test(output)
}

function isConfigurationErrorOutput(output: string): boolean {
  return /configuration error|invalid config|misconfig|unknown option|invalid argument|requires a value/i.test(output)
}

function classifyCommandFailure(args: {
  argv: string[]
  exitCode: number
  stdout: string
  stderr: string
  missingExecutable?: string
  blockedByPermissions?: boolean
}): CommandResult["failure_classification"] {
  const output = `${args.stdout}\n${args.stderr}`
  if (args.missingExecutable) return "missing_executable"
  if (args.blockedByPermissions) return "permission_restriction"
  if (args.exitCode === 0 && isGodotExportCommand(args.argv) && isSyntaxErrorOutput(output)) return undefined
  if (isSyntaxErrorOutput(output)) return "syntax_error"
  if (isConfigurationErrorOutput(output)) return "configuration_error"
  if (args.exitCode === 0) return undefined
  if (output.trim()) return "test_failure"
  return "command_error"
}

function isGodotExportCommand(argv: string[]): boolean {
  const executable = basename(argv[0] ?? "").toLowerCase()
  if (!/^godot(?:[\d.]+)?$/.test(executable)) {
    return false
  }
  return argv.some((arg) => /^--export(?:-debug|-release)?$/.test(arg))
}

function commandBlocksPass(command: Pick<CommandResult, "exit_code" | "failure_classification">): boolean {
  return (
    command.exit_code !== 0
    || command.failure_classification === "syntax_error"
    || command.failure_classification === "configuration_error"
  )
}

function parseCommandOverride(rawOverride: string[]): CommandSpec[] {
  if (rawOverride.length === 0) {
    return []
  }
  if (rawOverride.length === 1) {
    return [parseOverrideTokens(tokenizeCommandString(rawOverride[0] ?? ""), "command override 1")]
  }

  const shellStyleEntries = rawOverride.filter((item) => looksLikeShellStyleOverride(item))
  if (shellStyleEntries.length === 0) {
    return [parseOverrideTokens([...rawOverride], "command override 1")]
  }
  if (shellStyleEntries.length !== rawOverride.length) {
    throw new Error("command_override cannot mix tokenized argv entries with multiple shell-style command strings.")
  }

  return rawOverride.map((command, index) => parseOverrideTokens(tokenizeCommandString(command), `command override ${index + 1}`))
}

async function detectCommands(root: string, ticket: { acceptance?: unknown }, args: SmokeArgs): Promise<CommandSpec[]> {
  if (Array.isArray(args.command_override) && args.command_override.length > 0) {
    return augmentGodotReleaseCommands(root, ticket, parseCommandOverride(args.command_override))
  }
  const acceptanceCommands = await detectAcceptanceCommands(root, ticket)
  if (acceptanceCommands.length > 0) {
    return augmentGodotReleaseCommands(root, ticket, acceptanceCommands)
  }
  const makeOverride = await detectMakeSmokeTarget(root)
  if (makeOverride.length > 0) {
    return makeOverride
  }

  const commands = [
    ...(await detectNodeCommands(root)),
    ...(await detectPythonCommands(root, args)),
    ...(await detectRustCommands(root)),
    ...(await detectGoCommands(root)),
  ]

  const seen = new Set<string>()
  return commands.filter((command) => {
    const key = renderCommand(command)
    if (seen.has(key)) {
      return false
    }
    seen.add(key)
    return true
  })
}

async function runCommand(root: string, command: CommandSpec): Promise<CommandResult> {
  return new Promise((resolve) => {
    const startedAt = Date.now()
    let stdout = ""
    let stderr = ""
    let settled = false

    let child
    try {
      child = spawn(command.argv[0], command.argv.slice(1), {
        cwd: root,
        env: {
          ...process.env,
          ...(command.env_overrides ?? {}),
        },
        stdio: ["ignore", "pipe", "pipe"],
      })
    } catch (error) {
      const errorCode = typeof error === "object" && error && "code" in error ? String((error as { code?: string }).code || "") : ""
      const errorStderr = String(error)
      const missingExecutable = errorCode === "ENOENT" ? command.argv[0] : undefined
      const blockedByPermissions = errorCode === "EACCES" || errorCode === "EPERM" || isPermissionRestrictionOutput(errorStderr)
      resolve({
        ...command,
        exit_code: -1,
        duration_ms: Date.now() - startedAt,
        stdout: "",
        stderr: errorStderr,
        missing_executable: missingExecutable,
        failure_classification: classifyCommandFailure({ argv: command.argv, exitCode: -1, stdout: "", stderr: errorStderr, missingExecutable, blockedByPermissions }),
        blocked_by_permissions: blockedByPermissions || undefined,
      })
      return
    }

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString()
    })
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString()
    })
    child.on("error", (error) => {
      if (settled) return
      settled = true
      const errorCode = typeof error === "object" && error && "code" in error ? String((error as { code?: string }).code || "") : ""
      const renderedError = `${stderr}\n${String(error)}`.trim()
      const missingExecutable = errorCode === "ENOENT" ? command.argv[0] : undefined
      const blockedByPermissions = errorCode === "EACCES" || errorCode === "EPERM" || isPermissionRestrictionOutput(renderedError)
      resolve({
        ...command,
        exit_code: -1,
        duration_ms: Date.now() - startedAt,
        stdout,
        stderr: renderedError,
        missing_executable: missingExecutable,
        failure_classification: classifyCommandFailure({ argv: command.argv, exitCode: -1, stdout, stderr: renderedError, missingExecutable, blockedByPermissions }),
        blocked_by_permissions: blockedByPermissions || undefined,
      })
    })
    child.on("close", (code) => {
      if (settled) return
      settled = true
      const renderedStderr = stderr.trim()
      const missingExecutable = code === 127 || /command not found|ENOENT/i.test(renderedStderr) ? command.argv[0] : undefined
      const blockedByPermissions = isPermissionRestrictionOutput(`${stdout}\n${stderr}`)
      resolve({
        ...command,
        exit_code: code ?? -1,
        duration_ms: Date.now() - startedAt,
        stdout,
        stderr,
        missing_executable: missingExecutable,
        failure_classification: classifyCommandFailure({ argv: command.argv, exitCode: code ?? -1, stdout, stderr, missingExecutable, blockedByPermissions }),
        blocked_by_permissions: blockedByPermissions || undefined,
      })
    })
  })
}

function fence(body: string): string {
  const cleaned = body.trimEnd() || "<no output>"
  return `~~~~text\n${cleaned}\n~~~~`
}

function renderArtifact(ticketId: string, commands: CommandResult[], passed: boolean, note: string): string {
  const commandSections = commands.length
    ? commands
        .map(
          (command, index) => `### ${index + 1}. ${command.label}\n\n- reason: ${command.reason}\n- command: \`${renderCommand(command)}\`\n- exit_code: ${command.exit_code}\n- duration_ms: ${command.duration_ms}\n- missing_executable: ${command.missing_executable || "none"}\n- failure_classification: ${command.failure_classification || "none"}\n- blocked_by_permissions: ${command.blocked_by_permissions ? "true" : "false"}\n\n#### stdout\n\n${fence(command.stdout)}\n\n#### stderr\n\n${fence(command.stderr)}`,
        )
        .join("\n\n")
    : "No deterministic smoke-test commands were detected."

  return `# Smoke Test\n\n## Ticket\n\n- ${ticketId}\n\n## Overall Result\n\nOverall Result: ${passed ? "PASS" : "FAIL"}\n\n## Notes\n\n${note}\n\n## Commands\n\n${commandSections}\n`
}

function classifyCommandKind(command: CommandResult): "build_or_quality_gate" | "test_or_runtime" | "other" {
  const rendered = `${command.label} ${renderCommand(command)}`.toLowerCase()
  if (/(build|check|lint|clippy|vet|typecheck|tsc|compile|analy[sz]e)/.test(rendered)) {
    return "build_or_quality_gate"
  }
  if (/(test|pytest|rspec|phpunit|godot|xcodebuild)/.test(rendered)) {
    return "test_or_runtime"
  }
  return "other"
}
function classifySmokeFailure(results: CommandResult[]): "environment" | "ticket" | "configuration" | null {
  const failed = results.find((command) => commandBlocksPass(command))
  if (!failed) return null
  const output = `${failed.stdout}\n${failed.stderr}`
  if (failed.failure_classification === "syntax_error" || failed.failure_classification === "configuration_error") {
    return "configuration"
  }
  if (failed.exit_code === -1 || failed.failure_classification === "missing_executable" || /No module named|command not found|ENOENT|not installed|missing/i.test(output)) {
    return "environment"
  }
  if (/No deterministic smoke-test command/i.test(output)) {
    return "configuration"
  }
  return "ticket"
}

function classifyHostSurfaceFailure(results: CommandResult[]): "missing_executable" | "permission_restriction" | "runtime_setup" | null {
  const failed = results.find((command) => commandBlocksPass(command))
  if (!failed) return null
  if (failed.failure_classification === "missing_executable" || failed.missing_executable) {
    return "missing_executable"
  }
  if (failed.failure_classification === "permission_restriction" || failed.blocked_by_permissions) {
    return "permission_restriction"
  }
  if (classifySmokeFailure(results) !== "environment") {
    return null
  }
  const output = `${failed.stdout}\n${failed.stderr}`
  if (/No module named|not installed|missing/i.test(output)) {
    return "runtime_setup"
  }
  return null
}

async function persistArtifact(ticketId: string, body: string, passed: boolean): Promise<string> {
  const manifest = await loadManifest()
  const workflow = await loadWorkflowState()
  const ticket = getTicket(manifest, ticketId)
  const path = normalizeRepoPath(defaultArtifactPath(ticket.id, SMOKE_STAGE, SMOKE_KIND))
  await writeText(path, body)

  const registry = await loadArtifactRegistry()
  const artifact = await registerArtifactSnapshot({
    ticket,
    registry,
    source_path: path,
    kind: SMOKE_KIND,
    stage: SMOKE_STAGE,
    summary: passed ? "Deterministic smoke test passed." : "Deterministic smoke test failed.",
  })

  if (passed) {
    markTicketSmokeVerified(ticket)
  }
  await saveWorkflowBundle({ workflow, manifest, registry, skipGraphValidation: true })
  return artifact.path
}

export default tool({
  description: "Run deterministic smoke-test commands, write a canonical smoke-test artifact, and report pass or fail.",
  args: {
    ticket_id: tool.schema.string().describe("Optional ticket id. Defaults to the active ticket.").optional(),
    scope: tool.schema.string().describe("Optional smoke-test scope hint such as full-suite or ticket.").optional(),
    test_paths: tool.schema.array(tool.schema.string()).describe("Optional scoped pytest paths to run instead of the full detected Python suite.").optional(),
    command_override: tool.schema.array(tool.schema.string()).describe("Optional explicit smoke-test command override. Accepts tokenized argv for one command, one shell-style command string, or multiple shell-style command strings executed in order. Leading KEY=VALUE entries are treated as environment overrides.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const ticket = getTicket(manifest, args.ticket_id)
    const root = rootPath()
    await requireBootstrapReady(workflow, root)
    const latestQaArtifact = latestArtifact(ticket, { stage: "qa", trust_state: "current" }) || currentArtifacts(ticket, { stage: "qa" }).at(-1)

    if (!latestQaArtifact) {
      throw new Error(`Cannot run smoke tests for ${ticket.id} before a QA artifact exists.`)
    }

    let commands: CommandSpec[] = []
    try {
      commands = await detectCommands(root, ticket, args)
    } catch (error) {
      const body = renderArtifact(
        ticket.id,
        [],
        false,
        `The smoke-test run failed because command_override is malformed: ${String(error)}`,
      )
      const artifactPath = await persistArtifact(ticket.id, body, false)
      return JSON.stringify(
        {
          ticket_id: ticket.id,
          passed: false,
          qa_artifact: latestQaArtifact.path,
          smoke_test_artifact: artifactPath,
          scope: args.scope || null,
          test_paths: args.test_paths || [],
          failure_classification: "configuration",
          blocker: String(error),
        },
        null,
        2,
      )
    }
    if (commands.length === 0) {
      const body = renderArtifact(
        ticket.id,
        [],
        false,
        "No deterministic smoke-test command was detected. Add a project smoke-test command or standard build or test scripts, then rerun the smoke-test stage.",
      )
      const artifactPath = await persistArtifact(ticket.id, body, false)
      return JSON.stringify(
        {
          ticket_id: ticket.id,
          passed: false,
          qa_artifact: latestQaArtifact.path,
          smoke_test_artifact: artifactPath,
          commands: [],
          failure_classification: "configuration",
          blocker: "No deterministic smoke-test commands detected.",
        },
        null,
        2,
      )
    }

    const results: CommandResult[] = []
    let passed = true
    for (const command of commands) {
      const result = await runCommand(root, command)
      results.push(result)
      if (commandBlocksPass(result)) {
        passed = false
        break
      }
    }
    const failureClassification = classifySmokeFailure(results)
    const hostSurfaceClassification = classifyHostSurfaceFailure(results)
    const failedCommand = results.find((result) => commandBlocksPass(result))
    const failedCommandKind = failedCommand ? classifyCommandKind(failedCommand) : null

    const note = passed
      ? "All detected deterministic smoke-test commands passed."
      : hostSurfaceClassification === "permission_restriction"
        ? "The smoke-test run failed because the host denied a required command or file access path. Fix the permission/tool policy or run the canonical smoke command in an allowed host context before treating this as a ticket regression."
      : failureClassification === "environment"
        ? "The smoke-test run failed because the environment or required toolchain is not ready. Fix bootstrap/runtime setup before treating this as a ticket regression."
        : failureClassification === "configuration"
          ? "The smoke-test run failed because the smoke-test surface is not configured correctly."
          : failedCommand && failedCommandKind === "build_or_quality_gate"
            ? `The smoke-test run failed on the build or quality gate command \`${failedCommand.label}\`. Inspect the recorded command output before closeout and do not treat this as a generic test-only failure.`
          : "The smoke-test run stopped on the first failing command. Inspect the recorded output before closeout."
    const body = renderArtifact(ticket.id, results, passed, note)
    const artifactPath = await persistArtifact(ticket.id, body, passed)

    return JSON.stringify(
      {
        ticket_id: ticket.id,
        passed,
        qa_artifact: latestQaArtifact.path,
        smoke_test_artifact: artifactPath,
        scope: args.scope || (args.test_paths && args.test_paths.length > 0 ? "ticket" : "full-suite"),
        test_paths: args.test_paths || [],
        failure_classification: failureClassification,
        host_surface_classification: hostSurfaceClassification,
        failed_command_label: failedCommand?.label || null,
        failed_command_kind: failedCommandKind,
        commands: results.map((result) => ({
          label: result.label,
          command: renderCommand(result),
          exit_code: result.exit_code,
          missing_executable: result.missing_executable || null,
          failure_classification: result.failure_classification || null,
          blocked_by_permissions: result.blocked_by_permissions === true,
          duration_ms: result.duration_ms,
        })),
      },
      null,
      2,
    )
  },
})
