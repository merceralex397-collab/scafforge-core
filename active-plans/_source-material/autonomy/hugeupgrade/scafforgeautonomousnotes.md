Scafforge extension / upgrade plan / rework

Autonomous Mode, Orchestration, and a viewer app

The objective: To have a fully autonomous AI powered software development factory. A self improving loop. 

This will work by essentially automating our entire lifecycle / process with Scafforge and downstream repositories.

Process would be as follows:


Spec Maker Workspace
This has AI agents with a variety of different skills. They can receive concepts or ideas, and expand on these thoroughly.
I'm thinking a few different ideas on this. Firstly, if we make this workspace exposed as an MCP server, then services like ChatGPT that can run automations can send ideas here. We can also have researcher agents, that would be able to check places like Reddit, or other parts of the internet, in order to get ideas, storyline ideas etc.
Agents for more technical design. Agents for writing stories/world building/character design. Agents for describing art style, themes, asset types etc.
So here, we would have an "inbox" folder where if a file is dropped in, an AI agent is automatically triggered to work on it and turn it into a full spec. When they finish, they move it into approved. 
If a spec gets moved to approved, it would call a scafforge-greenfield-automation agent.

This agent would just run the typical greenfield process for Scafforge.


Note: This would be our *Final* version.

The downstream repository would then begin working. I'm thinking that after each phase is completed in downstreams, each phase should go on as a PR at this point. There should be a tool to call an independent code reviewer agent. 

This agent performs a thorough review of the implementation. Checks against the specs, the tickets, the code itself, confirms best practices. We may need specialized reviewer agents for each stack type. If not, we would at least need specialized agent skills. 

Each phase should have specific completion criterias so that the PR cannot be merged until they are met. 

If the downstream repo should hit a blocker, or the code reviewer finds any problems, this should trigger a scafforge-audit-agent to be ran.

This agent would follow the normal audit process and a copy is added to the scafforge-archive repo.

At this point, we want a new agent type / skill to be used:

scafforge-investigator-agent
This agents job is to examine the repo, the audit report, the work logs, and scafforge itself. It should compile a complete investigative report explaining how the downstream repository ran into issues, and how these could have been prevented by Scafforge. 

scafforge-fixer-agent - this agent would implement the full scope of the changes from investigator agent. This then gets submitted as a PR.

another review should be ran here, this time for the scafforge PR itself. Any issues get sent back to the fixer agent.

When issues are resolved and Scafforge can be merged, then, a new agent can be called to run audit/repair on the downstream repo.

Then, the downstream repo would resume working. 


Additional scafforge agents:

1. scafforge-meta-skill-engineer-agent

Meta-Skill-Engineering is a skill creation/improvement/enhancement system that I created. The idea here would be that this would be able to seed Scafforge with a library of extra skills that can be added to downstream repositories upon greenfield generation.

Additionally, if the skills in downstream repos seem problematic, then an agent can be invoked using this toolset in order to enhance the downstream skills.


2. scafforge-archive-researcher-agent

This agent to be ran periodically (can be adjusted). Will go through any logs or files within the archives and examine the current scafforge repo state.

Would periodically pull logs / session files / database info from agent runs and add to the archive and categorize.

Checks scafforge for regressions.

Checks logs for recurring patterns or issues that are blockers.

Checks for any unimplemented steps from plans.

Checks for any agent confusion during downstream work and how this can be streamlined/helped.

Checks for any other issues within scafforge.

Will create a plan that is sent to scafforge-fixer-agent. PR is opened in the same way as previous method, reviewed, and merged.

For the app:










