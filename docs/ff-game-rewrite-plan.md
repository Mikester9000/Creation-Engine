# GameRewritten Asset Master Plan (No Animation / No Audio)

This file continues and consolidates the earlier planning direction into one strict, copy-paste-ready master plan for extending **Creation-Engine** so it can produce the full non-animation, non-audio asset set for **Mikester9000/GameRewritten**.

This plan is intentionally optimized for a weak local LLM:

- one small task at a time
- one file changed per task
- explicit `READ_FILE` and `READ_LINES`
- deterministic order
- minimal choices
- no hidden reasoning steps

---

## Mission

Extend `/home/runner/work/Creation-Engine/Creation-Engine` so it can generate or export all static GameRewritten asset families except:

- animation
- rigging
- skeletal data
- audio
- music
- voice
- sound effects

Included scope:

- material texture sets
- terrain textures
- tile sets / tileset metadata
- world maps / level maps
- static prop meshes
- static environment meshes
- building kit meshes
- foliage meshes
- item / pickup meshes
- decal textures
- UI icons
- UI panels / frames
- static portraits / bust cards
- static enemy and NPC placeholder meshes
- manifests / catalogs / bundle metadata
- validation for all exported asset families
- GameRewritten-compatible relative paths and schema fields for all exported non-audio/non-animation assets

---

## Visual Art Direction Contract (Required)

All planned outputs in this file must align to the following target:

- Visual reference range: **FF7-FF12 era Final Fantasy style** (`FF7`, `FF8`, `FF9`, `FF10`, `FF11`, `FF12`).
- Quality bar: highest quality that still fits **PlayStation 2-era runtime constraints**.
- Gameplay compatibility: assets must remain readable for modern feature density (open-world JRPG expectations similar to `FFVII Remake` / `FFXV` gameplay complexity), but **visual rendering style stays PS1/PS2-era**.
- Future prompts, presets, bundle recipes, and acceptance checks must reject photoreal / modern-AAA visual drift.

---

## Current Repo Baseline (As-Built — All Tasks Complete)

All 20 tasks are complete. The following production-ready components exist:

**Core generators:**
- `creation_engine/cli.py` — full command router: `texture`, `map`, `mesh`, `*-pack`, `full-bundle`, `quality-check`, `bundle-audit`, `release-check`, `gui`, `list-backends`
- `creation_engine/engine.py` — `CreationEngine` class with all pack builders and `generate_full_bundle`
- `creation_engine/backend.py` — `ProceduralBackend` with family-aware texture/map/mesh generation and `BackendRegistry`

**Texture pipeline:**
- `creation_engine/texture/texture_gen.py` — material-family-aware PBR texture generator (Python fallback + C++ bridge)
- `creation_engine/texture/material_presets.py` — 80+ presets: region, civilization, corruption, elemental variants
- `creation_engine/texture/palette.py` — 50+ palettes: faction, biome, narrative mood, era variants
- `creation_engine/export/texture_exporter.py` — exports PNG + JSON manifest with 3D fields, narrative tags, `style_profile`

**Map pipeline:**
- `creation_engine/map/map_gen.py` — region/chunk-aware generator with 14+ themed layouts, neighbor-theme blending, per-tile height maps
- `creation_engine/map/tileset_specs.py` — 17 tileset themes: overworld, town, dungeon, cave, coast, desert, snowfield, temple, ruins, castle, forest, capital\_city, port\_city, highlands, volcanic, sacred\_ruins, imperial\_fortress, wasteland
- `creation_engine/export/map_exporter.py` — exports map JSON with narrative tags, `world_region_id`, `exploration_intent`, 3D fields, height map

**Mesh pipeline:**
- `creation_engine/mesh/mesh_family_specs.py` — full variant catalog for props, architecture, foliage, items, characters\_static, enemies\_static with 10+ examples each and named parts
- `creation_engine/mesh/mesh_builder.py` — primitive assembly, LOD policy per family, complexity budget
- `creation_engine/export/mesh_exporter.py` — exports OBJ + MTL + JSON manifest with narrative tags, placement intent, LOD policy

**Narrative metadata:**
- `creation_engine/narrative_tags.py` — canonical taxonomy: `region`, `faction`, `era`, `story_phase`, `culture_theme`, `world_region_id`, `exploration_intent`, `placement_intent`
- `creation_engine/prompting.py` — deterministic prompt tokenizer and narrative tag classifier

**Bundle and validation:**
- `creation_engine/game_rewritten_bundle.py` — 20 prompts × 13 asset families with region/lore-driven variants
- `creation_engine/quality_check.py` — hard aesthetic gate: banned terms, required FF style descriptors, narrative field validation, bundle completeness
- `creation_engine/asset_catalog.py` — shared family constants, slug helper, build order

