# Creation Engine

Texture + Map Editor for [Game Engine for Teaching](https://github.com/Mikester9000/Game-Engine-for-Teaching-)

Produces **PBR-lite PNG textures** and **JSON tilemaps** designed around a
practical FFXV-like look, with a fully **offline, deterministic AI-assist**
module that turns a text prompt into generator parameters.

---

## Feature Overview

| Feature | Details |
|---|---|
| **Texture channels** | Albedo, Normal, Roughness, Metallic, AO, Emissive |
| **Export formats** | PNG (textures) · JSON (materials & maps) |
| **AI Assist** | Offline rule-based prompt → PBR parameter mapping |
| **Deterministic** | Same seed = same output every time |
| **CLI-first** | Runs anywhere; GUI can be added later |
| **No network** | Zero runtime dependencies beyond a C++17 compiler |

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

### Generate textures

```bash
# Basic (uses AI assist to map prompt → PBR parameters)
./creation-engine texture --prompt "wet stone" --seed 123

# With explicit output directory and resolution
./creation-engine texture --prompt "polished gold" --seed 42 \
  --out assets/materials --width 128 --height 128

# AI assist alias (identical behaviour)
./creation-engine ai texture --prompt "ancient mossy brick" --seed 7
```

Output: `assets/<name>_albedo.png`, `_normal.png`, `_roughness.png`,
`_metallic.png`, `_ao.png`, `_emissive.png`, and `<name>.json`.

### Generate tilemaps

```bash
# Outdoor map with river + road
./creation-engine map --prompt "forest with river and road" --seed 123

# Dungeon
./creation-engine map --prompt "dungeon ruins" --seed 42

# AI assist alias
./creation-engine ai map --prompt "coastal desert with road" --seed 99
```

Output: `assets/<name>.json`

### Validate assets

```bash
./creation-engine validate --dir assets/
```

---

## Asset Format Specification

### Material JSON (`<name>.json`)

```json
{
  "version": "1.0",
  "name": "wet_stone",
  "prompt": "wet stone",
  "seed": 123,
  "params": {
    "baseColor": [0.256, 0.24, 0.224],
    "roughness": 0.3825,
    "metallic": 0,
    "ao": 1,
    "emissive": [0, 0, 0]
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
  texture    Generate PBR textures + material JSON
  map        Generate a procedural tilemap JSON
  ai texture (alias for texture)
  ai map     (alias for map)
  validate   Check JSON assets for required fields
  help       Show this message

Texture options:
  --prompt  "description"   Surface description (default: "stone")
  --seed    <uint>          Determinism seed    (default: 42)
  --name    <ident>         Output file prefix  (default: auto)
  --out     <dir>           Output directory    (default: assets/)
  --width   <px>            Texture width       (default: 64)
  --height  <px>            Texture height      (default: 64)

Map options:
  --prompt  "description"   Terrain description (default: "grass field")
  --seed    <uint>          Determinism seed    (default: 42)
  --name    <ident>         Output file prefix  (default: auto)
  --out     <dir>           Output directory    (default: assets/)

Validate options:
  --dir     <dir>           Directory to scan   (default: assets/)
```

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
└── src/
    ├── main.cpp            CLI entry point (texture/map/ai/validate commands)
    ├── ai/
    │   ├── AIAssist.hpp    Prompt → PBR parameter inference interface
    │   └── AIAssist.cpp    Keyword tables, preset lookup, modifier application
    ├── material/
    │   └── Material.hpp    PBR material struct + JSON serialisation
    ├── map/
    │   ├── MapGen.hpp      TileMap struct + generator interface
    │   └── MapGen.cpp      Heightmap terrain, dungeon, river, road generation
    ├── texture/
    │   ├── TextureGen.hpp  PBR texture generator interface
    │   └── TextureGen.cpp  Albedo/normal/roughness/metallic/AO/emissive generation
    └── util/
        ├── Noise.hpp       Seeded value noise + fBm + ridged fBm
        ├── PNGWriter.hpp   Zero-dependency PNG encoder (uncompressed deflate)
        └── JsonWriter.hpp  Minimal JSON builder (comma-before-element design)
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

