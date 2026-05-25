# Release Checklist: Static Asset Handoff (No Audio / No Animation)

Use this checklist exactly in order before handing Creation-Engine output to GameRewritten.
Every step must exit with status `0` and every pass criterion must be true before proceeding.

---

## Prerequisites

- Python 3.10+ installed and `creation-engine` CLI available on PATH.
- Repository installed: `pip install -e .` from repo root.
- Output directory does **not** contain leftover artifacts from a previous rejected build.
  If re-running after a failure, delete the output directory first and start from step 1.

---

## Step 1 — Build the deterministic full bundle

```bash
cd <repo-root>
creation-engine full-bundle --seed 101 --output assets
```

**Pass criteria:**
- Command exits with status `0`.
- `assets/bundles/full_static.json` exists and is valid JSON.
- No Python tracebacks appear in stdout/stderr.

**Failure recovery:**
- If the command fails with `Full bundle completeness validation failed`, read the error
  message to find which pack is missing or underfilled, then rerun just that pack command
  (e.g. `creation-engine prop-pack --seed 101 --output assets`) before re-running
  `full-bundle`.

---

## Step 2 — Run style and schema quality gate

```bash
creation-engine quality-check --output assets
```

**Pass criteria:**
- Command exits with status `0`.
- Output contains the string `Quality check passed`.
- No `banned style term`, `style_profile`, `missing field`, or `referenced file` errors appear.

**Failure recovery:**
- `banned style term` — A prompt contains a forbidden word (`photoreal`, `hyperreal`, etc.).
  Edit `creation_engine/game_rewritten_bundle.py` to remove the offending prompt, then
  regenerate and re-run quality-check.
- `style_profile` mismatch — A manifest was written with the wrong profile string.  Re-run
  the affected pack generator (not the full bundle) and re-run quality-check.
- `missing field` — A required manifest field is absent.  This indicates a code regression
  in an exporter.  Run `python3 -m pytest tests/` to identify which test fails, fix the
  exporter, then regenerate.

---

## Step 3 — Run production bundle audit gate

```bash
creation-engine bundle-audit --output assets
```

**Pass criteria:**
- Command exits with status `0`.
- Output contains `FF aesthetic compliance: PASS`.
- `Narrative coverage:` shows `X/X` where both numbers are equal.
- `Style coverage:` shows `X/X` where both numbers are equal.

**Failure recovery:**
- `FF aesthetic compliance: FAIL` — One or more manifests lack `narrative_tags` or
  `style_profile`.  Inspect the audit output for family breakdown, re-run the failing pack
  generator, then re-run from step 2.
- Narrative coverage below 100% — Some manifests lack complete narrative tag sets.  Check
  `creation_engine/narrative_tags.py` and the relevant exporter, then regenerate.

---

## Step 4 — Run production release readiness gate

```bash
creation-engine release-check --output assets
```

**Pass criteria:**
- Command exits with status `0`.
- Output contains `Release readiness passed`.
- The manifest count shown matches the count reported in step 3 bundle-audit.

**Failure recovery:**
- This gate runs quality-check + bundle-audit + completeness matrix in sequence.  Read the
  specific sub-failure message and follow the recovery steps for that sub-gate above.

---

## Step 5 — Run regression test suite

```bash
python3 -m pytest tests/test_backend_and_api.py tests/test_cli.py tests/test_gui.py -q
```

**Pass criteria:**
- Command exits with status `0`.
- All tests pass (currently 36 tests).
- Zero test failures or errors.

**Failure recovery:**
- Run `python3 -m pytest tests/ -v` for verbose output to identify which test failed.
- Fix the identified regression before proceeding.  Do **not** delete failing tests.

---

## Step 6 — Validate bundle completeness matrix

Open: `assets/bundles/full_static.json`

Read the `completeness_matrix` object and confirm:

| Field | Required value |
|---|---|
| `complete` | `true` |
| `missing_required_packs` | `[]` (empty array) |
| `underfilled_packs` | `[]` (empty array) |
| `missing_destination_targets` | `[]` (empty array) |
| All `per_pack[*].meets_minimum` | `true` |

**Pass criteria:** All fields above match the required values.

**Failure recovery:**
- `missing_required_packs` non-empty — Regenerate the listed packs and re-run `full-bundle`.
- `underfilled_packs` non-empty — The prompt list for that pack in
  `creation_engine/game_rewritten_bundle.py` has fewer than 20 entries.  Add prompts and
  regenerate.

---

## Step 7 — Validate asset family coverage

Confirm the following output directories exist and contain the minimum file counts:

| Directory | Minimum JSON manifests |
|---|---|
| `assets/materials/` | 20 |
| `assets/terrain/` | 20 |
| `assets/tilesets/` | 20 |
| `assets/props/` | 20 |
| `assets/architecture/` | 20 |
| `assets/foliage/` | 20 |
| `assets/items/` | 20 |
| `assets/decals/` | 20 |
| `assets/ui/` | 60 (icons + panels + portraits) |
| `assets/characters/` | 20 |
| `assets/enemies/` | 20 |

