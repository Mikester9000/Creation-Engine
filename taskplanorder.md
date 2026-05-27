# Task Plan Order — Creation-Engine Retail Deployment Completion
**Optimized for Qwen2.5-Coder-1.5B (or any small local LLM)**
**One file per task. One task at a time. No skipping. No reordering.**

---

## HOW TO USE THIS FILE

1. Read **only the current task card**.
2. Read the files listed in **READ_FILE / READ_LINES** first.
3. Make **exactly** the change described in **EXACT CHANGE**.
4. Run the **VERIFY COMMAND** shown.
5. If verification passes, move to the next task card.
6. If verification fails, re-read the task card and try again. Do not proceed until it passes.

---

---

# TASK 01
**Task Name:** Add `asset_family` field to individual map JSON exports

**Logic and purpose:**
The quality-check loop in `quality_check.py` skips any JSON file that does not contain the key `"asset_family"`. The function `export_tilemap` in `map_exporter.py` assembles a dict called `output` that is written as the map JSON, but this dict never includes `"asset_family"`. Every standalone map file is therefore invisible to quality-check, bundle-audit, and release-check. Adding one key-value pair fixes this for all future generated maps.

**Narrative code structure:**
Inside `export_tilemap`, the `output` dict is assembled starting at the line `output = {`. Add the key `"asset_family": "maps"` as the first key in that dict. This mirrors exactly what texture and mesh exporters already do via `build_manifest`.

**File to edit:**
`creation_engine/export/map_exporter.py`

**READ_FILE:** `creation_engine/export/map_exporter.py`
**READ_LINES:** 44–78

**Lines to edit:**
Line 44 — the line that begins `output = {`
Insert `"asset_family": "maps",` as the first key inside the dict literal.

**Number of lines to modify:** 1 line inserted (the dict body gains one new key-value pair)

**EXACT CHANGE:**
Find this block (line 44):
```python
    output = {
        "version": "1.1",
        "name": name,
```
Change to:
```python
    output = {
        "asset_family": "maps",
        "version": "1.1",
        "name": name,
```

**VERIFY COMMAND:**
```bash
python -m pytest tests/test_backend_and_api.py tests/test_cli.py -q
```
Expected: All tests pass. No errors.

---

---

# TASK 02
**Task Name:** Add tileset ID cross-reference check to quality validator

**Logic and purpose:**
After TASK 01 makes map JSONs visible to quality-check, the validator should also confirm that the `tileset` field in every map manifest refers to a real tileset ID from the known spec library. If someone generates a map referencing a deleted or misspelled tileset, quality-check should catch it.

**Narrative code structure:**
In `quality_check.py`, inside the `run_quality_check` function, after the call to `_validate_narrative_metadata`, add a call to a new helper `_validate_map_tileset_id`. This helper imports `TILESET_SPECS` from `creation_engine.map.tileset_specs`, builds the set of valid IDs, reads `manifest.get("tileset")`, and appends an error if the value is missing or not in the valid set. The helper only runs when `asset_family == "maps"`.

**File to edit:**
`creation_engine/quality_check.py`

**READ_FILE:** `creation_engine/quality_check.py`
**READ_LINES:** 97–154 (the for-loop body inside `run_quality_check`)
**READ_LINES ALSO:** 326–374 (existing helper functions at bottom of file, for style reference)

**Lines to edit:**
Line ~119 — after the line `_validate_narrative_metadata(manifest, rel_manifest, errors)`
Insert one call: `_validate_map_tileset_id(manifest, rel_manifest, errors)`

Then at the **end of the file** (after `_dedupe_errors`), add the new helper function.

**Number of lines to modify:** 1 line inserted (call site) + 12 lines added (helper function at end of file)

