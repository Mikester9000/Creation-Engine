# Creation Engine

Texture + Map Editor for [Game Engine for Teaching](https://github.com/Mikester9000/Game-Engine-for-Teaching-) with material export compatibility for [GameRewritten](https://github.com/Mikester9000/GameRewritten)

Produces **PBR-lite PNG textures** and **JSON tilemaps** designed around a
high-end **FF7–FF12 era JRPG look** (PS1/PS2-era target), with a
fully **offline, deterministic AI-assist** module that turns a text prompt
into generator parameters.

---

## Feature Overview

| Feature | Details |
|---|---|
| **Texture channels** | Albedo, Normal, Roughness, Metallic, AO, Emissive |
| **Export formats** | PNG (textures) · JSON (materials & maps) |
| **AI Assist** | Offline rule-based prompt → PBR parameter mapping |
| **Deterministic** | Same seed = same output every time |
| **CLI + GUI** | Runs from CLI and includes a desktop GUI for editing and preview |
| **No network** | Zero runtime dependencies beyond a C++17 compiler |

---

## Visual Art Direction Guardrail

All future generated content should target:

- **Visual style:** FF7–FF12 era JRPG art direction (FF7/FF8/FF9/FF10/FF11/FF12 reference range), aiming for the highest quality that can still run on PlayStation 2 class constraints.
- **Gameplay support:** asset readability suitable for modern large-scale JRPG gameplay expectations (FFVII Remake / FFXV style feature density), while keeping visuals in the PS1/PS2-era look.
- **Consistency rule:** avoid photoreal AAA-modern material calibration in new presets, prompts, and planned bundle outputs.

---

## Quickstart

### Build

```bash
git clone https://github.com/Mikester9000/Creation-Engine
cd Creation-Engine
mkdir build && cd build
cmake ..
make -j4
```

### Windows one-click GUI launcher

Double-click `run_creation_engine_gui.bat` (or `.\\run_creation_engine_gui.bat`) in File Explorer.

The script will:
- create a local `.venv/`
- install/upgrade runtime Python tooling (`pip`, `setuptools`, `wheel`)
- install required GUI/runtime packages (`numpy`, `pillow`)
- install Creation Engine locally and verify CLI imports
- create default asset folders (`assets/materials`, `assets/maps`, `assets/meshes`, `assets/ui`)
- launch the GUI

### Generate textures

```bash
./creation-engine texture --prompt "wet stone" --seed 123 --output assets
./creation-engine texture --prompt "polished gold" --seed 42 --output assets --width 128 --height 128
```

Output: `assets/<name>_albedo.png`, `_normal.png`, `_roughness.png`,
`_metallic.png`, `_ao.png`, `_emissive.png`, and `<name>.json`.

Single-asset generation also writes a download-friendly copy to
`assets/export/<family>/<name>/` plus `assets/export/index.json` so each
texture/asset file can be downloaded individually.

### Generate tilemaps

```bash
./creation-engine map --prompt "forest with river and road" --seed 123 --output assets
./creation-engine map --prompt "dungeon ruins" --seed 42 --output assets
./creation-engine mesh --prompt "stone pillar" --seed 7 --output assets
```

Output: `assets/<name>.json` for maps, `assets/<name>.obj` for meshes.

### Generate UI assets

```bash
./creation-engine ui-icon --prompt "quest icon" --seed 7 --output assets
./creation-engine ui-panel --prompt "inventory panel" --seed 7 --output assets
./creation-engine portrait --prompt "hero portrait" --seed 7 --output assets
```

### Generate prop and environment packs

```bash
./creation-engine prop-pack --seed 11 --output assets
./creation-engine architecture-pack --seed 11 --output assets
./creation-engine foliage-pack --seed 11 --output assets
./creation-engine item-pack --seed 11 --output assets
./creation-engine decal-pack --seed 11 --output assets
./creation-engine biome-pack --seed 11 --output assets
./creation-engine tileset-pack --seed 11 --output assets
./creation-engine character-static-pack --seed 11 --output assets
./creation-engine enemy-static-pack --seed 11 --output assets
```

### Generate the full GameRewritten static bundle

```bash
./creation-engine material-pack --seed 101 --output assets
./creation-engine full-bundle --seed 101 --output assets
```

These workflows generate only static assets. Animation, rigging, skeletal data, audio, music, voice, and sound effects stay out of scope.

### Validate output quality

```bash
./creation-engine quality-check --output assets
./creation-engine bundle-audit --output assets
./creation-engine release-check --output assets
```

Checks every manifest in `assets/` for required GameRewritten compatibility fields (`style_profile`, `content_target`, referenced files). Exits 0 on pass, 1 on any failure.
`bundle-audit` prints per-family counts, narrative metadata coverage, and FF-style compliance status for release readiness.
`release-check` is the production gate command that combines `quality-check`, `bundle-audit`, and full-bundle completeness matrix validation.

---


## GUI Workflow Highlights

The desktop editor now includes:
- asset browser panel rooted at the selected `--output` directory
- explicit file lifecycle actions: **New File**, **Load**, **Save**, **Save As**, **Delete**
- 2D/3D preview toggle for tilemap JSON and OBJ wireframe preview for mesh silhouette checks
- one-click in-app **Run Quality Check** status to validate export readiness

---

## Asset Format Specification

### Material JSON (`<name>.json`)

```json
{
  "version": "1.1",
  "name": "wet_stone",
  "asset_dimension": "3d",
  "render_pipeline": "3d_pbr",
  "coordinate_space": "Y_up",
  "shader": "Shaders/pbr_3d",
  "prompt": "wet stone",
  "seed": 123,
  "params": {
    "color":     [0.256, 0.24, 0.224, 1.0],
    "baseColor": [0.256, 0.24, 0.224, 1.0]
  },
  "textures": {
    "albedo":    "wet_stone_albedo.png",
    "normal":    "wet_stone_normal.png",
    "roughness": "wet_stone_roughness.png",
    "metallic":  "wet_stone_metallic.png",
    "ao":        "wet_stone_ao.png",
    "emissive":  ""
  }
}
```

Materials now include the required 3D manifest contract fields (`asset_dimension`, `render_pipeline`, `coordinate_space`, `shader`) plus RGBA `params.color`. The legacy `params.baseColor` key is also emitted with identical values so that existing tooling continues to work without modification. The format version is `1.1` to signal the schema change (added `shader`; canonical color key renamed to `color`).

**PBR channel descriptions:**

| Channel | Format | Values | Meaning |
|---------|--------|--------|---------|
| `albedo` | RGB PNG | [0,1] per channel | Surface colour under white light |
| `normal` | RGB PNG | XYZ in [0,1] | Tangent-space normal (`128,128,255` = flat) |
| `roughness` | Grayscale PNG | 0=mirror, 1=matte | Microfacet roughness (GGX) |
| `metallic` | Grayscale PNG | 0=dielectric, 1=metal | Conductive vs non-conductive surface |
| `ao` | Grayscale PNG | 0=occluded, 1=lit | Ambient occlusion (crevice shadowing) |
| `emissive` | RGB PNG | [0,1] | Self-emitted light (black = no emission) |

### Tilemap JSON (`<name>.json`)

```json
{
  "version": "1.0",
  "name": "forest_river",
  "prompt": "forest with river and road",
  "seed": 123,
  "width": 64,
  "height": 64,
  "tileSize": 64,
  "tileset": "forest_river_tileset.json",
  "tiles": [3, 3, 5, 2, ...],
  "props": [
    { "type": "chest",      "x": 12, "y": 8,  "label": "Treasure Chest" },
    { "type": "save_point", "x": 31, "y": 30, "label": "Save Crystal"   }
  ]
}
```

**Tile ID Table** (matches `TileType` enum in Game-Engine-for-Teaching-):

| ID | Name | Char | Passable | Description |
|----|------|------|----------|-------------|
| 0  | FLOOR | `.` | ✓ | Indoor walkable floor |
| 1  | WALL | `#` | ✗ | Solid wall |
| 2  | WATER | `~` | ✗ | Liquid (river, lake) |
| 3  | GRASS | `,` | ✓ | Outdoor grass |
| 4  | SAND | `:` | ✓ | Sand / beach |
| 5  | FOREST | `T` | ✓ | Dense trees |
| 6  | MOUNTAIN | `^` | ✗ | Rocky high ground |
| 7  | ROAD | `=` | ✓ | Paved road |
| 8  | DOOR | `+` | ✓ | Doorway |
| 9  | STAIRS_UP | `<` | ✓ | Staircase up |
| 10 | STAIRS_DOWN | `>` | ✓ | Staircase down |
| 11 | CHEST | `C` | ✓ | Treasure chest |
| 12 | SAVE_POINT | `S` | ✓ | Save crystal |
| 13 | SHOP_TILE | `$` | ✓ | Shop |
| 14 | INN_TILE | `I` | ✓ | Inn |
| 15 | BRIDGE | `=` | ✓ | Bridge over water |

---

## CLI Reference

```
creation-engine <command> [options]

Commands:
  gui                     Launch desktop GUI (file browser + create/edit/save/delete + 2D/3D previews)
  texture                 Generate PBR textures + material JSON
  map                     Generate a procedural tilemap JSON
  mesh                    Generate a static mesh OBJ + manifest
  ui-icon                 Generate a UI icon PNG + manifest
  ui-panel                Generate a UI panel PNG + manifest
  portrait                Generate a portrait card PNG + manifest
  material-pack           Generate all core material sets
  biome-pack              Generate terrain/biome material sets
  tileset-pack            Generate tileset metadata packs
  prop-pack               Generate static prop mesh packs
  architecture-pack       Generate architecture mesh packs
  foliage-pack            Generate foliage mesh packs
  item-pack               Generate item mesh packs
  decal-pack              Generate decal texture packs
  character-static-pack   Generate static NPC placeholder meshes
  enemy-static-pack       Generate static enemy placeholder meshes
  full-bundle             Generate the full GameRewritten static bundle
  quality-check           Validate generated assets for GameRewritten compatibility
  bundle-audit            Summarize bundle counts, narrative coverage, and FF compliance
  release-check           Run production readiness gate checks
  list-backends           List available generation backends

Texture options:
  --prompt  "description"   Surface description (default: "stone")
  --seed    <uint>          Determinism seed    (default: 42)
  --name    <ident>         Output file prefix  (default: auto)
  --output  <dir>           Output directory    (default: assets/)
  --width   <px>            Texture width       (default: 64)
  --height  <px>            Texture height      (default: 64)

Map options:
  --prompt  "description"   Terrain description (default: "grass field")
  --seed    <uint>          Determinism seed    (default: 42)
  --name    <ident>         Output file prefix  (default: auto)
  --output  <dir>           Output directory    (default: assets/)

Pack / bundle options:
  --seed    <uint>          Determinism seed    (default: 42)
  --output  <dir>           Output directory    (default: assets/)

Quality-check options:
  --output       <dir>    Directory to scan    (default: assets/)
  --min-png-size <bytes>  Minimum PNG file size threshold (default: 64)
```

---

## Production Completion Workflow

Run this deterministic release path for non-audio/non-animation asset delivery:

```bash
./creation-engine full-bundle --seed 101 --output assets
./creation-engine quality-check --output assets
./creation-engine bundle-audit --output assets
./creation-engine release-check --output assets
python -m pytest tests/test_backend_and_api.py tests/test_cli.py tests/test_gui.py
bash tests/run_tests.sh
```

Acceptance gates:
- `quality-check` must pass with no style, prompt, metadata, or file-reference errors.
- `bundle-audit` must report `FF aesthetic compliance: PASS` and full narrative/style coverage.
- `release-check` must pass to confirm quality, coverage, and full-bundle completeness matrix integrity in one command.
- test suite must pass before handoff into GameRewritten import flows.

---

## AI Assist — How It Works

The "AI" is fully offline and deterministic — no GPU, no network, no API keys.

**Prompt pipeline:**
```
"wet stone"
    │
    ▼
Tokenise → ["wet", "stone"]
    │
    ▼
Keyword → base preset lookup  →  stone: {baseColor:[0.32,0.30,0.28], roughness:0.85, ...}
    │
    ▼
Modifier application          →  wet: roughness×0.45, color×0.80
    │
    ▼
PBR Material {baseColor:[0.256,0.24,0.224], roughness:0.3825, metallic:0.0}
    │
    ▼
Seeded noise generation       →  PNG textures
```

**Supported material presets (nouns):**
`stone`, `rock`, `cliff`, `dirt`, `mud`, `sand`, `grass`, `soil`, `water`,
`ice`, `snow`, `wood`, `bark`, `moss`, `metal`, `iron`, `steel`, `gold`,
`copper`, `silver`, `lava`, `fire`, `marble`, `concrete`, `brick`, `tile`,
`floor`, `wall`, `road`

**Supported modifiers (adjectives):**
`wet`, `dry`, `polished`, `rough`, `cracked`, `aged`, `burnt`, `mossy`,
`dusty`, `shiny`, `dark`, `light`, `rusty`, `ancient`, `fresh`, `deep`,
`shallow`, `red`, `blue`, `green`, `orange`, `yellow`, `purple`, `black`, `white`

**Map keywords:**
`river`, `stream`, `road`, `path`, `dungeon`, `cave`, `ruins`,
`forest`, `mountain`, `desert`, `plains`, `coastal`, `large`, `small`

---

## Source Layout

```
Creation-Engine/
├── CMakeLists.txt
├── README.md
├── assets/
│   ├── materials/          Sample PNG + JSON outputs (wet_stone, forest_soil, polished_gold)
│   └── maps/               Sample tilemap JSONs (forest_river, dungeon_ruins)
└── creation_engine/        Python package (primary asset pipeline)
    ├── cli.py              CLI entry point
    ├── engine.py           CreationEngine API
    ├── backend.py          Backend registry + ProceduralBackend
    ├── asset_catalog.py    Asset family constants and build order
    ├── prompting.py        Prompt classification helpers
    ├── pack_builder.py     Pack + bundle manifest helpers
    ├── game_rewritten_bundle.py  Full bundle recipe
    ├── quality_check.py    GameRewritten compatibility validator
    ├── texture/
    │   ├── texture_gen.py  PBR texture generator
    │   ├── material_presets.py  Material preset tables
    │   └── palette.py      Color palette helpers
    ├── map/
    │   ├── map_gen.py      Tilemap generator
    │   └── tileset_specs.py  Tileset theme specs
    ├── mesh/
    │   ├── mesh_builder.py Mesh composition helper
    │   └── mesh_family_specs.py  Mesh family definitions
    ├── ui/
    │   ├── icon_gen.py     UI icon generator
    │   ├── panel_gen.py    UI panel generator
    │   ├── portrait_gen.py Portrait card generator
    │   └── ui_specs.py     UI spec tables
    └── export/
        ├── texture_exporter.py  PNG + manifest export
        ├── map_exporter.py      Tilemap JSON export
        ├── mesh_exporter.py     OBJ + MTL + manifest export
        └── manifest_exporter.py Shared manifest writer
```

---

## Lesson Plan Outline

### Module 1 — Procedural Noise (Noise.hpp)
- **Concepts**: Hash functions, interpolation, fractal Brownian motion
- **Exercises**:
  1. Change `octaves` from 4 → 1. How does the texture change?
  2. Change `persistence` from 0.5 → 0.8. What happens to fine detail?
  3. Add a third noise function using `ridgedFbm` for rock surfaces.

### Module 2 — PBR Shading Model (Material.hpp, TextureGen.cpp)
- **Concepts**: Albedo, roughness, metallic, AO, emissive; BRDF basics
- **Exercises**:
  1. Set `metallic=1.0` on stone — why does it look wrong?
  2. Set `roughness=0.0` on grass — what happens to specular highlights?
  3. Add a "patina" material: copper with green tint and increased roughness.

### Module 3 — PNG File Format (PNGWriter.hpp)
- **Concepts**: File signatures, chunked formats, CRC32, DEFLATE, Adler32
- **Exercises**:
  1. Open a generated PNG in a hex editor. Find the `IHDR`, `IDAT` bytes.
  2. Corrupt 1 byte in an IDAT chunk. Does PNG validation catch it? (Yes.)
  3. Add filter type 1 (Sub filter) support and compare file sizes.

### Module 4 — Procedural Tilemap Generation (MapGen.cpp)
- **Concepts**: Heightmaps, biome thresholds, dungeon BSP, river descent
- **Exercises**:
  1. Adjust the `WATER_MAX` threshold to 0.4 — does the map get more water?
  2. Implement a "village" biome: clusters of WALL tiles on GRASS.
  3. Add A\* pathfinding for roads instead of the greedy gradient walk.

### Module 5 — Rule-Based AI Assist (AIAssist.cpp)
- **Concepts**: Tokenisation, lookup tables, compositional parameter systems
- **Exercises**:
  1. Add a `"rusty"` modifier that adds orange tint to metal materials.
  2. Add a `"snow"` preset: white baseColor, roughness 0.9.
  3. Implement a confidence score: return top 3 matched presets.

### Module 6 — Asset Pipeline Integration
- **Concepts**: JSON as asset format, validation, deterministic generation
- **Exercises**:
  1. Load `wet_stone.json` in Python and print its `params.roughness`.
  2. Write a shell script that generates 10 materials with seeds 1–10.
  3. Add the `validate` command to a CI pipeline and break it intentionally.
