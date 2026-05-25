from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageOps

from creation_engine.quality_check import run_bundle_audit, run_quality_check, run_release_readiness_check


SUPPORTED_BROWSER_SUFFIXES = {
    ".json",
    ".obj",
    ".mtl",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
}


DEFAULT_NEW_FILE_TEMPLATES: dict[str, str] = {
    ".json": '{\n  "name": "new_asset",\n  "version": "1.0"\n}\n',
    ".txt": "",
    ".obj": "# Simple quad\nv -0.5 0.0 -0.5\nv 0.5 0.0 -0.5\nv 0.5 0.0 0.5\nv -0.5 0.0 0.5\nf 1 2 3\nf 1 3 4\n",
}


def _manifest_files(manifest: dict[str, Any]) -> dict[str, Any]:
    if isinstance(manifest.get("files"), dict):
        return manifest["files"]
    if isinstance(manifest.get("textures"), dict):
        return manifest["textures"]
    return {}


def _read_image_array(path: Path, size: tuple[int, int]) -> np.ndarray:
    image = Image.open(path).convert("RGB").resize(size, Image.Resampling.NEAREST)
    return np.asarray(image, dtype=np.float32) / 255.0


def _filter_file_index(file_index: list[Path], output_dir: Path, query: str) -> list[Path]:
    lowered_query = query.lower()
    return [path for path in file_index if lowered_query in str(path.relative_to(output_dir)).lower()]


def render_material_preview(manifest: dict[str, Any], manifest_path: Path) -> Image.Image:
    files = _manifest_files(manifest)
    albedo_name = files.get("albedo") or files.get("image")
    if not isinstance(albedo_name, str):
        raise ValueError("Manifest has no previewable texture entry.")

    material_dir = manifest_path.parent
    albedo_path = material_dir / albedo_name
    if not albedo_path.exists():
        raise FileNotFoundError(f"Missing texture: {albedo_path}")

    width = int(manifest.get("width", 256))
    height = int(manifest.get("height", 256))
    size = (max(1, width), max(1, height))
    albedo = _read_image_array(albedo_path, size)

    roughness = np.ones((size[1], size[0]), dtype=np.float32) * 0.6
    metallic = np.zeros((size[1], size[0]), dtype=np.float32)
    emissive = np.zeros((size[1], size[0], 3), dtype=np.float32)
    normal = np.dstack(
        (
            np.zeros((size[1], size[0]), dtype=np.float32),
            np.zeros((size[1], size[0]), dtype=np.float32),
            np.ones((size[1], size[0]), dtype=np.float32),
        )
    )

    if isinstance(files.get("roughness"), str) and (material_dir / files["roughness"]).exists():
        roughness = _read_image_array(material_dir / files["roughness"], size).mean(axis=2)
    if isinstance(files.get("metallic"), str) and (material_dir / files["metallic"]).exists():
        metallic = _read_image_array(material_dir / files["metallic"], size).mean(axis=2)
    if isinstance(files.get("emissive"), str) and files["emissive"]:
        emissive_path = material_dir / files["emissive"]
        if emissive_path.exists():
            emissive = _read_image_array(emissive_path, size)
    if isinstance(files.get("normal"), str) and (material_dir / files["normal"]).exists():
        normal_rgb = _read_image_array(material_dir / files["normal"], size)
        normal = (normal_rgb * 2.0) - 1.0
        norm = np.linalg.norm(normal, axis=2, keepdims=True)
        normal = normal / np.maximum(norm, 1e-4)

    light = np.array([0.4, -0.35, 0.85], dtype=np.float32)
    light /= np.linalg.norm(light)
    diffuse = np.clip(np.sum(normal * light[None, None, :], axis=2), 0.0, 1.0)
    ambient = 0.35
    specular = np.power(np.clip(diffuse, 0.0, 1.0), 18.0) * (1.0 - roughness)
    metallic_tint = np.clip(albedo * metallic[:, :, None], 0.0, 1.0)

    lit = (
        albedo * (ambient + diffuse[:, :, None] * 0.75)
        + specular[:, :, None] * (0.15 + metallic[:, :, None] * 0.2)
        + metallic_tint * 0.1
        + emissive * 0.7
    )
    lit = np.clip(lit, 0.0, 1.0)
    rendered = (lit * 255.0).astype(np.uint8)
    return Image.fromarray(rendered, mode="RGB")


