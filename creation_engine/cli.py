from __future__ import annotations

import argparse

from creation_engine.backend import BackendRegistry
from creation_engine.engine import CreationEngine


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

    subparsers.add_parser("list-backends", help="List available backends")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list-backends":
        for backend_name in BackendRegistry.available():
            print(backend_name)
        return 0

    engine = CreationEngine(backend=args.backend, seed=args.seed, output_dir=args.output)

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
    else:
        parser.error(f"Unknown command: {args.command}")
        return 2

    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