**GUI:**
- `creation_engine/gui.py` — desktop editor/preview app: load, edit, save, and preview assets

**Tests:**
- `tests/test_backend_and_api.py` — multi-family bundle, narrative metadata, tileset fallback tests
- `tests/test_cli.py` — narrative tags, aesthetic gate, completeness matrix, GUI, all CLI commands
- `tests/test_gui.py` — GUI smoke tests
- `tests/run_tests.sh` — Python CLI integration + quality gates (requires `creation-engine` on PATH, e.g. `pip install -e .`)

Current repo can do:

- All 13 asset pack families: materials, terrain, tilesets, props, architecture, foliage, items, decals, ui\_icons, ui\_panels, ui\_portraits, characters\_static, enemies\_static
- Full-bundle generation with completeness matrix validation
- Region-aware, chunk-stitchable open-world map generation
- Quality-check, bundle-audit, release-check CLI gates
- Desktop GUI for loading and previewing assets

---

## Target Output Tree

When all tasks are done, the repo should be able to generate output shaped like this:

```text
assets/
  materials/
  terrain/
  tilesets/
  maps/
  props/
  architecture/
  foliage/
  items/
  decals/
  characters/static/
  enemies/static/
  ui/icons/
  ui/panels/
  ui/portraits/
  manifests/
  bundles/
```

---

## Global Execution Rules

Use these rules for every task below.

1. Do tasks in order.
2. Do not combine tasks.
3. Modify only the file named in `WRITE_FILE`.
4. Read only the files listed in `READ_FILE`.
5. Keep all generation deterministic from prompt + seed.
6. Do not add networking.
7. Do not add cloud APIs.
8. Do not add animation or audio features.
9. Prefer pure Python and existing repo dependencies.
10. After each task, run only the smallest relevant test or command.
11. If a task creates a new file, do not also edit another file in that same task.
12. If later tasks need symbols from new files, do that in the later planned file-specific task.
13. Every exported asset must include enough metadata to map into `GameRewritten/Content/*` without manual schema guessing.
14. Keep compatibility targets focused on static assets only (no animation and no audio).
15. New prompts and presets must explicitly target PS2-era JRPG visual output and avoid modern photoreal style drift.
16. Planned bundle examples must include style language that reinforces FF7-FF12-era visual constraints.

Validation commands:

```bash
cd <repo-root>
python -m pytest tests/test_backend_and_api.py tests/test_cli.py tests/test_gui.py
bash tests/run_tests.sh
```

Production gate commands:

```bash
cd <repo-root>
creation-engine full-bundle --seed 101 --output assets
creation-engine quality-check --output assets
creation-engine bundle-audit --output assets
creation-engine release-check --output assets
python -m pytest tests/test_backend_and_api.py tests/test_cli.py tests/test_gui.py
bash tests/run_tests.sh
```

Release gate policy:

- `quality-check` is a hard fail gate for style profile, banned prompt drift, required FF descriptors, narrative metadata fields, and safe file references.
- `bundle-audit` is a hard fail gate for per-family counts, narrative coverage, and FF aesthetic compliance status.
- `release-check` is a combined gate: runs quality-check + bundle-audit + full-bundle completeness matrix validation in one command.
- Full-bundle manifest must include a `completeness_matrix` proving required packs, minimum counts per family, and complete content destination coverage.
- All manifests must include `asset_dimension: "3d"`, `render_pipeline: "3d_pbr"`, `coordinate_space: "Y_up"`, and `style_profile: "ps2_ff7_ff12_highest_quality_ps2"`.
- Texture manifests must include `shader: "Shaders/pbr_3d"`.
- Map manifests must include `render_mode: "3d"`, `height_map`, `narrative_tags`, `world_region_id`, and `exploration_intent`.
- Mesh manifests must include `narrative_tags`, `placement_intent`, `lod_policy`, and `coordinate_space`.

---

## Asset Families To Deliver

### Environment and world
- terrain materials
- biome materials
- tilesets
- overworld maps
- dungeon maps
- town maps
- encounter maps
- roads / rivers / cliffs / walls / floors

### Static 3D content
- props
- containers
- pickups
- foliage
- rocks
- ruins
- building modules
- furniture
- shrine / save point / shop marker / inn marker meshes
- static NPC placeholder meshes
- static enemy placeholder meshes

### 2D static content
- item icons
- skill icons
- element icons
- menu frames
- HUD panels
- portrait cards
- decals / signs / emblems

### Metadata
- per-asset manifest
- per-pack manifest
- bundle manifest
- validation schema fields shared by all exporters
- GameRewritten compatibility report per bundle

