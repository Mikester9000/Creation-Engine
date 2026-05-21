"""
Creation Engine – generate textures, materials, maps, meshes, shaders, fonts,
localization, navmeshes, and dialogue for game engines.

Quick-start
-----------
>>> from creation_engine import CreationEngine
>>> engine = CreationEngine()
>>> engine.generate_texture(prompt="wet stone", seed=123, output_dir="assets/")
"""

from creation_engine.engine import CreationEngine
from creation_engine.asset_catalog import (
    ALLOWED_BUNDLE_NAMES,
    ASSET_BUILD_ORDER,
    ASSET_FAMILY_ARCHITECTURE,
    ASSET_FAMILY_BUNDLES,
    ASSET_FAMILY_CHARACTERS_STATIC,
    ASSET_FAMILY_DECALS,
    ASSET_FAMILY_ENEMIES_STATIC,
    ASSET_FAMILY_FOLIAGE,
    ASSET_FAMILY_ITEMS,
    ASSET_FAMILY_MANIFESTS,
    ASSET_FAMILY_MAPS,
    ASSET_FAMILY_MATERIALS,
    ASSET_FAMILY_OUTPUT_DIRS,
    ASSET_FAMILY_PROPS,
    ASSET_FAMILY_TERRAIN,
    ASSET_FAMILY_TILESETS,
    ASSET_FAMILY_UI_ICONS,
    ASSET_FAMILY_UI_PANELS,
    ASSET_FAMILY_UI_PORTRAITS,
    slug_asset_family,
)

__all__ = [
    "CreationEngine",
    "ALLOWED_BUNDLE_NAMES",
    "ASSET_BUILD_ORDER",
    "ASSET_FAMILY_ARCHITECTURE",
    "ASSET_FAMILY_BUNDLES",
    "ASSET_FAMILY_CHARACTERS_STATIC",
    "ASSET_FAMILY_DECALS",
    "ASSET_FAMILY_ENEMIES_STATIC",
    "ASSET_FAMILY_FOLIAGE",
    "ASSET_FAMILY_ITEMS",
    "ASSET_FAMILY_MANIFESTS",
    "ASSET_FAMILY_MAPS",
    "ASSET_FAMILY_MATERIALS",
    "ASSET_FAMILY_OUTPUT_DIRS",
    "ASSET_FAMILY_PROPS",
    "ASSET_FAMILY_TERRAIN",
    "ASSET_FAMILY_TILESETS",
    "ASSET_FAMILY_UI_ICONS",
    "ASSET_FAMILY_UI_PANELS",
    "ASSET_FAMILY_UI_PORTRAITS",
    "slug_asset_family",
]
__version__ = "2.0.0"
