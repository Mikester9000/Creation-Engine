from __future__ import annotations

import re

ASSET_FAMILY_MATERIALS = "materials"
ASSET_FAMILY_TERRAIN = "terrain"
ASSET_FAMILY_TILESETS = "tilesets"
ASSET_FAMILY_MAPS = "maps"
ASSET_FAMILY_PROPS = "props"
ASSET_FAMILY_ARCHITECTURE = "architecture"
ASSET_FAMILY_FOLIAGE = "foliage"
ASSET_FAMILY_ITEMS = "items"
ASSET_FAMILY_DECALS = "decals"
ASSET_FAMILY_CHARACTERS_STATIC = "characters_static"
ASSET_FAMILY_ENEMIES_STATIC = "enemies_static"
ASSET_FAMILY_UI_ICONS = "ui_icons"
ASSET_FAMILY_UI_PANELS = "ui_panels"
ASSET_FAMILY_UI_PORTRAITS = "ui_portraits"
ASSET_FAMILY_MANIFESTS = "manifests"
ASSET_FAMILY_BUNDLES = "bundles"

ASSET_BUILD_ORDER = [
    ASSET_FAMILY_MATERIALS,
    ASSET_FAMILY_TERRAIN,
    ASSET_FAMILY_TILESETS,
    ASSET_FAMILY_MAPS,
    ASSET_FAMILY_PROPS,
    ASSET_FAMILY_ARCHITECTURE,
    ASSET_FAMILY_FOLIAGE,
    ASSET_FAMILY_ITEMS,
    ASSET_FAMILY_DECALS,
    ASSET_FAMILY_CHARACTERS_STATIC,
    ASSET_FAMILY_ENEMIES_STATIC,
    ASSET_FAMILY_UI_ICONS,
    ASSET_FAMILY_UI_PANELS,
    ASSET_FAMILY_UI_PORTRAITS,
    ASSET_FAMILY_MANIFESTS,
    ASSET_FAMILY_BUNDLES,
]

ASSET_FAMILY_OUTPUT_DIRS = {family: family.replace("_", "/") for family in ASSET_BUILD_ORDER}
ALLOWED_BUNDLE_NAMES = ("core_static", "world_foundation", "ui_foundation", "full_static")


def slug_asset_family(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "asset"
