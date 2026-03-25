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
  saveWorkflowBundle,
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

type DetectionResult = {
  commands: CommandSpec[]
  missingPrerequisites: string[]
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

async function readText(path: string): Promise<string> {
  try {
    return await readFile(path, "utf-8")
  } catch {
    return ""
  }
}

function isMissingModulePip(output: string): boolean {
  return /No module named pip/i.test(output)
}

function hasSectionValue(text: string, section: string, key: string): boolean {
  const blockMatch = text.match(new RegExp(`\\[${section.replace(".", "\\.")}\\]([\\s\\S]*?)(?:\\n\\[|$)`, "m"))
  if (!blockMatch) return false
  return new RegExp(`^\\s*${key.replace("-", "\\-")}\\s*=\\s*(?:\\[|\\{)`, "m").test(blockMatch[1] || "")
}

function hasPyprojectDevExtra(pyprojectText: string): boolean {
  return hasSectionValue(pyprojectText, "project.optional-dependencies", "dev")
}

function hasPyprojectPytestConfig(pyprojectText: string): boolean {
  return /\[tool\.pytest\.ini_options\]/m.test(pyprojectText)
}

async function detectPythonCommand(root: string): Promise<string | undefined> {
  for (const candidate of ["python3", "python"]) {
    const result = await runCommand(root, {
      label: `${candidate} availability`,
      argv: [candidate, "--version"],
      reason: `Check whether ${candidate} is available for Python environment setup.`,
    })
    if (result.exit_code === 0) return candidate
  }
  return undefined
}

async function isUvManagedVenv(root: string): Promise<boolean> {
  const pyvenv = await readText(join(root, ".venv", "pyvenv.cfg"))
  return /^uv\s*=/m.test(pyvenv)
}

async function detectUvPythonBootstrap(root: string, pyprojectText: string): Promise<DetectionResult> {
  const commands: CommandSpec[] = [
    {
      label: "uv availability",
      argv: ["uv", "--version"],
      reason: "Check whether uv is available for lockfile-based Python bootstrap.",
    },
  ]
  const syncArgs = ["uv", "sync", "--locked"]
  if (hasPyprojectDevExtra(pyprojectText)) {
    syncArgs.push("--extra", "dev")
  }
  commands.push({
    label: "uv sync",
    argv: syncArgs,
    reason: "Sync the Python environment from uv.lock without relying on global pip.",
  })
  commands.push({
    label: "project python ready",
    argv: [join(root, ".venv", "bin", "python"), "--version"],
    reason: "Verify the repo-local Python interpreter is available after bootstrap.",
  })
  const hasTests = existsSync(join(root, "tests")) || existsSync(join(root, "pytest.ini")) || hasPyprojectPytestConfig(pyprojectText)
  if (hasTests) {
    commands.push({
      label: "project pytest ready",
      argv: [join(root, ".venv", "bin", "pytest"), "--version"],
      reason: "Verify the repo-local pytest executable is available for validation work.",
    })
  }
  return { commands, missingPrerequisites: [] }
}

async function detectPipPythonBootstrap(root: string, pyprojectText: string): Promise<DetectionResult> {
  const commands: CommandSpec[] = []
  const missingPrerequisites: string[] = []
  const systemPython = await detectPythonCommand(root)
  if (!systemPython) {
    return { commands: [], missingPrerequisites: ["python"] }
  }

  const venvPython = join(root, ".venv", "bin", "python")
  if (!(await exists(venvPython))) {
    commands.push({
      label: "create repo virtualenv",
      argv: [systemPython, "-m", "venv", ".venv"],
      reason: "Create a repo-local Python virtual environment before installing dependencies.",
    })
  }

  commands.push({
    label: "repo pip availability",
    argv: [venvPython, "-m", "pip", "--version"],
    reason: "Verify pip is available inside the repo-local virtual environment.",
  })

  if (await exists(join(root, "requirements.txt"))) {
    commands.push({
      label: "pip install requirements",
      argv: [venvPython, "-m", "pip", "install", "-r", "requirements.txt"],
      reason: "Install Python runtime dependencies into the repo-local virtual environment.",
    })
  }
  if (await exists(join(root, "requirements-dev.txt"))) {
    commands.push({
      label: "pip install requirements-dev",
      argv: [venvPython, "-m", "pip", "install", "-r", "requirements-dev.txt"],
      reason: "Install Python development and test dependencies into the repo-local virtual environment.",
    })
  }

  const hasEditableProject =
    (await exists(join(root, "pyproject.toml"))) ||
    (await exists(join(root, "setup.py"))) ||
    (await exists(join(root, "setup.cfg")))
  if (hasEditableProject && !commands.some((command) => command.label.startsWith("pip install requirements"))) {
    const editableTarget = hasPyprojectDevExtra(pyprojectText) ? ".[dev]" : "."
    commands.push({
      label: "pip install editable project",
      argv: [venvPython, "-m", "pip", "install", "-e", editableTarget],
      reason: "Install the project package into the repo-local virtual environment.",
    })
  }

  commands.push({
    label: "project python ready",
    argv: [venvPython, "--version"],
    reason: "Verify the repo-local Python interpreter is available after bootstrap.",
  })

  const hasTests = existsSync(join(root, "tests")) || existsSync(join(root, "pytest.ini")) || hasPyprojectPytestConfig(pyprojectText)
  if (hasTests) {
    commands.push({
      label: "project pytest ready",
      argv: [join(root, ".venv", "bin", "pytest"), "--version"],
      reason: "Verify the repo-local pytest executable is available for validation work.",
    })
  }

  return { commands, missingPrerequisites }
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

async function detectNodeBootstrap(root: string): Promise<DetectionResult> {
  const packagePath = join(root, "package.json")
  if (!(await exists(packagePath))) return { commands: [], missingPrerequisites: [] }
  const packageJson = await readJson<PackageJson>(packagePath)
  const manager = choosePackageManager(root, packageJson)
  if (manager === "pnpm") return { commands: [{ label: "pnpm install", argv: ["pnpm", "install", "--frozen-lockfile"], reason: "Install Node dependencies from lockfile." }], missingPrerequisites: [] }
  if (manager === "yarn") return { commands: [{ label: "yarn install", argv: ["yarn", "install", "--immutable"], reason: "Install Node dependencies from lockfile." }], missingPrerequisites: [] }
  if (manager === "bun") return { commands: [{ label: "bun install", argv: ["bun", "install", "--frozen-lockfile"], reason: "Install Node dependencies from lockfile." }], missingPrerequisites: [] }
  if (existsSync(join(root, "package-lock.json"))) return { commands: [{ label: "npm ci", argv: ["npm", "ci"], reason: "Install Node dependencies from package-lock.json." }], missingPrerequisites: [] }
  return { commands: [{ label: "npm install", argv: ["npm", "install"], reason: "Install Node dependencies from package.json." }], missingPrerequisites: [] }
}

async function detectPythonBootstrap(root: string): Promise<DetectionResult> {
  const hasPythonSurface =
    (await exists(join(root, "pyproject.toml"))) ||
    (await exists(join(root, "setup.py"))) ||
    (await exists(join(root, "setup.cfg"))) ||
    (await exists(join(root, "requirements.txt"))) ||
    (await exists(join(root, "requirements-dev.txt")))
  if (!hasPythonSurface) return { commands: [], missingPrerequisites: [] }

  const pyprojectText = await readText(join(root, "pyproject.toml"))
  const useUv = (await exists(join(root, "uv.lock"))) || (await isUvManagedVenv(root))
  if (useUv) {
    return detectUvPythonBootstrap(root, pyprojectText)
  }
  return detectPipPythonBootstrap(root, pyprojectText)
}

async function detectRustBootstrap(root: string): Promise<DetectionResult> {
  if (!(await exists(join(root, "Cargo.toml")))) return { commands: [], missingPrerequisites: [] }
  return { commands: [{ label: "cargo fetch", argv: ["cargo", "fetch"], reason: "Fetch Rust dependencies." }], missingPrerequisites: [] }
}

async function detectGoBootstrap(root: string): Promise<DetectionResult> {
  if (!(await exists(join(root, "go.mod")))) return { commands: [], missingPrerequisites: [] }
  return { commands: [{ label: "go mod download", argv: ["go", "mod", "download"], reason: "Download Go module dependencies." }], missingPrerequisites: [] }
}

async function detectCommands(root: string): Promise<DetectionResult> {
  const detections = await Promise.all([
    detectNodeBootstrap(root),
    detectPythonBootstrap(root),
    detectRustBootstrap(root),
    detectGoBootstrap(root),
  ])
  return {
    commands: detections.flatMap((detection) => detection.commands),
    missingPrerequisites: [...new Set(detections.flatMap((detection) => detection.missingPrerequisites))],
  }
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

function classifyMissingPrerequisites(command: CommandSpec, result: CommandResult): string[] {
  if (result.missing_executable) return [result.missing_executable]
  const output = `${result.stdout}\n${result.stderr}`
  if (command.argv[1] === "-m" && command.argv[2] === "pip" && isMissingModulePip(output)) {
    return ["pip"]
  }
  return []
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
    const detection = await detectCommands(root)
    const commands = detection.commands
    const results: CommandResult[] = []
    const missingPrerequisites = new Set(detection.missingPrerequisites)
    let passed = detection.missingPrerequisites.length === 0

    for (const command of commands) {
      const result = await runCommand(root, command)
      results.push(result)
      for (const missing of classifyMissingPrerequisites(command, result)) {
        missingPrerequisites.add(missing)
      }
      if (result.exit_code !== 0) {
        passed = false
        break
      }
    }

    const fingerprint = await computeBootstrapFingerprint(root)
    const note = missingPrerequisites.size > 0
      ? `Bootstrap failed because required bootstrap prerequisites are missing: ${[...missingPrerequisites].join(", ")}. Install or seed the missing toolchain pieces, then rerun environment_bootstrap.`
      : passed
        ? "Dependency installation and bootstrap verification completed successfully."
        : "Bootstrap stopped on the first failing installation or readiness command. Inspect the captured output and fix the prerequisite or dependency error before smoke tests."
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

    await saveWorkflowBundle({ workflow, manifest, registry })

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
