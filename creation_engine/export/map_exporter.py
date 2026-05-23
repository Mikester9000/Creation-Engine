import json
from pathlib import Path

from creation_engine.export.manifest_exporter import DEFAULT_STYLE_PROFILE
from creation_engine.narrative_tags import (
    extract_narrative_tags,
    infer_exploration_intent,
    infer_placement_intent,
    infer_world_region_id,
)
from creation_engine.map.tileset_specs import tileset_spec_for_id, tileset_spec_for_theme
from creation_engine.prompting import tokenize_prompt


def export_tilemap(
    map_data: dict,
    output_dir: Path,
    name: str,
    prompt: str,
    seed: int | None,
) -> Path:
    """Export tilemap to JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)

    tiles = map_data["tiles"]
    tile_rows = tiles.tolist() if hasattr(tiles, "tolist") else list(tiles)
    height = len(tile_rows)
    width = len(tile_rows[0]) if tile_rows else 0

    theme = map_data.get("theme", "overworld")
    default_tileset_spec = tileset_spec_for_theme(theme)
    tileset_id = map_data.get("tileset", default_tileset_spec["id"])
    tileset_spec = tileset_spec_for_id(tileset_id) or default_tileset_spec

    tile_counts: dict[str, int] = {}
    for row in tile_rows:
        for tile in row:
            key = str(tile)
            tile_counts[key] = tile_counts.get(key, 0) + 1
    narrative_tags = map_data.get("narrative_tags") or extract_narrative_tags(tokenize_prompt(prompt))
    world_region_id = map_data.get("world_region_id", infer_world_region_id(narrative_tags))
    exploration_intent = map_data.get("exploration_intent", infer_exploration_intent(narrative_tags))

    output = {
        "version": "1.1",
        "name": name,
        "prompt": prompt,
        "seed": 42 if seed is None else seed,
        "width": width,
        "height": height,
        "map_family": map_data.get("map_family", "world"),
        "theme": theme,
        "tileset": tileset_id,
        "tileset_meta": {
            "id": tileset_spec["id"],
            "name": tileset_spec["name"],
            "tileSize": tileset_spec["tile_size"],
            "style": tileset_spec["style"],
        },
        "tiles": tile_rows,
        "props": map_data.get("props", []),
        "summary": {
            "tile_counts": tile_counts,
            "prop_count": len(map_data.get("props", [])),
        },
        "narrative_tags": narrative_tags,
        "world_region_id": world_region_id,
        "exploration_intent": exploration_intent,
        "placement_intent": infer_placement_intent("maps", narrative_tags),
        "content_target": {"world": "Content/World"},
        "style_profile": DEFAULT_STYLE_PROFILE,
        # 3D enforcement: maps are rendered in 3D space with per-tile elevation.
        "asset_dimension": "3d",
        "render_mode": "3d",
        "coordinate_space": "Y_up",
        "tile_height_scale": 1.0,
        "height_map": map_data.get("height_map", []),
    }
    if "chunk" in map_data:
        output["chunk"] = map_data["chunk"]

    path = output_dir / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    return path