def render_map_preview(map_data: dict[str, Any], tile_px: int = 10) -> Image.Image:
    raw_tiles = map_data.get("tiles")
    width = int(map_data.get("width", 0))
    height = int(map_data.get("height", 0))
    if not isinstance(raw_tiles, list) or width < 1 or height < 1:
        raise ValueError("Map JSON missing width, height, or tile data.")
    if raw_tiles and isinstance(raw_tiles[0], list):
        flattened: list[int] = []
        for row in raw_tiles:
            if not isinstance(row, list):
                raise ValueError("Map tile rows must be arrays of tile IDs.")
            flattened.extend(int(tile) for tile in row)
        raw_tiles = flattened
    if len(raw_tiles) != width * height:
        raise ValueError("Map tile data length does not match width*height.")

    color_map: dict[int, tuple[int, int, int]] = {
        0: (110, 95, 85),
        1: (55, 55, 60),
        2: (25, 85, 160),
        3: (52, 130, 62),
        4: (180, 165, 110),
        5: (42, 95, 48),
        6: (118, 112, 128),
        7: (145, 120, 90),
        8: (178, 142, 96),
        9: (190, 210, 240),
        10: (120, 155, 215),
        11: (205, 160, 95),
        12: (95, 220, 255),
        13: (220, 180, 90),
        14: (255, 225, 160),
        15: (126, 93, 70),
    }
    canvas = np.zeros((height * tile_px, width * tile_px, 3), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            tile_id = int(raw_tiles[y * width + x])
            color = color_map.get(tile_id, (255, 0, 255))
            canvas[y * tile_px : (y + 1) * tile_px, x * tile_px : (x + 1) * tile_px, :] = color
    return Image.fromarray(canvas, mode="RGB")


def render_map_3d_preview(map_data: dict[str, Any], tile_px: int = 18) -> Image.Image:
    raw_tiles = map_data.get("tiles")
    width = int(map_data.get("width", 0))
    height = int(map_data.get("height", 0))
    if not isinstance(raw_tiles, list) or width < 1 or height < 1:
        raise ValueError("Map JSON missing width, height, or tile data.")
    if raw_tiles and isinstance(raw_tiles[0], list):
        flattened: list[int] = []
        for row in raw_tiles:
            if not isinstance(row, list):
                raise ValueError("Map tile rows must be arrays of tile IDs.")
            flattened.extend(int(tile) for tile in row)
        raw_tiles = flattened
    if len(raw_tiles) != width * height:
        raise ValueError("Map tile data length does not match width*height.")
    if tile_px < 2:
        raise ValueError("tile_px must be >= 2 for 3D map preview rendering.")

    color_map: dict[int, tuple[int, int, int]] = {
        0: (118, 101, 90),
        1: (82, 82, 88),
        2: (48, 118, 194),
        3: (72, 154, 88),
        4: (200, 184, 128),
        5: (64, 121, 72),
        6: (143, 137, 151),
        7: (170, 143, 107),
        8: (203, 170, 118),
        9: (208, 226, 246),
        10: (147, 184, 232),
        11: (220, 178, 114),
        12: (125, 231, 255),
        13: (240, 200, 104),
        14: (255, 236, 182),
        15: (145, 110, 84),
    }
    water_tiles = {2, 12}
    wall_tiles = {1, 6}
    high_tiles = {9, 10, 14}

    canvas_width = (width + height + 2) * tile_px
    canvas_height = (width + height + 4) * (tile_px // 2)
    image = Image.new("RGB", (canvas_width, canvas_height), (18, 20, 28))
    draw = ImageDraw.Draw(image)

    origin_x = canvas_width // 2
    origin_y = tile_px
    half_w = tile_px // 2
    half_h = max(1, tile_px // 4)

    def shade(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
        return tuple(max(0, min(255, int(c * factor))) for c in color)

    for y in range(height):
        for x in range(width):
            tile_id = int(raw_tiles[y * width + x])
            base = color_map.get(tile_id, (255, 0, 255))
            level = 1
            if tile_id in wall_tiles:
                level = 3
            elif tile_id in high_tiles:
                level = 2
            elif tile_id in water_tiles:
                level = 0

            sx = origin_x + (x - y) * half_w
            sy = origin_y + (x + y) * half_h
            top_y = sy - (level * half_h)

            top = [
                (sx, top_y - half_h),
                (sx + half_w, top_y),
                (sx, top_y + half_h),
                (sx - half_w, top_y),
            ]
            right = [
                top[1],
                top[2],
                (top[2][0], top[2][1] + level * half_h),
                (top[1][0], top[1][1] + level * half_h),
            ]
            left = [
                top[2],
                top[3],
                (top[3][0], top[3][1] + level * half_h),
                (top[2][0], top[2][1] + level * half_h),
            ]

            if level > 0:
                draw.polygon(right, fill=shade(base, 0.75))
                draw.polygon(left, fill=shade(base, 0.6))
            draw.polygon(top, fill=base)
            draw.line(top + [top[0]], fill=shade(base, 0.45), width=1)

    return image


def render_obj_preview(obj_text: str, size: tuple[int, int] = (720, 720)) -> Image.Image:
    vertices: list[list[float]] = []
    edges: set[tuple[int, int]] = set()

    for line in obj_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if parts[0] == "v" and len(parts) >= 4:
            vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
        elif parts[0] == "f" and len(parts) >= 4:
            indices: list[int] = []
            for part in parts[1:]:
                idx_str = part.split("/")[0]
                idx = int(idx_str)
                if idx < 0:
                    idx = len(vertices) + idx + 1
                indices.append(idx - 1)
            for i in range(len(indices)):
                a = indices[i]
                b = indices[(i + 1) % len(indices)]
                if a == b:
                    continue
                if a < 0 or b < 0:
                    continue
                edges.add((min(a, b), max(a, b)))

    if not vertices:
        raise ValueError("OBJ data has no vertices.")

    verts = np.asarray(vertices, dtype=np.float32)
    center = verts.mean(axis=0)
    verts -= center
    scale = max(np.max(np.abs(verts)), 1e-4)
    verts /= scale

    yaw = np.radians(38.0)
    pitch = np.radians(24.0)
    rot_y = np.array(
        [[np.cos(yaw), 0.0, np.sin(yaw)], [0.0, 1.0, 0.0], [-np.sin(yaw), 0.0, np.cos(yaw)]],
        dtype=np.float32,
    )
    rot_x = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, np.cos(pitch), -np.sin(pitch)],
            [0.0, np.sin(pitch), np.cos(pitch)],
        ],
        dtype=np.float32,
    )
    transformed = verts @ rot_y.T @ rot_x.T

    z = transformed[:, 2] + 3.2
    perspective = 1.6 / np.maximum(z, 0.2)
    projected = transformed[:, :2] * perspective[:, None]

    width, height = size
    coords = np.zeros((projected.shape[0], 2), dtype=np.float32)
    coords[:, 0] = (projected[:, 0] * 0.42 + 0.5) * width
    coords[:, 1] = (0.5 - projected[:, 1] * 0.42) * height

    image = Image.new("RGB", size, (20, 20, 28))
    draw = ImageDraw.Draw(image)
    for a, b in sorted(edges):
        if a >= len(coords) or b >= len(coords):
            continue
        draw.line((coords[a, 0], coords[a, 1], coords[b, 0], coords[b, 1]), fill=(160, 220, 255), width=2)

    for px, py in coords:
        draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill=(255, 210, 110))
    return image


