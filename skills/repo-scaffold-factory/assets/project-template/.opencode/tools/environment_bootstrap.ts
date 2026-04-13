import { tool } from "@opencode-ai/plugin"
import { spawn } from "node:child_process"
import { existsSync, readdirSync } from "node:fs"
import { access, readFile, readdir } from "node:fs/promises"
import { homedir } from "node:os"
import { join } from "node:path"
import {
	computeBootstrapFingerprint,
	defaultBootstrapProofPath,
	findExistingRepoVenvExecutable,
	getTicket,
	loadArtifactRegistry,
	loadManifest,
	loadWorkflowState,
	normalizeRepoPath,
	registerArtifactSnapshot,
	repoVenvExecutable,
	rootPath,
	saveWorkflowBundle,
	writeText,
} from "../lib/workflow"

type PackageJson = {
	packageManager?: string
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
	failure_classification?: "missing_executable" | "permission_restriction" | "command_error"
	blocked_by_permissions?: boolean
}

type BootstrapBlocker = {
	executable: string
	reason: string
	install_command: string | null
}

type StackDetectionResult = {
	adapter_id: string
	detected: boolean
	indicator_files: string[]
	missing_executables: string[]
	missing_env_vars: string[]
	version_info: Record<string, string>
	warnings: string[]
	commands: CommandSpec[]
	blockers: BootstrapBlocker[]
}

type DetectionResult = {
	detections: StackDetectionResult[]
	commands: CommandSpec[]
	blockers: BootstrapBlocker[]
	warnings: string[]
	missingPrerequisites: string[]
}

type StackAdapter = {
	id: string
	detect(root: string): Promise<StackDetectionResult>
}

type BootstrapProvenance = {
	stack_label?: string
}

type TargetCompletionExpectation = {
	host_prerequisites: string[]
	repo_prerequisites: string[]
	release_proof: string
}

const TARGET_COMPLETION_EXPECTATIONS: Record<string, TargetCompletionExpectation> = {
	"godot-android": {
		host_prerequisites: ["godot", "java", "javac", "android-sdk", "godot-export-templates"],
		repo_prerequisites: ["export_presets.cfg Android preset", "repo-local android support surfaces"],
		release_proof: "build/android/__PROJECT_SLUG__-debug.apk",
	},
}

const SAFE_BOOTSTRAP_PATTERNS = [
	/^(?:apt-get|apt)\s+install\b.*(?:-y|--yes)\b/i,
	/^brew\s+install\b/i,
	/^pip(?:3)?\s+install\b/i,
	/^(?:python|python3|\.venv\/bin\/python)\s+-m\s+pip\s+install\b/i,
	/^(?:npm\s+install\s+-g|pnpm\s+add\s+-g)\b/i,
	/^cargo\s+(?:install|fetch)\b/i,
	/^go\s+(?:install|mod\s+download)\b/i,
	/^gem\s+install\b/i,
	/^sdkmanager\b/i,
	/^dotnet\s+(?:tool\s+install|restore|--info)\b/i,
	/^flutter\s+pub\s+get\b/i,
	/^dart\s+pub\s+get\b/i,
	/^mix\s+deps\.get\b/i,
	/^composer\s+install\b/i,
	/^(?:bundle|bundler)\s+install\b/i,
	/^rustup\s+(?:component\s+add|target\s+add)\b/i,
	/^zig\b/i,
	/^uv\s+sync\b/i,
	/^(?:python|python3)\s+-m\s+venv\b/i,
	/^(?:npm|pnpm|yarn|bun)\s+(?:ci|install)\b/i,
	/^(?:godot|godot4)\s+--headless\s+(?:--version|--check-only|--script|--export)\b/i,
	/^(?:\.\/gradlew|gradle|mvn|java|javac)\b/i,
	/^(?:cmake|make|ninja|gcc|g\+\+|clang|clang\+\+|meson)\b/i,
	/^(?:swift|swiftc|xcodebuild)\b/i,
	/^(?:ruby|bundle|bundler|rake|rspec)\b/i,
	/^(?:elixir|mix|erl)\b/i,
	/^(?:php|composer|ghc|cabal|stack)\b/i,
]

const EXECUTABLE_PROBES = new Map<string, Promise<boolean>>()

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

