import json

import numpy as np
import pytest
from creation_engine.backend import BackendRegistry, ProceduralBackend
from creation_engine.engine import CreationEngine
from creation_engine.export.map_exporter import export_tilemap
from creation_engine.narrative_tags import extract_narrative_tags
from creation_engine.map.map_gen import _generate_coast_layout, _pick_theme, generate_tilemap
from creation_engine.map.tileset_specs import TILESET_SPECS
from creation_engine.texture.palette import select_palette


def test_backend_registry_procedural_available():
    assert "procedural" in BackendRegistry.available()
    backend = BackendRegistry.create("procedural", seed=42)
    assert isinstance(backend, ProceduralBackend)


def test_engine_generates_assets(tmp_path):
    engine = CreationEngine(output_dir=tmp_path)

    tex_dir = engine.generate_texture("stone", width=8, height=8)
    assert (tex_dir / "stone_albedo.png").exists()
    assert (tex_dir / "stone_normal.png").exists()
    manifest_path = tex_dir / "stone.json"
    assert manifest_path.exists()
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["shader"] == "Shaders/pbr_3d"
    assert "color" in manifest["params"]
    assert "baseColor" in manifest["params"]
    assert manifest["content_target"]["material"] == "Content/Materials"
    assert manifest["content_target"]["textures"] == "Content/Textures"
    assert manifest["style_profile"] == "ps2_ff7_ff12_highest_quality_ps2"
    assert manifest["asset_family"] == manifest["family"]

    map_file = engine.generate_map("forest", width=8, height=8)
    assert map_file.exists()
    assert map_file.name == "forest.json"
    with open(map_file, encoding="utf-8") as f:
        map_manifest = json.load(f)
    assert map_manifest["map_family"] == "world"
    assert map_manifest["theme"] == "forest"
    assert map_manifest["tileset_meta"]["id"] == map_manifest["tileset"]
    assert map_manifest["content_target"]["world"] == "Content/World"
    assert map_manifest["summary"]["prop_count"] >= 0
    assert map_manifest["chunk"] == {"x": 0, "y": 0}

    mesh_file = engine.generate_mesh("pillar", complexity="low")
    assert mesh_file.exists()
    assert mesh_file.suffix == ".obj"
    assert (mesh_file.parent / "pillar.mtl").exists()
    assert (mesh_file.parent / "pillar.json").exists()
    with open(mesh_file.parent / "pillar.json", encoding="utf-8") as f:
        mesh_manifest = json.load(f)
    assert mesh_manifest["content_target"]["model"] == "Content/Models"
    assert mesh_manifest["style_profile"] == "ps2_ff7_ff12_highest_quality_ps2"
    assert "lod_policy" in mesh_manifest
    assert mesh_manifest["complexity"] == "low"
    assert isinstance(mesh_manifest["vertex_count"], int)
    assert isinstance(mesh_manifest["triangle_count"], int)


