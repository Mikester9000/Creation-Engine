from __future__ import annotations

import math
from typing import Any

import numpy as np

from creation_engine.mesh.mesh_family_specs import (
    MESH_VARIANT_SPECS,
    resolve_mesh_family,
    resolve_mesh_variant,
)
from creation_engine.prompting import tokenize_prompt

_COMPLEXITY_SCALE = {"low": 0.85, "medium": 1.0, "high": 1.2}
_LOD_POLICY = {
    "props": {"lod0": 0, "lod1": 15, "lod2": 30},
    "architecture": {"lod0": 0, "lod1": 20, "lod2": 45},
    "foliage": {"lod0": 0, "lod1": 18, "lod2": 35},
    "items": {"lod0": 0, "lod1": 12, "lod2": 24},
    "characters_static": {"lod0": 0, "lod1": 16, "lod2": 32},
    "enemies_static": {"lod0": 0, "lod1": 16, "lod2": 32},
}
_COMPLEXITY_BUDGET = {
    "low": {"vertex_budget": 256, "part_jitter": 0.02},
    "medium": {"vertex_budget": 512, "part_jitter": 0.04},
    "high": {"vertex_budget": 1024, "part_jitter": 0.06},
}


def build_mesh_from_prompt(
    prompt: str, complexity: str = "medium", seed: int = 42
) -> dict[str, Any]:
    tokens = tokenize_prompt(prompt)
    family = resolve_mesh_family(tokens)
    variant = resolve_mesh_variant(family, tokens)
    return build_mesh_from_variant(variant, prompt=prompt, complexity=complexity, seed=seed)


