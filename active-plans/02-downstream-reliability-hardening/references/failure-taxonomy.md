# Failure Taxonomy

## Confirmed Failure Families

### 1. Build And Load Breakers

- parse errors
- type mismatches
- missing globals or autoloads
- invalid indentation or script syntax

Primary sources:

- `../../_source-material/downstream-failures/womanvshorseissues/womanvshorseVA.md`
- `../../_source-material/downstream-failures/womanvshorseissues/womanvshorseVC.md`
- `../../_source-material/downstream-failures/womanvshorseissues/womanvshorseVD.md`

### 2. Asset Import Failures

- bad `ext-resource` paths
- malformed or empty `.glb`
- broken `.tscn` references
- missing imported dependencies

Primary sources:

- `../../_source-material/downstream-failures/womanvshorseissues/womanvshorseVB.md`
- `../../_source-material/downstream-failures/womanvshorseissues/womanvshorseVC.md`

### 3. Engine Configuration Drift

- renderer mismatches
- malformed input maps
- missing stretch/layout settings

Primary sources:

- `../../_source-material/downstream-failures/womanvshorseissues/womanvshorseVC.md`
- `../../_source-material/asset-pipeline/assetsplanning/spinner.md`

### 4. Visual Quality Regressions

- off-screen or squashed UI
- atrocious placeholder-looking assets
- menus without usable layout or visual hierarchy

Primary sources:

- `../../_source-material/downstream-failures/womanvshorseissues/README.MD`
- `../../_source-material/asset-pipeline/assetsplanning/spinner.md`

### 5. Completion Truth Gaps

- downstream agents claim completion without proof that the repo loads, runs, or looks acceptable

Primary sources:

- `../../_source-material/downstream-failures/womanvshorseissues/README.MD`
- `../../_source-material/asset-pipeline/assetsplanning/pipeline/asset-pipeline-agent-research-2026-04-14.md`

## Planning Consequence

No autonomy or scale-up work should bypass these proof layers. If Scafforge cannot reliably detect these failures, it is not ready to trust a larger autonomous loop.
