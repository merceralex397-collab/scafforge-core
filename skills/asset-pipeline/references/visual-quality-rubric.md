# Visual Quality Rubric

This rubric defines the package bar for visually reviewable output. It judges clarity, hierarchy, layout, and finish. It does **not** mandate one art style.

## Blocker rule

A finding is a **blocker** when it makes the product look broken, unreadable, misleading, or obviously unfinished in normal use. A finding is **polish** when the surface is coherent and usable but could feel sharper, livelier, or more consistent.

Style choice is not a blocker by itself. Flat, low-poly, chunky pixel art, minimalist UI, or stylized lighting are acceptable when the result is intentional, readable, and internally consistent.

## 2D UI and menus

### Blockers

- important UI is clipped, off-screen, pinned to the wrong corner, or collapses at common aspect ratios
- title screens, menus, HUD, or modal overlays do not fit the viewport or obscure the primary interaction surface
- text contrast, size, spacing, or hierarchy makes labels hard to read at normal viewing distance
- visual weight is evenly spread across too many boxes, making the main action unclear
- interaction affordances are ambiguous: buttons do not look clickable, focus state is invisible, or active/inactive states are hard to distinguish
- placeholder grey boxes, mixed placeholder art, or obviously temporary styling remain in user-facing flows

### Polish

- spacing rhythm is slightly uneven
- one surface feels denser or flatter than the rest of the UI
- motion feedback exists but feels abrupt or generic

## 2D game art and VFX

### Blockers

- silhouettes are muddy enough that the player cannot read the asset at gameplay scale
- sprite scale, line weight, palette, or finish varies so much that adjacent assets look accidentally mixed
- effects obscure gameplay, hide collisions, or overpower the playfield
- key feedback states are visually absent: hits, collection, fail-state, or progression changes do not read

### Polish

- impact, anticipation, or follow-through could be stronger
- effects communicate correctly but feel under-tuned

## 3D props and hero assets

### Blockers

- silhouette reads as accidental mush from the intended gameplay or presentation distance
- materials collapse into one unreadable value range, making major forms or interaction cues unclear
- UV/stretching, missing normals, or obvious export damage makes the asset look broken
- the finish level is inconsistent with neighboring assets in the same lane

### Polish

- material breakup could be clearer
- edge wear, value separation, or accent color could better support the intended read

## 3D scenes and environments

### Blockers

- the player or camera cannot read navigation lanes, interaction points, or major landmarks
- the scene is compositionally noisy enough that objectives, hazards, or traversal routes disappear
- lighting or fog destroys readability instead of supporting it
- major layout surfaces feel empty, random, or unfinished relative to the declared style

### Polish

- scene depth can be improved with stronger focal separation
- dressing is coherent but sparse

## Presentation and motion

### Blockers

- motion required by the product type is missing, misleading, or broken
- UI enters or exits in a way that harms readability or makes state changes feel wrong
- timing is so abrupt, floaty, or inconsistent that the interface feels broken rather than stylized
- camera shake, particles, or transition effects damage clarity instead of reinforcing feedback

### Polish

- timings are functional but stiff
- transitions communicate the state change but lack finish

## Review language

Use named failure categories rather than taste words:

- `screen-fit failure`
- `menu hierarchy failure`
- `readability failure`
- `affordance failure`
- `style-consistency failure`
- `silhouette failure`
- `material readability failure`
- `scene readability failure`
- `motion-feedback failure`

When documenting a failure, include:

1. affected surface
2. blocker or polish classification
3. concrete reason the output fails the rubric
4. evidence path

## Visual proof minimums

Visually reviewable repos should capture proof against this rubric. The QA artifact should record:

- `visual_proof_status`
- `visual_proof_evidence`
- `visual_proof_surfaces`
- `visual_rubric_blockers`
- `visual_style_note`

`visual_style_note` is where the reviewer states why the style is intentional, or why style variance is acceptable, so the contract stays separate from personal preference.