---

## GameRewritten Compatibility Contract

All tasks that export files must satisfy this compatibility contract:

- Material metadata must include `name`, `shader`, `textures`, `params.color` (RGBA, canonical), and `params.baseColor` (RGBA, legacy alias) so it can map to both new and old GameRewritten material loaders. Format version must be `1.1` or higher to signal the schema change.
- Texture and material references must be exported as deterministic relative paths that can be remapped into `Content/Textures` and `Content/Materials`.
- Map exports must include deterministic dimensions, tile payload, and tileset/theme metadata needed for GameRewritten world import adapters.
- Mesh exports must include deterministic model metadata and material slot references for placement in `Content/Models` and `Content/Materials`.
- UI exports (icons, panels, portraits) must include metadata that can be mapped to `Content/UI`.
- Bundle metadata must include a full file manifest with family labels and target `Content/*` destination hints.
- Bundle and per-asset manifests must include a deterministic `style_profile` value set exactly to `ps2_ff7_ff12_highest_quality_ps2` so art direction can be audited automatically.

**3D rendering fields (required on all manifests):**
- `asset_dimension: "3d"` — marks the asset as a 3D asset (not 2D sprite).
- `render_pipeline: "3d_pbr"` — signals the PBR render path.
- `coordinate_space: "Y_up"` — Y-axis is up (GameRewritten standard).
- Texture manifests: `shader: "Shaders/pbr_3d"`.
- Map manifests: `render_mode: "3d"` and `height_map` (2D float array, one elevation per tile).

**Narrative metadata fields (required on all manifests):**
- `narrative_tags` object with keys: `region`, `faction`, `era`, `story_phase`, `culture_theme` — values drawn from canonical lists in `creation_engine/narrative_tags.py`.
- `world_region_id` — deterministic region slug (e.g. `"kingdom_central"`, `"frozen_highlands"`).
- `exploration_intent` — slot for open-world routing (e.g. `"main_route"`, `"dungeon_entrance"`, `"optional_area"`).
- `placement_intent` — asset placement category (e.g. `"world_prop"`, `"town_prop"`, `"dungeon_prop"`).

---

## Phase Order

1. Foundation and shared metadata
2. Texture families and material metadata
3. Tilesets and richer map exports
4. Static mesh families and mesh metadata
5. UI and portrait asset families
6. Bundle orchestration for full GameRewritten output
7. Validation, docs, and examples

---

## Ordered One-File Task Cards

Each card below is designed to be pasted into another LLM exactly as-is.

---

### TASK 01 — Create shared asset family catalog

```text
TASK_ID: 01
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/asset_catalog.py
FILE_STATUS: NEW FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/engine.py
READ_LINES_1: 1-98
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/cli.py
READ_LINES_2: 1-89
GOAL: Create one authoritative catalog of GameRewritten asset families, output subdirectories, and allowed bundle names.
REQUIREMENTS:
- Define constants for materials, terrain, tilesets, maps, props, architecture, foliage, items, decals, characters_static, enemies_static, ui_icons, ui_panels, ui_portraits, manifests, bundles.
- Add a deterministic slug helper for asset family names.
- Add a simple ordered list constant for the full GameRewritten asset build order.
DONE_WHEN:
- The new file contains only shared catalog logic and no CLI parsing.
- Names are reusable by later engine and exporter tasks.
```

### TASK 02 — Export the shared catalog from package init

```text
TASK_ID: 02
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/__init__.py
FILE_STATUS: EXISTING FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/__init__.py
READ_LINES_1: 1-15
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/asset_catalog.py
READ_LINES_2: 1-200
EDIT_WINDOW: 1-15
GOAL: Re-export the new asset catalog symbols needed by outside callers.
MAX_EXISTING_LINES_TO_MODIFY: 15
DONE_WHEN:
- Package-level imports expose the shared catalog without adding side effects.
```

### TASK 03 — Create prompt normalization helpers

```text
TASK_ID: 03
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/prompting.py
FILE_STATUS: NEW FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/backend.py
READ_LINES_1: 1-178
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/engine.py
READ_LINES_2: 1-98
GOAL: Create deterministic prompt parsing helpers shared by textures, maps, meshes, and UI generators.
REQUIREMENTS:
- Normalize prompt text.
- Extract tags like biome, theme, item, building, character, enemy, icon, panel, portrait, decal.
- Never call external services.
- Return simple dict/list data only.
DONE_WHEN:
- The file can be imported by later generators without circular imports.
```

### TASK 04 — Create material preset library

