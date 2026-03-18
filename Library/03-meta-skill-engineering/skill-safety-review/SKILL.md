---
name: skill-safety-review
description: Review a skill for safety issues — destructive operations without confirmation, excessive permissions, prompt injection vulnerabilities, scope creep, and description-behavior mismatches. Use this before publishing skills to shared registries, after importing from untrusted sources, or when a skill performs consequential operations like file deletion, API calls, or deployments. Do not use for quality or routing evaluation (use skill-evaluation), for skills that are purely informational with no side effects, or for already-reviewed unchanged skills.
license: Apache-2.0
compatibility:
  clients: [openai-codex, gemini-cli, opencode, github-copilot]
metadata:
  owner: codex
  domain: skill-safety-review
  maturity: draft
  risk: low
  tags: [skill, safety, review]
---

# Purpose
Reviews skills for safety issues: destructive operations without confirmation, excessive permissions, scope creep, prompt injection vulnerabilities, and misleading descriptions. Required before publishing to shared registries.

# When to use this skill
Use when:
- User says "review for safety", "is this safe?", "security review"
- Before publishing to shared registry/marketplace
- Importing from untrusted external source
- Skill flagged during audit
- Skill performs consequential operations (deletion, API calls, deployments)

Do NOT use when:
- Reviewing quality/routing (use `skill-evaluation`)
- Skill purely informational, no side effects
- Already reviewed and unchanged

# Operating procedure
1. **Check destructive operations**:
   - File deletion (rm, unlink)
   - Database mods (DROP, DELETE)
   - Git force (force push, reset --hard)
   - External API calls (POST, PUT, DELETE)
   - System mods (chmod, service restart)
   - **Flag**: Any without confirmation step
2. **Check excessive permissions**:
   - More access than needed?
   - Accessing files outside scope?
   - Credentials not justified?
   - **Flag**: Any unjustified permission
3. **Check scope creep**:
   - Steps not implied by description?
   - Actions beyond user request?
   - Affects unexpected systems?
   - **Flag**: Unexpected actions
4. **Check prompt injection**:
   - Processes untrusted input?
   - Malicious input could alter behavior?
   - Unescaped interpolations?
   - **Flag**: External content → instructions path
5. **Check misleading descriptions**:
   - Description matches behavior?
   - Hidden behaviors?
   - Severity clear?
   - **Flag**: Mismatch
6. **Check scripts/**:
   - Unsafe operations?
   - Hardcoded credentials?
   - Unexpected network calls?
   - **Flag**: Undocumented operations
7. **Check error handling**:
   - What if fails mid-operation?
   - Cleanup for partial states?
   - **Flag**: Missing rollback for destructive ops
8. **Issue verdict**:
   - **Safe**: No issues
   - **Safe with warnings**: Minor issues documented
   - **Requires changes**: Must fix before use
   - **Unsafe**: Fundamental problems

# Output defaults
```
## Safety Review: [skill-name]

**Verdict**: [Safe | Safe with warnings | Requires changes | Unsafe]

### Destructive Operations
| Op | Location | Confirmation? | Status |
|----|----------|---------------|--------|
| rm | step 5 | No | ❌ Add confirmation |

### Permissions
| Permission | Justified? |
|------------|------------|
| File write | Yes |
| Network | No |

### Injection Risks
| Vector | Risk | Mitigation |
|--------|------|------------|
| File content | Medium | Sanitize |

### Required Changes
1. Add confirmation before rm
2. Justify network access
```

# References
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills — Agent skill trust model
- https://developers.openai.com/codex/sandboxing — Codex sandboxing and permission model
- https://docs.anthropic.com/en/docs/claude-code/overview — Claude Code permission system
- OWASP prompt injection guidance for LLM applications

# Failure handling
- **Can't understand skill**: Unsafe—if reviewer can't, user can't
- **Intentionally destructive** (cleanup skill): Ensure explicit, require confirmation, safe if guarded
- **External deps unauditable**: Note trust assumption
