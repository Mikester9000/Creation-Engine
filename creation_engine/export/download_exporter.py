from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


def write_download_bundle(
    *,
    output_root: Path,
    family: str,
    name: str,
    files: dict[str, Path],
    preview_image: Any | None = None,
    preview_filename: str | None = None,
) -> Path:
    """Create an export bundle with individual files for direct download."""
    bundle_dir = output_root / "export" / family / name
    bundle_dir.mkdir(parents=True, exist_ok=True)

    export_files: dict[str, str] = {}
    for label, source_path in files.items():
        if not source_path.exists():
            continue
        destination = bundle_dir / source_path.name
        if source_path.resolve() != destination.resolve():
            shutil.copy2(source_path, destination)
        export_files[label] = destination.name

    if preview_image is not None:
        preview_name = preview_filename or f"{name}_preview.png"
        preview_path = bundle_dir / preview_name
        preview_image.save(preview_path)
        export_files["preview"] = preview_path.name

    _upsert_export_index(
        output_root=output_root,
        entry={
            "family": family,
            "name": name,
            "bundle_path": str(bundle_dir.relative_to(output_root)),
            "files": export_files,
        },
    )
    return bundle_dir


def _upsert_export_index(*, output_root: Path, entry: dict[str, Any]) -> None:
    index_path = output_root / "export" / "index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {"exports": []}
    if index_path.exists():
        with open(index_path, encoding="utf-8") as file:
            loaded = json.load(file)
        if isinstance(loaded, dict) and isinstance(loaded.get("exports"), list):
            payload = loaded

    exports = [
        item
        for item in payload["exports"]
        if not (
            isinstance(item, dict)
            and item.get("family") == entry["family"]
            and item.get("name") == entry["name"]
        )
    ]
    exports.append(entry)
    exports.sort(key=lambda item: (str(item.get("family", "")), str(item.get("name", ""))))

    payload["exports"] = exports
    with open(index_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