def render_preview_from_json(parsed: dict[str, Any], source_path: Path, use_3d_view: bool = False) -> Image.Image:
    if "tiles" in parsed and "width" in parsed and "height" in parsed:
        if use_3d_view:
            return render_map_3d_preview(parsed)
        return render_map_preview(parsed)
    if "files" in parsed or "textures" in parsed:
        return render_material_preview(parsed, source_path)
    raise ValueError("No preview renderer available for this JSON schema.")


_SINGLE_ASSET_TYPES = [
    "texture",
    "map",
    "mesh",
    "ui-icon",
    "ui-panel",
    "portrait",
]

_PACK_TYPES = [
    "material-pack",
    "biome-pack",
    "tileset-pack",
    "prop-pack",
    "architecture-pack",
    "foliage-pack",
    "item-pack",
    "decal-pack",
    "character-static-pack",
    "enemy-static-pack",
]


class CreationEngineGuiApp:
    def __init__(self, root: Any, output_dir: str | Path, initial_file: str | None = None) -> None:
        self.root = root
        self.output_dir = Path(output_dir)
        self.current_path: Path | None = None
        self.current_is_binary = False
        self.preview_3d_enabled = False
        self.file_index: list[Path] = []
        self._preview_tk = None
        self._gen_panel_visible = False
        self._busy = False

        root.title("Creation Engine – Asset Studio")
        root.geometry("1600x920")

        import tkinter as tk
        from tkinter import BOTH, BOTTOM, LEFT, TOP, W, X, Button, Frame, Label, Listbox, PanedWindow, Text
        from tkinter.scrolledtext import ScrolledText
        from tkinter import ttk

        # ── Toolbar row 1: file operations ──────────────────────────────────
        toolbar = Frame(root, bd=1, relief="raised")
        toolbar.pack(side=TOP, fill=X, padx=0, pady=0)

        Button(toolbar, text="New File", command=self.new_file_dialog, width=9).pack(side=LEFT, padx=2, pady=3)
        Button(toolbar, text="Load File", command=self.load_file_dialog, width=9).pack(side=LEFT, padx=2, pady=3)
        Button(toolbar, text="Save", command=self.save_current, width=6).pack(side=LEFT, padx=2, pady=3)
        Button(toolbar, text="Save As", command=self.save_as_dialog, width=7).pack(side=LEFT, padx=2, pady=3)
        Button(toolbar, text="Delete", command=self.delete_current_file, width=7).pack(side=LEFT, padx=2, pady=3)
        Button(toolbar, text="Refresh Files", command=self.refresh_file_browser, width=11).pack(side=LEFT, padx=2, pady=3)

        ttk.Separator(toolbar, orient="vertical").pack(side=LEFT, fill="y", padx=4, pady=3)

        self.view_mode_btn = Button(toolbar, text="Enable 3D View", command=self.toggle_3d_mode, width=13)
        self.view_mode_btn.pack(side=LEFT, padx=2, pady=3)
        Button(toolbar, text="Refresh Viewer", command=self.refresh_preview, width=12).pack(side=LEFT, padx=2, pady=3)

        ttk.Separator(toolbar, orient="vertical").pack(side=LEFT, fill="y", padx=4, pady=3)

        Button(toolbar, text="Quality Check", command=self.run_quality_check_ui, width=12, bg="#3a7d44", fg="white").pack(side=LEFT, padx=2, pady=3)
        Button(toolbar, text="Bundle Audit", command=self.run_bundle_audit_ui, width=11, bg="#2e6da4", fg="white").pack(side=LEFT, padx=2, pady=3)
        Button(toolbar, text="Release Check", command=self.run_release_check_ui, width=12, bg="#8b1a1a", fg="white").pack(side=LEFT, padx=2, pady=3)

        ttk.Separator(toolbar, orient="vertical").pack(side=LEFT, fill="y", padx=4, pady=3)

        self._gen_toggle_btn = Button(
            toolbar, text="▼ Generate Panel", command=self._toggle_gen_panel, width=15, bg="#4a3c8c", fg="white"
        )
        self._gen_toggle_btn.pack(side=LEFT, padx=2, pady=3)

        self.path_label = Label(toolbar, text="No file loaded", anchor="w", relief="sunken", padx=4)
        self.path_label.pack(side=LEFT, fill=X, expand=True, padx=8, pady=3)

        # ── Generation panel (hidden by default) ────────────────────────────
        self._gen_panel = Frame(root, bd=1, relief="groove", padx=6, pady=4)

        # Row A: single asset generation
        row_a = Frame(self._gen_panel)
        row_a.pack(fill=X, pady=2)
        Label(row_a, text="Asset Type:", width=10, anchor=W).pack(side=LEFT)
        self._gen_type_var = tk.StringVar(value="texture")
        ttk.Combobox(
            row_a, textvariable=self._gen_type_var, values=_SINGLE_ASSET_TYPES, width=14, state="readonly"
        ).pack(side=LEFT, padx=(0, 8))

        Label(row_a, text="Prompt:", width=7, anchor=W).pack(side=LEFT)
        self._gen_prompt_var = tk.StringVar(value="ps2 jrpg wet stone")
        tk.Entry(row_a, textvariable=self._gen_prompt_var, width=44).pack(side=LEFT, padx=(0, 8))

        Label(row_a, text="Seed:", width=5, anchor=W).pack(side=LEFT)
        self._gen_seed_var = tk.StringVar(value="42")
        tk.Entry(row_a, textvariable=self._gen_seed_var, width=7).pack(side=LEFT, padx=(0, 8))

        Label(row_a, text="W:", width=3, anchor=W).pack(side=LEFT)
        self._gen_width_var = tk.StringVar(value="64")
        tk.Entry(row_a, textvariable=self._gen_width_var, width=5).pack(side=LEFT, padx=(0, 4))

        Label(row_a, text="H:", width=3, anchor=W).pack(side=LEFT)
        self._gen_height_var = tk.StringVar(value="64")
        tk.Entry(row_a, textvariable=self._gen_height_var, width=5).pack(side=LEFT, padx=(0, 8))

        Label(row_a, text="Complexity:", width=10, anchor=W).pack(side=LEFT)
        self._gen_complexity_var = tk.StringVar(value="medium")
        ttk.Combobox(
            row_a, textvariable=self._gen_complexity_var, values=["low", "medium", "high"], width=7, state="readonly"
        ).pack(side=LEFT, padx=(0, 8))

        Button(row_a, text="⚙ Generate Asset", command=self.generate_single_asset_ui, bg="#4a8c6a", fg="white", width=15).pack(side=LEFT, padx=4)

        # Row B: pack & bundle generation
        row_b = Frame(self._gen_panel)
        row_b.pack(fill=X, pady=2)
        Label(row_b, text="Pack Type:", width=10, anchor=W).pack(side=LEFT)
        self._pack_type_var = tk.StringVar(value="material-pack")
        ttk.Combobox(
            row_b, textvariable=self._pack_type_var, values=_PACK_TYPES, width=18, state="readonly"
        ).pack(side=LEFT, padx=(0, 8))

        Label(row_b, text="Seed:", width=5, anchor=W).pack(side=LEFT)
        self._pack_seed_var = tk.StringVar(value="42")
        tk.Entry(row_b, textvariable=self._pack_seed_var, width=7).pack(side=LEFT, padx=(0, 8))

        Button(row_b, text="⚙ Generate Pack", command=self.generate_pack_ui, bg="#4a6a8c", fg="white", width=14).pack(side=LEFT, padx=4)

        Label(row_b, text="  │", width=3).pack(side=LEFT)

        Label(row_b, text="Bundle Seed:", width=12, anchor=W).pack(side=LEFT)
        self._bundle_seed_var = tk.StringVar(value="42")
        tk.Entry(row_b, textvariable=self._bundle_seed_var, width=7).pack(side=LEFT, padx=(0, 8))

        Button(row_b, text="⚙ Generate Full Bundle", command=self.generate_full_bundle_ui, bg="#8c4a4a", fg="white", width=20).pack(side=LEFT, padx=4)

        # ── Main body ────────────────────────────────────────────────────────
        body = PanedWindow(root, orient="horizontal")
        self._body_frame = body
        body.pack(fill=BOTH, expand=True, padx=4, pady=(2, 0))

        browser_frame = Frame(body)
        editor_frame = Frame(body)
        preview_frame = Frame(body)
        body.add(browser_frame, minsize=240)
        body.add(editor_frame, stretch="always")
        body.add(preview_frame, stretch="always")

        # Browser
        Label(browser_frame, text="Asset Browser", anchor=W, font=("", 10, "bold")).pack(fill=X, padx=2)
        search_row = Frame(browser_frame)
        search_row.pack(fill=X, padx=2, pady=2)
        Label(search_row, text="Filter:", width=5, anchor=W).pack(side=LEFT)
        self._filter_var = tk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())
        tk.Entry(search_row, textvariable=self._filter_var).pack(side=LEFT, fill=X, expand=True)
        Button(search_row, text="✕", command=lambda: self._filter_var.set(""), width=2).pack(side=LEFT)
        self.file_list = Listbox(browser_frame, selectmode="single")
        self.file_list.pack(fill=BOTH, expand=True, padx=2)
        self.file_list.bind("<Double-Button-1>", self._open_selected_file_event)
        Button(browser_frame, text="Open Selected", command=self.open_selected_file).pack(fill=X, padx=2, pady=3)

        # Editor
        Label(editor_frame, text="File Editor", anchor=W, font=("", 10, "bold")).pack(fill=X, padx=2)
        self.editor = ScrolledText(editor_frame, wrap="none", font=("Courier", 10))
        self.editor.pack(fill=BOTH, expand=True, padx=2)

        # Preview
        Label(preview_frame, text="In-Game Preview", anchor=W, font=("", 10, "bold")).pack(fill=X, padx=2)
        self.preview_label = Label(preview_frame, text="Open a file to preview", bg="#12141e")
        self.preview_label.pack(fill=BOTH, expand=True, padx=2)
        self.preview_meta = Text(preview_frame, height=10, wrap="word", font=("Courier", 9))
        self.preview_meta.pack(fill=X, expand=False, padx=2)
        self.preview_meta.configure(state="disabled")

        # ── Status bar ───────────────────────────────────────────────────────
        self._status_bar = Label(root, text="Ready", anchor=W, relief="sunken", bd=1, padx=6, font=("", 9))
        self._status_bar.pack(side=BOTTOM, fill=X)

        self.refresh_file_browser()
        if initial_file:
            self.load_file(Path(initial_file))
        else:
            self._set_meta(
                "Ready. Create, generate, or load a file to edit.\n"
                f"Asset directory: {self.output_dir}\n"
                "Previews: images, map/material JSON, OBJ wireframe.\n"
                "Click '▼ Generate Panel' in the toolbar to create new assets."
            )
            self._set_status("Creation Engine ready. Use Generate Panel to create assets.")

    def _set_meta(self, text: str) -> None:
        self.preview_meta.configure(state="normal")
        self.preview_meta.delete("1.0", "end")
        self.preview_meta.insert("1.0", text)
        self.preview_meta.configure(state="disabled")

    def _set_status(self, text: str) -> None:
        self._status_bar.configure(text=text)
        self._status_bar.update_idletasks()

    def _toggle_gen_panel(self) -> None:
        self._gen_panel_visible = not self._gen_panel_visible
        if self._gen_panel_visible:
            self._gen_panel.pack(fill="x", padx=4, pady=(0, 2), before=self._body_frame)
            self._gen_toggle_btn.configure(text="▲ Generate Panel")
        else:
            self._gen_panel.pack_forget()
            self._gen_toggle_btn.configure(text="▼ Generate Panel")

    def _run_in_thread(self, fn: Any, *args: Any, on_done: Any = None) -> None:
        if self._busy:
            self._set_status("Busy — please wait for current operation to finish.")
            return

        self._busy = True
        self._set_status("Working…")

        def _worker() -> None:
            try:
                result = fn(*args)
                def _finish_success() -> None:
                    try:
                        if on_done:
                            on_done(result)
                        self.refresh_file_browser()
                        if on_done is None:
                            self._set_status("Done.")
                    finally:
                        self._busy = False

                self.root.after(0, _finish_success)
            except Exception as exc:
                error_text = f"Error: {exc}"

                def _finish_error() -> None:
                    self._set_meta(error_text)
                    self._set_status(error_text)
                    self._busy = False

                self.root.after(0, _finish_error)

        threading.Thread(target=_worker, daemon=True).start()

    # ── Generation actions ───────────────────────────────────────────────────

    def generate_single_asset_ui(self) -> None:
        from creation_engine.engine import CreationEngine

        asset_type = self._gen_type_var.get()
        prompt = self._gen_prompt_var.get().strip()
        if not prompt:
            self._set_status("Prompt cannot be empty.")
            return

        try:
            seed = int(self._gen_seed_var.get())
        except ValueError:
            seed = 42

        try:
            width = int(self._gen_width_var.get())
        except ValueError:
            width = 64

        try:
            height = int(self._gen_height_var.get())
        except ValueError:
            height = 64

        complexity = self._gen_complexity_var.get() or "medium"
        engine = CreationEngine(seed=seed, output_dir=self.output_dir)

        def _gen() -> Path:
            if asset_type == "texture":
                return engine.generate_texture(prompt, width=width, height=height, seed=seed)
            if asset_type == "map":
                return engine.generate_map(prompt, width=width, height=height, seed=seed)
            if asset_type == "mesh":
                return engine.generate_mesh(prompt, complexity=complexity, seed=seed)
            if asset_type == "ui-icon":
                return engine.generate_ui_icon(prompt, seed=seed)
            if asset_type == "ui-panel":
                return engine.generate_ui_panel(prompt, seed=seed)
            if asset_type == "portrait":
                return engine.generate_portrait(prompt, seed=seed)
            raise ValueError(f"Unknown asset type: {asset_type}")

        def _done(result: Path) -> None:
            msg = f"Generated {asset_type}: {result}"
            self._set_meta(msg)
            self._set_status(msg)
            if result.is_dir():
                for candidate in sorted(result.iterdir()):
                    if candidate.suffix == ".json":
                        self.load_file(candidate)
                        break
            elif result.exists():
                self.load_file(result)

        self._set_status(f"Generating {asset_type}: '{prompt}' …")
        self._run_in_thread(_gen, on_done=_done)

    def generate_pack_ui(self) -> None:
        from creation_engine.engine import CreationEngine

        pack_type = self._pack_type_var.get()
        try:
            seed = int(self._pack_seed_var.get())
        except ValueError:
            seed = 42

        engine = CreationEngine(seed=seed, output_dir=self.output_dir)

        _pack_method_map = {
            "material-pack": engine.generate_material_pack,
            "biome-pack": engine.generate_terrain_pack,
            "tileset-pack": engine.generate_tileset_pack,
            "prop-pack": engine.generate_prop_pack,
            "architecture-pack": engine.generate_architecture_pack,
            "foliage-pack": engine.generate_foliage_pack,
            "item-pack": engine.generate_item_pack,
            "decal-pack": engine.generate_decal_pack,
            "character-static-pack": engine.generate_character_static_pack,
            "enemy-static-pack": engine.generate_enemy_static_pack,
        }
        method = _pack_method_map.get(pack_type)
        if method is None:
            self._set_status(f"Unknown pack type: {pack_type}")
            return

        def _gen() -> Path:
            return method(seed=seed)

        def _done(result: Path) -> None:
            msg = f"Generated {pack_type}: {result}"
            self._set_meta(msg)
            self._set_status(msg)

        self._set_status(f"Generating {pack_type} (seed={seed}) …")
        self._run_in_thread(_gen, on_done=_done)

    def generate_full_bundle_ui(self) -> None:
        from creation_engine.engine import CreationEngine

        try:
            seed = int(self._bundle_seed_var.get())
        except ValueError:
            seed = 42

        engine = CreationEngine(seed=seed, output_dir=self.output_dir)

        def _gen() -> Path:
            return engine.generate_full_bundle(seed=seed)

        def _done(result: Path) -> None:
            msg = f"Full bundle generated: {result}"
            self._set_meta(msg + "\nRun Bundle Audit or Release Check to verify quality.")
            self._set_status(msg)

        self._set_status(f"Generating full GameRewritten bundle (seed={seed}) — this may take a while …")
        self._run_in_thread(_gen, on_done=_done)

    # ── Filter ───────────────────────────────────────────────────────────────

    def _apply_filter(self) -> None:
        from tkinter import END

        query = self._filter_var.get().lower()
        self._filtered_index = _filter_file_index(self.file_index, self.output_dir, query)
        self.file_list.delete(0, END)
        for path in self._filtered_index:
            rel = str(path.relative_to(self.output_dir))
            self.file_list.insert(END, rel)

    def refresh_file_browser(self) -> None:
        self.file_index = []
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)

        for path in sorted(self.output_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_BROWSER_SUFFIXES:
                continue
            self.file_index.append(path)

        self._apply_filter()
        self._set_status(f"Asset browser: {len(self.file_index)} files found.")

    def _open_selected_file_event(self, _event: Any) -> None:
        self.open_selected_file()

    def _is_within_output_dir(self, path: Path) -> bool:
        output_root = self.output_dir.resolve()
        resolved = path.resolve()
        return resolved == output_root or output_root in resolved.parents

    def open_selected_file(self) -> None:
        selection = self.file_list.curselection()
        if not selection:
            return
        index = selection[0]
        filtered = getattr(self, "_filtered_index", self.file_index)
        if index < 0 or index >= len(filtered):
            return
        self.load_file(filtered[index])

    def load_file_dialog(self) -> None:
        from tkinter import filedialog, messagebox

        selected = filedialog.askopenfilename(
            title="Open file",
            initialdir=str(self.output_dir),
        )
        if not selected:
            return

        selected_path = Path(selected)
        if not self._is_within_output_dir(selected_path):
            messagebox.showerror("Invalid path", "File must be inside the selected output directory.")
            return
        self.load_file(selected_path)

    def new_file_dialog(self) -> None:
        from tkinter import messagebox, simpledialog

        relative_path = simpledialog.askstring(
            "Create File",
            "Enter file path relative to asset folder (example: materials/new_asset.json):",
            initialvalue="new_asset.json",
        )
        if not relative_path:
            return
        target = (self.output_dir / relative_path).resolve()
        output_root = self.output_dir.resolve()
        if not self._is_within_output_dir(target):
            messagebox.showerror("Invalid path", "File must be inside the selected output directory.")
            return
        if target == output_root or target.exists() and target.is_dir():
            messagebox.showerror("Invalid path", "Please provide a file path, not a directory.")
            return

        if target.exists() and not messagebox.askyesno("Overwrite", f"Overwrite existing file?\n{target}"):
            return

        suffix = target.suffix.lower() or ".txt"
        template = DEFAULT_NEW_FILE_TEMPLATES.get(suffix, "")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(template, encoding="utf-8")
        self.refresh_file_browser()
        self.load_file(target)
        self._set_meta(f"Created file: {target}")

    def load_file(self, path: Path) -> None:
        self.current_path = path
        self.current_is_binary = False
        self.path_label.configure(text=str(path))
        suffix = path.suffix.lower()

        try:
            if suffix in {".png", ".jpg", ".jpeg", ".bmp"}:
                self.current_is_binary = True
                self.editor.delete("1.0", "end")
                self.editor.insert(
                    "1.0",
                    "Binary image file loaded. Edit image content in your art tool; save metadata changes here.",
                )
                image = Image.open(path).convert("RGB")
                self._show_image_preview(image)
                self._set_meta(f"Image preview loaded: {path.name}\nResolution: {image.width}x{image.height}")
                self._set_status(f"Loaded image: {path.name}")
            else:
                text = path.read_text(encoding="utf-8")
                self.editor.delete("1.0", "end")
                self.editor.insert("1.0", text)
                self._set_status(f"Loaded: {path.name}")
                self.refresh_preview()
        except Exception as exc:
            self._set_meta(f"Failed to load file: {exc}")
            self._set_status(f"Load error: {exc}")

    def save_current(self) -> None:
        if self.current_path is None:
            self.save_as_dialog()
            return
        if self.current_is_binary:
            self._set_meta("Binary image sources are read-only in this editor. Use external image tools.")
            self._set_status("Save skipped: binary images are read-only in editor.")
            return
        if not self._is_within_output_dir(self.current_path):
            self._set_meta("Save blocked: file must be inside the selected output directory.")
            self._set_status("Save blocked: outside output directory.")
            return

        self.current_path.parent.mkdir(parents=True, exist_ok=True)
        self.current_path.write_text(self.editor.get("1.0", "end-1c"), encoding="utf-8")
        self._set_meta(f"Saved: {self.current_path}")
        self._set_status(f"Saved: {self.current_path.name}")
        self.refresh_file_browser()
        self.refresh_preview()

    def save_as_dialog(self) -> None:
        from tkinter import filedialog, messagebox

        target = filedialog.asksaveasfilename(
            title="Save As",
            initialdir=str(self.output_dir),
            initialfile=self.current_path.name if self.current_path else "asset.json",
        )
        if not target:
            return
        target_path = Path(target)
        if not self._is_within_output_dir(target_path):
            messagebox.showerror("Invalid path", "File must be inside the selected output directory.")
            return
        self.current_path = target_path
        self.current_is_binary = False
        self.path_label.configure(text=str(self.current_path))
        self.save_current()

    def delete_current_file(self) -> None:
        from tkinter import messagebox

        if self.current_path is None:
            return
        if not self.current_path.exists():
            return
        if not self._is_within_output_dir(self.current_path):
            messagebox.showerror("Invalid path", "File must be inside the selected output directory.")
            return
        if not messagebox.askyesno("Delete file", f"Delete file?\n{self.current_path}"):
            return

        self.current_path.unlink()
        deleted = self.current_path
        self.current_path = None
        self.current_is_binary = False
        self.path_label.configure(text="No file loaded")
        self.editor.delete("1.0", "end")
        self.preview_label.configure(image="", text="Open a file to preview")
        self._set_meta(f"Deleted file: {deleted}")
        self._set_status(f"Deleted: {deleted.name}")
        self.refresh_file_browser()

    def toggle_3d_mode(self) -> None:
        self.preview_3d_enabled = not self.preview_3d_enabled
        if self.preview_3d_enabled:
            self.view_mode_btn.configure(text="Disable 3D View")
        else:
            self.view_mode_btn.configure(text="Enable 3D View")
        self.refresh_preview()

    def run_quality_check_ui(self) -> None:
        self._set_status("Running quality check…")

        def _done(result: Any) -> None:
            if result.ok:
                msg = f"Quality check passed. Manifests validated: {result.checked_manifests}"
                self._set_meta(
                    "Quality check passed.\n"
                    f"Validated manifests: {result.checked_manifests}\n"
                    "Ready for GameRewritten import validation."
                )
                self._set_status(msg)
                return
            joined = "\n".join(f"- {item}" for item in result.errors[:8])
            self._set_meta(
                "Quality check failed.\n"
                f"Validated manifests: {result.checked_manifests}\n"
                f"Top issues:\n{joined}"
            )
            self._set_status(f"Quality check FAILED — {len(result.errors)} issue(s) found.")

        self._run_in_thread(run_quality_check, self.output_dir, on_done=_done)

    def run_bundle_audit_ui(self) -> None:
        self._set_status("Running bundle audit…")

        def _done(result: Any) -> None:
            family_lines = "\n".join(f"  {k}: {v}" for k, v in result.family_counts.items())
            nc = result.narrative_coverage
            sc = result.style_coverage
            report = (
                f"Bundle Audit — manifests checked: {result.checked_manifests}\n"
                f"Family counts:\n{family_lines}\n"
                f"Narrative coverage: {nc['present']}/{nc['required']}\n"
                f"Style coverage: {sc['passing']}/{sc['required']}\n"
                f"FF aesthetic: {'PASS ✓' if result.ff_aesthetic_compliant else 'FAIL ✗'}"
            )
            if result.errors:
                report += "\nErrors:\n" + "\n".join(f"  - {e}" for e in result.errors[:6])
            self._set_meta(report)
            status = (
                "Bundle audit: FF aesthetic PASS"
                if result.ff_aesthetic_compliant
                else f"Bundle audit: FAIL — {len(result.errors)} issues"
            )
            self._set_status(status)

        self._run_in_thread(run_bundle_audit, self.output_dir, on_done=_done)

    def run_release_check_ui(self) -> None:
        self._set_status("Running release readiness check…")

        def _done(result: Any) -> None:
            if result.ok:
                msg = (
                    f"Release check PASSED ✓\n"
                    f"Manifests: {result.checked_manifests} | Bundle: {result.bundle_manifests_checked}\n"
                    "Asset bundle is production-ready for GameRewritten import."
                )
                self._set_meta(msg)
                self._set_status("Release check PASSED — bundle is production ready.")
                return
            joined = "\n".join(f"- {e}" for e in result.errors[:10])
            self._set_meta(f"Release check FAILED ✗\n{joined}")
            self._set_status(f"Release check FAILED — {len(result.errors)} issue(s).")

        self._run_in_thread(run_release_readiness_check, self.output_dir, on_done=_done)

    def _show_image_preview(self, image: Image.Image) -> None:
        from PIL import ImageTk

        fitted = ImageOps.contain(image, (560, 560), method=Image.Resampling.NEAREST)
        self._preview_tk = ImageTk.PhotoImage(fitted)
        self.preview_label.configure(image=self._preview_tk, text="")

    def refresh_preview(self) -> None:
        if self.current_path is None:
            return

        suffix = self.current_path.suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg", ".bmp"}:
            image = Image.open(self.current_path).convert("RGB")
            self._show_image_preview(image)
            self._set_meta(f"Raw asset image preview: {self.current_path.name}")
            return

        text = self.editor.get("1.0", "end-1c")
        try:
            if suffix == ".obj":
                preview_image = render_obj_preview(text)
                self._show_image_preview(preview_image)
                self._set_meta(
                    "3D wireframe preview generated from OBJ geometry.\n"
                    "Use this to sanity-check GameRewritten mesh silhouette before export."
                )
                return

            if suffix != ".json":
                self.preview_label.configure(image="", text="No renderer for this file type")
                self._set_meta(
                    "Loaded for editing only.\n"
                    "Supported previews: images, map/material JSON, and OBJ files."
                )
                return

            parsed = json.loads(text)
            preview_image = render_preview_from_json(
                parsed,
                self.current_path,
                use_3d_view=self.preview_3d_enabled,
            )
            self._show_image_preview(preview_image)

            if "files" in parsed or "textures" in parsed:
                self._set_meta(
                    "GameRewritten-style material preview.\n"
                    "Uses albedo/normal/roughness/metallic/emissive lighting approximation."
                )
            elif self.preview_3d_enabled:
                self._set_meta(
                    "3D map block preview generated from tile IDs.\n"
                    "Use this to check traversal readability before final export."
                )
            else:
                self._set_meta("2D tilemap preview generated from map JSON tile IDs.")
        except Exception as exc:
            self.preview_label.configure(image="", text="Preview unavailable")
            self._set_meta(f"Preview error: {exc}")


def run_gui(output_dir: str | Path = "assets", initial_file: str | None = None) -> None:
    try:
        import tkinter as tk
    except Exception as exc:
        raise RuntimeError("Tkinter is required to run the GUI.") from exc

    root = tk.Tk()
    CreationEngineGuiApp(root, output_dir=output_dir, initial_file=initial_file)
    root.mainloop()
