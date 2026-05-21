from __future__ import annotations

from typing import Iterable

NARRATIVE_TAG_KEYS = (
    "region",
    "faction",
    "era",
    "story_phase",
    "culture_theme",
)

NARRATIVE_TAG_VALUES = {
    "region": (
        "overworld",
        "frontier",
        "forest",
        "desert",
        "coast",
        "highlands",
        "volcanic",
        "ruins",
        "temple",
        "capital",
        "port_town",
        "wasteland",
        "cavern",
    ),
    "faction": (
        "neutral",
        "imperial",
        "rebel",
        "merchant_guild",
        "shrine_order",
        "ancients",
        "corrupted",
    ),
    "era": (
        "ancient",
        "golden_age",
        "war_of_ruin",
        "present_day",
        "post_cataclysm",
    ),
    "story_phase": (
        "prologue",
        "early_journey",
        "mid_conflict",
        "late_revelation",
        "endgame",
    ),
    "culture_theme": (
        "royal",
        "sacred",
        "magitek",
        "rustic",
        "maritime",
        "nomadic",
        "mystic",
        "corrupted",
    ),
}

_TOKEN_TAG_MAP = {
    "region": {
        "forest": "forest",
        "desert": "desert",
        "coast": "coast",
        "coastal": "coast",
        "highland": "highlands",
        "highlands": "highlands",
        "volcanic": "volcanic",
        "ruin": "ruins",
        "ruins": "ruins",
        "temple": "temple",
        "capital": "capital",
        "port": "port_town",
        "town": "port_town",
        "wasteland": "wasteland",
        "cave": "cavern",
        "cavern": "cavern",
    },
    "faction": {
        "imperial": "imperial",
        "rebel": "rebel",
        "merchant": "merchant_guild",
        "guild": "merchant_guild",
        "shrine": "shrine_order",
        "priest": "shrine_order",
        "ancient": "ancients",
        "corrupted": "corrupted",
    },
    "era": {
        "ancient": "ancient",
        "forgotten": "ancient",
        "golden": "golden_age",
        "war": "war_of_ruin",
        "present": "present_day",
        "modern": "present_day",
        "post": "post_cataclysm",
        "cataclysm": "post_cataclysm",
    },
    "story_phase": {
        "prologue": "prologue",
        "early": "early_journey",
        "journey": "early_journey",
        "mid": "mid_conflict",
        "conflict": "mid_conflict",
        "late": "late_revelation",
        "revelation": "late_revelation",
        "final": "endgame",
        "endgame": "endgame",
    },
    "culture_theme": {
        "royal": "royal",
        "sacred": "sacred",
        "holy": "sacred",
        "magitek": "magitek",
        "imperial": "magitek",
        "rustic": "rustic",
        "village": "rustic",
        "maritime": "maritime",
        "port": "maritime",
        "coastal": "maritime",
        "nomad": "nomadic",
        "nomadic": "nomadic",
        "mystic": "mystic",
        "crystal": "mystic",
        "corrupted": "corrupted",
        "shadow": "corrupted",
    },
}

_DEFAULT_TAGS = {
    "region": "overworld",
    "faction": "neutral",
    "era": "present_day",
    "story_phase": "early_journey",
    "culture_theme": "mystic",
}

_PLACEMENT_INTENT_BY_FAMILY = {
    "materials": "global_material",
    "terrain": "overworld_terrain",
    "tilesets": "world_tileset",
    "maps": "world_region_map",
    "props": "world_prop",
    "architecture": "landmark_structure",
    "foliage": "biome_decoration",
    "items": "loot_or_interactable",
    "decals": "environmental_marking",
    "ui_icons": "ui_symbol",
    "ui_panels": "ui_container",
    "ui_portraits": "ui_character_card",
    "characters_static": "npc_placeholder",
    "enemies_static": "enemy_placeholder",
    "bundles": "bundle_manifest",
}


def extract_narrative_tags(tokens: Iterable[str]) -> dict[str, str]:
    token_set = set(tokens)
    tags = dict(_DEFAULT_TAGS)
    for key in NARRATIVE_TAG_KEYS:
        mapping = _TOKEN_TAG_MAP[key]
        for token in token_set:
            value = mapping.get(token)
            if value:
                tags[key] = value
                break
    return tags


def infer_world_region_id(tags: dict[str, str]) -> str:
    return f"{tags['region']}__{tags['culture_theme']}"


def infer_exploration_intent(tags: dict[str, str]) -> str:
    if tags["region"] in {"temple", "ruins", "cavern"}:
        return "dungeon_exploration"
    if tags["region"] in {"capital", "port_town"}:
        return "settlement_navigation"
    if tags["region"] in {"coast", "forest", "desert", "highlands", "volcanic", "wasteland"}:
        return "open_world_traversal"
    return "overworld_traversal"


def infer_placement_intent(asset_family: str, tags: dict[str, str] | None = None) -> str:
    base = _PLACEMENT_INTENT_BY_FAMILY.get(asset_family, "generic_asset")
    if not tags:
        return base
    if asset_family in {"props", "architecture", "foliage", "items", "decals"}:
        return f"{tags['region']}_{base}"
    return base
