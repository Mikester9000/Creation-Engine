from __future__ import annotations

import numpy as np

from creation_engine.texture.palette import select_palette
from creation_engine.ui.ui_specs import UI_PANEL_FAMILIES, resolve_ui_panel_family


def generate_ui_panel(prompt: str, seed: int = 42, size: tuple[int, int] = (256, 64)) -> np.ndarray:
    family = resolve_ui_panel_family(prompt)
    palette = select_palette(UI_PANEL_FAMILIES[family]["palette"], seed)
    width, height = size
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[...] = palette[0]
    border = max(2, min(width, height) // 10)
    image[:border, :, :] = palette[3]
    image[-border:, :, :] = palette[1]
    image[:, :border, :] = palette[2]
    image[:, -border:, :] = palette[2]
    inner = image[border:-border, border:-border]
    if inner.size:
        gradient = np.linspace(0, 1, inner.shape[1], dtype=np.float32)[None, :, None]
        inner[:] = np.clip(inner * 0.6 + palette[1] * 0.4 + gradient * 18, 0, 255).astype(np.uint8)
    return _decorate_panel(image, family, palette)


def _decorate_panel(image: np.ndarray, family: str, palette: np.ndarray) -> np.ndarray:
    out = image.copy()
    h, w = out.shape[:2]
    if family == "hud_bar":
        out[h // 2 - 3 : h // 2 + 3, 8 : w - 8] = palette[3]
    elif family == "dialog_box":
        out[h - 12 : h - 6, 12 : w - 12] = palette[2]
    elif family == "inventory_slot":
        slot = min(h, w) // 4
        for row in range(2):
            for col in range(3):
                y0 = 8 + row * (slot + 6)
                x0 = 8 + col * (slot + 6)
                out[y0 : y0 + slot, x0 : x0 + slot] = palette[2]
    elif family == "tooltip_box":
        out[8 : h - 8, 8 : w - 8] = palette[1]
    return out
