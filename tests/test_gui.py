import json

import pytest

from creation_engine.engine import CreationEngine
from creation_engine.gui import (
    CreationEngineGuiApp,
    _filter_file_index,
    render_map_3d_preview,
    render_map_preview,
    render_material_preview,
    render_obj_preview,
    render_preview_from_json,
)


def test_render_map_preview_from_exported_map(tmp_path):
    engine = CreationEngine(output_dir=tmp_path)
    map_path = engine.generate_map("forest river", width=8, height=8)
    with open(map_path, encoding="utf-8") as f:
        map_data = json.load(f)

    image = render_map_preview(map_data, tile_px=4)
    assert image.width == map_data["width"] * 4
    assert image.height == map_data["height"] * 4


def test_render_map_3d_preview_from_exported_map(tmp_path):
    engine = CreationEngine(output_dir=tmp_path)
    map_path = engine.generate_map("forest river", width=8, height=8)
    with open(map_path, encoding="utf-8") as f:
        map_data = json.load(f)

    image = render_map_3d_preview(map_data, tile_px=12)
    assert image.width > 0
    assert image.height > 0


def test_render_map_3d_preview_rejects_too_small_tile_size():
    with pytest.raises(ValueError, match="tile_px"):
        render_map_3d_preview({"width": 1, "height": 1, "tiles": [0]}, tile_px=1)


def test_gui_path_guard_stays_inside_output_dir(tmp_path):
    app = CreationEngineGuiApp.__new__(CreationEngineGuiApp)
    app.output_dir = tmp_path

    assert app._is_within_output_dir(tmp_path / "materials" / "new_asset.json")
    assert not app._is_within_output_dir(tmp_path.parent / "outside.json")


def test_filter_file_index_and_selection_mapping(tmp_path):
    app = CreationEngineGuiApp.__new__(CreationEngineGuiApp)
    app.output_dir = tmp_path

    (tmp_path / "alpha.json").write_text("{}", encoding="utf-8")
    (tmp_path / "beta.json").write_text("{}", encoding="utf-8")

    app.file_index = [tmp_path / "alpha.json", tmp_path / "beta.json"]
    filtered = _filter_file_index(app.file_index, app.output_dir, "alpha")
    assert [path.name for path in filtered] == ["alpha.json"]

    app._filtered_index = filtered

    class _DummyList:
        def curselection(self):
            return (0,)

    loaded_paths = []
    app.file_list = _DummyList()
    app.load_file = loaded_paths.append
    app.open_selected_file()
    assert loaded_paths == [tmp_path / "alpha.json"]


def test_render_material_preview_from_exported_manifest(tmp_path):
    engine = CreationEngine(output_dir=tmp_path)
    texture_dir = engine.generate_texture("wet stone", width=16, height=16)
    manifest_path = texture_dir / "wet_stone.json"
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    image = render_material_preview(manifest, manifest_path)
    assert image.width == 16
    assert image.height == 16


def test_render_preview_from_textures_manifest(tmp_path):
    engine = CreationEngine(output_dir=tmp_path)
    texture_dir = engine.generate_texture("wet stone", width=16, height=16)
    manifest_path = texture_dir / "wet_stone.json"
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    manifest["textures"] = manifest.pop("files")
    image = render_preview_from_json(manifest, manifest_path)
    assert image.width == 16
    assert image.height == 16


def test_render_preview_from_map_json_in_3d_mode(tmp_path):
    engine = CreationEngine(output_dir=tmp_path)
    map_path = engine.generate_map("forest river", width=8, height=8)
    with open(map_path, encoding="utf-8") as f:
        map_data = json.load(f)

    image = render_preview_from_json(map_data, map_path, use_3d_view=True)
    assert image.width > map_data["width"]
    assert image.height > map_data["height"]


def test_render_obj_preview_wireframe():
    obj_text = "\n".join(
        [
            "v -0.5 -0.5 -0.5",
            "v 0.5 -0.5 -0.5",
            "v 0.5 0.5 -0.5",
            "v -0.5 0.5 -0.5",
            "v -0.5 -0.5 0.5",
            "v 0.5 -0.5 0.5",
            "v 0.5 0.5 0.5",
            "v -0.5 0.5 0.5",
            "f 1 2 3 4",
            "f 5 6 7 8",
            "f 1 2 6 5",
            "f 2 3 7 6",
            "f 3 4 8 7",
            "f 4 1 5 8",
        ]
    )
    image = render_obj_preview(obj_text, size=(320, 320))
    assert image.width == 320
    assert image.height == 320
