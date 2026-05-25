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

# ---------------------------------------------------------------------------
# Coherent noise helpers (pure numpy, no scipy dependency)
# ---------------------------------------------------------------------------

def _smooth_noise(rng: np.random.Generator, height: int, width: int, scale: int) -> np.ndarray:
    """Generate smooth noise by upsampling a low-res random grid.

    ``scale`` controls the coarseness: larger scale = larger features.
    Returns values in [0, 1] as float32.
    """
    grid_h = max(2, height // scale)
    grid_w = max(2, width // scale)
    coarse = rng.random((grid_h, grid_w)).astype(np.float32)
    img = Image.fromarray((coarse * 255).astype(np.uint8), mode="L")
    img = img.resize((width, height), Image.BILINEAR)
    return np.array(img, dtype=np.float32) / 255.0


def _fbm_noise(
    rng: np.random.Generator,
    height: int,
    width: int,
    octaves: int = 4,
    base_scale: int = 8,
    persistence: float = 0.5,
) -> np.ndarray:
    """Fractional Brownian Motion noise — layered smooth noise octaves.

    Returns values normalised to [0, 1].
    """
    result = np.zeros((height, width), dtype=np.float32)
    amplitude = 1.0
    total_amplitude = 0.0
    scale = base_scale
    for _ in range(octaves):
        result += amplitude * _smooth_noise(rng, height, width, scale)
        total_amplitude += amplitude
        amplitude *= persistence
        scale = max(2, scale // 2)
    return result / total_amplitude


def _normal_from_height(height_map: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """Derive a tangent-space normal map from a float32 [0,1] height field.

    Returns uint8 RGB packed as (R=X+128, G=Y+128, B=Z+255).
    Neighbours are clamped so edge pixels are correct.
    """
    h, w = height_map.shape
    # Sobel-style gradient using simple finite differences
    padded = np.pad(height_map, 1, mode="edge")
    dx = (padded[1:-1, 2:] - padded[1:-1, :-2]) * strength * 4.0
    dy = (padded[2:, 1:-1] - padded[:-2, 1:-1]) * strength * 4.0
    dz = np.ones((h, w), dtype=np.float32)
    length = np.sqrt(dx * dx + dy * dy + dz * dz)
    nx = np.clip(-dx / length * 0.5 + 0.5, 0.0, 1.0)
    ny = np.clip(-dy / length * 0.5 + 0.5, 0.0, 1.0)
    nz = np.clip(dz / length * 0.5 + 0.5, 0.0, 1.0)
    out = np.zeros((h, w, 3), dtype=np.uint8)
    out[..., 0] = (nx * 255).astype(np.uint8)
    out[..., 1] = (ny * 255).astype(np.uint8)
    out[..., 2] = (nz * 255).astype(np.uint8)
    return out


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

    # ------------------------------------------------------------------
    # Albedo: multi-octave coherent noise over a controlled base+tint
    # ------------------------------------------------------------------
    # Height field used for both albedo variation and normal derivation
    surface_h = _fbm_noise(rng, height, width, octaves=4, base_scale=max(4, min(height, width) // 4))

    base_color = np.array(material["base_color"], dtype=np.float32).reshape(1, 1, 3)
    tint = palette[rng.integers(0, len(palette))].astype(np.float32).reshape(1, 1, 3)
    # 75 % base colour, 25 % palette tint — preserves material identity
    tinted_base = base_color * 0.75 + tint * 0.25

    # Surface noise layered on top: ±20 luminance units at full amplitude
    noise_scale = 20.0
    noise_offset = (surface_h[..., np.newaxis] - 0.5) * 2.0 * noise_scale
    albedo = np.clip(tinted_base + noise_offset, 0, 255).astype(np.uint8)

    # Material-specific surface pattern overlays (PS2 FF style)
    albedo = _apply_material_surface(albedo, tokens, surface_h, palette, rng)

    if family == "ui_icons":
        albedo = _generate_icon_pattern(albedo, palette, tokens, rng)
    elif family == "ui_panels":
        albedo = _generate_panel_pattern(albedo, palette, rng)
    elif family == "ui_portraits":
        albedo = _generate_portrait_pattern(albedo, palette, tokens, rng)
    elif family == "decals":
        albedo = _generate_decal_pattern(albedo, palette, tokens, rng)

    # ------------------------------------------------------------------
    # Normal map derived from surface height field
    # ------------------------------------------------------------------
    normal_strength = _normal_strength_for_material(material_key, tokens)
    normal = _normal_from_height(surface_h, strength=normal_strength)

    # ------------------------------------------------------------------
    # Roughness / Metallic / AO — coherent spatial variation
    # ------------------------------------------------------------------
    rough_h = _fbm_noise(rng, height, width, octaves=2, base_scale=max(4, min(height, width) // 3))
    roughness_center = material["roughness"]
    roughness = np.clip(
        roughness_center + (rough_h - 0.5) * 0.18,
        0.02,
        0.98,
    )
    roughness = (roughness * 255).astype(np.uint8)

    metallic_center = material["metallic"]
    metallic_noise = _fbm_noise(rng, height, width, octaves=2, base_scale=max(4, min(height, width) // 4))
    metallic = np.clip(
        metallic_center + (metallic_noise - 0.5) * 0.08,
        0.0,
        1.0,
    )
    metallic = (metallic * 255).astype(np.uint8)

    ao_center = material["ao"]
    ao_h = _fbm_noise(rng, height, width, octaves=3, base_scale=max(4, min(height, width) // 5))
    ao = np.clip(ao_center - ao_h * 0.12, 0.0, 1.0)
    ao = (ao * 255).astype(np.uint8)

    # ------------------------------------------------------------------
    # Emissive — FF-specific glow by token keyword
    # ------------------------------------------------------------------
    emissive = _generate_emissive(tokens, surface_h, palette, rng, height, width)

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


def _normal_strength_for_material(material_key: str, tokens: list[str]) -> float:
    """Return bump strength tuned per material class for PS2 FF depth cues."""
    high_bump = {"stone", "rock", "brick", "bark", "wood", "cobblestone", "rubble", "cliff"}
    low_bump = {"fabric", "cloth", "leather", "skin", "sand", "snow", "moss"}
    metal_bump = {"metal", "iron", "steel", "copper", "gold", "silver", "chrome", "mithril"}
    crystal_bump = {"crystal", "ice", "glass", "gem", "materia"}
    if material_key in crystal_bump or any(t in crystal_bump for t in tokens):
        return 0.4
    if material_key in metal_bump or any(t in metal_bump for t in tokens):
        return 0.6
    if material_key in high_bump or any(t in high_bump for t in tokens):
        return 1.2
    if material_key in low_bump or any(t in low_bump for t in tokens):
        return 0.3
    return 0.8


def _apply_material_surface(
    albedo: np.ndarray,
    tokens: list[str],
    surface_h: np.ndarray,
    palette: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """Add PS2-style surface feature overlays based on material keywords."""
    out = albedo.copy()
    h, w = out.shape[:2]
    token_set = set(tokens)

    # Veined stone / marble — vertical-ish bright streaks
    if token_set & {"marble", "vein", "quartz"}:
        vein_h = _fbm_noise(rng, h, w, octaves=3, base_scale=max(3, w // 8), persistence=0.7)
        vein_mask = vein_h > 0.78
        out[vein_mask] = np.clip(out[vein_mask].astype(np.int16) + 35, 0, 255).astype(np.uint8)

    # Brick / tile — grid seams
    if token_set & {"brick", "tile", "cobblestone", "flagstone"}:
        seam_y = (np.arange(h) % max(4, h // 8)) < max(1, h // 40)
        seam_x = (np.arange(w) % max(4, w // 8)) < max(1, w // 40)
        seam_mask = seam_y[:, None] | seam_x[None, :]
        out[seam_mask] = np.clip(out[seam_mask].astype(np.int16) - 30, 0, 255).astype(np.uint8)

    # Wood grain — horizontal banding
    if token_set & {"wood", "plank", "bark", "timber"}:
        grain = np.sin(np.arange(h, dtype=np.float32)[:, None] / max(2, h / 10) * np.pi)
        grain_3d = (grain[..., np.newaxis] * 14).astype(np.int16)
        out = np.clip(out.astype(np.int16) + grain_3d, 0, 255).astype(np.uint8)

    # Crystal / materia — specular facets via threshold bands on surface_h
    if token_set & {"crystal", "materia", "gem", "jewel"}:
        facet = (np.floor(surface_h * 6) % 2).astype(bool)
        out[facet] = np.clip(out[facet].astype(np.int16) + 45, 0, 255).astype(np.uint8)
        out[~facet] = np.clip(out[~facet].astype(np.int16) - 20, 0, 255).astype(np.uint8)

    # Rust / worn metal — darker irregular patches
    if token_set & {"rust", "corroded", "worn", "aged", "weathered"}:
        rust_h = _fbm_noise(rng, h, w, octaves=2, base_scale=max(3, w // 6))
        rust_mask = rust_h > 0.65
        rust_tint = np.array([80, 35, 10], dtype=np.int16)
        out[rust_mask] = np.clip(
            out[rust_mask].astype(np.int16) * 0.55 + rust_tint, 0, 255
        ).astype(np.uint8)

    # Snow / ice — bright high patches
    if token_set & {"snow", "frost", "ice"}:
        snow_mask = surface_h > 0.72
        out[snow_mask] = np.clip(out[snow_mask].astype(np.int16) + 55, 0, 255).astype(np.uint8)

    # Lava — dark crust with bright cracks
    if token_set & {"lava", "magma", "molten"}:
        crack_mask = surface_h < 0.18
        out[crack_mask] = np.array([240, 110, 20], dtype=np.uint8)
        crust_mask = ~crack_mask
        out[crust_mask] = np.clip(out[crust_mask].astype(np.int16) - 60, 0, 255).astype(np.uint8)

    return out


def _generate_emissive(
    tokens: list[str],
    surface_h: np.ndarray,
    palette: np.ndarray,
    rng: np.random.Generator,
    height: int,
    width: int,
) -> np.ndarray:
    """Generate FF-specific emissive glow textures."""
    emissive = np.zeros((height, width, 3), dtype=np.uint8)
    token_set = set(tokens)

    # Materia / crystal pulse — blue-white or colour-tinted
    if token_set & {"materia", "crystal", "gem", "jewel"}:
        glow_h = _fbm_noise(rng, height, width, octaves=2, base_scale=max(3, width // 6))
        glow = (np.clip(glow_h - 0.45, 0.0, 1.0) / 0.55 * 180).astype(np.uint8)
        tint_color = palette[min(3, len(palette) - 1)]
        emissive[..., 0] = np.clip(glow.astype(np.int16) * tint_color[0] // 255, 0, 255).astype(np.uint8)
        emissive[..., 1] = np.clip(glow.astype(np.int16) * tint_color[1] // 255, 0, 255).astype(np.uint8)
        emissive[..., 2] = np.clip(glow.astype(np.int16) * tint_color[2] // 255, 0, 255).astype(np.uint8)

    # Holy / light — warm white radial bloom
    elif token_set & {"holy", "light", "sacred", "divine", "white_magic"}:
        yy, xx = np.ogrid[:height, :width]
        cx, cy = width // 2, height // 2
        dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (min(height, width) * 0.6)
        bloom = np.clip(1.0 - dist, 0.0, 1.0).astype(np.float32)
        emissive[..., 0] = (bloom * 200).astype(np.uint8)
        emissive[..., 1] = (bloom * 190).astype(np.uint8)
        emissive[..., 2] = (bloom * 160).astype(np.uint8)

    # Fire / lava / flame — red-orange flicker
    elif token_set & {"fire", "flame", "lava", "magma", "molten"}:
        fire_h = _fbm_noise(rng, height, width, octaves=3, base_scale=max(3, width // 8))
        intensity = np.clip(fire_h - 0.35, 0.0, 1.0) / 0.65
        emissive[..., 0] = (intensity * 240).astype(np.uint8)
        emissive[..., 1] = (intensity * 90).astype(np.uint8)
        emissive[..., 2] = (intensity * 10).astype(np.uint8)

    # Magitek / machinery — blue-green scan-line pulse
    elif token_set & {"magitek", "mako", "mech", "machine", "reactor"}:
        scan_y = np.arange(height, dtype=np.float32)[:, None]
        scan = (np.sin(scan_y / max(2, height / 12) * np.pi * 2) * 0.5 + 0.5).astype(np.float32)
        emissive[..., 0] = (scan * 20).astype(np.uint8)
        emissive[..., 1] = (scan * 160).astype(np.uint8)
        emissive[..., 2] = (scan * 120).astype(np.uint8)

    # Dark / rune / cursed — purple corruption glow
    elif token_set & {"rune", "cursed", "dark", "shadow", "void", "dark_magic"}:
        rune_h = _fbm_noise(rng, height, width, octaves=2, base_scale=max(3, width // 6))
        glow = np.clip(rune_h - 0.5, 0.0, 1.0) / 0.5
        emissive[..., 0] = (glow * 120).astype(np.uint8)
        emissive[..., 1] = (glow * 10).astype(np.uint8)
        emissive[..., 2] = (glow * 180).astype(np.uint8)

    # Save point / aether — soft blue-white
    elif token_set & {"save", "aether", "mist", "lifestream", "aura"}:
        aura_h = _fbm_noise(rng, height, width, octaves=2, base_scale=max(3, width // 5))
        glow = np.clip(aura_h - 0.4, 0.0, 1.0) / 0.6
        emissive[..., 0] = (glow * 40).astype(np.uint8)
        emissive[..., 1] = (glow * 140).astype(np.uint8)
        emissive[..., 2] = (glow * 230).astype(np.uint8)

    return emissive


def _generate_icon_pattern(
    image: np.ndarray,
    palette: np.ndarray,
    tokens: list[str],
    rng: np.random.Generator,
) -> np.ndarray:
    """Crisp two-tone icon with a readable silhouette — PS2 FF menu style."""
    out = np.zeros_like(image)
    h, w = out.shape[:2]
    yy, xx = np.ogrid[:h, :w]
    cx, cy = w // 2, h // 2
    out[...] = palette[0]
    radius = max(4, min(h, w) // 3)
    token_set = set(tokens)

    if token_set & {"sword", "blade", "weapon", "dagger", "spear"}:
        # Diagonal blade silhouette
        mask = np.abs(xx - (yy * 0.6 + w * 0.15)) < max(2, w // 16)
        out[mask] = palette[3]
        # Guard crosspiece
        guard_y = cy + 4
        out[max(0, guard_y - 2) : min(h, guard_y + 3), max(0, cx - 10) : min(w, cx + 10)] = palette[1]
    elif token_set & {"shield", "armor", "plate"}:
        # Kite shield shape
        mask_c = ((xx - cx) ** 2) / (radius ** 2) + ((yy - cy) ** 2) / ((radius * 1.1) ** 2) <= 1.0
        point = (yy > cy + 2) & (np.abs(xx - cx) < (h - yy) * 0.55)
        out[mask_c | point] = palette[2]
    elif token_set & {"potion", "flask", "vial", "elixir"}:
        # Rounded flask
        body = ((xx - cx) ** 2) / (radius ** 2) + ((yy - (cy + 3)) ** 2) / ((radius * 0.82) ** 2) <= 1.0
        out[body] = palette[2]
        neck = (np.abs(xx - cx) < max(2, w // 12)) & (yy < cy - 2) & (yy > cy - 10)
        out[neck] = palette[3]
    elif token_set & {"fire", "flame"}:
        # Teardrop flame
        flame = (xx - cx) ** 2 + (yy - (cy + 4)) ** 2 < (radius * 0.9) ** 2
        out[flame] = palette[3]
        inner = (xx - cx) ** 2 + (yy - cy) ** 2 < (radius * 0.45) ** 2
        out[inner] = palette[2]
    elif token_set & {"ice", "blizzard", "frost"}:
        # Diamond crystal
        diamond = np.abs(xx - cx) + np.abs(yy - cy) < radius
        out[diamond] = palette[3]
        shard = (np.abs(xx - cx) < 2) | (np.abs(yy - cy) < 2)
        out[diamond & shard] = palette[1]
    elif token_set & {"thunder", "lightning", "bolt"}:
        # Zigzag bolt
        mid = cx + (yy - cy) // 3
        bolt = np.abs(xx - mid) < max(2, w // 14)
        out[bolt] = palette[3]
    elif token_set & {"heal", "cure", "restore"}:
        # Cross
        out[max(0, cy - radius) : min(h, cy + radius), max(0, cx - 3) : min(w, cx + 4)] = palette[3]
        out[max(0, cy - 3) : min(h, cy + 4), max(0, cx - radius) : min(w, cx + radius)] = palette[3]
    else:
        # Generic circle badge
        out[(xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2] = palette[2]

    return out


def _generate_panel_pattern(
    image: np.ndarray,
    palette: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """Dark translucent panel with FF-style bevelled border and inner gradient."""
    out = np.zeros_like(image)
    h, w = out.shape[:2]
    # Dark fill — characteristic of FF dialog boxes
    out[...] = (palette[0].astype(np.int16) * 0.45 + 15).clip(0, 255).astype(np.uint8)
    border = max(2, min(h, w) // 10)
    # Bright top highlight, dark bottom shadow
    out[:border, :] = palette[3]
    out[-border:, :] = np.clip(palette[0].astype(np.int16) - 20, 0, 255).astype(np.uint8)
    # Side bevels
    out[:, :border] = palette[2]
    out[:, -border:] = np.clip(palette[1].astype(np.int16) - 20, 0, 255).astype(np.uint8)
    # Inner gentle horizontal gradient
    inner_region = out[border:-border, border:-border]
    if inner_region.size:
        grad = np.linspace(0.0, 1.0, inner_region.shape[1], dtype=np.float32)[None, :, None]
        base = palette[0].astype(np.float32) * 0.4 + 10
        highlight = palette[1].astype(np.float32) * 0.35 + 5
        inner_region[:] = np.clip(base * (1 - grad) + highlight * grad, 0, 255).astype(np.uint8)
    return out


def _generate_portrait_pattern(
    image: np.ndarray,
    palette: np.ndarray,
    tokens: list[str],
    rng: np.random.Generator,
) -> np.ndarray:
    """Stylised bust portrait silhouette — PS2 FF character portrait style."""
    out = np.zeros_like(image)
    h, w = out.shape[:2]
    cx, cy = w // 2, h // 2
    yy, xx = np.ogrid[:h, :w]
    # Gradient background
    bg_grad = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    bg = (palette[0].astype(np.float32) * (1 - bg_grad * 0.5)).clip(0, 255).astype(np.uint8)
    out[...] = bg

    # Face oval — upper-centre
    face_r_x = max(4, w // 5)
    face_r_y = max(4, h // 5)
    face_cy = cy - h // 8
    face = ((xx - cx) ** 2) / (face_r_x ** 2) + ((yy - face_cy) ** 2) / (face_r_y ** 2) <= 1.0
    out[face] = palette[3]

    # Hair / headgear — top of face oval
    hair_mask = face & (yy < face_cy)
    token_set = set(tokens)
    if token_set & {"knight", "warrior", "soldier", "dragoon"}:
        helm_top = (yy < face_cy - 2) & (np.abs(xx - cx) < face_r_x + 3)
        out[helm_top] = palette[2]
    elif token_set & {"mage", "wizard", "black_mage", "white_mage"}:
        out[hair_mask] = palette[2]
    else:
        out[hair_mask] = palette[1]

    # Shoulders / torso
    shoulder_mask = (np.abs(xx - cx) < int(w * 0.3)) & (yy > face_cy + face_r_y) & (yy < h)
    out[shoulder_mask] = palette[1]

    # Collar accent
    collar_mask = shoulder_mask & (yy < face_cy + face_r_y + max(2, h // 16))
    out[collar_mask] = palette[2]

    return out


def _generate_decal_pattern(
    image: np.ndarray,
    palette: np.ndarray,
    tokens: list[str],
    rng: np.random.Generator,
) -> np.ndarray:
    """Centred symbol decal — rune circle, emblem, or crest."""
    out = np.zeros_like(image)
    h, w = out.shape[:2]
    yy, xx = np.ogrid[:h, :w]
    cx, cy = w // 2, h // 2
    out[...] = palette[0]
    radius = max(4, min(h, w) // 3)
    token_set = set(tokens)

    # Outer ring
    ring = (((xx - cx) ** 2 + (yy - cy) ** 2) >= (radius - max(1, radius // 5)) ** 2) & (
        (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2
    )
    out[ring] = palette[3]

    if token_set & {"rune", "glyph", "seal", "sigil"}:
        # Cross inside ring
        cross_v = (np.abs(xx - cx) < max(1, w // 18)) & ((xx - cx) ** 2 + (yy - cy) ** 2 < radius ** 2)
        cross_h = (np.abs(yy - cy) < max(1, h // 18)) & ((xx - cx) ** 2 + (yy - cy) ** 2 < radius ** 2)
        out[cross_v | cross_h] = palette[1]
    elif token_set & {"emblem", "crest", "insignia"}:
        # Star / diamond
        star = (np.abs(xx - cx) + np.abs(yy - cy)) < radius - max(1, radius // 4)
        out[star] = palette[2]
    else:
        # Inner filled circle
        inner = (xx - cx) ** 2 + (yy - cy) ** 2 <= (radius - max(2, radius // 4)) ** 2
        out[inner] = palette[2]

    return out