def test_engine_pack_generation(tmp_path):
    engine = CreationEngine(output_dir=tmp_path)
    pack_manifest = engine.generate_material_pack(seed=7)
    assert pack_manifest.exists()
    with open(pack_manifest, encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["assets"]
    assert manifest["destination_map"]
    assert manifest["content_target"]["materials"] == "Content/Materials"
    assert manifest["style_profile"] == "ps2_ff7_ff12_highest_quality_ps2"


def test_single_assets_create_downloadable_export_bundles(tmp_path):
    engine = CreationEngine(output_dir=tmp_path)
    engine.generate_texture("stone", width=8, height=8)
    engine.generate_map("forest", width=8, height=8)
    mesh_path = engine.generate_mesh("pillar", complexity="low")
    engine.generate_ui_icon("quest icon", seed=11)

    texture_bundle = tmp_path / "export" / "props" / "stone"
    assert (texture_bundle / "stone_albedo.png").exists()
    assert (texture_bundle / "stone.json").exists()

    map_bundle = tmp_path / "export" / "maps" / "forest"
    assert (map_bundle / "forest.json").exists()
    assert (map_bundle / "forest_preview.png").exists()

    mesh_bundle = tmp_path / "export" / mesh_path.parent.name / "pillar"
    assert (mesh_bundle / "pillar.obj").exists()
    assert (mesh_bundle / "pillar.mtl").exists()
    assert (mesh_bundle / "pillar.json").exists()
    assert (mesh_bundle / "pillar_preview.png").exists()

    icon_bundle = tmp_path / "export" / "ui_icons" / "quest_icon"
    assert (icon_bundle / "quest_icon.png").exists()
    assert (icon_bundle / "quest_icon.json").exists()

    with open(tmp_path / "export" / "index.json", encoding="utf-8") as f:
        export_index = json.load(f)
    exports = {(item["family"], item["name"]) for item in export_index["exports"]}
    assert ("props", "stone") in exports
    assert ("maps", "forest") in exports
    assert (mesh_path.parent.name, "pillar") in exports
    assert ("ui_icons", "quest_icon") in exports


def test_full_bundle_manifest_includes_completeness_matrix(tmp_path):
    engine = CreationEngine(output_dir=tmp_path)
    bundle_manifest_path = engine.generate_full_bundle(seed=19)
    with open(bundle_manifest_path, encoding="utf-8") as f:
        bundle_manifest = json.load(f)

    matrix = bundle_manifest["completeness_matrix"]
    assert matrix["complete"] is True
    assert matrix["missing_required_packs"] == []
    assert matrix["underfilled_packs"] == []
    assert matrix["missing_destination_targets"] == []
    assert matrix["per_pack"]["material_pack"]["meets_minimum"] is True


def test_ui_manifest_contains_narrative_metadata(tmp_path):
    engine = CreationEngine(output_dir=tmp_path)
    icon_path = engine.generate_ui_icon("ps2 jrpg imperial quest icon", seed=5)
    with open(icon_path.with_suffix(".json"), encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["narrative_tags"]["faction"] == "imperial"
    assert manifest["world_region_id"]
    assert manifest["exploration_intent"]
    assert manifest["placement_intent"] == "ui_symbol"


def test_export_tilemap_unknown_theme_falls_back_to_overworld_tileset(tmp_path):
    map_file = export_tilemap(
        map_data={"tiles": np.array([[1, 2], [3, 4]], dtype=np.int32), "theme": "unknown_theme"},
        output_dir=tmp_path,
        name="unknown_theme_map",
        prompt="unknown",
        seed=1,
    )
    with open(map_file, encoding="utf-8") as f:
        exported = json.load(f)
    assert exported["tileset"] == TILESET_SPECS["overworld"]["id"]


def test_export_tilemap_uses_explicit_tileset_metadata_when_known(tmp_path):
    explicit_tileset_id = TILESET_SPECS["dungeon"]["id"]
    map_file = export_tilemap(
        map_data={
            "tiles": np.array([[1, 2], [3, 4]], dtype=np.int32),
            "theme": "forest",
            "tileset": explicit_tileset_id,
        },
        output_dir=tmp_path,
        name="explicit_tileset_map",
        prompt="explicit tileset",
        seed=1,
    )
    with open(map_file, encoding="utf-8") as f:
        exported = json.load(f)
    assert exported["tileset"] == explicit_tileset_id
    assert exported["tileset_meta"]["id"] == explicit_tileset_id


def test_generate_tilemap_rejects_non_positive_dimensions():
    with pytest.raises(ValueError, match="width and height must be >= 1"):
        generate_tilemap("forest", width=0, height=8, seed=1)


def test_coast_layout_clamps_shoreline_before_grass_mask():
    class StubRng:
        def random(self, shape):
            return np.full(shape, 0.9)

        def integers(self, low, high):
            return -2

    tiles = _generate_coast_layout(width=3, height=2, rng=StubRng())
    assert np.all(tiles[:, 0] == 2)


def test_pick_theme_maps_ruin_to_ruins():
    assert _pick_theme("ruin") == "ruins"


def test_extract_narrative_tags_is_stable_for_duplicate_family_tokens():
    tokens = ["coast", "forest", "desert", "royal"]
    assert extract_narrative_tags(tokens)["region"] == "coast"


def test_export_tilemap_prefers_existing_narrative_metadata(tmp_path):
    provided_tags = {
        "region": "temple",
        "faction": "rebel",
        "era": "ancient",
        "story_phase": "endgame",
        "culture_theme": "sacred",
    }
    map_file = export_tilemap(
        map_data={
            "tiles": np.array([[1, 2], [3, 4]], dtype=np.int32),
            "narrative_tags": provided_tags,
            "world_region_id": "custom_region",
            "exploration_intent": "dungeon_exploration",
            "chunk": {"x": 2, "y": -1},
        },
        output_dir=tmp_path,
        name="narrative_map",
        prompt="forest map",
        seed=1,
    )
    with open(map_file, encoding="utf-8") as f:
        exported = json.load(f)
    assert exported["narrative_tags"] == provided_tags
    assert exported["world_region_id"] == "custom_region"
    assert exported["exploration_intent"] == "dungeon_exploration"
    assert exported["chunk"] == {"x": 2, "y": -1}


def test_select_palette_holy_uses_holy_family():
    holy_palette = select_palette("holy", 7)
    sacred_palette = select_palette("sacred", 7)
    assert not np.array_equal(holy_palette, sacred_palette)
