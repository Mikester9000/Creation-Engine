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

_OVERWORLD_TILES = [
    {"id": 0, "name": "grass_plain", "passable": True, "material_family": "grass"},
    {"id": 1, "name": "cliff_wall", "passable": False, "material_family": "stone"},
    {"id": 2, "name": "river", "passable": False, "material_family": "water"},
    {"id": 3, "name": "forest_edge", "passable": True, "material_family": "leaf"},
    {"id": 4, "name": "dirt_trail", "passable": True, "material_family": "sand"},
    {"id": 5, "name": "dense_forest", "passable": True, "material_family": "leaf"},
    {"id": 6, "name": "highland_rock", "passable": True, "material_family": "stone"},
    {"id": 7, "name": "road", "passable": True, "material_family": "stone"},
]

_TOWN_TILES = [
    {"id": 0, "name": "cobblestone", "passable": True, "material_family": "stone"},
    {"id": 1, "name": "building_wall", "passable": False, "material_family": "stone"},
    {"id": 2, "name": "fountain_water", "passable": False, "material_family": "water"},
    {"id": 3, "name": "market_square", "passable": True, "material_family": "stone"},
    {"id": 4, "name": "alley_stone", "passable": True, "material_family": "stone"},
    {"id": 5, "name": "garden_grass", "passable": True, "material_family": "grass"},
    {"id": 6, "name": "entrance_arch", "passable": True, "material_family": "marble"},
    {"id": 7, "name": "bridge_wood", "passable": True, "material_family": "wood"},
]

_DUNGEON_TILES = [
    {"id": 0, "name": "dungeon_floor", "passable": True, "material_family": "stone"},
    {"id": 1, "name": "dungeon_wall", "passable": False, "material_family": "stone"},
    {"id": 2, "name": "dungeon_pit", "passable": False, "material_family": "water"},
    {"id": 3, "name": "mossy_floor", "passable": True, "material_family": "stone"},
    {"id": 4, "name": "trap_tile", "passable": True, "material_family": "stone"},
    {"id": 5, "name": "collapsed_rubble", "passable": False, "material_family": "stone"},
    {"id": 6, "name": "carved_door", "passable": True, "material_family": "stone"},
    {"id": 7, "name": "drain_grate", "passable": True, "material_family": "metal"},
]

_CAVE_TILES = [
    {"id": 0, "name": "cave_floor", "passable": True, "material_family": "stone"},
    {"id": 1, "name": "cave_wall", "passable": False, "material_family": "stone"},
    {"id": 2, "name": "underground_pool", "passable": False, "material_family": "water"},
    {"id": 3, "name": "stalactite_zone", "passable": False, "material_family": "stone"},
    {"id": 4, "name": "mineral_vein", "passable": True, "material_family": "crystal"},
    {"id": 5, "name": "fungus_bed", "passable": True, "material_family": "leaf"},
    {"id": 6, "name": "collapsed_ceiling", "passable": False, "material_family": "stone"},
    {"id": 7, "name": "narrow_passage", "passable": True, "material_family": "stone"},
]

_COAST_TILES = [
    {"id": 0, "name": "beach_sand", "passable": True, "material_family": "sand"},
    {"id": 1, "name": "sea_cliff", "passable": False, "material_family": "stone"},
    {"id": 2, "name": "ocean_shallow", "passable": False, "material_family": "water"},
    {"id": 3, "name": "ocean_deep", "passable": False, "material_family": "water"},
    {"id": 4, "name": "tidal_flat", "passable": True, "material_family": "sand"},
    {"id": 5, "name": "seagrass", "passable": True, "material_family": "leaf"},
    {"id": 6, "name": "dock_planks", "passable": True, "material_family": "wood"},
    {"id": 7, "name": "rocky_shore", "passable": True, "material_family": "stone"},
]

_DESERT_TILES = [
    {"id": 0, "name": "sand_flat", "passable": True, "material_family": "sand"},
    {"id": 1, "name": "dune_crest", "passable": True, "material_family": "sand"},
    {"id": 2, "name": "oasis_water", "passable": False, "material_family": "water"},
    {"id": 3, "name": "cracked_clay", "passable": True, "material_family": "sand"},
    {"id": 4, "name": "exposed_bedrock", "passable": True, "material_family": "stone"},
    {"id": 5, "name": "scrub_patch", "passable": True, "material_family": "leaf"},
    {"id": 6, "name": "sand_road", "passable": True, "material_family": "sand"},
    {"id": 7, "name": "ancient_ruin_stone", "passable": True, "material_family": "stone"},
]

