from pathlib import Path

import numpy as np


def export_obj(
    mesh_data: dict,
    output_dir: Path,
    name: str,
) -> Path:
    """Export mesh to Wavefront OBJ format.

    Parameters
    ----------
    mesh_data:
        Dict with keys: vertices, indices, normals, uvs
    output_dir:
        Output directory
    name:
        Asset name

    Returns
    -------
    Path
        Written OBJ file path
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    path = output_dir / f"{name}.obj"

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {name}\n")

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

        for i in range(0, len(indices), 3):
            i1, i2, i3 = indices[i] + 1, indices[i + 1] + 1, indices[i + 2] + 1
            f.write(f"f {i1} {i2} {i3}\n")

    return path