async function detectedStackLabel(root: string): Promise<string> {
	const provenance = await readJson<BootstrapProvenance>(join(root, ".opencode", "meta", "bootstrap-provenance.json"))
	if (provenance?.stack_label?.trim()) return provenance.stack_label.trim()
	const brief = await readText(join(root, "docs", "spec", "CANONICAL-BRIEF.md"))
	return brief.match(/^\s*-\s*Stack label:\s*`?([^`\n]+)`?\s*$/m)?.[1]?.trim() || ""
}

async function repoTargetsGodotAndroid(root: string): Promise<boolean> {
	const stackLabel = (await detectedStackLabel(root)).toLowerCase()
	if (stackLabel.includes("godot") && stackLabel.includes("android")) return true
	const brief = (await readText(join(root, "docs", "spec", "CANONICAL-BRIEF.md"))).toLowerCase()
	const androidTarget = /platform target is android|target platform is android|platform target:\s*android|\bandroid\b/.test(brief)
	const godotTarget = /engine is godot|\bgodot\b/.test(brief) || existsSync(join(root, "project.godot"))
	return androidTarget && godotTarget
}

async function discoverAndroidSdkPath(): Promise<string | null> {
	const envValue = process.env.ANDROID_HOME || process.env.ANDROID_SDK_ROOT
	if (envValue && await exists(envValue)) return envValue
	const home = homedir()
	for (const candidate of [
		join(home, "Android", "Sdk"),
		join(home, "Library", "Android", "sdk"),
		join(home, "AppData", "Local", "Android", "Sdk"),
	]) {
		if (await exists(candidate)) return candidate
	}
	return null
}

async function hasGodotExportTemplatesInstalled(): Promise<boolean> {
	const templatesRoot = join(homedir(), ".local", "share", "godot", "export_templates")
	if (!(await exists(templatesRoot))) return false
	try {
		const entries = await readdir(templatesRoot)
		return entries.length > 0
	} catch {
		return false
	}
}

function hasMeaningfulAndroidSupportSurface(root: string): boolean {
	const androidDir = join(root, "android")
	if (!existsSync(androidDir)) return false
	try {
		const stack = [androidDir]
		while (stack.length > 0) {
			const current = stack.pop()
			if (!current) continue
			for (const entry of readdirSync(current, { withFileTypes: true })) {
				const full = join(current, entry.name)
				if (entry.isDirectory()) {
					stack.push(full)
					continue
				}
				if (entry.isFile() && entry.name !== ".gitkeep") return true
			}
		}
		return false
	} catch {
		return false
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

function escapeRegExp(value: string): string {
	return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
}

function extractTomlSectionBody(text: string, section: string): string {
	const header = `[${section}]`
	const lines = text.split(/\r?\n/)
	const body: string[] = []
	let inSection = false
	for (const line of lines) {
		const trimmed = line.trim()
		if (!inSection) {
			if (trimmed === header) {
				inSection = true
			}
			continue
		}
		if (/^\[[^\]]+\]\s*$/.test(trimmed)) {
			break
		}
		body.push(line)
	}
	return body.join("\n")
}

function hasSectionValue(text: string, section: string, key: string): boolean {
	const sectionBody = extractTomlSectionBody(text, section)
	if (!sectionBody.trim()) return false
	return new RegExp(`^\\s*${escapeRegExp(key)}\\s*=\\s*(?:\\[|\\{)`, "m").test(sectionBody)
}

function unique<T>(items: T[]): T[] {
	return [...new Set(items)]
}

function renderCommand(command: CommandSpec): string {
	return command.argv.join(" ")
}

function createBlocker(executable: string, reason: string, installCommand?: string | null): BootstrapBlocker {
	return { executable, reason, install_command: installCommand ?? null }
}

function emptyDetection(adapterId: string): StackDetectionResult {
	return {
		adapter_id: adapterId,
		detected: false,
		indicator_files: [],
		missing_executables: [],
		missing_env_vars: [],
		version_info: {},
		warnings: [],
		commands: [],
		blockers: [],
	}
}

function finalizeDetection(detection: StackDetectionResult): StackDetectionResult {
	return {
		...detection,
		indicator_files: unique(detection.indicator_files),
		missing_executables: unique(detection.missing_executables),
		missing_env_vars: unique(detection.missing_env_vars),
		warnings: unique(detection.warnings),
		blockers: detection.blockers.filter((blocker, index, items) => items.findIndex((item) => item.executable === blocker.executable && item.reason === blocker.reason) === index),
	}
}

function withIndicators(adapterId: string, indicatorFiles: string[]): StackDetectionResult {
	const detection = emptyDetection(adapterId)
	detection.detected = indicatorFiles.length > 0
	detection.indicator_files = indicatorFiles
	return detection
}

async function listRootEntries(root: string): Promise<string[]> {
	try {
		return await readdir(root)
	} catch {
		return []
	}
}

async function rootEntriesMatching(root: string, pattern: RegExp): Promise<string[]> {
	return (await listRootEntries(root)).filter((entry) => pattern.test(entry))
}

async function commandExists(command: string, args: string[] = ["--version"]): Promise<boolean> {
	const cacheKey = `${command} ${args.join(" ")}`
	if (!EXECUTABLE_PROBES.has(cacheKey)) {
		EXECUTABLE_PROBES.set(
			cacheKey,
			new Promise((resolve) => {
				let child
				try {
					child = spawn(command, args, { stdio: "ignore" })
				} catch {
					resolve(false)
					return
				}
				child.on("error", (error) => {
					const code = typeof error === "object" && error && "code" in error ? String((error as { code?: string }).code || "") : ""
					resolve(code !== "ENOENT")
				})
				child.on("close", () => resolve(true))
			}),
		)
	}
	return EXECUTABLE_PROBES.get(cacheKey)!
}

async function firstAvailableExecutable(candidates: string[], args: string[] = ["--version"]): Promise<string | null> {
	for (const candidate of candidates) {
		if (await commandExists(candidate, args)) {
			return candidate
		}
	}
	return null
}

function isSafeBootstrapCommand(command: CommandSpec): boolean {
	const rendered = renderCommand(command)
	if (/\bsudo\b/i.test(rendered)) {
		return false
	}
	return SAFE_BOOTSTRAP_PATTERNS.some((pattern) => pattern.test(rendered))
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

function isPermissionRestrictionOutput(output: string): boolean {
	return /permission denied|operation not permitted|EACCES|EPERM|blocked by permission rules/i.test(output)
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
				failure_classification: missingExecutable ? "missing_executable" : blockedByPermissions ? "permission_restriction" : "command_error",
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
				failure_classification: missingExecutable ? "missing_executable" : blockedByPermissions ? "permission_restriction" : "command_error",
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
				failure_classification: code === 0 ? undefined : missingExecutable ? "missing_executable" : blockedByPermissions ? "permission_restriction" : "command_error",
				blocked_by_permissions: blockedByPermissions || undefined,
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

function isAdvisoryBootstrapFailure(command: CommandSpec, result: CommandResult): boolean {
	return command.label === "make query" && result.failure_classification === "command_error"
}

function renderArtifact(
	ticketId: string,
	fingerprint: string,
	detections: StackDetectionResult[],
	commands: CommandResult[],
	blockers: BootstrapBlocker[],
	warnings: string[],
	missingPrerequisites: string[],
	passed: boolean,
	note: string,
): string {
	const detectionSection = detections.length > 0
		? detections
				.filter((detection) => detection.detected)
				.map((detection) => `### ${detection.adapter_id}\n\n- indicator_files: ${detection.indicator_files.join(", ") || "none"}\n- missing_executables: ${detection.missing_executables.join(", ") || "none"}\n- missing_env_vars: ${detection.missing_env_vars.join(", ") || "none"}\n- warnings: ${detection.warnings.join(" | ") || "none"}`)
				.join("\n\n")
		: "No supported stack adapters detected any project surfaces."
	const commandSections = commands.length
		? commands
				.map(
					(command, index) => `### ${index + 1}. ${command.label}\n\n- reason: ${command.reason}\n- command: \`${renderCommand(command)}\`\n- exit_code: ${command.exit_code}\n- duration_ms: ${command.duration_ms}\n- missing_executable: ${command.missing_executable || "none"}\n- failure_classification: ${command.failure_classification || "none"}\n- blocked_by_permissions: ${command.blocked_by_permissions ? "true" : "false"}\n\n#### stdout\n\n${fence(command.stdout)}\n\n#### stderr\n\n${fence(command.stderr)}`,
				)
				.join("\n\n")
		: "No executable bootstrap commands were eligible to run."
	const prerequisites = missingPrerequisites.length > 0 ? missingPrerequisites.map((item) => `- ${item}`).join("\n") : "- None"
	const blockerLines = blockers.length > 0
		? blockers.map((item) => `- ${item.executable}: ${item.reason}${item.install_command ? ` | install_command: ${item.install_command}` : ""}`).join("\n")
		: "- None"
	const warningLines = warnings.length > 0 ? warnings.map((item) => `- ${item}`).join("\n") : "- None"

	return `# Environment Bootstrap\n\n## Ticket\n\n- ${ticketId}\n\n## Overall Result\n\nOverall Result: ${passed ? "PASS" : "FAIL"}\n\n## Environment Fingerprint\n\n- ${fingerprint}\n\n## Stack Detections\n\n${detectionSection}\n\n## Missing Prerequisites\n\n${prerequisites}\n\n## Blockers\n\n${blockerLines}\n\n## Warnings\n\n${warningLines}\n\n## Notes\n\n${note}\n\n## Commands\n\n${commandSections}\n`
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

function hasPyprojectDevExtra(pyprojectText: string): boolean {
	// Detect `[project.optional-dependencies]` / `dev = [...]` layouts without relying on a brittle multi-line regex.
	return hasSectionValue(pyprojectText, "project.optional-dependencies", "dev")
}

function hasPyprojectDevDependencyGroup(pyprojectText: string): boolean {
	// Detect `[dependency-groups]` / `dev = [...]` layouts for uv-managed repos.
	return hasSectionValue(pyprojectText, "dependency-groups", "dev")
}

function hasPyprojectUvDevDependencies(pyprojectText: string): boolean {
	// Detect legacy `[tool.uv.dev-dependencies]` layouts as a fallback.
	return /\[tool\.uv(?:\.[^\]]+)?\][\s\S]*?^\s*dev-dependencies\s*=/m.test(pyprojectText) || /\[tool\.uv\.dev-dependencies\]/m.test(pyprojectText)
}

function hasPyprojectPytestConfig(pyprojectText: string): boolean {
	// Detect `[tool.pytest.ini_options]` even when no tests/ directory exists yet.
	return /\[tool\.pytest\.ini_options\]/m.test(pyprojectText)
}

function hasPyprojectRuffConfig(pyprojectText: string): boolean {
	return /\[tool\.ruff(?:\.[^\]]+)?\]/m.test(pyprojectText)
}

