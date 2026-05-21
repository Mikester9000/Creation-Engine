from __future__ import annotations

import numpy as np

PALETTE_FAMILIES = {
    "forest": ((28, 74, 36), (62, 110, 52), (118, 152, 76), (182, 194, 108)),
    "desert": ((120, 92, 52), (168, 136, 76), (214, 186, 124), (238, 220, 164)),
    "coast": ((40, 88, 126), (84, 138, 172), (140, 178, 194), (210, 220, 206)),
    "ruin": ((52, 52, 58), (92, 92, 98), (128, 122, 110), (174, 162, 146)),
    "temple": ((76, 64, 58), (118, 102, 88), (166, 152, 130), (222, 210, 182)),
    "fire": ((110, 24, 12), (168, 44, 18), (214, 96, 22), (248, 176, 64)),
    "ice": ((46, 82, 120), (88, 134, 176), (148, 188, 214), (216, 236, 242)),
    "poison": ((36, 72, 26), (64, 110, 32), (94, 146, 40), (162, 212, 76)),
    "holy": ((124, 104, 46), (176, 154, 72), (224, 206, 120), (246, 238, 188)),
    "shadow": ((16, 18, 28), (34, 38, 56), (58, 64, 88), (102, 110, 138)),
    "town": ((88, 64, 44), (126, 90, 62), (174, 128, 92), (216, 178, 132)),
    "royal": ((62, 46, 110), (100, 76, 160), (148, 120, 198), (216, 192, 240)),
    "imperial": ((68, 72, 84), (98, 108, 128), (148, 156, 170), (210, 198, 182)),
    "rebel": ((64, 52, 38), (110, 86, 60), (168, 126, 84), (222, 188, 122)),
    "sacred": ((128, 114, 72), (176, 160, 102), (224, 210, 148), (250, 244, 202)),
    "corrupted": ((34, 24, 46), (58, 40, 78), (92, 62, 116), (148, 102, 172)),
    "village": ((92, 70, 50), (130, 98, 70), (178, 140, 100), (224, 186, 134)),
    "underworld": ((22, 20, 30), (44, 40, 58), (72, 66, 90), (118, 108, 142)),
    "highlands": ((72, 92, 66), (110, 132, 94), (154, 170, 118), (206, 214, 160)),
    "volcanic": ((76, 34, 24), (126, 52, 32), (178, 80, 42), (228, 132, 58)),
    "wasteland": ((86, 76, 62), (126, 112, 90), (170, 152, 122), (208, 190, 152)),
}

_PALETTE_ALIASES = {
    "ruins": "ruin",
    "holy": "sacred",
    "city": "imperial",
    "capital": "imperial",
    "port": "coast",
    "coastal": "coast",
    "harbor": "coast",
    "village": "village",
    "rebel": "rebel",
    "imperial": "imperial",
    "corrupted": "corrupted",
    "underworld": "underworld",
    "highlands": "highlands",
    "volcanic": "volcanic",
    "wasteland": "wasteland",
}


def select_palette(family: str, seed: int) -> np.ndarray:
    family_key = _PALETTE_ALIASES.get(family, family)
    colors = PALETTE_FAMILIES.get(family_key, PALETTE_FAMILIES["town"])
    base = np.array(colors, dtype=np.float32)
    rng = np.random.default_rng(seed)
    jitter = rng.integers(-12, 13, size=base.shape, dtype=np.int16).astype(np.float32)
    return np.clip(base + jitter, 0, 255).astype(np.uint8)


def pick_palette_family(tokens: list[str]) -> str:
    for token in tokens:
        if token in PALETTE_FAMILIES:
            return token
        alias = _PALETTE_ALIASES.get(token)
        if alias in PALETTE_FAMILIES:
            return alias
    return "town"