def build_mesh_from_variant(
    variant: str,
    prompt: str = "",
    complexity: str = "medium",
    seed: int = 42,
) -> dict[str, Any]:
    spec = MESH_VARIANT_SPECS[variant]
    scale = _COMPLEXITY_SCALE.get(complexity, 1.0)
    complexity_policy = _COMPLEXITY_BUDGET.get(complexity, _COMPLEXITY_BUDGET["medium"])
    rng = np.random.default_rng(seed + sum(ord(ch) for ch in prompt.lower()) + len(variant) * 17)

    vertices: list[np.ndarray] = []
    indices: list[np.ndarray] = []
    normals: list[np.ndarray] = []
    uvs: list[np.ndarray] = []
    vertex_offset = 0

    for part in spec["parts"]:
        part_mesh = _make_primitive_mesh(
            part,
            scale=scale,
            rng=rng,
            jitter_scale=float(complexity_policy["part_jitter"]),
        )
        part_vertices = part_mesh["vertices"]
        part_indices = part_mesh["indices"] + vertex_offset
        vertices.append(part_vertices)
        indices.append(part_indices)
        normals.append(part_mesh["normals"])
        uvs.append(part_mesh["uvs"])
        vertex_offset += len(part_vertices)

    mesh_vertices = np.vstack(vertices).astype(np.float32)
    mesh_indices = np.concatenate(indices).astype(np.int32)
    mesh_normals = np.vstack(normals).astype(np.float32)
    mesh_uvs = np.vstack(uvs).astype(np.float32)

    return {
        "vertices": mesh_vertices,
        "indices": mesh_indices,
        "normals": mesh_normals,
        "uvs": mesh_uvs,
        "family": spec["family"],
        "variant": variant,
        "material_slots": list(spec["material_slots"]),
        "prompt": prompt,
        "seed": seed,
        "source_generator": "creation_engine.mesh.mesh_builder.build_mesh_from_prompt",
        "content_target": {
            "model": "Content/Models",
            "materials": "Content/Materials",
        },
        "lod_policy": _LOD_POLICY.get(spec["family"], {"lod0": 0, "lod1": 18, "lod2": 36}),
        "complexity": complexity,
        "complexity_policy": complexity_policy,
        "vertex_count": int(mesh_vertices.shape[0]),
        "triangle_count": int(mesh_indices.shape[0] // 3),
        # 3D enforcement: all meshes are authored in Y-up world space.
        "asset_dimension": "3d",
        "coordinate_space": "Y_up",
        "unit_scale": 1.0,
    }


def _make_primitive_mesh(
    part: dict[str, Any],
    scale: float,
    rng: np.random.Generator,
    jitter_scale: float = 0.04,
) -> dict[str, np.ndarray]:
    kind = part["kind"]
    offset = np.array(part.get("offset", (0.0, 0.0, 0.0)), dtype=np.float32)
    part_scale = np.array(part.get("scale", (1.0, 1.0, 1.0)), dtype=np.float32) * scale
    jitter = rng.uniform(-jitter_scale, jitter_scale, size=3).astype(np.float32)
    offset = offset + jitter

    if kind == "box":
        vertices, indices = _box_geometry()
    elif kind == "prism":
        vertices, indices = _prism_geometry(int(part.get("sides", 8)))
    elif kind == "pyramid":
        vertices, indices = _pyramid_geometry()
    elif kind == "pillar":
        vertices, indices = _prism_geometry(6)
    else:
        vertices, indices = _box_geometry()

    vertices = vertices * part_scale.reshape(1, 3) + offset.reshape(1, 3)
    normals = vertices / np.clip(np.linalg.norm(vertices, axis=1, keepdims=True), 1e-6, None)
    uvs = _box_uvs(vertices)
    return {
        "vertices": vertices.astype(np.float32),
        "indices": indices.astype(np.int32),
        "normals": normals.astype(np.float32),
        "uvs": uvs.astype(np.float32),
    }


def _box_geometry() -> tuple[np.ndarray, np.ndarray]:
    vertices = np.array(
        [
            [-0.5, -0.5, -0.5],
            [0.5, -0.5, -0.5],
            [0.5, 0.5, -0.5],
            [-0.5, 0.5, -0.5],
            [-0.5, -0.5, 0.5],
            [0.5, -0.5, 0.5],
            [0.5, 0.5, 0.5],
            [-0.5, 0.5, 0.5],
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
    return vertices, indices


def _pyramid_geometry() -> tuple[np.ndarray, np.ndarray]:
    vertices = np.array(
        [
            [-0.5, -0.5, -0.5],
            [0.5, -0.5, -0.5],
            [0.5, -0.5, 0.5],
            [-0.5, -0.5, 0.5],
            [0.0, 0.5, 0.0],
        ],
        dtype=np.float32,
    )
    indices = np.array(
        [
            0,
            1,
            4,
            1,
            2,
            4,
            2,
            3,
            4,
            3,
            0,
            4,
            0,
            2,
            1,
            0,
            3,
            2,
        ],
        dtype=np.int32,
    )
    return vertices, indices


def _prism_geometry(sides: int = 8) -> tuple[np.ndarray, np.ndarray]:
    sides = max(3, sides)
    angles = np.linspace(0.0, 2.0 * math.pi, sides, endpoint=False)
    top = np.stack([np.cos(angles), np.full_like(angles, 0.5), np.sin(angles)], axis=1)
    bottom = np.stack([np.cos(angles), np.full_like(angles, -0.5), np.sin(angles)], axis=1)
    vertices = np.vstack([bottom, top]).astype(np.float32)

    indices: list[int] = []
    for i in range(sides):
        n = (i + 1) % sides
        indices.extend([i, n, sides + i])
        indices.extend([n, sides + n, sides + i])
    bottom_center = len(vertices)
    top_center = len(vertices) + 1
    vertices = np.vstack(
        [
            vertices,
            np.array([[0.0, -0.5, 0.0], [0.0, 0.5, 0.0]], dtype=np.float32),
        ]
    )
    for i in range(sides):
        n = (i + 1) % sides
        indices.extend([bottom_center, n, i])
        indices.extend([top_center, sides + i, sides + n])
    return vertices, np.array(indices, dtype=np.int32)


def _box_uvs(vertices: np.ndarray) -> np.ndarray:
    xs = vertices[:, 0]
    zs = vertices[:, 2]
    min_x, max_x = float(xs.min()), float(xs.max())
    min_z, max_z = float(zs.min()), float(zs.max())
    span_x = max(max_x - min_x, 1e-6)
    span_z = max(max_z - min_z, 1e-6)
    u = (xs - min_x) / span_x
    v = (zs - min_z) / span_z
    return np.stack([u, v], axis=1).astype(np.float32)
