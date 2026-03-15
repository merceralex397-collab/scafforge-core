import { spawnSync } from "node:child_process"
import { readdirSync } from "node:fs"
import { homedir } from "node:os"
import path from "node:path"
import process from "node:process"
import { parseArgs } from "node:util"
import { createInterface } from "node:readline/promises"

const DEFAULT_SCOPE = "full"
const DEFAULT_STACK_LABEL = "framework-agnostic"
const VALID_SCOPE_VALUES = new Set(["full", "opencode"])

function availableProfiles(root) {
  try {
    const profileRoot = path.join(root, "skills", "repo-scaffold-factory", "profiles")
    const profiles = readdirSync(profileRoot)
      .filter((entry) => entry.endsWith(".json"))
      .map((entry) => entry.slice(0, -".json".length))
      .sort()

    return profiles.length > 0 ? profiles : ["full"]
  } catch {
    return ["full"]
  }
}

function printInitHelp(profiles) {
  console.log(`Scafforge init

Usage:
  scafforge init [options]

This guided command collects the explicit scaffold decisions already required by
the bootstrap script, then forwards them to:
  skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py

Options:
  --dest <path>                 Prefill the destination repository root
  --project-name <name>         Prefill the human-facing project name
  --project-slug <slug>         Prefill the slug used in filenames
  --agent-prefix <prefix>       Prefill the OpenCode agent prefix
  --model-provider <provider>   Prefill the runtime model provider label
  --planner-model <model>       Prefill the planner/reviewer model
  --implementer-model <model>   Prefill the implementer model
  --utility-model <model>       Prefill the utility/docs model
  --profile <name>              Prefill scaffold profile (${profiles.join(", ")})
  --scope <full|opencode>       Prefill scaffold scope (default: full)
  --stack-label <label>         Prefill the stack label (default: framework-agnostic)
  --force                       Default the overwrite prompt to yes
  --yes                         Skip the final confirmation prompt
  -h, --help                    Show help for this command
`)
}

function slugify(value) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/-{2,}/g, "-")
    .replace(/^-|-$/g, "") || "project"
}

function expandHome(value) {
  if (value === "~") {
    return homedir()
  }

  if (value.startsWith("~/") || value.startsWith("~\\")) {
    return path.join(homedir(), value.slice(2))
  }

  return value
}

function resolveDest(value) {
  return path.resolve(expandHome(value))
}

function normalizeScope(value) {
  const normalized = value.trim().toLowerCase()

  if (normalized === "f") {
    return "full"
  }

  if (normalized === "o") {
    return "opencode"
  }

  return normalized
}

function validateSlug(value, label) {
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value)) {
    return `${label} must use lowercase letters, numbers, and hyphens only.`
  }

  return null
}

async function promptText(rl, label, { defaultValue, required = false, validate, transform = (value) => value } = {}) {
  while (true) {
    const suffix = defaultValue ? ` [${defaultValue}]` : ""
    const raw = await rl.question(`${label}${suffix}: `)
    const candidate = raw.trim() || defaultValue || ""

    if (!candidate) {
      if (required) {
        console.error(`${label} is required.`)
        continue
      }

      return ""
    }

    const transformed = transform(candidate)
    const error = validate?.(transformed)

    if (error) {
      console.error(error)
      continue
    }

    return transformed
  }
}

async function promptYesNo(rl, label, defaultValue = false) {
  const hint = defaultValue ? "Y/n" : "y/N"

  while (true) {
    const raw = (await rl.question(`${label} [${hint}]: `)).trim().toLowerCase()

    if (!raw) {
      return defaultValue
    }

    if (raw === "y" || raw === "yes") {
      return true
    }

    if (raw === "n" || raw === "no") {
      return false
    }

    console.error("Please answer yes or no.")
  }
}

function printSummary(config) {
  console.log(`
Scafforge init summary
  Project name:       ${config.projectName}
  Project slug:       ${config.projectSlug}
  Destination:        ${config.dest}
  Agent prefix:       ${config.agentPrefix}
  Profile:            ${config.profile}
  Scope:              ${config.scope}
  Output profile:     OpenCode-oriented
  Model provider:     ${config.modelProvider}
  Planner model:      ${config.plannerModel}
  Implementer model:  ${config.implementerModel}
  Utility model:      ${config.utilityModel}
  Stack label:        ${config.stackLabel}
  Overwrite files:    ${config.force ? "yes" : "no"}
`)
}

