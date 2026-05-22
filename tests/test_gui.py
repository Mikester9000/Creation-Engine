import json

from creation_engine.engine import CreationEngine
from creation_engine.gui import render_map_preview, render_material_preview


def test_render_map_preview_from_exported_map(tmp_path):
    engine = CreationEngine(output_dir=tmp_path)
    map_path = engine.generate_map("forest river", width=8, height=8)
    with open(map_path, encoding="utf-8") as f:
        map_data = json.load(f)

    image = render_map_preview(map_data, tile_px=4)
    assert image.width == map_data["width"] * 4
    assert image.height == map_data["height"] * 4


def test_render_material_preview_from_exported_manifest(tmp_path):
    engine = CreationEngine(output_dir=tmp_path)
    texture_dir = engine.generate_texture("wet stone", width=16, height=16)
    manifest_path = texture_dir / "wet_stone.json"
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    image = render_material_preview(manifest, manifest_path)
    assert image.width == 16
    assert image.height == 16
