from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class AssetBackend(ABC):
    @abstractmethod
    def generate_texture(
        self,
        prompt: str,
        width: int,
        height: int,
        **kwargs: Any,
    ) -> dict[str, np.ndarray]:
        raise NotImplementedError

    @abstractmethod
    def generate_mesh(
        self,
        prompt: str,
        complexity: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def generate_map(
        self,
        prompt: str,
        width: int,
        height: int,
        **kwargs: Any,
    ) -> dict[str, Any]:
        raise NotImplementedError


class ProceduralBackend(AssetBackend):
    def __init__(self, seed: int | None = None) -> None:
        self.seed = seed

    def generate_texture(
        self,
        prompt: str,
        width: int,
        height: int,
        **kwargs: Any,
    ) -> dict[str, np.ndarray]:
        from creation_engine.texture.texture_gen import generate_pbr_textures

        seed_value = kwargs.get("seed", self.seed)
        seed = int(42 if seed_value is None else seed_value)
        return generate_pbr_textures(prompt=prompt, width=width, height=height, seed=seed)

    def generate_mesh(
        self,
        prompt: str,
        complexity: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        del prompt
        detail = {"low": 1.0, "medium": 1.5, "high": 2.0}.get(complexity, 1.5)
        size = detail

        vertices = np.array(
            [
                [-size, -size, -size],
                [size, -size, -size],
                [size, size, -size],
                [-size, size, -size],
                [-size, -size, size],
                [size, -size, size],
                [size, size, size],
                [-size, size, size],
            ],
            dtype=np.float32,
        )
        indices = np.array(
            [
                0,
                1,
                2,
                0,
                2,
                3,
                4,
                6,
                5,
                4,
                7,
                6,
                0,
                4,
                5,
                0,
                5,
                1,
                1,
                5,
                6,
                1,
                6,
                2,
                2,
                6,
                7,
                2,
                7,
                3,
                3,
                7,
                4,
                3,
                4,
                0,
            ],
            dtype=np.int32,
        )

        normals = vertices / np.clip(np.linalg.norm(vertices, axis=1, keepdims=True), 1e-6, None)
        uvs = np.array(
            [
                [0.0, 0.0],
                [1.0, 0.0],
                [1.0, 1.0],
                [0.0, 1.0],
                [0.0, 0.0],
                [1.0, 0.0],
                [1.0, 1.0],
                [0.0, 1.0],
            ],
            dtype=np.float32,
        )

        return {
            "vertices": vertices,
            "indices": indices,
            "normals": normals,
            "uvs": uvs,
        }

    def generate_map(
        self,
        prompt: str,
        width: int,
        height: int,
        **kwargs: Any,
    ) -> dict[str, Any]:
        from creation_engine.map.map_gen import generate_tilemap

        seed_value = kwargs.get("seed", self.seed)
        seed = int(42 if seed_value is None else seed_value)
        return generate_tilemap(prompt=prompt, width=width, height=height, seed=seed)


class BackendRegistry:
    _registry: dict[str, type[AssetBackend]] = {}

    @classmethod
    def register(cls, name: str, backend: type[AssetBackend]) -> None:
        cls._registry[name] = backend

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> AssetBackend:
        if name not in cls._registry:
            available = ", ".join(sorted(cls._registry))
            raise ValueError(f"Unknown backend '{name}'. Available backends: {available}")
        return cls._registry[name](**kwargs)

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._registry.keys())


BackendRegistry.register("procedural", ProceduralBackend)
