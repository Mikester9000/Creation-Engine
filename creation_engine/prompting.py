from __future__ import annotations

import re

from creation_engine.asset_catalog import (
    ASSET_FAMILY_DECALS,
    ASSET_FAMILY_ENEMIES_STATIC,
    ASSET_FAMILY_ITEMS,
    ASSET_FAMILY_PROPS,
    ASSET_FAMILY_UI_ICONS,
    ASSET_FAMILY_UI_PANELS,
    ASSET_FAMILY_UI_PORTRAITS,
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_TAG_KEYWORDS = {
    "biome": {"forest", "desert", "coast", "snow", "temple", "ruin", "town", "swamp", "mountain"},
    "theme": {"holy", "shadow", "fire", "ice", "poison", "royal", "ancient"},
    "item": {"item", "potion", "sword", "shield", "armor", "ring", "gem"},
    "building": {"building", "house", "tower", "castle", "inn", "shop", "temple"},
    "character": {"character", "hero", "knight", "mage", "rogue", "cleric", "npc"},
    "enemy": {"enemy", "beast", "undead", "monster", "fiend"},
    "icon": {"icon", "glyph", "symbol"},
    "panel": {"panel", "frame", "hud", "window", "dialog"},
    "portrait": {"portrait", "bust", "card", "avatar"},
    "decal": {"decal", "emblem", "sticker", "sign", "sigil"},
}


def normalize_prompt(prompt: str) -> str:
    return " ".join(_TOKEN_RE.findall(prompt.lower()))


def tokenize_prompt(prompt: str) -> list[str]:
    return normalize_prompt(prompt).split()


def extract_prompt_tags(prompt: str) -> dict[str, list[str]]:
    tokens = set(tokenize_prompt(prompt))
    return {tag: sorted(tokens.intersection(words)) for tag, words in _TAG_KEYWORDS.items()}


def classify_prompt(prompt: str) -> dict[str, str | list[str]]:
    tags = extract_prompt_tags(prompt)
    family = ASSET_FAMILY_PROPS
    if tags["portrait"]:
        family = ASSET_FAMILY_UI_PORTRAITS
    elif tags["panel"]:
        family = ASSET_FAMILY_UI_PANELS
    elif tags["icon"]:
        family = ASSET_FAMILY_UI_ICONS
    elif tags["decal"]:
        family = ASSET_FAMILY_DECALS
    elif tags["enemy"]:
        family = ASSET_FAMILY_ENEMIES_STATIC
    elif tags["item"]:
        family = ASSET_FAMILY_ITEMS
    return {
        "normalized_prompt": normalize_prompt(prompt),
        "tokens": tokenize_prompt(prompt),
        "family": family,
        "tags": tags,
    }
