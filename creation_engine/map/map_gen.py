from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np


def generate_tilemap(
    prompt: str,
    width: int = 64,
    height: int = 64,
    seed: int | None = None,
) -> dict:
    """Generate tilemap using C++ backend or fallback.

    Returns
    -------
    dict
        Keys: tiles (2D array), props (list), tileset (str)
    """
    cpp_bin = Path(__file__).resolve().parents[2] / "build" / "creation-engine"

    if cpp_bin.exists():
        try:
            return _generate_cpp(cpp_bin, prompt, width, height, seed)
        except (subprocess.SubprocessError, OSError, FileNotFoundError, json.JSONDecodeError):
            pass

    return _generate_python_fallback(prompt, width, height, seed)


def _generate_cpp(cpp_bin: Path, prompt: str, width: int, height: int, seed: int | None):
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            str(cpp_bin),
            "map",
            "--prompt",
            prompt,
            "--seed",
            str(seed or 42),
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
            return {
                "tiles": np.array(data["tiles"]),
                "props": data.get("props", []),
                "tileset": data.get("tileset", "default"),
            }

    return _generate_python_fallback(prompt, width, height, seed)


def _generate_python_fallback(prompt: str, width: int, height: int, seed: int | None):
    del prompt
    np.random.seed(seed or 42)
    tiles = np.random.randint(0, 5, size=(height, width))
    return {
        "tiles": tiles,
        "props": [],
        "tileset": "default",
    }
