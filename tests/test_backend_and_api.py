import json

import numpy as np
import pytest
from creation_engine.backend import BackendRegistry, ProceduralBackend
from creation_engine.engine import CreationEngine
from creation_engine.export.map_exporter import export_tilemap
from creation_engine.map.map_gen import _generate_coast_layout, _pick_theme, generate_tilemap
from creation_engine.map.tileset_specs import TILESET_SPECS


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
    assert manifest["shader"] == "Shaders/basic3d"
    assert "color" in manifest["params"]
    assert "baseColor" in manifest["params"]
    assert manifest["content_target"]["material"] == "Content/Materials"
    assert manifest["content_target"]["textures"] == "Content/Textures"

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

    mesh_file = engine.generate_mesh("pillar", complexity="low")
    assert mesh_file.exists()
    assert mesh_file.suffix == ".obj"


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