function detectUvSyncDependencyArgs(pyprojectText: string): string[] {
	if (hasPyprojectDevExtra(pyprojectText)) return ["--extra", "dev"]
	if (hasPyprojectDevDependencyGroup(pyprojectText)) return ["--group", "dev"]
	if (hasPyprojectUvDevDependencies(pyprojectText)) return ["--all-extras"]
	return []
}

function hasPythonTestSurface(root: string, pyprojectText: string): boolean {
	return existsSync(join(root, "tests")) || existsSync(join(root, "pytest.ini")) || hasPyprojectPytestConfig(pyprojectText)
}

function hasRuffSurface(root: string, pyprojectText: string): boolean {
	return existsSync(join(root, "ruff.toml")) || existsSync(join(root, ".ruff.toml")) || hasPyprojectRuffConfig(pyprojectText)
}

async function detectUvPythonBootstrap(root: string, pyprojectText: string, indicatorFiles: string[]): Promise<StackDetectionResult> {
	const detection = withIndicators("python", indicatorFiles)
	const repoPython = repoVenvExecutable(root, "python")
	const repoPytest = repoVenvExecutable(root, "pytest")
	const repoRuff = repoVenvExecutable(root, "ruff")
	detection.commands.push({ label: "uv availability", argv: ["uv", "--version"], reason: "Check whether uv is available for lockfile-based Python bootstrap." })
	detection.commands.push({ label: "uv sync", argv: ["uv", "sync", "--locked", ...detectUvSyncDependencyArgs(pyprojectText)], reason: "Sync the Python environment from uv.lock without relying on global pip." })
	detection.commands.push({ label: "project python ready", argv: [repoPython, "--version"], reason: "Verify the repo-local Python interpreter is available after bootstrap." })
	if (hasPythonTestSurface(root, pyprojectText)) {
		detection.commands.push({ label: "project pytest ready", argv: [repoPytest, "--version"], reason: "Verify the repo-local pytest executable is available for validation work." })
	}
	if (hasRuffSurface(root, pyprojectText)) {
		detection.commands.push({ label: "project ruff ready", argv: [repoRuff, "--version"], reason: "Verify the repo-local ruff executable is still available after bootstrap sync." })
	}
	if (!(await commandExists("uv"))) {
		detection.missing_executables.push("uv")
		detection.blockers.push(createBlocker("uv", `Required by ${indicatorFiles.join(", ") || "uv-managed Python project"}.`, null))
	}
	return finalizeDetection(detection)
}