function buildBootstrapArgs(config) {
  const args = [
    "--dest",
    config.dest,
    "--project-name",
    config.projectName,
    "--project-slug",
    config.projectSlug,
    "--agent-prefix",
    config.agentPrefix,
    "--model-provider",
    config.modelProvider,
    "--planner-model",
    config.plannerModel,
    "--implementer-model",
    config.implementerModel,
    "--utility-model",
    config.utilityModel,
    "--profile",
    config.profile,
    "--scope",
    config.scope,
    "--stack-label",
    config.stackLabel,
  ]

  if (config.force) {
    args.push("--force")
  }

  return args
}

function buildNonInteractiveConfig(seed, profiles) {
  const projectName = (seed.projectName || "").trim()
  if (!projectName) {
    throw new Error("--project-name is required when using --yes.")
  }

  const projectSlug = seed.projectSlug || slugify(projectName)
  const slugError = validateSlug(projectSlug, "Project slug")
  if (slugError) {
    throw new Error(slugError)
  }

  const agentPrefix = seed.agentPrefix || projectSlug
  const prefixError = validateSlug(agentPrefix, "Agent prefix")
  if (prefixError) {
    throw new Error(prefixError)
  }

  const profile = seed.profile || "full"
  if (!profiles.includes(profile)) {
    throw new Error(`Profile must be one of: ${profiles.join(", ")}.`)
  }

  const scope = normalizeScope(seed.scope || DEFAULT_SCOPE)
  if (!VALID_SCOPE_VALUES.has(scope)) {
    throw new Error("Scope must be either full or opencode.")
  }

  const modelProvider = (seed.modelProvider || "").trim()
  const plannerModel = (seed.plannerModel || "").trim()
  const implementerModel = (seed.implementerModel || "").trim()
  if (!modelProvider) {
    throw new Error("--model-provider is required when using --yes.")
  }
  if (!plannerModel) {
    throw new Error("--planner-model is required when using --yes.")
  }
  if (!implementerModel) {
    throw new Error("--implementer-model is required when using --yes.")
  }

  return {
    projectName,
    projectSlug,
    dest: resolveDest(seed.dest || path.resolve(process.cwd(), projectSlug)),
    agentPrefix,
    profile,
    scope,
    modelProvider,
    plannerModel,
    implementerModel,
    utilityModel: (seed.utilityModel || plannerModel).trim(),
    stackLabel: (seed.stackLabel || DEFAULT_STACK_LABEL).trim(),
    force: Boolean(seed.force),
  }
}

function parseInitArgs(args, profiles) {
  const parsed = parseArgs({
    args,
    allowPositionals: true,
    options: {
      help: { type: "boolean", short: "h" },
      dest: { type: "string" },
      "project-name": { type: "string" },
      "project-slug": { type: "string" },
      "agent-prefix": { type: "string" },
      "model-provider": { type: "string" },
      "planner-model": { type: "string" },
      "implementer-model": { type: "string" },
      "utility-model": { type: "string" },
      profile: { type: "string" },
      scope: { type: "string" },
      "stack-label": { type: "string" },
      force: { type: "boolean" },
      yes: { type: "boolean" },
    },
  })

  if (parsed.positionals.length > 0) {
    throw new Error(`Unexpected arguments: ${parsed.positionals.join(" ")}`)
  }

  if (parsed.values.scope) {
    const scope = normalizeScope(parsed.values.scope)

    if (!VALID_SCOPE_VALUES.has(scope)) {
      throw new Error(`Invalid --scope value: ${parsed.values.scope}`)
    }

    parsed.values.scope = scope
  }

  if (parsed.values.profile && !profiles.includes(parsed.values.profile)) {
    throw new Error(`Invalid --profile value: ${parsed.values.profile}`)
  }

  return parsed.values
}