```text
TASK_ID: 04
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/texture/material_presets.py
FILE_STATUS: NEW FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/texture/texture_gen.py
READ_LINES_1: 1-98
GOAL: Create deterministic material preset tables for GameRewritten material families.
REQUIREMENTS:
- Include presets for stone, brick, dirt, grass, sand, wood, bark, leaf, water, metal, cloth, leather, crystal, lava, snow, ice, marble, rune, bone.
- Include modifier tables for ancient, cracked, wet, dry, polished, mossy, rusty, blessed, cursed, dark, light.
- Return plain Python structures.
DONE_WHEN:
- All later texture logic can select a preset from this file instead of embedding big tables inline.
```

### TASK 05 — Create palette helper library

```text
TASK_ID: 05
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/texture/palette.py
FILE_STATUS: NEW FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/texture/texture_gen.py
READ_LINES_1: 1-98
GOAL: Add deterministic color palette helpers for materials, icons, portraits, and decals.
REQUIREMENTS:
- Include palette families for forest, desert, coast, ruin, temple, fire, ice, poison, holy, shadow, town, royal.
- Allow seed-based palette variation while staying deterministic.
- Keep output compatible with numpy image generation.
DONE_WHEN:
- The file provides reusable palette selection helpers with no file I/O.
```

### TASK 06 — Upgrade texture generation to material families

```text
TASK_ID: 06
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/texture/texture_gen.py
FILE_STATUS: EXISTING FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/texture/texture_gen.py
READ_LINES_1: 1-98
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/texture/material_presets.py
READ_LINES_2: 1-260
READ_FILE_3: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/texture/palette.py
READ_LINES_3: 1-240
READ_FILE_4: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/prompting.py
READ_LINES_4: 1-220
EDIT_WINDOW: 13-97
GOAL: Replace simple fallback texture generation with deterministic material-family-aware generation.
MAX_EXISTING_LINES_TO_MODIFY: 85
REQUIREMENTS:
- Preserve current function name `generate_pbr_textures`.
- Keep C++ bridge path working if present.
- Improve Python fallback so prompts produce stable family-specific results.
- Support terrain, prop, decal, icon, and portrait texture-style prompts using one shared deterministic path.
DONE_WHEN:
- Different prompts generate visibly different but deterministic outputs.
- Existing texture command path still works.
```

### TASK 07 — Expand texture exporter with sidecar manifest

```text
TASK_ID: 07
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/export/texture_exporter.py
FILE_STATUS: EXISTING FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/export/texture_exporter.py
READ_LINES_1: 1-37
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/asset_catalog.py
READ_LINES_2: 1-220
EDIT_WINDOW: 7-37
GOAL: Export texture PNGs plus one metadata JSON manifest per asset set.
MAX_EXISTING_LINES_TO_MODIFY: 31
REQUIREMENTS:
- Keep existing PNG writing.
- Add material metadata JSON beside the PNGs.
- Include family, prompt, seed, width, height, channels, and relative file names.
- Include GameRewritten material compatibility fields (`shader`, `params.color` RGBA, and deterministic texture path hints).
- Return the main output directory path like today.
DONE_WHEN:
- A texture export produces both image files and one manifest JSON.
- Exported metadata is directly mappable into `GameRewritten/Content/Materials` and `GameRewritten/Content/Textures`.
```

### TASK 08 — Create tileset specification library

```text
TASK_ID: 08
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/map/tileset_specs.py
FILE_STATUS: NEW FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/map/map_gen.py
READ_LINES_1: 1-79
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/docs/file-format-spec.md
READ_LINES_2: 1-156
GOAL: Create reusable tileset specifications for overworld, town, dungeon, cave, coast, desert, snowfield, temple, ruins, and castle.
REQUIREMENTS:
- Each spec should define tile IDs, names, passability, and expected material families.
- Keep the data deterministic and static.
DONE_WHEN:
- Map generation can look up a tileset profile by theme instead of hardcoding everything inline.
```

### TASK 09 — Upgrade map generator to themed map families

```text
TASK_ID: 09
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/map/map_gen.py
FILE_STATUS: EXISTING FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/map/map_gen.py
READ_LINES_1: 1-79
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/map/tileset_specs.py
READ_LINES_2: 1-260
READ_FILE_3: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/prompting.py
READ_LINES_3: 1-220
EDIT_WINDOW: 10-78
GOAL: Replace the random fallback map generator with deterministic themed map generation for GameRewritten.
MAX_EXISTING_LINES_TO_MODIFY: 69
REQUIREMENTS:
- Support overworld, town, dungeon, ruins, coast, desert, forest, snow, temple, and cave prompts.
- Emit stable tile layouts, props, and chosen tileset ID.
- Keep current public function name `generate_tilemap`.
DONE_WHEN:
- Same prompt + seed gives same map.
- Different themed prompts produce meaningfully different layouts.
```

