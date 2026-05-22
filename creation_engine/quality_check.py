from __future__ import annotations

import glob
import json
from dataclasses import dataclass
from pathlib import Path

from creation_engine.asset_catalog import (
    ASSET_FAMILY_ARCHITECTURE,
    ASSET_FAMILY_CHARACTERS_STATIC,
    ASSET_FAMILY_DECALS,
    ASSET_FAMILY_ENEMIES_STATIC,
    ASSET_FAMILY_FOLIAGE,
    ASSET_FAMILY_ITEMS,
    ASSET_FAMILY_MATERIALS,
    ASSET_FAMILY_PROPS,
    ASSET_FAMILY_TERRAIN,
    ASSET_FAMILY_TILESETS,
    ASSET_FAMILY_UI_ICONS,
    ASSET_FAMILY_UI_PANELS,
    ASSET_FAMILY_UI_PORTRAITS,
)
from creation_engine.export.manifest_exporter import DEFAULT_STYLE_PROFILE
from creation_engine.narrative_tags import NARRATIVE_TAG_KEYS, NARRATIVE_TAG_VALUES

_BANNED_PROMPT_TERMS = (
    "photoreal",
    "photorealistic",
    "hyperreal",
    "ultra realistic",
    "modern aaa",
)
_REQUIRED_STYLE_TERMS = ("ps2", "jrpg")
_STYLE_VALIDATED_FAMILIES = {
    ASSET_FAMILY_MATERIALS,
    ASSET_FAMILY_TERRAIN,
    ASSET_FAMILY_TILESETS,
    ASSET_FAMILY_PROPS,
    ASSET_FAMILY_ARCHITECTURE,
    ASSET_FAMILY_FOLIAGE,
    ASSET_FAMILY_ITEMS,
    ASSET_FAMILY_DECALS,
    ASSET_FAMILY_UI_ICONS,
    ASSET_FAMILY_UI_PANELS,
    ASSET_FAMILY_UI_PORTRAITS,
    ASSET_FAMILY_CHARACTERS_STATIC,
    ASSET_FAMILY_ENEMIES_STATIC,
}
_NARRATIVE_VALIDATED_FAMILIES = set(_STYLE_VALIDATED_FAMILIES)


@dataclass(frozen=True)
class QualityCheckResult:
    ok: bool
    errors: list[str]
    checked_manifests: int


@dataclass(frozen=True)
class BundleAuditResult:
    ok: bool
    checked_manifests: int
    family_counts: dict[str, int]
    narrative_coverage: dict[str, int]
    style_coverage: dict[str, int]
    ff_aesthetic_compliant: bool
    errors: list[str]


def run_quality_check(output_dir: str | Path, *, min_png_size: int = 64) -> QualityCheckResult:
    root = Path(output_dir)
    root_error = _validate_root_dir(root)
    if root_error is not None:
        return QualityCheckResult(
            ok=False,
            errors=[root_error],
            checked_manifests=0,
        )
    if min_png_size < 0:
        return QualityCheckResult(
            ok=False,
            errors=[f"Minimum PNG size must be non-negative, got {min_png_size}"],
            checked_manifests=0,
        )

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

        if not isinstance(manifest, dict) or "asset_family" not in manifest:
            continue

        checked += 1
        rel_manifest = manifest_path.relative_to(root)
        if manifest.get("style_profile") != DEFAULT_STYLE_PROFILE:
            errors.append(
                f"{rel_manifest}: style_profile must be {DEFAULT_STYLE_PROFILE!r}, got {manifest.get('style_profile')!r}"
            )
        _validate_aesthetic_prompt(manifest, rel_manifest, errors)
        _validate_narrative_metadata(manifest, rel_manifest, errors)

        content_target = manifest.get("content_target")
        if not isinstance(content_target, dict) or not content_target:
            errors.append(f"{rel_manifest}: missing non-empty content_target mapping")

        asset_family = str(manifest.get("asset_family", ""))
        files = manifest.get("files")
        requires_files = asset_family not in {"maps", "tilesets"}
        if requires_files and (not isinstance(files, dict) or not files):
            errors.append(f"{rel_manifest}: missing non-empty files mapping")
            continue
        if not isinstance(files, dict):
            continue

        for key, rel_path in files.items():
            if not isinstance(rel_path, str) or not rel_path:
                errors.append(f"{rel_manifest}: files[{key!r}] must be a non-empty string")
                continue
            referenced, resolution_error = _resolve_reference(manifest_path.parent, root, rel_path)
            if resolution_error is not None:
                errors.append(f"{rel_manifest}: {resolution_error}: {rel_path}")
                continue
            if referenced is None or not referenced.exists():
                errors.append(f"{rel_manifest}: referenced file not found: {rel_path}")
                continue
            if not referenced.is_file():
                errors.append(f"{rel_manifest}: referenced path is not a file: {rel_path}")
                continue
            if referenced.suffix.lower() == ".png":
                _check_png_size(referenced, root, min_png_size, errors)

    if checked == 0:
        errors.append("No asset manifests found (no JSON file with asset_family field).")

    return QualityCheckResult(ok=not errors, errors=errors, checked_manifests=checked)


def run_bundle_audit(output_dir: str | Path) -> BundleAuditResult:
    root = Path(output_dir)
    root_error = _validate_root_dir(root)
    if root_error is not None:
        return BundleAuditResult(
            ok=False,
            checked_manifests=0,
            family_counts={},
            narrative_coverage={"required": 0, "present": 0},
            style_coverage={"required": 0, "passing": 0},
            ff_aesthetic_compliant=False,
            errors=[root_error],
        )

    family_counts: dict[str, int] = {}
    narrative_required = 0
    narrative_present = 0
    style_required = 0
    style_passing = 0
    errors: list[str] = []
    checked = 0

    for manifest_path in sorted(path for path in root.rglob("*.json") if path.is_file()):
        try:
            with open(manifest_path, encoding="utf-8") as file:
                manifest = json.load(file)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(manifest, dict) or "asset_family" not in manifest:
            continue

        checked += 1
        asset_family = str(manifest.get("asset_family", ""))
        family_counts[asset_family] = family_counts.get(asset_family, 0) + 1
        rel_manifest = manifest_path.relative_to(root)

        if asset_family in _STYLE_VALIDATED_FAMILIES:
            style_required += 1
            style_errors: list[str] = []
            _validate_aesthetic_prompt(manifest, rel_manifest, style_errors)
            if not style_errors:
                style_passing += 1
            else:
                errors.extend(style_errors)

        if asset_family in _NARRATIVE_VALIDATED_FAMILIES:
            narrative_required += 1
            narrative_errors: list[str] = []
            _validate_narrative_metadata(manifest, rel_manifest, narrative_errors)
            if not narrative_errors:
                narrative_present += 1
            else:
                errors.extend(narrative_errors)

    if checked == 0:
        errors.append("No asset manifests found (no JSON file with asset_family field).")

    ff_aesthetic_compliant = style_required == 0 or style_passing == style_required
    return BundleAuditResult(
        ok=not errors,
        checked_manifests=checked,
        family_counts=dict(sorted(family_counts.items())),
        narrative_coverage={"required": narrative_required, "present": narrative_present},
        style_coverage={"required": style_required, "passing": style_passing},
        ff_aesthetic_compliant=ff_aesthetic_compliant,
        errors=errors,
    )


def _check_png_size(path: Path, root: Path, min_png_size: int, errors: list[str]) -> None:
    size = path.stat().st_size
    if size < min_png_size:
        rel_path = path.relative_to(root)
        errors.append(
            f"{rel_path}: PNG file is too small ({size} bytes), expected at least {min_png_size} bytes"
        )


def _resolve_reference(manifest_parent: Path, root: Path, rel_path: str) -> tuple[Path | None, str | None]:
    if any(char in rel_path for char in "*?[]"):
        return None, "referenced file path must not contain glob metacharacters"

    root_resolved = root.resolve()
    direct = (manifest_parent / rel_path).resolve(strict=False)
    if not _is_within_root(direct, root_resolved):
        return None, "referenced file must stay within output directory"
    if direct.exists():
        return direct, None

    rooted = (root / rel_path).resolve(strict=False)
    if _is_within_root(rooted, root_resolved) and rooted.exists():
        return rooted, None

    matches = sorted(path.resolve() for path in root.rglob(glob.escape(rel_path)) if path.exists())
    if matches:
        return matches[0], None
    return direct, None


def _is_within_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _validate_root_dir(root: Path) -> str | None:
    if not root.exists():
        return f"Output directory does not exist: {root}"
    if not root.is_dir():
        return f"Output path is not a directory: {root}"
    return None


def _validate_aesthetic_prompt(manifest: dict, rel_manifest: Path, errors: list[str]) -> None:
    asset_family = str(manifest.get("asset_family", ""))
    if asset_family not in _STYLE_VALIDATED_FAMILIES:
        return
    prompt = manifest.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        errors.append(f"{rel_manifest}: prompt must be a non-empty string")
        return
    normalized_prompt = prompt.lower()
    for term in _BANNED_PROMPT_TERMS:
        if term in normalized_prompt:
            errors.append(f"{rel_manifest}: prompt contains banned style term {term!r}")
    missing_style_terms = [term for term in _REQUIRED_STYLE_TERMS if term not in normalized_prompt]
    if missing_style_terms:
        errors.append(
            f"{rel_manifest}: prompt must include FF style descriptors: {', '.join(missing_style_terms)}"
        )


def _validate_narrative_metadata(manifest: dict, rel_manifest: Path, errors: list[str]) -> None:
    asset_family = str(manifest.get("asset_family", ""))
    if asset_family not in _NARRATIVE_VALIDATED_FAMILIES:
        return
    narrative_tags = manifest.get("narrative_tags")
    if not isinstance(narrative_tags, dict):
        errors.append(f"{rel_manifest}: narrative_tags must be an object")
        return
    for key in NARRATIVE_TAG_KEYS:
        value = narrative_tags.get(key)
        if value not in NARRATIVE_TAG_VALUES[key]:
            allowed = ", ".join(NARRATIVE_TAG_VALUES[key])
            errors.append(
                f"{rel_manifest}: narrative_tags[{key!r}] must be one of [{allowed}], got {value!r}"
            )
    for field in ("world_region_id", "exploration_intent", "placement_intent"):
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{rel_manifest}: missing non-empty {field}")
