# Creation Engine Quick-Start Tutorial

## 1. Build
```bash
make
```

## 2. Generate textures
```bash
./creation-engine create-texture --type noise --seed 42 --size 64x64 --color ffffff --out assets/textures/ground.png
./creation-engine create-texture --type checker --seed 0 --size 64x64 --out assets/textures/checker.png
./creation-engine ai texture --prompt "lava rock" --seed 123 --size 64x64 --out assets/textures/lava.png
```

## 3. Create a tileset
```bash
./creation-engine create-tileset --from assets/textures/ground.png --tile 16x16 --out assets/maps/level1.tileset.json
```

## 4. Generate a map
```bash
./creation-engine create-map --width 30 --height 20 --tileSize 16 --tileset assets/maps/level1.tileset.json --out assets/maps/level1.json
./creation-engine ai map --prompt "forest with river" --width 30 --height 20 --tileSize 16 --seed 7 --out assets/maps/forest.json
```

## 5. Texture types
| Type | Description |
|------|-------------|
| noise | Perlin fBm noise |
| cellular | Worley/Voronoi noise |
| checker | Checkerboard |
| stripes | Alternating bands |
| gradient | Linear gradient |
| radial | Radial gradient |
| solid | Solid colour |
