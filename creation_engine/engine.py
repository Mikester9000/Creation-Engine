from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from PIL import Image

from creation_engine.asset_catalog import (
    ASSET_FAMILY_ARCHITECTURE,
    ASSET_FAMILY_BUNDLES,
    ASSET_FAMILY_CHARACTERS_STATIC,
    ASSET_FAMILY_DECALS,
    ASSET_FAMILY_ENEMIES_STATIC,
    ASSET_FAMILY_FOLIAGE,
    ASSET_FAMILY_ITEMS,
    ASSET_FAMILY_MAPS,
    ASSET_FAMILY_MATERIALS,
    ASSET_FAMILY_OUTPUT_DIRS,
    ASSET_FAMILY_PROPS,
    ASSET_FAMILY_TERRAIN,
    ASSET_FAMILY_TILESETS,
    ASSET_FAMILY_UI_ICONS,
    ASSET_FAMILY_UI_PANELS,
    ASSET_FAMILY_UI_PORTRAITS,
)
from creation_engine.backend import AssetBackend, BackendRegistry
from creation_engine.export.manifest_exporter import (
    DEFAULT_STYLE_PROFILE,
    build_manifest,
    write_manifest_json,
)
from creation_engine.export.map_exporter import export_tilemap
from creation_engine.export.mesh_exporter import export_obj
from creation_engine.export.texture_exporter import export_pbr_textures
from creation_engine.game_rewritten_bundle import GAME_REWRITTEN_BUNDLE_RECIPE
from creation_engine.map.tileset_specs import (
    resolve_tileset_theme,
    tileset_spec_for_theme,
)
from creation_engine.narrative_tags import (
    extract_narrative_tags,
    infer_exploration_intent,
    infer_placement_intent,
    infer_world_region_id,
)
from creation_engine.prompting import classify_prompt, tokenize_prompt
from creation_engine.ui.icon_gen import generate_ui_icon as build_ui_icon_image
from creation_engine.ui.panel_gen import generate_ui_panel as build_ui_panel_image
from creation_engine.ui.portrait_gen import generate_ui_portrait as build_ui_portrait_image

_BUNDLE_PROMPT_KEY_BY_PACK = {
    "material_pack": "materials",
    "biome_pack": "terrain",
    "tileset_pack": "tilesets",
    "prop_pack": "props",
    "architecture_pack": "architecture",
    "foliage_pack": "foliage",
    "item_pack": "items",
    "decal_pack": "decals",
    "ui_icon_pack": "ui_icons",
    "ui_panel_pack": "ui_panels",
    "ui_portrait_pack": "ui_portraits",
    "character_static_pack": "characters_static",
    "enemy_static_pack": "enemies_static",
}
_BUNDLE_MIN_COUNTS_BY_PACK = {
    pack_name: len(GAME_REWRITTEN_BUNDLE_RECIPE["prompts"][prompt_key])
    for pack_name, prompt_key in _BUNDLE_PROMPT_KEY_BY_PACK.items()
}
_REQUIRED_BUNDLE_DESTINATION_TARGETS = {
    target
    for family, target in GAME_REWRITTEN_BUNDLE_RECIPE["content_targets"].items()
    if family != ASSET_FAMILY_BUNDLES
}


