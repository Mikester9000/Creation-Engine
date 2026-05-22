from __future__ import annotations

import argparse

from creation_engine.backend import BackendRegistry
from creation_engine.engine import CreationEngine
from creation_engine.quality_check import run_bundle_audit, run_quality_check


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="creation-engine", description="Creation Engine CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    texture = subparsers.add_parser("texture", help="Generate PBR textures")
    texture.add_argument("--prompt", required=True)
    texture.add_argument("--seed", type=int, default=42)
    texture.add_argument("--output", default="assets")
    texture.add_argument("--backend", default="procedural")
    texture.add_argument("--width", type=int, default=64)
    texture.add_argument("--height", type=int, default=64)
    texture.add_argument("--name")

    tilemap = subparsers.add_parser("map", help="Generate tilemap")
    tilemap.add_argument("--prompt", required=True)
    tilemap.add_argument("--seed", type=int, default=42)
    tilemap.add_argument("--output", default="assets")
    tilemap.add_argument("--backend", default="procedural")
    tilemap.add_argument("--width", type=int, default=64)
    tilemap.add_argument("--height", type=int, default=64)
    tilemap.add_argument("--name")

    mesh = subparsers.add_parser("mesh", help="Generate 3D mesh")
    mesh.add_argument("--prompt", required=True)
    mesh.add_argument("--seed", type=int, default=42)
    mesh.add_argument("--output", default="assets")
    mesh.add_argument("--backend", default="procedural")
    mesh.add_argument("--complexity", default="medium", choices=["low", "medium", "high"])
    mesh.add_argument("--name")

    _add_prompted_image_command(subparsers, "ui-icon", "Generate UI icon", "--prompt")
    _add_prompted_image_command(subparsers, "ui-panel", "Generate UI panel", "--prompt")
    _add_prompted_image_command(subparsers, "portrait", "Generate portrait card", "--prompt")

    for command, help_text in [
        ("material-pack", "Generate material pack"),
        ("biome-pack", "Generate biome pack"),
        ("tileset-pack", "Generate tileset pack"),
        ("prop-pack", "Generate prop pack"),
        ("architecture-pack", "Generate architecture pack"),
        ("foliage-pack", "Generate foliage pack"),
        ("item-pack", "Generate item pack"),
        ("decal-pack", "Generate decal pack"),
        ("character-static-pack", "Generate static character pack"),
        ("enemy-static-pack", "Generate static enemy pack"),
        ("full-bundle", "Generate full GameRewritten bundle"),
    ]:
        pack = subparsers.add_parser(command, help=help_text)
        pack.add_argument("--seed", type=int, default=42)
        pack.add_argument("--output", default="assets")

    quality_check = subparsers.add_parser(
        "quality-check",
        help="Validate generated assets for GameRewritten compatibility quality",
    )
    quality_check.add_argument("--output", default="assets")
    quality_check.add_argument("--min-png-size", type=int, default=64)
    bundle_audit = subparsers.add_parser(
        "bundle-audit",
        help="Summarize production bundle coverage and FF style compliance",
    )
    bundle_audit.add_argument("--output", default="assets")

    subparsers.add_parser("list-backends", help="List available backends")

    return parser


def _add_prompted_image_command(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    command: str,
    help_text: str,
    prompt_flag: str,
) -> None:
    parser = subparsers.add_parser(command, help=help_text)
    parser.add_argument(prompt_flag, dest="prompt", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="assets")
    parser.add_argument("--name")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list-backends":
        for backend_name in BackendRegistry.available():
            print(backend_name)
        return 0
    if args.command == "quality-check":
        result = run_quality_check(args.output, min_png_size=args.min_png_size)
        if result.ok:
            print(f"Quality check passed ({result.checked_manifests} manifests validated)")
            return 0
        print("Quality check failed:")
        for error in result.errors:
            print(f"- {error}")
        return 1
    if args.command == "bundle-audit":
        result = run_bundle_audit(args.output)
        print(f"Bundle audit checked manifests: {result.checked_manifests}")
        print("Family counts:")
        for family, count in result.family_counts.items():
            print(f"- {family}: {count}")
        print(
            "Narrative coverage: "
            f"{result.narrative_coverage['present']}/{result.narrative_coverage['required']}"
        )
        print(
            "Style coverage: "
            f"{result.style_coverage['passing']}/{result.style_coverage['required']}"
        )
        print(
            "FF aesthetic compliance: "
            + ("PASS" if result.ff_aesthetic_compliant else "FAIL")
        )
        if result.errors:
            print("Bundle audit errors:")
            for error in result.errors:
                print(f"- {error}")
            return 1
        return 0

    if args.command in {"texture", "map", "mesh"}:
        engine = CreationEngine(backend=args.backend, seed=args.seed, output_dir=args.output)
    else:
        engine = CreationEngine(seed=args.seed, output_dir=args.output)

    if args.command == "texture":
        path = engine.generate_texture(
            prompt=args.prompt,
            width=args.width,
            height=args.height,
            output_dir=args.output,
            name=args.name,
            seed=args.seed,
        )
    elif args.command == "map":
        path = engine.generate_map(
            prompt=args.prompt,
            width=args.width,
            height=args.height,
            output_dir=args.output,
            name=args.name,
            seed=args.seed,
        )
    elif args.command == "mesh":
        path = engine.generate_mesh(
            prompt=args.prompt,
            complexity=args.complexity,
            output_dir=args.output,
            name=args.name,
            seed=args.seed,
        )
    elif args.command == "ui-icon":
        path = engine.generate_ui_icon(
            prompt=args.prompt, seed=args.seed, output_dir=args.output, name=args.name
        )
    elif args.command == "ui-panel":
        path = engine.generate_ui_panel(
            prompt=args.prompt, seed=args.seed, output_dir=args.output, name=args.name
        )
    elif args.command == "portrait":
        path = engine.generate_portrait(
            prompt=args.prompt, seed=args.seed, output_dir=args.output, name=args.name
        )
    elif args.command == "material-pack":
        path = engine.generate_material_pack(seed=args.seed, output_dir=args.output)
    elif args.command == "biome-pack":
        path = engine.generate_terrain_pack(seed=args.seed, output_dir=args.output)
    elif args.command == "tileset-pack":
        path = engine.generate_tileset_pack(seed=args.seed, output_dir=args.output)
    elif args.command == "prop-pack":
        path = engine.generate_prop_pack(seed=args.seed, output_dir=args.output)
    elif args.command == "architecture-pack":
        path = engine.generate_architecture_pack(seed=args.seed, output_dir=args.output)
    elif args.command == "foliage-pack":
        path = engine.generate_foliage_pack(seed=args.seed, output_dir=args.output)
    elif args.command == "item-pack":
        path = engine.generate_item_pack(seed=args.seed, output_dir=args.output)
    elif args.command == "decal-pack":
        path = engine.generate_decal_pack(seed=args.seed, output_dir=args.output)
    elif args.command == "character-static-pack":
        path = engine.generate_character_static_pack(seed=args.seed, output_dir=args.output)
    elif args.command == "enemy-static-pack":
        path = engine.generate_enemy_static_pack(seed=args.seed, output_dir=args.output)
    elif args.command == "full-bundle":
        path = engine.generate_full_bundle(seed=args.seed, output_dir=args.output)
    else:
        parser.error(f"Unknown command: {args.command}")

    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