### TASK 10 — Expand map exporter to richer metadata

```text
TASK_ID: 10
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/export/map_exporter.py
FILE_STATUS: EXISTING FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/export/map_exporter.py
READ_LINES_1: 1-55
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/map/tileset_specs.py
READ_LINES_2: 1-260
EDIT_WINDOW: 5-55
GOAL: Export richer map metadata compatible with full asset-bundle use.
MAX_EXISTING_LINES_TO_MODIFY: 51
REQUIREMENTS:
- Preserve current JSON output path behavior.
- Add map family, theme, tileset metadata, and summary counts.
- Keep tiles and props fields.
- Make exported JSON easy to validate later.
- Add destination hints for GameRewritten world ingestion under `Content/World`.
DONE_WHEN:
- Map exports contain enough metadata to be cataloged in bundles.
- Map metadata can be consumed by a deterministic adapter without ambiguous field inference.
```

### TASK 11 — Create static mesh family library

```text
TASK_ID: 11
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/mesh/mesh_family_specs.py
FILE_STATUS: NEW FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/backend.py
READ_LINES_1: 57-142
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/export/mesh_exporter.py
READ_LINES_2: 1-72
GOAL: Create deterministic static mesh family specs for props, architecture, foliage, items, NPC placeholders, and enemy placeholders.
REQUIREMENTS:
- Define family names, primitive recipes, scale ranges, and material slots.
- Include examples like chest, crate, barrel, table, chair, pillar, arch, wall_module, tree, bush, rock, potion, sword_icon_mesh, npc_humanoid, enemy_beast.
- Keep everything pure data.
DONE_WHEN:
- Later mesh generation can choose structured families without embedding all constants in backend.py.
```

### TASK 12 — Create mesh composition helper

```text
TASK_ID: 12
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/mesh/mesh_builder.py
FILE_STATUS: NEW FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/backend.py
READ_LINES_1: 57-142
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/mesh/mesh_family_specs.py
READ_LINES_2: 1-260
GOAL: Add deterministic helper code that builds simple mesh arrays from family specs.
REQUIREMENTS:
- Produce vertices, indices, normals, and uvs.
- Support primitive combinations beyond one cube.
- Keep implementation simple and deterministic.
DONE_WHEN:
- Backend mesh generation can call this helper instead of hardcoding a single mesh shape.
```

### TASK 13 — Upgrade backend mesh generation

```text
TASK_ID: 13
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/backend.py
FILE_STATUS: EXISTING FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/backend.py
READ_LINES_1: 1-178
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/prompting.py
READ_LINES_2: 1-220
READ_FILE_3: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/mesh/mesh_family_specs.py
READ_LINES_3: 1-260
READ_FILE_4: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/mesh/mesh_builder.py
READ_LINES_4: 1-260
EDIT_WINDOW: 57-155
GOAL: Replace the generic cube fallback mesh path with deterministic family-based mesh generation.
MAX_EXISTING_LINES_TO_MODIFY: 99
REQUIREMENTS:
- Preserve BackendRegistry and public backend methods.
- Continue returning vertices, indices, normals, and uvs.
- Use prompt classification to choose a static mesh family.
- Support props, architecture, foliage, items, static NPCs, and static enemies.
DONE_WHEN:
- `generate_mesh` creates different families from different prompts while staying deterministic.
```

### TASK 14 — Expand mesh exporter to OBJ + MTL + manifest

```text
TASK_ID: 14
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/export/mesh_exporter.py
FILE_STATUS: EXISTING FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/export/mesh_exporter.py
READ_LINES_1: 1-72
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/mesh/mesh_family_specs.py
READ_LINES_2: 1-260
EDIT_WINDOW: 6-72
GOAL: Export a richer static mesh package.
MAX_EXISTING_LINES_TO_MODIFY: 67
REQUIREMENTS:
- Keep OBJ export.
- Add MTL output.
- Add JSON sidecar manifest with family, prompt, seed, material slots, and file references.
- Include destination hints for `GameRewritten/Content/Models` and linked material records in `Content/Materials`.
- Keep triangulated validation.
DONE_WHEN:
- One mesh export writes OBJ, MTL, and manifest consistently.
- Mesh manifest fields are sufficient for direct GameRewritten importer wiring.
```

### TASK 15 — Create shared manifest exporter

