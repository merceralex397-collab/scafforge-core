1. Minimax M-2.5 Agent Testing

We have had issues around this model related to its temperature config (see the report in research - gpttalker-agent-failure-analysis)

Steps to take:

1. Create a new folder outside of Scafforge called MinimaxTesting and initialize as a repo
2. Create 10 Minimax agents called TestAgentA, TestAgentB, TestAgentC etc
Temperatures from 0.1 - 1.0 so TestAgentA is 0.1, TestAgentB is 0.2 etc

Create the following:

1. A generic coding task of some kind that would be suitable to test/benchmark an LLMs skill

2. A Generic problem that requires an implementation plan

Folder structure:

 MinimaxTesting ->
 -.opencode
   - agents
 - Tasks 
 - TaskResults
   - Agent A
     - Coding Task Result
     - Implementation Plan Task Result
   - Agent B
     - Coding Task Result
     - Implementation Plan Task Result
   - Agent C
     - Coding Task Result
     - Implementation Plan Task Result

etc etc

