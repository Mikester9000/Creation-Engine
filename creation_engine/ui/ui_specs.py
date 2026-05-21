from __future__ import annotations

UI_ICON_FAMILIES = {
    "weapon": {
        "aliases": {"weapon", "sword", "blade", "axe"},
        "palette": "royal",
        "shape": "blade",
    },
    "armor": {
        "aliases": {"armor", "shield", "helm", "plate"},
        "palette": "holy",
        "shape": "shield",
    },
    "potion": {
        "aliases": {"potion", "vial", "flask", "heal"},
        "palette": "forest",
        "shape": "bottle",
    },
    "fire": {"aliases": {"fire", "flame", "lava"}, "palette": "fire", "shape": "flame"},
    "ice": {"aliases": {"ice", "snow", "frost"}, "palette": "ice", "shape": "crystal"},
    "lightning": {"aliases": {"lightning", "bolt", "thunder"}, "palette": "holy", "shape": "bolt"},
    "heal": {"aliases": {"heal", "restore", "cure"}, "palette": "holy", "shape": "cross"},
    "poison": {"aliases": {"poison", "venom", "toxic"}, "palette": "poison", "shape": "skull"},
    "quest": {"aliases": {"quest", "objective", "mission"}, "palette": "royal", "shape": "star"},
    "shop": {"aliases": {"shop", "trade", "merchant"}, "palette": "town", "shape": "coin"},
    "save": {"aliases": {"save", "checkpoint", "crystal"}, "palette": "holy", "shape": "crystal"},
    "map": {"aliases": {"map", "world", "location"}, "palette": "desert", "shape": "scroll"},
}

UI_PANEL_FAMILIES = {
    "menu_frame": {"aliases": {"menu", "frame", "window"}, "palette": "royal"},
    "hud_bar": {"aliases": {"hud", "bar", "status"}, "palette": "town"},
    "dialog_box": {"aliases": {"dialog", "speech", "textbox"}, "palette": "holy"},
    "inventory_slot": {"aliases": {"inventory", "slot", "grid"}, "palette": "stone"},
    "tooltip_box": {"aliases": {"tooltip", "hint", "popup"}, "palette": "shadow"},
}

UI_PORTRAIT_FAMILIES = {
    "hero": {"aliases": {"hero", "protagonist", "leader"}, "palette": "royal"},
    "mage": {"aliases": {"mage", "wizard", "sorcerer"}, "palette": "royal"},
    "knight": {"aliases": {"knight", "warrior", "paladin"}, "palette": "holy"},
    "rogue": {"aliases": {"rogue", "thief", "assassin"}, "palette": "shadow"},
    "cleric": {"aliases": {"cleric", "priest", "healer"}, "palette": "holy"},
    "beast": {"aliases": {"beast", "wolf", "lion"}, "palette": "forest"},
    "undead": {"aliases": {"undead", "ghost", "skeleton"}, "palette": "shadow"},
    "merchant": {"aliases": {"merchant", "shopkeeper", "trader"}, "palette": "town"},
}


def _match_family(prompt: str, spec: dict[str, dict[str, object]], default: str) -> str:
    tokens = set(prompt.lower().split())
    for family, data in spec.items():
        if tokens.intersection(data["aliases"]):
            return family
    return default


def resolve_ui_icon_family(prompt: str) -> str:
    return _match_family(prompt, UI_ICON_FAMILIES, "quest")


def resolve_ui_panel_family(prompt: str) -> str:
    return _match_family(prompt, UI_PANEL_FAMILIES, "menu_frame")


def resolve_ui_portrait_family(prompt: str) -> str:
    return _match_family(prompt, UI_PORTRAIT_FAMILIES, "hero")
