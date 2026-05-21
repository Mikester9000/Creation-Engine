from __future__ import annotations

import numpy as np

from creation_engine.texture.palette import select_palette
from creation_engine.ui.ui_specs import UI_ICON_FAMILIES, resolve_ui_icon_family


def generate_ui_icon(prompt: str, seed: int = 42, size: int = 64) -> np.ndarray:
    family = resolve_ui_icon_family(prompt)
    palette = select_palette(UI_ICON_FAMILIES[family]["palette"], seed)
    image = np.zeros((size, size, 3), dtype=np.uint8)
    image[...] = palette[0]
    image = _draw_icon_shape(image, family, palette)
    return image


def _draw_icon_shape(image: np.ndarray, family: str, palette: np.ndarray) -> np.ndarray:
    out = image.copy()
    h, w = out.shape[:2]
    yy, xx = np.ogrid[:h, :w]
    cx, cy = w // 2, h // 2
    radius = max(4, min(h, w) // 3)
    if family == "weapon":
        mask = np.abs(xx - (yy * 0.55 + w * 0.18)) < max(2, w // 18)
        out[mask] = palette[3]
        out[max(0, cy - 6) : min(h, cy + 6), max(0, cx - 18) : min(w, cx - 2)] = palette[1]
    elif family == "armor":
        mask = ((xx - cx) ** 2) / (radius**2) + ((yy - cy) ** 2) / ((radius * 1.05) ** 2) <= 1.0
        out[mask] = palette[2]
        out[~mask] = palette[0]
    elif family == "potion":
        mask = ((xx - cx) ** 2) / (radius**2) + ((yy - (cy + 2)) ** 2) / (
            (radius * 0.8) ** 2
        ) <= 1.0
        out[mask] = palette[2]
        out[cy - 14 : cy - 8, cx - 4 : cx + 4] = palette[3]
    elif family == "fire":
        flame = ((xx - cx) ** 2 + (yy - (cy + 3)) ** 2) < (radius * 0.8) ** 2
        out[flame] = palette[3]
        inner = ((xx - cx) ** 2 + (yy - cy) ** 2) < (radius * 0.45) ** 2
        out[inner] = palette[2]
    elif family == "ice":
        diamond = np.abs(xx - cx) + np.abs(yy - cy) < radius
        out[diamond] = palette[3]
    elif family == "lightning":
        bolt = (
            (xx > cx - 4)
            & (xx < cx + 4)
            & (yy > cy - 14)
            & (yy < cy + 14)
            & (((yy - cy) > (xx - cx) * 1.5) | ((yy - cy) < (xx - cx) * -1.5))
        )
        out[bolt] = palette[3]
    elif family == "heal":
        out[cy - 12 : cy + 12, cx - 4 : cx + 4] = palette[3]
        out[cy - 4 : cy + 4, cx - 12 : cx + 12] = palette[3]
    elif family == "poison":
        out[cy - 12 : cy + 12, cx - 4 : cx + 4] = palette[3]
        out[cy + 4 : cy + 8, cx - 6 : cx + 6] = palette[1]
    elif family == "quest":
        star = (np.abs(xx - cx) + np.abs(yy - cy)) < radius
        out[star] = palette[3]
    elif family == "shop":
        out[cy - 10 : cy + 10, cx - 10 : cx + 10] = palette[2]
    elif family == "save":
        out[(xx - cx) ** 2 + (yy - cy) ** 2 <= radius**2] = palette[3]
    else:
        out[(xx - cx) ** 2 + (yy - cy) ** 2 <= radius**2] = palette[2]
    return out
