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
    "capital_city": {
        "id": "capital_city_tileset_v1",
        "name": "Capital City",
        "tile_size": 64,
        "style": "town",
        "tiles": BASE_TILE_DEFS,
    },
    "port_city": {
        "id": "port_city_tileset_v1",
        "name": "Port City",
        "tile_size": 64,
        "style": "town",
        "tiles": BASE_TILE_DEFS,
    },
    "highlands": {
        "id": "highlands_tileset_v1",
        "name": "Highlands",
        "tile_size": 64,
        "style": "forest",
        "tiles": BASE_TILE_DEFS,
    },
    "volcanic": {
        "id": "volcanic_tileset_v1",
        "name": "Volcanic Zone",
        "tile_size": 64,
        "style": "desert",
        "tiles": BASE_TILE_DEFS,
    },
    "sacred_ruins": {
        "id": "sacred_ruins_tileset_v1",
        "name": "Sacred Ruins",
        "tile_size": 64,
        "style": "ruins",
        "tiles": BASE_TILE_DEFS,
    },
    "imperial_fortress": {
        "id": "imperial_fortress_tileset_v1",
        "name": "Imperial Fortress",
        "tile_size": 64,
        "style": "indoor",
        "tiles": BASE_TILE_DEFS,
    },
    "wasteland": {
        "id": "wasteland_tileset_v1",
        "name": "Wasteland",
        "tile_size": 64,
        "style": "desert",
        "tiles": BASE_TILE_DEFS,
    },
}

THEME_ALIASES = {
    "overworld": "overworld",
    "plains": "overworld",
    "town": "town",
    "city": "town",
    "dungeon": "dungeon",
    "ruin": "ruins",
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
    "capital": "capital_city",
    "port": "port_city",
    "harbor": "port_city",
    "highland": "highlands",
    "highlands": "highlands",
    "volcanic": "volcanic",
    "lava": "volcanic",
    "sacred": "sacred_ruins",
    "fortress": "imperial_fortress",
    "imperial": "imperial_fortress",
    "wasteland": "wasteland",
}


def resolve_tileset_theme(prompt: str) -> str:
    tokens = prompt.lower().split()
    for token in tokens:
        if token in THEME_ALIASES:
            return THEME_ALIASES[token]
    return "overworld"


def tileset_spec_for_theme(theme: str) -> dict:
    return TILESET_SPECS.get(theme, TILESET_SPECS["overworld"])


def tileset_spec_for_id(tileset_id: str) -> dict | None:
    for spec in TILESET_SPECS.values():
        if spec["id"] == tileset_id:
            return spec
    return None
