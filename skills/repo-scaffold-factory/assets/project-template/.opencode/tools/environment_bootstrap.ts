import { tool } from "@opencode-ai/plugin"
import { spawn } from "node:child_process"
import { existsSync } from "node:fs"
import { access, readFile } from "node:fs/promises"
import { join } from "node:path"
import {
  computeBootstrapFingerprint,
  defaultBootstrapProofPath,
  getTicket,
  loadArtifactRegistry,
  loadManifest,
  loadWorkflowState,
  normalizeRepoPath,
  registerArtifactSnapshot,
  rootPath,
  saveArtifactRegistry,
  saveManifest,
  saveWorkflowState,
  writeText,
} from "./_workflow"

type PackageJson = {
  packageManager?: string
  scripts?: Record<string, string>
}

type CommandSpec = {
  label: string
  argv: string[]
  reason: string
}

type CommandResult = CommandSpec & {
  exit_code: number
  duration_ms: number
  stdout: string
  stderr: string
  missing_executable?: string
}

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

async function detectNodeBootstrap(root: string): Promise<CommandSpec[]> {
  const packagePath = join(root, "package.json")
  if (!(await exists(packagePath))) return []
  const packageJson = await readJson<PackageJson>(packagePath)
  const manager = choosePackageManager(root, packageJson)
  if (manager === "pnpm") return [{ label: "pnpm install", argv: ["pnpm", "install", "--frozen-lockfile"], reason: "Install Node dependencies from lockfile." }]
  if (manager === "yarn") return [{ label: "yarn install", argv: ["yarn", "install", "--immutable"], reason: "Install Node dependencies from lockfile." }]
  if (manager === "bun") return [{ label: "bun install", argv: ["bun", "install", "--frozen-lockfile"], reason: "Install Node dependencies from lockfile." }]
  if (existsSync(join(root, "package-lock.json"))) return [{ label: "npm ci", argv: ["npm", "ci"], reason: "Install Node dependencies from package-lock.json." }]
  return [{ label: "npm install", argv: ["npm", "install"], reason: "Install Node dependencies from package.json." }]
}

async function detectPythonBootstrap(root: string): Promise<CommandSpec[]> {
  const commands: CommandSpec[] = []
  if (await exists(join(root, "requirements.txt"))) {
    commands.push({
      label: "pip install requirements",
      argv: ["python3", "-m", "pip", "install", "-r", "requirements.txt"],
      reason: "Install Python runtime dependencies.",
    })
  }
  if (await exists(join(root, "requirements-dev.txt"))) {
    commands.push({
      label: "pip install requirements-dev",
      argv: ["python3", "-m", "pip", "install", "-r", "requirements-dev.txt"],
      reason: "Install Python test and development dependencies.",
    })
  }
  const hasEditableProject =
    (await exists(join(root, "pyproject.toml"))) ||
    (await exists(join(root, "setup.py"))) ||
    (await exists(join(root, "setup.cfg")))
  if (hasEditableProject && commands.length === 0) {
    commands.push({
      label: "pip install editable project",
      argv: ["python3", "-m", "pip", "install", "-e", "."],
      reason: "Install project package and declared extras.",
    })
  }
  return commands
}

async function detectRustBootstrap(root: string): Promise<CommandSpec[]> {
  if (!(await exists(join(root, "Cargo.toml")))) return []
  return [{ label: "cargo fetch", argv: ["cargo", "fetch"], reason: "Fetch Rust dependencies." }]
}

async function detectGoBootstrap(root: string): Promise<CommandSpec[]> {
  if (!(await exists(join(root, "go.mod")))) return []
  return [{ label: "go mod download", argv: ["go", "mod", "download"], reason: "Download Go module dependencies." }]
}

async function detectCommands(root: string): Promise<CommandSpec[]> {
  return [
    ...(await detectNodeBootstrap(root)),
    ...(await detectPythonBootstrap(root)),
    ...(await detectRustBootstrap(root)),
    ...(await detectGoBootstrap(root)),
  ]
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
        env: process.env,
        stdio: ["ignore", "pipe", "pipe"],
      })
    } catch (error) {
      resolve({
        ...command,
        exit_code: -1,
        duration_ms: Date.now() - startedAt,
        stdout: "",
        stderr: String(error),
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
      const missingExecutable = typeof error === "object" && error && "code" in error && (error as { code?: string }).code === "ENOENT"
        ? command.argv[0]
        : undefined
      resolve({
        ...command,
        exit_code: -1,
        duration_ms: Date.now() - startedAt,
        stdout,
        stderr: `${stderr}\n${String(error)}`.trim(),
        missing_executable: missingExecutable,
      })
    })
    child.on("close", (code) => {
      if (settled) return
      settled = true
      resolve({
        ...command,
        exit_code: code ?? -1,
        duration_ms: Date.now() - startedAt,
        stdout,
        stderr,
      })
    })
  })
}