**EXACT CHANGE — Step A (insert call after line 119):**
Find:
```python
        _validate_narrative_metadata(manifest, rel_manifest, errors)

        content_target = manifest.get("content_target")
```
Change to:
```python
        _validate_narrative_metadata(manifest, rel_manifest, errors)
        _validate_map_tileset_id(manifest, rel_manifest, errors)

        content_target = manifest.get("content_target")
```

**EXACT CHANGE — Step B (append helper at end of file after `_dedupe_errors`):**
```python

def _validate_map_tileset_id(manifest: dict, rel_manifest: Path, errors: list[str]) -> None:
    if str(manifest.get("asset_family", "")) != "maps":
        return
    from creation_engine.map.tileset_specs import TILESET_SPECS
    valid_ids = frozenset(spec["id"] for spec in TILESET_SPECS.values())
    tileset_id = manifest.get("tileset")
    if not isinstance(tileset_id, str) or not tileset_id.strip():
        errors.append(f"{rel_manifest}: maps must include a non-empty tileset field")
        return
    if tileset_id not in valid_ids:
        errors.append(
            f"{rel_manifest}: tileset id {tileset_id!r} is not a known tileset id"
        )
```

**VERIFY COMMAND:**
```bash
python -m pytest tests/test_backend_and_api.py tests/test_cli.py -q
```
Expected: All tests pass. No errors.

---

---

# TASK 03
**Task Name:** Add test for map asset_family visibility in quality-check

**Logic and purpose:**
TASK 01 adds `"asset_family": "maps"` to map JSONs. TASK 02 adds a tileset ID check. A regression test must confirm that after generating a map via CLI, quality-check counts that map in `checked_manifests` and passes. Without this test a future regression removing the field would be silent.

**Narrative code structure:**
New test function `test_map_is_visible_to_quality_check` in `tests/test_cli.py`. It runs `main(["map", "--prompt", "ps2 jrpg forest", "--seed", "7", "--output", str(tmp_path)])`, then calls `run_quality_check(tmp_path)`, and asserts `result.checked_manifests >= 1` and `result.ok is True`.

**File to edit:**
`tests/test_cli.py`

**READ_FILE:** `tests/test_cli.py`
**READ_LINES:** 1–10 (imports, to match style)
**READ_LINES ALSO:** 125–170 (end of file, to find insertion point)

**Lines to edit:**
End of file — append new test function after the last existing test.

**Number of lines to modify:** 0 lines changed, ~18 lines appended.

**EXACT CHANGE (append to end of file):**
```python


def test_map_is_visible_to_quality_check(tmp_path):
    rc = main(
        [
            "map",
            "--prompt",
            "ps2 jrpg forest",
            "--seed",
            "7",
            "--output",
            str(tmp_path),
        ]
    )
    assert rc == 0
    result = run_quality_check(tmp_path)
    assert result.checked_manifests >= 1
    assert result.ok is True
```

**VERIFY COMMAND:**
```bash
python -m pytest tests/test_cli.py::test_map_is_visible_to_quality_check -v
```
Expected: 1 test passes.

---

---

# TASK 04
**Task Name:** Add test for invalid narrative tag value rejection

**Logic and purpose:**
The function `_validate_narrative_metadata` in `quality_check.py` rejects manifests whose `narrative_tags` contain a value outside the allowed taxonomy. The failure path has no test. If someone weakens the narrative gate, no existing test would catch it.

**Narrative code structure:**
New test function `test_quality_check_rejects_invalid_narrative_tag_value` in `tests/test_cli.py`. It generates a texture, opens its manifest, overwrites `narrative_tags["region"]` with `"invalid_zone"` (which is not in the allowed taxonomy), saves the manifest back, then calls `run_quality_check(tmp_path)` and asserts `result.ok is False` and at least one error contains `"narrative_tags"`.

**File to edit:**
`tests/test_cli.py`

