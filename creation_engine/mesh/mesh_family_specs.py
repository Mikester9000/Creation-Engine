from __future__ import annotations

MESH_FAMILY_ORDER = [
    "props",
    "architecture",
    "foliage",
    "items",
    "characters_static",
    "enemies_static",
]

MESH_FAMILY_SPECS = {
    "props": {
        "id": "props",
        "label": "Props",
        "default_variant": "crate",
        "material_slots": ["wood", "metal"],
        "examples": [
            "chest",
            "crate",
            "barrel",
            "table",
            "chair",
            "rock",
            "campfire",
            "market_stall",
            "lantern_post",
        ],
    },
    "architecture": {
        "id": "architecture",
        "label": "Architecture",
        "default_variant": "pillar",
        "material_slots": ["stone", "marble"],
        "examples": [
            "pillar",
            "arch",
            "wall_module",
            "shrine_marker",
            "obelisk",
            "crystal_altar",
            "ruin_gateway",
            "fortress_bastion",
        ],
    },
    "foliage": {
        "id": "foliage",
        "label": "Foliage",
        "default_variant": "tree",
        "material_slots": ["bark", "leaf"],
        "examples": ["tree", "bush", "deadwood", "sacred_shrub"],
    },
    "items": {
        "id": "items",
        "label": "Items",
        "default_variant": "potion",
        "material_slots": ["glass", "metal", "crystal"],
        "examples": ["potion", "sword_icon_mesh", "relic_orb", "field_ration"],
    },
    "characters_static": {
        "id": "characters_static",
        "label": "Characters Static",
        "default_variant": "npc_humanoid",
        "material_slots": ["cloth", "leather", "metal"],
        "examples": ["npc_humanoid", "npc_guard", "npc_priest"],
    },
    "enemies_static": {
        "id": "enemies_static",
        "label": "Enemies Static",
        "default_variant": "enemy_beast",
        "material_slots": ["bone", "leather", "metal"],
        "examples": ["enemy_beast", "enemy_hunter", "enemy_sentinel"],
    },
}

