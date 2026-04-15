/**
 * example_scene.cpp - Demonstrates loading and using Creation Engine assets.
 *
 * This program shows a complete workflow:
 *   1. Load a tileset JSON.
 *   2. Load the sprite sheet texture for the tileset.
 *   3. Load a map JSON.
 *   4. Iterate the tile layers and print a simple ASCII visualisation.
 *
 * Compile (from the repository root):
 *   g++ -std=c++17 -Isrc -Ivendor \
 *       examples/game-engine-integration/example_scene.cpp \
 *       examples/game-engine-integration/TextureLoader.cpp \
 *       examples/game-engine-integration/TilesetLoader.cpp \
 *       examples/game-engine-integration/MapLoader.cpp \
 *       src/AssetIO.o src/MapEditor.o src/TextureGenerator.o \
 *       src/Noise.o src/AIAssist.o \
 *       -o example_scene -lm
 */

#include <iostream>
#include <string>
#include "TextureLoader.h"
#include "TilesetLoader.h"
#include "MapLoader.h"
#include "../../src/MapEditor.h"

// ASCII characters representing different tile types
static char tileChar(int id) {
    switch (id) {
        case 0: return ' ';   // empty
        case 1: return '.';   // ground
        case 2: return '#';   // wall
        case 3: return '~';   // water / river
        case 4: return 'B';   // building wall
        case 5: return '_';   // building floor
        default: return '?';
    }
}

int main() {
    std::cout << "=== Creation Engine - Example Scene ===\n\n";

    // ---- Step 1: Load tileset ----
    Tileset tileset;
    if (!TilesetLoader::load("assets/maps/default.tileset.json", tileset)) {
        std::cerr << "Run 'make' and the CLI tests first to generate assets.\n";
        return 1;
    }

    // ---- Step 2: Load tileset texture (CPU side) ----
    CPUImage tilesetImg;
    // The tileset texture may not exist in this demo; that's fine.
    if (TextureLoader::loadCPU(tileset.texturePath, tilesetImg)) {
        GPUTextureHandle gpuHandle = TextureLoader::uploadToGPU(tilesetImg);
        std::cout << "  GPU texture handle: " << gpuHandle << "\n\n";
        TextureLoader::freeGPU(gpuHandle);
    }

    // ---- Step 3: Load a map ----
    GameMap map;
    if (!MapLoader::load("assets/maps/test_map.json", map)) {
        return 1;
    }

    // ---- Step 4: Print ASCII visualisation of the first tile layer ----
    if (!map.tileLayers.empty()) {
        std::cout << "\nLayer: " << map.tileLayers[0].name << "\n";
        const TileLayer& layer = map.tileLayers[0];
        for (int y = 0; y < layer.height; ++y) {
            for (int x = 0; x < layer.width; ++x) {
                std::cout << tileChar(layer.at(x, y));
            }
            std::cout << "\n";
        }
    }

    // ---- Step 5: Print spawn points ----
    std::cout << "\nSpawn points:\n";
    for (const auto& sp : map.spawnPoints) {
        std::cout << "  " << sp.name << " @ (" << sp.x << ", " << sp.y << ")\n";
    }

    std::cout << "\nDone.\n";
    return 0;
}
