Scafforge: Autonomous Orchestration & Self-Improving Loop

Implementation & Architecture Plan

1. Executive Summary

Objective: Transform Scafforge into a fully autonomous, self-improving AI software development factory.
By automating the entire lifecycle—from raw idea ingestion to code generation, review, self-correction, and meta-improvement—Scafforge will operate as an independent pipeline that not only builds downstream repositories but continuously analyzes its own failures to upgrade its own source code and skill sets.

2. Architectural Pipeline Overview

The autonomous factory operates in a continuous, multi-stage loop, orchestrated across local and remote environments:

Ideation: Spec Maker Workspace (Idea $\rightarrow$ Spec)

Scaffolding: Greenfield Automation (Spec $\rightarrow$ Base Repo)

Execution & Review: Downstream Work (Code $\rightarrow$ PR $\rightarrow$ Review)

Self-Correction (The Meta-Loop): Audit $\rightarrow$ Investigate $\rightarrow$ Fix Scafforge $\rightarrow$ Resume

Orchestration Environment: The primary control app assumes a Windows host, orchestrating agents by bridging into WSL (Windows Subsystem for Linux) where Scafforge runs natively, or via SSH to remote build servers.

3. Phase Implementation Details

Phase 1: Spec Maker Workspace (Ideation & Design)

An isolated environment where raw concepts are expanded into comprehensive technical and creative specifications.

MCP Server Integration: Expose the workspace as an MCP (Model Context Protocol) server. This allows external automation triggers (e.g., ChatGPT, scheduled tasks) to drop raw ideas directly into an "Inbox" folder.

Specialized Agent Roster:

Concept Researchers: Trawl the internet (Reddit, forums, news sites) to discover fresh ideas, gather thematic inspiration, and track trending concepts.

Technical Researchers: Gather context on standard practices, API documentation, and stack-specific conventions required for the idea.

Creative Agents: Handle world-building, storyline generation, art style definition, and theme composition (for games/apps).

Technical Agents: Draft the architecture, database schemas, and API contracts. Their output is strictly standardized to output exactly what Scafforge requires to generate the repo (formatting the exact CANONICAL-BRIEF.md structure).

Workflow: * File drops in /inbox $\rightarrow$ Triggers Spec Agents.

Agents collaborate to format a Canonical Brief.

Completed spec is moved to /approved.

Phase 2: Greenfield Automation (Project Generation)

The bridge between the specification and the codebase.

Trigger: A file landing in the /approved directory.

Agent: scafforge-greenfield-automation

Action: Executes the standard Scafforge greenfield kickoff pass (scaffold-kickoff). It reads the spec, provisions the downstream repository, generates the initial tickets, team roles, and foundational code, preparing the repo for the execution phase.

Phase 3: Downstream Execution & Verification

Autonomous development within the generated repository.

Phase-Based PRs: Agents work on specific phases/tickets. Upon completing a phase, the agent submits a Pull Request rather than committing directly to main.

Independent Code Reviewer Agent:

Triggered on PR creation.

Cross-references the PR against: The original Spec, the Ticket requirements, the existing codebase, and stack-specific best practices.

Merge Gate: The PR cannot be merged until the Code Reviewer Agent validates that all strict completion criteria (enforced by the .opencode/plugins/stage-gate-enforcer.ts) are met.

Phase 4: The Self-Improving Feedback Loop (Meta-Repair)

If the downstream repo hits a blocker, or the Code Reviewer rejects the PR due to systemic issues or hallucinations, the self-improving loop activates.

Audit & Issue Logging: scafforge-audit-agent is triggered. It runs the standard audit process, dumping diagnostic logs into scafforge-archive. Simultaneously, it logs a formal Issue on the GitHub repository to track the failure and notify human overseers. (Uses Model Router for failover).

Investigation: scafforge-investigator-agent analyzes the downstream repo state, the audit report, agent work logs, and the Scafforge source code. It outputs a comprehensive root-cause analysis explaining how Scafforge's instructions/skills failed the downstream agent. (Uses Model Router for failover).

Meta-Fixing: scafforge-fixer-agent takes the investigation report and creates a PR on the Scafforge repository itself, updating prompts, scripts, or workflow state to prevent the issue from happening again. (Uses Model Router for failover).