```text
TASK_ID: 15
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/export/manifest_exporter.py
FILE_STATUS: NEW FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/export/texture_exporter.py
READ_LINES_1: 1-120
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/export/map_exporter.py
READ_LINES_2: 1-120
READ_FILE_3: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/export/mesh_exporter.py
READ_LINES_3: 1-160
GOAL: Create one shared helper to write normalized manifest JSON for all asset families.
REQUIREMENTS:
- Include version, asset family, prompt, seed, files, tags, and source generator.
- Include per-file `content_target` hints for GameRewritten `Content/*` directories.
- Keep file writing centralized.
- Do not add schema validation libraries.
DONE_WHEN:
- Later exporters or bundle builders can reuse one manifest writing helper.
```

### TASK 16 — Add UI asset specifications

```text
TASK_ID: 16
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/ui/ui_specs.py
FILE_STATUS: NEW FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/asset_catalog.py
READ_LINES_1: 1-220
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/prompting.py
READ_LINES_2: 1-220
GOAL: Create deterministic spec tables for UI icons, UI panels, and portrait cards.
REQUIREMENTS:
- Include icon families like weapon, armor, potion, fire, ice, lightning, heal, poison, quest, shop, save, map.
- Include panel families like menu_frame, hud_bar, dialog_box, inventory_slot, tooltip_box.
- Include portrait style families like hero, mage, knight, rogue, cleric, beast, undead, merchant.
DONE_WHEN:
- UI generation tasks can use structured spec tables instead of ad hoc prompt parsing.
```

### TASK 17 — Create icon generator

```text
TASK_ID: 17
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/ui/icon_gen.py
FILE_STATUS: NEW FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/texture/palette.py
READ_LINES_1: 1-240
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/ui/ui_specs.py
READ_LINES_2: 1-260
GOAL: Create a deterministic static icon generator for GameRewritten UI.
REQUIREMENTS:
- Output numpy arrays ready for PNG export.
- Support icon silhouettes and palette-driven fills.
- Keep results deterministic from prompt + seed.
DONE_WHEN:
- The file can generate small static icons without adding external imaging libraries beyond existing dependencies.
```

### TASK 18 — Create panel generator

```text
TASK_ID: 18
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/ui/panel_gen.py
FILE_STATUS: NEW FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/texture/palette.py
READ_LINES_1: 1-240
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/ui/ui_specs.py
READ_LINES_2: 1-260
GOAL: Create deterministic static panel and frame images for menus and HUD.
REQUIREMENTS:
- Generate bordered frames, dialog boxes, slots, bars, and backing plates.
- Keep outputs simple PNG-ready numpy arrays.
DONE_WHEN:
- The file can generate reusable UI panel art for menus and HUD.
```

### TASK 19 — Create portrait card generator

```text
TASK_ID: 19
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/ui/portrait_gen.py
FILE_STATUS: NEW FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/texture/palette.py
READ_LINES_1: 1-240
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/ui/ui_specs.py
READ_LINES_2: 1-260
GOAL: Create deterministic static portrait or bust-card images for party members, NPCs, and enemies.
REQUIREMENTS:
- No animation.
- No face rigging.
- Generate stylized static portrait cards from spec + seed.
DONE_WHEN:
- Portraits are static PNG-ready arrays and can be exported like other textures.
```

### TASK 20 — Add asset pack builder helpers

```text
TASK_ID: 20
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/pack_builder.py
FILE_STATUS: NEW FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/asset_catalog.py
READ_LINES_1: 1-220
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/export/manifest_exporter.py
READ_LINES_2: 1-220
GOAL: Create helper logic for assembling multi-asset packs and bundle manifests.
REQUIREMENTS:
- Support pack assembly for material pack, biome pack, prop pack, architecture pack, foliage pack, item pack, ui pack, portrait pack, character_static pack, enemy_static pack.
- Return simple manifest dicts and file target plans.
DONE_WHEN:
- Engine-level bundle methods can call one shared pack builder helper.
```

### TASK 21 — Upgrade engine with pack-level generation methods

```text
TASK_ID: 21
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/engine.py
FILE_STATUS: EXISTING FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/engine.py
READ_LINES_1: 1-98
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/asset_catalog.py
READ_LINES_2: 1-220
READ_FILE_3: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/pack_builder.py
READ_LINES_3: 1-240
READ_FILE_4: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/ui/icon_gen.py
READ_LINES_4: 1-220
READ_FILE_5: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/ui/panel_gen.py
READ_LINES_5: 1-220
READ_FILE_6: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/ui/portrait_gen.py
READ_LINES_6: 1-220
EDIT_WINDOW: 13-98
GOAL: Add high-level engine APIs for full non-audio/non-animation GameRewritten asset generation.
MAX_EXISTING_LINES_TO_MODIFY: 86
REQUIREMENTS:
- Preserve existing `generate_texture`, `generate_map`, and `generate_mesh` methods.
- Add pack methods for materials, terrain, tilesets, props, architecture, foliage, items, decals, ui_icons, ui_panels, ui_portraits, characters_static, enemies_static, and full bundle generation.
- Keep path handling deterministic and organized by family subdirectories.
DONE_WHEN:
- One engine instance can build either single assets or whole asset families.
```

### TASK 22 — Expand CLI for asset-family commands

```text
TASK_ID: 22
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/cli.py
FILE_STATUS: EXISTING FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/cli.py
READ_LINES_1: 1-89
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/engine.py
READ_LINES_2: 1-220
EDIT_WINDOW: 9-85
GOAL: Add CLI commands for all new GameRewritten asset families and bundle generation.
MAX_EXISTING_LINES_TO_MODIFY: 77
REQUIREMENTS:
- Keep existing texture/map/mesh/list-backends commands working.
- Add commands for ui-icon, ui-panel, portrait, material-pack, biome-pack, prop-pack, architecture-pack, foliage-pack, item-pack, character-static-pack, enemy-static-pack, and full-bundle.
- Keep argument naming consistent with current CLI style.
DONE_WHEN:
- A user can build either one asset family or the whole GameRewritten non-audio/non-animation bundle from the CLI.
```

### TASK 23 — Add bundle recipe definitions

```text
TASK_ID: 23
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/game_rewritten_bundle.py
FILE_STATUS: NEW FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/asset_catalog.py
READ_LINES_1: 1-220
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/pack_builder.py
READ_LINES_2: 1-240
GOAL: Define the exact recipe for the full GameRewritten static asset bundle.
REQUIREMENTS:
- List which asset packs are mandatory.
- List prompts or themes per pack.
- Exclude animation and audio explicitly.
- Define expected `Content/*` destination mapping for every included asset family.
- Keep bundle recipe data-only.
DONE_WHEN:
- Engine and CLI can build the full bundle from one deterministic recipe source.
```

### TASK 24 — Add bundle manifest exporter usage in engine

```text
TASK_ID: 24
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/engine.py
FILE_STATUS: EXISTING FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/engine.py
READ_LINES_1: 1-260
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/game_rewritten_bundle.py
READ_LINES_2: 1-220
READ_FILE_3: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/export/manifest_exporter.py
READ_LINES_3: 1-220
EDIT_WINDOW: 13-260
GOAL: Wire the bundle recipe into engine-level full-bundle generation and manifest export.
MAX_EXISTING_LINES_TO_MODIFY: 120
DONE_WHEN:
- The engine can build a full GameRewritten static asset bundle and write a top-level bundle manifest.
- The top-level bundle manifest contains destination mapping for all files and a compatibility summary block.
```

### TASK 25 — Add validation tests for richer asset outputs

```text
TASK_ID: 25
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/tests/test_backend_and_api.py
FILE_STATUS: EXISTING FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/tests/test_backend_and_api.py
READ_LINES_1: 1-24
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/engine.py
READ_LINES_2: 1-260
EDIT_WINDOW: 1-24
GOAL: Extend backend and engine tests to cover new manifests and at least one new pack-level generation path.
MAX_EXISTING_LINES_TO_MODIFY: 24
REQUIREMENTS:
- Keep current tests.
- Add assertions for sidecar manifests.
- Add assertions for one pack-level generation method.
- Add assertions that exported manifests include GameRewritten compatibility fields and `content_target` hints.
DONE_WHEN:
- Tests validate the expanded asset pipeline at API level.
```

### TASK 26 — Add CLI tests for new commands

```text
TASK_ID: 26
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/tests/test_cli.py
FILE_STATUS: EXISTING FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/tests/test_cli.py
READ_LINES_1: 1-25
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/cli.py
READ_LINES_2: 1-220
EDIT_WINDOW: 1-25
GOAL: Add CLI test coverage for at least one UI command and one full-pack command.
MAX_EXISTING_LINES_TO_MODIFY: 25
DONE_WHEN:
- CLI tests prove new command routing works and produces files in expected locations.
- CLI tests verify compatibility metadata exists in generated outputs.
```

### TASK 27 — Update README with full asset-bundle workflow

```text
TASK_ID: 27
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/README.md
FILE_STATUS: EXISTING FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/README.md
READ_LINES_1: 1-306
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/cli.py
READ_LINES_2: 1-220
EDIT_WINDOW: 1-306
GOAL: Document the new GameRewritten asset families and bundle commands.
MAX_EXISTING_LINES_TO_MODIFY: 80
REQUIREMENTS:
- Keep the current quickstart sections accurate.
- Add examples for UI generation, prop packs, and full bundle generation.
- Explicitly state that animation and audio are excluded.
DONE_WHEN:
- README matches the expanded CLI and output layout.
```

### TASK 28 — Update file format specification for new manifests

```text
TASK_ID: 28
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/docs/file-format-spec.md
FILE_STATUS: EXISTING FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/docs/file-format-spec.md
READ_LINES_1: 1-156
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/creation_engine/export/manifest_exporter.py
READ_LINES_2: 1-220
EDIT_WINDOW: 1-156
GOAL: Expand the spec doc so it covers texture manifests, mesh manifests, pack manifests, and bundle manifests.
MAX_EXISTING_LINES_TO_MODIFY: 100
DONE_WHEN:
- The format spec fully describes all static GameRewritten asset outputs except animation and audio.
```

### TASK 29 — Update tutorial with strict low-reasoning build sequence

```text
TASK_ID: 29
WRITE_FILE: /home/runner/work/Creation-Engine/Creation-Engine/docs/tutorial.md
FILE_STATUS: EXISTING FILE
READ_FILE_1: /home/runner/work/Creation-Engine/Creation-Engine/docs/tutorial.md
READ_LINES_1: 1-36
READ_FILE_2: /home/runner/work/Creation-Engine/Creation-Engine/README.md
READ_LINES_2: 1-380
EDIT_WINDOW: 1-36
GOAL: Rewrite the tutorial into a deterministic step-by-step asset pipeline tutorial for weak local LLM execution.
MAX_EXISTING_LINES_TO_MODIFY: 36
REQUIREMENTS:
- Include commands in exact order.
- Include texture, map, mesh, UI, and bundle examples.
- Keep it beginner-safe and deterministic.
DONE_WHEN:
- A user can follow the tutorial from empty output folder to full GameRewritten static asset bundle.
```

---

## Recommended Bundle Contents

The first full GameRewritten bundle should include at minimum:

- 24 material sets
- 8 biome/terrain material sets
- 8 tilesets
- 12 maps
- 40 props
- 24 architecture modules
- 24 foliage assets
- 20 item meshes
- 32 UI icons
- 12 UI panels
- 24 portrait cards
- 8 static NPC placeholder meshes
- 8 static enemy placeholder meshes
- 12 decal textures

---

## Suggested Prompt Families For The First Bundle

Use a fixed seed set such as `101, 102, 103, 104` and fixed prompts like:

- `ps2 jrpg ff10 style forest shrine stone hand-painted`
- `ps2 jrpg ff12 style desert ruin sandstone low-poly readable silhouettes`
- `ps2 jrpg ff9 style coastal fishing town wood diffuse-first shading`
- `ps2 jrpg ff10 style snow temple marble baked-light look`
- `ps2 jrpg ff7 style volcanic cave basalt stylized contrast`
- `ps2 jrpg ff12 style royal castle polished stone tileable 256 texture feel`
- `ps2 jrpg merchant wagon prop low-poly clean silhouette`
- `ps2 jrpg save crystal prop bright readable landmark`
- `ps2 jrpg healing potion item icon-friendly silhouette`
- `ps2 jrpg knight hero portrait painted ps2-era palette`
- `ps2 jrpg wolf enemy static low-poly readable combat shape`
- `ps2 jrpg quest icon bold shape low-resolution readability`
- `ps2 jrpg inventory panel ff10-era ui framing`

---

## Final Acceptance Criteria

The project is done when all statements below are true:

- Creation-Engine can generate all GameRewritten static asset families listed in this plan.
- Animation is still excluded.
- Audio is still excluded.
- Rigging and skeletal animation data remain excluded from scope.
- Existing texture, map, and mesh commands still work.
- New asset-family commands exist.
- A full GameRewritten bundle command exists.
- Every exported asset family writes metadata manifests.
- Every exported asset family includes deterministic destination hints for `GameRewritten/Content/*`.
- Bundle output includes a compatibility summary proving all non-audio/non-animation families were generated.
- Planned outputs and generated bundle metadata include explicit PS2-era FF7-FF12 style profile tags.
- Prompt families and presets used for generation explicitly enforce PS2-era visuals while supporting modern gameplay readability.
- README, format spec, and tutorial match the implementation.
- Tests cover both API and CLI paths for the new static asset pipeline.

---

## Strict Stop Conditions

Stop and fix before moving on if any of these happen:

- existing texture command breaks
- existing map command breaks
- existing mesh command breaks
- deterministic output changes unexpectedly for the same prompt + seed
- exporters stop writing files
- tests for current commands fail
- new code starts depending on network calls
- animation or audio work starts leaking into scope
