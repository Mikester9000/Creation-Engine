import json
from pathlib import Path

from creation_engine.map.tileset_specs import TILESET_SPECS


def export_tilemap(
    map_data: dict,
    output_dir: Path,
    name: str,
    prompt: str,
    seed: int | None,
) -> Path:
    """Export tilemap to JSON.

    Parameters
    ----------
    map_data:
        Dict with keys: tiles (array), props (list), tileset (str)
    output_dir:
        Output directory
    name:
        Asset name
    prompt:
        Original generation prompt
    seed:
        Generation seed

    Returns
    -------
    Path
        Written JSON file path
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    tiles = map_data["tiles"]
    tile_rows = tiles.tolist() if hasattr(tiles, "tolist") else list(tiles)
    height = len(tile_rows)
    width = len(tile_rows[0]) if tile_rows else 0

    theme = map_data.get("theme", "overworld")
    tileset_id = map_data.get("tileset", TILESET_SPECS[theme]["id"])
    tileset_spec = next(
        (spec for spec in TILESET_SPECS.values() if spec["id"] == tileset_id),
        TILESET_SPECS.get(theme, TILESET_SPECS["overworld"]),
    )

    tile_counts: dict[str, int] = {}
    for row in tile_rows:
        for tile in row:
            key = str(tile)
            tile_counts[key] = tile_counts.get(key, 0) + 1

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
        "content_target": {"world": "Content/World"},
    }

    path = output_dir / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    return path
