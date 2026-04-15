# Creation Engine File Format Specification

## Overview

The Creation Engine produces three types of asset files:

| File Type | Extension | Format |
|-----------|-----------|--------|
| Texture image | `.png` | PNG (RGBA, 4 bytes/pixel) |
| Texture metadata | `.png.meta.json` | JSON |
| Tileset definition | `.tileset.json` | JSON |
| Map / level | `.map.json` | JSON |

---

## 1. Texture Metadata (`.png.meta.json`)

Small sidecar JSON describing how a texture was generated.

```json
{
  "name": "assets/textures/noise.png",
  "width": 64,
  "height": 64,
  "type": "noise",
  "seed": 42
}
```

| Field  | Type   | Description                                  |
|--------|--------|----------------------------------------------|
| name   | string | Path or label for the texture                |
| width  | int    | Width in pixels                              |
| height | int    | Height in pixels                             |
| type   | string | Generation method: `noise`, `cellular`, etc. |
| seed   | int    | Deterministic seed used during generation    |

---

## 2. Tileset Definition (`.tileset.json`)

Describes how a sprite sheet PNG is divided into tiles.

```json
{
  "texturePath": "assets/textures/tileset.png",
  "tileWidth": 16,
  "tileHeight": 16,
  "tiles": [
    { "id": 0, "name": "empty",  "solid": false },
    { "id": 1, "name": "ground", "solid": false },
    { "id": 2, "name": "wall",   "solid": true  },
    { "id": 3, "name": "water",  "solid": false },
    { "id": 4, "name": "bwall",  "solid": true  },
    { "id": 5, "name": "bfloor", "solid": false }
  ]
}
```

| Field       | Type   | Description                        |
|-------------|--------|------------------------------------|
| texturePath | string | Relative path to the sprite sheet  |
| tileWidth   | int    | Pixel width of each tile           |
| tileHeight  | int    | Pixel height of each tile          |
| tiles       | array  | Metadata for each tile ID          |

Each tile object:

| Field | Type   | Description                              |
|-------|--------|------------------------------------------|
| id    | int    | Integer ID used in tile layers           |
| name  | string | Human-readable label                     |
| solid | bool   | `true` if the tile blocks movement       |

---

## 3. Map File (`.map.json`)

The most complex format; holds all layers and game objects for one level.

```json
{
  "name": "level1",
  "width": 20,
  "height": 15,
  "tileWidth": 16,
  "tileHeight": 16,
  "tilesetPath": "assets/maps/default.tileset.json",
  "tileLayers": [...],
  "objectLayers": [...],
  "entities": [...],
  "spawnPoints": [...],
  "triggers": [...]
}
```

### 3.1 Tile Layer

```json
{
  "name": "ground",
  "width": 20,
  "height": 15,
  "tiles": [2,2,2,...,1,1,1,...]
}
```

`tiles` is a flat, row-major array of integer tile IDs.  
Element at position `(x, y)` is `tiles[y * width + x]`.

### 3.2 Object Layer

```json
{
  "name": "buildings",
  "objects": [
    { "name": "building_0", "type": "building",
      "x": 48, "y": 32, "w": 64, "h": 48 }
  ]
}
```

### 3.3 Entity

```json
{ "id": "enemy_01", "type": "enemy", "x": 160, "y": 96 }
```

### 3.4 Spawn Point

```json
{ "name": "player_start", "x": 160, "y": 120 }
```

### 3.5 Trigger

```json
{
  "name": "exit_south", "action": "load_level:level2",
  "x": 128, "y": 224, "w": 64, "h": 16
}
```

---

## Tile ID Reference

| ID | Meaning        | Solid |
|----|----------------|-------|
| 0  | Empty / no tile | –    |
| 1  | Ground / floor  | No   |
| 2  | Wall            | Yes  |
| 3  | Water / river   | No   |
| 4  | Building wall   | Yes  |
| 5  | Building floor  | No   |
