# Task_List: One-File-at-a-Time Path to Program Completion

All tasks below are based on `program_assessment.md` and follow this fixed format:
- Task Name
- Coding logic + narrative design required
- Program/design function logic
- Final Fantasy aesthetic adherence check
- File to edit/create
- Line target

---

## Task 01
**Task Name:** Expand canonical bundle recipe for production-scale asset prompts

**Coding logic + narrative design required:**
Increase prompt sets in every family (`materials`, `terrain`, `tilesets`, `props`, `architecture`, `foliage`, `items`, `decals`, `ui`, `characters`, `enemies`) to include region/lore-driven variants (kingdom, ruins age, sacred vs corrupted, imperial vs rebel tone).

**Program/design function logic:**
`generate_*_pack` and `generate_full_bundle` consume this recipe directly; richer prompt lists increase deterministic content breadth without changing public CLI contracts.

**Final Fantasy aesthetic adherence check:**
Each prompt must include PS2-era FF direction cues and avoid photoreal modern AAA wording.

**File to edit/create:**
Edit `creation_engine/game_rewritten_bundle.py`

**Line target:**
Edit existing recipe block lines **3-52**.

---

## Task 02
**Task Name:** Add narrative metadata taxonomy constants

**Coding logic + narrative design required:**
Create canonical narrative tags (`region`, `faction`, `era`, `story_phase`, `culture_theme`) and allowed values for stable tagging.

**Program/design function logic:**
Central constants allow exporters and validators to enforce consistent narrative metadata across all manifests.

**Final Fantasy aesthetic adherence check:**
Taxonomy values should map to JRPG worldbuilding archetypes (kingdom, shrine, magitek ruin, ancient civilization).

**File to edit/create:**
Create `creation_engine/narrative_tags.py`

**Line target:**
Create file lines **1-220**.

---

## Task 03
**Task Name:** Add prompt-to-narrative tag extraction

**Coding logic + narrative design required:**
Extend prompt classification to return deterministic narrative tags from tokens and aliases.

**Program/design function logic:**
Classification output becomes the single source for manifest narrative tagging in textures/maps/meshes/UI.

**Final Fantasy aesthetic adherence check:**
Tag extraction must prioritize FF-like themes (crystal, empire, ruins, sanctum, wilderness routes, summon relics).

**File to edit/create:**
Edit `creation_engine/prompting.py`

**Line target:**
Edit lines **16-64**.

---

## Task 04
**Task Name:** Add narrative tags to texture manifests

**Coding logic + narrative design required:**
Inject narrative tags and world-region hints into texture/material export metadata.

**Program/design function logic:**
Texture manifests become directly sortable by region/faction/story-phase for GameRewritten import pipelines.

**Final Fantasy aesthetic adherence check:**
Ensure tags support elemental and kingdom style consistency (holy, shadow, fire, ice, forest, desert, coastal).

**File to edit/create:**
Edit `creation_engine/export/texture_exporter.py`

**Line target:**
Edit lines **52-76**.

---

## Task 05
**Task Name:** Add narrative tags to map exports

**Coding logic + narrative design required:**
Append narrative tags + region IDs + exploration intent fields to map JSON output.

**Program/design function logic:**
Map importer can route maps into open-world region systems and narrative progression states.

**Final Fantasy aesthetic adherence check:**
Map themes should stay consistent with JRPG traversal fantasy (overworld routes, ruins, temples, towns, dungeons).

**File to edit/create:**
Edit `creation_engine/export/map_exporter.py`

**Line target:**
Edit lines **34-58**.

---

## Task 06
**Task Name:** Add narrative tags to mesh manifests

**Coding logic + narrative design required:**
Include narrative metadata and placement intent (`world_prop`, `town_prop`, `dungeon_prop`, etc.) in mesh manifest export.

**Program/design function logic:**
Downstream engine can place generated assets contextually by map/region/story phase.

**Final Fantasy aesthetic adherence check:**
Mesh semantic categories should reflect FF set dressing (crystal altars, shrine pieces, ruins masonry, camp assets).

**File to edit/create:**
Edit `creation_engine/export/mesh_exporter.py`

**Line target:**
Edit lines **71-94**.