_SNOWFIELD_TILES = [
    {"id": 0, "name": "snow_flat", "passable": True, "material_family": "snow"},
    {"id": 1, "name": "ice_wall", "passable": False, "material_family": "crystal"},
    {"id": 2, "name": "frozen_lake", "passable": False, "material_family": "water"},
    {"id": 3, "name": "deep_snowdrift", "passable": True, "material_family": "snow"},
    {"id": 4, "name": "frost_rock", "passable": True, "material_family": "stone"},
    {"id": 5, "name": "snow_pine_patch", "passable": True, "material_family": "leaf"},
    {"id": 6, "name": "ice_road", "passable": True, "material_family": "crystal"},
    {"id": 7, "name": "blizzard_zone", "passable": True, "material_family": "snow"},
]

_TEMPLE_TILES = [
    {"id": 0, "name": "marble_floor", "passable": True, "material_family": "marble"},
    {"id": 1, "name": "sacred_wall", "passable": False, "material_family": "marble"},
    {"id": 2, "name": "ritual_pool", "passable": False, "material_family": "water"},
    {"id": 3, "name": "altar_tile", "passable": True, "material_family": "marble"},
    {"id": 4, "name": "rune_floor", "passable": True, "material_family": "marble"},
    {"id": 5, "name": "sacred_garden", "passable": True, "material_family": "leaf"},
    {"id": 6, "name": "crystal_pillar_base", "passable": False, "material_family": "crystal"},
    {"id": 7, "name": "ceremonial_steps", "passable": True, "material_family": "marble"},
]

_RUINS_TILES = [
    {"id": 0, "name": "broken_floor", "passable": True, "material_family": "stone"},
    {"id": 1, "name": "crumbled_wall", "passable": False, "material_family": "stone"},
    {"id": 2, "name": "stagnant_pool", "passable": False, "material_family": "water"},
    {"id": 3, "name": "rubble_pile", "passable": False, "material_family": "stone"},
    {"id": 4, "name": "overgrown_tile", "passable": True, "material_family": "grass"},
    {"id": 5, "name": "ivy_covered_floor", "passable": True, "material_family": "leaf"},
    {"id": 6, "name": "ancient_road_slab", "passable": True, "material_family": "stone"},
    {"id": 7, "name": "buried_glyph_tile", "passable": True, "material_family": "stone"},
]

_VOLCANIC_TILES = [
    {"id": 0, "name": "ash_flat", "passable": True, "material_family": "stone"},
    {"id": 1, "name": "obsidian_wall", "passable": False, "material_family": "stone"},
    {"id": 2, "name": "lava_flow", "passable": False, "material_family": "water"},
    {"id": 3, "name": "cooled_lava_rock", "passable": True, "material_family": "stone"},
    {"id": 4, "name": "volcanic_crater_edge", "passable": True, "material_family": "stone"},
    {"id": 5, "name": "ember_zone", "passable": True, "material_family": "stone"},
    {"id": 6, "name": "obsidian_road", "passable": True, "material_family": "stone"},
    {"id": 7, "name": "lava_tube_floor", "passable": True, "material_family": "stone"},
]

_SACRED_RUINS_TILES = [
    {"id": 0, "name": "shrine_floor", "passable": True, "material_family": "marble"},
    {"id": 1, "name": "sanctum_wall", "passable": False, "material_family": "marble"},
    {"id": 2, "name": "sacred_font", "passable": False, "material_family": "water"},
    {"id": 3, "name": "glyph_tile", "passable": True, "material_family": "marble"},
    {"id": 4, "name": "relic_pedestal", "passable": True, "material_family": "marble"},
    {"id": 5, "name": "overgrown_shrine", "passable": True, "material_family": "leaf"},
    {"id": 6, "name": "crystal_vein_floor", "passable": True, "material_family": "crystal"},
    {"id": 7, "name": "broken_altar_tile", "passable": True, "material_family": "marble"},
]

_IMPERIAL_FORTRESS_TILES = [
    {"id": 0, "name": "fortress_stone", "passable": True, "material_family": "stone"},
    {"id": 1, "name": "rampart_wall", "passable": False, "material_family": "stone"},
    {"id": 2, "name": "moat", "passable": False, "material_family": "water"},
    {"id": 3, "name": "parade_ground", "passable": True, "material_family": "stone"},
    {"id": 4, "name": "armory_floor", "passable": True, "material_family": "stone"},
    {"id": 5, "name": "iron_gate_tile", "passable": True, "material_family": "metal"},
    {"id": 6, "name": "barracks_plank", "passable": True, "material_family": "wood"},
    {"id": 7, "name": "watchtower_floor", "passable": True, "material_family": "stone"},
]

