from pathlib import Path

import numpy as np
from PIL import Image

from creation_engine.export.manifest_exporter import (
    DEFAULT_STYLE_PROFILE,
    build_manifest,
    write_manifest_json,
)
from creation_engine.narrative_tags import infer_placement_intent
from creation_engine.prompting import classify_prompt


def export_pbr_textures(
    texture_data: dict[str, np.ndarray],
    output_dir: Path,
    name: str,
    prompt: str = "",
    seed: int | None = None,
    family: str = "materials",
    width: int | None = None,
    height: int | None = None,
    parsed_prompt: dict[str, object] | None = None,
) -> Path:
    """Export PBR texture maps to PNG files."""
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

    parsed = parsed_prompt or classify_prompt(prompt)
    narrative_tags = parsed["narrative_tags"]
    manifest = build_manifest(
        asset_family=family,
        prompt=prompt,
        seed=seed,
        files=files,
        source_generator="creation_engine.texture.texture_gen.generate_pbr_textures",
        tags=[],
        content_target={
            "material": "Content/Materials",
            "textures": "Content/Textures",
        },
        name=name,
        style_profile=DEFAULT_STYLE_PROFILE,
        version="1.1",
        shader="Shaders/basic3d",
        width=int(width),
        height=int(height),
        channels=sorted(files.keys()),
        textures=files,
        params={
            "color": color,
            "baseColor": list(color),
        },
        narrative_tags=narrative_tags,
        world_region_id=parsed["world_region_id"],
        exploration_intent=parsed["exploration_intent"],
        placement_intent=infer_placement_intent(family, narrative_tags),
    )
    write_manifest_json(output_dir, name, manifest)

    return output_dir
