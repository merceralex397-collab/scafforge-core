#!/usr/bin/env node
import { spawnSync } from "node:child_process"
import { fileURLToPath } from "node:url"
import path from "node:path"
import { runInitCommand } from "./scafforge-init.mjs"

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, "..")

function runPython(scriptPath, args) {
  const result = spawnSync("python", [scriptPath, ...args], {
    cwd: root,
    stdio: "inherit",
  })
  return result.status ?? 1
}

const [command, ...args] = process.argv.slice(2)

async function main() {
  if (!command || command === "help" || command === "--help" || command === "-h") {
    console.log(`Scafforge

Usage:
  scafforge init [options]
  scafforge render-full [--profile full|minimum] <args...>
  scafforge render-opencode [--profile full|minimum] <args...>
  scafforge validate-contract

Commands:
  init              Prompt for scaffold decisions and forward them to the bootstrap script
  render-full       Render the full scaffold; defaults to the full profile
  render-opencode   Render only the OpenCode layer; accepts the same profile flag
  validate-contract Run the Scafforge contract validator
`)
    return 0
  }

  if (command === "init") {
    return runInitCommand({ root, args })
  }

  if (command === "render-full") {
    return runPython(path.join(root, "skills", "repo-scaffold-factory", "scripts", "bootstrap_repo_scaffold.py"), args)
  }

  if (command === "render-opencode") {
    return runPython(path.join(root, "skills", "opencode-team-bootstrap", "scripts", "bootstrap_opencode_team.py"), args)
  }

  if (command === "validate-contract") {
    return runPython(path.join(root, "scripts", "validate_scafforge_contract.py"), args)
  }

  console.error(`Unknown command: ${command}`)
  return 1
}

main()
  .then((code) => {
    process.exit(code)
  })
  .catch((error) => {
    console.error(error instanceof Error ? error.message : String(error))
    process.exit(1)
  })
