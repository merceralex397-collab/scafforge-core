# Smoke Tool Decomposition Assessment

## Status: ASSESSED — Implementation Deferred

The smoke_test.ts tool (810 lines) is genuinely monolithic with 8+ responsibilities. Key findings:

### Critical Issue: Fail-Fast Masking (Lines 757-764)
The `break` on first failure prevents discovery of multiple failure modes. If command #1 fails, commands #2-N never run.

### Proposed 5-Layer Architecture
1. **Command Detection Engine** (~160 lines) — already mostly isolated
2. **Command Executor** (~80 lines) — needs fail-fast removal
3. **Failure Diagnosis** (~35 lines) — needs extraction from inline classification
4. **Artifact Generation** (~80 lines) — separate rendering from I/O
5. **Orchestration** (~30 lines) — simplified control flow

### Resume Support: Missing
No checkpoints, no partial result persistence, no idempotency markers.

### Decision
Decomposition is warranted but NOT blocking Phase 5/6/7 work. Will implement after core validation targets are complete. The fail-fast behavior is the most urgent fix — it actively masks failure modes that would help diagnosis.

### Priority Fixes (if time permits)
1. Remove `break` in execution loop (run ALL commands)
2. Extract FailureClassifier as separate module
3. Add checkpoint persistence for resume support
