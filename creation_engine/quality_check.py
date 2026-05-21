from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from creation_engine.export.manifest_exporter import DEFAULT_STYLE_PROFILE


@dataclass(frozen=True)
class QualityCheckResult:
    ok: bool
    errors: list[str]
    checked_manifests: int


def run_quality_check(output_dir: str | Path, *, min_png_size: int = 64) -> QualityCheckResult:
    root = Path(output_dir)
    if not root.exists():
        return QualityCheckResult(ok=False, errors=[f"Output directory does not exist: {root}"], checked_manifests=0)

    manifest_paths = sorted(path for path in root.rglob("*.json") if path.is_file())
    errors: list[str] = []
    checked = 0

    for manifest_path in manifest_paths:
        try:
            with open(manifest_path, encoding="utf-8") as file:
                manifest = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{manifest_path}: invalid JSON ({exc})")
            continue

        if "asset_family" not in manifest:
            continue

        checked += 1
        rel_manifest = manifest_path.relative_to(root)
        if manifest.get("style_profile") != DEFAULT_STYLE_PROFILE:
            errors.append(
                f"{rel_manifest}: style_profile must be {DEFAULT_STYLE_PROFILE!r}, got {manifest.get('style_profile')!r}"
            )

        content_target = manifest.get("content_target")
        if not isinstance(content_target, dict) or not content_target:
            errors.append(f"{rel_manifest}: missing non-empty content_target mapping")

        files = manifest.get("files")
        if not isinstance(files, dict) or not files:
            errors.append(f"{rel_manifest}: missing non-empty files mapping")
            continue

        for key, rel_path in files.items():
            if not isinstance(rel_path, str) or not rel_path:
                errors.append(f"{rel_manifest}: files[{key!r}] must be a non-empty string")
                continue
            referenced = manifest_path.parent / rel_path
            if not referenced.exists():
                errors.append(f"{rel_manifest}: referenced file not found: {rel_path}")
                continue
            if referenced.suffix.lower() == ".png":
                _check_png_size(referenced, root, min_png_size, errors)

    if checked == 0:
        errors.append("No asset manifests found (no JSON file with asset_family field).")

    return QualityCheckResult(ok=not errors, errors=errors, checked_manifests=checked)


def _check_png_size(path: Path, root: Path, min_png_size: int, errors: list[str]) -> None:
    size = path.stat().st_size
    if size < min_png_size:
        rel_path = path.relative_to(root)
        errors.append(
            f"{rel_path}: PNG file is too small ({size} bytes), expected at least {min_png_size} bytes"
        )
