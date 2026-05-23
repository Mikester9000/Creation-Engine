from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageOps

from creation_engine.quality_check import run_quality_check


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


class CreationEngineGuiApp:
    def __init__(self, root: Any, output_dir: str | Path, initial_file: str | None = None) -> None:
        self.root = root
        self.output_dir = Path(output_dir)
        self.current_path: Path | None = None
        self.current_is_binary = False
        self.preview_3d_enabled = False
        self.file_index: list[Path] = []
        self._preview_tk = None

        root.title("Creation Engine GUI")
        root.geometry("1440x820")

        from tkinter import BOTH, LEFT, TOP, X, Button, Frame, Label, Listbox, PanedWindow, Text
        from tkinter.scrolledtext import ScrolledText

        toolbar = Frame(root)
        toolbar.pack(side=TOP, fill=X, padx=6, pady=6)

        Button(toolbar, text="New File", command=self.new_file_dialog).pack(side=LEFT, padx=2)
        Button(toolbar, text="Load File", command=self.load_file_dialog).pack(side=LEFT, padx=2)
        Button(toolbar, text="Save", command=self.save_current).pack(side=LEFT, padx=2)
        Button(toolbar, text="Save As", command=self.save_as_dialog).pack(side=LEFT, padx=2)
        Button(toolbar, text="Delete", command=self.delete_current_file).pack(side=LEFT, padx=2)
        Button(toolbar, text="Refresh Files", command=self.refresh_file_browser).pack(side=LEFT, padx=2)
        self.view_mode_btn = Button(toolbar, text="Enable 3D View", command=self.toggle_3d_mode)
        self.view_mode_btn.pack(side=LEFT, padx=2)
        Button(toolbar, text="Refresh Viewer", command=self.refresh_preview).pack(side=LEFT, padx=2)
        Button(toolbar, text="Run Quality Check", command=self.run_quality_check_ui).pack(side=LEFT, padx=2)

        self.path_label = Label(toolbar, text="No file loaded", anchor="w")
        self.path_label.pack(side=LEFT, fill=X, expand=True, padx=8)

        body = PanedWindow(root, orient="horizontal")
        body.pack(fill=BOTH, expand=True, padx=6, pady=(0, 6))

        browser_frame = Frame(body)
        editor_frame = Frame(body)
        preview_frame = Frame(body)
        body.add(browser_frame, minsize=250)
        body.add(editor_frame, stretch="always")
        body.add(preview_frame, stretch="always")

        Label(browser_frame, text="Asset Browser").pack(fill=X)
        self.file_list = Listbox(browser_frame)
        self.file_list.pack(fill=BOTH, expand=True)
        self.file_list.bind("<Double-Button-1>", self._open_selected_file_event)
        Button(browser_frame, text="Open Selected", command=self.open_selected_file).pack(fill=X, pady=4)

        self.editor = ScrolledText(editor_frame, wrap="none")
        self.editor.pack(fill=BOTH, expand=True)

        self.preview_label = Label(preview_frame, text="Open a file to preview")
        self.preview_label.pack(fill=BOTH, expand=True)
        self.preview_meta = Text(preview_frame, height=9, wrap="word")
        self.preview_meta.pack(fill=X, expand=False)
        self.preview_meta.configure(state="disabled")

        self.refresh_file_browser()
        if initial_file:
            self.load_file(Path(initial_file))
        else:
            self._set_meta(
                "Ready. Create or load a file to edit.\n"
                f"Default asset directory: {self.output_dir}\n"
                "Viewer supports images, maps/material JSON, and OBJ wireframe previews."
            )

    def _set_meta(self, text: str) -> None:
        self.preview_meta.configure(state="normal")
        self.preview_meta.delete("1.0", "end")
        self.preview_meta.insert("1.0", text)
        self.preview_meta.configure(state="disabled")

    def refresh_file_browser(self) -> None:
        from tkinter import END

        self.file_index = []
        self.file_list.delete(0, END)
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)

        for path in sorted(self.output_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_BROWSER_SUFFIXES:
                continue
            self.file_index.append(path)
            self.file_list.insert(END, str(path.relative_to(self.output_dir)))

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
        if index < 0 or index >= len(self.file_index):
            return
        self.load_file(self.file_index[index])

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
            else:
                text = path.read_text(encoding="utf-8")
                self.editor.delete("1.0", "end")
                self.editor.insert("1.0", text)
                self.refresh_preview()
        except Exception as exc:
            self._set_meta(f"Failed to load file: {exc}")

    def save_current(self) -> None:
        if self.current_path is None:
            self.save_as_dialog()
            return
        if self.current_is_binary:
            self._set_meta("Binary image sources are read-only in this editor. Use external image tools.")
            return
        if not self._is_within_output_dir(self.current_path):
            self._set_meta("Save blocked: file must be inside the selected output directory.")
            return

        self.current_path.parent.mkdir(parents=True, exist_ok=True)
        self.current_path.write_text(self.editor.get("1.0", "end-1c"), encoding="utf-8")
        self._set_meta(f"Saved: {self.current_path}")
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
        self.refresh_file_browser()

    def toggle_3d_mode(self) -> None:
        self.preview_3d_enabled = not self.preview_3d_enabled
        if self.preview_3d_enabled:
            self.view_mode_btn.configure(text="Disable 3D View")
        else:
            self.view_mode_btn.configure(text="Enable 3D View")
        self.refresh_preview()

    def run_quality_check_ui(self) -> None:
        result = run_quality_check(self.output_dir)
        if result.ok:
            self._set_meta(
                "Quality check passed.\n"
                f"Validated manifests: {result.checked_manifests}\n"
                "Ready for GameRewritten import validation."
            )
            return
        joined = "\n".join(f"- {item}" for item in result.errors[:8])
        self._set_meta(
            "Quality check failed.\n"
            f"Validated manifests: {result.checked_manifests}\n"
            f"Top issues:\n{joined}"
        )

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
