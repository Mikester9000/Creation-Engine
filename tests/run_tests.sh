#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

echo "--- Generating test assets ---"
./creation-engine create-texture --type noise    --seed 42  --size 64x64 --out assets/textures/test_noise.png
./creation-engine create-texture --type checker  --seed 0   --size 64x64 --out assets/textures/test_checker.png
./creation-engine create-map --width 20 --height 15 --tileSize 16 --out assets/maps/test_map.json
./creation-engine ai texture --prompt "lava rock" --seed 123 --size 64x64 --out assets/textures/test_lava.png
./creation-engine ai map --prompt "forest with river" --width 20 --height 15 --tileSize 16 --out assets/maps/test_forest.json --seed 42

echo "--- Running validation ---"
g++ -std=c++17 -o tests/validate_assets tests/validate_assets.cpp
./tests/validate_assets
echo "All tests complete."