Quick check command:

```bash
for d in assets/materials assets/terrain assets/tilesets assets/props \
          assets/architecture assets/foliage assets/items assets/decals \
          assets/characters assets/enemies; do
  count=$(find "$d" -name "*.json" | wc -l)
  echo "$d: $count manifests"
done
find assets/ui -name "*.json" | wc -l
```

**Pass criteria:** Each directory meets or exceeds its minimum.

---

## Step 8 — Visual FF-style review sample set

Sample a minimum of 5 assets from each of these families and inspect the generated PNG files:

- `assets/materials/` — Check albedo texture colour palette against PS2-era FF hue range.
- `assets/terrain/` — Verify biome ground textures read clearly at 128×128.
- `assets/props/` — Confirm 3-D silhouette is stylized, not hyper-detailed.
- `assets/architecture/` — Landmark structures should have clear JRPG fantasy silhouette.
- `assets/ui/` (icons) — Icons must read at small scale with bold colour separation.

**Pass criteria (for each sampled asset):**
- Visual tone remains FF7-FF12 PS2-era stylized (controlled saturation, readable silhouette).
- No photoreal modern-AAA surface detail appears.
- Landmark silhouettes remain readable at gameplay camera distances.
- UI icons read legibly at 32×32 pixels.

**Failure recovery:**
- If visual drift is detected, identify the prompt in `game_rewritten_bundle.py` that caused it,
  update the prompt to include `ps2 jrpg` style cues, then regenerate only the affected pack.

---

## Step 9 — Verify narrative metadata sampling

Open 3 manifests from different families and confirm each contains:

```json
{
  "narrative_tags": {
    "region": "<valid region>",
    "faction": "<valid faction>",
    "era": "<valid era>",
    "story_phase": "<valid phase>",
    "culture_theme": "<valid theme>"
  },
  "world_region_id": "<region>__<culture_theme>",
  "exploration_intent": "<intent string>",
  "placement_intent": "<intent string>"
}
```

Valid values are defined in `creation_engine/narrative_tags.py`.

**Pass criteria:** All three sampled manifests contain well-formed narrative metadata.

---

## Step 10 — Prepare GameRewritten import package

Assemble the final delivery directory:

```bash
mkdir -p delivery/static_assets
cp -r assets/materials  delivery/static_assets/
cp -r assets/terrain    delivery/static_assets/
cp -r assets/tilesets   delivery/static_assets/
cp -r assets/props      delivery/static_assets/
cp -r assets/architecture delivery/static_assets/
cp -r assets/foliage    delivery/static_assets/
cp -r assets/items      delivery/static_assets/
cp -r assets/decals     delivery/static_assets/
cp -r assets/ui         delivery/static_assets/
cp -r assets/characters delivery/static_assets/
cp -r assets/enemies    delivery/static_assets/
cp -r assets/bundles    delivery/static_assets/
```

Include the bundle manifest at the delivery root:

```bash
cp assets/bundles/full_static.json delivery/full_static_manifest.json
```

**Pass criteria:** `delivery/` tree is complete and `full_static_manifest.json` is valid JSON.

---

## Step 11 — GameRewritten content path mapping

Verify that each pack's `destination_map` matches the GameRewritten `Content/` tree.

| Asset family | GameRewritten content path |
|---|---|
| Materials / textures | `Content/Materials`, `Content/Textures` |
| Terrain biomes | `Content/Textures` |
| Tilesets | `Content/World` |
| Props / Architecture / Foliage / Items | `Content/Models` |
| Decals | `Content/Textures` |
| UI icons / panels / portraits | `Content/UI` |
| Character / enemy placeholders | `Content/Models` |
| Bundle manifests | `Content/Bundles` |

Cross-reference with `assets/bundles/full_static.json` → `destination_map` entries.

**Pass criteria:** Every `destination_map` entry matches the table above and no unknown paths appear.

---

## Final Release Decision

| # | Gate | Status |
|---|---|---|
| 1 | Full bundle generated | ☐ PASS / ☐ FAIL |
| 2 | Quality check passed | ☐ PASS / ☐ FAIL |
| 3 | Bundle audit passed | ☐ PASS / ☐ FAIL |
| 4 | Release readiness passed | ☐ PASS / ☐ FAIL |
| 5 | Regression tests passed | ☐ PASS / ☐ FAIL |
| 6 | Completeness matrix complete | ☐ PASS / ☐ FAIL |
| 7 | Family coverage minimums met | ☐ PASS / ☐ FAIL |
| 8 | Visual FF-style review passed | ☐ PASS / ☐ FAIL |
| 9 | Narrative metadata present | ☐ PASS / ☐ FAIL |
| 10 | Delivery package assembled | ☐ PASS / ☐ FAIL |
| 11 | GameRewritten path mapping verified | ☐ PASS / ☐ FAIL |

Release is **APPROVED** only if all gates above are marked PASS.
Any gate marked FAIL means **REJECTED** — fix and re-run from the failed step before
re-attempting the release decision.
