# Release Checklist: Static Asset Handoff (No Audio / No Animation)

Use this checklist exactly in order before handing Creation-Engine output to GameRewritten.

## 1) Build the deterministic full bundle

```bash
cd /home/runner/work/Creation-Engine/Creation-Engine
creation-engine full-bundle --seed 101 --output assets
```

Pass criteria:
- Command exits with status `0`.
- `assets/bundles/full_static.json` exists.

## 2) Run style and schema quality gate

```bash
creation-engine quality-check --output assets
```

Pass criteria:
- Command exits with status `0`.
- Output contains `Quality check passed`.
- No banned prompt term, metadata, or file reference errors are reported.

## 3) Run production bundle audit gate

```bash
creation-engine bundle-audit --output assets
```

Pass criteria:
- Command exits with status `0`.
- Output contains `FF aesthetic compliance: PASS`.
- Narrative and style coverage lines report full required coverage.

## 4) Run regression tests

```bash
python -m pytest tests/test_backend_and_api.py tests/test_cli.py
```

Pass criteria:
- Command exits with status `0`.
- All tests pass.

## 5) Validate bundle completeness matrix

Read file:
- `assets/bundles/full_static.json`

Pass criteria:
- `completeness_matrix.complete` is `true`.
- `missing_required_packs` is empty.
- `underfilled_packs` is empty.
- `missing_destination_targets` is empty.

## 6) Visual FF-style review sample set

Review a small sample from these output families:
- `assets/materials`
- `assets/terrain`
- `assets/props`
- `assets/architecture`
- `assets/ui/icons`

Pass criteria:
- Visual tone remains FF7-FF12 PS2-era stylized.
- No photoreal modern-AAA drift appears.
- Landmark silhouettes remain readable for modern JRPG gameplay density.

## Final release decision

Release is **APPROVED** only if all steps above pass.
Any failed step means **REJECTED** until fixed and re-run from step 1.