async function detectPipPythonBootstrap(root: string, pyprojectText: string, indicatorFiles: string[]): Promise<StackDetectionResult> {
	const detection = withIndicators("python", indicatorFiles)
	const systemPython = await detectPythonCommand(root)
	if (!systemPython) {
		detection.missing_executables.push("python")
		detection.blockers.push(createBlocker("python", `Required by ${indicatorFiles.join(", ") || "Python project surface"}.`, null))
		return finalizeDetection(detection)
	}

	const venvPython = (await findExistingRepoVenvExecutable(root, "python")) ?? repoVenvExecutable(root, "python")
	const venvPytest = (await findExistingRepoVenvExecutable(root, "pytest")) ?? repoVenvExecutable(root, "pytest")
	const venvRuff = (await findExistingRepoVenvExecutable(root, "ruff")) ?? repoVenvExecutable(root, "ruff")
	if (!(await exists(venvPython))) {
		detection.commands.push({ label: "create repo virtualenv", argv: [systemPython, "-m", "venv", ".venv"], reason: "Create a repo-local Python virtual environment before installing dependencies." })
	}
	detection.commands.push({ label: "repo pip availability", argv: [venvPython, "-m", "pip", "--version"], reason: "Verify pip is available inside the repo-local virtual environment." })
	if (await exists(join(root, "requirements.txt"))) {
		detection.commands.push({ label: "pip install requirements", argv: [venvPython, "-m", "pip", "install", "-r", "requirements.txt"], reason: "Install Python runtime dependencies into the repo-local virtual environment." })
	}
	if (await exists(join(root, "requirements-dev.txt"))) {
		detection.commands.push({ label: "pip install requirements-dev", argv: [venvPython, "-m", "pip", "install", "-r", "requirements-dev.txt"], reason: "Install Python development and test dependencies into the repo-local virtual environment." })
	}
	const hasEditableProject = (await exists(join(root, "pyproject.toml"))) || (await exists(join(root, "setup.py"))) || (await exists(join(root, "setup.cfg")))
	if (hasEditableProject && !detection.commands.some((command) => command.label.startsWith("pip install requirements"))) {
		detection.commands.push({ label: "pip install editable project", argv: [venvPython, "-m", "pip", "install", "-e", hasPyprojectDevExtra(pyprojectText) ? ".[dev]" : "."], reason: "Install the project package into the repo-local virtual environment." })
	}
	detection.commands.push({ label: "project python ready", argv: [venvPython, "--version"], reason: "Verify the repo-local Python interpreter is available after bootstrap." })
	if (hasPythonTestSurface(root, pyprojectText)) {
		detection.commands.push({ label: "project pytest ready", argv: [venvPytest, "--version"], reason: "Verify the repo-local pytest executable is available for validation work." })
	}
	if (hasRuffSurface(root, pyprojectText)) {
		detection.commands.push({ label: "project ruff ready", argv: [venvRuff, "--version"], reason: "Verify the repo-local ruff executable is available for lint/runtime validation work." })
	}
	return finalizeDetection(detection)
}

async function detectNodeBootstrap(root: string): Promise<StackDetectionResult> {
	const packagePath = join(root, "package.json")
	if (!(await exists(packagePath))) return emptyDetection("node")
	const detection = withIndicators("node", ["package.json"])
	const packageJson = await readJson<PackageJson>(packagePath)
	const manager = choosePackageManager(root, packageJson)
	if (!(await commandExists(manager, ["--version"]))) {
		detection.missing_executables.push(manager)
		detection.blockers.push(createBlocker(manager, "Required to install Node dependencies from package.json.", manager === "npm" ? null : `npm install -g ${manager}`))
		return finalizeDetection(detection)
	}
	if (manager === "pnpm") detection.commands.push({ label: "pnpm install", argv: ["pnpm", "install", "--frozen-lockfile"], reason: "Install Node dependencies from lockfile." })
	else if (manager === "yarn") detection.commands.push({ label: "yarn install", argv: ["yarn", "install", "--immutable"], reason: "Install Node dependencies from lockfile." })
	else if (manager === "bun") detection.commands.push({ label: "bun install", argv: ["bun", "install", "--frozen-lockfile"], reason: "Install Node dependencies from lockfile." })
	else if (existsSync(join(root, "package-lock.json"))) detection.commands.push({ label: "npm ci", argv: ["npm", "ci"], reason: "Install Node dependencies from package-lock.json." })
	else detection.commands.push({ label: "npm install", argv: ["npm", "install"], reason: "Install Node dependencies from package.json." })
	return finalizeDetection(detection)
}

async function detectPythonBootstrap(root: string): Promise<StackDetectionResult> {
	const indicatorFiles = ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "requirements-dev.txt"].filter((file) => existsSync(join(root, file)))
	if (indicatorFiles.length === 0) return emptyDetection("python")
	const pyprojectText = await readText(join(root, "pyproject.toml"))
	const useUv = existsSync(join(root, "uv.lock")) || (await isUvManagedVenv(root))
	return useUv ? detectUvPythonBootstrap(root, pyprojectText, indicatorFiles) : detectPipPythonBootstrap(root, pyprojectText, indicatorFiles)
}

async function detectRustBootstrap(root: string): Promise<StackDetectionResult> {
	if (!(await exists(join(root, "Cargo.toml")))) return emptyDetection("rust")
	const detection = withIndicators("rust", ["Cargo.toml"])
	if (!(await commandExists("cargo"))) {
		detection.missing_executables.push("cargo")
		detection.blockers.push(createBlocker("cargo", "Required by Cargo.toml.", null))
		return finalizeDetection(detection)
	}
	detection.commands.push({ label: "cargo fetch", argv: ["cargo", "fetch"], reason: "Fetch Rust dependencies." })
	return finalizeDetection(detection)
}

async function detectGoBootstrap(root: string): Promise<StackDetectionResult> {
	if (!(await exists(join(root, "go.mod")))) return emptyDetection("go")
	const detection = withIndicators("go", ["go.mod"])
	if (!(await commandExists("go"))) {
		detection.missing_executables.push("go")
		detection.blockers.push(createBlocker("go", "Required by go.mod.", null))
		return finalizeDetection(detection)
	}
	detection.commands.push({ label: "go mod download", argv: ["go", "mod", "download"], reason: "Download Go module dependencies." })
	return finalizeDetection(detection)
}

