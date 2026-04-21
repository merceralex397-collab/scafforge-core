# Layout Truth Regression

- **Defect family:** broken viewport/stretch configuration that makes the first screen untrustworthy
- **Expected audit classification:** mixed defect with repo-local `EXEC-GODOT-013` plus package follow-up surfaced through `scafforge-repair`
- **Expected repair behavior:** keep restart/handoff blocked, carry the diagnosis into Scafforge first, then route the downstream layout fix through repo-local follow-up
- **Final expected next move:** land the package prevention fixes, restore the canonical 2D stretch configuration, and rerun audit or repair verification
