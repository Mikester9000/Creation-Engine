from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from creation_engine.asset_catalog import ASSET_FAMILY_OUTPUT_DIRS
from creation_engine.export.manifest_exporter import DEFAULT_STYLE_PROFILE, build_manifest


@dataclass(frozen=True)
class PackEntry:
    name: str
    family: str
    prompt: str
    seed: int
    content_target: str
    source_generator: str
    files: dict[str, str]
    tags: list[str]


PACK_DEFINITIONS = {
    "material_pack": {"family": "materials"},
    "biome_pack": {"family": "terrain"},
    "tileset_pack": {"family": "tilesets"},
    "prop_pack": {"family": "props"},
    "architecture_pack": {"family": "architecture"},
    "foliage_pack": {"family": "foliage"},
    "item_pack": {"family": "items"},
    "decal_pack": {"family": "decals"},
    "ui_icon_pack": {"family": "ui_icons"},
    "ui_panel_pack": {"family": "ui_panels"},
    "ui_portrait_pack": {"family": "ui_portraits"},
    "character_static_pack": {"family": "characters_static"},
    "enemy_static_pack": {"family": "enemies_static"},
    "full_bundle": {"family": "bundles"},
}


def pack_output_dir(root: Path, family: str) -> Path:
    return Path(root) / ASSET_FAMILY_OUTPUT_DIRS.get(family, family)


def build_pack_manifest(
    pack_name: str, entries: list[PackEntry], *, style_profile: str = DEFAULT_STYLE_PROFILE
) -> dict[str, Any]:
    destination_map: dict[str, str] = {}
    for entry in entries:
        for file_name in entry.files.values():
            destination_map[file_name] = entry.content_target

    return build_manifest(
        asset_family=pack_name,
        prompt=pack_name.replace("_", " "),
        seed=entries[0].seed if entries else 42,
        files={entry.name: entry.files.get("manifest", "") for entry in entries},
        source_generator="creation_engine.pack_builder.build_pack_manifest",
        tags=[entry.family for entry in entries],
        content_target={entry.family: entry.content_target for entry in entries},
        name=pack_name,
        style_profile=style_profile,
        pack_entries=[entry.__dict__ for entry in entries],
        destination_map=destination_map,
    )


def build_bundle_manifest(
    bundle_name: str,
    pack_names: list[str],
    pack_manifests: list[dict[str, Any]],
    destination_map: dict[str, str],
    content_targets: dict[str, str],
    *,
    style_profile: str = DEFAULT_STYLE_PROFILE,
) -> dict[str, Any]:
    return build_manifest(
        asset_family="bundles",
        prompt=bundle_name.replace("_", " "),
        seed=pack_manifests[0]["seed"] if pack_manifests else 42,
        files={manifest["name"]: f"{manifest['name']}.json" for manifest in pack_manifests},
        source_generator="creation_engine.pack_builder.build_bundle_manifest",
        tags=pack_names,
        content_target=content_targets,
        name=bundle_name,
        style_profile=style_profile,
        pack_manifests=pack_names,
        destination_map=destination_map,
    )
