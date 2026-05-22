from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
from creation_engine.narrative_tags import (
    extract_narrative_tags,
    infer_exploration_intent,
    infer_world_region_id,
)
from creation_engine.map.tileset_specs import THEME_ALIASES, TILESET_SPECS
from creation_engine.prompting import tokenize_prompt


def generate_tilemap(
    prompt: str,
    width: int = 64,
    height: int = 64,
    seed: int | None = None,
    region_id: str | None = None,
    chunk_x: int = 0,
    chunk_y: int = 0,
) -> dict:
    """Generate tilemap using C++ backend or fallback.

    Returns
    -------
    dict
        Keys: tiles (2D array), props (list), tileset (str)
    """
    if width < 1 or height < 1:
        raise ValueError("width and height must be >= 1")

    cpp_bin = Path(__file__).resolve().parents[2] / "build" / "creation-engine"

    can_use_cpp_backend = region_id is None and int(chunk_x) == 0 and int(chunk_y) == 0
    if cpp_bin.exists() and can_use_cpp_backend:
        try:
            return _generate_cpp(
                cpp_bin,
                prompt,
                width,
                height,
                seed,
                region_id=region_id,
                chunk_x=chunk_x,
                chunk_y=chunk_y,
            )
        except (subprocess.SubprocessError, OSError, FileNotFoundError, json.JSONDecodeError):
            pass

    return _generate_python_fallback(
        prompt,
        width,
        height,
        seed,
        region_id=region_id,
        chunk_x=chunk_x,
        chunk_y=chunk_y,
    )


def _generate_cpp(
    cpp_bin: Path,
    prompt: str,
    width: int,
    height: int,
    seed: int | None,
    *,
    region_id: str | None,
    chunk_x: int,
    chunk_y: int,
):
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            str(cpp_bin),
            "map",
            "--prompt",
            prompt,
            "--seed",
            str(42 if seed is None else seed),
            "--out",
            tmpdir,
            "--width",
            str(width),
            "--height",
            str(height),
            "--name",
            "bridge",
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        json_files = list(Path(tmpdir).glob("*.json"))
        if json_files:
            with open(json_files[0], encoding="utf-8") as f:
                data = json.load(f)
            theme = _pick_theme(prompt)
            narrative_tags = extract_narrative_tags(tokenize_prompt(prompt))
            world_region_id = region_id or infer_world_region_id(narrative_tags)
            tileset_name = data.get("tileset", TILESET_SPECS[theme]["id"])
            return {
                "tiles": np.array(data["tiles"]),
                "props": data.get("props", []),
                "tileset": tileset_name,
                "theme": theme,
                "map_family": "world",
                "narrative_tags": narrative_tags,
                "world_region_id": world_region_id,
                "chunk": {"x": int(chunk_x), "y": int(chunk_y)},
                "exploration_intent": infer_exploration_intent(narrative_tags),
            }

    return _generate_python_fallback(
        prompt,
        width,
        height,
        seed,
        region_id=region_id,
        chunk_x=chunk_x,
        chunk_y=chunk_y,
    )


def _generate_python_fallback(
    prompt: str,
    width: int,
    height: int,
    seed: int | None,
    *,
    region_id: str | None,
    chunk_x: int,
    chunk_y: int,
):
    seed_value = 42 if seed is None else seed
    tokens = tokenize_prompt(prompt)
    narrative_tags = extract_narrative_tags(tokens)
    world_region_id = region_id or infer_world_region_id(narrative_tags)
    region_mix = sum(ord(ch) for ch in world_region_id)
    chunk_mix = int(chunk_x) * 73856093 + int(chunk_y) * 19349663
    theme = _pick_theme(prompt)
    spec = TILESET_SPECS[theme]
    prompt_mix = sum(ord(ch) for ch in prompt.lower())
    rng = np.random.default_rng(seed_value + prompt_mix + region_mix + chunk_mix)

    if spec["style"] == "indoor":
        tiles = _generate_indoor_layout(width, height, rng, floor_id=0, wall_id=1)
    elif spec["style"] == "coast":
        tiles = _generate_coast_layout(width, height, rng)
    elif spec["style"] == "desert":
        tiles = _generate_desert_layout(width, height, rng)
    elif spec["style"] == "snow":
        tiles = _generate_snow_layout(width, height, rng)
    elif spec["style"] == "forest":
        tiles = _generate_forest_layout(width, height, rng)
    elif spec["style"] == "town":
        tiles = _generate_town_layout(width, height, rng)
    elif spec["style"] == "ruins":
        tiles = _generate_ruins_layout(width, height, rng)
    else:
        tiles = _generate_overworld_layout(width, height, rng)

    if spec["style"] in {"outdoor", "forest", "desert", "coast", "snow", "town"}:
        neighbor_theme = _choose_neighbor_theme(theme, chunk_x, chunk_y)
        neighbor_style = TILESET_SPECS[neighbor_theme]["style"]
        tiles = _blend_neighbor_theme(tiles, neighbor_style, rng)

    return {
        "tiles": tiles,
        "props": _generate_props(theme, width, height, rng),
        "tileset": spec["id"],
        "theme": theme,
        "map_family": "world",
        "narrative_tags": narrative_tags,
        "world_region_id": world_region_id,
        "chunk": {"x": int(chunk_x), "y": int(chunk_y)},
        "exploration_intent": infer_exploration_intent(narrative_tags),
    }


