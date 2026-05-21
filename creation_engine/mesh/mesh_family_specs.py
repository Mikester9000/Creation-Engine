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
        "examples": ["chest", "crate", "barrel", "table", "chair", "rock"],
    },
    "architecture": {
        "id": "architecture",
        "label": "Architecture",
        "default_variant": "pillar",
        "material_slots": ["stone", "marble"],
        "examples": ["pillar", "arch", "wall_module", "shrine_marker", "obelisk"],
    },
    "foliage": {
        "id": "foliage",
        "label": "Foliage",
        "default_variant": "tree",
        "material_slots": ["bark", "leaf"],
        "examples": ["tree", "bush"],
    },
    "items": {
        "id": "items",
        "label": "Items",
        "default_variant": "potion",
        "material_slots": ["glass", "metal", "crystal"],
        "examples": ["potion", "sword_icon_mesh"],
    },
    "characters_static": {
        "id": "characters_static",
        "label": "Characters Static",
        "default_variant": "npc_humanoid",
        "material_slots": ["cloth", "leather", "metal"],
        "examples": ["npc_humanoid"],
    },
    "enemies_static": {
        "id": "enemies_static",
        "label": "Enemies Static",
        "default_variant": "enemy_beast",
        "material_slots": ["bone", "leather", "metal"],
        "examples": ["enemy_beast"],
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
    "shrine_marker": {"shrine", "altar", "sanctum"},
    "obelisk": {"obelisk", "spike"},
    "pillar": {"pillar", "column"},
    "arch": {"arch", "gateway"},
    "wall_module": {"wall", "module", "panel"},
    "tree": {"tree", "forest", "oak", "pine"},
    "bush": {"bush", "shrub"},
    "potion": {"potion", "vial", "flask"},
    "sword_icon_mesh": {"sword", "blade", "weapon"},
    "npc_humanoid": {"npc", "human", "humanoid"},
    "enemy_beast": {"enemy", "beast", "wolf", "monster"},
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
