import { tool } from "@opencode-ai/plugin"
import { spawn } from "node:child_process"
import { existsSync } from "node:fs"
import { access, readFile } from "node:fs/promises"
import { join } from "node:path"
import {
  currentArtifacts,
  defaultArtifactPath,
  getTicket,
  latestArtifact,
  loadArtifactRegistry,
  loadManifest,
  loadWorkflowState,
  normalizeRepoPath,
  registerArtifactSnapshot,
  requireBootstrapReady,
  rootPath,
  saveArtifactRegistry,
  saveManifest,
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
}

type PythonRunner = {
  label: string
  argv: string[]
  reason: string
}

const SMOKE_STAGE = "smoke-test"
const SMOKE_KIND = "smoke-test"

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

async function detectPythonCommands(root: string): Promise<CommandSpec[]> {
  const pythonSignals = ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"]
  const hasPythonProject = await Promise.all(pythonSignals.map((name) => exists(join(root, name)))).then((hits) => hits.some(Boolean))
  if (!hasPythonProject) {
    return []
  }

  const detectPythonRunner = async (): Promise<PythonRunner> => {
    if (await exists(join(root, "uv.lock"))) {
      return {
        label: "uv-managed python",
        argv: ["uv", "run", "python"],
        reason: "Detected uv.lock; using repo-managed uv runtime",
      }
    }

    const repoVenvPython = join(root, ".venv", "bin", "python")
    if (await exists(repoVenvPython)) {
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

  const pythonRunner = await detectPythonRunner()

  const commands: CommandSpec[] = [
    {
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
    },
  ]

  if ((await exists(join(root, "tests"))) || (await exists(join(root, "pytest.ini")))) {
    commands.push({
      label: "pytest",
      argv: [...pythonRunner.argv, "-m", "pytest"],
      reason: `${pythonRunner.reason}; detected Python test surface`,
    })
  }

  return commands
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

async function detectCommands(root: string): Promise<CommandSpec[]> {
  const makeOverride = await detectMakeSmokeTarget(root)
  if (makeOverride.length > 0) {
    return makeOverride
  }

  const commands = [
    ...(await detectNodeCommands(root)),
    ...(await detectPythonCommands(root)),
    ...(await detectRustCommands(root)),
    ...(await detectGoCommands(root)),
  ]

  const seen = new Set<string>()
  return commands.filter((command) => {
    const key = command.argv.join("\u0000")
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
      resolve({
        ...command,
        exit_code: -1,
        duration_ms: Date.now() - startedAt,
        stdout,
        stderr: `${stderr}\n${String(error)}`.trim(),
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

function renderArtifact(ticketId: string, commands: CommandResult[], passed: boolean, note: string): string {
  const commandSections = commands.length
    ? commands
        .map(
          (command, index) => `### ${index + 1}. ${command.label}\n\n- reason: ${command.reason}\n- command: \`${command.argv.join(" ")}\`\n- exit_code: ${command.exit_code}\n- duration_ms: ${command.duration_ms}\n\n#### stdout\n\n${fence(command.stdout)}\n\n#### stderr\n\n${fence(command.stderr)}`,
        )
        .join("\n\n")
    : "No deterministic smoke-test commands were detected."

  return `# Smoke Test\n\n## Ticket\n\n- ${ticketId}\n\n## Overall Result\n\nOverall Result: ${passed ? "PASS" : "FAIL"}\n\n## Notes\n\n${note}\n\n## Commands\n\n${commandSections}\n`
}

async function persistArtifact(ticketId: string, body: string, passed: boolean): Promise<string> {
  const manifest = await loadManifest()
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

  await saveManifest(manifest)
  await saveArtifactRegistry(registry)
  return artifact.path
}

export default tool({
  description: "Run deterministic smoke-test commands, write a canonical smoke-test artifact, and report pass or fail.",
  args: {
    ticket_id: tool.schema.string().describe("Optional ticket id. Defaults to the active ticket.").optional(),
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

    const commands = await detectCommands(root)
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
      if (result.exit_code !== 0) {
        passed = false
        break
      }
    }

    const note = passed
      ? "All detected deterministic smoke-test commands passed."
      : "The smoke-test run stopped on the first failing command. Inspect the recorded output before closeout."
    const body = renderArtifact(ticket.id, results, passed, note)
    const artifactPath = await persistArtifact(ticket.id, body, passed)

    return JSON.stringify(
      {
        ticket_id: ticket.id,
        passed,
        qa_artifact: latestQaArtifact.path,
        smoke_test_artifact: artifactPath,
        commands: results.map((result) => ({
          label: result.label,
          command: result.argv.join(" "),
          exit_code: result.exit_code,
          duration_ms: result.duration_ms,
        })),
      },
      null,
      2,
    )
  },
})