async function collectConfig(seed, profiles) {
  const rl = createInterface({
    input: process.stdin,
    output: process.stdout,
  })

  try {
    console.log("Scafforge init collects the explicit bootstrap inputs before rendering.")
    console.log("Press Enter to accept a default where one is shown.\n")

    const projectName = await promptText(rl, "Project name", {
      defaultValue: seed.projectName,
      required: true,
    })

    const suggestedSlug = seed.projectSlug || slugify(projectName)
    const projectSlug = await promptText(rl, "Project slug", {
      defaultValue: suggestedSlug,
      required: true,
      validate: (value) => validateSlug(value, "Project slug"),
    })

    const suggestedDest = seed.dest ? resolveDest(seed.dest) : path.resolve(process.cwd(), projectSlug)
    const dest = await promptText(rl, "Destination repository root", {
      defaultValue: suggestedDest,
      required: true,
      transform: resolveDest,
    })

    const agentPrefix = await promptText(rl, "Agent prefix", {
      defaultValue: seed.agentPrefix || projectSlug,
      required: true,
      validate: (value) => validateSlug(value, "Agent prefix"),
    })

    const profile = await promptText(rl, `Scaffold profile (${profiles.join("/")})`, {
      defaultValue: seed.profile || "full",
      required: true,
      validate: (value) => (profiles.includes(value) ? null : `Profile must be one of: ${profiles.join(", ")}.`),
    })

    const scope = await promptText(rl, "Scaffold scope (full/opencode)", {
      defaultValue: seed.scope || DEFAULT_SCOPE,
      required: true,
      transform: normalizeScope,
      validate: (value) => (VALID_SCOPE_VALUES.has(value) ? null : "Scope must be either full or opencode."),
    })

    const modelProvider = await promptText(rl, "Model provider", {
      defaultValue: seed.modelProvider,
      required: true,
    })

    const plannerModel = await promptText(rl, "Planner model", {
      defaultValue: seed.plannerModel,
      required: true,
    })

    const implementerModel = await promptText(rl, "Implementer model", {
      defaultValue: seed.implementerModel,
      required: true,
    })

    const utilityModel = await promptText(rl, "Utility model", {
      defaultValue: seed.utilityModel || plannerModel,
      required: true,
    })

    const stackLabel = await promptText(rl, "Stack label", {
      defaultValue: seed.stackLabel || DEFAULT_STACK_LABEL,
      required: true,
    })

    const force = await promptYesNo(rl, "Overwrite existing files if needed?", seed.force)

    return {
      projectName,
      projectSlug,
      dest,
      agentPrefix,
      profile,
      scope,
      modelProvider,
      plannerModel,
      implementerModel,
      utilityModel,
      stackLabel,
      force,
    }
  } finally {
    rl.close()
  }
}

export async function runInitCommand({ root, args }) {
  const profiles = availableProfiles(root)
  let parsed

  try {
    parsed = parseInitArgs(args, profiles)
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error))
    console.error("Run `scafforge init --help` for usage.")
    return 1
  }

  if (parsed.help) {
    printInitHelp(profiles)
    return 0
  }

  const seed = {
    projectName: parsed["project-name"],
    projectSlug: parsed["project-slug"],
    dest: parsed.dest,
    agentPrefix: parsed["agent-prefix"],
    profile: parsed.profile,
    scope: parsed.scope,
    modelProvider: parsed["model-provider"],
    plannerModel: parsed["planner-model"],
    implementerModel: parsed["implementer-model"],
    utilityModel: parsed["utility-model"],
    stackLabel: parsed["stack-label"],
    force: Boolean(parsed.force),
  }
  const config = parsed.yes ? buildNonInteractiveConfig(seed, profiles) : await collectConfig(seed, profiles)

  printSummary(config)

  if (!parsed.yes) {
    const rl = createInterface({
      input: process.stdin,
      output: process.stdout,
    })

    try {
      const shouldContinue = await promptYesNo(rl, "Render the scaffold with these settings?", true)

      if (!shouldContinue) {
        console.log("Init cancelled.")
        return 0
      }
    } finally {
      rl.close()
    }
  }

  const bootstrapScript = path.join(root, "skills", "repo-scaffold-factory", "scripts", "bootstrap_repo_scaffold.py")
  const result = spawnSync("python", [bootstrapScript, ...buildBootstrapArgs(config)], {
    cwd: root,
    stdio: "inherit",
  })

  return result.status ?? 1
}
