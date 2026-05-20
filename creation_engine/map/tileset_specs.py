from __future__ import annotations

BASE_TILE_DEFS = [
    {"id": 0, "name": "floor", "passable": True, "material_family": "stone"},
    {"id": 1, "name": "wall", "passable": False, "material_family": "stone"},
    {"id": 2, "name": "water", "passable": False, "material_family": "water"},
    {"id": 3, "name": "grass", "passable": True, "material_family": "grass"},
    {"id": 4, "name": "sand", "passable": True, "material_family": "sand"},
    {"id": 5, "name": "forest", "passable": True, "material_family": "leaf"},
    {"id": 6, "name": "snow", "passable": True, "material_family": "snow"},
    {"id": 7, "name": "road", "passable": True, "material_family": "stone"},
]

TILESET_SPECS = {
    "overworld": {
        "id": "overworld_tileset_v1",
        "name": "Overworld",
        "tile_size": 64,
        "style": "outdoor",
        "tiles": BASE_TILE_DEFS,
    },
    "town": {
        "id": "town_tileset_v1",
        "name": "Town",
        "tile_size": 64,
        "style": "town",
        "tiles": BASE_TILE_DEFS,
    },
    "dungeon": {
        "id": "dungeon_tileset_v1",
        "name": "Dungeon",
        "tile_size": 64,
        "style": "indoor",
        "tiles": BASE_TILE_DEFS,
    },
    "cave": {
        "id": "cave_tileset_v1",
        "name": "Cave",
        "tile_size": 64,
        "style": "indoor",
        "tiles": BASE_TILE_DEFS,
    },
    "coast": {
        "id": "coast_tileset_v1",
        "name": "Coast",
        "tile_size": 64,
        "style": "coast",
        "tiles": BASE_TILE_DEFS,
    },
    "desert": {
        "id": "desert_tileset_v1",
        "name": "Desert",
        "tile_size": 64,
        "style": "desert",
        "tiles": BASE_TILE_DEFS,
    },
    "snowfield": {
        "id": "snowfield_tileset_v1",
        "name": "Snowfield",
        "tile_size": 64,
        "style": "snow",
        "tiles": BASE_TILE_DEFS,
    },
    "temple": {
        "id": "temple_tileset_v1",
        "name": "Temple",
        "tile_size": 64,
        "style": "indoor",
        "tiles": BASE_TILE_DEFS,
    },
    "ruins": {
        "id": "ruins_tileset_v1",
        "name": "Ruins",
        "tile_size": 64,
        "style": "ruins",
        "tiles": BASE_TILE_DEFS,
    },
    "castle": {
        "id": "castle_tileset_v1",
        "name": "Castle",
        "tile_size": 64,
        "style": "indoor",
        "tiles": BASE_TILE_DEFS,
    },
    "forest": {
        "id": "forest_tileset_v1",
        "name": "Forest",
        "tile_size": 64,
        "style": "forest",
        "tiles": BASE_TILE_DEFS,
    },
}

THEME_ALIASES = {
    "overworld": "overworld",
    "plains": "overworld",
    "town": "town",
    "city": "town",
    "dungeon": "dungeon",
    "ruins": "ruins",
    "coast": "coast",
    "coastal": "coast",
    "desert": "desert",
    "forest": "forest",
    "snow": "snowfield",
    "snowfield": "snowfield",
    "temple": "temple",
    "cave": "cave",
    "castle": "castle",
}

