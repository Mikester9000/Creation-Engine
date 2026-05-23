# Creation-Engine Style Support Task
## Goal
Transform `Creation-Engine` into a reliable content-authoring and asset-bundling pipeline for `GameRewritten` so it can consistently produce the handmade visual language of PS2-era Final Fantasy-inspired 3D worlds.

The purpose of `Creation-Engine` is **not** to chase photoreal output.
The purpose is **not** to become a generic modern asset generator.
The purpose is to become a **deterministic, style-locked, production-support toolchain** that creates content for a full 3D explorable game while preserving:

- the emotional composition associated with early Final Fantasy pre-rendered worlds
- the handmade stylization of PS2-era JRPG environments
- the readability demands of a modern real-time 3D action RPG
- the runtime constraints and visual discipline required by `GameRewritten`

This task defines the toolchain-side transformation required inside `Creation-Engine`.

---

## Core Toolchain Pillars

### 1. Style-locked output, not generic output
Every generated or bundled asset must reinforce the target style.
The tool must reject drift toward photoreal, noisy, overly modern, or visually incoherent output.

### 2. Support authored worlds, not just isolated assets
The engine must help produce content that can be assembled into memorable regions, towns, ruins, shrines, roads, interiors, and landmarks.
The output must support worldbuilding, not just object generation.

### 3. Deterministic production pipeline
The same prompts, tags, seeds, and recipes should reliably produce the same category and style direction.
The workflow should be auditable and reproducible.

### 4. Runtime-aware output for GameRewritten
Everything produced must be aligned with the technical and artistic expectations of `GameRewritten`.
The pipeline must generate content that is easy to import, categorize, validate, and use in a controlled runtime environment.

---

## Non-Goals

Do **not** turn `Creation-Engine` into:
- a photoreal asset pipeline
- a modern AAA material authoring stack
- an unconstrained procedural content generator
- a style-agnostic prompt toy
- a high-variance experimental content system without deterministic guardrails

Do **not** optimize for:
- visual realism over silhouette
- texture complexity over readability
- unconstrained generation over auditability
- quantity without curation
- content novelty that breaks the GameRewritten art contract

---

## Transformation Outcome Required

`Creation-Engine` must become capable of the following:

1. Produce assets, packs, and bundles that reliably fit the handmade PS2-era Final Fantasy-inspired look.
2. Generate content grouped by clear world-authoring categories usable by `GameRewritten`.
3. Support region identity, landmark creation, and narrative/world-state-aware content planning.
4. Export deterministic manifests and metadata so the runtime can validate and ingest content safely.
5. Scale from vertical-slice asset support to broader world production without style drift.

---

# Required Toolchain Transformation Areas

## A. Style Profile Enforcement
Create or complete a strict style-governance system across prompts, recipes, manifests, and validation.

### Must support
- one canonical style profile for `GameRewritten`
- prompt rules that reinforce PS2-era Final Fantasy-inspired stylization
- rejection or warning for photoreal or modern-AAA drift
- style-profile stamping in per-asset and bundle manifests
- compatibility reporting for final outputs
- deterministic style conformance checks where possible

### Done when
- Output cannot silently drift away from the intended look.
- Assets and bundles can be audited for style compliance.
- The runtime can trust the declared style profile.

---

## B. Asset Family Coverage
Expand and organize output so the pipeline supports real worldbuilding, not just placeholders.

### Must support
- terrain materials
- biome materials
- tilesets
- props
- architecture modules
- foliage
- decals
- item meshes
- UI icons
- UI panels
- portraits
- static character placeholders
- static enemy placeholders
- landmark-supporting content families

### Additional requirement
Each family must include enough variation to support actual region building, not only proof-of-concept examples.

### Done when
- A small but believable world slice can be assembled from pipeline output.
- Category coverage is sufficient for towns, roads, shrines, ruins, camps, dungeons, and regional landmarks.

---

## C. Region, Faction, and Narrative Taxonomy
The content pipeline must become world-aware, not only asset-aware.

### Must support
- region tags
- biome tags
- faction tags
- sacred/corrupted/ruined/restored state tags
- narrative tone tags
- era/history tags where useful
- landmark importance tags
- compatibility tags for bundle selection and runtime use

### Design intent
Generated or bundled assets should help build recognizable world identity.
A “forest shrine” region should not feel interchangeable with an “imperial outpost” or a “coastal town”.

### Done when
- Content can be grouped and selected by region identity and story function.
- Bundle composition can reinforce distinct places and moods.

---

## D. Open-World Pack and Bundle Structure
The toolchain must support larger world production in an organized way.

### Must support
- pack segmentation by category and region
- deterministic bundle recipes
- destination mapping for runtime import
- compatibility summaries
- pack manifests and top-level bundle manifests
- separation between required packs and optional packs
- scalable organization for future growth

### Done when
- A vertical slice bundle and a larger multi-region bundle can both be produced cleanly.
- `GameRewritten` can ingest content without manual re-sorting.

---

## E. Runtime Contract for GameRewritten
The content pipeline must output data that `GameRewritten` can trust and consume with minimal ambiguity.

