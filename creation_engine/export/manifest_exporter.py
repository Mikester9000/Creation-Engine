from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_STYLE_PROFILE = "ps2_ff7_ff12_highest_quality_ps2"

# All assets in this engine target a full 3D game pipeline.
ASSET_DIMENSION = "3d"
RENDER_PIPELINE = "3d_pbr"
COORDINATE_SPACE = "Y_up"


def build_manifest(
    *,
    asset_family: str,
    prompt: str,
    seed: int | None,
    files: dict[str, str],
    source_generator: str,
    tags: dict[str, list[str]] | list[str] | None = None,
    content_target: dict[str, str] | None = None,
    name: str | None = None,
    version: str = "1.0",
    style_profile: str = DEFAULT_STYLE_PROFILE,
    **extra: Any,
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "version": version,
        "asset_family": asset_family,
        "family": asset_family,
        "name": name or asset_family,
        "prompt": prompt,
        "seed": 42 if seed is None else int(seed),
        "files": files,
        "tags": tags or [],
        "source_generator": source_generator,
        "content_target": content_target or {},
        "style_profile": style_profile,
        # 3D enforcement: every generated asset targets the 3D PBR pipeline.
        "asset_dimension": ASSET_DIMENSION,
        "render_pipeline": RENDER_PIPELINE,
        "coordinate_space": COORDINATE_SPACE,
    }
    manifest.update(extra)
    return manifest


def write_manifest_json(output_dir: Path, name: str, manifest: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{name}.json"
    with open(path, "w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)
    return path