**READ_FILE:** `tests/test_cli.py`
**READ_LINES:** 1–10 (imports)
**READ_LINES ALSO:** end of file (to find insertion point after TASK 03's test)

**Lines to edit:**
End of file — append new test function after `test_map_is_visible_to_quality_check`.

**Number of lines to modify:** 0 lines changed, ~22 lines appended.

**EXACT CHANGE (append to end of file):**
```python


def test_quality_check_rejects_invalid_narrative_tag_value(tmp_path):
    rc = main(
        [
            "texture",
            "--prompt",
            "ps2 jrpg stone",
            "--seed",
            "42",
            "--output",
            str(tmp_path),
        ]
    )
    assert rc == 0
    manifest_path = tmp_path / "stone.json"
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    manifest["narrative_tags"]["region"] = "invalid_zone"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    result = run_quality_check(tmp_path)
    assert result.ok is False
    assert any("narrative_tags" in error for error in result.errors)
```

**VERIFY COMMAND:**
```bash
python -m pytest tests/test_cli.py::test_quality_check_rejects_invalid_narrative_tag_value -v
```
Expected: 1 test passes.

---

---

# TASK 05
**Task Name:** Add LOD policy content assertions to mesh manifest tests

**Logic and purpose:**
`mesh_builder.py` injects a `lod_policy` dict into every mesh. The existing test `test_engine_generates_assets` confirms the key exists but does not check that the tier keys (`lod0`, `lod1`, `lod2`) are present or that `lod0` equals 0. A regression in the LOD spec table in `mesh_builder.py` would currently pass silently.

**Narrative code structure:**
New test function `test_mesh_manifest_contains_lod_policy` in `tests/test_backend_and_api.py`. It creates a `CreationEngine`, calls `generate_mesh("ps2 jrpg stone pillar", complexity="low")`, opens the `.json` manifest, and asserts `manifest["lod_policy"]` has keys `"lod0"`, `"lod1"`, `"lod2"` and that `manifest["lod_policy"]["lod0"] == 0`.

**File to edit:**
`tests/test_backend_and_api.py`

**READ_FILE:** `tests/test_backend_and_api.py`
**READ_LINES:** 1–10 (imports)
**READ_LINES ALSO:** 50–62 (existing mesh manifest test, for style reference)
**READ_LINES ALSO:** 190–194 (end of file, insertion point)

**Lines to edit:**
End of file — append new test function.

**Number of lines to modify:** 0 lines changed, ~18 lines appended.

**EXACT CHANGE (append to end of file):**
```python


def test_mesh_manifest_contains_lod_policy(tmp_path):
    engine = CreationEngine(output_dir=tmp_path)
    mesh_file = engine.generate_mesh("ps2 jrpg stone pillar", complexity="low")
    manifest_path = mesh_file.parent / (mesh_file.stem + ".json")
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    lod = manifest["lod_policy"]
    assert "lod0" in lod
    assert "lod1" in lod
    assert "lod2" in lod
    assert lod["lod0"] == 0
```

**VERIFY COMMAND:**
```bash
python -m pytest tests/test_backend_and_api.py::test_mesh_manifest_contains_lod_policy -v
```
Expected: 1 test passes.

---

---

# TASK 06
**Task Name:** Add region-chunk determinism test

**Logic and purpose:**
`generate_tilemap` in `map_gen.py` accepts `chunk_x`, `chunk_y` and uses them to salt the RNG seed so each world chunk is unique but reproducible. No test currently verifies: (a) same inputs → same output, (b) different chunk coords → different output. This is a critical property for an open-world content pipeline.

**Narrative code structure:**
New test function `test_generate_tilemap_chunk_determinism` in `tests/test_backend_and_api.py`. It calls `generate_tilemap("ps2 jrpg forest", width=8, height=8, seed=5, chunk_x=0, chunk_y=0)` twice and asserts the tile arrays are equal with `np.array_equal`. Then calls with `chunk_x=1, chunk_y=0` and asserts the tile arrays differ.

**File to edit:**
`tests/test_backend_and_api.py`

**READ_FILE:** `tests/test_backend_and_api.py`
**READ_LINES:** 1–10 (imports, confirm `generate_tilemap` is imported)
**READ_LINES ALSO:** end of file after TASK 05's test (insertion point)

**Lines to edit:**
End of file — append new test function after `test_mesh_manifest_contains_lod_policy`.

**Number of lines to modify:** 0 lines changed, ~20 lines appended.

**EXACT CHANGE (append to end of file):**
```python


def test_generate_tilemap_chunk_determinism():
    result_a = generate_tilemap("ps2 jrpg forest", width=8, height=8, seed=5, chunk_x=0, chunk_y=0)
    result_b = generate_tilemap("ps2 jrpg forest", width=8, height=8, seed=5, chunk_x=0, chunk_y=0)
    tiles_a = np.array(result_a["tiles"])
    tiles_b = np.array(result_b["tiles"])
    assert np.array_equal(tiles_a, tiles_b), "Same seed+chunk must produce same tiles"

    result_c = generate_tilemap("ps2 jrpg forest", width=8, height=8, seed=5, chunk_x=1, chunk_y=0)
    tiles_c = np.array(result_c["tiles"])
    assert not np.array_equal(tiles_a, tiles_c), "Different chunk must produce different tiles"
```

**VERIFY COMMAND:**
```bash
python -m pytest tests/test_backend_and_api.py::test_generate_tilemap_chunk_determinism -v
```
Expected: 1 test passes.

---

---

# TASK 07
**Task Name:** Add all-packs completeness assertion to bundle test

**Logic and purpose:**
`test_full_bundle_manifest_includes_completeness_matrix` currently only asserts that `material_pack` has `meets_minimum == True`. All 13 packs must be verified. If any pack silently drops assets, the existing test passes while the bundle is incomplete.

**Narrative code structure:**
Extend `test_full_bundle_manifest_includes_completeness_matrix` in `tests/test_backend_and_api.py` to add a loop over `matrix["per_pack"].items()` asserting every pack has `meets_minimum is True`, and assert that `len(matrix["per_pack"]) == 13`.

**File to edit:**
`tests/test_backend_and_api.py`

**READ_FILE:** `tests/test_backend_and_api.py`
**READ_LINES:** 77–89 (existing `test_full_bundle_manifest_includes_completeness_matrix`)

**Lines to edit:**
Lines 85–89 (inside the existing test, after the last assert) — append 4 more assert lines inside the same function body.

**Number of lines to modify:** 0 lines changed, 4 lines appended inside existing function.

**EXACT CHANGE:**
Find the end of the existing test function (after line `assert matrix["per_pack"]["material_pack"]["meets_minimum"] is True`):
```python
    assert matrix["per_pack"]["material_pack"]["meets_minimum"] is True
```
Change to:
```python
    assert matrix["per_pack"]["material_pack"]["meets_minimum"] is True
    assert len(matrix["per_pack"]) == 13
    for pack_name, pack_data in matrix["per_pack"].items():
        assert pack_data["meets_minimum"] is True, f"{pack_name} does not meet minimum asset count"
```

**VERIFY COMMAND:**
```bash
python -m pytest tests/test_backend_and_api.py::test_full_bundle_manifest_includes_completeness_matrix -v
```
Expected: 1 test passes.

---

---

# TASK 08
**Task Name:** Add pytest configuration to pyproject.toml

**Logic and purpose:**
`pyproject.toml` defines the package but has no `[tool.pytest.ini_options]` section. Without this, `python -m pytest` with no arguments may use environment defaults and may not discover all tests. Adding a minimal pytest config makes test discovery consistent across all environments.

**Narrative code structure:**
Append a `[tool.pytest.ini_options]` table to the bottom of `pyproject.toml` with `testpaths = ["tests"]` and `addopts = ["-q", "--tb=short"]`. Optionally add a `[tool.coverage.run]` table to define coverage source.

**File to edit:**
`pyproject.toml`

**READ_FILE:** `pyproject.toml`
**READ_LINES:** 1–end (read whole file to find the last line)

**Lines to edit:**
End of file — append 8 lines.

**Number of lines to modify:** 0 lines changed, 8 lines appended.

**EXACT CHANGE (append to end of file):**
```toml

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-q", "--tb=short"]

[tool.coverage.run]
source = ["creation_engine"]
```

**VERIFY COMMAND:**
```bash
python -m pytest -q
```
Expected: All tests discovered and pass. No import errors.

---

---

# TASK 09
**Task Name:** Update GameRewritten plan doc to align with current implementation

**Logic and purpose:**
`docs/ff-game-rewrite-plan.md` was written before the current architecture. It does not mention the 18-tileset system, 5-dimension narrative taxonomy, 13-pack bundle recipe with minimum counts, the 3-command release gate, LOD policy, or completeness matrix. The document is the human handoff contract for GameRewritten and must be accurate.

**Narrative code structure:**
Add a new section at the **end** of the document titled `## Implementation Facts (Current)`. This section lists the real CLI commands, real module names, real pack list, real release gate sequence, and the manifest contract fields. Do NOT remove or rewrite any existing narrative/world design content. Only add the new section at the end.

**File to edit:**
`docs/ff-game-rewrite-plan.md`

**READ_FILE:** `docs/ff-game-rewrite-plan.md`
**READ_LINES:** 1–30 (read the top to understand structure)
**READ_LINES ALSO:** last 20 lines (find the exact end of file for appending)

**Lines to edit:**
End of file — append the new section.

**Number of lines to modify:** 0 lines changed, ~60 lines appended.

**EXACT CHANGE (append to end of file):**
```markdown

---

## Implementation Facts (Current — 2026-05-27)

The following facts reflect the actual implemented state of the codebase.
This section supersedes any earlier architectural descriptions in this document.

### CLI Commands (Stable)
```
creation-engine texture         -- PBR textures + material JSON
creation-engine map             -- Tilemap JSON
creation-engine mesh            -- OBJ + MTL + mesh manifest
creation-engine ui-icon         -- UI icon PNG + manifest
creation-engine ui-panel        -- UI panel PNG + manifest
creation-engine portrait        -- Portrait card PNG + manifest
creation-engine material-pack   -- 20 material prompts
creation-engine biome-pack      -- 20 terrain prompts
creation-engine tileset-pack    -- 20 tileset prompts
creation-engine prop-pack       -- 20 prop prompts
creation-engine architecture-pack  -- 20 architecture prompts
creation-engine foliage-pack    -- 20 foliage prompts
creation-engine item-pack       -- 20 item prompts
creation-engine decal-pack      -- 20 decal prompts
creation-engine character-static-pack  -- 20 NPC prompts
creation-engine enemy-static-pack      -- 20 enemy prompts
creation-engine full-bundle     -- All 13 packs in one command
creation-engine quality-check   -- Validate manifests
creation-engine bundle-audit    -- Coverage + FF compliance report
creation-engine release-check   -- Full production gate
```

### Required Packs (13 total, 20 assets each = 260 total)
1. material_pack
2. biome_pack
3. tileset_pack
4. prop_pack
5. architecture_pack
6. foliage_pack
7. item_pack
8. decal_pack
9. ui_icon_pack
10. ui_panel_pack
11. ui_portrait_pack
12. character_static_pack
13. enemy_static_pack

### Narrative Taxonomy (5 dimensions)
Every manifest includes `narrative_tags` with exactly these keys:
- `region`: overworld, frontier, forest, desert, coast, highlands, volcanic, ruins, temple, capital, port_town, wasteland, cavern
- `faction`: neutral, imperial, rebel, merchant_guild, shrine_order, ancients, corrupted
- `era`: ancient, golden_age, war_of_ruin, present_day, post_cataclysm
- `story_phase`: prologue, early_journey, mid_conflict, late_revelation, endgame
- `culture_theme`: royal, sacred, magitek, rustic, maritime, nomadic, mystic, corrupted

### Tileset Themes (18 total)
overworld, town, dungeon, cave, coast, desert, snowfield, temple, ruins, castle,
forest, capital_city, port_city, highlands, volcanic, sacred_ruins, imperial_fortress, wasteland

### Release Gate Sequence (exact commands, in order)
```bash
creation-engine full-bundle --seed 101 --output assets
creation-engine quality-check --output assets
creation-engine bundle-audit --output assets
creation-engine release-check --output assets
python -m pytest tests/test_backend_and_api.py tests/test_cli.py tests/test_gui.py
bash tests/run_tests.sh
```
All commands must exit 0. Any non-zero exit is a blocker.

### Manifest Contract Fields (required in every asset manifest)
- `asset_family` — string identifying asset type
- `style_profile` — must equal `"ps2_ff7_ff12_highest_quality_ps2"`
- `content_target` — dict mapping to GameRewritten content paths
- `narrative_tags` — 5-key taxonomy dict (see above)
- `world_region_id` — derived string (region__culture_theme)
- `exploration_intent` — one of: dungeon_exploration, settlement_navigation, open_world_traversal, overworld_traversal
- `placement_intent` — family-specific placement hint string
- `prompt` — source prompt string (must not contain banned terms)
```

**VERIFY COMMAND:**
```bash
python -m pytest -q
```
Expected: All tests still pass. (This task edits only a .md file — no code change.)

---

---

# TASK 10
**Task Name:** Final validation — run full pipeline end-to-end

**Logic and purpose:**
After Tasks 01–09 are applied, the complete pipeline must be validated in one run. This confirms: generation works, all quality gates pass, all tests pass, and no regressions were introduced.

**No file to edit.** This is an execution-only task.

**EXACT COMMANDS (run in order, all must exit 0):**
```bash
cd /path/to/Creation-Engine
pip install -e . -q
python -m pytest tests/test_backend_and_api.py tests/test_cli.py tests/test_gui.py -q
bash tests/run_tests.sh
```

**READ_FILE:** `tests/run_tests.sh`
**READ_LINES:** 1–30

**Pass criteria:**
- `pytest` reports 0 failures, 0 errors
- `bash tests/run_tests.sh` prints `All tests complete.` with no non-zero exit codes
- `quality-check` prints `Quality check passed`
- `bundle-audit` prints `FF aesthetic compliance: PASS`
- `release-check` prints `Release readiness passed`

**If any command fails:**
- Read the first error line carefully
- Identify which task card introduced that failure
- Re-apply that task card's EXACT CHANGE
- Re-run TASK 10 from the beginning

---

---

## Summary Table

| Task | File | Lines Changed | Purpose |
|------|------|---------------|---------|
| 01 | `creation_engine/export/map_exporter.py` | 1 line inserted | Add asset_family to map JSON |
| 02 | `creation_engine/quality_check.py` | 1 line inserted + 12 lines appended | Tileset ID cross-reference check |
| 03 | `tests/test_cli.py` | 18 lines appended | Map quality-check visibility test |
| 04 | `tests/test_cli.py` | 22 lines appended | Invalid narrative tag rejection test |
| 05 | `tests/test_backend_and_api.py` | 18 lines appended | LOD policy content assertion |
| 06 | `tests/test_backend_and_api.py` | 20 lines appended | Chunk determinism test |
| 07 | `tests/test_backend_and_api.py` | 4 lines appended inside existing test | All-packs completeness assertion |
| 08 | `pyproject.toml` | 8 lines appended | Pytest config |
| 09 | `docs/ff-game-rewrite-plan.md` | ~60 lines appended | Plan doc alignment |
| 10 | (no file) | — | Final validation run |

**Total code lines changed: ~164 lines across 5 files.**
**After Task 10 passes: Creation-Engine is retail-ready for GameRewritten handoff.**