---

## Task 07
**Task Name:** Expand tileset specs to full open-world template set

**Coding logic + narrative design required:**
Add more specialized tileset profiles (capital city, port city, highlands, volcanic zone, sacred ruins, imperial fortress, wasteland).

**Program/design function logic:**
`map_gen` theme resolution can choose richer deterministic layouts and tileset metadata per region.

**Final Fantasy aesthetic adherence check:**
Tile definitions and styles should preserve readable stylized FF PS2-era silhouettes and color pacing.

**File to edit/create:**
Edit `creation_engine/map/tileset_specs.py`

**Line target:**
Edit lines **14-111**.

---

## Task 08
**Task Name:** Add region-aware open-world map generation

**Coding logic + narrative design required:**
Add deterministic region seed mixing and multi-theme zone blending to produce contiguous open-world-ready map chunks.

**Program/design function logic:**
`generate_tilemap` should support region/chunk metadata to stitch world traversal spaces.

**Final Fantasy aesthetic adherence check:**
Generated layouts must preserve explorable JRPG readability, landmark density, and route clarity.

**File to edit/create:**
Edit `creation_engine/map/map_gen.py`

**Line target:**
Edit lines **78-230**.

---

## Task 09
**Task Name:** Expand material preset library for production asset breadth

**Coding logic + narrative design required:**
Add many more material presets and modifiers for region + civilization + corruption states.

**Program/design function logic:**
Texture generation fallback uses these tables directly, increasing output diversity while staying deterministic.

**Final Fantasy aesthetic adherence check:**
Calibrate roughness/metallic/base-color to stylized PS2-era FF look (avoid realistic PBR extremes).

**File to edit/create:**
Edit `creation_engine/texture/material_presets.py`

**Line target:**
Edit lines **1-260**.

---

## Task 10
**Task Name:** Expand palette libraries for biome + faction identity

**Coding logic + narrative design required:**
Add deterministic palettes for faction and narrative mood variants (imperial, rebel, sacred, corrupted, royal, village, underworld).

**Program/design function logic:**
All image generators reuse these palettes for consistent world style language.

**Final Fantasy aesthetic adherence check:**
Palette rules should enforce FF-style color discipline: controlled saturation, readable accents, non-photoreal tone.

**File to edit/create:**
Edit `creation_engine/texture/palette.py`

**Line target:**
Edit lines **1-240**.

---

## Task 11
**Task Name:** Expand mesh family variants to game-scale set coverage

**Coding logic + narrative design required:**
Add more variants for props/architecture/foliage/items/NPC/enemy placeholders, including story landmarks and world-interaction markers.

**Program/design function logic:**
`mesh_builder` and backend prompt resolution produce broader static model output sets for open-world population.

**Final Fantasy aesthetic adherence check:**
Variant shapes and proportions must remain stylized heroic fantasy with PS2-era readable silhouettes.

**File to edit/create:**
Edit `creation_engine/mesh/mesh_family_specs.py`

**Line target:**
Edit lines **12-312**.

---

## Task 12
**Task Name:** Add mesh LOD metadata and complexity policy

**Coding logic + narrative design required:**
Add deterministic LOD profile fields and complexity presets per mesh family for open-world performance tiers.

**Program/design function logic:**
Exported mesh metadata can be consumed by runtime importers to assign render-distance strategy.

**Final Fantasy aesthetic adherence check:**
LOD degradation should preserve iconic silhouette and recognizable fantasy function.

**File to edit/create:**
Edit `creation_engine/mesh/mesh_builder.py`

**Line target:**
Edit lines **18-74**.

---

## Task 13
**Task Name:** Enforce stricter aesthetic validation rules

**Coding logic + narrative design required:**
Extend quality checks to validate style profile, banned prompt terms, required FF-style descriptors, and manifest narrative fields.

**Program/design function logic:**
`quality-check` becomes hard gate for style and metadata integrity before bundle acceptance.

**Final Fantasy aesthetic adherence check:**
Reject prompts/manifests implying modern photoreal or non-FF stylistic drift.

**File to edit/create:**
Edit `creation_engine/quality_check.py`

**Line target:**
Edit lines **18-125**.

---