MESH_VARIANT_SPECS = {
    "chest": {
        "family": "props",
        "label": "Chest",
        "material_slots": ["wood", "metal"],
        "parts": [
            {"kind": "box", "scale": (1.0, 0.55, 0.75), "offset": (0.0, -0.05, 0.0)},
            {"kind": "box", "scale": (1.0, 0.28, 0.82), "offset": (0.0, 0.38, 0.0)},
            {"kind": "box", "scale": (0.12, 0.42, 0.82), "offset": (-0.44, 0.12, 0.0)},
            {"kind": "box", "scale": (0.12, 0.42, 0.82), "offset": (0.44, 0.12, 0.0)},
        ],
    },
    "crate": {
        "family": "props",
        "label": "Crate",
        "material_slots": ["wood"],
        "parts": [
            {"kind": "box", "scale": (1.0, 1.0, 1.0), "offset": (0.0, 0.0, 0.0)},
            {"kind": "box", "scale": (0.92, 0.06, 0.92), "offset": (0.0, 0.47, 0.0)},
        ],
    },
    "barrel": {
        "family": "props",
        "label": "Barrel",
        "material_slots": ["wood", "metal"],
        "parts": [
            {"kind": "prism", "scale": (0.82, 1.0, 0.82), "offset": (0.0, 0.0, 0.0), "sides": 8},
            {"kind": "box", "scale": (0.9, 0.08, 0.9), "offset": (0.0, 0.48, 0.0)},
            {"kind": "box", "scale": (0.9, 0.08, 0.9), "offset": (0.0, -0.48, 0.0)},
        ],
    },
    "table": {
        "family": "props",
        "label": "Table",
        "material_slots": ["wood"],
        "parts": [
            {"kind": "box", "scale": (1.4, 0.14, 0.9), "offset": (0.0, 0.55, 0.0)},
            {"kind": "box", "scale": (0.15, 0.95, 0.15), "offset": (-0.6, 0.0, -0.35)},
            {"kind": "box", "scale": (0.15, 0.95, 0.15), "offset": (0.6, 0.0, -0.35)},
            {"kind": "box", "scale": (0.15, 0.95, 0.15), "offset": (-0.6, 0.0, 0.35)},
            {"kind": "box", "scale": (0.15, 0.95, 0.15), "offset": (0.6, 0.0, 0.35)},
        ],
    },
    "chair": {
        "family": "props",
        "label": "Chair",
        "material_slots": ["wood"],
        "parts": [
            {"kind": "box", "scale": (0.8, 0.14, 0.8), "offset": (0.0, -0.05, 0.0)},
            {"kind": "box", "scale": (0.8, 0.9, 0.14), "offset": (0.0, 0.48, -0.34)},
            {"kind": "box", "scale": (0.12, 0.82, 0.12), "offset": (-0.32, 0.0, -0.28)},
            {"kind": "box", "scale": (0.12, 0.82, 0.12), "offset": (0.32, 0.0, -0.28)},
            {"kind": "box", "scale": (0.12, 0.82, 0.12), "offset": (-0.32, 0.0, 0.28)},
            {"kind": "box", "scale": (0.12, 0.82, 0.12), "offset": (0.32, 0.0, 0.28)},
        ],
    },
    "rock": {
        "family": "props",
        "label": "Rock",
        "material_slots": ["stone"],
        "parts": [
            {"kind": "pyramid", "scale": (0.95, 0.7, 0.9), "offset": (0.0, 0.0, 0.0)},
            {"kind": "box", "scale": (0.55, 0.3, 0.45), "offset": (0.22, -0.1, -0.15)},
        ],
    },
    "save_point": {
        "family": "props",
        "label": "Save Point",
        "material_slots": ["crystal", "stone"],
        "parts": [
            {"kind": "prism", "scale": (0.42, 1.1, 0.42), "offset": (0.0, 0.32, 0.0), "sides": 6},
            {"kind": "box", "scale": (0.68, 0.14, 0.68), "offset": (0.0, -0.45, 0.0)},
        ],
    },
    "boat_marker": {
        "family": "props",
        "label": "Boat Marker",
        "material_slots": ["wood", "cloth"],
        "parts": [
            {"kind": "box", "scale": (1.0, 0.18, 0.32), "offset": (0.0, -0.18, 0.0)},
            {"kind": "pyramid", "scale": (0.65, 0.95, 0.4), "offset": (0.0, 0.42, 0.0)},
        ],
    },
    "campfire": {
        "family": "props",
        "label": "Campfire",
        "material_slots": ["wood", "stone"],
        "parts": [
            {"kind": "box", "scale": (0.95, 0.08, 0.95), "offset": (0.0, -0.42, 0.0)},
            {"kind": "box", "scale": (0.12, 0.42, 0.12), "offset": (-0.22, -0.2, -0.04)},
            {"kind": "box", "scale": (0.12, 0.42, 0.12), "offset": (0.22, -0.2, 0.04)},
            {"kind": "pyramid", "scale": (0.36, 0.44, 0.36), "offset": (0.0, -0.12, 0.0)},
        ],
    },
    "market_stall": {
        "family": "props",
        "label": "Market Stall",
        "material_slots": ["wood", "cloth"],
        "parts": [
            {"kind": "box", "scale": (1.45, 0.12, 0.9), "offset": (0.0, 0.55, 0.0)},
            {"kind": "box", "scale": (1.55, 0.18, 0.95), "offset": (0.0, 0.85, 0.0)},
            {"kind": "box", "scale": (0.14, 1.05, 0.14), "offset": (-0.6, 0.0, -0.34)},
            {"kind": "box", "scale": (0.14, 1.05, 0.14), "offset": (0.6, 0.0, -0.34)},
            {"kind": "box", "scale": (0.14, 1.05, 0.14), "offset": (-0.6, 0.0, 0.34)},
            {"kind": "box", "scale": (0.14, 1.05, 0.14), "offset": (0.6, 0.0, 0.34)},
        ],
    },
    "lantern_post": {
        "family": "props",
        "label": "Lantern Post",
        "material_slots": ["wood", "metal"],
        "parts": [
            {"kind": "pillar", "scale": (0.16, 1.7, 0.16), "offset": (0.0, 0.1, 0.0)},
            {"kind": "box", "scale": (0.65, 0.08, 0.08), "offset": (0.22, 0.82, 0.0)},
            {"kind": "box", "scale": (0.2, 0.28, 0.2), "offset": (0.46, 0.62, 0.0)},
        ],
    },
    "shrine_marker": {
        "family": "architecture",
        "label": "Shrine Marker",
        "material_slots": ["stone", "marble"],
        "parts": [
            {"kind": "pillar", "scale": (0.36, 1.45, 0.36), "offset": (0.0, 0.28, 0.0)},
            {"kind": "box", "scale": (0.85, 0.15, 0.85), "offset": (0.0, -0.52, 0.0)},
            {"kind": "prism", "scale": (0.52, 0.38, 0.52), "offset": (0.0, 1.15, 0.0), "sides": 8},
        ],
    },
    "obelisk": {
        "family": "architecture",
        "label": "Obelisk",
        "material_slots": ["stone", "marble"],
        "parts": [
            {"kind": "pyramid", "scale": (0.45, 1.8, 0.45), "offset": (0.0, 0.55, 0.0)},
            {"kind": "box", "scale": (0.65, 0.18, 0.65), "offset": (0.0, -0.6, 0.0)},
        ],
    },
    "pillar": {
        "family": "architecture",
        "label": "Pillar",
        "material_slots": ["stone"],
        "parts": [
            {"kind": "pillar", "scale": (0.45, 1.8, 0.45), "offset": (0.0, 0.0, 0.0)},
            {"kind": "box", "scale": (0.68, 0.12, 0.68), "offset": (0.0, -0.92, 0.0)},
            {"kind": "box", "scale": (0.58, 0.1, 0.58), "offset": (0.0, 0.94, 0.0)},
        ],
    },
    "arch": {
        "family": "architecture",
        "label": "Arch",
        "material_slots": ["stone", "marble"],
        "parts": [
            {"kind": "box", "scale": (0.3, 1.5, 0.3), "offset": (-0.48, 0.0, 0.0)},
            {"kind": "box", "scale": (0.3, 1.5, 0.3), "offset": (0.48, 0.0, 0.0)},
            {"kind": "box", "scale": (1.25, 0.24, 0.32), "offset": (0.0, 0.88, 0.0)},
        ],
    },
    "wall_module": {
        "family": "architecture",
        "label": "Wall Module",
        "material_slots": ["stone"],
        "parts": [
            {"kind": "box", "scale": (1.5, 1.0, 0.28), "offset": (0.0, 0.0, 0.0)},
            {"kind": "box", "scale": (0.18, 1.18, 0.18), "offset": (-0.6, 0.0, 0.12)},
            {"kind": "box", "scale": (0.18, 1.18, 0.18), "offset": (0.6, 0.0, 0.12)},
        ],
    },
    "crystal_altar": {
        "family": "architecture",
        "label": "Crystal Altar",
        "material_slots": ["marble", "crystal"],
        "parts": [
            {"kind": "box", "scale": (1.35, 0.2, 1.35), "offset": (0.0, -0.62, 0.0)},
            {"kind": "box", "scale": (0.72, 0.34, 0.72), "offset": (0.0, -0.34, 0.0)},
            {"kind": "prism", "scale": (0.35, 1.05, 0.35), "offset": (0.0, 0.45, 0.0), "sides": 8},
        ],
    },
    "ruin_gateway": {
        "family": "architecture",
        "label": "Ruin Gateway",
        "material_slots": ["stone", "marble"],
        "parts": [
            {"kind": "box", "scale": (0.28, 1.8, 0.32), "offset": (-0.58, 0.0, 0.0)},
            {"kind": "box", "scale": (0.28, 1.8, 0.32), "offset": (0.58, 0.0, 0.0)},
            {"kind": "box", "scale": (1.6, 0.24, 0.34), "offset": (0.0, 0.92, 0.0)},
            {"kind": "box", "scale": (1.1, 0.12, 0.28), "offset": (0.0, 0.62, 0.0)},
        ],
    },
    "fortress_bastion": {
        "family": "architecture",
        "label": "Fortress Bastion",
        "material_slots": ["stone", "metal"],
        "parts": [
            {"kind": "box", "scale": (1.45, 1.2, 1.1), "offset": (0.0, 0.0, 0.0)},
            {"kind": "box", "scale": (1.55, 0.16, 1.2), "offset": (0.0, 0.72, 0.0)},
            {"kind": "box", "scale": (0.28, 0.42, 0.28), "offset": (-0.56, 1.0, -0.42)},
            {"kind": "box", "scale": (0.28, 0.42, 0.28), "offset": (0.56, 1.0, -0.42)},
            {"kind": "box", "scale": (0.28, 0.42, 0.28), "offset": (-0.56, 1.0, 0.42)},
            {"kind": "box", "scale": (0.28, 0.42, 0.28), "offset": (0.56, 1.0, 0.42)},
        ],
    },
    "tree": {
        "family": "foliage",
        "label": "Tree",
        "material_slots": ["bark", "leaf"],
        "parts": [
            {"kind": "pillar", "scale": (0.28, 1.45, 0.28), "offset": (0.0, -0.1, 0.0)},
            {"kind": "prism", "scale": (1.0, 0.92, 1.0), "offset": (0.0, 0.72, 0.0), "sides": 6},
            {"kind": "box", "scale": (0.72, 0.48, 0.72), "offset": (0.2, 1.0, -0.18)},
        ],
    },
    "bush": {
        "family": "foliage",
        "label": "Bush",
        "material_slots": ["leaf"],
        "parts": [
            {"kind": "prism", "scale": (0.68, 0.38, 0.68), "offset": (0.0, 0.0, 0.0), "sides": 6},
            {"kind": "box", "scale": (0.42, 0.26, 0.42), "offset": (0.28, 0.1, 0.1)},
            {"kind": "box", "scale": (0.42, 0.26, 0.42), "offset": (-0.18, 0.08, -0.2)},
        ],
    },
    "deadwood": {
        "family": "foliage",
        "label": "Deadwood",
        "material_slots": ["bark"],
        "parts": [
            {"kind": "pillar", "scale": (0.22, 1.2, 0.22), "offset": (0.0, -0.02, 0.0)},
            {"kind": "box", "scale": (0.82, 0.1, 0.12), "offset": (0.0, 0.42, 0.06)},
            {"kind": "box", "scale": (0.58, 0.08, 0.1), "offset": (-0.12, 0.68, -0.04)},
        ],
    },
    "sacred_shrub": {
        "family": "foliage",
        "label": "Sacred Shrub",
        "material_slots": ["leaf", "crystal"],
        "parts": [
            {"kind": "prism", "scale": (0.62, 0.34, 0.62), "offset": (0.0, 0.0, 0.0), "sides": 6},
            {"kind": "box", "scale": (0.36, 0.38, 0.36), "offset": (0.0, 0.28, 0.0)},
            {"kind": "prism", "scale": (0.18, 0.24, 0.18), "offset": (0.2, 0.42, -0.08), "sides": 8},
        ],
    },
    "potion": {
        "family": "items",
        "label": "Potion",
        "material_slots": ["glass", "crystal", "metal"],
        "parts": [
            {"kind": "prism", "scale": (0.42, 0.82, 0.42), "offset": (0.0, -0.02, 0.0), "sides": 8},
            {"kind": "box", "scale": (0.18, 0.38, 0.18), "offset": (0.0, 0.52, 0.0)},
            {"kind": "box", "scale": (0.26, 0.1, 0.26), "offset": (0.0, 0.75, 0.0)},
        ],
    },
    "sword_icon_mesh": {
        "family": "items",
        "label": "Sword Icon Mesh",
        "material_slots": ["metal", "leather"],
        "parts": [
            {"kind": "box", "scale": (0.12, 1.15, 0.18), "offset": (0.0, 0.4, 0.0)},
            {"kind": "box", "scale": (0.42, 0.12, 0.24), "offset": (0.0, -0.1, 0.0)},
            {"kind": "box", "scale": (0.18, 0.28, 0.18), "offset": (0.0, -0.42, 0.0)},
        ],
    },
    "relic_orb": {
        "family": "items",
        "label": "Relic Orb",
        "material_slots": ["crystal", "metal"],
        "parts": [
            {"kind": "prism", "scale": (0.42, 0.42, 0.42), "offset": (0.0, 0.24, 0.0), "sides": 10},
            {"kind": "box", "scale": (0.62, 0.12, 0.62), "offset": (0.0, -0.12, 0.0)},
            {"kind": "box", "scale": (0.2, 0.3, 0.2), "offset": (0.0, -0.34, 0.0)},
        ],
    },
    "field_ration": {
        "family": "items",
        "label": "Field Ration",
        "material_slots": ["cloth", "leather"],
        "parts": [
            {"kind": "box", "scale": (0.72, 0.42, 0.38), "offset": (0.0, 0.0, 0.0)},
            {"kind": "box", "scale": (0.78, 0.08, 0.44), "offset": (0.0, 0.22, 0.0)},
        ],
    },
    "npc_humanoid": {
        "family": "characters_static",
        "label": "NPC Humanoid",
        "material_slots": ["cloth", "leather", "metal"],
        "parts": [
            {"kind": "box", "scale": (0.55, 0.72, 0.32), "offset": (0.0, 0.22, 0.0)},
            {"kind": "box", "scale": (0.4, 0.38, 0.4), "offset": (0.0, 0.92, 0.0)},
            {"kind": "box", "scale": (0.16, 0.72, 0.16), "offset": (-0.28, -0.35, 0.0)},
            {"kind": "box", "scale": (0.16, 0.72, 0.16), "offset": (0.28, -0.35, 0.0)},
            {"kind": "box", "scale": (0.18, 0.78, 0.18), "offset": (-0.18, -1.02, 0.0)},
            {"kind": "box", "scale": (0.18, 0.78, 0.18), "offset": (0.18, -1.02, 0.0)},
        ],
    },
    "npc_guard": {
        "family": "characters_static",
        "label": "NPC Guard",
        "material_slots": ["cloth", "metal", "leather"],
        "parts": [
            {"kind": "box", "scale": (0.6, 0.78, 0.34), "offset": (0.0, 0.18, 0.0)},
            {"kind": "box", "scale": (0.42, 0.36, 0.42), "offset": (0.0, 0.9, 0.0)},
            {"kind": "box", "scale": (0.18, 0.72, 0.18), "offset": (-0.22, -0.98, 0.0)},
            {"kind": "box", "scale": (0.18, 0.72, 0.18), "offset": (0.22, -0.98, 0.0)},
            {"kind": "box", "scale": (0.16, 0.7, 0.16), "offset": (-0.34, -0.22, 0.0)},
            {"kind": "box", "scale": (0.16, 0.7, 0.16), "offset": (0.34, -0.22, 0.0)},
        ],
    },
    "npc_priest": {
        "family": "characters_static",
        "label": "NPC Priest",
        "material_slots": ["cloth", "crystal"],
        "parts": [
            {"kind": "box", "scale": (0.52, 0.88, 0.3), "offset": (0.0, 0.15, 0.0)},
            {"kind": "box", "scale": (0.38, 0.34, 0.38), "offset": (0.0, 0.9, 0.0)},
            {"kind": "box", "scale": (0.16, 0.74, 0.16), "offset": (-0.18, -0.98, 0.0)},
            {"kind": "box", "scale": (0.16, 0.74, 0.16), "offset": (0.18, -0.98, 0.0)},
            {"kind": "prism", "scale": (0.14, 0.3, 0.14), "offset": (0.0, 0.48, 0.24), "sides": 8},
        ],
    },
    "enemy_beast": {
        "family": "enemies_static",
        "label": "Enemy Beast",
        "material_slots": ["bone", "leather", "metal"],
        "parts": [
            {"kind": "box", "scale": (0.72, 0.52, 0.44), "offset": (0.0, 0.1, 0.0)},
            {"kind": "box", "scale": (0.44, 0.34, 0.32), "offset": (0.45, 0.22, 0.0)},
            {"kind": "box", "scale": (0.18, 0.66, 0.18), "offset": (-0.34, -0.32, -0.18)},
            {"kind": "box", "scale": (0.18, 0.66, 0.18), "offset": (-0.34, -0.32, 0.18)},
            {"kind": "prism", "scale": (0.22, 0.52, 0.22), "offset": (-0.68, 0.0, 0.0), "sides": 6},
        ],
    },
    "enemy_hunter": {
        "family": "enemies_static",
        "label": "Enemy Hunter",
        "material_slots": ["leather", "metal", "bone"],
        "parts": [
            {"kind": "box", "scale": (0.58, 0.76, 0.34), "offset": (0.0, 0.2, 0.0)},
            {"kind": "box", "scale": (0.4, 0.34, 0.4), "offset": (0.0, 0.92, 0.0)},
            {"kind": "box", "scale": (0.18, 0.72, 0.18), "offset": (-0.2, -0.98, 0.0)},
            {"kind": "box", "scale": (0.18, 0.72, 0.18), "offset": (0.2, -0.98, 0.0)},
            {"kind": "box", "scale": (0.18, 0.68, 0.18), "offset": (0.38, -0.14, 0.04)},
        ],
    },
    "enemy_sentinel": {
        "family": "enemies_static",
        "label": "Enemy Sentinel",
        "material_slots": ["stone", "metal", "crystal"],
        "parts": [
            {"kind": "box", "scale": (0.66, 1.02, 0.4), "offset": (0.0, 0.06, 0.0)},
            {"kind": "box", "scale": (0.48, 0.36, 0.48), "offset": (0.0, 0.88, 0.0)},
            {"kind": "box", "scale": (0.2, 0.76, 0.2), "offset": (-0.24, -1.02, 0.0)},
            {"kind": "box", "scale": (0.2, 0.76, 0.2), "offset": (0.24, -1.02, 0.0)},
            {"kind": "prism", "scale": (0.14, 0.34, 0.14), "offset": (0.0, 0.4, 0.3), "sides": 8},
        ],
    },
}

