from __future__ import annotations

MATERIAL_PRESETS = {
    "stone": {"base_color": (112, 112, 120), "roughness": 0.82, "metallic": 0.02, "ao": 0.92},
    "brick": {"base_color": (140, 76, 66), "roughness": 0.78, "metallic": 0.01, "ao": 0.90},
    "dirt": {"base_color": (118, 88, 58), "roughness": 0.87, "metallic": 0.00, "ao": 0.92},
    "grass": {"base_color": (74, 116, 58), "roughness": 0.83, "metallic": 0.00, "ao": 0.95},
    "sand": {"base_color": (196, 180, 128), "roughness": 0.91, "metallic": 0.00, "ao": 0.89},
    "wood": {"base_color": (124, 90, 58), "roughness": 0.73, "metallic": 0.01, "ao": 0.90},
    "bark": {"base_color": (84, 62, 48), "roughness": 0.89, "metallic": 0.00, "ao": 0.91},
    "leaf": {"base_color": (60, 122, 54), "roughness": 0.74, "metallic": 0.00, "ao": 0.93},
    "water": {"base_color": (44, 110, 180), "roughness": 0.10, "metallic": 0.00, "ao": 0.98},
    "metal": {"base_color": (152, 156, 168), "roughness": 0.26, "metallic": 0.92, "ao": 0.95},
    "cloth": {"base_color": (106, 92, 142), "roughness": 0.87, "metallic": 0.00, "ao": 0.92},
    "leather": {"base_color": (126, 82, 48), "roughness": 0.76, "metallic": 0.00, "ao": 0.90},
    "crystal": {"base_color": (120, 180, 220), "roughness": 0.18, "metallic": 0.08, "ao": 0.96},
    "lava": {"base_color": (202, 72, 24), "roughness": 0.53, "metallic": 0.00, "ao": 0.86},
    "snow": {"base_color": (230, 238, 245), "roughness": 0.93, "metallic": 0.00, "ao": 0.97},
    "ice": {"base_color": (176, 214, 232), "roughness": 0.24, "metallic": 0.03, "ao": 0.95},
    "marble": {"base_color": (210, 206, 198), "roughness": 0.40, "metallic": 0.02, "ao": 0.94},
    "rune": {"base_color": (96, 86, 132), "roughness": 0.52, "metallic": 0.05, "ao": 0.92},
    "bone": {"base_color": (214, 206, 176), "roughness": 0.66, "metallic": 0.00, "ao": 0.90},
}

MATERIAL_MODIFIERS = {
    "ancient": {"brightness": 0.88, "roughness_add": 0.10, "metallic_mul": 0.90},
    "cracked": {"brightness": 0.93, "roughness_add": 0.09, "metallic_mul": 0.80},
    "wet": {"brightness": 0.86, "roughness_add": -0.35, "metallic_mul": 1.00},
    "dry": {"brightness": 1.02, "roughness_add": 0.12, "metallic_mul": 0.90},
    "polished": {"brightness": 1.08, "roughness_add": -0.25, "metallic_mul": 1.15},
    "mossy": {"brightness": 0.90, "roughness_add": 0.08, "metallic_mul": 0.80},
    "rusty": {"brightness": 0.94, "roughness_add": 0.14, "metallic_mul": 0.85},
    "blessed": {"brightness": 1.10, "roughness_add": -0.04, "metallic_mul": 1.05},
    "cursed": {"brightness": 0.80, "roughness_add": 0.10, "metallic_mul": 0.92},
    "dark": {"brightness": 0.70, "roughness_add": 0.02, "metallic_mul": 1.00},
    "light": {"brightness": 1.15, "roughness_add": -0.02, "metallic_mul": 1.00},
}
