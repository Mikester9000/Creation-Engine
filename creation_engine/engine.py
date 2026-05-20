from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from creation_engine.backend import AssetBackend, BackendRegistry
from creation_engine.export.map_exporter import export_tilemap
from creation_engine.export.mesh_exporter import export_obj
from creation_engine.export.texture_exporter import export_pbr_textures


class CreationEngine:
    def __init__(
        self,
        backend: str | AssetBackend = "procedural",
        seed: int | None = None,
        output_dir: str | Path = "assets",
    ) -> None:
        self.seed = seed
        self.output_dir = Path(output_dir)

        if isinstance(backend, AssetBackend):
            self.backend = backend
        else:
            self.backend = BackendRegistry.create(backend, seed=seed)

    def generate_texture(
        self,
        prompt: str,
        width: int = 64,
        height: int = 64,
        output_dir: str | Path | None = None,
        name: str | None = None,
        **kwargs: Any,
    ) -> Path:
        out_dir = Path(output_dir) if output_dir else self.output_dir / "materials"
        asset_name = name or self._make_name(prompt)
        seed = kwargs.pop("seed", self.seed)
        texture_data = self.backend.generate_texture(
            prompt=prompt,
            width=width,
            height=height,
            seed=seed,
            **kwargs,
        )
        return export_pbr_textures(texture_data=texture_data, output_dir=out_dir, name=asset_name)

    def generate_map(
        self,
        prompt: str,
        width: int = 64,
        height: int = 64,
        output_dir: str | Path | None = None,
        name: str | None = None,
        **kwargs: Any,
    ) -> Path:
        out_dir = Path(output_dir) if output_dir else self.output_dir / "maps"
        asset_name = name or self._make_name(prompt)
        seed = kwargs.pop("seed", self.seed)
        map_data = self.backend.generate_map(
            prompt=prompt,
            width=width,
            height=height,
            seed=seed,
            **kwargs,
        )
        return export_tilemap(
            map_data=map_data,
            output_dir=out_dir,
            name=asset_name,
            prompt=prompt,
            seed=seed,
        )

    def generate_mesh(
        self,
        prompt: str,
        complexity: str = "medium",
        output_dir: str | Path | None = None,
        name: str | None = None,
        **kwargs: Any,
    ) -> Path:
        out_dir = Path(output_dir) if output_dir else self.output_dir / "meshes"
        asset_name = name or self._make_name(prompt)
        mesh_data = self.backend.generate_mesh(
            prompt=prompt,
            complexity=complexity,
            seed=kwargs.pop("seed", self.seed),
            **kwargs,
        )
        return export_obj(mesh_data=mesh_data, output_dir=out_dir, name=asset_name)

    @staticmethod
    def _make_name(prompt: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", prompt.lower()).strip("_")
        return slug or "asset"
