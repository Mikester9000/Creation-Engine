from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps


def _read_image_array(path: Path, size: tuple[int, int]) -> np.ndarray:
    image = Image.open(path).convert("RGB").resize(size, Image.Resampling.NEAREST)
    return np.asarray(image, dtype=np.float32) / 255.0


def render_material_preview(manifest: dict[str, Any], manifest_path: Path) -> Image.Image:
    files = manifest.get("files", {})
    albedo_name = files.get("albedo") or files.get("image")
    if not isinstance(albedo_name, str):
        raise ValueError("Manifest has no previewable texture entry.")

    material_dir = manifest_path.parent
    albedo_path = material_dir / albedo_name
    if not albedo_path.exists():
        raise FileNotFoundError(f"Missing texture: {albedo_path}")

    width = int(manifest.get("width", 256))
    height = int(manifest.get("height", 256))
    size = (max(32, width), max(32, height))
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


def render_preview_from_json(parsed: dict[str, Any], source_path: Path) -> Image.Image:
    if "tiles" in parsed and "width" in parsed and "height" in parsed:
        return render_map_preview(parsed)
    if "files" in parsed:
        return render_material_preview(parsed, source_path)
    raise ValueError("No preview renderer available for this JSON schema.")


class CreationEngineGuiApp:
    def __init__(self, root: Any, output_dir: str | Path, initial_file: str | None = None) -> None:
        self.root = root
        self.output_dir = Path(output_dir)
        self.current_path: Path | None = None
        self._preview_tk = None

        root.title("Creation Engine GUI")
        root.geometry("1200x760")

        from tkinter import BOTH, LEFT, RIGHT, TOP, X, Y, Button, Frame, Label, PanedWindow, Text
        from tkinter.scrolledtext import ScrolledText

        toolbar = Frame(root)
        toolbar.pack(side=TOP, fill=X, padx=6, pady=6)

        Button(toolbar, text="Load File", command=self.load_file_dialog).pack(side=LEFT, padx=2)
        Button(toolbar, text="Save", command=self.save_current).pack(side=LEFT, padx=2)
        Button(toolbar, text="Save As", command=self.save_as_dialog).pack(side=LEFT, padx=2)
        Button(toolbar, text="Refresh Viewer", command=self.refresh_preview).pack(side=LEFT, padx=2)

        self.path_label = Label(toolbar, text="No file loaded", anchor="w")
        self.path_label.pack(side=LEFT, fill=X, expand=True, padx=8)

        body = PanedWindow(root, orient="horizontal")
        body.pack(fill=BOTH, expand=True, padx=6, pady=(0, 6))

        editor_frame = Frame(body)
        preview_frame = Frame(body)
        body.add(editor_frame, stretch="always")
        body.add(preview_frame, stretch="always")

        self.editor = ScrolledText(editor_frame, wrap="none")
        self.editor.pack(fill=BOTH, expand=True)

        self.preview_label = Label(preview_frame, text="Open a file to preview")
        self.preview_label.pack(fill=BOTH, expand=True)
        self.preview_meta = Text(preview_frame, height=8, wrap="word")
        self.preview_meta.pack(fill=X, expand=False)
        self.preview_meta.configure(state="disabled")

        if initial_file:
            self.load_file(Path(initial_file))
        else:
            default_assets = self.output_dir
            self._set_meta(
                "Ready. Load any file to edit.\n"
                f"Default asset directory: {default_assets}\n"
                "Viewer supports material/texture manifests, map JSON, and PNG/JPG assets."
            )

    def _set_meta(self, text: str) -> None:
        self.preview_meta.configure(state="normal")
        self.preview_meta.delete("1.0", "end")
        self.preview_meta.insert("1.0", text)
        self.preview_meta.configure(state="disabled")

    def load_file_dialog(self) -> None:
        from tkinter import filedialog

        selected = filedialog.askopenfilename(
            title="Open file",
            initialdir=str(self.output_dir),
        )
        if selected:
            self.load_file(Path(selected))

    def load_file(self, path: Path) -> None:
        self.current_path = path
        self.path_label.configure(text=str(path))
        suffix = path.suffix.lower()

        try:
            if suffix in {".png", ".jpg", ".jpeg", ".bmp"}:
                self.editor.delete("1.0", "end")
                self.editor.insert("1.0", "Binary image file loaded. Use viewer panel for preview.")
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
        self.current_path.write_text(self.editor.get("1.0", "end-1c"), encoding="utf-8")
        self._set_meta(f"Saved: {self.current_path}")
        self.refresh_preview()

    def save_as_dialog(self) -> None:
        from tkinter import filedialog

        target = filedialog.asksaveasfilename(
            title="Save As",
            initialdir=str(self.output_dir),
            initialfile=self.current_path.name if self.current_path else "asset.json",
        )
        if not target:
            return
        self.current_path = Path(target)
        self.path_label.configure(text=str(self.current_path))
        self.save_current()

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
        if suffix != ".json":
            self.preview_label.configure(image="", text="No renderer for this file type")
            self._set_meta(
                "Loaded for editing only.\nSupported viewer previews: JSON material/map manifests and images."
            )
            return

        text = self.editor.get("1.0", "end-1c")
        try:
            parsed = json.loads(text)
            preview_image = render_preview_from_json(parsed, self.current_path)
            self._show_image_preview(preview_image)
            if "files" in parsed:
                self._set_meta(
                    "GameRewritten-style material preview.\n"
                    "This approximates in-game lighting using albedo/normal/roughness/metallic/emissive."
                )
            else:
                self._set_meta("Tilemap preview generated from map JSON tile IDs.")
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
