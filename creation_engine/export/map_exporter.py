import json
from pathlib import Path


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

    output = {
        "version": "1.0",
        "name": name,
        "prompt": prompt,
        "seed": 42 if seed is None else seed,
        "width": width,
        "height": height,
        "tiles": tile_rows,
        "props": map_data.get("props", []),
        "tileset": map_data.get("tileset", "default"),
    }

    path = output_dir / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    return path