Meta-Review: An independent reviewer agent checks the Scafforge PR.

Resumption: Once the Scafforge PR is merged, a fresh audit/repair is triggered on the downstream repo using the newly updated Scafforge skills, and downstream work resumes.

4. Continuous Ecosystem Enhancement (Background Daemons)

Alongside the active development pipeline, background agents continuously improve the ecosystem.

A. scafforge-meta-skill-engineer-agent

Purpose: Skill creation and enhancement.

Function: Seeds Scafforge with a growing library of modular skills that can be injected into downstream repos during Greenfield generation.

Reactive Function: If downstream skills prove problematic or inefficient during execution, this agent can be invoked to surgically enhance the specific skills in the downstream repo.

B. scafforge-archive-researcher-agent

Purpose: Proactive, asynchronous system optimization. (Uses Model Router for failover).

Function: Runs on a scheduled cron job to mine the scafforge-archive repository.

Tasks:

Categorizes and structures raw logs, session files, and database info.

Checks Scafforge for regressions across multiple project runs.

Spots recurring patterns or blockers that individual run-audits might miss.

Identifies agent confusion/looping behavior to suggest prompt streamlining.

Checks active-plans for unimplemented steps.

Output: Generates a global improvement plan and sends it directly to the scafforge-fixer-agent to initiate a Scafforge upgrade PR.

5. The Viewer App (Factory Dashboard)

Fleshing out the UI/UX requirements for monitoring and managing the autonomous factory.

Since the factory operates autonomously, human interaction shifts from coding to monitoring, orchestrating, and configuring. The Viewer App should provide:

Project Initiation (The Forge): A dedicated interface allowing the user to start new projects directly from within the app. Users can type out rough ideas, drag-and-drop reference files to instantly trigger the /inbox workflow, or chat directly with the Spec Maker agents to brainstorm before kicking off the generation pipeline.

Cross-System Orchestration: Built-in terminal and execution environments capable of connecting via SSH to remote servers or directly into local WSL instances. The app acts as the bridge, ensuring commands route correctly regardless of where the Scafforge repository lives.

Provider & Model Configuration (The Model Router): A secure settings hub where users can input API keys for various providers (OpenAI, Anthropic, DeepSeek, local models, etc.). It includes a Model Router UI to assign specific models to specific agent roles. Crucially, it allows setting up Fallback Models (e.g., Primary: deepseek-reasoner, Fallback 1: gpt-4o, Fallback 2: claude-3-5-sonnet) to ensure the autonomous loop never halts due to a provider outage or rate limit.

Autonomy & Permission Controls: Granular settings to dial the factory's autonomy up or down. Users can set global or per-project permission levels:

Fully Autonomous: Agents execute, review, and merge PRs without human input.

Merge Approval: Agents do the work but require human sign-off to merge PRs.

Strict/Human-in-the-Loop: Agents require human approval for high-risk tool calls, architectural decisions, or Scafforge meta-updates.

Pipeline Visualization: A real-time kanban/node-graph showing the status of all active projects (Inbox $\rightarrow$ Spec $\rightarrow$ Scaffolding $\rightarrow$ Dev $\rightarrow$ Review $\rightarrow$ Deployed).

Includes a collapsible Ticket View that taps into tickets/manifest.json and tickets/BOARD.md, showing real-time ticket lifecycles (planning $\rightarrow$ implementation $\rightarrow$ review $\rightarrow$ qa $\rightarrow$ done).

Intervention & Override: While autonomous, the app should allow a human to dynamically pause the pipeline, manually approve/reject Specs mid-generation, or override a stuck Code Reviewer agent.

Meta-Loop Dashboard: A dedicated screen showing Scafforge's self-improvement over time. Tracks scafforge-fixer-agent PRs, showing exactly what Scafforge learned and fixed autonomously.

Live Agent Feeds: A terminal-style view tapping into the active logs of working agents (e.g., watching the Code Reviewer argue with the Dev Agent in real-time).

Archive Intelligence: A graphical interface for the scafforge-archive-researcher-agent's findings, showing metrics like "Most Common Blockers," "Agent Confusion Hotspots," and "Skill Effectiveness."