import json
from pathlib import Path

import numpy as np
from PIL import Image


def export_pbr_textures(
    texture_data: dict[str, np.ndarray],
    output_dir: Path,
    name: str,
    prompt: str = "",
    seed: int | None = None,
    family: str = "materials",
    width: int | None = None,
    height: int | None = None,
) -> Path:
    """Export PBR texture maps to PNG files.

    Parameters
    ----------
    texture_data:
        Dict with keys: albedo, normal, roughness, metallic, ao, emissive
    output_dir:
        Output directory
    name:
        Asset name prefix

    Returns
    -------
    Path
        Output directory path
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    files: dict[str, str] = {}
    for channel, data in texture_data.items():
        if data.dtype == np.float32:
            data = (data * 255).clip(0, 255).astype(np.uint8)

        img = Image.fromarray(data)
        filename = f"{name}_{channel}.png"
        img.save(output_dir / filename)
        files[channel] = filename

    if width is None or height is None:
        sample = texture_data.get("albedo")
        if sample is not None:
            height = int(sample.shape[0])
            width = int(sample.shape[1])
        else:
            height = 0
            width = 0

    albedo = texture_data.get("albedo")
    if albedo is None:
        color = [1.0, 1.0, 1.0, 1.0]
    else:
        mean = np.mean(albedo.astype(np.float32) / 255.0, axis=(0, 1))
        color = [round(float(mean[0]), 4), round(float(mean[1]), 4), round(float(mean[2]), 4), 1.0]

    manifest = {
        "version": "1.1",
        "name": name,
        "family": family,
        "prompt": prompt,
        "seed": 42 if seed is None else int(seed),
        "width": int(width),
        "height": int(height),
        "shader": "Shaders/basic3d",
        "channels": sorted(files.keys()),
        "textures": files,
        "params": {
            "color": color,
            "baseColor": list(color),
        },
        "content_target": {
            "material": "Content/Materials",
            "textures": "Content/Textures",
        },
    }
    with open(output_dir / f"{name}.json", "w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)

    return output_dir
