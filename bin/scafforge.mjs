#!/usr/bin/env node
import { spawnSync } from "node:child_process"
import { fileURLToPath } from "node:url"
import path from "node:path"

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, "..")

function runPython(scriptPath, args) {
  const result = spawnSync("python", [scriptPath, ...args], {
    cwd: root,
    stdio: "inherit",
  })
  process.exit(result.status ?? 1)
}

const [command, ...args] = process.argv.slice(2)

if (!command || command === "help" || command === "--help" || command === "-h") {
  console.log(`Scafforge

Usage:
  scafforge render-full <args...>
  scafforge render-opencode <args...>
  scafforge validate-contract

Commands:
  render-full       Wrap skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py
  render-opencode   Wrap skills/opencode-team-bootstrap/scripts/bootstrap_opencode_team.py
  validate-contract Run the Scafforge contract validator
`)
  process.exit(0)
}

if (command === "render-full") {
  runPython(path.join(root, "skills", "repo-scaffold-factory", "scripts", "bootstrap_repo_scaffold.py"), args)
}

if (command === "render-opencode") {
  runPython(path.join(root, "skills", "opencode-team-bootstrap", "scripts", "bootstrap_opencode_team.py"), args)
}

if (command === "validate-contract") {
  runPython(path.join(root, "scripts", "validate_scafforge_contract.py"), args)
}

console.error(`Unknown command: ${command}`)
process.exit(1)
