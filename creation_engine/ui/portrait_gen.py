from __future__ import annotations

import numpy as np

from creation_engine.texture.palette import select_palette
from creation_engine.ui.ui_specs import UI_PORTRAIT_FAMILIES, resolve_ui_portrait_family


def generate_ui_portrait(prompt: str, seed: int = 42, size: int = 96) -> np.ndarray:
    family = resolve_ui_portrait_family(prompt)
    palette = select_palette(UI_PORTRAIT_FAMILIES[family]["palette"], seed)
    image = np.zeros((size, size, 3), dtype=np.uint8)
    image[...] = palette[0]
    yy, xx = np.ogrid[:size, :size]
    cx, cy = size // 2, size // 2
    face = (xx - cx) ** 2 + (yy - (cy - 4)) ** 2 <= (size * 0.22) ** 2
    shoulders = (np.abs(xx - cx) < size * 0.28) & (yy > size * 0.58)
    image[face] = palette[3]
    image[shoulders] = palette[1]
    if family in {"knight", "cleric"}:
        image[face & (yy < cy)] = palette[2]
    elif family == "mage":
        image[: int(size * 0.34), :, :] = palette[2]
    elif family == "rogue":
        image[(xx < cx) & (yy > size * 0.2) & (yy < size * 0.8)] = palette[2]
    elif family == "beast":
        image[(xx - cx) ** 2 + (yy - cy) ** 2 <= (size * 0.28) ** 2] = palette[2]
    elif family == "undead":
        image[face] = palette[1]
        image[(xx - cx) ** 2 + (yy - (cy - 4)) ** 2 <= (size * 0.12) ** 2] = palette[3]
    elif family == "merchant":
        image[yy > size * 0.26] = palette[2]
    return image
