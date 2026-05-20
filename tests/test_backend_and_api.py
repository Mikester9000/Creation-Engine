import json

from creation_engine.backend import BackendRegistry, ProceduralBackend
from creation_engine.engine import CreationEngine


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

    mesh_file = engine.generate_mesh("pillar", complexity="low")
    assert mesh_file.exists()
    assert mesh_file.suffix == ".obj"