_WASTELAND_TILES = [
    {"id": 0, "name": "parched_earth", "passable": True, "material_family": "sand"},
    {"id": 1, "name": "debris_wall", "passable": False, "material_family": "stone"},
    {"id": 2, "name": "toxic_pool", "passable": False, "material_family": "water"},
    {"id": 3, "name": "cracked_plain", "passable": True, "material_family": "sand"},
    {"id": 4, "name": "scavenger_road", "passable": True, "material_family": "sand"},
    {"id": 5, "name": "rusted_metal_floor", "passable": True, "material_family": "metal"},
    {"id": 6, "name": "bone_field", "passable": True, "material_family": "stone"},
    {"id": 7, "name": "shelter_ruin_tile", "passable": True, "material_family": "stone"},
]

TILESET_SPECS = {
    "overworld": {
        "id": "overworld_tileset_v1",
        "name": "Overworld",
        "tile_size": 64,
        "style": "outdoor",
        "tiles": _OVERWORLD_TILES,
    },
    "town": {
        "id": "town_tileset_v1",
        "name": "Town",
        "tile_size": 64,
        "style": "town",
        "tiles": _TOWN_TILES,
    },
    "dungeon": {
        "id": "dungeon_tileset_v1",
        "name": "Dungeon",
        "tile_size": 64,
        "style": "indoor",
        "tiles": _DUNGEON_TILES,
    },
    "cave": {
        "id": "cave_tileset_v1",
        "name": "Cave",
        "tile_size": 64,
        "style": "indoor",
        "tiles": _CAVE_TILES,
    },
    "coast": {
        "id": "coast_tileset_v1",
        "name": "Coast",
        "tile_size": 64,
        "style": "coast",
        "tiles": _COAST_TILES,
    },
    "desert": {
        "id": "desert_tileset_v1",
        "name": "Desert",
        "tile_size": 64,
        "style": "desert",
        "tiles": _DESERT_TILES,
    },
    "snowfield": {
        "id": "snowfield_tileset_v1",
        "name": "Snowfield",
        "tile_size": 64,
        "style": "snow",
        "tiles": _SNOWFIELD_TILES,
    },
    "temple": {
        "id": "temple_tileset_v1",
        "name": "Temple",
        "tile_size": 64,
        "style": "indoor",
        "tiles": _TEMPLE_TILES,
    },
    "ruins": {
        "id": "ruins_tileset_v1",
        "name": "Ruins",
        "tile_size": 64,
        "style": "ruins",
        "tiles": _RUINS_TILES,
    },
    "castle": {
        "id": "castle_tileset_v1",
        "name": "Castle",
        "tile_size": 64,
        "style": "indoor",
        "tiles": _DUNGEON_TILES,
    },
    "forest": {
        "id": "forest_tileset_v1",
        "name": "Forest",
        "tile_size": 64,
        "style": "forest",
        "tiles": _OVERWORLD_TILES,
    },
    "capital_city": {
        "id": "capital_city_tileset_v1",
        "name": "Capital City",
        "tile_size": 64,
        "style": "town",
        "tiles": _TOWN_TILES,
    },
    "port_city": {
        "id": "port_city_tileset_v1",
        "name": "Port City",
        "tile_size": 64,
        "style": "town",
        "tiles": _COAST_TILES,
    },
    "highlands": {
        "id": "highlands_tileset_v1",
        "name": "Highlands",
        "tile_size": 64,
        "style": "forest",
        "tiles": _OVERWORLD_TILES,
    },
    "volcanic": {
        "id": "volcanic_tileset_v1",
        "name": "Volcanic Zone",
        "tile_size": 64,
        "style": "desert",
        "tiles": _VOLCANIC_TILES,
    },
    "sacred_ruins": {
        "id": "sacred_ruins_tileset_v1",
        "name": "Sacred Ruins",
        "tile_size": 64,
        "style": "ruins",
        "tiles": _SACRED_RUINS_TILES,
    },
    "imperial_fortress": {
        "id": "imperial_fortress_tileset_v1",
        "name": "Imperial Fortress",
        "tile_size": 64,
        "style": "indoor",
        "tiles": _IMPERIAL_FORTRESS_TILES,
    },
    "wasteland": {
        "id": "wasteland_tileset_v1",
        "name": "Wasteland",
        "tile_size": 64,
        "style": "desert",
        "tiles": _WASTELAND_TILES,
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