### Must support
- consistent family/category naming
- stable file placement rules
- prefab/material mapping metadata
- manifest fields required for import validation
- source prompt and seed traceability where relevant
- compatibility summaries for final bundles
- graceful fallback metadata for incomplete families

### Done when
- The handoff between `Creation-Engine` and `GameRewritten` is explicit and documented.
- Runtime-side import logic does not depend on guesswork.

---

## F. Landmark and Composition Support
The pipeline must assist in making authored worlds feel memorable.

### Must support
- landmark-oriented architecture and prop sets
- silhouette-readable hero assets
- shrine / ruin / gate / tower / bridge / crystal / monument style support
- vista-supporting asset groupings
- landmark tags in manifests
- content intended for visual focal points, not only filler placement

### Done when
- Output can support memorable viewpoints and navigational anchors.
- World spaces can be composed around focal structures instead of uniform clutter.

---

## G. Texture, Mesh, and UI Output Discipline
All content families must serve the same visual language.

### Must support
- low-frequency texture direction
- readable silhouette-first mesh direction
- deterministic family-aware mesh generation
- stylized icon and portrait generation
- anti-noise visual constraints
- low-resolution-friendly UI framing and icon clarity
- family-specific generation rules instead of generic fallback output

### Done when
- Different content families still feel like they belong to the same game.
- Generated assets are readable under `GameRewritten`’s stylized runtime presentation.

---

## H. Validation, QA, and Release Readiness
The toolchain must support production, not only experimentation.

### Must support
- deterministic regression checks
- bundle validation rules
- visual/style checklist support
- release handoff checklist
- coverage checks for required packs
- compatibility summaries for final export
- reproducibility expectations for key outputs

### Done when
- A bundle can be evaluated as pass/fail before handoff.
- Regressions and style drift are easier to detect.

---

# Required Deliverable Milestones

## Milestone 1 — Style Contract Lock
Establish the strict style profile and validation baseline for all GameRewritten-targeted output.

### Must include
- canonical `GameRewritten` style profile
- prompt and recipe rules for style adherence
- manifest-level style stamping
- initial anti-photoreal drift checks
- one validated reference bundle recipe

### Result
The tool no longer behaves like a generic output system; it behaves like a style-locked JRPG content pipeline.

---

## Milestone 2 — Vertical Slice Content Support
Produce enough structured output to support one convincing GameRewritten playable area.

### Must include
- materials
- terrain/biome support
- architecture set
- props
- foliage
- decals
- one landmark-capable content set
- one UI support set
- one static character placeholder set
- one static enemy placeholder set
- deterministic bundle manifest for the slice

### Result
A single region can be populated in a visually coherent way using pipeline output.

---

## Milestone 3 — Region Identity Framework
Expand the content system so bundles can represent different places and moods.

### Must include
- region-based prompt expansion
- faction/state/tag support
- region-aware pack grouping
- landmark tags
- narrative/world-state-aware asset categorization
- improved family breadth for towns, ruins, shrines, roads, camps, and dungeons

### Result
The pipeline can support multiple distinct world areas without flattening them into one generic style.

---

## Milestone 4 — Production Handoff Contract
Finalize the import/export relationship with `GameRewritten`.

### Must include
- stable final bundle schema
- compatibility and destination mapping
- validation checklist
- release handoff documentation
- explicit expectations for runtime importer behavior
- graceful handling of partial or placeholder content

### Result
`Creation-Engine` becomes a reliable production support repo rather than an experimental generator.

---

# Implementation Priorities

## Priority 1
Lock style profile enforcement first.

Focus first on:
- style profile rules
- prompt discipline
- manifest stamping
- anti-drift validation

## Priority 2
Expand asset families in ways that support worldbuilding.

Focus second on:
- architecture
- props
- foliage
- terrain
- landmark assets
- UI readability assets

## Priority 3
Make the pipeline world-aware.

Focus third on:
- region tags
- faction/state metadata
- bundle segmentation
- landmark metadata
- narrative grouping

## Priority 4
Lock runtime contract and release process.

Focus fourth on:
- bundle schema
- destination maps
- compatibility summaries
- release validation
- handoff documentation

---

# Acceptance Standard

This task is complete only when `Creation-Engine` can produce content for `GameRewritten` that:

- consistently matches the handmade PS2-era Final Fantasy-inspired style target
- avoids photoreal or modern-AAA drift
- supports authored explorable 3D worldbuilding
- includes enough family/category breadth for a convincing vertical slice
- exports deterministic manifests and bundle metadata
- provides a stable and trustworthy handoff contract for runtime import

If the result is only “a generator that can make retro-looking assets sometimes,” the task is **not** complete.
If the result is “a deterministic, style-locked, world-supporting asset pipeline for GameRewritten,” the task is on target.

---

# Final Instruction
All future prompt systems, asset-family logic, manifests, bundle logic, export logic, validation, and release work in `Creation-Engine` should be judged against this question:

**Does this change make Creation-Engine better at producing reliable, handmade-feeling, PS2-era Final Fantasy-inspired content for a fully explorable 3D GameRewritten world?**

If not, the change should be revised, reduced, or rejected.