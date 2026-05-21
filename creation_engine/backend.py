from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
from creation_engine.mesh.mesh_builder import build_mesh_from_prompt


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
        seed_value = kwargs.get("seed", self.seed)
        seed = int(42 if seed_value is None else seed_value)
        return build_mesh_from_prompt(prompt=prompt, complexity=complexity, seed=seed)

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
