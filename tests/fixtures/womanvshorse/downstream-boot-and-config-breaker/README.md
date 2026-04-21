# Downstream Boot And Config Breaker

- **Defect family:** broken resource linkage plus renderer/input-map drift in a Godot Android 2D repo
- **Expected audit classification:** mixed defect with repo-local `EXEC-GODOT-002`, `EXEC-GODOT-014`, and `EXEC-GODOT-015` plus package follow-up surfaced through `scafforge-repair`
- **Expected repair behavior:** carry the diagnosis into Scafforge first, then keep repo-local remediation follow-up for the downstream source/config surfaces
- **Final expected next move:** land the package prevention fixes, repair the downstream Godot source/config surfaces, then rerun audit or repair verification
