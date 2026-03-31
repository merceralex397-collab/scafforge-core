# Host Tool Or Permission Blockage

This family captures the GPTTalker sessions where tool or permission blockage was being misread as a repo defect, which pushed the agent toward false next actions and workaround behavior.

Archive origin:

- `scafforgechurnissue/GPTTalkerAgentLogs/session4.md`
- `scafforgechurnissue/CodexLogs/28/rollout-2026-03-28T12-58-06-019d3485-f083-7c91-938c-37a0230badbb.jsonl`

What mattered:

- the repo needed to surface host/tool blockage explicitly
- restart guidance could not claim a normal lifecycle continuation when the real blocker lived outside the repo
- weaker agents should see one blocker path, not a mix of repo-state and host-state advice

Current protection:

- generated execution tools classify missing executables and permission restrictions explicitly
- smoke coverage proves those classifications through actual generated tool execution