def _pick_theme(prompt: str) -> str:
    tokens = tokenize_prompt(prompt)
    for token in tokens:
        if token in THEME_ALIASES:
            return THEME_ALIASES[token]
    return "overworld"


def _choose_neighbor_theme(theme: str, chunk_x: int, chunk_y: int) -> str:
    themed_neighbors = {
        "overworld": ["forest", "coast", "highlands"],
        "forest": ["overworld", "ruins", "highlands"],
        "desert": ["wasteland", "volcanic", "overworld"],
        "coast": ["port_city", "overworld", "forest"],
        "snowfield": ["highlands", "overworld", "temple"],
        "town": ["overworld", "forest", "coast"],
        "capital_city": ["overworld", "imperial_fortress", "town"],
        "port_city": ["coast", "town", "overworld"],
        "highlands": ["forest", "snowfield", "overworld"],
        "volcanic": ["wasteland", "desert", "ruins"],
        "wasteland": ["desert", "volcanic", "ruins"],
        "ruins": ["forest", "desert", "sacred_ruins"],
        "sacred_ruins": ["ruins", "temple", "forest"],
        "temple": ["sacred_ruins", "forest", "overworld"],
    }
    options = themed_neighbors.get(theme, ["overworld"])
    idx = abs(int(chunk_x) * 31 + int(chunk_y) * 17) % len(options)
    return options[idx]


def _generate_overworld_layout(width: int, height: int, rng: np.random.Generator) -> np.ndarray:
    noise = rng.random((height, width))
    tiles = np.full((height, width), 3, dtype=np.int32)
    tiles[noise < 0.12] = 2
    tiles[noise > 0.82] = 5
    tiles[(noise > 0.48) & (noise < 0.54)] = 7
    return tiles


def _generate_forest_layout(width: int, height: int, rng: np.random.Generator) -> np.ndarray:
    noise = rng.random((height, width))
    tiles = np.full((height, width), 3, dtype=np.int32)
    tiles[noise > 0.55] = 5
    stream_col = int(rng.integers(0, max(1, width)))
    tiles[:, max(0, stream_col - 1) : min(width, stream_col + 1)] = 2
    return tiles


def _generate_desert_layout(width: int, height: int, rng: np.random.Generator) -> np.ndarray:
    noise = rng.random((height, width))
    tiles = np.full((height, width), 4, dtype=np.int32)
    tiles[(noise > 0.58) & (noise < 0.73)] = 0
    road_row = int(rng.integers(0, max(1, height)))
    tiles[max(0, road_row - 1) : min(height, road_row + 1), :] = 7
    return tiles


def _generate_coast_layout(width: int, height: int, rng: np.random.Generator) -> np.ndarray:
    noise = rng.random((height, width))
    shoreline = int(width * 0.35) + int(rng.integers(-2, 3))
    shoreline = min(max(1, shoreline), width - 1) if width > 1 else 1
    tiles = np.full((height, width), 4, dtype=np.int32)
    tiles[:, :shoreline] = 2
    tiles[(noise > 0.70) & (np.arange(width)[None, :] > shoreline)] = 3
    return tiles


