# Creation Engine — Lesson Plan

A self-paced course for game-development students learning C++ and procedural content generation.

## Prerequisites
- Basic C++ (variables, functions, structs, vectors)
- How to compile with g++ or CMake
- Familiarity with the command line

---

## Module 1 — Procedural Noise (est. 3 hours)

**Learning goals:**
- Understand what "pseudo-random but deterministic" means.
- Implement Perlin noise from scratch.
- Extend it with Fractal Brownian Motion (fBm).
- Implement Worley/cellular noise.

**Files to study:** `src/Noise.h`, `src/Noise.cpp`

**Exercises:**
1. Modify `noise2D` to print a 16×16 ASCII visualisation to the terminal.
2. Add a third coordinate `z` to make `noise3D` for animated textures.
3. Change `cellular2D` to return the *second*-nearest distance (F2 variant).

---

## Module 2 — Procedural Textures (est. 4 hours)

**Learning goals:**
- Represent a 2-D image as a flat array of RGBA pixels.
- Use noise functions to drive colour values.
- Combine multiple generators (gradient + noise) for richer results.
- Derive a normal map from a height map using a Sobel filter.

**Files to study:** `src/TextureGenerator.h`, `src/TextureGenerator.cpp`

**Exercises:**
1. Implement a `voronoi` texture that colours each cell differently.
2. Create a `marble` texture by feeding `sin(x + noise)` into a colour map.
3. Use `normalMapFromHeight` on the Perlin noise texture and inspect the result.

---

## Module 3 — Asset I/O (est. 2 hours)

**Learning goals:**
- Use a single-header library (stb_image) to read and write PNG files.
- Serialise C++ structs to JSON without an external library.
- Parse a fixed-schema JSON file with simple string scanning.

**Files to study:** `src/AssetIO.h`, `src/AssetIO.cpp`, `docs/file-format-spec.md`

**Exercises:**
1. Add a `loadTextureMetadata` function that reads back the `.meta.json` sidecar.
2. Extend `saveMap` to include a `"version": 1` field for future compatibility.
3. Write a function that validates a map JSON and reports any missing fields.

---

## Module 4 — Tile Maps (est. 5 hours)

**Learning goals:**
- Understand layered tile map design (ground, collision, decoration, objects).
- Use noise to generate terrain automatically.
- Implement a random-walk algorithm for river generation.
- Place building footprints procedurally.

**Files to study:** `src/MapEditor.h`, `src/MapEditor.cpp`

**Exercises:**
1. Add a `generateForest` function that scatters tree objects (ID 6) on ground tiles.
2. Implement a simple flood-fill to ensure all ground tiles are reachable from the spawn.
3. Add a `generateDungeon` function using Binary Space Partitioning (BSP) rooms and corridors.

---

## Module 5 — CLI Design (est. 2 hours)

**Learning goals:**
- Parse command-line arguments without a library.
- Route subcommands to handler functions.
- Return meaningful exit codes for scripting.

**Files to study:** `src/main.cpp`

**Exercises:**
1. Add a `--normal-map` flag to `create-texture` that also outputs a derived normal map.
2. Add a `create-animation` command that generates N frames with an animated noise slice.
3. Write a Bash script that generates a complete set of biome textures in one command.

---

## Module 6 — AI Assist / Intent Matching (est. 2 hours)

**Learning goals:**
- Map natural-language phrases to structured parameters.
- Extend a keyword table without changing the core generation code.

**Files to study:** `src/AIAssist.h`, `src/AIAssist.cpp`

**Exercises:**
1. Add a "swamp" biome keyword with appropriate colours and noise settings.
2. Add a "city" map type that places many buildings with road object layers.
3. Combine biome textures: "lava field" = lava texture + dungeon map.

---

## Module 7 — Game Engine Integration (est. 4 hours)

**Files to study:** `examples/game-engine-integration/`

**Learning goals:**
- Load assets at runtime in a game loop.
- Upload CPU images to the GPU (OpenGL stub).
- Render a tile layer with a 2-D camera.

**Exercises:**
1. Replace the GPU stub with real `glTexImage2D` calls.
2. Implement a tile renderer that draws each layer at the correct z-depth.
3. Hook the `Trigger` data into a game-event system.

---

## Capstone Project

Build a small top-down game that:
- Uses the Creation Engine to generate the world at startup (or at build time).
- Loads textures, tilesets, and maps at runtime.
- Renders at least two tile layers.
- Respects solid tiles for collision detection.
- Fires triggers when the player enters a trigger zone.
