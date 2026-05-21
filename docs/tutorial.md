# Creation Engine Static Asset Tutorial

Follow every step in order. Do not skip steps. Use the exact commands shown.

## Step 1 — Install the package

```bash
cd Creation-Engine
pip install -e ".[dev]"
```

## Step 2 — Generate a single texture

```bash
creation-engine texture --prompt "wet stone" --seed 42 --output assets
```

Expected output: `assets/wet_stone_albedo.png`, `assets/wet_stone.json`.

## Step 3 — Generate a single tilemap

```bash
creation-engine map --prompt "forest with river and road" --seed 42 --output assets
```

Expected output: `assets/forest_with_river_and_road.json`.

## Step 4 — Generate a single static mesh

```bash
creation-engine mesh --prompt "stone pillar" --seed 42 --output assets
```

Expected output: `assets/stone_pillar.obj`, `assets/stone_pillar.mtl`, `assets/stone_pillar.json`.

## Step 5 — Generate UI assets

```bash
creation-engine ui-icon --prompt "quest icon" --seed 42 --output assets
creation-engine ui-panel --prompt "inventory panel" --seed 42 --output assets
creation-engine portrait --prompt "hero portrait" --seed 42 --output assets
```

Expected output: one PNG and one JSON per command in `assets/`.

## Step 6 — Generate material and terrain packs

```bash
creation-engine material-pack --seed 101 --output assets
creation-engine biome-pack --seed 101 --output assets
creation-engine tileset-pack --seed 101 --output assets
```

Expected output: subdirectories under `assets/` with manifests for each pack.

## Step 7 — Generate prop, architecture, and foliage packs

```bash
creation-engine prop-pack --seed 101 --output assets
creation-engine architecture-pack --seed 101 --output assets
creation-engine foliage-pack --seed 101 --output assets
```

## Step 8 — Generate item, decal, and character packs

```bash
creation-engine item-pack --seed 101 --output assets
creation-engine decal-pack --seed 101 --output assets
creation-engine character-static-pack --seed 101 --output assets
creation-engine enemy-static-pack --seed 101 --output assets
```

## Step 9 — Generate the full GameRewritten static bundle

```bash
creation-engine full-bundle --seed 101 --output assets
```

Expected output: `assets/bundles/full_static.json` listing all asset packs.

## Step 10 — Validate the output

```bash
creation-engine quality-check --output assets
```

Expected result: `Quality check passed (N manifests validated)`. If it fails, fix the reported errors before continuing.

## Rules

- Keep animation out of scope. Do not add rigging or skeletal data.
- Keep audio out of scope. Do not add music, voice, or sound effects.
- Use the same seed for repeatable, deterministic output.
- Generate one asset family at a time when debugging.
- Always run `quality-check` after generating a new bundle.

