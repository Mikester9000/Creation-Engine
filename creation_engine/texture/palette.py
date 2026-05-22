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
    # Extended faction palettes
    "imperial_gold": ((88, 72, 40), (138, 110, 56), (188, 158, 74), (232, 210, 128)),
    "imperial_dark": ((42, 46, 58), (66, 74, 92), (100, 110, 130), (158, 166, 186)),
    "rebel_earth": ((58, 46, 32), (96, 78, 54), (144, 116, 80), (196, 162, 108)),
    "royal_crimson": ((82, 24, 28), (120, 38, 44), (168, 68, 72), (216, 136, 130)),
    "sacred_dawn": ((148, 118, 72), (196, 164, 104), (232, 208, 148), (252, 242, 198)),
    "sacred_dusk": ((106, 76, 58), (148, 108, 80), (192, 152, 112), (236, 200, 158)),
    "corrupted_void": ((28, 20, 38), (48, 36, 64), (76, 54, 98), (122, 86, 148)),
    "corrupted_plague": ((38, 52, 28), (62, 88, 40), (90, 124, 54), (138, 176, 88)),
    # Extended biome palettes
    "deep_forest": ((18, 54, 26), (42, 88, 42), (86, 126, 58), (148, 172, 88)),
    "snowfield": ((172, 190, 210), (198, 214, 228), (220, 232, 240), (242, 248, 252)),
    "arctic": ((98, 128, 162), (142, 172, 198), (186, 208, 224), (224, 238, 246)),
    "swamp": ((38, 60, 36), (60, 90, 54), (88, 120, 72), (132, 158, 96)),
    "river": ((36, 96, 142), (72, 136, 172), (118, 172, 196), (178, 214, 224)),
    "cave": ((36, 34, 40), (62, 60, 68), (94, 90, 100), (138, 132, 146)),
    "dungeon": ((44, 40, 48), (72, 68, 78), (106, 100, 112), (158, 148, 164)),
    "overworld": ((52, 106, 58), (94, 148, 78), (144, 182, 106), (200, 214, 148)),
    "port": ((44, 80, 112), (80, 124, 158), (130, 168, 192), (194, 216, 226)),
    "capital": ((72, 76, 88), (108, 114, 132), (154, 160, 176), (210, 208, 200)),
    # Narrative mood palettes
    "ancient_kingdom": ((68, 54, 40), (108, 86, 62), (158, 130, 94), (212, 180, 134)),
    "fallen_empire": ((58, 62, 74), (88, 94, 110), (128, 132, 148), (186, 182, 176)),
    "living_wilds": ((38, 92, 44), (74, 134, 68), (118, 168, 88), (176, 202, 126)),
    "haunted_ruin": ((48, 44, 54), (76, 70, 84), (108, 100, 116), (158, 148, 168)),
    "crystal_shrine": ((96, 148, 178), (136, 188, 210), (178, 218, 232), (220, 242, 248)),
    "magitek_forge": ((62, 68, 82), (92, 102, 120), (136, 148, 168), (196, 204, 214)),
    "summon_realm": ((74, 44, 96), (110, 68, 140), (154, 106, 186), (210, 162, 232)),
}

_PALETTE_ALIASES = {
    "ruins": "ruin",
    "holy": "sacred",
    "city": "imperial",
    "capital": "capital",
    "port": "port",
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
    "dungeon": "dungeon",
    "cave": "cave",
    "overworld": "overworld",
    "snowfield": "snowfield",
    "snow": "snowfield",
    "swamp": "swamp",
    "forest": "forest",
    "desert": "desert",
    "shrine": "sacred",
    "temple": "temple",
    "royal": "royal",
    "shadow": "shadow",
    "fire": "fire",
    "ice": "ice",
    "town": "town",
    "kingdom": "ancient_kingdom",
    "crystal": "crystal_shrine",
    "magitek": "magitek_forge",
    "summon": "summon_realm",
}


def select_palette(family: str, seed: int) -> np.ndarray:
    family_key = family if family in PALETTE_FAMILIES else _PALETTE_ALIASES.get(family, family)
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
