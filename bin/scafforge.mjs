#!/usr/bin/env node
import { spawnSync } from "node:child_process"
import { fileURLToPath } from "node:url"
import path from "node:path"

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, "..")

function runPython(scriptPath, args) {
  for (const executable of ["python3", "python"]) {
    const result = spawnSync(executable, [scriptPath, ...args], {
      cwd: process.cwd(),
      stdio: "inherit",
    })
    if (!result.error || result.error.code !== "ENOENT") {
      process.exit(result.status ?? 1)
    }
  }
  console.error("Unable to find a Python interpreter. Install python3 or provide `python` in PATH.")
  process.exit(1)
}

const [command, ...args] = process.argv.slice(2)

if (!command || command === "help" || command === "--help" || command === "-h") {
  console.log(`Scafforge

Usage:
  scafforge render-full <args...>
  scafforge render-opencode <args...>
  scafforge repair-process <repo-root> [args...]
  scafforge validate-contract

Commands:
  render-full       Wrap skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py
  render-opencode   Wrap skills/opencode-team-bootstrap/scripts/bootstrap_opencode_team.py
  repair-process    Wrap skills/repo-process-doctor/scripts/apply_repo_process_repair.py
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

if (command === "repair-process") {
  runPython(path.join(root, "skills", "repo-process-doctor", "scripts", "apply_repo_process_repair.py"), args)
}

console.error(`Unknown command: ${command}`)
process.exit(1)
