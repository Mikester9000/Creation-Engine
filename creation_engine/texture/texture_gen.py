from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from creation_engine.prompting import classify_prompt
from creation_engine.texture.material_presets import MATERIAL_MODIFIERS, MATERIAL_PRESETS
from creation_engine.texture.palette import pick_palette_family, select_palette

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
    parsed = classify_prompt(prompt)
    tokens = parsed["tokens"]
    family = parsed["family"]
    material_key = _pick_material_key(tokens)
    material = dict(MATERIAL_PRESETS[material_key])

    for token in tokens:
        mod = MATERIAL_MODIFIERS.get(token)
        if mod is None:
            continue
        material["base_color"] = tuple(
            int(np.clip(channel * mod["brightness"], 0, 255)) for channel in material["base_color"]
        )
        material["roughness"] = float(
            np.clip(material["roughness"] + mod["roughness_add"], 0.02, 0.98)
        )
        material["metallic"] = float(np.clip(material["metallic"] * mod["metallic_mul"], 0.0, 1.0))

    prompt_mix = sum(ord(ch) for ch in parsed["normalized_prompt"])
    rng = np.random.default_rng(seed + prompt_mix)
    palette_family = pick_palette_family(tokens)
    palette = select_palette(palette_family, seed + prompt_mix)

    noise = rng.integers(-32, 33, size=(height, width, 3), dtype=np.int16)
    base_color = np.array(material["base_color"], dtype=np.int16).reshape(1, 1, 3)
    tint = palette[rng.integers(0, len(palette))]
    tinted_base = ((base_color * 3 + tint.astype(np.int16)) // 4).astype(np.int16)
    albedo = np.clip(tinted_base + noise, 0, 255).astype(np.uint8)

    if family == "ui_icons":
        flat = np.mean(albedo, axis=2, dtype=np.float32)
        mask = flat > np.quantile(flat, 0.55)
        albedo = np.zeros_like(albedo)
        albedo[..., 0] = palette[3][0]
        albedo[..., 1] = palette[3][1]
        albedo[..., 2] = palette[3][2]
        albedo[~mask] = palette[0]
    elif family == "ui_panels":
        albedo = _generate_panel_pattern(albedo, palette)
    elif family == "ui_portraits":
        albedo = _generate_portrait_pattern(albedo, palette, rng)
    elif family == "decals":
        albedo = _generate_decal_pattern(albedo, palette)

    normal = np.zeros((height, width, 3), dtype=np.uint8)
    normal[..., 0] = 128
    normal[..., 1] = 128
    normal[..., 2] = 255

    roughness_center = int(material["roughness"] * 255)
    metallic_center = int(material["metallic"] * 255)
    roughness = np.clip(
        roughness_center + rng.integers(-22, 23, size=(height, width), dtype=np.int16),
        0,
        255,
    ).astype(np.uint8)
    metallic = np.clip(
        metallic_center + rng.integers(-12, 13, size=(height, width), dtype=np.int16),
        0,
        255,
    ).astype(np.uint8)
    ao_center = int(material["ao"] * 255)
    ao = np.clip(
        ao_center + rng.integers(-8, 9, size=(height, width), dtype=np.int16), 0, 255
    ).astype(np.uint8)

    emissive = np.zeros((height, width, 3), dtype=np.uint8)
    if any(token in {"lava", "rune", "holy", "cursed", "fire"} for token in tokens):
        glow = np.clip(rng.integers(0, 56, size=(height, width), dtype=np.int16), 0, 255).astype(
            np.uint8
        )
        emissive[..., 0] = glow
        emissive[..., 1] = (glow // 2).astype(np.uint8)

    return {
        "albedo": albedo,
        "normal": normal,
        "roughness": roughness,
        "metallic": metallic,
        "ao": ao,
        "emissive": emissive,
    }


def _pick_material_key(tokens: list[str]) -> str:
    for token in tokens:
        if token in MATERIAL_PRESETS:
            return token
    return "stone"


def _generate_panel_pattern(image: np.ndarray, palette: np.ndarray) -> np.ndarray:
    out = image.copy()
    h, w = out.shape[0], out.shape[1]
    border = max(1, min(h, w) // 12)
    out[:border, :, :] = palette[0]
    out[-border:, :, :] = palette[0]
    out[:, :border, :] = palette[1]
    out[:, -border:, :] = palette[1]
    return out


def _generate_portrait_pattern(
    image: np.ndarray, palette: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    out = image.copy()
    h, w = out.shape[0], out.shape[1]
    cx, cy = w // 2, h // 2
    y, x = np.ogrid[:h, :w]
    radius = max(3, min(h, w) // 3)
    mask = (x - cx) ** 2 + (y - cy) ** 2 <= radius**2
    out[~mask] = palette[0]
    accent = palette[rng.integers(1, len(palette))]
    out[mask] = ((out[mask].astype(np.uint16) + accent.astype(np.uint16)) // 2).astype(np.uint8)
    return out


def _generate_decal_pattern(image: np.ndarray, palette: np.ndarray) -> np.ndarray:
    out = np.zeros_like(image)
    h, w = out.shape[0], out.shape[1]
    out[...] = palette[0]
    size = max(2, min(h, w) // 3)
    y0, x0 = h // 2 - size // 2, w // 2 - size // 2
    out[y0 : y0 + size, x0 : x0 + size] = palette[3]
    return out
