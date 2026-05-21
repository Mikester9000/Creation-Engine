# Creation Engine Static Asset Tutorial

## 1. Build
```bash
make
```

## 2. Generate one texture family
```bash
./creation-engine texture --prompt "wet stone" --seed 42 --output assets
```

## 3. Generate one map
```bash
./creation-engine map --prompt "forest with river and road" --seed 42 --output assets
```

## 4. Generate one static mesh
```bash
./creation-engine mesh --prompt "stone pillar" --seed 42 --output assets
```

## 5. Generate one UI asset
```bash
./creation-engine ui-icon --prompt "quest icon" --seed 42 --output assets
```

## 6. Generate a material pack
```bash
./creation-engine material-pack --seed 42 --output assets
```

## 7. Generate the full static bundle
```bash
./creation-engine full-bundle --seed 42 --output assets
```

## 8. Rules
- Keep animation out of scope.
- Keep audio out of scope.
- Use the same seed for repeatable output.
- Generate one family at a time when debugging.