async function detectGodotBootstrap(root: string): Promise<StackDetectionResult> {
	const indicatorFiles = ["project.godot", "export_presets.cfg"].filter((file) => existsSync(join(root, file)))
	if (indicatorFiles.length === 0) return emptyDetection("godot")
	const detection = withIndicators("godot", indicatorFiles)
	const projectText = await readText(join(root, "project.godot"))
	const configVersion = projectText.match(/config_version=(\d+)/)?.[1]
	if (configVersion) detection.version_info.config_version = configVersion
	const androidExpectation = TARGET_COMPLETION_EXPECTATIONS["godot-android"]
	const godotExecutable = await firstAvailableExecutable(["godot4", "godot"], ["--version"])
	if (!godotExecutable) {
		detection.missing_executables.push("godot")
		detection.blockers.push(createBlocker("godot", "Required by project.godot.", null))
	} else {
		detection.commands.push({ label: `${godotExecutable} headless version`, argv: [godotExecutable, "--headless", "--version"], reason: "Verify the Godot runtime is available for headless validation." })
	}
	const exportPresets = await readText(join(root, "export_presets.cfg"))
	const requiresAndroid = /android/i.test(exportPresets) || await repoTargetsGodotAndroid(root)
	if (requiresAndroid) {
		const androidSdkPath = await discoverAndroidSdkPath()
		if (!androidSdkPath) {
			detection.missing_env_vars.push("ANDROID_HOME/ANDROID_SDK_ROOT")
			detection.blockers.push(createBlocker("android-sdk", `Required for the Godot Android target declared by the canonical target-completion contract (${androidExpectation.release_proof}).`, "sdkmanager --install 'platform-tools' 'platforms;android-34' 'build-tools;34.0.0'"))
		} else {
			detection.version_info.android_sdk_path = androidSdkPath
		}
		if (!(await firstAvailableExecutable(["java"], ["-version"]))) {
			detection.blockers.push(createBlocker("java", "Required for Android export support in Godot.", null))
		} else if (!process.env.JAVA_HOME) {
			// java is in PATH but JAVA_HOME is not set — Godot's Android Gradle build requires JAVA_HOME,
			// not just a java binary in PATH. Without it the export fails with "A valid Java SDK path is
			// required in Editor Settings." Derive a candidate path from the binary and surface it as a blocker.
			detection.blockers.push(createBlocker(
				"JAVA_HOME",
				"JAVA_HOME is not set. Godot's Android Gradle build requires JAVA_HOME (not just java in PATH). " +
				"Run: export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java)))) && echo $JAVA_HOME",
				"export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))"
			))
		}
		if (!(await firstAvailableExecutable(["javac"], ["-version"]))) detection.blockers.push(createBlocker("javac", "Required for Android export support in Godot.", null))
		if (!(await hasGodotExportTemplatesInstalled())) detection.blockers.push(createBlocker("godot-export-templates", "Required for Godot Android debug APK export.", null))
		if (!existsSync(join(root, "export_presets.cfg"))) {
			detection.warnings.push(`Android target declared in canonical brief, but repo prerequisite ${androidExpectation.repo_prerequisites[0]} is still missing.`)
		}
		if (!hasMeaningfulAndroidSupportSurface(root)) {
			detection.warnings.push(`Android target declared in canonical brief, but repo prerequisite ${androidExpectation.repo_prerequisites[1]} is still missing.`)
		}

		// Debug keystore detection for Android export
		const keystoreCandidates = [
			join(homedir(), ".android", "debug.keystore"),
			join(homedir(), ".local", "share", "godot", "keystores", "debug.keystore"),
		]
		const foundKeystore = keystoreCandidates.find((k) => existsSync(k))
		if (foundKeystore) {
			detection.version_info.android_debug_keystore = foundKeystore
		} else {
			detection.blockers.push(createBlocker(
				"android-debug-keystore",
				"No Android debug keystore found. Required for Godot Android debug APK export. " +
				"Generate one with: keytool -genkeypair -v -keystore ~/.android/debug.keystore -alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 -storepass android -keypass android",
				"keytool -genkeypair -v -keystore ~/.android/debug.keystore -alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 -storepass android -keypass android",
			))
		}
	}

	// Blender detection for game projects with asset pipelines
	const blenderExecutable = await firstAvailableExecutable(["blender"], ["--version"])
	if (blenderExecutable) {
		detection.version_info.blender_executable = blenderExecutable
	}

	return finalizeDetection(detection)
}