class CreationEngine:
    def __init__(
        self,
        backend: str | AssetBackend = "procedural",
        seed: int | None = None,
        output_dir: str | Path = "assets",
    ) -> None:
        self.seed = seed
        self.output_dir = Path(output_dir)

        if isinstance(backend, AssetBackend):
            self.backend = backend
        else:
            self.backend = BackendRegistry.create(backend, seed=seed)

    def generate_texture(
        self,
        prompt: str,
        width: int = 64,
        height: int = 64,
        output_dir: str | Path | None = None,
        name: str | None = None,
        **kwargs: Any,
    ) -> Path:
        out_dir = (
            Path(output_dir)
            if output_dir
            else self.output_dir / ASSET_FAMILY_OUTPUT_DIRS[ASSET_FAMILY_MATERIALS]
        )
        asset_name = name or self._make_name(prompt)
        seed = kwargs.pop("seed", self.seed)
        texture_data = self.backend.generate_texture(
            prompt=prompt,
            width=width,
            height=height,
            seed=seed,
            **kwargs,
        )
        parsed = classify_prompt(prompt)
        return export_pbr_textures(
            texture_data=texture_data,
            output_dir=out_dir,
            name=asset_name,
            prompt=prompt,
            seed=seed,
            family=str(parsed["family"]),
            width=width,
            height=height,
            parsed_prompt=parsed,
        )

    def generate_map(
        self,
        prompt: str,
        width: int = 64,
        height: int = 64,
        output_dir: str | Path | None = None,
        name: str | None = None,
        **kwargs: Any,
    ) -> Path:
        out_dir = (
            Path(output_dir)
            if output_dir
            else self.output_dir / ASSET_FAMILY_OUTPUT_DIRS[ASSET_FAMILY_MAPS]
        )
        asset_name = name or self._make_name(prompt)
        seed = kwargs.pop("seed", self.seed)
        map_data = self.backend.generate_map(
            prompt=prompt,
            width=width,
            height=height,
            seed=seed,
            **kwargs,
        )
        return export_tilemap(
            map_data=map_data,
            output_dir=out_dir,
            name=asset_name,
            prompt=prompt,
            seed=seed,
        )

    def generate_mesh(
        self,
        prompt: str,
        complexity: str = "medium",
        output_dir: str | Path | None = None,
        name: str | None = None,
        **kwargs: Any,
    ) -> Path:
        asset_name = name or self._make_name(prompt)
        mesh_data = self.backend.generate_mesh(
            prompt=prompt,
            complexity=complexity,
            seed=kwargs.pop("seed", self.seed),
            **kwargs,
        )
        mesh_family = str(mesh_data.get("family", ASSET_FAMILY_PROPS))
        out_dir = (
            Path(output_dir)
            if output_dir
            else self.output_dir / ASSET_FAMILY_OUTPUT_DIRS[mesh_family]
        )
        return export_obj(mesh_data=mesh_data, output_dir=out_dir, name=asset_name)

    def generate_ui_icon(
        self,
        prompt: str,
        seed: int | None = None,
        output_dir: str | Path | None = None,
        name: str | None = None,
    ) -> Path:
        return self._export_ui_image(
            prompt=prompt,
            seed=seed,
            output_dir=output_dir,
            name=name,
            family=ASSET_FAMILY_UI_ICONS,
            generator=build_ui_icon_image,
            width=64,
            height=64,
            source_generator="creation_engine.ui.icon_gen.generate_ui_icon",
        )

    def generate_ui_panel(
        self,
        prompt: str,
        seed: int | None = None,
        output_dir: str | Path | None = None,
        name: str | None = None,
    ) -> Path:
        return self._export_ui_image(
            prompt=prompt,
            seed=seed,
            output_dir=output_dir,
            name=name,
            family=ASSET_FAMILY_UI_PANELS,
            generator=build_ui_panel_image,
            width=256,
            height=64,
            source_generator="creation_engine.ui.panel_gen.generate_ui_panel",
        )

    def generate_portrait(
        self,
        prompt: str,
        seed: int | None = None,
        output_dir: str | Path | None = None,
        name: str | None = None,
    ) -> Path:
        return self._export_ui_image(
            prompt=prompt,
            seed=seed,
            output_dir=output_dir,
            name=name,
            family=ASSET_FAMILY_UI_PORTRAITS,
            generator=build_ui_portrait_image,
            width=128,
            height=128,
            source_generator="creation_engine.ui.portrait_gen.generate_ui_portrait",
        )

    def generate_material_pack(
        self, seed: int | None = None, output_dir: str | Path | None = None
    ) -> Path:
        return self._generate_texture_pack(
            pack_name="material_pack",
            asset_family=ASSET_FAMILY_MATERIALS,
            prompts=GAME_REWRITTEN_BUNDLE_RECIPE["prompts"]["materials"],
            output_dir=output_dir,
            seed=seed,
        )

    def generate_terrain_pack(
        self, seed: int | None = None, output_dir: str | Path | None = None
    ) -> Path:
        return self._generate_texture_pack(
            pack_name="biome_pack",
            asset_family=ASSET_FAMILY_TERRAIN,
            prompts=GAME_REWRITTEN_BUNDLE_RECIPE["prompts"]["terrain"],
            output_dir=output_dir,
            seed=seed,
        )

    def generate_tileset_pack(
        self, seed: int | None = None, output_dir: str | Path | None = None
    ) -> Path:
        return self._generate_tileset_pack(
            pack_name="tileset_pack",
            prompts=GAME_REWRITTEN_BUNDLE_RECIPE["prompts"]["tilesets"],
            output_dir=output_dir,
            seed=seed,
        )

    def generate_prop_pack(
        self, seed: int | None = None, output_dir: str | Path | None = None
    ) -> Path:
        return self._generate_mesh_pack(
            "prop_pack",
            GAME_REWRITTEN_BUNDLE_RECIPE["prompts"]["props"],
            output_dir,
            seed,
            ASSET_FAMILY_PROPS,
        )

    def generate_architecture_pack(
        self, seed: int | None = None, output_dir: str | Path | None = None
    ) -> Path:
        return self._generate_mesh_pack(
            "architecture_pack",
            GAME_REWRITTEN_BUNDLE_RECIPE["prompts"]["architecture"],
            output_dir,
            seed,
            ASSET_FAMILY_ARCHITECTURE,
        )

    def generate_foliage_pack(
        self, seed: int | None = None, output_dir: str | Path | None = None
    ) -> Path:
        return self._generate_mesh_pack(
            "foliage_pack",
            GAME_REWRITTEN_BUNDLE_RECIPE["prompts"]["foliage"],
            output_dir,
            seed,
            ASSET_FAMILY_FOLIAGE,
        )

    def generate_item_pack(
        self, seed: int | None = None, output_dir: str | Path | None = None
    ) -> Path:
        return self._generate_mesh_pack(
            "item_pack",
            GAME_REWRITTEN_BUNDLE_RECIPE["prompts"]["items"],
            output_dir,
            seed,
            ASSET_FAMILY_ITEMS,
        )

    def generate_decal_pack(
        self, seed: int | None = None, output_dir: str | Path | None = None
    ) -> Path:
        return self._generate_texture_pack(
            pack_name="decal_pack",
            asset_family=ASSET_FAMILY_DECALS,
            prompts=GAME_REWRITTEN_BUNDLE_RECIPE["prompts"]["decals"],
            output_dir=output_dir,
            seed=seed,
        )

    def generate_ui_icon_pack(
        self, seed: int | None = None, output_dir: str | Path | None = None
    ) -> Path:
        return self._generate_ui_pack(
            pack_name="ui_icon_pack",
            prompts=GAME_REWRITTEN_BUNDLE_RECIPE["prompts"]["ui_icons"],
            output_dir=output_dir,
            seed=seed,
            family=ASSET_FAMILY_UI_ICONS,
            generator=self.generate_ui_icon,
        )

    def generate_ui_panel_pack(
        self, seed: int | None = None, output_dir: str | Path | None = None
    ) -> Path:
        return self._generate_ui_pack(
            pack_name="ui_panel_pack",
            prompts=GAME_REWRITTEN_BUNDLE_RECIPE["prompts"]["ui_panels"],
            output_dir=output_dir,
            seed=seed,
            family=ASSET_FAMILY_UI_PANELS,
            generator=self.generate_ui_panel,
        )

    def generate_ui_portrait_pack(
        self, seed: int | None = None, output_dir: str | Path | None = None
    ) -> Path:
        return self._generate_ui_pack(
            pack_name="ui_portrait_pack",
            prompts=GAME_REWRITTEN_BUNDLE_RECIPE["prompts"]["ui_portraits"],
            output_dir=output_dir,
            seed=seed,
            family=ASSET_FAMILY_UI_PORTRAITS,
            generator=self.generate_portrait,
        )

    def generate_character_static_pack(
        self, seed: int | None = None, output_dir: str | Path | None = None
    ) -> Path:
        return self._generate_mesh_pack(
            "character_static_pack",
            GAME_REWRITTEN_BUNDLE_RECIPE["prompts"]["characters_static"],
            output_dir,
            seed,
            ASSET_FAMILY_CHARACTERS_STATIC,
        )

    def generate_enemy_static_pack(
        self, seed: int | None = None, output_dir: str | Path | None = None
    ) -> Path:
        return self._generate_mesh_pack(
            "enemy_static_pack",
            GAME_REWRITTEN_BUNDLE_RECIPE["prompts"]["enemies_static"],
            output_dir,
            seed,
            ASSET_FAMILY_ENEMIES_STATIC,
        )

    def generate_full_bundle(
        self, seed: int | None = None, output_dir: str | Path | None = None
    ) -> Path:
        bundle_seed = seed if seed is not None else (self.seed if self.seed is not None else 42)
        out_root = Path(output_dir) if output_dir else self.output_dir
        pack_builders = [
            self.generate_material_pack,
            self.generate_terrain_pack,
            self.generate_tileset_pack,
            self.generate_prop_pack,
            self.generate_architecture_pack,
            self.generate_foliage_pack,
            self.generate_item_pack,
            self.generate_decal_pack,
            self.generate_ui_icon_pack,
            self.generate_ui_panel_pack,
            self.generate_ui_portrait_pack,
            self.generate_character_static_pack,
            self.generate_enemy_static_pack,
        ]

        pack_manifests: list[dict[str, Any]] = []
        destination_map: dict[str, str] = {}
        for builder in pack_builders:
            manifest_path = builder(seed=bundle_seed, output_dir=out_root)
            with open(manifest_path, encoding="utf-8") as file:
                manifest = json_load(file)
            pack_manifests.append(manifest)
            for filename, target in manifest.get("destination_map", {}).items():
                destination_map[filename] = target
        completeness_matrix = self._build_bundle_completeness_matrix(pack_manifests, destination_map)
        if not completeness_matrix["complete"]:
            failures: list[str] = []
            if completeness_matrix["missing_required_packs"]:
                failures.append(
                    "missing packs: " + ", ".join(completeness_matrix["missing_required_packs"])
                )
            if completeness_matrix["underfilled_packs"]:
                failures.append(
                    "underfilled packs: "
                    + ", ".join(
                        f"{entry['name']} ({entry['actual']}/{entry['expected_min']})"
                        for entry in completeness_matrix["underfilled_packs"]
                    )
                )
            if completeness_matrix["missing_destination_targets"]:
                failures.append(
                    "missing destination targets: "
                    + ", ".join(completeness_matrix["missing_destination_targets"])
                )
            raise ValueError("Full bundle completeness validation failed: " + " ; ".join(failures))

        bundle_dir = out_root / ASSET_FAMILY_OUTPUT_DIRS[ASSET_FAMILY_BUNDLES]
        bundle_dir.mkdir(parents=True, exist_ok=True)
        bundle_manifest = build_manifest(
            asset_family=ASSET_FAMILY_BUNDLES,
            prompt=GAME_REWRITTEN_BUNDLE_RECIPE["name"],
            seed=bundle_seed,
            files={manifest["name"]: f"{manifest['name']}.json" for manifest in pack_manifests},
            source_generator="creation_engine.engine.CreationEngine.generate_full_bundle",
            tags=GAME_REWRITTEN_BUNDLE_RECIPE["required_packs"],
            content_target=GAME_REWRITTEN_BUNDLE_RECIPE["content_targets"],
            name=GAME_REWRITTEN_BUNDLE_RECIPE["name"],
            style_profile=GAME_REWRITTEN_BUNDLE_RECIPE["style_profile"],
            pack_manifests=[manifest["name"] for manifest in pack_manifests],
            required_packs=GAME_REWRITTEN_BUNDLE_RECIPE["required_packs"],
            destination_map=destination_map,
            compatibility_summary={
                "style_profile": GAME_REWRITTEN_BUNDLE_RECIPE["style_profile"],
                "excluded": ["animation", "audio", "music", "voice", "sound_effects"],
                "generated_families": [
                    ASSET_FAMILY_MATERIALS,
                    ASSET_FAMILY_TERRAIN,
                    ASSET_FAMILY_TILESETS,
                    ASSET_FAMILY_PROPS,
                    ASSET_FAMILY_ARCHITECTURE,
                    ASSET_FAMILY_FOLIAGE,
                    ASSET_FAMILY_ITEMS,
                    ASSET_FAMILY_DECALS,
                    ASSET_FAMILY_UI_ICONS,
                    ASSET_FAMILY_UI_PANELS,
                    ASSET_FAMILY_UI_PORTRAITS,
                    ASSET_FAMILY_CHARACTERS_STATIC,
                    ASSET_FAMILY_ENEMIES_STATIC,
                ],
            },
            completeness_matrix=completeness_matrix,
        )
        return write_manifest_json(bundle_dir, bundle_manifest["name"], bundle_manifest)

    @staticmethod
    def _make_name(prompt: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", prompt.lower()).strip("_")
        return slug or "asset"

    def _export_ui_image(
        self,
        prompt: str,
        seed: int | None,
        output_dir: str | Path | None,
        name: str | None,
        family: str,
        generator: Any,
        width: int,
        height: int,
        source_generator: str,
    ) -> Path:
        out_dir = (
            Path(output_dir) if output_dir else self.output_dir / ASSET_FAMILY_OUTPUT_DIRS[family]
        )
        asset_name = name or self._make_name(prompt)
        seed_value = seed if seed is not None else (self.seed if self.seed is not None else 42)
        image = generator(prompt=prompt, seed=seed_value, size=width if height == width else (width, height))
        if image.shape[0] != height or image.shape[1] != width:
            raise ValueError(f"{family} generator returned unexpected image size")
        out_dir.mkdir(parents=True, exist_ok=True)
        png_path = out_dir / f"{asset_name}.png"
        Image.fromarray(image).save(png_path)
        parsed = classify_prompt(prompt)
        narrative_tags = parsed["narrative_tags"]
        manifest = build_manifest(
            asset_family=family,
            prompt=prompt,
            seed=seed_value,
            files={"image": png_path.name, "manifest": f"{asset_name}.json"},
            source_generator=source_generator,
            tags=[family],
            content_target={"ui": "Content/UI"},
            name=asset_name,
            style_profile=DEFAULT_STYLE_PROFILE,
            width=width,
            height=height,
            channels=["image"],
            narrative_tags=narrative_tags,
            world_region_id=parsed["world_region_id"],
            exploration_intent=parsed["exploration_intent"],
            placement_intent=infer_placement_intent(family, narrative_tags),
        )
        write_manifest_json(out_dir, asset_name, manifest)
        return png_path

    def _generate_texture_pack(
        self,
        pack_name: str,
        asset_family: str,
        prompts: list[str],
        output_dir: str | Path | None,
        seed: int | None,
    ) -> Path:
        out_root = Path(output_dir) if output_dir else self.output_dir
        out_dir = out_root / ASSET_FAMILY_OUTPUT_DIRS[asset_family]
        out_dir.mkdir(parents=True, exist_ok=True)
        seed_value = seed if seed is not None else (self.seed if self.seed is not None else 42)
        entries: list[dict[str, Any]] = []
        for index, prompt in enumerate(prompts):
            asset_seed = seed_value + index
            asset_name = self._make_name(prompt)
            self.generate_texture(
                prompt=prompt, output_dir=out_dir, name=asset_name, seed=asset_seed,
                width=128, height=128,
            )
            entry = {
                "name": asset_name,
                "prompt": prompt,
                "seed": asset_seed,
                "family": asset_family,
                "manifest": f"{asset_name}.json",
                "files": {
                    "manifest": f"{asset_name}.json",
                    "albedo": f"{asset_name}_albedo.png",
                    "normal": f"{asset_name}_normal.png",
                    "roughness": f"{asset_name}_roughness.png",
                    "metallic": f"{asset_name}_metallic.png",
                    "ao": f"{asset_name}_ao.png",
                    "emissive": f"{asset_name}_emissive.png",
                },
                "content_target": (
                    "Content/Materials"
                    if asset_family == ASSET_FAMILY_MATERIALS
                    else "Content/Textures"
                ),
            }
            entry["destination_map"] = {
                filename: entry["content_target"] for filename in entry["files"].values()
            }
            entries.append(entry)
        return self._write_pack_manifest(
            pack_name, out_dir, entries, style_profile=DEFAULT_STYLE_PROFILE
        )

    def _generate_mesh_pack(
        self,
        pack_name: str,
        prompts: list[str],
        output_dir: str | Path | None,
        seed: int | None,
        output_family: str,
    ) -> Path:
        out_root = Path(output_dir) if output_dir else self.output_dir
        out_dir = out_root / ASSET_FAMILY_OUTPUT_DIRS[output_family]
        out_dir.mkdir(parents=True, exist_ok=True)
        seed_value = seed if seed is not None else (self.seed if self.seed is not None else 42)
        entries: list[dict[str, Any]] = []
        for index, prompt in enumerate(prompts):
            asset_seed = seed_value + index
            asset_name = self._make_name(prompt)
            mesh_path = self.generate_mesh(
                prompt=prompt, output_dir=out_dir, name=asset_name, seed=asset_seed
            )
            entry = {
                "name": asset_name,
                "prompt": prompt,
                "seed": asset_seed,
                "family": output_family,
                "manifest": f"{asset_name}.json",
                "files": {
                    "obj": mesh_path.name,
                    "mtl": f"{asset_name}.mtl",
                    "manifest": f"{asset_name}.json",
                },
                "content_target": "Content/Models",
            }
            entry["destination_map"] = {
                filename: entry["content_target"] for filename in entry["files"].values()
            }
            entries.append(entry)
        return self._write_pack_manifest(
            pack_name, out_dir, entries, style_profile=DEFAULT_STYLE_PROFILE
        )

    def _generate_ui_pack(
        self,
        pack_name: str,
        prompts: list[str],
        output_dir: str | Path | None,
        seed: int | None,
        family: str,
        generator: Any,
    ) -> Path:
        out_root = Path(output_dir) if output_dir else self.output_dir
        out_dir = out_root / ASSET_FAMILY_OUTPUT_DIRS[family]
        out_dir.mkdir(parents=True, exist_ok=True)
        seed_value = seed if seed is not None else (self.seed if self.seed is not None else 42)
        entries: list[dict[str, Any]] = []
        for index, prompt in enumerate(prompts):
            asset_seed = seed_value + index
            asset_name = self._make_name(prompt)
            png_path = generator(
                prompt=prompt, seed=asset_seed, output_dir=out_dir, name=asset_name
            )
            entry = {
                "name": asset_name,
                "prompt": prompt,
                "seed": asset_seed,
                "family": family,
                "manifest": f"{asset_name}.json",
                "files": {"image": png_path.name, "manifest": f"{asset_name}.json"},
                "content_target": "Content/UI",
            }
            entry["destination_map"] = {
                filename: entry["content_target"] for filename in entry["files"].values()
            }
            entries.append(entry)
        return self._write_pack_manifest(
            pack_name, out_dir, entries, style_profile=DEFAULT_STYLE_PROFILE
        )

    def _generate_tileset_pack(
        self,
        pack_name: str,
        prompts: list[str],
        output_dir: str | Path | None,
        seed: int | None,
    ) -> Path:
        out_root = Path(output_dir) if output_dir else self.output_dir
        out_dir = out_root / ASSET_FAMILY_OUTPUT_DIRS[ASSET_FAMILY_TILESETS]
        out_dir.mkdir(parents=True, exist_ok=True)
        seed_value = seed if seed is not None else (self.seed if self.seed is not None else 42)
        entries: list[dict[str, Any]] = []
        for index, prompt in enumerate(prompts):
            asset_seed = seed_value + index
            theme = resolve_tileset_theme(prompt)
            spec = tileset_spec_for_theme(theme)
            asset_name = self._make_name(prompt)
            narrative_tags = extract_narrative_tags(tokenize_prompt(prompt))
            manifest = {
                "version": "1.1",
                "asset_family": ASSET_FAMILY_TILESETS,
                "family": ASSET_FAMILY_TILESETS,
                "name": asset_name,
                "prompt": prompt,
                "seed": asset_seed,
                "theme": theme,
                "tileset": spec["id"],
                "tileset_meta": {
                    "id": spec["id"],
                    "name": spec["name"],
                    "tileSize": spec["tile_size"],
                    "style": spec["style"],
                },
                "tiles": spec["tiles"],
                "narrative_tags": narrative_tags,
                "world_region_id": infer_world_region_id(narrative_tags),
                "exploration_intent": infer_exploration_intent(narrative_tags),
                "placement_intent": infer_placement_intent(ASSET_FAMILY_TILESETS, narrative_tags),
                "content_target": {"world": "Content/World"},
                "style_profile": DEFAULT_STYLE_PROFILE,
            }
            write_manifest_json(out_dir, asset_name, manifest)
            entry = {
                "name": asset_name,
                "prompt": prompt,
                "seed": asset_seed,
                "family": ASSET_FAMILY_TILESETS,
                "manifest": f"{asset_name}.json",
                "files": {"manifest": f"{asset_name}.json"},
                "content_target": "Content/World",
            }
            entry["destination_map"] = {f"{asset_name}.json": entry["content_target"]}
            entries.append(entry)
        return self._write_pack_manifest(
            pack_name, out_dir, entries, style_profile=DEFAULT_STYLE_PROFILE
        )

    def _build_bundle_completeness_matrix(
        self, pack_manifests: list[dict[str, Any]], destination_map: dict[str, str]
    ) -> dict[str, Any]:
        manifests_by_name = {str(manifest.get("name", "")): manifest for manifest in pack_manifests}
        required_packs = list(GAME_REWRITTEN_BUNDLE_RECIPE["required_packs"])
        missing_required_packs = sorted(
            pack_name for pack_name in required_packs if pack_name not in manifests_by_name
        )

        per_pack: dict[str, dict[str, Any]] = {}
        underfilled_packs: list[dict[str, Any]] = []
        for pack_name in required_packs:
            expected_min = int(_BUNDLE_MIN_COUNTS_BY_PACK.get(pack_name, 0))
            manifest = manifests_by_name.get(pack_name)
            actual = len(manifest.get("assets", [])) if isinstance(manifest, dict) else 0
            meets_minimum = actual >= expected_min
            per_pack[pack_name] = {
                "expected_min": expected_min,
                "actual": actual,
                "meets_minimum": meets_minimum,
            }
            if manifest is not None and not meets_minimum:
                underfilled_packs.append(
                    {"name": pack_name, "expected_min": expected_min, "actual": actual}
                )

        destination_targets = set(destination_map.values())
        missing_destination_targets = sorted(
            target for target in _REQUIRED_BUNDLE_DESTINATION_TARGETS if target not in destination_targets
        )

        complete = (
            not missing_required_packs
            and not underfilled_packs
            and not missing_destination_targets
        )
        return {
            "complete": complete,
            "required_packs": required_packs,
            "missing_required_packs": missing_required_packs,
            "per_pack": per_pack,
            "underfilled_packs": underfilled_packs,
            "required_destination_targets": sorted(_REQUIRED_BUNDLE_DESTINATION_TARGETS),
            "missing_destination_targets": missing_destination_targets,
        }

    def _write_pack_manifest(
        self, pack_name: str, output_dir: Path, entries: list[dict[str, Any]], *, style_profile: str
    ) -> Path:
        destination_map: dict[str, str] = {}
        for entry in entries:
            destination_map.update(entry.get("destination_map", {}))
        manifest = build_manifest(
            asset_family=pack_name,
            prompt=pack_name.replace("_", " "),
            seed=entries[0]["seed"] if entries else 42,
            files={entry["name"]: entry["manifest"] for entry in entries},
            source_generator="creation_engine.engine.CreationEngine",
            tags=[entry["family"] for entry in entries],
            content_target={entry["family"]: entry["content_target"] for entry in entries},
            name=pack_name,
            style_profile=style_profile,
            assets=entries,
            destination_map=destination_map,
        )
        return write_manifest_json(output_dir, pack_name, manifest)


def json_load(file_obj: Any) -> Any:
    import json

    return json.load(file_obj)