def _generate_snow_layout(width: int, height: int, rng: np.random.Generator) -> np.ndarray:
    noise = rng.random((height, width))
    tiles = np.full((height, width), 6, dtype=np.int32)
    tiles[noise < 0.10] = 2
    tiles[(noise > 0.42) & (noise < 0.49)] = 7
    return tiles


def _generate_town_layout(width: int, height: int, rng: np.random.Generator) -> np.ndarray:
    tiles = np.full((height, width), 0, dtype=np.int32)
    tiles[::4, :] = 7
    tiles[:, ::6] = 7
    for _ in range(max(2, width * height // 200)):
        x = int(rng.integers(1, max(2, width - 3)))
        y = int(rng.integers(1, max(2, height - 3)))
        tiles[y : y + 2, x : x + 3] = 1
    return tiles


def _generate_ruins_layout(width: int, height: int, rng: np.random.Generator) -> np.ndarray:
    tiles = _generate_indoor_layout(width, height, rng, floor_id=0, wall_id=1)
    rubble = rng.random((height, width)) > 0.88
    tiles[rubble] = 4
    return tiles


def _generate_indoor_layout(
    width: int,
    height: int,
    rng: np.random.Generator,
    floor_id: int,
    wall_id: int,
) -> np.ndarray:
    tiles = np.full((height, width), floor_id, dtype=np.int32)
    tiles[0, :] = wall_id
    tiles[-1, :] = wall_id
    tiles[:, 0] = wall_id
    tiles[:, -1] = wall_id
    for _ in range(max(2, width // 8)):
        x = int(rng.integers(2, max(3, width - 2)))
        tiles[:, x : x + 1] = wall_id
    for _ in range(max(2, height // 8)):
        y = int(rng.integers(2, max(3, height - 2)))
        tiles[y : y + 1, :] = wall_id
    return tiles


def _generate_props(
    theme: str, width: int, height: int, rng: np.random.Generator
) -> list[dict[str, int | str]]:
    templates = {
        "overworld": ["save_point", "chest"],
        "forest": ["chest", "campfire"],
        "desert": ["chest", "obelisk"],
        "coast": ["boat_marker", "chest"],
        "snowfield": ["save_point", "ice_crystal"],
        "town": ["shop_marker", "inn_marker"],
        "dungeon": ["chest", "enemy_spawn"],
        "ruins": ["chest", "shrine_marker"],
        "temple": ["save_point", "shrine_marker"],
        "cave": ["chest", "enemy_spawn"],
        "castle": ["save_point", "chest"],
        "capital_city": ["shop_marker", "inn_marker", "save_point"],
        "port_city": ["boat_marker", "shop_marker"],
        "highlands": ["campfire", "chest"],
        "volcanic": ["enemy_spawn", "shrine_marker"],
        "sacred_ruins": ["save_point", "shrine_marker"],
        "imperial_fortress": ["enemy_spawn", "chest"],
        "wasteland": ["enemy_spawn", "chest"],
    }
    types = templates.get(theme, ["chest"])
    props: list[dict[str, int | str]] = []
    for prop_type in types:
        props.append(
            {
                "type": prop_type,
                "x": int(rng.integers(1, max(2, width - 1))),
                "y": int(rng.integers(1, max(2, height - 1))),
            }
        )
    return props


def _blend_neighbor_theme(
    base_tiles: np.ndarray, neighbor_style: str, rng: np.random.Generator
) -> np.ndarray:
    height, width = base_tiles.shape
    out = base_tiles.copy()
    blend_mode = int(rng.integers(0, 3))
    mask = np.zeros((height, width), dtype=bool)
    if blend_mode == 0:
        split = max(1, width // 4)
        mask[:, :split] = True
    elif blend_mode == 1:
        split = max(1, height // 4)
        mask[:split, :] = True
    else:
        noise = rng.random((height, width))
        mask = noise > 0.84

    if neighbor_style == "coast":
        out[mask] = 2
    elif neighbor_style == "desert":
        out[mask] = 4
    elif neighbor_style == "snow":
        out[mask] = 6
    elif neighbor_style == "forest":
        out[mask] = 5
    elif neighbor_style == "town":
        out[mask] = 7
    elif neighbor_style == "ruins":
        out[mask] = 4
    else:
        out[mask] = 3
    return out
