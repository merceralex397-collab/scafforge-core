# Prompt Anti-Patterns

## Status over evidence

Bad:

- `planned` means a planner output must already exist

Why it fails:

- weaker models route from labels even when the canonical artifact is missing

Safer pattern:

- keep status coarse
- require the actual planner artifact or full plan content before plan review

## Raw-file stage control

Bad:

- update the ticket file, board, and manifest directly to move stages

Why it fails:

- three surfaces drift
- read-only agents get impossible instructions

Safer pattern:

- use ticket tools and workflow state for stage control
- derive the board from manifest state

## Impossible read-only delegation

Bad:

- ask a planner or inspection agent to write repo files

Why it fails:

- the model either hallucinates success or routes around the missing capability

Safer pattern:

- persist artifacts only through write-capable tools
- make capability limits explicit in the prompt

## Broad command follow-on scope

Bad:

- a status or preflight command silently continues the whole workflow

Why it fails:

- the agent over-runs the user's requested scope

Safer pattern:

- keep human entrypoint commands narrow
- state the exact next internal stage and stop if the command is only a summary or preflight action

## Eager skill loading

Bad:

- tell a primary agent to `Load these skills:` before it resolves ticket or workflow state

Why it fails:

- weaker models may call the skill tool immediately with missing or malformed arguments
- the agent burns its first step on setup choreography instead of resolving the actual task state

Safer pattern:

- start from `ticket_lookup` or the canonical state tool first
- tell the agent to load a named skill only when it materially reduces ambiguity
- if the skill tool is used, load one explicit skill name at a time

## Workflow thrash loops

Bad:

- retry the same `ticket_update` transition until something different happens

Why it fails:

- the agent burns time and tokens without learning anything new
- repeated lifecycle errors often mean the contract or artifact proof is missing, not that more probing will help

Safer pattern:

- after the first lifecycle rejection, re-run `ticket_lookup`
- read `transition_guidance`
- load `ticket-execution` if process ambiguity remains
- if the same blocker repeats, stop and return the contradiction instead of probing

## Unsupported stage probing

Bad:

- try `stage=todo`, jump straight to `qa`, or search for another stage/status pair that the tool will accept

Why it fails:

- the state machine becomes guess-and-check instead of evidence-driven workflow
- weaker models start searching for loopholes instead of fixing the missing proof

Safer pattern:

- validate stage transitions against the explicit lifecycle contract
- reject unknown stages
- route the agent back to the required artifact or approval state

## Evidence-free PASS claims

Bad:

- write implementation, QA, or smoke-test artifacts that say PASS when the transcript shows validation could not run

Why it fails:

- later routing decisions trust fabricated evidence
- closeout appears complete even though no executable proof exists

Safer pattern:

- require raw command output in implementation and QA artifacts
- make `smoke_test` the only legal producer of smoke-test artifacts
- return a blocker whenever validation cannot run

## Slash-command self-use

Bad:

- tell an agent to use `/resume`, `/kickoff`, or another `.opencode/commands/` entry as part of autonomous execution

Why it fails:

- commands are human entrypoints, not internal workflow primitives
- the agent starts treating documentation as a hidden tool surface

Safer pattern:

- keep human commands narrow and human-invoked only
- put autonomous routing in tools, plugins, prompts, and repo-local skills