function fence(body: string): string {
  const cleaned = body.trimEnd() || "<no output>"
  return `~~~~text\n${cleaned}\n~~~~`
}

function renderArtifact(
  ticketId: string,
  fingerprint: string,
  commands: CommandResult[],
  missingPrerequisites: string[],
  passed: boolean,
  note: string,
): string {
  const commandSections = commands.length
    ? commands
        .map(
          (command, index) => `### ${index + 1}. ${command.label}\n\n- reason: ${command.reason}\n- command: \`${command.argv.join(" ")}\`\n- exit_code: ${command.exit_code}\n- duration_ms: ${command.duration_ms}\n- missing_executable: ${command.missing_executable || "none"}\n\n#### stdout\n\n${fence(command.stdout)}\n\n#### stderr\n\n${fence(command.stderr)}`,
        )
        .join("\n\n")
    : "No installable dependency surfaces were detected in this repo."
  const prerequisites = missingPrerequisites.length > 0 ? missingPrerequisites.map((item) => `- ${item}`).join("\n") : "- None"

  return `# Environment Bootstrap\n\n## Ticket\n\n- ${ticketId}\n\n## Overall Result\n\nOverall Result: ${passed ? "PASS" : "FAIL"}\n\n## Environment Fingerprint\n\n- ${fingerprint}\n\n## Missing Prerequisites\n\n${prerequisites}\n\n## Notes\n\n${note}\n\n## Commands\n\n${commandSections}\n`
}

export default tool({
  description: "Install and verify project/runtime/test dependencies, then record bootstrap proof for the repo environment.",
  args: {
    ticket_id: tool.schema.string().describe("Optional ticket id that owns the bootstrap proof artifact. Defaults to the active ticket.").optional(),
  },
  async execute(args) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const ticket = getTicket(manifest, args.ticket_id)
    const root = rootPath()
    const commands = await detectCommands(root)
    const results: CommandResult[] = []
    const missingPrerequisites = new Set<string>()
    let passed = true

    for (const command of commands) {
      const result = await runCommand(root, command)
      results.push(result)
      if (result.missing_executable) {
        missingPrerequisites.add(result.missing_executable)
      }
      if (result.exit_code !== 0) {
        passed = false
        break
      }
    }

    const fingerprint = await computeBootstrapFingerprint(root)
    const note = missingPrerequisites.size > 0
      ? `Bootstrap failed because required executables are missing: ${[...missingPrerequisites].join(", ")}. Install the missing toolchain packages, then rerun environment_bootstrap.`
      : passed
        ? "Dependency installation and bootstrap verification completed successfully."
        : "Bootstrap stopped on the first failing installation command. Inspect the captured output and fix the prerequisite or dependency error before smoke tests."
    const body = renderArtifact(ticket.id, fingerprint, results, [...missingPrerequisites], passed, note)
    const canonicalPath = normalizeRepoPath(defaultBootstrapProofPath(ticket.id))
    await writeText(canonicalPath, body)

    const registry = await loadArtifactRegistry()
    const artifact = await registerArtifactSnapshot({
      ticket,
      registry,
      source_path: canonicalPath,
      kind: "environment-bootstrap",
      stage: "bootstrap",
      summary: passed ? "Environment bootstrap completed successfully." : "Environment bootstrap failed.",
    })

    workflow.bootstrap = {
      status: passed ? "ready" : "failed",
      last_verified_at: new Date().toISOString(),
      environment_fingerprint: fingerprint,
      proof_artifact: artifact.path,
    }

    await saveManifest(manifest)
    await saveArtifactRegistry(registry)
    await saveWorkflowState(workflow)

    return JSON.stringify(
      {
        ticket_id: ticket.id,
        bootstrap_status: workflow.bootstrap.status,
        proof_artifact: artifact.path,
        environment_fingerprint: fingerprint,
        missing_prerequisites: [...missingPrerequisites],
        commands: results.map((result) => ({
          label: result.label,
          command: result.argv.join(" "),
          exit_code: result.exit_code,
          missing_executable: result.missing_executable || null,
          duration_ms: result.duration_ms,
        })),
      },
      null,
      2,
    )
  },
})
