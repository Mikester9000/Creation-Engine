from pathlib import Path

import numpy as np
from PIL import Image


def export_pbr_textures(
    texture_data: dict[str, np.ndarray],
    output_dir: Path,
    name: str,
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

    for channel, data in texture_data.items():
        if data.dtype == np.float32:
            data = (data * 255).clip(0, 255).astype(np.uint8)

        img = Image.fromarray(data)
        img.save(output_dir / f"{name}_{channel}.png")

    return output_dir
