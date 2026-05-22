from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from creation_engine.export.manifest_exporter import (
    DEFAULT_STYLE_PROFILE,
    build_manifest,
    write_manifest_json,
)
from creation_engine.narrative_tags import (
    extract_narrative_tags,
    infer_exploration_intent,
    infer_placement_intent,
    infer_world_region_id,
)
from creation_engine.prompting import tokenize_prompt


def export_obj(
    mesh_data: dict,
    output_dir: Path,
    name: str,
) -> Path:
    """Export mesh to Wavefront OBJ, MTL, and JSON manifest."""
    output_dir.mkdir(parents=True, exist_ok=True)

    path = output_dir / f"{name}.obj"
    mtl_path = output_dir / f"{name}.mtl"
    material_slots = list(mesh_data.get("material_slots") or [mesh_data.get("family", "material")])

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {name}\n")
        f.write(f"mtllib {mtl_path.name}\n")

        vertices = mesh_data["vertices"]
        for v in vertices:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

        normals = mesh_data.get("normals")
        if normals is not None:
            for n in normals:
                f.write(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")

        uvs = mesh_data.get("uvs")
        if uvs is not None:
            for uv in uvs:
                f.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")

        indices = mesh_data["indices"]
        if isinstance(indices, np.ndarray):
            indices = indices.reshape(-1).tolist()

        if len(indices) % 3 != 0:
            raise ValueError(
                f"Index buffer length {len(indices)} is not a multiple of 3; "
                "only triangulated meshes are supported."
            )

        has_uvs = uvs is not None
        has_normals = normals is not None
        f.write(f"usemtl {material_slots[0]}\n")
        for i in range(0, len(indices), 3):
            i1, i2, i3 = indices[i] + 1, indices[i + 1] + 1, indices[i + 2] + 1
            if has_uvs and has_normals:
                f.write(f"f {i1}/{i1}/{i1} {i2}/{i2}/{i2} {i3}/{i3}/{i3}\n")
            elif has_normals:
                f.write(f"f {i1}//{i1} {i2}//{i2} {i3}//{i3}\n")
            elif has_uvs:
                f.write(f"f {i1}/{i1} {i2}/{i2} {i3}/{i3}\n")
            else:
                f.write(f"f {i1} {i2} {i3}\n")

    _write_mtl(mtl_path, material_slots, mesh_data)
    prompt_text = str(mesh_data.get("prompt", ""))
    narrative_tags = extract_narrative_tags(tokenize_prompt(prompt_text))

    extra_manifest_fields = {
        key: mesh_data[key]
        for key in (
            "lod_policy",
            "complexity",
            "complexity_policy",
            "vertex_count",
            "triangle_count",
        )
        if key in mesh_data
    }

    manifest = build_manifest(
        asset_family=str(mesh_data.get("family", "meshes")),
        prompt=prompt_text,
        seed=mesh_data.get("seed", 42),
        files={
            "obj": path.name,
            "mtl": mtl_path.name,
            "manifest": f"{name}.json",
        },
        source_generator=str(
            mesh_data.get(
                "source_generator", "creation_engine.backend.ProceduralBackend.generate_mesh"
            )
        ),
        tags=[str(mesh_data.get("family", "meshes")), str(mesh_data.get("variant", ""))],
        content_target=mesh_data.get(
            "content_target",
            {"model": "Content/Models", "materials": "Content/Materials"},
        ),
        name=name,
        style_profile=str(mesh_data.get("style_profile", DEFAULT_STYLE_PROFILE)),
        material_slots=material_slots,
        narrative_tags=narrative_tags,
        world_region_id=mesh_data.get("world_region_id", infer_world_region_id(narrative_tags)),
        exploration_intent=mesh_data.get(
            "exploration_intent", infer_exploration_intent(narrative_tags)
        ),
        placement_intent=mesh_data.get(
            "placement_intent",
            infer_placement_intent(str(mesh_data.get("family", "meshes")), narrative_tags),
        ),
        **extra_manifest_fields,
    )
    write_manifest_json(output_dir, name, manifest)

    return path


def _write_mtl(mtl_path: Path, material_slots: list[str], mesh_data: dict) -> None:
    with open(mtl_path, "w", encoding="utf-8") as file:
        for slot in material_slots:
            digest = hashlib.sha1(f"{slot}:{mesh_data.get('variant', '')}".encode("utf-8")).digest()
            r, g, b = (component / 255.0 for component in digest[:3])
            file.write(f"newmtl {slot}\n")
            file.write("Ka 0.100 0.100 0.100\n")
            file.write(f"Kd {r:.3f} {g:.3f} {b:.3f}\n")
            file.write("Ks 0.000 0.000 0.000\n")
            file.write("d 1.000\n")
            file.write("illum 2\n\n")