_MESH_FAMILY_KEYWORDS = {
    "characters_static": {
        "character",
        "npc",
        "hero",
        "knight",
        "mage",
        "rogue",
        "cleric",
        "villager",
    },
    "enemies_static": {"enemy", "beast", "undead", "monster", "fiend", "wolf", "dragon", "goblin"},
    "foliage": {"tree", "bush", "leaf", "forest", "plant"},
    "architecture": {"pillar", "arch", "wall", "castle", "temple", "shrine", "building", "roof"},
    "items": {"potion", "sword", "blade", "icon", "gem", "relic", "artifact"},
}

_VARIANT_KEYWORDS = {
    "chest": {"chest", "treasure", "loot", "coffer"},
    "crate": {"crate", "box", "package"},
    "barrel": {"barrel", "cask", "keg"},
    "table": {"table", "desk", "dining"},
    "chair": {"chair", "seat", "stool"},
    "rock": {"rock", "stone", "boulder"},
    "save_point": {"save", "crystal", "checkpoint"},
    "boat_marker": {"boat", "ship", "harbor", "dock"},
    "campfire": {"campfire", "camp", "firepit"},
    "market_stall": {"stall", "market", "vendor"},
    "lantern_post": {"lantern", "lamp", "post"},
    "shrine_marker": {"shrine", "altar", "sanctum"},
    "obelisk": {"obelisk", "spike"},
    "crystal_altar": {"crystal", "altar", "relic"},
    "ruin_gateway": {"gateway", "gate", "ruin"},
    "fortress_bastion": {"fortress", "bastion", "tower"},
    "pillar": {"pillar", "column"},
    "arch": {"arch", "gateway"},
    "wall_module": {"wall", "module", "panel"},
    "tree": {"tree", "forest", "oak", "pine"},
    "bush": {"bush", "shrub"},
    "deadwood": {"deadwood", "stump", "withered"},
    "sacred_shrub": {"sacred", "shrub", "blessed"},
    "potion": {"potion", "vial", "flask"},
    "sword_icon_mesh": {"sword", "blade", "weapon"},
    "relic_orb": {"orb", "relic", "artifact"},
    "field_ration": {"ration", "pack", "supply"},
    "npc_humanoid": {"npc", "human", "humanoid"},
    "npc_guard": {"guard", "soldier", "watch"},
    "npc_priest": {"priest", "cleric", "acolyte"},
    "enemy_beast": {"enemy", "beast", "wolf", "monster"},
    "enemy_hunter": {"hunter", "raider", "assassin"},
    "enemy_sentinel": {"sentinel", "construct", "warden"},
}


def resolve_mesh_family(tokens: list[str]) -> str:
    token_set = set(tokens)
    for family in MESH_FAMILY_ORDER:
        if token_set.intersection(_MESH_FAMILY_KEYWORDS.get(family, set())):
            return family
    return "props"


def resolve_mesh_variant(family: str, tokens: list[str]) -> str:
    token_set = set(tokens)
    for variant, keywords in _VARIANT_KEYWORDS.items():
        spec = MESH_VARIANT_SPECS[variant]
        if spec["family"] == family and token_set.intersection(keywords):
            return variant
    default_variant = MESH_FAMILY_SPECS[family]["default_variant"]
    return default_variant