async function detectJavaAndroidBootstrap(root: string): Promise<StackDetectionResult> {
	const indicatorFiles = ["build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "pom.xml"].filter((file) => existsSync(join(root, file)))
	if (indicatorFiles.length === 0) return emptyDetection("java-android")
	const detection = withIndicators("java-android", indicatorFiles)
	const combinedBuildText = (await Promise.all(["build.gradle", "build.gradle.kts", "pom.xml"].filter((file) => existsSync(join(root, file))).map((file) => readText(join(root, file))))).join("\n")
	const sourceCompatibility = combinedBuildText.match(/sourceCompatibility\s*=\s*['"]?([^'"\n]+)/)?.[1]
	if (sourceCompatibility) detection.version_info.source_compatibility = sourceCompatibility
	const isAndroid = /com\.android\.(application|library)|android\s*\{/.test(combinedBuildText) || existsSync(join(root, "AndroidManifest.xml"))
	if (!(await firstAvailableExecutable(["java"], ["-version"]))) detection.blockers.push(createBlocker("java", `Required by ${indicatorFiles.join(", ")}.`, null))
	if (!(await firstAvailableExecutable(["javac"], ["-version"]))) detection.blockers.push(createBlocker("javac", `Required by ${indicatorFiles.join(", ")}.`, null))
	if (existsSync(join(root, "gradlew"))) detection.commands.push({ label: "gradle wrapper version", argv: ["./gradlew", "--version"], reason: "Verify the project Gradle wrapper is available." })
	else if (indicatorFiles.some((file) => file.startsWith("build.gradle"))) {
		if (await commandExists("gradle")) detection.commands.push({ label: "gradle version", argv: ["gradle", "--version"], reason: "Verify Gradle is available for Java or Android builds." })
		else detection.blockers.push(createBlocker("gradle", "Required by build.gradle when no Gradle wrapper is present.", null))
	}
	if (indicatorFiles.includes("pom.xml")) {
		if (await commandExists("mvn")) detection.commands.push({ label: "maven version", argv: ["mvn", "--version"], reason: "Verify Maven is available for pom.xml projects." })
		else detection.blockers.push(createBlocker("maven", "Required by pom.xml.", null))
	}
	if (isAndroid && !process.env.ANDROID_HOME && !process.env.ANDROID_SDK_ROOT) {
		detection.missing_env_vars.push("ANDROID_HOME/ANDROID_SDK_ROOT")
		detection.blockers.push(createBlocker("android-sdk", "Required by Android Gradle configuration.", "sdkmanager --install 'platform-tools' 'platforms;android-34' 'build-tools;34.0.0'"))
	}
	return finalizeDetection(detection)
}

async function detectCppBootstrap(root: string): Promise<StackDetectionResult> {
	const rootEntries = await listRootEntries(root)
	const indicatorFiles = ["CMakeLists.txt", "Makefile", "configure", "meson.build"].filter((file) => existsSync(join(root, file)))
	if (indicatorFiles.length === 0 && !rootEntries.some((entry) => /\.(?:c|cc|cpp|cxx|h|hpp)$/.test(entry))) {
		return emptyDetection("c-cpp")
	}
	const detection = withIndicators("c-cpp", indicatorFiles.length > 0 ? indicatorFiles : rootEntries.filter((entry) => /\.(?:c|cc|cpp|cxx|h|hpp)$/.test(entry)).slice(0, 5))
	const compiler = await firstAvailableExecutable(["g++", "gcc", "clang++", "clang"], ["--version"])
	if (!compiler) detection.blockers.push(createBlocker("c-compiler", "Required by detected C/C++ build surface.", null))
	else detection.commands.push({ label: `${compiler} version`, argv: [compiler, "--version"], reason: "Verify a C/C++ compiler is available." })
	if (indicatorFiles.includes("CMakeLists.txt")) {
		if (await commandExists("cmake")) detection.commands.push({ label: "cmake version", argv: ["cmake", "--version"], reason: "Verify CMake is available for this project." })
		else detection.blockers.push(createBlocker("cmake", "Required by CMakeLists.txt.", null))
	}
	if (indicatorFiles.includes("Makefile")) {
		if (await commandExists("make")) detection.commands.push({ label: "make version", argv: ["make", "--version"], reason: "Verify make is available for this project." })
		else detection.blockers.push(createBlocker("make", "Required by Makefile.", null))
	}
	if (indicatorFiles.includes("meson.build")) {
		if (await commandExists("meson")) detection.commands.push({ label: "meson version", argv: ["meson", "--version"], reason: "Verify Meson is available for this project." })
		else detection.blockers.push(createBlocker("meson", "Required by meson.build.", null))
	}
	if (indicatorFiles.includes("configure") && !(await commandExists("sh", ["--version"]))) {
		detection.warnings.push("configure script detected; validate a shell environment manually before build configuration.")
	}
	return finalizeDetection(detection)
}

async function detectDotnetBootstrap(root: string): Promise<StackDetectionResult> {
	const indicatorFiles = (await rootEntriesMatching(root, /\.(?:csproj|fsproj|sln)$/)).concat(existsSync(join(root, "global.json")) ? ["global.json"] : [])
	if (indicatorFiles.length === 0) return emptyDetection("dotnet")
	const detection = withIndicators("dotnet", indicatorFiles)
	const globalJson = await readText(join(root, "global.json"))
	const sdkVersion = globalJson.match(/"version"\s*:\s*"([^"]+)"/)?.[1]
	if (sdkVersion) detection.version_info.sdk = sdkVersion
	if (!(await commandExists("dotnet", ["--info"]))) {
		detection.blockers.push(createBlocker("dotnet", `Required by ${indicatorFiles.join(", ")}.`, null))
		return finalizeDetection(detection)
	}
	detection.commands.push({ label: "dotnet info", argv: ["dotnet", "--info"], reason: "Verify the .NET SDK is available." })
	detection.commands.push({ label: "dotnet restore", argv: ["dotnet", "restore"], reason: "Restore .NET project dependencies." })
	return finalizeDetection(detection)
}

async function detectFlutterBootstrap(root: string): Promise<StackDetectionResult> {
	if (!(await exists(join(root, "pubspec.yaml")))) return emptyDetection("flutter-dart")
	const pubspec = await readText(join(root, "pubspec.yaml"))
	const isFlutter = /^\s*flutter\s*:/m.test(pubspec)
	const detection = withIndicators("flutter-dart", ["pubspec.yaml"])
	const sdkConstraint = pubspec.match(/^\s*sdk:\s*["']?([^"'\n]+)/m)?.[1]
	if (sdkConstraint) detection.version_info.sdk = sdkConstraint
	if (isFlutter) {
		if (!(await commandExists("flutter"))) detection.blockers.push(createBlocker("flutter", "Required by Flutter pubspec.yaml project.", null))
		else detection.commands.push({ label: "flutter pub get", argv: ["flutter", "pub", "get"], reason: "Resolve Flutter package dependencies." })
	} else {
		if (!(await commandExists("dart"))) detection.blockers.push(createBlocker("dart", "Required by Dart pubspec.yaml project.", null))
		else detection.commands.push({ label: "dart pub get", argv: ["dart", "pub", "get"], reason: "Resolve Dart package dependencies." })
	}
	return finalizeDetection(detection)
}

async function detectSwiftBootstrap(root: string): Promise<StackDetectionResult> {
	const indicatorFiles = ["Package.swift"].filter((file) => existsSync(join(root, file))).concat((await listRootEntries(root)).filter((entry) => /\.(?:xcodeproj|xcworkspace)$/.test(entry)))
	if (indicatorFiles.length === 0) return emptyDetection("swift")
	const detection = withIndicators("swift", indicatorFiles)
	if (!(await commandExists("swift"))) detection.blockers.push(createBlocker("swift", `Required by ${indicatorFiles.join(", ")}.`, null))
	else detection.commands.push({ label: "swift version", argv: ["swift", "--version"], reason: "Verify Swift is available." })
	if (!(await commandExists("swiftc"))) detection.blockers.push(createBlocker("swiftc", `Required by ${indicatorFiles.join(", ")}.`, null))
	if (indicatorFiles.some((entry) => /\.(?:xcodeproj|xcworkspace)$/.test(entry))) {
		if (await commandExists("xcodebuild", ["-version"])) detection.commands.push({ label: "xcodebuild version", argv: ["xcodebuild", "-version"], reason: "Verify Xcode build tooling is available." })
		else detection.warnings.push("Xcode project detected but xcodebuild is not available on this host.")
	}
	return finalizeDetection(detection)
}

async function detectZigBootstrap(root: string): Promise<StackDetectionResult> {
	const indicatorFiles = ["build.zig", "build.zig.zon"].filter((file) => existsSync(join(root, file)))
	if (indicatorFiles.length === 0) return emptyDetection("zig")
	const detection = withIndicators("zig", indicatorFiles)
	if (!(await commandExists("zig"))) detection.blockers.push(createBlocker("zig", `Required by ${indicatorFiles.join(", ")}.`, null))
	else detection.commands.push({ label: "zig version", argv: ["zig", "version"], reason: "Verify Zig is available." })
	return finalizeDetection(detection)
}

async function detectRubyBootstrap(root: string): Promise<StackDetectionResult> {
	const indicatorFiles = ["Gemfile"].filter((file) => existsSync(join(root, file))).concat(await rootEntriesMatching(root, /\.gemspec$/))
	if (indicatorFiles.length === 0) return emptyDetection("ruby")
	const detection = withIndicators("ruby", indicatorFiles)
	if (!(await commandExists("ruby"))) detection.blockers.push(createBlocker("ruby", `Required by ${indicatorFiles.join(", ")}.`, null))
	const bundlerExecutable = (await commandExists("bundle")) ? "bundle" : (await commandExists("bundler")) ? "bundler" : null
	if (!bundlerExecutable) detection.blockers.push(createBlocker("bundler", "Required to install Gemfile dependencies.", "gem install bundler"))
	else detection.commands.push({ label: "bundle install", argv: [bundlerExecutable, "install"], reason: "Install Ruby gem dependencies." })
	return finalizeDetection(detection)
}

async function detectElixirBootstrap(root: string): Promise<StackDetectionResult> {
	if (!(await exists(join(root, "mix.exs")))) return emptyDetection("elixir")
	const detection = withIndicators("elixir", ["mix.exs"])
	if (!(await commandExists("elixir"))) detection.blockers.push(createBlocker("elixir", "Required by mix.exs.", null))
	if (!(await commandExists("mix"))) detection.blockers.push(createBlocker("mix", "Required by mix.exs.", null))
	else detection.commands.push({ label: "mix deps.get", argv: ["mix", "deps.get"], reason: "Resolve Elixir dependencies." })
	return finalizeDetection(detection)
}

async function detectPhpBootstrap(root: string): Promise<StackDetectionResult> {
	if (!(await exists(join(root, "composer.json")))) return emptyDetection("php")
	const detection = withIndicators("php", ["composer.json"])
	if (!(await commandExists("php", ["-v"]))) detection.blockers.push(createBlocker("php", "Required by composer.json.", null))
	if (!(await commandExists("composer", ["--version"]))) detection.blockers.push(createBlocker("composer", "Required by composer.json.", null))
	else detection.commands.push({ label: "composer install", argv: ["composer", "install"], reason: "Install PHP dependencies." })
	return finalizeDetection(detection)
}

async function detectHaskellBootstrap(root: string): Promise<StackDetectionResult> {
	const indicatorFiles = (await rootEntriesMatching(root, /\.cabal$/)).concat(["stack.yaml", "cabal.project"].filter((file) => existsSync(join(root, file))))
	if (indicatorFiles.length === 0) return emptyDetection("haskell")
	const detection = withIndicators("haskell", indicatorFiles)
	if (!(await commandExists("ghc", ["--version"]))) detection.blockers.push(createBlocker("ghc", `Required by ${indicatorFiles.join(", ")}.`, null))
	if (indicatorFiles.includes("stack.yaml")) {
		if (!(await commandExists("stack", ["--version"]))) detection.blockers.push(createBlocker("stack", "Required by stack.yaml.", null))
		else detection.commands.push({ label: "stack version", argv: ["stack", "--version"], reason: "Verify Stack is available." })
	} else {
		if (!(await commandExists("cabal", ["--version"]))) detection.blockers.push(createBlocker("cabal", `Required by ${indicatorFiles.join(", ")}.`, null))
		else detection.commands.push({ label: "cabal version", argv: ["cabal", "--version"], reason: "Verify Cabal is available." })
	}
	return finalizeDetection(detection)
}

async function detectGenericMakeBootstrap(root: string): Promise<StackDetectionResult> {
	if (!(await exists(join(root, "Makefile")))) return emptyDetection("generic-make")
	const detection = withIndicators("generic-make", ["Makefile"])
	if (!(await commandExists("make"))) {
		detection.blockers.push(createBlocker("make", "Required by Makefile.", null))
		return finalizeDetection(detection)
	}
	detection.commands.push({ label: "make query", argv: ["make", "-qp"], reason: "Inspect available Make targets for manual bootstrap guidance." })
	detection.warnings.push("Generic Makefile surface detected. Review the reported targets and choose the project-specific bootstrap target if needed.")
	return finalizeDetection(detection)
}

async function detectGenericShellBootstrap(root: string): Promise<StackDetectionResult> {
	const indicatorFiles = ["build.sh", "install.sh", "bootstrap.sh", "setup.sh"].filter((file) => existsSync(join(root, file)))
	if (indicatorFiles.length === 0) return emptyDetection("generic-shell")
	const detection = withIndicators("generic-shell", indicatorFiles)
	detection.warnings.push(`Manual bootstrap scripts detected: ${indicatorFiles.join(", ")}. Review them manually before execution.`)
	return finalizeDetection(detection)
}

const STACK_ADAPTERS: StackAdapter[] = [
	{ id: "node", detect: detectNodeBootstrap },
	{ id: "python", detect: detectPythonBootstrap },
	{ id: "rust", detect: detectRustBootstrap },
	{ id: "go", detect: detectGoBootstrap },
	{ id: "godot", detect: detectGodotBootstrap },
	{ id: "java-android", detect: detectJavaAndroidBootstrap },
	{ id: "c-cpp", detect: detectCppBootstrap },
	{ id: "dotnet", detect: detectDotnetBootstrap },
	{ id: "flutter-dart", detect: detectFlutterBootstrap },
	{ id: "swift", detect: detectSwiftBootstrap },
	{ id: "zig", detect: detectZigBootstrap },
	{ id: "ruby", detect: detectRubyBootstrap },
	{ id: "elixir", detect: detectElixirBootstrap },
	{ id: "php", detect: detectPhpBootstrap },
	{ id: "haskell", detect: detectHaskellBootstrap },
	{ id: "generic-make", detect: detectGenericMakeBootstrap },
	{ id: "generic-shell", detect: detectGenericShellBootstrap },
]

async function detectCommands(root: string): Promise<DetectionResult> {
	const detections = (await Promise.all(STACK_ADAPTERS.map((adapter) => adapter.detect(root)))).filter((detection) => detection.detected)
	const blockers = detections.flatMap((detection) => detection.blockers)
	const warnings = detections.flatMap((detection) => detection.warnings)
	const missingPrerequisites = unique([
		...detections.flatMap((detection) => detection.missing_executables),
		...detections.flatMap((detection) => detection.missing_env_vars),
		...blockers.map((blocker) => blocker.executable),
	])
	const commands: CommandSpec[] = []
	const seenCommands = new Set<string>()
	for (const detection of detections) {
		for (const command of detection.commands) {
			const rendered = renderCommand(command)
			if (seenCommands.has(rendered)) continue
			seenCommands.add(rendered)
			commands.push(command)
		}
	}
	return { detections, commands, blockers, warnings: unique(warnings), missingPrerequisites }
}

export default tool({
	description: "Install and verify project/runtime/test dependencies, then record bootstrap proof for the repo environment.",
	args: {
		ticket_id: tool.schema.string().describe("Optional ticket id that owns the bootstrap proof artifact. Defaults to the active ticket.").optional(),
		recovery_mode: tool.schema.boolean().describe("Whether this bootstrap run is being used to recover a blocked planning or lease state.").optional(),
	},
	async execute(args) {
		const manifest = await loadManifest()
		const workflow = await loadWorkflowState()
		const ticket = getTicket(manifest, args.ticket_id)
		const root = rootPath()
		const detection = await detectCommands(root)
		const unsafeWarnings = detection.commands.filter((command) => !isSafeBootstrapCommand(command)).map((command) => `Rejected unsafe bootstrap command: ${renderCommand(command)}`)
		const commands = detection.commands.filter((command) => isSafeBootstrapCommand(command))
		const results: CommandResult[] = []
		const warnings = unique([...detection.warnings, ...unsafeWarnings])
		const missingPrerequisites = new Set(detection.missingPrerequisites)
		let hostSurfaceClassification: "none" | "missing_executable" | "permission_restriction" | "command_error" = detection.blockers.length > 0 || detection.missingPrerequisites.length > 0
			? "missing_executable"
			: "none"
		let passed = detection.blockers.length === 0 && detection.missingPrerequisites.length === 0

		if (passed) {
			for (const command of commands) {
				const result = await runCommand(root, command)
				results.push(result)
				if (isAdvisoryBootstrapFailure(command, result)) {
					warnings.push(`Ignoring non-fatal advisory bootstrap probe failure: ${renderCommand(command)}`)
					continue
				}
				if (hostSurfaceClassification === "none" && result.failure_classification) {
					hostSurfaceClassification = result.failure_classification
				}
				for (const missing of classifyMissingPrerequisites(command, result)) {
					missingPrerequisites.add(missing)
				}
				if (result.exit_code !== 0) {
					passed = false
					break
				}
			}
		}

		const fingerprint = await computeBootstrapFingerprint(root)
		const blockers = detection.blockers
		if (missingPrerequisites.size > 0) {
			passed = false
		}
		workflow.bootstrap_blockers = blockers
		const note = blockers.length > 0
			? `Bootstrap failed because required bootstrap prerequisites are missing: ${blockers.map((item) => item.executable).join(", ")}. Resolve the blockers or surface them to the user before implementation.`
			: missingPrerequisites.size > 0
				? `Bootstrap failed because required bootstrap prerequisites are missing: ${[...missingPrerequisites].join(", ")}. Install or seed the missing toolchain pieces, then rerun environment_bootstrap.`
				: hostSurfaceClassification === "permission_restriction"
					? "Bootstrap failed because the host denied a required command or file access path. Fix the permission/tool policy or run bootstrap in a host that allows the managed commands, then rerun environment_bootstrap."
					: passed
						? args.recovery_mode
							? "Dependency installation and bootstrap verification completed successfully in bootstrap-recovery mode."
							: "Dependency installation and bootstrap verification completed successfully."
						: "Bootstrap stopped on the first failing installation or readiness command. Inspect the captured output and fix the prerequisite or dependency error before smoke tests."
		const body = renderArtifact(ticket.id, fingerprint, detection.detections, results, blockers, warnings, [...missingPrerequisites], passed, note)
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

		await saveWorkflowBundle({ workflow, manifest, registry, skipGraphValidation: true })

		return JSON.stringify(
			{
				ticket_id: ticket.id,
				bootstrap_status: workflow.bootstrap.status,
				recovery_mode: args.recovery_mode === true,
				proof_artifact: artifact.path,
				environment_fingerprint: fingerprint,
				host_surface_classification: hostSurfaceClassification,
				missing_prerequisites: [...missingPrerequisites],
				blockers,
				warnings,
				detections: detection.detections.map((item) => ({
					adapter_id: item.adapter_id,
					indicator_files: item.indicator_files,
					missing_executables: item.missing_executables,
					missing_env_vars: item.missing_env_vars,
					version_info: item.version_info,
					warnings: item.warnings,
				})),
				bootstrap_commands: commands.map((command) => ({ label: command.label, command: renderCommand(command), reason: command.reason })),
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
