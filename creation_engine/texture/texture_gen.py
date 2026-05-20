from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

CHANNELS = ("albedo", "normal", "roughness", "metallic", "ao", "emissive")


def generate_pbr_textures(
    prompt: str,
    width: int = 64,
    height: int = 64,
    seed: int = 42,
) -> dict[str, np.ndarray]:
    """Generate PBR textures using C++ backend or fallback."""
    cpp_bin = Path(__file__).resolve().parents[2] / "build" / "creation-engine"

    if cpp_bin.exists():
        try:
            return _generate_cpp(cpp_bin, prompt, width, height, seed)
        except (subprocess.SubprocessError, OSError, FileNotFoundError):
            pass

    return _generate_python_fallback(prompt, width, height, seed)


def _generate_cpp(
    cpp_bin: Path,
    prompt: str,
    width: int,
    height: int,
    seed: int,
) -> dict[str, np.ndarray]:
    with tempfile.TemporaryDirectory() as tmpdir:
        output_name = "bridge"
        cmd = [
            str(cpp_bin),
            "texture",
            "--prompt",
            prompt,
            "--seed",
            str(seed),
            "--out",
            tmpdir,
            "--name",
            output_name,
            "--width",
            str(width),
            "--height",
            str(height),
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        generated: dict[str, np.ndarray] = {}
        for channel in CHANNELS:
            path = Path(tmpdir) / f"{output_name}_{channel}.png"
            if not path.exists():
                return _generate_python_fallback(prompt, width, height, seed)
            with Image.open(path) as img:
                generated[channel] = np.array(img)

        return generated


def _generate_python_fallback(
    prompt: str,
    width: int,
    height: int,
    seed: int,
) -> dict[str, np.ndarray]:
    prompt_mix = sum(ord(ch) for ch in prompt)
    rng = np.random.default_rng(seed + prompt_mix)

    albedo = rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)
    normal = np.zeros((height, width, 3), dtype=np.uint8)
    normal[..., 0] = 128
    normal[..., 1] = 128
    normal[..., 2] = 255

    roughness = rng.integers(64, 220, size=(height, width), dtype=np.uint8)
    metallic = rng.integers(0, 64, size=(height, width), dtype=np.uint8)
    ao = rng.integers(180, 255, size=(height, width), dtype=np.uint8)

    emissive = np.zeros((height, width, 3), dtype=np.uint8)

    return {
        "albedo": albedo,
        "normal": normal,
        "roughness": roughness,
        "metallic": metallic,
        "ao": ao,
        "emissive": emissive,
    }