## Task 14
**Task Name:** Add full-bundle completeness matrix validation

**Coding logic + narrative design required:**
Validate that full bundle contains every required family, minimum asset counts per family, and complete destination map coverage.

**Program/design function logic:**
Prevents shipping under-filled bundles that technically pass file checks but fail content-completeness goals.

**Final Fantasy aesthetic adherence check:**
Require coverage across FF-consistent content categories (town/dungeon/overworld/ruins/sanctum visual kits).

**File to edit/create:**
Edit `creation_engine/engine.py`

**Line target:**
Edit lines **353-420**.

---

## Task 15
**Task Name:** Add CLI command for production bundle audit report

**Coding logic + narrative design required:**
Add a command that summarizes family counts, narrative tag coverage, and style-check compliance for a generated bundle.

**Program/design function logic:**
Provides one deterministic command for release readiness review before importing into GameRewritten.

**Final Fantasy aesthetic adherence check:**
Audit output must include explicit FF aesthetic compliance status.

**File to edit/create:**
Edit `creation_engine/cli.py`

**Line target:**
Edit lines **61-170**.

---

## Task 16
**Task Name:** Expand automated tests for completion criteria

**Coding logic + narrative design required:**
Add tests for narrative tags, aesthetic gate failures, completeness matrix, and deterministic region/chunk behavior.

**Program/design function logic:**
Locks production requirements so regressions fail fast.

**Final Fantasy aesthetic adherence check:**
Tests must include pass/fail cases for FF style profile and banned prompt drift.

**File to edit/create:**
Edit `tests/test_cli.py`

**Line target:**
Edit lines **35-142**.

---

## Task 17
**Task Name:** Expand backend/API integration tests for full static pipeline

**Coding logic + narrative design required:**
Add tests that generate multi-family bundles and assert presence/consistency of narrative and destination metadata.

**Program/design function logic:**
Confirms end-to-end correctness from prompt to manifest relationships.

**Final Fantasy aesthetic adherence check:**
Assert style profile and FF-oriented metadata are always included in generated assets.

**File to edit/create:**
Edit `tests/test_backend_and_api.py`

**Line target:**
Edit lines **18-121**.

---

## Task 18
**Task Name:** Update master documentation for production completion workflow

**Coding logic + narrative design required:**
Document completion workflow: generate packs, run quality gates, run audit report, and export/import sequence for GameRewritten.

**Program/design function logic:**
Provides deterministic human/operator runbook to produce final non-audio/non-animation asset delivery.

**Final Fantasy aesthetic adherence check:**
Document explicit style guardrails and acceptance rubric tied to FF PS2-era visual targets.

**File to edit/create:**
Edit `README.md`

**Line target:**
Edit lines **25-241**.

---

## Task 19
**Task Name:** Update formal GameRewritten plan contract doc

**Coding logic + narrative design required:**
Align existing long-form plan with final implementation architecture, narrative metadata schema, audit process, and completion gates.

**Program/design function logic:**
Makes planning artifact authoritative and synchronized with code path to production readiness.

**Final Fantasy aesthetic adherence check:**
Keep the FF7-FF12 visual contract and modern gameplay readability requirement as non-negotiable acceptance rules.

**File to edit/create:**
Edit `docs/ff-game-rewrite-plan.md`

**Line target:**
Edit lines **1-520** (targeted updates only; preserve structure).

---

## Task 20
**Task Name:** Add release checklist artifact for final static asset handoff

**Coding logic + narrative design required:**
Create a strict release checklist including command sequence, validation expectations, and pass/fail criteria for handoff to GameRewritten.

**Program/design function logic:**
Creates a deterministic final gate so completed program output is reproducible and verifiable.

**Final Fantasy aesthetic adherence check:**
Checklist must include visual review requirements for FF PS2-era styling and anti-photoreal drift.

**File to edit/create:**
Create `docs/release_static_assets_checklist.md`

**Line target:**
Create file lines **1-260**.

---

## Completion Note
If Tasks 01-20 are completed in order, the Creation-Engine pipeline will move from “strong foundational static generator” to a production-ready, audited, narrative-aware static asset factory for GameRewritten (excluding audio and animation by design).
